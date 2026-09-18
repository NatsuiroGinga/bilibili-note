# DRIFT 第三章训练增强缓存无明文恢复实施简报

> **状态：设计可行，真实验证待做。** 本简报只关闭正式训练在“不落盘增强域名缓存”条件下的恢复算法缺口，不实现代码、不启动训练或评价，也不证明任何方法有效。

> **实施者：** `gpt-5.6-luna`，实际 `effort` 由父代理按实现难度选择。实施前须重读本简报、`implementation_plan.md` §四及两个目标训练文件；不得改变数据、训练臂、预算、输入处理、候选核、随机种子或断点间隔。

## 一、任务边界与结论

正式训练继续直接读取规范 `SourceStore`，内存中的增强字符串缓存不写入检查点。恢复时先以**独立局部随机数生成器**重放首轮已经访问的源索引前缀，重建缓存并核对检查点中的缓存计数／根摘要；核对通过后才载入训练状态，并最后恢复检查点保存的 Python、NumPy、PyTorch、CUDA 和当前骨干自己的 `variant_rng` 状态。

该算法不新增科研机制。它成立只因为当前训练语义同时满足：首轮洗牌固定、规范源中每个索引每轮只访问一次、缓存只在首次访问建立且永不更新／删除、候选生成不依赖模型、模型分数只选择已有候选。任一前提未来改变，旧恢复策略立即失效并须用新策略身份重新验收。

旧 `official_p2p3_full.py` 把完整 `adv_cache` 写入断点；该旧断点只作证据，不能迁移。新正式断点只保存常规训练状态、下一批游标以及缓存策略身份、计数和摘要，不保存域名、攻击字符串、成员集合、逐实体哈希列表或索引列表。

## 二、已核代码事实

| 事实 | 证据位置 | 本简报结论 |
| --- | --- | --- |
| DRIFT 变体流为独立 `random.Random(SEED)` | `official_p2p3_full.py:292` | 缓存重放使用新的局部生成器，不使用 Python 全局随机状态。 |
| 每轮顺序由新的 `random.Random(SEED + ep)` 洗牌 | `official_p2p3_full.py:314` | 首轮顺序可由 `SEED+1` 和同一源长度精确重建，不消耗训练随机状态。 |
| DRIFT B 使用 `setdefault(i, [perturb2(...)])` | `official_p2p3_full.py:321-323` | 首次值只由首轮首次访问决定；缓存命中仍会先计算默认表达式并额外消耗 `variant_rng`。 |
| DRIFT D/F 仅在 `i not in adv_cache` 时生成一次 base 和四个候选 | `official_p2p3_full.py:324-330` | 缓存内容只依赖首轮首次访问顺序；缓存只存四个候选，不存 base。 |
| D/F 模型分数只用于从缓存候选中选择 | `official_p2p3_full.py:331-355` | 模型状态不参与缓存内容重建，不在重放阶段执行前向。 |
| 旧实现保存并恢复完整缓存 | `official_p2p3_full.py:254-268,297-306` | 旧模式违反新无明文缓存合同，不迁移其 `adv_cache` 字段。 |
| B-ResNet 有独立 `random.Random(SEED)` 和固定逐轮洗牌 | `bresnet_p2p3.py:299-304` | B-ResNet 使用自己的局部重放路径，不能与 DRIFT 共用可变 RNG 对象。 |
| B-ResNet B 显式 `if i not in adv_cache` | `bresnet_p2p3.py:311-319` | 缓存命中不生成多余变体，也不继续消耗 B-ResNet 的 `variant_rng`。 |
| B-ResNet D/F 首次生成 base 和四个候选 | `bresnet_p2p3.py:323-333` | 与 DRIFT 的缓存内容形状相同，但保持独立策略身份和实现路径。 |
| 两文件均没有缓存删除、清空或更新分支 | 两文件全文对 `adv_cache` 写操作核验 | 首轮建成的条目后续保持不变。 |

正式直读训练还须先验证：`SourceStore` 已按规范 exact eSLD `unique()`，源顺序根、标签根、实体数、配置哈希与检查点相同；每轮 `order` 是 `[0,n)` 的完整排列。首轮每个源索引只访问一次由这个排列性质保证，不从旧重复曝光脚本外推。

## 三、四种缓存策略必须分开

| 策略身份 | 适用臂 | 首次访问的缓存值 | 首轮后的 RNG 行为 |
| --- | --- | --- | --- |
| `drift_b_setdefault_v1` | DRIFT B | 对原域名调用一次 DRIFT `perturb2`，保存一个字符串 | 每次恶意缓存命中仍求值 `perturb2` 并消耗 DRIFT `variant_rng`，但不得改缓存值。 |
| `drift_df_base4_v1` | DRIFT D/F | 先生成一个 base，再从 base 依次生成四个候选；只保存四候选 | 命中不生成、不消耗；模型评分只改变本批入选项。 |
| `bresnet_b_if_missing_v1` | B-ResNet B | 对原域名调用一次 `off.perturb2`，保存一个字符串 | 命中不生成、不消耗。不得把 DRIFT B 的 `setdefault` 副作用写入本路径。 |
| `bresnet_df_base4_v1` | B-ResNet D/F | 先生成一个 base，再从 base 依次生成四个候选；只保存四候选 | 命中不生成、不消耗；保持 B-ResNet 独立 RNG 对象和代码身份。 |

A/G 不建立增强缓存，策略为 `none`。四种活动策略不得因为种子、`perturb2` 函数或候选数相同而合并。各训练臂使用独立进程、独立 `variant_rng` 和独立检查点。

## 四、拟实现接口与文件所有权

### 4.1 只修改的生产文件

| 文件 | 拟实现职责 |
| --- | --- |
| `thesis/experiments/llm_probe/tools/ch3_drift_official_p2p3_formal.py` | 实现 DRIFT B 与 D/F 各自的首轮缓存重放、缓存摘要、保存字段校验和恢复顺序；继续保留 DRIFT B 命中时的 `setdefault` RNG 消耗语义。 |
| `thesis/experiments/llm_probe/tools/ch3_drift_bresnet_p2p3_formal.py` | 独立实现 B-ResNet B 与 D/F 的重放；B 命中保持显式 `if-not-in`，不得调用 DRIFT 的可变 RNG 或重放函数。 |
| `.Codex/docs/2026-09-12-DRIFT正式评价合同裁决/implementation-report.md` | 记录实现差异、检查命令、真实缓存重建／中断收据、峰值资源和未通过项。 |

现有两个训练配置、`ch3_drift_formal_contract.py`、直读加载器和启动器只读复用。缓存策略由 `(checkpoint_schema_version, backbone, arm, code_sha256)` 唯一确定，不增加命令行覆盖项，不修改已验收科研数值。若实现发现必须扩大文件范围，先写报告并交主代理确认，不能自行新建共享缓存模块。

### 4.2 两个独立内部接口

以下均为**拟实现**的私有接口，返回值只驻留内存：

```text
_rebuild_drift_adv_cache(
    source_store, arm, next_epoch, next_batch_idx, batch_size, seed
) -> dict[int, tuple[str, ...]]

_rebuild_bresnet_adv_cache(
    source_store, arm, next_epoch, next_batch_idx, batch_size, seed
) -> dict[int, tuple[str, ...]]

_cache_summary(
    cache, cache_policy_id, source_order_sha256
) -> {entry_count, value_count, root_sha256}
```

两个训练文件可以分别保留同名私有 `_cache_summary`，但编码必须都复用现有 `ch3_drift_formal_contract.length_prefix_encode` 与 `sha256_bytes`。不得共享可变 RNG、缓存对象或骨干特有的重放函数。

## 五、精确重建算法

### 5.1 重放边界

设规范源大小为 `n`，批量为 `B`，`next_epoch/next_batch_idx` 表示下一批：

```text
epoch1_order = shuffle([0, n), Random(SEED + 1))

if next_epoch == 1:
    replay_end = min(n, next_batch_idx * B)
else:
    replay_end = n

seen_epoch1_indices = epoch1_order[:replay_end]
```

`next_epoch==1,next_batch_idx==0` 对应空缓存；首轮末或 `next_epoch>=2` 对应完整首轮缓存。恢复入口先验证游标范围、批数、批量、源大小、源顺序根和标签根；不接受“尽量恢复”或忽略差异开关。

### 5.2 重建步骤

1. 只读载入检查点元数据，暂不恢复任何全局或变体随机状态。
2. 直接读取现有 Parquet，按正式加载器建立内存 `SourceStore`；核对输入收据、规范源顺序根、标签根、`n`、批量、种子、骨干、臂、配置和代码身份。
3. 用独立局部 `shuffle_rng = random.Random(SEED + 1)` 重建首轮排列；该对象不进入运行时状态。
4. 用独立局部 `replay_rng = random.Random(SEED)`，按 `seen_epoch1_indices` 的顺序只处理恶意标签：
   - B：每个已见恶意索引只调用一次相应骨干的 `perturb2`，缓存一个结果。
   - D/F：每个已见恶意索引先调用一次生成 base，再按既有顺序调用四次生成候选，只缓存四候选。
   - A/G：缓存保持空。
5. 计算缓存条目数、字符串总数和根摘要，与检查点字段逐项完全相等后才继续；不相等即失败关闭并保留原检查点。
6. 载入模型和优化器状态。随后恢复 Python 全局、NumPy、PyTorch CPU、CUDA 的检查点状态；最后创建当前骨干自己的运行时 `variant_rng` 并加载检查点 `rng_variant`。
7. 用独立 `Random(SEED + next_epoch)` 重建当前轮顺序，从 `next_batch_idx` 继续。重建缓存使用的 `replay_rng` 立即释放，绝不能替代已经恢复的运行时 `variant_rng`。

DRIFT B 的首轮缓存内容只需按每个索引首次访问重建。它在第二轮及以后由 `setdefault` 默认表达式造成的额外随机消耗**不参与缓存重建**；这些消耗已经体现在检查点 `rng_variant` 中，第 6 步恢复后，后续缓存命中的多余消耗继续与原路径一致。B-ResNet B 不得执行这些额外调用。

### 5.3 缓存根摘要

缓存摘要在内存中按源索引升序计算：

```text
entry_digest = SHA-256(length_prefix_encode(
    cache_policy_id,
    str(source_index),
    str(len(values)),
    SHA-256(values[0].encode("utf-8")), ...
))

cache_root = SHA-256(length_prefix_encode(
    cache_schema_version,
    cache_policy_id,
    source_order_sha256,
    entry_digest_0, ...
))
```

只将最终 `cache_root` 和计数写入检查点／收据。`source_index`、单项摘要、域名和候选字符串不落盘。空缓存也按相同模式产生确定摘要，不能用空字符串代替。

## 六、检查点保存字段

新正式检查点保留 `implementation_plan.md` 已冻结的常规字段，并要求以下缓存相关字段：

```text
cache_schema_version
cache_policy_id
cache_entry_count
cache_value_count
cache_root_sha256
```

常规身份至少包含：检查点模式、骨干、臂、运行身份、配置与代码哈希、输入收据哈希、规范源顺序／标签根、源实体数、批量、轮数、种子、下一轮和下一批游标。常规可恢复状态包含模型、优化器、Python、NumPy、PyTorch CPU/CUDA 和该骨干的 `rng_variant` 状态。

禁止出现：`adv_cache`、原域名、增强域名、候选列表、成员集合、源索引列表、洗牌索引列表或其磁盘旁路文件。旧 v1/v2 检查点即使含完整缓存也不得转成新模式。

## 七、容量与时间实测

禁止因“不落盘缓存”省略缓存容量。正式单臂峰值至少同时包含：

- 完整内存 `SourceStore`、标签和规范顺序结构；
- 当前轮完整洗牌索引；
- B 每个已见恶意实体的一个字符串及字典／元组开销；
- D/F 每个已见恶意实体的四个候选字符串及字典／元组开销；
- D/F 生成时的瞬时 base、当前批候选／owner、模型与优化器；
- DRIFT B 缓存命中时 `setdefault` 默认表达式产生的瞬时字符串和 CPU 开销；该项不适用于 B-ResNet B。

Luna 在服务器以真实完整 `SourceStore` 分别测量四个 `cache_policy_id` 的重建墙钟、每秒恶意实体数、进程峰值 RSS、cgroup `memory.current/memory.max`、缓存条目数／字符串数和摘要耗时。D/F 必须按四候选峰值测量，不能用 B 外推。容量不足只阻断相应缓存臂，不允许落盘缓存、索引或数据副本，也不能预填猜测 ETA。

## 八、真实中断验收计划

不创建人工夹具、单元测试或集成测试，不使用合成域名。本轮不执行以下命令；由 Luna 实现后按顺序完成。

### 8.1 语法、导入和入口

从 `thesis/experiments/llm_probe` 执行：

```bash
PYTHONPYCACHEPREFIX=/tmp/ch3-drift-formal-pycache \
  /opt/miniconda3/envs/rwkv/bin/python -m py_compile \
  tools/ch3_drift_official_p2p3_formal.py \
  tools/ch3_drift_bresnet_p2p3_formal.py

/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_official_p2p3_formal.py --help
/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_bresnet_p2p3_formal.py --help
```

不运行 `black` 或其他自动格式化器。这些检查不证明恢复正确。

### 8.2 全源缓存重建审计

两个正式训练入口的既有 `--audit` 模式须在各自真实工程运行目录中读取正式源与合法检查点，重建缓存但不执行模型更新：

```bash
source tools/env/activate.sh
uv run --no-sync python tools/ch3_drift_official_p2p3_formal.py \
  --config configs/ch3-drift-official-p2p3-formal-v3.json \
  --run-dir <DRIFT真实工程运行目录> --arm <B或D> --audit

uv run --no-sync python tools/ch3_drift_bresnet_p2p3_formal.py \
  --config configs/ch3-drift-bresnet-p2p3-formal-v1.json \
  --run-dir <B-ResNet真实工程运行目录> --arm <B或D> --audit
```

分别覆盖 `drift_b_setdefault_v1`、`drift_df_base4_v1`、`bresnet_b_if_missing_v1`、`bresnet_df_base4_v1` 四个策略；D/F 共用生成策略时以代码身份断言两臂确实调用同一路径。审计只写 `cache-rebuild-audit.json`：运行／输入／代码身份、游标、策略、条目数、字符串数、根摘要、重建时间和峰值资源，不含任何实体或字符串。

### 8.3 真实中断与继续

1. 对每个缓存策略使用真实源、冻结批量和新工程身份运行到既有计划规定的断点边界，确认断点原子完成后中断；不新增保存频率或缩小正式输入。
2. 首轮中间断点若按既有间隔实际存在，验证“首轮前缀”重建；首轮末断点验证完整缓存。DRIFT B 还须从首轮末恢复进入下一轮，以覆盖缓存命中仍消耗 `variant_rng` 的路径。
3. 在恢复前由 `--audit` 重建缓存，条目数、字符串数和根摘要必须与断点完全相同；源顺序、标签、代码、策略或摘要任一不符必须非零退出。
4. `--resume` 先重建并核对缓存，再恢复检查点状态。恢复后的第一批记录主样本主键根、实际入批增强根、缓存根、游标和 `rng_variant` 状态摘要；只保存摘要。
5. 与同一检查点未中断路径的下一批摘要逐项严格相同。继续到下一个既有断点后，再核对缓存根／计数和 `rng_variant` 状态摘要；DRIFT B 与 B-ResNet B 分别验收，不能用一侧替代另一侧。
6. 模型分数或权重若因同设备前向仍有已知数值噪声，只记录实测差异，不自行新增容差；缓存根、输入批根、游标和随机状态摘要仍必须严格相同。

上述工程收据通过只证明恢复输入与缓存语义一致，不是科学效果实验。任何缓存策略未通过时只阻断使用该策略的正式臂；不阻断直读接口、A/G 或其他已验证策略。

## 九、失效条件与交付

以下任一变化使当前恢复算法失效，必须新建策略身份和实施简报后才能恢复旧游标：

- `SourceStore` 顺序、标签、去重方式或输入处理变化；
- 首轮不是固定完整排列，实体可能首轮重复／漏过，或动态批处理改变索引访问顺序；
- 批量、种子、`perturb2` 实现、候选数或生成调用顺序变化；
- 缓存条目被更新、删除、淘汰，或候选生成开始依赖模型分数／参数；
- DRIFT B 改掉或新增 `setdefault` 命中副作用，或 B-ResNet B 引入该副作用；
- 两骨干共享可变 RNG／缓存，或恢复时重放生成器污染检查点随机状态；
- 容量不足而试图改成磁盘缓存、成员副本、索引或派生数据。

实施报告必须列出实际修改文件、四个策略的代码哈希、所有检查命令与返回码、真实中断运行身份、检查点和审计收据路径、缓存／批／随机状态摘要、CPU 重建成本、峰值资源、失败保留行为和未验证项。只有主代理核验原始收据后，才能把相应策略从“真实验证待做”改为“工程恢复通过”；不得写成 F、B、D 或任一骨干的科研有效性证据。
