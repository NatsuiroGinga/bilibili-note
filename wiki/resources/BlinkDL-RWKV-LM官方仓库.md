---
title: "BlinkDL RWKV-LM 官方仓库"
date: 2026-08-08
tags:
  - RWKV
  - 代码仓库
  - RWKV8
  - 外部资源
  - 类型/参考
---

# BlinkDL RWKV-LM 官方仓库

## 资源信息

- 地址：<https://github.com/BlinkDL/RWKV-LM>
- 核验日期：2026-09-07；远端 `HEAD` 为 `9a75f9f037afa4418ee6283b584b92b1adb89ca1`。
- 许可证：Apache-2.0。
- 仓库包含 RWKV-v1 至 RWKV-v8 目录、RWKV-8 设计文档与 ROSA 图件；核验时页面显示约 900 次提交。

## 对机制移植的直接提示

- 仓库明确指出，RWKV-7 不是一个可以脱离初始化、权重衰减和参数组学习率后随意替换的单层；普通 PyTorch 层无法自行保证这些训练条件。把 RWKV-7 机制移植到普通基座时，必须把初始化与参数组策略纳入实验合同。
- 仓库提供 RWKV-7 的参考训练实现、简化实现和 CUDA 内核；简化实现被作者标为“更慢且不同”，不能把其结果与正式实现混为一谈。
- RWKV-8 当前由设计文档与源码承载。ROSA 没有 RWKV-8 正式架构论文；社区预印本 ROSA-Tuning 不能替代官方架构证据。DeepEmbed 在 `RWKV-v7/rwkv_v7a_demo.py` 中以逐层 token 条件前馈通道调制实现，DeepEmbedAttention 在 `rwkv_v7b_demo.py` 中实现且同时保留 DeepEmbed；两者均无独立正式论文和完整公开训练合同。
- 因此 ROSA、DeepEmbed 与 DeepEmbedAttention 只能列为官方代码/设计资源支持的工程候选。直接移植不能构成本课题创新，网络安全效果必须由等容量、破坏性负控和真实泛化轴实验支持。

## 证据边界

- 仓库中的吞吐、显存和性能数字属于作者在特定硬件、形状和实现上的报告，不能外推到本课题。
- 仓库说明不能替代 RWKV、RWKV-5/6、RWKV-7 正式论文的公式和实验引用。
- 仓库演示脚本证明算子与命名存在，不证明 DRIFT 的未来年份、未见家族、低误报或校准问题得到改善。

## 关联

- [[RWKV论文生态目录]]
- [[wiki/papers/RWKV/2025-Peng-RWKV7-Goose|RWKV-7 Goose]]
