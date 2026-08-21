# RWKV K0 CUDA 融合核工作笔记

## 一、当前 K0 合同

- 容量选择收据已封印 `selected_adapter=R2`、`selected_capacity=K0`、`target_arrays_loaded=0`。
- K0 形状为 `hidden_size=112`、`head_size=16`、`heads=7`、`sequence_length=128`、`lora_size=8`、单 TimeMix 层，结构身份为 `legacy_single_time_mix`。
- K0 R2 当前参数量台账为 `104274`；本任务不增删任何模型参数。
- 当前 BF16 入口在 TimeMix 投影后将 `r,w_clamped,k,v,a,kk` 提升到 FP32，再调用纯 PyTorch `legacy.rwkv7_op`；递归状态和 GroupNorm 保持 FP32。
- 活动纯 PyTorch BF16 训练正在服务器进行，本任务不修改其任何文件，不访问其服务器状态。

## 二、官方固定源码

- 官方仓库：`https://github.com/BlinkDL/RWKV-LM`。
- 固定提交：`952102498e9ed367ea0a59ee64106916d474d30f`。
- 许可证：Apache License 2.0。
- 本机已归档 tarball：`thesis/experiments/llm_probe/artifacts/rwkv-baseline-deps/rwkv-baseline-deps-prefetch-20260806t030118z-attempt3/sources/RWKV-LM-952102498e9ed367ea0a59ee64106916d474d30f.tar.gz`。
- `RWKV-v7/train_temp/cuda/rwkv7_clampw.cpp` SHA-256：`f6781adacbe0ab8638b666e0bd49098e262a861b7cc95fb1735ab54a43d82628`。
- `RWKV-v7/train_temp/cuda/rwkv7_clampw.cu` SHA-256：`a879dd478457290ebe793a10fcd0c1b93db1e1afb9d51ff8f8f1245a0146bbfb`。
- 根 `LICENSE` SHA-256：`c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`。

## 三、公式与接口映射

- 当前纯 PyTorch 算子输入为 `r,w_clamped,k,v,a,b`，其中 `w_clamped=-softplus(-w_raw)-0.5`，算子内计算 `exp(-exp(w_clamped))`。
- 官方 `rwkv7_clampw` 核输入为 `r,w_raw,k,v,a,b`，核内通过 `W_SCALE=-exp(-0.5)` 与 sigmoid 计算相同的 soft-clamp 衰减。
- 当前 TimeMix 调用映射应为 `fused(r, w_raw, recurrent_k, v, -kk, kk*a_gate)`；不得传入 `w_clamped`。
- 官方 Python 包装的两处 `64` 是可改头宽：源码注释明示 `can change 64 to your HEAD_SIZE`。CUDA 核本体以 `_N_` 编译宏参数化，反向 `float4` 读取要求 `N%4==0`，K0 `N=16` 满足。
- 前向每个批样本和头保持 `N` 行 FP32 状态，每 `16` 步保存一个 `N×N` FP32 边界状态，并保存 `[B,T,H,N]` FP32 `sa`。
- 输入、输出、上游梯度与六输入梯度均为 BF16；核内状态和累加为 FP32。

## 四、Context7 核验

- 解析库 ID：`/pytorch/pytorch`，高信誉；可用版本列表最新为 `v2.11.0`。
- 为获取更新文档，采用高信誉站点 ID `/websites/pytorch_2_12`。Context7 未提供目标 `2.13` 文档条目。
- PyTorch 2.12 文档确认 `torch.utils.cpp_extension.load(name, sources, extra_cflags, verbose, ...)` 以 JIT 方式编译并加载 C++/CUDA 扩展。
- PyTorch 2.12 文档确认自定义 `torch.autograd.Function` 实现静态 `forward` 和 `backward`，通过 `.apply(...)` 调用，与官方固定源码一致。
- 目标 `2.13.0+cu130` 的精确 ABI、参数兼容和 `sm_120` 代码生成仍需目标服务器实测。

## 五、误差门与性能门

- BF16 正常数单次舍入单位 `u=2^-8=0.00390625`。官方核在前向输出和反向六梯度各发生一次 BF16 量化，且使用 CUDA `__expf` 与 fast-math；内部主状态仍为 FP32。
- 在看到任何待测结果前冻结 `atol=0.03125=8u`、`rtol=0.02≈5.12u`，混合通过式为 `|candidate-reference| <= atol + rtol*|reference|`。
- 近零元素的 `max_rel` 仅作诊断，通过性以混合门判定，避免用分母噪声误判。
- 整轮性能资格不设虚构加速比：`fused_valid_flows_per_second >= pytorch_valid_flows_per_second`，且 `fused_peak_memory <= pytorch_peak_memory`。若数值或选择一致门失败，即使性能更快也否决接入。

## 六、待完成

- 落盘官方原件、专用 C++ 注册文件和清单。
- 实现不触发导入时编译的独立 Python 后端。
- 实现合成、LSPR23 首批和整轮基准阶段。
- 冻结配置、唯一启动器和实施报告。
