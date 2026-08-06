# Codex → Claude Code 迁移设计

- **日期**:2026-08-06
- **方案**:B(保留 `.Codex/` 为共享源,Claude 侧补 settings 适配)
- **目标**:Claude Code 达到完全可用 parity;规则源与基础设施保持中立/共享,可在 Codex 与 Claude Code 之间切换;不烧掉回 Codex 的桥。
- **范围**:仓库 `/Users/bilibili/personal/note`,不含全局 `~/.codex/`、`~/.claude/` 改动(全局层已基本对齐)。

---

## 1. 架构总览

```
规则层(已入库,工具中立)          基础设施层(.Codex/ 共享,gitignored)
┌─────────────────────────┐      ┌──────────────────────────────┐
│ AGENTS.md (根+7子目录)   │      │ .Codex/docs/    工作记忆(250份)│
│   ← 改写为工具中立        │      │ .Codex/hooks/   5个Python脚本 │
│ CLAUDE.md (根+6子目录)   │      │ .Codex/tools/   prettier      │
│   ← 薄适配:@AGENTS.md    │      │ .Codex/precompact_snapshot.json│
│                          │      │ .Codex/hooks.json  Codex侧注册 │
└─────────────────────────┘      └──────────────────────────────┘
                                          ↑
配置层(各工具原生)                     │ 同一批脚本
┌───────────────┐  ┌──────────────┐      │
│ .claude/       │  │ ~/.codex/     │─────┘
│ settings.json  │  │ config.toml   │
│  ← 新增 hooks  │  │  (不动)       │
└───────────────┘  └──────────────┘
```

**原则**

- 规则内容单一真源:`AGENTS.md`(根 + 7 子目录)。
- 钩子脚本单一真源:`.Codex/hooks/`;各工具只在自己的配置文件里注册引用,不复制脚本。
- 工作记忆单一真源:`.Codex/docs/`(gitignored,Codex/Claude Code 共用)。
- 入库设计规约:`.claude/docs/`(git-tracked)。
- Codex 侧 `~/.codex/config.toml` 与 `.Codex/hooks.json` 不动,切换回 Codex 零成本。

---

## 2. 规则源改写(AGENTS.md 工具中立化)

逐文件把 Codex 专属措辞改为工具中立表述,保留全部研究、实验、凭据、搜索、调试规则的实质。

### 2.1 改写映射表

| 当前措辞(Codex 专属) | 改写为(工具中立) |
|---|---|
| "Codex 启动时从项目根走到当前工作目录" | "编码代理从项目根走到当前工作目录加载规则" |
| "Codex 不会因为随后编辑了子目录文件而动态重新发现规则" | "代理不会因后续编辑动态重载规则;跨子域任务须主动完整读取对应局部文件" |
| "Codex 不会因为随后编辑…动态重新发现规则"小节整段 | 保留规则意图,主语改为"代理" |
| "Codex 专属工具名、技能名、代理名、配置名或斜杠命令,应遵循其安全与质量目标,并只使用当前 Claude Code 实际可用的等效能力;不得假定不存在的命令或工具" | 删除前半句(已由各工具原生加载机制覆盖),保留"不得假定不存在的命令或工具" |
| "当 Claude Code 的原生规则加载行为与 `AGENTS.md` 的 Codex 机制描述不同,以 Claude Code 的实际加载方式为准" | 改为"当两个代理的原生加载行为与 `AGENTS.md` 描述不同,以各自实际加载方式为准" |
| "使用 `/memory` 核对本会话实际加载的 `CLAUDE.md` 与规则文件" | 保留(Claude Code 命令) |
| "`.codexignore`" | 删除该句;`.ignore` 已统一控制 `rg`/`fd` |
| "不得假定 Codex 支持 Claude Code 的斜杠命令;只使用当前环境实际提供的技能、代理和可复现命令" | 改为"不得假定一个代理支持另一个代理的斜杠命令;只使用当前环境实际提供的技能、代理和命令" |
| "上下文恢复协议"中 `screen` 会话核验 | 保留 `screen` 核验(服务器事实),删除"Codex"主语 |
| "运行事实以服务器原始日志…不得用旧进度覆盖新证据" | 保留,表述已中立 |
| 实验工程开发范式段(`brainstorming` / `writing-plans` / `subagent-driven-development` / `test-driven-development`) | 保留(技能名是跨工具的 superpowers 体系,Codex 与 Claude Code 都可用),删除"Codex"主语 |
| "所有生成的文档统一放在 `.Codex/docs/`" | 保留(共享工作记忆目录) |

### 2.2 根 `CLAUDE.md` 适配段更新

当前"适配说明"段更新为:

> - 本文件是 Claude Code 的根级入口;`AGENTS.md` 是本仓库规则唯一来源,工具中立。
> - 每个受管子目录的 `CLAUDE.md` 通过 `@AGENTS.md` 导入同目录 `AGENTS.md`。Claude Code 读取该目录内文件时,按目录级原生加载机制生效。
> - 规则源 `AGENTS.md` 由 Codex 与 Claude Code 共享;基础设施(`.Codex/hooks/`、`.Codex/docs/`、`.Codex/tools/`)亦共享,各工具只在自己的配置文件里注册引用。
> - 当两个代理的原生加载行为与 `AGENTS.md` 描述不同,以各自实际加载方式为准;研究边界、数据证据、凭据保护、验证和写入规则仍完整有效。
> - 使用 `/memory` 核对本会话实际加载的 `CLAUDE.md` 与规则文件;规则是行为指引,权限、沙箱和工具限制以 Claude Code 设置为准。
> - **文档目录约定**:本仓库过程文档(计划、笔记、审计、过程记录)放 `.Codex/docs/`(共享工作记忆,gitignored);入库设计规约放 `.claude/docs/`。此约定覆盖全局规则中"`.claude/docs/`"的默认指向。

### 2.3 子目录 CLAUDE.md

7 个子目录(`output/`、`raw/`、`thesis/`、`wiki/`、`thesis/experiments/llm_probe/`、`thesis/experiments/llm_probe/scripts/`、根)的 `CLAUDE.md` 已是 `@AGENTS.md` 薄导入,无需改动;仅根 `CLAUDE.md` 加上述覆盖行。

---

## 3. Hooks 映射表

| Codex 钩子(`.Codex/hooks.json`) | Claude Code 钩子(`.claude/settings.json`) | 脚本 | 改动 |
|---|---|---|---|
| PreToolUse `*` → prettier_guard | PreToolUse matcher `Bash` → prettier_guard | `.Codex/hooks/prettier_guard.py` | **无改动**,原样引用。脚本 stdin 契约(`{hook_event_name, tool_name, tool_input}`)、工具名白名单(含 `Bash`)、输出(`hookSpecificOutput.permissionDecision:"deny"`)与 Claude Code PreToolUse 完全一致。 |
| PreCompact `manual\|auto` → precompact_snapshot | PreCompact → precompact_snapshot | `.Codex/hooks/precompact_snapshot.py` | **小补丁**:`REQUIRED_INPUT_KEYS` 移除 `turn_id`、`model`,改为可选(见 §4)。 |
| (未注册) project_policy_guard | 不接入 | `.Codex/hooks/project_policy_guard.py` | 保持休眠(`main()` 已 `return 0`),迁移期不注册。 |
| (未注册) server_launcher_guard | 不接入 | `.Codex/hooks/server_launcher_guard.py` | project_policy_guard 的依赖,随之休眠。 |

**超时单位换算**:Codex `timeout: 5`(秒)→ Claude Code `timeout: 5000`(毫秒)。

---

## 4. `precompact_snapshot.py` 补丁

### 4.1 问题

`precompact_snapshot.py` 的 `REQUIRED_INPUT_KEYS` 强制要求:

```python
REQUIRED_INPUT_KEYS = {
    "cwd",
    "hook_event_name",
    "model",
    "session_id",
    "transcript_path",
    "trigger",
    "turn_id",
}
```

`_parse_payload` 对缺失字段抛 `SnapshotError` → `_failure_output` → 优雅降级(压缩继续,快照不更新)。Codex 的 PreCompact payload 提供全部 7 字段;Claude Code 的 PreCompact payload 不含 `turn_id`、`model`,导致脚本在 Claude Code 下每次失效。

### 4.2 改法

把 `turn_id`、`model` 从"必需"降为"可选":

```python
REQUIRED_INPUT_KEYS = {
    "cwd",
    "hook_event_name",
    "session_id",
    "transcript_path",
    "trigger",
}
OPTIONAL_INPUT_KEYS = {
    "model",
    "turn_id",
}
```

`_parse_payload` 只校验 `REQUIRED_INPUT_KEYS`;`OPTIONAL_INPUT_KEYS` 不参与缺失校验,但可被调用方按需读取(当前脚本未使用这两个字段值,仅做存在性校验,故移除校验无副作用)。

**对 Codex 的影响**:无。Codex payload 仍含这两个字段,降为可选不改变其行为。

**配置路径**:`CONFIG_PATH = Path(".codex/precompact_snapshot.json")`(小写),实际文件位于 `.Codex/precompact_snapshot.json`(大写 C)。macOS APFS 默认大小写不敏感,可正常读取。若未来在大小写敏感文件系统运行,需统一大小写——列为已知局限(§7)。

### 4.3 测试

`.Codex/hooks/tests/` 既有测试用例若依赖 `turn_id`/`model` 必填,需同步放宽。实施时跑 `python3 -m pytest .Codex/hooks/tests/`,按失败用例最小修订。

---

## 5. `.claude/settings.json` 目标内容

```json
{
  "permissions": {
    "allow": [
      "Bash(cp /Users/bilibili/Downloads/2504.13592v2.pdf /Users/bilibili/personal/note/raw/papers/)",
      "Bash(pdftotext -layout /Users/bilibili/personal/note/raw/papers/2504.13592v2.pdf -)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$(git rev-parse --show-toplevel)/.Codex/hooks/prettier_guard.py\"",
            "timeout": 5000
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$(git rev-parse --show-toplevel)/.Codex/hooks/precompact_snapshot.py\"",
            "timeout": 8000
          }
        ]
      }
    ]
  }
}
```

保留既有 2 条权限;新增 `hooks` 段。Codex 侧 `.Codex/hooks.json` 不动。

---

## 6. 文档目录约定

| 目录 | 用途 | 入库 |
|---|---|---|
| `.Codex/docs/` | 共享工作记忆(task_plan、notes、审计、过程记录);Codex 与 Claude Code 共用;250 份既有文档零位移 | 否(gitignored) |
| `.claude/docs/` | 提交入库的设计规约、迁移说明 | 是(`.gitignore` 仅排除 `.claude/logs/`) |

根 `CLAUDE.md` 增加覆盖行(见 §2.2),使本仓库过程文档目录优先指向 `.Codex/docs/`,覆盖全局 `~/.claude/CLAUDE.md` 中"`.claude/docs/`"的默认指向。

---

## 7. 已知局限

1. **`.Codex/` 命名不中立**:共享目录仍叫 `.Codex/`(工具品牌名),中立性靠文档约定而非物理体现。可在 phase 2 重命名为 `.agent/`,但需同步改 `~/.codex/config.toml`、`precompact_snapshot.json`、各 AGENTS.md 路径、`.gitignore`——当前不做的权衡是"最小扰动 250 份文档与活动计划路径"。
2. **大小写敏感文件系统**:`precompact_snapshot.py` 硬编码 `.codex/`(小写),文件实际为 `.Codex/`。macOS 默认不敏感可过;迁移到 Linux 大小写敏感环境需统一。
3. **休眠门禁未迁移**:`project_policy_guard.py`(及其依赖 `server_launcher_guard.py`)未注册,引用 Codex 专属工具名(`Agent`/`spawn_agent`)。将来若要在 Claude Code 启用,需把工具名改为 Claude Code 的 `Task`,并解禁 `main()` 的 `return 0`。
4. **全局层未在本范围**:`~/.codex/config.toml`、`~/.codex/AGENTS.md`、`~/.claude/CLAUDE.md`、`~/.claude/rules/` 的对齐不在本次迁移范围(已基本对齐)。

---

## 8. 验证清单(实施后执行)

1. **prettier_guard 手测**:喂入含 `prettier` 的 Bash payload → 返回 `{"hookSpecificOutput":{"permissionDecision":"deny",...}}`。
2. **precompact_snapshot 手测**:喂入 Claude Code PreCompact payload(无 `turn_id`/`model`)→ 不报错;`output/开题改进交接文档.md`、`output/第一创新点实验总控.md` 出现 `<!-- PRECOMPACT_SNAPSHOT_START -->` 区块。
3. **既有测试**:`python3 -m pytest .Codex/hooks/tests/` 全过。
4. **规则中立化**:`rg "Codex 启动时|\.codexignore|Codex 不会因为"` 命中数为 0。
5. **Claude Code 集成**:启动会话,触发 `/compact`,确认快照区块被写入两份恢复文档。
6. **Codex 可逆性**:不动 `~/.codex/config.toml` 与 `.Codex/hooks.json`,启动 Codex 确认钩子仍生效、`.Codex/docs/` 活动计划仍可达。

---

## 9. 实施步骤(供 writing-plans 展开)

1. 改写根 `AGENTS.md`:按 §2.1 映射表逐条替换 Codex 专属措辞。
2. 更新根 `CLAUDE.md` 适配段为 §2.2 文本。
3. 补丁 `.Codex/hooks/precompact_snapshot.py`:§4.2,把 `turn_id`/`model` 降为可选。
4. 同步 `.Codex/hooks/tests/`:按 §4.3 跑测试,最小修订失败用例。
5. 写入 `.claude/settings.json`:§5 目标内容。
6. 执行 §8 验证清单全部通过。
7. 提交:规约文档(`.claude/docs/`)、改写后的 `AGENTS.md`、`CLAUDE.md`、`precompact_snapshot.py`、测试修订、`.claude/settings.json` 分组提交。
