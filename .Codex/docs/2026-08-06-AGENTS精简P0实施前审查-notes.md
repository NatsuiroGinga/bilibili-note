# AGENTS 精简 P0 实施前审查笔记

## 当前工作树边界

- 审查开始时工作树已有 28 个已跟踪文件修改及大量未跟踪研究制品。
- 与本任务直接相关且已存在用户修改的文件包括 `AGENTS.md`、`thesis/AGENTS.md`、`thesis/experiments/llm_probe/AGENTS.md`、`thesis/experiments/llm_probe/scripts/AGENTS.md`。
- 本审查不覆盖、不撤销、不格式化这些既有改动。

## 待核验证据

- P0 调研中的删除/保留/迁移清单。
- 用户级与项目级钩子配置的实际加载字段。
- `security-guard` 与 `skill-forced-eval` 被引用脚本、路径解析和测试。
- 各层规则的精确字节数与路径组合。
- 关键规则的唯一或重复承载位置。

## 初始风险

- 仓库根与 `llm_probe` 对当前服务器变量的描述互相冲突。
- 未验证钩子前不能删除它拟替代的文字安全规则。
- 当前工作树不是干净基线，实施代理必须只改审查明确授权的片段并保留用户差异。

## 当前字节与发现链

- 10 份规则当前共 `49,302` 字节；官方调研中的 `48,254` 已因根规则增加 `305` 字节、RWKV 局部规则增加 `743` 字节而过期。
- 用户级 `12,302`；仓库根 `10,585`；`thesis` `4,608`；`llm_probe` `5,722`；`scripts` `1,041`；RWKV 局部 `4,495` 字节。
- 根链 `22,887`；`llm_probe` 链 `33,217`，超过 `32,768` 共 `449`；`scripts` 链 `34,258`，超过 `1,490`；RWKV 链 `29,309`，余量 `3,459`。
- 按现有目标 `2,600 + 4,200 + 4,608 + 3,000` 计算，P0 后 `llm_probe` 链约 `14,408`，不是调研报告写的 `13,808`；`scripts` 约 `15,449`，RWKV 约 `13,222`。
- 三个 P0 文件按目标字节计算减少 `18,809`，10 文件总量约 `30,493`。

## 钩子事实

- `~/.codex/hooks.json` 的安全守卫命令把 home 与绝对路径传给 `path.join`，实测解析为 `/Users/bilibili/Users/bilibili/.codex/hooks/security-guard.js`。
- `~/.codex/config.toml` 的 Hook 状态明确把该 `PreToolUse` 条目标为 `enabled = false`；因此当前安全守卫未生效。
- 安全脚本的危险 Bash 样例会退出 `2`，但普通 Bash 输出当前 `PreToolUse` 不支持的 `{"continue":true}`；`apply_patch` 样例也只放行，因为脚本只识别旧的 `Write`/`Edit` 工具名和 `file_path` 输入。
- 官方当前协议：`PreToolUse` 的文件编辑输入仍报告 `tool_name = apply_patch`，输入在 `tool_input.command`；`continue` 对该事件不受支持，会被标为 Hook 失败并继续工具调用。
- `skill-forced-eval.js` 读取旧字段 `user_prompt`。官方当前字段为 `prompt`；实测 `{prompt:"/commit"}` 仍注入消息，而 `{user_prompt:"/commit"}` 才静默。
- 该技能 Hook 当前为 `enabled = true`，每个普通提示均输出固定 `systemMessage`。官方当前协议把 `systemMessage` 作为界面/事件警告；真正的开发上下文应使用 `hookSpecificOutput.additionalContext`。P0 目标本来就是移除重复注入，因此推荐移除活动注册，不修成新的常驻注入。
- 项目 `hooks.json` 只注册 Prettier 拒绝和 PreCompact，描述明确“其他项目执行门禁继续暂停”。`project_policy_guard.py` 的 `main()` 直接返回 `0`；`server_launcher_guard.py` 未注册。不能把二者已有单元测试等同于运行时生效。
- `default.rules` 当前只有 `allow` 规则，没有 `prompt` 或 `forbidden`，不能承接 `rg/fd/sed`、危险同步或用户改动保护等文字规则。

## 项目 Hook 回归

- 全套 `72` 项回归为 `71` 通过、`1` 失败。
- Prettier、项目策略、服务器启动器、命令级集成和 Node 启动器的定向测试分别 `3/3`、`25/25`、`13/13`、`2/2`、`4/4` 通过。
- 唯一失败是 `test_missing_source_preserves_existing_documents_and_reports_failure`。根因是 2026-08-04 已把“活动计划缺失”正式改为写入“未设置”并成功，而旧测试仍期待报警并保持文档不变；这是测试与已记录行为漂移，不是随机失败。
- 更重要的是，活动 PreCompact 配置仍固定 R2 计划，脚本目标仍固定两份 PINN `output/` 文档。当前 RWKV 会话中，工作树差异证明它在 2026-08-06 刷新了两份 PINN 文档的快照时间。它不能作为 RWKV 路线恢复的等价承载；P0 不得据此删除路线规则。

## 等价承载结论

- 简体中文：没有可靠 Hook 等价物，必须保留在用户级规则。
- 通用沟通、规划、调试、测试驱动开发、审查与交付结构：已有对应技能和平台指令，可删除长示例，只留触发与最小验证原则。
- 仓库文档位置、证据晋级与子域路由：根规则及局部规则承载，用户级可删除论文专属细节。
- 路线恢复：RWKV 局部规则与总控承载细节，但根规则仍必须保留唯一选路、入口和写回边界；PreCompact 不能替代。
- 凭据与防泄漏：根规则和 `llm_probe` 均有承载，但变量名和当前服务器不能留在长期规则；保留不可落盘、不可回显和启动前读取当前路线事实源。
- GPU 通知：当前由 `llm_probe` 与 RWKV 总控共同承载；P0 必须在 `llm_probe` 保留跨路线的通知与费用确认短规则。
- SwanLab：当前由 `llm_probe` 承载。固定项目名可移入冻结配置或路线总控，但在线记录、云端核验和本地原始日志不能删除。
- 用户改动保护：安全 Hook 当前既禁用又不覆盖 `apply_patch`；必须在用户级保留“不覆盖、回滚、暂存或删除用户/并行任务改动”的短规则，并删除危险的自动 `git checkout -- <file>` 指令。
- 搜索工具与证据排除：`.ignore` 承接当前机械排除，根规则仍须保留不得排除证据和运行制品的短边界；`.rules` 目前不承接命令禁令。
