# Hook-P0 实施报告

日期：2026-07-30

## 结论

Hook-P0 的代码与三目录命令级集成验证已经完成。现有服务器启动守卫不再向 `PreToolUse` 返回不受支持的字段，钩子命令也不再依赖会话当前目录。压缩前快照同时修复了系统 Python 3.9 下的单点兼容性问题。

真实 Codex 子进程已经从最深的 `scripts` 目录加载项目钩子配置，但外部连接异常使模型没有发出工具调用。因此，报告不把“Codex 确实在工具执行前拒绝”标为已验证；该部分仍需在网络正常的新会话中通过 `/hooks` 信任新哈希后复核。

## 输入与依据

- 审计报告：`.Codex/docs/agents-rules-hook-audit.md`
- 项目规则：`AGENTS.md`、`.Codex/docs/AGENTS.md`
- 当前版本：`codex-cli 0.144.5`
- 官方契约：<https://learn.chatgpt.com/docs/hooks>
- 本地技能：`hook-development`、`codex-hook-emulation`

官方版本行为明确规定：`PreToolUse` 返回 `continue`、`stopReason` 或 `suppressOutput` 会被判为钩子失败并继续工具调用；仓库钩子应从 Git 根定位脚本。旧技能示例与当前版本冲突时，本轮以官方版本行为为准。

## 根因

1. `server_launcher_guard.py` 的中性与拒绝分支都返回了 `continue` 和 `suppressOutput`。这些字段不受当前 `PreToolUse` 支持，原拒绝分支可能失败开放。
2. `.codex/hooks.json` 使用 `python3 .codex/hooks/...`。命令以会话 `cwd` 运行，从 `llm_probe` 或 `scripts` 启动时脚本路径不存在。
3. 三目录验证额外发现系统 `python3` 为 3.9.6，而 `precompact_snapshot.py` 使用 `zip(..., strict=True)`。该语法参数需要 Python 3.10，原快照会捕获异常并保留旧文档。

## 变更内容

### `.codex/hooks.json`

- 两条命令统一改为 `python3 "$(git rev-parse --show-toplevel)/.codex/hooks/<脚本>"`。
- 未修改事件、匹配器、超时、状态提示或守卫范围。

### `.codex/hooks/server_launcher_guard.py`

- 中性分支改为返回 `None`，命令入口以退出码零且无标准输出表示放行。
- 拒绝分支只返回 `hookSpecificOutput`，其中包含 `hookEventName`、`permissionDecision=deny` 和 `permissionDecisionReason`。
- 命令入口仅在存在拒绝对象时输出 JSON。
- 保留原有解析失败时失败开放的边界；未扩展检测规则。

### `.codex/hooks/precompact_snapshot.py`

- 删除一处 `zip(..., strict=True)` 的 `strict` 参数，使脚本兼容实际使用的 Python 3.9。
- 两个被压缩序列都来自固定的两份恢复文档，长度不一致不存在外部输入路径，因此该修改不改变快照语义。

### 测试与记录

- 更新 `.codex/hooks/tests/test_server_launcher_guard.py`，锁定中性无输出和拒绝对象字段集合。
- 新增 `.codex/hooks/tests/test_hooks_integration.py`，从三个工作目录运行配置命令，覆盖放行、拒绝和隔离快照。
- 新增 `.Codex/docs/hooks/task_plan.md`、`.Codex/docs/hooks/notes.md` 和本报告。

## 验证结果

### 修复前反例

命令：

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .codex/hooks/tests -p 'test_*.py'
```

结果：共 `21` 项，`12` 项失败、`3` 项错误。失败覆盖不受支持的输出字段和两个子目录的相对路径；错误覆盖 Python 3.9 的 `zip(..., strict=True)` 不兼容。

### 修复后完整测试

相同命令结果：

```text
Ran 21 tests in 0.701s
OK
```

### 三目录集成

命令：

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -v -s .codex/hooks/tests -p 'test_hooks_integration.py'
```

结果：`2/2` 通过。每项内部均遍历以下三个工作目录：

- `/Users/bilibili/personal/note`
- `/Users/bilibili/personal/note/thesis/experiments/llm_probe`
- `/Users/bilibili/personal/note/thesis/experiments/llm_probe/scripts`

覆盖结果：

- 正确的远程初始化顺序：退出码零，标准输出为空。
- 错误的 `nounset` 顺序：退出码零，输出唯一受支持的 `PreToolUse` 拒绝对象。
- `PreCompact`：在临时隔离项目中更新两份恢复文档，三个目录均保持单一快照区块，真实恢复文档未被修改。

### 格式化与静态检查

- `uvx black <四个本轮 Python 文件>`：完成格式化。
- `uvx black --check <四个本轮 Python 文件>`：四个文件均无需修改。
- `prettier --write .codex/hooks.json`：完成格式化。
- `prettier --check .codex/hooks.json`：通过。
- `PYTHONPYCACHEPREFIX=/tmp/hook-p0-pycache python3 -m py_compile <五个 Hook Python 文件>`：通过。
- `git diff --check -- .codex/hooks.json .codex/hooks .Codex/docs/hooks`：退出码零；但这些路径被忽略，该命令不能替代上述格式化和编译验证。

### 真实 Codex 子进程

从 `scripts` 目录使用 `--dangerously-bypass-hook-trust`、只读沙箱和临时会话启动一次安全反例。CLI 成功加载项目配置并进入模型回合，但 WebSocket 重连和多个 MCP 连接异常后，模型只输出执行意图，没有发出 Shell 工具调用。未执行目标命令，也未观察到 `PreToolUse` 拒绝事件。

裁决：**真实 Codex 运行时拒绝未验证，三目录最接近真实的命令级集成已验证。**

## 失败边界与剩余风险

1. 守卫无法解析输入或事件不匹配时，退出码为零且无输出，属于明确失败开放；这是保留原有边界，避免非目标工具被误阻断。
2. 明确识别错误顺序时返回结构化 `deny`，属于该规则范围内的失败关闭。
3. Git 根解析失败时钩子命令会非零退出；按 Codex 行为，工具调用可能继续。项目钩子正常只在仓库内加载，三个指定目录均已验证 Git 根一致。
4. `PreCompact` 失败时仍保留两份恢复文档原文，并通过 `systemMessage` 报警后继续压缩。
5. 钩子定义哈希已改变。普通新会话必须通过 `/hooks` 审查并信任新哈希，否则 Codex 会跳过非托管钩子。
6. 当前大小写不敏感文件系统把 `.gitignore` 的 `.Codex/` 同时应用到 `.codex/`，所有本轮钩子文件和报告均不出现在普通 `git status` 中。若要用 Git 持久化，需要另立任务调整忽略规则；本轮未越界修改。
7. Hook 只检查当前已有的 `source ~/.bashrc` 与 `nounset` 顺序，不代表完整远程执行合同已机械化。

## 未修改内容

- 所有 `AGENTS.md`
- 论文正文、实验源码、配置、数据和运行制品
- GPU 服务器及其任务状态
- Git 配置、历史、暂存区和远程仓库

## 后续最小动作

1. 在网络正常的新 Codex 会话中，从仓库根打开 `/hooks`，审查并信任新的项目钩子哈希。
2. 从 `scripts` 目录重新运行安全打印反例，确认工具调用在执行前被拒绝；随后把真实事件证据追加到本报告。
3. 如需提交这些文件，单独处理 `.Codex/` 与 `.codex/` 在大小写不敏感文件系统上的忽略冲突，不在本轮顺带修改。
