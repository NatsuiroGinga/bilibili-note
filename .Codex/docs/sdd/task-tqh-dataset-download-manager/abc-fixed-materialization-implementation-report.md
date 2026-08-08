# TQH-C2 A/B/C 固定预算物化器实施报告

## 结论

合同任务 1–3 的本地首版已经完成。实现新增固定 36-cell 分配、每 cell 最多 1,000 条的确定性比例抽样、兼容行组内交错样本的目标包过滤聚合器，以及新的预算候选协议命令入口。

本轮未连接服务器、未运行 `pytest`、未读取或物化完整包表、未创建真实协议输出，也未执行 Git 提交。

## 修改文件

- `thesis/experiments/llm_probe/configs/tqhc2_abc_fixed_assignment_v1.json`
  - 使用本地已批准 A/B/C 主记录的 36-cell 统计执行唯一一次既有受约束组合搜索。
  - 冻结四个套件的 `train/validation/test` 分配和生成审计。
  - 固定预算为 35,235 条流、2,475,729 条包，来源映射流为 303,599 条。
  - 文件 SHA-256 为 `f3af9b362837d617216ab12b224642aa83bbeecadbf0f30750e8349ecff925fc`。
- `thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate_abc_fixed.py`
  - 新增 `load_fixed_suite_groups`，拒绝缺失、额外、重复或绑定不一致的 cell，并检查四套分配的 cell 数、留出 profile 和硬覆盖。
  - 新增 `select_budget_samples`，使用整数最大余数配额；余数并列时按标签字典序裁决，类内按 `sha256("tqhc2-abc-budget-v1|" + sample_id)` 排序。
  - 新增 `filter_and_aggregate_budget_packets`，逐 profile、逐 Parquet 行组扫描，只保留冻结目标 `sample_id`；按 `sample_id, packet_index` 稳定排序后复用既有 `_aggregate_features` 与规范序列哈希语义。
  - 增加未知样本、profile/cell 绑定、cell 顺序回退、包序号重复/缺口/回退、主记录计数、模型字段有限性与全量目标覆盖检查。
  - 新增 `materialize_candidate_abc_budget`，写出 `samples.parquet`、`groups.parquet`、12 份 JSONL 清单、字段角色、来源、审计、制品哈希和 `protocol.yaml`；失败保留 `_INCOMPLETE`，成功后删除该标记。
  - 协议记录固定分配 SHA-256、样本清单 SHA-256、抽样算法、源码 SHA-256、峰值常驻内存记录要求和 `review_pending` 限制。
- `thesis/experiments/llm_probe/tests/test_tqh_c2_candidate_abc_fixed.py`
  - 覆盖固定分配校验、预算配额、可复现性、行组内交错、跨行组续接、非法包序号、未知样本、计数不一致、cell 顺序回退、双输出逐字节一致、冻结协议加载、拒绝覆盖和失败标记保留。
- `thesis/experiments/llm_probe/pyproject.toml`
  - 注册 `flow-probe-materialize-tqh-c2-abc-budget = "flow_probe.tqh_c2_candidate_abc_fixed:main"`。

## 未修改文件

- `thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate_abc.py`
- 历史 C-only 物化器、通用 A/B/C 命令和既有运行制品。
- 两份高层恢复文档与实验总控。

## 静态检查

首次尝试：

```text
UV_CACHE_DIR=/tmp/uv-cache uv run --frozen black ...
```

结果：失败。入口变更触发 `uv` 重建可编辑包，受限网络无法访问镜像并解析 `hatchling>=1.27`。该失败发生在 Black 启动前，不是源码格式或语法错误。

随后直接使用既有虚拟环境工具：

```text
.venv/bin/black src/flow_probe/tqh_c2_candidate_abc_fixed.py tests/test_tqh_c2_candidate_abc_fixed.py
```

结果：通过，两个 Python 文件已格式化。

```text
PYTHONPYCACHEPREFIX=/tmp/tqh-abc-fixed-pycache .venv/bin/python -m py_compile src/flow_probe/tqh_c2_candidate_abc_fixed.py tests/test_tqh_c2_candidate_abc_fixed.py
```

结果：通过，无语法错误。

## 未执行门禁

- 按本机规则未运行任何 `pytest`；精确行为测试需要在服务器项目 `uv` 环境中执行。
- 未运行 Ruff；当前分派明确限定本机只运行 Black 与 `py_compile`。
- 未执行真实预算物化、双目录逐字节比较、峰值常驻内存测量或正式发布。
- 未执行独立代码审查，协议状态必须继续保持 `review_pending`。

## 遗留风险

- 当前仅有静态检查证据，行为正确性仍需服务器精确测试确认。
- 真实包表扫描的总时长、峰值常驻内存、最终保留包数和双物化一致性尚未验证。
- 任务 4 的独立审查发现严重或重要问题时，不得启动或保留真实物化结果。
