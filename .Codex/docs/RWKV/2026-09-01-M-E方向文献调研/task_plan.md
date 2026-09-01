# M-E 方向文献调研任务计划

- 日期：2026-09-01
- 代理：me_direction_literature_fable（model=fable，effort 继承会话）
- 决策目标：裁决「继续投 M-E」还是「换机制一候选」

## 背景速记

- 机制二 BER（损失层）已过目标年正增益门；机制一原候选 CEM 被目标年负增益否决。
- M-E＝FT-Transformer 数值分词器上的实体历史门控 PLE 位移通道：
  `f_j(x,s_e) = (b_j + x·W_j) + γ_θ(s_e)·Σ_t ε_t(x)·u_t^{(j)}`，
  `γ_θ(s_e) = σ(MLP(s_e))·1[c≥1]`，`s_e=[log(1+c)/log(1+C), log(1+Δ)/log(1+D)]`。
- 已知弱点：(a) 理论只有零门退化/严格过去性/算子计数，无定理；
  (b) 首片段样本（>50%）门恒为零；(c) 源年验证集 20 个正实体只影响 13 个；
  (d) 条件变量 c 源年内部前后半段均值漂移 3.8 倍。

## 四个问题

1. 方向已有工作盘点；M-E 是否为已知方法（FiLM/hypernetwork/条件嵌入）的特例或换名？
2. 是否存在理论更厚（泛化界/表达力/收敛性/信息论/因果）的条件化表示方法？
3. 弱点对应文献：(a) 条件信号稀疏（冷启动/缺失历史）；(b) 条件变量漂移的稳健化。
4. 更适合的机制一候选（表示层/结构层、可挂 FT-Transformer、~10 万参数、无运行时状态机），给 2–3 个并排序。

## 步骤

- [x] 建目录与 task_plan.md / notes.md
- [x] 本地索引 status（fresh，built 2026-08-31，papers=528）
- [x] 本地 hybrid 查询批 1：FiLM / conditional embedding / numerical embedding / hypernetwork
- [x] 本地 hybrid 查询批 2：entity/user conditioning、concept drift robustness、cold start gating
- [x] 复核已有原件与既有裁决（8-28 五篇审计、8-31 门作用域量化、第三章恢复卡）
- [x] 联网检索补缺口（WebSearch 2 组＋arXiv 下载 8 篇原件）
- [x] 关键论断逐条核对公式与页码（FiLM p2-3、LHUC p3 式3、CBN p4 式4-5、GW p5-6 Thm1-3、Pan p2-3、DAIN p2-3 式1-9、ICLAD p9）
- [x] 8 份 wiki 笔记＋INDEX 新增「条件化与特征调制谱系」节
- [x] 写调研报告.md 初稿（判据：理论厚度 → 换候选）
- [x] 接收主进程当轮更正（07147ad 朱第三章交互项证据＋MinerU 强制）：6 处承载公式页面全部 MinerU 复核一致；判据修正为「与 BER 的交互机制解释」
- [x] 重写调研报告.md：**继续投 M-E（附三条件），实体条件不变式归一化预注册为第一替补**
- [x] git add + commit（只加精确路径）

## 证据等级约定

- 【全文级】：原件在 raw/ 或本次下载，已核对公式/页码
- 【摘要级】：只读到摘要/网页，不得支撑论断
- 【推论】/【待验证假设】：无法当下验证的判断
