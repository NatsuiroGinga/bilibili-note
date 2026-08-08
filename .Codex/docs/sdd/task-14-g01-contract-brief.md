# 任务十四 G0/G1 协议复用审计简报

## 目标

判断任务十一 S1/S2 是否可以分别作为任务十四 G0/G1 使用，避免无意义重复训练。

## 输入

- `.Codex/docs/2026-07-21-任务十一边界锚定稀疏监督实验记录.md`
- `.Codex/docs/2026-07-22-任务十四G0-G5同预算训练设计.md`
- 本地与服务端 `runs/physics-sparse/qwen3-1.7b-seed42-s1-anchor0-fullphys202-v1/`
- 本地与服务端 `runs/physics-sparse/qwen3-1.7b-seed42-s2-anchor0-fullphys202-v1/`

## 必查字段

随机种子、202 次有效更新、模型绝对路径、训练与验证输入 SHA-256、状态掩码 SHA-256、物理样本顺序、学习率、生成批大小、梯度累积、物理批大小、状态监督模式、损失权重和最终评价函数版本。

## 约束

- 只读审计，不修改代码、配置、权重或结果。
- 不启动训练，不运行测试，不下载模型。
- 可使用 `GPU_SSH`/`GPU_PWD` 连接服务器；变量缺失时先 `source ~/.zshrc`。
- 服务端操作范围限制在 `/root/autodl-tmp/thesis/experiments/llm_probe`。

## 输出

写入 `.Codex/docs/sdd/task-14-g01-contract-report.md`。报告必须逐字段给出证据，并以“可严格复用”或“必须重跑”之一结尾；如必须重跑，给出具体差异，不执行重跑。

