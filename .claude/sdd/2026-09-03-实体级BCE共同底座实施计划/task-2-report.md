# 任务 2 实施报告：挂载到 training_step，开关默认关闭

## 工作现场

与任务 1 相同的现场更正：宿主代码在 worktree
`/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819`（分支
`codex/ch4-dtep-pbc-20260819`），不在主仓库 `/Users/bilibili/personal/note`
（分支 `codex/ch3-cpa-elp-20260820`）。本任务的实施计划与任务 1 报告都只存在于
主仓库的 `.Codex/docs/RWKV/2026-09-03-实体级BCE共同底座实施计划.md` 与
`.claude/sdd/2026-09-03-实体级BCE共同底座实施计划/task-1-report.md`——这正是根
`AGENTS.md` 记录过的已知反例（"恢复卡引用的两份文档在另一分支，链接在当前工作树点不开"）。
本报告延续任务 1 的落点（主仓库 `.claude/sdd/...`），保持与既有台账同一位置；
但全部实现、验证与提交都发生在上述 worktree 内。

## 改动的确切位置

全部改动集中在唯一文件
`thesis/experiments/llm_probe/tools/ch3_ft_c00_dual_selection.py`（82 行新增，
0 行删除），四处：

### 1. 新增纯字符串常量（`ENTITY_TAIL_AGGREGATION_ALLOWED_KEYS` 定义之后）

```python
ENTITY_BCE_AGGREGATIONS = ("maximum", "tail_mean")
ENTITY_BCE_ALLOWED_KEYS = ("enabled", "weight", "aggregation")
```

不设独立 `alpha` 键：挂载时直接复用既有的 `ENTITY_TAIL_AGGREGATION_FROZEN_ALPHA`
（`0.5`，2026-09-01 尾部聚合参数裁决报告冻结），不新增第二个可能与之不一致的冻结值。

### 2. `validate_config` 新增 `entity_bce` 校验块（`entity_aggregation` 块之后、
`entity_gated_ple` 块之前）

就地缺省读取（`mechanism.get("entity_bce", {})`），**不进 `DEFAULT_MECHANISM`**——
理由与 `entity_aggregation`/`entity_gated_ple` 完全相同：给 `DEFAULT_MECHANISM`
加键会改变缺 `mechanism` 键的既有 C00 配置的科学身份，拒掉在途检查点。校验规则严格
按实施计划任务 2 步骤 1 字面执行：`enabled` 必须是布尔；`enabled` 为真时 `weight`
必须是正 `float`、`aggregation` 必须在 `("maximum", "tail_mean")` 中、且不接受
计划未登记的键。

### 3. `training_step`（原 1445 行起，现因前两处新增偏移到 1475 行起）挂载实体级 BCE

- 新增关键字参数 `entity_ids: Any = None`（默认 `None`，与 `mechanism_context`
  同风格）。
- 循环外一次性读取：`mechanism = config.get("mechanism", DEFAULT_MECHANISM)`
  → `entity_bce_cfg = mechanism.get("entity_bce", {})` →
  `entity_bce_enabled = bool(entity_bce_cfg.get("enabled", False))`。这三行是
  纯字典读取，无副作用，无论开关是否打开都会执行，但**不消耗任何 RNG、不构造任何
  张量**，因此不影响"关闭路径逐位相同"这条要求（已用真实数据实测，见下）。
- 仅当 `entity_bce_enabled` 为真时，在**每个微批**的 `with precision.fp32_island(...)`
  区块内、`loss_sum`（既有逐流 BCE 求和）算出之后，追加：
  1. 用 `arrays["E23"]`（经新参数 `entity_ids` 传入）取该微批对应片段的实体 ID，
     广播到 `(micro, length)` 后摊平成一维；
  2. 用 `np.unique(..., return_inverse=True)` 把全局实体 ID 重编为**本微批局部**
     的紧凑下标——这是 `entity_bce_loss` 文档字符串要求的契约（`entity_labels`
     长度即"批内实体总数"），不是我发明的编码方式，是任务 1 模块接口本身的要求；
  3. 实体标签取该实体在本微批内全部**有效**流标签的最大值（`np.maximum.at`，
     只在 `flow_valid` 掩码内取值，与 `validation_metrics` 现有的
     `np.maximum.at(entity_labels, entities, labels)` 同一模式）；
  4. 调用任务 1 的 `entity_bce_loss(logits32.reshape(-1), valid_t.reshape(-1),
     local_entity_of_row, local_entity_labels, entity_bce_aggregation,
     ENTITY_TAIL_AGGREGATION_FROZEN_ALPHA, torch_module)`，取其 `loss`，**诊断字典
     整体丢弃、不保留、不落盘**（原因见下方"第 4 条"）；
  5. `loss_sum = loss_sum + entity_bce_weight * entity_bce_value`，随后按既有代码
     不变地调用 `accumulator.backward(loss_sum, ...)`——不新增第二次 `backward()`，
     不改变梯度累积的微批边界。

粒度选择说明：实体级 BCE 按**微批**（不是整个有效批）计算，逐字对应实施计划任务 2
步骤 2 的原文——"在既有逐流损失求和之后、`accumulator.backward` 之前"，这个位置在
微批循环内部。一个实体若跨微批出现，会在多个微批里分别被部分计入（用该微批内可见的
子集重新聚合），这是"阶段 A 筛选"范围内的工程简化，不是文献要求的精确形式；由于
`weight` 要在任务 3 用真实梯度范数比值实测标定（而不是理论推导一个"正确"值），
这个粒度选择被 weight 的经验标定吸收，不改变"能否验证 6.3 疑虑"这一阶段 A 目的。
若后续（阶段 B）证明这个粒度选择本身有问题，需要用户或后续任务重新裁决，本报告
如实记录这一设计决定，不隐藏。

### 4. 两处调用点新增 `entity_ids=arrays["E23"]`

- `probe_runtime` 内（原 2858 行附近，现约 2958 行）
- `run_training` 内的训练循环（原 3189 行附近，现约 3270 行）

两处调用点所在函数都已有局部变量 `arrays`（来自 `prepare_data` 的返回值），
不需要新增数据读取。

## 上一任务遗留的四条，逐条处理

1. **接口命名**：确认模块实际签名参数名为 `entity_labels`（不是 `labels`），
   挂载代码按位置传参，不依赖关键字名，规避了该差异。
2. **`alpha` 的 `maximum` 语义**：挂载代码统一传 `ENTITY_TAIL_AGGREGATION_FROZEN_ALPHA`
   （`0.5`）作为 `alpha` 形参（防御性校验用途），`aggregation="maximum"` 时该值
   不参与聚合运算（`entity_bce_loss` 内部对 `maximum` 模式调用
   `tail_aggregate(..., alpha=None)`，与 `alpha` 形参本身的取值无关）——这是
   任务 1 模块既有设计，本任务原样复用，未新增歧义。
3. **共享 worktree 的并发提交**：任务执行期间用 `git status --short -- <目标文件>`
   核对过多次，全程只有一个文件 `tools/ch3_ft_c00_dual_selection.py` 处于修改
   状态；HEAD 在任务执行期间从 `f5d4993` 前移到 `422d754`（其他会话的无关提交），
   但用 `git log --oneline b866542..422d754 -- tools/ch3_ft_c00_dual_selection.py`
   确认这些提交**未触碰**本任务的目标文件，逐位等价检查用的 `git show HEAD:<path>`
   基线未受影响。
4. **diagnostics 未 JSON 化（本任务最重的一条）**：挂载代码**完全不保留**
   `entity_bce_loss` 返回的 diagnostics 字典（`entity_scores`/`k_per_entity`/
   `m_per_entity`/`scored_mask` 等实体级张量）——调用处写的是
   `entity_bce_value, _entity_bce_diagnostics = entity_bce_module.entity_bce_loss(...)`，
   下划线前缀变量从未被读取、从未进入 `training_step` 的返回字典。`training_step`
   的返回值形状与改动前完全一致（仍是 `loss`/`gradient_norm`/`valid_flows`/
   `sampled_sequences` 四个标量字段），而这个返回字典正是会被
   `probe_runtime` 里 `atomic_json(output_root / "budget-receipt.json", receipt)`
   通过 `"one_optimizer_step": {**step, **...}` 原样吸收进 JSON 收据的对象——
   即 2026-09-02 张量写入 JSON 导致训练崩溃、GPU 空转 15 小时那次事故的确切
   位置类型。本任务通过"根本不保留"而不是"事后转换"规避该类事故，比转换更彻底。

## 关闭开关的逐位等价检查（本任务核心验收）

### 方法

用真实本机数据（`runs/diagnostics/dijk-repro/cache/` 下的 LSPR23 训练区真实
片段，与任务 1 自检同一数据源）、真实配置
`configs/ch3-ft-c00-dual-selection-mps-screening-v1.json`（本机可跑的本地路径版
C00 配置；该配置本身不含 `mechanism` 键，`entity_bce` 因此天然缺省关闭），CPU
设备（`cpu-fp32-v1` 精度档，`autocast=False`）、`torch.set_float32_matmul_precision("highest")`。

- 用 `git show HEAD:thesis/experiments/llm_probe/tools/ch3_ft_c00_dual_selection.py`
  取改动前版本（HEAD 未被本任务提交污染，见上一节第 3 条的核对），写入临时文件后
  用 `importlib.util.spec_from_file_location` 加载为独立模块 `old_mod`（模块名
  `ch3_ft_c00_dual_selection_OLD`，加载后立即删除临时文件，不进仓库）。
- 用同一份真实数据、同一模型初始权重（`torch.manual_seed(42)` 后
  `build_model_optimizer` 一次，深拷贝 `state_dict()`/`optimizer.state_dict()`
  作为可复原的初始状态）分别跑 `new_mod.training_step(...)`（新签名，显式传
  `entity_ids=arrays["E23"]`，模拟真实调用点）与 `old_mod.training_step(...)`
  （旧签名，无 `entity_ids`），每次调用前都：还原模型与优化器到初始状态、
  重建同种子的显式采样 `torch.Generator`、**并重置全局 `torch.manual_seed`**。
- **踩坑记录（如实记录一次误判）**：第一次运行时两次调用的 `loss`/`gradient_norm`
  与全部 53 个参数的 `.grad` 均不相等（`max_abs_diff≈0.109`），一度像是"关闭路径
  被污染"。根因排查（`systematic-debugging`，单变量法）：FT-Transformer 骨干含
  非零 `attention_dropout=0.2`、`ffn_dropout=0.1`，`model.train()` 下 dropout
  掩码取自**全局默认 RNG**，而不是显式传入 `sample_distinct_positions` 的那个
  `torch.Generator`；脚本只重置了显式 `generator`，未重置全局 RNG，导致两次调用
  的 dropout 掩码不同。这是**测试方法学的漏洞，不是挂载代码的漏洞**——两次调用
  之间除 dropout 掩码外没有任何其他状态差异来源可以解释这类"全部参数普遍小幅
  偏移"的模式（若是代码路径泄漏，预期是结构性差异或崩溃，不会是这种量级均匀的
  扰动）。加上 `torch.manual_seed(GENERATOR_SEED)` 复位全局 RNG 后重跑，结论反转。

### 结果（第二次，修正测试方法学后）

```
NEW result: {'loss': 1.36223810876254, 'gradient_norm': 5.497368812561035, 'valid_flows': 3475, 'sampled_sequences': 64}
OLD result: {'loss': 1.36223810876254, 'gradient_norm': 5.497368812561035, 'valid_flows': 3475, 'sampled_sequences': 64}
{
  "loss_equal": true,
  "gradient_norm_equal": true,
  "valid_flows_equal": true,
  "sampled_sequences_equal": true,
  "param_name_sets_equal": true,
  "all_grads_equal": true,
  "num_params_compared": 53,
  "num_mismatched_params": 0,
  "max_abs_diff_over_mismatched": 0.0
}
BITEXACT_CHECK_PASSED
```

`loss` 与 `gradient_norm` 用 Python `==` 精确比较（非近似），全部 53 个模型参数的
`.grad` 用 `torch.equal`（逐元素位级比较）比较，全部通过，`max_abs_diff` 为 `0.0`。

真实数据规模：训练区 `208,598` 行、验证区 `22,444` 行（`ch3-ft-c00-dual-selection-mps-screening-v1`
配置对应的完整本地 LSPR23 训练区），本次单步采样 `64` 个序列、命中 `3,475` 个有效流。

验证脚本：`/private/tmp/.../scratchpad/task2_bitexact_verify.py`（跑完即删，
未进仓库；核心逻辑已在本报告完整复述）。

## 四份既有配置身份核对（步骤 4）

改动前后各跑一次 `--validate-config`，`science_identity_sha256` 逐位不变：

| 配置 | 值 |
| --- | --- |
| C00-half | `2e35c17aa278120e42e9fb021b0c077e1604634f0891349d64f2a6874057220d` |
| C01-half | `d1102e2bf4cec02e0ed047126826b0298b5c51da886a77c659f38205a31f2a7c` |
| C10-half | `dfed8add18f7f574717d670645124e8288b65f60c86967b041e79d7c9947c005` |
| C11-half | `383457025029c09483b15972058cb5a4f886d60c782139608c78f4ad1078f231` |

四份值与任务简报给出的预期（含简报只给前 16 位的 C10）逐字一致。命令：

```bash
cd thesis/experiments/llm_probe
for c in ch3-ft-c00-halfwidth-screening-v1 ch3-ft-c01-halfwidth-screening-v1 \
         ch3-ft-c10-halfwidth-screening-v1 ch3-ft-c11-halfwidth-screening-v1; do
  /opt/miniconda3/envs/rwkv/bin/python tools/ch3_ft_c00_dual_selection.py \
    --config configs/$c.json --validate-config
done
```

（四份配置均不含 `mechanism` 键或不含 `mechanism.entity_bce` 键，`science_projection`
函数把整段 `config.get("mechanism", DEFAULT_MECHANISM)` 原样纳入身份投影——由于
本任务未修改这四份 JSON 文件本身、也未修改 `science_projection` 函数，这四份
配置读出的 `mechanism` 字典逐位不变，身份哈希不可能变化；上表是对此推理的真实
运行核验，不是单纯推理。）

## 附加正控：entity_bce 打开时能否在真实数据上跑通

不是本任务的核心验收（核心验收是上面的关闭路径逐位等价），但用同一真实数据、
`mechanism.entity_bce={enabled:true, weight:1.0, aggregation:...}`（仅供跑通
形状与类型，非任务 3 的登记权重值）分别跑 `"maximum"` 与 `"tail_mean"` 两种聚合，
确认：

```
{"aggregation": "maximum",   "result": {"loss": 1.3683714250801131, "gradient_norm": 5.703458786010742, "valid_flows": 3475, "sampled_sequences": 64}, "loss_finite": true, "grad_norm_finite": true, "all_param_grads_finite": true}
{"aggregation": "tail_mean", "result": {"loss": 1.2194828558713198,  "gradient_norm": 4.006649017333984,  "valid_flows": 3475, "sampled_sequences": 64}, "loss_finite": true, "grad_norm_finite": true, "all_param_grads_finite": true}
ENABLED_SMOKE_PASSED
```

两种聚合都成功跑完一个真实优化步：`loss`、`gradient_norm` 均为有限值，全部模型
参数的 `.grad` 均为有限值（无 `NaN`/`Inf`）。两种聚合下的 `valid_flows`/
`sampled_sequences` 与关闭路径完全一致（`3475`/`64`），符合预期——这两个字段
只统计逐流采样与有效流，不受实体级损失是否叠加影响。`loss`/`gradient_norm`
在两种聚合、以及与"关闭"状态相比均不同，符合预期（实体级 BCE 项确实被叠加进了
总损失）。验证脚本：`/private/tmp/.../scratchpad/task2_enabled_smoke.py`
（跑完即删，未进仓库）。

## 编译与静态检查

```
/opt/miniconda3/envs/rwkv/bin/python -c "import py_compile; py_compile.compile('tools/ch3_ft_c00_dual_selection.py', doraise=True)"
# PY_COMPILE_OK
```

未运行 `black` 或任何自动格式化器（禁止项）。未创建任何人工夹具或单元测试；
全部验证使用真实本机 LSPR23 训练区数据。

## 魔法数字门禁核对

本任务**不引入任何新的数值权重**：`entity_bce_weight` 的具体数值不在本任务
写死——挂载代码只是"按配置读出的 `weight` 相乘"，配置本身（含权重登记依据）
是任务 3 的责任。四份既有生产配置都不含 `mechanism.entity_bce` 键，因此权重
魔法数字门禁在本任务层面无适用对象；`alpha` 复用已冻结常量
`ENTITY_TAIL_AGGREGATION_FROZEN_ALPHA`（0.5），未引入第二个冻结值。

## 提交

```bash
git commit -m "feat(ch3): mount entity BCE in training_step behind a flag" -- thesis/experiments/llm_probe/tools/ch3_ft_c00_dual_selection.py
```

提交哈希：`c96bb748834ecc18feb98899b4a21d4d535ee832`（分支
`codex/ch4-dtep-pbc-20260819`），1 个文件、82 行新增、0 行删除，提交信息末尾无
`Co-Authored-By` 署名。提交前用 `git status --short -- <目标文件>` 确认只有该
文件处于修改状态，未用 `git add .`，未夹带 worktree 内其他会话的改动。

## 需要用户或任务 3、4 关注的问题

1. **实体级 BCE 的计算粒度是"微批"而不是"整个有效批"**（见上文"改动的确切位置"
   第 3 条的粒度选择说明）。这个设计决定影响 `weight` 的实际数值含义——任务 3
   实测 `‖∇L_flow‖` 与 `‖∇L_entity‖` 时，两者都是在**这个粒度**下产生的真实梯度，
   标定出的 `weight` 天然吸收了这个粒度选择，不需要额外换算；但若后续要把粒度
   改成"整个有效批"，`weight` 需要重新标定，不能直接复用任务 3 的登记值。
2. **本任务未对 `entity_bce` 与 `entity_memory`/`entity_ranking` 同时启用做互斥
   校验**——不是因为不重要，而是实施计划任务 2 步骤 1 的校验范围只写了
   `enabled`/`weight`/`aggregation` 三项，且四格设计文档（`thesis/methods/
   四格设计的不对称与改法.md`）第三节明确 C01/C11（阶段 B）需要 `entity_bce` 与
   `entity_ranking` 同时打开，此时不应报错；而 `entity_bce` 与 `entity_memory`
   同时打开目前会被静默忽略（`entity_memory_enabled=true` 时训练分派到
   `entity_memory_training_step`，从不读取 `mechanism.entity_bce`），产生"配置
   看似生效、实际未生效"的风险。当前四份生产配置都不受影响（`entity_memory`
   均为假），但若未来有人手写一份同时打开两者的配置，不会得到报错提示。建议任务 3
   或后续任一挂载 CEM 路径的任务补一条校验，或在文档中显式记录这一限制。
