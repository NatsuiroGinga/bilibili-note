# Hook P1、生命周期与受管远端诊断恢复报告

## 状态

- 日期：2026-07-30。
- 生命周期结论：用户级配置和启动器已经修复，新启动的 Codex 与 Claude 进程均通过验收；**修复前已启动的当前 Codex 进程仍缓存旧命令，必须完全退出并重新启动后才会生效**。
- 远端短查询结论：`command -v`、引号内 `rg` 正则交替符和服务器 `/usr/bin/fdfind` 三项误拒绝已修复，真实管道、写命令、字面量反斜杠换行和未受管远程命令继续拒绝。
- 实验入口结论：`guarded_rsync` 已能保存限长、脱敏的底层诊断，并提供不传输文件的 `--prepare-only`。失败根因是本机环境加载与沙箱网络权限必须同时满足；同时加载 `~/.zshrc` 并在沙箱外运行的仅准备诊断已通过。
- 未执行模型下载、文件同步、实验阶段或正式运行；未提交或推送 Git。

## 生命周期恢复

### 根因

项目 `.codex/hooks.json` 原本只注册 `PreToolUse` 与 `PreCompact`，三类生命周期错误来自用户级配置。

1. `/Users/bilibili/.codex/hooks.json` 中的 `SessionStart`、`UserPromptSubmit` 和 `Stop` 命令把钩子目录与完整绝对路径再次 `path.join`，实际形成重复的不存在路径。三个命令均可独立复现 `MODULE_NOT_FOUND` 和退出码 `1`。
2. `/Users/bilibili/.claude/settings.json` 的三个命令依赖裸 `node`。普通终端环境可运行，但限制为 `/usr/bin:/bin:/usr/sbin:/sbin` 的 `PATH` 时退出 `127`。
3. 当前 `codex resume` 进程启动于 15:31，用户配置修改于 16:29。修改后当前会话仍报告旧的 `UserPromptSubmit hook (failed)`，而 16:55 新启动的临时 Codex 进程没有该错误。这证明生命周期配置在进程或会话启动时加载，修改文件不会热更新当前会话。

### 修改

- 新增仓库源文件 `.codex/hooks/run_node_hook.sh`。
- 新增 `.codex/hooks/tests/test_run_node_hook.py`，覆盖标准输入、标准错误和子进程退出码透传，未知脚本拒绝，Node 缺失失败，以及限制 `PATH` 时从 NVM 恢复。
- 安装相同内容的用户级副本：
  - `/Users/bilibili/.codex/hooks/run-node-hook.sh`
  - `/Users/bilibili/.claude/hooks/run-node-hook.sh`
- 仅更新以下两个配置中的三条命令字段：
  - `/Users/bilibili/.codex/hooks.json`
  - `/Users/bilibili/.claude/settings.json`
- 启动器只允许 `session-start.js`、`skill-forced-eval.js` 和 `stop-summary.js`，优先使用现有 `node`，否则加载 `$HOME/.nvm/nvm.sh`，仍缺失时明确退出 `127`。
- 启动器使用 `exec` 执行子脚本，不吞掉标准输入、标准输出、标准错误或真实退出码。
- 仓库源文件与两个安装副本的 SHA-256 均为 `825621b74d945baa5abb87d89a5057f25ba824da426020787c0a498fbd331e8b`。

### 验收

1. 限制 `PATH` 直接执行两个用户配置中的实际命令：Codex 与 Claude 的 `SessionStart`、`UserPromptSubmit`、`Stop` 共 6 组均退出 `0`，标准错误为空。
2. 真实 `claude -p --include-hook-events`：
   - 用户 `SessionStart`、`UserPromptSubmit`、`Stop` 均各执行一次并返回成功、退出码 `0`、标准错误为空。
   - Superpowers 与 MCPmarket 的 `SessionStart` 同时成功；二者未被禁用或修改。
   - 整体会话正常完成。
3. 新启动的只读临时 `codex exec --ephemeral --json`：
   - 未出现任何生命周期 Hook 失败。
   - 正常完成用户提示并返回“新会话钩子验收通过。”
   - 进程另有既存的模型缓存、代理角色和 MCP 网络告警，但均不是 Hook 退出错误。
4. 当前旧 Codex 进程仍需重启；在旧进程内继续发送提示不能作为修复后验收。

## 远端短查询恢复

### 根因

1. 通用命令规约把只读查询 `command -v` 当作普通包装器剥离，导致 `source ~/.bashrc; command -v uv` 被错误规约为不允许的裸 `uv`。
2. 审批在引号解析前按原始字符拒绝 `|`，无法区分真实管道与 `rg "tcp|udp"` 中的正则交替符。
3. 白名单使用交互式别名 `fd`，而仓库证据表明服务器非交互 Shell 的实际可执行文件为 `/usr/bin/fdfind`。

### 修改

- `.codex/hooks/project_policy_guard.py`：精确保留 `command -v`，按词法令牌识别真实控制符，并用 `fdfind` 替换 `fd`。
- `.codex/hooks/tests/test_project_policy_guard.py`：新增 6 项正反回归。
- `.codex/hooks/tests/test_hooks_integration.py`：允许夹具改用受管 Expect 入口，拒绝夹具继续验证 `.bashrc` 与 `nounset` 的顺序。

### 验收

- 修复前 25 项策略测试中 4 项按预期失败，分别对应三个误拒绝和错误放行 `fd`。
- 修复后策略测试 25/25 通过。
- 真实管道、只读查询后执行 `touch`、直接 `ssh`、字面量反斜杠换行、嵌套 Shell 和项目外伪包装器均继续拒绝。

## 受管远端准备诊断

### 原问题

三次 `guarded_remote_stage.py --apply` 均在 `guarded_rsync.apply_sync_plan` 的 `prepare` 子进程失败，但原实现只记录“远端目标父目录创建或验证失败”，丢失退出码、标准输出和标准错误。直接执行 `/tmp/gpu-exec.exp` 又被 Hook 正确禁止，因此无法区分本机环境、Expect、登录、远端 Shell 或路径故障。

### 修改

- `thesis/experiments/llm_probe/scripts/guarded_rsync.py`：
  - 新增 `ManagedCommandFailure`，保留固定步骤名、原始退出码及脱敏后的标准输出和标准错误。
  - 输出最长 2000 个字符，移除控制字符、凭据值、凭据赋值、远端地址和端口。
  - `prepare`、`transfer` 和 `verify` 的非零退出均使用同一结构化诊断。
  - 抽取 `prepare_remote_parent` 并新增互斥选项 `--prepare-only`，只创建与验证目标父目录，不运行 `rsync`。
- `thesis/experiments/llm_probe/scripts/guarded_remote_stage.py`：将内层 `ManagedCommandFailure.diagnostic` 写入外层失败收据。
- `.codex/hooks/tests/test_guarded_wrappers.py`：新增 3 项测试，覆盖凭据与主机端口脱敏、长度限制、不触发传输及外层收据传播。
- `thesis/experiments/llm_probe/scripts/AGENTS.md`：新增受管子进程诊断与 `--prepare-only` 的长期合同。
- `.Codex/docs/hooks/guarded-rsync-prepare-diagnostic-plan.md`：记录范围、步骤和停止条件。

### 根因证据

| 条件                      | 退出码 | 脱敏诊断                                | 结论                                   |
| ------------------------- | -----: | --------------------------------------- | -------------------------------------- |
| 未加载 `~/.zshrc`，沙箱内 |      1 | Expect 读取 `env(GPU_SSH)` 时变量不存在 | 本机凭据环境未传入子进程，连接尚未开始 |
| 已加载 `~/.zshrc`，沙箱内 |    255 | 连接操作被拒绝                          | 凭据已传入，剩余问题是沙箱网络限制     |
| 已加载 `~/.zshrc`，沙箱外 |      0 | `prepare_exit_code=0`                   | Expect、登录和远端父目录准备均正常     |

对应收据：

- `thesis/experiments/llm_probe/runs/hook-receipts/guarded-rsync-prepare-diagnostic-20260730.json`
- `thesis/experiments/llm_probe/runs/hook-receipts/guarded-rsync-prepare-diagnostic-20260730-sourced.json`
- `thesis/experiments/llm_probe/runs/hook-receipts/guarded-rsync-prepare-diagnostic-20260730-escalated.json`

此前三次完整阶段尝试分别改变了环境加载或沙箱权限，但没有同时满足两项前置条件。后续正式受管远端阶段必须先加载 `~/.zshrc`，并在批准的沙箱外环境执行；本报告不授权自动重试下载。

## 交付门禁

1. Python 格式化：隔离执行 `uvx black`；最终 `black --check` 确认 7 个修改文件无需再格式化。
2. Python 语法检查：使用 `PYTHONPYCACHEPREFIX=/private/tmp/hook-p1-pycache`，7 个修改文件均通过 `py_compile`。
3. Shell 语法：仓库启动器和两个用户级安装副本分别通过 `bash -n`；系统未安装 `shfmt`。
4. JSON 语法：`/Users/bilibili/.codex/hooks.json` 与 `/Users/bilibili/.claude/settings.json` 均通过 `jq empty`。
5. 受管包装器聚焦回归：19/19 通过。
6. 完整钩子回归：收集 69 项，68 项通过；唯一错误是并发修改后的项目 `.codex/hooks.json` 已按用户要求暂停 `PreToolUse`，旧集成测试强制读取该事件而触发 `KeyError`。本代理未恢复该配置，也未擅自放宽测试。
7. 在项目门禁被暂停前，本轮早期完整钩子回归为 66/66 通过。

## 变更边界

未修改现有三个生命周期 JavaScript 脚本、`/Users/bilibili/.codex/hooks/hooks.json`、MCPmarket、Superpowers、实验模型、参数、数据、运行制品内容和服务器任务。未暂存、提交或推送 Git。

当前仓库 `.gitignore` 的 `.Codex/` 规则在本机大小写不敏感文件系统上同时忽略 `.Codex/` 与 `.codex/`。因此钩子源码、测试和本报告必须按明确路径审查，不能只依赖普通 `git status --short`。

## 必要下一步

1. 完全退出当前 Codex 进程并重新启动；在新进程发送一个最小提示，确认不再出现 `UserPromptSubmit hook (failed)`。仅恢复同一旧进程或继续当前线程不足以加载新配置。
2. 如继续共享 B0 模型任务，使用“加载 `~/.zshrc` + 已批准沙箱外执行”的既有受管阶段入口；不得用裸 `ssh`、直接 Expect 或未诊断的重复下载代替。
3. 由新的审查代理检查本报告列出的明确路径；当前报告不替代独立审查。
