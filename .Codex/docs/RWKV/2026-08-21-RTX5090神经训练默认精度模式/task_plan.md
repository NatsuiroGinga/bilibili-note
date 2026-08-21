# RTX 5090 神经训练默认精度模式实施计划

> **执行要求：**本计划由已分派的 Codex 实现代理逐项执行。仓库禁止人工测试夹具、独立冒烟实验、自动格式化与本轮服务器访问，因此验收限于配置解析、Python 语法、无 `torch` 导入、命令帮助、合同自检与差异检查。

**目标：**建立不修改现有训练入口的单卡 RTX 5090 神经模型统一精度、敏感计算、等效微批量、检查点边界与资源收据脚手架。

**架构：**配置文件冻结可审查的精度与累积语义，独立 Python 模块提供可复用的合同验证、AMP 上下文、FP32 敏感区、有效单位累积器、检查点元数据与资源收据函数。模块不在顶层导入 PyTorch，使本机缺少 `torch` 时仍能解析合同、执行 `--validate-profile` 和显示帮助；现有模型须由各自入口显式接入。

**技术栈：**Python 3.10+、JSON Schema 2020-12、目标运行时 PyTorch `2.13.0+cu130`、单张 RTX 5090。

**规格：**父任务消息、提交 `586f8c1` 固化的 PyTorch 通用规则、`thesis/experiments/llm_probe/AGENTS.md`、统一可微神经骨干合同及 GRANDE、RWKV、TabM、全容量 MLP 资源证据。

## 全局约束

- 默认配置标识固定为 `cuda-bf16-amp-fp32-sensitive-v1`。
- CUDA 默认使用 `torch.amp.autocast("cuda", dtype=torch.bfloat16)`；模型参数和优化器状态保持 FP32；BF16 不使用 `GradScaler`。
- softmax、对数、概率归一化、损失、归约、指标以及模型声明的递归状态或路由敏感计算进入禁用 autocast 的 FP32 敏感区。
- CPU 和 MPS 默认 FP32；FP16 只作无 BF16 设备回退并使用 `GradScaler`；FP32 只作有数值异常收据的回退。
- 同族结构或机制的科学比较必须使用同一精度配置；跨配置只可作完整系统帕累托或工程比较。
- 有效批量由实验合同给出，微批量只取其机械因子；每个原始优化步只清梯度、裁剪和更新一次，损失按该步全部有效单位归一化，尾批不补不丢。
- activation checkpointing 默认关闭；`torch.compile`、TF32 默认关闭且脚手架不得擅自启用。
- 检查点只在完整优化器步边界保存，含精度配置、缩放器、微批、累积、归一化单位、随机状态和边界声明。
- 资源收据必须含 PyTorch 内部已分配/保留及两类峰值、外部进程显存与吞吐。
- 不访问服务器，不同步，不启动实验，不修改任何活动模型入口、模型结构、运行根或历史收据。

## 文件所有权

- 新建：`thesis/experiments/llm_probe/tools/neural_precision_runtime.py`
- 新建：`thesis/experiments/llm_probe/configs/neural-precision-profile.schema.json`
- 新建：`thesis/experiments/llm_probe/configs/neural-precision-profiles-v1.json`
- 新建：`.Codex/docs/RWKV/2026-08-21-RTX5090神经训练默认精度模式/task_plan.md`
- 新建：`.Codex/docs/RWKV/2026-08-21-RTX5090神经训练默认精度模式/notes.md`
- 新建：`.Codex/docs/RWKV/2026-08-21-RTX5090神经训练默认精度模式/实施报告.md`
- 条件修改：`.Codex/docs/RWKV/2026-08-20-第三章神经骨干跨进程协作看板.md`，仅在提交前仍无未提交改动时给 N-12/N-13 增加配置引用；否则只向主进程提供建议补丁。

## 任务一：冻结配置与模式合同

**接口：**

- `neural-precision-profile.schema.json` 描述配置结构和必填字段。
- `neural-precision-profiles-v1.json` 提供默认 BF16、FP16 回退与 FP32 收据回退三个配置，以及有效批、比较、检查点和资源收据共同合同。

- [x] 核验目标目录修改前状态与共享暂存区。
- [x] 读取 `$pytorch-patterns`、提交 `586f8c1`、目标版本与资源证据。
- [x] 通过 Context7 查询 `/pytorch/pytorch` 与 PyTorch 2.12 官方文档；记录 2.13 精确页面缺失边界。
- [x] 新建 JSON Schema 与配置实例。
- [x] 使用模块 `--validate-profile` 无 `torch` 校验配置实例。

## 任务二：实现独立共享运行时

**接口：**

- `load_and_validate_contract(path)`：只依赖标准库加载并验证配置。
- `validate_runtime_profile(profile, device_type, torch_module)`：核验设备能力、参数精度与缩放器语义。
- `autocast_context(profile, device_type, torch_module)`：按配置返回 CUDA autocast 或空上下文。
- `fp32_island(*tensors, device_type, torch_module)`：禁用 CUDA autocast 并把传入浮点张量转为 FP32。
- `EffectiveBatchAccumulator`：按本步全部有效单位归一化多个微批损失，只在边界执行一次裁剪与更新。
- `build_checkpoint_runtime_state(...)`：只允许完整优化器步边界，保存配置、累积、归一化、缩放器和随机状态。
- `collect_resource_receipt(...)`：合并内部 CUDA 显存、外部进程显存和吞吐。
- `validate_comparison_profiles(...)`：阻止跨配置纯结构或机制因果比较。

- [x] 实现延迟 PyTorch 注入和配置验证。
- [x] 实现精度上下文、FP32 敏感区与 FP16 缩放器回退。
- [x] 实现有效单位累积器、比较门、检查点与资源收据辅助函数。
- [x] 实现 `--validate-profile` 和 `--self-check` 命令入口。

## 任务三：验证、文档与交付

- [x] 执行 `uv run --no-sync python -m py_compile tools/neural_precision_runtime.py`。
- [x] 执行无 `torch` 导入检查、`--help`、Schema JSON 解析、`--validate-profile` 与 `--self-check`。
- [x] 执行 `git diff --check` 和目标路径差异复核。
- [x] 看板目标编辑前保持干净，已只增加 N-12/N-13 默认配置引用。
- [x] 完成 `notes.md` 和 `实施报告.md`，明确尚无本项目全模型精度效果 A/B，LSPR23 源年代表模型验证仍待执行。
- [x] 共享暂存区复核发现另一代理已暂存 N-12 配置与工具；按规则不暂存、不提交、不清空，已记录精确阻塞。

## 状态

- 当前阶段：实现与静态验收完成；提交被共享暂存区占用阻塞。
- 已关闭：规则、接口、资源与 Context7 证据核验；配置、共享工具、静态验收、看板接入和报告。
- 待关闭：主进程在共享暂存区释放后原子提交本任务 7 个目标文件。
- 阻塞项：共享暂存区含 `thesis/experiments/llm_probe/configs/ch3-tabm32-paper-recipe-protocol-a-seed42-v1.json` 与 `thesis/experiments/llm_probe/tools/ch3_tabm32_paper_recipe_protocol_a.py`，本代理不得夹带或清空。

## 错误记录

- 首次在沙箱内调用 Context7 未返回内容；按权限规范联网重试后成功。
- `ch3_gru_precision_probe.py` 路径不存在；通过 `fd` 核验实际文件名为 `ch3_backbone_gru_precision_probe.py`，未修改任何文件。
- 首轮 `uv run --no-sync` 因默认用户缓存 `/Users/bilibili/.cache/uv` 不在沙箱写权限内而停止；显式使用 `/tmp/codex-neural-precision-uv-cache` 后同一组命令全部通过。
- 首次最终 Schema 检查把 Python 代码放在 shell 双引号内，`$schema` 被 shell 展开为空键并触发 `KeyError`；改用单引号保护代码后返回 `schema-json-ok`。
