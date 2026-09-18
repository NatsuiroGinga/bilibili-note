# LSPR 论文与跨年评价检索笔记

- **最后更新**：2026-09-07
- **当前阶段**：全文与引用核验完成，正在形成综合证据表
- **下一动作**：完成 `证据综述.md` 并执行文档验证

## 已冻结问题

1. 哪些论文直接使用 LSPR 数据，而不是只引用数据集？
2. 是否存在明确的 LSPR23 训练、LSPR24 测试或其他跨年协议？
3. 跨年评价使用哪些任务粒度、指标、基线和统计重复？
4. 论文允许读取哪些目标年信息：无标签特征、少量标签、验证标签、完整测试标签或仅事后分析？
5. 其证据结构如何支撑两个互补机制、联合框架和 `2×2` 消融，而不是退化为单机制或基线盘点？

## 证据等级

- **A**：本地原始 PDF 已读，主张已定位到页码、节、表或公式。
- **B**：合法在线全文已读，主张已定位，原件尚未入库。
- **C**：在线摘要或数据集页面，仅作候选发现。
- **D**：仅题录或搜索片段，不支撑结论。

## 查询记录

### Q1 本地混合索引状态与重建

- 初查命令：`uv run --project scripts/literature_search --locked python -m scripts.literature_search status --json`
- 初查结果：索引存在但 `stale=true`，原因为当前工作树新增 8 份文档；向量模型为 `intfloat/multilingual-e5-small`。
- 处置：按仓库规则执行完整增量构建，完成 `1972` 篇笔记、`150383` 个分块和同数向量。
- 复查结果：`built_at=2026-09-07T03:56:25.880759+00:00`，`stale=false`，`index_sha256=85f40aaae8e44fe723ff9c42d12df5c2a9bc2617e88b6b840cfbc80a5981e586`。

### Q2 本地直接近邻查询

- 统一参数：`--scope local --mode hybrid --offline --top-k 15 --json`；`local` 在工具中规范化为 `paper`。
- 查询式：`LSPR LSPR23 LSPR24 LSPR25 dataset cross-year evaluation`。
- 查询式：`LSPR23 LSPR24 training testing cross-year generalization`。
- 查询式：`Locked Shields Partners Run machine learning deep learning random forest Transformer`。
- 查询式：`Allard Dijk LSPR flow sequence classification`。
- 核心命中：
  - `wiki/papers/datasets/LSPR24/Dijk-2026-LSPR23到LSPR25序列构造跨年评估.md`
  - `wiki/papers/datasets/LSPR24/Leoste-2025-LSPR23到LSPR24跨年泛化.md`
  - `wiki/papers/datasets/LSPR24/Dijk-2024-LSPR23数据集与随机森林复现.md`
  - `wiki/papers/datasets/LSPR24-Locked-Shields实兵演习数据集.md`
- 非直接命中：FT-Transformer IoT、时间漂移表格方法、CESNET-TLS-Year22、FOIL 等只因“跨数据集／跨时间”语义相似被召回，不直接使用 LSPR；不纳入本任务核心证据表。
- 初步结论：本地库已有两篇明确执行 `LSPR23→LSPR24` 的全文研究，一篇 LSPR23 数据论文和一篇 LSPR24 发布论文；需由 Zotero 与在线检索核查是否还有未入库直接使用论文。

### Q3 Zotero 检索

- 语义查询已执行，返回 20 个候选键，但 Zotero 桌面本地接口对每个条目均报 `Connection refused`，无法取得题录。
- 随后用 `LSPR`、`Locked Shields Partners Run`、`Allard Dijk`、`Johan Valdemar Leoste` 做精确检索，均报同一连接错误。
- 官方辅助脚本确认 `local_api_enabled_pref=true`，但 `api_running=false`、`connector_running=false`。尝试按技能规则启动 Zotero 后，接口仍超时。
- 本轮不得把该结果解释为“Zotero 无条目”。已有全文笔记记录四篇核心材料的条目键：`CDDWA2UR`、`XXQ64ZGX`、`M8EZZ9S9`、`U4ZMBMEK`；这些是既有记录，本轮未能实时复查。

### Q4 在线候选与题录核验

- Google Scholar 命令行已安装，但因没有可用 Cookie 报错，未进行认证交互。
- 通用网页检索查询：`"LSPR23" dataset machine learning paper`、`"LSPR24" cybersecurity dataset machine learning`、`"LSPR23" "LSPR24" cross-year`、`"Locked Shields Partners Run" paper`、`"LSPR23" Transformer`、`"LSPR23" random forest`。
- Scite 精确检索 `"LSPR23" OR "LSPR24"` 只返回 Dijk 2024 与 Dijk 2026；SciSpace 返回的其他高相似候选主要是 2023 年私有 Locked Shields 轨迹或其他 IDS 数据集，不是 LSPR23/24 直接使用论文。
- 官方来源交叉核验：ScienceDirect／DOI、IEEE／作者公开全文、TalTech 官方学位库、SSRN、Zenodo 数据发布页。
- 在线扩展没有发现新的、可取得全文且直接执行 LSPR23→LSPR24 的论文。

### Q5 PDF 全文与关键页复核

- 使用 `mineru-open-api flash-extract` 分段读取四篇本地 PDF；长文按独立页码文件写入 `/tmp/lspr-review/`，没有修改 `raw/`。
- 认证状态以 `mineru-open-api auth --verify` 只读确认，输出为令牌格式有效且来源为本机配置；没有显示或记录令牌。
- 对 Leoste 第 51–67、79–86 页和 Dijk 2026 第 21–37 页进一步使用 `mineru-open-api extract` 精确模式，启用表格与公式识别，并以含页码的独立文件名输出。
- 四份原件 SHA-256：
  - Dijk 2024：`d28b3dd264ab41efa270c76c62c325454ec48e40b87bc0fd2a1bc512ee40dc4c`
  - Dijk 等 2025：`bdba910a6e2329202edf41ea7f47690d0676a55e05b0b57e15b709da6f952a71`
  - Leoste 2025：`2905780372be5089a7270e6e5ae6437fd4b5dfe1f9fd70f8c385632a038756dd`
  - Dijk 等 2026：`eccb238307cc46a5f500033d1edefea63d53edc2c7adc79b3695d1eeddf78c95`

## 逐篇记录

### 候选 P1：Dijk 等（2024），LSPR23 数据集论文

- 本地笔记：`wiki/papers/datasets/LSPR24/Dijk-2024-LSPR23数据集与随机森林复现.md`
- 本地原件：`raw/papers/datasets/1-s2.0-S2214212624001492-main.pdf`
- 稳定标识：`10.1016/j.jisa.2024.103847`
- 证据等级：A；本轮已回到原始 PDF 复核研究问题、标签、表 4、表 7 与表 8。
- 纳入理由：官方 LSPR23 发布、标签与字段来源、Suricata 和同年随机森林基线。
- 边界：没有跨年评价；同年 `4:1` 切分细节和精确输入字段未充分披露。

### 候选 P2：Dijk 等（2025），LSPR24 发布论文

- 本地笔记：`wiki/papers/datasets/LSPR24-Locked-Shields实兵演习数据集.md`
- 本地原件：`raw/papers/datasets/2025_Meier_LSPR24_Blue-Team-Automation.pdf`
- 稳定标识：`10.23919/CyCon65856.2025.11103720`；数据 DOI `10.5281/zenodo.14900873`。
- 证据等级：A；本轮已回到原始 PDF 复核第 6 节数据规模、标签改进与指标边界。
- 纳入理由：官方 LSPR24 数据规模、内部／跳板标签改进和发布边界。
- 边界：没有机器学习训练—测试协议或定量模型性能。

### 候选 P3：Leoste（2025），LSPR23→LSPR24 跨年基线

- 本地笔记：`wiki/papers/datasets/LSPR24/Leoste-2025-LSPR23到LSPR24跨年泛化.md`
- 本地原件：`raw/papers/datasets/LSPR24/2025_Leoste_Comparative_Analysis_ML_DL_LSPR23_LSPR24.pdf`
- 官方条目：`https://digikogu.taltech.ee/et/item/49a1c14f-f2c5-4129-a23e-f943ba230816`
- 证据等级：A；本轮已用 MinerU 精确模式复核表 8、10、11 及目标年信息使用段。
- 纳入理由：直接以 LSPR23 训练并冻结到 LSPR24，对比随机森林和一维卷积神经网络，并消融包到达间隔。
- 初步跨年事实：有包到达间隔时两模型 F1 均约 `18.4%`；同年随机切分 F1 约 `99.8%`。
- 目标年权限复核：模型在 LSPR23 训练，LSPR24 不重训；但第 3.4.7 节明确说特征缩减预试曾以 LSPR24 验证，第 4.3 节又用 LSPR24 标签比较有／无 IAT 两套配置。因此它是目标年知情的跨年评价，不能作为严格未触碰目标测试。
- 预处理差异：LSPR23 对数值缺失做中位数填补，LSPR24 评价前直接删除含 `NaN` 行；跨年差值混入预处理口径变化。

### 候选 P4：Dijk 等（2026），三年度序列构造评估

- 本地笔记：`wiki/papers/datasets/LSPR24/Dijk-2026-LSPR23到LSPR25序列构造跨年评估.md`
- 本地原件：`raw/papers/datasets/LSPR24/ssrn-6597680.pdf`
- 稳定标识：`10.2139/ssrn.6597680`
- 证据等级：A；本轮已用 MinerU 精确模式复核表 3 至表 5、切分、指标与统计节。
- 纳入理由：直接比较 LSPR23、LSPR24、LSPR25 的八种序列构造、三类模型及相邻年度冻结评价。
- 初步跨年事实：`LSPR23→LSPR24` 同年选优配置的平均精确率分别由 XGBoost `1.0000→0.2416`、GRU `0.9984→0.1758`、Transformer `0.9964→0.0742`。
- 目标年权限复核：公平选型表按源年同年平均精确率选择配置，再评价下一年；目标年标签用于评价指标。该论文同时对每个年度另做同年训练，故整项研究并非“从未接触目标年”，但公平选型分析的选择规则本身不读下一年表现。
- 关键统计：194 个相邻年度比较中 178 个下降（91.75%）；LSPR23→LSPR24 中位平均精确率差为 `-0.731`；同年平均精确率与跨年差距的相关系数为 `-0.87`。

### 排除 P5：Di Gennaro 等（2026）

- 本地原件：`raw/papers/datasets/LSPR24/2026_DiGennaro_Hierarchical_Hybrid_SDN_IDS.pdf`。
- 排除理由：全文仅在相关工作中引用 LSPR23；全部实验使用 KRONOS-SDN `Open` 交换机子集，没有 LSPR 训练、测试或指标。

## 综合判断草案

- 直接 LSPR 跨年证据目前集中在 Leoste 2025 与 Dijk 2026 两篇，且都以逐流二分类为主；没有论文直接验证本课题的实体级评价、两个机制或联合算法。
- 同年随机验证不能替代跨年选模。Leoste 的同年 F1 约 `99.8%`，下一年仅约 `18.4%`；Dijk 的源年同年选优配置跨年平均精确率保留率只有 `24.16%/17.61%/7.45%`。
- 对本项目，LSPR24 已被历史实验访问；即使当前实现机械保证选型时不读目标数组，也只能报告“`target_informed=true` 的冻结跨年评价／确认性基准”，不能声称“首次开启的独立最终测试”。
- 最终研究结构继续要求两个可独立开关的机制和一个联合框架；LSPR 论文只约束问题、协议、直接基线和证据编排，不足以替代机制来源文献与真实 `2×2` 实验。

## 待核问题

- “LSPR23→LSPR24”是否为论文原作者明确采用的协议，还是本课题基于年度版本自行定义的评价合同。
- 官方数据论文是否给出跨年基线，或仅给出同年训练/测试与数据描述。
- 目标年标签若被用于阈值、模型选择或超参数选择，是否仍被作者称为跨域/跨年泛化，以及该表述是否严谨。
