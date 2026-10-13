#!/usr/bin/env python
"""层覆盖审计：训练核可达层 vs 评价算子实际预算层。

用途
----
为第三章正文 §3.4.3／§3.5.1 与论断 A39 提供**可复现**的层覆盖量化，
替代此前无制品支撑的「严格重叠 2.2%／扩到八位 63.7%」两个数字。

口径（严格定义，正文必须照此陈述）
--------------------------------
记成员 ``x`` 的**评价预算层**为 ``q_actual(x)`` —— 由共享前缀编辑算子的
``random_half`` 档在 ``x`` 上实际施加的替换次数（``edit_v2.generate`` 的
``q_actual`` 字段，恒等于输出与输入的汉明距离）。

记**训练核可达层上限** ``Q_train`` —— 本章训练核族（``perturb2`` 单次／
累积复合）在成员上实际达到的最大汉明层。该值由 ``measurements.json``
的 ``train_kernel`` 直方图给出（支持集 {0,1,2,3,4}，故 ``Q_train = 4``）；
本脚本不重测该量，只按给定 ``Q_train`` 计算覆盖。

本脚本报告三个覆盖量：

- ``coverage_train``  = P(q_actual ≤ Q_train)  训练层上限以内的评价成员占比
- ``coverage_eval8``  = P(q_actual ≤ 8)        评价预算落在八位以内的成员占比
- ``exact_hits``      = 各具体层的成员占比（用于说明「严格同层」有多稀）

**不主张**：覆盖率高低不等于方法优劣；本量只用于界定「训练层覆盖到哪、
评价层落在哪」这条边界，不得据此声称课程调度有效。

零训练、CPU 只读；只读源期 30,000 个 DGA 成员与既有算子实现。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

WORKTREE = Path("/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908")
TOOLS = WORKTREE / "thesis/experiments/llm_probe/tools"
SPEC_DIR = WORKTREE / ".Codex/docs/2026-09-23-DRIFT源期训练抽样合同"
TRAINER_DIR = WORKTREE / ".Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案"
OUT = Path(__file__).resolve().parent / "layer-coverage-audit.json"

# 与 P0 制品逐字一致的流身份（见 p0-legal-attack-result.json 的 stream_id 字段）
STREAM_ID = (
    "p0-legal-attack|shared_prefix_edit_v2|"
    "ch3-drift-source-p0-legal-attack-bdf-mps-20261013-v1"
)
SPEC_DISPLAY = ".Codex/docs/2026-09-23-DRIFT源期训练抽样合同/candidate-spec-diagnostic-v1.json"
# load_fixed_source_members 只接受仓库相对路径
SPEC = SPEC_DISPLAY

# 训练核可达层上限，取自 measurements.json 的 train_kernel 直方图支持集 {0,1,2,3,4}
Q_TRAIN = 4
# 课程预算扩到八位后的假想上限（仅用于报告「若训练覆盖到 8 会怎样」）
Q_EVAL8 = 8


def main() -> int:
    sys.path.insert(0, str(TOOLS))
    sys.path.insert(0, str(SPEC_DIR))
    sys.path.insert(0, str(TRAINER_DIR))
    import ch3_drift_formal_edit_v2 as edit_v2  # noqa: E402
    import official_p2p3 as official  # noqa: E402

    all_domains, all_labels, receipts = official.load_fixed_source_members(SPEC, "source_train")

    # 正文与论断 A39 的口径是「源训练 DGA 成员」——须剔除良性角色。
    # 良性角色含点号，其「可编辑位」定义与 DGA 不同，混入会压低 q_actual（实测均值由
    # 7.69 降到 6.90，并引入 q_actual=0 的成员）。按收据的 class 字段严格筛选。
    if sum(int(r["selected_count"]) for r in receipts) != len(all_domains):
        raise AssertionError("收据 selected_count 之和与成员总数不符，切片不可靠")
    domains: list[str] = []
    offset = 0
    for role in receipts:
        count = int(role["selected_count"])
        block = all_domains[offset : offset + count]
        offset += count
        if role.get("class") == "dga":
            domains.extend(block)
    if not domains:
        raise AssertionError("未筛选出任何 DGA 成员，class 判据可能已失效")
    n = len(domains)

    hist: dict[int, int] = {}
    errors = 0
    for x in domains:
        try:
            result = edit_v2.generate(x, "random_half", STREAM_ID)
        except Exception as exc:  # 算子自身应保证无异常；此处只作守恒计数
            errors += 1
            print(f"[warn] generate 抛错：{type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        q = int(result["q_actual"])
        # 守恒校验：hamming 必须等于 q_actual（算子合同）
        if int(result["hamming"]) != q:
            raise AssertionError(f"hamming != q_actual：{x!r} hamming={result['hamming']} q={q}")
        hist[q] = hist.get(q, 0) + 1

    counted = sum(hist.values())
    if counted + errors != n:
        raise AssertionError(f"计数不守恒：counted={counted} errors={errors} n={n}")

    coverage_train = sum(c for q, c in hist.items() if q <= Q_TRAIN) / counted
    coverage_eval8 = sum(c for q, c in hist.items() if q <= Q_EVAL8) / counted
    mean_q = sum(q * c for q, c in hist.items()) / counted

    payload = {
        "schema": "layer-coverage-audit-v1",
        "purpose": "训练核可达层与评价预算层的覆盖量化（正文 §3.4.3/§3.5.1、论断 A39）",
        "zero_training": True,
        "member_count": counted,
        "errors": errors,
        "member_receipt_sha256": None,
        "receipts_roles": [r.get("role") for r in receipts],
        "operator": {
            "module": "thesis/experiments/llm_probe/tools/ch3_drift_formal_edit_v2.py",
            "tier": "random_half",
            "tier_rule": "b_nominal = max(1, n_e // 2)（共享前缀编辑，n_e 为可编辑位数）",
            "stream_id": STREAM_ID,
            "q_actual_definition": "输出与输入的汉明距离（脚本内以 result['hamming'] 逐条断言相等）",
        },
        "member_source": {
            "candidate_spec": SPEC_DISPLAY,
            "entry": "official_p2p3.load_fixed_source_members(..., purpose='source_train')",
            "purpose": "source_train",
        },
        "train_kernel": {
            "q_train_cap": Q_TRAIN,
            "support": [0, 1, 2, 3, 4],
            "source": ".Codex/docs/2026-10-13-机制推导/measurements.json 的 train_kernel 直方图",
            "note": "支持集含 1 层，来自第二阶段把 base 已改位改回原字符的字符回弹",
        },
        "eval_layer_histogram": {str(q): hist[q] for q in sorted(hist)},
        "metrics": {
            "q_actual_mean": mean_q,
            "q_actual_min": min(hist),
            "q_actual_max": max(hist),
            "coverage_train": coverage_train,
            "coverage_eval8": coverage_eval8,
            "exact_hit_rate": {str(q): hist.get(q, 0) / counted for q in (2, 3, 4, 8)},
        },
        "boundary": [
            "覆盖率只界定训练层与评价层的重叠范围，不构成方法优劣证据。",
            "q_actual 由算子在该成员上的确定流给出，与模型的预测分数无关。",
            "本轮训练预算冻结为 q_t ∈ {1,2,4}；coverage_eval8 只作参照，不对应本轮任何训练臂。",
        ],
    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(payload["metrics"], ensure_ascii=False, indent=1))
    print(f"[ok] 制品已写入 {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
