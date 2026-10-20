# 探测任务下发的监控方案设计（基于知识库检索）

> 检索方式：research-knowledge MCP（lexical 模式在索引中无命中，实际内容以直接读取 ~/Dev/Research vault 文件为准）。
> 检索日期：2026-08-27

## 一、检索结果汇总（知识来源）

### 1. moni 监控 / PromQL 相关

| 条目 | 路径 | 关键内容 |
| --- | --- | --- |
| MCDN PromQL 指标与告警查询边界 | `~/Dev/Research/manba-bi/Knowledge/mcdn-promql-monitoring.md` | `mcdn_network_quality` 是单公网探测目标丢包率；告警必须先聚合同节点多目标，不能单目标直接推断节点故障；`mcdn_lines_info{info_type="isp_lines"}` 线路可用率；查询返回空须区分「数据源选错」与「阈值过高」 |
| Moni 指标查询 openapi（Hawkeye） | `~/Dev/Research/bban-api/Sources/Docs/hawkeye-prometheus-openapi.md` | 即时查询 `GET /report/api/v2/query/datasource/{id}?query=`；范围查询 `/query_range/...?query=&start=&end=&step=60`；`Authorization` JWT 头；限流 5 QPS；`code=0` 表示成功；必须禁用代理 |
| Moni Go HTTP 客户端指标基数控制 | `~/Dev/Research/bban-api/Sources/Docs/moni-http-client-metric-cardinality.md` | go-common HTTP 客户端默认生成 Moni 监控；动态路径会造成高基数指标；用 Metric URL 聚合 / `PathRemap` / `HostRemap` 控制基数 |
| PromQL 监控草稿 | `~/Dev/Research/_ingestion-staging/.../manba-bi-promql-monitoring.md` | PromQL 文档只记录指标语义/标签/聚合与阈值来源，查询地址与 Token 不进知识库 |

### 2. 探测任务下发链路

| 条目 | 路径 | 关键内容 |
| --- | --- | --- |
| mcdn-v 探测任务体系 | `~/Dev/Research/bban-api/Knowledge/mcdn-v-probe-task-system.md` | 三层：候选池（`isMcdnVodProbeTarget`）+ 确定性抽样（`percentage`）+ 结果查询严格分派；下发路径 Taishan 失败降级、结果查询严格报错（容错不对称）；admin 生成任务 → noded `GET /v1/task` 领取 → 执行 → `POST /v1/taskresult` 上报 → Redis/Taishan；`Source` 字段为 MinerChannel（如 OSTHWEAST） |
| MCDN 探测结果转 Prometheus（mcdn_probe.py） | `~/Dev/Research/bban-api/Knowledge/mcdn-probe-prometheus-exporter.md` | 三套独立体系（A 探测任务结果 / B 拨测 dialing / C 跨运营商丢包率）不可混用；textfile collector 部署；指标 `mcdn_probe_*`；标识符体系（BBAN id vs instance_name）需映射 |
| JSON 转 Prometheus 通用工作流 | `~/Dev/Research/bban-api/Knowledge/json-to-prometheus-textfile-workflow.md` | 七步：定技术路线 → 实测响应结构 → 确认鉴权层级 → 对齐标识符 → 指标 schema 判空 → 原子写部署 → 端到端实跑验证 |
| BBAN 探测任务接口使用说明 | `~/Dev/Research/bban-api/Knowledge/bban-probe-task-api.md` | 查看候选池用已签名 SLB 接口 `/api/bban2/v1/all-probe-task`；候选池 ≠ miner 实际任务（受 `minerProbePercentage` 影响） |
| MCDN 探测目标与配置 | `~/Dev/Research/bban-api/Knowledge/bban-mcdn-probe-targets.md` | 判定顺序：北斗同步 service_type → 人工探测配置 → 目标 IP；配置键用 BA 节点 ID 不用主机名 |
| 灰度放量记录 | `~/Dev/Research/manba-bi/Knowledge/mcdn-vod-probe-config-rollout.md` | 246 台 mcdn-v 分三批（40/80/122）灰度；候选口径三层（874 全量 / 246 mcdn / 242 can=true）不可混 |

### 3. 现有代码中的探针指标（证据）

- `app/admin/internal/service/prom_metrics.go:638-743`：`bban2_probe_source_type{source,type}`（noded/miner/none × tcp/snmp/icmp 节点数）
- `prom_metrics.go:985-1006`：`bban2_dialing_tcp_rtt_ms`、`bban2_dialing_tcp_loss_rate`、`bban2_dialing_http_speed_mbps`（Go 服务内建 promauto）
- `prom_metrics.go:505-515`：`bban2_fuse2_node_info` / `bban2_fuse2_ability_info`（节点能力可用率）

---

## 二、探测任务下发监控方案设计

### 2.1 监控目标与链路拆解

监控对象是「探测任务下发」全链路，四段都要有指标：

```text
① 候选池构建 → ② 抽样下发 → ③ noded 领取/执行 → ④ 结果上报/存储
   (admin probe.go)      (percentage)      (bi/noded)       (Redis/Taishan)
```

**监控核心矛盾**：候选池数量 ≠ 实际下发任务数量 ≠ 有结果的节点数量。三者比例关系本身就是最重要的监控信号（知识库踩坑三、bban-probe-task-api 均强调）。

### 2.2 指标设计（按链路四段）

| 链路段 | 指标名（建议） | 类型 | 标签 | 说明 |
| --- | --- | --- | --- | --- |
| ① 候选池 | `bban2_probe_candidate_total` | Gauge | `node_type`(mcdn-v/ncdn/ec) | 候选池规模；每轮任务生成时更新 |
| ② 下发 | `bban2_probe_dispatch_total` | Gauge | `node_type` | 实际生成任务数（`all-probe-task` 口径），与候选池对比算覆盖率 |
| ② 下发 | `bban2_probe_dispatch_percentage` | Gauge | - | `minerProbePercentage` 配置值，抽样比例漂移时可见 |
| ③ 领取 | `bban2_probe_task_fetch_total` | Counter | `node_type` | noded `GET /v1/task` 领取次数 |
| ④ 上报 | `bban2_probe_result_report_total` | Counter | `source`(MinerChannel) | noded `POST /v1/taskresult` 上报次数 |
| ④ 存储 | `bban2_probe_result_freshness_seconds` | Gauge | `node_type` | `now() - report_timestamp`，结果新鲜度，链路延迟的代理指标 |
| ④ 覆盖 | `bban2_probe_result_cover_ratio` | Gauge | `probe_type` | 有结果节点数 / 下发任务节点数；任务多但结果少 = 执行失败 |
| 质量 | `mcdn_probe_tcp_loss_rate` 等 | Gauge | `instance_name,source,port` | 已有指标（知识库已落地），直接复用，不改 schema |

### 2.3 PromQL 告警规则示例

```promql
# 1. 下发量骤降 / 下发为空（可能是 Taishan service_type 查询降级把 mcdn 跳过）
(sum(bban2_probe_dispatch_total{node_type="mcdn-v"}) / sum(bban2_probe_candidate_total{node_type="mcdn-v"})) < 0.5

# 2. 结果新鲜度超阈值（链路中断：noded 没领取或上报卡住）
max(bban2_probe_result_freshness_seconds{node_type="mcdn-v"}) > 300

# 3. 有任务但无结果（覆盖率为 0 或骤降）
sum(bban2_probe_result_cover_ratio) < 0.9

# 4. 单节点丢包率告警：必须先聚合同节点多个探测目标，禁止单目标直接判定
max by (instance_name) (avg(mcdn_probe_tcp_loss_rate)) > 0.2

# 5. 采集新鲜度（指标本身是否还有人在写，防脚本/采集挂了）
absent_over_time(mcdn_probe_tcp_rtt_ms[5m]) == 1
```

### 2.4 告警设计原则（直接来自知识库踩坑，必须遵守）

1. **聚合先行，单点不判**：单探测目标的异常不能直接推断节点故障，先 `by (instance_name)` 聚合多目标再告警（mcdn-promql-monitoring）。
2. **区分「数据源选错」与「阈值过高」**：PromQL 返回空时不能直接当无数据告警，先确认 datasource_id 正确（mcdn 指标在 datasource=74，76 不含任何 mcdn 指标）。
3. **候选池 ≠ 实际任务 ≠ 有结果**：三者数量差是设计如此（只有人工配置过 ProbeConfig 的节点才有任务），不能把「任务少」当异常；要用比例漂移做告警而非绝对值。
4. **阈值不拍脑袋**：单次采样分布（如 >20 命中 0 个）不能当长期常量，阈值必须基于时间窗口统计后确定。
5. **基数控制**：新增查询类监控脚本时用稳定的指标路径 / `PathRemap`，避免动态查询路径进入 Moni HTTP 客户端指标标签导致基数超限。
6. **查询规范**：Hawkeye OpenAPI 请求必须禁代理（`--noproxy '*'`）、`Authorization` 用 JWT、token 不写入知识库与日志。
7. **标识符体系对齐**：BBAN 内部 id（如 `mcdn-ydy-sxxa-ct-50059223`）与 Grafana 模板变量 `instance_name`（hostname 风格）不可互推，指标身份标签必须先做映射（mcdn_probe.py 踩坑二）。

### 2.5 落地建议（两条技术路线，按数据源选）

- **路线 A（服务内建）**：候选池/下发/领取/上报指标可直接在 `admin`（Go）用 `promauto` 内建 Gauge/Counter，参考 `prom_metrics.go` 既有模式，随服务发布，最省事。
- **路线 B（textfile collector）**：若指标数据源是外部 REST 接口（如 `/v0/all-probe-task`），用独立脚本 + node_exporter textfile collector，严格走知识库七步工作流（实测响应结构 → 鉴权 → 标识符映射 → schema 判空 → 原子写 → 端到端验证），并注意目标环境可能是 Python 3.5 老语法。
- 结果质量指标（`mcdn_probe_*`）已由 `mcdn_probe.py` 落地，本次方案不重复造，直接在其 schema 上叠加链路四段指标即可。

---

## 三、关键未决假设（无法仅凭知识库确认）

- `minerProbePercentage` 实际配置值及 8 台 miner 机器的当前在线状态，需读 paladin 配置与运行数据确认，本方案按「抽样比例可观测」设计而非硬编码。
- 生产环境是否有 miner noded 连接 prod admin（pre 无 `[GenerateSimplifyTask]` 日志），端到端链路是否已生效，影响领取/上报两段指标的可用性判断。
- 告警阈值（覆盖率 0.5/0.9、新鲜度 300s）为初始建议值，需上线后按真实数据分布校准。

## 四、复用知识条目

- `~/Dev/Research/manba-bi/Knowledge/mcdn-promql-monitoring.md`
- `~/Dev/Research/bban-api/Knowledge/mcdn-probe-prometheus-exporter.md`
- `~/Dev/Research/bban-api/Knowledge/json-to-prometheus-textfile-workflow.md`
- `~/Dev/Research/bban-api/Knowledge/mcdn-v-probe-task-system.md`
- `~/Dev/Research/bban-api/Knowledge/bban-probe-task-api.md`
- `~/Dev/Research/bban-api/Knowledge/bban-mcdn-probe-targets.md`
- `~/Dev/Research/bban-api/Sources/Docs/hawkeye-prometheus-openapi.md`
- `~/Dev/Research/bban-api/Sources/Docs/moni-http-client-metric-cardinality.md`
