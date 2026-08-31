#!/usr/bin/env python3
"""M-E 门作用域诊断：量化 𝟙[c≥1] 让多少样本、多少实体真正受机制影响。

存在理由（2026-08-31）：M-E 的门 `γ_θ(s)·𝟙[c≥1]` 使实体首片段恒不生效，
而第三章主指标是实体 AP。片段份额、流份额与实体份额三者差异极大——门激活片段占
`44.57%`、覆盖 `93.47%` 的流，但只有 `2.22%` 的实体有任何激活片段。用前两者描述
作用域会严重高估机制对实体级指标的影响面。

本脚本给出三层结果：全源区作用域、按源年切分分层的作用域、门输入的实体级判别力上界。
第三项是关键的证伪量：门只依赖 `s = [log(1+c), log(1+Δ)]`，故直接用 `c` 或 `Δ` 当分数
所得的实体 AP，就是门这条路径能提供的实体级信息上界；若它接近 C00，则 M-E 的任何增益
都无法与该先验区分。

`--assert-frozen` 把预注册断言变成程序动作：核验本次实测与已冻结数字逐项一致，
供正式运行在创建运行身份前调用，防止实现引入意外的门激活路径。

只读 LSPR23，`target_reads = 0`。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
from sklearn.metrics import average_precision_score

# 协议 A 源年切分参数，与 base.source_split 一致
SPLIT_SEED = 42
VALIDATION_FRACTION = 0.1
TIME_TAIL_FRACTION = 0.15

# 已冻结的预注册数字，来源见 .Codex/docs/RWKV/2026-08-31-M-E门作用域源年量化.md
FROZEN: Dict[str, Any] = {
    "train_sequences": 208_598,
    "validation_sequences": 22_444,
    "malicious_entity_count": 239,
    "validation_malicious_entities": 20,
    "validation_malicious_gate_reachable": 13,
    "validation_benign_gate_reachable": 350,
    "overall_gate_active_segments": 121_135,
    "overall_malicious_gate_reachable": 117,
}

LABEL_CHUNK = 20_000


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def strict_past_segment_state(
    entity: np.ndarray, stamp: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """按 (实体, 时间) 升序向量化推进，为每个片段生成其到达前的实体状态。

    返回 `(prior_segments, gap)`，与片段一一对应：
    - `prior_segments`：形式化的 `c_{e,t} = t − 1`，该实体在此片段前已出现的片段数
    - `gap`：形式化的 `Δ_{e,t}`，距同实体上一片段的时间间隔，首片段取 `0`

    两者都只依赖该实体在当前片段之前的片段，满足形式化第 4.1 节的严格过去性。
    """
    order = np.lexsort((stamp, entity))
    entity_sorted = entity[order]
    stamp_sorted = stamp[order]
    n = entity_sorted.size

    is_group_start = np.empty(n, dtype=bool)
    is_group_start[0] = True
    np.not_equal(entity_sorted[1:], entity_sorted[:-1], out=is_group_start[1:])

    group_id = np.cumsum(is_group_start) - 1
    group_start_index = np.flatnonzero(is_group_start)
    position_in_group = np.arange(n, dtype=np.int64) - group_start_index[group_id]

    gap_sorted = np.zeros(n, dtype=np.float64)
    gap_sorted[1:] = stamp_sorted[1:] - stamp_sorted[:-1]
    gap_sorted[is_group_start] = 0.0

    prior_segments = np.empty(n, dtype=np.int64)
    prior_segments[order] = position_in_group
    gap = np.empty(n, dtype=np.float64)
    gap[order] = gap_sorted
    return prior_segments, gap


def segment_malicious_mask(
    flow_index: np.ndarray, mask: np.ndarray, labels: np.ndarray
) -> np.ndarray:
    """片段级恶意标记：片段的任一有效流为恶意即为恶意。分块以免一次展开千万级索引。"""
    n_seq = flow_index.shape[0]
    result = np.zeros(n_seq, dtype=bool)
    for start in range(0, n_seq, LABEL_CHUNK):
        end = min(start + LABEL_CHUNK, n_seq)
        idx = np.asarray(flow_index[start:end])
        valid = np.asarray(mask[start:end]) > 0.5
        result[start:end] = (labels[idx] * valid).max(axis=1) > 0.5
    return result


def source_split(entity: np.ndarray, stamp: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """逐字复现 base.source_split：按实体随机留出验证集并切除时间尾部。"""
    unique_entity = np.unique(entity)
    permutation = np.random.RandomState(SPLIT_SEED).permutation(len(unique_entity))
    count = max(1, int(len(unique_entity) * VALIDATION_FRACTION))
    validation_entities = set(unique_entity[permutation[:count]].tolist())
    entity_mask = np.fromiter((value in validation_entities for value in entity), bool, len(entity))
    time_mask = stamp >= np.quantile(stamp, 1.0 - TIME_TAIL_FRACTION)
    train_rows = np.flatnonzero(~(entity_mask | time_mask))
    validation_rows = np.flatnonzero(entity_mask & ~time_mask)
    return train_rows, validation_rows


def summarize_scope(
    rows: np.ndarray,
    entity: np.ndarray,
    segment_malicious: np.ndarray,
    gate_active: np.ndarray,
    n_entity: int,
) -> Dict[str, Any]:
    """给定片段行集合，统计门在片段侧与实体侧的作用域。"""
    ent = entity[rows]
    active = gate_active[rows]

    entity_malicious = np.zeros(n_entity, dtype=bool)
    np.logical_or.at(entity_malicious, ent, segment_malicious[rows])
    entity_active = np.zeros(n_entity, dtype=bool)
    np.logical_or.at(entity_active, ent, active)
    present = np.zeros(n_entity, dtype=bool)
    present[ent] = True

    malicious = entity_malicious & present
    benign = (~entity_malicious) & present
    return {
        "sequences": int(len(rows)),
        "entities": int(present.sum()),
        "malicious_entities": int(malicious.sum()),
        "benign_entities": int(benign.sum()),
        "gate_active_sequences": int(active.sum()),
        "gate_active_sequence_share": float(active.mean()),
        "malicious_entities_gate_reachable": int((entity_active & malicious).sum()),
        "malicious_share_gate_reachable": float(entity_active[malicious].mean())
        if malicious.sum()
        else 0.0,
        "benign_entities_gate_reachable": int((entity_active & benign).sum()),
        "benign_share_gate_reachable": float(entity_active[benign].mean()) if benign.sum() else 0.0,
    }


def gate_input_upper_bounds(
    rows: np.ndarray,
    entity: np.ndarray,
    segment_malicious: np.ndarray,
    prior_segments: np.ndarray,
    gap: np.ndarray,
) -> Dict[str, Any]:
    """门输入单独当分数的实体 AP，即门这条路径的实体级信息上界。

    实体聚合口径与 C00 一致：`maximum_over_validation_flows`。
    `log(1+c)` 与 `c` 的 AP 必然相同（AP 对单调变换不变），据此自校验。
    """
    ent = entity[rows]
    unique_entity, inverse = np.unique(ent, return_inverse=True)
    truth = np.zeros(len(unique_entity), dtype=np.int64)
    np.maximum.at(truth, inverse, segment_malicious[rows].astype(np.int64))

    candidates = {
        "prior_segment_count_c": prior_segments[rows].astype(np.float64),
        "log1p_c": np.log1p(prior_segments[rows].astype(np.float64)),
        "gate_indicator_c_ge_1": (prior_segments[rows] >= 1).astype(np.float64),
        "gap_since_last_segment": gap[rows],
    }
    results: Dict[str, Any] = {}
    for name, per_segment in candidates.items():
        score = np.full(len(unique_entity), -np.inf)
        np.maximum.at(score, inverse, per_segment)
        results[name] = float(average_precision_score(truth, score))
    results["random_baseline"] = float(truth.mean())
    results["_monotone_self_check_passed"] = bool(
        results["prior_segment_count_c"] == results["log1p_c"]
    )
    return results


def build_report(cache_root: Path) -> Dict[str, Any]:
    entity = np.load(cache_root / "E23.npy")
    stamp = np.load(cache_root / "T23.npy")
    flow_index = np.load(cache_root / "I23.npy", mmap_mode="r")
    mask = np.load(cache_root / "M23.npy", mmap_mode="r")
    labels = np.load(cache_root / "y23.npy")

    log(f"载入源年缓存：{entity.shape[0]} 个片段")
    segment_malicious = segment_malicious_mask(flow_index, mask, labels)
    prior_segments, gap = strict_past_segment_state(entity, stamp)
    gate_active = prior_segments >= 1
    n_entity = int(entity.max()) + 1

    train_rows, validation_rows = source_split(entity, stamp)
    all_rows = np.arange(entity.shape[0])
    flows_per_segment = np.asarray(mask).sum(axis=1)

    log("切分与作用域统计完成，开始计算门输入判别力上界")
    report = {
        "schema_version": "ch3-ft-me-gate-scope-v1",
        "evidence_tier": "source_year_data_characterization",
        "target_reads": 0,
        "cache_root": str(cache_root),
        "overall": {
            **summarize_scope(all_rows, entity, segment_malicious, gate_active, n_entity),
            "gate_active_flow_share": float(
                flows_per_segment[gate_active].sum() / flows_per_segment.sum()
            ),
        },
        "train": summarize_scope(train_rows, entity, segment_malicious, gate_active, n_entity),
        "validation": summarize_scope(
            validation_rows, entity, segment_malicious, gate_active, n_entity
        ),
        "validation_gate_input_upper_bounds": gate_input_upper_bounds(
            validation_rows, entity, segment_malicious, prior_segments, gap
        ),
    }
    return report


def assert_frozen(report: Dict[str, Any]) -> list[str]:
    """核验实测与冻结数字逐项一致，返回不一致项的说明。"""
    observed = {
        "train_sequences": report["train"]["sequences"],
        "validation_sequences": report["validation"]["sequences"],
        "malicious_entity_count": report["overall"]["malicious_entities"],
        "validation_malicious_entities": report["validation"]["malicious_entities"],
        "validation_malicious_gate_reachable": report["validation"][
            "malicious_entities_gate_reachable"
        ],
        "validation_benign_gate_reachable": report["validation"]["benign_entities_gate_reachable"],
        "overall_gate_active_segments": report["overall"]["gate_active_sequences"],
        "overall_malicious_gate_reachable": report["overall"]["malicious_entities_gate_reachable"],
    }
    failures = [
        f"{key}：冻结 {FROZEN[key]}，实测 {value}"
        for key, value in observed.items()
        if value != FROZEN[key]
    ]
    if not report["validation_gate_input_upper_bounds"]["_monotone_self_check_passed"]:
        failures.append("单调变换自校验失败：log1p_c 与 c 的实体 AP 应逐位相同")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="M-E 门作用域诊断（只读 LSPR23）")
    parser.add_argument("--cache-root", type=Path, required=True, help="含 E23/T23/I23/M23/y23 的目录")
    parser.add_argument("--output", type=Path, default=None, help="报告落盘路径；省略则只打印")
    parser.add_argument(
        "--assert-frozen",
        action="store_true",
        help="核验实测与预注册冻结数字一致，不一致时以退出码 3 失败",
    )
    args = parser.parse_args()

    if not args.cache_root.is_dir():
        log(f"缓存目录不存在：{args.cache_root}")
        return 2

    report = build_report(args.cache_root)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"报告已写入 {args.output}")

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.assert_frozen:
        failures = assert_frozen(report)
        if failures:
            log("冻结数字核验未通过：")
            for item in failures:
                log(f"  - {item}")
            return 3
        log("冻结数字核验通过，共 8 项加 1 项自校验")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
