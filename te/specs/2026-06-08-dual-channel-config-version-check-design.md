# 点直播兜底 SDK 双通道配置版本巡检告警设计文档

## 背景

根据点直播兜底 SDK 方案，点直播配置通过**双通道**方式进行配置数据传输：

- **Cloud 前端进行双写**：配置管理页面同时写入两条通道
- **配置管理进行双读**：兜底 SDK 从两条通道读取配置
- 现有数据结构中增加 `version` 字段（int64，值基于时间戳）
- 采用**版本号优先**的方式读取，版本相同时以非 Paladin 侧为主

由于 Cloud 前端双写可能发生单边写入失败（比如一个通道写入成功，另一个失败），导致两通道配置版本不一致。需要增加巡检告警机制，定期检测双通道配置版本是否一致。

## 目标

- 巡检 `live_bcdn_rate_config` 和 `vod_mirror_os_config` 两个配置在双通道中的版本是否一致
- 版本不一致时记录告警日志并通过企微发送通知
- 从两个渠道获取配置版本并对比

## 非目标

- 不修复版本不一致（仅检测和告警，修复需要人工介入）
- 不涉及兜底 SDK 本身的逻辑修改

## 双通道架构

```
Cloud 前端（配置管理页面）
    │
    ├── 双写 ────────────────────────────────┐
    │                                         │
    ▼                                         ▼
┌───────────────────┐             ┌──────────────────────────┐
│ CDN Platform API  │             │ Paladin Keyspace         │
│ (通道 A)          │             │ (通道 B)                 │
│                   │             │                          │
│ 点播 API          │             │ live_bcdn_rate_config    │
│ 直播 API          │             │ vod_mirror_os_config     │
│ 鉴权: app_key +   │             │                          │
│       ts + sign   │             │                          │
└────────┬──────────┘             └─────────────┬────────────┘
         │                                      │
         └────── 双读 ──────────────────────────┘
                        │
                  配置中包含 version 字段
```

## 巡检模型

### 模型命名

`ConfigVersionCheckModel`，注册在 `model/intent_model/` 包下。

### 调度频率

`"0 */5 * * * *"`（每 5 分钟）

### 巡检流程

```
ConfigVersionCheckModel.Handle()
    │
    ├── 1. 读取 Paladin keyspace (通道 B)
    │       ├── paladin.v2 KeyspaceSubscribe + KeyspaceString
    │       ├── live_keyspace_name/live_keyspace_data_id（从 conf.toml 读取）
    │       └── vod_keyspace_name/vod_keyspace_data_id（从 conf.toml 读取）
    │
    ├── 2. 读取 CDN Platform API (通道 A，分别调用)
    │       ├── 直播 API: CdnPlatformLiveUrl → live_bcdn_rate_config version
    │       ├── 点播 API: CdnPlatformVodUrl → vod_mirror_os_config version
    │       ├── 签名: tool.Sign(url, body, secret) 实现 MD5 签名
    │       └── 各 API 独立失败不影响另一方
    │
    ├── 3. 从 JSON 中提取 version
    │       ├── 格式 A: {"version": 1781076116, ...}
    │       ├── 格式 B: {"code": 0, "data": {"version": 1779073076}, ...}
    │       ├── 格式 C: {"返回数据": {"version": "1781076116", ...}, ...}（直播 API，值为 string）
    │       └── 使用 json.NewDecoder + UseNumber() 防止精度丢失
    │
    ├── 4. 版本对比
    │       ├── live_bcdn_rate_config: Paladin vs 直播 API
    │       └── vod_mirror_os_config:  Paladin vs 点播 API
    │
    └── 5. 不一致 → 告警
            ├── 记录 error 日志（含双通道版本号）
            └── 写入 PropertyPostMsgEvent change cube → 企微告警
```

## 双通道读取方案

### 通道 B：Paladin Keyspace（go-common paladin.v2）

```go
import "go-common/library/conf/paladin.v2"

// Init（在 init() 中调用，或在 tellurium.go 启动时完成）
paladin.Init()

// 订阅并读取 keyspace 配置（keyspace 和 dataId 从 conf.toml 配置获取）
paladin.KeyspaceSubscribe(liveKeyspaceName, liveKeyspaceDataId)
content, _ := paladin.KeyspaceString(liveKeyspaceName, liveKeyspaceDataId)
// content 为 JSON 字符串，从中解析 version
```

#### keyspace 配置（conf.toml `[config_version_check]` 段，可覆盖）

| 配置项 | 默认值 | 用途 |
|--------|--------|------|
| `live_keyspace_name` | `live_bcdn_rate_config` | 直播带宽比例配置 keyspace |
| `live_keyspace_data_id` | `bcdn_rate` | 直播带宽比例配置 dataId |
| `vod_keyspace_name` | `vod_mirror_os_config` | 点播回源配置 keyspace |
| `vod_keyspace_data_id` | `mirror_os` | 点播回源配置 dataId |

默认值定义在 `framework/constant/constant.go`，通过 `CheckConfig()` 从配置覆盖。

### 通道 A：CDN Platform API

两个独立 API，分别对应直播和点播（URL 从 `conf.toml` 配置获取）：

| 用途 | API 地址 |
|------|---------|
| **点播** | `http://bvc-ost-oss.bilibili.co/api/raynor/v1/cdn/playurl/3rd-new/backup` |
| **直播** | `https://bvc-nerve.bilibili.co/x/video/zodiac/leo/video.live.playurl-control-v2/playurlcontrol.PlayurlControl/Get` |

#### API 鉴权方式

点播 API 需要进行 MD5 签名，直播 API **无需鉴权**。

签名算法：
```
1. URL 添加 app_key 和 ts(ms) 参数
2. 所有 query 参数按 key 字母排序
3. 拼接：key1=va11^_^key2=val2^_^...^_^^_^secret
   （GET 无 body，body 用空字符串代替）
4. sign = MD5(拼接字符串)
```

项目中已有的 `tool.Sign(url, body, secret)` 实现了上述签名算法，直接复用。

## 版本号解析

### JSON 格式兼容

`readVersionFromJSON` 兼容三种 JSON 结构：

```json
// 格式 A（live_bcdn_rate_config - 顶层 version）
{"version": 1781076116, "cdn_tag": "...", "room_rate": "..."}

// 格式 B（vod_mirror_os_config - data.version）
{"code": 0, "data": {"version": 1779073076, "os_population": 10000}, "message": "success"}

// 格式 C（直播 API 返回 - 返回数据.version，值为 string）
{"返回数据": {"version": "1781076116", ...}, ...}
```

使用 `json.NewDecoder` + `UseNumber()` 将数字解析为 `json.Number`，再通过 `Int64()` 转为 `int64`，避免大整数被 `float64` 截断导致精度丢失。格式 C 中 version 为 string 类型，使用 `strconv.ParseInt` 解析。

### 类型选择：int64

version 值基于 UTC 毫秒时间戳（如 `1781076116`），在 `int64` 范围内。统一使用 `int64` 而非 `uint64`，简化类型转换。

## 数据结构定义

```go
type configVersionPair struct {
    LiveBcdnRateConfig int64 // live_bcdn_rate_config 版本号
    VodMirrorOsConfig  int64 // vod_mirror_os_config 版本号
}
```

## 配置链

遵循项目既定的配置模式（同 `CdnPlatformVodUrl` 模式）：

```
conf.toml  →  config.go TeConfig   →  config.go CheckConfig  →  constant.go   →  模型代码
([config_version_check])  (解析到 struct)   (覆盖到 constant)   (var 默认值)   (c.xxx 引用)
```

### constant.go 默认值

```go
var (
    ConfigVersionCheckLiveKeyspaceName   = "live_bcdn_rate_config"
    ConfigVersionCheckLiveKeyspaceDataId = "bcdn_rate"
    ConfigVersionCheckVodKeyspaceName    = "vod_mirror_os_config"
    ConfigVersionCheckVodKeyspaceDataId  = "mirror_os"
)
```

### conf.toml 配置段

```toml
[config_version_check]
live_keyspace_name = "live_bcdn_rate_config"
live_keyspace_data_id = "bcdn_rate"
vod_keyspace_name = "vod_mirror_os_config"
vod_keyspace_data_id = "mirror_os"
```

### config.go TeConfig 结构体

```go
type TeConfig struct {
    // ... 其他配置 ...
    ConfigVersionCheck struct {
        LiveKeyspaceName   string `toml:"live_keyspace_name"`
        LiveKeyspaceDataId string `toml:"live_keyspace_data_id"`
        VodKeyspaceName    string `toml:"vod_keyspace_name"`
        VodKeyspaceDataId  string `toml:"vod_keyspace_data_id"`
    } `toml:"config_version_check"`
}
```

## 告警机制

### 告警条件

两个配置分别对比，任意一个版本不一致即触发告警：

| 配置 | Paladin 版本 | CDN API 版本 | 状态 |
|------|-------------|-------------|------|
| `live_bcdn_rate_config` | 1781076116 | 1781076116 | ✅ 一致 |
| `vod_mirror_os_config` | 1779073076 | 1779073077 | ⚠️ 不一致 |

### 告警内容

通过 `engine.WriteChangeCube` 写入 `PropertyPostMsgEvent`，由 `PostMsgAppModel` 发送企微消息：

```
配置版本不一致
配置: vod_mirror_os_config
Paladin 版本: 1779073076
视频CDN运管平台 版本: 1779073077
```

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| Paladin keyspace 订阅失败 | 记录 error 日志，该 keyspace 版本为 0 |
| Paladin keyspace 读取失败 | 记录 error 日志，该 keyspace 版本为 0 |
| CDN API URL 未配置 | 记录 warn 日志，返回空结果 |
| CDN API HTTP 请求失败 | 记录 error 日志，该 API 版本为 0 |
| JSON 解析失败（无 version 字段） | 记录 error 日志，该配置版本为 0 |
| 版本不一致 | 记录 error 日志 + WriteChangeCube 企微告警 |
| 版本一致 | 记录 warn 日志 |
| dev 模式（keyspace 不可用） | 自动回退到 `docs/` 目录本地 JSON 文件读取 |

### 关于 nil 返回

- `readFromPaladin`：始终返回非 nil 的 `*configVersionPair`（版本为 0 表示读取失败）
- `readFromCdnPlatform`：URL 未配置时返回 nil；执行失败返回非 nil（版本为 0）

## 涉及文件

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `model/intent_model/config_version_check_model.go` | 新增 | 配置版本巡检模型（主逻辑） |
| `model/intent_model/config_version_check_model_test.go` | 新增 | 完整测试套件（含 dev 模式本地回退） |
| `conf/config.go` | 修改 | 新增 `ConfigVersionCheck` 结构体 + `CheckConfig` 覆盖 |
| `conf/conf.toml` | 修改 | 新增 `[config_version_check]` 配置段 |
| `framework/constant/constant.go` | 修改 | 新增 keyspace 默认值变量 |

## 测试验证

### dev 模式（推荐，无需 MySQL/Redis）

```bash
# 前置条件：ClickHouse 容器
docker run -d --name clickhouse-te \
  -e CLICKHOUSE_PASSWORD=test123 \
  -p 127.0.0.1:8123:8123 \
  clickhouse/clickhouse-server:latest

# 全链路测试
ZONE=sh001 DEPLOY_ENV=dev go test -run TestConfigVersionCheckModel_Handle \
  -v -count=1 -timeout 180s ./model/intent_model/ 2>&1
```

### prod 模式（需要 MySQL 和 Redis 容器）

```bash
# 前置条件
docker run -d --name te-test-mysql \
  -e MYSQL_ROOT_PASSWORD=test_root_pwd \
  -e MYSQL_USER=tellurium \
  -e MYSQL_PASSWORD=5xLDmtCz3iYZO0tLAt8aZuYTt46vln9Q \
  -e MYSQL_DATABASE=pili_inferno \
  -p 127.0.0.1:3306:3306 mysql:8.0
docker run -d --name te-test-redis -p 127.0.0.1:28040:6379 redis:7-alpine

# 运行命令
cd /Users/bilibili/Dev/te/.claude/worktrees/config-version-check
ZONE=sh001 DEPLOY_ENV=prod \
  APP_ID=video.bvc-bda.dsa-tellurium \
  PALADIN_APP_ID=video.bvc-bda.dsa-tellurium \
  CONF_TOKEN=cf14f9ab006090c10b222d014adaaa5f \
  go test -run <TestName> -v -count=1 -timeout 180s ./model/intent_model/ 2>&1
```

### 测试场景

| 测试函数 | 验证内容 |
|---------|---------|
| `TestReadFromPaladin` | Paladin keyspace 读取（dev 模式回退到本地文件） |
| `TestReadConfigFromPaladin` | 直接调用 paladin.v2 Keyspace API |
| `TestReadLiveConfigFromCdnPlatform` | 直播 API 无需鉴权 |
| `TestReadVodConfigFromCdnPlatform` | 点播 API tool.Sign 签名 |
| `TestConfigVersionCheckModel_Handle` | 全链路：双通道读取 + 版本对比 + 告警测试 |

### dev 模式本地回退机制

dev 模式下 Paladin keyspace 不可用（使用本地配置加载），测试通过 `paladinFromEnv()` 自动回退：

1. 先尝试 `readFromPaladin`（keyspace 读取）
2. 如果版本号均为 0（dev 模式 keyspace 不可用），自动调用 `readFromPaladinDev`
3. `readFromPaladinDev` 从 `docs/paladin_live_bcdn_rate_config.json` 和 `docs/paladin_vod_mirror_os_config.json` 读取版本号

### 部署后验证日志

```
# 正常日志
ConfigVersionCheckModel: live_bcdn_rate_config version=1781076116, logId:xxx
ConfigVersionCheckModel: vod_mirror_os_config version=1779073076, logId:xxx

# 告警日志
配置版本不一致
配置: live_bcdn_rate_config
Paladin 版本: 1781076116
视频CDN运管平台 版本: 1781076117
```