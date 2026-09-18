#!/usr/bin/env python3
"""DRIFT 折0双侧风险约束更新专家混合的零重训短步筛查。"""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import itertools
import json
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import torch

import ch3_drift_n12_g2_family_isolated_short_step as g2
import ch3_drift_t17_equal3_auxheads_gradient_base as g0
import neural_precision_runtime as precision


SCHEMA_VERSION = "ch3-drift-update-expert-mixture-fold0-short-step-v1"
BRANCHES = ("char", "subword")
TASKS = ("MTP", "TPP", "TOV")
HEAD_PREFIXES = ("mtp_head", "tpp_head", "tov_head")


@dataclass(frozen=True)
class CombinedArm:
    name: str
    states: Mapping[str, Mapping[str, torch.Tensor]]
    receipt: Mapping[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def atomic_torch(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    torch.save(dict(value), partial)
    os.replace(partial, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def optimizer_hash(state: Mapping[str, Any]) -> str:
    buffer = io.BytesIO()
    torch.save(dict(state), buffer)
    return hashlib.sha256(buffer.getvalue()).hexdigest()


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("配置 schema_version 不匹配")
    if config.get("approved_scope") != "fold0_t17_zero_retraining_risk_constrained_update_only":
        raise ValueError("配置范围不匹配")
    if config.get("screening_only") is not True or config.get("seed") != 42:
        raise ValueError("必须保持 screening_only 和种子 42")
    if config.get("dataset_revision") != "3b31077020cd1c013d0a75cad51042a2327c4521":
        raise ValueError("数据 revision 不匹配")
    if tuple(config.get("arms", ())) != ("no_update", "joint_all_equal", "risk_feasible_update_mixture"):
        raise ValueError("三臂合同不匹配")
    if int(config["short_step"]["batch_size"]) != 1024 or int(config["short_step"]["batches"]) != 32:
        raise ValueError("短步必须固定为 32 x 1024")
    if float(config["mixture"]["total_execution_mass"]) != 6.0:
        raise ValueError("执行系数总质量必须为 6")
    expected = {"char": {"TOV": 1.151309601185306}, "subword": {"TOV": 4.848690398814694}}
    if config["mixture"]["execution_coefficients"] != expected:
        raise ValueError("风险可行混合系数偏离冻结值")
    g2.reject_future_values(config)
    return config


def verify_file(path: Path, expected: str, description: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"{description}不存在：{path}")
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{description} SHA-256 不匹配")
    return actual


def source_identity(config: Mapping[str, Any], root: Path) -> tuple[dict[str, Any], dict[str, Any], Mapping[str, Any], tuple[g2.FoldSpec, ...], Mapping[str, g2.InputSpec], Any, Mapping[str, Any], str]:
    source = config["g2_source"]
    g2_config_path = root / str(source["config"])
    g2_script_path = root / str(source["script"])
    verify_file(g2_config_path, str(source["config_sha256"]), "G2 配置")
    verify_file(g2_script_path, str(source["script_sha256"]), "G2 入口")
    g2_config = g2.load_config(g2_config_path)
    g2_predecessors = g2.verify_predecessors(g2_config, root)
    inputs = {
        "fit_benign": g2.load_spec(g2_config["inputs"]["fit"][0], root, "G2 fit benign"),
        "fit_dga": g2.load_spec(g2_config["inputs"]["fit"][1], root, "G2 fit DGA"),
        "val_benign": g2.load_spec(g2_config["inputs"]["validation"][0], root, "G2 val benign"),
        "val_dga": g2.load_spec(g2_config["inputs"]["validation"][1], root, "G2 val DGA"),
    }
    identity = {
        "config_sha256": sha256_file(g2_config_path),
        "script_sha256": sha256_file(g2_script_path),
        "inputs": [item.sha256 for item in inputs.values()],
        "predecessors": g2_predecessors,
    }
    mapping = g2.build_family_mapping(g2_config, root)
    folds = g2.build_complementary_folds(mapping)
    if folds[0].index != 0:
        raise ValueError("G2 折0身份不匹配")
    p0_config = g2.pilot.load_config(root / str(g2_config["p0"]["config"]), root)
    contract_path = root / str(g2_config["runtime"]["precision_contract"])
    verify_file(contract_path, str(g2_config["runtime"]["precision_contract_sha256"]), "精度合同")
    device = g2.pilot.device_for_run()
    contract = precision.load_and_validate_contract(contract_path)
    profile_id = precision.profile_for_device(contract, device.type)
    if device.type == "cuda" and profile_id != g2_config["runtime"]["precision_profile"]:
        raise ValueError("实际精度 profile 偏离冻结 G2 合同")
    profile = precision.validate_runtime_profile(contract, profile_id, device.type, torch)
    torch.set_float32_matmul_precision("high")
    return identity, g2_config, mapping, folds, inputs, p0_config, profile, profile_id


def verify_g2_artifacts(config: Mapping[str, Any], root: Path, identity: Mapping[str, Any]) -> Path:
    source = config["g2_source"]
    run_dir = root / str(source["run_dir"])
    for name, expected in source["fixed_artifacts"].items():
        verify_file(run_dir / name, str(expected), f"G2 固定制品 {name}")
    for branch, arms in source["arm_receipts"].items():
        for arm, expected in arms.items():
            receipt_path = run_dir / "arms" / f"fold-0-{branch}-{arm}.json"
            verify_file(receipt_path, str(expected), f"G2 arm 收据 {branch}/{arm}")
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("identity") != identity or receipt.get("receipt", {}).get("batches") != 32:
                raise ValueError(f"G2 arm 收据身份或批数不匹配：{branch}/{arm}")
    return run_dir


def load_fold0_endpoint(
    config: Mapping[str, Any],
    root: Path,
    source_run_dir: Path,
    identity: Mapping[str, Any],
    fold: g2.FoldSpec,
    p0_config: Mapping[str, Any],
    device: torch.device,
) -> tuple[g2.EndpointReceipt, g2.ProbeReceipt]:
    endpoint_path = source_run_dir / "fold-0-endpoint.pt"
    probe_path = source_run_dir / "fold-0-probe.pt"
    if not endpoint_path.is_file() or not probe_path.is_file():
        raise FileNotFoundError("G2 折0端点或冻结探针不存在")
    endpoint = g2.load_endpoint(endpoint_path, fold, source_run_dir, p0_config, identity, device)
    probe_state = torch.load(probe_path, map_location="cpu", weights_only=False)
    if probe_state.get("identity") != identity:
        raise ValueError("G2 折0探针身份不匹配")
    probe = g2.build_probe(endpoint, p0_config, device)
    probe.classifier.load_state_dict(probe_state["classifier"], strict=True)
    return endpoint, g2.ProbeReceipt(probe, probe_state["receipt"])


def verify_block_and_gradients(
    config: Mapping[str, Any],
    source_run_dir: Path,
    identity: Mapping[str, Any],
    fold: g2.FoldSpec,
    endpoint: g2.EndpointReceipt,
    inputs: Mapping[str, g2.InputSpec],
    g2_config: Mapping[str, Any],
) -> tuple[g2.BlockSpec, Mapping[str, g2.GradientReceipt]]:
    block = g2.fixed_block(fold, inputs, g2_config)
    if block.batches != int(config["short_step"]["batches"]) or len(block.domains) != 32768:
        raise ValueError("折0固定成员块大小不匹配")
    gradients: dict[str, g2.GradientReceipt] = {}
    for branch in BRANCHES:
        state = torch.load(source_run_dir / f"fold-0-{branch}-gradients.pt", map_location="cpu", weights_only=False)
        if state.get("identity") != identity or state.get("fold") != 0 or state.get("branch") != branch:
            raise ValueError(f"G2 {branch} 梯度身份不匹配")
        gradients[branch] = g2.GradientReceipt(state["summary"], state["vectors"])
    for branch, arms in config["g2_source"]["arm_receipts"].items():
        for arm in arms:
            receipt = json.loads((source_run_dir / "arms" / f"fold-0-{branch}-{arm}.json").read_text(encoding="utf-8"))
            endpoint_hash = g2.state_hash(endpoint.branches[branch].state_dict())
            if (
                receipt.get("block_sha256") != block.digest
                or receipt.get("receipt", {}).get("samples") != len(block.domains)
                or receipt.get("endpoint_sha256") != endpoint_hash
                or receipt.get("start_model_sha256") != endpoint_hash
            ):
                raise ValueError(f"G2 {branch}/{arm} 未使用同一固定成员块")
    return block, gradients


def raw_lp_receipt(config: Mapping[str, Any], gradients: Mapping[str, g2.GradientReceipt]) -> dict[str, Any]:
    lp = config["mixture"]["raw_gradient_lp"]
    labels = tuple(f"{branch}:{task}" for branch in BRANCHES for task in TASKS)
    risks = ("benign_bce", "dga_micro_bce", "dga_family_macro_bce")
    matrix = [
        [g2.vector_dot(gradients[branch].vectors["risks"][risk], gradients[branch].vectors["tasks"][task]) for branch in BRANCHES for task in TASKS]
        for risk in risks
    ]
    weights, gamma = solve_max_min_simplex(matrix)
    residuals = [sum(row[index] * weights[index] for index in range(len(labels))) for row in matrix]
    if not all(math.isfinite(value) for value in weights + [gamma, *residuals]):
        raise FloatingPointError("原始梯度 LP 产生非有限值")
    expected_weights = [float(lp["simplex_weights"][branch][task]) for branch in BRANCHES for task in TASKS]
    if any(not math.isclose(actual, expected, rel_tol=1e-7, abs_tol=1e-10) for actual, expected in zip(weights, expected_weights, strict=True)):
        raise ValueError("LP 实际求解权重偏离冻结收据")
    if not math.isclose(gamma, float(lp["max_min"]), rel_tol=1e-7, abs_tol=1e-12):
        raise ValueError("LP 实际求解最大最小裕量偏离冻结收据")
    for risk, actual in zip(risks, residuals, strict=True):
        if not math.isclose(actual, float(lp["raw_dot"][risk]), rel_tol=1e-8, abs_tol=1e-12):
            raise ValueError(f"原始梯度 LP 收据不匹配：{risk}")
    branch_diagnostics = {}
    for branch_index, branch in enumerate(BRANCHES):
        branch_matrix = [row[branch_index * len(TASKS) : (branch_index + 1) * len(TASKS)] for row in matrix]
        _, branch_gamma = solve_max_min_simplex(branch_matrix)
        branch_diagnostics[branch] = {"max_min": branch_gamma, "comparison": "disclosure_only_not_a_frozen_global_gate"}
    delta_star = max(0.0, -gamma)
    execution = [6.0 * value for value in weights]
    return {
        "columns": labels,
        "risks": risks,
        "matrix": matrix,
        "matrix_sha256": hashlib.sha256(json.dumps(matrix, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "solver": "deterministic_simplex_vertex_enumeration",
        "solver_dependency": "Python 标准库和 PyTorch 张量点积",
        "simplex_weights": dict(zip(labels, weights, strict=True)),
        "execution_coefficients": dict(zip(labels, execution, strict=True)),
        "simplex_max_min": gamma,
        "constraint_residuals": dict(zip(risks, residuals, strict=True)),
        "minimum_max_violation_delta_star": delta_star,
        "decision": "execute_update" if gamma >= 0.0 and delta_star == 0.0 else "skip_update",
        "per_branch_simplex": branch_diagnostics,
        "frozen_reference": lp,
    }


def solve_max_min_simplex(matrix: list[list[float]]) -> tuple[list[float], float]:
    """枚举 LP 顶点，避免引入未冻结的外部求解器依赖。"""
    if len(matrix) != 3 or not matrix or not matrix[0]:
        raise ValueError("LP 矩阵必须为 3 x N，且 N >= 1")
    risk_count, expert_count = len(matrix), len(matrix[0])
    if any(len(row) != expert_count for row in matrix):
        raise ValueError("LP 矩阵各风险行长度必须一致")
    best: tuple[float, tuple[float, ...]] | None = None
    for support_size in range(1, min(risk_count, expert_count) + 1):
        for support in itertools.combinations(range(expert_count), support_size):
            for active_risks in itertools.combinations(range(risk_count), support_size):
                equations = [[1.0] * support_size + [0.0]]
                targets = [1.0]
                for risk in active_risks:
                    equations.append([matrix[risk][index] for index in support] + [-1.0])
                    targets.append(0.0)
                system = torch.tensor(equations, dtype=torch.float64)
                target = torch.tensor(targets, dtype=torch.float64)
                if torch.linalg.matrix_rank(system) != system.shape[0]:
                    continue
                solution = torch.linalg.solve(system, target).tolist()
                local_weights, gamma = solution[:-1], float(solution[-1])
                if any(value < -1e-11 for value in local_weights):
                    continue
                weights = [0.0] * expert_count
                for index, value in zip(support, local_weights, strict=True):
                    weights[index] = max(0.0, float(value))
                margins = [sum(row[index] * weights[index] for index in range(expert_count)) for row in matrix]
                if any(value + 1e-11 < gamma for value in margins):
                    continue
                candidate = min(margins)
                key = tuple(weights)
                if best is None or candidate > best[0] + 1e-14 or (math.isclose(candidate, best[0], abs_tol=1e-14) and key < best[1]):
                    best = (candidate, key)
    if best is None:
        raise RuntimeError("未找到 LP 可行顶点")
    return list(best[1]), float(best[0])


def branch_delta(start: Mapping[str, torch.Tensor], end: Mapping[str, torch.Tensor]) -> float:
    return math.sqrt(sum(float(torch.sum((end[name].detach().double() - value.detach().double()).square()).cpu()) for name, value in start.items()))


def run_arm(
    name: str,
    coefficients: Mapping[str, Mapping[str, float]],
    endpoint: g2.EndpointReceipt,
    block: g2.BlockSpec,
    g2_config: Mapping[str, Any],
    device: torch.device,
    profile: Mapping[str, Any],
) -> CombinedArm:
    models = {branch: copy.deepcopy(endpoint.branches[branch]).to(device) for branch in BRANCHES}
    starts = {branch: g2.state_hash(model.state_dict()) for branch, model in models.items()}
    optimizers: dict[str, torch.optim.Optimizer] = {}
    optimizer_starts: dict[str, str] = {}
    for branch, model in models.items():
        model.train()
        for parameter_name, parameter in model.named_parameters():
            parameter.requires_grad_(not parameter_name.startswith(HEAD_PREFIXES))
        optimizer = torch.optim.Adam(model.parameters(), lr=float(g2_config["training"]["learning_rate"]))
        optimizer.load_state_dict(copy.deepcopy(endpoint.optimizers[branch]))
        optimizers[branch] = optimizer
        optimizer_starts[branch] = optimizer_hash(optimizer.state_dict())
    steps: list[dict[str, Any]] = []
    for index in range(block.batches):
        values = list(block.domains[index * int(g2_config["training"]["batch_size"]) : (index + 1) * int(g2_config["training"]["batch_size"])])
        step: dict[str, Any] = {"batch_index": index, "members": len(values), "branches": {}}
        for branch in BRANCHES:
            if name == "no_update":
                step["branches"][branch] = {"optimizer_step": False}
                continue
            model = models[branch]
            optimizer = optimizers[branch]
            ids = g2.encode_branch(branch, values, endpoint.tokenizer, g2_config, device)
            views = tuple(
                value.to(device)
                for value in g2.pilot.pretraining_views(
                    ids.detach().cpu(),
                    42 + index,
                    int(g2_config["pretraining"]["ignore_index"]),
                    float(g2_config["pretraining"]["mask_ratio"]),
                    float(g2_config["pretraining"]["shuffle_probability"]),
                )
            )
            optimizer.zero_grad(set_to_none=True)
            with precision.autocast_context(profile, device.type, torch):
                _, losses, valid = g0.task_losses(model, views, int(g2_config["pretraining"]["ignore_index"]))
            loss = sum(float(coefficients[branch].get(task, 0.0)) * losses[task].float() for task in TASKS)
            if not torch.isfinite(loss):
                raise FloatingPointError(f"{name}/{branch} 组合损失非有限")
            loss.backward()
            before = float(torch.nn.utils.clip_grad_norm_(model.parameters(), float(g2_config["training"]["gradient_clip_norm"])))
            if not math.isfinite(before):
                raise FloatingPointError(f"{name}/{branch} 梯度非有限")
            optimizer.step()
            step["branches"][branch] = {
                "optimizer_step": True,
                "task_valid_supervision": valid,
                "task_loss": {task: float(losses[task].detach().cpu()) for task in TASKS},
                "combined_loss": float(loss.detach().cpu()),
                "pre_clip_norm": before,
                "was_clipped": before > float(g2_config["training"]["gradient_clip_norm"]),
            }
        steps.append(step)
    states = {branch: model.state_dict() for branch, model in models.items()}
    end_hashes = {branch: g2.state_hash(state) for branch, state in states.items()}
    deltas = {branch: branch_delta(endpoint.branches[branch].state_dict(), states[branch]) for branch in BRANCHES}
    return CombinedArm(
        name,
        states,
        {
            "arm": name,
            "block_sha256": block.digest,
            "batches": block.batches,
            "samples": len(block.domains),
            "start_model_sha256": starts,
            "end_model_sha256": end_hashes,
            "start_optimizer_sha256": optimizer_starts,
            "end_optimizer_sha256": {branch: optimizer_hash(optimizers[branch].state_dict()) for branch in BRANCHES},
            "optimizer_steps_per_branch": 0 if name == "no_update" else block.batches,
            "update_l2_norm_per_branch": deltas,
            "update_l2_norm_combined": math.sqrt(sum(value * value for value in deltas.values())),
            "coefficients": coefficients,
            "steps": steps,
        },
    )


def evaluate_combined_arm(
    arm: CombinedArm,
    endpoint: g2.EndpointReceipt,
    probe: g2.ProbeReceipt,
    fold: g2.FoldSpec,
    inputs: Mapping[str, g2.InputSpec],
    mapping: g2.FamilyMapping,
    shuffled: g2.ShuffledLabels,
    p0_config: Mapping[str, Any],
    g2_config: Mapping[str, Any],
    device: torch.device,
    profile: Mapping[str, Any],
    threshold: float,
) -> dict[str, Any]:
    armed = g2.EndpointReceipt(endpoint.tokenizer, {branch: copy.deepcopy(endpoint.branches[branch]) for branch in BRANCHES}, endpoint.optimizers, endpoint.rng_state, endpoint.receipt)
    for branch in BRANCHES:
        armed.branches[branch].load_state_dict(arm.states[branch], strict=True)
    compatibility_arm = g2.ArmReceipt(arm.name, "char", arm.states["char"], arm.receipt)
    return g2.evaluate_arm(compatibility_arm, armed, probe, fold, inputs, mapping, shuffled, p0_config, g2_config, device, profile, threshold, False)


def compare_metrics(candidate: Mapping[str, Any], baseline: Mapping[str, Any]) -> dict[str, float]:
    return {name: float(candidate[name]) - float(baseline[name]) for name in ("benign_bce", "dga_micro_bce", "dga_family_macro_bce")}


def adjudicate(results: Mapping[str, Mapping[str, Any]]) -> tuple[str, dict[str, Any]]:
    mixture = results["risk_feasible_update_mixture"]["frozen_probe"]
    no_update = results["no_update"]["frozen_probe"]
    joint = results["joint_all_equal"]["frozen_probe"]
    against_no_update = compare_metrics(mixture, no_update)
    against_joint = compare_metrics(mixture, joint)
    def passes(delta: Mapping[str, float]) -> bool:
        return all(value <= 0.0 for value in delta.values()) and (delta["dga_micro_bce"] < 0.0 or delta["dga_family_macro_bce"] < 0.0)
    evidence = {"mixture_minus_no_update": against_no_update, "mixture_minus_joint_all_equal": against_joint, "passes_no_update": passes(against_no_update), "passes_joint_all_equal": passes(against_joint)}
    return ("eligible_for_formalization_only" if evidence["passes_no_update"] and evidence["passes_joint_all_equal"] else "rejected_after_finite_step", evidence)


def manifest(run_dir: Path, config_path: Path, root: Path) -> dict[str, Any]:
    paths = [config_path, Path(__file__).resolve(), root / "scripts/remote_launchers/run_ch3_drift_update_expert_mixture_fold0_short_step_v1.sh"]
    entries = [{"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size} for path in paths if path.is_file()]
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "status.json"}:
            entries.append({"path": str(path.relative_to(run_dir)), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    return {"schema_version": SCHEMA_VERSION, "files": entries}


def main() -> int:
    args = parse_args()
    root, run_dir, config_path = args.project_root.resolve(), args.run_dir.resolve(), args.config.resolve()
    config = load_config(config_path)
    if run_dir.name != config["run_identity"]:
        raise ValueError("运行目录与冻结身份不一致")
    if run_dir.exists() and not args.resume:
        raise FileExistsError("运行目录已存在；只允许同身份 --resume")
    run_dir.mkdir(parents=True, exist_ok=True)
    status_path, checkpoint_path = run_dir / "status.json", run_dir / "checkpoint.pt"
    started = time.monotonic()
    atomic_json(status_path, {"status": "running", "stage": "verify"})
    try:
        identity, g2_config, mapping, folds, inputs, p0_config, profile, profile_id = source_identity(config, root)
        source_run_dir = verify_g2_artifacts(config, root, identity)
        fold = folds[0]
        endpoint, probe = load_fold0_endpoint(config, root, source_run_dir, identity, fold, p0_config, g2.pilot.device_for_run())
        block, gradients = verify_block_and_gradients(config, source_run_dir, identity, fold, endpoint, inputs, g2_config)
        if block.digest != str(config["g2_source"]["fixed_block_sha256"]):
            raise ValueError("固定成员块哈希偏离研究卡")
        lp_receipt = raw_lp_receipt(config, gradients)
        atomic_json(run_dir / "solver-receipt.json", lp_receipt)
        if lp_receipt["decision"] != "execute_update":
            raise RuntimeError("原始梯度 LP 不可行；禁止执行松弛更新")
        source_receipt = {
            "g2_run_dir": str(source_run_dir),
            "g2_endpoint_sha256": sha256_file(source_run_dir / "fold-0-endpoint.pt"),
            "g2_probe_sha256": sha256_file(source_run_dir / "fold-0-probe.pt"),
            "g2_tokenizer_sha256": sha256_file(source_run_dir / "fold-0" / "tokenizer.json"),
            "g2_optimizer_start_sha256": {branch: optimizer_hash(endpoint.optimizers[branch]) for branch in BRANCHES},
            "g2_endpoint_model_sha256": {branch: g2.state_hash(endpoint.branches[branch].state_dict()) for branch in BRANCHES},
            "g2_gradient_sha256": {branch: sha256_file(source_run_dir / f"fold-0-{branch}-gradients.pt") for branch in BRANCHES},
            "fixed_block_sha256": block.digest,
        }
        script_hash, config_hash = sha256_file(Path(__file__).resolve()), sha256_file(config_path)
        own_identity = {"config_sha256": config_hash, "script_sha256": script_hash, "g2_identity": identity, "source_receipt": source_receipt}
        atomic_json(run_dir / "effective-config.json", {"config": config, "identity": own_identity, "profile": profile_id})
        shuffled = g2.build_shuffled_labels([(key, family) for key, family in mapping.val_members.items() if key in fold.meta_val_digests], identity["config_sha256"])
        threshold = g2.frozen_fit_threshold(endpoint, probe, fold, inputs, g2_config, g2.pilot.device_for_run())
        coefficients = {
            "no_update": {branch: {} for branch in BRANCHES},
            "joint_all_equal": {branch: {task: 1.0 for task in TASKS} for branch in BRANCHES},
            "risk_feasible_update_mixture": config["mixture"]["execution_coefficients"],
        }
        results: dict[str, Any] = {}
        for name in config["arms"]:
            arm_path = run_dir / "arms" / f"{name}.json"
            if args.resume and arm_path.is_file():
                existing = json.loads(arm_path.read_text(encoding="utf-8"))
                if existing.get("identity") != own_identity or existing.get("receipt", {}).get("block_sha256") != block.digest:
                    raise ValueError(f"{name} 断点身份不匹配")
                results[name] = existing
                continue
            arm = run_arm(name, coefficients[name], endpoint, block, g2_config, g2.pilot.device_for_run(), profile)
            metrics = evaluate_combined_arm(arm, endpoint, probe, fold, inputs, mapping, shuffled, p0_config, g2_config, g2.pilot.device_for_run(), profile, threshold)
            results[name] = {"identity": own_identity, "receipt": arm.receipt, "frozen_probe": metrics}
            atomic_json(arm_path, results[name])
            atomic_torch(checkpoint_path, {"identity": own_identity, "stage": "arms", "completed_arms": sorted(results), "rng_state": g2.pilot.capture_rng_state()})
        verdict, evidence = adjudicate(results)
        device = g2.pilot.device_for_run()
        resources = {
            "device": torch.cuda.get_device_name(0) if device.type == "cuda" else str(device),
            "device_type": device.type,
            "precision_profile": profile_id,
            "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()) if device.type == "cuda" else None,
            "peak_reserved_bytes": int(torch.cuda.max_memory_reserved()) if device.type == "cuda" else None,
        }
        result = {
            "schema_version": SCHEMA_VERSION,
            "status": "completed",
            "screening_only": True,
            "run_identity": config["run_identity"],
            "identity": own_identity,
            "forbidden_years_accessed": [],
            "fold": 0,
            "source_frozen_threshold": threshold,
            "short_step": {"batches": block.batches, "samples": len(block.domains), "block_sha256": block.digest},
            "source_receipt": source_receipt,
            "raw_gradient_lp": lp_receipt,
            "finite_step_interpretation": "Adam 预条件、逐批非线性和梯度裁剪使有限步结果成为对 raw-gradient LP 的真实检验，不保证保持其线性可行性。",
            "arms": results,
            "adjudication_evidence": evidence,
            "verdict": verdict,
            "runtime": {"wall_seconds": time.monotonic() - started, "resources": resources, "precision_profile": profile},
            "interpretation_boundary": config["interpretation_boundary"],
        }
        atomic_json(run_dir / "result.json", result)
        atomic_torch(checkpoint_path, {"identity": own_identity, "stage": "completed", "result_sha256": sha256_file(run_dir / "result.json"), "rng_state": g2.pilot.capture_rng_state()})
        atomic_json(run_dir / "manifest.json", manifest(run_dir, config_path, root))
        atomic_json(status_path, {"status": "completed", "stage": "completed", "result_sha256": sha256_file(run_dir / "result.json"), "checkpoint_sha256": sha256_file(checkpoint_path), "manifest_sha256": sha256_file(run_dir / "manifest.json")})
        return 0
    except Exception as error:
        atomic_json(status_path, {"status": "failed", "error_type": type(error).__name__, "error": str(error)})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
