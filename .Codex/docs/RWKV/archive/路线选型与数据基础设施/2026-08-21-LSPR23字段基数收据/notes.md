# LSPR23 字段基数收据笔记

## 已核验事实

- 既有 TabM4 Protocol A 的 `source_split`：先对 `np.unique(E23)` 用 `np.random.RandomState(42)` 排列，前 `max(1, int(n*0.1))` 个实体为验证实体；再以 `np.quantile(T23, 0.85)` 定义时间尾部。训练行是 `~(entity_mask | time_mask)`，验证行是 `entity_mask & ~time_mask`。
- 既有断言要求 `150680` 个序列实体、`208598` 个训练序列、`22444` 个验证序列且训练验证序列行交集为零。
- 七个字段及固定列顺序来自 `tools/dijk2026_replication/dijk_fields.py`：`SrcPort`、`DstPort`、`Protocol`、`L3/L4 Protocol`、`Int/Ext Dst IP`、`External_src`、`External_dst`。
- N-12 当前状态为 `WAITING_FOR_CODEX_CARDINALITY_RECEIPT`，需要本收据的字段基数、覆盖率、训练有效流数、切分身份及数组/字段清单哈希；本收据不做编码方案裁决。

## 未运行事项

- 本代理按边界未访问服务器、未同步、未启动诊断。主进程可用启动器的唯一命令运行。
