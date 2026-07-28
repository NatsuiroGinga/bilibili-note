#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/traffic-control-module.h"

#include <cstdint>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace ns3;

namespace {

struct ScenarioConfig {
  std::string name;
  double benignRateMbps;
  double attackRateMbps;
  bool hasAttack;
  bool capacityShift;
  bool randomLoss;
};

ScenarioConfig ResolveScenario(const std::string &name) {
  if (name == "benign-low") {
    return {name, 0.25, 0.0, false, false, false};
  }
  if (name == "benign-high") {
    return {name, 0.90, 0.0, false, false, false};
  }
  if (name == "benign-capacity-shift") {
    return {name, 0.90, 0.0, false, true, false};
  }
  if (name == "benign-random-loss") {
    return {name, 0.75, 0.0, false, false, true};
  }
  if (name == "dos-udp-medium") {
    return {name, 0.25, 8.0, true, false, false};
  }
  if (name == "dos-udp-high") {
    return {name, 0.25, 15.0, true, false, false};
  }
  if (name == "dos-udp-capacity-shift") {
    return {name, 0.25, 8.0, true, true, false};
  }
  throw std::invalid_argument("未知场景：" + name);
}

class QueueWindowCollector {
public:
  QueueWindowCollector(const std::string &outputPath,
                       const ScenarioConfig &scenario, uint32_t seed,
                       uint32_t run, double windowSeconds,
                       double durationSeconds,
                       const std::vector<double> &attackStartSeconds,
                       int64_t jitterStreamBase, double jitterMaxMs,
                       int64_t errorStream, double downstreamErrorRate,
                       uint64_t capacityBps, uint32_t queueLimitPackets)
      : m_output(outputPath), m_scenario(scenario), m_seed(seed), m_run(run),
        m_windowSeconds(windowSeconds), m_durationSeconds(durationSeconds),
        m_attackStartSeconds(attackStartSeconds),
        m_jitterStreamBase(jitterStreamBase), m_jitterMaxMs(jitterMaxMs),
        m_errorStream(errorStream), m_downstreamErrorRate(downstreamErrorRate),
        m_capacityBps(capacityBps), m_windowStartCapacityBps(capacityBps),
        m_queueLimitPackets(queueLimitPackets) {
    if (!m_output.is_open()) {
      throw std::runtime_error("无法创建输出文件：" + outputPath);
    }
    m_output
        << "schema_version,scenario_id,topology_id,queue_model,group_id,seed,"
           "run,"
           "window_index,"
           "window_start_s,window_end_s,is_attack,attack_exposure_fraction,"
           "traffic_phase,label_primary,label_family,label_subtype,jitter_"
           "stream_base,"
           "jitter_max_ms,error_stream,downstream_error_rate,capacity_start_"
           "bps,"
           "capacity_end_bps,service_budget_bytes,"
           "queue_limit_packets,"
           "queue_start_bytes,queue_end_bytes,offered_bytes,enqueued_bytes,"
           "departed_bytes,dropped_before_enqueue_bytes,dropped_after_dequeue_"
           "bytes,"
           "device_tx_drop_bytes,downstream_error_loss_bytes,sink_received_"
           "bytes,"
           "enqueued_packets,departed_packets,"
           "dropped_before_enqueue_packets,dropped_after_dequeue_packets,"
           "device_tx_drop_packets,downstream_error_loss_packets,sink_received_"
           "packets,"
           "queue_balance_residual_bytes\n";
  }

  void Start() {
    Simulator::Schedule(Seconds(m_windowSeconds), &QueueWindowCollector::Flush,
                        this);
  }

  void SetCapacity(uint64_t capacityBps) {
    const double now = Simulator::Now().GetSeconds();
    m_capacityBitSeconds += m_capacityBps * (now - m_lastCapacityUpdateSeconds);
    m_lastCapacityUpdateSeconds = now;
    m_capacityBps = capacityBps;
  }

  void OnEnqueue(Ptr<const QueueDiscItem> item) {
    const auto bytes = static_cast<uint64_t>(item->GetSize());
    m_enqueuedBytes += bytes;
    m_enqueuedPackets += 1;
    m_currentQueueBytes += bytes;
  }

  void OnDequeue(Ptr<const QueueDiscItem> item) {
    const auto bytes = static_cast<uint64_t>(item->GetSize());
    NS_ABORT_MSG_IF(m_currentQueueBytes < bytes, "队列追踪出现负字节数");
    m_departedBytes += bytes;
    m_departedPackets += 1;
    m_currentQueueBytes -= bytes;
  }

  void OnDropBeforeEnqueue(Ptr<const QueueDiscItem> item, const char *) {
    m_droppedBeforeBytes += item->GetSize();
    m_droppedBeforePackets += 1;
  }

  void OnDropAfterDequeue(Ptr<const QueueDiscItem> item, const char *) {
    // 该包已经通过 Dequeue 离开队列，不能在队列余额中再次扣减。
    m_droppedAfterBytes += item->GetSize();
    m_droppedAfterPackets += 1;
  }

  void OnDeviceTxDrop(Ptr<const Packet> packet) {
    m_deviceTxDropBytes += packet->GetSize();
    m_deviceTxDropPackets += 1;
  }

  void OnDownstreamErrorLoss(Ptr<const Packet> packet) {
    m_downstreamErrorLossBytes += packet->GetSize();
    m_downstreamErrorLossPackets += 1;
  }

  void OnSinkRx(Ptr<const Packet> packet, const Address &) {
    m_sinkReceivedBytes += packet->GetSize();
    m_sinkReceivedPackets += 1;
  }

private:
  void Flush() {
    const double windowEnd = Simulator::Now().GetSeconds();
    const double windowStart = windowEnd - m_windowSeconds;
    double attackExposureFraction = 0.0;
    for (const double attackStart : m_attackStartSeconds) {
      if (windowEnd <= attackStart) {
        continue;
      }
      attackExposureFraction +=
          windowStart >= attackStart
              ? 1.0
              : (windowEnd - attackStart) / m_windowSeconds;
    }
    if (!m_attackStartSeconds.empty()) {
      attackExposureFraction /= m_attackStartSeconds.size();
    }
    const bool attackActive = attackExposureFraction > 0.0;
    const std::string trafficPhase =
        !attackActive
            ? "benign"
            : (attackExposureFraction < 1.0 - 1e-9 ? "transition" : "attack");
    m_capacityBitSeconds +=
        m_capacityBps * (windowEnd - m_lastCapacityUpdateSeconds);
    const double serviceBudgetBytes = m_capacityBitSeconds / 8.0;
    const uint64_t offeredBytes = m_enqueuedBytes + m_droppedBeforeBytes;
    const int64_t residual = static_cast<int64_t>(m_currentQueueBytes) -
                             static_cast<int64_t>(m_windowStartQueueBytes) -
                             static_cast<int64_t>(offeredBytes) +
                             static_cast<int64_t>(m_departedBytes) +
                             static_cast<int64_t>(m_droppedBeforeBytes);
    const std::string labelPrimary = attackActive ? "malicious" : "benign";
    const std::string labelFamily = attackActive ? "dos" : "benign";
    const std::string labelSubtype = attackActive ? "udp" : "benign";
    std::ostringstream groupId;
    groupId << "star-bottleneck-v1|" << m_scenario.name << "|seed" << m_seed
            << "|run" << m_run;

    m_output << "flow_probe_ns3_queue_v3," << m_scenario.name
             << ",star-bottleneck-v1,fifo-queue-disc," << groupId.str() << ','
             << m_seed << ',' << m_run << ',' << m_windowIndex << ','
             << std::fixed << std::setprecision(6) << windowStart << ','
             << windowEnd << ',' << (attackActive ? 1 : 0) << ','
             << attackExposureFraction << ',' << trafficPhase << ','
             << labelPrimary << ',' << labelFamily << ',' << labelSubtype << ','
             << m_jitterStreamBase << ',' << m_jitterMaxMs << ','
             << m_errorStream << ',' << m_downstreamErrorRate << ','
             << m_windowStartCapacityBps << ',' << m_capacityBps << ','
             << serviceBudgetBytes << ',' << m_queueLimitPackets << ','
             << m_windowStartQueueBytes << ',' << m_currentQueueBytes << ','
             << offeredBytes << ',' << m_enqueuedBytes << ',' << m_departedBytes
             << ',' << m_droppedBeforeBytes << ',' << m_droppedAfterBytes << ','
             << m_deviceTxDropBytes << ',' << m_downstreamErrorLossBytes << ','
             << m_sinkReceivedBytes << ',' << m_enqueuedPackets << ','
             << m_departedPackets << ',' << m_droppedBeforePackets << ','
             << m_droppedAfterPackets << ',' << m_deviceTxDropPackets << ','
             << m_downstreamErrorLossPackets << ',' << m_sinkReceivedPackets
             << ',' << residual << '\n';
    m_output.flush();

    m_windowStartQueueBytes = m_currentQueueBytes;
    m_enqueuedBytes = 0;
    m_departedBytes = 0;
    m_droppedBeforeBytes = 0;
    m_droppedAfterBytes = 0;
    m_deviceTxDropBytes = 0;
    m_downstreamErrorLossBytes = 0;
    m_sinkReceivedBytes = 0;
    m_enqueuedPackets = 0;
    m_departedPackets = 0;
    m_droppedBeforePackets = 0;
    m_droppedAfterPackets = 0;
    m_deviceTxDropPackets = 0;
    m_downstreamErrorLossPackets = 0;
    m_sinkReceivedPackets = 0;
    m_capacityBitSeconds = 0.0;
    m_lastCapacityUpdateSeconds = windowEnd;
    m_windowStartCapacityBps = m_capacityBps;
    m_windowIndex += 1;

    if (windowEnd + m_windowSeconds <= m_durationSeconds + 1e-9) {
      Simulator::Schedule(Seconds(m_windowSeconds),
                          &QueueWindowCollector::Flush, this);
    }
  }

  std::ofstream m_output;
  ScenarioConfig m_scenario;
  uint32_t m_seed;
  uint32_t m_run;
  double m_windowSeconds;
  double m_durationSeconds;
  std::vector<double> m_attackStartSeconds;
  int64_t m_jitterStreamBase;
  double m_jitterMaxMs;
  int64_t m_errorStream;
  double m_downstreamErrorRate;
  uint64_t m_capacityBps;
  uint64_t m_windowStartCapacityBps;
  uint32_t m_queueLimitPackets;
  uint32_t m_windowIndex{0};
  uint64_t m_currentQueueBytes{0};
  uint64_t m_windowStartQueueBytes{0};
  uint64_t m_enqueuedBytes{0};
  uint64_t m_departedBytes{0};
  uint64_t m_droppedBeforeBytes{0};
  uint64_t m_droppedAfterBytes{0};
  uint64_t m_deviceTxDropBytes{0};
  uint64_t m_downstreamErrorLossBytes{0};
  uint64_t m_sinkReceivedBytes{0};
  uint64_t m_enqueuedPackets{0};
  uint64_t m_departedPackets{0};
  uint64_t m_droppedBeforePackets{0};
  uint64_t m_droppedAfterPackets{0};
  uint64_t m_deviceTxDropPackets{0};
  uint64_t m_downstreamErrorLossPackets{0};
  uint64_t m_sinkReceivedPackets{0};
  double m_capacityBitSeconds{0.0};
  double m_lastCapacityUpdateSeconds{0.0};
};

void ChangeCapacity(Ptr<PointToPointNetDevice> device,
                    QueueWindowCollector *collector, uint64_t capacityBps) {
  device->SetDataRate(DataRate(capacityBps));
  collector->SetCapacity(capacityBps);
}

ApplicationContainer InstallOnOff(Ptr<Node> sender, Ipv4Address destination,
                                  uint16_t port, double rateMbps,
                                  double startSeconds, double stopSeconds) {
  OnOffHelper source("ns3::UdpSocketFactory",
                     InetSocketAddress(destination, port));
  std::ostringstream rate;
  rate << rateMbps << "Mbps";
  source.SetAttribute("DataRate", DataRateValue(DataRate(rate.str())));
  source.SetAttribute("PacketSize", UintegerValue(1024));
  source.SetAttribute("OnTime",
                      StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  source.SetAttribute("OffTime",
                      StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  auto applications = source.Install(sender);
  applications.Start(Seconds(startSeconds));
  applications.Stop(Seconds(stopSeconds));
  return applications;
}

} // namespace

int main(int argc, char *argv[]) {
  std::string scenarioName = "benign-low";
  std::string outputPath = "queue-truth.csv";
  uint32_t seed = 42;
  uint32_t run = 1;
  double durationSeconds = 12.0;
  double windowSeconds = 0.1;
  double attackStartSeconds = 5.0;
  uint32_t senderCount = 4;
  uint32_t queueLimitPackets = 50;
  uint64_t initialCapacityBps = 5000000;
  uint64_t shiftedCapacityBps = 2500000;
  constexpr int64_t jitterStreamBase = 100;
  constexpr int64_t errorStream = 500;
  constexpr double jitterMaxSeconds = 0.04;
  constexpr double downstreamErrorRate = 0.01;

  CommandLine command(__FILE__);
  command.AddValue("scenario", "受控场景名称", scenarioName);
  command.AddValue("output", "真值 CSV 输出路径", outputPath);
  command.AddValue("seed", "随机种子", seed);
  command.AddValue("run", "同一种子的独立运行编号", run);
  command.AddValue("duration", "仿真时长，单位秒", durationSeconds);
  command.AddValue("window", "聚合窗口，单位秒", windowSeconds);
  command.Parse(argc, argv);

  const ScenarioConfig scenario = ResolveScenario(scenarioName);
  NS_ABORT_MSG_IF(windowSeconds <= 0.0 || durationSeconds <= windowSeconds,
                  "窗口与仿真时长不合法");
  RngSeedManager::SetSeed(seed);
  RngSeedManager::SetRun(run);

  std::vector<double> sourceStartSeconds;
  std::vector<double> attackStartTimes;
  sourceStartSeconds.reserve(senderCount);
  attackStartTimes.reserve(senderCount - 1);
  for (uint32_t index = 0; index < senderCount; ++index) {
    auto startJitter = CreateObject<UniformRandomVariable>();
    startJitter->SetStream(jitterStreamBase + index);
    const bool attackSource = scenario.hasAttack && index > 0;
    const double baseStart = attackSource ? attackStartSeconds : 1.0;
    const double actualStart =
        baseStart + startJitter->GetValue(0.0, jitterMaxSeconds);
    sourceStartSeconds.push_back(actualStart);
    if (attackSource) {
      attackStartTimes.push_back(actualStart);
    }
  }

  NodeContainer senders;
  senders.Create(senderCount);
  NodeContainer router;
  router.Create(1);
  NodeContainer victim;
  victim.Create(1);
  NodeContainer all;
  all.Add(senders);
  all.Add(router);
  all.Add(victim);
  InternetStackHelper internet;
  internet.Install(all);

  PointToPointHelper access;
  access.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
  access.SetChannelAttribute("Delay", StringValue("1ms"));
  for (uint32_t index = 0; index < senderCount; ++index) {
    auto devices = access.Install(senders.Get(index), router.Get(0));
    std::ostringstream network;
    network << "10.1." << (index + 1) << ".0";
    Ipv4AddressHelper address;
    address.SetBase(network.str().c_str(), "255.255.255.0");
    address.Assign(devices);
  }

  PointToPointHelper bottleneck;
  bottleneck.SetDeviceAttribute("DataRate",
                                DataRateValue(DataRate(initialCapacityBps)));
  bottleneck.SetChannelAttribute("Delay", StringValue("5ms"));
  // 显式队列规则承载瓶颈积压，设备队列只保留发送串行化所需的最小缓冲。
  bottleneck.SetQueue("ns3::DropTailQueue", "MaxSize", StringValue("1p"));
  auto bottleneckDevices = bottleneck.Install(router.Get(0), victim.Get(0));
  auto routerDevice =
      DynamicCast<PointToPointNetDevice>(bottleneckDevices.Get(0));
  auto victimDevice =
      DynamicCast<PointToPointNetDevice>(bottleneckDevices.Get(1));
  NS_ABORT_MSG_IF(routerDevice == nullptr || victimDevice == nullptr,
                  "瓶颈链路设备类型不正确");

  TrafficControlHelper trafficControl;
  std::ostringstream queueLimit;
  queueLimit << queueLimitPackets << 'p';
  trafficControl.SetRootQueueDisc("ns3::FifoQueueDisc", "MaxSize",
                                  StringValue(queueLimit.str()));
  auto queueDiscs = trafficControl.Install(routerDevice);
  auto queueDisc = queueDiscs.Get(0);
  NS_ABORT_MSG_IF(queueDisc == nullptr, "无法安装瓶颈 FifoQueueDisc");

  Ipv4AddressHelper bottleneckAddress;
  bottleneckAddress.SetBase("10.2.0.0", "255.255.255.0");
  auto bottleneckInterfaces = bottleneckAddress.Assign(bottleneckDevices);
  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  if (scenario.randomLoss) {
    auto errorModel = CreateObject<RateErrorModel>();
    errorModel->SetAttribute("ErrorUnit",
                             EnumValue(RateErrorModel::ERROR_UNIT_PACKET));
    errorModel->SetAttribute("ErrorRate", DoubleValue(downstreamErrorRate));
    errorModel->AssignStreams(errorStream);
    victimDevice->SetAttribute("ReceiveErrorModel", PointerValue(errorModel));
  }

  QueueWindowCollector collector(
      outputPath, scenario, seed, run, windowSeconds, durationSeconds,
      attackStartTimes, jitterStreamBase, jitterMaxSeconds * 1000.0,
      errorStream, scenario.randomLoss ? downstreamErrorRate : 0.0,
      initialCapacityBps, queueLimitPackets);
  queueDisc->TraceConnectWithoutContext(
      "Enqueue", MakeCallback(&QueueWindowCollector::OnEnqueue, &collector));
  queueDisc->TraceConnectWithoutContext(
      "Dequeue", MakeCallback(&QueueWindowCollector::OnDequeue, &collector));
  queueDisc->TraceConnectWithoutContext(
      "DropBeforeEnqueue",
      MakeCallback(&QueueWindowCollector::OnDropBeforeEnqueue, &collector));
  queueDisc->TraceConnectWithoutContext(
      "DropAfterDequeue",
      MakeCallback(&QueueWindowCollector::OnDropAfterDequeue, &collector));
  routerDevice->TraceConnectWithoutContext(
      "MacTxDrop",
      MakeCallback(&QueueWindowCollector::OnDeviceTxDrop, &collector));
  victimDevice->TraceConnectWithoutContext(
      "PhyRxDrop",
      MakeCallback(&QueueWindowCollector::OnDownstreamErrorLoss, &collector));

  constexpr uint16_t port = 9000;
  PacketSinkHelper sink("ns3::UdpSocketFactory",
                        InetSocketAddress(Ipv4Address::GetAny(), port));
  auto sinkApplications = sink.Install(victim.Get(0));
  sinkApplications.Start(Seconds(0.5));
  sinkApplications.Stop(Seconds(durationSeconds));
  auto packetSink = DynamicCast<PacketSink>(sinkApplications.Get(0));
  packetSink->TraceConnectWithoutContext(
      "Rx", MakeCallback(&QueueWindowCollector::OnSinkRx, &collector));

  const Ipv4Address victimAddress = bottleneckInterfaces.GetAddress(1);
  const double trafficStopSeconds = durationSeconds;
  if (scenario.hasAttack) {
    InstallOnOff(senders.Get(0), victimAddress, port, scenario.benignRateMbps,
                 sourceStartSeconds[0], trafficStopSeconds);
    for (uint32_t index = 1; index < senderCount; ++index) {
      InstallOnOff(senders.Get(index), victimAddress, port,
                   scenario.attackRateMbps, sourceStartSeconds[index],
                   trafficStopSeconds);
    }
  } else {
    for (uint32_t index = 0; index < senderCount; ++index) {
      InstallOnOff(senders.Get(index), victimAddress, port,
                   scenario.benignRateMbps, sourceStartSeconds[index],
                   trafficStopSeconds);
    }
  }

  if (scenario.capacityShift) {
    Simulator::Schedule(Seconds(6.0), &ChangeCapacity, routerDevice, &collector,
                        shiftedCapacityBps);
  }
  collector.Start();
  Simulator::Stop(Seconds(durationSeconds + 0.001));
  Simulator::Run();
  Simulator::Destroy();
  return 0;
}
