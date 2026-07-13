---
title: MCDN 线路可用率
date: 2026-07-13
tags:
  - go-op
  - 线路可用率
  - MCDN
  - 监控
related:
  - "[[北斗资源上下线及踢点策略技术文档]]"
  - "[[mcdn-packet-loss-design]]"
  - "[[go-op MOC]]"
---

# MCDN 线路可用率

## 概述

线路可用率是衡量 MCDN 节点**实际已配置的 IP 线路数是否达标**的核心指标。每个 MCDN 节点需要一定数量的线路（IP）来承载其总带宽，线路不足会导致节点无法提供额定带宽，影响服务质量。

## 计算公式

```
线路可用率(%) = 实际 IP 数 ÷ (总带宽 ÷ 单线路带宽) × 100
```

即：

```
线路可用率(%) = len(ips) ÷ (total_bandwidth / line_bandwidth) × 100
```

| 变量 | 来源字段 | 含义 |
|------|---------|------|
| 实际 IP 数 | `len(ips)` | 当前节点已分配的 IP 地址数量 |
| 总带宽 | `total_bandwidth` | 节点额定总带宽（Mbps） |
| 单线路带宽 | `line_bandwidth` | 每条线路可承载的带宽（Mbps） |
| 理论线路数 | `total_bandwidth / line_bandwidth` | 跑满总带宽所需的线路条数 |

### 计算示例

**正常节点：**

```
total_bandwidth = 6500 Mbps
line_bandwidth  = 1300 Mbps
实际 IP 数      = 5 个
理论线路数      = 6500 ÷ 1300 = 5 条
线路可用率      = 5 ÷ 5 × 100 = 100%  ✅
```

**不足节点：**

```
total_bandwidth = 6500 Mbps
line_bandwidth  = 1300 Mbps
实际 IP 数      = 4 个
理论线路数      = 6500 ÷ 1300 = 5 条
线路可用率      = 4 ÷ 5 × 100 = 80%   ⚠️
```

**完全不可用节点：**

```
total_bandwidth = 10000 Mbps
line_bandwidth  = 10000 Mbps
实际 IP 数      = 0 个
理论线路数      = 10000 ÷ 10000 = 1 条
线路可用率      = 0 ÷ 1 × 100 = 0%    🔴
```

## 数据链路

```
MCDN 资源 API
  (mcdn-data.biliapi.net/api/v1/portal/mcdn/resource)
         │
         ▼
line_availability.py（定时执行）
         │
         ▼
Prometheus 文本格式输出 → Prometheus 采集
         │
         ├─── mcdn_lines_info{info_type="isp_lines"}  ← 线路可用率
         └─── mcdn_lines_info{info_type="ip_repeat"}   ← IP 冲突检测
         │
         ▼
告警规则 / Grafana 看板
```

## Prometheus 指标

### `mcdn_lines_info` 指标标签

| 标签 | 含义 | 示例值 |
|------|------|--------|
| `country` | 国家 | `中国` |
| `region` | 大区 | `华南`、`华东`、`华北` |
| `factory` | 厂商代码 | `bili`、`wx`、`qny`、`ppio` |
| `operator` | 运营商 | `电信`、`联通`、`移动` |
| `province` | 省份 | `广东`、`福建`、`湖北` |
| `type` | 服务类型 | `点播`、`直播`、`mp2sp`、`点直混部`、`mnet` |
| `service_type` | 调度范围 | `global`（全局调度）、`province`（省内调度） |
| `info_type` | 指标类型 | `isp_lines`（线路可用率）、`ip_repeat`（IP 冲突） |
| `mcdn_identity` | 节点唯一标识 | `mcdn-bili-gz01-dx-v-001` |

### info_type 取值说明

| info_type 值 | 含义 | 指标值 |
|-------------|------|--------|
| `isp_lines` | 线路可用率百分比 | 0~100 正常，>100 表示 IP 冗余（数据异常） |
| `ip_repeat` | IP 冲突标记 | `100` 表示该节点存在与其他节点重复的 IP |

## 告警规则

### MOB-线路可用率小于 50%-自动下线

```
PromQL:
mcdn_lines_info{info_type="isp_lines",mcdn_identity=~"mcdn-.*-mp2sp-.*"}
  + on(instance_name) group_left(app)
  hawkeye_instance_app_relation{app=~"ops.fuxi.portal-moni",product=~"服务器"}

操作符: <
阈值: 50
```

- **监控对象**：MP2SP 类型的 MCDN 节点
- **触发条件**：线路可用率低于 50%
- **告警动作**：自动下线，将节点从调度池中摘除

### 为什么线路不足要自动下线？

节点线路不足却不摘除，会导致：

1. **线路过载**：少数线路需要承载全部额定流量，单条线路跑满瓶颈，丢包率飙升
2. **用户体验劣化**：点播/直播出现卡顿、加载失败
3. **灰色故障**：节点没宕机但服务质量极差，比明确故障更难排查

**与其让残血节点硬撑，不如摘掉流量，分给线路就绪的健康节点。** 这是熔断保护策略，优先保障服务质量而非维持在线节点数量。

## 常见异常场景

| 场景 | 线路可用率 | 原因分析 |
|------|-----------|---------|
| IP 未分配 | 0% | 节点已上线但尚未分配任何 IP |
| 线路缺口 | 60%~80% | 部分 IP 未到货或配置未完成 |
| IP 冗余 | 200%~1000% | `total_bandwidth` 与 `line_bandwidth` 值相同但配了多个 IP，通常为数据配置问题 |
| IP 冲突 | `ip_repeat` = 100 | 多个节点分配到相同 IP，调度冲突 |

## 脚本执行

脚本位置：`.claude/scripts/line_availability.py`

```bash
python3 .claude/scripts/line_availability.py
```

当前（2026-06-24）运行结果摘要：

- 在线节点总数：约 1,183 个
- 线路可用率 100%：约 1,148 个（97%）
- 线路可用率异常：约 35 个（3%）
- IP 冲突：0 个
