# Google Scholar 混合检索接入笔记

## 环境核对

- 日期：2026-08-20。
- 工作树：`/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819`。
- `command -v scholar` 无输出，当前环境不能执行真实 Scholar 查询。
- `/Users/bilibili/.codex/skills/google-scholar/domain-knowledge.local.md` 不存在，无法应用用户自定义期刊、作者和研究组优先级。
- 未进行认证、登录、PDF 下载或任何仓库外写入。

## 已核接口

- 来源：`/Users/bilibili/.codex/skills/google-scholar/SKILL.md`，版本 `0.2.0`。
- 传统关键词检索：`scholar lookup "查询" --json`。
- Scholar Labs 自然语言检索：`scholar search "问题" --json`，认证和功能支持依赖更强，不应作为默认模式。
- JSON 结果字段：`title`、`authors`、`journal`、`year`、`citations`、`snippet`、`url`、`pdfUrl`、`clusterId`、`position`。
- 技能要求：程序化处理必须使用 `--json`；Scholar 仅用于发现；不得虚构缺失题录；限流时应停止快速重试。

## 现有架构

- `PAPER_PROVIDER_ORDER` 决定进入论文候选合并的在线来源。
- `_candidate_key` 依次使用 DOI、arXiv、规范题名加年份、来源标识去重。
- `_merge_candidates` 保留来源列表与 `provider_records`，并补齐作者、年份、URL、DOI 和 arXiv。
- `scope=all` 在本地结果完成后调用在线发现，在线单来源失败不删除本地结果。
- `--offline` 将全部在线来源标记为 `skipped_offline`。

## 设计裁决

- 新增 `google_scholar` 到论文来源顺序和在线并发来源表，复用现有跨来源去重。
- 通过 `shutil.which` 查找命令，通过 `subprocess.run` 的参数列表调用，固定 `--json`，禁止 `shell=True`。
- 默认 `lookup`；仅通过显式环境配置请求 `search`，且状态记录实际模式，不做静默回退或伪装。
- CLI 的 stderr 不原样进入输出，避免外部工具意外回显敏感信息；只映射为缺认证、验证码、限流、超时、JSON 或一般命令失败。
- Scholar 特有发现元数据写入该来源的 `provider_records`，包括聚类标识、引用数、期刊、排名和 PDF 发现链接；这些字段不改变全文证据状态。

## 技能冲突与采纳

- Google Scholar 技能建议认证失败后运行 `scholar auth`，但本任务明确禁止登录交互；采纳任务边界，只报告 `failed_missing_auth`，不自动认证。
- 技能允许 `--download`，但本任务禁止自动下载；不调用下载相关参数。
- 根规则要求第三方接口先核文档；本任务已读取本地已安装技能的命令和 JSON 合同。当前命令与源码均缺失，无法进一步运行时核验，实施报告必须保留此风险。

## 验证记录

- 初次运行 uv 验证时，文件系统沙箱拒绝读取用户级 uv 缓存，错误为 `Operation not permitted`；此时 Python 未启动，随后按规则使用已批准的限定前缀在沙箱外重跑。
- `python -m py_compile scripts/literature_search/online.py`：通过。
- 导入 `search_google_scholar`：通过。
- `python -m scripts.literature_search query --help`：通过。
- `scope=all --mode lexical --offline`：通过；保留 2 条本地结果；Google Scholar 与其他 6 个外部来源均为 `skipped_offline`；外部三类候选均为空。
- 公开通用查询 `machine learning` 的 Scholar 来源级调用：适配器返回 `unavailable_missing_command`、`command_mode=lookup`、`candidate_count=0`，未发出网络请求。
- 未运行 `black`、人工测试夹具、单元测试或集成测试。
