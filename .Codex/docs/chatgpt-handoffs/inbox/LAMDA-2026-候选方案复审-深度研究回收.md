# LAMDA 候选方案复审：深度研究回收

## 交接信息

- 复用会话：`🔎 LAMDA 深度研究`
- 对话地址：<https://chatgpt.com/c/6aa0f8a4-6340-83e9-bed4-0967ab3ffaf0>
- 复审任务：同一会话追加的候选方案审查；未新建会话。
- `actual_model`：`GPT-5.5 Thinking`
- `actual_effort`：`high / deep-research`
- `actual_mode`：`Deep Research`
- `used_apps`：`web.run`，检索公开论文、会议页面、arXiv 和作者／组织官方 GitHub；未使用私有连接器。
- 代码执行：未运行 Python、训练脚本、LAMDA 数据处理或 GPU 实验。

## 复审结论

1. 最终目标应明确为“固定 FPR operating point 下减少恶意 FNR”，而不是单独追求 AP 或 F1。
2. 以当前 ER 开发基准为锚：FPR `0.013148`、FNR `0.059478`、旧恶意负向翻转率 `0.052107`。
3. 筛选硬门建议为：候选 FPR 不高于 `0.013148`，FNR 低于 `0.059478`，旧恶意负向翻转率不高于 `0.052107`。双风险投影的 `0.031984` 只能作安全侧参考，不应升级为硬门，否则会重新奖励过强保护、压制恶意修复。
4. 训练代理约束不能替代真实二值 FPR；必须使用独立且时间一致的良性 gate，并把 source/dev 与最终封印年隔离。
5. PCT/Focal Distillation 负责旧正确决策保护，恶意漏判修复必须单独定义；PCT 不能独自保证 FPR 不升。
6. 双玩家约束应理解为模型玩家与约束玩家的原始—对偶优化，不是攻击者—防守者博弈。TFCO/Cotter 的 two-player／proxy-Lagrangian 是理论来源。
7. MIR/GSS 只在本地证据表明历史 reference 代表性是瓶颈时进入；TERM、DGR、IWMS、主动学习和课程学习不应先于最小候选。

## 与本地四臂结果的冲突处理

复审报告是在本地四臂最终制品回收前生成的，曾建议先完成 gap×conditional-gate 四臂。该动作现已完成，本地结果显示：

- 缺口修复 FNR `0.030905`，但 FPR `0.138637`，违反硬门；
- 条件门控 FPR `0.012232`，但 FNR `0.070306`，且与既有双风险投影行为一致；
- 联合臂 FPR `0.078325`，违反硬门。

因此复审报告中的“先完成 gap×conditional-gate”不再是下一动作；它已被本地证据执行并否决。当前下一动作应转为 PCT 直接基线和独立 FPR gate 的最小筛选。

## 推荐的候选分层

| 层 | 候选 | 角色 | 当前处理 |
| --- | --- | --- | --- |
| 修复层 | 历史真实恶意漏判定向回放 | 提高恶意正向修复 | 当前简单 margin 加权实现已违反 FPR 门，需与保护层重新任务化 |
| 保护层 | PCT／Focal Distillation | 降低旧正确样本回归 | 作为直接基线，不能改名为创新 |
| 安全层 | 独立真实 FPR gate | 约束模型选择与部署验收 | 必须存在，不能只用平滑损失 |
| 约束层 | 双玩家 proxy-Lagrangian | 跨步更新安全预算 | 只有修复候选重新获得可行信号后再筛选 |
| 记忆层 | MIR／GSS | 选择更有代表性的历史 reference | 只有本地诊断证明记忆代表性是瓶颈才进入 |

## 固定信息集合与失败门

- 年度更新允许使用上一冻结模型、当前已到达训练标签、历史回放、已冻结阈值和历史统计；禁止未来标签、封印年结果和事后调阈值。
- `conditional gate` 若几乎每步触发而退化为始终投影，或几乎从不触发且等价 ER，均应停止。
- 双玩家乘子若单调发散、触及人为上限仍违反真实 FPR，说明当前代理和信息集合不可行，不能继续调大乘子。
- 如果平滑代理满足但真实二值 FPR 超标，判定为代理—硬约束不一致。
- 课程学习只有在源年能定义稳定难度顺序、并通过随机／反向顺序对照时才有资格；当前没有 LAMDA 证据。

## 论文与官方代码来源

- Cotter 等，JMLR 2019，arXiv `1809.04198`：proxy-Lagrangian 与不可微 rate constraint。
- Cotter 等，ICML 2019，arXiv `1807.00028`：训练玩家与独立约束验证玩家分离。
- Kumar、Narasimhan、Cotter，ICML 2021，arXiv `2107.10960`：固定 FPR 下优化 FNR 的 rate-constrained 目标。
- Yan 等，CVPR 2021，arXiv `2011.09161`：PCT 与 Focal Distillation。
- Ghiani 等，Regression-aware Continual Learning，arXiv `2507.18313v2`：NFR/PFR 分解与 Android 恶意软件安全回归外部证据。
- Chaudhry 等，A-GEM，ICLR 2019，arXiv `1812.00420v2`：冲突梯度投影。
- Aljundi 等，MIR，NeurIPS 2019，arXiv `1908.04742v3`；GSS，NeurIPS 2019，arXiv `1903.08671v5`：干扰与梯度多样性记忆选择。
- 官方代码入口均已在候选台账或对应全文笔记登记；外部论文数值不得写成 LAMDA 结果。

## 当前决策

本复审支持把第三章主问题写成“恶意漏判修复与低误报约束的联合维护”，但不支持任何候选已在 LAMDA 上有效。下一轮只在 PCT/TFCO 原件和接口核验后，运行最小 PCT＋FPR gate 源年筛选；若仍无候选同时过三项硬门，保留 ER 基线并停止扩展。
