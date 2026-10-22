# 第五章 Web 平台后端（阶段 A）

Go + Gin + GORM/MySQL 的任务生命周期服务，封装第三章回放构成器与第四章成员化引擎组成的
Python 训练内核 `tools/ch5_system_runner.py`。平台只做组装、任务调度、日志与结果读取，
不包含任何新的训练算法；前端 Vue3 与集成测试属于后续阶段。

## 一、环境与依赖

| 项 | 要求 |
| --- | --- |
| Go | 实测 `go1.24.13 darwin/arm64`；`go.mod` 声明 `go 1.24.0` |
| Gin | 固定 `v1.11.0`（`v1.12.0` 要求 Go ≥ 1.25，本机不升级工具链） |
| GORM | `gorm.io/gorm v1.31.2` + `gorm.io/driver/mysql v1.6.0` |
| MySQL | 5.7+ / 8.x；不提供 SQLite 回退 |
| Python 内核 | 默认 `/opt/miniconda3/envs/rwkv/bin/python`（仓库冻结的本机实验环境） |

数据库 DSN **只从环境变量 `CH5_MYSQL_DSN` 读取**，不提供命令行参数，避免凭据进入 shell 历史
和进程列表。平台不打印 DSN。示例占位：

```bash
export CH5_MYSQL_DSN='<user>:<password>@tcp(127.0.0.1:3306)/ch5platform?charset=utf8mb4&parseTime=True'
```

启动时会解析 DSN、Ping 数据库并自动迁移 `tasks` 表；连接失败即退出，不回退其他存储。
若 DSN 缺少 `parseTime=True`，平台只在内存中补齐该参数，不改变凭据来源。

## 二、配置

| 参数 | 环境变量 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `-addr` | `CH5_ADDR` | `127.0.0.1:8080` | HTTP 监听地址 |
| `-repo-root` | `CH5_REPO_ROOT` | 自动向上查找 `platform/backend/go.mod` | 仓库根目录 |
| `-probe-dir` | `CH5_PROBE_DIR` | `<repo-root>/thesis/experiments/llm_probe` | 训练内核工作目录 |
| `-python` | `CH5_PYTHON` | `/opt/miniconda3/envs/rwkv/bin/python` | Python 解释器 |
| `-runner` | `CH5_RUNNER` | `tools/ch5_system_runner.py` | 内核脚本，相对路径以 `probe-dir` 为基准 |
| `-frontend-dist` | `CH5_FRONTEND_DIST` | `<repo-root>/platform/frontend/dist` | 前端构建产物；存在则启用静态托管 |
| `-cors-origins` | `CH5_CORS_ORIGINS` | Vite 5173/4173 的 localhost 与 127.0.0.1 | 逗号分隔；`*` 表示允许全部 |
| `-skip-db` | `CH5_SKIP_DB=1` | 关闭 | **仅开发验证**：内存任务存储，不连接 MySQL，不启动训练协程 |
| `-check-db` | — | 关闭 | 只检查 DSN、Ping、迁移后退出 |
| `-smoke` | — | 关闭 | 用同一 exec 路径运行 `<python> --version` 后退出，不启动服务 |
| `-debug` | — | 关闭 | Gin debug 模式 |

`CH5_MYSQL_DSN` 没有对应的命令行参数，这是有意的安全约束。

## 三、启动

从仓库根：

```bash
export CH5_MYSQL_DSN='...'
go -C platform/backend run .
```

或进入模块目录：

```bash
cd platform/backend
export CH5_MYSQL_DSN='...'
go run .
```

构建并运行：

```bash
go -C platform/backend build -o bin/ch5platform .
./platform/backend/bin/ch5platform -repo-root "$(pwd)"
```

开发期无 MySQL 时只验证 API 接线：

```bash
go -C platform/backend run . -skip-db
```

该模式会打印醒目警告，使用进程内存储，**不启动工作协程**，因此提交的任务只会停留在
`pending`，不会产生任何训练子进程；服务退出后数据丢弃。禁止用于真实实验。

数据库连线自检：

```bash
go -C platform/backend run . -check-db
```

未设置 `CH5_MYSQL_DSN` 或数据库不可达时，该命令以非零码退出并提示检查环境变量。

## 四、API

前缀 `/api`，错误统一返回 `{"error": "..."}`。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查，含存储后端 `mysql` / `memory` |
| POST | `/api/tasks` | 提交任务。Body：`{"data_budget": "naive" 或 "quota_deficit", "member_engine": "off" 或 "tabm4"}`；成功 201 返回任务视图 |
| GET | `/api/tasks` | 任务列表，按 ID 降序；无任务返回 `[]` |
| GET | `/api/tasks/{id}` | 单任务详情，含 `cell` 与结果快照 `metrics` |
| GET | `/api/tasks/{id}/log?lines=200` | 尾随日志，默认 200 行，上限 5000 行；日志未创建时 `exists=false` |
| GET | `/api/tasks/{id}/results` | 已完成任务返回完成时的结果 JSON 快照（等同当时的 `{cell}-result.json`）；pending/running/failed 返回 409；快照缺失时回退读取当前结果文件，文件不存在返回 404 |
| GET | `/api/comparison` | 返回 `runs/diagnostics/ch5-system/system-comparison.json` 原文；文件不存在返回 404 |

任务视图字段：`id`、`data_budget`、`member_engine`、`status`、`created_at`、`started_at`、
`finished_at`、`log_path`、`cell`，详情额外含 `metrics`（任务完成时的结果 JSON 快照）。

前端：`platform/frontend/dist/index.html` 存在时启用静态托管，未知非 `/api` 路径回退到
`index.html`（SPA 路由）；未构建时所有非 API 路径返回 404 JSON。CORS 默认允许本地 Vite
开发端口，按需用 `-cors-origins` 扩展。

## 五、与 Python 训练内核的边界

平台不实现训练，只按双开关调用内核。实际子进程与任务规格完全一致：

```text
cwd = <repo-root>/thesis/experiments/llm_probe
cmd = /opt/miniconda3/envs/rwkv/bin/python tools/ch5_system_runner.py \
        --data-budget <naive|quota_deficit> --member-engine <off|tabm4>
```

| data_budget | member_engine | cell | 结果文件 |
| --- | --- | --- | --- |
| `naive` | `off` | `naive` | `naive-result.json` |
| `quota_deficit` | `off` | `replay` | `replay-result.json` |
| `naive` | `tabm4` | `naive_members` | `naive_members-result.json` |
| `quota_deficit` | `tabm4` | `full` | `full-result.json` |

- 日志：`runs/diagnostics/ch5-system/task_<id>.log`（相对 `probe-dir`），stdout/stderr 汇总重定向。
- 状态机：`pending → running → completed | failed`。子进程退出码非零、结果文件缺失/不可读/
  不是合法 JSON/`cell` 与任务不符，均记为 `failed`，失败原因追加到日志并写入 `metrics_json`。
- 陈旧结果防护：结果文件修改时间必须晚于本次任务开始时间，否则拒绝使用，避免把上一轮
  同名结果误当成本次读数。任务完成时把结果 JSON 快照写入 `metrics_json`；`/results` 对已完成
  任务优先返回该快照，避免同一 cell 的后续运行覆盖文件后读到他次读数。
- 启动恢复：上一次进程遗留的 `running` 任务会被标记为 `failed`。该行为假设**单实例部署**；
  多个后端实例共享同一数据库时不得启用同一队列（否则可能误伤另一实例在执行的任务）。
  正常 SIGTERM/SIGINT 会取消 `exec.CommandContext` 并终止子进程；若后端被 SIGKILL 强制杀死，
  Python 子进程可能成为孤儿，重启后需人工确认没有遗留训练进程再提交新任务。
- 串行约束：平台内只有一个工作协程，同刻最多一个训练子进程（MPS 约束）。平台**不会**
  感知或协调直接手工运行的四格脚本；外部运行期间不要通过平台提交任务。
- 内核环境：子进程继承父进程环境，`LAMDA_DATA_ROOT` 等变量需在启动平台前设置；平台不读取
  或记录训练数据内容。
- 阶段 A 不提交真实训练任务。exec 接线用 `-smoke` 验证：同一 `runner.RunLogged` 路径执行
  `<python> --version`，仅证明命令、工作目录与日志重定向可用，不代表任何训练结果。

## 六、验证命令

```bash
go -C platform/backend build ./...
go -C platform/backend vet ./...
go -C platform/backend run . -smoke                 # exec 接线（非训练）
go -C platform/backend run . -skip-db               # 另开终端 curl /api/tasks
```

接口契约、四格映射与结果字段以 `thesis/methods/第五章形态与实现计划.md` 和
`thesis/experiments/llm_probe/tools/ch5_system_runner.py` 为准；平台侧只做组装与展示，
不改变任何研究语义、数值或判据。
