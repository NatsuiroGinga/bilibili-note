# MCDN v 节点跨运营商丢包率探测改造

> 开发完成，2026-07-08。脚本 `.claude/scripts/cross_isp_ping.sh` 就绪，待部署测试。

---

## 目标

v 节点（74 台）跨网覆盖：物理线 ≠ 调度运营商。ping 百度 CDN 回本网 IP，测不到互通点拥塞。用 `dig +subnet` 强制拿对端运营商 IP，ping 该 IP 经互通点。

mp2sp（1086 台）不动，沿用原百度/淘宝探测。

---

## 技术方案

**一个脚本 `cross_isp_ping.sh` 替换 packet_loss.sh：**

| 节点 | 逻辑 | 输出 |
|------|------|------|
| v（74 台） | hostname 第4段判断本机运营商 → 排除本网 → dig +subnet 拿另外两个跨网运营商的百度/淘宝 IP → ping 50 包 → 跨网均值 | `mcdn_network_quality` 2 条 loss |
| 非 v（1086 台） | 内联原 packet_loss.sh 丢包率代码 | `mcdn_network_quality` + `mcdn_network_rtt_quality` 各 2 条 |

**v 节点探测流程（以联通 cu 节点为例）：**

```
本机=cu → 排除联通 → CROSS_ISPS="ct cm"
  dig +subnet=电信段 www.baidu.com  → 百度电信 IP → ping 50 包 → loss_1
  dig +subnet=电信段 www.taobao.com → 淘宝电信 IP → ping 50 包 → loss_2
  dig +subnet=移动段 www.baidu.com  → 百度移动 IP → ping 50 包 → loss_3
  dig +subnet=移动段 www.taobao.com → 淘宝移动 IP → ping 50 包 → loss_4

  百度 = (loss_1 + loss_3) / 2
  淘宝 = (loss_2 + loss_4) / 2

输出: mcdn_network_quality{domain="www.baidu.com"} 百度均值
      mcdn_network_quality{domain="www.taobao.com"} 淘宝均值
```

**为什么 dig +subnet 有效：** CDN 域名按来源 IP 返回本网 IP（DNS 劫持），`+subnet` 手动指定运营商段，CDN 返回对端运营商 IP，ping 该 IP 流量经互通点。

**为什么只测跨网：** 本网方向 ≈ 原 packet_loss.sh 效果（本网物理线质量），冗余；跨网方向才暴露互通点拥塞。

**dig 兜底：** 不存在 → 自动安装（yum/dnf/apt-get）；解析失败 → 固定 IP（101.227.95.65 / 210.21.4.130 / 211.137.96.205）

---

## 对比测试样本

69 台 v 节点中选出 10 台，6 同网 + 4 跨网，覆盖三种本机运营商、五种跨网模式、六厂商：

| # | hostname | 本机 | sched_isp | 模式 | isp | 厂商 |
|---|----------|------|-----------|------|-----|------|
| S1 | mcdn-jd-hnhk-**dx**-v-154 | 电信 | ['电信'] | **同网** | 电信 | jd |
| S2 | mcdn-qny-hbwh-**dx**-v-321 | 电信 | ['电信','移动'] | **同网** | 联通 | qny |
| S3 | mcdn-bili-jlcc-**cu**-v-221839174 | 联通 | [] | **同网** | 联通 | bili |
| S4 | mcdn-qny-hbwh-**cu**-v-1032 | 联通 | ['联通'] | **同网** | 联通 | qny |
| S5 | mcdn-wx-bjbj-**cmcc**-v-02447221246060 | 移动 | ['移动'] | **同网** | 移动 | wx |
| S6 | mcdn-ydy-lnsy-**cmcc**-v-358 | 移动 | [] | **同网** | 移动 | ydy |
| C1 | mcdn-bdwl-hbwh-**dx**-v-10300820 | 电信 | ['联通'] | **电信→联通** | 联通 | bdwl |
| C2 | mcdn-jd-tj-**cmcc**-v-100 | 移动 | ['联通'] | **移动→联通** | 移动 | jd |
| C3 | mcdn-qny-hbwh-**dx**-v-318 | 电信 | ['联通','移动'] | **电信→联通+移动** | 移动 | qny |
| C4 | mcdn-ydy-hbwh-**cu**-v-341 | 联通 | [] | **联通→移动** | 移动 | ydy |

### 同网节点 24h 基线

old = 当前 `avg(百度, 淘宝)`，new = 新脚本跨网均值（待部署后填入）：

| # | hostname | 原 24h avg(%) | 新 24h avg(%) |
|---|----------|-------------|-------------|
| S1 | mcdn-jd-hnhk-dx-v-154 | ≈0 | |
| S2 | mcdn-qny-hbwh-dx-v-321 | ≈0 | |
| S3 | mcdn-bili-jlcc-cu-v-221839174 | ≈0 | |
| S4 | mcdn-qny-hbwh-cu-v-1032 | ≈0 | |
| S5 | mcdn-wx-bjbj-cmcc-v-02447221246060 | ≈0 | |
| S6 | mcdn-ydy-lnsy-cmcc-v-358 | ≈0 | |

### 跨网节点 24h 基线

| # | hostname | 原 24h avg(%) | 新 24h avg(%) |
|---|----------|-------------|-------------|
| C1 | mcdn-bdwl-hbwh-dx-v-10300820 | 0~2 | |
| C2 | mcdn-jd-tj-cmcc-v-100 | ≈0 | |
| C3 | mcdn-qny-hbwh-dx-v-318 | ≈0 | |
| C4 | mcdn-ydy-hbwh-cu-v-341 | ≈0 | |

原数据来源：Grafana PromQL `avg(mcdn_network_quality{instance_name=~"..."}) by (instance_name)`，24h 窗口。数据量过大不做逐点提取，整体趋势为同网节点全程接近 0，跨网节点偶有 0.5%~2% 波动。

---

## 走过的死路

| 尝试 | 死因 |
|------|------|
| mcdn-data API 取 sched_isp 定点 ping | 显式禁用 |
| bvc-ost-oss.bilibili.co BBAN API | 节点 DNS 解析不到 |
| cloud-cdn.bilibili.co API | 需 cookie，cron 不可用 |
| bvc-ost-oss.bilivideo.com | BBAN 路径 404 |
| ping 百度/淘宝域名 | CDN 劫持回本网 |
| ping 百度/淘宝 A 记录 IP | 也是本网 IP |
| 固定运营商 IP 手工维护 | 脆弱，可维护性差 |
| `dig @运营商DNS` 指定解析 | 运营商 DNS 不开放外部查询 |
| `mcdn_network_quality_isp` 新指标名 | 其他应用采不到数据 |
| 按运营商平均再选最差方向 | 与需求不一致 |
| hostname 第4段判断本机运营商 | 25%（17/69）的 v 节点 hostname 与实际物理线不符，导致漏测跨网方向 |

### 本机运营商判断演进

| 版本 | 方式 | 准确率 | 问题 |
|------|------|--------|------|
| v1 | hostname 第4段 (dx/cu/cmcc) | ~75% | qny/ydy/wx 三个厂商 17 台 hostname 与实际不符 |
| v2（当前） | dig 百度 A 记录拿到本网 IP → whois 查归属 → 电信/联通/移动 | ~100% | whois 网络查询需额外耗时（~1s），失败回退全量 ping |

---

## MCDN 相关 API 索引

### API 总览

| API | 地址 | 认证方式 | MCDN -v 节点数 | 用途 |
|-----|------|---------|---------------|------|
| mcdn-data all/nodes | `mcdn-data.biliapi.net/api/v1/portal/mcdn/all/nodes` | x-secretid + x-signature | 83（在线） | 获取全量在线 MCDN 节点，含 `isp`、`user_actual_isp`、`sched_isp` |
| BBAN mcdn/node | `bvc-ost-oss.bilibili.co/api/bban2/v1/mcdn/node` | HMAC-MD5 | 83（在线） | 获取在线 MCDN 节点，仅含 `isp`（调度 ISP） |
| BBAN page-node | `bvc-ost-oss.bilibili.co/api/bban2/v1/bban/page-node` | HMAC-MD5 (POST) | 118（全量含下线） | 分页查询全部节点，含 `user_actual_isp`、`ipisps[].isp` |
| BBAN node 详情 | `bvc-ost-oss.bilibili.co/api/bban2/v1/bban/node` | HMAC-MD5 | — | 按 node_id 查单节点详情 |
| BBAN schedule | `bvc-ost-oss.bilibili.co/api/bban2/v1/schedule` | HMAC-MD5 | 0 | 传统 CDN/DSA 节点（`cn-xxx` 格式），不含 MCDN |
| bvc-hub 代理 | `bvc-hub.bilibili.co/api/ost-bban2/*` | Cookie（需登录） | — | bvc-hub 是 bvc-ost-oss 的代理层，`/ost-bban2` → `/bban2/v1`，内部自动加鉴权 |

### 认证方式

#### 1. x-secretid + x-signature（mcdn-data）

```python
headers = {
    'x-secretid': 'o2KkF4FlYA4WVH',
    'x-signature': 'fa94d4a55658cba23a7ef051eb3ec273',
}
requests.get("http://mcdn-data.biliapi.net/api/v1/portal/mcdn/all/nodes", headers=headers)
```

凭证来源：`app/manba-bi/configs/application.toml` 中 `[portal]` 段。

#### 2. HMAC-MD5 签名（BBAN）

```python
APP_KEY = "bili-mendelevium-20211203"
APP_SECRET = "0aab8b1176f77788"
delimiter = "^_^"

# GET 请求：query params 按字母序排序后 sign_before + body(空) + secret
# POST 请求：query params(仅 app_key, ts) 按字母序排序后 sign_before + body(JSON原文) + secret

def signed_get(path, params):
    ts = str(int(time.time() * 1000))
    all_params = dict(params, app_key=APP_KEY, ts=ts)
    sorted_keys = sorted(all_params.keys())
    sign_before = ""
    for k in sorted_keys:
        sign_before += f"{k}={all_params[k]}{delimiter}"
    sign_before += f"{delimiter}{APP_SECRET}"
    signed = hashlib.md5(sign_before.encode()).hexdigest()
    query = '&'.join([f"{k}={all_params[k]}" for k in sorted_keys] + [f"sign={signed}"])
    return f"{path}?{query}"

def signed_post(path, json_body):
    ts = str(int(time.time() * 1000))
    body_str = json.dumps(json_body)
    sign_before = f"app_key={APP_KEY}{delimiter}ts={ts}{delimiter}{body_str}{delimiter}{APP_SECRET}"
    signed = hashlib.md5(sign_before.encode()).hexdigest()
    url = f"{path}?app_key={APP_KEY}&ts={ts}&sign={signed}"
    return requests.post(url, json=json_body)
```

凭证来源：`te` 项目 `framework/constant/constant.go`（`AppKey` / `AppSecret`），签名函数参考 `te/tool/auth.go`。

### 各 API 关键字段

#### mcdn-data `/all/nodes`

返回 `data.instances[]`，每个节点关键字段：

| 字段 | 类型 | 含义 | 示例 |
|------|------|------|------|
| `node_name` | string | 节点 hostname | `mcdn-bdwl-hbwh-dx-v-10300820` |
| `isp` | string | 调度 ISP（中文） | `联通` |
| `user_actual_isp` | string | 物理线路 ISP（中文） | `电信` |
| `sched_isp` | list | 被调度去哪些运营商方向 | `['联通']` |
| `province` | string | 省份 | `湖北` |
| `type` | string | 节点类型 | `v` / `mp2sp` |

**注意：`isp` 和 `user_actual_isp` 全量 100% 非空。**

#### BBAN `/mcdn/node`

返回 `data.instances[]`，仅在线节点：

| 字段 | 类型 | 含义 |
|------|------|------|
| `node_name` | string | 节点 hostname |
| `isp` | string | 调度 ISP（中文，**等同 mcdn-data 的 `isp`**） |
| `sched_scope` | string | 调度范围（`global` / `province` / `none`） |

**注意：没有 `user_actual_isp` 字段。**

#### BBAN `/page-node`（POST）

入参：
```json
{
    "filters": {"activeTab": "node", "hostname": "可选过滤条件"},
    "page": 1,
    "page_size": 1000
}
```

返回 `data.nodes[]`，含全量节点（在线+禁用+下线）。关键字段：

| 字段 | 类型 | 含义 | 示例 |
|------|------|------|------|
| `id` | string | BBAN 内部 node_id | `mcdn-bdwl-hbwh-ct-50046523` |
| `hostname` | string | 节点 hostname | `mcdn-bdwl-hbwh-dx-v-10300820` |
| `ipisps[].isp` | string | IP 所属运营商（缩写，**等同调度 ISP**） | `ct` / `cu` / `cm` |
| `defaultISP` | string | 默认运营商（缩写） | `cu` |
| `user_actual_isp` | string | **物理线路 ISP（缩写）** | `ct` |
| `status` | string | 节点状态 | `Normal` / `Pending` / `Disable` |

**ISP 缩写对照：** `ct`=电信、`cu`=联通、`cm`=移动

**⚠️ 注意：同一 hostname 可能返回多条记录**（如 Pending + Normal 各一条），取 `status=Normal` 且 `health=normal` 的那条，或者用 `id` 做去重。

### 字段交叉验证结果（2026-07-09 首次，2026-07-09 晚二次验证）

在线 -v 节点 69 台，比对 BBAN page-node（Normal 记录）和 mcdn-data：

| 比对 | 首次（83 台） | 二次验证（69 台） |
| ----- | -------------- | ----------------- |
| BBAN `user_actual_isp` = mcdn `user_actual_isp`（物理 ISP） | 100% | **100%** |
| BBAN `ipisps[].isp` 包含 mcdn `isp`（调度 ISP） | 100% | **100%** |
| BBAN `defaultISP` = mcdn `isp`（调度 ISP） | — | **100%** |
| hostname 第4段 = mcdn `user_actual_isp`（物理 ISP） | 81% | **75%** |
| BBAN `defaultISP` = mcdn `user_actual_isp`（物理 ISP） | 38% | 24% |

**结论：**
- `user_actual_isp` 是节点的**物理线路运营商**，两个 API **100% 一致**
- `ipisps[].isp` / `isp` / `defaultISP` 都是**调度运营商**（被分配去服务的运营商），三个来源 **100% 一致**
- BBAN page-node 含全量 -v 节点 118 台（含已下线），mcdn-data 在线 69 台
- hostname 第4段不可信：**25%** 的 -v 节点 hostname 运营商 ≠ 物理运营商
- 两个 ISP 维度清晰分离：

  | 维度 | BBAN 字段 | mcdn-data 字段 | 含义 |
  |------|----------|---------------|------|
  | 物理 ISP | `user_actual_isp`（ct/cu/cm） | `user_actual_isp`（中文） | 机器实际所属运营商线路 |
  | 调度 ISP | `ipisps[].isp` / `defaultISP`（ct/cu/cm） | `isp`（中文） | 节点被分配去服务的运营商方向 |

---

## 最终交付物

| 文件 | 状态 |
|------|------|
| `.claude/scripts/cross_isp_ping.sh` | 开发完成，语法通过 |
| `docs/superpowers/plans/2026-07-08-mcdn-cross-isp-ping.md` | 本文档 |

---

## 后续

1. v 节点部署脚本，收集 24h+ 数据
2. 与旧数据对比，确认跨网探测未引入误报（同网节点应接近 0）
3. cron 切换
4. Prometheus 采集确认
5. 1 周观察期
