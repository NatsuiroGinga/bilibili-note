# 非对称物理适配唯一修复实验过程笔记

## 2026-07-22 接口审计

- S3 训练目录：`runs/physics-sparse/qwen3-1.7b-seed42-s3-anchor0-plus-one-fullphys202-v1/`；适配器为 `final_adapter/`，状态头为 `state_head.pt`。
- S4 训练目录：`runs/physics-sparse/qwen3-1.7b-seed42-s4-anchor0-plus-one-fullphys202-v1/`。
- S3/S4 `eval300` 均已完成，当前服务器无 `screen`、GPU 进程或显存占用。
- 服务端 PEFT 为 `0.19.1`。`PeftModel.set_adapter` 只接受单适配器，底层 `LoraModel.set_adapter` 接受适配器列表；组合激活后必须再次显式冻结 S3 参数，并仅把物理私有 LoRA 与状态头放入优化器。
- GeNIS 训练 JSONL 的任务层级字段为 `task`：家族为 `attack_family`，子类为 `attack_subtype`。训练保持原始确定性调度，家族样本仅参与前向占位，不进入生成损失。
- 服务器数据盘使用率 `75%`、剩余 `13 GiB`，低于提醒门槛；RTX 5090 当前空闲。

## 实现决策

- 新增独立训练模块，不改变 S1 至 S4 的原有训练语义。
- 家族分区评估只激活 S3；`subtype_validation`、`subtype_test` 和三个未知攻击分区同时激活 S3 与物理私有 LoRA。
- 训练前后都记录家族关闭物理分支的 logits 等价性；该检查使用同一批输入、同一 S3 参数和关闭后的相同适配器集合。

## 两步冒烟

- 服务端输出：`runs/asymmetric-physics/qwen3-1.7b-seed42-asymmetric-physics-smoke2-v1/`。
- SwanLab 运行号：`k9luyk5e`；退出码 `0`，上传 `176` 条记录。
- `step_metrics.jsonl` 为 `2/2` 步，适配器、状态头、配置、环境、输入哈希、两个样本顺序、训练摘要和制品清单均存在。
- 检测适配器训练前后内存摘要一致；家族关闭物理分支的训练前后最大 logits 差为 `0.0`；零初始化组合路径相对 S3 的最大 logits 差为 `0.0`。

## 202 步正式训练

- 启动时间：`2026-07-22 19:52:25`。
- `screen`：`380848.asym-phys-202`；训练 PID：`380859`。
- 输出：`runs/asymmetric-physics/qwen3-1.7b-seed42-asymmetric-physics-full202-v1/`。
- SwanLab：`5uxosw7z`。
- 首轮核验时已完成 `17/202` 步，进程显存约 `6986 MiB`，记录的训练峰值分配约 `4214.5 MiB`。
- 正式训练已完成 `202/202` 步，运行时间 `470.61` 秒，最终峰值分配显存 `6555.53 MiB`，SwanLab 状态待云端终验。
- 检测适配器训练前后摘要一致，家族关闭物理分支的最大 logits 差为 `0.0`。
- 未观测状态均方误差为 `0.028954`，物理残差均方误差为 `0.027822`；相对 S3 的 `0.139720` 和 `0.108131` 分别改善约 `79.28%` 和 `74.27%`，机制门槛先行通过。

## eval300 正式评估

- 启动时间：`2026-07-22 20:01:21`。
- `screen`：`381610.asym-phys-eval300`；评估 PID：`381620`。
- 输出：`runs/asymmetric-physics-evaluation/qwen3-1.7b-seed42-asymmetric-physics-eval300-v1/`。
- SwanLab：`5orlbko9`。
- 家族分区使用 S3 单适配器路径；子类验证、子类测试和三个未知攻击分区使用 S3 与物理私有 LoRA 的组合路径。

## 最终裁决

- SwanLab 云端接口确认训练运行 `5uxosw7z` 与评估运行 `5orlbko9` 均为 `FINISHED`，且两者均存在标量指标序列。
- 家族自由生成宏平均 F1 为 `0.929208`，与 S3 完全一致，家族保护门槛通过。
- 子类自由生成宏平均 F1 为 `0.763372`，低于 S3 的 `0.852319`，差值 `-0.088946`，门槛失败。
- 三个未知攻击的候选评分召回率分别为 `0.003333`、`0`、`0`，均值 `0.001111`；相对 S3 均值下降 `0.374444`，门槛失败。
- 三个开放集场景的候选评分良性误报率均值为 `0.078889`，相对 S3 下降 `0.164444`，门槛通过。
- 未观测状态均方误差和物理残差相对 S3 分别改善 `79.277%` 与 `74.270%`，门槛通过。
- 子类测试期望校准误差从 `0.410308` 降至 `0.300612`，差值 `-0.109696`，门槛通过。
- 两千次按真实标签分层的配对自助法确认退化稳定：子类宏平均 F1 差值的 95% 置信区间为 `[-0.105843, -0.071871]`，未知召回均值差值的 95% 置信区间为 `[-0.404444, -0.345556]`。
- 结论：私有物理分支能显著拟合状态与有限队列残差，并能严格隔离家族路径，但没有把物理表征收益转化为子类及未知攻击检测收益。该唯一修复实验失败并永久停止，不再增加第二修复变体。
- 统计比较程序沿用 S3/S4 比较结构，文件中的 `s4` 键实际指本次不对称物理适配候选，不代表重新运行了原 S4。
- 独立代理复审未发现会推翻失败裁决的严重或重要问题，记录见 `review.md`。

## 制品回收与完整性

- 服务端正式训练：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/asymmetric-physics/qwen3-1.7b-seed42-asymmetric-physics-full202-v1/`。
- 本地正式训练：`thesis/experiments/llm_probe/runs/asymmetric-physics/qwen3-1.7b-seed42-asymmetric-physics-full202-v1/`。
- 服务端正式评估：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/asymmetric-physics-evaluation/qwen3-1.7b-seed42-asymmetric-physics-eval300-v1/`。
- 本地正式评估：`thesis/experiments/llm_probe/runs/asymmetric-physics-evaluation/qwen3-1.7b-seed42-asymmetric-physics-eval300-v1/`。
- 本地统计比较：`thesis/experiments/llm_probe/runs/asymmetric-physics-evaluation/s3-asymmetric-seed42-eval300-comparison-v1/`。
- 正式训练摘要、逐步指标、路由等价性、状态头、私有适配器权重、评估摘要、评估逐步指标、比较摘要和配对自助法结果共九项关键制品的本地与服务器 SHA-256 逐项一致。
- 私有适配器权重大小为 `69,782,384` 字节；训练结束后数据盘使用率为 `76%`，剩余 `13 GiB`。

## 学习率设计边界

- 本次 `full202` 已按正式协议固定 AdamW 常数学习率 `2e-4`，不得改写、重跑替换或以调度结果覆盖。
- 只有本次结构通过全部核心门槛后，任务十九才允许增加一次 `warmup-cosine` 调度消融：前 20 步从 `2e-5` 线性预热至 `2e-4`，后 182 步无重启余弦衰减至 `2e-5`。
- 该消融保持 AdamW、损失权重、参数组、数据顺序、批量和 202 步预算不变，每步记录实际学习率，不扫描任何调度参数或替代调度器。
- 该消融不是失败结构的补救手段。当前结构已有两个核心门槛失败，因此该消融已经取消，不再运行。
