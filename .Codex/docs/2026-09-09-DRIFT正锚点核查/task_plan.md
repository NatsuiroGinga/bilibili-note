# DRIFT 正锚点资格核查计划（2026-09-09）

**状态：✅ 已完成（2026-09-10，全量 30 万/年）+ K4 补测完成。裁决见 §八。**

## 八、最终裁决（2026-09-10，含 K4 补测与 MPS 敏感性冲突的解决）

**裁决：route/selection 族正锚点判定【未通过】——信号脆弱且无结构，不构成 CARS 立项资格。**

读数链：
1. 低阶键问二（主探针 89324 前向流）：coverage 2885、rescued 1339、induced 1546、**net −207**。
2. 低阶键问二（K4 脚本、同一特征缓存经分类头重算）：coverage 4089、rescued 2401、induced 1688、**net +713**——对齐诊断确认两实现代码逐位等价，差异全部来自 **MPS 前向位级非确定性**（与 LAMDA 线已登记的 MPS 非确定放大机制同源）。
3. 冲突根因：lookup 的正效用**集中在 10 个候选 cell 中的 1 个**，且该 cell 的效用值贴着 0——前向噪声即可翻转其符号。同一模型同一数据，两次前向流给出相反符号的裁决。
4. 问一 lookup BA 0.9598 仅比置信度启发式（0.9555）高 0.43pp——伪成功形态（报告预警）被负锚对照识别。
5. K4 联合表示键：与低阶键读数逐位相同（cell 分配未变），无增量信息。
6. 支路实力 10.7:1 完全不对称（char 独对 97,546 vs subword 9,135）——"which-branch"退化为单侧问题。

**按"符号在重跑间翻转的读数不得进入候选排序"纪律：route 族正锚点不通过。CARS 不立项；N14 撤销；LR/gate 训练无依据。**

豁口如实登记：若未来消除 MPS 非确定性（固定确定性核或 CPU 全量重跑）后该单 cell 效用稳定为正，route 族可复议；但"单一 cell 承载全部信号"的结构本身已足以否定章级机制潜力。

### 下一动作（建构者流程，用户已裁决混合形态出局）

route 族关闭后，按"成熟家族取件"循环转向 **N13 测试时适应（TTA）家族**：TENT/CoTTA/SAR 在 drift 基准上已发表正增益、DRIFT 逐年面板是主场、原论文未做。第一步 = TENT 式最小臂（熵最小化只适应归一化层统计/参数，T18 单年）证正增益，再谈任务化。协议四项（到达顺序/无标签接口/更新对象/分表）由主代理按最小证伪原则拟定后随方案交用户。

## 一、任务定位

DRIFT 第三章恢复卡"唯一下一动作"：标准可学习门控的正锚点资格核查。
外部设计来源：深度研究报告 (6)（`.Codex/docs/chatgpt-handoffs/inbox/deep-research-report (6).md`，LAMDA 树，GPT-5.5 Thinking high/deep-research，用户回收）的"可学习门控的正锚点资格核查"节（两问式零梯度设计）；主进程补充 LR 选择器版作交叉证据。

## 二、研究问题（跑前冻结）

DRIFT 官方模型的三个冻结动作（静态融合 C00 / char 反事实支 / subword 反事实支）在源年存在 35% 判定分歧、C00 错误中 6,823/10,356/11,499 个至少一支可纠（T17/T18/T19 聚合制品）。问题：**推理时可观测的键能否跨源年稳定预测 (a) 哪支更可靠、(b) 覆盖 C00 是否净受益？**

## 三、判据（冻结，出数即裁决）

- **问一（which-branch）**：T17 的 exclusive-correct 样本（恰一反事实支正确）按 cell（K1 三路判定模式 × K2 置信差符号 × K3 冲突强度四分位）统计偏好 → lookup 表直接用于 T18。通过 = balanced accuracy 严格 > 0.5 且 covered_n ≥ 1000；**置信度启发式为负锚对照**（同覆盖子集上若 lookup 不优于启发式则视为伪成功）。
- **问二（override）**：T17 按 cell 学效用表（u_k = 挽回数 − 改错数，cell 样本 ≥50），最优效用支为正才覆盖 → T18 执行。通过 = coverage > 0 且 net（rescued − induced）> 0。
- **裁决映射**：两问全过 → CARS 有立项资格，交 Sol 落正式研究卡由用户裁决；问一过/问二不过 → "M1-v2 冲突搬到 route 层"反驳成立，CARS 降级为 BGO 类窄方案或关闭；问一不过 → 选择/路由族关闭，N14 撤销，新研究卡不立。

## 四、实现合同

- **反事实语义与全部前向函数复用原工具** `tools/ch3_drift_official_branch_conflict_diagnostic.py`（extract_features/probabilities/branch_features），分类概率 = softmax[:,1]；中和均值 = T17 benign+DGA **val 全量**（30 万）合并分支特征均值（config `full:true`，已实测修正过取样偏差：前 6000 抽样均值曾致 subword 挽回=0 的假象）。
- 模型：`runs/models/drift-official-dsn2026/finetuning.pt`（24,180,226 参数），官方快照 model.py/tokenizer。
- 数据：T17/T18 val 全量（各 30 万域，`{year}_{benign,dga}_val.parquet`）。**T19 与 T20–T25 不读取。**
- 运行：MPS（`PYTORCH_ENABLE_MPS_FALLBACK=1`，Transformer mask 检查算子无 MPS 实现，该算子落 CPU）。无标签泄漏；LR 选择器（C=1.0）仅用 gate 特征（两反事实概率、|差|、融合概率、差值对、字符串统计 5 维）。
- 禁止：读 T20+ 数据、训练主干、改判据、运行中改样本。

## 五、制品

- `positive_anchor_probe.py`（本目录，py_compile 通过）
- `positive-anchor-result.json`（运行终态，含两问判读与判据对照）
- `probe-console.log`（运行控制台）
- 自检记录：融合错误率 0.0278 vs 既有制品 0.02825（6000 域抽样，结构对齐 ✓）

## 六、已知风险

- K3 分位箱边界在 T17 上算、T18 复用——若 T18 分布偏移大，cell 覆盖率可能不足（已在判据里以 covered_n 防守）。
- MPS fallback 使前向偏慢（全量约 20–40 分钟）；若中断按脚本幂等重跑（无检查点，直接重跑）。
- 两问 lookup 的 cell 最小样本阈值（30/50）是任务化设定，无文献依据，已在方案中声明；若结果对阈值敏感，报告将附敏感性说明。

## 七、后续（判据通过时才启动）

1. Sol 落 CARS 正式研究卡（thesis/methods/，含消融八臂 C00/C-H/C-STACK/C-MOE/C-L2D/C-A/C-K/CARS 与通过门 ΔFPR≤0、未见家族 FNR 改善或宏 TPR 改善、源年不塌）；
2. 文献排重：报告点名的 MoE (Shazeer 2017 §2)、multi-expert L2D (Verma AISTATS 2023)、PiCCE (Liu 2026)、SERAC、PCT、CADE、DWM 需本地全文核验；
3. 用户裁决冻结。
