# LSPR24 描述性评价脚本参数化报告

- 日期：2026-09-03
- 文件：`thesis/experiments/llm_probe/tools/ch3_ft_lspr24_descriptive_eval.py`
- 任务：给四格评价脚本加 `--cell-runs`（覆盖运行名）与 `--allow-partial-cells`（部分评价，
  2026-09-03 用户明确授权）两个参数；只做参数化与授权范围内的门禁调整，不改任何指标计算、
  聚合口径、阈值或选轮口径。
- 环境：`/opt/miniconda3/envs/rwkv/bin/python`（未使用系统 `python3`）。
- 未做任何真实评价、未连服务器、未用 GPU；全部验证为 `--dry-run` 级别。
- 未运行 `black` 或任何格式化器（仓库 `AGENTS.md` 明确禁止，任务简报同样硬性禁止）。

## 一、改动内容与确切行号

改动后文件共 1421 行（改动前 1274 行），`git diff --stat`：209 行新增、63 行删除。

### 1. 新增常量（第 75–87 行）

- `DEFAULT_CELL_RUN_IDS`（第 78–83 行）：把原来硬编码在 `resolve_cell_runs` 函数体内的
  四格全容量正式档运行名提升为模块级常量，取值逐字不变。
- `PARTIAL_EVALUATION_AUTHORIZATION_NOTE`（第 87 行）：
  `"部分评价由用户 2026-09-03 明确授权"`，供收据与日志统一引用，避免措辞漂移。

### 2. 新增 `parse_cell_runs_argument`（第 186–212 行）

解析 `--cell-runs` 的 `"c00=<run_id>,c10=<run_id>,c01=<run_id>,c11=<run_id>"` 形式；
`None` 时原样返回 `None`（调用方据此走默认映射）；格式错误、未知格短键、空运行名、
零有效条目均 `raise SystemExit` 并给出具体错误。

### 3. 改写 `resolve_cell_runs`（第 215–250 行）

签名由 `(runs_root) -> dict[str, Path]` 改为
`(runs_root, cell_run_ids=None, allow_partial=False) -> tuple[dict[str, Path], list[str]]`。

- `cell_run_ids=None` 时用 `DEFAULT_CELL_RUN_IDS`，逐字复现改动前行为。
- 显式传入时**完全替换**默认映射（不合并），未提及的格记为 `"{cell}(未指定)"`；
  这是刻意设计——避免把缩容档运行名与默认全容量档运行名悄悄混用，破坏
  `assert_cross_cell_agreement` 想保证的"同一比较集"前提。
- `missing and not allow_partial` 时报错文案与改动前逐字相同：
  `"四格未齐备，缺：{...}；不做部分评价"`。
- 新增两条：`resolved` 为空时报错（部分评价至少需要一格）；`missing` 非空但
  `allow_partial=True` 时打印带 `PARTIAL_EVALUATION_AUTHORIZATION_NOTE` 的日志。

### 4. 新增 `compute_four_cell_verdict`（第 264–294 行）

抽出源年/目标年共用的四格判据计算：C10−C00、C01−C00 两个 pairwise 增量，若双方都在
`ap_of_cell` 中则计算浮点差值，否则返回字符串 `"无法计算：c00 或 {cell} 缺失"`；
C11 是否最佳与交互项只在四格齐全（`all(cell in ap_of_cell for cell in CELLS)`）时计算，
否则均为字符串 `"无法计算：四格未齐备"`——不输出 `null`、不输出 `0`。四格齐全时的浮点
运算顺序与改动前 `run_preflight`/`evaluate` 内联代码逐位相同（同一表达式顺序）。

### 5. 修正两处 `CELLS[0]` 硬编码

- `assert_cross_cell_agreement`（第 326–331 行）：`agreement[name] = values[CELLS[0]]`
  → `next(iter(values.values()))`。原实现假定 c00 恒在场；部分评价时 c00 可能缺席，
  这里改为取任意一格（`distinct` 长度已保证组内相同）。
- `load_shared_transform`（第 357–367 行）：同理把 `cell_runs[CELLS[0]]` /
  `hashes[CELLS[0]]` 改为 `cell_runs[first_cell]` / `hashes[first_cell]`，
  `first_cell = next(iter(cell_runs))`（字典插入顺序遵循 `CELLS`＝c00,c10,c01,c11）。

### 6. `build_manifest` 签名变化（第 1003–1035 行）

新增 `present_cells: tuple[str, ...]`、`missing_cells: list[str]` 两个参数；
`"cells"` 字段从恒定的 `list(CELLS)` 改为 `list(present_cells)`，并新增
`"missing_cells"`、`"partial_evaluation"`、`"partial_evaluation_authorization"` 三个字段。

### 7. `run_preflight` 签名与逻辑（第 1045–1086 行）

新增 `cell_run_ids`、`allow_partial` 两个入参；返回值新增 `missing_cells`（四元组变
四元组第四项）。`for cell in CELLS: if cell not in cell_runs: continue` 只核验实际
存在的格；四格判据改用 `compute_four_cell_verdict`；日志按是否部分评价分两条路径，
四格齐全路径的格式化字符串与改动前逐字相同。

### 8. `evaluate` 签名与内部改动（第 1089 行起）

新增 `missing_cells: list[str]` 入参；新增 `present_cells = tuple(cell for cell in CELLS
if cell in cell_runs)`（保持 `CELLS` 规范顺序）。内部 6 处 `for cell in CELLS` /
`configs[CELLS[0]]` / `primary = {cell: ... for cell in CELLS}` 等全部改为基于
`present_cells`；`expected_units` 与门槛检查消息按实际格数动态生成（不再恒为"八个"）；
`target_primary_verdict` 改用 `compute_four_cell_verdict`；`result` 新增顶层
`"partial_evaluation"` 字段（`enabled`/`present_cells`/`missing_cells`/
`authorization_note`）；`target-summary.json` 同步新增该字段；`write_status` 的
完成文案在部分评价时追加缺格与授权说明；`build_manifest` 调用改传
`present_cells`、`missing_cells`。

### 9. `main()` CLI 与收据（第 1347 行起）

新增 `--cell-runs`（默认 `None`）与 `--allow-partial-cells`（`store_true`，默认
`False`）两个 `argparse` 参数；解析出 `cell_run_ids` 后传入 `run_preflight`；
`--dry-run` 分支的 `preflight.json` 新增 `cells_present`、`missing_cells`、
`partial_evaluation`、`partial_evaluation_authorization` 字段，控制台日志按是否
部分评价分两条文案。

## 二、新参数用法示例

```bash
# 默认（不带新参数）：行为与改动前逐字一致
python tools/ch3_ft_lspr24_descriptive_eval.py --dry-run

# 覆盖为缩容档四格运行名，仍要求四格齐备（不开 --allow-partial-cells）
python tools/ch3_ft_lspr24_descriptive_eval.py --dry-run \
  --cell-runs "c00=ch3-ft-c00-halfwidth-screening-v1,c10=ch3-ft-c10-halfwidth-screening-v1,c01=ch3-ft-c01-halfwidth-screening-v1,c11=ch3-ft-c11-halfwidth-screening-v1"

# 部分评价：只给两格 + 显式授权开关
python tools/ch3_ft_lspr24_descriptive_eval.py --dry-run \
  --cell-runs "c00=ch3-ft-c00-halfwidth-screening-v1,c01=ch3-ft-c01-halfwidth-screening-v1" \
  --allow-partial-cells
```

## 三、四项验证

### 验证 1：缺省行为逐字不变

取改动前版本（`git show HEAD:.../ch3_ft_lspr24_descriptive_eval.py`）复制为
`tools/_pre_ch3_ft_lspr24_descriptive_eval.py`（验证完已删除），与改动后版本各跑一次：

```bash
python tools/_pre_ch3_ft_lspr24_descriptive_eval.py --dry-run --output-root <scratch>/pre
python tools/ch3_ft_lspr24_descriptive_eval.py       --dry-run --output-root <scratch>/post
diff <scratch>/pre_stdout.txt <scratch>/post_stdout.txt   # 无差异
diff <scratch>/pre_stderr.txt <scratch>/post_stderr.txt   # 无差异
```

两者退出码均为 `1`，stdout 均为：
```
[     0.0s] 核验四格齐备与源年封印状态
```
stderr 均为：
```
评价停止：四格未齐备，缺：c11(ch3-ft-c11-cem-ber-cuda-formal-v1)；不做部分评价
```
`diff` 结果均为空——**逐字一致，通过**。

### 验证 2：新参数生效（缩容档四格名，不开部分评价开关）

```bash
python tools/ch3_ft_lspr24_descriptive_eval.py --dry-run \
  --cell-runs "c00=ch3-ft-c00-halfwidth-screening-v1,c10=ch3-ft-c10-halfwidth-screening-v1,c01=ch3-ft-c01-halfwidth-screening-v1,c11=ch3-ft-c11-halfwidth-screening-v1"
```
退出码 `1`，stderr：
```
评价停止：四格未齐备，缺：c10(ch3-ft-c10-halfwidth-screening-v1), c01(ch3-ft-c01-halfwidth-screening-v1), c11(ch3-ft-c11-halfwidth-screening-v1)；不做部分评价
```
报错信息里出现的是缩容档运行名，且因缺格停止——**通过**。但缺格清单是
`c10, c01, c11` 三格，而不是简报预期的仅 `c10, c11` 两格；原因见下文"重要发现"。

### 验证 3：门禁未被削弱（只给三格必须仍报错）

```bash
python tools/ch3_ft_lspr24_descriptive_eval.py --dry-run \
  --cell-runs "c00=ch3-ft-c00-dual-selection-cuda-formal-v1,c10=ch3-ft-c10-entity-memory-cuda-formal-v1,c01=ch3-ft-c01-entity-ranking-cuda-formal-v1"
```
（未传 `--allow-partial-cells`）退出码 `1`，stderr：
```
评价停止：四格未齐备，缺：c11(未指定)；不做部分评价
```
**通过**——默认门禁在新参数下依然生效。

### 验证 4：导入检查

```bash
python -c "import ast; ast.parse(open('tools/ch3_ft_lspr24_descriptive_eval.py',encoding='utf-8').read())"
python -c "import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'src'); import ch3_ft_lspr24_descriptive_eval"
```
两条均无异常，`import OK`——**通过**。

### 补充验证：协调者追加的部分评价开关（用户 2026-09-03 授权覆盖原「门禁不可动」要求）

按协调者给出的确切命令跑 `--dry-run`：
```bash
python tools/ch3_ft_lspr24_descriptive_eval.py --dry-run \
  --cell-runs "c00=ch3-ft-c00-halfwidth-screening-v1,c01=ch3-ft-c01-halfwidth-screening-v1" \
  --allow-partial-cells
```
退出码 `0`。实际输出：
```
[     0.0s] 核验四格齐备与源年封印状态
[     0.0s] 部分评价：缺 c10(未指定), c01(ch3-ft-c01-halfwidth-screening-v1), c11(未指定)；继续评价已存在的 ['c00'] 格；部分评价由用户 2026-09-03 明确授权
[     0.0s]   c00: 源年实体AP=0.735506（轮17） 逐流AP=0.999946（轮19）
[     0.0s] 部分评价：缺 c10(未指定), c01(ch3-ft-c01-halfwidth-screening-v1), c11(未指定)；C10−C00=无法计算：c00 或 c10 缺失 C01−C00=无法计算：c00 或 c01 缺失 C11最佳=无法计算：四格未齐备 交互=无法计算：四格未齐备；部分评价由用户 2026-09-03 明确授权
[     0.0s] 预检完成（--dry-run），部分评价：缺 c10(未指定), c01(ch3-ft-c01-halfwidth-screening-v1), c11(未指定)；部分评价由用户 2026-09-03 明确授权；未做目标年前向
```
`preflight.json` 中 `"interaction": "无法计算：四格未齐备"`（字符串，非 `null`/`0`），
`"missing_cells"` 与 `"partial_evaluation_authorization"` 均按要求落盘。

**只识别到 1 格（c00），不是协调者预期的 2 格（c00+c01）**——见下文"重要发现"。
为隔离"实现是否正确"与"c01-halfwidth 本身的数据缺口"，另跑了一组两格都真实齐备
的对照（`c00-formal` + `c10-formal`，两者 `receipts/selection.json` 均存在）：
```bash
python tools/ch3_ft_lspr24_descriptive_eval.py --dry-run \
  --cell-runs "c00=ch3-ft-c00-dual-selection-cuda-formal-v1,c10=ch3-ft-c10-entity-memory-cuda-formal-v1" \
  --allow-partial-cells
```
退出码 `0`：
```
[     0.0s] 部分评价：缺 c01(未指定), c11(未指定)；继续评价已存在的 ['c00', 'c10'] 格；部分评价由用户 2026-09-03 明确授权
[     0.0s]   c00: 源年实体AP=0.788795（轮17） 逐流AP=0.999887（轮16）
[     0.0s]   c10: 源年实体AP=0.815031（轮17） 逐流AP=0.999235（轮20）
[     0.0s] 部分评价：缺 c01(未指定), c11(未指定)；C10−C00=0.02623616649141547 C01−C00=无法计算：c00 或 c01 缺失 C11最佳=无法计算：四格未齐备 交互=无法计算：四格未齐备；部分评价由用户 2026-09-03 明确授权
```
两格都正确识别，C10−C00 正确计算出浮点差值（0.02623616649141547），C01/C11 相关项
正确标"无法计算"——**证明部分评价实现本身正确**，验证 4 的"只识别到 1 格"是数据本身
缺口，不是代码缺陷。

## 四、重要发现（如实报告，未自行处理）

**`ch3-ft-c01-halfwidth-screening-v1` 缺 `receipts/selection.json`，尽管该运行状态为
`finished`/`exit_code=0` 且已有全部三个选轮检查点。**

实测（本机 `runs/diagnostics/ch3-ft-c01-halfwidth-screening-v1/`）：

- `status.json`：`{"state": "finished", "stage": "train", "exit_code": 0, "target_reads": 0,
  "early_stopped_at_epoch": 10, "configured_epochs": 20, "stop_reason": "2026-09-03 用户裁定:
  缩容档只用前 10 轮,后 10 轮不提供关于机制是否生效的新信息"}`
- `checkpoints/`：`inflight.pt`、`selected-by-entity.pt`、`selected-by-entity-tail.pt`、
  `selected-by-flow.pt` 均存在。
- `receipts/`：只有 `entity-ranking-diagnostics-{1..10}.json`、`execution-path.json`、
  `input-transform.json`、`split.json`，**没有 `selection.json`**。
- 对照 `ch3-ft-c00-halfwidth-screening-v1`：同样 `finished`，`receipts/` 下**有**
  `selection.json`。

`resolve_cell_runs` 沿用改动前的门禁标准——以 `receipts/selection.json` 是否存在判定
"该格是否存在"（这是原逻辑本来就用的判据，本任务未改动其含义，只是把它从硬编码搬到
参数化路径）。因此 C01-half 在协调者给出的命令下被判为"未指定/缺失"，而非"存在"。

**本任务未改动这条判据**，因为：
1. 任务简报明确要求"不得改任何指标计算、聚合口径、阈值或输出格式"；
2. 用哪个文件证明"该格评价可用"属于科学判据（`selection.json` 里的 `best_by_entity`/
   `best_by_flow` 是后续 `load_sealed_selection` 读取源年封印指标的唯一来源，改用
   checkpoint 存在与否作判据会绕过这层校验）；
3. 这更像是 C01-half 训练/落盘链路本身的一个缺口，需要主代理或原实现者判断是
   "还未写完"还是"写入失败"，不属于本次参数化任务的授权范围。

**未依据以上发现放宽或改动任何门禁**，也未修改判据标准以凑成协调者预期的"识别到两格"。

## 五、`run_tier == "formal"` 门禁核查（如实报告，未自行放宽）

沿评价脚本的实际调用链逐一核查：`load_cell_model` → `dual.build_model_optimizer` →
`dual.effective_base_config` → `base.validate_config`；以及 `dual.resolve_runtime`、
`dual.build_entity_memory_state`。

- `rg -n "run_tier" tools/ch3_ft_transformer_field_token_protocol_a.py`（即 `base` 模块）
  **零命中**。
- `ch3_ft_c00_dual_selection.py`（`dual` 模块）中含 `run_tier` 检查的函数只有
  `validate_config`（第 424/439/445 行），而该函数**只被 `initialize_run`（训练入口，
  第 2830 行起）与该模块自身 CLI 的 `--validate-config` 分支调用**，评价脚本的调用链
  完全不经过它。
- `build_model_optimizer`（第 1278 行起）内部只断言参数量、`width_profile`、
  `expected_parameter_count`，**不读取 `identity.run_tier`**。

**结论：评价脚本的实际执行路径上不存在任何依赖 `run_tier == "formal"` 的断言或分支**，
`screening_only` 的缩容档运行可以被本工具正常加载与打分，无需放宽任何门禁。

## 六、未验证/留待后续

- `evaluate()`（非 `--dry-run` 的真实前向路径）中 `present_cells`/`missing_cells` 相关
  改动**未做端到端真实评价验证**——任务明确要求"不得跑真实评价、不碰服务器、不用
  GPU"。已通过代码走查确认：`primary`、`target_verdict`、`expected_units`、
  `target-summary.json` 的 `rows` 循环等全部基于 `present_cells` 而非 `CELLS`，
  逻辑与 `--dry-run` 路径（已实测）同构；建议在 C11-half（或未来全容量 C11）落盘
  `selection.json` 后，用真实两格或四格数据补一次 `evaluate()` 端到端验证。
- C01-half 缺 `selection.json` 的根因未排查（是否为写入逻辑遗漏、任务被提前终止导致
  某阶段未执行、或 rsync 拉取遗漏该文件），需要能访问训练/落盘代码或服务器状态的人
  或代理跟进；本任务按"不碰服务器"的限制未做进一步排查。
