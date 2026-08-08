# Hook-P1 调查笔记

## 真实运行时反例

工作目录：`thesis/experiments/llm_probe/scripts`

安全命令只打印包含服务器标记和错误 `nounset` 顺序的文字，即使失败开放也不连接服务器、不修改文件：

```bash
printf '%s\n' 'ssh host set -u; source ~/.bashrc; /root/autodl-tmp'
```

观察结果：

- Codex 成功产生 `command_execution` 事件。
- 命令执行完成，退出码为 0，输出了测试文字。
- 未出现 Hook 拒绝或 Hook 失败事件。
- 代理最终明确判断“未被项目 PreToolUse 钩子拒绝”。

随后只移除 `--ignore-user-config`，相同反例在工具执行前被现有项目守卫拒绝；从 `llm_probe` 目录执行的 `printf '%s\n' hook-allow` 正常返回 0。真实运行时的基础允许与拒绝现已成立。

根因裁决：本机该选项不仅隔离了用户配置，还使本次项目 Hook 没有进入实际工具路径。后续项目 Hook 验收禁止使用 `--ignore-user-config`；仍使用 `--dangerously-bypass-hook-trust` 仅跳过临时会话的哈希信任交互。

## 待区分层级

1. 普通配置与 `--dangerously-bypass-hook-trust`：项目守卫被发现、匹配并执行。
2. `--ignore-user-config`：本机实际行为不适合项目 Hook 集成验收，按失败开放处理。
3. Shell 工具实际匹配现有 `Bash` 别名，结构化拒绝被 Codex 接受。

## 纪律

- 不因命令级直接测试通过而宣称框架集成通过。
- 不在定位真实失败层级前扩展策略规则。
- 不把外部连接错误误写为 Hook 逻辑错误；本次模型最终成功发出并完成工具调用，已排除“模型未触发工具”这一层。
