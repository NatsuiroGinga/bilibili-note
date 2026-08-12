---
title: "NetMamba: Efficient Network Traffic Classification via Pre-training Unidirectional Mamba"
authors:
  - Tongze Wang
  - Xiaohui Xie
  - Yong Cui
  - 等
year: 2024
date: 2026-08-08
journal: "ICNP 2024；arXiv:2405.11449v4"
source_pdf: "[[raw/papers/traffic-foundation-models/2405.11449_NetMamba_高效流量分类状态空间.pdf]]"
tags:
  - 流量基础模型
  - NetMamba
  - Mamba
  - 状态空间模型
  - 骨干候选
  - 类型/论文
key_finding: "NetMamba = 4 层单向 Mamba 编码器 + 2 层解码器（预训练 2.2M / 微调 1.9M 参数），输入固定为流前 5 个包 × (80 头部 + 240 载荷) = 1600 字节切成 400 个 4 字节 stride，MAE 掩码率 0.9；它是把 Mamba 块整体换成 RWKV-7 的最干净对照载体，但其架构消融显示 Mamba 相对 vanilla Transformer 的优势只有 0.5—2.6 个百分点。"
---

# NetMamba

> Wang 等, 2024, ICNP 2024 · arXiv:2405.11449v4，8 页

## 一句话

第一个把 Mamba 用于流量分类的模型，规模极小（<2.5M 参数）、输入表示简单可复用，架构消融给出了"骨干替换"实验所需的全部对照点（双向 Mamba、级联 Mamba、vanilla Transformer、Linear Transformer）。

## 论文证据

- 第 4 页 §V 与表 II/III：超参完整给出——`M=5`（每条流取前 5 个包）、`Nh=80`（每包头部字节）、`Np=240`（每包载荷字节）、`Lb=1600`（单流字节数组长度）、`Ls=4`（stride 长度）、`Ns=400`（stride 数）、`L=401`（含尾部 class token 的序列长度）、`Lvis=41`（掩码率 r=0.9 后可见 token 数）、`Denc=256`、`Ddec=128`、`Eenc=512`、`Edec=256`、`N=16`（SSM 状态维）。编码器 4 个 Mamba 块，解码器 2 个。
- 第 4 页 §V-2：**去偏做法**——排除 ARP/DHCP 等非 IP 协议包；"通过移除以太网头对所有包做匿名化"。注意本版**只删以太网头，未删 IP 地址与端口**（这一点在 NetMamba+ 中才补上，见 [[2026-Wang-NetMamba-Plus-多模态与长尾微调]]）。头部与载荷各自定长（80/240）以做"字节平衡"，超长裁剪、不足补齐。
- 第 4—5 页 §V-4：一维 stride 切分（沿字节序列切非重叠的 1×4 段）取代二维 patch，理由是二维 patch 会把垂直相邻但语义无关的字节分到同一 token。
- 第 5 页 §VI-A-1 与式 (4)：class token **追加在序列末尾**（因为单向 Mamba 从前往后处理，末尾 token 才能聚合全序列）；微调时只把末尾 class token 送 MLP 头。
- 第 5—6 页 §VI-B 与式 (5)—(7)：MAE 式预训练，随机 shuffle 后保留前 `Lvis` 个 token 进编码器，class token 恒不被掩码；解码器用 mask token + 新位置嵌入重建，损失为掩码 stride 的 MSE。微调换成 MLP 头 + 交叉熵。
- 第 6 页 §VII-A-1：六个数据集——CrossPlatform(Android) 254 类、CrossPlatform(iOS) 253 类、ISCXTor2016 8 类、ISCXVPN2016 7 类、CICIoT2022 6 类、USTC-TFC2016 20 类；对每类设流数上下限，低于下限丢弃、高于上限随机采样；8:1:1 划分，微调 120 epoch。
- 第 7 页表 IV/V：NetMamba 准确率 0.9094（CP-Android）/0.9301（CP-iOS）/0.9928（CICIoT2022）/0.9986（ISCXTor）/0.9805（ISCXVPN）/0.9960（USTC-TFC）。相对最好基线的 F1 提升自述为 **0.18%—0.31%**（第 7 页 §VII-B-1），且在 CICIoT2022 上**落后 YaTC 最多 0.72 个百分点**、在 ISCXVPN/USTC-TFC 上略逊于 YaTC。
- 第 8 页表 VI（消融，本文对本课题最关键的一张表）：
  - 换成双向 Mamba：六数据集里五个略降（CP-Android 0.9094→0.9012），CICIoT2022 反而升到 0.9974。
  - 换成级联 Mamba：全面显著下降（CP-Android 0.8194）。
  - 换成 **vanilla Transformer**：0.8836/0.9058/0.9938/0.9973/0.9632/0.9954——与 Mamba 的差距仅 **0.5—2.6 个百分点**，CICIoT2022 与 ISCXTor 上 Transformer 反而更好。
  - 换成 **Linear Transformer**：崩溃（CP-iOS 0.4226），作者归因于注意力过度压缩。
  - 去位置嵌入：降 0.03%—2.17%（说明 Mamba 的隐式位置信息不够）。
  - 去预训练：降 0.20%—4.70%。
  - **去头部：降 15.51%—48.75%**（w/o Header 在 ISCXVPN 上 0.9805→0.5058）。
  - 去载荷：只降 0.16%—0.84%，且 ISCXTor 上**去掉载荷后准确率反而升到 1.0000**。
  - 换二维 patch：最多降 1.88%。
- 第 7 页 §VII-C 与式 (10)—(12)：给出复杂度比较 Ω(vanilla)=4LD²+2L²D、Ω(linear)=3LD²+2LD、Ω(SSM)=96LD+32LD；推理速度较基线快 1.22—60.11 倍，batch=64 时比最佳基线 YaTC(OF) 快 2.24 倍。
- 第 8 页 §VII-E：few-shot 用 leave-one-out（微调数据集从预训练集合中剔除），即**预训练语料就是这六个数据集本身**——这正是 netFound 指出 NetMamba 把 Crossmarket 用进预训练的依据。
- 第 8 页 §VIII 结论：自陈"当前实现依赖专用 GPU 硬件，限制了在真实网络设备上的部署"。

## 与本课题六个关注点的对照

- (a) 输入形态：**原始字节**（头部 80 + 载荷 240，前 5 包）。与本课题的窗口级统计特征不同构；若复用其表示，需要自建"字段/统计 → stride"的适配层。剔除的只有以太网头，IP 与端口仍在输入中（潜在捷径）。
- (b) 有效历史：硬性 5 个包、1600 字节，**无任何包数或字节数长度消融**。序列长度恒为 401。
- (c) 跨字段交互：只靠单向 SSM 的顺序状态传递，没有显式跨字段机制；消融显示去掉显式位置嵌入就掉最多 2.17%，说明状态本身对位置/字段结构的编码不充分。
- (d) 预训练目标与规模：单一目标（掩码 stride 重建 MSE），掩码率 0.9；预训练 150,000 步、batch 128，语料即上述六个公开集（leave-one-out）。
- (e) 评测缺陷：预训练与微调同源是明确的泄漏路径；netFound 表 3 实测其嵌入平均余弦相似度 0.96（严重塌缩），冻结编码器 ISCX-VPN F1 仅 0.1362。
- (f) 可得性：代码 github.com/wangtz19/NetMamba（论文脚注 1）；权重许可证论文未标注。

## 论文自陈局限与消融缺失

- 唯一自陈局限是"依赖专用 GPU 算子，难以部署到资源受限设备"（第 8 页 §VIII）。没有讨论泄漏、捷径、分布漂移。
- 消融缺失：无序列长度/包数消融、无 stride 长度 `Ls` 消融、无掩码率消融、无状态维 `N` 消融、无模型规模缩放实验、无多种子与置信区间（全表为单点数字）。
- 被回避的劣势：正文用"consistently achieves accuracy above 90%"包装，但表 IV/V 显示 NetMamba 在 6 个数据集中只有 3 个第一，CICIoT2022 上被 TFE-GNN 的 1.000 全面压制；"提升 0.18%—0.31%"是绝对百分点，按错误相对下降口径 CP-Android 从 YaTC(OF) 0.9077 到 0.9096 只有 (0.0923-0.0904)/0.0923 = **+2.1%**，属噪声量级。
- Mamba 相对 vanilla Transformer 的分类优势在多数集上小于 1 个百分点，其主要卖点实为**推理效率**而非表达力。这直接约束"把 Mamba 换成 RWKV-7"这类替换实验的可期望增益上限。

## 允许主张

- NetMamba 提供了参数量 <2.5M、序列长度固定 401、单向递归骨干的流量分类完整流水线，是"骨干模块整体替换"最干净的实验载体。
- 其消融表给出了同一表示方案下 Mamba / 双向 Mamba / 级联 Mamba / vanilla Transformer / Linear Transformer 的横向对照，可直接作为 RWKV-7 替换实验的对照基线集合。
- 包头字段是主信号、载荷贡献接近零（去载荷仅降 0.16%—0.84%，个别集上升）——这条与本课题"字段交互是主信号"的实测方向一致。

## 禁止主张

- 不能说 Mamba/SSM 在流量分类上比 Transformer 更准——同表示下差距 0.5—2.6 个百分点且方向不一致。
- 不能把其六数据集高分当作泛化证据：预训练语料与微调数据集同源，且第三方（netFound）实测其冻结表示塌缩、下游冻结 F1 极低。
- 不能把"5 个包"当作有效历史的实证结论，论文无长度消融。
- 不能声称其权重可自由商用——许可证未标注。

## 相关

- [[2026-Wang-NetMamba-Plus-多模态与长尾微调]]（同组期刊扩展版）
- [[2026-Beltiukov-netFound-协议感知流量基础模型]]（第三方对其表示质量的负面实测）
- `wiki/papers/rwkv/2024-Wang-NetMamba-网络流量分类.md`（RWKV 路线下已有的同论文笔记，视角不同；若需合并请以本篇为流量基础模型主线正本）
