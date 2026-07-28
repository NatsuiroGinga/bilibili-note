#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/traffic-control-module.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <limits>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace ns3;

namespace {

struct DomainConfig {
  std::string configId{"smoke"};
  std::string split{"smoke"};
  uint32_t seed{20260722};
  uint32_t run{1};
  double durationSeconds{12.0};
  double windowSeconds{0.1};
  std::string trafficMode{"benign"};
  std::string transport{"udp"};
  std::string queueModel{"fifo"};
  std::string arrivalModel{"constant"};
  double initialCapacityMbps{5.0};
  double shiftedCapacityMbps{5.0};
  double capacityShiftSeconds{0.0};
  double accessDelayMs{1.0};
  double bottleneckDelayMs{5.0};
  uint32_t queueLimitPackets{50};
  double downstreamLossRate{0.0};
  uint32_t senderCount{4};
  double benignRateMbps{0.5};
  double attackRateMbps{8.0};
  double attackStartSeconds{5.0};
  uint32_t packetSizeBytes{1024};
  double jitterMaxMs{40.0};
  double burstOnMeanSeconds{0.2};
  double burstOffMeanSeconds{0.1};
  double measurementNoiseStdRatio{0.0};
  std::string outputPath{"domain-randomized-v5.csv"};
};

uint64_t MbpsToBps(double value) {
  return static_cast<uint64_t>(std::llround(value * 1000000.0));
}

std::string RateString(double mbps) {
  std::ostringstream value;
  value << std::fixed << std::setprecision(6) << mbps << "Mbps";
  return value.str();
}

std::string DelayString(double milliseconds) {
  std::ostringstream value;
  value << std::fixed << std::setprecision(6) << milliseconds << "ms";
  return value.str();
}

std::string QueueDiscType(const std::string &queueModel) {
  if (queueModel == "fifo") {
    return "ns3::FifoQueueDisc";
  }
  if (queueModel == "codel") {
    return "ns3::CoDelQueueDisc";
  }
  if (queueModel == "red") {
    return "ns3::RedQueueDisc";
  }
  throw std::invalid_argument("未知队列策略：" + queueModel);
}

std::string SocketFactoryName(const std::string &transport) {
  if (transport == "udp") {
    return "ns3::UdpSocketFactory";
  }
  if (transport == "tcp") {
    return "ns3::TcpSocketFactory";
  }
  throw std::invalid_argument("未知传输协议：" + transport);
}

void ValidateConfig(const DomainConfig &config) {
  NS_ABORT_MSG_IF(config.configId.empty() || config.split.empty(),
                  "配置标识与切分不能为空");
  NS_ABORT_MSG_IF(config.seed == 0 || config.run == 0,
                  "随机种子与运行编号必须为正整数");
  NS_ABORT_MSG_IF(config.durationSeconds <= config.windowSeconds ||
                      config.windowSeconds <= 0.0,
                  "窗口与仿真时长不合法");
  NS_ABORT_MSG_IF(config.trafficMode != "benign" &&
                      config.trafficMode != "dos",
                  "流量模式必须为 benign 或 dos");
  SocketFactoryName(config.transport);
  QueueDiscType(config.queueModel);
  NS_ABORT_MSG_IF(config.arrivalModel != "constant" &&
                      config.arrivalModel != "bursty",
                  "到达过程必须为 constant 或 bursty");
  NS_ABORT_MSG_IF(config.initialCapacityMbps <= 0.0 ||
                      config.shiftedCapacityMbps <= 0.0,
                  "链路容量必须为正数");
  NS_ABORT_MSG_IF(config.capacityShiftSeconds < 0.0 ||
                      config.capacityShiftSeconds >= config.durationSeconds,
                  "容量变化时刻不合法");
  NS_ABORT_MSG_IF(config.accessDelayMs <= 0.0 ||
                      config.bottleneckDelayMs <= 0.0,
                  "链路时延必须为正数");
  NS_ABORT_MSG_IF(config.queueLimitPackets == 0 || config.senderCount < 2,
                  "队列上限必须为正数且发送端不得少于两个");
  NS_ABORT_MSG_IF(config.downstreamLossRate < 0.0 ||
                      config.downstreamLossRate >= 1.0,
                  "独立丢包率必须位于 [0,1)");
  NS_ABORT_MSG_IF(config.benignRateMbps <= 0.0 ||
                      config.attackRateMbps <= 0.0,
                  "发送速率必须为正数");
  NS_ABORT_MSG_IF(config.attackStartSeconds <= 0.0 ||
                      config.attackStartSeconds >= config.durationSeconds,
                  "攻击起始时刻不合法");
  NS_ABORT_MSG_IF(config.packetSizeBytes < 64 || config.packetSizeBytes > 1500,
                  "应用负载包长必须位于 64 至 1500 字节");
  NS_ABORT_MSG_IF(config.jitterMaxMs < 0.0 ||
                      config.burstOnMeanSeconds <= 0.0 ||
                      config.burstOffMeanSeconds <= 0.0,
                  "起始抖动和突发参数不合法");
  NS_ABORT_MSG_IF(config.measurementNoiseStdRatio < 0.0,
                  "测量噪声标准差比例不得为负数");
}

class QueueWindowCollector {
public:
  QueueWindowCollector(const DomainConfig &config,
                       const std::vector<double> &attackStartTimes,
                       uint64_t initialCapacityBps)
      : m_config(config), m_attackStartTimes(attackStartTimes),
        m_capacityBps(initialCapacityBps),
        m_windowStartCapacityBps(initialCapacityBps),
        m_noiseGenerator(static_cast<uint64_t>(config.seed) * 1000003ULL +
                         config.run),
        m_noiseDistribution(0.0, config.measurementNoiseStdRatio),
        m_output(config.outputPath) {
    if (!m_output.is_open()) {
      throw std::runtime_error("无法创建输出文件：" + config.outputPath);
    }
    m_output
        << "schema_version,config_id,split,group_id,seed,run,window_index,"
           "window_start_s,window_end_s,public_total_packets,"
           "public_total_l3_bytes,public_packet_length_mean_l3_bytes,"
           "public_packet_length_min_l3_bytes,"
           "public_packet_length_max_l3_bytes,public_iat_mean_ms,"
           "public_packet_rate_pps,public_byte_rate_Bps,"
           "supervision_measurement_noise_std_ratio,supervision_traffic_mode,"
           "supervision_transport,supervision_queue_model,"
           "supervision_arrival_model,supervision_initial_capacity_bps,"
           "supervision_shifted_capacity_bps,"
           "supervision_capacity_shift_s,supervision_access_delay_ms,"
           "supervision_bottleneck_delay_ms,"
           "supervision_queue_limit_packets,"
           "supervision_downstream_loss_rate,supervision_sender_count,"
           "supervision_benign_rate_mbps,supervision_attack_rate_mbps,"
           "supervision_attack_start_s,supervision_packet_size_bytes,"
           "supervision_jitter_max_ms,supervision_burst_on_mean_s,"
           "supervision_burst_off_mean_s,supervision_is_attack,"
           "supervision_attack_exposure_fraction,"
           "supervision_capacity_start_bps,supervision_capacity_end_bps,"
           "supervision_capacity_integral_link_bytes,"
           "supervision_queue_start_l3_bytes,"
           "supervision_queue_end_l3_bytes,"
           "supervision_qdisc_received_l3_bytes,"
           "supervision_qdisc_enqueued_l3_bytes,"
           "supervision_qdisc_dequeued_l3_bytes,"
           "supervision_qdisc_dropped_before_enqueue_l3_bytes,"
           "supervision_qdisc_dropped_after_dequeue_l3_bytes,"
           "supervision_downstream_error_loss_ppp_frame_bytes,"
           "supervision_sink_received_app_payload_bytes,"
           "supervision_queue_start_packets,supervision_queue_end_packets,"
           "supervision_qdisc_received_packets,"
           "supervision_qdisc_enqueued_packets,"
           "supervision_qdisc_dequeued_packets,"
           "supervision_qdisc_dropped_before_enqueue_packets,"
           "supervision_qdisc_dropped_after_dequeue_packets,"
           "supervision_downstream_error_loss_packets,"
           "supervision_sink_received_packets,"
           "supervision_queue_balance_residual_l3_bytes,"
           "supervision_queue_balance_residual_packets\n";
  }

  void Start() {
    Simulator::Schedule(Seconds(m_config.windowSeconds),
                        &QueueWindowCollector::Flush, this);
  }

  void SetCapacity(uint64_t capacityBps) {
    const double now = Simulator::Now().GetSeconds();
    m_capacityBitSeconds += m_capacityBps * (now - m_lastCapacityUpdateSeconds);
    m_lastCapacityUpdateSeconds = now;
    m_capacityBps = capacityBps;
  }

  void OnEnqueue(Ptr<const QueueDiscItem> item) {
    RecordArrival(item);
    const uint64_t bytes = item->GetSize();
    m_enqueuedBytes += bytes;
    m_enqueuedPackets += 1;
    m_currentQueueBytes += bytes;
    m_currentQueuePackets += 1;
  }

  void OnDequeue(Ptr<const QueueDiscItem> item) {
    const uint64_t bytes = item->GetSize();
    NS_ABORT_MSG_IF(m_currentQueueBytes < bytes || m_currentQueuePackets == 0,
                    "队列追踪出现负状态");
    m_dequeuedBytes += bytes;
    m_dequeuedPackets += 1;
    m_currentQueueBytes -= bytes;
    m_currentQueuePackets -= 1;
  }

  void OnDropBeforeEnqueue(Ptr<const QueueDiscItem> item, const char *) {
    RecordArrival(item);
    m_droppedBeforeBytes += item->GetSize();
    m_droppedBeforePackets += 1;
  }

  void OnDropAfterDequeue(Ptr<const QueueDiscItem> item, const char *) {
    m_droppedAfterBytes += item->GetSize();
    m_droppedAfterPackets += 1;
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
  void RecordArrival(Ptr<const QueueDiscItem> item) {
    const uint64_t bytes = item->GetSize();
    m_arrivalMinBytes = std::min(m_arrivalMinBytes, bytes);
    m_arrivalMaxBytes = std::max(m_arrivalMaxBytes, bytes);
    const double now = Simulator::Now().GetSeconds();
    if (m_hasPreviousArrival) {
      m_arrivalIatSumSeconds += now - m_previousArrivalSeconds;
      m_arrivalIatCount += 1;
    }
    m_previousArrivalSeconds = now;
    m_hasPreviousArrival = true;
  }

  double NoisyValue(double truth) {
    if (truth <= 0.0 || m_config.measurementNoiseStdRatio == 0.0) {
      return truth;
    }
    return std::max(0.0, truth * (1.0 + m_noiseDistribution(m_noiseGenerator)));
  }

  void Flush() {
    const double windowEnd = Simulator::Now().GetSeconds();
    const double windowStart = windowEnd - m_config.windowSeconds;
    m_capacityBitSeconds +=
        m_capacityBps * (windowEnd - m_lastCapacityUpdateSeconds);
    const double capacityIntegralBytes = m_capacityBitSeconds / 8.0;
    const uint64_t receivedBytes = m_enqueuedBytes + m_droppedBeforeBytes;
    const uint64_t receivedPackets = m_enqueuedPackets + m_droppedBeforePackets;
    const int64_t residualBytes =
        static_cast<int64_t>(m_currentQueueBytes) -
        static_cast<int64_t>(m_windowStartQueueBytes) -
        static_cast<int64_t>(receivedBytes) +
        static_cast<int64_t>(m_dequeuedBytes) +
        static_cast<int64_t>(m_droppedBeforeBytes);
    const int64_t residualPackets =
        static_cast<int64_t>(m_currentQueuePackets) -
        static_cast<int64_t>(m_windowStartQueuePackets) -
        static_cast<int64_t>(receivedPackets) +
        static_cast<int64_t>(m_dequeuedPackets) +
        static_cast<int64_t>(m_droppedBeforePackets);

    double attackExposure = 0.0;
    for (const double attackStart : m_attackStartTimes) {
      if (windowEnd > attackStart) {
        attackExposure += windowStart >= attackStart
                              ? 1.0
                              : (windowEnd - attackStart) /
                                    m_config.windowSeconds;
      }
    }
    if (!m_attackStartTimes.empty()) {
      attackExposure /= m_attackStartTimes.size();
    }

    const double publicPackets = NoisyValue(receivedPackets);
    const double publicBytes = NoisyValue(receivedBytes);
    const double packetLengthMean =
        publicPackets > 0.0 ? publicBytes / publicPackets : 0.0;
    const double packetLengthMin =
        receivedPackets > 0 ? NoisyValue(m_arrivalMinBytes) : 0.0;
    const double packetLengthMax =
        receivedPackets > 0 ? NoisyValue(m_arrivalMaxBytes) : 0.0;
    const double iatMeanMs =
        m_arrivalIatCount > 0
            ? 1000.0 * m_arrivalIatSumSeconds / m_arrivalIatCount
            : 0.0;
    const std::string groupId = m_config.configId + "|seed" +
                                std::to_string(m_config.seed) + "|run" +
                                std::to_string(m_config.run);

    m_output << "flow_probe_ns3_domain_randomization_v5," << m_config.configId
             << ',' << m_config.split << ',' << groupId << ',' << m_config.seed
             << ',' << m_config.run << ',' << m_windowIndex << ',' << std::fixed
             << std::setprecision(9) << windowStart << ',' << windowEnd << ','
             << publicPackets << ',' << publicBytes << ',' << packetLengthMean
             << ',' << packetLengthMin << ',' << packetLengthMax << ','
             << iatMeanMs << ',' << publicPackets / m_config.windowSeconds << ','
             << publicBytes / m_config.windowSeconds << ','
             << m_config.measurementNoiseStdRatio << ',' << m_config.trafficMode
             << ',' << m_config.transport << ',' << m_config.queueModel << ','
             << m_config.arrivalModel << ','
             << MbpsToBps(m_config.initialCapacityMbps) << ','
             << MbpsToBps(m_config.shiftedCapacityMbps) << ','
             << m_config.capacityShiftSeconds << ',' << m_config.accessDelayMs
             << ',' << m_config.bottleneckDelayMs << ','
             << m_config.queueLimitPackets << ','
             << m_config.downstreamLossRate << ',' << m_config.senderCount << ','
             << m_config.benignRateMbps << ',' << m_config.attackRateMbps << ','
             << m_config.attackStartSeconds << ',' << m_config.packetSizeBytes
             << ',' << m_config.jitterMaxMs << ','
             << m_config.burstOnMeanSeconds << ','
             << m_config.burstOffMeanSeconds << ','
             << (attackExposure > 0.0 ? 1 : 0) << ',' << attackExposure << ','
             << m_windowStartCapacityBps << ',' << m_capacityBps << ','
             << capacityIntegralBytes << ',' << m_windowStartQueueBytes << ','
             << m_currentQueueBytes << ',' << receivedBytes << ','
             << m_enqueuedBytes << ',' << m_dequeuedBytes << ','
             << m_droppedBeforeBytes << ',' << m_droppedAfterBytes << ','
             << m_downstreamErrorLossBytes << ',' << m_sinkReceivedBytes << ','
             << m_windowStartQueuePackets << ',' << m_currentQueuePackets << ','
             << receivedPackets << ',' << m_enqueuedPackets << ','
             << m_dequeuedPackets << ',' << m_droppedBeforePackets << ','
             << m_droppedAfterPackets << ',' << m_downstreamErrorLossPackets
             << ',' << m_sinkReceivedPackets << ',' << residualBytes << ','
             << residualPackets << '\n';
    m_output.flush();

    m_windowStartCapacityBps = m_capacityBps;
    m_windowStartQueueBytes = m_currentQueueBytes;
    m_windowStartQueuePackets = m_currentQueuePackets;
    m_enqueuedBytes = 0;
    m_dequeuedBytes = 0;
    m_droppedBeforeBytes = 0;
    m_droppedAfterBytes = 0;
    m_downstreamErrorLossBytes = 0;
    m_sinkReceivedBytes = 0;
    m_enqueuedPackets = 0;
    m_dequeuedPackets = 0;
    m_droppedBeforePackets = 0;
    m_droppedAfterPackets = 0;
    m_downstreamErrorLossPackets = 0;
    m_sinkReceivedPackets = 0;
    m_arrivalMinBytes = std::numeric_limits<uint64_t>::max();
    m_arrivalMaxBytes = 0;
    m_arrivalIatSumSeconds = 0.0;
    m_arrivalIatCount = 0;
    m_hasPreviousArrival = false;
    m_capacityBitSeconds = 0.0;
    m_lastCapacityUpdateSeconds = windowEnd;
    m_windowIndex += 1;

    if (windowEnd + m_config.windowSeconds <=
        m_config.durationSeconds + 1e-9) {
      Simulator::Schedule(Seconds(m_config.windowSeconds),
                          &QueueWindowCollector::Flush, this);
    }
  }

  DomainConfig m_config;
  std::vector<double> m_attackStartTimes;
  uint64_t m_capacityBps;
  uint64_t m_windowStartCapacityBps;
  std::mt19937_64 m_noiseGenerator;
  std::normal_distribution<double> m_noiseDistribution;
  std::ofstream m_output;
  uint32_t m_windowIndex{0};
  uint64_t m_currentQueueBytes{0};
  uint64_t m_windowStartQueueBytes{0};
  uint64_t m_currentQueuePackets{0};
  uint64_t m_windowStartQueuePackets{0};
  uint64_t m_enqueuedBytes{0};
  uint64_t m_dequeuedBytes{0};
  uint64_t m_droppedBeforeBytes{0};
  uint64_t m_droppedAfterBytes{0};
  uint64_t m_downstreamErrorLossBytes{0};
  uint64_t m_sinkReceivedBytes{0};
  uint64_t m_enqueuedPackets{0};
  uint64_t m_dequeuedPackets{0};
  uint64_t m_droppedBeforePackets{0};
  uint64_t m_droppedAfterPackets{0};
  uint64_t m_downstreamErrorLossPackets{0};
  uint64_t m_sinkReceivedPackets{0};
  uint64_t m_arrivalMinBytes{std::numeric_limits<uint64_t>::max()};
  uint64_t m_arrivalMaxBytes{0};
  double m_arrivalIatSumSeconds{0.0};
  uint64_t m_arrivalIatCount{0};
  bool m_hasPreviousArrival{false};
  double m_previousArrivalSeconds{0.0};
  double m_capacityBitSeconds{0.0};
  double m_lastCapacityUpdateSeconds{0.0};
};

void ChangeCapacity(Ptr<PointToPointNetDevice> device,
                    Ptr<QueueDisc> queueDisc, const std::string &queueModel,
                    QueueWindowCollector *collector, uint64_t capacityBps) {
  device->SetDataRate(DataRate(capacityBps));
  if (queueModel == "red") {
    queueDisc->SetAttribute("LinkBandwidth",
                            DataRateValue(DataRate(capacityBps)));
  }
  collector->SetCapacity(capacityBps);
}

ApplicationContainer InstallSource(Ptr<Node> sender, Ipv4Address destination,
                                   uint16_t port, const DomainConfig &config,
                                   double rateMbps, double startSeconds,
                                   int64_t stream) {
  OnOffHelper source(SocketFactoryName(config.transport),
                     InetSocketAddress(destination, port));
  source.SetAttribute("DataRate", DataRateValue(DataRate(RateString(rateMbps))));
  source.SetAttribute("PacketSize", UintegerValue(config.packetSizeBytes));
  if (config.arrivalModel == "constant") {
    source.SetAttribute(
        "OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
    source.SetAttribute(
        "OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  } else {
    std::ostringstream onTime;
    onTime << "ns3::ExponentialRandomVariable[Mean="
           << config.burstOnMeanSeconds << ']';
    std::ostringstream offTime;
    offTime << "ns3::ExponentialRandomVariable[Mean="
            << config.burstOffMeanSeconds << ']';
    source.SetAttribute("OnTime", StringValue(onTime.str()));
    source.SetAttribute("OffTime", StringValue(offTime.str()));
  }
  auto applications = source.Install(sender);
  auto onOff = DynamicCast<OnOffApplication>(applications.Get(0));
  NS_ABORT_MSG_IF(onOff == nullptr, "无法创建 OnOffApplication");
  onOff->AssignStreams(stream);
  applications.Start(Seconds(startSeconds));
  applications.Stop(Seconds(config.durationSeconds));
  return applications;
}

} // namespace

int main(int argc, char *argv[]) {
  DomainConfig config;
  CommandLine command(__FILE__);
  command.AddValue("configId", "唯一配置标识", config.configId);
  command.AddValue("split", "配置切分", config.split);
  command.AddValue("seed", "随机种子", config.seed);
  command.AddValue("run", "独立运行编号", config.run);
  command.AddValue("duration", "仿真时长，单位秒", config.durationSeconds);
  command.AddValue("window", "聚合窗口，单位秒", config.windowSeconds);
  command.AddValue("trafficMode", "流量模式", config.trafficMode);
  command.AddValue("transport", "传输协议", config.transport);
  command.AddValue("queueModel", "队列策略", config.queueModel);
  command.AddValue("arrivalModel", "到达过程", config.arrivalModel);
  command.AddValue("initialCapacityMbps", "初始容量", config.initialCapacityMbps);
  command.AddValue("shiftedCapacityMbps", "变化后容量", config.shiftedCapacityMbps);
  command.AddValue("capacityShiftSeconds", "容量变化时刻", config.capacityShiftSeconds);
  command.AddValue("accessDelayMs", "接入时延", config.accessDelayMs);
  command.AddValue("bottleneckDelayMs", "瓶颈时延", config.bottleneckDelayMs);
  command.AddValue("queueLimitPackets", "队列包上限", config.queueLimitPackets);
  command.AddValue("downstreamLossRate", "独立下游丢包率", config.downstreamLossRate);
  command.AddValue("senderCount", "发送端数量", config.senderCount);
  command.AddValue("benignRateMbps", "单良性发送端速率", config.benignRateMbps);
  command.AddValue("attackRateMbps", "单攻击发送端速率", config.attackRateMbps);
  command.AddValue("attackStartSeconds", "攻击开始时刻", config.attackStartSeconds);
  command.AddValue("packetSizeBytes", "应用负载包长", config.packetSizeBytes);
  command.AddValue("jitterMaxMs", "起始抖动上限", config.jitterMaxMs);
  command.AddValue("burstOnMeanSeconds", "突发开启均值", config.burstOnMeanSeconds);
  command.AddValue("burstOffMeanSeconds", "突发关闭均值", config.burstOffMeanSeconds);
  command.AddValue("measurementNoiseStdRatio", "公共观测噪声比例", config.measurementNoiseStdRatio);
  command.AddValue("output", "v5 CSV 输出路径", config.outputPath);
  command.Parse(argc, argv);
  ValidateConfig(config);

  RngSeedManager::SetSeed(config.seed);
  RngSeedManager::SetRun(config.run);
  const uint64_t initialCapacityBps = MbpsToBps(config.initialCapacityMbps);
  const uint64_t shiftedCapacityBps = MbpsToBps(config.shiftedCapacityMbps);

  std::vector<double> sourceStartTimes;
  std::vector<double> attackStartTimes;
  sourceStartTimes.reserve(config.senderCount);
  for (uint32_t index = 0; index < config.senderCount; ++index) {
    auto jitter = CreateObject<UniformRandomVariable>();
    jitter->SetStream(1000 + index);
    const bool attackSource = config.trafficMode == "dos" && index > 0;
    const double baseStart = attackSource ? config.attackStartSeconds : 1.0;
    const double actualStart =
        baseStart + jitter->GetValue(0.0, config.jitterMaxMs / 1000.0);
    sourceStartTimes.push_back(actualStart);
    if (attackSource) {
      attackStartTimes.push_back(actualStart);
    }
  }

  NodeContainer senders;
  senders.Create(config.senderCount);
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
  access.SetChannelAttribute("Delay",
                             StringValue(DelayString(config.accessDelayMs)));
  for (uint32_t index = 0; index < config.senderCount; ++index) {
    auto devices = access.Install(senders.Get(index), router.Get(0));
    std::ostringstream network;
    network << "10.1." << (index + 1) << ".0";
    Ipv4AddressHelper address;
    address.SetBase(network.str().c_str(), "255.255.255.0");
    address.Assign(devices);
  }

  PointToPointHelper bottleneck;
  bottleneck.SetDeviceAttribute(
      "DataRate", DataRateValue(DataRate(initialCapacityBps)));
  bottleneck.SetChannelAttribute(
      "Delay", StringValue(DelayString(config.bottleneckDelayMs)));
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
  queueLimit << config.queueLimitPackets << 'p';
  if (config.queueModel == "red") {
    trafficControl.SetRootQueueDisc(
        QueueDiscType(config.queueModel), "MaxSize",
        StringValue(queueLimit.str()), "LinkBandwidth",
        DataRateValue(DataRate(initialCapacityBps)), "LinkDelay",
        TimeValue(MilliSeconds(config.bottleneckDelayMs)));
  } else {
    trafficControl.SetRootQueueDisc(QueueDiscType(config.queueModel),
                                    "MaxSize", StringValue(queueLimit.str()));
  }
  auto queueDiscs = trafficControl.Install(routerDevice);
  auto queueDisc = queueDiscs.Get(0);
  NS_ABORT_MSG_IF(queueDisc == nullptr, "无法安装瓶颈队列规则");
  NS_ABORT_MSG_IF(queueDisc->GetInstanceTypeId().GetName() !=
                      QueueDiscType(config.queueModel),
                  "根队列规则类型与配置不一致");
  NS_ABORT_MSG_IF(queueDisc->GetMaxSize() != QueueSize(queueLimit.str()),
                  "根队列规则上限与配置不一致");

  Ipv4AddressHelper bottleneckAddress;
  bottleneckAddress.SetBase("10.2.0.0", "255.255.255.0");
  auto bottleneckInterfaces = bottleneckAddress.Assign(bottleneckDevices);
  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  if (config.downstreamLossRate > 0.0) {
    auto errorModel = CreateObject<RateErrorModel>();
    errorModel->SetAttribute("ErrorUnit",
                             EnumValue(RateErrorModel::ERROR_UNIT_PACKET));
    errorModel->SetAttribute("ErrorRate",
                             DoubleValue(config.downstreamLossRate));
    errorModel->AssignStreams(5000);
    victimDevice->SetAttribute("ReceiveErrorModel", PointerValue(errorModel));
  }

  QueueWindowCollector collector(config, attackStartTimes, initialCapacityBps);
  NS_ABORT_MSG_IF(!queueDisc->TraceConnectWithoutContext(
                      "Enqueue", MakeCallback(&QueueWindowCollector::OnEnqueue,
                                              &collector)),
                  "无法连接追踪源 Enqueue");
  NS_ABORT_MSG_IF(!queueDisc->TraceConnectWithoutContext(
                      "Dequeue", MakeCallback(&QueueWindowCollector::OnDequeue,
                                              &collector)),
                  "无法连接追踪源 Dequeue");
  NS_ABORT_MSG_IF(!queueDisc->TraceConnectWithoutContext(
                      "DropBeforeEnqueue",
                      MakeCallback(&QueueWindowCollector::OnDropBeforeEnqueue,
                                   &collector)),
                  "无法连接追踪源 DropBeforeEnqueue");
  NS_ABORT_MSG_IF(!queueDisc->TraceConnectWithoutContext(
                      "DropAfterDequeue",
                      MakeCallback(&QueueWindowCollector::OnDropAfterDequeue,
                                   &collector)),
                  "无法连接追踪源 DropAfterDequeue");
  NS_ABORT_MSG_IF(!victimDevice->TraceConnectWithoutContext(
                      "PhyRxDrop",
                      MakeCallback(&QueueWindowCollector::OnDownstreamErrorLoss,
                                   &collector)),
                  "无法连接追踪源 PhyRxDrop");

  const uint16_t port = 9000;
  PacketSinkHelper sink(SocketFactoryName(config.transport),
                        InetSocketAddress(Ipv4Address::GetAny(), port));
  auto sinkApplications = sink.Install(victim.Get(0));
  sinkApplications.Start(Seconds(0.25));
  sinkApplications.Stop(Seconds(config.durationSeconds));
  auto packetSink = DynamicCast<PacketSink>(sinkApplications.Get(0));
  NS_ABORT_MSG_IF(packetSink == nullptr, "无法创建 PacketSink");
  NS_ABORT_MSG_IF(!packetSink->TraceConnectWithoutContext(
                      "Rx", MakeCallback(&QueueWindowCollector::OnSinkRx,
                                         &collector)),
                  "无法连接追踪源 Rx");

  for (uint32_t index = 0; index < config.senderCount; ++index) {
    const bool attackSource = config.trafficMode == "dos" && index > 0;
    InstallSource(senders.Get(index), bottleneckInterfaces.GetAddress(1), port,
                  config,
                  attackSource ? config.attackRateMbps
                               : config.benignRateMbps,
                  sourceStartTimes[index], 10000 + index * 10);
  }

  if (config.capacityShiftSeconds > 0.0 &&
      shiftedCapacityBps != initialCapacityBps) {
    Simulator::Schedule(Seconds(config.capacityShiftSeconds), &ChangeCapacity,
                        routerDevice, queueDisc, config.queueModel, &collector,
                        shiftedCapacityBps);
  }
  collector.Start();
  Simulator::Stop(Seconds(config.durationSeconds + config.windowSeconds));
  Simulator::Run();
  Simulator::Destroy();
  return 0;
}
