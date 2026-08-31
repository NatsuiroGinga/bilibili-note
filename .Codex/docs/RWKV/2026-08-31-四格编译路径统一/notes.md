# 四格编译路径统一 · 工作笔记

<!-- RESEARCH_ROUTE=RWKV -->

- 日期：2026-08-31
- 全部读数来自目标机 `connect.westc.seetacloud.com`（容器 `autodl-container-280f4f89e7-feccf71f`）
  的真实运行，不是推演。

## 一、目标机只读核验（2026-08-31）

| 项 | 实测值 | 命令来源 |
| --- | --- | --- |
| GPU | `NVIDIA GeForce RTX 4080 SUPER` | `nvidia-smi --query-gpu=name,memory.total,memory.used,compute_cap --format=csv` |
| 显存 | `32760 MiB`，查询时 `0 MiB` 占用 | 同上 |
| 计算能力 | `8.9`（`sm_89`） | 同上 |
| PyTorch | `2.13.0+cu130`，CUDA `13.0` | `torch.__version__` / `torch.version.cuda` |
| `float32_matmul_precision` | `highest`（未改动） | `torch.get_float32_matmul_precision()` |
| 磁盘 | `/root/autodl-tmp` `100G` 用 `74G` 余 `27G` | `df -h` |

**与旧三格的硬差异**：旧 C00／C01／C10 三格正式制品跑在 `sm_120` 的 RTX 5090 上
（见其配置 `torch_compile.evidence` 字段原文），当前机器是 `sm_89` 的 4080 SUPER。
恢复卡门禁要求「同一 GPU」，因此**旧三格无论如何都不满足门禁**，必须与 C11 一起重跑。

## 二、接口核验表（写代码前在目标机逐项实测，未凭记忆）

| 库 | 目标机版本 | 接口 | 核验到的签名／结构 | 结论 |
| --- | --- | --- | --- | --- |
| torch | `2.13.0+cu130` | `torch._dynamo.utils.counters` | `defaultdict`，实测键 `frames{total,ok}`、`stats{calls_captured,unique_graphs}`、`graph_break`（`Counter`：完整原因文本→次数）、`unimplemented`、`resumes`、`aot_autograd`、`inductor`、`aten_mm_info` | 可用 |
| torch | 同上 | `torch._dynamo.utils.graph_break_reasons` | `list`，每项含 `.reason`（多行文本）、`.user_stack`（`FrameSummary` 列表，带 `filename`／`lineno`／`name`／`line`）、`.graph_break`（`bool`） | 可用，**是「断在哪」的唯一直接来源** |
| torch | 同上 | `torch._dynamo.explain` | `(f, *extra_args, **extra_kwargs) -> Any`；返回 `ExplainOutput`，字段 `break_reasons`／`compile_times`／`graph_break_count`／`graph_count`／`graphs`／`op_count`／`ops_per_graph`／`out_guards` | 可用（用于离线诊断，未进生产代码） |
| torch | 同上 | `torch._dynamo.eval_frame.OptimizedModule` | 存在；编译包装体带 `_orig_mod` | 可用 |
| torch | 同上 | `torch.compiler.is_compiling()` | 即时执行下返回 `False` | 存在，最终未采用（见第五节） |
| torch | 同上 | `torch.utils.checkpoint.checkpoint` | `(function, *args, use_reentrant: bool \| None = None, context_fn=..., determinism_check='default', debug=False, early_stop=True, **kwargs)` | 与既有代码写法一致 |
| torch | 同上 | `torch._dynamo.config.cache_size_limit` | `8` | 记录，未改动 |

**计数器语义（实测，非推断）**：`counters` 是**编译期**累积量。同形状重复调用命中缓存时
`frames`／`graph_break` 全部不再增长（实测 `frames` 两次调用后仍是 `24/20`）；换一种输入分布触发
新编译时才增长（实测 `total` 由 `24` 变 `25`）。因此它回答的是「本进程一共编译了多少帧、
在哪里断裂」，不是「执行了多少次」。执行次数由本任务新增的调用点台账单独计数。

## 三、动手前的三条关键实测

### 3.1 CEM 注意力的图断裂位置（`torch._dynamo.explain` 直接读出）

对真实 `ch3_ft_causal_entity_memory.CausalEntityMemoryAttention(width=192, heads=8, slots=8)`
单独编译，`graph_count=5`、`graph_break_count=4`，四处断裂逐行定位：

| 文件行 | 源码 | 断裂原因 |
| --- | --- | --- |
| `ch3_ft_causal_entity_memory.py:334` | `if bool(has_history.any()):` | `Unsupported Tensor.item() call with capture_scalar_outputs=False` |
| `:335` | `active_hidden = cls_hidden[has_history]` | `Dynamic shape operator`（`aten.nonzero.default` 输出形状依赖数据） |
| `:336` | `active_memory = memory[has_history]` | 同上 |
| `:337` | `active_valid = memory_valid[has_history]` | 同上 |

另外 inductor 侧还报 `Backend compiler exception: inductor failed with aten.nonzero.default`，
即便放开 `capture_dynamic_output_shape_ops` 也会在后端再断一次。

### 3.2 `checkpoint(编译模型)` 与 `checkpoint(原模块)` 的差别（决定性实测）

构造与 `_entity_ranking_*_forward` 同形状分布的微批序列 `[64, 64, 37]`（等长微批加尾部残批），
分别把编译包装体和 `_orig_mod` 放进 `torch.utils.checkpoint.checkpoint(..., use_reentrant=False)`：

| 传入对象 | `counters` 实测 |
| --- | --- |
| 编译包装体 | `frames total=3 ok=3`、`unique_graphs=2`，并生成**动态形状核** `aten.addmm_s77_192_192`、`aten.mm_1_192_s77`（`s77` 是符号维） |
| `_orig_mod` | `counters` **全空**（`{}`），Dynamo 完全不介入 |

这条实测同时给出两个结论：

1. 修改前的 `_entity_ranking_bare_forward`（C01）**确实在编译路径下执行**，
   与已固定为 `_orig_mod` 的 `_entity_ranking_memory_forward`（C11）不一致，
   即恢复卡门禁第 2 条当时不成立；
2. 提交 `0a47546` 记录的「前向与重算 FFN 宽度元数据 `255/256` 不一致」有了机制解释：
   变长微批让 Dynamo 从静态图切到符号维动态图，检查点反向重算时元数据对不上。
   传 `_orig_mod` 从根上消除该类硬失败。

### 3.3 裸 FT 骨干本身零图断裂

C00 探针实测 `frames_total=4`、`frames_ok=4`、`graph_break_total=0`。
即逐流骨干在这套 torch 上完整编译，没有任何回退。断裂全部来自因果实体记忆模块。

## 四、探针运行（独立运行身份，不占四格正式身份）

四个探针 `ch3-ft-pathprobe-{c00,c01,c10,c11}-v1`，
入口 `--calibrate-runtime`（一个完整优化步 ＋ 一次完整源验证），
`budget.state = "unmeasured"`（`epochs=0`／`steps_per_epoch=0`，`--run` 入口会被拒绝），
输出根独立，四臂全部 `exit=0`。**未读取任何 LSPR24 数组，`target_reads=0`。**

| 探针 | 调用点 → 实际路径 | 编译帧 | 图断裂 | 仓库断点 | 单步秒 | 完整源验证秒 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| C00 | `flow_forward_bare_train`／`_validation`／`_zero_gate_model`／`_zero_gate_reference` 全 `compiled_entry` | 4/4 | 0 | 0 | 22.00 | 47.76 |
| C01 | 上述逐流点 `compiled_entry`；`ranking_forward_bare` **`eager`** | 4/4 | 0 | 0 | 9.36 | 47.34 |
| C10 | `flow_forward_entity_memory_train`／`_validation` `compiled_entry` | 24/24 | 15 | 4 | 7.08 | 186.59 |
| C11 | `flow_forward_entity_memory_combined`／`_validation` `compiled_entry`；`ranking_forward_entity_memory` **`eager`** | 24/24 | 15 | 4 | 9.11 | 184.88 |

C10 与 C11 的四个仓库断点逐条相同，就是 3.1 表里的 `334/335/336/337` 四行。

**单步秒不可作吞吐比较**：`--calibrate-runtime` 只跑一步，该步包含首次编译，
C00 的 `22.00` 秒里绝大部分是编译预热。可比的是完整源验证耗时——它跑完整个验证集，
只有首批是冷的：C00 `47.76` 对 C01 `47.34`（同一逐流代码路径，差 `0.9%`，互为一致性佐证），
C10 `186.59` 对 C11 `184.88`（同一记忆代码路径，差 `0.9%`）。
记忆路径的验证扫描是裸骨干的 `3.9` 倍。

### 四格比对判定（`tools/ch3_ft_execution_path_receipt.py --compare`）

```
共同逐流骨干统一走编译路径            consistent = true（四臂均 compiled_entry）
C01与C11的实体排序检查点统一即时执行    consistent = true（两臂均 eager）
C10与C11的记忆注意力统一执行路径        consistent = true（两臂均 compiled_entry）
break_signatures_identical_within_groups = true
consistent = true
```

## 五、设计取舍记录

- **为什么不用 `torch.compiler.is_compiling()` 打标记**：它只在 Dynamo 追踪期返回 `True`，
  要读到这个值必须在被编译函数内部写全局副作用，反而增加一处 Dynamo 需要重放的副作用，
  有改变编译行为的风险。改用「调用入口是不是 `OptimizedModule`」判定，
  纯外层 Python，零编译副作用。
- **为什么台账用模块级单例**：七个前向调用点分散在宿主的六个函数里，逐层传参要改六个函数签名，
  并牵动断点恢复与零门断言的调用方。沿用与 `torch._dynamo.utils.counters` 相同的单例写法，
  只在 `run_training`／`probe_runtime` 入口 `reset()` 一次。
- **为什么不加阻断门**：按 `thesis/experiments/llm_probe/AGENTS.md`「默认不新增阻断门、
  披露优先于阻断」，单臂内部无法判断四格是否同路径，硬失败没有意义。
  一致性判定放在四臂收据齐备后的离线 `--compare`。
- **断裂签名只在组内比较**：C00／C01 不构造记忆模块，仓库断点必然为空；
  C10／C11 必然带记忆模块的四个断点。四臂放同一集合比较会必然不一致，
  那是机制差异不是路径差异。首版实现犯了这个错并被自己的比对工具报出来，已改为按
  「是否走记忆路径」分组、组内逐条比较。

## 六、即时执行对照臂实测

四个对照臂 `ch3-ft-pathprobe-{c00,c01,c10,c11}-eager-v1`，唯一差异是
`runtime.torch_compile.enabled = false`，科学身份与对应编译臂逐位相同
（`science_identity_sha256` 一致，只有 `runtime_identity_sha256` 不同）。
四臂收据均为 `frames = 0/0`、`graph_break_total = 0`，即 Dynamo 完全不介入。

| 臂 | 单步秒（编译／即时） | 完整源验证秒（编译／即时） | 即时/编译 | 峰值显存（编译／即时） |
| --- | --- | --- | ---: | --- |
| C00 | 22.00 ／ 1.28 | 47.76 ／ 61.27 | 1.283 | 13,733 ／ 17,877 MiB |
| C01 | 9.36 ／ 2.26 | 47.34 ／ 62.09 | 1.312 | 17,893 ／ 17,891 MiB |
| C10 | 7.08 ／ 1.69 | 186.59 ／ 183.92 | **0.986** | 14,721 ／ 18,813 MiB |
| C11 | 9.11 ／ 3.63 | 184.88 ／ 185.44 | **1.003** | 19,773 ／ 19,715 MiB |

**编译对记忆臂没有收益**：C10 比值 `0.986`（即时还快 `1.4%`）、C11 比值 `1.003`，
两者都在测量噪声内。原因由观测层直接给出——记忆臂被切成 `24` 帧、`15` 次图断裂，
守卫与帧切换开销吃掉了融合收益。编译的价值只存在于裸骨干侧（`1.28–1.31×`）。

显存同理：即时执行只让逐流阶段主导的臂上升约 `30%`（C00、C10），
排序阶段主导的 C01／C11 不变（其排序检查点在两种配置下都是即时执行）。
**两套方案的四臂最高峰值几乎相同**：编译 `19,773 MiB`、全即时 `19,715 MiB`，
卡上 `32,760 MiB`，显存不构成约束。

单步秒对编译臂不可用作吞吐（含首次编译）；即时臂的单步秒也不是稳态
（首步含 cuDNN／cuBLAS 自动调优与显存分配），故一律以完整源验证扫描为稳态判据。

## 七、`execution_environment` 字段的追加与验证

`environment-receipt.json` 只记 `torch.__version__`、`platform` 与显存字节数，
**没有 GPU 型号与计算能力**；而 inductor 为不同计算能力生成不同的核，
门禁的「同一 GPU」条款因此无法机械判定。故给执行路径收据追加
`execution_environment`，并让 `--compare` 一并判定。

真实运行验证（复跑 `ch3-ft-pathprobe-c00-v1`，`exit=0`，21:14:22）：

```
"execution_environment": {"torch": "2.13.0+cu130", "cuda": "13.0",
  "float32_matmul_precision": "highest",
  "device_name": "NVIDIA GeForce RTX 4080 SUPER", "device_capability": [8, 9]}
```

两条分支都已实跑：与 v1 收据混比得 `execution_environment_identical = null`（无法判定，
不冒充通过）；两份 v2 收据相比得 `true`。该复跑同时复现了首轮 C00 的路径与断裂结论
（四点全 `compiled_entry`、`frames 4/4`、`graph_break 0`；完整源验证 `47.49` 秒对首轮 `47.76` 秒，
差 `0.6%`）。

## 八、文件所有权与待办

- `tools/ch3_ft_c00_dual_selection.py` 有三方并发写。本机工作树与 `HEAD` 已同时包含
  本任务的埋点（提交 `da1a817`）与主代理的筛选层设备门放宽（提交 `13d59c0`），无冲突。
  **服务器副本停留在 `20:58` 推送的 `da1a817` 版本，缺 `13d59c0`**，
  按协调要求本任务不再推送该文件，由主代理统一推送合并版本。
- 服务器上的 `tools/ch3_ft_execution_path_receipt.py` 是本任务独有文件，
  已推送到含 `execution_environment` 的最新版本（哈希与本机一致）。
- 正式四格重跑不在本任务范围，由主代理另行安排。
