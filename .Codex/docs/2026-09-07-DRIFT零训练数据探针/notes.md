# DRIFT-DGA 2026 零训练数据探针笔记

## 2026-09-07 初始化

- 用户指定数据集为 `snsec-net/dga-detection-drift26dsn`。
- 上游比较综述将其定位为 2026 年独立长期漂移终测，研究对象是域名检测；其不能替代带实体历史的加密流告警主任务。
- 本探针只允许公开只读元数据、远端聚合与最小公开行预览；小样观察不构成总体分布结论。

## 待记录证据

- Dataset Viewer：有效性、配置、切分、首行、大小、统计、Parquet 分片。
- CLI：仓库 revision、文件树和字节大小。
- 可行性：每项跨年统计的字段合同、最小读取范围、流式算法、成本和阻塞。

## 2026-09-07 官方只读核验

- Dataset Viewer `/is-valid`：`preview`、`viewer`、`search`、`filter`、`statistics` 均为真。
- `/splits`：无 `pending`、无 `failed`；存在 `T17` 至 `T25` 九个年度。每年有 `eSLD` 的 `train`、`validation`、`test`，以及 `raw` 的 `benign`、`dga`。
- CLI `hf datasets info`：公开、未门控、未禁用；revision 为 `3b31077020cd1c013d0a75cad51042a2327c4521`，最后修改时间为 `2026-07-20T06:24:36+00:00`。描述声明数据覆盖 2017--2025。
- `/size`：全仓 580,182,195 行，原始与 Parquet 计费大小均为 7,879,096,861 字节，内存展开估计 11,739,375,235 字节。`raw` 九年合计 3,701,856,314 字节。
- `T25_raw/dga` 最小公开预览：列为 `domain: large_string`、`family: large_string`、`label: int32`，首行标签为 1。`T25_raw/benign` 的单行分页确认相同模式、`family=benign`、`label=0`。`T25_eSLD/train`：列为 `domain: large_string`、`label: int64`，首行标签为 0。
- CLI `hf datasets parquet` 返回所有转换后公开 Parquet URL 与字节数。`T17_eSLD/train` 为 46,317,550 字节、3,000,000 行；`T25_eSLD/test` 为 325,972,307 字节、19,559,420 行。`T17_raw` 为 255,393,017 字节、19,140,719 行；`T25_raw` 为 356,371,760 字节、29,219,079 行。
- Dataset Viewer 的 `statistics` 能力是列统计接口，不是自定义 SQL 聚合。其 `rows` 每页上限为 100；没有发现可为字符 n-gram、后缀集合、域名交集或家族隔离返回精确总体数的公开远端聚合接口。

## 解释边界

- 三次行预览只验证字段名、类型及标签语义，不能代表总体家族、后缀或标签比例。
- `T17`--`T25` 按数据集描述对应 2017--2025；仓库名中的 `26` 是 DSN 2026 发表年份，不应误记为采集到 2026 年。
- 后续评估遵循单一冻结训练种子。配对 bootstrap 或置换重采样的是固定预测上的独立评价单元，不是训练随机性评估。
