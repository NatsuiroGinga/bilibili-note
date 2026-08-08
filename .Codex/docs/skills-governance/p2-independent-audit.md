# P2 Codex 技能裁剪独立验收报告

## 结论

**通过。** P2 技能裁剪已在 Codex 0.144.5 的新独立进程中生效，活动技能数量、关键能力保留、插件停用、配置解析和回滚备份均满足治理合同。当前没有阻止 P2 投入后续新会话的缺陷。

## 验收范围

- 只读核验 `/Users/bilibili/.codex/config.toml`，未输出配置正文或凭据。
- 运行时证据使用 `/tmp/codex-skills-p2/prompt-input.json`。
- 合并摘要使用 `/tmp/codex-skills-p2/merge-summary.json`。
- 回滚证据使用 `/Users/bilibili/.codex/backups/skills-governance-p2-20260731-142459/`。
- 未修改用户配置，未联网，未操作服务器，未运行格式化或测试驱动开发流程。

## 验收结果

### 1. 配置解析

- `codex --strict-config doctor --json` 成功读取用户配置。
- `config.toml parse` 为 `ok`。
- 技能启动警告为 `0`，插件启动警告为 `0`。
- `config.load` 的警告来自四个既有重复代理角色定义，不是 TOML 解析错误，也不是技能或插件裁剪错误。

严格自检的总体状态仍为失败，但失败项是网络可达性和状态路径；另有可选 MCP、网络套接字与更新检查警告。这些状态与 P2 技能裁剪分开裁决，不影响本次配置解析通过的结论。

### 2. 新进程活动技能

| 指标 | 结果 |
| --- | ---: |
| 活动技能 | 45 |
| 技能区字符数 | 18,033 |
| 唯一技能名 | 45 |
| 同名重复组 | 0 |

活动技能数位于计划规定的 `45–65` 范围下界，且已消除活动索引中的同名重复来源。

### 3. 关键能力保留

下列能力均至少保留一个活动技能来源：

- 规划与研究：`planning-with-files`、`research-ideation`。
- 结果处理：`results-analysis`、`results-report`。
- 论文写作：`ml-paper-writing`、`writing-anti-ai`、`citation-verification`。
- PDF：`pdf-converter`、`pdf:pdf`。
- Zotero 与 Obsidian：`zotero-obsidian-bridge`、`obsidian-project-kb-core`，并保留 Obsidian 文献、来源摄取和制品技能。
- 实验跟踪：`swanlab-skill`。
- 调试：`superpowers:systematic-debugging`、`bug-detective`。
- Git：`git-workflow`、`git-commit`、`git-push`。
- 架构：`architecture-design`。
- 子代理开发：`superpowers:subagent-driven-development`、`superpowers:writing-plans`。

### 4. 插件停用

以下五个插件在当前用户配置中均为 `enabled = false`：

- `sites@openai-bundled`
- `gopls-lsp@claude-plugins-official`
- `google-calendar@openai-curated`
- `slack@openai-curated`
- `chrome-devtools-mcp@claude-plugins-official`

### 5. 合并与备份完整性

- 当前用户配置 SHA-256 为 `48bb5dc077939647fc7934a04c4bab5442b6607a2b3dd18d1d6a11f0a0707cab`，与合并摘要中的 `merged_sha256` 一致。
- 变更前备份 SHA-256 为 `e6db1ff50fa5a3d12d3d83b2ff251096e72792a4eb7c3d2e89b765f06a728321`，与合并摘要中的 `base_sha256` 一致。
- 变更前配置备份存在，权限为 `0600`。
- 备份目录中的 `README.md` 已记录用途、哈希、变更内容、验收边界和回滚命令。
- 合并后共有 `204` 个显式技能配置项，本轮新增 `67` 个禁用项；技能和插件原件均未删除。

## 非阻塞遗留项

- 严格自检仍报告网络可达性和状态路径失败，以及可选 MCP、网络套接字和更新检查警告。这些不是 P2 引入的问题。
- `config.load` 仍报告四个重复代理角色名：`code-reviewer`、`literature-reviewer`、`rebuttal-writer`、`tdd-guide`。该问题属于代理角色治理，不属于技能裁剪验收范围。
- 已启动的旧 Codex 会话不会热加载新技能清单；必须新建或重启会话才能稳定使用裁剪结果。

## 最终裁决

P2 技能裁剪可以投入使用。后续若出现关键任务无法召回对应技能，应依据私有备份做增量恢复，不应直接覆盖此后新增的其他用户配置。
