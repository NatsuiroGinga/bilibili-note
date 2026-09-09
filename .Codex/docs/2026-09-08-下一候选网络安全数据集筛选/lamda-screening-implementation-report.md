# LAMDA 来源期与近时段资格探针实现报告

## 范围

- 工作树：`/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908`
- 工具：`thesis/experiments/llm_probe/tools/ch3_lamda_source_near_screening.py`
- 权威运行制品：`thesis/experiments/llm_probe/runs/diagnostics/lamda-iclr2026-source-near-screening-budget1m-v3/`
- 状态：已完成。

## 唯一技能收据

读取时刻：`2026-09-08T12:05:39+0800`。以下为改码前重新核验的绝对路径与 SHA256。

| 技能 | 绝对路径 | SHA256 |
| --- | --- | --- |
| 日常编码 | `/Users/bilibili/.codex/skills/backup/daily-coding-20260811-112930/SKILL.md` | `da2399b50859b9d57281b9bc0dc456082db93d47486ae22967ebf3f17d354ae3` |
| PyTorch 模式 | `/Users/bilibili/.codex/skills/pytorch-patterns/SKILL.md` | `22b76f559f17d4b0e44eda71d353065e5da181203d165546edb08c16cc362d85` |
| 子代理驱动开发 | `/Users/bilibili/.codex/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/subagent-driven-development/SKILL.md` | `8dd1b8e698edec3700c6d89517dbe96febd3bacd3f6ea21c1a3569c62ea104b5` |

## 已冻结事实

- 仅允许打开 2013、2014、2016、2017 的 Parquet 行数据；2018--2025 只由输入 `manifest.json` 的文件级记录代表。
- 发布方特征空间使用了未来协变量。所有输出必须记录 `published_feature_space_uses_future_covariates=true` 与官方代码 revision `7728bfafcd5539a286b5f8c47b6f1e3b2d1f4249`，因此本探针只量化错误余量和 URL 特征影响，不能裁决无泄漏正式资格。
- 本机实际环境为 Python `3.14.5`、torch `2.12.0`、pyarrow `25.0.1`、scikit-learn `1.9.0`、numpy `2.4.6`。早期沙箱探测的 `torch.backends.mps.is_available()` 为 `False`，不代表获批真实运行环境；设备事实以 v3 `resource.json` 为准，实际为 `mps`。

## 实现与修复

- 实现 `load_and_verify_manifest`、允许年份文件发现、特征视图加载、分批 PyArrow 投影、IID AP 选模、IID 良性零假阳性阈值、按月及恶意家族召回、训练特征向量 SHA256 新颖掩码和两视图差量输出。
- `v1` 已完整运行，但发现 `without_url_domain` 用 3158 维向量查询 4561 维训练指纹集合。因此该视图的 `novel_without_source_feature_vector` 及依赖它的 URL 新颖差量无效。缺陷已写入 v1 的 `status.json`、`metrics.json`、`manifest.json`；v1 保留且未删除。
- `v2` 修复为：两个模型视图都以完整 4561 位特征计算同一个来源训练指纹掩码；去 URL 视图仅在模型输入中去除 1403 个 URL 特征。
- `v2` 完成时保留真实 `started_at`，并在 `manifest.json` 列出 `effective-config.json`、`status.json`、`metrics.json`、`resource.json`、`progress.jsonl` 的字节数与 SHA256。`manifest.json` 自身不列哈希，以避免自指哈希。
- v1/v2 的完整/去 URL 模型分别为 `5364481/3927809` 参数，超过本机筛选 `1000000` 参数上限。两者的 `status.json`、`metrics.json`、`manifest.json` 均已写入 `resource_contract_violation` 和 `authoritative_for_dataset_qualification=false`，只保留为探索收据。
- `v3` 采用 `input→128→64→32→1`，运行时同时断言实际参数量等于冻结值且不超过 `1000000`。完整/去 URL 视图的实际参数量为 `594753/415169`。

## 验证与真实运行

三个规定命令均使用 `/opt/miniconda3/envs/rwkv/bin/python`：

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `-m py_compile thesis/experiments/llm_probe/tools/ch3_lamda_source_near_screening.py` | 0 | 语法通过。 |
| `thesis/experiments/llm_probe/tools/ch3_lamda_source_near_screening.py --help` | 0 | CLI 入口通过。 |
| 探针入口，输出目录为 `lamda-iclr2026-source-near-screening-budget1m-v3` | 0 | 真实来源期/近时段运行完成，参数合同通过。 |

权威运行状态与制品：

- 状态：`thesis/experiments/llm_probe/runs/diagnostics/lamda-iclr2026-source-near-screening-budget1m-v3/status.json`，`completed`，运行时段 `2026-09-08T04:31:01.967262Z` 至 `2026-09-08T04:39:35.564492Z`。
- 指标：`thesis/experiments/llm_probe/runs/diagnostics/lamda-iclr2026-source-near-screening-budget1m-v3/metrics.json`。完整视图的 IID AP 为 `0.9944039`、2016/2017 AP 为 `0.9373960`/`0.3462362`、2016/2017 FNR 为 `0.2224487`/`0.9184887`；去 URL 视图的 IID AP 为 `0.9916174`、2016/2017 AP 为 `0.9184015`/`0.3168854`、2016/2017 FNR 为 `0.2347676`/`0.9167096`。
- 资源：`thesis/experiments/llm_probe/runs/diagnostics/lamda-iclr2026-source-near-screening-budget1m-v3/resource.json`。实际设备为 `mps`，墙钟 `513.6264` 秒，峰值常驻内存 `2375991296` 字节；MPS 峰值显存为 `null`，因为没有可靠通用接口。
- 新颖掩码：两个视图的 2016/2017 来源重复向量数均为 `9776`/`1255`，符合“无论模型视图都用完整 4561 位特征”合同。
- 清单自检：v1、v2、v3 的 `manifest.json` 中五个非自指输出文件的字节与 SHA256 均与当前文件匹配；仅 v3 满足参数资源合同。

## 局限与边界

- 每个输出均写入 `published_feature_space_uses_future_covariates=true` 和官方向量化代码 revision `7728bfafcd5539a286b5f8c47b6f1e3b2d1f4249`。发布的 4561 维特征空间使用未来协变量，本探针仅描述错误余量与 URL 特征影响，不能裁决无泄漏正式资格。
- 此为单训练种子 `screening_only` 运行；方向性结果不构成正式模型有效性结论，也不参与 RWKV 机制存废。
