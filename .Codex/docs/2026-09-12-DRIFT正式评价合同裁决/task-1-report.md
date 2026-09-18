# 任务 1：正式配置与共享合同报告

## 结论

任务 1 的纯 CPU 合同层已完成。三份配置通过严格读取；30 个真实输入角色全部存在并通过 Parquet 元数据核对；合同模块导入不加载 PyTorch、NumPy、PyArrow 或设备后端。成员物化、模型训练、模型评价和臂间比较仍未实现，入口不会创建虚假完成状态。

## 变更文件

仅新增以下文件：

1. `thesis/experiments/llm_probe/configs/ch3-drift-formal-evaluation-v1.json`
2. `thesis/experiments/llm_probe/configs/ch3-drift-official-p2p3-formal-v3.json`
3. `thesis/experiments/llm_probe/configs/ch3-drift-bresnet-p2p3-formal-v1.json`
4. `thesis/experiments/llm_probe/tools/ch3_drift_formal_contract.py`
5. 本报告
6. `task-1-skill-receipt.json`

未修改 `pyproject.toml`、`uv.lock`、通用启动器、旧脚本、恢复卡、模型、数据和运行制品。本任务未引入 SciPy。

## 配置合同

- 评价配置冻结 revision `3b31077020cd1c013d0a75cad51042a2327c4521`，完整列出 T17–T19 的 18 个源角色及 T20–T25 的 12 个无后缀目标角色。
- 正式面板仅为 `target_official_annual_v1` 与 `source_validation_benign_v1`；`target_new_entity_annual_v1` 保留为 `formal=false` 的资格收据候选。
- 成员规则为 `exact_esld` 去重、UTF-8 8 字节大端长度前缀、摘要升序、每年每类 `min(200000, unique_count)`；配置没有 `member_seed` 字段，也不接受成员种子。
- 正式攻击严格为 `k=1`、`k=2`、`random_half` 共享前缀档位；`krand`、`maskdga`、可变目标上限和阈值覆盖均声明为禁止键。
- 阈值工作点固定为 `tau_0p1=0.001` 与 `tau_1p0=0.01`，同分数整组处理，判定规则为 `score >= threshold`。
- DRIFT 配置：A/B/D/F/G 单臂选择，批量 1024、3 轮、种子 42、Adam、骨干学习率 `1e-6`、头学习率 `1e-4`、良性权重 3.0、训练期判定 0.5，断点版本为 `ch3_drift_official_p2p3_formal_checkpoint_v3`。批量 1024 来自主方案 §5.7/§5.6 后段冻结正式运行配置及既有正式运行收据。
- BResNet 配置：A/B/D/F/G 单臂选择，批量 128、3 轮、种子 42、Adam、全参数学习率 `1e-3`、良性权重 3.0、训练期判定 0.5，断点版本为 `ch3_drift_bresnet_p2p3_formal_checkpoint_v1`。B 臂是拟实现身份，不继承历史 B 运行或读数。

当前规范配置哈希（规范 JSON SHA-256）：

- 评价：`21ade01a084c1c52aff74f6922fc8400e30875542e2830fd98d7a82d71cac680`
- DRIFT：`27d6606d8f063345b9b3e02dd5ef955abba9553eca0ac15519bc3a26d6811ee1`
- BResNet：`232ec1eb1931b2cbe57a130ebfec7eafc46d4a76f5bea6d539b16ae88a8cd429`

## 公共接口

后续生产模块只应消费以下接口：

```text
canonical_json_bytes(value: Any) -> bytes
sha256_bytes(value: bytes) -> str
sha256_file(path: Path, chunk_size: int = 1048576) -> str
length_prefix_encode(*fields: str) -> bytes
member_hash(namespace: str, revision: str, panel_id: str, year: int, class_name: str, exact_esld: str) -> str
attack_stream_id(attack_namespace: str, revision: str, exact_esld: str) -> str
resolve_repo_relative(path_value: str | Path, *, must_exist: bool = False) -> Path
resolve_run_dir(path_value: str | Path) -> Path
load_config(path_value: str | Path) -> tuple[dict[str, Any], str]
atomic_write_json(path_value: str | Path, payload: Mapping[str, Any]) -> str
read_status(run_dir_value: str | Path) -> dict[str, Any] | None
transition_status(run_dir_value: str | Path, new_status: str, *, stage: str, error_class: str | None = None, recoverable: bool = True) -> str
audit_input_roles(config: Mapping[str, Any]) -> dict[str, Any]
```

命令入口为：

```text
python tools/ch3_drift_formal_contract.py --gate assets|train|evaluate|compare --config <仓库相对路径> --run-dir <仓库相对路径> [--backbone drift|bresnet] [--arm A|B|D|F|G] [--audit|--materialize|--run|--resume|--summarize]
```

`assets --audit` 仅表示配置和真实输入角色审计通过，输出 `audit_complete=true`、`input_roles_complete=true`、`assets_complete=false`、`complete=false`；它不表示成员等正式资产已完成。训练、评价和比较的审计输出 `contract_valid=true, complete=false, downstream_status=未实现`。`--materialize`、`--run`、`--resume`、`--summarize` 在下游模块存在前以退出码 2 失败关闭。

状态迁移仅允许 `created→running→complete` 或进入 `failed`；只有 `recoverable=true` 的失败状态可按同一身份回到 `running`，不会由合同层为下游创建空的 `complete` 状态。路径解析以仓库根为固定主根，`configs/`、`runs/`、`tools/`、`scripts/` 短路径显式映射到 `thesis/experiments/llm_probe/`，不依赖当前工作目录，符号链接解析越出允许根时失败。`resolve_run_dir` 进一步要求运行目录位于 `llm_probe/runs/` 下，命令行 `--run-dir` 和状态写入均经过该门。

## 真实验证

所有命令均从本机唯一实验解释器 `/opt/miniconda3/envs/rwkv/bin/python` 执行，未导入模型或占用 MPS：

| 检查 | 结果 |
| --- | --- |
| `-m py_compile tools/ch3_drift_formal_contract.py` | 退出码 0 |
| 评价配置 `--gate assets --audit` | 退出码 0，30/30 角色 |
| DRIFT 配置 `--gate train --backbone drift --arm F --audit` | 退出码 0，合同有效，下游未实现、`complete=false` |
| `import ch3_drift_formal_contract` 后检查 `sys.modules` | `torch=False`、`numpy=False`、`pyarrow=False` |
| `--help` | 退出码 0 |
| 训练配置 `--summarize` | 退出码 2，明确“下游生产模块尚未实现” |
| 30 个实际 Parquet 元数据读取 | 退出码 0，全部字段 `domain,label`、角色无重复 |

30 个真实文件的元数据核对摘要如下；T25 的两个带 `_test` 后缀文件未纳入合同。

| 角色 | 字节数 | 行数 | 行组数 |
| --- | ---: | ---: | ---: |
| T17_benign_train | 18,025,405 | 1,500,000 | 2 |
| T17_benign_test | 3,255,096 | 263,418 | 1 |
| T17_benign_val | 1,912,958 | 150,000 | 1 |
| T17_dga_train | 28,292,145 | 1,500,000 | 2 |
| T17_dga_test | 249,175,714 | 13,238,780 | 13 |
| T17_dga_val | 2,910,706 | 150,000 | 1 |
| T18_benign_train | 20,909,890 | 1,500,000 | 2 |
| T18_benign_test | 210,813,709 | 15,166,488 | 15 |
| T18_benign_val | 2,181,256 | 150,000 | 1 |
| T18_dga_train | 28,272,010 | 1,500,000 | 2 |
| T18_dga_test | 253,220,479 | 13,465,679 | 13 |
| T18_dga_val | 2,914,766 | 150,000 | 1 |
| T19_benign_train | 20,954,840 | 1,500,000 | 2 |
| T19_benign_test | 280,409,687 | 20,128,914 | 20 |
| T19_benign_val | 2,188,663 | 150,000 | 1 |
| T19_dga_train | 26,943,190 | 1,500,000 | 2 |
| T19_dga_test | 264,790,180 | 14,768,573 | 15 |
| T19_dga_val | 2,779,236 | 150,000 | 1 |
| T20_benign | 225,640,613 | 17,641,109 | 17 |
| T20_dga | 315,129,538 | 18,693,748 | 18 |
| T21_benign | 184,399,715 | 14,529,793 | 14 |
| T21_dga | 327,739,910 | 19,544,570 | 19 |
| T22_benign | 198,898,646 | 15,582,922 | 15 |
| T22_dga | 330,100,350 | 19,763,134 | 19 |
| T23_benign | 56,321,783 | 4,699,668 | 5 |
| T23_dga | 330,144,406 | 19,761,563 | 19 |
| T24_benign | 20,742,059 | 1,871,063 | 2 |
| T24_dga | 348,036,553 | 20,795,174 | 20 |
| T25_benign | 22,393,269 | 2,016,200 | 2 |
| T25_dga | 349,193,153 | 20,843,220 | 20 |

## 边界与后续

- 本任务没有物化成员清单，因此未宣称去重、冲突、重合或资格审计已完成；这些由任务 2 生成真实收据。
- 本任务没有生成攻击资产、模型检查点、逐实体分数或比较区间；这些下游缺失不会被合同入口伪装成完成。
- 新实体资格政策和配对重采样参数保持未冻结，未写入猜测默认值。
- 本报告未运行人工夹具、单元测试、集成测试、自动格式化器或 Git 操作。

## 本轮修订

主代理复核后已修正：DRIFT 批量由 256 冻结为 1024；`epochs=3` 与 `seed=42` 改为严格值断言；路径解析取消任意 `cwd` 回退并增加符号链接越界门；配置要求 `panels` 实际包含全部批准面板；规范 JSON 拒绝 NaN/Infinity；状态字段和不可恢复失败迁移严格校验；资产审计输出不再使用 `complete=true` 表示正式资产完成；删除未使用的 `secrets` 导入。

本轮复核得到 DRIFT 规范配置哈希 `27d6606d8f063345b9b3e02dd5ef955abba9553eca0ac15519bc3a26d6811ee1`；BResNet 哈希保持 `232ec1eb1931b2cbe57a130ebfec7eafc46d4a76f5bea6d539b16ae88a8cd429`，评价配置哈希保持 `21ade01a084c1c52aff74f6922fc8400e30875542e2830fd98d7a82d71cac680`。重新读取三份配置均通过；30 个真实 Parquet 存在性和元数据复核通过，字段集合为 `{domain,label}`，合计 262,674,016 行、265 个行组。未运行自动格式化器、人工夹具、单元/集成测试或 Git 操作。

## 第二轮修订后的真实审计状态记录

`_validate_input_roles` 现在要求每项同时满足 `role = f"T{year}_{class}_{split}"`（目标角色为 `f"T{year}_{class}"`）以及 `path = f"{input_root}/{expected_role}.parquet"`，从而将角色名称、字段组合和具体文件路径绑定。三份配置重新严格加载后，对 30 个真实 Parquet 逐文件读取元数据，字段集合为 `{domain,label}`，无缺失角色。

使用真实输入执行 `audit_only` 状态链，未物化成员、攻击或模型资产：

执行命令为：`/opt/miniconda3/envs/rwkv/bin/python` 运行一次内联审计入口，调用 `load_config("thesis/experiments/llm_probe/configs/ch3-drift-formal-evaluation-v1.json")`、`audit_input_roles(config)`、30 个 `pyarrow.parquet.ParquetFile` 元数据读取，以及 `transition_status(run_dir, "created|running|complete", stage="audit_only")` 和 `read_status(run_dir)`；命令返回码为 0。

```text
状态路径：thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-contract-audit-v1/status.json
created  SHA-256：0273067d41b6c979c031dbb5f71e32a27afd90919c7a4efa748f78fb130cf135
running  SHA-256：fdc4ca363753ed7dd493c1d1b2ca81a97337c83b05dc9ab92e0754ef2e236246
complete SHA-256：0eea3f0b21c9ce67ab771678aaa287100cac1baa7d9d47329f7ca4dbc5fdb453
读回：{"status":"complete","stage":"audit_only","error_class":null,"recoverable":true}
审计结果：{"input_roles":30,"audit_only":true,"formal_assets_complete":false}
```

该 `complete` 仅表示真实输入审计阶段完成，不表示正式资产完成；状态文件保留在独立的 `contract-audit` 运行身份下，后续物化仍需任务 2 生成自身清单和完成收据。
