# N12 G1 实现报告

## 状态

- 日期：2026-09-08。
- 实现状态：已完成静态实现与入口验证；尚未启动本机或远端真实数据运行。
- 科学状态：实验待证。G1 的输出最多裁决是否允许进入 G2，不能表述为 family 伪未来、短步伤害或课程有效。

## 已新增文件

- `thesis/experiments/llm_probe/tools/ch3_drift_n12_g1_equal3_gradient_screen.py`
- `thesis/experiments/llm_probe/configs/ch3-drift-n12-g1-equal3-gradient-screen-v1.json`
- `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_drift_n12_g1_equal3_gradient_screen_v1.sh`
- `g1-implementation-plan.md`
- 本报告。

未修改或回滚任何既有源码、配置、运行制品、恢复卡或论文正文。

## 实现边界

1. 入口仅接收配置中列出的 T17 `fit`、T17 `val` 和 T17 raw DGA family 文件，并递归拒绝输入清单中的 T18--T25 字符串。
2. G0 字符与子词端点必须分别通过结果、检查点、状态、G0 配置、冻结运行源码快照、有效监督数、优化器和随机状态核验；新字符端点不称为 P0。G0 活动源码在运行后已修复，G1 因而核验字符运行目录内 SHA-256 为 `43601c...` 的实际运行快照，避免后续代码修复污染既有制品谱系。
3. 检测探针只训练 P0 同型 max+mean 分类头。两个编码器在探针拟合中冻结；batch 1024、Adam `1e-4`、dropout 0.1、完整 T17 fit 一遍均由 P0/G0 冻结配置复用。
4. MTP、TPP、TOV 梯度使用 G0 的同一 `pretraining_views(seed + batch_index)`、`train()` 模式、任务头和损失定义。每任务以全体有效监督数归一，保存完整 FP32 参数梯度累积。
5. 风险梯度在冻结探针 `eval()` 模式下计算。良性与 DGA micro 为完整 T17 val BCE；family macro 仅对 raw 首标签可唯一连接的 DGA eSLD 等权聚合，歧义或缺失键排除。
6. 结果报告原始点积、两侧范数、余弦、单位方向内积、任务间余弦、有效监督数和 family 映射计数。只有同一分支和风险下出现一个任务余弦负值、另一个非负值，才输出 `eligible_for_g2_only`。
7. 资源收据同时记录实际 `float32_matmul_precision`、CUDA matmul TF32 与 cuDNN TF32 开关；通用精度配置与 P0/G0 的 `high` 数值路径存在文字差异时以实际运行收据披露，不据此改变本轮计算。

## 可恢复性

- 每 32 个 I/O 批次原子覆盖 `checkpoint.pt`。
- 探针阶段保存分类头、Adam 状态、进度、损失累计和随机状态。
- family 和梯度阶段保存探针状态、G0/P0 绑定身份、FP32 全成员梯度向量、有效监督单位、进度、family 摘要和随机状态。
- 恢复时重新核验配置、脚本、T17 输入、P0 和 G0 SHA-256；不持久化原始域名。

## 已执行验证

```bash
/opt/miniconda3/envs/rwkv/bin/python -m py_compile tools/ch3_drift_n12_g1_equal3_gradient_screen.py
/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_n12_g1_equal3_gradient_screen.py --help
/opt/miniconda3/envs/rwkv/bin/python -c "import sys; sys.path.insert(0, 'tools'); import ch3_drift_n12_g1_equal3_gradient_screen as g; from pathlib import Path; c=g.load_config(Path('configs/ch3-drift-n12-g1-equal3-gradient-screen-v1.json')); print(c['schema_version'], c['run_identity'])"
jq empty configs/ch3-drift-n12-g1-equal3-gradient-screen-v1.json
bash -n scripts/remote_launchers/run_ch3_drift_n12_g1_equal3_gradient_screen_v1.sh
git diff --check -- <本任务新增文件>
```

以上命令均通过。根据实验工程规则，未创建人工夹具、未运行 pytest、未运行 black，也未发起远端启动。

## 遗留风险

- 尚未经历真实 T17 全量运行，因而检查点序列化吞吐、峰值显存和断点恢复只完成静态审查，待主代理启动真实 G1 后以制品核验。
- 负余弦本身只是零更新一阶方向证据。即使 G1 输出可进入 G2，也不能跳过 G2 的短步、family 打乱负控与后续课程资格门。
