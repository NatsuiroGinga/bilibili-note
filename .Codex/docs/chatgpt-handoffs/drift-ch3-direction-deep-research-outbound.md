---
requested_mode: deep-research
requested_model: auto
requested_effort: high
fallback_model: 普通ChatGPT当前可用的高能力模型，降档前明确说明
requested_apps: [Sider Scholar, Scite, GitHub]
actual_model: 未投递，待界面核验
actual_effort: 未投递，待界面核验
status: 待主代理投递普通ChatGPT
---

# 域名检测抗漂移方法的公开文献定点排重

请在普通 ChatGPT 深度研究中执行，只做公开文献发现与反例审查。启动前核对界面可用模式、模型和剩余额度；不要转入 ChatGPT Work、Workspace Agents 或 Codex。采用高能力可用模型和高推理强度，并报告实际配置。

## 公开问题

域名字符串恶意检测常使用字符/子词表示与遮蔽恢复、顺序验证等自监督任务。请比较以下三类整体方法的最近邻、先例和失败条件，不提出数据集专属参数或宣称任何新方法有效：

1. 用源侧留出家族/环境的主任务验证反馈选择辅助更新：相对静态任务子集、普通验证驱动调权、ForkMerge、梯度手术和课程学习，还可能有哪些实质差量？
2. 无标签自监督测试时适应：冻结分类头，更新编码器或轻量对象，并限制误报/漏报伤害；哪些工作真正研究 DGA 或恶意软件？哪些只是视觉/异常检测？是否使用未来标签、真值类别平衡、完整目标批统计或非因果选择？
3. 用局部字符/子词键估计专家相对可靠性并选择分支：与动态专家、质量感知融合、条件记忆及普通错误预测的区别是什么？键能预测错误为何不足以证明可纠错？

## 已知公开题录

- DRIFT: Drift-Resilient Invariant-Feature Transformer for DGA Detection，DOI `10.1109/DSN69566.2026.00077`，arXiv `2605.10436`。
- MADCAT: Combating Malware Detection Under Concept Drift with Test-Time Adaptation，arXiv `2505.18734`。
- ForkMerge: Mitigating Negative Transfer in Auxiliary-Task Learning，NeurIPS 2023，DOI `10.52202/075280-1322`。
- SoTTA: Robust Test-Time Adaptation on Noisy Data Streams，Gong 等，NeurIPS 2023。
- Gradient Surgery for Multi-Task Learning，arXiv `2001.06782`。
- GradNorm: Gradient Normalization for Adaptive Loss Balancing in Deep Multitask Networks，arXiv `1711.02257`。
- 非平稳域泛化 AIRL，arXiv `2405.06816`；MalMoE，arXiv `2602.10157`。

## 范围与工具

- 候选发现优先 Sider Scholar；不可用时改 Consensus。用 Scite 核对引用语境，用 GitHub 核对作者公开实现的数据权限。不要全工具轮流重复查同一题目。
- 最多返回六篇最能改变排重判断的新增直接近邻，允许零篇。不扩展到无关网络安全任务或笼统的大模型综述。
- 每项给题录、稳定标识、全文 URL、相关页码/公式、公开数据权限、最近邻覆盖、关键反例、尚需实证的问题。
- 区分已读全文、仅摘要、仅题录；摘要和题录不能支撑机制归属、创新否决或效果结论。
- 对明显重复的方案直接说明重复在哪里；没有不可约差量就说没有，不为凑数生成模块。

## 交付

一页候选矩阵加简短反例清单；附查询式、检索时间、实际模型/模式/强度、不可获取全文清单。所有输出标记“外部候选，待本地全文和实验复核”。不裁决具体实验、不修改研究合同、不执行代码、不索取仓库、数据、日志、模型、权重、目标期信息或任何凭据。
