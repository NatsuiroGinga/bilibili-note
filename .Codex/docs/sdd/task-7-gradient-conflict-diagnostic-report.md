# 任务七：真实批次梯度冲突诊断报告

- **日期**：2026-07-21
- **状态**：完成
- **正式运行**：`qwen3-1.7b-seed42-init-real20-v1`
- **SwanLab**：`vda5m96i`，`FINISHED`

## 1. 目的与范围

三档物理损失权重均未同时改善生成、状态和物理验证指标。本任务不更新模型参数，而是在初始 Qwen3-1.7B LoRA 与状态头上，使用 20 个真实 GeNIS/ns-3 配对批次直接测量三个目标在共享 LoRA 参数上的梯度方向和尺度。

实现文件：

- `thesis/experiments/llm_probe/src/flow_probe/gradient_conflict.py`
- `thesis/experiments/llm_probe/tests/test_gradient_conflict.py`
- `thesis/experiments/llm_probe/pyproject.toml`

命令入口：`flow-probe-diagnose-gradient-conflict`。

## 2. 实现约束

- 生成端每个配对步使用 4 个微批次，每批 4 个样本，等效批量 16。
- 状态与物理端每步使用同一组 4 个 ns-3 样本。
- 20 步均不执行优化器更新，`optimizer_updates=0`。
- 梯度点积和范数按 LoRA 参数张量逐项累计，不构造 17M 参数全量拼接向量。
- 保存的真值残差继续由既有数据接口拒绝。
- 正式物理残差严格除以正容量积分，不增加 `epsilon`。

## 3. 测试

唯一红测因模块尚不存在而失败：

```text
ModuleNotFoundError: No module named 'flow_probe.gradient_conflict'
```

红测日志：

```text
/root/autodl-tmp/thesis/experiments/llm_probe/runs/physics-gradient-conflict/verification-20260721-task7/red-test.log
```

服务器验证：

- 目标测试：**4/4** 通过。
- 直接受影响测试：**22/22** 通过。
- 本地 Black、Ruff 和 `git diff --check` 通过。

测试覆盖逐张量余弦、零梯度与非有限梯度拒绝、四档加权范数比和配对采样确定性。

## 4. 正式结果

| 指标                          |         结果 |
| ----------------------------- | -----------: |
| 配对批次                      |           20 |
| `cos(g_gen,g_physics)` 均值   |    -0.022452 |
| 生成-物理负夹角               |  20/20，100% |
| `cos(g_gen,g_state)` 均值     |     0.008956 |
| 生成-状态负夹角               |    8/20，40% |
| `cos(g_state,g_physics)` 均值 |     0.420673 |
| 状态-物理负夹角               |    5/20，25% |
| 生成梯度范数均值              |    34.820494 |
| 状态梯度范数均值              |     1.262911 |
| 物理梯度范数均值              |     3.697686 |
| 运行时间                      |    52.224 秒 |
| 峰值显存                      | 3478.814 MiB |

加权物理梯度相对生成梯度的平均范数比：

| `lambda_physics` |      比值 |
| ---------------: | --------: |
|            0.001 | 0.0001067 |
|             0.01 | 0.0010669 |
|             0.03 | 0.0032008 |
|              0.1 | 0.0106693 |

加权物理梯度相对状态梯度的平均范数比：

| `lambda_physics` |     比值 |
| ---------------: | -------: |
|            0.001 | 0.003191 |
|             0.01 | 0.031912 |
|             0.03 | 0.095736 |
|              0.1 | 0.319119 |

样本顺序 SHA-256：

```text
f085346605c5547154e8d715bcd5b0b42c3b74426932335ad1a26f8621077737
```

## 5. 制品

服务器：

```text
/root/autodl-tmp/thesis/experiments/llm_probe/runs/physics-gradient-conflict/qwen3-1.7b-seed42-init-real20-v1/
```

本地归档：

```text
thesis/experiments/llm_probe/runs/physics-gradient-conflict/qwen3-1.7b-seed42-init-real20-v1/
```

运行保存配置、环境、输入哈希、样本顺序、20 条逐步指标、汇总、控制台、SwanLab 原始日志和制品清单。运行编号 `vda5m96i`，峰值显存 3478.814 MiB，服务器运行结束后 screen 已退出、GPU 空闲。

## 6. 裁决

生成与物理梯度在 20/20 批次上方向持续为负，满足进入最小梯度协调或冲突投影对照的前提。但平均余弦绝对值只有 0.022452，且 `lambda_physics=0.01` 时加权物理梯度仅为生成梯度的约 0.107%。因此证据只能支持“存在持续但较弱的一阶冲突”，不能表述为强冲突或唯一根因。

下一实验只允许在相同 M2 权重和协议上增加最小投影对照；若投影不能同时保留生成、状态和物理收益，则停止扩展该机制。
