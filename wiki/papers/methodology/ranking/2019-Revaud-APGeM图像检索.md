---
title: "Learning With Average Precision: Training Image Retrieval With a Listwise Loss"
authors: [Jérôme Revaud, Jon Almazán, Rafael S. Rezende, César Roberto de Souza]
year: 2019
date: 2026-08-13
journal: "Proceedings of the IEEE/CVF International Conference on Computer Vision（ICCV 2019），5107–5116"
source_pdf: "[[raw/papers/methodology/ranking/2019-Revaud-AP-GeM-ICCV.pdf]]"
sha256: "b16a3fd4c48b7a4cef0eaf8147a730fb31178e6982875a8946361c620aea7e12"
tags:
  - 平均精确率
  - 广义均值池化
  - 图像检索
  - 类型/论文
key_finding: "在图像检索中把可反向传播学习阶数的 GeM 池化与列表式可微 mAP 损失联合端到端训练，直接占用“可学习广义均值池化＋直接 AP”这一宽泛组合。"
method: "用软直方图近似 AP，采用多阶段反向传播容纳超大批量；图像描述子由可学习幂次的 GeM 池化产生。"
baseline: "GeM+三元组损失、GeM+对比损失、R-MAC 及其他全局／局部检索表示"
aliases:
  - AP-GeM
  - GeM-AP
  - Revaud2019-APGeM
---

# AP-GeM：可学习 GeM 与列表式 AP 的直接组合

> Revaud 等，2019，ICCV · 10 个物理页 · Zotero `JMWPSGXB`（另有一次导入残留重复项 `HYETU4UY`，未擅自删除）

## 论文原结论

- 第 3—4 页公式（2）—（12）从 AP 定义出发，用三角核软分箱替代不可微排序，得到批内列表式 `mAP_Q` 损失。
- 第 5 页给出三阶段反向传播：先计算全部描述子，再计算列表损失对描述子的梯度，最后逐图重算并累积网络梯度；它解决的是显存而不是随机包无偏性。
- 第 6 页明确说明 GeM 幂次与其他权重一起通过反向传播学习；第 6—7 页表 1—2直接报告 `GeM (AP)`，说明可学习广义均值和直接 AP 已经在同一训练管线中出现。
- 第 6 页还按类均衡批内 AP 权重，说明“对组等权的列表 AP”也有相邻先例，但其组是图像类别，不是可变流数实体。

## 与本课题的关系

- **被占用点**：不能声称首次组合可学习 `Lp`／GeM 与 AP、首次让池化阶数受 AP 梯度学习、或首次做组均衡 AP。
- **关键差异**：本文对图像空间位置做 GeM，再按图像检索关系优化批内 mAP；没有实体内随机 K 流、有限总体矩方差、实体均匀目标测度、逆概率校正或因果跨流编码。
- **仍可主张**：面向可变长网络实体、以设计型两级抽样恢复实体均匀 AP 目标并控制复合偏差的任务特定算法；但不能把原始构件拼装本身当作原创。
- **实验待证**：该任务特定设计是否超过同预算的 `GeM/AP` 直接迁移、SOAP/SOX 与完整实体基线。

## 证据记录

- 全文：CVF 正式开放版本，10 页；关键位置为物理第 3—7 页。
- 官方页：<https://openaccess.thecvf.com/content_ICCV_2019/html/Revaud_Learning_With_Average_Precision_Training_Image_Retrieval_With_a_Listwise_ICCV_2019_paper.html>
- 证据强度：当前最直接的机制近邻之一；尚非本课题完整同构。

