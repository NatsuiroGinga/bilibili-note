# 正式共享编辑 v2（评价侧）实施计划

**状态**：计划已冻结（2026-10-13）；规格依据 `thesis/methods/第三章-正式攻击与目标抽样合同裁决.md` §十二
（预算定义已裁决为可编辑位 `|E|`）。单一实现代理执行，主代理验收。

## 一、目标与边界

**做**：实现评价侧合法共享编辑算子 `shared_prefix_edit_v2`，用于对既有 B／D／F 检查点做
**零训练**同成员攻击复评（P0）。

**不做**：不改任何训练侧生成器（`official_p2p3.py::perturb2/perturb_half` 保持原样）；
不重训、不重标阈值、不改成员、不改三档名称；不访问目标年模型分数。

**为什么现在做**：预算定义此前是唯一阻塞（待用户裁决），现已由数据＋文献＋威胁模型裁决为 `|E|`；
且**源年 DGA 含点率为 0**，两候选方案在源期逐行等价 ⇒ P0 不受该定义变更影响，可立即执行。

## 二、文件边界

| 文件 | 动作 |
| --- | --- |
| `thesis/experiments/llm_probe/tools/ch3_drift_formal_edit_v2.py` | **新建**（唯一新生产文件） |
| `thesis/experiments/llm_probe/tools/ch3_drift_formal_edit.py` | 只读参照，**不改** |
| `.Codex/docs/2026-10-13-正式编辑预算科学筛选/` | 审计收据与日志落点 |

## 三、接口规格（冻结）

```python
SCHEMA_VERSION = "ch3-drift-formal-edit-v2"
NAMESPACE = "shared_prefix_edit_v2"

def validate_basic_syntax(x: str) -> dict:
    """返回 {ok: bool, reason: str|None, labels: list[dict]}。
    ok 条件：仅 ASCII 小写字母/数字/连字符/点；每个标签 1–63 字节；
    标签首尾为字母或数字；无空标签（无前导/尾随/连续点）。"""

def editable_positions(x: str) -> dict:
    """返回 {L, E_positions: list[int], n_e: int, frozen_labels: int}。
    - 点号位置排除（冻结）；
    - 标签以 'xn--' 开头，或标签第 3、4 位同时为连字符 ⇒ 整标签冻结并计数；
    - 其余普通标签的非点号位置中，**存在合法非恒等替换字符**者计入 E_positions；
      合法替换集：标签首/尾位仅 {a-z0-9}；内部位 {a-z0-9-} 且第 3、4 位不新生成 '-'；
      排除与原字符不区分大小写相同的选项。"""

def generate(x: str, tier: str, stream_id: str) -> dict:
    """tier ∈ {'k1','k2','random_half'}。确定性：由 (NAMESPACE, stream_id, x) 派生随机流。
    名义预算 b: k1→1, k2→2, random_half→max(1, |E|//2)；实际 q_t = min(b, |E|)。
    对 E_positions 无放回洗牌，逐位选一个合法替换字符，应用前 q_t 项。
    返回 {ok, output, L, n_e, frozen_labels, b_nominal, q_actual,
          hamming, changed_positions_digest, stream_identity, output_sha256}。
    - |E| == 0 ⇒ ok=False, reason='no_editable_position'（不静默计作攻击）；
    - 共同前缀：同一 (x, stream_id) 下，q_a ≤ q_b 时较小档的改动位置与替换字符
      逐项等于较大档的前 q_a 项（同一洗牌排列的前缀）。"""

def audit_members(domains: Iterable[str], stream_id: str) -> dict:
    """对成员做合法性审计，返回聚合收据（逐实体机械核：
    原串合格 ⇒ 三输出均合格；点号位置不变；长度不变；Hamming == q_actual；
    k1/k2 前缀嵌套于 random_half）。任何非法输出计入失败计数并使审计失败。"""
```

## 四、验收（实现代理必须执行并交出收据）

1. `py_compile` ＋ 导入检查通过。
2. **真实源成员审计**：对 T17／T18／T19 全部 DGA 文件（train/test/val）各取确定性子集
   （上限 200,000／文件，固定哈希抽样）跑 `audit_members`，**非法输出必须为 0**；
   收据写入 `edit-v2-audit-receipt.json`（含每文件计数、失败明细、代码 SHA-256、数据 SHA-256）。
3. **前缀嵌套机械核**：随机抽 1,000 个成员验证 `k1 ⊂ k2 ⊂ random_half` 的位置与字符逐项一致。
4. **确定性核**：同 (x, stream_id) 两次调用 output 完全相同。
5. **埋点**：审计按文件打进度行（`file=sys.stderr, flush=True`）。

## 五、制品路径

- 生产代码：`thesis/experiments/llm_probe/tools/ch3_drift_formal_edit_v2.py`
- 审计收据：`.Codex/docs/2026-10-13-正式编辑预算科学筛选/edit-v2-audit-receipt.json`
- 审计日志：同目录 `edit-v2-audit-console.log`

## 六、阻塞条件

- 基础语法规则与 `|E|` 定义如与 `第三章-正式攻击与目标抽样合同裁决.md` §十二 冲突 ⇒ 停止并回报。
- 真实成员审计出现**非零非法输出** ⇒ 停止，保留失败明细，不进入 P0。
- 不得为通过审计而放宽语法规则或静默丢弃成员。

## 七、下一步（本任务验收后）

P0 复评（另立任务）：用本算子对 B／D／F 三臂已冻结检查点在**同一源 DGA 成员**上生成三档攻击，
按已批准的两档源阈值（0.1% 主／1% 辅）与既定指标评分，逐档给出漏检计数、配对错误交叉数、
实际编辑预算与语法通过率。**支持继续考察 F／D 的门**：预定主攻击档在 0.1% 源预算下相对 B
有严格更低的漏检，且 1% 档完整报告；干净 DGA 已测劣势与逐档取舍不得藏入总分。
