# 第三章定稿模型权重归档（协议 A）

本目录保存**第三章正文采用的那一批模型**的权重。第三章表格里的四格数字就是用这四份权重
在 LSPR24 上算出来的，逐位可复现。

## 一、这是哪一批模型

- **检查点策略：协议 A** —— 跑满 20 epoch 不早停，逐 epoch 在 **LSPR23 实体不相交验证集**上算逐流 AP，
  取该 AP 最大的**单个** epoch 的权重。**没有末 5 个 epoch 权重平均，也没有多检查点概率集成。**
- 训练数据 LSPR23 全量（208,598 条训练序列），选择信号只来自 LSPR23 的 22,444 条实体不相交验证序列。
- 种子 42，无学习率调度器，训练确定性。
- 四格选中的 epoch 分别是：**C00 第 14、C01 第 14、C10 第 19、C11 第 10**。

## 二、四格各自是什么

因子 A 是「因果前缀聚合」（`aggregate_enabled`），因子 B 是「可学习 Lp 序列级池化」（`lp_enabled`）。

| 格 | A 因果前缀聚合 | B Lp 池化 | 角色 |
| --- | --- | --- | --- |
| `C00` | 关 | 关 | 基线：逐流 MLP |
| `C01` | 关 | 开 | 仅 Lp 池化 |
| `C10` | 开 | 关 | 仅因果前缀聚合 |
| `C11` | 开 | 开 | **完整方法 CPA-ELP** |

`lp_enabled=False` 的两格里 `p_log` 保持初值（`p = 2.0`），不参与实体聚合口径；
它们的实体级指标用 max 聚合，等价于 Lp 在该格退化为 max。

## 三、与同一仓库里另一份归档的区别（不要弄混）

本 Hugging Face 仓库里有**两批权重，协议不同，数字不同，不可互换**：

| | 本目录 `protocol-a-final/` | 仓库根的 `checkpoints/`（冻结协议） |
| --- | --- | --- |
| 检查点策略 | 协议 A：验证集单 epoch argmax | 冻结协议：末 5 个 epoch，step-16000~20000 |
| 每格权重数 | 1 份 | 5 份 |
| 推理口径 | 单检查点直接打分 | 末五检查点逐流概率算术平均 |
| 是否为第三章正文数字 | **是** | 否 |
| 来源运行 | `runs/diagnostics/ch3-final-weights` | `runs/diagnostics/ch4-entity-length-bucket-diagnostic-seed42-v1` |

**第三章正文引用的是本目录这一批。** 冻结协议那批用于第四章分桶诊断，两者的实体 AP 相差可达数个百分点，
互相替换会导致正文数字对不上。

## 四、输入约定

模型吃的是**已标准化**的 83 维逐流特征。缓存约定是：先用 LSPR23 的逐列均值/标准差标准化，
再裁剪到 `[-10, 10]`，非有限值置 0。`runs/diagnostics/dijk-repro/cache/X23.npy`、`X24.npy` 就是这个约定。

字段口径对齐 Dijk 2026 附录 A 的 83 字段：端口、协议与粗粒度拓扑指示允许入模；
原始 IP 只作分组键，标签派生字段、既有 IDS 输出、演习身份字段一律不入模。

若手上是**未标准化**的原始特征，需要标准化统计量（`mean`/`std`）与字段顺序，
它们在同仓库根目录的 `normalization.json` 与 `features.json`（与本批权重共用同一份缓存统计量）。

## 五、推理

```bash
uv run --no-sync python inference.py \
  --package-root . --cell C11 \
  --x-npy     runs/diagnostics/dijk-repro/cache/X24.npy \
  --index-npy runs/diagnostics/dijk-repro/cache/I24.npy \
  --mask-npy  runs/diagnostics/dijk-repro/cache/M24.npy \
  --input-convention standardized-cache \
  --out-npy /tmp/scores_C11.npy
```

`--input-convention` 必须显式给。给错约定不会报错，只会安静地输出错误分数。

## 六、第四章从哪里接续

- **接 `C11`**，它是完整方法 CPA-ELP，也是第三章主表里代表本方法的那一格。
  `C00/C01/C10` 只在需要重做机制消融或对照时才用。
- 载入：`C11/weights.safetensors` → `inference.py` 里的 `Model(83, 192, aggregate=True)`。
  实体级聚合要用 `C11/config.json` 里 `selected.p_at_selected` 记录的 Lp 指数，
  不能用初值 2.0，也不能改用 max（改了实体 AP 会掉十几个百分点）。
- 配套数据：`runs/diagnostics/dijk-repro/cache/` 下的 LSPR23/LSPR24 缓存
  （`X*/y*/I*/M*/E23/T23/s24/d24/t24`）。实体键的构造是无序 IP 对 `min|max`，
  实体标签取该实体下逐流标签的最大值。
- 注意事项：
  1. **LSPR24 不是独立测试集。** 它已在多轮人机循环中反复用于探索性评价，
     第四章若要声称泛化增益，需要另立不可见的最终测试集。
  2. 第三章的结论对检查点策略**不稳健**：换成末 5 平均（冻结协议）会得到相反的排序结论。
     第四章在此基础上做改进时，必须固定协议 A，不要中途换检查点策略。
  3. LSPR23 实体不相交验证集只有 20 个正例实体，验证 AP 已接近 1.0，
     它只能用来选 epoch，不能当作有分辨力的模型比较信号。
  4. 模型只有 90,242 个参数，训练两分钟量级，重跑成本远低于加载归档；
     归档的价值在于**锁定第三章正文那一批具体权重**，不是省算力。

## 七、边界

- 模型只供研究复核与第四章接续，不得直接用于生产告警或安全处置。
- 包内不含数据、缓存、IP、标签、实体标识或逐样本预测。
- `metrics.json` 里的 LSPR24 指标只供研究复核，不得解释为独立测试性能。
