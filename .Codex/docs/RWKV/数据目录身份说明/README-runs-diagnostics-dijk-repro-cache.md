# 本目录的 X 数组不是 raw83 原始数据

`X23.npy` 与 `X24.npy` 是 dijk 复现管线**标准化之后**的逐流特征矩阵，不是 Dijk 2026 附录 A 的
83 字段原值，也不等于协议A的任何一个候选视图。目录名 `dijk-repro/cache` 不提示这件事，
形状、dtype 和文件字节数与冻结的 raw83 产品完全一致，**只看文件名、`ls -la` 或 `shape` 无法区分**。

判断能不能用，看的是**训练侧与评价侧是否同源**，不是「有没有用缓存」：
在这份缓存上训练出来的模型（例如 GRANDE 源年）继续读它，口径自洽；
按 `raw83 → 候选A → 候选B` 拟合的模型（表格 ResNet、CUDA-RWKV）读它，
模型会看到训练时从未见过的输入分布，**结果无效但一切看起来正常**。

## 一、部署与副本

| 位置 | 路径 |
| --- | --- |
| 服务器（数据实际所在处） | `/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache/README.md` |
| 仓库权威副本 | `.Codex/docs/RWKV/数据目录身份说明/README-runs-diagnostics-dijk-repro-cache.md` |

本机 `thesis/experiments/llm_probe/.gitignore` 有 `runs/*`，缓存目录不入版本控制，
所以权威副本放在 `.Codex/docs/RWKV/` 下。两处内容必须逐字一致。改完仓库副本后按下面的固定入口重新部署：

```bash
source ~/.zshrc
export GPU_SSH_ACTIVE="ssh -o ProxyCommand=none -o ProxyJump=none ${GPU_SSH_B76#ssh }"
export GPU_PWD_ACTIVE="$GPU_PWD_B76"
expect thesis/experiments/llm_probe/tools/remote_exec/gpu_rsync_push.exp \
  .Codex/docs/RWKV/数据目录身份说明/README-runs-diagnostics-dijk-repro-cache.md \
  /root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache/README.md
```

服务器与凭据键的规范来源是 `.Codex/docs/RWKV/RWKV路线总控.md` 第五节；凭据只从环境变量读取，不回显。

## 二、X 数组到底做了什么变换

变换谱系记录在 `thesis/experiments/llm_probe/tools/ch3_final_weights_assets/README.md` 第四节
与同目录 `inference.py` 的 `--input-convention standardized-cache`，`inference.py` 第 109–110 行是可执行定义：

```python
x[~np.isfinite(x)] = 0.0
x = np.clip((x - mean) / std, -10, 10).astype(np.float32, copy=False)
```

三步，顺序不能换：

1. **非有限值先置 0**（所以缓存里一个 NaN 都没有，而 raw83 产品保留 NaN）；
2. 按 **LSPR23 逐列均值与标准差**标准化，LSPR24 复用同一套统计量；
3. 裁剪到 `[-10, 10]`。

`mean` / `std` 与字段顺序存放在与该批权重共用的 `normalization.json` 与 `features.json`。

## 三、实测差异（LSPR23，2026-08-25）

把缓存 `X23.npy` 与协议A冻结 `lspr23-raw83.npy` 逐单元比对。两者同为 `float32 (16353511, 83)`，
文件字节数同为 `5,429,365,780`（`16353511 × 83 × 4 = 5,429,365,652` 再加 `128` 字节 npy 头）。

| 观测 | 数值 |
| --- | --- |
| 有限值不同的单元数 | `1,224,589,881` |
| 只有产品侧非有限（NaN）的单元数 | `18,276,864` |
| 缓存侧非有限单元数 | `0` |
| 与 raw83 的最大绝对差（前 20 万行样本） | `251799984.0` |
| 相对差 `>1e-3` 的单元比例 | `0.913` |

第 0 列 `SrcPort` 的同一个单元：缓存 `-0.3009…`，raw83 `48778.0`，协议A候选A视图 `0.0932…`。
三个值互不相同，说明缓存既不是原值也不是候选A。

证据来源：`runs/diagnostics/ch3-cuda-rwkv-lspr24-inmemory-descriptive-eval-v1/diagnostics/`
下的 `diagnose_cache_vs_product.py`、`diagnose_x23_nature.py` 与 `diagnose.log`、`diagnose-x23.log`；
结论收在 `.Codex/docs/RWKV/2026-08-25-CUDA-RWKV四格LSPR24零物化描述性评价/实施报告.md` 第一节。

LSPR24 侧 `X24.npy` 出自同一管线、同一套 LSPR23 统计量，同样不是原值。

### 2026-08-26 独立复核

在 B76 上重跑前 `200,000` 行的对照（`float64` 相减，只统计两侧都有限的单元）：

| 项 | 复核实测 | 说明 |
| --- | --- | --- |
| 两侧形状／dtype／字节数 | `(16353511, 83)` `float32` `5,429,365,780`，完全相同 | 与上表一致 |
| 缓存非有限单元（前 20 万行） | `0` | 与全量 `0` 一致 |
| raw83 非有限单元（前 20 万行） | `44,308` | 与全量 `18,276,864` 同向 |
| 最大绝对差 | `251799990.0` | 原诊断记 `251799984.0`，差 `6` |
| 相对差 `>1e-3` 占比 | `0.9154366365` | 原诊断记 `0.913` |
| 第 0 列第 0 行 | 缓存 `-0.30094578862190247`、raw83 `48778.0` | 与原诊断逐位一致 |
| 缓存样本全局最大值 | `10.0` | 独立印证「裁剪到 `[-10, 10]`」 |
| `I24`／`M24` 对冻结合同的 SHA-256 | 两项均 `True` | 冻结登记有效 |

两处数值差异是**计算口径差异，不是结论差异**：`251799984.0` 是 `float32` 可精确表示的值，
本次在 `float64` 下相减得 `251799990.0`，说明原诊断在 `float32` 下相减；
相对差占比的差来自本次只在「两侧都有限」的子集上统计。两种口径都给出同一结论。

## 四、逐文件说明

`N23 = 16,353,511` 条流、`S23 = 271,815` 条序列；`N24 = 20,227,356` 条流、`S24 = 200,825` 条序列；
序列最大长度 `Lmax = 128`。下表字节数于 2026-08-26 在 B76 用 `ls -la` 逐项复核，
本目录共 `16` 个文件，与下表一一对应，**没有第 17 个文件，也没有任何清单文件**。

| 文件 | 字节 | 是什么 | 可否直接喂模型 |
| --- | ---: | --- | --- |
| `X23.npy` | 5,429,365,780 | LSPR23 逐流 83 维特征，**已按第二节三步变换** | **否**，除非模型本身就训练在这份缓存上 |
| `X24.npy` | 6,715,482,320 | LSPR24 逐流 83 维特征，**已按第二节三步变换** | **否**，同上 |
| `I23.npy` | 278,338,688 | 序列索引 `int64 (271815, 128)`，元素是 X 的行号 | 是，与协议A产品逐字节相同 |
| `I24.npy` | 205,644,928 | 序列索引 `int64 (200825, 128)` | 是，已被冻结合同登记哈希 |
| `M23.npy` | 139,169,408 | 序列掩码 `(271815, 128)`，每元素 4 字节 | 是，与协议A产品逐字节相同 |
| `M24.npy` | 102,822,528 | 序列掩码 `(200825, 128)` | 是，已被冻结合同登记哈希 |
| `y23.npy` | 65,414,172 | LSPR23 逐流标签 `float32 (16353511,)` | 是，转 `int8` 后内容摘要等于源年清单登记值 |
| `y24.npy` | 80,909,552 | LSPR24 逐流标签 `float32 (20227356,)` | 是，与冻结 Parquet 的 `Label` 逐元素相等 |
| `t24.npy` | 161,818,976 | LSPR24 逐流开始时刻，每元素 8 字节 | 是，与冻结 Parquet 的 `mTimestampStart` 逐元素相等 |
| `t23_flow.npy` | 130,828,216 | LSPR23 逐流开始时刻，存成 `float64` | 值与协议A产品相同，**但 dtype 不同故文件摘要不同**，不要用摘要比对 |
| `ent23.npy` | 130,828,216 | LSPR23 逐流实体 id，每元素 8 字节 | 是 |
| `E23.npy` | 2,174,648 | LSPR23 **逐序列**实体 id `(271815,)` | 是，实体不相交划分用 |
| `T23.npy` | 2,174,648 | LSPR23 **逐序列**时间 `(271815,)` | 是，时间尾部划分用 |
| `s24.npy` | 494,808,757 | LSPR24 逐流源 IP，object 数组，需 `allow_pickle=True` | 是，仅作分组键；哈希已登记 |
| `d24.npy` | 495,445,716 | LSPR24 逐流目的 IP，object 数组，需 `allow_pickle=True` | 是，仅作分组键；哈希已登记 |
| `cat24.npy` | 21,475,328 | LSPR24 逐流攻击类别名，object 数组 | 是，仅作评价分面；不得入模 |

已登记的冻结哈希：`I24`、`M24` 在
`thesis/experiments/llm_probe/configs/ch3-protocol-a-raw83-target-v1.json` 的 `year_product.sequence_arrays`；
`y24`、`s24`、`d24` 在 `thesis/experiments/llm_probe/tools/ch3_published_neural_operational_backfill.py`
的 `SHARED_INPUTS`。**`X23` 与 `X24` 没有任何冻结合同登记它们的哈希或语义**——这正是本目录出事的原因。

本目录**没有** `dataset-manifest.json`、`cache-manifest.json` 或任何字段清单，
本文件是唯一的身份记录。成员数曾有 `16` 与 `17` 两种历史记录，
2026-08-26 实测为 `16`；消费前仍按实际 `ls` 核对，不要沿用数量假设。

## 五、需要 83 字段原值时走哪条路

| 年份 | 权威来源 |
| --- | --- |
| LSPR23 | `runs/data-prepared/ch3-protocol-a-raw83-shared-v1/generations/source-v1/raw/lspr23-raw83.npy` |
| LSPR24 | `data/raw/lspr24-v1/lspr24_v2.parquet`（`sha256=1d96f0a0…`，`20,227,356` 行，`21` 行组，`101` 字段） |

LSPR24 没有物化的 raw83 数组，正确做法是**直读冻结 Parquet 并在内存内重建候选视图**。
参考实现：`thesis/experiments/llm_probe/tools/ch3_cuda_rwkv_lspr24_inmemory_descriptive_eval.py`
（配置 `configs/ch3-cuda-rwkv-lspr24-inmemory-descriptive-eval-v1.json`）。它按行组流式读取 83 个
Dijk 字段，逐批 `_canonicalize_raw83` → `_transform_a` → `_transform_b`，结果只驻内存（约 `6.7 GiB`），
序列结构仍取本目录的 `I24` / `M24`。

该路径已被两条证据验证：从冻结 `lspr23-raw83.npy` 重建候选 B 视图与已封印视图逐单元比对
`mismatched_cells = 0`；源年验证区四格复算与封印指标七项最大绝对差 `0.0`。

## 六、三条判定规则

1. **同形状、同 dtype、同字节数不等于同内容。** 本目录与 raw83 产品在这三项上完全一致，内容差
   `1,224,589,881` 个单元。判断数据身份只能查变换谱系或抽样逐单元对照。
2. **先问模型训练在哪份视图上**，再决定评价读哪份数组。两侧必须同源。
3. **不确定就抽样对照**：取同一行同一列，打印缓存值、raw83 值与目标候选视图值。三者不同就说明选错了。

已发生的实际损失：2026-08-25 表格 ResNet 的 LSPR24 评价（提交 `66873dd`）从本目录取 `X24.npy`
再叠加候选 A/B 变换，而其源年训练消费的是共享 Raw83 产品，两侧不同源，该轮结果口径存疑需重跑。
同日 CUDA-RWKV 因执行了第六节第三条的抽样对照而当场发现，改走第五节路径。
