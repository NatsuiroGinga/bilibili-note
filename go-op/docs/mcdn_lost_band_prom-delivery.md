---
title: mcdn_vanished_bandwidth 交付格式
date: 2026-07-13
tags:
  - go-op
  - MCDN
  - 带宽
  - Prometheus
  - 类型/交付
related:
  - "[[investigation-plan-reserve-bw-drop]]"
  - "[[go-op MOC]]"
---

# mcdn_vanished_bandwidth 交付格式

## 指标

```
mcdn_vanished_bandwidth
```

**类型**：Gauge（每分钟覆盖一次）  
**单位**：Mbps（`total_bandwidth` 原始值，与 `mcdn_network_mcdn_all` 同单位）  
**含义**：本轮消失（或带宽缩减）节点的 `total_bandwidth` 之和

## 标签

| 标签 | 含义 | 示例值 |
|------|------|--------|
| `country` | 国家 | `"中国"` |
| `region` | 大区 | `"东北"` `"华中"` `"华东"` |
| `factory` | 厂商 | `"ydy"` `"tt"` `"wx"` `"jd"` |
| `operator` | 运营商 | `"电信"` `"联通"` `"移动"` |
| `province` | 省份 | `"黑龙江"` `"河南"` `"广东"` |
| `type` | 节点类型 | `"点播"` `"直播"` `"mp2sp"` `"bstar"` `"点直混部"` `"mnet"` |
| `service_type` | 调度范围 | `"global"`（固定） |
| `real_isp` | 实际 ISP | `"电信"` `"联通"` `"移动"` |
| **`reason`** | **消失原因（核心）** | **`stop` `loss` `gone` `degraded`** |

## `reason` 枚举

| 值 | 含义 | 判定逻辑 |
|----|------|---------|
| `stop` | 踢点下线 | 节点消失 + pcdn API 查到的 `is_disabled=true` |
| `loss` | 心跳失联 | 节点消失 + pcdn API 查到的 `is_disabled=false` |
| `gone` | 已彻底删除 | 节点消失 + pcdn API 查不到（被重建/重新交付） |
| `degraded` | 带宽缩减 | 节点在线但 `total_bandwidth` 比上一轮少（编排降量） |

## 标签与 `mcdn_network_mcdn_all` 对应关系

除 `reason` 外，所有标签名和值完全一致。Grafana 可对两者做标签匹配：

```promql
# 在线储备
mcdn_network_mcdn_all{country="中国",region="华中",factory="wx",operator="联通",
  province="河南",type="mp2sp",service_type="global",real_isp="联通"} 11000

# 该节点消失（踢点下线）
mcdn_vanished_bandwidth{country="中国",region="华中",factory="wx",operator="联通",
  province="河南",type="mp2sp",service_type="global",real_isp="联通",reason="stop"} 11000
```

## 输出样本

无变化时（兜底零值）：
```
mcdn_vanished_bandwidth{country="中国",factory="",operator="",province="",real_isp="",reason="stop",region="",service_type="global",type="点播"} 0
```

有变化时：
```
mcdn_vanished_bandwidth{country="中国",factory="wx",operator="联通",province="河南",real_isp="联通",reason="stop",region="华中",service_type="global",type="mp2sp"} 6
mcdn_vanished_bandwidth{country="中国",factory="wx",operator="联通",province="河南",real_isp="联通",reason="stop",region="华中",service_type="global",type="mp2sp"} 5
```

## Grafana 用法

所有查询与在线储备带宽使用完全相同的过滤条件（factory/region/province/operator/real_isp 列表）。对比在线储备，只需把指标名从 `mcdn_network_mcdn_all` 换成 `mcdn_vanished_bandwidth`，并加上 `reason` 标签。

```promql
# BVC 踢点带宽（stop）
sum(mcdn_vanished_bandwidth{type=~"点播",factory=~"(bdwl|bili|jd|jk|jkwl|jny|lfy|ppio|qny|tt|wx|xd|ydy|ydzd)",region=~"(东北|华东|华中|华北|华南|西北|西南)",province=~"(上海|云南|内蒙古|北京|吉林|四川|天津|宁夏|安徽|山东|山西|广东|广西|新疆|江苏|江西|河北|河南|浙江|海南|湖北|湖南|甘肃|福建|贵州|辽宁|重庆|陕西|青海|黑龙江)",operator=~"(电信|移动|联通)",service_type=~"global",real_isp=~"(电信|移动|联通)",reason="stop",zone="sh031"})

# BVC 失联带宽（loss）
sum(mcdn_vanished_bandwidth{...,reason="loss",zone="sh031"})

# BVC 已删除（gone）
sum(mcdn_vanished_bandwidth{...,reason="gone",zone="sh031"})

# BVC 编排降量（degraded）
sum(mcdn_vanished_bandwidth{...,reason="degraded",zone="sh031"})
```

归因闭合（与在线储备带宽对比）：

```promql
# 在线储备带宽
sum(mcdn_network_mcdn_all{type=~"点播",factory=~"(bdwl|bili|jd|jk|jkwl|jny|lfy|ppio|qny|tt|wx|xd|ydy|ydzd)",region=~"(东北|华东|华中|华北|华南|西北|西南)",province=~"(上海|云南|内蒙古|北京|吉林|四川|天津|宁夏|安徽|山东|山西|广东|广西|新疆|江苏|江西|河北|河南|浙江|海南|湖北|湖南|甘肃|福建|贵州|辽宁|重庆|陕西|青海|黑龙江)",operator=~"(电信|移动|联通)",service_type=~"global",real_isp=~"(电信|移动|联通)",zone="sh031"})

# 消失带宽（按原因分组）
sum(mcdn_vanished_bandwidth{type=~"点播",...,zone="sh031"}) by (reason)
```

在线储备下降 ≈ sum(stop + loss + gone + degraded)，单位 Mbps，除以 1000 转 Gbps。

## 部署

| 项目 | 值 |
|------|-----|
| 脚本路径 | `/data/cdn_tools/mcdn_lost_band_prom.py` |
| cron 频率 | 每分钟 |
| 输出文件 | `/usr/local/prometheus/node_exporter_textfile_directory/mcdn_lost_band.prom` |
| 数据源 API | `mcdn-data.biliapi.net/api/v1/portal/mcdn/all/nodes` |
| 快照文件 | `/tmp/mcdn_lost_band_snapshot.json`（内部用，每次覆盖） |
