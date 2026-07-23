# 任务 2B 实现报告：配置、Shell 与训练入口

## 状态

`DONE_WITH_CONCERNS`

配置、Shell 与控制台入口已完成接入和静态检查；真实 Qwen、S3、CUDA 与 SwanLab 行为仍须在 GPU 服务器冒烟中验收。

## 变更文件

- 新增 `thesis/experiments/llm_probe/configs/bounded_physics_conditioning_seed42.yaml`。
- 新增 `thesis/experiments/llm_probe/scripts/run_bounded_physics_conditioning.sh`。
- 修改 `thesis/experiments/llm_probe/pyproject.toml`，仅增加 `flow-probe-train-bounded-physics` 入口。
- 新增 `.Codex/docs/sdd/task-bounded-physics-conditioning/task-2b-report.md`。
- 未修改任务 1、任务 2A 的生产源码或测试。

## 接入契约

- 配置固定 Qwen3-1.7B 绝对路径、种子 42、GeNIS 与 ns-3 数据、有效生成批量 16、双锚点状态监督、损失权重、梯度裁剪、202 步轨迹声明和梯度检查点关闭。
- 配置固定 SwanLab 在线模式、`mortiswang/malicious-traffic-llm` 项目和本实验标签。
- Shell 只把 `e1` 映射为 `structure_only`，把 `e2` 映射为 `combined`；其他实验组立即失败。
- Shell 固定 S3 适配器、基座、配置和 `uv run --no-sync` 入口，不接受路径覆盖。
- Shell 要求调用者显式提供输出目录，并在运行前拒绝既有目录、符号链接或启动日志。
- Shell 仅允许 2 步冒烟或 202 步正式训练；两者复用训练核心中同一条固定 202 步学习率轨迹。

## 验证结果

- 格式化：`.Codex/tools/prettier/node_modules/.bin/prettier --write thesis/experiments/llm_probe/configs/bounded_physics_conditioning_seed42.yaml .Codex/docs/sdd/task-bounded-physics-conditioning/task-2b-report.md`，退出状态 `0`。
- Shell 语法：`bash -n thesis/experiments/llm_probe/scripts/run_bounded_physics_conditioning.sh`，退出状态 `0`。
- 入口唯一性：目标入口精确匹配计数为 `1`。
- 差异检查：`git diff --check`，退出状态 `0`，无输出。
- Python 静态复核：`UV_CACHE_DIR=/tmp/codex-uv-cache uv run --no-sync ruff check src/flow_probe/bounded_physics_train.py`，退出状态 `0`，输出 `All checks passed!`。
- Git：未提交，未推送。

## 运行制品

本任务不启动本机或 GPU 训练，没有新增运行目录或 SwanLab 运行。

## 遗留风险与边界

- 按任务要求未运行本机 `pytest`；配置与 Shell 的服务器行为须在任务 4 冒烟中验证。
- 本任务未扩展任务 3 的评估或统计入口。
