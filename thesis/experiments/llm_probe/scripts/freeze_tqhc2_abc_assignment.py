#!/usr/bin/env python3
"""按预注册硬覆盖规则重新冻结 TQH-C2 域内单元分配。"""

from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from itertools import product
from pathlib import Path

EXPECTED_PROFILES = frozenset({"A", "B", "C"})
EXPECTED_INTERVALS = (30, 300, 1800, 3600)
EXPECTED_JITTERS = frozenset({0, 30, 70})
INDOMAIN_SUITE_ID = "tqhc2_cell_indomain"


def _candidate_groups(cells: list[dict[str, object]]) -> list[dict[str, object]]:
    by_interval = {
        interval: [cell for cell in cells if int(cell["interval_s"]) == interval]
        for interval in EXPECTED_INTERVALS
    }
    candidates: list[dict[str, object]] = []
    for selected in product(*(by_interval[interval] for interval in EXPECTED_INTERVALS)):
        if {str(cell["profile"]) for cell in selected} != EXPECTED_PROFILES:
            continue
        if {int(cell["jitter_pct"]) for cell in selected} != EXPECTED_JITTERS:
            continue
        group_ids = tuple(sorted(str(cell["capture_group_id"]) for cell in selected))
        candidates.append(
            {
                "group_ids": group_ids,
                "group_id_set": frozenset(group_ids),
                "mapped_count": sum(int(cell["mapped_count"]) for cell in selected),
            }
        )
    if not candidates:
        raise ValueError("不存在满足域内三档抖动硬覆盖的四单元组合")
    return candidates


def _select_pair(
    candidates: list[dict[str, object]], total: int, candidate_id: str
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    targets = {
        "train": Fraction(8, 10),
        "validation": Fraction(1, 10),
        "test": Fraction(1, 10),
    }
    best_key: tuple[Fraction, str] | None = None
    best: tuple[dict[str, object], dict[str, object], dict[str, int]] | None = None
    for validation in candidates:
        for test in candidates:
            if validation["group_id_set"] & test["group_id_set"]:
                continue
            counts = {
                "validation": int(validation["mapped_count"]),
                "test": int(test["mapped_count"]),
            }
            counts["train"] = total - counts["validation"] - counts["test"]
            fractions = {name: Fraction(count, total) for name, count in counts.items()}
            deviation = sum(abs(fractions[name] - targets[name]) for name in targets)
            tie = hashlib.sha256(
                (
                    f"{candidate_id}|{INDOMAIN_SUITE_ID}|"
                    f"{'|'.join(validation['group_ids'])}|{'|'.join(test['group_ids'])}"
                ).encode("ascii")
            ).hexdigest()
            key = (deviation, tie)
            if best_key is None or key < best_key:
                best_key = key
                best = (validation, test, counts)
    if best_key is None or best is None:
        raise ValueError("不存在互斥的域内验证与测试组合")
    validation, test, counts = best
    audit = {
        "candidate_count": len(candidates),
        "deterministic_tie_break": best_key[1],
        "l1_sample_fraction_deviation": float(best_key[0]),
        "sample_counts": counts,
        "sample_fractions": {name: count / total for name, count in counts.items()},
        "selection_method": (
            "域内验证和测试硬覆盖 A/B/C、四档 interval 与三档 jitter；"
            "在可行组合中最小化样本比例偏差"
        ),
        "target_sample_fractions": {name: float(value) for name, value in targets.items()},
        "test_jitter_count": 3,
        "validation_jitter_count": 3,
    }
    return validation, test, audit


def freeze_assignment(input_path: Path, output_path: Path) -> dict[str, object]:
    if output_path.exists():
        raise FileExistsError(f"输出已存在，拒绝覆盖：{output_path}")
    document = json.loads(input_path.read_text(encoding="utf-8"))
    cells = document["cells"]
    if len(cells) != 36:
        raise ValueError("固定清单必须包含 36 个单元")
    candidate_id = str(document["generation"]["candidate_id"])
    candidates = _candidate_groups(cells)
    validation, test, audit = _select_pair(
        candidates, sum(int(cell["mapped_count"]) for cell in cells), candidate_id
    )
    validation_ids = validation["group_id_set"]
    test_ids = test["group_id_set"]
    suite = next(item for item in document["suites"] if item["suite_id"] == INDOMAIN_SUITE_ID)
    for assignment in suite["assignments"]:
        cell_id = str(assignment["capture_group_id"])
        assignment["split_id"] = (
            "validation"
            if cell_id in validation_ids
            else "test" if cell_id in test_ids else "train"
        )
    suite["selection_audit"] = audit
    document["generation"]["method"] = "一次受约束组合搜索后冻结；域内验证与测试采用三档抖动硬覆盖"
    payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    output_path.write_text(payload, encoding="utf-8")
    return {
        "candidate_count": len(candidates),
        "output_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "test_ids": sorted(test_ids),
        "validation_ids": sorted(validation_ids),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = freeze_assignment(args.input.resolve(), args.output.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
