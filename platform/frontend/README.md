# 第五章 Web 平台前端（阶段 B）

Vue 3 + Element Plus + ECharts 的实验配置、任务生命周期、12 年面板结果与系统四格消融界面。
前端只展示平台与训练内核已经产生的读数，不实现训练、不改写任何数值或判据。

## 一、页面与路由

| 路由 | 页面 | 数据来源 |
| --- | --- | --- |
| `/` | 实验配置（双开关＋只读参数＋提交） | `POST /api/tasks`、`GET /api/health`、`GET /api/tasks`、CLI 四格快照 |
| `/tasks` | 任务列表与运行状态（5 秒轮询） | `GET /api/tasks`（MySQL `tasks` 表）＋ CLI 归档收据 |
| `/tasks/:id` | 平台任务结果详情 | `GET /api/tasks/{id}`、`GET /api/tasks/{id}/results`（任务完成时快照） |
| `/results/:cell` | 归档格结果详情 | `public/artifacts/cells/{cell}-result.json`（构建期从 `runs/diagnostics` 同步） |
| `/comparison` | 系统四格消融对比 | CLI 收据构建期快照＋平台任务快照＋第四章 TABM4 先导参考 |

## 二、制品读取方式（二选一：直接 fetch 静态 JSON）

**本实现选择“直接 fetch 静态 JSON”**，未修改后端代码。理由：阶段 B 的边界要求不改后端；
逐格结果、CLI 四格收据与先导参考均由构建期快照提供。

**为何 CLI 收据必须用快照**：`ch5_system_runner.py` 的单格运行会重写
`system-comparison.json` 与同名 `{cell}-result.json`。平台 E2E 的 naive 运行会覆盖 CLI 的
`naive-result.json`；若界面直接读实时文件，就会把“平台入口”的读数误标成“CLI 收据”。
因此 CLI 行固定读构建期快照（manifest 记录源路径、SHA256 与修改时间），平台行固定读
`GET /api/tasks/{id}/results` 的任务完成快照，两者在表格的“运行入口”列分开标注。

- `platform/frontend/snapshots/ch5-cli/` 是**入库的冻结快照**，保存本次平台 E2E 之前的 CLI 四格收据：
  `system-comparison.json`、`{naive,replay,naive_members,full}-result.json`。
  `PROVENANCE.json` 逐文件记录原始路径、原始 mtime、SHA256、CLI 读数摘要，以及哪次平台任务覆盖了源文件。
- `scripts/sync-artifacts.mjs` 把冻结快照复制到 `public/artifacts/`；第四章 TABM4 先导参考仍从
  `thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-tabm-pilot/tabm4-result.json` 读取（未被本次运行覆盖）。
- 同步脚本生成 `public/artifacts/manifest.json`，逐文件记录快照路径、原始路径、SHA256、字节数与修改时间；
  界面上的“读数来源 / 制品路径”行直接读取该清单，避免把副本误当成实时读数。
- `public/artifacts/` 与 `dist/` 被 `.gitignore` 忽略；克隆后先运行 `npm run sync:artifacts` 或直接
  `npm run build`（build 会先同步）。`snapshots/ch5-cli/` 不被忽略，因此图件数据可随仓库复现。

> 本次 E2E 平台任务 #1 完成后，`runs/diagnostics/ch5-system/naive-result.json` 与
> `system-comparison.json` 已被平台运行重写；原始 CLI 收据仍可从 Git `HEAD` 与上述冻结快照取得。
> 平台 naive 与冻结 CLI naive 的全部面板指标逐项比较 `max_abs_delta = 0.0`。

## 三、构建与运行

```bash
cd platform/frontend
npm install
npm run build             # 先同步制品，再产出 dist/
```

Go 后端默认托管 `<repo-root>/platform/frontend/dist`：

```bash
go -C platform/backend run . -skip-db          # 仅前端联调，不连 MySQL、不执行训练
```

开发模式（Vite 5173，`/api` 代理到 127.0.0.1:8080）：

```bash
npm run dev
```

真实端到端（MySQL + 串行训练）：

```bash
docker compose -f platform/docker-compose.yml up -d
export CH5_MYSQL_DSN='root:<password>@tcp(127.0.0.1:3306)/ch5platform?charset=utf8mb4&parseTime=True'
go -C platform/backend run .
```

MySQL 密码只从环境变量 `CH5_MYSQL_ROOT_PASSWORD` / `CH5_MYSQL_DSN` 读取，不写入仓库。
`platform/docker-compose.yml` 的 healthcheck 使用容器内环境变量，不在命令行回显密码。

## 四、界面截图

```bash
cd platform/frontend
npx playwright install chromium     # 首次
CH5_BASE_URL=http://127.0.0.1:8080 CH5_SHOT_TASK_ID=<completed task id> npm run capture
```

产物落 `thesis/figures/第五章/`，1920×1080 PNG；生成脚本为
`scripts/capture-screenshots.mjs`，使用 Playwright Chromium，逐页等待
`window.__PAGE_READY__` 后截图。图件清单记录在 `thesis/figures/第五章/图件清单.json`。

## 五、组件树

```text
src/
  main.js                 应用入口（Element Plus 全局注册）
  router.js               四个页面路由
  api.js                  平台 API 与只读制品读取
  format.js               四格/状态元数据、F1/墙钟/时间格式化
  ready.js                截图就绪标记
  App.vue                 顶栏、导航、健康状态
  views/
    ConfigView.vue        配置页（双开关、四格映射、只读参数、提交）
    TaskListView.vue      任务列表（5 秒轮询、生命周期、CLI 归档表）
    TaskDetailView.vue    结果详情（任务/归档选择、KPI、折线、逐年表、断言）
    ComparisonView.vue    四格消融（柱状图、2×2 矩阵、逐格读数表）
  components/
    CellBadge.vue         四格标签
    StatusTag.vue         任务状态标签
    F1LineChart.vue       12 年 F1 折线（末年回评 vs 当年评价）
    YearlyTable.vue       逐年指标表
    ConfigAssertions.vue  配置断言与冻结协议溯源
    ComparisonBarChart.vue 四格 12y mean 柱状图＋平台 E2E 菱形标记
```
