"""比较共享基底单码对照与物理状态路由候选。"""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Mapping
from pathlib import Path

from flow_probe.physics_routed_experts import EXPERT_NAMES

SCHEMA_VERSION = "physics_routed_experts_comparison_v1"
MINIMUM_EXPERT_RATE = 0.05
MINIMUM_NORMALIZED_ENTROPY = 0.50
MINIMUM_RELATIVE_IMPROVEMENT = 0.01
MAXIMUM_RELATIVE_WORSENING = 0.01
MAXIMUM_FAMILY_LOGIT_DIFFERENCE = 1e-6
EXPECTED_ALLOWED_FIELDS = (
    "predicted_state.q4_minus_q0",
    "predicted_state.mean_q0_to_q4",
)
EXPECTED_REJECTED_FIELDS = (
    "state_target",
    "queue_capacity",
    "received_throughput",
    "dequeued_throughput",
    "dropped_throughput",
    "attack_label",
    "dataset_source",
    "scenario_id",
    "unknown_attack_label",
)


class RoutedExpertAnalysisError(ValueError):
    """输入制品不满足固定比较协议。"""


def _read_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise RoutedExpertAnalysisError(f"输入制品不存在：{path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RoutedExpertAnalysisError(f"输入制品根节点必须是对象：{path}")
    return value


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RoutedExpertAnalysisError(f"{name} 必须是对象")
    return value


def _finite_float(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RoutedExpertAnalysisError(f"{name} 必须是数值")
    result = float(value)
    if not math.isfinite(result):
        raise RoutedExpertAnalysisError(f"{name} 必须是有限值")
    return result


def _relative_improvement(reference: float, candidate: float) -> float:
    if reference < 0.0 or candidate < 0.0:
        raise RoutedExpertAnalysisError("损失指标不得为负")
    if reference == 0.0:
        return 0.0 if candidate == 0.0 else -1.0
    return (reference - candidate) / reference


def _load_run(output: Path) -> dict[str, object]:
    root = Path(output)
    if not root.is_dir():
        raise RoutedExpertAnalysisError(f"运行目录不存在：{root}")
    summary = _read_json(root / "training_summary.json")
    return {
        "root": root,
        "summary": summary,
        "route_thresholds": _read_json(root / "route_thresholds.json"),
        "routing_contract": _read_json(root / "routing_contract.json"),
        "expert_codes": _read_json(root / "expert_codes.json"),
        "route_usage": _read_json(root / "route_usage.json"),
        "specialization": _read_json(root / "specialization.json"),
        "expert_condition_gradients": _read_json(root / "expert_condition_gradients.json"),
        "family_equivalence": _read_json(root / "family_equivalence.json"),
        "structure_config": _read_json(root / "structure_config.json"),
    }


def _budget_gate(single: Mapping[str, object], routed: Mapping[str, object]) -> dict[str, object]:
    single_budget = _mapping(single["summary"], "single.summary").get("budget")
    routed_budget = _mapping(routed["summary"], "routed.summary").get("budget")
    left = _mapping(single_budget, "single.budget")
    right = _mapping(routed_budget, "routed.budget")
    required = {
        "target_layers": [24, 25, 26, 27],
        "rank_per_layer": 16,
        "rank_sum": 64,
        "full_rank_channels_activated_per_forward": 16,
        "codes_are_parameters": False,
        "three_independent_lora_experts": False,
    }
    fixed_contract = all(
        left.get(name) == value and right.get(name) == value for name, value in required.items()
    )
    equal_fields = (
        "shared_basis_parameter_count",
        "gate_parameter_count",
        "outcome_state_head_parameter_count",
        "frozen_router_state_head_parameter_count",
        "trainable_parameter_count",
        "expected_trainable_parameter_count",
    )
    exact_equality = all(left.get(name) == right.get(name) for name in equal_fields)
    self_consistent = all(
        budget.get("trainable_parameter_count") == budget.get("expected_trainable_parameter_count")
        for budget in (left, right)
    )
    return {
        "required_contract": required,
        "equal_fields": list(equal_fields),
        "fixed_contract": fixed_contract,
        "exact_parameter_budget_equality": exact_equality,
        "self_consistent": self_consistent,
        "pass": fixed_contract and exact_equality and self_consistent,
    }


def _sample_order_gate(
    single_summary: Mapping[str, object],
    routed_summary: Mapping[str, object],
) -> dict[str, object]:
    single_order = _mapping(single_summary.get("sample_order"), "single.sample_order")
    routed_order = _mapping(routed_summary.get("sample_order"), "routed.sample_order")
    generation_equal = single_order.get("generation_sha256") == routed_order.get(
        "generation_sha256"
    )
    physics_equal = single_order.get("physics_sha256") == routed_order.get("physics_sha256")
    return {
        "generation_equal": generation_equal,
        "physics_equal": physics_equal,
        "single": dict(single_order),
        "routed": dict(routed_order),
        "pass": generation_equal and physics_equal,
    }


def _routing_integrity_gate(
    single: Mapping[str, object],
    routed: Mapping[str, object],
) -> dict[str, object]:
    single_thresholds = _mapping(single["route_thresholds"], "single.route_thresholds")
    routed_thresholds = _mapping(routed["route_thresholds"], "routed.route_thresholds")
    thresholds_equal = all(
        _finite_float(single_thresholds.get(name), f"single.{name}")
        == _finite_float(routed_thresholds.get(name), f"routed.{name}")
        for name in ("growth", "pressure")
    )
    contracts = (
        _mapping(single["routing_contract"], "single.routing_contract"),
        _mapping(routed["routing_contract"], "routed.routing_contract"),
    )
    contracts_valid = all(
        tuple(contract.get("allowed_fields", ())) == EXPECTED_ALLOWED_FIELDS
        and tuple(contract.get("rejected_fields", ())) == EXPECTED_REJECTED_FIELDS
        and contract.get("family_expert_mask_fixed_false") is True
        and contract.get("unknown_attack_labels_in_training_or_calibration") is False
        for contract in contracts
    )
    calibration_valid = all(
        _mapping(thresholds.get("calibration"), "thresholds.calibration").get("calibration_source")
        == "frozen_router_state_head_predictions_only"
        and _mapping(thresholds.get("calibration"), "thresholds.calibration").get(
            "unknown_attack_labels_used"
        )
        is False
        and _mapping(thresholds.get("calibration"), "thresholds.calibration").get(
            "saved_raw_predictions"
        )
        is False
        for thresholds in (single_thresholds, routed_thresholds)
    )
    return {
        "thresholds_equal": thresholds_equal,
        "allowed_and_rejected_fields_valid": contracts_valid,
        "calibration_predictions_only": calibration_valid,
        "pass": thresholds_equal and contracts_valid and calibration_valid,
    }


def _code_gate(single: Mapping[str, object], routed: Mapping[str, object]) -> dict[str, object]:
    expected_gram = [[16.0, 0.0, 0.0], [0.0, 16.0, 0.0], [0.0, 0.0, 16.0]]
    code_records = (
        _mapping(single["expert_codes"], "single.expert_codes"),
        _mapping(routed["expert_codes"], "routed.expert_codes"),
    )
    valid = all(
        record.get("pairwise_inner_products") == expected_gram
        and record.get("full_support") is True
        and record.get("codes_are_parameters") is False
        and record.get("single_code") == [1.0] * 16
        for record in code_records
    )
    identical = code_records[0] == code_records[1]
    return {
        "expected_pairwise_inner_products": expected_gram,
        "valid": valid,
        "identical_across_variants": identical,
        "pass": valid and identical,
    }


def _usage_gate(routed: Mapping[str, object]) -> dict[str, object]:
    usage = _mapping(routed["route_usage"], "routed.route_usage")
    details: dict[str, object] = {}
    passed = True
    for split in ("subtype_generation_validation", "physics_validation"):
        record = _mapping(usage.get(split), f"route_usage.{split}")
        rates = record.get("rates")
        if not isinstance(rates, list) or len(rates) != 3:
            raise RoutedExpertAnalysisError(f"{split}.rates 必须包含三个值")
        normalized_rates = [_finite_float(value, f"{split}.rates") for value in rates]
        entropy = _finite_float(record.get("normalized_entropy"), f"{split}.entropy")
        split_pass = (
            min(normalized_rates) >= MINIMUM_EXPERT_RATE and entropy >= MINIMUM_NORMALIZED_ENTROPY
        )
        details[split] = {
            "rates": normalized_rates,
            "normalized_entropy": entropy,
            "minimum_rate_pass": min(normalized_rates) >= MINIMUM_EXPERT_RATE,
            "entropy_pass": entropy >= MINIMUM_NORMALIZED_ENTROPY,
            "pass": split_pass,
        }
        passed = passed and split_pass
    return {
        "minimum_expert_rate": MINIMUM_EXPERT_RATE,
        "minimum_normalized_entropy": MINIMUM_NORMALIZED_ENTROPY,
        "splits": details,
        "pass": passed,
    }


def _gradient_gate(routed: Mapping[str, object]) -> dict[str, object]:
    evidence = _mapping(
        routed["expert_condition_gradients"],
        "routed.expert_condition_gradients",
    )
    norms = evidence.get("gradient_norms")
    if not isinstance(norms, list) or len(norms) != 3:
        raise RoutedExpertAnalysisError("专家条件梯度必须包含三个范数")
    normalized = [_finite_float(value, "gradient_norm") for value in norms]
    valid_scope = (
        evidence.get("evidence_name") == "expert_condition_gradient"
        and evidence.get("parameter_scope") == "four_layer_shared_A_B"
        and evidence.get("independent_expert_parameter_updates_claimed") is False
    )
    return {
        "expert_names": list(EXPERT_NAMES),
        "gradient_norms": normalized,
        "valid_shared_parameter_scope": valid_scope,
        "all_nonzero": all(value > 0.0 for value in normalized),
        "pass": valid_scope and all(value > 0.0 for value in normalized),
    }


def _specialization_gate(routed: Mapping[str, object]) -> dict[str, object]:
    record = _mapping(routed["specialization"], "routed.specialization")
    margins = record.get("diagonal_margins")
    degradations = record.get("corresponding_expert_removal_state_loss_degradation")
    matrix = record.get("joint_loss_matrix")
    valid_matrix = (
        isinstance(matrix, list)
        and len(matrix) == 3
        and all(isinstance(row, list) and len(row) == 3 for row in matrix)
    )
    positive_margins = (
        isinstance(margins, list)
        and len(margins) == 3
        and all(
            value is not None and _finite_float(value, "diagonal_margin") > 0.0 for value in margins
        )
    )
    positive_degradation = (
        isinstance(degradations, list)
        and len(degradations) == 3
        and all(
            value is not None and _finite_float(value, "removal_degradation") > 0.0
            for value in degradations
        )
    )
    flags = (
        record.get("all_conditions_present") is True
        and record.get("all_diagonal_best") is True
        and record.get("all_removals_degrade") is True
    )
    return {
        "matrix_3x3": valid_matrix,
        "positive_diagonal_margins": positive_margins,
        "positive_corresponding_removal_degradation": positive_degradation,
        "saved_flags_valid": flags,
        "pass": valid_matrix and positive_margins and positive_degradation and flags,
    }


def _family_gate(
    single: Mapping[str, object],
    routed: Mapping[str, object],
) -> dict[str, object]:
    records = (
        _mapping(single["family_equivalence"], "single.family_equivalence"),
        _mapping(routed["family_equivalence"], "routed.family_equivalence"),
    )
    differences = [
        _finite_float(record.get("maximum_difference"), "family.maximum_difference")
        for record in records
    ]
    digests_unchanged = all(
        record.get("detection_adapter_sha256_before")
        == record.get("detection_adapter_sha256_after")
        and record.get("router_state_head_sha256_before")
        == record.get("router_state_head_sha256_after")
        for record in records
    )
    masks_false = all(record.get("expert_row_mask") is False for record in records)
    return {
        "maximum_logit_differences": differences,
        "maximum_allowed": MAXIMUM_FAMILY_LOGIT_DIFFERENCE,
        "frozen_digests_unchanged": digests_unchanged,
        "family_expert_masks_false": masks_false,
        "pass": (
            max(differences) <= MAXIMUM_FAMILY_LOGIT_DIFFERENCE
            and digests_unchanged
            and masks_false
        ),
    }


def _joint_gain_gate(
    single_summary: Mapping[str, object],
    routed_summary: Mapping[str, object],
) -> dict[str, object]:
    single_validation = _mapping(single_summary.get("validation"), "single.validation")
    routed_validation = _mapping(routed_summary.get("validation"), "routed.validation")
    metric_names = (
        "subtype_generation_loss",
        "state_mse_unobserved",
        "physics_residual_mse",
    )
    single_values = {
        name: _finite_float(single_validation.get(name), f"single.{name}") for name in metric_names
    }
    routed_values = {
        name: _finite_float(routed_validation.get(name), f"routed.{name}") for name in metric_names
    }
    improvements = {
        name: _relative_improvement(single_values[name], routed_values[name])
        for name in metric_names
    }
    generation_pass = improvements["subtype_generation_loss"] >= MINIMUM_RELATIVE_IMPROVEMENT
    state_improvement = improvements["state_mse_unobserved"]
    physics_improvement = improvements["physics_residual_mse"]
    physical_joint_pass = (
        max(state_improvement, physics_improvement) >= MINIMUM_RELATIVE_IMPROVEMENT
        and min(state_improvement, physics_improvement) >= -MAXIMUM_RELATIVE_WORSENING
    )
    return {
        "single": single_values,
        "routed": routed_values,
        "relative_improvements": improvements,
        "minimum_required_improvement": MINIMUM_RELATIVE_IMPROVEMENT,
        "maximum_allowed_worsening": MAXIMUM_RELATIVE_WORSENING,
        "generation_pass": generation_pass,
        "state_or_physics_joint_pass": physical_joint_pass,
        "pass": generation_pass and physical_joint_pass,
    }


def analyze_physics_routed_experts(
    single_output: Path,
    routed_output: Path,
    output: Path,
) -> dict[str, object]:
    """生成逐项门槛结果，并在任一失败时把 overall_pass 固定为假。"""

    single = _load_run(Path(single_output))
    routed = _load_run(Path(routed_output))
    single_summary = _mapping(single["summary"], "single.summary")
    routed_summary = _mapping(routed["summary"], "routed.summary")
    variants_valid = (
        single_summary.get("variant") == "single" and routed_summary.get("variant") == "routed"
    )
    same_seed = single_summary.get("seed") == routed_summary.get("seed") == 42
    formal_steps = (
        single_summary.get("max_steps") == routed_summary.get("max_steps") == 50
        and single_summary.get("formal_probe") is True
        and routed_summary.get("formal_probe") is True
    )
    gates = {
        "run_contract": {
            "variants_valid": variants_valid,
            "same_seed_42": same_seed,
            "both_formal_50_steps": formal_steps,
            "pass": variants_valid and same_seed and formal_steps,
        },
        "budget": _budget_gate(single, routed),
        "sample_order": _sample_order_gate(single_summary, routed_summary),
        "routing_integrity": _routing_integrity_gate(single, routed),
        "codes": _code_gate(single, routed),
        "usage": _usage_gate(routed),
        "expert_condition_gradients": _gradient_gate(routed),
        "specialization": _specialization_gate(routed),
        "family_equivalence": _family_gate(single, routed),
        "joint_gain": _joint_gain_gate(single_summary, routed_summary),
    }
    overall_pass = all(bool(_mapping(record, name).get("pass")) for name, record in gates.items())
    result = {
        "schema_version": SCHEMA_VERSION,
        "single_output": str(Path(single_output)),
        "routed_output": str(Path(routed_output)),
        "thresholds": {
            "minimum_expert_rate": MINIMUM_EXPERT_RATE,
            "minimum_normalized_entropy": MINIMUM_NORMALIZED_ENTROPY,
            "minimum_relative_improvement": MINIMUM_RELATIVE_IMPROVEMENT,
            "maximum_relative_worsening": MAXIMUM_RELATIVE_WORSENING,
            "maximum_family_logit_difference": MAXIMUM_FAMILY_LOGIT_DIFFERENCE,
        },
        "gates": gates,
        "failed_gates": [name for name, record in gates.items() if not record["pass"]],
        "overall_pass": overall_pass,
        "next_action": (
            "eligible_for_formal_validation"
            if overall_pass
            else "stop_without_tuning_or_202_step_extension"
        ),
    }
    output_path = Path(output)
    if output_path.exists() or output_path.is_symlink():
        raise RoutedExpertAnalysisError(f"分析输出已存在，拒绝覆盖：{output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="比较单码与物理状态路由共享基底专家")
    parser.add_argument("--single-output", type=Path, required=True)
    parser.add_argument("--routed-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = analyze_physics_routed_experts(
        args.single_output,
        args.routed_output,
        args.output,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
