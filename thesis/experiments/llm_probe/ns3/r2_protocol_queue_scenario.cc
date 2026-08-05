#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/ipv4-l3-protocol.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/ppp-header.h"
#include "ns3/tcp-congestion-ops.h"
#include "ns3/traffic-control-module.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace ns3;

namespace {

constexpr const char *kSchemaVersion = "flow_probe_r2_ns3_protocol_windows_v1";
constexpr const char *kNs3Version = "3.48";
constexpr const char *kTcpCongestionControl = "ns3::TcpNewReno";
constexpr const char *kCwndTraceName = "CongestionWindow";
constexpr const char *kCwndAggregation = "time_weighted_mean_over_observed_senders";
constexpr uint16_t kPppIpv4Protocol = 0x0021;

struct ScenarioConfig {
  std::string physicsGroupSha256{"unset"};
  std::string matrixConfigSha256{"unset"};
  std::string r2ContractSha256{"unset"};
  std::string split{"train-fit"};
  uint32_t runSeed{1};
  std::string transportFamily{"UDP"};
  double durationSeconds{12.0};
  double windowSeconds{0.1};
  std::string trafficMode{"benign"};
  uint32_t binaryLabel{0};
  std::string arrivalModel{"constant"};
  std::string queueModel{"fifo"};
  double offeredLoadRatio{0.35};
  double initialCapacityMbps{10.0};
  double shiftedCapacityMbps{10.0};
  double capacityChangeSeconds{6.0};
  double accessDelayMs{1.0};
  double bottleneckDelayMs{5.0};
  uint32_t queueLimitPackets{32};
  double downstreamLossRate{0.0};
  uint32_t senderCount{8};
  uint32_t benignSenderCount{8};
  uint32_t attackSenderCount{0};
  double totalOfferedLoadMbps{3.5};
  uint32_t packetSizeBytes{1200};
  double burstOnSeconds{0.2};
  double burstOffSeconds{0.1};
  std::string outputPath{"r2-protocol.csv.partial"};
};

bool IsHexSha256(const std::string &value) {
  if (value.size() != 64) {
    return false;
  }
  return std::all_of(value.begin(), value.end(), [](unsigned char character) {
    return (character >= '0' && character <= '9') ||
           (character >= 'a' && character <= 'f');
  });
}

uint64_t MbpsToBps(double value) {
  return static_cast<uint64_t>(std::llround(value * 1000000.0));
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

std::string SocketFactoryName(const std::string &transportFamily) {
  if (transportFamily == "TCP") {
    return "ns3::TcpSocketFactory";
  }
  if (transportFamily == "UDP") {
    return "ns3::UdpSocketFactory";
  }
  throw std::invalid_argument("未知传输协议：" + transportFamily);
}

uint8_t IpProtocolNumber(const std::string &transportFamily) {
  return transportFamily == "TCP" ? 6 : 17;
}

void ValidateConfig(const ScenarioConfig &config) {
  NS_ABORT_MSG_IF(!IsHexSha256(config.physicsGroupSha256) ||
                      !IsHexSha256(config.matrixConfigSha256) ||
                      !IsHexSha256(config.r2ContractSha256),
                  "配置及合同标识必须是小写 SHA-256");
  NS_ABORT_MSG_IF(config.runSeed == 0, "运行种子必须为非零整数");
  SocketFactoryName(config.transportFamily);
  QueueDiscType(config.queueModel);
  NS_ABORT_MSG_IF(config.durationSeconds != 12.0 ||
                      config.windowSeconds != 0.1,
                  "R2 正式运行必须使用 12 秒时长与 0.1 秒窗口");
  NS_ABORT_MSG_IF(config.trafficMode != "benign" &&
                      config.trafficMode != "dos",
                  "流量模式必须为 benign 或 dos");
  NS_ABORT_MSG_IF((config.trafficMode == "benign" && config.binaryLabel != 0) ||
                      (config.trafficMode == "dos" && config.binaryLabel != 1),
                  "流量模式与二元标签不一致");
  NS_ABORT_MSG_IF(config.arrivalModel != "constant" &&
                      config.arrivalModel != "bursty",
                  "到达过程必须为 constant 或 bursty");
  NS_ABORT_MSG_IF(config.initialCapacityMbps <= 0.0 ||
                      config.shiftedCapacityMbps <= 0.0 ||
                      config.totalOfferedLoadMbps <= 0.0,
                  "容量与提供负载必须为正数");
  NS_ABORT_MSG_IF(config.capacityChangeSeconds <= 0.0 ||
                      config.capacityChangeSeconds >= config.durationSeconds,
                  "容量变化时刻不合法");
  NS_ABORT_MSG_IF(config.accessDelayMs <= 0.0 ||
                      config.bottleneckDelayMs <= 0.0,
                  "链路时延必须为正数");
  NS_ABORT_MSG_IF(config.queueLimitPackets == 0 || config.senderCount == 0,
                  "队列上限与发送者总数必须为正整数");
  NS_ABORT_MSG_IF(config.benignSenderCount + config.attackSenderCount !=
                      config.senderCount,
                  "发送者组成与总数不一致");
  NS_ABORT_MSG_IF(config.trafficMode == "benign" &&
                      config.attackSenderCount != 0,
                  "良性配置不得包含攻击发送者");
  NS_ABORT_MSG_IF(config.trafficMode == "dos" &&
                      (config.attackSenderCount == 0 ||
                       config.benignSenderCount == 0),
                  "DoS 配置必须同时包含良性与攻击发送者");
  NS_ABORT_MSG_IF(config.downstreamLossRate < 0.0 ||
                      config.downstreamLossRate >= 1.0,
                  "下游独立丢包率必须位于 [0,1)");
  NS_ABORT_MSG_IF(config.packetSizeBytes < 64 ||
                      config.packetSizeBytes > 1400,
                  "应用载荷包长必须位于 64 至 1400 字节");
  NS_ABORT_MSG_IF(config.burstOnSeconds <= 0.0 ||
                      config.burstOffSeconds <= 0.0,
                  "突发开关周期必须为正数");
}

class WindowCollector {
public:
  explicit WindowCollector(const ScenarioConfig &config,
                           uint64_t initialCapacityBps)
      : m_config(config), m_capacityBps(initialCapacityBps),
        m_windowStartCapacityBps(initialCapacityBps),
        m_cwndStates(config.senderCount), m_output(config.outputPath) {
    if (!m_output.is_open()) {
      throw std::runtime_error("无法创建输出文件：" + config.outputPath);
    }
    m_output
        << "schema_version,physics_group_sha256,matrix_config_sha256,"
           "r2_contract_sha256,split,run_seed,transport_family,window_index,"
           "window_start_s,window_end_s,public_total_packets,"
           "public_total_l3_bytes,public_packet_length_mean_l3_bytes,"
           "public_packet_length_min_l3_bytes,"
           "public_packet_length_max_l3_bytes,public_iat_mean_ms,"
           "public_packet_rate_pps,public_byte_rate_Bps,truth_traffic_mode,"
           "truth_binary_label,truth_arrival_model,truth_queue_model,"
           "truth_ns3_version,truth_tcp_congestion_control,"
           "truth_offered_load_ratio,truth_initial_capacity_bps,"
           "truth_shifted_capacity_bps,truth_capacity_change_s,"
           "truth_access_delay_ms,truth_bottleneck_delay_ms,"
           "truth_queue_limit_packets,truth_downstream_loss_rate,"
           "truth_sender_count,truth_benign_sender_count,"
           "truth_attack_sender_count,truth_total_offered_load_bps,"
           "truth_packet_size_app_payload_bytes,truth_capacity_start_bps,"
           "truth_capacity_end_bps,truth_capacity_integral_link_bytes,"
           "truth_queue_start_l3_bytes,truth_queue_end_l3_bytes,"
           "truth_qdisc_received_l3_bytes,truth_qdisc_enqueued_l3_bytes,"
           "truth_qdisc_dequeued_l3_bytes,"
           "truth_qdisc_drop_before_enqueue_l3_bytes,"
           "truth_qdisc_drop_after_dequeue_l3_bytes,"
           "truth_downstream_error_loss_l3_bytes,"
           "truth_receiver_local_deliver_l3_bytes,"
           "truth_device_tx_drop_l3_bytes,truth_queue_start_packets,"
           "truth_queue_end_packets,truth_qdisc_received_packets,"
           "truth_qdisc_enqueued_packets,truth_qdisc_dequeued_packets,"
           "truth_qdisc_drop_before_enqueue_packets,"
           "truth_qdisc_drop_after_dequeue_packets,"
           "truth_downstream_error_loss_packets,"
           "truth_receiver_local_deliver_packets,"
           "truth_device_tx_drop_packets,"
           "truth_queue_balance_residual_l3_bytes,"
           "truth_queue_balance_residual_packets,"
           "truth_tcp_cwnd_applicable,truth_tcp_cwnd_observed,"
           "truth_tcp_cwnd_trace_connected_senders,"
           "truth_tcp_cwnd_observed_senders,truth_tcp_cwnd_mean_bytes,"
           "truth_tcp_cwnd_min_bytes,truth_tcp_cwnd_max_bytes,"
           "truth_tcp_cwnd_trace_name,truth_tcp_cwnd_aggregation,"
           "truth_udp_applicable,truth_udp_planned_app_payload_packets,"
           "truth_udp_planned_app_payload_bytes,"
           "truth_udp_actual_send_events,truth_udp_actual_send_bytes,"
           "truth_udp_target_rate_bps,truth_udp_burst_mode,"
           "truth_udp_burst_active\n";
  }

  void Start() {
    Simulator::Schedule(Seconds(m_config.windowSeconds),
                        &WindowCollector::Flush, this);
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
    NS_ABORT_MSG_IF(packet == nullptr, "PhyRxDrop 收到空包");
    PppHeader pppHeader;
    const uint32_t declaredPppHeaderBytes = pppHeader.GetSerializedSize();
    NS_ABORT_MSG_IF(packet->GetSize() < declaredPppHeaderBytes,
                    "PhyRxDrop 包长不足以容纳 PPP 头");
    const uint32_t parsedPppHeaderBytes = packet->PeekHeader(pppHeader);
    NS_ABORT_MSG_IF(parsedPppHeaderBytes != declaredPppHeaderBytes,
                    "PhyRxDrop PPP 头解析长度与声明长度不符");
    NS_ABORT_MSG_IF(pppHeader.GetProtocol() != kPppIpv4Protocol,
                    "PhyRxDrop PPP 头不是 IPv4 协议");
    m_downstreamErrorLossBytes += packet->GetSize() - parsedPppHeaderBytes;
    m_downstreamErrorLossPackets += 1;
  }

  void OnDeviceTxDrop(Ptr<const Packet> packet) {
    m_deviceTxDropBytes += packet->GetSize();
    m_deviceTxDropPackets += 1;
  }

  void OnLocalDeliver(const Ipv4Header &header, Ptr<const Packet> packet,
                      uint32_t) {
    if (header.GetProtocol() != IpProtocolNumber(m_config.transportFamily)) {
      return;
    }
    m_receiverLocalDeliverBytes +=
        packet->GetSize() + header.GetSerializedSize();
    m_receiverLocalDeliverPackets += 1;
  }

  void RegisterCwndTrace(uint32_t senderIndex) {
    NS_ABORT_MSG_IF(senderIndex >= m_cwndStates.size(),
                    "TCP 发送者索引越界");
    auto &state = m_cwndStates[senderIndex];
    NS_ABORT_MSG_IF(state.traceConnected, "同一 TCP socket 重复连接 cwnd trace");
    state.traceConnected = true;
    state.lastUpdateSeconds = Simulator::Now().GetSeconds();
  }

  void OnCongestionWindow(uint32_t senderIndex, uint32_t, uint32_t newValue) {
    NS_ABORT_MSG_IF(m_config.transportFamily != "TCP",
                    "UDP 不得写入 TCP cwnd 状态");
    NS_ABORT_MSG_IF(senderIndex >= m_cwndStates.size(),
                    "TCP 发送者索引越界");
    auto &state = m_cwndStates[senderIndex];
    NS_ABORT_MSG_IF(!state.traceConnected, "cwnd 回调未绑定已登记 trace");
    IntegrateCwnd(state, Simulator::Now().GetSeconds());
    state.currentBytes = newValue;
    state.observed = true;
    state.minimumBytes = std::min(state.minimumBytes, newValue);
    state.maximumBytes = std::max(state.maximumBytes, newValue);
  }

  void OnApplicationPlanned(bool udpApplicable, uint32_t payloadBytes) {
    if (!udpApplicable) {
      return;
    }
    m_udpPlannedPackets += 1;
    m_udpPlannedBytes += payloadBytes;
  }

  void OnApplicationSent(bool udpApplicable, uint32_t sentBytes) {
    if (!udpApplicable || sentBytes == 0) {
      return;
    }
    m_udpActualSendEvents += 1;
    m_udpActualSendBytes += sentBytes;
  }

private:
  struct CwndState {
    bool traceConnected{false};
    bool observed{false};
    uint32_t currentBytes{0};
    uint32_t minimumBytes{std::numeric_limits<uint32_t>::max()};
    uint32_t maximumBytes{0};
    double integralByteSeconds{0.0};
    double observedSeconds{0.0};
    double lastUpdateSeconds{0.0};
  };

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

  static void IntegrateCwnd(CwndState &state, double nowSeconds) {
    NS_ABORT_MSG_IF(nowSeconds < state.lastUpdateSeconds,
                    "cwnd 时间追踪发生回退");
    const double duration = nowSeconds - state.lastUpdateSeconds;
    if (state.observed) {
      state.integralByteSeconds += state.currentBytes * duration;
      state.observedSeconds += duration;
    }
    state.lastUpdateSeconds = nowSeconds;
  }

  void Flush() {
    const double windowEnd = Simulator::Now().GetSeconds();
    const double windowStart = windowEnd - m_config.windowSeconds;
    m_capacityBitSeconds +=
        m_capacityBps * (windowEnd - m_lastCapacityUpdateSeconds);
    const double capacityIntegralBytes = m_capacityBitSeconds / 8.0;
    const uint64_t receivedBytes = m_enqueuedBytes + m_droppedBeforeBytes;
    const uint64_t receivedPackets =
        m_enqueuedPackets + m_droppedBeforePackets;
    const int64_t residualBytes =
        static_cast<int64_t>(m_currentQueueBytes) -
        static_cast<int64_t>(m_windowStartQueueBytes) -
        static_cast<int64_t>(m_enqueuedBytes) +
        static_cast<int64_t>(m_dequeuedBytes);
    const int64_t residualPackets =
        static_cast<int64_t>(m_currentQueuePackets) -
        static_cast<int64_t>(m_windowStartQueuePackets) -
        static_cast<int64_t>(m_enqueuedPackets) +
        static_cast<int64_t>(m_dequeuedPackets);

    const double packetLengthMean =
        receivedPackets > 0
            ? static_cast<double>(receivedBytes) / receivedPackets
            : 0.0;
    const uint64_t packetLengthMin =
        receivedPackets > 0 ? m_arrivalMinBytes : 0;
    const uint64_t packetLengthMax =
        receivedPackets > 0 ? m_arrivalMaxBytes : 0;
    const double iatMeanMs =
        m_arrivalIatCount > 0
            ? 1000.0 * m_arrivalIatSumSeconds / m_arrivalIatCount
            : 0.0;

    uint32_t traceConnectedSenders = 0;
    uint32_t observedSenders = 0;
    uint32_t cwndMinimum = std::numeric_limits<uint32_t>::max();
    uint32_t cwndMaximum = 0;
    double cwndIntegral = 0.0;
    double cwndObservedSeconds = 0.0;
    for (auto &state : m_cwndStates) {
      traceConnectedSenders += state.traceConnected ? 1 : 0;
      if (state.traceConnected) {
        IntegrateCwnd(state, windowEnd);
      }
      if (state.observed) {
        observedSenders += 1;
        cwndIntegral += state.integralByteSeconds;
        cwndObservedSeconds += state.observedSeconds;
        cwndMinimum = std::min(cwndMinimum, state.minimumBytes);
        cwndMaximum = std::max(cwndMaximum, state.maximumBytes);
      }
    }
    const bool tcpApplicable = m_config.transportFamily == "TCP";
    const bool cwndObserved = tcpApplicable && observedSenders > 0;
    const double cwndMean =
        cwndObservedSeconds > 0.0 ? cwndIntegral / cwndObservedSeconds : 0.0;
    if (!cwndObserved) {
      cwndMinimum = 0;
      cwndMaximum = 0;
    }
    const bool udpApplicable = m_config.transportFamily == "UDP";
    const bool udpBurstActive = udpApplicable && m_udpPlannedPackets > 0;

    m_output << kSchemaVersion << ',' << m_config.physicsGroupSha256 << ','
             << m_config.matrixConfigSha256 << ','
             << m_config.r2ContractSha256 << ',' << m_config.split << ','
             << m_config.runSeed << ',' << m_config.transportFamily << ','
             << m_windowIndex << ',' << std::fixed << std::setprecision(9)
             << windowStart << ',' << windowEnd << ',' << receivedPackets << ','
             << receivedBytes << ',' << packetLengthMean << ','
             << packetLengthMin << ',' << packetLengthMax << ',' << iatMeanMs
             << ',' << receivedPackets / m_config.windowSeconds << ','
             << receivedBytes / m_config.windowSeconds << ','
             << m_config.trafficMode << ',' << m_config.binaryLabel << ','
             << m_config.arrivalModel << ',' << m_config.queueModel << ','
             << kNs3Version << ',' << kTcpCongestionControl << ','
             << m_config.offeredLoadRatio << ','
             << MbpsToBps(m_config.initialCapacityMbps) << ','
             << MbpsToBps(m_config.shiftedCapacityMbps) << ','
             << m_config.capacityChangeSeconds << ',' << m_config.accessDelayMs
             << ',' << m_config.bottleneckDelayMs << ','
             << m_config.queueLimitPackets << ','
             << m_config.downstreamLossRate << ',' << m_config.senderCount << ','
             << m_config.benignSenderCount << ','
             << m_config.attackSenderCount << ','
             << MbpsToBps(m_config.totalOfferedLoadMbps) << ','
             << m_config.packetSizeBytes << ',' << m_windowStartCapacityBps
             << ',' << m_capacityBps << ',' << capacityIntegralBytes << ','
             << m_windowStartQueueBytes << ',' << m_currentQueueBytes << ','
             << receivedBytes << ',' << m_enqueuedBytes << ','
             << m_dequeuedBytes << ',' << m_droppedBeforeBytes << ','
             << m_droppedAfterBytes << ',' << m_downstreamErrorLossBytes << ','
             << m_receiverLocalDeliverBytes << ',' << m_deviceTxDropBytes << ','
             << m_windowStartQueuePackets << ',' << m_currentQueuePackets << ','
             << receivedPackets << ',' << m_enqueuedPackets << ','
             << m_dequeuedPackets << ',' << m_droppedBeforePackets << ','
             << m_droppedAfterPackets << ',' << m_downstreamErrorLossPackets
             << ',' << m_receiverLocalDeliverPackets << ','
             << m_deviceTxDropPackets << ',' << residualBytes << ','
             << residualPackets << ',' << (tcpApplicable ? 1 : 0) << ','
             << (cwndObserved ? 1 : 0) << ',' << traceConnectedSenders << ','
             << observedSenders << ',' << cwndMean << ',' << cwndMinimum << ','
             << cwndMaximum << ','
             << (tcpApplicable ? kCwndTraceName : "NONE") << ','
             << (tcpApplicable ? kCwndAggregation : "not_applicable") << ','
             << (udpApplicable ? 1 : 0) << ',' << m_udpPlannedPackets << ','
             << m_udpPlannedBytes << ',' << m_udpActualSendEvents << ','
             << m_udpActualSendBytes << ','
             << (udpApplicable ? MbpsToBps(m_config.totalOfferedLoadMbps) : 0)
             << ','
             << (udpApplicable && m_config.arrivalModel == "bursty" ? 1 : 0)
             << ','
             << (udpBurstActive ? 1 : 0) << '\n';
    m_output.flush();

    m_windowStartCapacityBps = m_capacityBps;
    m_windowStartQueueBytes = m_currentQueueBytes;
    m_windowStartQueuePackets = m_currentQueuePackets;
    m_enqueuedBytes = 0;
    m_dequeuedBytes = 0;
    m_droppedBeforeBytes = 0;
    m_droppedAfterBytes = 0;
    m_downstreamErrorLossBytes = 0;
    m_receiverLocalDeliverBytes = 0;
    m_deviceTxDropBytes = 0;
    m_enqueuedPackets = 0;
    m_dequeuedPackets = 0;
    m_droppedBeforePackets = 0;
    m_droppedAfterPackets = 0;
    m_downstreamErrorLossPackets = 0;
    m_receiverLocalDeliverPackets = 0;
    m_deviceTxDropPackets = 0;
    m_udpPlannedPackets = 0;
    m_udpPlannedBytes = 0;
    m_udpActualSendEvents = 0;
    m_udpActualSendBytes = 0;
    m_arrivalMinBytes = std::numeric_limits<uint64_t>::max();
    m_arrivalMaxBytes = 0;
    m_arrivalIatSumSeconds = 0.0;
    m_arrivalIatCount = 0;
    m_hasPreviousArrival = false;
    m_capacityBitSeconds = 0.0;
    m_lastCapacityUpdateSeconds = windowEnd;
    for (auto &state : m_cwndStates) {
      state.integralByteSeconds = 0.0;
      state.observedSeconds = 0.0;
      if (state.observed) {
        state.minimumBytes = state.currentBytes;
        state.maximumBytes = state.currentBytes;
      }
    }
    m_windowIndex += 1;

    if (windowEnd + m_config.windowSeconds <=
        m_config.durationSeconds + 1e-9) {
      Simulator::Schedule(Seconds(m_config.windowSeconds),
                          &WindowCollector::Flush, this);
    }
  }

  ScenarioConfig m_config;
  uint64_t m_capacityBps;
  uint64_t m_windowStartCapacityBps;
  std::vector<CwndState> m_cwndStates;
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
  uint64_t m_receiverLocalDeliverBytes{0};
  uint64_t m_deviceTxDropBytes{0};
  uint64_t m_enqueuedPackets{0};
  uint64_t m_dequeuedPackets{0};
  uint64_t m_droppedBeforePackets{0};
  uint64_t m_droppedAfterPackets{0};
  uint64_t m_downstreamErrorLossPackets{0};
  uint64_t m_receiverLocalDeliverPackets{0};
  uint64_t m_deviceTxDropPackets{0};
  uint64_t m_udpPlannedPackets{0};
  uint64_t m_udpPlannedBytes{0};
  uint64_t m_udpActualSendEvents{0};
  uint64_t m_udpActualSendBytes{0};
  uint64_t m_arrivalMinBytes{std::numeric_limits<uint64_t>::max()};
  uint64_t m_arrivalMaxBytes{0};
  double m_arrivalIatSumSeconds{0.0};
  uint64_t m_arrivalIatCount{0};
  bool m_hasPreviousArrival{false};
  double m_previousArrivalSeconds{0.0};
  double m_capacityBitSeconds{0.0};
  double m_lastCapacityUpdateSeconds{0.0};
};

class ProtocolTrafficApplication : public Application {
public:
  void Configure(Address peer, const ScenarioConfig &config,
                 WindowCollector *collector, uint32_t senderIndex,
                 double targetRateMbps, double phaseOffsetSeconds) {
    m_peer = peer;
    m_config = config;
    m_collector = collector;
    m_senderIndex = senderIndex;
    m_targetRateMbps = targetRateMbps;
    m_phaseOffsetSeconds = phaseOffsetSeconds;
  }

private:
  void StartApplication() override {
    m_running = true;
    m_socket = Socket::CreateSocket(
        GetNode(), TypeId::LookupByName(SocketFactoryName(m_config.transportFamily)));
    NS_ABORT_MSG_IF(m_socket == nullptr, "无法创建传输层 socket");
    NS_ABORT_MSG_IF(m_socket->Bind() != 0, "发送 socket 绑定失败");
    if (m_config.transportFamily == "TCP") {
      const bool connected = m_socket->TraceConnectWithoutContext(
          kCwndTraceName,
          MakeCallback(&ProtocolTrafficApplication::OnCongestionWindow, this));
      NS_ABORT_MSG_IF(!connected, "无法连接 TCP CongestionWindow trace");
      m_collector->RegisterCwndTrace(m_senderIndex);
      m_socket->SetConnectCallback(
          MakeCallback(&ProtocolTrafficApplication::ConnectionSucceeded, this),
          MakeCallback(&ProtocolTrafficApplication::ConnectionFailed, this));
      const int result = m_socket->Connect(m_peer);
      NS_ABORT_MSG_IF(result != 0, "TCP Connect 调用失败");
    } else {
      NS_ABORT_MSG_IF(m_socket->Connect(m_peer) != 0, "UDP Connect 调用失败");
      m_connected = true;
      ScheduleNext(Seconds(0));
    }
  }

  void StopApplication() override {
    m_running = false;
    if (m_sendEvent.IsPending()) {
      Simulator::Cancel(m_sendEvent);
    }
    if (m_socket != nullptr) {
      m_socket->Close();
      m_socket = nullptr;
    }
  }

  void ConnectionSucceeded(Ptr<Socket>) {
    m_connected = true;
    ScheduleNext(Seconds(0));
  }

  void ConnectionFailed(Ptr<Socket>) {
    NS_ABORT_MSG("TCP 连接失败");
  }

  void OnCongestionWindow(uint32_t oldValue, uint32_t newValue) {
    m_collector->OnCongestionWindow(m_senderIndex, oldValue, newValue);
  }

  int64_t BurstPhaseTimeSteps(Time now) const {
    const int64_t cycleTimeSteps =
        Seconds(m_config.burstOnSeconds).GetTimeStep() +
        Seconds(m_config.burstOffSeconds).GetTimeStep();
    NS_ABORT_MSG_IF(cycleTimeSteps <= 0,
                    "突发周期量化后必须包含正的时间步");
    const int64_t phaseOffsetTimeSteps =
        Seconds(m_phaseOffsetSeconds).GetTimeStep();
    return (now.GetTimeStep() + phaseOffsetTimeSteps) % cycleTimeSteps;
  }

  bool BurstActive(Time now) const {
    if (m_config.arrivalModel == "constant") {
      return true;
    }
    const int64_t burstOnTimeSteps =
        Seconds(m_config.burstOnSeconds).GetTimeStep();
    return BurstPhaseTimeSteps(now) < burstOnTimeSteps;
  }

  Time DelayUntilBurstActive(Time now) const {
    const int64_t burstOnTimeSteps =
        Seconds(m_config.burstOnSeconds).GetTimeStep();
    const int64_t cycleTimeSteps =
        burstOnTimeSteps + Seconds(m_config.burstOffSeconds).GetTimeStep();
    const int64_t phaseTimeSteps = BurstPhaseTimeSteps(now);
    NS_ABORT_MSG_IF(phaseTimeSteps < burstOnTimeSteps,
                    "活动突发阶段不得请求下一开启延迟");
    const int64_t delayTimeSteps = cycleTimeSteps - phaseTimeSteps;
    NS_ABORT_MSG_IF(delayTimeSteps <= 0,
                    "非活动突发阶段的下一事件延迟必须严格为正时间步");
    return TimeStep(static_cast<uint64_t>(delayTimeSteps));
  }

  Time PacketInterval() const {
    double instantaneousRateBps = m_targetRateMbps * 1000000.0;
    if (m_config.arrivalModel == "bursty") {
      const double duty = m_config.burstOnSeconds /
                          (m_config.burstOnSeconds +
                           m_config.burstOffSeconds);
      instantaneousRateBps /= duty;
    }
    return Seconds(m_config.packetSizeBytes * 8.0 / instantaneousRateBps);
  }

  void ScheduleNext(Time delay) {
    if (m_running && m_connected) {
      m_sendEvent = Simulator::Schedule(
          delay, &ProtocolTrafficApplication::AttemptSend, this);
    }
  }

  void AttemptSend() {
    if (!m_running || !m_connected || m_socket == nullptr) {
      return;
    }
    const Time now = Simulator::Now();
    if (!BurstActive(now)) {
      ScheduleNext(DelayUntilBurstActive(now));
      return;
    }
    const bool udpApplicable = m_config.transportFamily == "UDP";
    m_collector->OnApplicationPlanned(udpApplicable,
                                      m_config.packetSizeBytes);
    const int sent = m_socket->Send(Create<Packet>(m_config.packetSizeBytes));
    if (sent > 0) {
      m_collector->OnApplicationSent(udpApplicable,
                                     static_cast<uint32_t>(sent));
    }
    ScheduleNext(PacketInterval());
  }

  Ptr<Socket> m_socket;
  Address m_peer;
  ScenarioConfig m_config;
  WindowCollector *m_collector{nullptr};
  uint32_t m_senderIndex{0};
  double m_targetRateMbps{0.0};
  double m_phaseOffsetSeconds{0.0};
  bool m_running{false};
  bool m_connected{false};
  EventId m_sendEvent;
};

void ChangeCapacity(Ptr<PointToPointNetDevice> device,
                    Ptr<QueueDisc> queueDisc, const std::string &queueModel,
                    WindowCollector *collector, uint64_t capacityBps) {
  device->SetDataRate(DataRate(capacityBps));
  if (queueModel == "red") {
    queueDisc->SetAttribute("LinkBandwidth",
                            DataRateValue(DataRate(capacityBps)));
  }
  collector->SetCapacity(capacityBps);
}

std::vector<double> SenderRates(const ScenarioConfig &config) {
  const double average = config.totalOfferedLoadMbps / config.senderCount;
  std::vector<double> rates(config.senderCount, average);
  if (config.attackSenderCount == 0) {
    return rates;
  }
  const double attackRate = average * 1.5;
  const double benignTotal = config.totalOfferedLoadMbps -
                             attackRate * config.attackSenderCount;
  NS_ABORT_MSG_IF(benignTotal <= 0.0 || config.benignSenderCount == 0,
                  "发送者组成无法保持固定总提供负载");
  const double benignRate = benignTotal / config.benignSenderCount;
  for (uint32_t index = 0; index < config.senderCount; ++index) {
    rates[index] = index < config.benignSenderCount ? benignRate : attackRate;
  }
  return rates;
}

} // namespace

int main(int argc, char *argv[]) {
  ScenarioConfig config;
  CommandLine command(__FILE__);
  command.AddValue("physicsGroupSha256", "不可逆物理配对组标识",
                   config.physicsGroupSha256);
  command.AddValue("matrixConfigSha256", "任务04冻结配置哈希",
                   config.matrixConfigSha256);
  command.AddValue("r2ContractSha256", "任务01共享合同配置哈希",
                   config.r2ContractSha256);
  command.AddValue("split", "冻结划分", config.split);
  command.AddValue("runSeed", "配对共享的非零31位运行种子",
                   config.runSeed);
  command.AddValue("transportFamily", "TCP 或普通 UDP",
                   config.transportFamily);
  command.AddValue("duration", "仿真时长，单位秒",
                   config.durationSeconds);
  command.AddValue("window", "聚合窗口，单位秒", config.windowSeconds);
  command.AddValue("trafficMode", "benign 或 dos", config.trafficMode);
  command.AddValue("binaryLabel", "二元审计标签", config.binaryLabel);
  command.AddValue("arrivalModel", "constant 或 bursty",
                   config.arrivalModel);
  command.AddValue("queueModel", "fifo、codel 或 red",
                   config.queueModel);
  command.AddValue("offeredLoadRatio", "相对初始容量的负载带",
                   config.offeredLoadRatio);
  command.AddValue("initialCapacityMbps", "初始瓶颈容量",
                   config.initialCapacityMbps);
  command.AddValue("shiftedCapacityMbps", "变化后瓶颈容量",
                   config.shiftedCapacityMbps);
  command.AddValue("capacityChangeSeconds", "容量变化时刻",
                   config.capacityChangeSeconds);
  command.AddValue("accessDelayMs", "接入链路单向时延",
                   config.accessDelayMs);
  command.AddValue("bottleneckDelayMs", "瓶颈链路单向时延",
                   config.bottleneckDelayMs);
  command.AddValue("queueLimitPackets", "队列上限",
                   config.queueLimitPackets);
  command.AddValue("downstreamLossRate", "下游独立丢包率",
                   config.downstreamLossRate);
  command.AddValue("senderCount", "发送者总数", config.senderCount);
  command.AddValue("benignSenderCount", "良性发送者数",
                   config.benignSenderCount);
  command.AddValue("attackSenderCount", "攻击发送者数",
                   config.attackSenderCount);
  command.AddValue("totalOfferedLoadMbps", "配对共享的总提供负载",
                   config.totalOfferedLoadMbps);
  command.AddValue("packetSizeBytes", "应用载荷包长",
                   config.packetSizeBytes);
  command.AddValue("burstOnSeconds", "突发开启时长",
                   config.burstOnSeconds);
  command.AddValue("burstOffSeconds", "突发关闭时长",
                   config.burstOffSeconds);
  command.AddValue("output", "CSV .partial 输出路径", config.outputPath);
  command.Parse(argc, argv);
  ValidateConfig(config);

  RngSeedManager::SetSeed(config.runSeed);
  RngSeedManager::SetRun(1);
  Config::SetDefault("ns3::TcpL4Protocol::SocketType",
                     TypeIdValue(TcpNewReno::GetTypeId()));
  const uint64_t initialCapacityBps = MbpsToBps(config.initialCapacityMbps);
  const uint64_t shiftedCapacityBps = MbpsToBps(config.shiftedCapacityMbps);

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
  access.SetDeviceAttribute("DataRate", StringValue("1Gbps"));
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
  bottleneck.SetQueue("ns3::DropTailQueue", "MaxSize",
                      StringValue("10000p"));
  auto bottleneckDevices = bottleneck.Install(router.Get(0), victim.Get(0));
  auto routerDevice =
      DynamicCast<PointToPointNetDevice>(bottleneckDevices.Get(0));
  auto victimDevice =
      DynamicCast<PointToPointNetDevice>(bottleneckDevices.Get(1));
  NS_ABORT_MSG_IF(routerDevice == nullptr || victimDevice == nullptr,
                  "瓶颈设备类型不正确");

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
                  "队列规则类型与配置不一致");
  NS_ABORT_MSG_IF(queueDisc->GetMaxSize() != QueueSize(queueLimit.str()),
                  "队列上限与配置不一致");

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

  WindowCollector collector(config, initialCapacityBps);
  NS_ABORT_MSG_IF(!queueDisc->TraceConnectWithoutContext(
                      "Enqueue", MakeCallback(&WindowCollector::OnEnqueue,
                                              &collector)),
                  "无法连接 QueueDisc Enqueue trace");
  NS_ABORT_MSG_IF(!queueDisc->TraceConnectWithoutContext(
                      "Dequeue", MakeCallback(&WindowCollector::OnDequeue,
                                              &collector)),
                  "无法连接 QueueDisc Dequeue trace");
  NS_ABORT_MSG_IF(!queueDisc->TraceConnectWithoutContext(
                      "DropBeforeEnqueue",
                      MakeCallback(&WindowCollector::OnDropBeforeEnqueue,
                                   &collector)),
                  "无法连接 QueueDisc DropBeforeEnqueue trace");
  NS_ABORT_MSG_IF(!queueDisc->TraceConnectWithoutContext(
                      "DropAfterDequeue",
                      MakeCallback(&WindowCollector::OnDropAfterDequeue,
                                   &collector)),
                  "无法连接 QueueDisc DropAfterDequeue trace");
  NS_ABORT_MSG_IF(!victimDevice->TraceConnectWithoutContext(
                      "PhyRxDrop",
                      MakeCallback(&WindowCollector::OnDownstreamErrorLoss,
                                   &collector)),
                  "无法连接 PointToPointNetDevice PhyRxDrop trace");
  NS_ABORT_MSG_IF(!routerDevice->TraceConnectWithoutContext(
                      "MacTxDrop",
                      MakeCallback(&WindowCollector::OnDeviceTxDrop,
                                   &collector)),
                  "无法连接 PointToPointNetDevice MacTxDrop trace");
  auto victimIpv4 = victim.Get(0)->GetObject<Ipv4L3Protocol>();
  NS_ABORT_MSG_IF(victimIpv4 == nullptr, "无法取得接收端 Ipv4L3Protocol");
  NS_ABORT_MSG_IF(!victimIpv4->TraceConnectWithoutContext(
                      "LocalDeliver",
                      MakeCallback(&WindowCollector::OnLocalDeliver,
                                   &collector)),
                  "无法连接 Ipv4L3Protocol LocalDeliver trace");

  constexpr uint16_t port = 9000;
  PacketSinkHelper sink(SocketFactoryName(config.transportFamily),
                        InetSocketAddress(Ipv4Address::GetAny(), port));
  auto sinkApplications = sink.Install(victim.Get(0));
  sinkApplications.Start(Seconds(0.0));
  sinkApplications.Stop(Seconds(config.durationSeconds));

  const auto senderRates = SenderRates(config);
  const double burstCycle = config.burstOnSeconds + config.burstOffSeconds;
  for (uint32_t index = 0; index < config.senderCount; ++index) {
    const bool attackSender = index >= config.benignSenderCount;
    const double phaseOffset =
        attackSender ? 0.0
                     : burstCycle * static_cast<double>(index) /
                           config.senderCount;
    auto application = CreateObject<ProtocolTrafficApplication>();
    application->Configure(
        InetSocketAddress(bottleneckInterfaces.GetAddress(1), port), config,
        &collector, index, senderRates[index], phaseOffset);
    senders.Get(index)->AddApplication(application);
    application->SetStartTime(Seconds(0.01));
    application->SetStopTime(Seconds(config.durationSeconds));
  }

  if (shiftedCapacityBps != initialCapacityBps) {
    Simulator::Schedule(Seconds(config.capacityChangeSeconds), &ChangeCapacity,
                        routerDevice, queueDisc, config.queueModel, &collector,
                        shiftedCapacityBps);
  }
  collector.Start();
  Simulator::Stop(Seconds(config.durationSeconds + config.windowSeconds));
  Simulator::Run();
  Simulator::Destroy();
  return 0;
}
