# Task 1：实体级 BCE 损失函数（独立模块，零宿主改动）

## 全局约束（逐字取自计划）

- 缩容档 `width_profile = half`，骨干参数量断言 `240955`；`run_tier = screening_only`。
- `evaluation.target_reads` 必须为 `0`；**全程不得读取 LSPR24**。
- `mechanism.entity_aggregation.alpha` 严格等于已冻结的 `0.5`，不得按实验读数回调。
- **三项损失的权重是新魔法数字**，须按根 `AGENTS.md` 门禁登记：用途和值、文献依据
  （没有则写「无直接文献依据」）、数学推导、真实数据诊断路径、适用边界、
  是否接触最终目标标签、核验状态。**不得随手取 `1.0` 而不登记。**
- 新增开关**默认关闭**，关闭时必须走与改动前**逐位相同**的代码路径。
- 提交用 `git commit -m "..." -- <精确路径>`，**绝不 `git add .`**，
  提交信息末尾**不得**有 Co-Authored-By 署名。
- **不停正在跑的 C01-half**——它按旧 C00 定义训练，仍是有效对照证据。

---

---

**Files**
- Create: `thesis/experiments/llm_probe/tools/ch3_ft_entity_bce.py`

**Interfaces**
- Produces：`entity_bce_loss(flow_logits, flow_valid, entity_of_row, labels, aggregation, alpha, torch_module) -> tuple[Tensor, dict]`
  供任务 2 的宿主调用。`aggregation` 取 `"maximum"` 或 `"tail_mean"`。

- [ ] **步骤 1：读既有实体聚合实现，不要另造**

先读 `tools/ch3_ft_entity_ranking_loss.py` 中已有的实体内聚合代码
（ETA 的 top-`k` 均值已在其中实现并经实测核验）。
**本任务必须复用该聚合逻辑，不得重新实现一份**——两份实现会漂移。
若发现它与本任务需要的签名不兼容，**停下报告**，不要自行改造它（它服务于 BER，是在用的）。

- [ ] **步骤 2：实现聚合与损失**

```python
def entity_bce_loss(flow_logits, flow_valid, entity_of_row, entity_labels,
                    aggregation, alpha, torch_module):
    """实体级 BCE：先把逐流 logits 聚合成实体分数，再对实体做二分类。

    aggregation="maximum" 时取实体内最大值（z1'=0）；
    aggregation="tail_mean" 时取 top-ceil(alpha*m) 的均值（z1'=1，即 ETA）。
    返回 (loss, diagnostics)。loss 对 flow_logits 可导。
    """
```

**关键约束**：
- 聚合必须在 **FP32** 中做（仓库合同：阈值状态、CVaR 归约、梯度范数与投影须 FP32）
- 无效流（`flow_valid` 为假）必须**完全排除**，不得以 `0` 参与 max 或 top-k
- 空实体（全部流无效）必须跳过而非产生 `NaN`
- `alpha` 只接受 `0.5`，其他值 raise

- [ ] **步骤 3：真实数据自检，不建夹具**

用 `tools/` 下既有的物化视图读一小批真实片段（**不得构造人工夹具**，仓库明令），
断言三件事并打印数字：

1. `aggregation="maximum"` 时，实体分数逐位等于该实体有效流 logits 的 `max`
2. `aggregation="tail_mean"` 且实体只有 1 条有效流时，结果**逐位等于** `maximum`
   （`ceil(0.5*1)=1`，退化为 max）
3. `loss.backward()` 后，梯度只落在被选中的流上，非选中流梯度恰为 `0`

自检脚本跑完即删，不进仓库。

- [ ] **步骤 4：提交**

```bash
git commit -m "feat(ch3): add entity-level BCE loss module" -- thesis/experiments/llm_probe/tools/ch3_ft_entity_bce.py
```

---
