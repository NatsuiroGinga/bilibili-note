# 关键词与向量混合文献检索

该工具只索引 `wiki/papers/**/*.md`。它不会读取 PDF，不会修改笔记、原件或 Zotero。

## 索引默认行为（2026-08-28 落地，见下方评测报告）

以下两项是 `documents.py:load_notes` 的默认行为，非可选项：

1. **排除 MOC 导航页**：文件名字面量为 `INDEX.md` 的笔记不进入索引（当前 15 篇）。
   依据：25 条真实查询评测中，这批页面占语料 2.9%，却占据 40% 的查询第 1 名命中，
   超额表征约 14 倍——正文是论文标题清单，几乎匹配所有主题查询的字符三元组。
2. **索引 frontmatter 的人工标注**：`tags`、`key_finding`、`venue`、`authors`、`year`、`aliases`
   六个字段被渲染成一个「## 条目元数据」小节并入正文（不改变 `parse_frontmatter` 对其余调用方的
   返回契约），走既有分块通路参与词法与向量检索。此前这些字段随整段 frontmatter 被剥离丢弃，
   全库 0 命中，覆盖率却达 tags 100%、key_finding 96.6%。

两项合计（对照报告中的 V3）把词法通道从 `Recall@5 0.8575 / MRR 0.7933 / nDCG@10 0.7958`
提到 `Recall@5 0.9332 / MRR 1.0000 / nDCG@10 0.9657`（25 条真实查询集，见
`scripts/literature_search/evaluation_queries_real.json`）。完整评测方法、失败模式分析与
被否决的备选方案（分块聚合改 Top-N 求和、排除重定向页）见
`.Codex/docs/RWKV/2026-08-28-文献检索精度评测与改进方案.md` 与
`.Codex/docs/RWKV/2026-08-28-检索V3改进落地报告.md`。

## 环境

**唯一受支持的入口是 uv 项目环境，从仓库根目录执行：**

```bash
uv run --project scripts/literature_search --locked python -m scripts.literature_search <子命令>
```

该环境由 `scripts/literature_search/pyproject.toml` 与 `uv.lock` 锁定，
词法与向量通道所需依赖全部在内（实测 `numpy 2.0.2`、`sentence-transformers 5.1.1`）。
首次执行会安装依赖（含约 106 MiB 的 torch），之后命中缓存。

**不要使用下列入口，它们都会失败或给出误导性结果**（2026-08-31 实测）：

| 入口 | 实际状态 |
| --- | --- |
| `.cache/literature-search/venv/bin/python` | 历史遗留，依赖不完整，连 `numpy` 都没有，导入即失败 |
| 系统 `python3` | 是否有 `numpy` 取决于机器，且一定没有向量后端 |
| conda 环境（如 `/opt/miniconda3/envs/rwkv`） | 有 `numpy` 与 `torch`，但没有 `sentence-transformers`，`--mode hybrid` 直接报错 |

模型使用 `intfloat/multilingual-e5-small` 固定修订，首次完整构建会下载约 488 MB 到
Hugging Face 标准缓存。可用 `--model-cache` 指定缓存目录，或在缓存准备好后加 `--offline` 禁止网络。

## 命令

以下命令一律从仓库根目录执行。为省略重复，先设一个别名：

```bash
alias litsearch='uv run --project scripts/literature_search --locked python -m scripts.literature_search'
```

```bash
# 完整构建（含向量通道）
litsearch build

# 只构建中文词法索引（跳过向量编码，构建快但 --mode hybrid 不可用）
litsearch build --lexical-only

# 查询与状态
litsearch query "正常性漂移异常检测" --mode hybrid --top-k 10
litsearch status --json

# 冻结对照集
litsearch evaluate
```

## 在线候选

`query` 使用统一范围：

- `--scope local`：只返回本地全文笔记证据，默认值。
- `--scope online`：只返回外部题录或摘要候选及来源状态。
- `--scope all`：分区返回本地证据与外部候选，二者不混排分数。

```bash
litsearch query "normality shift anomaly detection" --scope all --mode lexical --json
```

可选环境变量只从进程环境读取，不写入索引或输出：

- `OPENALEX_API_KEY`：启用 OpenAlex `search.semantic`；缺失时尝试普通 `search` 并标记降级。
- `SEMANTIC_SCHOLAR_API_KEY`：以 `x-api-key` 头发送；缺失时使用公共接口。
- `CROSSREF_MAILTO`：进入 Crossref 礼貌池。

每次查询对每个来源至多发出一次请求。HTTP 403、429、超时、网络或 JSON 错误都会记录为来源级失败；`scope=all` 仍返回本地结果。所有在线结果均标记为未核全文候选，不自动写入 `raw/`、`wiki/` 或 Zotero。

macOS 受限沙箱若禁止默认字节码缓存，可在命令前设置：

```bash
PYTHONPYCACHEPREFIX=/tmp/literature-search-pycache
```

## 可再生制品

- 默认索引：`.cache/literature-search/index.sqlite3`
- 默认模型缓存：`~/.cache/huggingface/hub`
- 清理索引：删除上述 SQLite 文件；下次 `build` 会原子重建。
- 清理模型：使用 `hf cache list` 确认条目，再用 `hf cache rm model/intfloat/multilingual-e5-small --dry-run` 预检。
- 索引和模型缓存都不应提交 Git。

`status` 会重新计算笔记来源清单哈希（当前 510 篇，已排除 15 篇 `INDEX.md` 导航页）；
`stale=true` 表示必须重建。
