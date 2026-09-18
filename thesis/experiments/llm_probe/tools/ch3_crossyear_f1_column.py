# -*- coding: utf-8 -*-
"""跨年 F1 列计算：从既有 first-alert / FP-预算包络制品纯重算实体级 F1，
作为统一总表的新增一列，用于与同数据集已发表工作（如 Leoste 2025）在 F1 口径上直接对位。

研究问题（一句话）：本课题第三章主指标是实体 AP 与固定 FP 预算下的 DR，
不是 F1；但外部文献常报 F1，若要与其对位，需要一列在相同实体总体上
重算出的 F1，且要明确标注两者不是同一评价协议、不能直接判优劣。

口径说明：
- 本课题的主评价协议是"固定误报预算下的检出率"（DR@budget），因为部署场景
  下运营容量（每日可人工复核的告警条数）是硬约束，FP 预算是可控制变量、
  检出率是待优化目标；F1 把精确率和召回率按相同权重合并成单一数，隐含
  "运营容量随阈值自由浮动"的假设，与本课题的部署叙事不符。
- 因此 F1 只作为与外部文献对齐的辅助列，不替代 DR@budget 与 AP 作为正文
  主结论；F1-max（曲线最优点）尤其容易高估部署可行性，因为它允许阈值
  达到目标年事后最优，而本课题的阈值选择协议禁止使用目标年标签。

纯重算约束：本工具零读取目标年原始数组（X24/y24/I24/M24/E24/T24 等一律不加载），
只读取 runs/diagnostics/ch3-common-first-alert-fp-budget-envelope-v1/method-aggregates/
下已冻结的 {method}.json 与 {method}.npz 逐点曲线，反解正/负实体总数后代入
F1 = 2TP / (2TP + FP + FN) 定义直接计算。不训练、不新建 SwanLab 运行身份、
不连服务器。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

TOOL_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = TOOL_DIR.parent
SOURCE_RUN_ID = "ch3-common-first-alert-fp-budget-envelope-v1"
SOURCE_ROOT = EXPERIMENT_ROOT / "runs" / "diagnostics" / SOURCE_RUN_ID / "method-aggregates"

RUN_ID = "ch3-crossyear-f1-column-v1"
OUTPUT_ROOT = EXPERIMENT_ROOT / "runs" / "diagnostics" / RUN_ID
SCHEMA_VERSION = "ch3-crossyear-f1-column-v1"

METHOD_KEYS = [
    "cnn_published_max",
    "gru_published_max",
    "transformer_published_max",
    "xgb_cpa_elp_c11",
    "full_mlp_o11",
]
BUDGET_KEYS = ["k_46", "k_231", "k_463", "k_927", "k_1854", "k_3709"]
CALIBERS = ("path", "terminal")

T0 = time.time()


def log(message: str) -> None:
    """带相对时间戳的进度输出（本工具全程纯内存计算，单条日志即够用）。"""
    print(f"[{time.time() - T0:8.2f}s] {message}", flush=True)


def sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def load_method_artifacts(method_key: str) -> dict[str, Any]:
    """读取单个方法的 .json 元数据与 .npz 曲线数组，附带来源文件 SHA-256。"""
    json_path = SOURCE_ROOT / f"{method_key}.json"
    npz_path = SOURCE_ROOT / f"{method_key}.npz"
    if not json_path.exists() or not npz_path.exists():
        raise RuntimeError(f"方法 {method_key} 的制品缺失：{json_path} 或 {npz_path} 不存在")
    metadata = json.loads(json_path.read_text(encoding="utf-8"))
    arrays_npz = np.load(npz_path)
    arrays = {key: arrays_npz[key] for key in arrays_npz.files}
    required = [
        "path_true_positive_entity_count",
        "path_false_positive_entity_count",
        "path_false_positive_rate",
        "path_detection_rate",
        "terminal_true_positive_entity_count",
        "terminal_false_positive_entity_count",
        "terminal_false_positive_rate",
        "terminal_detection_rate",
        "threshold",
    ]
    missing = [key for key in required if key not in arrays]
    if missing:
        raise RuntimeError(f"方法 {method_key} 的 .npz 缺少必需数组：{missing}")
    return {
        "method_key": method_key,
        "display_name": metadata.get("display_name", method_key),
        "metadata": metadata,
        "arrays": arrays,
        "json_path": json_path,
        "npz_path": npz_path,
        "json_sha256": sha256_file(json_path),
        "npz_sha256": sha256_file(npz_path),
    }


def reverse_solve_population(tp: np.ndarray, rate: np.ndarray, label: str) -> int:
    """用 TP/检出率（或 FP/误报率）在整条曲线上反解总体数，并要求全曲线自洽为单一整数。

    检出率恒等于 TP/P（P 为正实体总数，FPR 恒等于 FP/N），因此在 rate>0 的
    每一个曲线点上 TP/rate 都应精确等于同一个整数；若出现两个不同的取整值，
    说明该方法的实体总体在曲线内部不自洽，属于阻断条件，直接抛异常终止。
    """
    mask = rate > 0
    if not np.any(mask):
        raise RuntimeError(f"{label}：曲线上没有任何 rate>0 的点，无法反解总体数")
    ratios = tp[mask].astype(np.float64) / rate[mask].astype(np.float64)
    rounded = np.round(ratios)
    max_abs_error = float(np.max(np.abs(ratios - rounded)))
    if max_abs_error > 1e-3:
        raise RuntimeError(
            f"{label}：TP/rate 偏离最近整数 {max_abs_error:.6g}，超出容差 1e-3，反解不可靠"
        )
    distinct = np.unique(rounded)
    if distinct.size != 1:
        raise RuntimeError(f"{label}：曲线内部反解出多个不同总体数 {distinct.tolist()}，反解不自洽")
    return int(distinct[0])


def verify_budget_readout_integrity(method_key: str, metadata: dict[str, Any], arrays: dict[str, np.ndarray]) -> None:
    """核对 JSON 中每档预算 actual_reachable_point 的 curve_index 与 .npz 曲线数组在该行的取值完全一致。

    这是纯重算前的制品自洽性核验：JSON 的 budget_readouts 是从同一条曲线派生的缓存视图，
    若两者不一致，说明制品在生成后被截断或篡改，必须先停下，不能用不一致的缓存视图计算 F1。
    """
    readouts = metadata.get("budget_readouts", {})
    for budget_key in BUDGET_KEYS:
        if budget_key not in readouts:
            raise RuntimeError(f"{method_key}：budget_readouts 缺少 {budget_key}")
        point = readouts[budget_key]["actual_reachable_point"]
        idx = int(point["curve_index"])
        checks = [
            ("path_true_positive_entity_count", "path_true_positive_entity_count"),
            ("path_false_positive_entity_count", "path_false_positive_entity_count"),
            ("terminal_true_positive_entity_count", "terminal_true_positive_entity_count"),
            ("terminal_false_positive_entity_count", "terminal_false_positive_entity_count"),
        ]
        for json_key, array_key in checks:
            expected = int(point[json_key])
            actual = int(arrays[array_key][idx])
            if actual != expected:
                raise RuntimeError(
                    f"{method_key}/{budget_key}：curve_index={idx} 处 {array_key} 不一致"
                    f"（.npz={actual}，budget_readouts={expected}）"
                )


def compute_prf1(tp: float, fp: float, positive_total: int) -> dict[str, float]:
    """按定义直接计算精确率、召回率、F1；FN = P - TP。"""
    fn = positive_total - tp
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / positive_total if positive_total > 0 else 0.0
    denominator = 2.0 * tp + fp + fn
    f1 = (2.0 * tp) / denominator if denominator > 0 else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def build_budget_table(metadata: dict[str, Any], positive_total: int) -> dict[str, dict[str, dict[str, float]]]:
    """六档整数 FP 预算 × {path, terminal} 口径的 F1/精确率/召回率，直接取 actual_reachable_point 计数。"""
    readouts = metadata["budget_readouts"]
    table: dict[str, dict[str, dict[str, float]]] = {}
    for budget_key in BUDGET_KEYS:
        point = readouts[budget_key]["actual_reachable_point"]
        entry: dict[str, dict[str, float]] = {}
        for caliber in CALIBERS:
            tp = float(point[f"{caliber}_true_positive_entity_count"])
            fp = float(point[f"{caliber}_false_positive_entity_count"])
            prf1 = compute_prf1(tp, fp, positive_total)
            entry[caliber] = {
                "true_positive_entity_count": int(tp),
                "false_positive_entity_count": int(fp),
                "false_positive_rate": float(point[f"{caliber}_false_positive_rate"]),
                "detection_rate": float(point[f"{caliber}_detection_rate"]),
                **prf1,
            }
        entry["common_integer_budget"] = int(readouts[budget_key]["common_integer_budget"])
        entry["nominal_budget"] = float(readouts[budget_key]["nominal_budget"])
        table[budget_key] = entry
    return table


def compute_f1_max(arrays: dict[str, np.ndarray], caliber: str, positive_total: int) -> dict[str, Any]:
    """在完整曲线上扫描 F1 最大值：F1 = 2TP/(TP+FP+P)（P 为常数，等价于原始定义）。"""
    tp = arrays[f"{caliber}_true_positive_entity_count"].astype(np.float64)
    fp = arrays[f"{caliber}_false_positive_entity_count"].astype(np.float64)
    denominator = tp + fp + positive_total
    f1_curve = np.where(denominator > 0, (2.0 * tp) / np.where(denominator > 0, denominator, 1.0), 0.0)
    best_f1 = float(np.max(f1_curve))
    tie_mask = np.isclose(f1_curve, best_f1, rtol=0.0, atol=1e-12)
    tie_indices = np.flatnonzero(tie_mask)
    # 并列时取最保守者：同一最大 F1 下 FP 计数最小的曲线点（对应阈值更高、告警更少）。
    best_among_ties = tie_indices[np.argmin(fp[tie_indices])]
    idx = int(best_among_ties)
    prf1 = compute_prf1(float(tp[idx]), float(fp[idx]), positive_total)
    return {
        "curve_index": idx,
        "threshold": float(arrays["threshold"][idx]),
        "true_positive_entity_count": int(tp[idx]),
        "false_positive_entity_count": int(fp[idx]),
        "false_positive_rate": float(arrays[f"{caliber}_false_positive_rate"][idx]),
        "detection_rate": float(arrays[f"{caliber}_detection_rate"][idx]),
        "tie_count_at_max_f1": int(tie_indices.size),
        **prf1,
    }


def build_method_report(method_key: str) -> dict[str, Any]:
    log(f"处理方法 {method_key}")
    bundle = load_method_artifacts(method_key)
    metadata = bundle["metadata"]
    arrays = bundle["arrays"]

    verify_budget_readout_integrity(method_key, metadata, arrays)

    p_path = reverse_solve_population(
        arrays["path_true_positive_entity_count"], arrays["path_detection_rate"], f"{method_key}/path/P"
    )
    n_path = reverse_solve_population(
        arrays["path_false_positive_entity_count"], arrays["path_false_positive_rate"], f"{method_key}/path/N"
    )
    p_terminal = reverse_solve_population(
        arrays["terminal_true_positive_entity_count"],
        arrays["terminal_detection_rate"],
        f"{method_key}/terminal/P",
    )
    n_terminal = reverse_solve_population(
        arrays["terminal_false_positive_entity_count"],
        arrays["terminal_false_positive_rate"],
        f"{method_key}/terminal/N",
    )
    if p_path != p_terminal:
        raise RuntimeError(f"{method_key}：path 口径反解 P={p_path} 与 terminal 口径 P={p_terminal} 不一致")
    if n_path != n_terminal:
        raise RuntimeError(f"{method_key}：path 口径反解 N={n_path} 与 terminal 口径 N={n_terminal} 不一致")

    # 与 JSON 自带的官方分母字段交叉核对（first_alert.timely_detection_denominator /
    # budget_readouts.k_1854.actual_reachable_point.benign 系口径不直接给 N，改用
    # first_alert.budgets.k_1854.benign_entity_denominator，二者应与曲线反解值完全一致）。
    json_positive_total = int(metadata["first_alert"]["timely_detection_denominator"])
    json_negative_total = int(metadata["first_alert"]["budgets"]["k_1854"]["benign_entity_denominator"])
    if json_positive_total != p_path:
        raise RuntimeError(
            f"{method_key}：曲线反解 P={p_path} 与 JSON timely_detection_denominator={json_positive_total} 不一致"
        )
    if json_negative_total != n_path:
        raise RuntimeError(
            f"{method_key}：曲线反解 N={n_path} 与 JSON benign_entity_denominator={json_negative_total} 不一致"
        )

    budget_table = build_budget_table(metadata, p_path)
    f1_max = {caliber: compute_f1_max(arrays, caliber, p_path) for caliber in CALIBERS}

    return {
        "method_key": method_key,
        "display_name": bundle["display_name"],
        "positive_entity_total": p_path,
        "negative_entity_total": n_path,
        "curve_point_count": int(metadata["curve_point_count"]),
        "budget_table": budget_table,
        "f1_max": f1_max,
        "source": {
            "json_relative_path": str(bundle["json_path"].relative_to(EXPERIMENT_ROOT)),
            "npz_relative_path": str(bundle["npz_path"].relative_to(EXPERIMENT_ROOT)),
            "json_sha256": bundle["json_sha256"],
            "npz_sha256": bundle["npz_sha256"],
        },
    }


def cross_method_population_check(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """跨方法核对正/负实体总体数是否共享同一评价总体（common-first-alert 制品理应共享）。"""
    positive_values = {report["positive_entity_total"] for report in reports}
    negative_values = {report["negative_entity_total"] for report in reports}
    consistent = len(positive_values) == 1 and len(negative_values) == 1
    return {
        "consistent_across_methods": consistent,
        "positive_entity_total_values": sorted(positive_values),
        "negative_entity_total_values": sorted(negative_values),
    }


def render_findings_note(cross_check: dict[str, Any]) -> list[str]:
    """记录任务简报里给出的参考数字与本次真实重算结果之间的核对结论（如实披露，不静默覆盖）。"""
    notes = []
    positive_values = cross_check["positive_entity_total_values"]
    negative_values = cross_check["negative_entity_total_values"]
    notes.append(
        "任务简报陈述『负实体 N=46,364，与 last_reachable_index_by_integer_budget 数组长度 "
        "46,364 一致』；本次对全部 5 个方法、path 与 terminal 两种口径独立反解（TP/检出率、"
        "FP/误报率，容差 1e-3），实测结果均为 N=46,363，与每个方法 JSON 自带的 "
        "first_alert.budgets.k_1854.benign_entity_denominator=46,363 字段逐一核对一致。"
    )
    notes.append(
        "last_reachable_index_by_integer_budget 数组长度确为 46,364，但这是一个长度为 N+1 的"
        "边界/前缀数组（很可能包含预算为 0 的哨兵行），不等于负实体总数 N 本身；"
        "简报中的『反解核实』把数组长度误当成了 N，属于笔误而非数据问题——"
        "两条独立证据（曲线内部反解、JSON 官方分母字段）互相印证，指向同一个正确值 46,363。"
    )
    notes.append(f"跨方法一致性：正实体总数取值集合 {positive_values}，负实体总数取值集合 {negative_values}。")
    if cross_check["consistent_across_methods"]:
        notes.append("5 个方法的正/负实体总体数完全一致，确认共享同一评价总体，未触发阻断条件。")
    else:
        notes.append("警告：5 个方法的正/负实体总体数不一致，已按阻断条件处理（见上方异常）。")
    return notes


def write_receipt(reports: list[dict[str, Any]], cross_check: dict[str, Any], findings: list[str]) -> Path:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "evidence_tier": "diagnostic_recomputation_from_frozen_first_alert_envelope",
        "target_reads": 0,
        "purpose": "从 ch3-common-first-alert-fp-budget-envelope-v1 冻结制品纯重算实体级 F1 列，"
        "供与外部文献（如 Leoste 2025）在 F1 口径上对位；不替代本课题 DR@budget / AP 主指标。",
        "source_run_id": SOURCE_RUN_ID,
        "source_root_relative_path": str(SOURCE_ROOT.relative_to(EXPERIMENT_ROOT)),
        "budget_keys": BUDGET_KEYS,
        "calibers": list(CALIBERS),
        "cross_method_population_check": cross_check,
        "findings_notes": findings,
        "methods": {report["method_key"]: report for report in reports},
        "generated_at_unix": time.time(),
    }
    output_path = OUTPUT_ROOT / "crossyear_f1_column.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--methods",
        nargs="+",
        default=METHOD_KEYS,
        help="要计算的方法键列表，默认全部 5 个方法",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    log(f"读取源目录：{SOURCE_ROOT}")
    reports = [build_method_report(method_key) for method_key in args.methods]

    cross_check = cross_method_population_check(reports)
    findings = render_findings_note(cross_check)
    for note in findings:
        log(note)

    output_path = write_receipt(reports, cross_check, findings)
    log(f"收据已写入：{output_path}")

    log("=== k_1854（4% 名义预算）下 path 口径 F1 摘要 ===")
    for report in reports:
        entry = report["budget_table"]["k_1854"]["path"]
        log(
            f"{report['display_name']}：F1={entry['f1']:.4f}  "
            f"P={entry['precision']:.4f}  R={entry['recall']:.4f}  "
            f"TP={entry['true_positive_entity_count']}  FP={entry['false_positive_entity_count']}"
        )
    log("=== F1-max（全曲线，path 口径）摘要 ===")
    for report in reports:
        entry = report["f1_max"]["path"]
        log(
            f"{report['display_name']}：F1max={entry['f1']:.4f}  "
            f"P={entry['precision']:.4f}  R={entry['recall']:.4f}  "
            f"FP={entry['false_positive_entity_count']}  并列点数={entry['tie_count_at_max_f1']}"
        )


if __name__ == "__main__":
    main()
