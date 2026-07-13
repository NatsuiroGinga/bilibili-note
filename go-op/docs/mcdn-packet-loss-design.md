---
title: MCDN 节点丢包率指标与告警
date: 2026-06-23
tags:
  - go-op
  - 丢包率
  - MCDN
  - 监控
  - 告警
related:
  - "[[北斗资源上下线及踢点策略技术文档]]"
  - "[[line-availability]]"
  - "[[mcdn-cross-isp-ping-change-summary]]"
  - "[[go-op MOC]]"
---

# MCDN 节点丢包率指标与告警

> 记录于 2026-06-23，更新于 2026-06-25。

## 完整流程

每台 MCDN 节点上跑着一个 cron 脚本，每分钟执行以下步骤：

### 1. 判断节点类型，选不同的 ping 目标

```text
读 /etc/type 文件：
  非 Bstar → ping 百度 + 淘宝（国内节点，测国内公网质量）
  Bstar   → ping Google + B 站（海外节点，测国际公网 + 回源质量）
```

### 2. 每个目标独立探测，发 100 个包算丢包率

```text
ping -i 0.1 -W 1 -c 100 www.baidu.com
  → 发了 100 个 ICMP 包，回了 95 个 → 丢包率 5%

ping -i 0.1 -W 1 -c 100 www.taobao.com
  → 发了 100 个包，回了 97 个 → 丢包率 3%
```

### 3. 各自原样上报 Prometheus，不互相干扰

```text
mcdn_network_quality{type="loss",domain="www.baidu.com"} 5
mcdn_network_quality{type="loss",domain="www.taobao.com"} 3
```

两个域名各自一条指标，独立进入 Prometheus。脚本不合并、不取平均。

### 4. 告警平台用 PromQL 取平均

到了告警平台侧，用 `avg by(app, mcdn_identity)` 把同一个节点（`mcdn_identity`）两个 domain 的值算出均值（(5+3)/2 = 4），按业务（`app`）和节点（`mcdn_identity`）分组，然后再和阈值比较。这样避免百度自己挂了导致误下线——只有一个目标丢包时均值不会太高。

### 5. 超阈值触发告警

| 节点类型 | 阈值 | 业务方 |
| --- | --- | --- |
| 点播 / 直播 / 点直混部 | > 20% | BVC（视频云） |
| 点播 / 直播 / 点直混部 | > 15% | MOB（移动端） |
| MP2SP | > 15% | MOB（移动端） |

平均丢包率超过阈值 → 告警平台发 webhook → 下游自动摘除节点。

## 告警规则 PromQL

### 规则一：BVC-丢包率大于20%-自动下线（点播/直播/点直混部）

```text
avg by(app, mcdn_identity) (
  mcdn_network_quality{
    app=~"mcdn",
    mcdn_identity=~"mcdn-.*-(v|live|bvcmix)-.*"
  }
)
< 20
```

### 规则二：MOB-丢包率大于15%-自动下线（点播/直播/点直混部）

```text
avg by(app, mcdn_identity) (
  mcdn_network_quality{
    app=~"mcdn",
    mcdn_identity=~"mcdn-.*-(v|live|bvcmix)-.*"
  }
)
< 15
```

### 规则三：MOB-丢包率大于15%-自动下线（MP2SP）

```text
avg by(app, mcdn_identity) (
  mcdn_network_quality{
    app=~"mcdn",
    mcdn_identity=~"mcdn-.*-mp2sp-.*"
  }
)
< 15
```

### PromQL 标签含义

| 标签 | 含义 |
| --- | --- |
| `app` | 业务（如 `mcdn`），由 Prometheus relabel 从实例映射注入 |
| `mcdn_identity` | 节点身份（hostname），由 Prometheus relabel 从 `instance` 注入 |

### PromQL 语义解析

以规则三为例：

```text
avg by(app, mcdn_identity) (
  mcdn_network_quality{
    app=~"mcdn",
    mcdn_identity=~"mcdn-.*-mp2sp-.*"
  }
)
< 15
```

语义：筛选所有 MP2SP 类型的 MCDN 节点，按业务（`app`）和节点身份（`mcdn_identity`）分组，对同一节点的两个探测目标（如百度、淘宝）的丢包率取平均值。若某节点平均值超过 15%，触发告警。

逐部分说明：

| 片段 | 说明 |
| --- | --- |
| `mcdn_network_quality` | 指标名，存储各节点到公网探测目标的丢包率 |
| `app=~"mcdn"` | 按业务标签过滤，只取 MCDN 业务 |
| `mcdn_identity=~"mcdn-.*-mp2sp-.*"` | 按节点身份标签过滤，只取 MP2SP 类型节点 |
| `avg by(app, mcdn_identity)` | 按业务和节点分组聚合，对组内多个 domain 值取算术平均 |
| `< 15` | 阈值判定，平均值大于 15 则触发告警 |

## agent 脚本参考

脚本位置：`.claude/scripts/packet_loss.sh`（生产环境中部署在每台 MCDN 节点上，由 cron 定时执行）。

```bash
#!/bin/bash
# 根据 /etc/type 区分节点类型，选择不同探测目标
if [[ `cat /etc/type` != 'bstar' ]]; then
    list="www.baidu.com www.taobao.com"      # 国内节点
else
    list="www.google.com www.bilibili.com"   # Bstar 海外节点 + B站
fi

for i in $list; do
    re0=`ping -i 0.1 -W 1 -c 100 $i -n -q | grep -wE "packet loss|rtt min"`
    loss0=`echo $re0 | awk '{print $6}' | cut -d\% -f 1`
    rtt0=`echo $re0 | awk '{print $14}' | awk -F"/" '{print $2}'`
    echo "mcdn_network_quality{type=\"loss\",domain=\"$i\"} $loss0"
    echo "mcdn_network_rtt_quality{type=\"rtt\",domain=\"$i\"} $rtt0"
done
```

| ping 参数 | 含义 |
| --- | --- |
| `-i 0.1` | 发包间隔 0.1 秒（100 包 ≈ 10 秒） |
| `-W 1` | 单包超时 1 秒 |
| `-c 100` | 发 100 个 ICMP 包 |
| `-n` | 不做 DNS 反查 |
| `-q` | 静默汇总模式 |

**脚本产出的所有指标**：

| 指标名 | 标签 | 含义 |
| --- | --- | --- |
| `mcdn_network_quality` | `type="loss"`, `domain` | 丢包率（%） |
| `mcdn_network_rtt_quality` | `type="rtt"`, `domain` | 平均 RTT 延迟（ms），超时取 9999 |
| `mcdn_base_info` | `type="frequency"/"memory_total"/"cpu_processor"` | CPU 主频 / 内存总量 / CPU 核数 |

**关键细节**：

- 脚本只输出 `type` 和 `domain` 两个标签，**没有** `app` 和 `mcdn_identity`，后者由 Prometheus 采集侧通过 `relabel_config` 从 `instance`（hostname）注入
- Bstar（星辰）节点使用 `www.google.com` 而非百度，适配海外网络环境
