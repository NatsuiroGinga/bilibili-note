# DRIFT 权重 Hugging Face 登记任务计划

## 目标

建立仅登记已完成、身份闭合且可作为模型权重使用的 DRIFT 本机目录，并上传至私有 Hugging Face 模型仓库。

## 范围

- 本机登记目录：`thesis/experiments/llm_probe/runs/model-registry/drift-route-checkpoints/`
- 远端仓库：`Heehobino/drift-route-checkpoints`（私有）
- 远端路径：`checkpoints/<run_identity>/`
- 仅候选 G0 字符与子词完成权重；G1 仅登记不上传原因；G2 保持待定且不读取可变检查点。

## 阶段

- [x] 阶段 1：读取 DRIFT 恢复链与本地规则，确认边界。
- [x] 阶段 2：核验 G0/G1/G2 状态、G0 源检查点和可导出权重。
- [x] 阶段 3：导出 G0 `state_dict`、生成最小溯源清单与中文 README，并做一次敏感信息和文件类型预检。
- [x] 阶段 4：核验 Hugging Face 认证，创建或复用私有模型仓库并上传。
- [x] 阶段 5：核验远端文件列表与本地 SHA-256，完成上传报告。

## 决策

- G2 在本任务中只能登记为 `pending`，除非本代理本轮直接观测到 `status=completed` 且所有哈希闭合；不等待其完成。
- G1 检查点含梯度和 family 状态，不属于可发布模型权重，只在登记清单记录排除原因。
- G0 导出使用指定的本机 `rwkv` 解释器，源检查点保持只读。

## 当前状态

已完成。远端最终提交、文件清单、私有属性、本地与远端 SHA-256 和元数据一致性均已核验。
