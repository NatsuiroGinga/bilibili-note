# 任务 3 实现报告：正式评估与统计入口

## 状态

`DONE_WITH_CONCERNS`

评估生产代码、固定配置、两个服务器 Shell、直接测试和控制台入口已完成。按照任务纪律未在本机运行 `pytest`，真实 Qwen、S3、有界结构、CUDA、SwanLab、六分区预测和 seed44 物理测试仍须在 GPU 服务器验收。

## 变更文件

- 新增 `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_evaluation.py`。
- 新增 `thesis/experiments/llm_probe/configs/bounded_physics_conditioning_seed42_eval300.yaml`。
- 新增 `thesis/experiments/llm_probe/scripts/run_bounded_physics_conditioning_eval.sh`。
- 新增 `thesis/experiments/llm_probe/scripts/run_bounded_physics_conditioning_analysis.sh`。
- 新增 `thesis/experiments/llm_probe/tests/test_bounded_physics_evaluation.py`。
- 修改 `thesis/experiments/llm_probe/pyproject.toml`，只增加 `flow-probe-evaluate-bounded-physics` 入口。
- 新增 `.Codex/docs/sdd/task-bounded-physics-conditioning/task-3-report.md`。
- 未修改 `bounded_physics_conditioning.py`、`bounded_physics_train.py`、`s3_s4_detection_analysis.py` 或其他训练实现。

## 固定检测评估

- `e1` 与 `e2` 分别严格绑定正式 202 步训练目录、正式 `eval300` 输出目录和 SwanLab 运行名，命令行不接受模型、适配器、训练目录或输出目录覆盖。
- 配置固定 Qwen3-1.7B 绝对路径、种子 42、六个 GeNIS 分区、每标签 300 条、生成批量 16、候选批量 24、最大已知类拒识率 0.05 和进度间隔 25。
- 分层抽样直接复用既有评估计划、派生种子和抽样函数；运行前要求当前 `selected_samples_manifest.json` 与 S3 正式评估完全一致。
- 阈值只由 `subtype_validation` 的候选置信度校准；未知攻击不进入训练或阈值校准。
- 自由生成只调用 `PhysicsConditionedRuntime.generate`，固定贪心、单束、缓存生成；候选评分只调用 `PhysicsConditionedRuntime.forward` 并显式传入逐候选 `completion_start`。
- 候选评分同时比较同一提示各候选的五维预测状态和九个条件词元，保存逐样本及全局 `candidate_condition_repeat_max_diff`；任何差值超过 `1e-6` 立即判运行无效。
- 启用结构的十二个预测文件保留既有 `predictions/<split>_{free,candidate}.jsonl` 布局，供 `s3_s4_detection_analysis.analyze` 直接读取。
- 显式旁路的十二个预测文件写入 `bypass_predictions/`；逐样本核对标识、真值、生成文本、解析结果、候选预测、置信度、阈值和全部候选分数，数值最大差超过 `1e-6` 即失败。只排除不可复现的运行时延字段。
- 公开推理请求只允许 `sample_id` 与 `prompt`；队列或状态真值、ns-3 场景号、攻击真值和未知攻击标记均被拒绝。评估真值只在推理返回后按 `sample_id` 附加，用于指标计算和预测制品。
- 自由生成与候选评分均保存总耗时、样本吞吐、词元数、摊销时延第 50/95 百分位和峰值显存；运行时审计保存训练前向、缓存生成和候选评分三条结构路径的挂钩计数。

## seed44 物理测试补充

- 正式评估固定只读 `runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/test.jsonl`，要求恰好 807 条 seed44 测试记录。
- 物理测试复用既有 `anchor0_plus_one` 状态掩码、状态批次、`ContinuousQueueStateHead` 和有限队列残差实现；批量固定为 8，不调参、不校准、不更新任何参数。
- 每个 E1/E2 评估目录单独生成 `physics_test_summary.json`，保存 `five_dimensional_reference_mse`、`observed_reference_mse`、`unobserved_reference_mse` 和 `queue_residual_reference_mse`。
- 训练摘要中的 physics validation 结果不再作为最终物理结论。评估输出生成 `analysis_training_view/training_summary.json`，既有分析器需要的 `state_mse_unobserved` 与 `physics_residual_mse` 只映射自 `physics_test_summary.json`。
- 统计 Shell 新增 `e2-vs-e1` 模式，以 E1 为历史 `s3` 参照、E2 为历史 `s4` 候选；因此既有九项门槛中的两项物理相对改善正式使用相同 seed44 测试制品计算。历史键只表示参照与当前候选，不改变方法身份。

## 统计入口

- `run_bounded_physics_conditioning_analysis.sh` 支持 `e1`、`e2` 和 `e2-vs-e1` 三个固定路由。
- 三个路由均直接调用既有 `flow_probe.s3_s4_detection_analysis.analyze` 的模块入口，不修改九项门槛。
- 自助法固定 2,000 次、种子 42，并由既有实现按真实标签分层配对抽样。
- 既有分析器在统计前再次要求参照与候选的 `selected_samples_manifest.json` 完全一致。

## 直接测试

`tests/test_bounded_physics_evaluation.py` 覆盖：

- 固定六分区、每标签 300 条、E2 绑定和 seed44 物理测试路径或样本数。
- 公开推理拒绝攻击标签、状态目标、ns-3 场景号和未知攻击标记。
- 训练前向、缓存生成和候选评分三条路径均通过运行时，候选评分显式收到 `completion_start`。
- 同提示候选状态或九个条件词元泄漏时拒绝运行。
- 旁路逐样本恢复 S3，同时不比较时延。
- 十二预测文件布局与两条推理路径的吞吐、词元数、时延分位数和峰值显存字段。
- 统计兼容视图从物理测试指标而非训练验证指标建立。

## 验证结果

- 失败测试命令：无。任务明确禁止本机运行 `pytest`，因此未构造或执行本地红绿测试历史。
- 通过测试命令：未执行；新增测试须在 GPU 服务器项目 `uv` 环境运行。
- Python 格式化：`UV_CACHE_DIR=/tmp/codex-uv-cache uv run --no-sync black src/flow_probe/bounded_physics_evaluation.py tests/test_bounded_physics_evaluation.py`，首次重新格式化 2 个文件；最终自审修正后再次执行，退出状态 `0`，2 个文件均无需改写。
- Python 静态检查：首次执行 `UV_CACHE_DIR=/tmp/codex-uv-cache uv run --no-sync ruff check src/flow_probe/bounded_physics_evaluation.py tests/test_bounded_physics_evaluation.py`，只报告导入排序 `I001`，没有语法、未定义名称或结构缺陷。最终自审随后隔离公开推理真值并使加载方式与既有 S3 评估一致；Black 已解析最终源码，依据仓库规则不因格式偏好修改并不重复运行 Ruff。
- 文档与配置格式化：Prettier 检查评估 YAML 与本报告，退出状态 `0`，两个文件均无需改写；本报告因隐藏目录默认忽略而使用 `--ignore-path /dev/null` 显式检查。
- Shell 语法：`bash -n scripts/run_bounded_physics_conditioning_eval.sh scripts/run_bounded_physics_conditioning_analysis.sh`，退出状态 `0`，无输出。
- 差异检查：`git diff --check`，退出状态 `0`，无输出。
- Git：未提交，未推送。

## 运行制品

本任务不启动本机或 GPU 评估，没有新增评估目录、SwanLab 运行编号或统计结果。任务 4 在服务器执行后，每个 E1/E2 评估目录应包含启用与旁路预测、检测摘要、阈值、运行时审计、旁路审计、`physics_test_summary.json`、统计兼容训练摘要和通用 SwanLab 制品。

## 遗留风险与边界

- 未在服务器运行新增测试，真实 PeftModel 层路径、4 位模型设备放置、严格结构加载和缓存生成尚未获得运行证据。
- 未实际证明旁路十二个预测文件与既有 S3 逐样本一致；任何文本、标签、阈值或候选分数偏差都会在正式评估中立即失败。
- 未实际读取服务端 seed44 测试文件；记录数不是 807、状态掩码缺失或物理字段不完整都会在检测评估前失败。
- E2 相对 E1 的测试集物理改善是否达到 10%，以及检测配对自助置信区间是否通过，只能由任务 4 的正式制品裁决。
