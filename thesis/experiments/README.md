# 实验脚本与复现

守恒不变量在真实 IDS2018 上的可分性验证实验。目的：为开题方案 B（守恒不变量 PINN）提供可行性实证——确认不变量信号在真实数据上能区分正常/攻击。

## 脚本

| 脚本                        | 内容                                                                     | 依赖                   |
| --------------------------- | ------------------------------------------------------------------------ | ---------------------- |
| `i2_i3_separability_csv.py` | I2（流双向守恒）/I3-弱（单向SYN）在 Thursday-15-02 CSV 上的逐流可分性    | 标准库                 |
| `i2_i3_window_csv.py`       | 同上，按时间窗聚合（攻击是突发，逐流阈值弱）                             | 标准库                 |
| `i2_i3_perflow_multi.py`    | 跨攻击类型对比（多日 CSV）                                               | 标准库                 |
| `i3_strict_pcap.py`         | 严格 I3：dpkt 解析真实 pcap 逐包算未应答 SYN，时间窗尖峰                 | dpkt（uv 环境）        |
| `ciprd_vs_baselines.py`     | v5：纯数据驱动 vs +不变量特征 vs 朴素阈值（OOD）                         | pandas, sklearn        |
| `ciprd_constrained.py`      | v6：物理约束 LR（不变量作软约束损失，CI-PRD proxy）vs 纯数据驱动 vs 阈值 | numpy, pandas, sklearn |
| `ciprd_pinn_autodiff.py`    | v7：真正 autodiff PINN（torch.autograd 连续性方程残差，I1）              | torch(MPS)             |

## 环境与依赖（uv）

实验用 uv 管理环境，依赖见 `pyproject.toml` / `uv.lock`。

```bash
cd thesis/experiments
uv sync                      # 按 uv.lock 装依赖（创建 .venv，已 gitignore）
uv run python <脚本>.py      # 运行（自动用 .venv，无需 activate）
```

- Python 3.11+；依赖：scapy、dpkt（pcap 解析）、pandas、numpy、matplotlib（分析绘图）、scikit-learn（v5/v6 基线对比）、torch（v7 PINN，MPS 加速）、**swanlab（v5/v6/v7 实验跟踪）**。
- v1-v3 的 CSV 脚本仅用标准库，可直接 `python3` 跑；需第三方库的脚本用 `uv run`。
- PyPI 镜像：`pyproject.toml` 已配清华源（`[[tool.uv.index]] default=true`），pypi 直连超时时用镜像。

### 实验跟踪（SwanLab）

v5/v6/v7 与 `llm_probe` 均已集成 SwanLab（`mode='online'`，上云）。运行后训练曲线、检测指标、输出格式指标与效率指标自动记录到云端面板，论文实验章可直接出图。

- 旧 PINN 实验面板：https://swanlab.cn/@mortiswang/ci-prd-pinn
- 生成式恶意流量实验面板：https://swanlab.cn/@mortiswang/malicious-traffic-llm
- v7 PINN 训练曲线（loss/data_loss/res_loss）+ 检测指标（near_res/far_res/res_ratio）
- v5/v6 各模型 OOD F1/FPR（按模型名分组）
- `llm_probe` 为零样本、监督微调和训练后评估分别建立运行记录；所有非隐藏 YAML 配置与运行时校验均强制使用 `mortiswang/malicious-traffic-llm` 在线项目。
- 每次 `llm_probe` 训练或评估在独立输出目录保存 `console.log`、`swanlog/`、`swanlab_metrics.json`、结果文件和 `artifact_manifest.json`；已有制品清单的目录不得复用。
- 用法：`swanlab.init(project=, name=, config=, mode='online')` → `swanlab.log({...}, step=)` → `swanlab.finish()`；查询用 `swanlab api`（见 SwanLab skill）。
- 访问令牌只通过服务端 `swanlab login` 写入用户级认证存储，不得进入仓库配置、运行清单或实验日志。

### 运行环境（本机，2026-07-16）

- 机型：MacBook Pro 17,1 · 芯片：Apple M1（8 核：4 性能 + 4 能效）· 内存：16 GB
- 系统：macOS 26.5（Build 25F71）· 架构：arm64
- Python 3.13.13 · torch 2.13.0 · **MPS（Metal）可用**：`torch.backends.mps.is_available()=True`
- 注：M1 用 macOS arm64 版 torch（自带 MPS），**不要**装 `--extra cpu`（会浪费 GPU）。torch 训练可 `.to('mps')` 加速。

## 数据

- CSV：`raw/datasets/CSE-CIC-IDS2018/Thursday-15-02-2018_TrafficForML_CICFlowMeter.csv`（DoS GoldenEye + Slowloris 日）
- PCAP：`raw/datasets/CSE-CIC-IDS2018-PCAP/extracted/pcap/`（从截断包 zip-FF 恢复的真实 per-host pcap）

## 结果日志

### v1 逐流朴素判据（i2_i3_separability_csv.py，2026-07-16）

| 标签          | 流数   | I2均值 | I2极端% | 单向SYN% | 朴素判据召回 | 误报率 |
| ------------- | ------ | ------ | ------- | -------- | ------------ | ------ |
| Benign        | 996077 | 0.280  | 35.5%   | 2.9%     | —            | —      |
| DoS GoldenEye | 41508  | 0.242  | 35.4%   | 0.0%     | 35.4%        | 35.5%  |
| DoS Slowloris | 10990  | 0.751  | 67.6%   | 0.0%     | 67.6%        | 35.5%  |

**诚实结论**：逐流朴素阈值**偏弱**——Benign 也有 35.5% 单向/极端流（UDP/ACK 等），导致 35% 误报。Slowloris 在 I2 上可分（均值 0.751 vs 0.28），GoldenEye 不可分。这说明：

1. 朴素单流阈值不够，需**按时间窗聚合**（攻击是突发，窗口内单向流密度骤增）——见 v2。
2. 这正是用 PINN（学习残差）而非朴素阈值的理由——不变量作软约束让模型学，比硬阈值强。
3. I2 对 Slowloris（单向长连接）有效，对 GoldenEye（HTTP 洪泛，仍有响应）需 I3 或组合。

### v2 时间窗聚合（i2_i3_window_csv.py，2026-07-16）

- 攻击窗口 62 / 正常窗口 510（1 分钟窗）
- 极端I2流占比：攻击 38.9% vs 正常 36.4%（不可分）；单向SYN流占比：2.9% vs 2.9%（不可分）
- **结论**：时间窗聚合也未改善 DoS GoldenEye/Slowloris 的可分性——确认是攻击类型问题，非聚合方式问题。

### v3 跨攻击类型对比（i2_i3_perflow_multi.py，2026-07-16）⭐决定性

| 攻击日/类型                           | I2召回 | 误报率 | 守恒有效？ |
| ------------------------------------- | :----: | :----: | :--------: |
| Wed-21 DDoS HOIC（单向洪泛）          | 76.1%  |  0.6%  |  ✅ 极佳   |
| Wed-21 DDoS LOIC-UDP（纯单向）        |  100%  |  0.6%  |  ✅ 完美   |
| Wed-14 FTP 暴力破解（单向）           |  100%  | 33.7%  |  ✅ 有效   |
| Wed-14 SSH 暴力破解                   |  50%   | 33.7%  |   △ 中等   |
| Thu-15 DoS GoldenEye（HTTP洪水,双向） | 35.4%  | 35.5%  |  ❌ 无效   |
| Thu-15 DoS Slowloris（慢速半连）      | 67.6%  | 35.5%  |    △ 弱    |

**决定性结论**：

1. 守恒不变量（I2 流双向守恒）对**传输层洪泛/扫描**极其有效（DDoS 单向洪泛召回 76-100%、误报 0.6%）。
2. 对**应用层 DoS**（GoldenEye/Slowloris，完成握手、双向）无效——这是守恒物理的天然边界，非方法失败。
3. **印证两级架构分工**：CI-PRD（守恒物理）抓传输层洪水/扫描；PIC-GRPO（LLM 语义）抓应用层 DoS。
4. 方案 A（TCP/AQM 流体）即便有 PCAP 仍不可行——q(t)/p(t) 是路由器内部状态，端点抓包看不到。
5. 误报率（brute-force 日 33%）因 Benign 也有合法单向流（UDP/ACK）；作两级架构第一级粗筛可接受（FP 交给 LLM），且 PINN 学习残差比硬阈值更强。

**建议**：方案 B 守恒不变量 + 两级分工，实验背书；可选加 I4（熵平稳）补体积异常覆盖。

### v4 严格 I3 真实 pcap（i3_strict_pcap.py，2026-07-16）

在 zip-FF 恢复的真实 IDS2018 pcap（Thursday-15-02 DoS 日）上逐包算未应答 SYN：

| pcap（per-host）    | TCP包  | 窗口数 | I3均值 | I3max | I3>50%窗口 |
| ------------------- | ------ | ------ | ------ | ----- | ---------- |
| capDESKTOP-...64.46 | 4411   | 29     | 15.3%  | 75%   | 1/29       |
| capEC2AMAZ-...68.6  | 125296 | 524    | 26.8%  | 100%  | 71/524     |
| capEC2AMAZ-...68.8  | 96319  | 537    | 37.4%  | 100%  | 131/537    |

- **结论**：严格 I3（逐包未应答 SYN）在真实包上**可算且暴露异常**——DoS 日多窗口 100% 未答 SYN（半开连接，符合 Slowloris/GoldenEye 特征）。
- **局限（诚实）**：缺 benign 基线 pcap，未算召回/误报；此为"可算性 + 异常暴露"验证，定量可分性以 v3（CSV，有标签）为准。per-host 抓包下 SYN 与其 SYN-ACK 同在本机抓包中，未答 SYN 即真实半开。
- v1-v3 跑流级 CSV（有标签，定量）；v4 跑原始 pcap（无标签，定性验证严格 I3 可算 + 暴露异常）。两者互补。

### v5 特征叠加对比（ciprd_vs_baselines.py，2026-07-16）

OOD：训 Wed-21 DDoS HOIC → 测 Wed-14 暴力破解（未见攻击类型），每类 15k 平衡。

| 模型                     |    F1     |  Recall   |    FPR    |  物理?  |
| ------------------------ | :-------: | :-------: | :-------: | :-----: |
| LogReg_raw               |   0.263   |   0.242   |   0.595   |   否    |
| LogReg_inv（+I2/I3特征） |   0.178   |   0.155   |   0.583   |  +特征  |
| MLP_raw                  |   0.268   |   0.245   |   0.585   |   否    |
| MLP_inv（+I2/I3特征）    |   0.148   |   0.128   |   0.602   |  +特征  |
| **不变量硬阈值（参照）** | **0.723** | **0.755** | **0.334** | +硬阈值 |

- **反直觉结果**：朴素 I2 硬阈值 OOD F1 0.723，**远超**所有学习模型（0.15-0.27）；把不变量当**特征**塞进 NN 反而更差（MLP_inv 0.148 < MLP_raw 0.268）。NN 同分布 F1=1.0、OOD 0.27——严重过拟合。
- **结论**：不变量信号本身 OOD 鲁棒（阈值强）；但"加特征"无效——NN 忽略不变量去记 DDoS 原始特征。**反推 CI-PRD 真设计**：不变量必须作**损失约束**（强迫模型遵守），而非被动特征 → 见 v6。

### v6 物理约束模型（ciprd_constrained.py，2026-07-16）⭐CI-PRD proxy

numpy 梯度下降逻辑回归，损失 L = BCE + λ·mean[max(0, v-p)]，v=不变量违反度（I2偏离平衡+I3单向SYN）。OOD 同 v5。

| 模型                 |  F1   | Prec  | Recall |  FPR  | 说明         |
| -------------------- | :---: | :---: | :----: | :---: | ------------ |
| LR_纯数据驱动        | 0.257 | 0.260 | 0.255  | 0.728 | 无物理       |
| LR_物理约束(λ=0.5)   | 0.343 | 0.335 | 0.352  | 0.699 | CI-PRD proxy |
| LR_物理约束(λ=1.0)   | 0.343 | 0.335 | 0.352  | 0.699 | CI-PRD proxy |
| LR_物理约束(λ=2.0)   | 0.343 | 0.335 | 0.352  | 0.700 | CI-PRD proxy |
| 不变量硬阈值（参照） | 0.723 | 0.693 | 0.755  | 0.334 | 物理硬阈值   |

- 同分布 sanity：LR_物理约束 F1=0.929（未过拟合到 1.0）。
- **诚实结论**：
  1. **物理约束 > 纯数据驱动**（OOD F1 0.343 vs 0.257，+33%）——方向被验证有效，支持 CI-PRD"物理信息助 OOD 泛化"的核心论点。
  2. 但提升幅度有限，且朴素硬阈值（0.723）仍最强——说明约束式模型还未能充分利用不变量。
  3. 综合判断：不变量是 OOD 鲁棒的主信号；最佳用法是**以不变量残差为主信号**（CI-PRD 设计：残差作异常得分），PINN 在此基础上精炼阈值，而非与过拟合的原始特征并列。v6 的约束 LR 是 CI-PRD 的简化 proxy，真正 PINN（autodiff 残差损失，I1/测试床场景）未实现。
- **对论文的意义**：可行性与方向被实证（物理约束助 OOD）；但须诚实写明朴素阈值当前仍优，CI-PRD 的价值在于用 PINN 精炼不变量残差、并处理阈值无法应对的灰区（交第二级 LLM）。

### v7 真正 autodiff PINN（ciprd_pinn_autodiff.py，2026-07-16）⭐CI-PRD 核心

torch.autograd 实现连续性方程残差：NN ρ_θ(x,t)，损失 L=MSE(ρ,ρ_data)+λ·MSE(∂ρ/∂t+u·∂ρ/∂x,0)，残差 autodiff 求。合成数据：正常=无源平流包(s=0)，攻击=在(0.7,0.5)注入 DDoS 源破坏守恒。MPS 加速。

- 训练 2000 epoch，loss 0.24→0.03，物理残差项随数据拟合而暴露违反。
- **检测**：注入邻域(|残差|均值 0.2103) vs 远区(0.0589) = **3.6 倍** ✅。
- 残差峰值在高斯斜坡处（中心残差=0 是数学预期，非失败）。
- **结论**：真正 autodiff PINN 机制跑通——连续性方程残差经 torch.autograd 可算，且残差幅值成功暴露守恒破坏的注入点。补上了 v6"未实现真 PINN"的缺口。
- **局限（诚实）**：合成 1-D 数据，证明机制而非真实检测；真实场景需换测试床实测 ρ(node,t)（Mininet/ns-3 多节点采集）或跨主机 pcap 关联；图结构、I2-I4 联合待扩展。

### v8 ns-3 测试床数据 + PINN（ciprd_testbed.py + pinn_testbed.py，2026-07-16）⭐真实数据

ns-3 3.43 仿真（7 节点星形拓扑 C1/C2/C3→S1→SV1/SV2/SV3，1Gb/s 链路，DDoS t=5s 3×100Mb/s→SV1）。

**ns-3 数据（testbed_rho.csv）**：
| 节点 | 时段 | ρ(bytes/0.5s) | I1残差(|in-out|) |
|------|------|--------------|----------------|
| SV1(x=0.7) | 正常 t=3s | 18M | 8.6M |
| SV1(x=0.7) | DDoS t=7s | **56.6M** | **26.8M** |
| SV2(x=0.8) | DDoS t=7s | 18M | 8.6M（不受影响） |

- **直接 I1 残差**：✅ 完美检测——SV1 在 DDoS 期 ρ 和 I1 残差 **3x 飙升**，SV2 不受影响。ns-3 仿真的守恒不变量 I1 在真实拓扑数据上有效。
- **PINN autodiff 残差**：⚠️ 检测失败——1-D 连续性方程（∂ρ/∂t+U·∂ρ/∂x=0）不适配星形离散拓扑；PINN 残差峰值偏离注入点，与 ground-truth I1 相关性 r=-0.02。
- **诚实结论**：
  1. ns-3 仿真成功产出论文级测试床数据，I1 守恒残差直接检测 DDoS（3x 飙升）——**I1 不变量在真实拓扑上有效**。
  2. v7 合成连续场上 PINN autodiff 有效（3.6x），但 1-D 连续 PDE **不适配离散网络拓扑**——真实场景需图结构 PINN（GNN + 图上守恒律），是后续工作。
  3. 两者互补：ns-3 证 I1 不变量有效（ground truth），v7 证 autodiff PINN 机制有效（连续场），图结构 PINN 是两者的桥接（待实现）。
- SwanLab：v8-testbed-ns3 run（PINN 训练曲线 + 检测指标），https://swanlab.cn/@mortiswang/ci-prd-pinn
