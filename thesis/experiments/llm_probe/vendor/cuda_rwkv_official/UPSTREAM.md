# BlinkDL RWKV-7 CUDA 源码说明

## 来源

- 官方仓库：`https://github.com/BlinkDL/RWKV-LM`
- 固定提交：`952102498e9ed367ea0a59ee64106916d474d30f`
- 许可证：Apache License 2.0
- 官方原路径：`RWKV-v7/train_temp/cuda/rwkv7_clampw.cpp`、`RWKV-v7/train_temp/cuda/rwkv7_clampw.cu`

`upstream/` 中的两个文件与固定提交逐字节一致。`derived/cuda_rwkv_clampw.cpp`
只把算子注册命名空间改为编译时必填的中性宏，并重排 C++ 格式；CUDA 计算核不作任何修改。

## 容量专用编译合同

| 容量 | 通道 | 头大小 | 头数 | 序列长度 | 分块长度 | 注册命名空间 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `small` | 112 | 16 | 7 | 128 | 16 | `cuda_rwkv_small_clampw` |
| `large` | 768 | 64 | 12 | 128 | 16 | `cuda_rwkv_large_clampw` |

两个容量使用独立扩展名、命名空间和持久构建根。六输入、输出与六梯度为 BF16，递归状态、分块状态和核内累加为 FP32。
