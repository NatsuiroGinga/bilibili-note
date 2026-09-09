# LAMDA 双风险梯度投影筛查计划

## 目标

检验将 A-GEM 的平均历史损失投影改造成“旧恶意保护＋良性误报”两个风险参考梯度，是否能避免阶段 C 等单位修复损失造成的 FPR 爆炸，同时保留当前恶意样本的监督修复。该候选仍为 `screening_only`，不预设有效或创新成立。

## 文献与实验依据

- A-GEM 原件与笔记：`raw/papers/attack-detection/lamda-related/2019-Chaudhry-A-GEM-Efficient-Lifelong-Learning.pdf`、`wiki/papers/attack-detection/2019-Chaudhry-AGEM高效终身学习.md`；其核心是记忆参考梯度的半空间投影。
- 阶段 C 失败证据：`.Codex/docs/2026-09-09-LAMDA决策角色记忆双侧修复/analysis/analysis-report.md`；等单位损失使开发期 FPR 从 `0.013148` 升至 `0.089252`。
- 数据角色：manifest 冻结的来源年 `2013/2014`、开发年 `2016/2017`、封印年 `2018--2025`。本筛查只枚举来源／开发年。

## 候选定义

每个年度更新开始时保存教师模型 `theta^-`。当前批次梯度为 `g`。从已允许信息构造两个参考梯度：

\[
g_P=\nabla_\theta L_P(\theta),\quad
P=\{(x,1)\in B_{t-1}:h_{\theta^-}(x)=1\},
\]

\[
g_N=\nabla_\theta L_N(\theta),\quad
N=\{(x,0)\in D_t^{train}:h_{\theta^-}(x)=1\}.
\]

依次执行 A-GEM 风格半空间投影：

\[
\Pi_{r}(g)=
\begin{cases}
g,&g^\top r\ge0,\\
g-\dfrac{g^\top r}{\|r\|_2^2}r,&g^\top r<0.
\end{cases}
\]

更新梯度为 `g' = Pi_{g_N}(Pi_{g_P}(g))`。当前训练区的真实恶意样本仍只通过普通 BCE 进入 `g`，不额外复制修复样本；参考梯度只用于方向约束，不使用测试标签。

## 最小实验

- `ER`：标准总容量 200 的 reservoir、普通 BCE。
- `ER+双风险投影`：同一 reservoir、同一训练暴露量，在每批对当前梯度做上述两个参考梯度投影。
- 直接对照：A-GEM 单一平均记忆梯度（若实现成本可控）；不与阶段 C 被否决的等单位风险损失混跑。
- 年份：完整读取 `2013/2014/2016/2017`；开发期只汇总 2016/2017 `current_year`。

## 通过与失败门

- 通过候选筛查的最低条件：开发期 FPR 不高于 ER、旧恶意负向翻转不高于 ER，并且 AP/FNR/恶意正向修复至少一项改善。
- 失败：FPR 上升、只保持旧预测而不修复当前恶意、优于 A-GEM 的差异无法归因于双风险参考、或参考集合使用未来标签。
- 单种子与发布特征未来协变量使所有结果保持 `screening_only`；通过后才允许设计第二机制和联合实验。
