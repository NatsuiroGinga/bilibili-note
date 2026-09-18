# N12 G1 全 T17 零更新梯度筛查实施计划

## 状态与边界

- 状态：实施中；仅实现 `screening_only` 的 G1，不启动本机或远端运行。
- 文件所有权：
  - `thesis/experiments/llm_probe/tools/ch3_drift_n12_g1_equal3_gradient_screen.py`
  - `thesis/experiments/llm_probe/configs/ch3-drift-n12-g1-equal3-gradient-screen-v1.json`
  - `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_drift_n12_g1_equal3_gradient_screen_v1.sh`
  - 本目录的本计划与实现报告。
- 明确不实现：G2、family 交叉拟合、family 打乱负控、PF-FAC、T18--T25 读取、参数更新型辅助训练或课程效果声明。

## 权威输入

- 研究卡第 5.1 节冻结 G0 的 T17 端点、种子 42、每类 1,500,000、batch 1024、Adam `1e-4`、一遍成员、原 MTP/TPP/TOV 定义和每 32 批次检查点；第 6 节定义 `g`、`u`、原始内积和余弦；第 7.1--7.2 节定义制品与 G1 停止门。
- G0 配置 SHA-256：`85f19d44be6a646df85c34daba7ff93390f5d997281ed06b419992459ec07ce5`；G0 脚本 SHA-256：`43601c2229bae12efc0185f72083df6951ee55092b41802ea9e4c5378c5bc68d`。
- 字符端点：结果 `1815b8e81289df2dd613ab640d49413d378afb1518344378c7b60aa422e17c71`，检查点 `70f195ff8048b450772f1d95a8913cc4633e52aca03cde0d621859451fb630a1`。子词端点：结果 `d8ddb63a94d107facd0ab6c910cf560bf46f798cda071406067b1fb1d949db2d`，检查点 `1c4b931ff85d26cc2b517e21e2b1a821424b3089cec9d7513b4785c1f83c951c`。
- T17 raw DGA 只用于将 family 聚合回 eSLD；family 不进入检测探针输入，也不称为底层生成器。

## 唯一实现解释

1. 从两个 G0 检查点加载新身份的 `PretrainedBranch`，保留其训练后 MTP/TPP/TOV 头；字符端点不称为 P0，子词端点与 P0 相同仅作为已核验事实记录。
2. 用两支 `EncoderBranch` 的 max+mean 池化特征训练 P0 同型轻量二分类头。编码器冻结，探针头使用 P0 的 batch 1024、Adam `1e-4`、dropout 0.1 和一次完整 T17 拟合成员遍历；这不是对 P0 分类器的续训。
3. 对每个分支在完整 T17 fit 的同一固定批顺序、`train()` 模式和 G0 `pretraining_views(seed + batch_index)` 下计算 MTP/TPP/TOV。每批任务均值乘以其有效监督数，累积后除以全成员有效监督总数，得到任务定义下的完整成员平均梯度；此归一化避免尾批或监督位置数改变任务方向。
4. 探针冻结且设为 `eval()`。在完整 T17 val 上分别对良性 BCE、DGA micro BCE、排除歧义 eSLD 后的 DGA family 宏 BCE 求编码器梯度。family 仅决定 macro 加权，绝不送入模型。
5. 对所有 `branch x task x risk` 保存 FP32 原始点积、两范数、余弦和单位方向内积。G1 仅当同一分支与风险下至少一个任务余弦小于零且另一个非负时输出“允许进入 G2”；否则输出“G1 否决”。

## 可恢复性与制品

- 每 32 个 I/O 批次原子保存 `checkpoint.pt`；探针阶段保存模型、优化器、RNG、进度和身份，梯度阶段保存 FP32 完整参数分片累积、有效监督数、进度和 RNG。恢复前重新核验脚本、配置、T17 输入、P0/G0 哈希。
- 结果仅保存聚合梯度摘要、family 映射计数和资源收据；检查点可保存完整梯度向量，不保存原始域名。
- 使用 `cuda-bf16-amp-fp32-sensitive-v1` 的共享精度合同；参数、优化器、归一化和损失保持 FP32，BF16 仅用于 CUDA 前向计算。

## 验收命令

```bash
/opt/miniconda3/envs/rwkv/bin/python -m py_compile tools/ch3_drift_n12_g1_equal3_gradient_screen.py
/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_n12_g1_equal3_gradient_screen.py --help
jq empty configs/ch3-drift-n12-g1-equal3-gradient-screen-v1.json
bash -n scripts/remote_launchers/run_ch3_drift_n12_g1_equal3_gradient_screen_v1.sh
git diff --check -- <本任务五个新文件>
```

## 技能与收据

- `daily-coding`：`/Users/bilibili/.codex/skills/backup/daily-coding-20260811-112930/SKILL.md`，SHA-256 `da2399b50859b9d57281b9bc0dc456082db93d47486ae22967ebf3f17d354ae3`，读取时刻 `2026-09-08T13:34:31+0800`。
- `pytorch-patterns`：`/Users/bilibili/.codex/skills/pytorch-patterns/SKILL.md`，SHA-256 `22b76f559f17d4b0e44eda71d353065e5da181203d165546edb08c16cc362d85`，读取时刻 `2026-09-08T13:34:31+0800`。

## 已知风险

- G1 的负余弦只能支持进入 G2，不足以宣称短步伤害、family 特异性或课程有效。
- raw family 连接的歧义 eSLD 必须排除；若可唯一 family 无效或梯度非有限，则为工程无效而非科学否决。
