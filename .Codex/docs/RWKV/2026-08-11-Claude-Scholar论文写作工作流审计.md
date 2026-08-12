# Claude Scholar 论文写作工作流审计

- 审计日期：2026-08-11
- 范围：本机 `/tmp/claude-scholar` 源码快照、`~/.claude`、`~/.codex`、`~/.agents` 已有技能/代理镜像；不安装、不迁移、不执行外部调用。
- 执行代理：`claude_scholar_writing_workflow_terra_medium`；模型：`gpt-5.6-terra`；推理强度：`medium`。
- 路线约束：`RESEARCH_ROUTE=RWKV`。当前 `G0-D=NOT_READY`、`G0-F=NOT_READY`，第三章候选均为“实验待证”。本审计不得将候选、快速筛选或既有机制图写成方法有效的论文结论。

## 结论

推荐把 Claude Scholar 用作“证据约束下的写作辅助层”，而不是论文结论生成器。当前可以建立第三章的结构、论断台账、图表清单、引用核验清单和待证占位稿；只有通过冻结开发区快速消融、正式多种子实验与最终测试隔离门禁后，才可把对应实验结果写入正文。

正式章节目录与可执行正文规则已落在 [`thesis/chapters/AGENTS.md`](../../../../thesis/chapters/AGENTS.md)。其中明确第三、四章现有工作稿可能是历史 PINN 内容，目录迁移不等于 RWKV 路线采纳。

`ml-paper-writing`、`citation-verification`、`writing-anti-ai`、`paper-miner` 是当前最有直接价值的组合。Nature 系列工具只抽取可迁移的“论断—证据—边界”纪律，不采用其英文期刊叙事、数据公开或审稿回复模板替代中文学位论文规范。

本论文既定章节结构、章级工作量和理论—实验组织方式，以朱焱雷论文第三、四、五章为**参照边界**：保留“单章单问题、章内多机制协同、理论与实验共同支撑”的原则，结合本路线的 RWKV 机制、跨年度合同和真实实验独立展开。不得机械复制朱文的章节、机制、公式、图表或数值；也不得照搬 Claude Scholar 的 Nature/会议稿件结构。Claude Scholar 只提供写作工具链与证据治理方法，不能替代或重写既定的中文学位论文结构。

## 本地可用性矩阵

|资产|本地核验入口|当前会话可调用状态|触发与输入|输出/依赖|本论文阶段与裁决|
|---|---|---|---|---|---|
|`ml-paper-writing`|`/tmp/claude-scholar/skills/ml-paper-writing/SKILL.md`；`~/.codex/skills/ml-paper-writing/SKILL.md`|已登记技能|从研究仓库、实验制品、文献或草稿起草；要求先过“论断台账”门|章节草稿、文献工作流、引用占位；声明依赖 `semanticscholar`、`arxiv`、`habanero`、`requests`|**推荐**。仅取论断门、证据优先、引用工作流和章节迭代；不采用 NeurIPS/ICML 等会议模板和篇幅假设|
|`nature-writing`|`/tmp/claude-scholar/skills/nature-writing/SKILL.md`；`~/.codex/skills/nature-writing/SKILL.md`|本地存在，未在本会话技能清单登记|作者提供论断、结果、图、笔记或中文草稿；先要求核心论断、证据、边界|英文 Nature 风格草稿及 `Claim-evidence map`|**选择性借用，暂不直接启用**。可复用“从证据向外写”“每个主要论断有比较/消融/压力测试”；不输出 Nature 风格英文正文|
|`nature-polishing`|`/tmp/claude-scholar/skills/nature-polishing/SKILL.md`；`~/.codex/skills/nature-polishing/SKILL.md`|已登记技能|已有段落或中文学术草稿；不允许凭空补数据、引用、机制或创新|重组后英文润色文本及修订说明；参考 Nature 模式和 Academic Phrasebank|**后期有限使用**。仅用于英文摘要/投稿衍生材料，或借其“先修逻辑再润色”检查；中文学位论文不套用 Nature 英文文风|
|`nature-response`|`/tmp/claude-scholar/skills/nature-response/SKILL.md`；`~/.codex/skills/nature-response/SKILL.md`|本地存在，未在本会话技能清单登记|编辑决定、审稿意见、修订记录、页行/图表位置|逐点回复追踪表、回复信、修订清单；不允许虚构修改或统计结果|**当前不启用**。仅收到真实外审意见后，以其追踪表方式辅助答辩/期刊修回|
|`nature-data`|`/tmp/claude-scholar/skills/nature-data/SKILL.md`；`~/.codex/skills/nature-data/SKILL.md`|本地存在，未在本会话技能清单登记|目标期刊、数据/代码/图源清单、访问限制和存储方案|英文数据可用性声明、仓储计划、数据集引用、FAIR 缺口|**当前不启用**。路线明确“不以公开代码/数据为前置门槛”；若未来投稿且有期刊要求，再按实际许可证、LSPR 来源和本地制品生成声明|
|`citation-verification`|`/tmp/claude-scholar/skills/citation-verification/SKILL.md`；`~/.codex/skills/citation-verification/SKILL.md`|已登记技能|DOI、出版商页、arXiv、CrossRef、Semantic Scholar 或已核验 Zotero 条目|元数据核验、BibTeX 与“`[CITATION NEEDED]`”缺口；脚本批量模式另需 `bibtexparser`、`requests`、`semanticscholar`、`arxiv`|**推荐，全文写作前后均启用**。先核验元数据与论断支撑位置；不从记忆生成条目。脚本 README 与主技能对实际流程描述不一致，批处理前必须重新确认采用来源|
|`writing-anti-ai`|`/tmp/claude-scholar/skills/writing-anti-ai/SKILL.md`；`~/.codex/skills/writing-anti-ai/SKILL.md`|已登记技能|用户要求去除机器腔、检查中文/英文段落|识别填充语、空泛归因、模板化并列与过度连接，并据此改写|**推荐为最后一轮语言检查**。只能删冗余、补具体事实和调整句法，不能弱化限定条件、替换技术术语或改变论断证据关系|
|`latex-conference-template-organizer`|`/tmp/claude-scholar/skills/latex-conference-template-organizer/SKILL.md`；`~/.codex/skills/latex-conference-template-organizer/SKILL.md`|已登记技能|指定会议的 LaTeX 模板压缩包及官方要求；其工作模式要求先分析、再确认|Overleaf 结构、`main.tex`、章节目录、图表/参考文献目录和 README|**当前不启用**。仅在确定会议投稿且拿到官方模板后使用，不能整理或替换本校学位论文模板|
|`paper-miner`|`/tmp/claude-scholar/agents/paper-miner.md`；`~/.codex/agents/paper-miner/AGENTS.md`；`~/.codex/agents/paper-miner/config.toml`|**已注册 Codex 代理**，`~/.codex/config.toml` 的 `[agents.paper-miner]` 指向其配置；当前会话也可作为 `paper-miner` 代理类型调度|本地 PDF/DOCX、arXiv 链接或可读文本；可聚焦引言、方法、结果、场馆|可复用修辞、结构信号、短语、场馆信号与标准化报告；写入已安装的全局记忆|**推荐，需显式调度**。只沉淀章节编排和证据叙述，不提取朱焱雷的方法、公式或数值作为本论文内容|
|`/mine-writing-patterns`|`/tmp/claude-scholar/commands/mine-writing-patterns.md`；`~/.agents/skills/source-command-mine-writing-patterns/SKILL.md`|Claude 源码中是斜杠命令；Codex 中迁移为技能，但 `~/.codex/config.toml` 当前将其设为 `enabled = false`，**不可作为当前直接入口**|`source` 必填，`focus` 可选：`general/introduction/method/results/rebuttal/venue`|设计上调用 `paper-miner`，更新全局已安装写作记忆并返回六段式摘要|**不安装、不启用**。功能等价的已注册 `paper-miner` 代理足够；若以后启用命令，必须先确认其实际运行时和写入路径|

### 路径与版本注意

1. Claude 源码命令指定 `~/.claude/skills/ml-paper-writing/references/knowledge/paper-miner-writing-memory.md`，而迁移到 Codex 的命令/代理指定 `~/.codex/skills/...`；两处文件在本机均存在。
2. 因此执行前必须读取实际运行时绑定的命令或代理，并在交付中记录其**实际写入路径**。不能假定 `/tmp/claude-scholar` 源码树就是生效记忆。
3. `paper-miner` 的全局记忆只存写作启发，不能成为第三章科学结论、引用真实性或实验结果的事实源；项目内事实仍以 `raw/` 原件、`wiki/` 全文笔记、RWKV 总控、配置、原始日志和制品为准。

## `paper-miner` 的实际调用链与使用边界

### 身份、注册与可发现性

1. `paper-miner` 不是 `SKILL.md` 技能，也不是本会话中可直接输入的普通斜杠命令；它是 Codex 的**具名代理**。已核验的注册链为：`~/.codex/config.toml` 的 `[agents.paper-miner]` → `~/.codex/agents/paper-miner/config.toml` → `~/.codex/agents/paper-miner/AGENTS.md`。
2. 其配置的名称为 `paper-miner`，描述为“从成功论文中提取写作知识”，模型继承主配置，没有单独模型覆盖；其开发者指令要求保留来源、避免重复，只合并耐久的写作效用信息。
3. 当前 Codex 已有同等代理能力，因此没有安装、移植、复制或覆盖任何文件。此结论由当前会话代理类型和上述注册链共同支持。
4. Claude 源码的 `/mine-writing-patterns` 是“命令 → `paper-miner` 代理”的包装器。Codex 迁移副本是 `source-command-mine-writing-patterns` 技能，但当前配置为 `enabled = false`；它不构成当前可执行入口。

### 实际输入、输出与记忆位置

|环节|已核验行为|本论文执行约束|
|---|---|---|
|输入|`paper-miner` 接受 PDF、DOCX、arXiv 链接或可读文本；可抽取题名、作者、场馆和年份。Claude 命令包装器还定义 `source` 必填，`focus` 可选|仅交付朱焱雷原始全文或已核验全文文本，不使用题录错误的 `wiki/papers/attack-detection/朱焱雷.md` 作为事实输入|
|焦点|`general`、`introduction`、`method`、`results`、`rebuttal`、`venue`|朱焱雷第三/四/五章分别使用 `method`、`results`、`general` 或 `venue`，但不请求“复写本论文”|
|分析|提取写作模式、章节结构信号、可复用短语、场馆信号、回复信号和“如何帮助写作”|只保留章节职能、论证顺序、理论与实验如何互相支撑、表图如何服务问题；短语只作修辞备选，不能复制成段文字|
|输出|标准报告应有元数据、六栏记忆写入摘要、新模式、复用建议和阻塞/限制|主代理在交付验收时额外核对“本论文不可迁移内容”清单：具体机制、公式、数据、实验数值、结论和原句均禁止迁移|
|写入|Codex 代理与 `ml-paper-writing` 当前指向 `~/.codex/skills/ml-paper-writing/references/knowledge/paper-miner-writing-memory.md`；该文件与 `/tmp/claude-scholar` 同名初始模板的 SHA-256 相同|全局记忆是跨项目写作资产，不是论文证据库；不得在项目内新建第二份 `paper-miner` 记忆或把其内容直接提升为论文结论|

### 推荐的显式调度简报

将以下文字作为调度 `paper-miner` 时的任务简报，而不是让其自行决定论文结构：

```text
输入：<朱焱雷原始全文路径>；范围：第三/四/五章；焦点：method（第三、四章）与 general（第五章）。
目标：只提取单章问题界定、多个机制的协同叙述、理论—实验的证据链、图表和小结的章节职能。
禁止：提取、复用或改写任何具体机制、公式、算法、数据、数值、结论、图表内容和连续原句。
输出：来源页码/章节、可迁移结构模式、不可迁移内容清单、对本论文既定章节的映射建议。
写入：仅更新实际 Codex 已安装写作记忆；返回精确写入路径和来源状态。
```

### 对朱焱雷第三、四、五章的正确沉淀方式

1. 第三章只沉淀“章级问题 → 两机制/多机制各司其职 → 统一算法与适配 → 性质/边界 → 比较、消融、诊断和限制”的论证顺序。现有研究笔记已核验其第三章为 26 页，并列出对应结构和证据组。
2. 第四章只沉淀“效率或第二个章级问题必须拥有独立问题定义、机制链、理论分析和资源/消融实证”的组织原则，不把其动态过滤、缓存复用或任何性能数字迁移到 RWKV 路线。
3. 第五章只在本论文确有系统章节的既定需求时，沉淀“需求 → 架构 → 功能模块 → 部署环境 → 测试 → 小结”的系统论证模式；不得因挖掘结果擅自新增、删减或重排本论文的章节。
4. 全局写作记忆中的每个朱焱雷条目必须保留全文来源和“仅结构/论证模式”标签。随后中文正文代理仍须以 RWKV 总控、候选登记册、论断台账和真实制品决定章节内容。

## 推荐工作流与阶段门禁

### 阶段 W0：范围恢复与写作许可证

- 输入：RWKV 总控、候选登记册、跨年度数据合同、当前制品/运行状态、用户明确的章节与目标语言。
- 动作：将每个拟写段落标为 `设计可行`、`实验待证`、`实验支持` 或 `实验否决`；候选名称、数据合同和最终测试边界从总控读取，不由写作者改写。
- 通过门：不存在把 C1-C12、种子 42 快速筛选、方法示意图或历史 E2 结果写成当前 RWKV 方案结论的句子。
- 失败处理：仅写提纲/占位符，如“[待冻结开发区实验验证]”，不得润色为肯定论断。

### 阶段 W1：证据与论断台账

- 输入：每个主张对应的配置哈希、数据版本/切分、基线、指标定义、原始日志、制品路径、图表源和文献原件位置。
- 动作：在第三章专属过程文档维护最小台账：`论断编号 | 允许表述 | 禁止强化 | 证据类型 | 配置/制品 | 图表/表格 | 状态 | 引用`。
- 通过门：每个“提出”“优于”“稳定”“可泛化”“机制导致”等句子均有可定位证据；没有证据的句子明确标为待证。
- 可用资产：`ml-paper-writing` 的论断门与 `nature-writing` 的 `Claim-evidence map` 形式，不使用其英文产物。

### 阶段 W2：章节骨架与高质量论文结构挖掘

- 输入：朱焱雷全文原件、现有结构化笔记、RWKV 方案与门槛基准；输入必须是全文而非错误元数据笔记。
- 动作：使用已注册的 `paper-miner` 代理，只抽取“章节职能、段落推进、图表服务的论断、结果小节顺序”。随后由人工核对并写回本项目的结构台账，而非把全局记忆当作结论来源。当前不调用处于禁用状态的 `/mine-writing-patterns` 迁移入口。
- 推荐骨架：`3.1 引言` → `3.2 问题定义与跨年度合同` → `3.3 总体框架及两个机制` → `3.4 算法与基座适配` → `3.5 性质、假设和边界` → `3.6 实验评估` → `3.7 小结`。这是从 `wiki/papers/attack-detection/朱焱雷-加密流量博弈对抗与高效训练.md` 提取的结构参照，机制内容必须完全由 RWKV 路线证据重建。
- 通过门：明确标注“借结构，不借机制、公式、数据或提升数字”；第三章研究笔记已指出朱文的定理严格假设有限，当前论文必须补齐可观测变量、适用条件与可证伪结论。第四、五章同样按既定中文学位论文目录和朱文的章级参照延展，不因 Claude Scholar 的期刊/会议工作流重排。

### 阶段 W3：方法和协议稿

- 输入：冻结的数据合同、可观测变量、机制接口、算法、预注册的比较/消融计划和现有方法图。
- 动作：先写问题定义、输入输出、算法、训练/推理协议、假设与边界；对未实验机制使用“拟验证/候选”措辞。
- 图表门：现有 `thesis/figures/第三章/图3-1` 至 `图3-5` 只可支撑方法与协议描述。结果图必须由相应门禁通过后的已核验制品生成；PDF 是排版优先版，SVG 是可编辑版，图件清单记录生成环境。
- 通过门：不把图示当作实证；不使用最终 20% 测试信息选择章节方法、阈值或图表。

### 阶段 W4：实验结果接入与结果叙述

- 输入：冻结开发区 `2×2` 快速消融的全部四变体，之后是正式强基线、多种子、跨基座、困难面板、效率与诊断制品。
- 动作：每个结果小节按“预注册问题 → 表/图原始值 → 统计/差异口径 → 可支持的解释 → 限制”写作；完整方法、单机制、基座均报告，不能只取最好种子。
- 快速筛选门：仅能写入过程报告，不能成为论文结论。进入正式实验的最低信号是完整方法优于基座、至少一项单机制正增益、完整方法不弱于最佳单机制、诊断沿理论预期变化。
- 正式门：三种子、置信区间、强基线、至少两个预冻结困难面板、消融交互项、资源开销齐备后，才允许写“实验支持”。错误相对下降的定义、绝对百分点差和基线比较对象必须同表给出。

### 阶段 W5：引用、反向核验与语言收尾

- 引用：先把文献论断映射到全文笔记/原件页码，再用 DOI、出版商页、arXiv、CrossRef、Semantic Scholar 或核验过的 Zotero 条目核对元数据；未过核验保留 `[CITATION NEEDED]`，不生成记忆型 BibTeX。
- 反向核验：从表格和图题回查正文中的每个数字、比较对象、数据版本与限定词；再从每个强主张回查台账。
- 润色：最后才用 `writing-anti-ai` 检查中文空话、重复转折、模板化并列和夸张修辞。只修语言，不改变台账状态、技术定义、数值、引用或限制。
- 通过门：引用、制品、图表、正文和结论的断言强度一致；不出现“首创”“显著优于”“长时记忆有效”“跨年度泛化”等无证据表述。

## 第三章的具体接入方式

|对象|唯一事实输入|写作接入规则|不得写入的内容|
|---|---|---|---|
|实验结果|冻结配置、原始日志、结果表、运行制品和指标程序|台账中记录运行目录、种子、分割、基线、指标和统计；表/图只从同一证据行导出|快速筛选的正增益作为最终结论；未运行候选的效果描述|
|论断|台账中的允许/禁止表述与证据状态|正文每一主张贴近其表、图或原始制品；证据不足使用待证占位|由相关工作动机推导本方法有效；由机制直觉推出因果解释|
|图表|`thesis/figures/第三章/README.md`、图件清单与实验制品|方法图服务结构和协议；结果图服务特定实验问题；每个图题独立说明数据、比较和边界|用方法图暗示性能；用未过门禁制品绘制正式结果图|
|引用|原件、`wiki/` 全文笔记、已核验书目信息|引用分别承担机制来源、数据/许可证、比较方法和论断依据；书目信息与句子论断双重核验|仅凭摘要、搜索片段或全局写作记忆支撑科学论断|
|反 AI 润色|已通过 W5 的中文段落与论断台账|逐段删除空泛套话，改为可核验的对象、条件、数字和限制|为“自然”而删除不利结果、失败条件、不确定性或引用|

## 当前不应启用的技能或模式

1. `nature-response`：没有真实编辑决定或审稿意见，当前调用会产生无事实基础的修回框架。
2. `nature-data`：当前路线不以公开数据、代码或模型为论文前置；未确定目标期刊和仓储方案前，不能生成 Nature 数据可用性声明。
3. `latex-conference-template-organizer`：尚未给出会议、官方模板或投稿目标，且不应替换学校学位论文模板。
4. `nature-writing` 的全文英文/Nature 叙事模式，以及 `ml-paper-writing` 的 NeurIPS/ICML/ACL 等会议成稿、模板和篇幅流程：本论文是中文学位论文，最多借用其证据、边界和结果叙述检查，禁止据此重排既定章节。
5. `nature-polishing` 的 Nature 英文成稿模式：仅在明确生成英文投稿材料时使用；不得提前覆盖中文正文的学位论文规范。
6. `paper-miner` 自动写入全局记忆：在未明确全局记忆目标、待分析全文和聚焦范围前不执行，避免污染跨项目记忆；任何写入前还需检查 Claude/Codex 两个候选记忆路径。
7. 引用核验脚本批处理：现有 README 将脚本定位为参考实现，且其 API 依赖未在本任务核验；没有明确 `.bib/.tex` 输入、网络许可和依赖状态时不运行。

## 建议的代理与命令编排

1. 主写作代理：恢复 RWKV 路线，维护章节级论断台账，决定哪一阶段可进入。只有主代理解释实验状态，避免写作代理自行升级论断。
2. `paper-miner`：在用户明确要求后，单独处理朱焱雷或其他高质量全文；传入 `method` 或 `results` 焦点，输出必须包含来源状态和全局记忆实际写入路径。
3. `paper-miner` 调度焦点：先用 `method` 提取章节、公式/算法叙述的组织模式，再用 `results` 提取表图叙述和消融顺序；禁止把提取短语直接粘贴进正文。`/mine-writing-patterns` 当前禁用，不列为执行入口。
4. 文献/引用核验代理：按单篇或单一参考文献集合核验题录和论断支持位置，输出未核验清单；不与正文润色并行混写。
5. 中文正文写作代理：只接收通过 W1 的论断台账与 W3/W4 对应制品，产生小节草稿和“论断—证据—边界”映射。
6. `writing-anti-ai`：在事实核验后串行执行。其输入必须带原段落和禁止改变的术语/数值清单。

## 每次最小上下文输入清单

1. 当前章节、目标语言、预期读者和允许写作范围。
2. RWKV 总控与候选登记册中的当前状态、冻结合同和禁止结论。
3. 本次小节的论断台账行，包括允许措辞、禁止强化、证据状态、制品/日志路径和对应图表。
4. 数据集版本、时间切分、最终测试访问状态、字段/标签权限和评价指标定义。
5. 完整基线、候选、单机制与消融矩阵，包含种子、预算、原始数值、置信区间及失败运行。
6. 图表源文件、图题草案、图件清单及每幅图服务的问题。
7. 需要引用的原件路径或已核验 Zotero 条目、页码/公式/表格位置与引用用途。
8. 对 `paper-miner` 额外提供：全文路径、焦点、目标运行时，以及允许写入的全局记忆路径。
9. 对 `writing-anti-ai` 额外提供：禁止改动的术语、符号、数值、限定条件和引用键。

## 安装/移植缺口

- 本任务未安装或修改任何技能、代理、命令、AGENTS 文件或论文正文。
- `nature-writing`、`nature-response`、`nature-data` 的技能文件存在于本机，但未在当前会话的已登记技能清单中出现；如未来确需直接调用，应先核验 Codex 注册机制和来源版本，而不是复制文件。
- `/mine-writing-patterns` 在 Claude 源码中是命令、在 Codex 侧以 `source-command-mine-writing-patterns` 技能存在，且已核验当前配置为 `enabled = false`。功能等价的 `paper-miner` 代理已注册，因此无需为本论文启用或移植该命令。
- `paper-miner` 的全局记忆路径存在 Claude 与 Codex 两套大小写不同的安装根。当前 Codex 代理应写 `~/.codex/skills/ml-paper-writing/references/knowledge/paper-miner-writing-memory.md`；首次真实写入时仍应在交付中报告实际路径。本审计未进行写入。
- `citation-verification` 的批处理脚本依赖包及联网可用性未核验。未来需要自动批量核验时，先单独做只读依赖与输入格式预检。

## 审计证据入口

- Claude Scholar 源码：`/tmp/claude-scholar/skills/`、`/tmp/claude-scholar/agents/paper-miner.md`、`/tmp/claude-scholar/commands/mine-writing-patterns.md`。
- 已安装镜像：`~/.codex/skills/`、`~/.codex/agents/paper-miner/AGENTS.md`、`~/.agents/skills/source-command-mine-writing-patterns/SKILL.md`、`~/.claude/skills/`。
- RWKV 当前事实：`.Codex/docs/RWKV/RWKV路线总控.md`、`.Codex/docs/RWKV/2026-08-08-第三章候选方案登记册.md`。
- 第三章工作量与结构参照：`.Codex/docs/RWKV/2026-08-08-朱焱雷第三章候选门槛基准.md`、`.Codex/docs/RWKV/2026-08-08-朱焱雷第三章候选门槛基准-研究笔记.md`、`wiki/papers/attack-detection/朱焱雷-加密流量博弈对抗与高效训练.md`。
- 现有图表边界：`thesis/figures/第三章/README.md`、`thesis/figures/第三章/图件清单.json`。
