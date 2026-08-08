# Codex 技能上下文治理报告

日期：2026-07-30  
Codex 版本：`0.144.5`

## 结论

本轮已完成低风险、可逆的 P0/P1 治理。默认活动技能由 `134` 个降为 `121` 个，逐字节相同的重复技能名组由 `13` 个降为 `0` 个。技能文件、插件配置、内容不同的同名技能和论文实验文件均未改变。

该改动明显降低重复检索和误选风险，但没有显著减少技能区的原始字符数。技能区由 `22,255` 字符降为 `22,243` 字符，原因是 Codex 会在固定预算内为剩余技能显示更完整的描述。若目标是进一步释放上下文，而不只是去重，必须进入需要用户批准的 P2 作用域裁剪。

## 1. 原因核验

Codex 官方文档确认以下行为：

1. Codex 启动时先注入每个技能的名称、描述和路径，完整 `SKILL.md` 只在选中技能后读取。这是渐进式披露，不是完全按需发现。
2. Codex 会扫描仓库、用户、管理员和系统技能目录。同名技能不会合并，两个来源都可能出现在选择器和初始技能清单中。
3. 初始技能清单最多使用模型上下文窗口的 `2%`；上下文窗口未知时上限为 `8,000` 字符。技能很多时，Codex 先缩短描述，再视情况省略技能。
4. `[[skills.config]]` 是官方支持的逐技能启停机制，修改后需要重启 Codex。
5. `agents/openai.yaml` 中的 `allow_implicit_invocation = false` 只禁止隐式调用，官方文档没有说明它会从初始技能清单移除元数据，因此不能把它当成上下文治理手段。
6. 配置档案必须通过 `--profile` 显式选择。Codex `0.134.0` 以后不再支持在主配置中设置默认配置档案。

依据：

- [构建技能](https://learn.chatgpt.com/docs/build-skills)
- [自定义概览](https://learn.chatgpt.com/docs/customization/overview#skills)
- [配置档案](https://learn.chatgpt.com/docs/config-file/config-advanced#profiles)
- [配置优先级](https://learn.chatgpt.com/docs/config-file/config-basic#configuration-precedence)
- [配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)
- [插件结构](https://developers.openai.com/plugins/build/plugins)

官方手册抓取脚本在普通沙箱中因域名解析失败、在联网环境中因服务器返回 `403` 失败。本轮随后使用 OpenAI 官方文档服务逐页核验，没有使用 Claude Code 行为推断 Codex 机制。

## 2. 修改前盘点

| 项目 | 数量 |
| --- | ---: |
| 本地 `SKILL.md` 文件 | 175 |
| 默认活动技能 | 134 |
| 唯一技能名 | 109 |
| 重复技能名组 | 25 |
| `~/.agents/skills` 与 `~/.codex/skills` 同目录名组 | 37 |
| 逐字节相同组 | 20 |
| 内容不同组 | 17 |
| 已由旧配置去重的相同组 | 7 |
| 本轮待去重的相同组 | 13 |

重复的根因是 `~/.agents/skills` 与旧的 `~/.codex/skills` 同时被发现。仓库内不存在 `.agents/skills`，因此本轮重复不是仓库技能造成的。

## 3. P0/P1 变更

在修改前，用户配置已备份到权限受限的私有目录：

```text
/Users/bilibili/.codex/backups/skills-context-default-20260730-172211
```

随后向 `~/.codex/config.toml` 增加 `13` 个 `[[skills.config]]` 条目，只禁用与 `~/.agents/skills` 规范副本逐字节相同的旧 `~/.codex/skills` 副本。

变更具有以下边界：

- 未删除、移动或修改任何 `SKILL.md`；
- 未改变插件安装、启用或鉴权策略；
- 未处理内容不同的同名技能；
- 未修改代理角色、钩子、`AGENTS.md`、论文或实验文件；
- 既有 `thesis-skills` 配置档案保留，默认配置现在具有相同的 13 项去重效果。

## 4. 独立进程验证

新的独立 Codex 进程执行 `debug prompt-input` 后得到：

| 指标 | 修改前 | 修改后 |
| --- | ---: | ---: |
| 活动技能 | 134 | 121 |
| 唯一技能名 | 109 | 109 |
| 重复技能名组 | 25 | 12 |
| 技能区字符数 | 22,255 | 22,243 |

进一步核验结果：

- `175` 个技能文件的路径和 SHA-256 全部不变；
- `20` 组逐字节相同技能均只剩一个活动来源；
- `17` 组内容不同的同名技能状态未变；
- 用户配置只新增 `13` 个禁用项，其余配置完全一致；
- 插件配置完全一致；
- 既有 `thesis-skills` 配置档案仍正常加载，活动技能仍为 `121` 个；
- 官方自检中配置解析正常，技能警告和插件警告均为 `0`；
- 自检共有 `15` 项正常、`3` 项警告，警告来自既有的重复代理角色和可选 MCP 状态，与本轮技能配置无关。

过程中文件所有者、模式和目录状态均正常，但沙箱内的 shell 对 `.Codex/docs/skills-governance/` 新建目录或文件返回 `Operation not permitted`。该现象定位为当前 shell 沙箱写入边界，不是仓库目录权限损坏。本轮没有改权限或绕开仓库规则；手工文档使用规定的 `apply_patch` 写入，格式化命令经受控授权执行。

机器可读验收结果见 `2026-07-30-default-skills-verification.json`。

## 5. `AGENTS.md` 占用

| 作用域 | 字节数 |
| --- | ---: |
| `~/.codex/AGENTS.md` | 10,385 |
| 仓库根 `AGENTS.md` | 8,035 |
| 从仓库根启动时累计 | 18,420 |
| `.Codex/docs/AGENTS.md` | 1,927 |
| 从过程文档目录启动时累计 | 20,347 |
| 默认组合上限 | 32,768 |

当前规则累计没有超限，不是技能清单过多的直接原因。规则仍应继续遵循“全局只放个人默认、仓库只放长期边界、局部规则放最近目录”的分层原则。

## 6. 尚存问题

默认活动索引仍有 `12` 组内容不同的同名技能：

- `kaggle-learner`
- `ml-paper-writing`
- `obsidian-project-kb-core`
- `research-ideation`
- `results-report`
- `review-response`
- `skill-development`
- `skill-improver`
- `skill-quality-reviewer`
- `uv-package-manager`
- `verification-loop`
- `writing-anti-ai`

这些副本不能按文件名直接去重。它们的正文不同，必须先比较触发范围、工作流完整性、引用资源和当前论文仓库适配性，再选择保留来源。

当前会话在启动时已缓存旧技能清单。默认去重只会在完全退出并重新启动 Codex 后反映到交互界面；独立诊断进程已经验证新会话会加载 `121` 个活动技能。

## 7. P2 待批准项

以下操作均未执行：

1. 对 `12` 组内容不同的同名技能执行批量质量评审，每组只保留一个活动来源。完成后理论下限为 `109` 个活动技能，但技能区仍可能继续占满其预算。
2. 建立显式选择的 `thesis-core` 配置档案，按论文研究场景禁用前端、站点托管、云部署、无关模板和不使用的浏览器性能技能。建议先把目标控制在 `45–65` 个活动技能，再用真实任务回归验证召回率。
3. 审查插件级技能来源。只有确认整个插件近期不用时才禁用插件，避免为了少量上下文丢失浏览器、文档、GitHub 或 LaTeX 能力。
4. 对自有技能的长描述做批量质量评审，优先把触发条件前置。该动作主要改善隐式匹配，不应宣称能在技能清单仍达到预算上限时明显节省字符。
5. 单独治理 `code-reviewer`、`literature-reviewer`、`rebuttal-writer`、`tdd-guide` 四个重复代理角色。它们会产生启动警告，但不属于技能去重。

## 8. 回滚

修改前后的完整配置均保存在私有备份目录中。若没有后续配置变更，可用 `config.toml.before` 恢复并重启 Codex。若此后配置又发生变化，应只移除本轮新增的 13 个条目，避免用整文件恢复覆盖新配置。
