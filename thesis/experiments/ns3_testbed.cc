/*
 * ns3_testbed.cc — CI-PRD 测试床仿真（§3.3 设计）
 *
 * 拓扑：7 节点星形（C1/C2/C3 → S1 核心交换机 → SV1/SV2/SV3）
 * 正常流量：客户端 TCP BulkSend 向服务端发数据 + UDP 背景流
 * DDoS 注入：t=5s 起，3 个 OnOff 高率 UDP 流洪泛 SV1
 * 数据采集：每 Δ=0.5s 窗口，per-node 字节计数 → CSV
 *   输出：x_position, t, rho, i1_residual
 *   ρ = bytes_in / Δ；I1 残差 = |bytes_in - bytes_out|
 *
 * 编译：放入 ns-3-dev/scratch/，执行 ./ns3 build
 * 运行：./ns3 run "ns3_testbed --output=testbed_rho.csv"
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"

#include <fstream>
#include <vector>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("TestbedSim");

// ===== 节点位置（1-D 映射，对齐 PINN 的 x∈[0,1]）=====
const int N_NODES = 7;
const double X_POS[N_NODES] = {0.0, 0.1, 0.2, 0.5, 0.7, 0.8, 0.9};
// C1, C2, C3, S1, SV1, SV2, SV3

// ===== per-node per-window 字节计数器 =====
struct NodeCounter {
    uint64_t bytesIn;
    uint64_t bytesOut;
};
static std::vector<NodeCounter> g_counters(N_NODES);
static double g_windowStart = 0.0;
static const double DELTA = 0.5;  // 采样窗口
static std::ofstream g_csv;

// ===== trace 回调：记录每节点收/发字节 =====
static int GetNodeId(Ptr<Node> node) {
    return node->GetId();
}

static void
MacRxCallback(Ptr<Node> node, Ptr<const Packet> p) {
    g_counters[node->GetId()].bytesIn += p->GetSize();
}

static void
MacTxCallback(Ptr<Node> node, Ptr<const Packet> p) {
    g_counters[node->GetId()].bytesOut += p->GetSize();
}

// ===== 周期采集：输出 CSV 行 + 重置计数器 =====
static void
CollectWindow() {
    double t = Simulator::Now().GetSeconds();
    for (int i = 0; i < N_NODES; i++) {
        double rho = g_counters[i].bytesIn / DELTA;
        double i1res = std::abs((double)g_counters[i].bytesIn - (double)g_counters[i].bytesOut);
        g_csv << X_POS[i] << "," << t << "," << rho << "," << i1res << "\n";
        g_counters[i] = {0, 0};  // 重置
    }
    // 调度下一次采集
    Simulator::Schedule(Seconds(DELTA), &CollectWindow);
}

// ===== DDoS 注入：t=5s 启动洪泛到 SV1 =====
static void
StartDDoS(NodeContainer attackers, Ipv4Address victimIp, uint16_t port) {
    NS_LOG_INFO(">>> DDoS 注入启动: t=" << Simulator::Now().GetSeconds() << "s");
    OnOffHelper onoff("ns3::UdpSocketFactory",
                      Address(InetSocketAddress(victimIp, port)));
    onoff.SetAttribute("DataRate", DataRateValue(DataRate("100Mb/s")));
    onoff.SetAttribute("PacketSize", UintegerValue(1024));
    ApplicationContainer apps = onoff.Install(attackers);
    apps.Start(Seconds(0));
    apps.Stop(Seconds(10));
}

int
main(int argc, char *argv[]) {
    std::string outputFile = "testbed_rho.csv";
    double simTime = 10.0;
    double ddosTime = 5.0;
    CommandLine cmd;
    cmd.AddValue("output", "CSV output path", outputFile);
    cmd.AddValue("simTime", "Simulation time (s)", simTime);
    cmd.AddValue("ddosTime", "DDoS start time (s)", ddosTime);
    cmd.Parse(argc, argv);

    LogComponentEnable("TestbedSim", LOG_LEVEL_INFO);

    // ===== 创建节点 =====
    NodeContainer clients, switchNode, servers;
    clients.Create(3);  // C1, C2, C3 (nodeId 0,1,2)
    switchNode.Create(1);  // S1 (nodeId 3)
    servers.Create(3);  // SV1, SV2, SV3 (nodeId 4,5,6)

    // ===== 安装协议栈 =====
    InternetStackHelper internet;
    internet.Install(clients);
    internet.Install(switchNode);
    internet.Install(servers);

    // ===== PointToPoint 链路 =====
    PointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate", StringValue("10Mbps"));
    p2p.SetChannelAttribute("Delay", StringValue("2ms"));

    // 客户端 ↔ S1
    std::vector<NetDeviceContainer> clientLinks(3);
    Ipv4AddressHelper addr;
    addr.SetBase("10.1.0.0", "255.255.255.0");
    for (int i = 0; i < 3; i++) {
        clientLinks[i] = p2p.Install(clients.Get(i), switchNode.Get(0));
        addr.Assign(clientLinks[i]);
        addr.NewNetwork();
    }
    // S1 ↔ 服务端
    std::vector<NetDeviceContainer> serverLinks(3);
    addr.SetBase("10.2.0.0", "255.255.255.0");
    for (int i = 0; i < 3; i++) {
        serverLinks[i] = p2p.Install(switchNode.Get(0), servers.Get(i));
        addr.Assign(serverLinks[i]);
        addr.NewNetwork();
    }

    // ===== 获取 SV1 的 IP（DDoS 目标）=====
    Ptr<Ipv4> sv1Ipv4 = servers.Get(0)->GetObject<Ipv4>();
    Ipv4Address victimIp = sv1Ipv4->GetAddress(1, 0).GetLocal();

    // ===== 正常流量：TCP BulkSend C→SV =====
    uint16_t port = 9000;
    for (int i = 0; i < 3; i++) {
        // 服务端装 PacketSink
        PacketSinkHelper sink("ns3::TcpSocketFactory",
                              Address(InetSocketAddress(Ipv4Address::GetAny(), port + i)));
        ApplicationContainer sinkApps = sink.Install(servers.Get(i));
        sinkApps.Start(Seconds(0));
        sinkApps.Stop(Seconds(simTime));

        // 客户端装 BulkSend
        Ptr<Ipv4> cliIpv4 = clients.Get(i)->GetObject<Ipv4>();
        Ipv4Address svIp = servers.Get(i)->GetObject<Ipv4>()->GetAddress(1, 0).GetLocal();
        BulkSendHelper bulk("ns3::TcpSocketFactory",
                            Address(InetSocketAddress(svIp, port + i)));
        bulk.SetAttribute("MaxBytes", UintegerValue(0));  // 无限发送
        ApplicationContainer bulkApps = bulk.Install(clients.Get(i));
        bulkApps.Start(Seconds(1.0));
        bulkApps.Stop(Seconds(simTime));
    }

    // ===== UDP 背景流 =====
    OnOffHelper udp("ns3::UdpSocketFactory",
                    Address(InetSocketAddress(servers.Get(1)->GetObject<Ipv4>()->GetAddress(1,0).GetLocal(), 5000)));
    udp.SetAttribute("DataRate", DataRateValue(DataRate("1Mb/s")));
    udp.SetAttribute("PacketSize", UintegerValue(512));
    ApplicationContainer udpApps = udp.Install(clients.Get(0));
    udpApps.Start(Seconds(0.5));
    udpApps.Stop(Seconds(simTime));

    // ===== 连接 trace 回调（per-node byte counting）=====
    for (int n = 0; n < N_NODES; n++) {
        Ptr<Node> node;
        if (n < 3) node = clients.Get(n);
        else if (n == 3) node = switchNode.Get(0);
        else node = servers.Get(n - 4);

        for (uint32_t d = 0; d < node->GetNDevices(); d++) {
            Ptr<NetDevice> dev = node->GetDevice(d);
            // MacRx: 接收
            dev->TraceConnectWithoutContext("MacRx",
                MakeBoundCallback(&MacRxCallback, node));
            // MacTx: 发送
            dev->TraceConnectWithoutContext("MacTx",
                MakeBoundCallback(&MacTxCallback, node));
        }
    }

    // ===== 调度 DDoS =====
    NodeContainer ddosAttackers;
    ddosAttackers.Add(clients.Get(0));
    ddosAttackers.Add(clients.Get(1));
    ddosAttackers.Add(clients.Get(2));
    Simulator::Schedule(Seconds(ddosTime), &StartDDoS,
                        ddosAttackers, victimIp, 7000);

    // ===== 开 CSV + 调度周期采集 =====
    g_csv.open(outputFile);
    g_csv << "x,t,rho,i1_residual\n";
    Simulator::Schedule(Seconds(DELTA), &CollectWindow);

    // ===== 运行 =====
    NS_LOG_INFO("=== 测试床仿真启动 ===");
    NS_LOG_INFO("拓扑: 7 节点星形 (C1/C2/C3 → S1 → SV1/SV2/SV3)");
    NS_LOG_INFO("DDoS: t=" << ddosTime << "s 起, 3x100Mb/s UDP → SV1(x=0.7)");
    NS_LOG_INFO("采集: Δ=" << DELTA << "s, 输出 " << outputFile);
    Simulator::Stop(Seconds(simTime));
    Simulator::Run();
    Simulator::Destroy();
    g_csv.close();

    NS_LOG_INFO("=== 仿真完成, 数据已写入 " << outputFile << " ===");
    return 0;
}
