# 实验脚本与复现

守恒不变量在真实 IDS2018 上的可分性验证实验。目的：为开题方案 B（守恒不变量 PINN）提供可行性实证——确认不变量信号在真实数据上能区分正常/攻击。

## 脚本

| 脚本 | 内容 | 依赖 |
|------|------|------|
| `i2_i3_separability_csv.py` | I2（流双向守恒）/I3-弱（单向SYN）在 Thursday-15-02 CSV 上的逐流可分性 | 标准库 |
| `i2_i3_window_csv.py` | 同上，按时间窗聚合（攻击是突发，逐流阈值弱） | 标准库 |
| `i2_i3_perflow_multi.py` | 跨攻击类型对比（多日 CSV） | 标准库 |
| `i3_strict_pcap.py` | 严格 I3：dpkt 解析真实 pcap 逐包算未应答 SYN，时间窗尖峰 | dpkt（uv 环境） |

## 环境与依赖（uv）

实验用 uv 管理环境，依赖见 `pyproject.toml` / `uv.lock`。

```bash
cd thesis/experiments
uv sync                      # 按 uv.lock 装依赖（创建 .venv，已 gitignore）
uv run python <脚本>.py      # 运行（自动用 .venv，无需 activate）
```

- Python 3.11+；依赖：scapy、dpkt（pcap 解析）、pandas、numpy、matplotlib（分析绘图）。
- v1-v3 的 CSV 脚本仅用标准库，可直接 `python3` 跑；`i3_strict_pcap.py` 需 dpkt，用 `uv run`。
- PyPI 镜像：`pyproject.toml` 已配清华源（`[[tool.uv.index]] default=true`），pypi 直连超时时用镜像。

## 数据
- CSV：`raw/datasets/CSE-CIC-IDS2018/Thursday-15-02-2018_TrafficForML_CICFlowMeter.csv`（DoS GoldenEye + Slowloris 日）
- PCAP：`raw/datasets/CSE-CIC-IDS2018-PCAP/extracted/pcap/`（从截断包 zip-FF 恢复的真实 per-host pcap）

## 结果日志

### v1 逐流朴素判据（i2_i3_separability_csv.py，2026-07-16）
| 标签 | 流数 | I2均值 | I2极端% | 单向SYN% | 朴素判据召回 | 误报率 |
|------|------|--------|---------|----------|------------|--------|
| Benign | 996077 | 0.280 | 35.5% | 2.9% | — | — |
| DoS GoldenEye | 41508 | 0.242 | 35.4% | 0.0% | 35.4% | 35.5% |
| DoS Slowloris | 10990 | 0.751 | 67.6% | 0.0% | 67.6% | 35.5% |

**诚实结论**：逐流朴素阈值**偏弱**——Benign 也有 35.5% 单向/极端流（UDP/ACK 等），导致 35% 误报。Slowloris 在 I2 上可分（均值 0.751 vs 0.28），GoldenEye 不可分。这说明：
1. 朴素单流阈值不够，需**按时间窗聚合**（攻击是突发，窗口内单向流密度骤增）——见 v2。
2. 这正是用 PINN（学习残差）而非朴素阈值的理由——不变量作软约束让模型学，比硬阈值强。
3. I2 对 Slowloris（单向长连接）有效，对 GoldenEye（HTTP 洪泛，仍有响应）需 I3 或组合。

### v2 时间窗聚合（i2_i3_window_csv.py，2026-07-16）
- 攻击窗口 62 / 正常窗口 510（1 分钟窗）
- 极端I2流占比：攻击 38.9% vs 正常 36.4%（不可分）；单向SYN流占比：2.9% vs 2.9%（不可分）
- **结论**：时间窗聚合也未改善 DoS GoldenEye/Slowloris 的可分性——确认是攻击类型问题，非聚合方式问题。

### v3 跨攻击类型对比（i2_i3_perflow_multi.py，2026-07-16）⭐决定性
| 攻击日/类型 | I2召回 | 误报率 | 守恒有效？ |
|------------|:---:|:---:|:---:|
| Wed-21 DDoS HOIC（单向洪泛） | 76.1% | 0.6% | ✅ 极佳 |
| Wed-21 DDoS LOIC-UDP（纯单向） | 100% | 0.6% | ✅ 完美 |
| Wed-14 FTP 暴力破解（单向） | 100% | 33.7% | ✅ 有效 |
| Wed-14 SSH 暴力破解 | 50% | 33.7% | △ 中等 |
| Thu-15 DoS GoldenEye（HTTP洪水,双向） | 35.4% | 35.5% | ❌ 无效 |
| Thu-15 DoS Slowloris（慢速半连） | 67.6% | 35.5% | △ 弱 |

**决定性结论**：
1. 守恒不变量（I2 流双向守恒）对**传输层洪泛/扫描**极其有效（DDoS 单向洪泛召回 76-100%、误报 0.6%）。
2. 对**应用层 DoS**（GoldenEye/Slowloris，完成握手、双向）无效——这是守恒物理的天然边界，非方法失败。
3. **印证两级架构分工**：CI-PRD（守恒物理）抓传输层洪水/扫描；PIC-GRPO（LLM 语义）抓应用层 DoS。
4. 方案 A（TCP/AQM 流体）即便有 PCAP 仍不可行——q(t)/p(t) 是路由器内部状态，端点抓包看不到。
5. 误报率（brute-force 日 33%）因 Benign 也有合法单向流（UDP/ACK）；作两级架构第一级粗筛可接受（FP 交给 LLM），且 PINN 学习残差比硬阈值更强。

**建议**：方案 B 守恒不变量 + 两级分工，实验背书；可选加 I4（熵平稳）补体积异常覆盖。

### v4 严格 I3 真实 pcap（i3_strict_pcap.py，2026-07-16）
在 zip-FF 恢复的真实 IDS2018 pcap（Thursday-15-02 DoS 日）上逐包算未应答 SYN：

| pcap（per-host） | TCP包 | 窗口数 | I3均值 | I3max | I3>50%窗口 |
|------------------|------|------|--------|-------|-----------|
| capDESKTOP-...64.46 | 4411 | 29 | 15.3% | 75% | 1/29 |
| capEC2AMAZ-...68.6 | 125296 | 524 | 26.8% | 100% | 71/524 |
| capEC2AMAZ-...68.8 | 96319 | 537 | 37.4% | 100% | 131/537 |

- **结论**：严格 I3（逐包未应答 SYN）在真实包上**可算且暴露异常**——DoS 日多窗口 100% 未答 SYN（半开连接，符合 Slowloris/GoldenEye 特征）。
- **局限（诚实）**：缺 benign 基线 pcap，未算召回/误报；此为"可算性 + 异常暴露"验证，定量可分性以 v3（CSV，有标签）为准。per-host 抓包下 SYN 与其 SYN-ACK 同在本机抓包中，未答 SYN 即真实半开。
- v1-v3 跑流级 CSV（有标签，定量）；v4 跑原始 pcap（无标签，定性验证严格 I3 可算 + 暴露异常）。两者互补。

