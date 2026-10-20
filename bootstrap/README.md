# bootstrap：让新机器只靠 GitHub 就能恢复工作环境

> **背景**：2026-10-20 用户要求「换一台新机器只靠 GitHub 能继续任务」。
> 核查发现 git 里只有**研究资产**，缺**运行环境**。本目录补齐其中可搬运的部分，
> 并如实列出**搬不走的部分**。

---

## 一、本目录包含什么（`~/.claude` 的可搬运部分）

| 内容 | 来源 | 大小 | 为什么必须搬 |
| --- | --- | ---: | --- |
| `claude/skills/` | `~/.claude/skills/` | 7.2 MB / 848 文件 | **本地自建技能**（results-analysis、daily-coding、paper-self-review、ml-paper-writing、citation-verification、chatgpt-handoff 等），无法从公开来源重装 |
| `claude/rules/` | `~/.claude/rules/` | 28 KB / 7 文件 | 全局规则入口 |
| `claude/agents/` | `~/.claude/agents/` | 60 KB / 6 文件 | 代理定义 |
| `claude/commands/` | `~/.claude/commands/` | 420 KB / 66 文件 | 斜杠命令 |
| `claude/memory/` | `~/.claude/projects/<本项目>/memory/` | 小 | **跨会话上下文的核心**（33 个记忆文件） |
| `claude/CLAUDE.md`、`claude/AGENTS.md` | `~/.claude/` | 20 KB | 用户级全局规则 |
| `claude/settings.json.reference` | `~/.claude/settings.json` | 6 KB | **仅作参考**，不自动覆盖 |

**恢复**：`bash bootstrap/restore.sh`（会先备份现有项）。见脚本头部说明。

**已做的凭据扫描**：本目录全部文件扫过 `api_key|token|secret|password|sk-|ghp_` 模式，
命中项均为**占位符或类型注解**（`sk-abc123`、`api_key: Option`、`apiKey = null`、`API_KEY=your_k`），**无真实凭据**。

---

## 二、本目录**不**包含什么（以及为什么）

| 内容 | 大小 | 为什么不在 git | 新机器怎么办 |
| --- | ---: | --- | --- |
| **插件** | 54 MB | 可从 marketplace 重装 | 见 §三 |
| **聊天记录**（`~/.claude/projects/*.jsonl`） | **896 MB**（本项目） | 体积过大，且含未脱敏对话 | 见 §四 |
| `~/.codex/` | **6.3 GB** | 状态、日志、备份 | 只需重设 API 配置与身份；研究规则在仓库 `.Codex/` 内 |
| **数据集**（LAMDA Baseline 视图） | 341 MB | 可再生 | 跑 `scripts/download_lamda_baseline.py`，见 §五 |
| **Python 环境** | — | 可重建 | 见 §六 |

---

## 三、插件重装清单

当前已安装的 marketplace 与插件（2026-10-20 实测）：

**marketplaces**：`anthropic-agent-skills`、`claude-plugins-official`、`fullstack-dev-skills`、`obsidian-skills`、`rust-skills`

**plugins**：`anthropic-agent-skills`、`claude-plugins-official`、`mcpmarket-me`、`rust-skills`

**⇒ 在新机器上按上表重新添加 marketplace 并安装插件即可。本仓库的规则与技能**不依赖**插件内容**——`bootstrap/claude/skills/` 已包含工作流实际用到的技能。

---

## 四、聊天记录（**搬不走，也不建议搬**）

**事实**：本项目会话记录 `~/.claude/projects/-Users-bilibili-personal-note/` 共 **896 MB**。
Claude Code 的 `--resume` 依赖该目录下的 `*.jsonl`，且目录名由**工作目录路径转义**决定。

**⇒ 两点结论：**

1. **不能进 git**：体积远超合理仓库规模，且对话内容未脱敏（可能含路径、片段代码、凭据线索）。
2. **换了机器路径后，`--resume` 本身也需要对应目录名**——把 jsonl 搬过去还要保证路径一致，否则 Claude Code 认不到。

**替代方案（本项目实际采用的）**：

- **`claude/memory/`（33 个记忆文件）** —— 已随本包同步，这是**跨会话上下文的提炼**（用户偏好、反复纠正过的错误、项目约束）。
- **`.Codex/docs/2026-10-15-上下文压缩恢复/` 的六份检查点** —— 已随仓库同步，记录每次压缩前的完整状态。
- **`.Codex/docs/LAMDA/` 的路线总控与恢复卡** —— 恢复协议的正式入口。

**⇒ 新机器靠「记忆 ＋ 检查点 ＋ 恢复卡」重建上下文，而不是靠原始聊天记录。** 若要保留原始记录，请另存到私有存储（如加密云盘），**不要进这个仓库**。

---

## 五、数据集

**不入库**（`.gitignore` 已排除 `runs/data-raw/`）。重下载：

```bash
/opt/miniconda3/envs/rwkv/bin/python \
  thesis/experiments/llm_probe/scripts/download_lamda_baseline.py
```

脚本 docstring 记录：仓库 `IQSeC-Lab/LAMDA`、**revision `ad9614bdd5556767f97ced2fce797c2f06408ebf`**、DOI `10.57967/hf/5563`；只取 `Baseline/**` 与 `README.md`。
落点 `<仓库根>/thesis/experiments/llm_probe/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767`，可用 `LAMDA_DATA_ROOT` 覆盖。

---

## 六、Python 环境

本仓库规则规定：**本机实验一律用 `/opt/miniconda3/envs/rwkv/bin/python`**（Python 3.14、torch 2.12）。
新机器需重建该环境（或接受版本差异，并在运行日志里如实记录）。

另有两个 uv 项目：

- 文献混合检索：`uv run --project scripts/literature_search --locked ...`
- 论文图件：`uv run --project "thesis/figures/第N章" ...`

---

## 七、恢复后必须做的验证

1. `bash bootstrap/restore.sh` 后重启 Claude Code，确认技能可被 `Skill` 工具列出
2. 跑一次基线复现（不需要 GPU 权限，约 2 分钟）：
   ```bash
   LAMDA_DATA_ROOT=<上面下载的路径> \
   /opt/miniconda3/envs/rwkv/bin/python \
     thesis/experiments/llm_probe/tools/ch3_lamda_domain_il_e4.py \
     --strategy expreplay --memory 200 --buffer-scheme quota --reuse-scheme deficit --buffer-repeat 2
   ```
   **期望末年 2025 的 12 年平均 F1 = `0.8170`。对不上说明环境或数据不对，不要继续。**
