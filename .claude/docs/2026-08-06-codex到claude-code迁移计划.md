# Codex → Claude Code 迁移实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Claude Code 在本仓库达到与 Codex 等价的规则加载与钩子门禁能力,同时保留可切回 Codex 的桥。

**Architecture:** 方案 B——`AGENTS.md` 作为工具中立单一规则源(改写 Codex 专属措辞),`.Codex/hooks/` 作为共享脚本真源,Claude Code 在 `.claude/settings.json` 里注册引用同一批脚本;`precompact_snapshot.py` 补丁让 Codex 专属的 `turn_id`/`model` 字段降为可选以兼容 Claude Code 的 PreCompact payload。

**Tech Stack:** Python 3(钩子脚本)、JSON(`.claude/settings.json`)、Markdown(规则文件)、pytest(既有钩子测试)。

**设计规约:** `.claude/docs/2026-08-06-codex到claude-code迁移设计.md`

**文档目录约定:** 本计划与设计规约均位于 `.claude/docs/`(git-tracked);过程工作记忆在 `.Codex/docs/`(gitignored)。

---

## File Structure

| 文件 | 责任 | 动作 |
|---|---|---|
| `.Codex/hooks/precompact_snapshot.py` | PreCompact 钩子:压缩前刷新两份恢复文档快照 | 改(`REQUIRED_INPUT_KEYS` 移除 `turn_id`/`model`,新增 `OPTIONAL_INPUT_KEYS`) |
| `.Codex/hooks/tests/test_precompact_snapshot.py` | precompact_snapshot 单元测试 | 加 1 个最小 payload 测试方法 |
| `AGENTS.md`(根) | 仓库长期规则单一真源 | 改 5 行 Codex 专属措辞为工具中立 |
| `CLAUDE.md`(根) | Claude Code 根级入口,薄导入 `AGENTS.md` | 改"适配说明"段 + 加文档目录约定覆盖行 |
| `.claude/settings.json` | Claude Code 权限与钩子注册 | 改:保留权限,新增 `hooks` 段 |

子目录 `AGENTS.md`(output/raw/thesis/wiki/llm_probe/scripts)**不动**(已无 Codex 专属措辞)。Codex 侧 `~/.codex/config.toml`、`.Codex/hooks.json` **不动**。

---

## Task 1: precompact_snapshot.py 补丁(TDD)

**Files:**
- Modify: `.Codex/hooks/precompact_snapshot.py:30-38`(`REQUIRED_INPUT_KEYS` 区)
- Test: `.Codex/hooks/tests/test_precompact_snapshot.py`(加方法)

- [ ] **Step 1: 写失败测试**

在 `.Codex/hooks/tests/test_precompact_snapshot.py` 的 `PreCompactSnapshotTest` 类内(建议置于 `test_sample_input_matches_official_required_fields` 之后)新增方法:

```python
    def test_parse_payload_accepts_minimal_payload_without_optional_fields(self) -> None:
        import io

        minimal_payload = {
            "session_id": "test-session",
            "transcript_path": None,
            "cwd": str(self.root),
            "hook_event_name": "PreCompact",
            "trigger": "manual",
        }
        stream = io.StringIO(json.dumps(minimal_payload))
        parsed = HOOK._parse_payload(stream, self.root)
        self.assertEqual(parsed["hook_event_name"], "PreCompact")
        self.assertEqual(parsed["trigger"], "manual")
        self.assertNotIn("turn_id", parsed)
        self.assertNotIn("model", parsed)
```

- [ ] **Step 2: 跑测试,确认失败**

Run:
```bash
cd /Users/bilibili/personal/note && python3 -m pytest .Codex/hooks/tests/test_precompact_snapshot.py::PreCompactSnapshotTest::test_parse_payload_accepts_minimal_payload_without_optional_fields -v
```
Expected: FAIL,`SnapshotError: PreCompact 输入缺少字段：model, turn_id`(由 `_parse_payload` 抛出)。

- [ ] **Step 3: 最小实现:把 `turn_id`/`model` 降为可选**

在 `.Codex/hooks/precompact_snapshot.py:30-38`,把:

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

改为:

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

`_parse_payload` 的缺失字段校验逻辑(`missing = sorted(REQUIRED_INPUT_KEYS.difference(payload))`)无需改动——它现在只校验 5 个必需字段。Codex payload 仍含 `turn_id`/`model`,降为可选对 Codex 无副作用。

- [ ] **Step 4: 跑新测试,确认通过**

Run:
```bash
cd /Users/bilibili/personal/note && python3 -m pytest .Codex/hooks/tests/test_precompact_snapshot.py::PreCompactSnapshotTest::test_parse_payload_accepts_minimal_payload_without_optional_fields -v
```
Expected: PASS。

- [ ] **Step 5: 跑 precompact 全套测试,确认无回归**

Run:
```bash
cd /Users/bilibili/personal/note && python3 -m pytest .Codex/hooks/tests/test_precompact_snapshot.py -v
```
Expected: 全部 PASS(原 6 个方法 + 新 1 个)。`test_sample_input_matches_official_required_fields` 仍通过,因为 `precompact-input.json` 样本是 `REQUIRED_INPUT_KEYS` 的超集。

- [ ] **Step 6: 提交**

```bash
cd /Users/bilibili/personal/note && git add .Codex/hooks/precompact_snapshot.py .Codex/hooks/tests/test_precompact_snapshot.py
```

注意:`.Codex/` 在 `.gitignore` 内(`copilot/` / `.Codex/`),`git add` 会被忽略。需确认:

```bash
git check-ignore .Codex/hooks/precompact_snapshot.py
```

若输出该路径(被忽略),则本任务**不产生 git 提交**,改动只存于本地工作树(与既有 `.Codex/` 基础设施一致,均不入库)。记录该事实,跳到下一任务。

若未被忽略(规则有变),提交信息:
```
fix(hooks): accept PreCompact payload without codex-only fields
```

---

## Task 2: 根 AGENTS.md 工具中立化

**Files:**
- Modify: `AGENTS.md:5,9,11,22,52`

本任务是文档改写,不适用 TDD;验证用 `rg` 检索命中数归零。

- [ ] **Step 1: 改第 5 行(全局继承引用)**

`AGENTS.md:5`,把:

```
本文件只规定本毕业论文仓库特有的长期规则。身份、简体中文沟通、通用写作、规划、技能路由、执行、验证和交付格式继承自 `~/.codex/AGENTS.md`，不在此重复。
```

改为:

```
本文件只规定本毕业论文仓库特有的长期规则。身份、简体中文沟通、通用写作、规划、技能路由、执行、验证和交付格式继承自全局规则（Codex `~/.codex/AGENTS.md` 与 Claude Code `~/.claude/CLAUDE.md`），不在此重复。
```

- [ ] **Step 2: 改第 9 行**

`AGENTS.md:9`,把:

```
- Codex 启动时从项目根走到当前工作目录；每层只使用 `AGENTS.override.md`、`AGENTS.md` 或已配置回退文件中的第一个。离当前目录更近的规则优先。
```

改为:

```
- 编码代理从项目根走到当前工作目录加载规则；每层只使用 `AGENTS.override.md`、`AGENTS.md` 或已配置回退文件中的第一个。离当前目录更近的规则优先。
```

- [ ] **Step 3: 改第 11 行**

`AGENTS.md:11`,把:

```
- Codex 不会因为随后编辑了子目录文件而动态重新发现规则。从仓库根启动时，只要任务涉及下列子域，必须在分析或编辑前主动**完整读取**对应局部文件；任务横跨多个子域时逐一读取。
```

改为:

```
- 代理不会因后续编辑子目录文件而动态重载规则。从仓库根启动时，只要任务涉及下列子域，必须在分析或编辑前主动**完整读取**对应局部文件；任务横跨多个子域时逐一读取。
```

- [ ] **Step 4: 改第 22 行**

`AGENTS.md:22`,把:

```
- 不得假定 Codex 支持 Claude Code 的斜杠命令；只使用当前环境实际提供的技能、代理和可复现命令。
```

改为:

```
- 不得假定一个代理支持另一个代理的斜杠命令；只使用当前环境实际提供的技能、代理和命令。
```

- [ ] **Step 5: 改第 52 行**

`AGENTS.md:52`,把:

```
- 根目录以 `.ignore` 控制 `rg` 与已解析的 `fd`/`fdfind` 遍历命令的默认搜索噪声；在本机 Codex 明确验证支持前，不得依赖或新建 `.codexignore`。
```

改为:

```
- 根目录以 `.ignore` 控制 `rg` 与已解析的 `fd`/`fdfind` 遍历命令的默认搜索噪声；在本机明确验证支持前，不得依赖或新建 `.codexignore`。
```

- [ ] **Step 6: 验证 Codex 专属措辞归零**

Run:
```bash
cd /Users/bilibili/personal/note && rg -n "Codex 启动时|\.codexignore|Codex 不会因为|不得假定 Codex 支持|Codex 机制描述" AGENTS.md
```
Expected: 无输出(命中数 0)。

- [ ] **Step 7: 提交**

```bash
cd /Users/bilibili/personal/note && git add AGENTS.md && git commit -m "docs(agents): rewrite codex-specific wording to tool-neutral"
```

---

## Task 3: 根 CLAUDE.md 适配段与文档目录约定

**Files:**
- Modify: `CLAUDE.md`(根,"Claude Code 适配说明"整段)

- [ ] **Step 1: 重写"适配说明"段**

`CLAUDE.md` 中,把现有"## Claude Code 适配说明"整段(从该标题到文件末尾)替换为:

```
## Claude Code 适配说明

- 本文件是 Claude Code 的根级入口；`AGENTS.md` 是本仓库规则唯一来源，工具中立。
- 每个受管子目录的 `CLAUDE.md` 通过 `@AGENTS.md` 导入同目录 `AGENTS.md`。Claude Code 读取该目录内文件时，按目录级原生加载机制生效。
- 规则源 `AGENTS.md` 由 Codex 与 Claude Code 共享；基础设施（`.Codex/hooks/`、`.Codex/docs/`、`.Codex/tools/`）亦共享，各工具只在自己的配置文件里注册引用，不复制脚本。
- 当两个代理的原生加载行为与 `AGENTS.md` 描述不同，以各自实际加载方式为准；研究边界、数据证据、凭据保护、验证和写入规则仍完整有效。
- 使用 `/memory` 核对本会话实际加载的 `CLAUDE.md` 与规则文件；规则是行为指引，权限、沙箱和工具限制以 Claude Code 设置为准。
- **文档目录约定**：本仓库过程文档（计划、笔记、审计、过程记录）放 `.Codex/docs/`（共享工作记忆，gitignored）；入库设计规约放 `.claude/docs/`。此约定覆盖全局规则中"`.claude/docs/`"的默认指向。
```

保留文件顶部的 `# Claude Code 项目规则` 标题与 `@AGENTS.md` 导入行不动。

- [ ] **Step 2: 验证导入行 intact**

Run:
```bash
cd /Users/bilibili/personal/note && head -5 CLAUDE.md
```
Expected: 前两行是 `# Claude Code 项目规则` 与空行,第四行附近有 `@AGENTS.md`。

- [ ] **Step 3: 提交**

```bash
cd /Users/bilibili/personal/note && git add CLAUDE.md && git commit -m "docs(claude): update adapter section and doc dir override"
```

---

## Task 4: .claude/settings.json 注册钩子

**Files:**
- Modify: `.claude/settings.json`

- [ ] **Step 1: 写入目标内容**

把 `.claude/settings.json` 整体替换为:

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

- [ ] **Step 2: 校验 JSON 合法**

Run:
```bash
cd /Users/bilibili/personal/note && python3 -m json.tool .claude/settings.json > /dev/null && echo OK
```
Expected: `OK`。

- [ ] **Step 3: prettier_guard 烟测(应 deny)**

Run:
```bash
cd /Users/bilibili/personal/note && printf '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"npx prettier --write foo.js"}}' | python3 .Codex/hooks/prettier_guard.py
```
Expected: 输出 JSON 含 `"permissionDecision":"deny"` 与 `[P0-NO-PRETTIER]`。

- [ ] **Step 4: prettier_guard 反例烟测(无 pretier → 无输出)**

Run:
```bash
cd /Users/bilibili/personal/note && printf '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 .Codex/hooks/prettier_guard.py; echo "exit=$?"
```
Expected: 无 JSON 输出,`exit=0`(脚本对非 prettier 命令返回 None,main 退出 0)。

- [ ] **Step 5: precompact_snapshot 烟测(用临时项目根,不触真实恢复文档)**

Run:
```bash
cd /Users/bilibili/personal/note
TMP=$(mktemp -d)
mkdir -p "$TMP/.codex" "$TMP/output"
printf '{"enabled":true,"active_plan":""}\n' > "$TMP/.codex/precompact_snapshot.json"
printf '# 恢复\n' > "$TMP/output/开题改进交接文档.md"
printf '# 总控\n' > "$TMP/output/第一创新点实验总控.md"
printf '{"hook_event_name":"PreCompact","session_id":"smoke","transcript_path":"/tmp/x","cwd":"%s","trigger":"manual"}\n' "$TMP" | python3 .Codex/hooks/precompact_snapshot.py --project-root "$TMP"
echo "---"
rg -c PRECOMPACT_SNAPSHOT "$TMP/output/开题改进交接文档.md"
rm -rf "$TMP"
```
Expected: 第一段输出 `{"continue":true,"suppressOutput":true}`;第二段输出 `2`(START+END 两行)。

- [ ] **Step 6: 提交**

```bash
cd /Users/bilibili/personal/note && git add .claude/settings.json && git commit -m "feat(claude): register shared codex hooks in settings.json"
```

---

## Task 5: 最终验证

**Files:** 无改动,仅验证。

- [ ] **Step 1: 钩子全套测试**

Run:
```bash
cd /Users/bilibili/personal/note && python3 -m pytest .Codex/hooks/tests/ -v
```
Expected: 全部 PASS。记录失败项(若有)。

- [ ] **Step 2: 规则中立化归零校验**

Run:
```bash
cd /Users/bilibili/personal/note && rg -n "Codex 启动时|\.codexignore|Codex 不会因为|不得假定 Codex 支持|Codex 机制描述" AGENTS.md
```
Expected: 无输出。

- [ ] **Step 3: prettier_guard 烟测复跑**

复跑 Task 4 Step 3,确认 `deny`。

- [ ] **Step 4: precompact_snapshot 烟测复跑**

复跑 Task 4 Step 5,确认 `continue:true` 与快照写入。

- [ ] **Step 5: 手动集成验证(需新会话)**

在**新的** Claude Code 会话中触发 `/compact`,然后:
```bash
cd /Users/bilibili/personal/note && rg -c "PRECOMPACT_SNAPSHOT_START" output/开题改进交接文档.md output/第一创新点实验总控.md
```
Expected: 两文件各输出 `1`(快照区块被 Claude Code 的 PreCompact 钩子刷新)。

若手动验证未在本轮执行,标记为"待用户在真实会话验证",不阻塞提交。

- [ ] **Step 6: Codex 可逆性核验(只读)**

确认 `~/.codex/config.toml` 与 `.Codex/hooks.json` 在本轮**未被修改**:
```bash
cd /Users/bilibili/personal/note && git status --short ~/.codex/config.toml .Codex/hooks.json 2>/dev/null; rg -n "prettier_guard|precompact_snapshot" .Codex/hooks.json
```
Expected: 两个文件均不在 `git status` 改动列表(前者在 home,后者 gitignored);`hooks.json` 仍引用两个脚本。Codex 侧切换回可用。

---

---

## Task 6: MCP 配置迁移(github、openaiDeveloperDocs、zotero env)

**Files:**
- Modify: `~/.claude/settings.json`(全局 home,非 git 跟踪)
- Modify: `~/.zshrc`(全局 home,非 git 跟踪)
- 读源: `~/.codex/config.toml`(取 literal token 值,不回显、不入计划文档)

**安全边界**:带凭据的字段**只写入 `~/.zshrc`**(全局 home,非 git 跟踪);`~/.claude/settings.json` 与计划文档**只出现 `${VAR}` 引用,不落明文**。Claude Code 从 shell 继承 env,`GitLab` 条目 `"Bearer ${GITLAB_TOKEN}"` 已证实 MCP `headers` 支持 `${VAR}` 展开;stdio MCP `env` 同样用 `${VAR}` 引用。

- [ ] **Step 1: 把全部 token export 到 `~/.zshrc`**

`GITLAB_TOKEN` 已在 `~/.zshrc` export。读取 `~/.codex/config.toml`,把下列 token 追加 export 到 `~/.zshrc` 末尾(镜像既有 `export GITLAB_TOKEN=...` 模式;此处不回显值):

```
export GITHUB_PERSONAL_ACCESS_TOKEN=<从 ~/.codex/config.toml [shell_environment_policy.set] 复制>
export ZOTERO_API_KEY=<从 ~/.codex/config.toml [mcp_servers.zotero.env] 复制>
export ZOTERO_LIBRARY_ID=21101662
export ZOTERO_LIBRARY_TYPE=user
export UNPAYWALL_EMAIL=<从 ~/.codex/config.toml [mcp_servers.zotero.env] 复制>
export UNSAFE_OPERATIONS=all
```

追加后:
```bash
source ~/.zshrc && for v in GITHUB_PERSONAL_ACCESS_TOKEN ZOTERO_API_KEY ZOTERO_LIBRARY_ID UNPAYWALL_EMAIL; do echo "$v 长度: ${#v}"; done
```
Expected: 各变量输出非 0 长度(确认 env 已注入,不回显值)。

- [ ] **Step 2: 在 `~/.claude/settings.json` mcpServers 加 github 与 openaiDeveloperDocs**

在 `~/.claude/settings.json` 的 `"mcpServers"` 对象内,追加两个键(与既有 `zotero`、`streamable-mcp-server` 并列):

```json
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    },
    "openaiDeveloperDocs": {
      "type": "http",
      "url": "https://developers.openai.com/mcp"
    }
```

保留既有 `streamable-mcp-server`、`zotero` 两条不动。

- [ ] **Step 3: 校验 JSON 合法**

```bash
python3 -m json.tool ~/.claude/settings.json > /dev/null && echo OK
```
Expected: `OK`。

- [ ] **Step 4: zotero env 改用 `${VAR}` 引用**

`~/.claude/settings.json` 中 `mcpServers.zotero` 改为全部用 `${VAR}` 引用 zshrc 已 export 的变量,不落明文:

```json
    "zotero": {
      "command": "zotero-mcp",
      "args": ["serve"],
      "env": {
        "ZOTERO_API_KEY": "${ZOTERO_API_KEY}",
        "ZOTERO_LIBRARY_ID": "${ZOTERO_LIBRARY_ID}",
        "ZOTERO_LIBRARY_TYPE": "${ZOTERO_LIBRARY_TYPE}",
        "UNPAYWALL_EMAIL": "${UNPAYWALL_EMAIL}",
        "UNSAFE_OPERATIONS": "${UNSAFE_OPERATIONS}",
        "NO_PROXY": "localhost,127.0.0.1"
      }
    }
```

- [ ] **Step 5: 不迁移的 MCP(记录,不动)**

codex 的 `computer-use`(codex 已禁用)、`node_repl`(`/Applications/ChatGPT.app` 专属二进制)、`huggingface`(已在 `~/.claude.json` 项目级为 `hf-mcp-server`)、`GitLab`/`ast-grep`(已在 `~/.claude.json`)——本轮不处理。

- [ ] **Step 6: 不提交**

`~/.claude/settings.json` 与 `~/.zshrc` 均在 home 目录,非仓库跟踪,无 `git commit`。

---

## Task 7: 禁用 skills 与可选 plugin 对齐

**Files:**
- Rename: `~/.claude/skills/webapp-testing` → `~/.claude/skills/webapp-testing.disabled`
- Rename: `~/.claude/skills/ui-ux-pro-max` → `~/.claude/skills/ui-ux-pro-max.disabled`
- Rename: `~/.claude/skills/summary` → `~/.claude/skills/summary.disabled`
- Modify(可选): `~/.claude/settings.json` 的 `enabledPlugins."gopls-lsp@claude-plugins-official"`

Claude Code 的 skill 禁用机制:**目录名加 `.disabled` 后缀**(已由 `web-design-reviewer.disabled` 证实)。codex `[[skills.config]] enabled=false` 中 15 条,可迁的是 4 个用户级 skill(`web-design-reviewer` 已禁用,余 3 个本任务处理);codex 内置 browser/computer-use/template skill 共 9 条在 Claude 不存在,no-op;document-skills 的 `pptx`/`xlsx` 子 skill 在插件缓存内,重命名会被插件更新覆盖,**本轮不处理**(列为局限)。

- [ ] **Step 1: 禁用 3 个用户级 skill**

```bash
mv ~/.claude/skills/webapp-testing ~/.claude/skills/webapp-testing.disabled
mv ~/.claude/skills/ui-ux-pro-max ~/.claude/skills/ui-ux-pro-max.disabled
mv ~/.claude/skills/summary ~/.claude/skills/summary.disabled
```

- [ ] **Step 2: 验证禁用生效**

```bash
ls -d ~/.claude/skills/webapp-testing.disabled ~/.claude/skills/ui-ux-pro-max.disabled ~/.claude/skills/summary.disabled ~/.claude/skills/web-design-reviewer.disabled
```
Expected: 4 个 `.disabled` 目录均列出。新会话的可用 skills 列表里这 4 个将不再以可用形式出现。

- [ ] **Step 3: (可选)对齐 gopls-lsp 插件禁用状态**

codex 把 `gopls-lsp@claude-plugins-official` 禁用,Claude 当前 `enabled=true`。本仓库有 Go 规则(`~/.claude/rules/go-*.md`),**保留启用**对 Go 工作更有利。若要严格对齐 codex,在 `~/.claude/settings.json` 的 `enabledPlugins` 把:

```json
    "gopls-lsp@claude-plugins-official": true
```

改为 `false`。**默认不改**(保留启用),仅记录分歧。

- [ ] **Step 4: 不提交**

`~/.claude/skills/` 与 `~/.claude/settings.json` 均在 home,非仓库跟踪,无 `git commit`。

---

## 验收清单(全部 ✅ 后视为迁移落地完成)

- [ ] Task 1: precompact_snapshot 补丁 + 新测试通过 + 既有测试无回归
- [ ] Task 2: AGENTS.md 5 行改写,Codex 专属措辞命中数 0
- [ ] Task 3: CLAUDE.md 适配段 + 文档目录约定覆盖行
- [ ] Task 4: settings.json 注册双钩子,JSON 合法,双烟测通过
- [ ] Task 5: 钩子全套测试 PASS,规则中立化归零,双烟测复跑通过
- [ ] Task 6: github/openaiDeveloperDocs MCP 加入,zshrc token export,JSON 合法
- [ ] Task 7: 3 个用户级 skill 重命名 `.disabled`,gopls-lsp 分歧已记录
- [ ] (手动)新会话 `/mcp` 确认 `github`、`openaiDeveloperDocs`、`zotero`、`GitLab`、`ast-grep` 均已连接;`/compact` 触发快照写入两份恢复文档
- [ ] (只读)Codex 侧 config.toml / hooks.json 未变,可切回

---

## 已知局限(沿用设计 §7)

1. `.Codex/` 命名不中立,靠文档约定体现中立;phase 2 可重命名。
2. `precompact_snapshot.py` 硬编码 `.codex/`(小写),macOS 大小写不敏感可过;Linux 大小写敏感环境需统一。
3. `project_policy_guard.py` 与 `server_launcher_guard.py` 保持休眠,未接入 Claude Code;将来启用需改工具名(`Agent`/`spawn_agent` → `Task`)并解禁 `main()`。
4. 全局层(`~/.codex/`、`~/.claude/`)不在本计划范围。
5. `document-skills` 子 skill(`pptx`/`xlsx`)的禁用依赖插件缓存目录重命名,会被插件更新覆盖,本轮不处理;codex 内置 browser/computer-use/template skill 共 9 条在 Claude 不存在,no-op。
6. stdio MCP `env` 的 `${VAR}` 展开若不生效(新会话 `/mcp` 中 zotero 报鉴权失败即征兆),回退方案:把对应变量值直接写入 `~/.claude/settings.json` 的 zotero env(home 非跟踪,用户已许可硬编码),或用 wrapper 脚本 `source ~/.zshrc && exec zotero-mcp serve`。
