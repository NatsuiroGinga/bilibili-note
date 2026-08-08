# 协议自适应多动力学 PINN 文献全文核验计划

## 目标

先完成 `raw/papers/pinn/protocol-adaptive/` 中 10 篇核心 PDF 的逐篇全文核验，再筛查冻结时点 `raw/papers/pinn/` 下 76 个 PDF 文件对象、73 篇唯一内容与既有 wiki/Zotero 记录；只有完成本地证据穷尽和缺口审计后，才检索并下载缺失的一手文献，最终给出 R2 综合裁决与可直接执行的数据重建合同。后续补入的 7 份外部一手原件单列，不回写本地冻结批次分母；并行研究任务新增的原件不纳入本 R2 清单。

## 任务边界

- 原件只读，不修改、覆盖、重命名或删除任何 PDF。
- 核心十篇阶段不联网扩张；76 个文件对象、73 篇唯一内容的冻结本地批次完成后，只针对仍未闭合的承重证据缺口检索和下载一手文献。
- 不访问服务器，不修改实验代码、数据制品或两份恢复文档，不启动数据重建与实验。
- 每批只处理 2 篇；对应笔记和 `INDEX.md` 写回后立即报告检查点。
- 每批对题名、DOI、arXiv 标识和作者执行 Zotero 去重；无重复时导入准确书目、关联对应本地 PDF，并把条目键和附件状态回写到论文笔记。
- 单篇 PDF 转换最多 5 分钟；超时立即终止，改用本地 `pdftotext` 分页提取和原 PDF 逐页核验。
- 自动提取文本只作定位辅助；方程、实验数字、消融结论和关键措辞必须保留 PDF 页码或章节。
- 76 个文件对象逐篇记录纳入、排除、重复或待核验状态；只对直接承重项做全文笔记，不为无关论文制造重复笔记或 Zotero 条目。
- 停止条件为：承重机制与字段均有可追溯一手证据和反例边界，连续两个筛查批次没有新增可迁移机制或失败条件，且数据重建与 A/B/C/D 合同不再变化。

## 冻结裁决合同

- C 是章级主方法。
- `C-A` 衡量物理路由贡献；`B-A` 衡量协议直接信息贡献；`D-B` 衡量同额外信息条件下的路由增量。
- 若只有 B/D 提升而 C 不提升，则否决 R2，不能把协议标签捷径包装成物理路由收益。
- 重点核验：固定硬适用掩码、仅来自协议置信度的软强度、分类损失到路由器的梯度阻断、共享守恒/协议专家/未知回退、TQH 标签捷径、GeNIS 字段回接、ns-3 多协议真值及公平基线。

## 批次与状态

- [x] 阶段一：读取规则、SCHEMA、问题卡、既有计划和笔记，冻结本轮边界。
- [x] 批次一：全文核验 GatedPINN 与 MoE-PINN，写入两篇笔记和方向索引，完成 Zotero 去重、导入、PDF 附件关联与笔记回链。
- [x] 批次二：全文核验 Physics-Fails 与 Partial-Physics-Neural-ODE，完成两篇笔记、方向索引、Zotero 去重、导入、PDF 附件关联与笔记回链。
- [x] 批次三：全文核验 Neural-Hybrid-Automata 与 Latent-Hybridisation-Model，完成两篇笔记、索引、Zotero 去重、导入、附件关联与笔记回链。
- [x] 批次四：全文核验 Nested-Mixture-of-Experts 与 RPLPO，完成笔记、索引、Zotero 与附件写回；累计达到 8 篇后先提交 R2 最小实验合同可执行性中期裁决。
- [x] 中期裁决：写入 `r2-minimum-experiment-contract-midterm.md`，明确字段、方程、梯度阻断、A/B/C/D、三源数据门禁和停止条件。
- [x] 批次五：全文核验 QUIC-Classification 与 VisQUIC；VisQUIC 与既有数据集原件 SHA-256 相同，复用既有笔记和 Zotero 条目，不制造重复对象。
- [x] 本地普查：冻结批次共 76 个文件对象、73 篇唯一内容；状态为纳入全文 28、背景保留 31、排除 14、重复 3、待筛查 0。
- [x] 缺口审计：覆盖 TCP/UDP/QUIC 动力学、推理可见字段、隐藏状态真值、协议置信度校准、分类梯度隔离和标签捷径。
- [x] 外部补证：只为 QUIC 现行线图像与漂移校准两处残余缺口补入 RFC 8999/9000/9001/9287/9312、Guo 2017 和 Ovadia 2019，并完成 Zotero、原件和 wiki 回链。
- [x] 数据合同：将字段白名单/黑名单、原始来源、重建算法、缺失掩码、分组切分、双构建哈希与基线重跑要求写入 `r2-data-rebuild-contract.md`。
- [x] 综合：形成方法—字段—假设—失败边界矩阵，按 A/B/C/D 合同给出 R2 裁决。
- [x] 验证：检查全部纳入笔记、`source_pdf`、INDEX 入链、YAML 可解析性、链接、路径、哈希与 Zotero 证据，并完成最终报告。

## 每篇强制提取项

1. 书目信息与原件路径。
2. 原文页码或章节定位。
3. 方程语义、状态变量和参数梯度路径。
4. 可观测字段、潜在状态与所需真值。
5. 适用假设、失败边界与实验口径。
6. 可迁移机制、本课题推论、不能直接照搬之处和待验证假设。

## 制品路径

- 逐篇笔记：`wiki/papers/pinn/protocol-adaptive/`
- 方向索引：`wiki/papers/pinn/protocol-adaptive/INDEX.md`
- 过程证据：`.Codex/docs/research/protocol-adaptive-pinn/notes.md`
- 最终综合：`.Codex/docs/research/protocol-adaptive-pinn/final-report.md`
- 冻结本地批次筛查清单：`.Codex/docs/research/protocol-adaptive-pinn/local-corpus-screening.md`
- 最终数据重建合同：`.Codex/docs/research/protocol-adaptive-pinn/r2-data-rebuild-contract.md`

## 验收命令

- `fd -t f -e md . wiki/papers/pinn/protocol-adaptive`
- `rg '^source_pdf:|^key_finding:|^## ' wiki/papers/pinn/protocol-adaptive --line-number`
- `rg '原文位置|失败边界|可观测|不能直接' wiki/papers/pinn/protocol-adaptive --line-number`
- 使用 Zotero 本地接口复查每篇条目键、所属集合及 PDF 子附件。
- 使用 YAML 解析、链接、路径、哈希和 PDF 页级证据的确定性检查；按用户最新覆盖，不运行 Markdown 自动格式化、格式导向修改或空白门禁。

## 错误与风险记录

- 初次按 `wiki/SCHEMA.md` 读取失败；已确认规范实际位于仓库根 `SCHEMA.md`，随后完整读取。
- 首次编辑使用删除并重建文件的补丁方式，`apply_patch` 拒绝删除目标文件；未产生文件变更，已改用原位更新。
- 创建 Zotero 专用子目录时受当前文件权限阻止；不扩大权限面，改为将批次 BibTeX 放在现有研究目录。
- 删除重复索引链接的合并补丁因并发方已先行删除而校验失败；该补丁整体未落盘，复查确认索引当前只保留一条链接。
- Partial-Physics-Neural-ODE 的初始 BibTeX 草稿含原件未提供的会议地点；在导入前已删除该未经核验字段，Zotero 未接收错误地点。
- 工作区存在与本任务无关的既有修改；本任务不触碰这些文件，也不回滚用户或其他代理的变更。
- 当前共享 B0 无协议字段，GeNIS 需回接字段，现有 ns-3 真值仅覆盖 UDP；文献机制不能替代数据可观测性证据。
- 用户扩大范围后，原“仅 10 篇、不联网”边界已失效；已按冻结批次 76 个文件对象、73 篇唯一内容完成本地筛查，再只为残余缺口补入一手文献。
- 用户最新覆盖取消所有格式化和空白门禁；已完成的既有格式化不回滚，后续只保留内容、结构、链接、路径、哈希与证据验证。

## 当前状态

**文献筛查、数据合同和最终验证均已完成**：核心十篇、本地冻结批次 76 个文件对象/73 篇唯一内容和 7 份外部一手补证均已闭合。最终裁决为“计算图可冻结，数据门禁未通过，禁止启动 R2”；QUIC 第一轮继续走未知回退。本轮不运行数据重建或实验。
