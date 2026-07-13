---
name: mysql
description: MySQL msg_data_all 表结构、索引、字段含义、查询性能注意事项与已知问题
globs: ["*"]
---

# msg_data_all 表知识库

## 表基本信息

- 表名：`msg_data_all`，约 130 万行
- 字符集：`utf8mb4`，排序规则：`utf8mb4_unicode_ci`
- 引擎：InnoDB
- 生产 MySQL 配置：`readTimeout=1s`，超时后 Go MySQL driver 主动关闭连接返回 `invalid connection`

## 已存在的索引

```sql
PRIMARY KEY (id)
KEY ix_mtime (mtime)
KEY ix_is_deleted_myinstance (is_deleted, myinstance)
KEY ix_is_deleted_action_id_ctime (is_deleted, action_id, ctime)
```

`ix_is_deleted_action_id_ctime` 是核心索引，覆盖 `is_deleted=0 AND action_id=N AND ctime >= T` 类查询。

## action_id 含义

| 值 | 含义 |
|----|------|
| 100 | 直接下线 |
| 200 | 预测下线（已停用） |
| 300 | 告警通知 |
| 400 | 自动上线 |

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `instance_name` | varchar(255) | 机器名 |
| `myinstance` | varchar(255) | 机器名（与 `instance_name` 相同） |
| `alertname` | varchar(64) | 告警规则名，如 `BVC-丢包率大于20%-自动下线` |
| `service_type` | varchar(64) | 服务类型：`视频云` / `移动端` / `北斗` / `星辰` |
| `action_id` | int(11) | 操作类型 |
| `ctime` | datetime | 创建时间 |
| `msg` | varchar(2000) | 告警附加信息，当前仅预测下线场景有值，其他场景为空 |

## service_type 与机器类型

| service_type | 对应 hostname | 业务 |
|-------------|---------------|------|
| `视频云` | `-v-` | BVC 点播，丢包率>=20%触发下线 |
| `移动端` | `-mp2sp-` | MOB 移动端，丢包率>=15%触发下线 |
| `北斗` | — | 运维门户操作记录 |

## 查询性能问题

### 背景

生产环境 `msg_data_all` 表约 130 万行，MySQL 配置 `readTimeout=1s`。部分查询因全表扫描超时报 `invalid connection`。

### 现象

| 查询 | 生产结果 | 原因 |
|------|---------|------|
| `msgdata` 无参数 | ✅ 成功 | 走主键倒序取最大 id，微秒级 |
| `msgdata?action_id=100` + 时间范围 | ✅ 成功 | action_id=100 占比 ~80%，子查询很快命中 |
| `msgdata?action_id=200` + 时间范围 | ❌ 报错 | action_id=200 占比极低，子查询需扫描大量行 >1s |
| `tip/myinstance` | ❌ 报错 | `SELECT DISTINCT myinstance WHERE is_deleted=0` 全表扫 130 万行 >1s |
| `msgdata?action_id=200` 无时间范围 | ❌ 报错 | 同上，子查询无索引过滤 |

### `invalid connection` 的真实含义

不是连接老化断开，而是 **Go MySQL 驱动在 `readTimeout` 超时后主动关闭连接并返回 `invalid connection`**。这是驱动层的超时表现，不是 MySQL 服务端错误。

### msgdata 分页 SQL 原理

使用「基于游标的分页」模式：

```sql
-- 子查询：找到当前页的起始 id
SELECT id FROM msg_data_all WHERE is_deleted=0 <条件> ORDER BY id DESC LIMIT offset, 1
-- 主查询：取 id <= 起始 id 的 pageSize 条
SELECT ... FROM msg_data_all WHERE id <= (子查询) AND action_id !=400 <条件> ORDER BY id DESC LIMIT pageSize
```

### 修复方案：加复合索引

```sql
-- 优化 tip 接口（覆盖索引，无需回表）
ALTER TABLE msg_data_all ADD INDEX ix_is_deleted_myinstance (is_deleted, myinstance);

-- 优化 msgdata 分页查询（覆盖子查询全部条件（is_deleted, action_id, ctime））
ALTER TABLE msg_data_all ADD INDEX ix_is_deleted_action_id_ctime (is_deleted, action_id, ctime);
```

### 复合索引列顺序原则

SQL 执行顺序：`FROM → WHERE → SELECT → DISTINCT → ORDER BY → LIMIT`。WHERE 先过滤，所以过滤条件（`is_deleted`、`action_id`）放索引最左边。`ix_is_deleted_myinstance` 中的 `myinstance` 利用索引天然有序性加速 DISTINCT，`ix_is_deleted_action_id_ctime` 的 `ctime` 放在最后做范围扫描。测试环境 EXPLAIN 验证：rows 从 130 万降至 58。

### 自动上线查询

当日扫描行数约 102~275 行，命中 `ix_is_deleted_action_id_ctime` 索引。用 `GROUP_CONCAT` + `ORDER BY ctime DESC` 取最新 alertname，避免二次查询。

### 自动上线观测 SQL

配对逻辑：`action_id=400` JOIN `action_id=100`，取上线事件前最近的下线事件配对。观测 SQL 见 `.claude/scripts/autoonline_compare_release.sql`。

## 已知问题

1. `invalid connection` 含义：不是连接老化断开，是 `readTimeout=1s` 超时后 Go MySQL driver 主动关闭连接
2. `action_id=400` 记录只有 `myinstance` 和 `action_id`，没有 `service_type`/`alertname`/`msg`，分析时需从配对的下线事件取
3. 自动上线的 `doOnline` 写入 `action_id=400` 时，`msg` 字段留空（目前只有预测下线 `action_id=200` 写入 msg）
