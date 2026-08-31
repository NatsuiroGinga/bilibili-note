# 关键词与向量混合文献检索

该工具只索引 `wiki/papers/**/*.md`。它不会读取 PDF，不会修改笔记、原件或 Zotero。

## `rrf_constant = 5`（2026-08-31 由实验改定，原值 60）

按仓库魔法数字门禁登记依据：

| 项 | 内容 |
| --- | --- |
| 用途与值 | 倒数排名融合（RRF）的平滑常数，`config.json` 的 `rrf_constant`，由 `60` 改为 `5` |
| 文献依据 | **无直接文献给出该值。** `2510.16393`（wiki 笔记：学习排序与稠密表示混合级联）只提供**健全性判据**：融合结果须同时高于两个单通道，该文用 LambdaMART 学习融合、未研究 RRF 常数；`2505.14432` 有 RRF 融合的正面先例但同样未研究常数取值 |
| 统计推导 | RRF 得分为 `Σ 1/(k + rank)`。`k` 越大，各名次的贡献越趋同，强通道的高名次优势被压平；本库两通道强弱悬殊（向量命中率 `0.3250` 对词法 `0.1750`），大 `k` 会让弱通道拖累强通道 |
| 数据诊断 | 200 条中立跨语言查询（论文 PDF 英文摘要检索中文笔记）上扫描：`k=5` 与 `k=10` 同为命中率 `0.3300`，`k=20` 为 `0.3000`，`k=60` 为 `0.2700`，`k=120` 为 `0.2600`。MRR 在 `k=5` 最高（`0.1803`）。含噪版查询上独立扫描方向一致（`k=5` 为 `0.3700`、`k=60` 为 `0.3000`） |
| 健全性核验 | 仅 `k≤10` 时 hybrid（`0.3300`）同时高于 vector（`0.3250`）与 lexical（`0.1750`），满足 `2510.16393` 的判据；`k=60` 的 `0.2700` 低于 vector，即融合有害 |
| 适用边界 | 结论建立在本库当前语料（510 篇同领域中文笔记）与 `multilingual-e5-small` 上。更换模型、语料或两通道强弱关系反转时须重新扫描 |
| 是否接触最终目标标签 | 否。评测查询由 `raw/` 论文 PDF 摘要构造，与 LSPR 数据及论文实验完全无关 |
| 核验状态 | 已核验。两组独立查询同向，`k=5` 与 `k=10` 在命中率上并列，取 `k=5` 因其 MRR 更高 |

完整评测过程见 `.Codex/docs/RWKV/2026-08-28-文献检索精度评测与改进方案.md` 附录 A 与 B。

**回归检查（2026-08-31）：`rrf_constant` 60→5 对多文档主题查询零副作用。**
`evaluate.py` 的命中率与 MRR 只看「任一相关文档是否进入 Top-k」，不反映
`method_neighbor` 类查询（同一查询有 2–8 篇相关笔记）真正关心的**多文档召回率**。
补测 `evaluation_queries_real.json` 中 `≥2` 篇相关路径的 12 条查询：

| `rrf_constant` | hybrid 多文档平均召回率 | 最低召回率 |
| ---: | ---: | ---: |
| `60`（旧值） | `0.8970` | `0.5000` |
| `5`（现值） | `0.8970` | `0.5000` |

两者逐位相同。改动只在跨语言场景带来提升（附录 D.6.3），对主要使用场景
（中文主题查询）零回归。

**改 `config.json` 后必须重建索引才生效。** `cli.py:152` 的
`actual_config = _index_config(connection, config)` 会优先采用**索引 metadata 里存的配置**，
只有索引未存时才回退到 `config.json`。这是有意设计——保证查询与建索引时的分块、模型等参数一致——
但代价是改任何配置项（包括只影响查询期的 `rrf_constant`）都要 `build` 一次。
判断是否生效看 `status --json` 输出的 `config` 段，那读的就是索引里的值。
2026-08-31 曾因此误判：改完 `config.json` 直接查询，实际仍在用旧的 `rrf_constant = 60`。

## `chunk_title_prefix`（2026-08-31 新增，默认 `true`，未改变默认行为）

`config.json` 的开关，控制是否把「笔记标题＋小节标题」拼进每个分块开头
（`documents.py:chunk_note`）。加它是为了诊断「标题在同一篇笔记的每个分块里重复出现，
是否构成过度表征、压低检索质量」这一假设——道理上类似已排除的 `INDEX.md` 超额表征问题。

**实测结论：否决，对当前评测集无实质影响。** 200 条中立跨语言查询上对比：

| 配置 | lexical 命中/MRR | vector 命中/MRR | hybrid 命中/MRR |
| --- | --- | --- | --- |
| `chunk_title_prefix=true`（默认） | `0.1750`/`0.1408` | `0.3200`/`0.1970` | `0.3300`/`0.1776` |
| `chunk_title_prefix=false` | `0.1750`/`0.1392` | `0.3200`/`0.1509` | `0.3150`/`0.1493` |

命中率完全相同，关闭后 MRR 反而略降。**保持默认 `true`，不建议关闭。**

这不代表标题重复毫无危害——它的实际影响体现在「查询本身包含笔记标题词」的场景
（例如由 `key_finding` 改写的中文查询，标题词天然被保留），与本节验证的
「分块内容被标题稀释」是两个不同问题，不要混用这个开关的实测结果去论证前者。
完整对照见 `.Codex/docs/RWKV/2026-08-28-文献检索精度评测与改进方案.md` 附录 D.6.1。

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
