# 关键词与向量混合文献检索

该工具只索引 `wiki/papers/**/*.md`。它不会读取 PDF，不会修改笔记、原件或 Zotero。

## 环境

词法索引只需要仓库现有 Python 与 NumPy。完整向量索引建议建立隔离环境：

```bash
uv venv .cache/literature-search/venv --python 3.11
uv pip install --python .cache/literature-search/venv/bin/python \
  -r scripts/literature_search/requirements.txt
```

模型使用 `intfloat/multilingual-e5-small` 固定修订，首次完整构建会下载约 488 MB 到 Hugging Face 标准缓存。可用 `--model-cache` 指定缓存目录，或在缓存准备好后加 `--offline` 禁止网络。

## 命令

```bash
# 完整构建
.cache/literature-search/venv/bin/python -m scripts.literature_search build

# 不安装向量依赖时先构建中文词法索引
python3 -m scripts.literature_search build --lexical-only

# 查询与状态
.cache/literature-search/venv/bin/python -m scripts.literature_search query \
  "正常性漂移异常检测" --mode hybrid --top-k 10
python3 -m scripts.literature_search status --json

# 冻结对照集
.cache/literature-search/venv/bin/python -m scripts.literature_search evaluate
```

## 在线候选

`query` 使用统一范围：

- `--scope local`：只返回本地全文笔记证据，默认值。
- `--scope online`：只返回外部题录或摘要候选及来源状态。
- `--scope all`：分区返回本地证据与外部候选，二者不混排分数。

```bash
python3 -m scripts.literature_search query \
  "normality shift anomaly detection" --scope all --mode lexical --json
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

`status` 会重新计算 507 篇笔记的来源清单哈希；`stale=true` 表示必须重建。
