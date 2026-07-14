---
title: checkStatus CPU 健康检查实现方案
date: 2026-07-07
tags:
  - go-op
  - CPU
  - MCDN
  - 设计
  - checkStatus
  - 类型/设计
related:
  - "[[MCDN CPU 高负载机器总览]]"
  - "[[go-op MOC]]"
---

# checkStatus CPU 健康检查实现方案

> 状态：已设计，待实现
> 最后更新：2026-07-07

---

## 一、方案选择了直查 MCDN 资源 API

跳过 moni/Graphana/Prometheus/relay 等所有中间层，直接在 `checkStatus` 中查 MCDN 资源 API 的 `cpu_used` 字段。

### 为什么不选其他方案

| 方案 | 问题 |
|------|------|
| `sum(mcdn_cpu_moni{type="cpu"})` | Prometheus 即时查询，但 v-308 验证了该指标是平滑/累计值，暴冲前后均无变化，无法区分闲忙 |
| `node_load1` / `node_cpu_seconds_total` | moni API 当前 data source 29 只支持 `mcdn_init_status_application`，是否支持这些指标待验证 |
| relay + top 采集 | 异步执行有延迟，不适合实时判定 |
| portal `GetServerSid` | 已有 API 不返回 `cpu_used` |

### 选中的方案

**MCDN 资源 API：`https://mcdn-data.biliapi.net/api/v1/portal/mcdn/resource`**

- 实时返回全量在线节点的 `cpu_used`（百分值，如 46.75）
- portal 包已封装对 MCDN 资源 API 的调用能力（`GetServerSid` 同一数据源）
- 已经在 v-1125 和 v-1169 等机器的分析中验证过准确性

---

## 二、API 关键字段

```json
{
  "server_name": "mcdn-qny-jstz-dx-v-1125",
  "cpu_used": 46.75,
  "load_stat_1": 2.78,
  "load_stat_5": 3.15,
  "load_stat_15": 5.07,
  "mem_used": 54.86,
  "mem_total": 66856615936,
  "is_disabled": false,
  "incoming": 7037762,
  "outgoing": 21681674,
  "ips": ["58.222.41.87"]
}
```

| 字段 | 类型 | 说明 | checkStatus 用法 |
|------|------|------|------|
| `cpu_used` | float | 节点级 CPU 使用率（百分比） | **主判定：> 70% 暂缓上线** |
| `load_stat_1` | float | 1 分钟 load | 可选辅助判定 |
| `incoming` | int | 入流量（B/s） | 可选辅助，间接反映回源带宽 |
| `is_disabled` | bool | 是否已下线 | 已有逻辑已处理 |
| `ips` | array | 有效 IP 列表 | 可以用来判断是否已有 dial_ips |

---

## 三、实现方案

### 阈值推导

基于六台机器的 CPU 分析和 v-357 正常对照：

```
v-357（正常）cpu_used: 39.92%（当前），平时更低
v-1169（暴冲）cpu_used: 1.68%（已下线后），在线时 ~80%+
触发下线阈值: 80%
checkStatus 拦截阈值: 70%（留 10% buffer）
```

### 伪代码

```go
const cpuOnlineThreshold = 70.0  // CPU 超过此值则暂缓自动上线

func (s *Service) checkStatus(param *model.Instance) bool {
    // 查 MCDN 资源 API 获取节点 cpu_used
    info, err := s.portal.GetServerResource(param.Name)
    if err != nil {
        // API 查询失败不阻塞上线，兼容现网
        log.Warn("checkStatus 查 CPU 失败, name=%s, err=%v", param.Name, err)
        return true
    }

    if info.CpuUsed > cpuOnlineThreshold {
        log.Warn("checkStatus CPU 过高暂缓上线, name=%s, cpu=%.1f%%, threshold=%.0f%%",
            param.Name, info.CpuUsed, cpuOnlineThreshold)
        // TODO: 可选发送通知给运维
        return false
    }

    log.Info("checkStatus CPU 正常，批准上线, name=%s, cpu=%.1f%%", param.Name, info.CpuUsed)
    return true
}
```

### 需要新增的代码

| 文件 | 变更 |
|------|------|
| `app/manba-bi/pkg/portal/model.go` | 新增 `ResourceInfo` 结构体（`CpuUsed float64`） |
| `app/manba-bi/pkg/portal/org.go` | 新增 `GetServerResource(name string)` → 查 `cpu_used` |
| `app/manba-bi/internal/service/autoonline.go` | `checkStatus` 替换现有空实现 |

### portal 包变更要点

portal 包已使用 MCDN 资源 API（`GetServerSid` 等方法复用同一数据源），新增 `GetServerResource` 可直接复用已有的 HTTP 客户端和认证（`x-secretid` + `x-signature`），只需：

1. 请求 `GET /api/v1/portal/mcdn/resource`（已有的全量查询）
2. 在返回的 `mcdn_alls` 列表中按 `server_name` 匹配目标节点
3. 返回匹配节点的 `cpu_used`

---

## 四、影响分析

| 机器 | 此前死循环 | checkStatus 后 |
|------|-----------|------|
| v-1169 | 上线→2%→接入流量→bvc暴涨→80%→下线→30分钟后重复 | 上线前查 cpu_used，>70% 暂缓，等 bvc 自然回落后再上线 |
| v-1109 | 同上 | 同上 |
| v-1125 | blink 修后仍在暴冲 | 同上 |
| v-344 | bvc 从 108% 飙到 522% | 同上 |
| v-337 | 被 check.miku.stat + md5sum 叠加 | 清除非业务进程后，checkStatus 也会拦截 |
| v-308 | 间歇运维任务暴冲 | 同上 |

**注意：checkStatus 不能阻止机器暴冲，但能阻止暴冲后立刻重新上线再次暴冲的死循环。**

---

## 五、验证方法

1. 选一台已经触发下线的机器（如 v-1109），等待自动上线窗口
2. 查看日志确认 `checkStatus CPU 过高暂缓上线` 的 WARN 日志
3. 确认机器不会被上线
4. 观察 cpu_used 随时间下降，达到 < 70% 后下一次自动上线周期正常恢复

---

## 六、相关文档

- 六台机器分析：[cpu-top-六台机器总览](cpu-top-六台机器总览.md)
- v-1125 回源带宽因果链：[cpu-analysis-mcdn-qny-jstz-dx-v-1125](cpu-analysis-mcdn-qny-jstz-dx-v-1125.md)
- MCDN 资源 API 采集脚本：[mcdn_base_info.py](../scripts/moni/mcdn_base_info.py)
