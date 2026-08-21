# XGBoost＋CPA-ELP 运营指标零训练回填计划

## 目标

为第三章冻结的 `XGBoost＋CPA-ELP` C11 目标年结果新增一个独立、零训练、目标只评价的运营指标回填入口。入口只重建一次 LSPR24 `semantic168`，只用冻结最终模型执行一次 GPU 打分，并在内存中生成实际可达六档检测率、完整同分组告警预算曲线，以及按 1 基实体内曝光序号定义的首次告警未告警率、分位数和按时检出曲线。

## 文件所有权

- 新增 `thesis/experiments/llm_probe/tools/ch3_xgb_cpa_elp_operational_backfill.py`。
- 新增 `thesis/experiments/llm_probe/configs/ch3-xgb-cpa-elp-operational-backfill-v1.json`。
- 新增 `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_xgb_cpa_elp_operational_backfill_v1.sh`。
- 新增本目录 `实施报告.md`。
- 不修改既有 continuation、父模型、统一总表、总表来源配置、运行目录、恢复卡或路线总控。

## 冻结身份与失败门

- 父运行固定为 `ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1`。
- 目标完整模型固定为 `model_semantic168.json`，SHA-256 必须等于 `1805e15d96ac4ebb57df910640a4c5e1af58f692659db2eb80b724851efe42e9`。
- 模型必须实际加载为 800 树；父选择必须为 `semantic168` 与 `p_semantic168=1.0`。
- 必须核验父配置、选择收据、有效配置收据、父模型，以及已完成目标评价 continuation 的状态、结果、清单和哈希。
- 目标年固定为已访问的描述性评价池；`target_retrained=false`、目标分数调用次数为 1、逐流和逐实体分数均不持久化。

## 数据与接口合同

| 项 | 冻结值 |
| --- | --- |
| 目标缓存 | `X24/y24/I24/M24/s24/d24/t24` |
| 禁止缓存 | `raw83` 单独评价、任何源年数组、三折或折外数组 |
| 输入表示 | 由 `X24＋I24＋M24` 在内存重建一次 `semantic168` |
| 实体键 | `s24/d24` 构造无向地址对 |
| 实体顺序 | `I24/M24` 冻结序列顺序；以 `t24` 核验每段时间非降 |
| 最终实体分数 | C11，`p=1` 的全曝光算术平均 |
| 六档预算 | `0.1%/0.5%/1%/2%/4%/8%`，阈值保留完整负类同分组 |
| 完整曲线 | 每个实际可达负实体数只保留一个同分组点，不做名义预算插值 |
| 首次告警 | 从实体第一条合法流起按 1 基 `exposure_index` 计数，在线分数为前缀算术平均 |
| 时间时延 | `time_delay_available=false`，不得从 `t24` 猜测真实可用时刻或单位 |
| 持久化 | 仅聚合 JSON、聚合曲线 NPZ、资源收据、状态、日志和 manifest |

本任务不新增数据视图、模型适配器、训练机制或科研超参数，因此无需重新建立数据集－模型适配表或朱论文机制对位表。它只补齐现有冻结 C11 的评价制品。

## 阶段

- [x] P0：读取根规则、`llm_probe`、`scripts` 与 RWKV 路线规则，恢复第三章事实。
- [x] P0：审计 continuation、父恢复证明器、统一总表曲线与首次告警接口、MLP/RWKV 首次告警实现。
- [x] P0：先创建并独立提交计划与证据笔记。
- [ ] P0：实现配置静态合同、父选择/配置/模型/缓存/时间顺序/目标只评价失败门。
- [ ] P0：实现一次 `semantic168` 重建、一次 GPU 打分及内存聚合。
- [ ] P0：实现六档实际可达 DR、完整同分组曲线和首次告警聚合制品。
- [ ] P0：实现资源门、阶段原子状态、幂等恢复和唯一远程启动命令。
- [ ] P1：运行 `py_compile`、导入、`--help`、`--validate-config`、`bash -n` 和静态身份检查。
- [ ] P1：更新实施报告，共享暂存检查后只提交独占文件。

## 验收命令

```bash
source tools/env/activate.sh
uv run --no-sync python -m py_compile tools/ch3_xgb_cpa_elp_operational_backfill.py
uv run --no-sync python -c 'import importlib.util, pathlib; p=pathlib.Path("tools/ch3_xgb_cpa_elp_operational_backfill.py"); s=importlib.util.spec_from_file_location("xgb_operational_backfill", p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)'
uv run --no-sync python tools/ch3_xgb_cpa_elp_operational_backfill.py --help
uv run --no-sync python tools/ch3_xgb_cpa_elp_operational_backfill.py --config configs/ch3-xgb-cpa-elp-operational-backfill-v1.json --validate-config
bash -n scripts/remote_launchers/run_ch3_xgb_cpa_elp_operational_backfill_v1.sh
```

不运行 `black`、人工夹具、单元测试、集成测试、真实实验或任何服务器命令。

## 资源与阻塞条件

- GPU 空闲显存门：至少 11 GiB。
- 控制组可用主存门：至少 48 GiB。
- 项目盘可用空间门：至少 10 GiB，且使用率低于 80%。
- 墙钟上限：无。
- 任一父身份、制品哈希、树数、缓存形状、时间顺序、目标只评价或 manifest 完整性断言失败即停止；禁止以重训、重选、读取 `raw83`、持久化分数或修改旧运行补救。

## 当前状态

计划与证据审计完成，等待独立文档提交后进入实现。
