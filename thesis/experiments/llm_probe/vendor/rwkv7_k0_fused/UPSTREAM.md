# BlinkDL RWKV-7 K0 基础 WKV 源码说明

## 来源

- 官方仓库：`https://github.com/BlinkDL/RWKV-LM`
- 固定提交：`952102498e9ed367ea0a59ee64106916d474d30f`
- 许可证：Apache License 2.0
- 官方原路径：`RWKV-v7/train_temp/cuda/rwkv7_clampw.cpp`、`RWKV-v7/train_temp/cuda/rwkv7_clampw.cu`

`upstream/` 中的两个文件与固定提交逐字节一致。`derived/rwkv7_k0_clampw.cpp` 基于官方 C++ 注册文件，只将 `TORCH_LIBRARY` 命名空间改为 `rwkv7_k0_clampw`，并重排了格式；CUDA 计算核未修改。

## K0 专用编译合同

- `_N_=16`
- `_CHUNK_LEN_=16`
- BF16 输入、输出和梯度
- FP32 递归状态、分块状态和核内累加
- `C=112`、`H=7`、`T=128`
- 目标架构 `sm_120`

上述专用化不改变当前 K0 TimeMix 参数、公式、ChannelMix 缺失、单层身份或训练合同。
