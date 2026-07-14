---
title: 双通道配置版本巡检告警 - 实现计划
date: 2026-06-08
tags:
  - te
  - 配置巡检
  - 双通道
  - 计划
  - 类型/计划
aliases:
  - dual-channel-config-version-check-plan
related:
  - "[[双通道配置版本巡检告警设计]]"
  - "[[te MOC]]"
---

# 点直播兜底 SDK 双通道配置版本巡检告警 — 改造实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将已实现的 `ConfigVersionCheckModel` 中的通道 A 从单一 `CdnPlatformUrl` + `?keyspace=` 模式改造为双 API（点播 + 直播）带鉴权签名调用

**当前状态：** Paladin 通道（readFromPaladin）已完成，`readVersionFromJSON` 已完成，`compareAndAlert` 已完成。需要改造 readFromMcdnPlatform → readFromCdnPlatform。

**Tech Stack:** Go, go-common paladin.v2, md5 ^_^ 签名, utf-8

---

## 文件结构

| 文件 | 动作 | 职责 |
|------|------|------|
| `conf/config.go` | 修改 | `ThirdRelevantConfig` 中 `CdnPlatformUrl` 拆分为 `CdnPlatformVodUrl` + `CdnPlatformLiveUrl` |
| `model/intent_model/config_version_check_model.go` | 修改 | `readFromMcdnPlatform` 重命名为 `readFromCdnPlatform`，实现 MD5 鉴权签名，分别调用点播/直播 API |

---

### Task 1: conf/config.go — 拆分 CdnPlatformUrl 为点播和直播两个字段

**说明：** 单 URL + `?keyspace=xxx` 模式不再适用。点播和直播是两个独立的 API 路径，需要分别配置。

- [ ] **Step 1: 修改 ThirdRelevantConfig**

```go
type ThirdRelevantConfig struct {
	AppKey             string `toml:"app_key"`
	AppSecret          string `toml:"app_secret"`
	BbanSchedule       string `toml:"bban_schedule"`
	NoticeWebhook      string `toml:"notice_webhook"`
	DebugNoticeWebhook string `toml:"debug_notice_webhook"`
	InspectionWebhook  string `toml:"inspection_webhook"`
	CdnPlatformVodUrl  string `toml:"cdn_platform_vod_url"`  // 点播 CDN 平台 API，空则不检查
	CdnPlatformLiveUrl string `toml:"cdn_platform_live_url"` // 直播 CDN 平台 API，空则不检查
}
```

`CdnPlatformVodUrl` = `https://cloud-cdn.bilibili.co/api/ost-res-manager/cdn/playurl/3rd-new/backup`
`CdnPlatformLiveUrl` = `https://cloud-cdn.bilibili.co/api/live-playurl-control-v2/all`

为空时静默跳过该通道的读取（函数返回 nil，调用方已有兼容逻辑）。

---

### Task 2: 改造 config_version_check_model.go

#### 已完成部分（无须改动）

- `ConfigVersionCheckModel` 骨架 + init 注册 ✓
- `readFromPaladin()` — 使用 go-common paladin.v2 KeyspaceSubscribe + KeyspaceString ✓
- `readVersionFromJSON()` — 使用 UseNumber() 解析 json.Number ✓
- `compareAndAlert()` — 版本对比 + 企微告警 ✓
- 所有类型为 `int64` ✓
- 测试文件 ✓

#### 待改造部分

- [ ] **Step 1: 在 import 中添加鉴权所需的标准库**

```go
import (
	"crypto/md5"
	"encoding/hex"
	"net/url"
	"sort"
	"strconv"
	"strings"
)
```

当前已有 `encoding/json`、`fmt`、`strings`、`time`，需要新增 `crypto/md5`、`encoding/hex`、`net/url`、`sort`、`strconv`。

- [ ] **Step 2: 添加常量 — 点播和直播 API 与 keyspace 的映射**

```go
// API 地址与 keyspace 的映射关系
var keyspaceAPIMap = map[string]string{
	keyspaceNameLiveBcdnRate: cConf.Config.ThirdRelevant.CdnPlatformLiveUrl,
	keyspaceNameVodMirrorOs:  cConf.Config.ThirdRelevant.CdnPlatformVodUrl,
}
```

- [ ] **Step 3: 实现 signUrl — 生成带鉴权的签名 URL**

参照 raynor 库 `library/tools/sign/sign.go` 的 `^_^` 算法：

```go
// signURL 对 URL 添加 app_key、ts 参数并计算 MD5 签名
// 签名算法（与 API 鉴权 PDF 一致）：
// 1. 添加 app_key 和 ts(毫秒) 到 query
// 2. query 按键字母排序
// 3. 拼接 key=value^_^...^_^^_^secret
// 4. 计算 MD5 作为 sign
func signURL(rawURL, appKey, secret string) (string, error) {
	ts := strconv.FormatInt(time.Now().UnixMilli(), 10)
	sep := "?"
	if strings.Contains(rawURL, "?") {
		sep = "&"
	}
	signedURL := fmt.Sprintf("%s%sapp_key=%s&ts=%s", rawURL, sep, appKey, ts)

	u, err := url.Parse(signedURL)
	if err != nil {
		return "", fmt.Errorf("parse url failed: %w", err)
	}

	keys := make([]string, 0, len(u.Query()))
	for k := range u.Query() {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	delimiter := "^_^"
	var signBefore strings.Builder
	for _, k := range keys {
		signBefore.WriteString(k + "=" + u.Query().Get(k) + delimiter)
	}
	// GET 请求无 body，用空字符串 + delimiter + secret
	signBefore.WriteString(delimiter + secret)

	h := md5.New()
	h.Write([]byte(signBefore.String()))
	sign := hex.EncodeToString(h.Sum(nil))

	return fmt.Sprintf("%s&sign=%s", signedURL, sign), nil
}
```

注意：PDF 示例中使用的字符集是 utf-8，Go 默认即 utf-8，无误。

- [ ] **Step 4: 将 `readFromMcdnPlatform` 重命名为 `readFromCdnPlatform` 并改造**

```go
func readFromCdnPlatform(logId string) *configVersionPair {
	vodURL := cConf.Config.ThirdRelevant.CdnPlatformVodUrl
	liveURL := cConf.Config.ThirdRelevant.CdnPlatformLiveUrl
	appKey := cConf.Config.ThirdRelevant.AppKey
	appSecret := cConf.Config.ThirdRelevant.AppSecret

	if vodURL == "" && liveURL == "" {
		log.Warn("ConfigVersionCheckModel: CdnPlatformUrl not configured, skip channel A, logId:%v", logId)
		return nil
	}

	result := &configVersionPair{}

	// 读取 live_bcdn_rate_config（调用直播 API）
	if liveURL != "" {
		version, err := fetchVersionFromSignedURL(liveURL, appKey, appSecret, logId)
		if err != nil {
			log.Error("ConfigVersionCheckModel: fetch %v from live API failed, err:%v, logId:%v",
				keyspaceNameLiveBcdnRate, err, logId)
		} else {
			result.LiveBcdnRateConfig = version
			log.Warn("ConfigVersionCheckModel: live API %v version=%d, logId:%v",
				keyspaceNameLiveBcdnRate, version, logId)
		}
	}

	// 读取 vod_mirror_os_config（调用点播 API）
	if vodURL != "" {
		version, err := fetchVersionFromSignedURL(vodURL, appKey, appSecret, logId)
		if err != nil {
			log.Error("ConfigVersionCheckModel: fetch %v from vod API failed, err:%v, logId:%v",
				keyspaceNameVodMirrorOs, err, logId)
		} else {
			result.VodMirrorOsConfig = version
			log.Warn("ConfigVersionCheckModel: vod API %v version=%d, logId:%v",
				keyspaceNameVodMirrorOs, version, logId)
		}
	}

	return result
}

// fetchVersionFromSignedURL 对 URL 添加鉴权签名后发起 GET 请求，解析 version
func fetchVersionFromSignedURL(rawURL, appKey, secret, logId string) (int64, error) {
	req, err := signURL(rawURL, appKey, secret)
	if err != nil {
		return 0, fmt.Errorf("sign url failed: %w", err)
	}

	resp, err := cConf.HttpGet(req)
	if err != nil {
		return 0, fmt.Errorf("http get failed: %w", err)
	}

	return readVersionFromJSON(string(resp), logId)
}
```

注意 `fetchVersionFromPlatform` 可以删除，被 `fetchVersionFromSignedURL` 替代。

- [ ] **Step 5: 更新 Handle() 中的调用链**

```go
func (m *ConfigVersionCheckModel) Handle(logId string) {
	log.Warn("ConfigVersionCheckModel, time:%v, logId:%v", time.Now(), logId)

	// 1. 从 Paladin keyspace 读取配置（通道 B）
	paladinVersions := readFromPaladin(logId)

	// 2. 从视频CDN运管平台读取配置（通道 A，如已配置）
	mcdnVersions := readFromCdnPlatform(logId) // ← 改这里

	// 3. 对比版本
	compareAndAlert(paladinVersions, mcdnVersions, logId)
}
```

- [ ] **Step 6: 删除不再需要的 `fetchVersionFromPlatform` 函数**（被 `fetchVersionFromSignedURL` 替代）

- [ ] **Step 7: 清理 import — 移除不再需要的包**

检查是否有不再使用的 import（如 `fmt`、`strings` 等仍被使用，保留）。需要确认：
- `"go-common/library/log"` — 仍使用 ✓
- `"go-common/library/conf/paladin.v2"` — 仍使用 ✓
- `cConf` — 仍使用 ✓
- `encoding/json` — 仍使用 ✓
- `strings` — `strings.Builder` in signURL ✓
- `time` — 仍使用 ✓
- 新增：`crypto/md5`、`encoding/hex`、`net/url`、`sort`、`strconv`

---

### Task 3: 更新测试

- [ ] **Step 1: 更新测试文件 import**

测试文件导入 `"strings"` 用于 `strings.NewReader`（`readVersionFromJSON` 中使用），确保已导入。

- [ ] **Step 2: 运行 paladin 测试**

```bash
cd /Users/bilibili/Dev/te/.claude/worktrees/config-version-check
ZONE=sh001 DEPLOY_ENV=dev go test -run TestReadFromPaladin -v -count=1 -timeout 180s ./model/intent_model/ 2>&1
```

预期：`--- PASS`，日志中显示从 paladin keyspace 读取到的 version 值。

- [ ] **Step 3: 编译验证**

```bash
cd /Users/bilibili/Dev/te/.claude/worktrees/config-version-check
go build ./model/intent_model/ 2>&1
```

预期：无错误输出。

---

### Task 4: conf.toml 配置更新

- [ ] **Step 1: 确认 conf.toml 中已有 AppKey/AppSecret 配置**

```toml
[third_relevant]
app_key = "xxx"
app_secret = "yyy"
# ... 原有字段 ...
cdn_platform_vod_url = "https://cloud-cdn.bilibili.co/api/ost-res-manager/cdn/playurl/3rd-new/backup"
cdn_platform_live_url = "https://cloud-cdn.bilibili.co/api/live-playurl-control-v2/all"
```

---

## 自审检查

| 检查项 | 结果 |
|--------|------|
| 类型一致 | `readFromCdnPlatform` 返回 `*configVersionPair`，字段 `int64`，与 `compareAndAlert` 匹配 |
| API 映射 | 直播→`live_bcdn_rate_config`，点播→`vod_mirror_os_config` |
| 鉴权实现 | 与 raynor `library/tools/sign/sign.go` 算法一致 |
| 空 URL 处理 | 为空时该通道仅记录 warn 并跳过 |
| 错误传播 | 单个 API 失败不阻断另一个，部分结果仍参与对比 |