#!/usr/bin/env python3
"""机械验收已发表神经基线运营指标回填制品。"""

from __future__ import annotations

import argparse
import ast
import bisect
import hashlib
import io
import json
import math
import struct
import zipfile
from pathlib import Path
from typing import Any


MODELS = ("transformer", "cnn", "gru")
BUDGETS = (
    "fpr_0.001",
    "fpr_0.005",
    "fpr_0.01",
    "fpr_0.02",
    "fpr_0.04",
    "fpr_0.08",
)
CURVE_FIELDS = (
    "threshold",
    "threshold_tie_group_size",
    "tie_group_positive_entity_count",
    "tie_group_negative_entity_count",
    "true_positive_entity_count",
    "false_positive_entity_count",
    "actual_fpr",
    "detection_rate",
)
EXPECTED_INPUT_IDENTITIES = {
    "transformer": {
        "bytes": 80909552,
        "dtype": "float32",
        "sha256": "4bb845444a03cea0579c28120f2afe2d48559c8644c6a8fc80ddd37b5e63922d",
        "shape": [20227356],
    },
    "cnn": {
        "bytes": 80909552,
        "dtype": "float32",
        "sha256": "3d3674d98799140b9dadaa580c481986bd579acad6455dae79948adcb1a0749d",
        "shape": [20227356],
    },
    "gru": {
        "bytes": 80909552,
        "dtype": "float32",
        "sha256": "8e75dcc7b787a4ed3d5c5f2fc250b3b2b20de083c6a5826ef9108d80f9b80ad2",
        "shape": [20227356],
    },
    "flow_labels": {
        "bytes": 80909552,
        "dtype": "float32",
        "sha256": "455a4932e0483af59ebccc64b462d3c620f671c6969f15312d8358cf7f410b46",
        "shape": [20227356],
    },
    "source_addresses": {
        "bytes": 494808757,
        "dtype": "object",
        "sha256": "bdae8476d927d2f6610335649c01e8db71ee48a375bd48f9c13bb7b968d25243",
        "shape": [20227356],
    },
    "destination_addresses": {
        "bytes": 495445716,
        "dtype": "object",
        "sha256": "a3621eaf4d683aac2f6f70ce2c2ad71d769b26fca6bfd981bb98ec81398f21cb",
        "shape": [20227356],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_npy(payload: bytes) -> tuple[dict[str, Any], tuple[int | float, ...]]:
    handle = io.BytesIO(payload)
    if handle.read(6) != bytes.fromhex("934e554d5059"):
        raise ValueError("NPY 魔数不匹配")
    version = tuple(handle.read(2))
    width = 2 if version == (1, 0) else 4
    length_format = "<H" if width == 2 else "<I"
    header_length = struct.unpack(length_format, handle.read(width))[0]
    header = ast.literal_eval(handle.read(header_length).decode("latin1").strip())
    if header["fortran_order"]:
        raise ValueError("不支持 Fortran 顺序数组")
    shape = header["shape"]
    if len(shape) != 1:
        raise ValueError(f"只接受一维数组，实际为 {shape}")
    count = shape[0]
    format_map = {"<f8": "d", "<i8": "q"}
    if header["descr"] not in format_map:
        raise ValueError(f"不支持的数据类型 {header['descr']}")
    values = struct.unpack(f"<{count}{format_map[header['descr']]}", handle.read())
    return header, values


def load_npz(path: Path) -> dict[str, tuple[dict[str, Any], tuple[int | float, ...]]]:
    result = {}
    with zipfile.ZipFile(path) as archive:
        for member in archive.namelist():
            key = member.removesuffix(".npy")
            result[key] = load_npy(archive.read(member))
    return result


class Validator:
    def __init__(self) -> None:
        self.check_count = 0
        self.failures: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        self.check_count += 1
        if not condition:
            self.failures.append(message)


def close(left: float, right: float, tolerance: float = 1e-15) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=tolerance)


def latest_value(
    x_values: tuple[int | float, ...],
    y_values: tuple[int | float, ...],
    query: int | float,
) -> float:
    index = bisect.bisect_right(x_values, query) - 1
    return 0.0 if index < 0 else float(y_values[index])


def compare_step_curves(
    challenger_x: tuple[int | float, ...],
    challenger_y: tuple[int | float, ...],
    reference_x: tuple[int | float, ...],
    reference_y: tuple[int | float, ...],
) -> dict[str, Any]:
    grid = sorted(set(challenger_x) | set(reference_x))
    differences = [
        latest_value(challenger_x, challenger_y, point)
        - latest_value(reference_x, reference_y, point)
        for point in grid
    ]
    violating = [index for index, difference in enumerate(differences) if difference < 0.0]
    first_violation = None
    last_violation = None
    violation_ranges = []
    if violating:
        index = violating[0]
        first_violation = {
            "axis_value": grid[index],
            "difference": differences[index],
        }
        index = violating[-1]
        last_violation = {
            "axis_value": grid[index],
            "difference": differences[index],
        }
        range_start = violating[0]
        previous = violating[0]
        for index in violating[1:]:
            if index != previous + 1:
                violation_ranges.append(
                    {
                        "start_axis_value": grid[range_start],
                        "end_axis_value": grid[previous],
                        "point_count": previous - range_start + 1,
                    }
                )
                range_start = index
            previous = index
        violation_ranges.append(
            {
                "start_axis_value": grid[range_start],
                "end_axis_value": grid[previous],
                "point_count": previous - range_start + 1,
            }
        )
    minimum_index = min(range(len(differences)), key=differences.__getitem__)
    return {
        "dominates_or_ties_everywhere": not violating,
        "strictly_better_somewhere": any(value > 0.0 for value in differences),
        "comparison_point_count": len(grid),
        "violation_count": len(violating),
        "minimum_difference": min(differences),
        "minimum_difference_axis_value": grid[minimum_index],
        "maximum_difference": max(differences),
        "first_violation": first_violation,
        "last_violation": last_violation,
        "violation_ranges": violation_ranges,
    }


def false_positive_envelope(
    false_positives: tuple[int | float, ...],
    true_positives: tuple[int | float, ...],
    negative_count: int,
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    best_at_count = [-1] * (negative_count + 1)
    for false_positive, true_positive in zip(false_positives, true_positives):
        fp = int(false_positive)
        best_at_count[fp] = max(best_at_count[fp], int(true_positive))
    envelope: list[float] = []
    current = 0
    for value in best_at_count:
        if value >= 0:
            current = max(current, value)
        envelope.append(current / 752.0)
    return tuple(range(negative_count + 1)), tuple(envelope)


def main() -> int:
    args = parse_args()
    root = args.input_root
    validator = Validator()

    aggregate = load_json(root / "aggregate-results.json")
    complete_receipt = load_json(root / "complete-alert-budget-curves-receipt.json")
    timing_receipt = load_json(root / "first-alert-timing-receipt.json")
    input_receipt = load_json(root / "input-receipt.json")
    manifest = load_json(root / "manifest.json")
    resource = load_json(root / "resource-receipt.json")
    status = load_json(root / "status.json")
    complete_arrays = load_npz(root / "complete-alert-budget-curves.npz")
    timing_arrays = load_npz(root / "first-alert-timing-curves.npz")

    validator.require(manifest["complete"] is True, "清单未标记完成")
    validator.require(status["state"] == "finished", "状态不是 finished")
    validator.require(status["stage"] == "complete", "阶段不是 complete")
    validator.require(status["exit_code"] == 0, "退出码不是 0")
    validator.require(aggregate["complete"] is True, "聚合结果未标记完成")
    for field in ("training_runs", "inference_runs", "gpu_array_reads"):
        validator.require(status[field] == 0, f"状态字段 {field} 不是零")
        validator.require(manifest[field] == 0, f"清单字段 {field} 不是零")
    validator.require(not aggregate["score_fusion_performed"], "发生了分数融合")
    validator.require(manifest["forbidden_artifacts_absent"], "禁用制品并非全部缺席")

    file_checks = {}
    for name, expected in manifest["files"].items():
        path = root / name
        actual = {"bytes": path.stat().st_size, "sha256": sha256(path)}
        file_checks[name] = {
            "expected": expected,
            "actual": actual,
            "passed": actual["bytes"] == expected["bytes"]
            and actual["sha256"] == expected["sha256"],
        }
        validator.require(file_checks[name]["passed"], f"清单摘要不一致：{name}")

    validator.require(input_receipt["entity_count"] == 47115, "实体总数不是 47115")
    validator.require(input_receipt["positive_entity_count"] == 752, "正实体数不是 752")
    validator.require(input_receipt["negative_entity_count"] == 46363, "负实体数不是 46363")
    validator.require(input_receipt["flow_count"] == 20227356, "逐流样本数不一致")
    validator.require(
        set(input_receipt["files"]) == set(EXPECTED_INPUT_IDENTITIES),
        "冻结输入模型键或实体/标签键集合不一致",
    )
    for name, expected_identity in EXPECTED_INPUT_IDENTITIES.items():
        actual_identity = {
            key: input_receipt["files"][name][key]
            for key in ("bytes", "dtype", "sha256", "shape")
        }
        validator.require(
            actual_identity == expected_identity,
            f"冻结输入身份不一致：{name}",
        )
    validator.require(
        input_receipt["entity_construction"]
        == "lexically_factorized_unordered_source_destination_pair",
        "实体构造身份不一致",
    )
    validator.require(
        set(input_receipt["model_reproduction"]) == set(MODELS),
        "旧锚记录的模型键集合不一致",
    )
    metric_key_map = {
        "flow_average_precision": "flow_average_precision",
        "max_pool_entity_average_precision": "max_pool_entity_average_precision",
        "dr_at_4_percent_fpr": "dr_at_4_percent_fpr",
    }
    for model in MODELS:
        for aggregate_key, receipt_key in metric_key_map.items():
            validator.require(
                aggregate["models"][model][aggregate_key]
                == input_receipt["model_reproduction"][model]["actual"][receipt_key],
                f"{model} 的全精度重算值与聚合结果不一致：{aggregate_key}",
            )

    expected_curve_keys = {
        f"{model}__{field}" for model in MODELS for field in CURVE_FIELDS
    }
    expected_timing_keys = {
        f"{model}__{budget}__{field}"
        for model in MODELS
        for budget in BUDGETS
        for field in ("exposure_index", "timely_detection_rate")
    }
    validator.require(set(complete_arrays) == expected_curve_keys, "完整曲线 NPZ 键集合不一致")
    validator.require(set(timing_arrays) == expected_timing_keys, "首次告警 NPZ 键集合不一致")

    curve_summary: dict[str, Any] = {}
    for model in MODELS:
        arrays = {
            field: complete_arrays[f"{model}__{field}"][1] for field in CURVE_FIELDS
        }
        lengths = {field: len(values) for field, values in arrays.items()}
        point_count = complete_receipt["models"][model]["point_count"]
        validator.require(set(lengths.values()) == {point_count}, f"{model} 曲线长度不一致")
        validator.require(
            all(math.isfinite(float(value)) for value in arrays["threshold"]),
            f"{model} 阈值存在非有限值",
        )
        validator.require(
            all(
                left >= right
                for left, right in zip(arrays["threshold"], arrays["threshold"][1:])
            ),
            f"{model} 阈值不是单调不增",
        )
        validator.require(
            all(
                size == positive + negative
                for size, positive, negative in zip(
                    arrays["threshold_tie_group_size"],
                    arrays["tie_group_positive_entity_count"],
                    arrays["tie_group_negative_entity_count"],
                )
            ),
            f"{model} 并列组大小与正负分解不一致",
        )
        cumulative_positive = 0
        cumulative_negative = 0
        cumulative_ok = True
        rate_ok = True
        for index in range(point_count):
            cumulative_positive += int(arrays["tie_group_positive_entity_count"][index])
            cumulative_negative += int(arrays["tie_group_negative_entity_count"][index])
            cumulative_ok &= arrays["true_positive_entity_count"][index] == cumulative_positive
            cumulative_ok &= arrays["false_positive_entity_count"][index] == cumulative_negative
            rate_ok &= close(
                float(arrays["actual_fpr"][index]), cumulative_negative / 46363.0
            )
            rate_ok &= close(
                float(arrays["detection_rate"][index]), cumulative_positive / 752.0
            )
        validator.require(cumulative_ok, f"{model} 曲线累计计数不一致")
        validator.require(rate_ok, f"{model} 曲线比率与计数不一致")
        validator.require(cumulative_positive == 752, f"{model} 最终 TP 不完整")
        validator.require(cumulative_negative == 46363, f"{model} 最终 FP 不完整")

        for budget in BUDGETS:
            receipt = complete_receipt["models"][model]["budget_readouts"][budget]
            aggregate_readout = aggregate["models"][model]["alert_budget_readouts"][budget]
            validator.require(receipt == aggregate_readout, f"{model} {budget} 聚合读数与收据不一致")
            point = receipt["best_reachable_point"]
            index = point["curve_index"]
            validator.require(
                arrays["false_positive_entity_count"][index]
                == point["false_positive_entity_count"],
                f"{model} {budget} FP 索引不一致",
            )
            validator.require(
                close(float(arrays["detection_rate"][index]), point["detection_rate"]),
                f"{model} {budget} DR 索引不一致",
            )
            validator.require(
                close(float(arrays["threshold"][index]), point["threshold"]),
                f"{model} {budget} 阈值索引不一致",
            )
            validator.require(
                receipt["actual_reachable_fpr"] <= receipt["nominal_target_fpr"],
                f"{model} {budget} 实际 FPR 超预算",
            )
            validator.require(
                receipt["next_reachable_point"]["actual_reachable_fpr"]
                > receipt["nominal_target_fpr"],
                f"{model} {budget} 下一并列组未越预算",
            )

        curve_summary[model] = {
            "point_count": point_count,
            "tie_group_size_max": max(arrays["threshold_tie_group_size"]),
            "tie_group_size_gt_1_count": sum(
                value > 1 for value in arrays["threshold_tie_group_size"]
            ),
            "zero_false_positive_point_count": sum(
                value == 0 for value in arrays["false_positive_entity_count"]
            ),
        }

    timing_summary: dict[str, Any] = {}
    for model in MODELS:
        timing_summary[model] = {}
        for budget in BUDGETS:
            prefix = f"{model}__{budget}"
            x_values = timing_arrays[f"{prefix}__exposure_index"][1]
            y_values = timing_arrays[f"{prefix}__timely_detection_rate"][1]
            receipt = timing_receipt["models"][model]["budgets"][budget]
            aggregate_readout = aggregate["models"][model]["first_alert"]["budgets"][budget]
            validator.require(receipt == aggregate_readout, f"{model} {budget} 首次告警收据不一致")
            validator.require(len(x_values) == len(y_values), f"{model} {budget} 首次告警轴长度不等")
            validator.require(
                len(x_values) == receipt["timely_curve_point_count"],
                f"{model} {budget} 首次告警点数不一致",
            )
            validator.require(
                all(left < right for left, right in zip(x_values, x_values[1:])),
                f"{model} {budget} 曝光轴不是严格递增",
            )
            validator.require(
                all(left <= right for left, right in zip(y_values, y_values[1:])),
                f"{model} {budget} 按时检出率不是单调不减",
            )
            validator.require(
                all(math.isfinite(float(value)) for value in y_values),
                f"{model} {budget} 按时检出率存在非有限值",
            )
            validator.require(
                close(float(y_values[-1]), receipt["alerted_positive_entity_count"] / 752.0),
                f"{model} {budget} 按时检出曲线终点不一致",
            )
            validator.require(
                close(
                    receipt["positive_unalerted_rate"],
                    receipt["never_alerted_positive_entity_count"] / 752.0,
                ),
                f"{model} {budget} 未告警率与计数不一致",
            )
            timing_summary[model][budget] = {
                "point_count": len(x_values),
                "terminal_timely_detection_rate": y_values[-1],
            }

    dominance: dict[str, Any] = {}
    for challenger in ("transformer", "cnn"):
        challenger_fp = complete_arrays[f"{challenger}__false_positive_entity_count"][1]
        challenger_tp = complete_arrays[f"{challenger}__true_positive_entity_count"][1]
        gru_fp = complete_arrays["gru__false_positive_entity_count"][1]
        gru_tp = complete_arrays["gru__true_positive_entity_count"][1]
        challenger_x, challenger_y = false_positive_envelope(challenger_fp, challenger_tp, 46363)
        gru_x, gru_y = false_positive_envelope(gru_fp, gru_tp, 46363)
        complete_curve = compare_step_curves(challenger_x, challenger_y, gru_x, gru_y)

        timing_comparisons = {}
        timing_all = True
        for budget in BUDGETS:
            challenger_prefix = f"{challenger}__{budget}"
            gru_prefix = f"gru__{budget}"
            result = compare_step_curves(
                timing_arrays[f"{challenger_prefix}__exposure_index"][1],
                timing_arrays[f"{challenger_prefix}__timely_detection_rate"][1],
                timing_arrays[f"{gru_prefix}__exposure_index"][1],
                timing_arrays[f"{gru_prefix}__timely_detection_rate"][1],
            )
            challenger_unalerted = timing_receipt["models"][challenger]["budgets"][budget][
                "positive_unalerted_rate"
            ]
            gru_unalerted = timing_receipt["models"]["gru"]["budgets"][budget][
                "positive_unalerted_rate"
            ]
            result["unalerted_rate_not_higher"] = challenger_unalerted <= gru_unalerted
            result["unalerted_rate_difference"] = challenger_unalerted - gru_unalerted
            result["budget_timing_dominates"] = (
                result["dominates_or_ties_everywhere"]
                and result["unalerted_rate_not_higher"]
            )
            timing_all &= result["budget_timing_dominates"]
            timing_comparisons[budget] = result

        six_dr_differences = {
            budget: complete_receipt["models"][challenger]["budget_readouts"][budget][
                "detection_rate"
            ]
            - complete_receipt["models"]["gru"]["budget_readouts"][budget][
                "detection_rate"
            ]
            for budget in BUDGETS
        }
        six_dr_all = all(value >= 0.0 for value in six_dr_differences.values())
        operational_dominates = (
            six_dr_all
            and complete_curve["dominates_or_ties_everywhere"]
            and timing_all
            and (
                any(value > 0.0 for value in six_dr_differences.values())
                or complete_curve["strictly_better_somewhere"]
                or any(
                    result["strictly_better_somewhere"]
                    or result["unalerted_rate_difference"] < 0.0
                    for result in timing_comparisons.values()
                )
            )
        )
        flow_ap_difference = (
            aggregate["models"][challenger]["flow_average_precision"]
            - aggregate["models"]["gru"]["flow_average_precision"]
        )
        entity_ap_difference = (
            aggregate["models"][challenger]["max_pool_entity_average_precision"]
            - aggregate["models"]["gru"]["max_pool_entity_average_precision"]
        )
        dominance[challenger] = {
            "challenger": challenger,
            "reference": "gru",
            "six_budget_dr_differences": six_dr_differences,
            "six_budget_dr_not_lower": six_dr_all,
            "complete_budget_curve": complete_curve,
            "first_alert_by_budget": timing_comparisons,
            "first_alert_all_budgets_dominates": timing_all,
            "operational_vector_dominates": operational_dominates,
            "flow_average_precision_difference": flow_ap_difference,
            "entity_average_precision_difference": entity_ap_difference,
            "complete_performance_vector_dominates": (
                operational_dominates
                and flow_ap_difference >= 0.0
                and entity_ap_difference >= 0.0
            ),
        }

    model_readouts = {}
    for model in MODELS:
        model_readouts[model] = {
            "display_name": aggregate["models"][model]["display_name"],
            "flow_average_precision": aggregate["models"][model]["flow_average_precision"],
            "entity_average_precision": aggregate["models"][model][
                "max_pool_entity_average_precision"
            ],
            "budget_readouts": {
                budget: {
                    "nominal_target_fpr": complete_receipt["models"][model][
                        "budget_readouts"
                    ][budget]["nominal_target_fpr"],
                    "actual_reachable_fpr": complete_receipt["models"][model][
                        "budget_readouts"
                    ][budget]["actual_reachable_fpr"],
                    "detection_rate": complete_receipt["models"][model][
                        "budget_readouts"
                    ][budget]["detection_rate"],
                    "false_positive_entity_count": complete_receipt["models"][model][
                        "budget_readouts"
                    ][budget]["false_positive_entity_count"],
                    "threshold": complete_receipt["models"][model]["budget_readouts"][
                        budget
                    ]["threshold"],
                    "threshold_tie_group_size": complete_receipt["models"][model][
                        "budget_readouts"
                    ][budget]["threshold_tie_group_size"],
                    "first_alert_actual_fpr": timing_receipt["models"][model]["budgets"][
                        budget
                    ]["realized_first_alert_fpr"],
                    "positive_unalerted_rate": timing_receipt["models"][model]["budgets"][
                        budget
                    ]["positive_unalerted_rate"],
                    "first_alert_exposure_quantiles": timing_receipt["models"][model][
                        "budgets"
                    ][budget]["malicious_first_alert_exposure_quantiles"],
                }
                for budget in BUDGETS
            },
            "old_anchor_exact_record": {
                metric: {
                    "historical_registered_value": input_receipt["model_reproduction"][model][
                        "expected"
                    ][metric],
                    "recomputed_full_precision_value": input_receipt["model_reproduction"][model][
                        "actual"
                    ][metric],
                    "exact_delta": input_receipt["model_reproduction"][model]["actual"][metric]
                    - input_receipt["model_reproduction"][model]["expected"][metric],
                }
                for metric in (
                    "flow_average_precision",
                    "max_pool_entity_average_precision",
                    "dr_at_4_percent_fpr",
                )
            },
        }

    output = {
        "schema_version": "published-neural-operational-backfill-analysis-validation-v1",
        "input_root": str(root),
        "mechanical_validation": {
            "passed": not validator.failures,
            "check_count": validator.check_count,
            "failures": validator.failures,
            "manifest_file_checks": file_checks,
        },
        "dataset_counts": {
            "flow_count": input_receipt["flow_count"],
            "entity_count": input_receipt["entity_count"],
            "positive_entity_count": input_receipt["positive_entity_count"],
            "negative_entity_count": input_receipt["negative_entity_count"],
        },
        "frozen_input_identity": {
            "config_sha256": input_receipt["config_sha256"],
            "tool_sha256": input_receipt["tool_sha256"],
            "entity_construction": input_receipt["entity_construction"],
            "files": input_receipt["files"],
            "model_keys": sorted(input_receipt["model_reproduction"]),
        },
        "models": model_readouts,
        "curve_summary": curve_summary,
        "timing_summary": timing_summary,
        "dominance_over_gru": dominance,
        "resource": resource,
        "evidence_boundary": {
            "evaluation_role": aggregate["evaluation_role"],
            "time_delay_available": aggregate["time_delay_available"],
            "training_runs": aggregate["training_runs"],
            "inference_runs": aggregate["inference_runs"],
            "score_fusion_performed": aggregate["score_fusion_performed"],
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(output["mechanical_validation"], ensure_ascii=False))
    return 0 if not validator.failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
