# DRIFT 双侧风险约束更新专家混合实施计划

<!-- RESEARCH_ROUTE=DRIFT -->

- **日期**：2026-09-08
- **状态**：待主代理／用户批准后实施
- **设计源**：[研究卡](../../../thesis/methods/第三章-DRIFT双侧风险约束更新专家混合研究卡.md)
- **范围**：只实现折0零训练求解收据与三臂32批联合短步；不运行折1、目标年份或 N12 重训
- **所有权**：后续唯一实现代理负责本计划列出的新工具、配置和运行目录；不得修改或回滚其他代理与用户改动

## 一、P0 输入冻结

实现前逐项机械断言：

| 输入 | 路径／值 | 必须成立 |
| --- | --- | --- |
| G1结果 | `thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-n12-g1-equal3-gradient-screen-v1/result.json` | 包含六任务对三风险的原始内积 |
| G2字符梯度 | `.../ch3-drift-n12-g2-family-isolated-short-step-v1/fold-0-char-gradients.pt` | SHA-256 `c39ae82559ba1f1798e6177f1a1fb1698e7954315d132ee2939afff83baf575e` |
| G2子词梯度 | `.../ch3-drift-n12-g2-family-isolated-short-step-v1/fold-0-subword-gradients.pt` | SHA-256 `8d33c563bf4477aa8ac34f40590a4e17545b5df74af2ccb6f704da55f58513be` |
| 固定块 | G2折0既有32批 | 32768样本；SHA-256 `62fefb2765c8137f60155371b3e8a9d2bf0a609f2c65a94a09cf403858584b20` |
| G2配置 | 既有配置 | SHA-256 `680defe1231c6da7ed0ef5ade50193f716eaed637b98d43815029cc47ff07435` |
| G2入口 | 既有实现 | SHA-256 `ee77137c828d1cdeaf6c444bc3cd72e6d90fcce439ef3ee18e47dac5a9d2d593` |

不得把原始 `status.json` 的 `running/verify` 改写为完成；G2仍是用户批准的折0充分性早停。

## 二、P0 文件范围

后续实现代理只可新增：

- `thesis/experiments/llm_probe/tools/ch3_drift_dual_risk_update_expert_mix.py`
- `thesis/experiments/llm_probe/configs/ch3-drift-dual-risk-update-expert-mix-fold0-v1.json`
- `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_drift_dual_risk_update_expert_mix_fold0_v1.sh`
- `thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-dual-risk-update-expert-mix-fold0-v1/`
- `.Codex/docs/2026-09-08-DRIFT更新专家混合/implementation-report.md`

允许复用既有 G2 函数，但不得修改 G2 原始代码、配置、14个 arm、两份梯度制品、检查点或状态文件。若复用必须修改既有生产文件，先停止并由主代理重新划定所有权。

## 三、P0 求解器合同

1. 从折0现有原始内积构造 `A[j,i]=<r_j,g_i>`，列顺序固定为 `char:MTP,char:TPP,char:TOV,subword:MTP,subword:TPP,subword:TOV`。
2. 解 `max gamma`，满足 `Aw>=gamma*1`、`w>=0`、`sum(w)=1`。
3. 期望复算权重为 `char:TOV=0.1918849335`、`subword:TOV=0.8081150665`，其余0；不得把期望值硬编码成求解输出。
4. 执行系数固定为 `alpha=6w`；机械断言非负、有限且 `sum(alpha)=6`。
5. 单独复算三项未四舍五入残差，并将输入矩阵、求解状态、`w`、`alpha`、`gamma`、残差、依赖版本和输入哈希写入 `solver-receipt.json`。
6. 同时求最小最大违约 `delta*`。若主问题不可行或 `delta*>0`，写 `decision=skip_update`，联合臂复制 `no_update` 端点并停止更新；不得执行松弛解。
7. 另写每分支独立单纯形诊断，预期最大最小裕量为 `-3.673e-06`；该诊断不改变全局解。

## 四、P0 三臂执行合同

三个臂必须从完全相同的字符／子词端点、优化器状态和随机状态开始，并消费同一32批、32768样本块：

| 臂 | 系数 | 说明 |
| --- | --- | --- |
| `no_update` | 六项全0 | 只跑相同评价路径 |
| `all_equal` | 六项全1 | 总质量6；两支同步更新 |
| `dual_risk_constrained_joint` | `alpha=6w*` | 两支同步更新；当前解只启用两个 TOV |

每个臂须恢复独立优化器副本，不共享可变状态；同一步先形成六个任务损失，再按该臂系数合成梯度，最后使用既有 G2 相同的裁剪与优化器顺序。禁止通过改变学习率、步数、裁剪、损失缩减、混合精度或批次顺序补偿某臂。

## 五、P0 输出与原子发布

每个臂写独立 JSON，至少包含：

- 运行身份、臂名、折号、32批、32768样本、块哈希；
- 两个起点和终点模型哈希、两个优化器状态身份；
- 六任务系数、每步有效监督计数；
- 合成梯度范数、裁剪前范数、是否裁剪、非有限检查；
- 良性 BCE、DGA micro BCE、DGA family-macro BCE、AP、AUROC；
- 默认阈值与既有源 FPR 阈值下的 FPR、FNR；
- 相对 `no_update` 和 `all_equal` 的未四舍五入差值。

先写临时文件，字段与哈希闭合后原子发布；失败保留原退出码、失败阶段和可恢复状态，不发布伪完成 `result.json`。

## 六、P0 裁决器

裁决器只机械执行研究卡第九节：

1. 联合臂相对 `no_update` 三个 BCE 均 `<=0`；
2. 相对 `no_update` 至少一个 DGA BCE 严格 `<0`；
3. 相对 `all_equal` 三个 BCE 均 `<=0`；
4. 相对 `all_equal` 至少一个 BCE 严格 `<0`；
5. 32批完成、指标有限、输入和优化器合同未漂移。

任一失败输出 `rejected_after_fold0_joint_short_step`。全部通过只输出 `eligible_for_next_design_review`，不得自动运行折1或目标年份。

## 七、实现步骤

### 步骤1：只读适配

- 读取 `thesis/experiments/llm_probe/scripts/AGENTS.md` 与既有 G2 工具接口。
- 确认两份梯度制品的键、参数名、张量形状和优化器恢复结构。
- 在实施报告登记实际安装的求解依赖与版本；首次使用第三方求解接口前按根规则查官方签名。

### 步骤2：求解与收据

- 实现确定性全局线性规划和最小松弛诊断。
- 用既有折0输入只运行零训练求解模式，核对权重、三残差、独立分支不可行结果和总质量6。
- 求解收据通过前不得进入32批更新。

### 步骤3：三臂联合短步

- 为两个分支加载独立端点与优化器副本。
- 按固定顺序串行运行三个臂，避免显存争用改变执行路径。
- 每臂消费相同数据块与随机增强收据，完成后立即评价并原子发布。

### 步骤4：机械裁决与报告

- 生成 `result.json` 与三臂比较表。
- 报告完整指标，不筛选有利指标。
- 若失败，立即停止；不调权、不改尺度、不延长步数。

## 八、验收命令

后续实现后执行最小相关验证，不创建人工夹具或单元测试：

```bash
cd thesis/experiments/llm_probe
source tools/env/activate.sh
uv run --no-sync python -m py_compile tools/ch3_drift_dual_risk_update_expert_mix.py
uv run --no-sync python tools/ch3_drift_dual_risk_update_expert_mix.py --config configs/ch3-drift-dual-risk-update-expert-mix-fold0-v1.json --solve-only
```

真实32批运行必须走仓库当前远程启动器合同，并在启动前由主代理核验服务器身份、磁盘、GPU、持久会话和是否已有同名运行。计划阶段不执行这些命令。

## 九、阻塞与停止

- 任一输入哈希不符：工程阻塞，保留证据，不作科学失败。
- 两支不能从各自优化器状态在同一批序上联合恢复：接口阻塞，停止并修订计划，不退化为重新训练。
- 主线性规划不可行或最小松弛 `delta*>0`：联合臂跳过更新。
- 三臂任一运行身份、数据块、步数、优化器或评价阈值不一致：比较无效。
- 任一科学门失败：当前静态联合形式否决，不扩展实验。

## 十、计划完成定义

本计划只有在以下制品全部存在并通过机械核验时才算实施完成：`solver-receipt.json`、三个臂 JSON、`result.json`、入口日志、哈希清单与 `implementation-report.md`。计划文档本身不表示机制获批、代码完成或实验有效。
