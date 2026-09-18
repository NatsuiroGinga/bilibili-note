# DRIFT 权重 Hugging Face 登记笔记

## 已核范围

- 数据 revision：`3b31077020cd1c013d0a75cad51042a2327c4521`。
- G0 字符与子词训练均已完成，恢复卡已登记结果与检查点 SHA-256。
- G1 的科学状态为 `eligible_for_g2_only`，其检查点包含梯度和 family 状态，不能作为模型权重上传。
- G2 当前为 `running/verify`，不得读取或上传其可变检查点。

## G0 本地核验

- 字符运行身份 `ch3-drift-t17-equal3-auxheads-char-gradient-base-v1`：源检查点 SHA-256 为 `70f195ff8048b450772f1d95a8913cc4633e52aca03cde0d621859451fb630a1`，导出的纯 `state_dict` SHA-256 为 `238de2c4277c60271136d5f7326c412ff88773a85495ba6143a7c7124544c2b6`，字节数 `4105657`。
- 子词运行身份 `ch3-drift-t17-equal3-auxheads-subword-gradient-base-v1`：源检查点 SHA-256 为 `1c4b931ff85d26cc2b517e21e2b1a821424b3089cec9d7513b4785c1f83c951c`，导出的纯 `state_dict` SHA-256 为 `791cb5af4b03502befa4944f6205045209c0104fcbdc66084bd2b1d8745f48fe`，字节数 `51141177`。
- 两份导出均为 80 个张量的纯 `state_dict`；不含优化器、随机状态、样本或日志。

## 上传与远端核验

- `hf auth whoami` 确认当前账号为 `Heehobino`；`Heehobino/drift-route-checkpoints` 已创建为私有模型仓库。
- 两份权重制品上传提交为 `f66608f9bc3a240152280fe81d5c40d34914d262`；最终元数据提交为 `d93915042e55edd659e5119888f821d10d30a96b`。
- 最终下载副本中的两份权重 SHA-256 与本机导出一致，README、总清单与两份溯源 JSON 均逐字一致。
- G2 复查仍为 `running/verify`，终态哈希为空；本机清单保持 `pending`。

## 待核

- G0 源检查点的本地路径、状态和实际 SHA-256。
- 导出后 `state_dict` 的键结构、字节数与 SHA-256。
- Hugging Face 认证身份、仓库私有属性、上传提交与远端哈希一致性。
