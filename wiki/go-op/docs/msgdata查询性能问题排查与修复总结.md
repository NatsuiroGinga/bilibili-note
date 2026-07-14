---
title: msgdata 查询性能问题排查与修复总结
date: 2026-07-13
tags:
  - go-op
  - MySQL
  - 性能
  - 排查
  - 类型/排查
related:
  - "[[mysql]]"
  - "[[北斗资源上下线及踢点策略技术文档]]"
  - "[[go-op MOC]]"
---

# msgdata 查询性能问题排查与修复总结

## 背景

生产环境 `msg_data_all` 表存储了 MCDN 节点上下线事件记录，约 **130 万行**，MySQL 配置 `readTimeout=1s`（后调整为 3s）。两个接口因查询超时返回 `invalid connection` 错误。

| 接口 | 功能 | 所属服务 |
|------|------|---------|
| `GET /api/v1/portal/bi/tip/:key` | 搜索条件提示（去重值） | manba-bi |
| `GET /api/v1/portal/bi/msgdata` | 查询下线事件列表（分页） | manba-bi |

---

## 问题一：tip 接口

### 1.1 现象

浏览器访问 `https://portal.bilibili.co/api/v1/portal/bi/tip/myinstance`，始终返回 `{"code":1500,"message":"invalid connection"}`。

无参数访问 `msgdata` 接口正常（`total=42`），确认数据库连接本身没有问题。

### 1.2 根因分析

**执行的 SQL：**

```sql
SELECT DISTINCT myinstance FROM msg_data_all WHERE is_deleted=0
```

这条 SQL 需要全表扫描 130 万行，在内存中做 DISTINCT 去重。MySQL 配置的 `readTimeout=1s` 内无法完成，**Go MySQL 驱动在 `readTimeout` 超时后主动断开连接，返回 `invalid connection`**。

#### EXPLAIN 执行计划

**初始状态——表上只有 `ix_ctime(ctime)` 和 `ix_myinstance(myinstance)` 两个单列索引：**

| type | key   | rows    | Extra                        |
|------|-------|---------|------------------------------|
| ALL  | —     | 1303122 | Using where; Using temporary |

全表扫描 130 万行，使用临时表做 DISTINCT。

**添加 `ix_is_deleted_myinstance(is_deleted, myinstance)` 索引后：**

| type | key                      | rows   | Extra                     |
|------|--------------------------|--------|---------------------------|
| ref  | ix_is_deleted_myinstance | 632191 | Using where; Using index |

扫描行从 130 万降至 63 万，但耗时仍在 1s 边缘波动。

**加大 `readTimeout=3s` 后：**

✅ 始终成功，查询耗时约 1~2s。

### 1.3 修复方案

加复合索引 + 加大 `readTimeout`：

```sql
-- 覆盖索引，无需回表
ALTER TABLE msg_data_all ADD INDEX ix_is_deleted_myinstance (is_deleted, myinstance);
```

**索引列顺序原理：** `is_deleted` 在最左列做等值过滤，`myinstance` 在第二列利用索引有序性加速 DISTINCT。

**DSN 调整：** `readTimeout` 从 1s 调整为 3s。

### 1.4 验证结果

| 修复前                     | 修复后    |
|:---------------------------|:----------|
| ❌ `invalid connection`    | ✅ < 50ms |

---

## 问题二：msgdata 分页接口

### 2.1 现象

浏览器访问 `https://portal.bilibili.co/api/v1/portal/bi/msgdata?action_id=200&stime=1780314070&etime=1781610070`，始终返回 `{"code":1500,"message":"invalid connection"}`。

而同样的条件改为 `action_id=100` 则查询正常，且不带时间范围参数时也正常（`total=42`）。

### 2.2 根因分析

**分页 SQL 使用"基于游标的分页"模式：**

```sql
-- 子查询：找到当前页的起始 id
SELECT id FROM msg_data_all 
WHERE is_deleted=0 AND ctime BETWEEN ? AND ? AND action_id=200
ORDER BY id DESC LIMIT offset, 1

-- 主查询：取 id <= 起始 id 的 pageSize 条
SELECT 17个字段 FROM msg_data_all 
WHERE id <= (子查询结果) AND action_id !=400 AND ...
ORDER BY id DESC LIMIT pageSize
```

**子查询是性能瓶颈。** 需要过滤 `is_deleted=0`、`action_id=200`、`ctime` 范围三个条件，但表上没有任何索引覆盖这三个条件的组合。

`action_id=100` 在表中占比约 80%（105 万条），从 id 最大值倒序扫描时几乎是第一行就命中；而 `action_id=200` 数量极少，需要扫描大量行才能遇到一条匹配，超过 `readTimeout=1s`。

#### EXPLAIN 执行计划

**加索引前（`action_id=200`）：**

| type  | key      | rows    | Extra       |
|-------|----------|---------|-------------|
| index | PRIMARY  | 1264386 | Using where |

全表扫描 126 万行。

**加索引后（`action_id=200`）：**

```text
SUBQUERY: type=range,  key=ix_search,  key_len=13,  rows=1
          Extra: Using where; Using index; Using filesort
```

`key_len=13` 说明索引三列全部用上（is_deleted=4 + action_id=4 + ctime=5），`rows=1` 说明在索引树内精准定位后只取一条记录。**扫描行数从 126 万降至 1 行。**

**加索引后（`action_id=100`）—— MySQL 选择了不同路径：**

```text
SUBQUERY: type=index,  key=PRIMARY,  key_len=4,  rows=1327896
          Extra: Using where
```

`possible_keys` 中含有 `ix_search`，但 MySQL 优化器经过代价评估后，选择了 PRIMARY 全表扫描而非新索引。

**原因分析：**

子查询的结构是 `ORDER BY id DESC LIMIT 0, 1`——取 id 最大的那条符合条件的记录。MySQL 优化器对两个执行路径做了代价对比：

| 路径        | 扫描方式                                       | 预期代价                                           |
|-------------|----------------------------------------------|---------------------------------------------------|
| 走 PRIMARY   | 从 id 最大值倒序扫描，遇到第一条符合条件的立即返回 | `action_id=100` 占比约 80%，几乎第一行就命中，只需扫约 1~10 行 |
| 走 ix_search | 在索引中定位 `is_deleted=0→action_id=100→ctime` 范围，正向扫描全范围，再对 id 做 filesort 取最大值 | 需要扫完整个 ctime 范围内的所有匹配行，再排序             |

MySQL 优化器判定 **全表扫描倒序取第一行代价 < 索引范围扫描 + filesort 代价**，因此选择了 PRIMARY，而放弃新索引。

这个选择是正确的——`action_id=100` 占比 80%，倒序扫描几乎立即命中，**实际耗时同样 < 1ms，不超时。**

#### 执行计划差异总结

| action_id | 加索引前                     | 加索引后                                      | 实际效果                  |
|:---------:|:----------------------------|:---------------------------------------------|:-------------------------|
| 200       | 全表扫 126 万行 ❌ 超时        | **走 ix_search，rows=1** ✅                     | **1 行精准命中**          |
| 100       | 全表扫 126 万行但立即命中 ✅    | 仍走 PRIMARY，但占比 80% 几乎首行命中 ✅          | **始终 < 1ms**            |

核心结论：**复合索引 `(is_deleted, action_id, ctime)` 精准解决了低频条件（`action_id=200`）的全表扫描问题；高频条件（`action_id=100`）因自身数据分布优势，优化器选择了更高效的全表扫描路径，两者都不超时。**

### 2.3 修复方案

```sql
-- 覆盖子查询全部条件（is_deleted, action_id, ctime）
ALTER TABLE msg_data_all ADD INDEX ix_search (is_deleted, action_id, ctime);
```

**索引列顺序原理：** `is_deleted` → `action_id`（等值匹配）→ `ctime`（范围扫描），WHERE 先执行过滤，过滤条件放索引最左边。

**为什么不加 `id`：** `(is_deleted, action_id, ctime)` 已覆盖子查询全部 WHERE 条件，子查询 `LIMIT 0, 1` 只取一条记录，filesort 开销极小而可忽略，简化索引维护成本更优。

### 2.4 验证结果

| 查询                        | 修复前                     | 修复后      |
|-----------------------------|:---------------------------|:------------|
| `action_id=200` + 时间范围  | ❌ `invalid connection`    | ✅ < 100ms  |
| `action_id=100` + 时间范围  | ✅ 正常                     | ✅ 正常      |
| 无参数                      | ✅ 正常                     | ✅ 正常      |

---

## 经验总结

### `invalid connection` 的排查思路

1. **不是连接池问题**：如果只是偶尔出现，可能是连接池空闲超时；如果是始终失败，一定是查询超时
2. **不是 MySQL 服务端报错**：这是 Go MySQL 驱动在 `readTimeout` 超时后主动断开的连接，不是 MySQL 返回的错误信息
3. **验证方法**：同条件下的其他查询能正常返回，说明数据库连接本身正常，问题出在具体 SQL 上

### 分页 SQL 的索引优化

使用「子查询找起始 id + 主查询取数据」的分页模式时，子查询是性能瓶颈。子查询的条件组合必须在唯一索引或复合索引中完全覆盖，否则必然触发全表扫描。

### 复合索引优化原则

- **等值条件放左边**：`is_deleted=0`、`action_id=200` 放索引最左列
- **范围条件放右边**：`ctime BETWEEN` 放等值条件之后
- **利用覆盖索引**：确保查询字段全部在索引内，避免回表
