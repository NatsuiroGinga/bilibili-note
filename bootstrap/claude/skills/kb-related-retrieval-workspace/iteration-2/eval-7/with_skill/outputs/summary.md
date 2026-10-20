---
kind: eval-output
task: 探测任务下发的监控方案设计
skill: kb-related-retrieval
date: 2026-08-27
---

# 知识库检索：moni / promql / exporter

## 检索结果

- mcdn-v-probe-task-system（bban-api/Knowledge/mcdn-v-probe-task-system.md）
  - 摘要：mcdn-v 探测任务三层体系：候选池（isMcdnVodProbeTarget：IsMCDN + SID + service_type=="v"）-> 确定性抽样下发 GenerateProbeTaskForMinerNoded(percentage) -> noded GET /v1/task 领取 / POST /v1/taskresult 上报。**下发路径对 Taishan 查询失败静默降级（mcdn 被跳过、ncdn 不受影响），结果查询路径严格报错不降级（容错不对称）**。候选池数量 != 实际下发任务数（还取决于 MySQL bban_probe_config 是否有配置）。结果存 Redis/Taishan（bban_probe_kv，key {bban2_probe_result:<nodeID>}$<type>$<source>），Source 是 miner 渠道（如 OSTALIWEST）。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md

- mcdn-probe-prometheus-exporter（bban-api/Knowledge/mcdn-probe-prometheus-exporter.md）
  - 摘要：MCDN 质量监控是**三套互不相干体系**（A 探测任务结果 / B 拨测 / C 跨运营商丢包率），命名相似但数据源、存储、Prometheus 出口全不同。
  体系 A 用 mcdn_probe.py（textfile collector，cron 原子写 .prom，node_exporter 读取）补上 mcdn_probe_* 指标出口，只暴露 instance_name 标签。
  踩坑：中心化监控机脚本自打节点身份；BBAN id != hostname 需 schedule 映射；bvc-hub 网关要登录态但 /v0 内网直连无鉴权；{code,message,ttl,data} 壳解包。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-probe-prometheus-exporter.md

- mcdn-promql-monitoring（manba-bi/Knowledge/mcdn-promql-monitoring.md）
  - 摘要：Hawkeye OpenAPI 查询方法（即时 /report/api/v2/query/datasource/{id}?query=，范围 /query_range + start/end/step，JWT Authorization 头，5 QPS 上限，必须禁用代理）。
  mcdn_network_quality 在 **datasource 74**（非 76 非 29）。查询返回空必须区分「数据源选错」与「阈值过高」。go-op pkg/moni/core.go 已有 Hawkeye 客户端（datasource 29）。
  - 跳转：obsidian://open?vault=Research&file=manba-bi/Knowledge/mcdn-promql-monitoring.md

- json-to-prometheus-textfile-workflow（bban-api/Knowledge/json-to-prometheus-textfile-workflow.md）
  - 摘要：REST JSON -> Prometheus 指标的七步清单（技术路线判断 -> 实测响应结构 -> 确认鉴权层级 -> 对齐标识符体系 -> 判空防御 -> cron+原子写 -> 端到端实跑）。数据源已在 Go 服务内用 promauto；数据源是外部 REST API 用脚本 + textfile collector。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/json-to-prometheus-textfile-workflow.md

- moni-http-client-metric-cardinality（bban-api/Sources/Docs/moni-http-client-metric-cardinality.md）
  - 摘要：go-common HTTP 客户端默认生成 Moni 监控与 Trace；路径值不固定会形成高基数指标，长期运行指标超限+内存上涨。解决：聚合 Metric URL、RESTfulGet 模板路径、PathRemap/HostRemap。新增查询客户端时路径须稳定。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Sources/Docs/moni-http-client-metric-cardinality.md

- hawkeye-prometheus-openapi / hawkeye-prometheus-datasource-query（bban-api/Sources/Docs/）
  - 摘要：Hawkeye 生产 http://hawkeye.bilibili.co，UAT http://uat-hawkeye.bilibili.co；即时查询参数 query，范围查询 start/end/step（实施时应显式传 step）；响应 value（vector）/ values（matrix）；curl 需 URL 编码；Grafana UID 与 Hawkeye datasource_id 不可互转。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Sources/Docs/hawkeye-prometheus-openapi.md

- bban-probe-task-api（bban-api/Knowledge/bban-probe-task-api.md）
  - 摘要：查看目标是否进候选池用已签名 SLB /api/bban2/v1/all-probe-task 精确匹配节点 ID；未命中只能说明未进当前候选池；不要把候选池当 miner 实际任务（还受 minerProbePercentage 影响）。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/bban-probe-task-api.md

- mcdn-vod-probe-config-rollout（manba-bi/Knowledge/mcdn-vod-probe-config-rollout.md）
  - 摘要：批量配置灰度 246 台 mcdn-v（icmp=false/snmp=false/vod_play=true/tcp_ports=[80,443]），分批 40/80/122，固定种子可复现。批间观察点：mcdn_probe_tcp_rtt_ms/loss_rate 四路 miner 渠道均开始产出、值合理、*_report_timestamp 新鲜度正常、miner 主机无 CPU/fd 异常——可复用为灰度健康门禁模板。
  - 跳转：obsidian://open?vault=Research&file=manba-bi/Knowledge/mcdn-vod-probe-config-rollout.md

- te-model-registry-and-config / te-mcdn-bandwidth-waterline（te/Knowledge/）
  - 摘要：te 框架企微告警统一出口 WriteChangeCube(c.PropertyPostMsgEvent, entity, msg, c.LayerPostMsg, extra, conf.Config.ThirdRelevant.NoticeWebhook, logId)；三参数组合是发企微标志。水位线例子：MCDN 用 hostname 前缀 mcdn 分流 + 独立阈值，超阈直接发企微绕过下游 change cube 链路。
  - 跳转：obsidian://open?vault=Research&file=te/Knowledge/te-model-registry-and-config.md

- bban-taishan-probe-mapping（bban-api/Knowledge/bban-taishan-probe-mapping.md）
  - 摘要：service_type 与探测结果读写源由配置开关 serviceFromTaishan/qosFromTaishan 决定（Taishan bban_probe_kv V2 key / Redis HSET 双写）；探测配置存 MySQL bban_probe_config（node_id+dtime=0）；Taishan 无原生 HGETALL，ba 用 SCAN 分页封装。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping.md

## 关联文档

- mcdn-v-probe-task-system 出链（5）：bban-probe-task-api、bban-mcdn-probe-targets、et-bban-probe-design-docs、mcdn-probe-prometheus-exporter、json-to-prometheus-textfile-workflow
- mcdn-v-probe-task-system 入链（重点）：mcdn-probe-prometheus-exporter、bban-node-status-silent-success、bban-node-field-semantics、bban-taishan-probe-mapping
- mcdn-probe-prometheus-exporter 入链：mcdn-cross-isp-packet-loss、mcdn-promql-monitoring、mcdn-vod-probe-config-rollout、bban-node-field-semantics
- mcdn-promql-monitoring 入链：mcdn-probe-prometheus-exporter、Daily/2026-08-21
- 图扩展（depth=2 可达）：bban-signature-body-coverage（POST body 签名）、bban-node-field-semantics、mcdn-cross-isp-packet-loss（体系 C exporter）、mcdn-设备交付全链路（五仓库基线）

---

# 探测任务下发监控方案设计

## 一、监控对象与链路

探测任务下发是 6 段链路，每段断链都应有独立信号：

```text
① 候选池构建  isMcdnVodProbeTarget(IsMCDN+SID+service_type=="v") + MySQL bban_probe_config
② 抽样下发    GenerateProbeTaskForMinerNoded(percentage)  确定性抽样 sort+取前 ceil
③ noded 领取  GET /v1/task（仅 miner 节点）
④ noded 执行  miner 云主机裸连 URL/ffmpeg（HTTP 不读 TargetIP）
⑤ 结果上报    POST /v1/taskresult
⑥ 结果存储    配置开关决定 Redis(HSET) 或 Taishan(bban_probe_kv)
⑦ 指标出口    mcdn_probe.py(textfile) / prom_metrics.go(promauto)
```

监控核心价值是捕获三个知识库确认的**静默风险**：

1. **下发路径 Taishan 失败静默降级**（mcdn 被跳过、ncdn 不受影响，probe.go:152-157）——不主动暴露计数则完全无感知。
2. **候选池 != 实际任务数**（需 bban_probe_config 有记录，实测 1334 候选仅 1 条 mcdn 任务）——用候选池做告警基线必误报。
3. **结果新鲜度是最终断链信号**（noded 不拉/不执行/不上报都会体现为 report_timestamp 过期）。

## 二、指标分层设计

### 第 1 层：下发侧——admin 服务内建 promauto（改 prom_metrics.go，最小侵入）

| 指标名 | 类型 | 标签 | 含义 / 告警用途 |
| --- | --- | --- | --- |
| bban2_probe_candidate_total | Gauge | node_type=mcdn\|ncdn\|ec | 候选池节点数（只做趋势面板，不作告警基线，因 != 实际任务） |
| bban2_probe_config_covered_total | Gauge | node_type | 有 ProbeConfig 的节点数（任务基线的正确口径，mcdn-v 期望约 246） |
| bban2_probe_dispatch_total | Counter | node_type, probe_type | 实际生成下发的任务数（含抽样后） |
| bban2_probe_taishan_svc_type_degraded_total | Counter | - | 下发路径 Taishan 查询失败降级次数（静默风险，必须显式暴露） |
| bban2_probe_taskresult_received_total | Counter | node_type | 收到 /v1/taskresult 上报数 |
| bban2_probe_result_query_error_total | Counter | - | 结果查询路径严格错误次数（容错不对称的另一半） |
| bban2_probe_result_max_report_ts | Gauge | node_type, probe_type | 最新结果上报时间戳，用于新鲜度计算 |

### 第 2 层：结果侧——复用已有 mcdn_probe.py textfile 出口（体系 A）

已有指标直接用，重点补"新鲜度"维度，而不是再造一套：

```promql
# 结果新鲜度：最新上报距现在多久
time() - mcdn_probe_tcp_report_timestamp{instance_name=~"$instance_name"}
# 多路 miner 渠道覆盖：正常应看到 OSTALIWEST/OSTHWNORTH/OSTTXEAST/OSTTXSOUTH
count by (instance_name) (mcdn_probe_tcp_rtt_ms)
```

### 第 3 层：告警出口——te 框架企微统一出口

复用 WriteChangeCube(c.PropertyPostMsgEvent, ...) 三参数组合发企微；若走 manba-bi/Blink 则复用 go-op moni 客户端与 --apply/--restore 快照模式。不在中间层打日志，告警消息统一在顶层生成。

## 三、PromQL 告警规则（建议阈值 + 判定）

| 规则 | PromQL | 触发含义 |
| --- | --- | --- |
| R1 结果断链 | time() - max by (instance_name) (mcdn_probe_tcp_report_timestamp) > 120 | noded 未领取/未执行/未上报 |
| R2 配置覆盖率骤降 | bban2_probe_config_covered_total{node_type="mcdn"} < 0.9 * 期望基线(246) | 批量配置被误改/回滚 |
| R3 Taishan 降级 | increase(bban2_probe_taishan_svc_type_degraded_total[10m]) > 0 | 下发静默跳过 mcdn |
| R4 下发率异常 | bban2_probe_dispatch_total / clamp_min(bban2_probe_config_covered_total,1) < 0.5 | 抽样/判定链异常 |
| R5 结果查询严格错误 | increase(bban2_probe_result_query_error_total[10m]) > 0 | 结果路径故障（应 fail 而非降级） |
| R6 miner 渠道覆盖缺失 | count by (instance_name) (mcdn_probe_tcp_rtt_ms) < 4 | 某 miner 渠道断 |

> 阈值全部是**建议初值**，需按灰度观察点（mcdn-vod-probe-config-rollout 批间门禁）用真实数据校准，禁止直接当长期常量。

## 四、实现顺序（最小可证伪路径）

1. 先加第 1 层 7 个 in-service 指标（只改 prom_metrics.go + probe.go 上报点，不碰对外接口）。
2. 用 mcdn_probe_config_batch.py 灰度批次做**对照实验**：放量一批后看 dispatch/report 指标上升、新鲜度正常——验证指标能反映下发行为变化。
3. 接 R1/R3（最便宜且覆盖最大静默风险），再补 R2/R4。
4. 接第 3 层企微出口，告警消息带 instance_name + 节点类型，禁用代理、稳定 metric path。

## 五、必须遵守的知识库约束（踩坑清单）

- **告警基线用 config_covered_total，禁止用候选池**（候选池 != 任务数）。
- **标识符体系**：指标只暴露 instance_name，不暴露 BBAN id；如需 id 需 schedule 映射。
- **HTTP 客户端指标基数**：admin 新增 Hawkeye/Taishan 查询客户端时用稳定 metric path / PathRemap，防高基数。
- **datasource 选择**：查 mcdn_network_quality 用 74（非 76/29）；范围查询显式传 step；返回空先分「数据源选错 vs 阈值过高」。
- **代理**：所有请求 trust_env=False / curl --noproxy '*'。
- **textfile 部署**：cron `> file.$$ && mv` 原子写；目标环境 Python 3.5 禁新语法；单文件独立部署禁仓库相对路径依赖。
- **判空与单位**：外部 JSON 字段可能 null（未开启探测项 != 异常），判空跳过；比率计算分母判 0；单位体现在指标名后缀。

## 六、待验证假设

- instance_name 是否会被云端 crond/采集环境自动注入——知识库**不确认**该说法，方案默认脚本自打标签，不依赖环境注入。
- 第 1 层各指标建议阈值需在 prod 发布后（pre 无生产 noded 连接）用真实数据校准。
- {nodeId}.bilivideo.com 播放地址是否真被 CDN 调度到对应节点，是 Hebe 侧黑盒，不影响下发链路监控但影响 VodPlay 结果解读。

## 图谱提示

以上检索结果与关联文档可在 Obsidian Graph View 中查看可视化图谱（打开 ~/Dev/Research vault，点左侧图谱图标），核心节点：mcdn-v-probe-task-system -> mcdn-probe-prometheus-exporter -> mcdn-promql-monitoring 构成主链路；moni-http-client-metric-cardinality 与 hawkeye-* 是监控基础设施约束；te-model-registry-and-config 是告警出口。

