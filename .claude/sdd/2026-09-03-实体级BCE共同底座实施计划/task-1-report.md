# 任务 1 实施报告：实体级 BCE 损失模块

## 关键更正：工作现场从主仓库切换到 worktree

简报给出的工作目录 `/Users/bilibili/personal/note`（分支 `codex/ch3-cpa-elp-20260820`）
**不含**宿主脚本 `tools/ch3_ft_entity_ranking_loss.py`、`tools/ch3_ft_c00_dual_selection.py`。

排查证据：

```
git merge-base --is-ancestor fc0d255 HEAD   # NO（fc0d255 是 ranking_loss 落地的提交）
git branch --all --contains fc0d255         # 只有 codex/ch4-dtep-pbc-20260819
```

两个分支从公共祖先 `c365c0a` 各自演进了数百个提交，是两条独立的第三章实验线。
真实宿主代码在 worktree：

```
/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819   分支 codex/ch4-dtep-pbc-20260819
```

**在发现并切换现场之前，我在主仓库只执行了只读排查**（`rg`/`fd`/`git log`/`git show`/
`git branch`/`git worktree list`/`git merge-base`），未做任何 Edit/Write/git add/git commit。
协调方随后发来更正消息，确认应在该 worktree 内工作，与我的排查结论一致。本报告下述全部
实现、自检与提交均发生在该 worktree 内。

## 复用的既有聚合实现

`tools/ch3_ft_entity_ranking_loss.py` 第 150-244 行的 `tail_aggregate(flow_scores,
flow_valid, flow_entity, num_entities, alpha)`——文档字符串明确标注"实体内尾部聚合的
**唯一算术实现**"。本模块只 `import` 它，未重写、未改造、未复制其内部逻辑：

```python
from ch3_ft_entity_ranking_loss import require, tail_aggregate
```

映射关系（均直接复用 `tail_aggregate` 已有的语义，不新增公式）：
- `aggregation="maximum"` → 调 `tail_aggregate(..., alpha=None)`，`k≡1` 退化为 max；
- `aggregation="tail_mean"` → 调 `tail_aggregate(..., alpha=0.5)`，即 ETA。

`ch3_ft_c00_dual_selection.py`、`ch3_ft_entity_ranking_loss.py` 两个文件在本次任务中
**未被修改**（已用 `git status --short` 核对，工作树无差异）。

## 三项自检：精确命令与实测数字

自检脚本临时写在会话 scratchpad
（`/private/tmp/claude-501/.../scratchpad/entity_bce_self_check.py`），运行后已删除，
未进入任何 Git 仓库。真实数据来自 worktree 内既有物化视图：

```
runs/diagnostics/dijk-repro/cache/{E23,I23,M23,T23,y23}.npy   # 271,815 条真实 LSPR23 训练区片段
```

运行前机械核验目标年文件（X24/y24/I24/M24/E24/T24）在该缓存目录不存在，满足
"全程不得读取 LSPR24"。采样用既有 `EntityStratifiedSampler`（`n_pos=3, n_neg=12`，
`seed=42`），并复用 `ch3_ft_entity_ranking_loss._cap_segments_per_entity` 把每实体
片段数截到 8，得到真实抽样批：28 个真实片段、15 个真实实体、3,584 个真实逐流位置
（valid 掩码、实体归属、实体标签全部来自真实数据；flow_logits 用固定种子随机数——
这条性质对任意 logits 取值都须成立，与是否来自训练模型无关）。

执行命令：

```
/opt/miniconda3/envs/rwkv/bin/python "<scratchpad>/entity_bce_self_check.py"
```

实测输出（逐条对应简报步骤 3 的三项要求）：

```
真实缓存就绪：271,815 片段（LSPR23 训练区）
抽样批：正实体=3 负实体=12 片段（截段后）=28
真实片段展开后逐流规模：3,584，实体数：15
[自检1] scored实体数=15 逐位相等=True 最大绝对差=0.000000e+00
[自检2] 单有效流实体数=6
[自检2] 逐位相等=True 最大绝对差=0.000000e+00
[自检3] 被选中流数=975 非选中流最大绝对梯度=0.000000e+00 选中流中非零梯度数=975
ALL_SELF_CHECKS_PASSED
```

- **自检1**（`aggregation="maximum"` 实体分数逐位等于该实体有效流 logits 的
  `max`）：参照值用独立于 `tail_aggregate` 的手工 `scatter_reduce(reduce="amax")`
  计算，15 个 scored 实体上最大绝对差 `0.000000e+00`，`torch.equal` 为真。
- **自检2**（`tail_mean` 在恰有 1 条有效流的实体上退化为 `maximum`）：本批命中
  6 个单流实体，`torch.equal` 为真，最大绝对差 `0.000000e+00`。
- **自检3**（梯度只落在被选中流上）：对 `tail_mean` 损失 `backward()`；独立于
  `tail_aggregate` 用纯 NumPy 逐实体重算 top-k 选中集合（`np.argsort` 降序、稳定排序、
  `k=ceil(0.5*m_e)`），核对得非选中流（2,609 条）梯度绝对值最大为 `0.0`，选中流
  （975 条）中有 975 条梯度非零（全部非零）。

三项均在 `/opt/miniconda3/envs/rwkv/bin/python`（PyTorch 2.12.0）下于 CPU 上运行，
未涉及 MPS，`scatter_reduce`（用于自检参照计算）在 CPU 上执行，符合仓库对该算子的
设备限制。

## 编译与导入检查

```
/opt/miniconda3/envs/rwkv/bin/python -c "import py_compile; py_compile.compile('ch3_ft_entity_bce.py', doraise=True)"
# PY_COMPILE_OK
/opt/miniconda3/envs/rwkv/bin/python -c "import ch3_ft_entity_bce as m; print(m.entity_bce_loss)"
# IMPORT_OK <function entity_bce_loss at ...>
```

未运行 `black` 或任何自动格式化器（禁止项）。生成的 `.pyc`（本模块自身编译缓存）
已从 `tools/__pycache__/` 中删除；未触碰该目录下属于其他并行工作的既有缓存文件。

## 第三方 API 核验

`torch.nn.functional.binary_cross_entropy_with_logits` 用 `npx ctx7@latest` 核对
`/websites/pytorch_2_12`（与本机安装的 2.12.0 对齐）官方签名：
`(input, target, weight=None, size_average=None, reduce=None, reduction='mean',
pos_weight=None)`，确认 `reduction` 为合法关键字参数、取值含 `'none'`。本模块显式传
`reduction="none"` 后按 `m_per_entity > 0` 掩码取均值，理由已写入模块文档字符串
（默认 `'mean'` 会把空实体的零分数计入分母，稀释掉真实的 scored 实体损失）。

## 魔法数字门禁核对

本模块**未引入任何新的数值魔法数字**：
- `alpha` 的冻结值 `0.5` 不是本模块新增的选择，是既有裁决
  （`.Codex/docs/RWKV/2026-09-01-尾部聚合参数裁决/裁决报告.md`）的复用与防御性校验——
  本函数对任何非 `0.5` 的输入一律 `raise`，不做任何"回调"。
- 简报提到的"三项损失的权重"属任务 2（宿主组合三种损失时的加权）范畴，本任务的
  `entity_bce_loss` 本身不产生加权损失，只返回单一未加权的标量损失，无权重魔法数字
  需要登记。

## 开关默认关闭 / 逐位相同路径

本任务是纯新增独立文件，未触碰任何宿主代码路径，因此"关闭时逐位相同"这条约束
在本任务层面自动成立（没有可改变的既有路径）；该约束的实质验收落在任务 2（宿主接线）。

## 提交

```
git add -- thesis/experiments/llm_probe/tools/ch3_ft_entity_bce.py
git commit -m "feat(ch3): add entity-level BCE loss module" -- thesis/experiments/llm_probe/tools/ch3_ft_entity_bce.py
```

提交哈希：`b764b32f5cacb0669a133c3940015d1d3c4e4384`（分支
`codex/ch4-dtep-pbc-20260819`），1 个文件、155 行新增，提交信息末尾无
`Co-Authored-By` 署名。提交前后用 `git status --short` 核对，未夹带 worktree 内
其他会话遗留的未提交改动（该 worktree 是共享工作区，`git status` 显示约 113 处
无关未提交/未跟踪项，均未触碰）。

## 需要用户或任务 2 关注的问题

1. **接口命名的一处细节**：简报"Interfaces"一行写的是
   `entity_bce_loss(..., labels, ...)`，而简报步骤 2 给出的字面代码桩用的是
   `entity_labels`。本实现采用了更详细的字面代码桩，参数名为
   `entity_labels`（不是 `labels`）。任务 2 按关键字调用时请使用 `entity_labels`，
   或按位置传参可规避此差异。
2. **`alpha` 参数在 `aggregation="maximum"` 时的语义**：无论 `aggregation` 取何值，
   传入的 `alpha` 都必须字面等于 `0.5`（否则 raise）；但当 `aggregation="maximum"`
   时，函数内部实际调用 `tail_aggregate(..., alpha=None)`（而不是 `0.5`），
   即真正参与聚合运算的是 `None`（k≡1），`alpha` 形参此时只起防御性校验作用、
   不参与聚合公式。这是刻意设计（复用 `tail_aggregate` 已有的 `alpha=None` 语义，
   不额外发明"maximum 模式下 alpha 应该是多少"的新规则），但容易被后续读者误解为
   "maximum 模式下 alpha 被忽略"，故在此明确记录。
3. **共享 worktree 的并发提交风险**：任务执行期间，该 worktree 内出现了另一个
   与本任务无关的提交（`51b95b9 docs(methods): bring training-efficiency paper
   originals and notes into worktree`），推测是另一并行会话在同一 worktree 下
   操作。本次未发生冲突（提交的文件互不相交），但该 worktree 目前是多会话共享
   状态，若后续有并发写入同一文件的任务，存在暂存区互相覆盖的风险，建议协调方
   确认是否需要为并行任务分配独立 worktree。
4. **diagnostics 返回值含未 JSON 化的张量**：`entity_scores`/`k_per_entity`/
   `m_per_entity`/`scored_mask` 是 detach 后的原始张量（非逐流数组、非实体成员表，
   是实体级张量），供任务 2 在内存中直接使用（例如反传诊断），但若任务 2 要把
   diagnostics 落盘为 JSON 运行收据，需要自行转换为标量或列表——本模块沿用了
   `ch3_ft_entity_ranking_loss.bag_policy_diagnostics` 里 `active_entity_scores`
   同款"内存诊断用张量、非持久化收据"的既有约定，不是遗漏。
