# RWKV 论文检索

## 结论

RWKV（Receptance Weighted Key Value）试图兼顾 Transformer 的可并行训练和循环网络的高效推理。其核心研究主线是语言模型架构演化、长上下文、高效部署，以及向视觉和多模态任务迁移。

## 一、原始架构与后续演化

1. [RWKV: Reinventing RNNs for the Transformer Era](https://aclanthology.org/2023.findings-emnlp.936/)，Peng 等，2023，EMNLP Findings。提出 RWKV；训练可并行化、推理计算和状态内存随序列长度保持常数级。Sider Scholar 记录为 316 次引用。
2. [Eagle and Finch: RWKV with Matrix-Valued States and Dynamic Recurrence](https://arxiv.org/abs/2404.05892)，Peng 等，2024，预印本。提出 Eagle（RWKV-5）与 Finch（RWKV-6），引入多头矩阵值状态和动态递归。
3. [RWKV-X: A Linear Complexity Hybrid Language Model](https://arxiv.org/abs/2504.21463)，Hou 等，2025，预印本。以 RWKV 处理短程依赖、稀疏注意力处理长程上下文，目标是在训练保持线性复杂度、解码保持常数复杂度。

## 二、高效部署与压缩

1. [RWKV-edge: Deeply Compressed RWKV for Resource-Constrained Devices](https://arxiv.org/abs/2412.10856)，Choe、Ji、Lin，2024，预印本。组合结构优化和后训练压缩，面向机器人、手机等设备。
2. [RWKVQuant: Quantizing the RWKV Family with Proxy Guided Hybrid of Scalar and Vector Quantization](https://arxiv.org/abs/2505.03803)，Xu 等，2025，预印本。提出适配 RWKV 非线性和权重分布特点的后训练量化方法。

## 三、视觉、多模态与生成模型扩展

1. [Vision-RWKV: Efficient and Scalable Visual Perception with RWKV-Like Architectures](https://arxiv.org/abs/2403.02308)，Duan 等，2024，预印本。将 RWKV 改造为视觉骨干网络，面向高分辨率视觉和稠密预测。
2. [RWKV-CLIP: A Robust Vision-Language Representation Learner](https://arxiv.org/abs/2406.06973)，Gu 等，2024，预印本。以 RWKV 构建视觉语言表示学习模型，并处理网页图文数据的噪声问题。
3. [Diffusion-RWKV: Scaling RWKV-Like Architectures for Diffusion Models](https://arxiv.org/abs/2404.04478)，Fei 等，2024，预印本。把 RWKV 式架构用于图像扩散生成，针对高分辨率输入降低空间聚合复杂度。
4. [SpikeGPT: Generative Pre-trained Language Model with Spiking Neural Networks](https://arxiv.org/abs/2302.13939)，Zhu 等，2023，预印本。受 RWKV 启发，以脉冲神经网络构建生成式语言模型。

## 四、综述与辅助入口

1. [A Survey of RWKV](https://arxiv.org/abs/2412.14847)，Li 等，2024，预印本。涵盖 RWKV 原理、语言和视觉应用、与 Transformer 的比较及开放问题。

## 建议阅读顺序

1. 先读原始论文，理解时间混合、通道混合及训练/推理形态。
2. 再读 Eagle and Finch，掌握 RWKV-5/6 的状态和递归机制。
3. 若关注超长上下文，读 RWKV-X。
4. 若关注端侧部署，读 RWKV-edge 和 RWKVQuant。
5. 若关注非文本任务，按 Vision-RWKV → RWKV-CLIP → Diffusion-RWKV 的顺序阅读。

## 局限性

- 除原始 EMNLP Findings 论文外，本清单中的多项核心工作仍以预印本形式发布；使用前应核验正式发表版本、代码和复现结果。
- Consensus 和 scite 当前不可用，因此未提供智能引文、全文摘录或跨论文的引文立场统计。
