# Codex Skills P0/P1 实施报告

日期：2026-07-30  
实施范围：仅执行 `.Codex/docs/codex-agents-hook-research.md` 规定的 Skills-P0 与 Skills-P1。

## 1. 结论

P0 盘点与 P1 可逆隔离均已完成。P1 没有删除、移动或改写任何 `SKILL.md`，而是新增一个只有显式选择才生效的 Codex 配置档案：

```text
/Users/bilibili/.codex/thesis-skills.config.toml
```

使用该档案时，13 个逐字节相同的旧副本不再进入运行时技能索引；对应技能名称仍由 `~/.agents/skills` 中的规范副本提供。活动技能总数由 134 个降为 121 个。

默认启动行为没有改变。只有下列形式才启用隔离档案：

```bash
codex --profile thesis-skills
codex --profile thesis-skills exec "任务描述"
```

## 2. P0 盘点结果

| 项目 | 数量 |
| --- | ---: |
| 当前实际发现的本地 `SKILL.md` | 175 |
| P0 运行时活动技能 | 134 |
| `~/.agents/skills` 与 `~/.codex/skills` 的同目录名组 | 37 |
| 逐字节相同组 | 20 |
| 内容不同组 | 17 |
| 已由既有用户配置去重 | 7 |
| P1 需要隔离的相同副本 | 13 |
| 无效前置元数据 | 0 |

历史调研记录曾写 176 个本地技能，本轮以实际文件系统重新盘点得到 175 个。没有为凑齐历史数量而复制或补造文件。完整清单、路径、哈希和分类见：

- `p0/skills-inventory.json`
- `p0/duplicate-groups.json`
- `p0/duplicate-groups.md`
- `p0/p1-candidates.json`
- `p0/summary.json`

用户主配置原件只备份到权限为 `0700` 的私有目录，没有写入仓库：

```text
/Users/bilibili/.codex/backups/skills-governance-p0-20260730-1302
```

仓库内只记录脱敏状态和私有备份位置。

## 3. P1 方案与试点裁决

### 3.1 项目配置试点失败并已回滚

首先在项目级 `.codex/config.toml` 只禁用 `planning-with-files` 的旧副本。严格配置解析可以通过，但新的 `codex debug prompt-input` 仍同时列出两条来源，说明当前 Codex 版本不会在项目配置层应用 `skills.config`。

该试点文件已完整移除。当前 `.codex/config.toml` 不存在，未留下无效项目配置。试点证据位于：

- `p1/pilot/codex-doctor.json`
- `p1/pilot/active-index.txt`

### 3.2 专用配置档案试点成功

随后改用 Codex 官方支持的配置档案叠加机制。单项试点使活动技能从 134 个降为 133 个，并满足：

- `r1/planning-with-files/SKILL.md` 仍在活动索引；
- `r0/planning-with-files/SKILL.md` 已从活动索引消失；
- 技能名称仍可显式调用。

试点通过后才扩展至其余 12 项。最终模板保存在 `p1/thesis-skills.config.toml`，安装文件与模板的 SHA-256 均为：

```text
c9958a18b1f0eb82f902a7f7d9bbd71167fd965d4c70d4c165c3bb0e9f65fc85
```

安装文件权限为 `0600`。

## 4. P1 隔离清单

以下每组的两个文件 SHA-256 完全一致。P1 保留 `~/.agents/skills` 规范副本，只在 `thesis-skills` 档案中禁用 `~/.codex/skills` 旧副本。

| 技能 | 规范副本 | 隔离副本 | SHA-256 |
| --- | --- | --- | --- |
| `latex-conference-template-organizer` | `~/.agents/skills/latex-conference-template-organizer/SKILL.md` | `~/.codex/skills/latex-conference-template-organizer/SKILL.md` | `3042069e385f515be086ea8f3aff7b3ef68570a54648f62182645ef9da19e0f5` |
| `nature-data` | `~/.agents/skills/nature-data/SKILL.md` | `~/.codex/skills/nature-data/SKILL.md` | `16761a2d6aef2a28f25b4eb443c4d47d7e393d4de525b11793b72452f1d116d8` |
| `nature-polishing` | `~/.agents/skills/nature-polishing/SKILL.md` | `~/.codex/skills/nature-polishing/SKILL.md` | `946eeed13b86805fbd926e6adc25c84d825e3726f001a11175b9ad277e3a2792` |
| `nature-response` | `~/.agents/skills/nature-response/SKILL.md` | `~/.codex/skills/nature-response/SKILL.md` | `9521d5cd6d66b331a635dda21608fc9546d0ef10140d3cfa28f1acb11c0da159` |
| `nature-writing` | `~/.agents/skills/nature-writing/SKILL.md` | `~/.codex/skills/nature-writing/SKILL.md` | `9cf73605a225fd17d1ee191c5f8f978a198902eeb3ff467edc7de38bfdbeae4c` |
| `obsidian-kb-artifacts` | `~/.agents/skills/obsidian-kb-artifacts/SKILL.md` | `~/.codex/skills/obsidian-kb-artifacts/SKILL.md` | `14f01b72484904ae2eab93e159fdfcf7a631d5deb36eeff7fe057214404bad6e` |
| `obsidian-literature-workflow` | `~/.agents/skills/obsidian-literature-workflow/SKILL.md` | `~/.codex/skills/obsidian-literature-workflow/SKILL.md` | `63f63a1a1465d450e53c3cd8baa970391fefdf5617db9ba63e724553f5e83ad7` |
| `paper-self-review` | `~/.agents/skills/paper-self-review/SKILL.md` | `~/.codex/skills/paper-self-review/SKILL.md` | `e9c0040db7394e537becb5209f1b0100eb1267fbf1c540a2da07d7876cb93a41` |
| `planning-with-files` | `~/.agents/skills/planning-with-files/SKILL.md` | `~/.codex/skills/planning-with-files/SKILL.md` | `6b527bee3d60e5f57c255c194aeb7b56e0bf429400a6be6191df6d70698ca9c6` |
| `post-acceptance` | `~/.agents/skills/post-acceptance/SKILL.md` | `~/.codex/skills/post-acceptance/SKILL.md` | `1d3432e6bff94c61779df9fea3c719ed425bf6fe90e8acb0366a7f1c51e6401e` |
| `publication-chart-skill` | `~/.agents/skills/publication-chart-skill/SKILL.md` | `~/.codex/skills/publication-chart-skill/SKILL.md` | `dd95ca64069b85bd7dddb99bc5ad0762bfb402106524b22eb85973fa255a5d87` |
| `results-analysis` | `~/.agents/skills/results-analysis/SKILL.md` | `~/.codex/skills/results-analysis/SKILL.md` | `2232f74d141fad4a3e23635be0109217713d34bf0cb7be8d120e6296f4b79782` |
| `zotero-obsidian-bridge` | `~/.agents/skills/zotero-obsidian-bridge/SKILL.md` | `~/.codex/skills/zotero-obsidian-bridge/SKILL.md` | `7d89742d4db187eb8ef93032a9b39470c41fb560ce4ff661b69ea946176b477a` |

统一裁决理由：两份内容逐字节相同，保留当前官方用户目录 `~/.agents/skills` 中的副本，隔离旧的 `~/.codex/skills` 副本。没有进行文件删除，因此回滚只需停用配置档案。

另外 7 组相同副本已由 P0 前存在的用户配置去重，本轮没有改写它们：`architecture-design`、`bug-detective`、`code-review-excellence`、`daily-paper-generator`、`expression-skill`、`git-workflow`、`obsidian-source-ingestion`。

## 5. 验证结果

机器验收文件：`p1/verification.json`。14 项检查全部通过：

- 本地技能文件仍为 175 个，所有文件路径和 SHA-256 与 P0 一致；
- 活动技能由 134 个精确降为 121 个；
- 20 组逐字节相同技能均只剩 1 个活动来源；
- 17 组内容不同的同名技能在路径、哈希、字节数和活动状态上均未变化；
- 13 个配置项唯一、全部为 `enabled = false`，且与 P0 候选清单完全一致；
- 显式调用 `$planning-with-files`、`$results-analysis`、`$nature-data` 均解析到 `~/.agents/skills` 规范路径；
- 插件安装、启用、版本、安装策略和鉴权策略未变化；
- 插件市场集合未变化；
- 用户主配置已恢复为 P0 SHA-256：`f69e9dd08bd84a315a2b94abafd3b86fdeff96ed46df2c7562d9876a5f775a0f`；
- 项目级 `.codex/config.toml` 不存在；
- 专用配置档案权限为 `0600`。

验证期间，`codex plugin list --available` 自动刷新了 `claude-plugins-official` 的市场缓存，并使 `chrome-devtools-mcp` 的来源提交哈希变化。插件版本、安装和启用状态没有变化。用户主配置中由该查询改动的 `last_revision` 与 `last_updated` 两个缓存字段已从 P0 私有备份恢复；刷新后的中间配置也保存在同一私有备份目录。没有回退或改写插件缓存。

显式调用验收第一次使用 WebSocket 时发生连接重置，Codex 自动回退到 HTTPS 后正常返回结果。事件日志为 `p1/explicit-skill-events.jsonl`，最终回答为 `p1/explicit-skill-last-message.txt`。

## 6. 已变更与未变更范围

### 已新增或安装

- `.Codex/docs/skills-governance/audit_skills.py`
- `.Codex/docs/skills-governance/verify_p1.py`
- `.Codex/docs/skills-governance/p0/` 下的 P0 盘点制品
- `.Codex/docs/skills-governance/p1/` 下的试点、最终索引与验收制品
- `.Codex/docs/skills-governance/p0-p1-implementation-report.md`
- `/Users/bilibili/.codex/thesis-skills.config.toml`
- `/Users/bilibili/.codex/backups/skills-governance-p0-20260730-1302/` 下的私有回滚备份

### 明确未变更

- 所有 `SKILL.md` 文件内容、名称和位置；
- 17 组内容不同的同名技能；
- `allow_implicit_invocation`；
- 插件启用状态和全局默认插件策略；
- `AGENTS.md`、Hooks、代理角色配置；
- 论文、实验代码、服务器配置和实验制品；
- 用户主配置的最终内容；
- 项目级 `.codex/config.toml`。

显式调用事件中暴露出既有的重复代理角色警告：`code-reviewer`、`literature-reviewer`、`rebuttal-writer`、`tdd-guide`。这些属于代理治理后续阶段，不在 Skills-P0/P1 授权范围内，本轮没有处理。

## 7. 回滚方案

### 立即停用

启动 Codex 时不传 `--profile thesis-skills` 即可。默认配置从未绑定该档案，因此不需要修改任何文件。

### 完整撤销安装

将配置档案移动到既有私有备份目录，而不是删除：

```bash
mv /Users/bilibili/.codex/thesis-skills.config.toml \
  /Users/bilibili/.codex/backups/skills-governance-p0-20260730-1302/thesis-skills.config.toml.disabled
```

恢复时执行反向移动。由于技能文件从未删除，完整撤销不会造成技能丢失。

## 8. P2 及以后阶段边界

本轮到 P1 为止，以下事项均未执行，必须等待新的用户授权：

- 不处理 17 组内容不同的同名技能；
- 不修改重复代理角色或代理注册；
- 不创建、启用或修改 Hooks；
- 不调整 `AGENTS.md` 层级、长度或内容；
- 不修改插件启用状态、默认调用策略或 `allow_implicit_invocation`；
- 不删除、移动或合并技能文件；
- 不把 `thesis-skills` 设为全局默认配置档案。
