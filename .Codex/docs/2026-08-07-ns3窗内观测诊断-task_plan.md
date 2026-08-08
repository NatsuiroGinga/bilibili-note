# ns-3 窗内观测诊断实施计划

> **执行要求：** 按 `executing-plans` 执行。本仓库 `AGENTS.md` **明令禁用 test-driven-development**，因此本计划不使用红绿灯循环、不要求先写失败测试。实现完成后只运行一次覆盖本次改动的最小验证，再并行审查。计划文档存 `.Codex/docs/`（项目约定覆盖技能默认路径）。

**目标：** 以全新诊断身份取得 ns-3 窗内队列观测量，用预注册判据 `G-diag` 裁决「窗口粒度是否为 99% 空边界的直接根因」，并为 v4 的采样点数 `K` 提供实测依据。

**架构：** 复制 v3 场景为**独立诊断场景文件**，只新增窗内观测量与可选队列轨迹；v3 场景源码、运行时配置、矩阵制品与物理池全部只读保留。诊断使用新运行时配置与新输出根，产物**不并入 v3**，沿用 `index24` 诊断先例。

**技术栈：** ns-3.48（C++17）、隔离 CMake `ns3-cmake-3.25.2`、Python 3（pandas/pyarrow）、`guarded_rsync.py` 白名单同步、`expect /tmp/gpu-exec.exp` 远程执行。

## 全局约束

- v3 场景源码 `ns3/r2_protocol_dynamics_v2_scenario.cc` 的 SHA-256 必须保持 `0123538bb10eba6a69e5057fdd1d3c817a457ede019efc8b4111b9c614311617`，与 `configs/r2_ns3_protocol_dynamics_v3_parallel_runtime.json` 的 `expected_scenario_source_sha256` 一致。**本计划任何步骤不得修改该文件。**
- 不得修改、覆盖或追加 `runs/ns3-data/r2-protocol-dynamics-v3-formal-attempt1/`、`runs/data-prepared/r2-final-tcp-udp-physics-v3/`、`runs/data-prepared/e2-physics-auxiliary-v1/` 及任何 E2 运行目录。
- 诊断产物写入 `runs/ns3-data/r2-protocol-dynamics-v3-diag-<UTC时间戳>/`，独立身份，不进入任何正式物化。
- 物理网格（`offered_load_ratio`、容量、`queue_limit_packets`、`traffic_mode`）与 `window_seconds=0.1` **一律不动**。本次只增加观测量，不改变被观测的物理过程。
- ns-3 固定在 `/root/autodl-tmp/thesis/ns3/ns-3.48/`，隔离 CMake 在 `/root/autodl-tmp/thesis/ns3/.tools/ns3-cmake-3.25.2/`，包装器使用 `env USER=ns3builder ./ns3 ...`。
- 远程同步只用 `scripts/guarded_rsync.py --apply` 白名单单文件并核对 SHA-256；禁止 `rsync --delete`。
- 不读取最终测试集。凭据只从环境变量读取，不得打印或写入任何文件。

## 预注册判据（运行前冻结，不得事后修改）

**G-diag**：在 `traffic_mode=dos` 且 `offered_load_ratio ≥ 1.05` 的窗口子集上，

- 通过：`diag_queue_peak_l3_bytes > 0` 的窗口比例 **≥ 50%**，且 `diag_queue_nonzero_seconds` 的中位数 **> 0**；
- 失败：上述比例 **< 50%**。

通过 → 「窗口粒度是主导根因」成立，进入 v4 重物化设计（需用户另行批准）。
失败 → 该假设被否决，改查相位对齐（比较 UDP 突发周期与 `0.1 s` 窗口周期的整除关系），**不得进入重物化**。

裁决只依据本判据，不得在看到数据后调整阈值。

## 文件结构

| 文件 | 职责 |
| --- | --- |
| `scripts/ns3/r2_protocol_dynamics_v3_diag_scenario.cc`（新建） | v3 场景的诊断副本，新增 4 个窗内观测列与可选队列轨迹输出 |
| `configs/r2_ns3_protocol_dynamics_v3_diag_runtime.json`（新建） | 诊断运行时配置，指向新场景源码与新输出根 |
| `scripts/analyze_ns3_intra_window_diagnostic.py`（新建） | 读取诊断 CSV，计算 `G-diag` 与 `K` 选型依据 |
| `tests/test_ns3_intra_window_diagnostic.py`（新建） | 覆盖观测量语义与 `G-diag` 计算的最小回归 |

---

## Task 1：诊断场景源码与窗内观测列

**Files:**
- Create: `scripts/ns3/r2_protocol_dynamics_v3_diag_scenario.cc`（由 `ns3/r2_protocol_dynamics_v2_scenario.cc` 完整复制后修改）

**Interfaces:**
- Produces: 主 CSV 在既有列尾追加 4 列 `diag_queue_peak_l3_bytes,diag_queue_peak_packets,diag_queue_nonzero_seconds,diag_queue_time_avg_l3_bytes`；`kMainSchema` 改为 `flow_probe_r2_ns3_main_v3_diag`。
- Consumes: 无。

- [ ] **Step 1：复制场景并确认基线未被触碰**

```bash
cd /Users/bilibili/personal/note/thesis/experiments/llm_probe
cp ns3/r2_protocol_dynamics_v2_scenario.cc ns3/r2_protocol_dynamics_v3_diag_scenario.cc
shasum -a 256 ns3/r2_protocol_dynamics_v2_scenario.cc
```

期望：输出仍为 `0123538bb10eba6a69e5057fdd1d3c817a457ede019efc8b4111b9c614311617`。若不是，立即停止并报告。

- [ ] **Step 2：在诊断场景中新增成员变量**

在 `WindowCollector` 私有成员区（原文件第 863–865 行 `m_currentQueueBytes` 等声明附近）追加：

```cpp
  // 诊断专用：窗内队列占用观测量，不参与任何守恒或物理计算。
  uint64_t m_windowPeakQueueBytes{0};
  uint64_t m_windowPeakQueuePackets{0};
  double m_windowQueueByteSeconds{0.0};
  double m_windowQueueNonzeroSeconds{0.0};
  Time m_lastQueueSampleTime{Seconds(0)};
```

- [ ] **Step 3：新增时间加权累积helper**

在 `WindowCollector` 中新增私有方法：

```cpp
  // 按上一次采样以来的时长累积占用，必须在改变队列长度之前调用。
  void AccumulateQueueOccupancy() {
    const Time now = Simulator::Now();
    const double elapsed = (now - m_lastQueueSampleTime).GetSeconds();
    if (elapsed > 0.0) {
      m_windowQueueByteSeconds +=
          elapsed * static_cast<double>(m_currentQueueBytes);
      if (m_currentQueueBytes > 0) {
        m_windowQueueNonzeroSeconds += elapsed;
      }
    }
    m_lastQueueSampleTime = now;
  }
```

- [ ] **Step 4：在入队与出队处挂钩**

原文件第 297–298 行（入队，队列增长）**之前**插入 `AccumulateQueueOccupancy();`，在 `m_currentQueuePackets += 1;` **之后**插入：

```cpp
    m_windowPeakQueueBytes =
        std::max(m_windowPeakQueueBytes, m_currentQueueBytes);
    m_windowPeakQueuePackets =
        std::max(m_windowPeakQueuePackets, m_currentQueuePackets);
```

原文件第 307–308 行（出队，队列减少）**之前**插入 `AccumulateQueueOccupancy();`。出队不会产生新峰值，无需更新峰值。

确认文件顶部已包含 `<algorithm>`；若无则加入 `#include <algorithm>`。

- [ ] **Step 5：改写主表表头**

在原文件第 173–195 行的 `m_mainOutput << "schema_version,...` 字符串末尾，把 `"truth_udp_backlog_end_bytes\n"` 改为：

```cpp
           "truth_udp_backlog_end_bytes,"
           "diag_queue_peak_l3_bytes,diag_queue_peak_packets,"
           "diag_queue_nonzero_seconds,diag_queue_time_avg_l3_bytes\n";
```

- [ ] **Step 6：改写 schema 常量**

把 `kMainSchema` 的取值改为 `flow_probe_r2_ns3_main_v3_diag`。这会使既有 v3 解析器主动拒绝诊断 CSV，是**期望行为**，用于防止诊断数据被误并入正式矩阵。

- [ ] **Step 7：在 Flush 中结算并写出**

在 `Flush()` 开头（原文件第 751 行 `const Time windowEndTime = Simulator::Now();` 之后）插入 `AccumulateQueueOccupancy();`，使窗口尾段时长被计入。

在写出 UDP 段之后、`m_mainOutput << '\n';` **之前**插入：

```cpp
    const double windowSeconds = m_config.windowSeconds;
    m_mainOutput << ',' << m_windowPeakQueueBytes << ','
                 << m_windowPeakQueuePackets << ','
                 << m_windowQueueNonzeroSeconds << ','
                 << (windowSeconds > 0.0
                         ? m_windowQueueByteSeconds / windowSeconds
                         : 0.0);
```

- [ ] **Step 8：在窗口重置处重新播种**

在原文件第 830–831 行 `m_windowStartQueueBytes = m_currentQueueBytes;` 之后插入：

```cpp
    m_windowPeakQueueBytes = m_currentQueueBytes;
    m_windowPeakQueuePackets = m_currentQueuePackets;
    m_windowQueueByteSeconds = 0.0;
    m_windowQueueNonzeroSeconds = 0.0;
    m_lastQueueSampleTime = windowEndTime;
```

峰值以窗口起始占用播种，保证「窗内只下降」的情形也能记录到真实峰值。

- [ ] **Step 9：确认 v3 基线仍未被改动**

```bash
cd /Users/bilibili/personal/note/thesis/experiments/llm_probe
shasum -a 256 ns3/r2_protocol_dynamics_v2_scenario.cc
```

期望：仍为 `0123538bb10eba6a69e5057fdd1d3c817a457ede019efc8b4111b9c614311617`。

---

## Task 2：可选队列轨迹输出

**Files:**
- Modify: `scripts/ns3/r2_protocol_dynamics_v3_diag_scenario.cc`

**Interfaces:**
- Produces: CLI 参数 `queueTraceIntervalMs`（默认 `0` 表示关闭）与 `queueTracePath`；开启时写出 `time_s,queue_l3_bytes,queue_packets` 三列 CSV。
- Consumes: Task 1 的成员变量。

- [ ] **Step 1：新增配置字段**

在场景配置结构体中加入：

```cpp
  uint32_t queueTraceIntervalMs{0};
  std::string queueTracePath{};
```

- [ ] **Step 2：注册 CLI 参数**

在 `command.AddValue("downstreamLossRate", ...)` 附近追加：

```cpp
  command.AddValue("queueTraceIntervalMs",
                   "队列轨迹采样间隔毫秒，0 表示关闭",
                   config.queueTraceIntervalMs);
  command.AddValue("queueTracePath", "队列轨迹输出路径",
                   config.queueTracePath);
```

- [ ] **Step 3：实现周期采样**

在 `WindowCollector` 中新增：

```cpp
  void StartQueueTrace() {
    if (m_config.queueTraceIntervalMs == 0 || m_config.queueTracePath.empty()) {
      return;
    }
    m_queueTraceOutput.open(m_config.queueTracePath);
    NS_ABORT_MSG_IF(!m_queueTraceOutput.is_open(), "无法创建队列轨迹文件");
    m_queueTraceOutput << "time_s,queue_l3_bytes,queue_packets\n";
    ScheduleQueueTrace();
  }

  void ScheduleQueueTrace() {
    Simulator::Schedule(MilliSeconds(m_config.queueTraceIntervalMs),
                        &WindowCollector::SampleQueueTrace, this);
  }

  void SampleQueueTrace() {
    m_queueTraceOutput << std::fixed << std::setprecision(6)
                       << Simulator::Now().GetSeconds() << ','
                       << m_currentQueueBytes << ',' << m_currentQueuePackets
                       << '\n';
    ScheduleQueueTrace();
  }
```

并新增私有成员 `std::ofstream m_queueTraceOutput;`。

- [ ] **Step 4：在 Start 中启用**

在 `Start()` 内、既有 `Simulator::Schedule(... &WindowCollector::Flush ...)` 之后追加 `StartQueueTrace();`。

---

## Task 3：诊断分析脚本与 G-diag

**Files:**
- Create: `scripts/analyze_ns3_intra_window_diagnostic.py`
- Create: `tests/test_ns3_intra_window_diagnostic.py`

**Interfaces:**
- Consumes: Task 1 产出的诊断主 CSV 与各运行的 `config.json`。
- Produces: 函数 `evaluate_g_diag(frame) -> dict`，返回键 `peak_nonzero_fraction`、`nonzero_seconds_median`、`passed`、`subset_rows`；以及 `suggest_k(frame) -> dict` 返回 `nonzero_seconds_median`、`suggested_k`。

- [ ] **Step 1：实现分析脚本**

脚本按 `physics_group_sha256` 把诊断 CSV 与 `config.json` 的 `traffic_mode`、`offered_load_ratio` 关联，筛出 `traffic_mode == "dos" and offered_load_ratio >= 1.05` 子集，计算：

```python
def evaluate_g_diag(frame: pd.DataFrame) -> dict[str, object]:
    """按预注册 G-diag 判据裁决窗口粒度假设。"""
    subset = frame[
        (frame["traffic_mode"] == "dos") & (frame["offered_load_ratio"] >= 1.05)
    ]
    if subset.empty:
        raise ValueError("G-diag 子集为空，无法裁决")
    peak_fraction = float((subset["diag_queue_peak_l3_bytes"] > 0).mean())
    nonzero_median = float(subset["diag_queue_nonzero_seconds"].median())
    return {
        "subset_rows": int(len(subset)),
        "peak_nonzero_fraction": peak_fraction,
        "nonzero_seconds_median": nonzero_median,
        "passed": peak_fraction >= 0.50 and nonzero_median > 0.0,
    }
```

`suggest_k` 按「子区间长度 ≤ 非零占用时长中位数」从候选 `{6, 11, 21}` 中选最小可行 `K`，即满足 `0.1 / (K - 1) <= nonzero_seconds_median` 的最小候选；若均不满足则返回 `None` 并要求扩大候选集。

- [ ] **Step 2：编写最小回归测试**

`tests/test_ns3_intra_window_diagnostic.py` 覆盖四点，全部用构造的小 DataFrame，不依赖真实运行：

1. 子集筛选正确排除 `benign` 与 `offered_load_ratio < 1.05`；
2. `peak_nonzero_fraction` 恰好 `0.50` 时判为通过（边界含等号）；
3. `nonzero_seconds_median == 0` 时判为不通过，即使峰值比例达标；
4. `suggest_k` 在中位数 `0.02` 时返回 `6`（`0.1/5 = 0.02 <= 0.02`），在中位数 `0.001` 时返回 `None`。

- [ ] **Step 3：本机静态检查**

```bash
cd /Users/bilibili/personal/note
env UV_CACHE_DIR=/tmp/uv-cache PYTHONPYCACHEPREFIX=/tmp/codex-pycache python3 -m py_compile \
  thesis/experiments/llm_probe/scripts/analyze_ns3_intra_window_diagnostic.py \
  thesis/experiments/llm_probe/tests/test_ns3_intra_window_diagnostic.py
```

期望：退出码 `0`。本机不运行 `pytest`。

---

## Task 3.5：独立诊断驱动脚本（2026-08-07 计划修订）

### 修订原因

原 Task 4 假设「新写一份运行时配置指向新场景」即可复用正式并行运行器。**该假设经核验为错**，正式运行器 `src/flow_probe/r2_ns3_protocol_dynamics_v2_parallel_runner.py` 有三处硬绑定：

1. `:207` 硬编码 `output_dir` 必须等于 `runs/ns3-data/r2-protocol-dynamics-v3-formal-attempt1`，否则抛「24路并行输出身份不符」；
2. `:227-231` 编译源固定为 `scratch/flow-probe-r2-dynamics-v2.cc`、可执行文件固定为 `build/scratch/ns3.48-flow-probe-r2-dynamics-v2-default`，编译诊断场景会**覆盖 v3 产物**；
3. `_verify_field_closure` 绑定 v3 场景哈希，换场景后不通过。

用户 2026-08-07 裁定：**不改正式运行器**，改写独立诊断驱动脚本。理由是正式运行器正是产出 v3 冻结矩阵（摘要 SHA `5072feb…`）的代码，改它会把 v3 可复现性从「代码原样未动」的事实退化为「改动未影响 v3 路径」的论证。

### 关键设计：复用 `_run_one`，用独立 scratch 名

- 驱动**不重写命令行构造**。`r2_ns3_tcp_truth_v2_runner._run_one(ns3_root, runs_root, coverage, run, contract_sha, source_sha, executable)` 已经承担全部单次运行职责：写 `config.json`（格式为 `{"coverage": ..., "run": run.to_record()}`）、写 `main.csv` 与 `tcp-sender-windows.csv`、目录命名 `{coverage}-{physics_group_sha256[:12]}`、拒绝覆盖既有目录、支持自定义 `executable`（要求位于 `ns3_root` 内且可执行）。
- 诊断场景拷入 scratch 时使用**独立文件名** `flow-probe-r2-dynamics-v3-diag.cc`，生成独立可执行文件 `ns3.48-flow-probe-r2-dynamics-v3-diag-default`。v3 的 scratch 副本与可执行文件**完全不受影响**，阻塞 2 就此消除。
- 驱动不做字段闭合校验、不写正式收据、不支持续跑——诊断产物不进任何正式矩阵，这些机制无必要。

**Files:**
- Create: `scripts/run_ns3_intra_window_diagnostic.py`
- Create: `tests/test_run_ns3_intra_window_diagnostic.py`

**Interfaces:**
- Consumes: `flow_probe.r2_ns3_tcp_truth_v2_runner._run_one`、`ProtocolRunConfig`、正式清单 `runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.jsonl`。
- Produces: 诊断输出根 `runs/ns3-data/r2-protocol-dynamics-v3-diag-attempt1/`，其下 `runs/<identity>-<sha12>/{config.json,main.csv,tcp-sender-windows.csv}` 与根级 `run-state.json`；函数 `select_runs(runs, *, only_gdiag_subset) -> list[tuple[int, ProtocolRunConfig]]`。

- [ ] **Step 1：实现驱动脚本**

CLI 至少提供：`--ns3-root`、`--executable`、`--output-root`、`--manifest`、`--contract-path`、`--workers`（默认 8）、`--only-gdiag-subset`（布尔）、`--queue-trace-interval-ms`（默认 0）。

`select_runs` 在 `only_gdiag_subset=True` 时只保留 `traffic_mode == "dos"` 且 `offered_load_ratio >= 1.05` 的运行，这与 G-diag 子集定义一致，可把 512 项降到 128 项。阈值 `1.05` 从 `analyze_ns3_intra_window_diagnostic` 导入同一常量，**不得重新定义**，避免两处阈值漂移。

失败处理：单个运行失败不得中断整批；记录该运行的失败原因，继续其余运行，最终 `run-state.json` 写 `planned_run_count`、`completed_run_count`、`failed_run_count` 与失败清单。全部完成且零失败才写 `status: finished`，否则 `status: partial`。

- [ ] **Step 2：编写最小回归测试**

用构造数据，不依赖 ns-3：

1. `select_runs(only_gdiag_subset=True)` 正确排除 `benign` 与 `offered_load_ratio < 1.05`，且保留边界值 `1.05`；
2. `select_runs(only_gdiag_subset=False)` 返回全量；
3. 阈值常量确实来自 `analyze_ns3_intra_window_diagnostic`，两处不存在独立定义（用 `is` 或直接断言同一常量对象/值并检查导入语句存在）；
4. 单个运行抛异常时不中断整批，`run-state.json` 记为 `partial` 并含失败清单（用打桩替身替换 `_run_one`）。

- [ ] **Step 3：本机静态检查**

```bash
cd /Users/bilibili/personal/note
env UV_CACHE_DIR=/tmp/uv-cache PYTHONPYCACHEPREFIX=/tmp/codex-pycache python3 -m py_compile \
  thesis/experiments/llm_probe/scripts/run_ns3_intra_window_diagnostic.py \
  thesis/experiments/llm_probe/tests/test_run_ns3_intra_window_diagnostic.py
```

期望退出码 `0`。本机不运行 `pytest`。

---

## Task 4：同步、编译与诊断矩阵运行

**Files:**
- Create: `configs/r2_ns3_protocol_dynamics_v3_diag_runtime.json`

**Interfaces:**
- Consumes: Task 1–3 的全部产物。
- Produces: `runs/ns3-data/r2-protocol-dynamics-v3-diag-<UTC时间戳>/`。

- [ ] **Step 1：诊断运行时配置（已作废，改由 Task 3.5 的 CLI 参数承担）**

`configs/r2_ns3_protocol_dynamics_v3_diag_runtime.json` 已创建但**不再使用**——正式并行运行器拒绝非 v3 输出身份，诊断改走 Task 3.5 的独立驱动脚本，参数由命令行传入。该配置文件保留作为参数记录，不同步、不加载。

- [ ] **Step 2：白名单同步**

```bash
cd /Users/bilibili/personal/note/thesis/experiments/llm_probe
for f in scripts/ns3/r2_protocol_dynamics_v3_diag_scenario.cc \
         scripts/analyze_ns3_intra_window_diagnostic.py \
         tests/test_ns3_intra_window_diagnostic.py \
         scripts/run_ns3_intra_window_diagnostic.py \
         tests/test_run_ns3_intra_window_diagnostic.py; do
  python3 scripts/guarded_rsync.py --source "$f" --apply
done
```

**同步路径已裁定（2026-08-07，用户决定）**：`ns3/` 不在 `guarded_execution_common.py` 的 `ALLOWED_FILE_ROOTS`（仅 `configs`/`scripts`/`src`/`tests`），实测被拒。**不放宽白名单**；诊断场景改放 `scripts/ns3/` 下（提交 `a741dcb`），运行时配置相应指向该路径。生产场景 `ns3/r2_protocol_dynamics_v2_scenario.cc` 保持原位不动。

- [ ] **Step 3：核对远端哈希**

对四个文件逐一比较本机 `shasum -a 256` 与远端 `sha256sum`，全部一致才继续。

- [ ] **Step 4：服务器唯一目标测试**

```bash
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest -q tests/test_ns3_intra_window_diagnostic.py \
  tests/test_run_ns3_intra_window_diagnostic.py
```

期望：全部通过。失败则停止，不进入编译。已实测 `11` 项通过。

**运行分析脚本时必须显式传 `--csv-name diag-window-observables.csv`**：旁车改造后诊断量不再落在主 CSV，而脚本默认值仍为 `result.csv`，不传会得到 `GDiagDataError`。

- [ ] **Step 5：编译诊断场景（用独立 scratch 名）**

把诊断场景拷入 `/root/autodl-tmp/thesis/ns3/ns-3.48/scratch/flow-probe-r2-dynamics-v3-diag.cc`（**独立文件名，不得覆盖 `flow-probe-r2-dynamics-v2.cc`**），编译产出 `build/scratch/ns3.48-flow-probe-r2-dynamics-v3-diag-default`。

**必须使用隔离 CMake，PATH 上的系统 cmake 是 3.22.1，低于 ns-3.48 要求的 3.25，直接跑会 `Configuring incomplete`：**

```bash
cd /root/autodl-tmp/thesis/ns3/ns-3.48
env USER=ns3builder PATH=/root/autodl-tmp/thesis/ns3/.tools/ns3-cmake-3.25.2/bin:$PATH \
  ./ns3 build flow-probe-r2-dynamics-v3-diag
```

已实测：加隔离 CMake 后 `13` 秒编译完成（仅构建该 scratch 目标）。

编译前后各核验一次：`scratch/flow-probe-r2-dynamics-v2.cc` 的 SHA-256 仍为 `0123538b…`，且 `build/scratch/ns3.48-flow-probe-r2-dynamics-v2-default` 的 mtime 未变。编译失败保留完整日志并停止。

- [ ] **Step 6：运行诊断矩阵**

用 Task 3.5 的驱动脚本运行，先加 `--only-gdiag-subset` 跑 G-diag 所需的 `128` 项（`dos` 且 `load ≥ 1.05`）。参照 v3 的 `512` 项 `35.65` 秒，`128` 项预期十几秒。运行前确认磁盘可用 ≥ `10 GiB`。

若 G-diag 判据需要更大样本或需要 `K` 选型依据，再补跑其余项与轨迹子集（`--queue-trace-interval-ms 1`）。

- [ ] **Step 7（新增）：首跑断言**

按 Task 1 复核结论核验三条，任一不成立立即停止并报告：

1. `diag_queue_nonzero_seconds` 全部落在 `[0, 0.1]`；
2. `diag_queue_peak_l3_bytes >= truth_queue_start_l3_bytes` 恒成立；
3. 诊断 CSV 中既有字段（守恒、通量、TCP/UDP）与 v3 同参数运行逐值一致，证明 diag 列未污染物理量。

另注意：场景默认输出路径与错误文案仍写 v2，运行时**必须显式传 `--output`**，不得依赖默认值。

- [ ] **Step 8：确认 v3 制品未被触碰**

```bash
cd /root/autodl-tmp/thesis/experiments/llm_probe
sha256sum ns3/r2_protocol_dynamics_v2_scenario.cc
ls -la runs/ns3-data/r2-protocol-dynamics-v3-formal-attempt1/matrix-summary.json
```

期望：场景哈希仍为 `0123538b…`；v3 矩阵汇总 mtime 未变。

---

## Task 5：裁决与写回

**Files:**
- Create: `.Codex/docs/2026-08-07-ns3窗内观测诊断报告.md`
- Modify: `.Codex/docs/2026-08-07-E2-ASPX种子42路线裁决.md`
- Modify: `output/第一创新点实验总控.md`

- [ ] **Step 1：运行分析并记录 G-diag 结果**

运行 `analyze_ns3_intra_window_diagnostic.py`，记录 `subset_rows`、`peak_nonzero_fraction`、`nonzero_seconds_median`、`passed` 与 `suggested_k`，以及诊断输出根路径与主 CSV 的 SHA-256。

- [ ] **Step 2：撰写诊断报告**

报告须写明：触发条件、预注册判据原文、实测数值、裁决（通过/否决）、证据路径、以及「本诊断只裁决观测粒度假设，不裁决物理是否有检测增益」。

- [ ] **Step 3：把 E2 改判依据写入裁决文档**

在 `2026-08-07-E2-ASPX种子42路线裁决.md` 增加修订小节，采用已确定的定性表述：改判「结果无效」的依据是**运行时即已存在、事后才被发现的有效性缺陷**（置换对照在 99% 恒零目标下不具备对照功能，且实现偏离预注册 F2），**不是对结果不满意**；E4 名额不消耗。

- [ ] **Step 4：更新实验总控**

在 §2.4 与 §7 记录诊断身份、裁决结果与下一门禁。若 `G-diag` 通过，下一门禁为「v4 合同落盘并取得用户批准」；若否决，下一门禁为「相位对齐排查」。

- [ ] **Step 5：把可复用规则写入故障手册**

在 `llm-probe-failure-prevention-handbook.md` 新增一节，记录「物理监督退化的识别与前置门禁」：触发条件（守恒目标近乎恒零）、根因（观测粒度与记账恒等式使残差恒零）、必须前置的 `G-mat`/`G-run` 门禁、以及禁止绕过项（不得靠调归一化分母掩盖退化）。

---

## 验收条件

1. `ns3/r2_protocol_dynamics_v2_scenario.cc` 的 SHA-256 全程保持 `0123538b…`，v3 矩阵、物理池、辅助表与 E2 运行目录零改动。
2. 诊断场景编译成功，512 项全部完成，产物位于独立诊断输出根。
3. 诊断 CSV 的 `kMainSchema` 为 `flow_probe_r2_ns3_main_v3_diag`，既有 v3 解析器对其主动拒绝。
4. `G-diag` 依预注册阈值给出唯一裁决，阈值未在见到数据后修改。
5. 服务器唯一目标测试通过；本机只做语法检查，未运行 `pytest`。
6. 诊断报告、裁决文档修订与总控更新齐备，且两份恢复文档不冲突。

## 决策记录

- 采用新建诊断场景文件而非就地修改：本机 v3 场景哈希与运行时配置的 `expected_scenario_source_sha256` 精确一致，就地修改会使 v3 不可复现。
- 诊断 schema 版本刻意与 v3 不同：让既有解析器**主动拒绝**诊断数据，从机制上防止误并入正式矩阵。
- 不改窗口时长与物理网格：本次只增加观测量。改变被观测过程会同时改变七字段语义与行数，属更大的合同变更，须留到 v4 且由用户批准。

## 错误记录

- 暂无。

## 当前状态

计划已落盘，等待执行 Task 1。
