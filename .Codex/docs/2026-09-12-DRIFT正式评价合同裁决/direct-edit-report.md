# 正式评价按需共享编辑算子报告

## 结论

按需共享编辑算子已完成并通过真实 T17 DGA 验证集审计。该结果只证明编辑算子、确定性、预算、汉明距离和前缀关系满足合同，**不表示任何训练臂或检测方法有效**。

## 变更范围

新增文件：

1. `thesis/experiments/llm_probe/tools/ch3_drift_formal_edit.py`
2. `thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-formal-edit-t17-validation-v1/direct-edit-audit.json`
3. `thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-formal-edit-t17-validation-v1/attack-collision-audit.json`
4. `thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-formal-edit-t17-validation-v2-batch4096/` 与 `ch3-drift-formal-edit-t17-validation-v2-batch16384/` 下的两组审计收据
5. 本报告和 `direct-edit-skill-receipt.json`

未修改现有合同模块、三份配置、MP 或 BResNet 代码、训练进程、依赖锁和任何输入 Parquet。没有物化成员数据集、攻击数据集、逐实体攻击清单或模型制品。

## 公共接口

```text
generate_shared_edits(
    exact_esld: str,
    *,
    attack_namespace: str,
    revision: str,
    alphabet: str = DEFAULT_ALPHABET,
) -> dict[str, Any]

generate_shared_edit_stream(
    exact_esld: str,
    *,
    attack_namespace: str,
    revision: str,
    alphabet: str = DEFAULT_ALPHABET,
) -> dict[str, Any]
```

返回值包含 `attack_stream_id`、三档请求／实际预算、`degenerate_budget` 和每档的内存字符串、汉明距离及 UTF-8 `output_sha256`。调用方评分后即可释放内存；审计收据不包含原域名或攻击字符串。

## 确定性算法

- 流身份严格复用合同的 `SHA256(length_prefix_encode(attack_namespace, revision, exact_esld))`，不含年份、面板、骨干、训练臂或自由种子。
- 计数器从 0 开始，以 8 字节大端整数拼接在 `length_prefix_encode(stream_id)` 后，逐块计算 SHA-256；每个 32 字节摘要按 8 字节大端无符号整数顺序消费。
- 每次从 `[0, n)` 取整数时使用 64 位拒绝采样：令 `limit = 2^64 - (2^64 mod n)`，仅接受小于 `limit` 的字；没有直接取余偏差。
- Fisher–Yates 从位置 `L-1` 递减到 `1`，抽取无放回位置排列。按排列顺序从配置字符表排除该位置原字符后均匀抽取替换字符。
- `q1=min(1,L)`、`q2=min(2,L)`、`qh=min(max(1,floor(L/2)),L)`；三个档位使用同一位置与替换字符流的对应前缀。空字符串拒绝，不执行 `strip`、大小写转换或 eSLD 重建。
- 长度导致实际预算重复时保留真实输出并置 `degenerate_budget=true`；不伪称三档始终严格递增。

## 真实输入与聚合结果

配置规范哈希为 `21ade01a084c1c52aff74f6922fc8400e30875542e2830fd98d7a82d71cac680`。首次实现审计代码哈希为 `7ca0c5e9a5c8f5010efe78b0db529b3f6d4bb4645beba0b86ff886fa189ea57e`；本轮加入合同编码复用、替换字符前缀核对和 Parquet 元数据行数核对后的修订代码哈希为 `6a430727fa50d6b4b14e8ba4b83cbf828c6cadfb2b3c72f89226bbb5abdd00bd`。

审计只读取：

`thesis/experiments/llm_probe/runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521/DRIFT_input_eSLD/T17_dga_val.parquet`

输入文件 SHA-256 为 `dfd47b8e99837c0567b4da81595a55fe12aa0a452372694e552656454a14a0a4`。结果如下：

| 项目 | 结果 |
| --- | ---: |
| 读取行数 | 150,000 |
| Parquet 元数据行数 | 150,000 |
| 有效行数 | 150,000 |
| 全文件处理核对 | 通过 |
| 三档确定性通过 | 150,000 |
| 三档预算／汉明／前缀通过 | 150,000 |
| 预算退化行数 | 349 |
| `half_weaker_than_k2` 行数 | 0 |
| 未记录失败 | 0 |
| 跨输入输出碰撞 | 1（`k=1`） |

碰撞仅以输出哈希和两个输入哈希记录在 `attack-collision-audit.json`，未保存对应字符串。三档输出聚合根摘要分别为：

```text
k=1          0679eb46e3eb573e278c4c253008f82f20b76dca3c0515684a1f21e189bd6ce6
k=2          f681737cf462b2df57963e2915208d6de3d0bdd932c7cf8501c6ce6b12a39336
random_half  43f23a62aa45b11b4ebfee53b8701865d13a61e031c7edc0e4e332b5f17073c4
```

修订代码以批次 4096 和 16384 分别在两个独立进程中全量复算；两次收据的三档 `root_sha256` 与 `xor_digest` 完全一致，源文件哈希和元数据行数也一致。

## 验证命令

- `/opt/miniconda3/envs/rwkv/bin/python -m py_compile thesis/experiments/llm_probe/tools/ch3_drift_formal_edit.py`：通过。
- 导入模块后检查 `torch`、`numpy`、`pyarrow`：均未加载。
- `--help` 入口检查：通过。
- 使用本机唯一实验解释器执行 `--audit --scope t17-validation`：通过，输出上述两份聚合 JSON 收据。
- 两个独立进程以批次 4096、16384 分别执行同一真实 T17 全量审计：均通过，聚合根摘要逐档一致。
- `git diff --check`：通过。
