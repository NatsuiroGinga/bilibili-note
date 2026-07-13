---
title: MCDN 带宽埋点需求文档
date: 2026-07-02
tags:
  - go-op
  - MCDN
  - 带宽
  - 监控
  - Prometheus
related:
  - "[[mcdn_lost_band_prom-delivery]]"
  - "[[go-op MOC]]"
---

# MCDN 带宽埋点需求文档

> **任务**：新增 Prometheus 指标辅助储备带宽下降归因
> **实现方式**：**新建采集脚本**（放 `.claude/scripts/moni/`，加入 `mcdn_moni_cron`），走 textfile + node_exporter
> **约束**：**不修改任何现有脚本**（`mcdn_offlin_info.py`、`mcdn_networkv4.py` 等已有大盘消费，改它们会影响线上），只新增

---

## 一、背景

7/1 BVC 在线储备带宽全天下降：636 → 474 Gb/s（最低 -162 Gb/s），23:59 回升至 513 Gb/s（仍低 123 Gb/s）。

数据文件：`.claude/logs/储备带宽-data-2026-07-02 17_14_10.csv`，1 分钟粒度，覆盖 7/1 00:00~23:59。

排查已确认 manba-bi 踢点次数（70 次）和 p_instances 心跳失联台数（7 台）量级都不够，**次数无法解释带宽流失，必须上带宽维度埋点**。

---

## 二、监控大盘数据源（已确认）

### 数据链路

```text
cron (mcdn_moni_cron) → python 脚本 → .prom 文件 → node_exporter textfile → Prometheus → Grafana
```

### 三个关键指标及其脚本

| 指标 | 脚本 | 数据源 API | 带宽字段 |
|------|------|-----------|---------|
| `mcdn_network_mcdn_all`（在线储备带宽） | `mcdn_networkv4.py` | `mcdn-data.biliapi.net/api/v1/portal/mcdn/all/nodes` | `total_bandwidth` |
| `mcdn_offlin_info{offline_type="stop"}`（停用带宽） | `mcdn_offlin_info.py` | `portal.bilibili.co/api/v1/portal/pcdn` | `lines * line_cap` |
| `mcdn_offlin_info{offline_type="loss"}`（失联带宽） | `mcdn_offlin_info.py` | `portal.bilibili.co/api/v1/portal/pcdn` | `lines * line_cap` |

停用带宽大盘 PromQL（按厂商分组）：

```promql
sum(mcdn_offlin_info{type=~"点播",factory=~"(bdwl|bili|jd|jk|jkwl|jny|lfy|ppio|qny|tt|wx|xd|ydy|ydzd)",region=~"(东北|华东|华中|华北|华南|西北|西南)",province=~"(上海|云南|内蒙古|北京|吉林|四川|天津|宁夏|安徽|山东|山西|广东|广西|新疆|江苏|江西|河北|河南|浙江|海南|湖北|湖南|甘肃|福建|贵州|辽宁|重庆|陕西|青海|黑龙江)",operator=~"(电信|移动|联通)",offline_type=~"stop",zone="sh031"}) by (factory) /1000
```

`/1000`：`mcdn_offlin_info.py` 输出的是 Mbps（`lines * line_cap`），除以 1000 转为 Gbps。

Grafana 大盘 PromQL：

```promql
sum(mcdn_network_mcdn_all{type=~"点播",factory=~"(bdwl|bili|jd|jk|jkwl|jny|lfy|ppio|qny|tt|wx|xd|ydy|ydzd)",region=~"(东北|华东|华中|华北|华南|西北|西南)",province=~"(上海|云南|内蒙古|北京|吉林|四川|天津|宁夏|安徽|山东|山西|广东|广西|新疆|江苏|江西|河北|河南|浙江|海南|湖北|湖南|甘肃|福建|贵州|辽宁|重庆|陕西|青海|黑龙江)",operator=~"(电信|移动|联通)",service_type=~"global",real_isp=~"(电信|移动|联通)",zone="sh031"})
```

其中 `type="点播"` 对应 BVC（`-v-`）节点，`service_type="global"` 来自 `sched_scope` 字段，`zone="sh031"` 限定单个 zone。

---

## 三、口径错位（归因脱节的根因）

现有 stop/loss 指标无法完整解释储备带宽下降，原因是两重口径错位：

### 1. 数据源 API 不同

- 储备带宽来自 mcdn-data 服务的 `/mcdn/all/nodes`
- 停用/失联来自 portal 服务的 `/api/v1/portal/pcdn`

两个服务读同一个 `p_instances` 表，但各自有缓存、各自判定在线。同一节点同一时刻，mcdn-data 可能认为在线、portal 可能认为失联，状态不同步。

### 2. 在线/失联阈值三重不一致

| 判定方 | 阈值 | 来源 |
|--------|------|------|
| portal（go-op 项目） | 3 分钟 | `app/portal/internal/dao/mcdn.go:14`（`time.ParseDuration("-3m")`） |
| `mcdn_offlin_info.py` loss | 10 分钟（600 秒） | 脚本第 48 行 |

节点停止上报后的时间线：

```
0~3min：两方都算在线
3~10min：portal 摘了，loss 还没记 → 储备带宽可能已下降，但 loss 没变化
>10min：loss 才记上
```

**6~10 分钟窗口是归因盲区**：储备带宽已下降，但 stop 没进（没踢点）、loss 没进（没超 10 分钟）。

---

## 四、7/1 归因匹配分析（每小时对齐）

停用/失联数据每小时更新一次，按整点对齐后归因关系如下：

### 每小时对照表

| 时间 | 储备 | 停用Σ | 失联Σ | 停+失 | 总 (= 储备+停+失) | 总Δ |
|------|------|------|------|------|------|------|
| 00:00 | 636 | 487 | 27 | 514 | 1150 | 基准 |
| 01:00 | 566 | 487 | 27 | 514 | 1080 | -70 ⚠️ |
| 02:00 | 616 | 547 | 37 | 584 | 1200 | +50 |
| 03:00 | 616 | 497 | 37 | 534 | 1150 | 0 |
| 04:00 | 626 | 497 | 37 | 534 | 1160 | +10 |
| 08:00 | 596 | 497 | 37 | 534 | 1130 | -20 |
| 09:00 | 576 | 527 | 45 | 572 | 1148 | -2 |
| 12:00 | 547 | 562 | 68 | 630 | 1177 | +27 |
| 14:00 | 538 | 614 | 81 | 695 | 1233 | +83 ⚠️ |
| 16:00 | 500 | 531 | 81 | 612 | 1112 | -38 |
| 18:00 | 471 | 587 | 73 | 660 | 1131 | -19 |
| 20:00 | 521 | 549 | 73 | 622 | 1143 | -7 |
| 23:00 | 498 | 593 | 73 | 666 | 1164 | +14 |

### 关键结论

1. **三者的和基本守恒**：`储备 + 停用 + 失联` 在 1150 附近波动，范围 1080～1233（±80）。这一波动可归因于 `total_bandwidth`（储备）与 `lines*line_cap`（停+失）的口径差异，以及两个 API 的缓存不同步。

2. **00:28 的 -94 暴跌在对齐后被平滑**：整点 01:00 储备 -70，停+失不变。小时粒度无法捕捉 2 分钟级的短时失联——这正是新脚本 `mcdn_lost_band_prom.py`（每分钟粒度）要解决的问题。

3. **停用带宽是下降的主因**：12:00-14:00 停用从 562 → 614（+52），对应储备从 547 → 538（-9）。储备底部（18:00=471）时停用（587）占总量近一半。

---

## 五、需求：新建同源口径脚本

### 目标

新建一个脚本，用**与储备带宽同源同口径**的方式统计失联带宽和停用带宽，使归因等式成立：

```
在线储备 = 全部节点 - 停用 - 失联 - 其他（编排降量等）
```

### 同源口径设计

| 维度 | 选择 | 理由 |
|------|------|------|
| 数据源 API | `/mcdn/all/nodes`（mcdn-data） | 与储备带宽同源 |
| 带宽字段 | `total_bandwidth` | 与储备带宽同字段 |
| 节点集合 | 该 API 返回的全部节点 | 含在线+离线 |

### 新脚本：`mcdn_lost_band_prom.py`（待实现）

**核心思路**：`/mcdn/all/nodes` 返回的节点里，对比上一轮快照，找出本轮消失的节点（失联）和新增的节点（恢复），用 `total_bandwidth` 累加。

```text
每轮（每分钟）：
  1. 调 /mcdn/all/nodes，取所有 type=v 节点 → {node_name: total_bandwidth}
  2. 读上一轮快照（本地 JSON）
  3. 失联节点 = 旧快照有、本轮无的节点
  4. 失联带宽 = Σ 失联节点的 total_bandwidth / 1000（Gbps）
  5. 输出 Gauge: mcdn_lost_band_v2_gbps{type="点播"} = 失联带宽
  6. 写回本轮快照（原子 mv）
```

### 指标设计

```text
# 与储备带宽同源同口径的失联带宽
mcdn_lost_band_v2_gbps{type="点播"} 56.78
```

- **类型**：Gauge
- **单位**：Gbps（`total_bandwidth / 1000`，与 `mcdn_network_mcdn_all` 一致）
- **标签**：`type`（点播/直播/...）
- **指标名带 `_v2`**：避免与现有 `mcdn_offlin_info{offline_type="loss"}` 混淆

### 注意事项

- **不改现有脚本**：`mcdn_offlin_info.py` 的 stop/loss 继续按原口径运行，现有大盘不受影响
- **首次启动**无快照，跳过对比
- **快照并发**：写入用 `tmp + mv` 原子操作
- **与踢点去重**：失联节点中若被 manba-bi 踢点（is_disabled=true），应从失联带宽排除避免重复。但 `/mcdn/all/nodes` 返回的节点 is_disabled 状态需确认是否可用

### 加入 cron

```cron
*/1 * * * * root python3 /data/cdn_tools/mcdn_lost_band_prom.py > /usr/local/prometheus/node_exporter_textfile_directory/mcdn_lost_band.prom.$$ && mv ... mcdn_lost_band.prom
```

---

## 六、归因用法

Grafana 上对照（新脚本上线后）：

| 曲线 | 来源 |
|------|------|
| 在线储备带宽 | `sum(mcdn_network_mcdn_all{type="点播"})` |
| 失联带宽（同源） | `mcdn_lost_band_v2_gbps{type="点播"}` |
| 停用带宽（现有） | `sum(mcdn_offlin_info{offline_type="stop"}) / 1000` |

**归因逻辑**：储备下降时，同源失联带宽同步上升 → 心跳失联主导；停用带宽上升 → 踢点主导。三者同源后 `储备Δ + 失联Δ + 停用Δ ≈ 0`（全部节点带宽守恒），归因闭合。

---

## 七、附录

### 代码与脚本索引

| 内容 | 路径 |
|------|------|
| 监控 cron 配置 | `.claude/scripts/moni/mcdn_moni_cron` |
| 在线储备带宽脚本（不改） | `.claude/scripts/moni/mcdn_networkv4.py` |
| 停用/失联带宽脚本（不改） | `.claude/scripts/moni/mcdn_offlin_info.py` |
| **失联带宽脚本（新增）** | **`.claude/scripts/moni/mcdn_lost_band_prom.py`** |
| 出流量占比脚本（不改） | `.claude/scripts/moni/mcdn_get_band_prom.py` |
| 节点信息脚本（不改） | `.claude/scripts/moni/mcdn_node.py` |
| portal 心跳阈值（3 分钟） | `app/portal/internal/dao/mcdn.go:14` |
| manba-bi 踢点逻辑（仅参考） | `app/manba-bi/internal/service/service.go:759` |
| msg_data_all 表知识库 | `.claude/rules/mysql.md` |

### API 索引

| API | 服务 | 用途 |
|-----|------|------|
| `mcdn-data.biliapi.net/api/v1/portal/mcdn/all/nodes` | mcdn-data（不在项目） | 在线节点列表 + `total_bandwidth` |
| `portal.bilibili.co/api/v1/portal/pcdn` | portal（go-op） | 全部节点 + `lines`/`line_cap`/`is_disabled`/`updated_at` |
