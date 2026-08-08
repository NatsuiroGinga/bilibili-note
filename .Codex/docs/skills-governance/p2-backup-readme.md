# Codex P2 技能裁剪备份说明

## 用途

本目录保存 2026-07-31 实施 P2 毕业论文作用域技能裁剪前的 Codex 用户配置。该变更只调整技能和插件的启用状态，不删除技能、插件、论文、数据、模型或实验制品。

## 备份内容

- `config.toml.before-p2`：变更前用户配置的完整私有备份。
- 变更前 SHA-256：`e6db1ff50fa5a3d12d3d83b2ff251096e72792a4eb7c3d2e89b765f06a728321`。
- 文件权限：`0600`。
- 备份目录：`/Users/bilibili/.codex/backups/skills-governance-p2-20260731-142459/`。

## 已实施变更

- 当前用户配置 SHA-256：`48bb5dc077939647fc7934a04c4bab5442b6607a2b3dd18d1d6a11f0a0707cab`。
- 技能禁用配置共 `204` 项，其中本轮新增 `67` 项。
- 停用 `sites`、Go 语言服务器、Google Calendar、Slack 和 Chrome 开发者工具插件。
- 独立 Codex 进程发现 `45` 个活动技能，技能区共 `18,033` 字符，同名重复组为 `0`。
- 规划、论文写作、结果分析、文献管理、PDF、调试、Git、SwanLab、Hugging Face、子代理开发和验证能力均保留至少一个活动来源。
- 当前已经运行的 Codex 会话不会热加载新列表，重启或新建会话后才会使用裁剪结果。

## 验收边界

- `codex --strict-config doctor --summary --no-color --ascii` 已确认配置成功加载。
- 自检仍报告既有的状态数据库完整性、网络可达性和可选 MCP 警告；这些问题不属于技能配置解析失败，也不是本轮变更引入。
- 独立复审报告见仓库 `.Codex/docs/skills-governance/p2-independent-audit.md`。该文件生成前，以本说明和治理计划中的主进程验证结果为准。

## 回滚

执行下列命令恢复变更前配置：

```bash
install -m 600 \
  /Users/bilibili/.codex/backups/skills-governance-p2-20260731-142459/config.toml.before-p2 \
  /Users/bilibili/.codex/config.toml
```

恢复后重新运行严格配置检查，并重启 Codex：

```bash
codex --strict-config doctor --summary --no-color --ascii
```

不要在确认多个新会话均能正常发现关键技能之前删除本备份。

## 相关文件

- 合并工具：`/Users/bilibili/personal/note/.Codex/docs/skills-governance/merge_p2_config.py`
- 治理计划：`/Users/bilibili/personal/note/.Codex/docs/2026-07-31-Codex技能上下文预算治理计划.md`
- 治理报告：`/Users/bilibili/personal/note/.Codex/docs/2026-07-31-Codex技能上下文预算治理报告.md`
