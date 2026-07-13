# MCDN v 节点丢包率探测改造总结

> 2026-07-08 启动，2026-07-10 联调完成。交付物：`.claude/scripts/mcdn_network.sh`

## 背景问题

v 节点丢包率探测一直和 mp2sp 一样 ping 百度/淘宝域名。CDN DNS 按请求来源 IP 返回本网 IP（DNS 劫持），导致 **62% 的异网覆盖 v 节点始终测本网物理线**，跨运营商互通点拥塞完全盲视。实际数据：一台物理电信→调度联通的机器，旧脚本 24h 丢包率接近 0%，新脚本在晚高峰捕捉到 5~19% 的联通方向丢包。

## 改造方案

核心思路：不再 ping 域名任由 DNS 劫持，改为 **dig +subnet 手工指定运营商 IP 段，强制 CDN 返回该运营商边缘 IP，ping 该 IP 走跨网互通点**。

ISP 来源从手动判断演进到 API 查询：

1. **v1（hostname 第 4 段）**：准确率仅 75%，qny/ydy/wx 三个厂商 17 台实际 ISP 与 hostname 不符
2. **v2（cip.cc HTTP 查询）**：准确率高但部分节点 HTTP 不通，且返回物理线而非调度方向
3. **v3（mcdn-data API）**：`isp` 字段与 BBAN 100% 一致，返回调度方向 ISP，配合缓存（/tmp，TTL 1 小时）+ 3 次重试（间隔 5s），99%+ 可用

## mcdn_network.sh 最终结构

```
启动
├─ 输出 base_info（CPU 频率/内存/核数）
├─ 判断机器类型（hostname 第 5 段）
│   ├─ 非 v → ping 域名（原 packet_loss.sh 逻辑，含 RTT）→ 退出
│   └─ v   ↓
├─ ISP 查询
│   ├─ mcdn-data API（isp 字段，调度方向）→ 成功：SCHED_ISP=ct/cu/cm
│   │   ├─ 3 次重试，每次间隔 5s
│   │   └─ 成功写入缓存 /tmp/mcdn_network_cache
│   ├─ 失败 → 缓存读取（TTL 1h）
│   └─ 缓存也失败 → cip.cc（物理线，排除本网）→ 全量三方向（最终兜底）
├─ dig +subnet 解析百度/淘宝在该运营商的 IP → ping 50 包
└─ 输出 2 行 mcdn_network_quality{domain="www.baidu.com/taobao.com"}
```

## 输出格式

与 `packet_loss.sh` 完全兼容，原有的 Prometheus 指标名、标签不变：

```
mcdn_network_quality{type="loss",domain="www.baidu.com"} <loss>
mcdn_network_quality{type="loss",domain="www.taobao.com"} <loss>
```

v 节点不输出 RTT（原脚本也不依赖 v 节点的 RTT 做告警）。

## 关键技术决策

| 决策 | 原因 |
|------|------|
| 用 `isp`（调度方向）而非 `user_actual_isp`（物理线） | 直接 ping 被调度去服务的方向，逻辑更直，ping 2 次即可 |
| API 优先 + 缓存 + 3 次重试 | 内网 API 99%+ 可用，偶有抖动一次重试恢复 |
| 砍掉跨方向取平均 | 调度方向只有一个，不需要排除本网再平均 |
| grep+sed 解析 JSON 而非 Python | 部分节点只有 Python 2，避免依赖 |
| `CROSS_ISP_DEBUG=1` 开关 | 生产环境零日志噪音，调试时一键开启 |
| 非 v 节点不改动 | mp2sp 节点无跨网覆盖问题，原逻辑继续生效 |

## 三级兜底

```
mcdn-data API → 缓存 → cip.cc → 全量三方向固定 IP
```

最坏情况下（API + 缓存 + cip.cc 全挂）仍能通过固定 IP ping 三方向，不会输出 loss=100 导致误告警。

## 实测效果

**C1 节点 `mcdn-bdwl-hbwh-dx-v-10300820`（物理=电信，调度=联通）24h 对比：**

| 时段 | 旧脚本（ping 电信） | 新脚本（ping 联通） |
|------|-------------------|---------------------|
| 00:00-17:00 | ~0% | 0~2%（偶有波动） |
| **17:29-22:00（晚高峰）** | **~0%** | **5~19%** |
| 22:00-次日 | ~0% | 逐步回落至 0% |

旧脚本在晚高峰对联通方向拥塞完全盲视，新脚本准确捕捉。

## 部署

| 项目 | 值 |
|------|-----|
| 脚本 | `.claude/scripts/mcdn_network.sh` |
| 部署路径 | 替换节点上原有 `packet_loss.sh`（cron 调用入口不变） |
| 适用节点 | 69 台 -v 节点 |
| 调试开关 | `CROSS_ISP_DEBUG=1 bash mcdn_network.sh` |
| 相关文档 | `.claude/docs/2026-07-08-mcdn-cross-isp-ping.md`（含 API 索引、ISP 字段验证） |
