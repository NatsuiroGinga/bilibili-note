# Codex 实验规则拆分与子代理启动校验调研

日期：2026-07-30

## 结论

当前最合适的方案不是单独增加一个 Hook，也不是永久提高 `project_doc_max_bytes`，而是组合使用六种官方机制：

1. 用嵌套 `AGENTS.md` 缩小规则适用范围，只保留需要模型持续判断的规则。
2. 用项目级 `PreToolUse` Hook 强制校验 `spawn_agent` 的 `task_name` 与任务描述，并拦截不安全的远程命令。
3. 用统一远程启动器和机器可读能力清单承担 `fd`、`rg`、`uv`、PATH、重启恢复等确定性检查。
4. 用项目技能保存较长的实验分派流程，利用渐进加载降低常驻上下文占用；定制代理只负责固定角色，不代替任务实例命名校验。
5. 用独立的论文配置档按路径屏蔽完全重复或当前无关的 Skills，不删除源文件，也不改变其他仓库的默认集合。
6. 对偶尔使用的自有 Skill 关闭隐式调用；对第三方 Skill 采用按需配置档。Codex 当前不能保证一个 Skill 在移出候选索引后仍可在同一会话显式调用。

`SubagentStart` 不适合作为启动门禁。官方明确说明它可以给子代理追加上下文，但 `continue: false` 不能阻止子代理启动。真正的启动前拒绝应放在匹配 `spawn_agent|Agent` 的 `PreToolUse` 中。

本机两个用户技能目录共发现 176 个 `SKILL.md`，其中有 37 个同名项：20 对内容完全相同，17 对内容分叉。应先通过独立配置档处理完全相同项，再审查分叉项；不要直接删除或建立不可维护的全量白名单。

## 官方文档核验结果

### `AGENTS.md` 的发现与大小限制

Codex 在每次运行开始时构建一次规则链。项目范围从项目根目录走到当前工作目录，每层按 `AGENTS.override.md`、`AGENTS.md`、`project_doc_fallback_filenames` 的顺序只读取一个文件；越靠近当前工作目录的内容越晚出现，因此优先级更高。项目规则合计默认最多读取 32 KiB，官方建议超限时拆到嵌套目录或调整 `project_doc_max_bytes`。[官方 AGENTS.md 文档](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

由此得到三个直接限制：

- `AGENTS.override.md` 是同层替换机制，不是同层附加文件；同一目录存在 override 时，该目录的 `AGENTS.md` 会被忽略。
- `project_doc_fallback_filenames` 只在标准文件缺失时提供候选名，而且每层仍只读取一个文件，不能用它把一个超长规则文件拆成同层多个片段。
- 自动发现只走到启动时的当前工作目录。若 Codex 从仓库根启动，仅仅编辑 `thesis/experiments/llm_probe/` 下的文件不会触发动态发现。实验专用会话应使用 `codex --cd thesis/experiments/llm_probe`；继续从仓库根运行时，仍需保留一条简短的人工路由规则。

`project_doc_max_bytes` 和 `project_doc_fallback_filenames` 是正式配置项。官方示例要求修改后重启 Codex 或开始新命令。[官方配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)；[官方 AGENTS.md 配置示例](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

### 项目配置层

Codex 支持项目级 `.codex/config.toml`。项目配置从项目根到当前工作目录分层，越近的配置优先，但只有受信任项目才会加载项目 `.codex/` 配置、Hook 和规则。[官方配置基础](https://learn.chatgpt.com/docs/config-file/config-basic)

该文件适合保存字节上限、代理并发数、默认子代理模型等配置，不适合继续堆放自然语言实验纪律。当前仓库和用户配置均未发现 `project_doc_max_bytes` 或 `project_doc_fallback_filenames` 的显式设置，因此当前应按默认 32 KiB 判断。

### Hook、工具覆盖与子代理事件

官方 Hook 支持项目级 `.codex/hooks.json` 或 `.codex/config.toml` 内联配置。项目 Hook 只有在项目受信任且精确 Hook 定义通过审查后才运行；定义变化后会因哈希变化重新进入待信任状态。[官方 Hook 文档](https://learn.chatgpt.com/docs/hooks)

`PreToolUse` 可以观察 Shell、`exec_command`、`apply_patch`、MCP 和其他本地函数工具，读取 `tool_input`，并在工具执行前拒绝或重写调用。官方工具覆盖表明确写明 `spawn_agent` 还会匹配别名 `Agent`。因此可以在子代理创建前检查本次环境中的 `tool_input.task_name` 与 `tool_input.message`，不合格时返回 `permissionDecision: "deny"`。[官方 Hook 工具覆盖与 PreToolUse 输出](https://learn.chatgpt.com/docs/hooks)

边界如下：

- 官方只保证把本地函数工具的参数作为 `tool_input` 传入；具体字段名属于工具自身接口。实施前应使用当前 `spawn_agent` 工具模式或一次无副作用捕获确认 `task_name`、`message` 字段，不能把字段名当作跨版本永久协议。
- Hosted 工具不经过这条本地工具 Hook 路径，部分专用工具路径也可能绕过默认路径。官方因此把 Hook 定位为有效防护栏，而不是完整安全边界。
- `SubagentStart` 发生在子代理已经开始时，只能附加开发上下文，不能阻止启动；它最多用于提醒子代理读取合同，不能校验创建请求。
- 当前只有 `type: "command"` 的 Hook 处理器会执行；`prompt` 与 `agent` 处理器虽可解析但会被跳过。
- 官方未承诺 Hook 定义热加载。最稳妥的启用步骤是开始新会话，使用 `/hooks` 审查并信任新定义，再做正反例验证。

### Skills、插件与定制代理

Skills 采用渐进加载：常驻上下文只包含名称、描述和路径，完整 `SKILL.md` 仅在被选中时加载。它适合承载实验分派模板、审查步骤、运行验收流程和远程操作说明，但模型是否选用技能本身不是机械强制，因此关键门禁仍应由 Hook 或脚本完成。[官方 Skills 文档](https://learn.chatgpt.com/docs/build-skills)

项目可在 `.codex/agents/*.toml` 定义定制代理，每个代理必须有 `name`、`description` 与 `developer_instructions`。这适合固定 `experiment_runner`、`experiment_reviewer`、`docs_researcher` 等角色，并限制模型、沙箱和工具面；它规范的是代理类型，不会自动校验每次任务实例的 `task_name`。[官方 Subagents 文档](https://learn.chatgpt.com/docs/agent-configuration/subagents)

插件可以打包 Skills、MCP 与 Hook，适合跨仓库或团队分发稳定能力。当前问题只属于单仓库，直接使用项目 Skills、项目代理和项目 Hook 更小、更容易审查；现在制作插件会增加安装、启用、信任和版本管理成本。[官方插件文档](https://learn.chatgpt.com/docs/build-plugins)

## 当前实验 `AGENTS.md` 审计

审计对象：`thesis/experiments/llm_probe/AGENTS.md`

| 指标 | 结果 |
| --- | ---: |
| 行数 | 118 |
| 字节数 | 25,589 |
| 二级章节数 | 10 |
| 列表规则数 | 83 |
| “已解决故障的防复发记录”规则数 | 28 |

当前项目规则链的字节数为：

| 文件 | 字节数 |
| --- | ---: |
| 根 `AGENTS.md` | 7,947 |
| `thesis/AGENTS.md` | 6,202 |
| `thesis/experiments/llm_probe/AGENTS.md` | 25,589 |
| 合计 | 39,738 |

合计比默认 32,768 字节多 6,970 字节。根与论文规则加载后，实验文件理论上只剩约 18,619 字节预算，因此不能依赖实验文件尾部的防复发和评测加速规则稳定进入上下文。永久把上限改到 64 KiB 只会掩盖结构问题并增加每轮上下文成本，不应作为最终方案。

当前文件混合了四种性质不同的内容：

1. 需要模型持续判断的长期规则，例如凭据边界、科学变量不可改变、正式结果证据要求。
2. 可复用工作流，例如分派、审查、Git、服务器恢复和 SwanLab 验收步骤。
3. 可以机械检查的条件，例如 Shell 引用、PATH、可执行文件、标签长度、输出目录为空、JSON 可解析。
4. 当前状态与历史事实，例如固定模型路径、某数据包数量、某版本缺陷和一次故障的完整修复经验。

只有第一类应长期留在通用 `AGENTS.md`。第二类应进入 Skill 或脚本；第三类应进入 Hook、启动器、模式校验和测试；第四类应进入机器可读配置、实验总控或 `.Codex/docs/` 历史记录。

## 推荐的最小拆分结构

建议最终结构如下，不增加同层回退文件：

```text
thesis/experiments/llm_probe/
├── AGENTS.md                 # 跨整个实验工程的少量长期规则，目标不超过 8 KiB
├── scripts/AGENTS.md         # 远程执行、rsync、重启恢复、Shell 与环境规则
├── src/flow_probe/AGENTS.md  # 数据合同、标签、模型入口、设备降级与运行制品规则
└── tests/AGENTS.md           # 最小测试选择、服务器 pytest、格式化与审查规则
```

`configs/AGENTS.md` 暂不创建。只有冻结协议和配置合同继续增长且无法由模式校验或测试表达时，再增加该层。

实验根 `AGENTS.md` 只保留：凭据不可落盘、正式实验证据合同、科学超参数不可因硬件降级而改变、服务器命令必须走统一启动器、子代理任务必须语义化命名、适用局部规则的路由。当前模型路径、数据量、具体版本和长故障说明移出。

需要注意：嵌套文件只有在当前工作目录位于对应路径时自动发现。建议把实验工作迁移到从 `llm_probe` 启动的专用会话；若仍从仓库根启动，实验根规则必须保留“按任务完整读取局部文件”的短路由，但不得把局部正文复制回根文件。[官方 AGENTS.md 分层说明](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

## `AGENTS.md` 渐进拆分执行合同

以下阶段是后续独立实现代理的执行合同。本次调研**不修改任何 `AGENTS.md`、Hook 或配置**。每一阶段必须形成独立差异、加载证据和回滚补丁；上一阶段没有通过新会话验收时，不得开始下一阶段。

当前三层链已经超过默认 32 KiB。迁移时“先新增子文件、验证后再删父级原文”会短暂增加字节数，因此新增阶段可使用一次性诊断命令 `codex --config project_doc_max_bytes=65536 --cd <子目录>` 核验完整链。该覆盖不能写入持久配置，也不能作为阶段最终通过证据；删除父级重复原文后，必须在**不带覆盖项**的新会话中重新验收。P4 和 P5 只接受默认 32 KiB 下的结果。

### P0：只读基线与回滚包

**修改范围：**不修改规则文件。只在 `.Codex/docs/agents-split/<运行标识>/P0/` 保存脱敏清单、字节统计、当前差异和后续回滚所需的原始文件副本或补丁；凭据、环境变量值和用户认证文件不得进入归档。

**前置验证：**记录当前 Codex 版本、仓库信任状态、工作树中与目标文件有关的既有改动，以及以下工作目录的理论活动链和逐文件字节数：仓库根、`thesis/experiments/llm_probe`、`scripts`、`src/flow_probe`、`tests`。运行时不存在的子级 `AGENTS.md` 标为“待创建”，不能伪造已加载状态。

**新会话验收：**分别从仓库根和 `llm_probe` 启动默认预算的只读新会话，在禁止搜索文件的前提下要求 Codex 报告启动时已注入的规则哨兵；再以 65,536 字节的一次性覆盖启动诊断会话，用于区分“路径没有发现”与“已发现但被预算截断”。基线必须明确证明：从仓库根启动不会自动加载 `thesis/` 和 `llm_probe/` 的深层规则，从 `llm_probe` 启动才会发现根、`thesis` 和实验根三层规则，同时记录默认预算下实际发生的截断。

**回滚命令：**P0 没有配置变更，无需回滚。若只想撤销本阶段新增的调研制品，先确认其中没有后续阶段依赖，再把整个 P0 目录移动到 `.Codex/docs/archive/`，不得删除其他历史记录。

**停止条件：**目标 `AGENTS.md` 存在未识别的并发改动；活动链与官方发现规则不符；无法建立不含凭据的备份；当前三层链字节数或文件内容与本文审计显著不一致。发生任一项时先更新基线，不得沿用旧字节数实施。

### P1：先拆 `scripts/AGENTS.md`

**修改范围：**只创建 `thesis/experiments/llm_probe/scripts/AGENTS.md`，并在验证后从实验根 `AGENTS.md` 删除已迁移的对应原文。迁移内容限于远程启动器、环境加载、`rsync`、`screen`、服务器重启恢复、`fd`/`rg`/`uv` 能力探测、Shell 引用，以及本次 `tee` 父目录与 `pipefail`/`PIPESTATUS` 防复发规则。实验根只保留一条简短路由和“正式远程命令必须使用统一启动器”的共同规则。

**前置验证：**先逐条建立“父文件原规则 → 子文件目标章节”映射，确认没有数据合同、训练配置或测试门禁混入。第一步只新增子文件，不删除父文件；运行 Markdown 格式化和 `git diff --check`，保存“仅新增”差异。

**新会话验收：**新增子文件后先从 `scripts` 启动一次 65,536 字节诊断会话，验证四层链及 `NOTE_LLM_PROBE_SCRIPTS` 哨兵，并用无副作用提示检查它能说出日志父目录、`set -Eeuo pipefail`、`PIPESTATUS` 和远程能力预检要求。通过后才从父文件删除重复原文，再从 `scripts` 和 `llm_probe` 各启动一次**默认预算**的新会话：前者应自动获得脚本规则，后者只应获得简短路由并在任务明确涉及 `scripts/` 时主动完整读取子文件。

**回滚命令：**阶段完成后保存只含这两个文件的正向补丁 `P1/stage.patch`。回滚前运行 `git apply -R --check P1/stage.patch`；检查通过后才运行 `git apply -R P1/stage.patch`。若目标行已有并发改动，停止自动回滚，改用 `apply_patch` 对照 P0 副本逐项恢复。

**停止条件：**从 `scripts` 启动未加载子规则；父文件删除后路由丢失；复杂远程任务从 `llm_probe` 启动时没有主动读取脚本规则；任一活动链超过 32,768 字节；`tee`/`pipefail` 正反例行为描述不完整。

### P2：迁移 `src/flow_probe/AGENTS.md`

**修改范围：**只创建 `src/flow_probe/AGENTS.md`，并在验证后从实验根删除生产代码、数据合同和正式运行合同的重复原文。子文件应承载字段与标签合同、数据处理边界、模型和训练入口、设备与精度降级、运行目录与制品完整性；当前模型路径、样本数量和一次性故障日志不进入规则。

**前置验证：**建立迁移映射，区分长期不变量与过时状态；核对这些规则是否同时适用于所有 `flow_probe` 生产模块。先只新增子文件并保存差异，不移动测试、Git 或远程 Shell 规则。

**新会话验收：**新增子文件后从 `src/flow_probe` 启动一次 65,536 字节诊断会话，验证 `NOTE_LLM_PROBE_FLOW_PROBE` 哨兵和四层活动链，并用一个只读数据合同审查提示确认标签、设备降级和制品要求可被复述。删除父文件重复原文后，再从 `src/flow_probe` 和 `llm_probe` 启动默认预算的新会话，确认前者自动加载局部规则，后者在涉及 `src/flow_probe/` 的任务中按父级短路由显式读取子规则。

**回滚命令：**保存只含实验根和 `src/flow_probe/AGENTS.md` 的 `P2/stage.patch`；使用 `git apply -R --check` 后再 `git apply -R`。检查失败即停止，不得覆盖用户在同一区域的新改动。

**停止条件：**生产规则被拆到测试层；科学变量因硬件降级规则变得可改；从 `llm_probe` 启动时任务未显式读取子规则；任一链超出字节上限；迁移造成同一合同在父子层出现不一致版本。

### P3：迁移 `tests/AGENTS.md`

**修改范围：**只创建 `tests/AGENTS.md`，并在验证后从实验根删除测试选择、服务器测试、格式化和静态检查的重复原文。子文件应明确最小覆盖优先、服务器环境为正式验收环境、Ruff 无新增问题时不重复修改和检查，以及格式化门禁不能阻塞已获授权的正式实验。

**前置验证：**确认待迁移内容只约束测试与验收，不把生产运行命令、科学评价协议或 Git 发布规则一起移动。先新增后验证，不同时清理父文件。

**新会话验收：**新增子文件后从 `tests` 启动一次 65,536 字节诊断会话，验证 `NOTE_LLM_PROBE_TESTS` 哨兵，并用“单文件缺陷修复应运行什么检查”的无副作用问题验证最小测试选择。删除父级重复原文后，再从 `tests` 和 `llm_probe` 启动默认预算的新会话，确认前者自动加载局部规则，后者在涉及测试的任务中显式读取局部文件，同时普通训练启动不会被 Black、Ruff 或完整测试无谓阻塞。

**回滚命令：**保存 `P3/stage.patch`，先执行反向补丁检查，再执行反向应用；并发修改存在时按 P0 备份人工恢复，不使用整文件覆盖。

**停止条件：**局部规则要求每次都跑完整测试；格式化或 Ruff 重新成为实验启动门禁；服务器测试要求被遗漏；父级短路由失效；任一活动链超过默认字节预算。

### P4：收敛实验根共同规则

**修改范围：**只精简 `llm_probe/AGENTS.md`，不再创建新的规则层。保留凭据不可落盘、正式实验证据合同、科学超参数不可因硬件变化而改变、子代理语义化命名、长任务不中断实验、Git 提醒边界，以及 `scripts`、`src/flow_probe`、`tests` 三条短路由。目标不超过 8 KiB。

**前置验证：**P1 至 P3 全部通过；逐条证明被删内容已在某个子文件、确定性脚本、Hook、测试或历史文档中有唯一归属。没有唯一归属的规则不得删除。

**新会话验收：**从 `llm_probe` 启动，确认根、`thesis`、实验根链低于 32 KiB，三个子域任务都会按路径读取对应局部规则，普通实验调度不会加载三份局部正文。再分别从三个子目录启动，确认各自四层链也低于上限且没有冲突。

**回滚命令：**保存仅包含实验根收敛改动的 `P4/stage.patch`；按反向检查、反向应用两步回滚。若发现遗漏，只恢复缺失条目，不把全部历史故障说明复制回父文件。

**停止条件：**实验根超过 8 KiB；共同规则被错误移入单一子域；路由要求不明确；同一条规则在父子文件中含义冲突；任何启动路径超过 32 KiB。

### P5：启动路径差异验收

**修改范围：**原则上不再移动正文，只允许修正短路由、哨兵和实施记录。不得借最终验收重新大改四份规则文件。

**前置验证：**冻结 P4 差异；为仓库根、`llm_probe`、`scripts`、`src/flow_probe` 和 `tests` 五个工作目录列出预期活动链和总字节。

**新会话验收：**逐目录启动全新会话，禁止工具搜索后报告已加载哨兵，再允许只读核对文件。预期结果必须是：仓库根只自动获得仓库根规则；`llm_probe` 自动获得仓库根、`thesis`、实验根；三个子目录分别再多获得自己的局部规则。仓库根启动的实验任务必须依据根级路由主动完整读取 `thesis/AGENTS.md`、`llm_probe/AGENTS.md` 和对应局部文件，或明确改用 `codex --cd thesis/experiments/llm_probe` 的专用会话。

**回滚命令：**P5 若只产生记录，无需回滚规则；若修正路由，单独保存 `P5/stage.patch` 并按反向检查、反向应用回滚。最终可以按 P4、P3、P2、P1 的逆序逐阶段撤销，不能跨阶段整文件复原。

**停止条件：**任何会话报告的链与预期不一致；根启动时误称深层规则会自动发现；短路由要求复制局部正文回父文件；字节预算、格式检查或五条路径中任一项未通过。

执行期间每阶段只允许一个实现代理修改上述目标文件，完成后由新的审查代理检查阶段映射、实际差异和加载证据。调研代理不兼任实现代理，避免把研究结论和实际迁移混成一次不可回滚改动。

## 子代理命名与任务描述门禁

推荐新增一个项目级命令 Hook，挂到 `PreToolUse`，匹配器使用 `^(spawn_agent|Agent)$`。Hook 读取本次调用参数并执行以下检查：

1. `task_name` 必须存在，使用小写蛇形命名，建议 5 至 48 个字符。
2. 拒绝 `task1`、`tmp`、`agent`、`worker1`、`test` 等无职责语义名称。
3. `message` 必须明确写出目标、文件或系统边界、预期交付和禁止事项或验证方式；不满足时拒绝而不是自动改名。
4. 拒绝结果应给出可直接重试的示例，例如 `tqhc2_eval_audit` 和结构化任务描述。
5. Hook 只校验新建代理。复用旧代理时由调度 Skill 要求声明中文职责别名；不能假装已经改变既有代理名称。

不建议 Hook 自动重写 `task_name`。自动命名可能掩盖任务边界不清，拒绝后让主代理重新提交更可审查。可以另建一个项目 Skill 保存任务描述模板，减少每次手写成本；Hook 仍是最终门禁。

## 服务器能力与远程命令防复发

### 统一能力探测

服务器曾出现 `fd: command not found`，说明“本机已安装”与“服务器当前非交互 PATH 可发现”被混为一谈。应建立固定的远程预检启动器，顺序如下：

1. 先 `source ~/.bashrc`，再启用 `set -Eeuo pipefail`；确需逐项收集管道状态时，必须在管道结束后立即保存 Bash 的 `PIPESTATUS`。
2. 显式补入服务器允许的工具目录，再分别运行 `command -v fd`、`command -v rg`、`command -v uv`。
3. 工具已经安装但不在 PATH 时修正 PATH，并记录实际绝对路径和版本。
4. `fd` 确实缺失时，只在“文件枚举”场景使用已批准的 `rg --files` 降级；其他语义不得偷偷替换。
5. `rg` 缺失时停止并给出安装动作，因为仓库规则不允许换用传统搜索工具。
6. `uv` 缺失时先检查 `/root/.local/bin/uv`；仍缺失则明确安装或停止，不允许在命令尾部才失败。
7. 每次服务器重启或实例变化后重新生成能力清单。

动态能力清单应写入持久化实验目录，例如 `runs/environment/server-capabilities/<启动标识>.json`，包含启动标识、时间、PATH、工具绝对路径、版本、GPU/CPU 和磁盘摘要。`AGENTS.md` 只保留“远程命令必须经过能力预检”这一条，不再保存“服务器现在有 fd”之类易过时事实。

### 远程工具 Hook

扩展现有 `PreToolUse` 的 `Bash` 检查：当命令包含 SSH、`GPU_SSH`、`expect /tmp/gpu-exec.exp` 或既有 GPU 启动器，并在远端载荷中使用 `fd`、`rg`、`uv` 时，只允许以下两类调用：

- 调用已验证的统一远程启动器；
- 在极小的一次性命令中，明确先加载环境并对所需工具执行能力探测。

其余调用拒绝，并提示改用启动器。Hook 只能检查命令形态，服务器工具是否真实可用仍由启动器验证。官方说明 `PreToolUse` 能检查 `Bash` 的 `tool_input.command`，但也提醒某些专用工具路径可能绕过 Hook，因此脚本本身必须继续失败即停。[官方 Hook 文档](https://learn.chatgpt.com/docs/hooks)

### 字面量 `\n` 与引用层级

另一类已发生故障是调用端把真实换行转成字面量 `\n`，导致远端 Bash 在 `cd` 前解析失败。建议执行以下约束：

- 禁止用 `JSON.stringify` 或多层字符串拼接生成传给 `expect /tmp/gpu-exec.exp` 的多行远程 Shell。
- 正式或超过一条简单语句的命令写入本地持久化 `.sh`，通过白名单 `rsync` 上传到服务器，核对 SHA-256 后用 `bash <脚本> <参数文件>` 执行。
- 动态参数写入 JSON/YAML 参数文件，由固定脚本解析；不要把配置重新拼回多层 Shell 字符串。
- 临时命令必须短且单行。需要多行时仍使用唯一暂存脚本，不使用嵌套 here-document 或多层引号。
- `PreToolUse` 对远程 `expect`/SSH 调用检查载荷中的两个字符反斜杠加 `n`；发现可疑字面量时拒绝并要求脚本传输。检查应区分 JSON 解码后的真实换行字符与字面量 `\n`。

最小自动验证应覆盖：字面量 `\n` 被拒绝；普通单行远程命令通过；调用统一启动器通过；裸远程 `fd`/`rg`/`uv` 被拒绝；工具存在但 PATH 缺失时预检能修正；工具确实缺失时产生明确状态和退出码；上传脚本哈希不一致时拒绝执行。

### 管道日志完整性与退出码

本轮预检已复现另一项远程包装器缺陷：命令使用 `前序命令 | tee target/log` 时，日志父目录尚未创建，`tee` 写入失败；包装器随后继续执行 `wc` 和 `jq`，后两者成功，导致 SSH 最终退出码为 0。表面上任务“成功”，实际上正式日志没有落盘。

该规则应写入建议的 `scripts/AGENTS.md` 和统一启动器合同，**不再堆入实验根 `AGENTS.md`**：

1. 任何 `命令 | tee 日志路径` 执行前，先用 `mkdir -p -- "$(dirname -- "$log_path")"` 创建父目录，并以 `test -d`、`test -w` 或一次受控临时写入核对目录可用。
2. 远程 Bash 包装器默认启用 `set -Eeuo pipefail`。这样前序命令或 `tee` 任一失败都会使管道失败，不能由后续成功命令掩盖。
3. 如果包装器为了汇总多个状态而暂时关闭 `errexit`，必须在管道结束后的第一条语句保存 `PIPESTATUS`，分别检查前序命令和 `tee`，随后恢复 `set -e`；不能只读取 `$?` 后继续运行。
4. 只有前序命令退出 0、`tee` 退出 0、日志文件存在且非空时，才允许执行后续 `wc`、`jq` 或上传步骤。任何条件失败都应写入独立状态文件并返回非零退出码。
5. 启动器的回归冒烟应覆盖：父目录不存在时自动创建；目标不可写时失败；前序命令失败但 `tee` 成功时失败；前序命令成功但 `tee` 失败时失败；二者成功时才继续后处理。

Hook 只需拦截绕过统一启动器的复杂远程管道，并提示改用启动器；目录创建、`pipefail`、`PIPESTATUS` 和日志制品验证属于确定性 Shell 合同，应由脚本本身实现。

## 机制比较

| 机制 | 当前仓库适合度 | 能否机械强制 | 常驻上下文 | 启用注意事项 |
| --- | --- | --- | --- | --- |
| 嵌套 `AGENTS.md` | 高 | 否，属于模型指令 | 仅适用路径加载，但正文仍占上下文 | 规则链每次运行开始构建；使用新会话或正确 `--cd` |
| `AGENTS.override.md` | 低，仅临时替换 | 否 | 与被替换文件相同 | 同层 `AGENTS.md` 会被忽略，不用于拆分 |
| 提高 `project_doc_max_bytes` | 仅迁移期应急 | 否 | 明显增加 | 修改后重启或新命令；拆分后恢复默认 |
| `project_doc_fallback_filenames` | 低 | 否 | 不降低 | 只是候选文件名，每层仍只取一个 |
| 项目 `.codex/config.toml` | 高，保存结构化设置 | 配置项可强制 | 不作为长篇自然语言规则注入 | 项目需受信任；新会话最稳妥 |
| `PreToolUse` Hook | 很高 | 是，可拒绝支持的工具调用 | 仅错误或附加信息进入上下文 | 新定义需审查信任；官方不承诺覆盖所有专用工具 |
| `SubagentStart` Hook | 低，适合提醒 | 否，不能阻止启动 | 可追加少量上下文 | 不用于命名门禁 |
| 项目 Skill | 高，保存长流程 | 否，除非由 Hook/规则要求 | 渐进加载，常驻成本较低 | 修改通常自动发现，未出现时重启 |
| 项目定制代理 | 中高，固定角色 | 只能固定代理类型 | 官方未给出精确上下文成本 | 不校验每次任务实例名；新会话最稳妥 |
| 插件 | 当前较低 | 可打包 Hook | 取决于所含能力 | 适合跨仓库分发，当前范围过重 |
| Hook 调用的复用脚本 | 很高 | 是 | 几乎不占模型上下文 | 脚本需独立测试；注册新 Hook 时需重新信任 |

## 官方现状：Codex Skills 与插件治理

以下跨平台官方资料的访问日期均为 **2026-07-30**。本节把结论分成三类：**事实**表示官方文档直接说明；**推断**表示由官方机制与本机审计共同推出，但官方未承诺结果；**未支持**表示所查官方文档没有给出该能力，不能把其他产品的行为套到 Codex。

### 渐进披露与索引预算

- **事实：**Codex 启动时先向模型提供技能的名称、描述和路径，选中技能后才加载完整 `SKILL.md`。初始技能清单最多占上下文窗口的 2%，未知窗口大小时上限为 8,000 个字符；技能过多时先缩短描述，仍超限时会省略部分技能并给出警告。[OpenAI：Build skills](https://learn.chatgpt.com/docs/build-skills)
- **事实：**技能可以通过 `/skills` 或 `$技能名` 显式调用，也可以依据描述隐式触发。仓库技能从当前目录逐级扫描到仓库根；用户技能的当前官方位置是 `$HOME/.agents/skills`。[OpenAI：Build skills](https://learn.chatgpt.com/docs/build-skills)
- **事实：**同名技能不会合并，两个条目都可能进入清单。[OpenAI：Build skills](https://learn.chatgpt.com/docs/build-skills)
- **推断：**不同路径下的完全相同技能仍会占用两个候选位置，因而可能提前触发描述缩短或条目省略。官方没有量化这种重复对触发准确率和延迟的影响。

### 禁用、手动调用与作用域

Codex 当前提供两种相邻但不等价的控制：

1. **事实：**可以在配置中使用 `[[skills.config]]`，按路径设置 `enabled = false`；修改后需要重启 Codex 才能生效。[OpenAI：Build skills](https://learn.chatgpt.com/docs/build-skills)
2. **事实：**自有技能可以在 `agents/openai.yaml` 中设置 `policy.allow_implicit_invocation: false`。这样模型不会隐式调用该技能，但用户仍可使用 `$技能名` 显式调用。[OpenAI：Build skills](https://learn.chatgpt.com/docs/build-skills)

二者的边界必须明确：

- **未支持：**官方没有说明 `allow_implicit_invocation: false` 会把名称、描述和路径移出初始技能清单。因此它能关闭自动触发，却不能被当作“确定节省索引预算”的办法。
- **未支持：**官方没有说明 `enabled = false` 后仍允许 `$技能名`。最安全的解释是该技能在当前会话不可用，必须重新启用并开始新会话。
- **结论：**Codex 目前没有官方承诺的单一开关，能够同时做到“从初始候选索引中移除”和“同一会话继续显式调用”。若只要求防止误触发，使用 `allow_implicit_invocation: false`；若必须真正缩减候选集合，使用独立配置档禁用，并在需要时切换到完整配置档重新启动会话。

Codex 配置优先级从高到低为：命令行参数、项目 `.codex/config.toml`、所选配置档、用户配置、系统配置、默认值。项目配置只在受信任项目中加载，且离当前目录更近的项目配置覆盖上层配置。[OpenAI：Basic configuration](https://learn.chatgpt.com/docs/config-file/config-basic)；[OpenAI：Advanced configuration](https://learn.chatgpt.com/docs/config-file/config-advanced)；[OpenAI：Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)

- **事实：**当前配置档使用 `$HOME/.codex/<配置档名>.config.toml`，由 `codex --profile <配置档名>` 选择；项目配置不能替用户自动选择配置档。[OpenAI：Advanced configuration](https://learn.chatgpt.com/docs/config-file/config-advanced)
- **推断：**可以建立一个只在论文仓库启动时选用的“论文精简配置档”，不影响其他仓库的默认技能集合。项目配置优先级更高，若以后在项目层再次设置同一路径，应以项目层为准。
- **注意：**`Build skills` 的示例把 `path` 写到 `SKILL.md`，配置参考页则把它描述为包含 `SKILL.md` 的目录。实施时应先从 `/skills` 复制 Codex 实际显示的路径，只做一项禁用并在新会话验证，不能凭文档差异批量改动。

### 插件、清单和可信边界

- **事实：**独立 Skill 可以在 `agents/openai.yaml` 声明界面元数据、调用策略和 MCP 工具依赖。依赖项包含类型、标识、描述、传输方式和地址，但不是可解析的版本锁或安装锁文件。[OpenAI：Build skills](https://learn.chatgpt.com/docs/build-skills)
- **事实：**Codex 插件可以打包 Skills、连接器、MCP 服务器和 Hooks；安装后需要开始新会话。`/plugins` 可查看和切换已安装插件。[OpenAI：Plugins](https://learn.chatgpt.com/docs/plugins)；[OpenAI：Build plugins](https://learn.chatgpt.com/docs/build-plugins)
- **事实：**配置参考明确提供插件所含 MCP 服务器和工具的启用、禁用及审批控制；这不等于一个通用的“每个插件内技能白名单”。[OpenAI：Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- **未支持：**所查 OpenAI 文档没有保证插件技能采用稳定的 `插件名:技能名` 命名空间。当前运行时确实能看到若干带前缀名称，但不能把本次观察当成长期接口。
- **未支持：**独立 Codex Skill 没有官方定义的版本解析、依赖锁定、来源签名、安装回滚和使用次数遥测。插件适合打包分发，但不能替代外部制品清单和 Git 提交锁定。
- **推断：**项目市场主要解决分发，不代表插件会仅因当前工作目录匹配而自动启用。论文仓库若不需要某个插件，应显式关闭并以新会话验证，不应依赖目录猜测。

## 工业界方案

### Anthropic Agent Skills 与 Claude Code

Anthropic 当前提供了最完整的“候选集合缩减且保留显式调用”机制：

- **事实：**`disable-model-invocation: true` 会禁止模型自动调用，技能描述不进入上下文，但用户仍能通过 `/技能名` 显式调用，调用时才加载完整内容。[Anthropic：Extend Claude with skills](https://code.claude.com/docs/en/skills)
- **事实：**本地覆盖项 `skillOverrides` 支持 `on`、`name-only`、`user-invocable-only`、`off` 四态；其中 `user-invocable-only` 对模型隐藏、对用户菜单可见，`off` 则两边都不可用。[Anthropic：Extend Claude with skills](https://code.claude.com/docs/en/skills)
- **事实：**Claude Code 的技能清单预算默认为模型上下文的 1%。它始终保留名称，空间不足时缩短或删除低使用技能的描述；`/doctor` 可估算主要贡献者，`/context` 可查看实际占用。[Anthropic：Extend Claude with skills](https://code.claude.com/docs/en/skills)
- **事实：**技能作用域包括企业、个人、项目和插件。同名技能的优先顺序为企业、个人、项目；插件技能使用 `插件名:技能名` 命名空间，不与普通技能冲突。嵌套项目技能可随首次进入对应子目录动态出现；较新版本还会对指向同一目标的符号链接去重。[Anthropic：Extend Claude with skills](https://code.claude.com/docs/en/skills)
- **事实：**技能可声明允许和禁止的工具，权限规则还能按精确技能名或前缀控制。插件清单带版本；社区目录可以锁定到提交 SHA，版本未变化时不会自动替换插件内容，并提供严格验证和单会话试装方式。[Anthropic：Extend Claude with skills](https://code.claude.com/docs/en/skills)；[Anthropic：Create plugins](https://code.claude.com/docs/en/plugins)
- **事实：**官方技能创建器支持隔离运行、`evals/evals.json`、技能与无技能基准、时间和词元对比、版本盲测、应触发与不应触发命中率。[Anthropic：Extend Claude with skills](https://code.claude.com/docs/en/skills)

可借鉴的是四态覆盖、稳定命名空间、按目录动态发现、使用频率裁剪和触发评测。**不能直接照搬** Claude Code 的字段到 Codex；Codex 只认可自己文档中定义的元数据。

开放的 Agent Skills 规范只规定 `name`、`description` 以及可选的 `license`、`compatibility`、`metadata` 和实验性 `allowed-tools`。`metadata.version` 只是自由元数据，不是跨宿主的版本锁；发现路径、优先级、调用控制、遥测和回滚仍由宿主实现。[Agent Skills：Specification](https://agentskills.io/specification)

### GitHub Copilot Skills、定制代理与 `gh skill`

- **事实：**Copilot Agent Skills 支持项目目录 `.github/skills`、`.claude/skills`、`.agents/skills`，以及个人目录 `~/.copilot/skills`、`~/.agents/skills`。选中后才注入完整内容，用户也能通过斜杠命令显式调用。[GitHub：About Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)；[GitHub：Add skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills)
- **事实：**Copilot CLI 提供 `/skills list`、`/skills info`、`/skills reload` 和交互式启停。官方同时提醒技能可能包含脚本，应只从可信来源安装。[GitHub：Add skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills)
- **事实：**`gh skill` 支持检索、预览、项目或用户作用域安装、更新、发布和 JSON 清单。安装可锁定到标签或提交 SHA；更新按树 SHA 比较，锁定项默认跳过，支持 `--dry-run` 和 `--force` 恢复来源版本。[GitHub CLI：gh skill install](https://cli.github.com/manual/gh_skill_install)；[GitHub CLI：gh skill update](https://cli.github.com/manual/gh_skill_update)；[GitHub CLI：gh skill list](https://cli.github.com/manual/gh_skill_list)；[GitHub CLI：gh skill preview](https://cli.github.com/manual/gh_skill_preview)
- **事实：**GitHub 定制代理另有 `disable-model-invocation`、`user-invocable`、工具白名单和同名文件的层级覆盖，但这些字段属于**定制代理**，不是 Agent Skills。[GitHub：Custom agents configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- **未支持：**所查官方 Skill 文档没有公开初始索引预算、同名技能优先级、插件式命名空间，或“禁用自动调用但保留显式调用”的 Skill 级四态开关。

本仓库最值得借鉴的是 `gh skill` 的来源 URL、版本、锁定状态、安装作用域、树 SHA、预览与干运行清单。即使仍由 Codex 执行，也可以把它作为**外部供应链台账**，但是否由 Codex 正确发现仍需 `/skills` 实测。

### Cursor Rules、Commands 与 Agent Skills

- **事实：**Cursor 项目 Rules 存放于 `.cursor/rules`，支持 `Always`、按路径自动附加、由代理按描述请求和 `Manual` 四种模式；`Manual` 规则只在用户通过 `@规则名` 指定时进入上下文。规则还可以嵌套在子目录。[Cursor：Rules](https://cursor.com/docs/rules)
- **事实：**Cursor Commands 使用 `.cursor/commands/*.md` 定义可复用斜杠工作流；该能力最初以测试阶段发布。[Cursor：1.6 changelog](https://cursor.com/changelog/1-6)
- **事实：**Cursor 已在编辑器和 CLI 中支持从 `SKILL.md` 动态发现 Agent Skills，并允许通过斜杠命令显式调用。[Cursor：Agent Skills](https://cursor.com/docs/skills)；[Cursor：2.4 changelog](https://cursor.com/changelog/2-4)
- **事实：**Cursor 的 Shell 与文件权限可以在全局或项目层配置，但当前官方权限页描述的是工具和命令权限，不是逐技能权限。[Cursor：CLI permissions](https://docs.cursor.com/cli/reference/permissions)
- **未支持：**所查 Cursor 官方页面没有公开 Skill 索引预算、重复项优先级、技能命名空间、手动专用技能覆盖、版本锁定、依赖声明或使用频率遥测。

Cursor 的可借鉴点是把“长期自动规则”和“手动工作流”分开。对 Codex 而言，对应关系只能是设计启发：短而通用的规则留在 `AGENTS.md`，长流程放 Skill；不能把 Cursor 的 `Manual` 字段直接写进 Codex Skill。

### 代表性注册表：Microsoft Semantic Kernel

Semantic Kernel 不是 `SKILL.md` 宿主，但给出了大规模能力注册表的代表性治理方法：

- **事实：**插件是一组带名称和描述的函数，只会在应用显式注册进 Kernel 后可用；插件名作为函数命名空间，允许不同插件出现同名函数。[Microsoft：Plugins in Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/concepts/plugins/)；[Microsoft：Function calling](https://learn.microsoft.com/en-us/semantic-kernel/concepts/ai-services/chat-completion/function-calling/)
- **事实：**实验性的上下文函数选择先用向量检索匹配函数名称和描述，再只把 Top-K 函数通告给模型。官方明确提醒 K 太小会漏掉必要函数，太大会增加词元成本和幻觉，并要求同步向量索引。[Microsoft：Contextual function selection](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-contextual-function-selection)
- **推断：**可扩展的通用结构应是“完整注册表 → 作用域和权限过滤 → 基于任务检索 Top-K → 将选中能力通告模型”，而不是把所有能力描述常驻上下文。应用仍能在模型候选集合之外直接调用已注册函数，因此可兼顾程序化显式调用。
- **未支持：**Codex 当前没有公开的 Skills Top-K 检索器接口，不能在本仓库自行接管它的内置技能选择。该模式只适合未来自建调度器或向 OpenAI 提交产品需求。

### 工业界机制对照

| 维度 | OpenAI Codex | Anthropic Claude Code | GitHub Copilot | Cursor | Semantic Kernel |
| --- | --- | --- | --- | --- | --- |
| 渐进披露 | 名称、描述、路径先加载，正文按需 | 名称、描述先加载，正文按需 | 正文按需 | Skills 动态发现 | 只通告选中函数 |
| 公开索引预算 | 2% 或 8,000 字符 | 1%，可查看主要贡献者 | 未公开 | 未公开 | 由应用设置 Top-K |
| 保留显式调用且不进模型候选 | **未完整支持**；仅能禁隐式但未保证移出索引 | `user-invocable-only` 或 `disable-model-invocation` | Skill 级未公开 | Manual Rules 可实现，但不是 Skills | 应用可直接调用未通告函数 |
| 同名治理 | 不合并 | 层级覆盖；插件命名空间 | Skill 级未公开 | 未公开 | 插件名命名空间 |
| 作用域 | 用户、仓库目录、插件 | 企业、个人、项目、插件 | 个人、项目 | 用户、项目、嵌套目录 | 应用注册边界 |
| 版本和来源 | 独立 Skill 未提供锁定 | 插件版本和提交 SHA | `gh skill` 标签或 SHA 锁定 | 未公开 | 由应用依赖系统管理 |
| 逐能力权限 | 可声明 MCP 工具依赖；未见 Skill 级权限白名单 | 精确技能和前缀权限 | Skills 可声明工具，CLI 可启停 | 工具级权限 | 应用白名单 |
| 测试和遥测 | 未公开内置触发评测或使用频率裁剪 | 官方隔离评测、A/B、命中率和低频裁剪 | 未公开触发评测 | 未公开 | 应用自行记录检索和调用 |
| 回滚 | 删除配置覆盖并重启 | 覆盖四态、插件版本和 SHA | `--dry-run`、锁定、`--force` | Git 回滚规则 | 依赖和应用版本回滚 |

## 适用于本仓库的组合

### 当前技能集合审计

本机只统计两个用户可见目录，未计插件缓存、系统技能和运行时临时贡献：

- `~/.agents/skills`：125 个 `SKILL.md`。
- `~/.codex/skills`：51 个 `SKILL.md`。
- 合计：176 个文件，是本机这两个待治理目录的文件规模。完整运行时还可能包含插件、系统和临时贡献，但这 176 项是否全部进入当前候选必须由 `/skills` 验证，不能直接把文件数当成运行时的上界或下界。
- 两处共有 37 个同名技能：20 对 SHA-256 完全一致，17 对内容不同。
- 名称以 `source-` 或 `command-` 开头的技能共有 52 个，应作为来源和用途审计对象，不能仅凭前缀判定删除。

20 对完全相同的重复项包括 `architecture-design`、`bug-detective`、`code-review-excellence`、`git-workflow`、`planning-with-files`、`results-analysis`、`publication-chart-skill` 和 `zotero-obsidian-bridge` 等。17 对内容分叉项包括 `research-ideation`、`ml-paper-writing`、`results-report`、`writing-anti-ai`、`obsidian-project-kb-core`、`uv-package-manager` 和 `verification-loop` 等。

**裁决：**先处理完全相同项，再逐对审查分叉项。完全相同项默认保留当前官方用户位置 `~/.agents/skills` 下的副本，把旧 `~/.codex/skills` 副本列入论文配置档禁用候选；分叉项必须比较版本、来源、依赖和实际调用结果，不能按目录批量覆盖。

### 三层候选集合

建议把技能分为三层，而不是建立一次性永久白名单：

| 层级 | 论文仓库中的用途 | 代表技能 | 处理方式 |
| --- | --- | --- | --- |
| 核心自动候选 | 高频且应被任务描述自动触发 | `planning-with-files`、`research-ideation`、`citation-verification`、`results-analysis`、`results-report`、`ml-paper-writing`、`architecture-design`、`bug-detective`、`swanlab-skill` | 保持启用并优化描述边界 |
| 手动候选 | 有用但只在明确请求时需要 | `pdf-converter`、`zotero-obsidian-bridge`、`hf-cli`、特定 Hugging Face 训练器、浏览器控制、图表与论文投稿技能 | 自有技能可关闭隐式调用；第三方技能不能擅改，保留启用或移入按需配置档 |
| 非当前候选 | 与毕业论文当前阶段无关或完全重复 | 网站构建、云部署、会后材料、非目标期刊整套技能、已确认的重复副本 | 在论文精简配置档中按路径禁用，不删除文件 |

核心层也不应无限扩张。`obsidian-project-kb-core`、`obsidian-literature-workflow` 与 `obsidian-source-ingestion` 应明确各自触发条件；Git 操作只保留一个主入口，再由该入口路由 `git-commit` 或 `git-push`，避免三段相近描述同时竞争。

### 最小可逆配置模板

本次只提供模板，**没有创建或修改任何配置**。第一阶段建议用独立配置档，而不是直接污染用户默认配置或项目配置：

```toml
# ~/.codex/thesis.config.toml
# 示例：保留 ~/.agents/skills 中的官方用户副本，禁用内容完全相同的旧副本。
[[skills.config]]
path = "/Users/bilibili/.codex/skills/architecture-design/SKILL.md"
enabled = false

[[skills.config]]
path = "/Users/bilibili/.codex/skills/bug-detective/SKILL.md"
enabled = false
```

用 `codex --profile thesis --cd /Users/bilibili/personal/note` 启动论文会话；普通会话不带该配置档。由于官方两页对 `path` 是目录还是文件的描述不一致，正式实施前必须以 `/skills` 当前显示的实际路径做单项验证，模板不能直接批量复制。

对本仓库自有、偶尔才用但必须在同一会话手动调用的 Skill，可以采用：

```yaml
# agents/openai.yaml
policy:
  allow_implicit_invocation: false
```

这只保证“禁止隐式调用、保留 `$技能名`”，**不保证减少初始索引字符**。不得直接修改插件缓存或第三方 Skill 的元数据；需要第三方技能时，优先通过配置档切换。

### 验收、遥测和回滚

候选治理不能只看文件数量，至少记录以下基线与验收数据：

1. 在未精简的新会话执行 `/skills`，保存实际条目数、被省略警告、同名项和路径，不用 `fd` 文件数代替运行时事实。
2. 启用论文配置档后再次记录相同数据。20 对完全重复项应只剩一个可用来源，核心技能不得缺失。
3. 为核心技能建立 10 条“应触发”和 10 条“不应触发”提示，至少运行 5 个独立会话，记录选中技能、错误触发、漏触发、首响应时延和输入词元。Codex 没有公开内置评测器时，将结果写成 JSONL 并保留 Codex 版本。
4. 对手动技能验证 `$技能名` 正向调用；对配置档禁用项验证其不再出现在 `/skills`。不要宣称禁用项还能在同一会话调用。
5. 对插件记录来源、版本或 Git SHA、所含 Skills、MCP 和 Hooks、启停时间与信任人。能由 `gh skill` 管理的独立技能，保存 `sourceURL`、`version`、`pinned`、`scope` 和 `path` 清单。
6. 每季度或 Codex 升级后复跑触发集。连续两个周期未显式或隐式使用的非核心技能进入待禁用清单；先禁用一个周期，再决定是否卸载。

最小回滚路径如下：

- 配置档异常：不带 `--profile thesis` 启动新会话即可恢复默认集合。
- 单项禁用异常：删除对应 `[[skills.config]]` 或改回启用，随后开始新会话。
- 插件异常：在 `/plugins` 重新启用或禁用，并按官方要求开始新会话。
- 元数据异常：回滚自有 Skill 的 Git 提交；第三方缓存不做原地修改。
- 触发准确率下降：先恢复上一份技能清单，再审查描述冲突；不以继续删技能掩盖错误路由。

### Skills 治理授权边界

截至 2026-07-30，用户只授权执行 **Skills-P0** 和 **Skills-P1**。本调研代理仅完成方案与合同，不兼任实施；文档完成后由新的实现代理单独执行，而且不能与上面的 `AGENTS.md` 渐进拆分放进同一批修改、补丁或验收记录。

**Skills-P0：只读冻结。**先保存运行时 `/skills` 清单、所有来源路径、SHA-256、同名分组、Codex 版本、脱敏配置层、所选配置档、插件贡献和当前索引警告。公开台账写入 `.Codex/docs/skill-governance/<运行标识>/P0/`，可能包含本机配置原文的回滚包只能放在权限为 700 的 `~/.codex/backups/`，不得纳入 Git，也不得复制 `auth.json`、令牌或环境变量值。P0 不改 Skill、配置、插件或隐式调用策略；运行时清单与文件审计无法对应时停止并先查明来源。

**Skills-P1：只处理 20 对逐字节相同副本。**必须在 P0 冻结完成后，通过专用论文配置档或等价隔离方式禁用每对中的一个路径；不删除文件，不改 `agents/openai.yaml`，不切换插件，不写入默认用户全局策略。每项台账必须记录技能名、保留的规范路径、被隔离路径、两者相同的 SHA-256、选择理由、配置差异和回滚动作。规范路径优先采用当前官方用户位置 `~/.agents/skills`，但只有 P0 证明该路径确实进入运行时后才能选定。

Skills-P1 每批修改后必须开始全新 Codex 会话，确认 `/skills` 中该名字至少剩一个可用来源，并用 `$技能名` 加“只报告已加载、不得执行外部动作”的参数做显式调用冒烟。立即回滚条件包括：任一名字完全消失；显式调用失败；两个路径哈希已变化；修改触及 17 对同名不同内容项；出现隐式调用策略、插件或默认用户配置差异。最快回滚是不用论文配置档启动新会话；随后用 P0 副本恢复论文配置档并再次验证。

**Skills-P2 及以后未授权。**低频技能的 `allow_implicit_invocation` 调整、确定无关技能或插件禁用、17 对内容分叉项裁决、使用遥测、季度淘汰和版本迁移都只保留为研究计划。任何实现前必须重新取得用户明确批准，不得借 P0/P1 顺带修改。

### 不阻塞实验的实施顺序

1. 执行 Skills-P0，只做运行时清单、来源、哈希、配置和 20 对完全重复项台账，不停止当前训练与评测。
2. Skills-P0 验收后，在独立 Codex 会话中对一个完全重复项试用论文配置档，验证 `/skills` 和显式 `$技能名`。
3. 单项通过后把其余 19 对分两批处理；每批都保存逐项台账，并可通过不选论文配置档立即回滚。
4. Skills-P1 全部通过后停止修改，向用户报告剩余索引、20 个规范来源和回滚包位置，等待新的明确授权。
5. 只有新授权后才审查 17 对分叉项、当前阶段无关插件和 52 个 `source-`/`command-` 候选；没有证据时保留并标明风险。
6. 项目配置迁移、隐式调用策略、遥测和季度淘汰均属于 Skills-P2 以后，不得在当前授权中执行。

## 暂不采用

- **不采用一次性全量白名单。**Codex 只有按路径启停，没有经过官方验证的声明式“除这些外全部禁用”；全量否定清单会随插件更新漂移。
- **不采用删除 Skill 文件去重。**20 对完全重复项可先由配置档屏蔽，17 对分叉项仍需判断规范版本；直接删除会破坏其他项目。
- **不把 `allow_implicit_invocation: false` 宣称为索引压缩。**官方只保证不隐式调用，没有保证名称和描述不进入候选清单。
- **不把已禁用 Skill 宣称为同会话可显式调用。**当前官方文档没有此保证；需要时切换完整配置档并启动新会话。
- **不修改插件缓存中的 `agents/openai.yaml`。**缓存升级可能覆盖修改，也会破坏来源完整性。
- **不照搬 Claude 的 `disable-model-invocation`、`skillOverrides` 或 Cursor 的 `Manual` 字段。**这些是对应宿主的正式机制，不是 Agent Skills 开放规范的通用字段。
- **不把项目 Marketplace 当成自动作用域。**它解决发现和分发，未证明插件只在指定仓库加载。
- **不在当前实验主会话中试验大规模启停。**候选治理使用独立配置档和新会话验证，避免改变正在运行的实验调度行为。
- **暂不自建向量 Top-K Skill 路由器。**Semantic Kernel 证明该模式可扩展，但 Codex 未开放内置 Skills 检索器；自建会形成第二套不可观测路由。
- **暂不因缺少官方遥测而主观裁剪。**先保存 `/skills` 清单和小规模触发集，至少有一个可复现观察周期后再移除候选。

## 综合建议实施顺序

1. 由新的实现代理按 P0 至 P5 渐进拆分 `AGENTS.md`；每阶段只处理约定文件，先新增、诊断加载、再删父级重复项，并保存独立补丁。调研代理不直接实施。
2. P5 在默认 32 KiB 下通过后，再实现统一远程启动器、能力清单和正反例验证，覆盖 `fd`/`rg`/`uv`、字面量 `\n`、日志父目录、`tee` 和 `pipefail` 故障。
3. 启动器稳定后扩展项目 `PreToolUse`，分别增加子代理命名门禁和远程命令门禁；用 `/hooks` 审查信任并验证拒绝行为。
4. 创建项目实验调度 Skill，保存任务描述模板、职责别名和进度汇报格式；可选创建 `experiment_runner`、`experiment_reviewer`、`docs_researcher` 定制代理，但不以角色名替代任务实例名。
5. Skills 数量治理另开独立会话，只执行已授权的 Skills-P0 与 Skills-P1：保存 `/skills` 基线并隔离 20 对完全重复副本；不得阻塞服务器实验，也不得与 `AGENTS.md` 拆分混在同一差异中。
6. Skills-P1 结束后停止并汇报。17 对分叉项、无关插件、隐式调用、路由评测和季度淘汰等待用户新的明确授权。

## 已证实与未证实边界

已由官方文档证实：嵌套规则发现顺序、同层只取一个文件、默认 32 KiB、项目配置与信任边界、Skills 渐进加载及其 2% 或 8,000 字符初始预算、同名技能不合并、按路径禁用、关闭隐式调用但保留显式调用、项目定制代理、`PreToolUse` 对 `spawn_agent`/`Agent` 的覆盖、`tool_input` 检查和拒绝能力、`SubagentStart` 不能阻止启动。

官方文档未保证：所有未来版本都使用 `task_name`/`message` 字段；所有专用工具都经过 Hook；Hook 定义在当前会话热更新；定制代理能替代任务实例命名；关闭隐式调用会移出初始 Skill 索引；禁用 Skill 后仍能在同一会话显式调用；Codex 会对跨目录同内容 Skill 去重；项目 Marketplace 会按当前仓库自动启停插件。因此实施时必须基于当前工具模式做契约测试，并在每次 Codex 升级后保留一组最小 Hook 与 Skill 路由正反例冒烟。
