#!/usr/bin/env python3
"""M1-v2 投影原始-对偶 T17 短窗资格入口。"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor

import ch3_drift_n10_conservative_fusion_pilot as pilot

SCHEMA = "ch3-drift-n10-conservative-fusion-m1-v2-short-window-v1"
ARMS = ("scale_free_primal_dual", "unit_hinge_control")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def capture_rng() -> dict[str, Any]:
    return {"python": random.getstate(), "numpy": np.random.get_state(), "torch_cpu": torch.get_rng_state(), "torch_cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None}


def restore_rng(state: dict[str, Any]) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch_cpu"])
    if torch.cuda.is_available() and state.get("torch_cuda") is not None:
        torch.cuda.set_rng_state_all(state["torch_cuda"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--arm", required=True, choices=ARMS)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != SCHEMA or config.get("implementation_status") != "approved_for_t17_short_window":
        raise ValueError("M1-v2 配置或批准状态不匹配")
    if config.get("screening_only") is not True or config.get("seed") != 42:
        raise ValueError("M1-v2 必须保持单种子筛选身份")
    if tuple(config.get("arms", [])) != ARMS:
        raise ValueError("实验臂清单不匹配")
    training = config["training"]
    if (int(training["batch_size"]), int(training["steps"]), int(training["samples"]), float(training["learning_rate"])) != (1024, 32, 32768, 1e-4):
        raise ValueError("短窗预算或学习率偏离研究卡")
    return config


def score(logits: Tensor) -> Tensor:
    return (logits[:, 1] - logits[:, 0]).float()


def ratio_terms(candidate: Tensor, baseline: Tensor, labels: Tensor, threshold: np.float32) -> tuple[Tensor | None, dict[str, Tensor | None], dict[str, int]]:
    values: dict[str, Tensor | None] = {}
    empty: dict[str, int] = {"error_negative": 0, "error_positive": 0, "correct_negative": 0, "correct_positive": 0}
    for label, name, wrong in ((0, "negative", baseline >= threshold), (1, "positive", baseline < threshold)):
        margin = candidate - threshold if label == 0 else threshold - candidate
        base_margin = baseline - threshold if label == 0 else threshold - baseline
        error_mask = labels.eq(label) & wrong
        correct_mask = labels.eq(label) & ~wrong
        if bool(error_mask.any()):
            values[f"e_{name}"] = torch.nn.functional.softplus(margin[error_mask]).mean() / torch.nn.functional.softplus(base_margin[error_mask]).mean().detach()
        else:
            values[f"e_{name}"] = None
            empty[f"error_{name}"] += 1
        if bool(correct_mask.any()):
            values[f"h_{name}"] = torch.nn.functional.softplus(margin[correct_mask]).mean() / torch.nn.functional.softplus(base_margin[correct_mask]).mean().detach()
        else:
            values[f"h_{name}"] = None
            empty[f"correct_{name}"] += 1
    errors = [value for key, value in values.items() if key.startswith("e_") and value is not None]
    return torch.stack(errors).mean() if errors else None, values, empty


def tensor_value(value: Tensor | None) -> float | None:
    return float(value.detach().cpu()) if value is not None else None


def vector_stats(primary: Tensor, constraints: list[Tensor], parameters: list[Tensor]) -> dict[str, float | None]:
    raw = torch.autograd.grad(primary, parameters, retain_graph=True, allow_unused=True)
    constrained = torch.autograd.grad(sum(constraints), parameters, retain_graph=True, allow_unused=True)
    raw_vector = torch.cat([item.detach().flatten() for item in raw if item is not None])
    con_vector = torch.cat([item.detach().flatten() for item in constrained if item is not None])
    raw_norm, con_norm = float(raw_vector.norm().cpu()), float(con_vector.norm().cpu())
    angle = float(torch.dot(raw_vector, con_vector).cpu() / (raw_vector.norm() * con_vector.norm()).clamp_min(1e-12))
    return {"raw_gradient_norm": raw_norm, "constraint_gradient_norm": con_norm, "gradient_cosine": angle}


def save_checkpoint(path: Path, value: dict[str, Any]) -> None:
    partial = path.with_name(path.name + ".partial")
    torch.save(value, partial)
    os.replace(partial, path)


def validate(static: torch.nn.Module, adapter: torch.nn.Module, alpha: Tensor, tokenizer: Any, parts: Any, p0_config: dict[str, Any], config: dict[str, Any], threshold: np.float32, device: torch.device) -> dict[str, Any]:
    all_base: list[Tensor] = []
    all_candidate: list[Tensor] = []
    all_labels: list[Tensor] = []
    activity = {"gate_entropy": [], "residual_magnitude": [], "alpha": float(alpha.detach().cpu())}
    static.eval(); adapter.eval()
    with torch.inference_mode():
        for domains, labels in pilot.iter_labeled_batches(parts, int(config["training"]["batch_size"]), int(config["seed"])):
            token_ids = pilot.encode_subword(domains, tokenizer, int(p0_config["model"]["max_len_token"]), device)
            char_ids = pilot.encode_char(domains, int(p0_config["model"]["max_len_char"]), device)
            token_feature, char_feature = static.encode_branches(token_ids, char_ids)
            baseline = static.static_logits(token_feature, char_feature)
            dynamic, diagnostics = pilot.fusion_logits(token_feature, char_feature, baseline, "conservative_correction", adapter)
            candidate = baseline + alpha.float() * (dynamic.float() - baseline)
            weights = diagnostics["branch_weights"]
            activity["gate_entropy"].append(float((-(weights * weights.clamp_min(1e-12).log()).sum(dim=1).mean()).cpu()))
            activity["residual_magnitude"].append(float(diagnostics["residual"].abs().mean().cpu()))
            all_base.append(baseline.cpu()); all_candidate.append(candidate.cpu()); all_labels.append(labels)
    baseline, candidate, labels = torch.cat(all_base), torch.cat(all_candidate), torch.cat(all_labels)
    objective, values, empty = ratio_terms(score(candidate), score(baseline), labels, threshold)
    correction = pilot.correction_risk(candidate, baseline, labels, threshold)
    candidate_metrics = pilot.binary_metrics(candidate, labels, threshold, int(config["evaluation"]["ece_bins"]))
    baseline_metrics = pilot.binary_metrics(baseline, labels, threshold, int(config["evaluation"]["ece_bins"]))
    return {"objective": tensor_value(objective), "ratios": {key: tensor_value(value) for key, value in values.items()}, "empty_sides": empty, "correction": correction, "candidate_metrics": candidate_metrics, "baseline_metrics": baseline_metrics, "activity": {"mean_gate_entropy": float(np.mean(activity["gate_entropy"])), "mean_residual_magnitude": float(np.mean(activity["residual_magnitude"])), "alpha": activity["alpha"]}}


def support_status(validation: dict[str, Any], alpha: float, hinge_result: dict[str, Any] | None) -> tuple[str, list[str]]:
    metrics, baseline = validation["candidate_metrics"], validation["baseline_metrics"]
    ratios = validation["ratios"]
    reasons: list[str] = []
    if not (ratios["h_negative"] <= 1 and ratios["h_positive"] <= 1 and validation["objective"] < 1): reasons.append("ratio_guardrail")
    source, source_base = metrics["source_fpr_threshold"], baseline["source_fpr_threshold"]
    if source["fpr"] > source_base["fpr"] or source["fnr"] > source_base["fnr"] or (source["fpr"] == source_base["fpr"] and source["fnr"] == source_base["fnr"]): reasons.append("source_vector")
    for key in ("auroc", "average_precision", "brier"):
        if (key == "brier" and metrics[key] > baseline[key]) or (key != "brier" and metrics[key] < baseline[key]): reasons.append(f"metric_{key}")
    if metrics["ece"]["value"] > baseline["ece"]["value"]: reasons.append("metric_ece")
    if alpha in {0.0, 1.0}: reasons.append("alpha_inert_or_boundary")
    if hinge_result is not None and hinge_result.get("validation", {}).get("objective") is not None and hinge_result["validation"]["objective"] <= validation["objective"]: reasons.append("hinge_not_inferior")
    return ("eligible_for_full_t17_review" if not reasons else "rejected_after_t17_short_window"), reasons


def main() -> int:
    args = parse_args(); root = args.project_root.resolve(); config = load_config(args.config.resolve()); run_dir = args.run_dir.resolve() / args.arm
    p0_config = json.loads((root / config["p0_config"]).read_text(encoding="utf-8"))
    p0_root = root / config["p0_run_root"]; p0_dir = p0_root / "p0_c00"
    checkpoint_path, status_path = run_dir / "checkpoint.pt", run_dir / "status.json"
    p0_result = json.loads((p0_dir / "result.json").read_text(encoding="utf-8")); p0_status = json.loads((p0_dir / "status.json").read_text(encoding="utf-8"))
    if p0_result.get("status") != "completed" or p0_status.get("status") != "completed": raise ValueError("P0 未完成")
    p0_checkpoint = p0_dir / "checkpoint.pt"; tokenizer_path = p0_dir / "tokenizer.json"
    p0_hash, tokenizer_hash = sha256_file(p0_checkpoint), sha256_file(tokenizer_path)
    if p0_result.get("checkpoint_hash") != p0_hash or p0_result.get("tokenizer_sha256") != tokenizer_hash: raise ValueError("P0 哈希不匹配")
    threshold_source = p0_result["source_threshold"]; threshold = np.float32(threshold_source["threshold_float32"])
    if threshold_source.get("threshold_space") != "logit_difference" or threshold_source.get("threshold_dtype") != "float32": raise ValueError("源阈值不匹配")
    parts = pilot.input_parts(p0_config, root, "fit"); input_hashes = pilot.verify_inputs(parts)
    code_hash, config_hash = sha256_file(Path(__file__)), sha256_file(args.config.resolve())
    identity = {"p0_checkpoint_sha256": p0_hash, "tokenizer_sha256": tokenizer_hash, "input_hashes": input_hashes, "config_sha256": config_hash, "script_sha256": code_hash}
    atomic_json(status_path, {"status": "running", "arm": args.arm, "identity": identity})
    pilot.set_seed(42); torch.set_float32_matmul_precision("high"); device = pilot.device_for_run()
    p0_state = pilot.load_checkpoint(p0_checkpoint); tokenizer = pilot.Tokenizer.from_file(str(tokenizer_path))
    static = pilot.build_static(p0_config, tokenizer.get_vocab_size()).to(device); static.token = pilot.EncoderBranch(static.token); static.char = pilot.EncoderBranch(static.char); static.load_state_dict(p0_state["static_model"], strict=True); static.eval()
    for parameter in static.parameters(): parameter.requires_grad = False
    torch.manual_seed(42); adapter = pilot.FusionAdapter(int(config["model"]["d_model"])).to(device); alpha = torch.nn.Parameter(torch.zeros((), device=device))
    optimizer = torch.optim.Adam([*adapter.parameters(), alpha], lr=float(config["training"]["learning_rate"]))
    state = pilot.load_checkpoint(checkpoint_path) if args.resume and checkpoint_path.is_file() else None
    start_step = 0; G = torch.zeros(2, device=device); V = torch.zeros(2, device=device); lambdas = torch.zeros(2, device=device); counters = {"empty_error_negative": 0, "empty_error_positive": 0, "empty_correct_negative": 0, "empty_correct_positive": 0, "positive_violation_negative": 0, "positive_violation_positive": 0, "skipped": 0}
    if state is not None:
        if state.get("identity") != identity: raise ValueError("恢复身份哈希不匹配")
        adapter.load_state_dict(state["adapter"]); alpha.data.copy_(state["alpha"]); optimizer.load_state_dict(state["optimizer"]); G, V, lambdas, start_step, counters = state["G"].to(device), state["V"].to(device), state["lambdas"].to(device), int(state["step"]), state["counters"]; restore_rng(state["rng_state"])
    started = time.monotonic(); trace: list[dict[str, Any]] = []
    for step, (domains, labels) in enumerate(pilot.iter_labeled_batches(parts, int(config["training"]["batch_size"]), int(config["seed"]))):
        if step < start_step: continue
        if step >= int(config["training"]["steps"]): break
        token_ids = pilot.encode_subword(domains, tokenizer, int(p0_config["model"]["max_len_token"]), device); char_ids = pilot.encode_char(domains, int(p0_config["model"]["max_len_char"]), device); labels = labels.to(device)
        with torch.inference_mode(), torch.autocast(device_type=device.type, enabled=False): token_feature, char_feature = static.encode_branches(token_ids, char_ids); baseline_logits = static.static_logits(token_feature, char_feature)
        with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=device.type == "cuda" and bool(config["training"]["cuda_bf16_autocast"])): dynamic, diagnostics = pilot.fusion_logits(token_feature, char_feature, baseline_logits, "conservative_correction", adapter)
        candidate = baseline_logits + alpha * (dynamic.float() - baseline_logits); F, values, empty = ratio_terms(score(candidate), score(baseline_logits), labels, threshold)
        h_values = [values["h_negative"], values["h_positive"]]; g = torch.stack([(value - 1) if value is not None else torch.zeros((), device=device) for value in h_values])
        for index, name in enumerate(("negative", "positive")):
            counters[f"empty_error_{name}"] += empty[f"error_{name}"]; counters[f"empty_correct_{name}"] += empty[f"correct_{name}"]; counters[f"positive_violation_{name}"] += int(g[index].detach().cpu() > 0)
        if F is None:
            counters["skipped"] += 1; primal = torch.dot(lambdas, g) if any(value is not None for value in h_values) else None
        elif args.arm == "scale_free_primal_dual": primal = F + torch.dot(lambdas, g)
        else: primal = F + torch.relu(g).sum()
        if primal is None: continue
        stats = vector_stats(F if F is not None else primal, [value for value in h_values if value is not None], [*adapter.parameters(), alpha])
        optimizer.zero_grad(set_to_none=True); primal.float().backward(); optimizer.step(); alpha.data.clamp_(0.0, 1.0)
        if args.arm == "scale_free_primal_dual":
            G = G + g.detach(); V = V + g.detach().square(); lambdas = torch.where(V > 0, torch.relu(G) / torch.sqrt(V), torch.zeros_like(V))
        if not torch.isfinite(primal) or not torch.isfinite(alpha) or not torch.isfinite(lambdas).all(): raise FloatingPointError("原始或对偶状态非有限")
        trace.append({"step": step + 1, "F": tensor_value(F), "E_negative": tensor_value(values["e_negative"]), "E_positive": tensor_value(values["e_positive"]), "H_negative": tensor_value(values["h_negative"]), "H_positive": tensor_value(values["h_positive"]), "g_negative": float(g[0].detach().cpu()), "g_positive": float(g[1].detach().cpu()), "G": G.detach().cpu().tolist(), "V": V.detach().cpu().tolist(), "lambda": lambdas.detach().cpu().tolist(), "alpha": float(alpha.detach().cpu()), "gate_entropy": float((-(diagnostics["branch_weights"] * diagnostics["branch_weights"].clamp_min(1e-12).log()).sum(dim=1).mean()).detach().cpu()), "residual": float(diagnostics["residual"].abs().mean().detach().cpu()), **stats})
        save_checkpoint(checkpoint_path, {"identity": identity, "adapter": adapter.state_dict(), "alpha": alpha.detach().cpu(), "optimizer": optimizer.state_dict(), "G": G.detach().cpu(), "V": V.detach().cpu(), "lambdas": lambdas.detach().cpu(), "step": step + 1, "samples": (step + 1) * int(config["training"]["batch_size"]), "counters": counters, "rng_state": capture_rng()})
    validation_parts = pilot.input_parts(p0_config, root, "validation")
    validation = validate(static, adapter, alpha, tokenizer, validation_parts, p0_config, config, threshold, device)
    hinge_path = args.run_dir.resolve() / "unit_hinge_control" / "result.json"; hinge = json.loads(hinge_path.read_text(encoding="utf-8")) if args.arm == "scale_free_primal_dual" and hinge_path.is_file() else None
    status, reasons = support_status(validation, float(alpha.detach().cpu()), hinge)
    result = {"schema_version": SCHEMA, "status": status, "arm": args.arm, "screening_only": True, "identity": identity, "source_threshold": threshold_source, "steps": len(trace), "samples": len(trace) * int(config["training"]["batch_size"]), "trace": trace, "counters": counters, "validation": validation, "decision_reasons": reasons, "runtime": {"wall_seconds": time.monotonic() - started, "throughput_examples_per_second": (len(trace) * int(config["training"]["batch_size"])) / max(time.monotonic() - started, 1e-12), "resource_contention": bool(config["training"]["resource_contention"]), "resources": pilot.resource_receipt()}, "interpretation_boundary": config["interpretation_boundary"]}
    atomic_json(run_dir / "result.json", result); atomic_json(status_path, {"status": status, "arm": args.arm, "result": "result.json", "checkpoint_sha256": sha256_file(checkpoint_path), "identity": identity}); return 0


if __name__ == "__main__":
    raise SystemExit(main())
