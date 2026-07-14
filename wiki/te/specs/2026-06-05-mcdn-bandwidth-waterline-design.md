---
title: MCDN 带宽利用率水位线检测设计
date: 2026-06-05
tags:
  - te
  - 水位线
  - MCDN
  - 带宽
  - 设计
  - 类型/设计
related:
  - "[[te MOC]]"
---

# mcdn 机器带宽利用率水位线检测设计文档

## 背景

现有 `WaterLineModel` 对所有机器的带宽利用率使用统一阈值（`band_width`，当前配置 90%）。需求是对 mcdn 机器单独设置 70% 的带宽利用率告警阈值，超阈值时直接发送企微告警，不经过下游 change cube 处理链路。

## 目标

- 检测 mcdn 机器带宽利用率是否超过独立阈值（默认 70%）
- 超阈值时写入 `PostMsgEvent`，由 `PostMsgAppModel` 直接发送企微告警
- 非 mcdn 机器行为不变，继续写入水位线 change cube，由下游模型（如 `HostDisableIntentModel`）处理
- CPU 和内存水位线逻辑不受影响，不改动

## 数据流

```
BiliDataCubeTableHostResource
    └── WaterLineModel.handle(EntityHostBand)
            ├── 非 mcdn 机器：threshold = conf.Config.WaterLine.BandWidth (90%)
            │       └── percent > threshold → WriteChangeCube → HostDisableIntentModel（下游处理）
            │
            └── mcdn 机器：threshold = conf.Config.WaterLine.McdnBandWidth (70%)
                    └── percent > threshold → WriteChangeCube(PropertyPostMsgEvent)
                            └── PostMsgAppModel → 企微机器人告警
```

**关键区别**：mcdn 超阈值不走 `HostDisableIntentModel`，而是直接通知。

## 变更内容

### 1. conf/config.go

`WaterLine` 结构体新增 `McdnBandWidth` 字段：

```go
WaterLine struct {
    CPU           int `toml:"cpu"`
    BandWidth     int `toml:"band_width"`
    Mem           int `toml:"mem"`
    McdnBandWidth int `toml:"mcdn_band_width"` // mcdn 机器带宽水位线阈值
} `toml:"water_line"`
```

### 2. conf/conf.toml

`[water_line]` 块新增配置项：

```toml
[water_line]
cpu = 500
band_width = 90
mem = 70
mcdn_band_width = 70  # mcdn 机器带宽已用大于70%则认为水位线过高
```

### 3. model/intent_model/water_line_model.go

在 `handle` 方法中，对 `entity == EntityHostBand && prefix == BiliMcdnPrefix` 的机器走独立分支：

```go
threshold := maxValue
if entity == c.EntityHostBand && strings.Contains(hostName, c.BiliMcdnPrefix) {
    threshold = conf.Config.WaterLine.McdnBandWidth
}
if percent > float64(threshold) {
    if entity == c.EntityHostBand && strings.Contains(hostName, c.BiliMcdnPrefix) {
        // mcdn 机器→直接写 PostMsgEvent，由 PostMsgAppModel 发送企微告警
        engine.WriteChangeCube(
            c.PropertyPostMsgEvent,
            hostName,
            fmt.Sprintf("mcdn带宽利用率超过%v%%", threshold),
            c.LayerPostMsg,
            c.EntityHostBand,
            conf.Config.ThirdRelevant.NoticeWebhook,
            logId)
    } else {
        // 非 mcdn 机器→正常水位线 change cube
        ...
        engine.WriteChangeCube(
            cubeEntity, hostName,
            fmt.Sprintf("%v的%v水位线大于%v%%", hostName, cubeEntity, threshold),
            "", "", dependency, logId)
    }
}
```

**关键变更点**：

- `threshold` 根据是否 mcdn 机器动态选择（复用同一个 `percent > threshold` 判断入口）
- mcdn 分支的 `entity` 参数改用 `c.PropertyPostMsgEvent`，通知走企微通道
- mcdn 分支写入 `c.LayerPostMsg` 层，由 `PostMsgAppModel` 消费

### 4. model/intent_model/water_line_model_test.go

- 新增 `TestPostMsg` 测试函数，调用 `PostMsgAppModel` 验证企微消息发送
- 在 `TestWaterLineModel` 中增加 `time.Sleep` 等待数据写入完成
- 移除测试前的 `engine.DeleteDataCubeData()` 清理调用，避免干扰

### 5. model/intent_model/water_line_model_test_input.json

- 字段名修正：`host_name` → `scoloum1`（与 `BiliDataCubeTableHostResource` 实际列名一致）
- 新增三条带宽测试数据：

  - `mcdn-jd-sxxa-cm-17000193` — `(350+300)/1000=65%` → 不告警（低于 70%）
  - `mcdn-hw-bja-cm-17000194` — `(400+350)/1000=75%` → 企微告警（高于 70%）
  - `edge-sh-sha-cm-17000195`（非 mcdn）— `(450+400)/1000=85%` → 不告警（低于全局 90%）

## 错误处理

- `McdnBandWidth` 未配置时 Go 默认值为 `0`，会导致所有 mcdn 机器都触发告警。与现有 `BandWidth` 字段约定一致：配置文件必须填写，不做额外兜底。
- `BiliMcdnPrefix` 常量（默认 `"mcdn"`）用于前缀匹配，需保证与数据中的 hostname 前缀一致

## 涉及文件

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `conf/config.go` | 修改 | 新增 `McdnBandWidth` 字段 |
| `conf/conf.toml` | 新增 | 完整配置模板（含 `mcdn_band_width`） |
| `model/intent_model/water_line_model.go` | 修改 | handle 方法新增 mcdn 独立分支 |
| `model/intent_model/water_line_model_test.go` | 修改 | 新增 `TestPostMsg` 用例 |
| `model/intent_model/water_line_model_test_input.json` | 修改 | 字段对齐 + mcdn 测试数据 |

## 测试验证

```bash
cd model/intent_model && go test -run TestWaterLineModel
cd model/intent_model && go test -run TestPostMsg
```

`TestPostMsg` 会实际调用企微 webhook，需在测试环境中验证 Webhook URL 正确。
