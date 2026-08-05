---
title: "分布漂移下预测不确定性与事后校准失效"
authors: [Yaniv Ovadia, Emily Fertig, Jie Ren, Zachary Nado, D. Sculley, Sebastian Nowozin, Joshua Dillon, Balaji Lakshminarayanan, Jasper Snoek]
year: 2019
date: 2026-07-30
journal: "NeurIPS 2019"
source_pdf: "[[raw/papers/pinn/protocol-adaptive/2019-Ovadia-Uncertainty-Dataset-Shift.pdf]]"
zotero_item_key: "MTKK55LQ"
zotero_citekey: "ovadia_can_2019"
zotero_attachment_key: "EUH6QLFC"
sha256: "b35489681c8bc2b3bae1f9122a97a0b7acd4e2bff604591cb36b7e6bbba612ec"
key_finding: "同分布验证集上的温度缩放不能保证分布漂移后的校准，轻微漂移即可破坏事后置信度，且漂移越强不确定性质量通常越差。"
tags:
  - 不确定性
  - 分布漂移
  - 置信度校准
  - 类型/论文
aliases:
  - Ovadia2019-Uncertainty
  - Uncertainty Under Dataset Shift
---

# 分布漂移下预测不确定性与事后校准失效

## 一句话

在 GeNIS 上校准良好不能证明 TQH 或新采集期的协议置信度可信，未知回退必须由跨源评价保护。

## 方法与证据

- PDF 第 1 至 2 页：论文把校准评价扩展到连续增强的协变量漂移和完全分布外数据，并比较温度缩放、随机失活、模型集成及贝叶斯近似。
- PDF 第 2 页：事后校准在独立同分布测试上可用，但在轻微输入漂移下也可能失败。
- PDF 第 5 至 6 页：验证集温度缩放不保证漂移数据校准；其 Brier 分数随漂移明显恶化，模型集成在多数设置更稳健。
- PDF 第 10 页总结：准确率与不确定性质量都会随漂移恶化，同分布上的较好校准通常不能迁移到漂移场景。

## 对 R2 的约束

- 校准评估必须包含按数据源、采集期、QUIC 版本和无握手条件的留一测试，而不是随机行拆分。
- 同时报告 Brier 分数、负对数似然、期望校准误差、覆盖率-错误率曲线和未知拒识率。
- 置信度低或跨源失配时必须关闭专属专家，只保留共享守恒；不得以最大概率强制路由。
- 模型集成可作上限复核，但不能因额外计算预算与 C 不匹配而成为唯一主方法。

## 文献信息

- 官方页面：https://papers.nips.cc/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html
