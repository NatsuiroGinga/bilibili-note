# 源侧前向数据门核查笔记

## 当前 FT 缓存事实

- 当前 FT half/entitybce 配置的 `paths.cache_root` 是 Dijk 标准化缓存；入口 `ch3_ft_c00_dual_selection.py` 以 mmap 直接读取 `X23/y23/I23/M23/E23/T23`，并调用基座 `source_split`。
- 缓存构建代码把 `T23` 建立在 `mTimestampStart` 的全局稳定排序之上；它是每段首条流的开始时刻。`T23` 不是逐流数组。
- 构建器曾读取并校验 `mTimestampStart <= mTimestampLast`，但 Dijk 缓存消费者只声明六个数组，未声明或读取 `mTimestampLast`。因此没有证据表明在流开始时其全部 83 维特征已经形成；对严格在线合同，完整特征形成时刻目前为“未核”。
- `I23` 为原始流行号索引，`M23` 为有效位置掩码，`E23` 为序列实体标识。它们不足以在一个时间截止点处分离同一实体的早晚流，或按角色截止重算实体标签。

## 既有切分的边界

- 当前 FT 基座 `source_split` 使用随机抽取的 `validation_entities` 与 `T23` 时间尾部：训练为非验证实体且不在时间尾部的序列，验证为验证实体且不在时间尾部的序列。
- 虽然接口断言训练和验证实体、有效流均不交叠，但验证并非整体晚于训练；两角色均可落在时间尾部之前。
- 因而现有 `train_rows`/`validation_rows` 只可作旧收据健康参照，不能证明 `max(train_time) < min(validation_time)`。

## 相邻 Raw83 接口隔离

- Raw83 `protocol_a_raw83.py` 另有清单与 `source_start_time_ns` 流侧旁车，但它不被当前 FT half/entitybce 配置消费。不得把该旁车的存在迁移为当前 FT 缓存已经具备逐流时间的证据。
- 当前 Dijk 缓存未在本工作树镜像；远端安全连接尚未建立，故不猜测凭据、地址或数组内容，也不运行全源扫描。
