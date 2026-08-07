#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/ipv4-l3-protocol.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/ppp-header.h"
#include "ns3/tcp-congestion-ops.h"
#include "ns3/tcp-socket-base.h"
#include "ns3/traffic-control-module.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <deque>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using namespace ns3;

namespace {

constexpr const char *kMainSchema = "flow_probe_r2_ns3_protocol_windows_v3";
// 诊断量写入独立旁车 CSV，主表保持与 v3 完全一致的 46 列，
// 以便 _validate_main 精确表头校验通过，并可与 v3 同参数运行逐值比对。
constexpr const char *kDiagSchema = "flow_probe_r2_ns3_diag_window_observables_v1";
constexpr const char *kTcpSchema = "flow_probe_r2_ns3_tcp_sender_windows_v2";
constexpr const char *kNs3Version = "3.48";
constexpr const char *kTcpCongestionControl = "ns3::TcpNewReno";
constexpr uint16_t kPppIpv4Protocol = 0x0021;

struct ScenarioConfig {
  std::string physicsGroupSha256{"unset"};
  std::string matrixConfigSha256{"unset"};
  std::string tcpTruthContractSha256{"unset"};
  std::string split{"train-fit"};
  uint32_t runSeed{1};
  std::string transportFamily{"TCP"};
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
  std::string outputPath{"r2-dynamics-v2-main.csv.partial"};
  std::string tcpOutputPath{"r2-dynamics-v2-tcp.csv.partial"};
  uint32_t queueTraceIntervalMs{0};
  std::string queueTracePath{};
};

bool IsHexSha256(const std::string &value) {
  return value.size() == 64 &&
         std::all_of(value.begin(), value.end(), [](unsigned char character) {
           return (character >= '0' && character <= '9') ||
                  (character >= 'a' && character <= 'f');
         });
}

// 旁车路径由主表路径推导，保证与 main.csv 落在同一运行目录，
// 无需正式运行器额外传参。
std::string DeriveDiagOutputPath(const std::string &mainOutputPath) {
  const std::string::size_type slash = mainOutputPath.find_last_of('/');
  if (slash == std::string::npos) {
    return "diag-window-observables.csv";
  }
  return mainOutputPath.substr(0, slash + 1) + "diag-window-observables.csv";
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
                      !IsHexSha256(config.tcpTruthContractSha256),
                  "配置及合同标识必须是小写 SHA-256");
  NS_ABORT_MSG_IF(config.runSeed == 0, "运行种子必须为非零整数");
  SocketFactoryName(config.transportFamily);
  QueueDiscType(config.queueModel);
  NS_ABORT_MSG_IF(config.durationSeconds != 12.0 ||
                      config.windowSeconds != 0.1,
                  "字段闭合必须使用12秒时长与0.1秒窗口");
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
                  "应用载荷包长必须位于64至1400字节");
}

class WindowCollector {
public:
  explicit WindowCollector(const ScenarioConfig &config)
      : m_config(config), m_states(config.senderCount),
        m_udpRegistered(config.senderCount, false),
        m_udpPhaseOffsetTimeSteps(config.senderCount, 0),
        m_mainOutput(config.outputPath), m_tcpOutput(config.tcpOutputPath),
        m_diagOutput(DeriveDiagOutputPath(config.outputPath)) {
    if (!m_mainOutput.is_open() || !m_tcpOutput.is_open() ||
        !m_diagOutput.is_open()) {
      throw std::runtime_error("无法创建 v2 输出文件");
    }
    m_mainOutput
        << "schema_version,physics_group_sha256,matrix_config_sha256,"
           "tcp_truth_contract_sha256,split,run_seed,transport_family,"
           "window_index,window_start_s,window_end_s,window_duration_s,"
           "public_total_packets,"
           "public_total_l3_bytes,orig_bytes,resp_bytes,orig_pkts,resp_pkts,"
           "orig_ip_bytes,resp_ip_bytes,truth_queue_start_l3_bytes,"
           "truth_queue_end_l3_bytes,truth_qdisc_received_l3_bytes,"
           "truth_qdisc_enqueued_l3_bytes,truth_qdisc_dequeued_l3_bytes,"
           "truth_qdisc_drop_before_enqueue_l3_bytes,"
           "truth_qdisc_drop_after_dequeue_l3_bytes,"
           "truth_queue_start_packets,truth_queue_end_packets,"
           "truth_qdisc_received_packets,truth_qdisc_enqueued_packets,"
           "truth_qdisc_dequeued_packets,"
           "truth_qdisc_drop_before_enqueue_packets,"
           "truth_qdisc_drop_after_dequeue_packets,"
           "truth_queue_balance_residual_l3_bytes,"
           "truth_queue_balance_residual_packets,truth_udp_applicable,"
           "truth_udp_burst_active_duration_s,"
           "truth_udp_planned_app_payload_packets,"
           "truth_udp_planned_app_payload_bytes,"
           "truth_udp_actual_send_packets,truth_udp_actual_send_bytes,"
           "truth_udp_app_drop_packets,truth_udp_app_drop_bytes,"
           "truth_udp_backlog_applicable,truth_udp_backlog_start_bytes,"
           "truth_udp_backlog_end_bytes\n";
    m_diagOutput << "schema_version,physics_group_sha256,transport_family,"
                    "window_index,diag_queue_peak_l3_bytes,"
                    "diag_queue_peak_packets,diag_queue_nonzero_seconds,"
                    "diag_queue_time_avg_l3_bytes\n";
    m_tcpOutput
        << "schema_version,physics_group_sha256,matrix_config_sha256,"
           "tcp_truth_contract_sha256,split,run_seed,transport_family,"
           "window_index,window_start_s,window_end_s,window_duration_s,"
           "sender_index,trace_connected,segment_size_bytes,"
           "cwnd_start_observed,cwnd_start_bytes,cwnd_end_observed,"
           "cwnd_end_bytes,ssthresh_start_observed,ssthresh_start_bytes,"
           "ssthresh_end_observed,ssthresh_end_bytes,"
           "bytes_in_flight_start_observed,bytes_in_flight_start_bytes,"
           "bytes_in_flight_end_observed,bytes_in_flight_end_bytes,"
           "cong_state_start,cong_state_end,acked_bytes_observed,"
           "acked_bytes,acked_segments_observed,acked_segments,"
           "rtt_observed,rtt_sample_count,rtt_mean_ms,rtt_min_ms,"
           "rtt_max_ms,loss_event_count_observed,loss_event_count,"
           "timeout_event_count_observed,timeout_event_count,"
           "cwnd_contraction_event_count,"
           "ssthresh_contraction_event_count,"
           "ack_residual_numerator_sum_bytes,"
           "ack_residual_squared_sum_bytes2,"
           "ack_residual_scale_squared_sum_bytes2,"
           "ack_residual_normalized_squared_sum,"
           "ack_residual_valid_terms,ack_residual_mse_bytes2,"
           "ack_residual_normalized_mse,"
           "loss_residual_numerator_sum_bytes,"
           "loss_residual_squared_sum_bytes2,"
           "loss_residual_scale_squared_sum_bytes2,"
           "loss_residual_normalized_squared_sum,"
           "loss_residual_valid_terms,loss_residual_mse_bytes2,"
           "loss_residual_normalized_mse\n";
  }

  void Start() {
    Simulator::Schedule(Seconds(m_config.windowSeconds),
                        &WindowCollector::Flush, this);
    StartQueueTrace();
  }

  void SetObservationInterface(uint32_t interface) {
    NS_ABORT_MSG_IF(m_observationInterfaceConfigured,
                    "瓶颈观测接口重复配置");
    m_observationInterface = interface;
    m_observationInterfaceConfigured = true;
  }

  void OnIpv4Tx(Ptr<const Packet> packet, Ptr<Ipv4>, uint32_t interface) {
    if (interface != m_observationInterface) {
      return;
    }
    RecordDirectionalPacket(packet, true);
  }

  void OnIpv4Rx(Ptr<const Packet> packet, Ptr<Ipv4>, uint32_t interface) {
    if (interface != m_observationInterface) {
      return;
    }
    RecordDirectionalPacket(packet, false);
  }

  void RegisterTcpSender(uint32_t senderIndex, uint32_t segmentSize) {
    auto &state = State(senderIndex);
    NS_ABORT_MSG_IF(state.traceConnected, "同一发送者重复注册 TCP trace");
    NS_ABORT_MSG_IF(segmentSize == 0, "TCP MSS 必须为正数");
    state.traceConnected = true;
    state.segmentSize = segmentSize;
    state.congState = TcpSocketState::CA_OPEN;
    state.congStateStart = TcpSocketState::CA_OPEN;
  }

  void RegisterUdpSender(uint32_t senderIndex, double phaseOffsetSeconds) {
    NS_ABORT_MSG_IF(senderIndex >= m_udpRegistered.size(),
                    "UDP发送者索引越界");
    NS_ABORT_MSG_IF(m_udpRegistered[senderIndex], "UDP发送者重复注册");
    m_udpRegistered[senderIndex] = true;
    m_udpPhaseOffsetTimeSteps[senderIndex] =
        Seconds(phaseOffsetSeconds).GetTimeStep();
  }

  void OnUdpPlanned(uint32_t payloadBytes) {
    m_udpPlannedPackets += 1;
    m_udpPlannedBytes += payloadBytes;
  }

  void OnUdpSendResult(uint32_t payloadBytes, int sentBytes) {
    if (sentBytes > 0) {
      m_udpActualPackets += 1;
      m_udpActualBytes += static_cast<uint32_t>(sentBytes);
    }
    if (sentBytes < 0) {
      m_udpAppDropPackets += 1;
      m_udpAppDropBytes += payloadBytes;
    } else if (static_cast<uint32_t>(sentBytes) < payloadBytes) {
      m_udpAppDropPackets += 1;
      m_udpAppDropBytes += payloadBytes - static_cast<uint32_t>(sentBytes);
    }
  }

  void OnEnqueue(Ptr<const QueueDiscItem> item) {
    const uint64_t bytes = item->GetSize();
    m_enqueuedBytes += bytes;
    m_enqueuedPackets += 1;
    AccumulateQueueOccupancy();
    m_currentQueueBytes += bytes;
    m_currentQueuePackets += 1;
    m_windowPeakQueueBytes =
        std::max(m_windowPeakQueueBytes, m_currentQueueBytes);
    m_windowPeakQueuePackets =
        std::max(m_windowPeakQueuePackets, m_currentQueuePackets);
  }

  void OnDequeue(Ptr<const QueueDiscItem> item) {
    const uint64_t bytes = item->GetSize();
    NS_ABORT_MSG_IF(m_currentQueueBytes < bytes || m_currentQueuePackets == 0,
                    "队列追踪出现负状态");
    m_dequeuedBytes += bytes;
    m_dequeuedPackets += 1;
    AccumulateQueueOccupancy();
    m_currentQueueBytes -= bytes;
    m_currentQueuePackets -= 1;
  }

  void OnDropBeforeEnqueue(Ptr<const QueueDiscItem> item, const char *) {
    m_dropBeforeBytes += item->GetSize();
    m_dropBeforePackets += 1;
  }

  void OnDropAfterDequeue(Ptr<const QueueDiscItem> item, const char *) {
    m_dropAfterBytes += item->GetSize();
    m_dropAfterPackets += 1;
  }

  void BeginAckPacket(uint32_t senderIndex) {
    auto &state = State(senderIndex);
    NS_ABORT_MSG_IF(!state.expectedAckCwnd.empty(),
                    "上一累计 ACK 的 NewReno 期望转移未被消费");
    if (state.rtoCandidate && state.rtoCandidateTime < Simulator::Now()) {
      state.rtoCandidate = false;
    }
  }

  void OnCongestionWindow(uint32_t senderIndex, uint32_t oldValue,
                          uint32_t newValue) {
    auto &state = State(senderIndex);
    state.cwndObserved = true;
    state.cwnd = newValue;
    if (newValue < oldValue) {
      state.cwndContractions += 1;
    }
    if (newValue > oldValue && !state.expectedAckCwnd.empty()) {
      const uint32_t expected = state.expectedAckCwnd.front();
      state.expectedAckCwnd.pop_front();
      RecordResidual(state.ackResidual, static_cast<int64_t>(newValue) - expected,
                     std::max<uint32_t>(state.segmentSize, expected));
    }
  }

  void OnSlowStartThreshold(uint32_t senderIndex, uint32_t oldValue,
                            uint32_t newValue) {
    auto &state = State(senderIndex);
    state.ssthreshObserved = true;
    state.ssthresh = newValue;
    state.thresholdCandidate = true;
    state.thresholdCandidateConsumed = false;
    state.thresholdCandidateTime = Simulator::Now();
    state.thresholdOld = oldValue;
    state.thresholdNew = newValue;
    state.thresholdBytesInFlightObserved = state.bytesInFlightObserved;
    state.thresholdBytesInFlight = state.bytesInFlight;
    if (newValue < oldValue) {
      state.ssthreshContractions += 1;
    }
  }

  void OnBytesInFlight(uint32_t senderIndex, uint32_t, uint32_t newValue) {
    auto &state = State(senderIndex);
    state.bytesInFlightObserved = true;
    state.bytesInFlight = newValue;
  }

  void OnCongState(uint32_t senderIndex, TcpSocketState::TcpCongState_t,
                   TcpSocketState::TcpCongState_t newValue) {
    auto &state = State(senderIndex);
    state.congState = newValue;
    if (newValue == TcpSocketState::CA_RECOVERY) {
      state.lossEvents += 1;
      RecordThresholdResidual(state);
    } else if (newValue == TcpSocketState::CA_LOSS) {
      RecordThresholdResidual(state);
    }
  }

  void OnRtoValue(uint32_t senderIndex, Time oldValue, Time newValue) {
    auto &state = State(senderIndex);
    Time expected = oldValue + oldValue;
    if (expected > Seconds(60)) {
      expected = Seconds(60);
    }
    if (newValue == expected && newValue != oldValue) {
      state.rtoCandidate = true;
      state.rtoCandidateTime = Simulator::Now();
    }
  }

  void OnRetransmission(uint32_t senderIndex) {
    auto &state = State(senderIndex);
    if (state.rtoCandidate && state.rtoCandidateTime == Simulator::Now() &&
        state.congState == TcpSocketState::CA_LOSS) {
      state.timeoutEvents += 1;
      RecordThresholdResidual(state);
      state.rtoCandidate = false;
    }
  }

  void OnHighestRxAck(uint32_t senderIndex, SequenceNumber32 oldValue,
                      SequenceNumber32 newValue) {
    auto &state = State(senderIndex);
    if (!state.ackBaselineEstablished) {
      state.ackBaselineEstablished = true;
      return;
    }
    const int32_t signedDelta = newValue - oldValue;
    if (signedDelta <= 0) {
      return;
    }
    const uint32_t delta = static_cast<uint32_t>(signedDelta);
    state.ackedBytes += delta;
    const uint64_t withRemainder = state.ackRemainderBytes + delta;
    const uint32_t segmentsAcked =
        static_cast<uint32_t>(withRemainder / state.segmentSize);
    state.ackRemainderBytes = withRemainder % state.segmentSize;
    state.ackedSegments += segmentsAcked;
    if (segmentsAcked == 0 || !state.cwndObserved ||
        !state.ssthreshObserved ||
        state.congState != TcpSocketState::CA_OPEN) {
      return;
    }
    uint32_t expectedCwnd = state.cwnd;
    uint32_t remaining = segmentsAcked;
    if (expectedCwnd < state.ssthresh && remaining >= 1) {
      expectedCwnd += state.segmentSize;
      remaining -= 1;
      state.expectedAckCwnd.push_back(expectedCwnd);
    }
    if (expectedCwnd >= state.ssthresh && remaining > 0) {
      const double rawAdder =
          static_cast<double>(state.segmentSize) * state.segmentSize /
          expectedCwnd;
      expectedCwnd +=
          static_cast<uint32_t>(std::max(1.0, rawAdder));
      state.expectedAckCwnd.push_back(expectedCwnd);
    }
  }

  void OnRttSample(uint32_t senderIndex, Time sample) {
    NS_ABORT_MSG_IF(sample.IsZero() || sample.IsNegative(),
                    "RTT 样本必须为正数");
    auto &state = State(senderIndex);
    const double milliseconds = sample.GetSeconds() * 1000.0;
    state.rttSamples += 1;
    state.rttSumMs += milliseconds;
    state.rttMinMs = std::min(state.rttMinMs, milliseconds);
    state.rttMaxMs = std::max(state.rttMaxMs, milliseconds);
  }

private:
  struct DirectionalCounters {
    uint64_t payloadBytes{0};
    uint64_t packets{0};
    uint64_t ipBytes{0};
  };

  struct TcpFlowKey {
    uint32_t sourceAddress{0};
    uint32_t destinationAddress{0};
    uint16_t sourcePort{0};
    uint16_t destinationPort{0};

    bool operator<(const TcpFlowKey &other) const {
      if (sourceAddress != other.sourceAddress) {
        return sourceAddress < other.sourceAddress;
      }
      if (destinationAddress != other.destinationAddress) {
        return destinationAddress < other.destinationAddress;
      }
      if (sourcePort != other.sourcePort) {
        return sourcePort < other.sourcePort;
      }
      return destinationPort < other.destinationPort;
    }
  };

  struct ResidualAccumulator {
    double numeratorSum{0.0};
    double squaredSum{0.0};
    double scaleSquaredSum{0.0};
    double normalizedSquaredSum{0.0};
    uint64_t validTerms{0};
  };

  struct SenderState {
    bool traceConnected{false};
    uint32_t segmentSize{0};
    bool cwndObserved{false};
    uint32_t cwnd{0};
    bool cwndStartObserved{false};
    uint32_t cwndStart{0};
    bool ssthreshObserved{false};
    uint32_t ssthresh{0};
    bool ssthreshStartObserved{false};
    uint32_t ssthreshStart{0};
    bool bytesInFlightObserved{false};
    uint32_t bytesInFlight{0};
    bool bytesInFlightStartObserved{false};
    uint32_t bytesInFlightStart{0};
    TcpSocketState::TcpCongState_t congState{TcpSocketState::CA_OPEN};
    TcpSocketState::TcpCongState_t congStateStart{TcpSocketState::CA_OPEN};
    bool ackBaselineEstablished{false};
    uint64_t ackRemainderBytes{0};
    uint64_t ackedBytes{0};
    uint64_t ackedSegments{0};
    uint64_t rttSamples{0};
    double rttSumMs{0.0};
    double rttMinMs{std::numeric_limits<double>::infinity()};
    double rttMaxMs{0.0};
    uint64_t lossEvents{0};
    uint64_t timeoutEvents{0};
    uint64_t cwndContractions{0};
    uint64_t ssthreshContractions{0};
    std::deque<uint32_t> expectedAckCwnd;
    bool thresholdCandidate{false};
    bool thresholdCandidateConsumed{false};
    Time thresholdCandidateTime;
    uint32_t thresholdOld{0};
    uint32_t thresholdNew{0};
    bool thresholdBytesInFlightObserved{false};
    uint32_t thresholdBytesInFlight{0};
    bool rtoCandidate{false};
    Time rtoCandidateTime;
    ResidualAccumulator ackResidual;
    ResidualAccumulator lossResidual;
  };

  SenderState &State(uint32_t senderIndex) {
    NS_ABORT_MSG_IF(senderIndex >= m_states.size(), "TCP 发送者索引越界");
    return m_states[senderIndex];
  }

  static uint64_t RecordUniqueTcpRange(
      std::vector<std::pair<uint64_t, uint64_t>> &covered,
      uint64_t start, uint64_t size) {
    if (size == 0) {
      return 0;
    }
    const uint64_t end = start + size;
    NS_ABORT_MSG_IF(end < start, "TCP序列区间发生整数溢出");
    uint64_t overlap = 0;
    for (const auto &[coveredStart, coveredEnd] : covered) {
      const uint64_t intersectionStart = std::max(start, coveredStart);
      const uint64_t intersectionEnd = std::min(end, coveredEnd);
      if (intersectionEnd > intersectionStart) {
        overlap += intersectionEnd - intersectionStart;
      }
    }
    NS_ABORT_MSG_IF(overlap > size, "TCP序列区间覆盖状态不合法");

    covered.emplace_back(start, end);
    std::sort(covered.begin(), covered.end());
    std::vector<std::pair<uint64_t, uint64_t>> merged;
    for (const auto &interval : covered) {
      if (merged.empty() || interval.first > merged.back().second) {
        merged.push_back(interval);
      } else {
        merged.back().second = std::max(merged.back().second, interval.second);
      }
    }
    covered.swap(merged);
    return size - overlap;
  }

  void RecordDirectionalPacket(Ptr<const Packet> packet, bool originator) {
    NS_ABORT_MSG_IF(!m_observationInterfaceConfigured,
                    "瓶颈观测接口尚未配置");
    NS_ABORT_MSG_IF(packet == nullptr, "IPv4方向追踪收到空包");
    Ptr<Packet> copy = packet->Copy();
    Ipv4Header ipv4Header;
    const uint32_t ipv4HeaderBytes = copy->RemoveHeader(ipv4Header);
    NS_ABORT_MSG_IF(ipv4HeaderBytes == 0,
                    "IPv4方向追踪无法解析IPv4首部");
    if (ipv4Header.GetProtocol() != IpProtocolNumber(m_config.transportFamily)) {
      return;
    }

    auto &counters = originator ? m_origCounters : m_respCounters;
    counters.packets += 1;
    counters.ipBytes += packet->GetSize();
    if (m_config.transportFamily == "UDP") {
      UdpHeader udpHeader;
      NS_ABORT_MSG_IF(copy->RemoveHeader(udpHeader) == 0,
                      "UDP方向追踪无法解析UDP首部");
      counters.payloadBytes += copy->GetSize();
      return;
    }

    TcpHeader tcpHeader;
    NS_ABORT_MSG_IF(copy->RemoveHeader(tcpHeader) == 0,
                    "TCP方向追踪无法解析TCP首部");
    const uint64_t payloadBytes = copy->GetSize();
    if (payloadBytes == 0) {
      return;
    }
    const TcpFlowKey flow{
        ipv4Header.GetSource().Get(), ipv4Header.GetDestination().Get(),
        tcpHeader.GetSourcePort(), tcpHeader.GetDestinationPort()};
    auto &coverage = originator ? m_origTcpCoverage : m_respTcpCoverage;
    counters.payloadBytes += RecordUniqueTcpRange(
        coverage[flow], tcpHeader.GetSequenceNumber().GetValue(), payloadBytes);
  }

  static void RecordResidual(ResidualAccumulator &accumulator,
                             int64_t numerator, uint32_t scale) {
    NS_ABORT_MSG_IF(scale == 0, "NewReno 残差归一化尺度必须为正数");
    const double residual = static_cast<double>(numerator);
    const double denominator = static_cast<double>(scale);
    accumulator.numeratorSum += residual;
    accumulator.squaredSum += residual * residual;
    accumulator.scaleSquaredSum += denominator * denominator;
    accumulator.normalizedSquaredSum +=
        (residual / denominator) * (residual / denominator);
    accumulator.validTerms += 1;
  }

  static void ResetResidual(ResidualAccumulator &accumulator) {
    accumulator = ResidualAccumulator{};
  }

  void RecordThresholdResidual(SenderState &state) {
    if (!state.thresholdCandidate || state.thresholdCandidateConsumed ||
        state.thresholdCandidateTime != Simulator::Now() ||
        !state.thresholdBytesInFlightObserved) {
      return;
    }
    const uint32_t expected = std::max<uint32_t>(
        2 * state.segmentSize,
        static_cast<uint32_t>(0.5 * state.thresholdBytesInFlight));
    RecordResidual(state.lossResidual,
                   static_cast<int64_t>(state.thresholdNew) - expected,
                   std::max<uint32_t>(state.segmentSize, expected));
    state.thresholdCandidateConsumed = true;
  }

  template <typename T>
  void WriteOptional(bool observed, const T &value) {
    if (observed) {
      m_tcpOutput << value;
    }
  }

  void WriteResidual(const ResidualAccumulator &residual) {
    m_tcpOutput << residual.numeratorSum << ',' << residual.squaredSum << ','
                << residual.scaleSquaredSum << ','
                << residual.normalizedSquaredSum << ',' << residual.validTerms
                << ',';
    if (residual.validTerms > 0) {
      m_tcpOutput << residual.squaredSum / residual.validTerms;
    }
    m_tcpOutput << ',';
    if (residual.validTerms > 0) {
      m_tcpOutput << residual.normalizedSquaredSum / residual.validTerms;
    }
  }

  void WriteTcpRow(uint32_t senderIndex, SenderState &state,
                   double windowStart, double windowEnd) {
    NS_ABORT_MSG_IF(!state.expectedAckCwnd.empty(),
                    "窗口结束时仍有未消费的 ACK 驱动转移");
    const bool ackObserved = state.ackBaselineEstablished;
    const bool rttObserved = state.rttSamples > 0;
    m_tcpOutput << kTcpSchema << ',' << m_config.physicsGroupSha256 << ','
                << m_config.matrixConfigSha256 << ','
                << m_config.tcpTruthContractSha256 << ',' << m_config.split
                << ',' << m_config.runSeed << ',' << m_config.transportFamily
                << ',' << m_windowIndex << ',' << std::fixed
                << std::setprecision(9) << windowStart << ',' << windowEnd << ','
                << m_config.windowSeconds << ',' << senderIndex << ','
                << (state.traceConnected ? 1 : 0) << ',' << state.segmentSize
                << ',' << (state.cwndStartObserved ? 1 : 0) << ',';
    WriteOptional(state.cwndStartObserved, state.cwndStart);
    m_tcpOutput << ',' << (state.cwndObserved ? 1 : 0) << ',';
    WriteOptional(state.cwndObserved, state.cwnd);
    m_tcpOutput << ',' << (state.ssthreshStartObserved ? 1 : 0) << ',';
    WriteOptional(state.ssthreshStartObserved, state.ssthreshStart);
    m_tcpOutput << ',' << (state.ssthreshObserved ? 1 : 0) << ',';
    WriteOptional(state.ssthreshObserved, state.ssthresh);
    m_tcpOutput << ',' << (state.bytesInFlightStartObserved ? 1 : 0) << ',';
    WriteOptional(state.bytesInFlightStartObserved, state.bytesInFlightStart);
    m_tcpOutput << ',' << (state.bytesInFlightObserved ? 1 : 0) << ',';
    WriteOptional(state.bytesInFlightObserved, state.bytesInFlight);
    m_tcpOutput << ',' << static_cast<uint32_t>(state.congStateStart) << ','
                << static_cast<uint32_t>(state.congState) << ','
                << (ackObserved ? 1 : 0) << ',';
    WriteOptional(ackObserved, state.ackedBytes);
    m_tcpOutput << ',' << (ackObserved ? 1 : 0) << ',';
    WriteOptional(ackObserved, state.ackedSegments);
    m_tcpOutput << ',' << (rttObserved ? 1 : 0) << ',' << state.rttSamples
                << ',';
    if (rttObserved) {
      m_tcpOutput << state.rttSumMs / state.rttSamples;
    }
    m_tcpOutput << ',';
    WriteOptional(rttObserved, state.rttMinMs);
    m_tcpOutput << ',';
    WriteOptional(rttObserved, state.rttMaxMs);
    m_tcpOutput << ',' << (state.traceConnected ? 1 : 0) << ','
                << state.lossEvents << ',' << (state.traceConnected ? 1 : 0)
                << ',' << state.timeoutEvents << ',' << state.cwndContractions
                << ',' << state.ssthreshContractions << ',';
    WriteResidual(state.ackResidual);
    m_tcpOutput << ',';
    WriteResidual(state.lossResidual);
    m_tcpOutput << '\n';
  }

  double UdpBurstActiveDuration(Time windowStart, Time windowEnd) const {
    if (m_config.transportFamily != "UDP") {
      return 0.0;
    }
    const int64_t start = windowStart.GetTimeStep();
    const int64_t end = windowEnd.GetTimeStep();
    NS_ABORT_MSG_IF(end <= start, "UDP活动时长窗口必须为正");
    if (m_config.arrivalModel == "constant") {
      return windowEnd.GetSeconds() - windowStart.GetSeconds();
    }
    const int64_t on = Seconds(m_config.burstOnSeconds).GetTimeStep();
    const int64_t off = Seconds(m_config.burstOffSeconds).GetTimeStep();
    const int64_t cycle = on + off;
    NS_ABORT_MSG_IF(on <= 0 || off <= 0 || cycle <= 0,
                    "UDP突发周期量化后不合法");
    int64_t totalActiveTimeSteps = 0;
    for (uint32_t sender = 0; sender < m_udpRegistered.size(); ++sender) {
      NS_ABORT_MSG_IF(!m_udpRegistered[sender],
                      "UDP发送者未登记活动相位");
      int64_t cursor = start;
      while (cursor < end) {
        const int64_t phase =
            (cursor + m_udpPhaseOffsetTimeSteps[sender]) % cycle;
        const bool active = phase < on;
        const int64_t boundary = active ? on - phase : cycle - phase;
        NS_ABORT_MSG_IF(boundary <= 0, "UDP活动区间边界必须为正");
        const int64_t next = std::min(end, cursor + boundary);
        if (active) {
          totalActiveTimeSteps += next - cursor;
        }
        cursor = next;
      }
    }
    const double senderSeconds =
        TimeStep(static_cast<uint64_t>(totalActiveTimeSteps)).GetSeconds();
    return senderSeconds / m_config.senderCount;
  }

  // 按上一次采样以来的时长累积占用，必须在改变队列长度之前调用。
  void AccumulateQueueOccupancy() {
    const Time now = Simulator::Now();
    const double elapsed = (now - m_lastQueueSampleTime).GetSeconds();
    if (elapsed > 0.0) {
      m_windowQueueByteSeconds +=
          elapsed * static_cast<double>(m_currentQueueBytes);
      if (m_currentQueueBytes > 0) {
        m_windowQueueNonzeroSeconds += elapsed;
      }
    }
    m_lastQueueSampleTime = now;
  }

  // 可选队列轨迹：按固定毫秒间隔只读采样当前队列占用，不参与任何
  // 守恒计算或诊断量累积，默认关闭时不创建文件、不注册调度事件。
  void StartQueueTrace() {
    if (m_config.queueTraceIntervalMs == 0 || m_config.queueTracePath.empty()) {
      return;
    }
    m_queueTraceOutput.open(m_config.queueTracePath);
    NS_ABORT_MSG_IF(!m_queueTraceOutput.is_open(), "无法创建队列轨迹文件");
    m_queueTraceOutput << "time_s,queue_l3_bytes,queue_packets\n";
    ScheduleQueueTrace();
  }

  void ScheduleQueueTrace() {
    Simulator::Schedule(MilliSeconds(m_config.queueTraceIntervalMs),
                        &WindowCollector::SampleQueueTrace, this);
  }

  void SampleQueueTrace() {
    m_queueTraceOutput << std::fixed << std::setprecision(6)
                       << Simulator::Now().GetSeconds() << ','
                       << m_currentQueueBytes << ',' << m_currentQueuePackets
                       << '\n';
    ScheduleQueueTrace();
  }

  void Flush() {
    const Time windowEndTime = Simulator::Now();
    AccumulateQueueOccupancy();
    const Time windowStartTime = windowEndTime - Seconds(m_config.windowSeconds);
    const double windowEnd = windowEndTime.GetSeconds();
    const double windowStart = windowStartTime.GetSeconds();
    const uint64_t receivedBytes = m_enqueuedBytes + m_dropBeforeBytes;
    const uint64_t receivedPackets = m_enqueuedPackets + m_dropBeforePackets;
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
    m_mainOutput << kMainSchema << ',' << m_config.physicsGroupSha256 << ','
                 << m_config.matrixConfigSha256 << ','
                 << m_config.tcpTruthContractSha256 << ',' << m_config.split
                 << ',' << m_config.runSeed << ',' << m_config.transportFamily
                 << ',' << m_windowIndex << ',' << std::fixed
                 << std::setprecision(9) << windowStart << ',' << windowEnd
                 << ',' << m_config.windowSeconds << ',' << receivedPackets
                 << ',' << receivedBytes << ',' << m_origCounters.payloadBytes
                 << ',' << m_respCounters.payloadBytes << ','
                 << m_origCounters.packets << ',' << m_respCounters.packets
                 << ',' << m_origCounters.ipBytes << ','
                 << m_respCounters.ipBytes << ','
                 << m_windowStartQueueBytes << ',' << m_currentQueueBytes << ','
                 << receivedBytes << ',' << m_enqueuedBytes << ','
                 << m_dequeuedBytes << ',' << m_dropBeforeBytes << ','
                 << m_dropAfterBytes << ',' << m_windowStartQueuePackets << ','
                 << m_currentQueuePackets << ',' << receivedPackets << ','
                 << m_enqueuedPackets << ',' << m_dequeuedPackets << ','
                 << m_dropBeforePackets << ',' << m_dropAfterPackets << ','
                 << residualBytes << ',' << residualPackets << ',';
    const bool udpApplicable = m_config.transportFamily == "UDP";
    m_mainOutput << (udpApplicable ? 1 : 0) << ',';
    if (udpApplicable) {
      m_mainOutput << UdpBurstActiveDuration(windowStartTime, windowEndTime)
                   << ',' << m_udpPlannedPackets << ',' << m_udpPlannedBytes
                   << ',' << m_udpActualPackets << ',' << m_udpActualBytes
                   << ',' << m_udpAppDropPackets << ',' << m_udpAppDropBytes
                   << ",0,,";
    } else {
      m_mainOutput << ",,,,,,,,,";
    }
    m_mainOutput << '\n';

    // 诊断量写入旁车 CSV，主表保持 46 列不变。
    const double windowSeconds = m_config.windowSeconds;
    m_diagOutput << kDiagSchema << ',' << m_config.physicsGroupSha256 << ','
                 << m_config.transportFamily << ',' << m_windowIndex << ','
                 << m_windowPeakQueueBytes << ',' << m_windowPeakQueuePackets
                 << ',' << std::fixed << std::setprecision(9)
                 << m_windowQueueNonzeroSeconds << ','
                 << (windowSeconds > 0.0
                         ? m_windowQueueByteSeconds / windowSeconds
                         : 0.0)
                 << '\n';

    if (m_config.transportFamily == "TCP") {
      for (uint32_t index = 0; index < m_states.size(); ++index) {
        auto &state = m_states[index];
        NS_ABORT_MSG_IF(!state.traceConnected,
                        "TCP 发送者未完整连接跟踪源");
        WriteTcpRow(index, state, windowStart, windowEnd);
        state.cwndStartObserved = state.cwndObserved;
        state.cwndStart = state.cwnd;
        state.ssthreshStartObserved = state.ssthreshObserved;
        state.ssthreshStart = state.ssthresh;
        state.bytesInFlightStartObserved = state.bytesInFlightObserved;
        state.bytesInFlightStart = state.bytesInFlight;
        state.congStateStart = state.congState;
        state.ackedBytes = 0;
        state.ackedSegments = 0;
        state.rttSamples = 0;
        state.rttSumMs = 0.0;
        state.rttMinMs = std::numeric_limits<double>::infinity();
        state.rttMaxMs = 0.0;
        state.lossEvents = 0;
        state.timeoutEvents = 0;
        state.cwndContractions = 0;
        state.ssthreshContractions = 0;
        ResetResidual(state.ackResidual);
        ResetResidual(state.lossResidual);
      }
    }
    m_mainOutput.flush();
    m_tcpOutput.flush();

    m_windowStartQueueBytes = m_currentQueueBytes;
    m_windowStartQueuePackets = m_currentQueuePackets;
    m_windowPeakQueueBytes = m_currentQueueBytes;
    m_windowPeakQueuePackets = m_currentQueuePackets;
    m_windowQueueByteSeconds = 0.0;
    m_windowQueueNonzeroSeconds = 0.0;
    m_lastQueueSampleTime = windowEndTime;
    m_enqueuedBytes = 0;
    m_dequeuedBytes = 0;
    m_dropBeforeBytes = 0;
    m_dropAfterBytes = 0;
    m_enqueuedPackets = 0;
    m_dequeuedPackets = 0;
    m_dropBeforePackets = 0;
    m_dropAfterPackets = 0;
    m_udpPlannedPackets = 0;
    m_udpPlannedBytes = 0;
    m_udpActualPackets = 0;
    m_udpActualBytes = 0;
    m_udpAppDropPackets = 0;
    m_udpAppDropBytes = 0;
    m_origCounters = DirectionalCounters{};
    m_respCounters = DirectionalCounters{};
    m_windowIndex += 1;
    if (windowEnd + m_config.windowSeconds <=
        m_config.durationSeconds + 1e-9) {
      Simulator::Schedule(Seconds(m_config.windowSeconds),
                          &WindowCollector::Flush, this);
    }
  }

  ScenarioConfig m_config;
  std::vector<SenderState> m_states;
  std::vector<bool> m_udpRegistered;
  std::vector<int64_t> m_udpPhaseOffsetTimeSteps;
  std::ofstream m_mainOutput;
  std::ofstream m_tcpOutput;
  std::ofstream m_diagOutput;
  std::ofstream m_queueTraceOutput;
  uint32_t m_windowIndex{0};
  uint64_t m_currentQueueBytes{0};
  uint64_t m_windowStartQueueBytes{0};
  uint64_t m_currentQueuePackets{0};
  uint64_t m_windowStartQueuePackets{0};
  // 诊断专用：窗内队列占用观测量，不参与任何守恒或物理计算。
  uint64_t m_windowPeakQueueBytes{0};
  uint64_t m_windowPeakQueuePackets{0};
  double m_windowQueueByteSeconds{0.0};
  double m_windowQueueNonzeroSeconds{0.0};
  Time m_lastQueueSampleTime{Seconds(0)};
  uint64_t m_enqueuedBytes{0};
  uint64_t m_dequeuedBytes{0};
  uint64_t m_dropBeforeBytes{0};
  uint64_t m_dropAfterBytes{0};
  uint64_t m_enqueuedPackets{0};
  uint64_t m_dequeuedPackets{0};
  uint64_t m_dropBeforePackets{0};
  uint64_t m_dropAfterPackets{0};
  uint64_t m_udpPlannedPackets{0};
  uint64_t m_udpPlannedBytes{0};
  uint64_t m_udpActualPackets{0};
  uint64_t m_udpActualBytes{0};
  uint64_t m_udpAppDropPackets{0};
  uint64_t m_udpAppDropBytes{0};
  bool m_observationInterfaceConfigured{false};
  uint32_t m_observationInterface{0};
  DirectionalCounters m_origCounters;
  DirectionalCounters m_respCounters;
  std::map<TcpFlowKey, std::vector<std::pair<uint64_t, uint64_t>>>
      m_origTcpCoverage;
  std::map<TcpFlowKey, std::vector<std::pair<uint64_t, uint64_t>>>
      m_respTcpCoverage;
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
  struct RttHistory {
    RttHistory(SequenceNumber32 sequence, uint32_t length, Time sent)
        : seq(sequence), count(length), time(sent) {}

    SequenceNumber32 seq;
    uint32_t count;
    Time time;
    bool retransmitted{false};
  };

  void StartApplication() override {
    m_running = true;
    m_socket = Socket::CreateSocket(
        GetNode(), TypeId::LookupByName(SocketFactoryName(m_config.transportFamily)));
    NS_ABORT_MSG_IF(m_socket == nullptr, "无法创建传输层 socket");
    NS_ABORT_MSG_IF(m_socket->Bind() != 0, "发送 socket 绑定失败");
    if (m_config.transportFamily == "TCP") {
      m_socket->SetAttribute("Sack", BooleanValue(false));
      m_socket->SetAttribute("Timestamp", BooleanValue(false));
      m_socket->SetAttribute("UseEcn", EnumValue(TcpSocketState::Off));
      UintegerValue segmentSize;
      m_socket->GetAttribute("SegmentSize", segmentSize);
      m_collector->RegisterTcpSender(m_senderIndex, segmentSize.Get());
      ConnectTcpTraces();
      m_socket->SetConnectCallback(
          MakeCallback(&ProtocolTrafficApplication::ConnectionSucceeded, this),
          MakeCallback(&ProtocolTrafficApplication::ConnectionFailed, this));
      NS_ABORT_MSG_IF(m_socket->Connect(m_peer) != 0, "TCP Connect 调用失败");
    } else {
      NS_ABORT_MSG_IF(m_socket->Connect(m_peer) != 0, "UDP Connect 调用失败");
      m_collector->RegisterUdpSender(m_senderIndex, m_phaseOffsetSeconds);
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

  void ConnectTcpTraces() {
    bool connected = m_socket->TraceConnectWithoutContext(
        "CongestionWindow",
        MakeCallback(&ProtocolTrafficApplication::OnCongestionWindow, this));
    NS_ABORT_MSG_IF(!connected, "无法连接 CongestionWindow trace");
    connected = m_socket->TraceConnectWithoutContext(
        "SlowStartThreshold",
        MakeCallback(&ProtocolTrafficApplication::OnSlowStartThreshold, this));
    NS_ABORT_MSG_IF(!connected, "无法连接 SlowStartThreshold trace");
    connected = m_socket->TraceConnectWithoutContext(
        "BytesInFlight",
        MakeCallback(&ProtocolTrafficApplication::OnBytesInFlight, this));
    NS_ABORT_MSG_IF(!connected, "无法连接 BytesInFlight trace");
    connected = m_socket->TraceConnectWithoutContext(
        "CongState", MakeCallback(&ProtocolTrafficApplication::OnCongState, this));
    NS_ABORT_MSG_IF(!connected, "无法连接 CongState trace");
    connected = m_socket->TraceConnectWithoutContext(
        "HighestRxAck",
        MakeCallback(&ProtocolTrafficApplication::OnHighestRxAck, this));
    NS_ABORT_MSG_IF(!connected, "无法连接 HighestRxAck trace");
    connected = m_socket->TraceConnectWithoutContext(
        "RTT", MakeCallback(&ProtocolTrafficApplication::OnRttState, this));
    NS_ABORT_MSG_IF(!connected, "无法连接 RTT trace");
    connected = m_socket->TraceConnectWithoutContext(
        "LastRTT", MakeCallback(&ProtocolTrafficApplication::OnLastRtt, this));
    NS_ABORT_MSG_IF(!connected, "无法连接 LastRTT trace");
    connected = m_socket->TraceConnectWithoutContext(
        "RTO", MakeCallback(&ProtocolTrafficApplication::OnRtoValue, this));
    NS_ABORT_MSG_IF(!connected, "无法连接 RTO trace");
    connected = m_socket->TraceConnectWithoutContext(
        "Tx", MakeCallback(&ProtocolTrafficApplication::OnTcpTx, this));
    NS_ABORT_MSG_IF(!connected, "无法连接 TCP Tx trace");
    connected = m_socket->TraceConnectWithoutContext(
        "Rx", MakeCallback(&ProtocolTrafficApplication::OnTcpRx, this));
    NS_ABORT_MSG_IF(!connected, "无法连接 TCP Rx trace");
    connected = m_socket->TraceConnectWithoutContext(
        "Retransmission",
        MakeCallback(&ProtocolTrafficApplication::OnRetransmission, this));
    NS_ABORT_MSG_IF(!connected, "无法连接 Retransmission trace");
  }

  void ConnectionSucceeded(Ptr<Socket>) {
    m_connected = true;
    ScheduleNext(Seconds(0));
  }

  void ConnectionFailed(Ptr<Socket>) { NS_ABORT_MSG("TCP 连接失败"); }

  bool TraceCollectionActive() const {
    return m_running &&
           Simulator::Now() < Seconds(m_config.durationSeconds);
  }

  void OnCongestionWindow(uint32_t oldValue, uint32_t newValue) {
    if (!TraceCollectionActive()) {
      return;
    }
    m_collector->OnCongestionWindow(m_senderIndex, oldValue, newValue);
  }

  void OnSlowStartThreshold(uint32_t oldValue, uint32_t newValue) {
    if (!TraceCollectionActive()) {
      return;
    }
    m_collector->OnSlowStartThreshold(m_senderIndex, oldValue, newValue);
  }

  void OnBytesInFlight(uint32_t oldValue, uint32_t newValue) {
    if (!TraceCollectionActive()) {
      return;
    }
    m_collector->OnBytesInFlight(m_senderIndex, oldValue, newValue);
  }

  void OnCongState(TcpSocketState::TcpCongState_t oldValue,
                   TcpSocketState::TcpCongState_t newValue) {
    if (!TraceCollectionActive()) {
      return;
    }
    m_collector->OnCongState(m_senderIndex, oldValue, newValue);
  }

  void OnHighestRxAck(SequenceNumber32 oldValue, SequenceNumber32 newValue) {
    if (!TraceCollectionActive()) {
      return;
    }
    m_collector->OnHighestRxAck(m_senderIndex, oldValue, newValue);
  }

  void OnRttState(Time, Time newValue) {
    if (!TraceCollectionActive()) {
      return;
    }
    NS_ABORT_MSG_IF(newValue.IsNegative(), "平滑 RTT 不得为负数");
  }

  void OnLastRtt(Time, Time newValue) {
    if (!TraceCollectionActive()) {
      return;
    }
    NS_ABORT_MSG_IF(newValue.IsNegative(), "最近 RTT 不得为负数");
  }

  void OnRtoValue(Time oldValue, Time newValue) {
    if (!TraceCollectionActive()) {
      return;
    }
    m_collector->OnRtoValue(m_senderIndex, oldValue, newValue);
  }

  void OnTcpTx(Ptr<const Packet> packet, const TcpHeader &header,
               Ptr<const TcpSocketBase>) {
    if (!TraceCollectionActive()) {
      return;
    }
    if (packet->GetSize() == 0) {
      return;
    }
    const SequenceNumber32 sequence = header.GetSequenceNumber();
    for (const auto &history : m_rttHistory) {
      if (sequence >= history.seq &&
          sequence < history.seq + SequenceNumber32(history.count)) {
        return;
      }
    }
    m_rttHistory.emplace_back(sequence, packet->GetSize(), Simulator::Now());
  }

  Time CalculateRttSample(const TcpHeader &header,
                          const RttHistory &history) const {
    if (header.GetAckNumber() >=
            history.seq + SequenceNumber32(history.count) &&
        !history.retransmitted) {
      return Simulator::Now() - history.time;
    }
    return Seconds(0);
  }

  void OnTcpRx(Ptr<const Packet>, const TcpHeader &header,
               Ptr<const TcpSocketBase>) {
    if (!TraceCollectionActive()) {
      return;
    }
    m_collector->BeginAckPacket(m_senderIndex);
    if (!(header.GetFlags() & TcpHeader::ACK) || m_rttHistory.empty()) {
      return;
    }
    const SequenceNumber32 ack = header.GetAckNumber();
    RttHistory latest = m_rttHistory.front();
    while (!m_rttHistory.empty()) {
      const auto &history = m_rttHistory.front();
      if (history.seq + SequenceNumber32(history.count) > ack) {
        break;
      }
      latest = history;
      m_rttHistory.pop_front();
    }
    const Time sample = CalculateRttSample(header, latest);
    if (!sample.IsZero()) {
      m_collector->OnRttSample(m_senderIndex, sample);
    }
  }

  void OnRetransmission(Ptr<const Packet> packet, const TcpHeader &header,
                        const Address &, const Address &,
                        Ptr<const TcpSocketBase>) {
    if (!TraceCollectionActive()) {
      return;
    }
    const SequenceNumber32 sequence = header.GetSequenceNumber();
    for (auto &history : m_rttHistory) {
      if (sequence >= history.seq &&
          sequence < history.seq + SequenceNumber32(history.count)) {
        history.retransmitted = true;
        history.count =
            (sequence + SequenceNumber32(packet->GetSize())) - history.seq;
        break;
      }
    }
    m_collector->OnRetransmission(m_senderIndex);
  }

  int64_t BurstPhaseTimeSteps(Time now) const {
    const int64_t cycleTimeSteps =
        Seconds(m_config.burstOnSeconds).GetTimeStep() +
        Seconds(m_config.burstOffSeconds).GetTimeStep();
    NS_ABORT_MSG_IF(cycleTimeSteps <= 0, "突发周期必须包含正时间步");
    return (now.GetTimeStep() + Seconds(m_phaseOffsetSeconds).GetTimeStep()) %
           cycleTimeSteps;
  }

  bool BurstActive(Time now) const {
    return m_config.arrivalModel == "constant" ||
           BurstPhaseTimeSteps(now) <
               Seconds(m_config.burstOnSeconds).GetTimeStep();
  }

  Time DelayUntilBurstActive(Time now) const {
    const int64_t on = Seconds(m_config.burstOnSeconds).GetTimeStep();
    const int64_t cycle =
        on + Seconds(m_config.burstOffSeconds).GetTimeStep();
    const int64_t phase = BurstPhaseTimeSteps(now);
    NS_ABORT_MSG_IF(phase < on, "活动阶段不得请求下一开启延迟");
    return TimeStep(static_cast<uint64_t>(cycle - phase));
  }

  Time PacketInterval() const {
    double instantaneousRateBps = m_targetRateMbps * 1000000.0;
    if (m_config.arrivalModel == "bursty") {
      const double duty = m_config.burstOnSeconds /
                          (m_config.burstOnSeconds + m_config.burstOffSeconds);
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
    if (m_config.transportFamily == "UDP") {
      m_collector->OnUdpPlanned(m_config.packetSizeBytes);
    }
    const int sent = m_socket->Send(Create<Packet>(m_config.packetSizeBytes));
    if (m_config.transportFamily == "UDP") {
      m_collector->OnUdpSendResult(m_config.packetSizeBytes, sent);
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
  std::deque<RttHistory> m_rttHistory;
};

void ChangeCapacity(Ptr<PointToPointNetDevice> device, Ptr<QueueDisc> queueDisc,
                    const std::string &queueModel, uint64_t capacityBps) {
  device->SetDataRate(DataRate(capacityBps));
  if (queueModel == "red") {
    queueDisc->SetAttribute("LinkBandwidth", DataRateValue(DataRate(capacityBps)));
  }
}

std::vector<double> SenderRates(const ScenarioConfig &config) {
  const double average = config.totalOfferedLoadMbps / config.senderCount;
  std::vector<double> rates(config.senderCount, average);
  if (config.attackSenderCount == 0) {
    return rates;
  }
  const double attackRate = average * 1.5;
  const double benignTotal =
      config.totalOfferedLoadMbps - attackRate * config.attackSenderCount;
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
  command.AddValue("physicsGroupSha256", "物理配对组标识",
                   config.physicsGroupSha256);
  command.AddValue("matrixConfigSha256", "冻结矩阵配置哈希",
                   config.matrixConfigSha256);
  command.AddValue("tcpTruthContractSha256", "TCP真值v2合同哈希",
                   config.tcpTruthContractSha256);
  command.AddValue("split", "冻结划分", config.split);
  command.AddValue("runSeed", "非零运行种子", config.runSeed);
  command.AddValue("transportFamily", "TCP或UDP", config.transportFamily);
  command.AddValue("duration", "仿真时长秒", config.durationSeconds);
  command.AddValue("window", "窗口时长秒", config.windowSeconds);
  command.AddValue("trafficMode", "benign或dos", config.trafficMode);
  command.AddValue("binaryLabel", "二元审计标签", config.binaryLabel);
  command.AddValue("arrivalModel", "constant或bursty", config.arrivalModel);
  command.AddValue("queueModel", "fifo、codel或red", config.queueModel);
  command.AddValue("offeredLoadRatio", "相对容量负载", config.offeredLoadRatio);
  command.AddValue("initialCapacityMbps", "初始瓶颈容量",
                   config.initialCapacityMbps);
  command.AddValue("shiftedCapacityMbps", "变化后瓶颈容量",
                   config.shiftedCapacityMbps);
  command.AddValue("capacityChangeSeconds", "容量变化时刻",
                   config.capacityChangeSeconds);
  command.AddValue("accessDelayMs", "接入单向时延", config.accessDelayMs);
  command.AddValue("bottleneckDelayMs", "瓶颈单向时延",
                   config.bottleneckDelayMs);
  command.AddValue("queueLimitPackets", "队列上限", config.queueLimitPackets);
  command.AddValue("downstreamLossRate", "下游独立丢包率",
                   config.downstreamLossRate);
  command.AddValue("queueTraceIntervalMs",
                   "队列轨迹采样间隔毫秒，0 表示关闭",
                   config.queueTraceIntervalMs);
  command.AddValue("queueTracePath", "队列轨迹输出路径",
                   config.queueTracePath);
  command.AddValue("senderCount", "发送者总数", config.senderCount);
  command.AddValue("benignSenderCount", "良性发送者数",
                   config.benignSenderCount);
  command.AddValue("attackSenderCount", "攻击发送者数",
                   config.attackSenderCount);
  command.AddValue("totalOfferedLoadMbps", "总提供负载",
                   config.totalOfferedLoadMbps);
  command.AddValue("packetSizeBytes", "应用载荷包长", config.packetSizeBytes);
  command.AddValue("burstOnSeconds", "突发开启时长", config.burstOnSeconds);
  command.AddValue("burstOffSeconds", "突发关闭时长", config.burstOffSeconds);
  command.AddValue("output", "主窗口CSV.partial", config.outputPath);
  command.AddValue("tcpOutput", "TCP发送者窗口CSV.partial",
                   config.tcpOutputPath);
  command.Parse(argc, argv);
  ValidateConfig(config);

  RngSeedManager::SetSeed(config.runSeed);
  RngSeedManager::SetRun(1);
  Config::SetDefault("ns3::TcpL4Protocol::SocketType",
                     TypeIdValue(TcpNewReno::GetTypeId()));
  Config::SetDefault("ns3::TcpSocketBase::Sack", BooleanValue(false));
  Config::SetDefault("ns3::TcpSocketBase::Timestamp", BooleanValue(false));
  Config::SetDefault("ns3::TcpSocketBase::UseEcn",
                     EnumValue(TcpSocketState::Off));
  Config::SetDefault("ns3::TcpNewReno::BetaLoss", DoubleValue(0.5));

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
  bottleneck.SetDeviceAttribute("DataRate",
                                DataRateValue(DataRate(initialCapacityBps)));
  bottleneck.SetChannelAttribute(
      "Delay", StringValue(DelayString(config.bottleneckDelayMs)));
  bottleneck.SetQueue("ns3::DropTailQueue", "MaxSize", StringValue("10000p"));
  auto bottleneckDevices = bottleneck.Install(router.Get(0), victim.Get(0));
  auto routerDevice = DynamicCast<PointToPointNetDevice>(bottleneckDevices.Get(0));
  auto victimDevice = DynamicCast<PointToPointNetDevice>(bottleneckDevices.Get(1));
  NS_ABORT_MSG_IF(routerDevice == nullptr || victimDevice == nullptr,
                  "瓶颈设备类型不正确");

  TrafficControlHelper trafficControl;
  std::ostringstream queueLimit;
  queueLimit << config.queueLimitPackets << 'p';
  if (config.queueModel == "red") {
    trafficControl.SetRootQueueDisc(
        QueueDiscType(config.queueModel), "MaxSize", StringValue(queueLimit.str()),
        "LinkBandwidth", DataRateValue(DataRate(initialCapacityBps)), "LinkDelay",
        TimeValue(MilliSeconds(config.bottleneckDelayMs)));
  } else {
    trafficControl.SetRootQueueDisc(QueueDiscType(config.queueModel), "MaxSize",
                                    StringValue(queueLimit.str()));
  }
  auto queueDiscs = trafficControl.Install(routerDevice);
  auto queueDisc = queueDiscs.Get(0);
  NS_ABORT_MSG_IF(queueDisc == nullptr, "无法安装瓶颈队列规则");

  Ipv4AddressHelper bottleneckAddress;
  bottleneckAddress.SetBase("10.2.0.0", "255.255.255.0");
  auto bottleneckInterfaces = bottleneckAddress.Assign(bottleneckDevices);
  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  if (config.downstreamLossRate > 0.0) {
    auto errorModel = CreateObject<RateErrorModel>();
    errorModel->SetAttribute("ErrorUnit",
                             EnumValue(RateErrorModel::ERROR_UNIT_PACKET));
    errorModel->SetAttribute("ErrorRate", DoubleValue(config.downstreamLossRate));
    errorModel->AssignStreams(5000);
    victimDevice->SetAttribute("ReceiveErrorModel", PointerValue(errorModel));
  }

  WindowCollector collector(config);
  auto routerIpv4 = router.Get(0)->GetObject<Ipv4L3Protocol>();
  NS_ABORT_MSG_IF(routerIpv4 == nullptr, "无法取得路由器 Ipv4L3Protocol");
  const int32_t observationInterface =
      routerIpv4->GetInterfaceForDevice(routerDevice);
  NS_ABORT_MSG_IF(observationInterface < 0, "无法定位路由器瓶颈IPv4接口");
  collector.SetObservationInterface(
      static_cast<uint32_t>(observationInterface));
  NS_ABORT_MSG_IF(!routerIpv4->TraceConnectWithoutContext(
                      "Tx", MakeCallback(&WindowCollector::OnIpv4Tx,
                                         &collector)),
                  "无法连接瓶颈IPv4 Tx方向追踪");
  NS_ABORT_MSG_IF(!routerIpv4->TraceConnectWithoutContext(
                      "Rx", MakeCallback(&WindowCollector::OnIpv4Rx,
                                         &collector)),
                  "无法连接瓶颈IPv4 Rx方向追踪");
  NS_ABORT_MSG_IF(!queueDisc->TraceConnectWithoutContext(
                      "Enqueue", MakeCallback(&WindowCollector::OnEnqueue, &collector)),
                  "无法连接 QueueDisc Enqueue trace");
  NS_ABORT_MSG_IF(!queueDisc->TraceConnectWithoutContext(
                      "Dequeue", MakeCallback(&WindowCollector::OnDequeue, &collector)),
                  "无法连接 QueueDisc Dequeue trace");
  NS_ABORT_MSG_IF(!queueDisc->TraceConnectWithoutContext(
                      "DropBeforeEnqueue",
                      MakeCallback(&WindowCollector::OnDropBeforeEnqueue, &collector)),
                  "无法连接 QueueDisc DropBeforeEnqueue trace");
  NS_ABORT_MSG_IF(!queueDisc->TraceConnectWithoutContext(
                      "DropAfterDequeue",
                      MakeCallback(&WindowCollector::OnDropAfterDequeue, &collector)),
                  "无法连接 QueueDisc DropAfterDequeue trace");

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
                        routerDevice, queueDisc, config.queueModel,
                        shiftedCapacityBps);
  }
  collector.Start();
  Simulator::Stop(Seconds(config.durationSeconds + config.windowSeconds));
  Simulator::Run();
  Simulator::Destroy();
  return 0;
}
