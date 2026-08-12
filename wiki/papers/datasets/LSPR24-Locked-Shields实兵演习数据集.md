---
title: "Next Steps in Cyber Blue Team Automation：LSPR24 数据集发布与蓝队自动化展望"
authors:
  - Allard Dijk
  - Roland Meier
  - Cosimo Melella
  - Mauno Pihelgas
  - Risto Vaarandi
  - Vincent Lenders
year: 2025
date: 2026-08-05
journal: "17th International Conference on Cyber Conflict"
source_pdf: "[[raw/papers/datasets/2025_Meier_LSPR24_Blue-Team-Automation.pdf]]"
dataset_doi: "10.5281/zenodo.14900873"
tags:
  - LSPR24
  - 网络入侵检测
  - NetFlow
  - 早期告警
  - 数据集
  - 类型/论文
key_finding: "LSPR24 含约 2000 万流、31.6 小时连续实兵式演习活动、逐流起止时间与红队关联标签，并改进内部及跳板流标注；它可作为广义网络流序列任务的条件首选，但攻击叙事的提交时间不等于真实动作起点。"
aliases:
  - LSPR24-Locked-Shields实兵演习数据集
  - LSPR24 数据集发布论文
related:
  - "[[resources/LSPR24-Zenodo数据发布页|LSPR24 Zenodo 官方数据发布页]]"
---

# Next Steps in Cyber Blue Team Automation：LSPR24 数据集发布与蓝队自动化展望

## 一句话

LSPR24 是本轮广义网络流量任务的条件首选；它能支撑生成式长序列状态与流完成级早期检测，但不能未经映射审计就声称全量真实攻击起点时延。

## 一级证据

- 官方论文第 13 至 14 页给出约 2000 万流、20 亿个包、287 GB 传输量、31.6 小时活动、约 1.3 万个 IPv4／IPv6 地址，其中 372 个地址与红队关联。
- 官方论文第 14 页明确说明，相比 LSPR23，LSPR24 改进了内部流标注，以更准确地分类跳板攻击。
- Zenodo 记录提供 2.8 GB 的 `lspr24_v2.parquet`、11.3 MB 攻击叙事、145.4 MB `eve.log` 和 5.0 GB 主机日志，合计约 8.0 GB。
- Zenodo 官方元数据接口将数据许可标为 CC0。
- 本地 PDF SHA-256：`bdba910a6e2329202edf41ea7f47690d0676a55e05b0b57e15b709da6f952a71`。

## 标签和事件边界

- `Label`、`Label_src` 与 `Label_dst` 只能用于真值、分组与评价，不能进入模型输入。
- 红队地址、主机名、`Expoid_*`、`Segment_*` 及其可逆编码同样禁止进入主轨，否则模型可能只记住身份。
- 攻击叙事包含空时间和非攻击任务；`Steps_submitted_time` 是提交时间，不是攻击开始时间。
- 主延迟应定义为“第一条已标恶意流完成至首次告警”。只有能把真实动作时间唯一映射到流、目标与端点的子集，才能另报动作起点时延。
- 完整流统计只能在 `mTimestampLast` 后使用，不能在 `mTimestampStart` 时把终态持续时间、字节或到达间隔暴露给模型。

## 对本课题的用途

第三章可按受保护端点或端点对重建因果窗口，预测下一窗口的流、包、字节、协议和连接状态分布。第四章可在相同外生轨迹上研究继续观察／告警的约束最优停止。正式训练前仍需核验事件覆盖、时间前向拆分、去身份非退化和困难面板样本数。

## 研究类型与指标边界

- 这是 **LSPR24 的发布与描述性分析来源**，不是在 LSPR24 上训练并比较机器学习模型的下游使用论文。
- 第 13 至 14 页报告数据规模、逐小时良恶流活动和 Suricata 告警曲线，并定性指出 Suricata 假阳性很多；论文没有给出 Suricata 的准确率、精确率、召回率、F1 或平均精确率。
- 因此不能把该论文计入“有可比较模型指标的 LSPR24 使用论文”，但它仍是数据来源、标签改进和发布事实的一级证据。

## 禁止主张

- 不能把红队关联标签解释为逐载荷确认的攻击效果。
- 不能把构造的连续阳性段称为官方攻击事件。
- 不能声称覆盖全部攻击家族或生产网零样本泛化。
- 不能把静态历史上的停止动作写成能够改变网络环境的在线强化学习。

## Evidence Record

- Evidence ID: ER-20260808-lspr24-release-01
- Source: Dijk 等 2025 会议论文全文，第 13 至 14 页，第 6 节
- Source type: full paper
- Supports: LSPR24 数据来源、规模、内容、逐小时活动和标签改进
- Contradicts: 把公开数据集自动视为已有成熟下游基线的假设
- Method / dataset / metric: 描述性统计与 Suricata 曲线；无定量模型评价指标
- Limitation: 没有训练／测试协议、模型对比或误差统计
- Project relevance: 数据真实性、字段与标签边界的一级来源
- Claim strength: supported

## 来源

- 论文：<https://roland-meier.ch/files/2025_CyCon_AI.pdf>
- 数据：<https://doi.org/10.5281/zenodo.14900873>
- 论文 DOI：<https://doi.org/10.23919/CyCon65856.2025.11103720>
- Zotero 条目键：`XXQ64ZGX`
