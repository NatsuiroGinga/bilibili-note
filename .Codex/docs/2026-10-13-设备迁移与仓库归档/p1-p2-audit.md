# 设备迁移与仓库归档 P1–P2 盘点

**盘点范围**：P1（盘点）＋ P2（归档清单）。**未执行**任何 `git add/commit/push/reset/checkout`、未创建远端、未删除或移动任何文件、未读取任何 `.env`／凭据／令牌／私钥文件的内容、未修改生产代码。

**快照时间**：2026-10-13 11:28 (+08:00)
**工作树**：`/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908`
**仓库远端**：`origin git@github.com:NatsuiroGinga/bilibili-note.git`（私有）

> **并发写入警告（必须首先阅读）**：盘点过程中活动工作树 `ch3-drift-20260908` 的 HEAD 由 `5a3a7eb3` 前移到 `0e63180d`（提交 `docs(drift): record confound discovery in source bdf comparison`），未跟踪文件集合同时增加（出现 `edit-v2-audit-console.log`）。**该工作树有并发写入者（主代理／其他代理会话）**。本报告 2026-10-13 11:28 的读数是一个移动快照，执行 P4 提交前必须重新采集 `git status`。本次盘点自身未做任何写入。

---

## 清单 1：工作树状态

| # | 工作树路径 | 分支 | HEAD | 上游／推送状态 | 未提交 | 未跟踪 | 目录体积（含 .git） | `.git` 记账 |
|---|---|---|---|---|---|---|---|---|
| 1 | `/Users/bilibili/personal/note`（根工作树） | `codex/ch3-cpa-elp-20260820` | `f6e0561e` | 上游 `origin/codex/ns3-pinn-m012-20260720`，**ahead 200** | 6 删除 ＋ 1 修改 | 6 | **51 G** | 主 `.git`＝**2.2 G**（对象库唯一） |
| 2 | `/Users/bilibili/personal/note/.claude/worktrees/gallant-kare-2cb8d3` | detached（＝`claude/gallant-kare-2cb8d3`）@ `42c80ffd` | `42c80ffd` | 无（detached）；对应分支已在 origin | 0 | 0 | 1.0 G | 共享主对象库 |
| 3 | `/Users/bilibili/personal/note/.claude/worktrees/objective-chaplygin-e2102b` | detached（＝`main`）@ `6f73b873` | `6f73b873` | 无（detached）；＝`origin/main` | 0 | 0 | 167 M | 共享主对象库 |
| 4 | `/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908` | **`exp/ch3-drift-20260908`** | `0e63180d`（盘点开始时为 `5a3a7eb3`） | 上游 `origin/exp/ch3-drift-20260908`，**ahead 5 → 盘点中又新增 1 提交** | 15 修改 | 42 | **29 G** | 共享主对象库 |
| 5 | `/Users/bilibili/personal/note/.worktrees/chatgpt-ch3-drift-20260907` | detached（＝`backup/chatgpt-ch3-drift-20260907`）@ `005b93c3` | `005b93c3` | 无（detached）；对应分支已在 origin | 0 | 1（`.pyc`） | 1.1 G | 共享主对象库 |

**体积口径说明**
- 5 个工作树共享同一个对象库，链接工作树的 `.git` 只是一个指针文件，各工作树管理目录合计仅 `1.9 M`（`/Users/bilibili/personal/note/.git/worktrees`）。
- 根工作树 51 G 的构成：`.worktrees/` 31 G ＋ `.claude/` 1.1 G ＋ `.git` 2.2 G ＋ 根级工作文件 ≈ 16.7 G（`thesis/` 12 G、`raw/` 3.2 G、`scripts/` 918 M、`zeek_orange_dmz.zip` 397 M、`.smart-env` 252 M、`ns3/` 79 M、`.cache/` 70 M、`.Codex/` 30 M、`wiki/` 13 M）。
- `ch3-drift-20260908` 29 G 的构成：`thesis/` 21 G ＋ `.cache/` 5.8 G ＋ `raw/` 1.1 G ＋ `scripts/` 1.0 G ＋ `.Codex/` 118 M ＋ `ns3/` 35 M ＋ `wiki/` 33 M。其中 `thesis/experiments/llm_probe/runs/` 单目录 21 G（全部被 Git 忽略）。

**未提交／未跟踪明细（关键项）**

- 根工作树：6 个 `.Codex/logs/session-2026090{8,9}-*.md` **在工作树中已删除但仍在 HEAD 跟踪**；`AGENTS.md` 已修改；4 个新会话日志＋2 个 chatgpt-handoff 文件未跟踪。
- `ch3-drift-20260908`：15 个修改集中在 `.Codex/docs/**`（DRIFT 路线总控、合同裁决、正式编辑预算筛选）与 `thesis/methods/第三章-*.md`、`AGENTS.md`、`.Codex/hooks.json`、`wiki/.../INDEX.md`；42 个未跟踪含 2 篇论文 PDF（4.0 M ＋ 968 K）、`raw/resources/2026-DSN-DRIFT/`（1.3 M）、新钩子 `mineru_extract_guard.py`／`sleep_guard.py` 及其测试、`ch3_drift_formal_edit_v2.py`、若干 chatgpt-handoff 交接件。
- 其余三个工作树基本干净（仅 chatgpt 工作树有 1 个 `.pyc`）。

**分支全景（只读采集）**
- 本地分支 16 个：`main`、`codex/ch3-cpa-elp-20260820`、`codex`/`exp` 系列 4 个、`claude/*` 3 个、`backup/*` 7 个（`backup/unreachable-*` 为历史不可达提交保护分支）。
- 远端分支 18 个，与本地基本一一对应；`origin/main` 与本地 `main` 同点 `6f73b873`。
- 两个 `.claude/worktrees` 与 `.worktrees/chatgpt-ch3-drift-20260907` 均为 **detached HEAD**，但其 HEAD 提交都已包含在对应本地分支内，**没有孤儿提交**，可按普通清洁工作树处理。

---

## 清单 2：可迁移文件归类

**口径**：可迁移＝**文档与源码**（规则文件、恢复卡、论文源码、原件清单、笔记）。运行制品、依赖环境、缓存不在本清单（见清单 4）。

**被 Git 跟踪的部分**（可随分支推送）：

| 工作树 | 跟踪文件数 | 跟踪内容总体积 | `raw/`（原件） | `thesis/`（论文与实验源码） | `wiki/`（笔记） | `.Codex/`（规则/恢复/过程文档） |
|---|---|---|---|---|---|---|
| 根工作树 | 4042 | ≈ 1508 MB | 358 个 / 780 MB | 1036 个 / 230 MB | 585 个 / 3.1 MB | 463 个 / 4.1 MB |
| `ch3-drift-20260908` | 3954 | ≈ 1548 MB | 513 个 / 1122 MB | 1425 个 / 241 MB | 1072 个 / 30 MB | 838 个 / 115 MB |
| `chatgpt-ch3-drift-20260907` | 4088 | ≈ 1166 MB | — | — | — | — |
| `gallant-kare-2cb8d3` | 3659 | ≈ 1085 MB | — | — | — | — |
| `objective-chaplygin-e2102b` | 151 | ≈ 167 MB | — | — | — | — |

> 跟踪体积主要由 `raw/papers/` 的 PDF 原件构成（根工作树 503 篇；DRIFT 工作树 513 篇）。**单文件均 < 100 MB**（最大跟踪文件 51.3 MB），不触发 GitHub 单文件上限，但**单次推送载荷约 1.1–1.5 GB**，需要评估推送耗时与远端配额。

**按类别**

1. **规则文件**（必须迁移，缺失将导致新设备无法恢复作业环境）
   `AGENTS.md`、`CLAUDE.md`、各子目录 `AGENTS.md`／`CLAUDE.md`、`.Codex/hooks.json`、`.Codex/hooks/**`、`.gitignore`、`.ignore`。均已跟踪。
   注：`.Codex/hooks.json` 在 DRIFT 工作树处于**已修改未提交**状态，`.Codex/hooks/mineru_extract_guard.py`、`sleep_guard.py` 及测试为**未跟踪新文件**——属于"必须迁移但尚未入库"的一类。
2. **恢复卡与路线总控**：`.Codex/docs/DRIFT/DRIFT路线总控.md`（已修改未提交）＋ `DRIFT第三章恢复卡.md`。已跟踪。
3. **论文源码**：`thesis/**/*.py`、`thesis/methods/*.md`、`thesis/figures/`（126 M，含图纸与脚本）、`thesis/chapters/`、各章 `pyproject.toml`／`uv.lock`。已跟踪；`thesis/experiments/llm_probe/{src,scripts,configs,tools,tests,vendor}` 已跟踪。
4. **原件与原件清单**：`raw/papers/**`（PDF 原件）、`raw/resources/**`、`raw/AGENTS.md`／`README.md`、各 `INDEX.md`。部分已跟踪，DRIFT 工作树新增 2 篇 PDF 与 `raw/resources/2026-DSN-DRIFT/` 未跟踪。
5. **笔记与知识库**：`wiki/**`、`02-Index.md`、`_system/`、`Research/`、`output/`、`.claude/docs/`、`.claude/project-memory/`、`.claude/sdd/`。已跟踪。
6. **项目级会话与过程记录**：`.Codex/docs/**`（DRIFT 工作树 838 个文件、115 MB；根工作树 463 个、4.1 MB）。这部分是 DRIFT 迁移的主要内容，也是**敏感复核的重点区域**（见清单 3）。
7. **论文工程依赖合同**：`uv.lock`、`pyproject.toml`、`requirements*`（若有）。已跟踪。

**未被 Git 跟踪、但属于"可迁移候选"的项**（需主代理逐项裁决）
- DRIFT 工作树 `.Codex/docs/2026-09-23-DRIFT源期训练抽样合同/` 下 5 个审计 JSON、`source_low_fpr_probe.py`、`无明文断点实施报告.md`。
- `.Codex/docs/chatgpt-handoffs/**` 交接件（outbound／sanitized／inbox／`*-paths.txt`／`handoff_paths.txt`）。**其中 `*-paths.txt` 记录本机绝对路径，属机器级信息，优先排除或改写成相对路径。**
- `.Codex/docs/2026-09-23-F风险保护与覆盖文献核查/`、`2026-09-23-O长度自适应K文献核查/`、`2026-09-24-MinerU令牌提取守卫/` 任务目录。
- `wiki/papers/attack-detection/dga/2019-Balaji-*.md`、`2022-Liu-*.md` 新增笔记。

---

## 清单 3：敏感排除项明细（**只列路径模式，不含任何值**）

### 3.0 高亮：疑似凭据已进入 Git 跟踪

**`Zotero.txt` 在三个工作树仍被 Git 跟踪，必须在 P4 推送前处置。**

| 项 | 事实 |
|---|---|
| 性质 | ASCII 文本，无换行符，4.0 K；DRIFT 分支 `.gitignore` 自带注释「凭据文件一律不入库（Zotero API key 曾被误提交，2026-09-11 移出跟踪；key 须轮换）」——即**仓库自身已记录这是一次凭据误提交** |
| 仍被跟踪 | 根工作树 `codex/ch3-cpa-elp-20260820`（引入提交 `943ae620`）、`chatgpt-ch3-drift-20260907`、`gallant-kare-2cb8d3` |
| 已修正 | `exp/ch3-drift-20260908` 分支已不跟踪，且 `.gitignore` 已加 `Zotero.txt` / `**/Zotero.txt` |
| 根工作树缺口 | 根工作树 `.gitignore` **没有** Zotero 规则，或使 `git add -A` 再次纳入 |
| 本报告立场 | **只登记、不定性、不清理**。凭据仍存在于对象历史中，单纯删除文件不能撤销历史泄露——是否轮换 key、是否清理历史属主代理的破坏性操作决策。本代理未读取该文件内容。 |

### 3.1 认证与凭据（**一律排除，不得入库，不得出网**）

| 路径模式 | 位置 | 说明 |
|---|---|---|
| `~/.codex/auth.json` | 全局 | 认证令牌文件（8 K） |
| `~/.codex/.codex-global-state.json`、`~/.codex/.codex-global-state.json.bak`、`~/.codex/..codex-global-state.json.tmp-*` | 全局 | 全局状态（1.3 M×2＋临时件），可能含令牌与会话凭据 |
| `~/.codex/config.toml`、`config.toml.bak*` | 全局 | **含明文凭据段**。键名（值已在盘点中屏蔽，未读取）：`[shell_environment_policy.set]` 与 `[mcp_servers.*.env]` 下出现 `ANTHROPIC_AUTH_TOKEN`、`GITHUB_PERSONAL_ACCESS_TOKEN`、`GITLAB_TOKEN`、`ZOTERO_API_KEY`、`bearer_token_env_var`。迁移前必须脱敏或整段排除 |
| `~/.codex/models_cache.json`、`installation_id`、`chrome-native-hosts-v2.json`、`external_agent_session_imports.json` | 全局 | 机器身份／浏览器宿主注册，属机器级配置 |
| `~/.codex/mcp-oauth-locks/`、`~/.codex/.codex-scholar-*` | 全局 | 认证锁与安装状态 |
| `~/.codex/*.sqlite*`（`state_5`、`thread_history_1`、`logs_2`、`queue_1`、`memories_1`、`goals_1`） | 全局 | 会话／日志／状态数据库（合计约 0.5 G），按"内容可能含粘贴凭据"处理 |
| `~/.codex/history.jsonl`、`session_index.jsonl`、`transcription-history.jsonl` | 全局 | 历史与索引；`session_index.jsonl` 的 `thread_name` 已实测含服务器连接串（见 3.3） |
| `~/.codex/shell_snapshots/` | 全局 | shell 环境快照，可能导出环境变量名／值 |
| `~/.codex/sessions/**` | 全局 | 原始会话转录（2.5 G／1623 文件），**不得整目录迁移** |
| `~/.codex/computer-use/`、`~/.codex/browser/`、`~/.codex/attachments/` | 全局 | 本地交互与附件缓存 |
| 项目内 `Zotero.txt`（任意工作树） | 仓库 | 见 3.0 |
| 项目内 `.claude/settings.local.json` | 仓库 | 机器级本地设置（未跟踪，状态正确，保持不跟踪） |
| 项目内 `.claude/settings.json` | 仓库 | **已跟踪**；本次只读取顶层键名，为 `claudeMdExcludes`/`hooks`/`permissions`，**未见 env/凭据段**，判定低风险但列入「待主代理裁决」 |
| `.env`、`.env.*`、`*.pem`、`*.key`、`*.p12`、`*.pfx`、`id_rsa*`、`id_ed25519*`、`.netrc`、`.npmrc`、`.pypirc`、`.git-credentials`、`known_hosts` | 通用 | 本次在仓库跟踪集合中**未发现**（除上述 `Zotero.txt`）；在新设备侧与 `~/.codex` 迁移中继续按模式排除 |

### 3.2 机器级连接配置（不得写入仓库）

| 路径模式 | 说明 |
|---|---|
| `~/.codex/config.toml` 的 `[projects."/Users/bilibili/..."]` 段 | 记录本机全部项目绝对路径与信任等级（约 60 个路径） |
| 项目内 `*-paths.txt`、`handoff_paths.txt`、`followup-safe-paths.txt`、`*.chatgpt-handoff.json`（含 `handoff_root`） | 记录本机绝对路径 |
| SSH 主机密钥、`~/.ssh/config`、容器／云主机地址与端口 | 本次未读取；`~/.codex/session_index.jsonl` 的线程标题中**已出现**云服务器连接串（`ssh -p <端口> root@<主机>` 形式）——**该索引文件本身即含机器级连接信息，须排除或脱敏** |

### 3.3 会话内容类敏感（可能含凭据与内部信息）

| 路径模式 | 事实 |
|---|---|
| 仓库内 `.Codex/logs/session-*.md` | 根工作树 **9 个已被 Git 跟踪**（6 个在工作树中已删除但仍在 HEAD），另有 4 个未跟踪新文件。DRIFT 工作树无此目录 |
| 仓库内 `**/.claude/logs/session-*.md` | **4 个已被 Git 跟踪**：`thesis/chapters/.claude/logs/`、`thesis/experiments/llm_probe/.claude/logs/`、`thesis/experiments/llm_probe/tools/.claude/logs/`（2 个）。DRIFT 分支 `.gitignore` 已改用 `**/` 前缀修正，但**已入库的 4 个不因规则变更自动移除** |
| `~/.codex/logs/session-*.md` | 全局会话日志 2 个 |
| `~/.codex/sessions/**` | 实测线程标题含内部工作信息（B 站 CDN/MCDN 业务、MR 编号、内部域名 `git.bilibili.co` 等）与服务器连接串 → **跨项目会话不得整体迁移** |

### 3.4 待主代理裁决（本代理按「不确定即排除」处理）

1. `Zotero.txt`（三个工作树仍跟踪）——是否轮换 key、是否清理历史、是否只是停止跟踪。
2. `.claude/settings.json`（已跟踪，含 hooks／permissions 配置；未见凭据，但属机器级配置）。
3. `.Codex/logs/session-*.md`（根工作树 9 个已跟踪）与 `**/.claude/logs/`（4 个已跟踪）——会话记录是否属可公开再分发的项目文档，**未读取内容，无法判定是否含敏感信息**。
4. 各 `*-paths.txt`／`handoff_paths.txt` 交接白名单——是否含本机绝对路径以外的敏感信息。
5. `xaa`（根工作树顶层，已跟踪，ASCII 文本 CRLF 4 K）——疑似文件切分残片，**未读取内容**。
6. `~/.codex/.codex-scholar-manifest.txt`、`.codex-scholar-install-state`、`backups/`、`skill-archives/`——是否属于"可迁移配置"还是"机器级安装状态"。

---

## 清单 4：大文件清单（> 100 MB）

**结论：全部 > 100 MB 文件均已被 Git 忽略，不进入 GitHub。** 跟踪集合中最大文件为 51.3 MB（`thesis/experiments/genis/runs/q0/.../features.npy`），低于 GitHub 单文件 100 MB 硬上限。

| 大小 | 路径 | Git 忽略 |
|---|---|---|
| 5.1 G | `.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache/X23.npy` | 忽略 |
| 2.1 G | `.worktrees/ch3-drift-20260908/.cache/literature-search/model-cache/models--BAAI--bge-m3/blobs/*` | 忽略 |
| 1.0 G | `.worktrees/ch3-drift-20260908/.cache/literature-search/model-cache/models--intfloat--multilingual-e5-base/blobs/*` | 忽略 |
| 881 M | `.worktrees/ch3-drift-20260908/.cache/literature-search/index.sqlite3` | 忽略 |
| 815 M | `.worktrees/ch3-drift-20260908/thesis/.../runs/diagnostics/ch3-ft-c10-entity-memory-cuda-formal-v1/checkpoints/inflight.pt` | 忽略 |
| 535 M | `thesis/experiments/llm_probe/artifacts/rwkv-baseline-deps/.../attempt3.tar.gz`（根工作树） | 忽略（`artifacts/`） |
| 516 M ×5 | `.worktrees/ch3-drift-20260908/thesis/.../runs/baselines/shared-b0-distilbert-seed42-.../model.safetensors` 等 | 忽略 |
| 472 M ×2 | `thesis/.../runs/diagnostics/dijk-repro/cache/{d24,s24}.npy`（根工作树） | 忽略 |
| 449 M | `.worktrees/.../.cache/literature-search/model-cache/models--intfloat--multilingual-e5-small/blobs/*` | 忽略 |
| 397 M | `zeek_orange_dmz.zip`（根工作树顶层） | 忽略（`zeek_orange_dmz.zip` 规则） |
| 337–344 M | `.git/objects/pack/*.pack`（≥5 个） | 属 Git 对象库，非工作树文件 |
| 362–363 M | `raw/datasets/TQH-C2*/...zip`、`raw/datasets/GeNIS-2025/2-flows.zip`（根工作树） | 忽略（`raw/datasets/`） |
| 323 M / 337 M | `scripts/literature_search/.venv/.../libtorch_cpu.dylib` | 忽略（`**/.venv/`） |
| 301–333 M ×8 | `.worktrees/ch3-drift-20260908/thesis/.../runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521/DRIFT_input_eSLD/T{17..25}_*.parquet` | 忽略（`runs/` 全目录） |
| 176–321 M ×9 | 同上 `raw_including_TLD/T{17..25}_dga.parquet` | 忽略 |
| 265 M ×2 | `.../runs/diagnostics/dijk-repro/cache/I23.npy`、`.../runs/server-backups/seeta-16851-20260907/dijk-repro/cache/I23.npy` | 忽略 |
| 277–278 M ×5 | `.../runs/diagnostics/ch3-drift-source-common-{a,b,d,f,g}-.../arm-*-checkpoint.pt` | 忽略 |
| 267 M | `.../runs/data-raw/drift-dga-.../DRIFT_input_eSLD/T19_benign_test.parquet` | 忽略 |
| 300 M ×3 | `.../runs/candidates/crossyear-rare-mass-protected-asymmetric-pot-q0-seed42-v1-rerun2/representations/{source-train,source-validation,target-development,target-prefix}/leaf.npy` | 忽略 |
| 96–208 M ×若干 | 根工作树 `thesis/experiments/llm_probe/runs/**` 的 parquet／pt／npy／wheel／tar.xz | 忽略 |
| 126–154 M ×3 | 根工作树 `runs/data-frozen/.../packet_observations.parquet`、`artifacts/rwkv-baseline-deps/.../*.whl` | 忽略 |

**获取方式登记（不迁移二进制）**
- `.cache/literature-search/model-cache/**`：由 `intfloat/multilingual-e5-small|base`、`BAAI/bge-m3` 公开模型缓存生成，可从公开 Hugging Face 重下（须登记 revision）。
- `raw/datasets/TQH-C2*`、`GeNIS-2025`：原始数据集，按 `raw/AGENTS.md` 登记下载来源、固定修订与 SHA-256／ETag。
- `runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521/**`：DRIFT 原始数据固定修订快照（修订号已含在目录名 `rev-3b31077020cd1c013d0a75cad51042a2327c4521`），按该修订重取。
- `runs/**` 的 checkpoint／npy／parquet：**需单独裁决**是否属"已存在且具备再分发条件的处理后数据"（P5 候选），或仅登记哈希与生成脚本。本盘点**不认定**其为可上传数据集。

---

## 附：`~/.codex/` 只读盘点

**总量 6.3 G**。仅读取目录结构与文件元数据（`ls`/`du`/文件计数），**未读取任何会话文件内容**；`config.toml` 只按行提取键名并将值屏蔽；`auth.json` 完全未读取。

### 目录结构与体积

| 子目录／文件 | 大小 | 文件数 | 归类 |
|---|---|---|---|
| `sessions/` | 2.5 G | 1623 | 跨项目原始会话转录（`YYYY/MM/DD/rollout-*.jsonl`） |
| `packages/` | 2.0 G | 185 | 运行时依赖包（可再生） |
| `plugins/` | 759 M | 7588 | 插件安装（可再生） |
| `.tmp/` | 229 M | — | 临时物 |
| `thread_history_1.sqlite` | 224 M | 1 | 会话历史库 |
| `releases/` | 157 M | 20 | 版本产物（可再生） |
| `logs_2.sqlite` ＋ `-wal` | 179 M | 2 | 日志库 |
| `state_5.sqlite` | 96 M | 1 | 状态库 |
| `computer-use/` | 70 M | 169 | 本地自动化产物 |
| `logs_2.sqlite-wal`／`queue_1.sqlite*`／`goals_1.sqlite` | — | — | 运行时数据库 |
| `cache/` | 38 M | 7 | 缓存 |
| `tools/` | 33 M | 1342 | 工具脚本 |
| `vendor_imports/` | 7.6 M | 800 | 第三方导入 |
| `skills/` | 6.6 M | 763 | **技能（可迁移候选）** |
| `sqlite/` | 6 M | 3 | 辅助库 |
| `.codex-global-state.json`（＋`.bak`） | 2.6 M | 2 | 全局状态（排除） |
| `skill-archives/` | 1.5 M | 303 | 技能归档 |
| `shell_snapshots/` | 1.6 M | 2 | shell 快照（排除） |
| `.codex-global-state`、`generated_images/`、`attachments/` | 0.3–1.3 M | — | 缓存类 |
| `memories/` | 740 K | 96 | **记忆（可迁移候选）** |
| `memories_1.sqlite` | 320 K | 1 | 记忆库 |
| `models_cache.json` | 200 K | 1 | 模型缓存 |
| `backups/` | 172 K | 11 | 配置备份 |
| `agents/` | 92 K | 16 | **子代理定义（可迁移候选）**；含 4 个 `.disabled.20260923` 备份 |
| `hooks/` | 100 K | 16 | **钩子脚本与规则 bundle（可迁移候选）** |
| `templates/`（72 K）、`scripts/`（96 K）、`utils/`、`docs/`（2 文件）、`logs/`（2 文件）、`rules/`（`default.rules`）、`automations/`、`ambient-suggestions/`、`browser/`、`app-server-*`、`process_manager/`、`pets/`、`ipc/`、`visualizations/` 等 | < 72 K 各 | 少量 | 混杂 |
| `config.toml` ＋ 6 个 `.bak` | 44 K 各 | 7 | **机器级配置，含明文凭据段** |
| `auth.json` | 8 K | 1 | **认证令牌——排除** |
| `history.jsonl`、`session_index.jsonl` | 816 K／16 K | 2 | 历史与索引（排除） |

### 按项目关联性粗略分组（依据 `session_index.jsonl` 的 85 条线程标题 + `config.toml` 的 `[projects.*]` 路径）

| 组 | 判定依据 | 时间分布（粗） | 迁移建议 |
|---|---|---|---|
| **A. 本论文项目**（note／DRIFT／第三章／PINN／Zotero／论文写作／PDF 转换） | 标题含 `note`、`thesis`、`Drift`／`Drift主线`、`$zotero`、`$pdf-converter`、`物理信息神经网络`、`消融实验与C域偏移`、`更新用户级 AGENTS 模型建议`、`每周回顾`／`Guardian review` 等 | 07-15 ~ 07-31、08-08、09-13、09-14、10-12；约 20–25 条 | **可迁移（须逐条脱敏）** |
| **B. B 站工程（工作）**（MCDN／NCDN／监控带宽／质量探测／MR216／manba／自动化上下线／内部域名） | 标题含 `NCDN`、`MCDN`、`监控大盘`、`MR 216`、`ops.cdnops`、`git.bilibili.co` 等 | 07-28 ~ 09-23；约 30+ 条 | **排除**（与论文无关且含内部信息） |
| **C. 个人与第三方插件试用**（画图、`File expenses`、Slack／Notion／Chrome 插件、`nihao`） | 标题直读 | 07-15 ~ 08-20 | **排除** |
| **D. 服务器／远端会话**（SSH 连接云服务器、`connect.westc.<...>`） | 标题含 `ssh -p <端口> root@<主机>` | 08-31 附近 | **排除**（机器级连接信息） |
| **E. `.codex` 自身配置与迁移话题**（Codex→Claude Code 迁移、读取 Claude Code 会话、优化检索 MCP、技能禁用配置） | 标题直读 | 08-05、08-17 ~ 09-22 | **可迁移（脱敏后）** |

**注意**：`session_index.jsonl` 只覆盖 85 条线程，而 `sessions/` 有 1623 个 rollout 文件——索引**不是全集**。按项目精确归属需要读取会话元数据（首行 cwd），而会话文件可能含敏感内容，**本盘点按安全边界未执行**；建议在 P3 用一个只读、只提取元数据字段（不输出正文）的最小脚本完成归属，而非由代理直接读会话。

---

## 不确定项与阻塞

| # | 项 | 影响 | 建议动作 |
|---|---|---|---|
| B1 | **`Zotero.txt` 仍被 3 个工作树跟踪**（疑似已泄露的 API key） | 阻断 P4 推送 | 主代理裁决：是否轮换 key、是否清历史、是否仅停止跟踪。**本代理不执行清理** |
| B2 | `~/.codex/config.toml` 含 `ANTHROPIC_AUTH_TOKEN`／`GITHUB_PERSONAL_ACCESS_TOKEN`／`GITLAB_TOKEN`／`ZOTERO_API_KEY` 明文键 | 阻断 `~/.codex` 整目录迁移 | 迁移前脱敏（删除 `[shell_environment_policy.set]` 与 `[mcp_servers.*.env]` 值）或仅迁移白名单子目录 |
| B3 | 4 个 `**/.claude/logs/session-*.md` 与根工作树 9 个 `.Codex/logs/session-*.md` 已入库 | 可能含敏感内容 | 未读内容，无法判定；交主代理裁决（可先剥离文本检索敏感模式） |
| B4 | `.claude/settings.json` 已跟踪 | 机器级配置 | 复核 hooks／permissions 中是否含本机路径与凭据引用 |
| B5 | `xaa`（已跟踪，ASCII CRLF） | 未知内容 | 主代理确认是否切分残片 |
| B6 | `raw/papers/` 503–513 篇 PDF 已跟踪，单次推送载荷 1.1–1.5 G | 推送耗时／远端配额 | 评估是否需要 LFS 或分流 |
| B7 | 活动工作树有**并发写入者**，HEAD 在盘点期间前移 | 快照会过期 | P4 前重新采集 `git status`；建议与并发会话协调写入窗口 |
| B8 | `runs/` 中 21 G 制品是否含"可公开再分发的处理后数据" | 影响 P5 | 需按 `raw/AGENTS.md` 逐项判定许可与派生过程，本盘点不认定 |

---

## P3–P6 执行建议与风险（**未执行，仅建议**）

**P3（独立私有设备迁移仓库）**
- 建议不要整体搬 `~/.codex`。按白名单迁移：`skills/`、`memories/`、`agents/`、`hooks/`、`rules/`、`templates/`、`AGENTS*.md`、`config.toml`（**脱敏后**）。
- 明确排除：`auth.json`、`.codex-global-state.json*`、`*.sqlite*`、`shell_snapshots/`、`sessions/`（或仅迁 A/E 组且逐条脱敏）、`packages/`、`plugins/`、`releases/`、`.tmp/`、`cache/`、`computer-use/`、`browser/`。
- **风险**：脱敏不彻底＝凭据进私有仓库（私有不构成豁免）；`config.toml` 键值分散在多个 `.bak`，容易漏删。
- **建议门禁**：迁移前对候选文件跑一次机械扫描（模式：`token|api[_-]?key|secret|password|BEGIN .*PRIVATE KEY`），命中即阻断并人工确认，避免依赖"记得检查"。

**P4（逐工作树提交并推送）**
- **前置**：先解决 B1。根工作树 `.gitignore` 缺 Zotero 规则，建议在所有分支统一补齐后再提交。
- 建议按工作树独立分支推送，**不混合**不相关改动；`ch3-drift-20260908` 的 15 个修改＋42 个未跟踪需按主题分组为多个原子提交。
- **风险**：活动工作树有并发写入者（B7），提交窗口可能与其它会话冲突；建议先与并发会话冻结写入。
- **风险**：单次推送 1.1–1.5 G 载荷（B6），可能超时或触发远端限制；建议先评估、必要时改 LFS。

**P5（处理后数据上传 Hugging Face）**
- 先确权：`runs/**` 制品是否具备再分发条件、许可为何、派生过程是否可复现。
- **风险**：把"本机跑出来的制品"直接等同"可上传数据集"，可能违反数据许可或泄露原始流量样本；原始数据只登记下载来源、版本与校验方式。

**P6（回读与交付说明）**
- 回读各远端分支提交号与 SHA，登记到 `迁移交付说明.md`。
- 明确列出**未迁移项**（21 G 制品、`~/.codex` 排除项、B1/B3 待裁决项）与获取方式。
- **风险**：若 P4 未处理 B1，历史中的凭据会在新设备克隆时一并带回。

---

**本报告为只读盘点产物，未改变任何 Git 状态、未删除或移动任何文件、未读取任何凭据文件内容。落盘后请由主代理验收；P3–P6 未执行。**
