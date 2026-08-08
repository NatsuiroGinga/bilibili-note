# E2 种子 43、44 固定复现实验记录

## 实验边界

- 变体固定为 E2 `combined`，不启动 E1，不扫描参数。
- 模型、S3 检测适配器、结构、学习率、损失权重、批量、202 步与评价门槛均不变。
- 训练随机种子分别为 43、44。
- GeNIS 训练与验证文件继续使用 `runs/data-bundled/genis-hierarchical-v2-multitask-seed42/`。
- eval300 的抽样目录与抽样种子继续固定为 `runs/data-sampled/genis-hierarchical-v2-seed42` 和 42。
- ns-3 训练、验证、测试划分继续使用 `runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/`；物理测试固定为 seed44 测试分区 807 条。
- S3 检测适配器与 S3 eval300 参照保持种子 42 正式制品不变。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_train.py`
- `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_evaluation.py`
- `thesis/experiments/llm_probe/scripts/run_bounded_physics_conditioning.sh`
- `thesis/experiments/llm_probe/scripts/run_bounded_physics_conditioning_eval.sh`
- `thesis/experiments/llm_probe/scripts/run_bounded_physics_conditioning_analysis.sh`
- `thesis/experiments/llm_probe/configs/bounded_physics_conditioning_seed43.yaml`
- `thesis/experiments/llm_probe/configs/bounded_physics_conditioning_seed44.yaml`
- `thesis/experiments/llm_probe/configs/bounded_physics_conditioning_seed43_eval300.yaml`
- `thesis/experiments/llm_probe/configs/bounded_physics_conditioning_seed44_eval300.yaml`

种子 42 入口仍使用原默认配置。新增参数只允许预注册种子 42、43、44；种子 43、44 的评估和统计只允许 E2。评估入口额外核对训练摘要中的种子与 `probe.seed` 一致，同时保持独立的 `evaluation.seed=42`。

## 训练运行

### 种子 43

- 服务端输出：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/bounded-physics-conditioning/qwen3-1.7b-seed43-e2-pinn-combined-full202-v1`
- 服务端启动日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/bounded-physics-conditioning/qwen3-1.7b-seed43-e2-pinn-combined-full202-v1.launcher.log`
- 本地待回收路径：`thesis/experiments/llm_probe/runs/bounded-physics-conditioning/qwen3-1.7b-seed43-e2-pinn-combined-full202-v1`
- screen：`bounded-e2-seed43-20260723`，运行完成后自动退出。
- SwanLab 项目：`mortiswang/malicious-traffic-llm`
- SwanLab 运行号：`9jxaq86w`
- SwanLab 地址：`https://swanlab.cn/@mortiswang/malicious-traffic-llm/runs/9jxaq86w/chart`
- 结果：`202/202`，启动器退出码 0，`training_summary.status=finished`。
- 运行时间：237.958 秒；单运行摘要峰值显存 7911.679 MiB。
- 验证：生成损失 0.0284846，五维状态均方误差 0.113619，未观测状态均方误差 0.113340，物理残差均方误差 0.0188611。

### 种子 44

- 服务端输出：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/bounded-physics-conditioning/qwen3-1.7b-seed44-e2-pinn-combined-full202-v1`
- 服务端启动日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/bounded-physics-conditioning/qwen3-1.7b-seed44-e2-pinn-combined-full202-v1.launcher.log`
- 本地待回收路径：`thesis/experiments/llm_probe/runs/bounded-physics-conditioning/qwen3-1.7b-seed44-e2-pinn-combined-full202-v1`
- screen：`bounded-e2-seed44-20260723`，运行完成后自动退出。
- SwanLab 项目：`mortiswang/malicious-traffic-llm`
- SwanLab 运行号：`ar06fmcj`
- SwanLab 地址：`https://swanlab.cn/@mortiswang/malicious-traffic-llm/runs/ar06fmcj/chart`
- 结果：`202/202`，启动器退出码 0，`training_summary.status=finished`。
- 运行时间：231.147 秒；单运行摘要峰值显存 7976.008 MiB。
- 验证：生成损失 0.0286329，五维状态均方误差 0.168428，未观测状态均方误差 0.154370，物理残差均方误差 0.0992674。

并行训练期间观察到 RTX 5090 合计约 21.9 GiB 显存和 91% 利用率。两组完成后 GPU 回到 0 MiB、0%。两次训练的冻结基座与 S3 可训练参数数均为 0；首步物理梯度到基座和注入器均为 0，到状态头均非零。

## SwanLab 云端核验

- 两组云端状态均为 `FINISHED`。
- 两组均返回 40 个自定义标量键。
- `train/learning_rate`、`train/generation_loss`、`train/state_loss`、`train/physics_loss` 均返回 202 个数据点，步号为 1 至 202。
- `validation/generation_loss` 均返回 1 个数据点，步号为 203。
- 云端只读查询结果保存在各训练输出目录的 `cloud_verification/` 子目录。

## eval300 运行中状态

### 种子 43

- 服务端输出：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-seed43-e2-pinn-combined-eval300-v1`
- 服务端启动日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-seed43-e2-pinn-combined-eval300-v1.launcher.log`
- 本地待回收路径：`thesis/experiments/llm_probe/runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-seed43-e2-pinn-combined-eval300-v1`
- screen：`426259.bounded-e2-eval-seed43-20260723`
- SwanLab 运行号：`tfk23ojb`
- SwanLab 地址：`https://swanlab.cn/@mortiswang/malicious-traffic-llm/runs/tfk23ojb/chart`

### 种子 44

- 服务端输出：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-seed44-e2-pinn-combined-eval300-v1`
- 服务端启动日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-seed44-e2-pinn-combined-eval300-v1.launcher.log`
- 本地待回收路径：`thesis/experiments/llm_probe/runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-seed44-e2-pinn-combined-eval300-v1`
- screen：`426263.bounded-e2-eval-seed44-20260723`
- SwanLab 运行号：`9ojphg2j`
- SwanLab 地址：`https://swanlab.cn/@mortiswang/malicious-traffic-llm/runs/9ojphg2j/chart`

2026-07-23 19:18 检查时，两组均已完成 `family_test` 900 条并进入 `subtype_validation` 1800 条，未发现 Traceback、显存溢出或非零退出。并行评估合计占用约 20.3 GiB，GPU 利用率 86%。

## 验证记录

通过项：

- 本地 Black：训练与评估 Python 文件通过。
- 本地 Prettier：四份新增 YAML 配置通过。
- 本地 `python3 -m py_compile`：训练与评估 Python 文件通过。
- 本地 `bash -n`：训练、评估和统计 Shell 通过。
- 本地 `git diff --check`：本任务源码和 Shell 通过。
- 服务端 `uv pip install --no-deps -e .`、`py_compile`、Shell 语法和配置构建通过。
- 训练四个同步文件与本地 SHA-256 一致；训练与评估文件均使用 rsync 白名单同步，未使用 `--delete`。

非阻塞项与已处理故障：

- 首轮本地 Black 和 Python 语法命令因沙箱外缓存不可写失败；将缓存改到 `/tmp` 后通过。
- 本地评估配置函数导入因本机未安装 GPU 可选组而缺少 `torch`；同一配置构建在服务器完整环境通过。
- rsync 包装器使用 `-rtv`，没有保留两个 Shell 的可执行位；初次 eval screen 在进入 Python 前退出，未产生输出目录或日志。服务端恢复为 0755 后使用相同未占用目录重启成功。
- Ruff 首次只报告既有导入顺序风格项 `I001`，没有语法或结构问题；按仓库规则不为格式偏好继续修改。

## 待完成

- 等待两个 eval300 正常退出并记录六分区、807 条物理测试、制品清单与 SwanLab 云端指标。
- 分别运行 E2 种子 43、44 相对固定 S3 的 2000 次配对自助统计。
- 将训练、评估和统计制品 rsync 回收到上述本地路径。
- 根据三种子统计结果更新实验总控；在多种子证据完成前不冻结论文结果性结论。
