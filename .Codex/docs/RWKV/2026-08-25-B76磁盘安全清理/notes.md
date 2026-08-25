# B76 清理只读证据

## 活动状态

- B76 仅发现活动 `screen`：`ch3-cuda-rwkv-raw83-qualification-seed42-v1`；对应训练进程存在。
- 未发现 GRANDE 指定运行的 `screen` 或匹配训练进程，但其目录仍按用户指令保护。
- 文件系统可用 `21,703,548,928` 字节，已用 `85,670,633,472` 字节；本审计不改变这些读数。

## 指定历史目录核验

远端项目根下，以下四个相对路径均不存在，因而没有可删除远端对象：

- `runs/diagnostics/ch3-baselines-full`
- `runs/diagnostics/ch3-baselines-param-matched`
- `runs/diagnostics/ch3-final-weights`
- `runs/candidates/crossyear-rare-mass-protected-asymmetric-pot-q0-seed42-v1-rerun2`

本机前三项位于主工作区，第四项位于当前工作树。普通文件、逻辑字节和聚合哈希详见报告。前三项没有匹配检查点；第四项也没有匹配检查点。它们的本机字节量显著小于 2026-08-22 既有审计记录的对应远端历史字节量，故不能证明为完整回收副本。

## 本轮工程目录

- `runs/diagnostics/ch3-cuda-rwkv-dual-extension-build-b76-v1`：`1,440,674` 字节，约两小时前更新。
- `runs/diagnostics/ch3-cuda-rwkv-raw83-qualification-seed42-v1`：`27,448,881` 字节，活动训练目录，保护。
- `runs/diagnostics/ch3-cuda-rwkv-raw83-qualification-seed42-v1-microbatch4-engineering-archive`：`12,829,892` 字节，约一小时前更新。
- `runs/diagnostics/ch3-grande-lspr24-zero-train-descriptive-eval-bf16-v1`：`770,411` 字节，按用户指令保护。

双扩展构建诊断与微批四工程归档合计仅 `14,270,566` 字节，远低于历史磁盘门缺口，且未完成逐项回收与生命周期裁决，不列入可删路径。
