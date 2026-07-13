---
title: 自动上线策略 - 区分 v 机器丢包率场景
date: 2026-06-25
tags:
  - go-op
  - 自动上线
  - 丢包率
  - MCDN
  - 策略
related:
  - "[[北斗资源上下线及踢点策略技术文档]]"
  - "[[go-op MOC]]"
---

# 自动上线策略：区分 -v 机器丢包率场景

> 记录于 2026-06-25，MR #1567（已合并），MR #1568（测试补充）。

## 背景

当前 `autoAction` 对所有机器统一执行"逐步升级"惩罚策略：

| 当日下线次数 | 等待时间 | 处理方式 |
|-------------|----------|----------|
| 1 次 | 30 分钟 | 自动上线 |
| 2 次 | 2 小时 | 自动上线 |
| ≥3 次 | — | 不自动上线，需人工 |

运维反馈 `-v-`（视频云）机器因丢包率触发下线后，逐步升级策略过于保守——第 2 次下线仍需等 2 小时，影响服务可用性。希望统一等待 30 分钟即可自动上线，取消逐步升级。

其他触发原因（磁盘、CPU 等）和其他机器类型（`-mp2sp-` 等）保持原策略不变。

## 核心设计

### 机器类型识别

通过 `service_type` 字段（`msg_data_all` 数据库列）判断：

| service_type | 对应机器 |
|-------------|---------|
| `"视频云"` | `-v-` 机器 |
| `"移动端"` | `-mp2sp-` 机器 |

复用已有常量 `BusinessTypeBvc = "视频云"`（定义于 `service/service.go:32`）。

### 触发原因识别

通过 `alertname` 字段（`msg_data_all` 数据库列）判断是否丢包率触发：

```go
func isPacketLossDownAlert(alertname string) bool {
    return strings.Contains(alertname, "丢包率")
}
```

`alertname` 示例：`BVC-丢包率大于20%-自动下线` / `MOB-丢包率大于15%-自动下线`。

### 策略分叉

```go
func shouldOnline(param *model.Instance, nowUnix int64) bool {
    elapsed := nowUnix - param.CreateTime

    // -v 机器 + 丢包率：取消逐步升级，统一 30 分钟
    if isVMachine(param.ServiceType) && isPacketLossDownAlert(param.Alertname) {
        return elapsed >= waitTimeShort    // 1800 秒
    }

    // 其他机器：逐步升级
    switch param.Value {
    case 1:
        return elapsed >= waitTimeShort    // 1800 秒
    case 2:
        return elapsed >= waitTimeLong     // 7200 秒
    default:
        return false                       // ≥3 次，不自动上线
    }
}
```

## 实现过程

### 第一轮：基础实现（MR #1567）

1. **`model/autoonline.go`**：`Instance` 结构体新增 `ServiceType` 和 `Alertname` 字段
2. **`GetInstance` SQL**：用 `SUBSTRING_INDEX(GROUP_CONCAT(alertname ORDER BY ctime DESC), ',', 1)` 在单次聚合查询中直接取出每台机器最新的 alertname，消除二次查询
3. **新增辅助函数**：`isVMachine`、`isPacketLossDownAlert`（纯函数，可单测）
4. **抽取 `doOnline`**：消除上线操作的重复代码，并修复 `ChangeServerStatus` 失败后仍写库发通知的问题
5. **魔数常量化**：`1800` → `waitTimeShort`、`7200` → `waitTimeLong`
6. **错误包裹**：`GetInstance` 使用 `fmt.Errorf + %w` 包裹数据库错误

### 第二轮：测试补充（MR #1568）

7. **抽出 `shouldOnline` 纯决策函数**：等待时间逻辑从 `autoAction` 解耦，支持独立单测，经审查确认重构前后行为完全等价
8. **`TestShouldOnline` 测试**：19 个用例，覆盖：

| 分组 | 用例数 | 验证内容 |
|------|--------|----------|
| -v 丢包率 | 7 | 统一 30 分钟不分次数，30分钟边界（≤29不上线/≥30上线） |
| -v 非丢包率 | 4 | 回退逐步升级（1次30分/2次2小时/≥3次人工） |
| mp2sp（移动端） | 5 | 即使丢包率也不享受统一30分钟，走逐步升级 |
| 空值边界 | 3 | 空 service_type/空 alertname → 走逐步升级 |

### 第三轮：生产观测

9. **`autoonline_observe.sql`**：观测 SQL（`app/manba-bi/configs/`），配对 action_id=400（上线）与 action_id=100（下线），输出实际等待秒数，供发布前/后人工对比

## 生产验证结果

发布变更后生产数据确认策略生效：

```
视频云 + 丢包率 + 下线2次:
  变更前: ~7500秒（~125分钟，旧策略2小时）
  变更后: 1952秒（33分钟）     ← 1800 + 调度抖动，策略生效
```

mp2sp（移动端）机器验证非 -v 机器未被误改——逐步升级正常（1次 31 分钟、2 次 124 分钟）。

## 改动文件

| 文件 | 改动 |
|------|------|
| `app/manba-bi/internal/model/autoonline.go` | Instance 加 ServiceType + Alertname 字段 |
| `app/manba-bi/internal/service/autoonline.go` | GetInstance 单次查询带 alertname；shouldOnline 决策函数；doOnline 抽取；常量化；错误包裹 |
| `app/manba-bi/internal/service/autoonline_test.go` | TestShouldOnline 19 用例 + TestIsVMachine + TestIsPacketLossDownAlert + TestIntegrationGetInstance |
| `app/manba-bi/configs/autoonline_observe.sql` | 生产观测 SQL（新增） |

## 关键决策记录

| 决策 | 理由 |
|------|------|
| alertname 在 GetInstance 聚合中直接取出 | 消除二次查询，避免 N+1 和 IN 上限问题 |
| 用 GROUP_CONCAT + 逗号分隔而非 0x01 | 当前 alertname 含连字符不含逗号，简洁优先 |
| shouldOnline 单独抽函数 | 无灰度部署，等待时间逻辑必须有单测覆盖 |
| 不在 SQL 层过滤已上线机器 | 北斗 API 是唯一权威实时状态源，调用量小，SQL 推断不可靠 |
| down_count_today ≥3 不自动判定 | 这类记录多为人工上线，wait_seconds 无策略参考意义 |
