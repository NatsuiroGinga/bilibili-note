# FlashAttention 安装与兼容性验证报告

## 一、最终裁决

- FlashAttention `2.8.3.post1` 已在服务器项目 `.venv` 中从源码编译并安装成功，Qwen3-1.7B 可使用 `flash_attention_2` 完成前向。
- BF16 核心算子与 PyTorch SDPA 的小张量输出一致，本次测试最大与平均绝对误差均为 `0.0`。
- 在 RTX 5090、BF16、批大小 `4`、序列长度 `512` 的 Qwen3-1.7B 前向基准中，FlashAttention 没有带来吞吐或峰值显存收益。
- **当前正式基线继续使用原生 SDPA；FlashAttention 只保留为可选兼容后端，不进入当前正式基线。**
- 本结论只适用于本次模型、硬件、批大小和序列长度，不外推到更长序列、训练反向或其他基座。

## 二、环境与安装

- GPU：NVIDIA GeForce RTX 5090，计算能力 `12.0`。
- Python：`3.10.12`。
- PyTorch：`2.13.0+cu130`。
- Transformers：`4.57.6`。
- CUDA 编译器：`13.0.88`。
- FlashAttention：`2.8.3.post1`。
- Ninja：`1.13.0`。
- einops：`0.8.2`。
- `torch`、`transformers`、`peft`、`trl`、`bitsandbytes` 安装前后版本一致。
- 源码构建耗时 `148 分 28 秒`，安装退出码为 `0`。
- 安装后数据盘使用率为 `66%`，剩余约 `18 GiB`。

## 三、功能验证

### 3.1 BF16 核心算子

- 输入形状：`[2, 64, 4, 64]`。
- 最大绝对误差：`0.0`。
- 平均绝对误差：`0.0`。
- 峰值显存：`1,114,112` 字节。
- 结果：通过。

### 3.2 Qwen3-1.7B 最小前向

- 注意力实现：`flash_attention_2`。
- 输入形状：`[1, 20]`。
- 输出形状：`[1, 20, 151936]`。
- 含模型加载墙钟时间：`4.0905` 秒。
- 峰值显存：`4,064,542,720` 字节，约 `3.79 GiB`。
- 结果：通过。

## 四、SDPA 与 FlashAttention 对照

固定条件：BF16、批大小 `4`、序列长度 `512`、预热 `5` 次、计时 `20` 次。

| 指标 | SDPA | FlashAttention |
| --- | ---: | ---: |
| 平均延迟 | 45.6915 ms | 45.8365 ms |
| P50 延迟 | 45.6505 ms | 45.8398 ms |
| P95 延迟 | 45.9206 ms | 45.8793 ms |
| 吞吐 | 44,822.3 token/s | 44,680.5 token/s |
| 峰值分配显存 | 4,729,373,184 B | 4,728,848,896 B |
| 前向峰值增量 | 1,254,096,896 B | 1,254,096,896 B |
| 峰值保留显存 | 5,312,086,016 B | 5,366,611,968 B |

- 延迟速度比为 `0.99684`，FlashAttention 约慢 `0.32%`。
- 峰值分配显存比为 `0.999889`，两者基本相同。
- 末位置 logits 最大绝对差为 `0.1875`，平均绝对差为 `0.02928`。
- 余弦相似度为 `0.999973`，Top-1 一致率为 `100%`。
- 全元素 `rtol=0.05, atol=0.05` 未通过，因此不能表述为严格逐元素一致。

## 五、故障与防复发

- 首次安装因 SSH 包装器超时后由人工终止，终止证据已保留；唯一重试补齐 CUDA 路径和 Ninja 后安装成功。
- 首个兼容验证脚本因非 ASCII 文本被错误按 JavaScript UTF-16 码元做 Base64 编码，在 Python 解析前失败，未执行 CUDA 或模型计算。
- 修正为 ASCII 脚本并通过语法预检后，核心算子验证成功。
- Qwen 首次集成验证因 `--no-deps` 安装缺少包声明的 `einops` 而停止；补装最小运行时依赖后前向成功。
- Base64 远程脚本的 UTF-8 编码与语法预检规则已写入 `thesis/experiments/llm_probe/AGENTS.md`。

## 六、制品路径

服务端与本机均保留相同的目录结构：

- 服务端：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/verification/flash-attention-install-20260730/`
- 本机：`thesis/experiments/llm_probe/runs/verification/flash-attention-install-20260730/`

关键文件：

- 安装日志：`install-attempt-2.log`。
- 安装状态：`attempt-2-state.txt`。
- 环境快照：`environment-summary.txt`、`toolchain-preflight.txt`。
- 版本对比：`pre-install-versions.txt`、`post-install-versions.txt`、`version-comparison.txt`。
- 核心兼容结果：`compatibility-results.json`、`functional.log`。
- Qwen 最小前向：`qwen-minimal-forward-results.json`、`qwen-minimal-forward.log`。
- 后端对照：`backend-benchmark-results.json`、`backend-benchmark.log`。

