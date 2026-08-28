# 全容量 MLP 独立实体头 S1 证据笔记

- **STATUS=APPROVED_FROZEN**
- **依据提交**：`a3a4cd4`、`5a9bc59`
- **S0 制品**：`thesis/experiments/llm_probe/runs/diagnostics/ch3-full-mlp-valid-2x2-source-s0-seed42-v1/aggregate-results.json`
- **S0 制品 SHA-256**：`013fcb0654626316ed3405e8f67bf1e8dd04149b04f0c46f7d7ec4de21db9163`

## S0 事实

- 状态 `finished/exit0`，`target_reads=0`、`training_runs=0`、`parameter_updates=0`、`formal_paper_evidence=false`。
- 源验证共 `13,529` 个实体，其中正实体仅 `20` 个、负实体 `13,509` 个。
- B00 固定 mean-max 相对 max 出现非支配源年信号；B10 固定 mean-max 的实体 AP 差为 `-0.1377261175624055`，终端曲线最差差值 `-0.4`，被 B10 max 支配。
- 因此本 S1 不是延续 B10 上已有正信号，而是在更强 B10 父检查点上检验可学习多算子信息；失败先验必须保留。

## 冻结身份

- 父运行：`ch3-full-mlp-complete-entity-lp-protocol-a-q0-seed42-v1-bf16-v1`。
- B10：`checkpoints/selected-B10.pt`，SHA-256=`5816387f1af57518a22514d5e21b8343a65747e4ffff41c6e6ef4786dd60d763`。
- O11：`checkpoints/selected-O11.pt`，SHA-256=`7226dd49852f18b7196fca134148f8a1263af4b461ebba5b6969220ff00ff9f6`。
- 父配置 SHA-256：`673bab8ef85e4653f8b104180dbe296f89e6a6468a4a91e53dc5bcfa65805161`。
- 源数据清单 SHA-256：`195e3e3f081920c72f37493cba59faf34b596271a86083b7f3897543eb04e88d`。
- B10 验证逐流概率 SHA-256：`ad7b7b8db54ee21733a44b6a2b9d6c54b60e703b42a7601d8d41e73187ab36a0`。

## LBFGS 接口

- 目标环境沿用父运行 PyTorch 与精度身份；实体头参数、输入、损失和梯度全部 FP64。
- Context7 已解析官方 PyTorch 库 `/pytorch/pytorch` 与官方文档镜像；仓库没有现成 `torch.optim.LBFGS` 生产实现可继承。
- 用户最终冻结：`lr=1.0`、`max_iter=100`、`max_eval=125`、`tolerance_grad=1e-7`、`tolerance_change=1e-9`、`history_size=10`、`line_search_fn=strong_wolfe`。
- 每个头从全零参数开始，只调用一次全批量 `optimizer.step(closure)`；无随机批次、无学习率／容量网格、无其他优化器回退。

## 局限

- 源验证只有 `20` 个正实体；S1 只作单次筛选，不报告显著性、稳定最优或跨年有效性。
- 参数匹配控制的两个输入列完全相同，函数秩低于候选；其作用是隔离“第二个自由参数”与“新增 max 信息”，不是另一个强模型族。
- LSPR24 读取固定为 `0`；任何目标年访问都使本运行无效。
