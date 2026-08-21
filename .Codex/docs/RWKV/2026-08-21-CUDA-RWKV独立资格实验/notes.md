# CUDA RWKV 独立正式资格实验记录

## 输入证据

- 纯 PyTorch BF16 工程锚：提交 `8d6b7b2`；工具摘要 `4471ed1b10cefda3e668d7c9d281ac635c51d8e7ab6c87f09de26498c6cfd27e`。
- CUDA 融合后端与基准：提交 `4efb193`。
- 官方来源：`BlinkDL/RWKV-LM@952102498e9ed367ea0a59ee64106916d474d30f`，`Apache-2.0`。
- 远端资格事实：合成与 LSPR23 首批等价通过；整轮吞吐比 `8.668993`；验证 AP 绝对差 `0.004199787`；reserved 显存比 `1.099476`；透明替换资格为否。
- 用户授权：允许把 CUDA 版 RWKV 作为独立数值变体正式训练。授权不改变失败门，也不证明效果。

## 实现决策

- 新入口是薄适配层，复用纯 PyTorch BF16 入口的数据、四格训练、双归一、评价、首次告警和恢复框架。
- 仅替换 K0 TimeMix 内部 WKV 递归。固定 `R2/K0`、`C=112`、`HEAD_SIZE=16`、`L=128`、单层，不暴露 K1/K2。
- 六个融合输入、输出和梯度为 BF16；CUDA 核内递归状态与累加为 FP32；归一化、Lp 池化、损失等其他敏感岛继续使用纯入口的 FP32 合同。
- 配置登记后端、基准、供应商清单、派生 C++、官方 CUDA、许可证和纯 PyTorch 工程锚的摘要。启动器将结构封印收据与失败资格收据摘要注入解析配置。
- 检查点增加融合数值变体身份，恢复时精确比较；纯 PyTorch 检查点没有该身份，必然拒绝。
- 运行结果、manifest 和恢复资源字段明确记录独立数值变体、扩展构建环境、20 步边界及恢复格数。

## 接口核验

- 本任务没有引入新的第三方接口。融合调用、`torch.autograd.Function`、扩展加载和 BF16/FP32 转换均复用提交 `4efb193` 已核验并完成远端资格基准的仓库内部实现。
- `pytorch-patterns` 已读取；采纳设备门、同种子、显式形状、参数/优化器 FP32、完整优化步恢复。技能示例建议混合精度可使用 `GradScaler`，与本仓库 BF16 硬合同冲突，本实现按近层规则保持 `scaler=null` 且不创建 `GradScaler`。

## 验证记录

- `uv run --no-sync python -m py_compile`：通过。
- JSON 标准库解析：通过。
- `bash -n`：通过。
- 首次直接模块导入失败：工作目录未把 `tools/` 加入模块路径，错误为 `ModuleNotFoundError`。改为 `PYTHONPATH=tools` 后通过；生产入口以文件路径执行，不受该验证命令影响。
- `/opt/miniconda3/envs/rwkv/bin/python`：模块导入、`--help`、模板 `--validate-config` 通过。
- 内存态解析配置：固定 K0、参数量 `104274`、`FusedK0TimeMix` 替换通过。
- 未运行 CUDA 编译、前向、反向、训练、目标评价、人工测试、`black` 或服务器命令。
