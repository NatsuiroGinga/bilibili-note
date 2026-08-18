"""TQH-C2 严格分组跨成员泛化 Q0 总控入口。"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from flow_probe import tqhc2_strict_crossmember_data as data
from flow_probe import tqhc2_strict_crossmember_models as models


class StrictCrossMemberQ0Error(RuntimeError):
    """表示 Q0 阶段顺序、冻结或评价合同被破坏。"""


EVIDENCE = {
    "screening_only": True,
    "formal_paper_evidence": False,
    "formal_final_role_created": False,
    "final_accessed": False,
}
PROTOCOLS = {
    "ab_to_c": {"display_name": "A+B→C", "source_members": ("A", "B")},
    "abd_to_c": {"display_name": "A+B+D→C", "source_members": ("A", "B", "D")},
}
IDENTITIES = (
    ("T0", "XGBoost强树锚"),
    ("B", "容量匹配残差基座"),
    ("M1", "1%锚带残差排序"),
    ("M2", "留一成员经验准入与强树回退"),
    ("M1_M2", "1%锚带残差排序与留一成员经验准入完整方法"),
    ("RND", "等准入数量确定性随机门"),
    ("SHUF", "捕获级打乱成员标签对照"),
    ("OPEN", "完整残差始终启用对照"),
    ("HGB", "HistGradientBoosting强树基线"),
    ("PAIRWISE_PAUC", models.PAIRWISE_DISPLAY_NAME),
    ("CORAL", "仅源成员Deep CORAL"),
    ("DANN", "仅源成员DANN"),
    ("GROUPDRO", "源成员GroupDRO"),
    ("VREX", "源成员风险方差V-REx"),
    ("CVAR", "固定最坏10%样本损失条件风险价值"),
    ("ENSEMBLE", "普通深度集成"),
    ("SELECTIVENET", "具有预测头选择头辅助头的SelectiveNet"),
)
IDENTITY_KEYS = tuple(key for key, _name in IDENTITIES)
CODE_FILENAMES = (
    "tqhc2_strict_crossmember_data.py",
    "tqhc2_strict_crossmember_models.py",
    "tqhc2_strict_crossmember_q0.py",
)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(partial, path)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise StrictCrossMemberQ0Error(f"无法读取 JSON：{path}：{error}") from error
    if not isinstance(value, dict):
        raise StrictCrossMemberQ0Error(f"JSON 顶层必须是对象：{path}")
    return value


def _sha256(path: Path) -> str:
    return data.sha256_file(path)


def _resolve(config_path: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (config_path.parent / path).resolve()


def _load_config(path: Path) -> dict[str, Any]:
    config = _read_json(path)
    required = {
        "schema_version",
        "contract_version",
        "run_id",
        "seed",
        "feature_fields",
        "protocols",
        "identities",
        "paths",
        "resources",
        "training",
        "xgboost",
        "hist_gradient_boosting",
        "pairwise_pauc_approximation",
        "neural_baselines",
        "candidate",
        "decision_thresholds",
        "swanlab",
        "evidence",
    }
    missing = required - set(config)
    if missing:
        raise StrictCrossMemberQ0Error(f"配置缺少字段：{sorted(missing)}")
    identities = config["identities"]
    expected_identity_rows = [
        {"key": key, "display_name": display_name} for key, display_name in IDENTITIES
    ]
    expected_protocols = {
        key: {
            "display_name": value["display_name"],
            "source_members": list(value["source_members"]),
        }
        for key, value in PROTOCOLS.items()
    }
    pairwise = config["pairwise_pauc_approximation"]
    candidate = config["candidate"]
    training = config["training"]
    if (
        config["schema_version"] != "tqhc2-strict-crossmember-q0-config-v1"
        or config["contract_version"] != "tqhc2-strict-crossmember-q0-v1"
        or config["seed"] != 42
        or tuple(config["feature_fields"]) != data.FEATURE_FIELDS
        or config["protocols"] != expected_protocols
        or identities != expected_identity_rows
        or config["evidence"] != EVIDENCE
        or pairwise["display_name"] != models.PAIRWISE_DISPLAY_NAME
        or pairwise["implementation_fidelity"] != models.PAIRWISE_FIDELITY
        or pairwise["beta"] != 0.01
        or candidate["beta"] != 0.01
        or candidate["lambda_rank"] != 1.0
        or candidate["lambda_delta"] != 0.001
        or candidate["temperature"] != 1.0
        or candidate["delta_odds_bound"] != 10.0
        or candidate["maximum_pairs_per_batch"] != 4096
        or candidate["u_ext_limit"] != 0.005
        or candidate["maximum_delta_e_limit"] != 0.005
        or candidate["kappa_quantile"] != 0.75
        or training["batch_size"] != 256
        or max(training["epoch_candidates"]) > 100
        or training["optimizer"] != "AdamW"
        or training["learning_rate"] != 0.001
        or training["weight_decay"] != 0.0001
        or config["resources"]["maximum_identity_concurrency"] not in {1, 2}
    ):
        raise StrictCrossMemberQ0Error("配置身份、机制、预算或证据合同漂移")
    if config["resources"]["maximum_identity_concurrency"] != 1:
        raise StrictCrossMemberQ0Error("本冻结配置默认串行；并发必须在新冻结配置中明确证明资源")
    return config


def _paths(config_path: Path, config: Mapping[str, Any]) -> dict[str, Path]:
    return {
        key: _resolve(config_path, str(value)) for key, value in config["paths"].items()
    }


def _code_hashes() -> dict[str, str]:
    module_root = Path(__file__).resolve().parent
    return {filename: _sha256(module_root / filename) for filename in CODE_FILENAMES}


def _git_summary(project_root: Path) -> dict[str, Any]:
    def run(*args: str) -> str:
        completed = subprocess.run(
            ["git", *args], cwd=project_root, text=True, capture_output=True, check=False
        )
        return completed.stdout.strip() if completed.returncode == 0 else "unavailable"

    status = run("status", "--short")
    return {
        "commit": run("rev-parse", "HEAD"),
        "worktree_dirty": bool(status and status != "unavailable"),
        "worktree_status_sha256": hashlib.sha256(status.encode()).hexdigest(),
    }


def _status(root: Path, state: str, stage: str, **extra: Any) -> None:
    _write_json(
        root / "status.json",
        {
            "schema_version": "tqhc2-strict-crossmember-q0-status-v1",
            "state": state,
            "stage": stage,
            "updated_at_epoch": time.time(),
            **EVIDENCE,
            **extra,
        },
    )
    print(
        json.dumps(
            {"event": "stage_status", "state": state, "stage": stage, **extra},
            ensure_ascii=False,
            sort_keys=True,
        ),
        flush=True,
    )


def _prepare_root(config_path: Path, config: Mapping[str, Any], paths: Mapping[str, Path]) -> Path:
    root = paths["output_root"]
    if root.exists():
        existing = root / "config.json"
        if not existing.is_file() or _sha256(existing) != _sha256(config_path):
            raise StrictCrossMemberQ0Error("运行根已存在但配置哈希不同，拒绝覆盖或恢复")
    else:
        root.mkdir(parents=True)
        shutil.copyfile(config_path, root / "config.json")
    return root


def audit(config_path: Path) -> dict[str, Any]:
    config = _load_config(config_path)
    paths = _paths(config_path, config)
    root = _prepare_root(config_path, config, paths)
    _status(root, "running", "audit")
    receipt = data.audit_inputs(paths["raw_root"])
    _write_json(root / "input_receipt.json", {**receipt, **EVIDENCE, "C_read_count": 0})
    dependency_names = (
        "joblib",
        "numpy",
        "pandas",
        "pyarrow",
        "scikit-learn",
        "swanlab",
        "torch",
        "xgboost",
    )
    dependencies = {}
    for name in dependency_names:
        try:
            dependencies[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as error:
            raise StrictCrossMemberQ0Error(f"冻结依赖不可用：{name}") from error
    disk = shutil.disk_usage(paths["project_root"])
    if disk.free < int(config["resources"]["minimum_free_disk_gib"] * 1024**3):
        raise StrictCrossMemberQ0Error("可用磁盘低于冻结资源门")
    environment = {
        "schema_version": "tqhc2-strict-crossmember-environment-v1",
        "python": sys.version,
        "platform": platform.platform(),
        "dependencies": dependencies,
        "git": _git_summary(paths["project_root"]),
        "code_sha256": _code_hashes(),
        "config_sha256": _sha256(config_path),
        "disk_free_gib": disk.free / 1024**3,
        "command_module": "flow_probe.tqhc2_strict_crossmember_q0",
        "C_read_count": 0,
        **EVIDENCE,
    }
    _write_json(root / "environment.json", environment)
    _status(root, "audited", "audit-complete", C_read_count=0)
    return environment


def _collect_source(loader: data.StrictCrossMemberLoader) -> list[data.CaptureBatch]:
    captures = []
    for role in ("source_train", "source_calibration"):
        captures.extend(loader.source_captures(data.SOURCE_MEMBERS, role))
    if loader.c_read_count != 0 or len(captures) != 36:
        raise StrictCrossMemberQ0Error("源侧必须读取 A/B/D 的 36 个捕获且 C_read_count=0")
    return captures


def _select_grid(
    candidates: Sequence[Mapping[str, Any]],
    folds: np.ndarray,
    train: Mapping[str, np.ndarray],
    fit_predict: Callable[[Mapping[str, Any], np.ndarray, np.ndarray], np.ndarray],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not 1 <= len(candidates) <= 4:
        raise StrictCrossMemberQ0Error("每个模型族只能比较 1 至 4 个预注册配置")
    summaries = []
    for candidate_index, candidate in enumerate(candidates):
        metrics = []
        started = time.perf_counter()
        for fold in range(4):
            fit_mask = folds != fold
            validation_mask = folds == fold
            score = fit_predict(candidate, fit_mask, validation_mask)
            metrics.append(
                models.normalized_partial_auc(train["y"][validation_mask], score)
            )
        summaries.append(
            {
                "candidate_index": candidate_index,
                "params": dict(candidate),
                "fold_npauc_0_01": metrics,
                "mean_npauc_0_01": float(np.mean(metrics)),
                "selection_seconds": time.perf_counter() - started,
            }
        )
    selected = max(
        summaries,
        key=lambda item: (
            item["mean_npauc_0_01"],
            -sum(
                float(value)
                for value in item["params"].values()
                if isinstance(value, int | float)
            ),
            -item["selection_seconds"],
        ),
    )
    return dict(selected["params"]), summaries


def _select_xgb(
    config: Mapping[str, Any], train: Mapping[str, np.ndarray]
) -> tuple[Any, dict[str, Any]]:
    folds = train["fold"]

    def fit_predict(
        candidate: Mapping[str, Any], fit_mask: np.ndarray, validation_mask: np.ndarray
    ) -> np.ndarray:
        params = {**config["xgboost"]["fixed"], **candidate}
        model = models.fit_xgboost(train["x"][fit_mask], train["y"][fit_mask], params, 42)
        return models.predict_tree_score(model, train["x"][validation_mask])

    selected, summaries = _select_grid(config["xgboost"]["grid"], folds, train, fit_predict)
    params = {**config["xgboost"]["fixed"], **selected}
    final_model = models.fit_xgboost(train["x"], train["y"], params, 42)
    return final_model, {"selected": params, "candidates": summaries}


def _select_hgb(
    config: Mapping[str, Any], train: Mapping[str, np.ndarray]
) -> tuple[Any, dict[str, Any]]:
    folds = train["fold"]

    def fit_predict(
        candidate: Mapping[str, Any], fit_mask: np.ndarray, validation_mask: np.ndarray
    ) -> np.ndarray:
        params = {**config["hist_gradient_boosting"]["fixed"], **candidate}
        model = models.fit_hist_gradient_boosting(
            train["x"][fit_mask], train["y"][fit_mask], params, 42
        )
        return models.predict_tree_score(model, train["x"][validation_mask])

    selected, summaries = _select_grid(
        config["hist_gradient_boosting"]["grid"], folds, train, fit_predict
    )
    params = {**config["hist_gradient_boosting"]["fixed"], **selected}
    return models.fit_hist_gradient_boosting(train["x"], train["y"], params, 42), {
        "selected": params,
        "candidates": summaries,
    }


def _select_pairwise(
    config: Mapping[str, Any], train: Mapping[str, np.ndarray], device: Any
) -> tuple[dict[str, Any], dict[str, Any]]:
    folds = train["fold"]
    pair_config = config["pairwise_pauc_approximation"]

    def fit_predict(
        candidate: Mapping[str, Any], fit_mask: np.ndarray, validation_mask: np.ndarray
    ) -> np.ndarray:
        payload, _receipt = models.train_pairwise_linear(
            train["x_scaled"][fit_mask],
            train["y"][fit_mask],
            train["member"][fit_mask],
            c_value=float(candidate["c_value"]),
            epochs=int(pair_config["epochs"]),
            seed=42,
            device=device,
        )
        return models.predict_pairwise(payload, train["x_scaled"][validation_mask], device)

    candidates = [{"c_value": value} for value in pair_config["c_grid"]]
    selected, summaries = _select_grid(candidates, folds, train, fit_predict)
    payload, receipt = models.train_pairwise_linear(
        train["x_scaled"],
        train["y"],
        train["member"],
        c_value=float(selected["c_value"]),
        epochs=int(pair_config["epochs"]),
        seed=42,
        device=device,
    )
    return payload, {**receipt, "candidates": summaries}


def _select_neural(
    config: Mapping[str, Any], train: Mapping[str, np.ndarray], objective: str, device: Any
) -> tuple[dict[str, Any], dict[str, Any]]:
    block = config["neural_baselines"][objective]
    candidates = block["grid"]
    folds = train["fold"]
    common = config["training"]

    def fit_predict(
        candidate: Mapping[str, Any], fit_mask: np.ndarray, validation_mask: np.ndarray
    ) -> np.ndarray:
        payload, _receipt = models.train_classifier(
            train["x_scaled"][fit_mask],
            train["y"][fit_mask],
            train["member"][fit_mask],
            train["capture"][fit_mask],
            objective=objective,
            objective_weight=float(candidate["objective_weight"]),
            epochs=int(candidate["epochs"]),
            batch_size=int(common["batch_size"]),
            learning_rate=float(candidate.get("learning_rate", common["learning_rate"])),
            weight_decay=float(common["weight_decay"]),
            seed=42,
            device=device,
            selective_auxiliary_weight=float(candidate.get("auxiliary_weight", 0.5)),
            dann_schedule=bool(candidate.get("progressive_schedule", False)),
        )
        score, _selection = models.predict_classifier(
            payload, train["x_scaled"][validation_mask], device
        )
        return score

    selected, summaries = _select_grid(candidates, folds, train, fit_predict)
    if objective == "coral" and float(selected["objective_weight"]) == 0.0:
        nonzero = [
            item for item in summaries if float(item["params"]["objective_weight"]) > 0.0
        ]
        selected = dict(max(nonzero, key=lambda item: item["mean_npauc_0_01"])["params"])
    payload, receipt = models.train_classifier(
        train["x_scaled"],
        train["y"],
        train["member"],
        train["capture"],
        objective=objective,
        objective_weight=float(selected["objective_weight"]),
        epochs=int(selected["epochs"]),
        batch_size=int(common["batch_size"]),
        learning_rate=float(selected.get("learning_rate", common["learning_rate"])),
        weight_decay=float(common["weight_decay"]),
        seed=42,
        device=device,
        selective_auxiliary_weight=float(selected.get("auxiliary_weight", 0.5)),
        dann_schedule=bool(selected.get("progressive_schedule", False)),
    )
    return payload, {**receipt, "selected": selected, "candidates": summaries}


def _select_residual_epochs(
    config: Mapping[str, Any], train: Mapping[str, np.ndarray], anchor: np.ndarray, device: Any
) -> tuple[int, list[dict[str, Any]]]:
    candidates = [{"epochs": int(value)} for value in config["training"]["epoch_candidates"]]
    folds = train["fold"]
    common = config["training"]

    def fit_predict(
        candidate: Mapping[str, Any], fit_mask: np.ndarray, validation_mask: np.ndarray
    ) -> np.ndarray:
        state, _receipt = models.train_residual_expert(
            train["x_scaled"][fit_mask],
            train["y"][fit_mask],
            train["member"][fit_mask],
            train["capture"][fit_mask],
            anchor[fit_mask],
            visible_members=tuple(
                sorted(str(value) for value in np.unique(train["member"][fit_mask]))
            ),
            use_m1=False,
            epochs=int(candidate["epochs"]),
            batch_size=int(common["batch_size"]),
            learning_rate=float(common["learning_rate"]),
            weight_decay=float(common["weight_decay"]),
            seed=42,
            device=device,
        )
        return anchor[validation_mask] + models.predict_residual(
            state, train["x_scaled"][validation_mask], device
        )

    selected, summaries = _select_grid(candidates, folds, train, fit_predict)
    return int(selected["epochs"]), summaries


def _shuffled_members(captures: np.ndarray, members: np.ndarray, seed: int) -> np.ndarray:
    unique_captures = sorted(str(value) for value in np.unique(captures))
    original = [str(members[np.flatnonzero(captures == capture)[0]]) for capture in unique_captures]
    shuffled = np.asarray(original, dtype=object)
    np.random.default_rng(seed).shuffle(shuffled)
    lookup = dict(zip(unique_captures, shuffled, strict=True))
    result = np.asarray([lookup[str(capture)] for capture in captures], dtype=object)
    if sorted(original) != sorted(str(value) for value in shuffled):
        raise StrictCrossMemberQ0Error("SHUF 未保持捕获级组数和组规模")
    return result


def _train_expert_family(
    config: Mapping[str, Any],
    train: Mapping[str, np.ndarray],
    anchor: np.ndarray,
    source_members: Sequence[str],
    *,
    leave_one_out: bool,
    use_m1: bool,
    epochs: int,
    device: Any,
    member_override: np.ndarray | None = None,
    seed_offset: int = 0,
) -> tuple[list[dict[str, np.ndarray]], list[dict[str, Any]]]:
    common = config["training"]
    grouping = train["member"] if member_override is None else member_override
    states = []
    receipts = []
    for index, held_out in enumerate(source_members):
        visible = (
            tuple(member for member in source_members if member != held_out)
            if leave_one_out
            else tuple(source_members)
        )
        state, receipt = models.train_residual_expert(
            train["x_scaled"],
            train["y"],
            grouping,
            train["capture"],
            anchor,
            visible_members=visible,
            use_m1=use_m1,
            epochs=epochs,
            batch_size=int(common["batch_size"]),
            learning_rate=float(common["learning_rate"]),
            weight_decay=float(common["weight_decay"]),
            seed=42 + seed_offset + index + 1,
            device=device,
        )
        receipt["held_out_member"] = held_out if leave_one_out else None
        states.append(state)
        receipts.append(receipt)
    return states, receipts


def _expert_matrix(
    states: Sequence[Mapping[str, np.ndarray]], x: np.ndarray, device: Any
) -> np.ndarray:
    return np.column_stack([models.predict_residual(state, x, device) for state in states])


def _tail_replacement_rates(
    labels: np.ndarray,
    members: np.ndarray,
    anchor_score: np.ndarray,
    candidate_score: np.ndarray,
    source_members: Sequence[str],
) -> dict[str, float]:
    rates = {}
    for member in source_members:
        negative = np.flatnonzero((members == member) & (labels == 0))
        tail_size = max(1, int(math.ceil(0.01 * len(negative))))
        anchor_tail = set(negative[np.argsort(-anchor_score[negative], kind="stable")[:tail_size]])
        candidate_tail = set(
            negative[np.argsort(-candidate_score[negative], kind="stable")[:tail_size]]
        )
        rates[member] = 1.0 - len(anchor_tail & candidate_tail) / tail_size
    return rates


def _score_artifact(
    artifact: Mapping[str, Any],
    x_raw: np.ndarray,
    *,
    uids: np.ndarray | None,
    capture_key: str | None,
    device: Any,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    scaler = models.RobustScaler(
        median=np.asarray(artifact["scaler"]["median"], dtype=np.float32),
        iqr=np.asarray(artifact["scaler"]["iqr"], dtype=np.float32),
    )
    x_scaled = scaler.transform(x_raw)
    anchor = models.predict_tree_score(artifact["anchor"], x_raw)
    scores: dict[str, np.ndarray] = {"T0": anchor}
    diagnostics: dict[str, np.ndarray] = {}
    for key in ("B", "M1"):
        matrix = _expert_matrix(artifact["experts"][key], x_scaled, device)
        scores[key] = anchor + matrix.mean(axis=1)
    for key in ("M2", "M1_M2", "SHUF"):
        matrix = _expert_matrix(artifact["experts"][key], x_scaled, device)
        gate = artifact["gates"][key]
        score, admission, disagreement = models.gate_from_experts(
            anchor,
            matrix,
            global_gate=bool(gate["global_gate"]),
            kappa=float(gate["kappa"]),
        )
        scores[key] = score
        diagnostics[f"{key}_admission"] = admission
        diagnostics[f"{key}_disagreement"] = disagreement
        if key == "M1_M2":
            scores["OPEN"] = anchor + matrix.mean(axis=1)
            if uids is not None and capture_key is not None:
                random_admission = models.deterministic_random_admission(
                    uids,
                    capture_key,
                    int(np.count_nonzero(admission)),
                    int(artifact["seed"]),
                )
                random_score = anchor.copy()
                random_score[random_admission] += matrix.mean(axis=1)[random_admission]
                scores["RND"] = random_score
                diagnostics["RND_admission"] = random_admission
            else:
                scores["RND"] = score.copy()
                diagnostics["RND_admission"] = admission.copy()
    scores["HGB"] = models.predict_tree_score(artifact["hgb"], x_raw)
    scores["PAIRWISE_PAUC"] = models.predict_pairwise(artifact["pairwise"], x_scaled, device)
    for key, objective in (
        ("CORAL", "coral"),
        ("DANN", "dann"),
        ("GROUPDRO", "groupdro"),
        ("VREX", "vrex"),
        ("CVAR", "cvar"),
    ):
        scores[key], _selection = models.predict_classifier(
            artifact["neural"][objective], x_scaled, device
        )
    ensemble_scores = [
        models.predict_classifier(payload, x_scaled, device)[0]
        for payload in artifact["neural"]["ensemble"]
    ]
    scores["ENSEMBLE"] = np.mean(np.column_stack(ensemble_scores), axis=1)
    scores["SELECTIVENET"], selection = models.predict_classifier(
        artifact["neural"]["selective"], x_scaled, device
    )
    if selection is None:
        raise StrictCrossMemberQ0Error("SelectiveNet 缺少真实选择头输出")
    diagnostics["SELECTIVENET_selection"] = selection
    missing = set(IDENTITY_KEYS) - set(scores)
    if missing:
        raise StrictCrossMemberQ0Error(f"评分缺少身份：{sorted(missing)}")
    for key, score in scores.items():
        if score.shape != (len(x_raw),) or not np.isfinite(score).all():
            raise StrictCrossMemberQ0Error(f"身份 {key} 分数形状错误或非有限")
    return scores, diagnostics


def _train_protocol(
    config: Mapping[str, Any],
    captures: Sequence[data.CaptureBatch],
    protocol_key: str,
    output_root: Path,
    device: Any,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_members = PROTOCOLS[protocol_key]["source_members"]
    selected = [capture for capture in captures if capture.descriptor.member in source_members]
    train_captures = [
        capture for capture in selected if capture.descriptor.role == "source_train"
    ]
    calibration_captures = [
        capture for capture in selected if capture.descriptor.role == "source_calibration"
    ]
    data.assert_source_support(selected, source_members)
    train = data.concatenate(train_captures)
    calibration = data.concatenate(calibration_captures)
    scaler = models.RobustScaler.fit(train["x"])
    train["x_scaled"] = scaler.transform(train["x"])
    calibration["x_scaled"] = scaler.transform(calibration["x"])
    anchor_model, xgb_receipt = _select_xgb(config, train)
    anchor_train = models.predict_tree_score(anchor_model, train["x"])
    anchor_calibration = models.predict_tree_score(anchor_model, calibration["x"])
    epochs, residual_cv = _select_residual_epochs(config, train, anchor_train, device)
    experts: dict[str, Any] = {}
    expert_receipts: dict[str, Any] = {}
    experts["B"], expert_receipts["B"] = _train_expert_family(
        config,
        train,
        anchor_train,
        source_members,
        leave_one_out=False,
        use_m1=False,
        epochs=epochs,
        device=device,
    )
    experts["M1"], expert_receipts["M1"] = _train_expert_family(
        config,
        train,
        anchor_train,
        source_members,
        leave_one_out=False,
        use_m1=True,
        epochs=epochs,
        device=device,
        seed_offset=100,
    )
    experts["M2"], expert_receipts["M2"] = _train_expert_family(
        config,
        train,
        anchor_train,
        source_members,
        leave_one_out=True,
        use_m1=False,
        epochs=epochs,
        device=device,
        seed_offset=200,
    )
    experts["M1_M2"], expert_receipts["M1_M2"] = _train_expert_family(
        config,
        train,
        anchor_train,
        source_members,
        leave_one_out=True,
        use_m1=True,
        epochs=epochs,
        device=device,
        seed_offset=300,
    )
    shuffled_train_member = _shuffled_members(train["capture"], train["member"], 442)
    experts["SHUF"], expert_receipts["SHUF"] = _train_expert_family(
        config,
        train,
        anchor_train,
        source_members,
        leave_one_out=True,
        use_m1=True,
        epochs=epochs,
        device=device,
        member_override=shuffled_train_member,
        seed_offset=400,
    )
    hgb, hgb_receipt = _select_hgb(config, train)
    pairwise, pairwise_receipt = _select_pairwise(config, train, device)
    neural: dict[str, Any] = {}
    neural_receipts: dict[str, Any] = {}
    for objective in ("coral", "dann", "groupdro", "vrex", "cvar", "selective"):
        neural[objective], neural_receipts[objective] = _select_neural(
            config, train, objective, device
        )
    ensemble_payloads = []
    ensemble_receipts = []
    ensemble_count = len(source_members)
    erm_config = config["neural_baselines"]["erm_ensemble"]
    for index in range(ensemble_count):
        payload, receipt = models.train_classifier(
            train["x_scaled"],
            train["y"],
            train["member"],
            train["capture"],
            objective="erm",
            objective_weight=0.0,
            epochs=epochs,
            batch_size=int(config["training"]["batch_size"]),
            learning_rate=float(config["training"]["learning_rate"]),
            weight_decay=float(config["training"]["weight_decay"]),
            seed=42 + int(erm_config["seed_offset"]) + index,
            device=device,
        )
        ensemble_payloads.append(payload)
        ensemble_receipts.append(receipt)
    neural["ensemble"] = ensemble_payloads
    neural_receipts["ensemble"] = ensemble_receipts
    artifact: dict[str, Any] = {
        "schema_version": "tqhc2-strict-crossmember-protocol-models-v1",
        "protocol_key": protocol_key,
        "source_members": list(source_members),
        "seed": 42,
        "scaler": {"median": scaler.median, "iqr": scaler.iqr},
        "anchor": anchor_model,
        "experts": experts,
        "hgb": hgb,
        "pairwise": pairwise,
        "neural": neural,
        "gates": {},
        "thresholds": {},
        "selectivenet_selection_threshold": None,
    }
    open_gates = {
        key: {"global_gate": True, "kappa": math.inf}
        for key in ("M2", "M1_M2", "SHUF")
    }
    calibration_scores, diagnostics = _score_artifact(
        {**artifact, "gates": open_gates},
        calibration["x"],
        uids=None,
        capture_key=None,
        device=device,
    )
    for key in ("M2", "M1_M2", "SHUF"):
        matrix = _expert_matrix(experts[key], calibration["x_scaled"], device)
        gate_members = calibration["member"]
        if key == "SHUF":
            gate_members = _shuffled_members(calibration["capture"], calibration["member"], 442)
        artifact["gates"][key] = models.fit_m2_gate(
            gate_members,
            calibration["y"],
            anchor_calibration,
            matrix,
            source_members,
        )
    calibration_scores, diagnostics = _score_artifact(
        artifact,
        calibration["x"],
        uids=None,
        capture_key=None,
        device=device,
    )
    for identity, score in calibration_scores.items():
        thresholds = []
        for member in source_members:
            negative = (calibration["member"] == member) & (calibration["y"] == 0)
            thresholds.append(float(np.quantile(score[negative], 0.99)))
        artifact["thresholds"][identity] = max(thresholds)
    selection = diagnostics["SELECTIVENET_selection"]
    artifact["selectivenet_selection_threshold"] = float(np.quantile(selection, 0.25))
    train_m1_matrix = _expert_matrix(experts["M1"], train["x_scaled"], device)
    train_m1_score = anchor_train + train_m1_matrix.mean(axis=1)
    tail_replacement = _tail_replacement_rates(
        train["y"], train["member"], anchor_train, train_m1_score, source_members
    )
    calibration_metrics = {
        identity: {
            "overall": models.aggregate_metrics(
                calibration["y"], score, artifact["thresholds"][identity]
            ),
            "members": {
                member: models.aggregate_metrics(
                    calibration["y"][calibration["member"] == member],
                    score[calibration["member"] == member],
                    artifact["thresholds"][identity],
                )
                for member in source_members
            },
        }
        for identity, score in calibration_scores.items()
    }
    artifact_path = output_root / protocol_key / "models.joblib"
    models.save_artifact(artifact_path, artifact)
    cv_receipt = {
        "schema_version": "tqhc2-strict-crossmember-cv-aggregate-v1",
        "protocol": protocol_key,
        "fold_count": 4,
        "selection_metric": "mean_npauc_0_01",
        "xgboost": xgb_receipt,
        "hist_gradient_boosting": hgb_receipt,
        "pairwise_pauc_approximation": pairwise_receipt,
        "residual_epoch_selection": residual_cv,
        "selected_residual_epochs": epochs,
        "neural": neural_receipts,
        "target_member_seen": False,
        "C_read_count": 0,
        **EVIDENCE,
    }
    calibration_receipt = {
        "schema_version": "tqhc2-strict-crossmember-source-calibration-v1",
        "protocol": protocol_key,
        "metrics": calibration_metrics,
        "gates": artifact["gates"],
        "thresholds": artifact["thresholds"],
        "selectivenet_selection_threshold": artifact["selectivenet_selection_threshold"],
        "expert_training": expert_receipts,
        "m1_anchor_band_replacement_rate": tail_replacement,
        "calibration_updated_model_parameters": False,
        "C_read_count": 0,
        **EVIDENCE,
    }
    return artifact, cv_receipt, calibration_receipt


def train_freeze(config_path: Path) -> dict[str, Any]:
    config = _load_config(config_path)
    paths = _paths(config_path, config)
    root = _prepare_root(config_path, config, paths)
    if not (root / "input_receipt.json").is_file():
        raise StrictCrossMemberQ0Error("必须先成功执行 audit")
    if (root / "training_freeze_receipt.json").exists():
        raise StrictCrossMemberQ0Error("冻结收据已存在，拒绝覆盖")
    _status(root, "running", "train-freeze", C_read_count=0)
    loader = data.StrictCrossMemberLoader(paths["raw_root"])
    captures = _collect_source(loader)
    split_receipt = data.aggregate_receipt(captures)
    split_receipt.update({**EVIDENCE, "C_read_count": loader.c_read_count})
    _write_json(root / "split_aggregate_receipt.json", split_receipt)
    device = models.device_from_config(str(config["training"]["device"]))
    artifacts = {}
    calibration_receipts = {}
    for protocol_key in PROTOCOLS:
        _status(root, "running", f"train-{protocol_key}", C_read_count=0)
        artifact, cv_receipt, calibration_receipt = _train_protocol(
            config, captures, protocol_key, root, device
        )
        artifacts[protocol_key] = artifact
        calibration_receipts[protocol_key] = calibration_receipt
        _write_json(root / protocol_key / "cv_aggregate.json", cv_receipt)
        _write_json(
            root / protocol_key / "source_calibration_aggregate.json", calibration_receipt
        )
    combined_calibration = {
        "schema_version": "tqhc2-strict-crossmember-source-calibration-all-v1",
        "protocols": calibration_receipts,
        "C_read_count": 0,
        **EVIDENCE,
    }
    _write_json(root / "source_calibration_aggregate.json", combined_calibration)
    identities = []
    for protocol_key in PROTOCOLS:
        artifact_path = root / protocol_key / "models.joblib"
        artifact_sha = _sha256(artifact_path)
        for key, display_name in IDENTITIES:
            fidelity = "native_implementation"
            if key == "PAIRWISE_PAUC":
                fidelity = models.PAIRWISE_FIDELITY
            identities.append(
                {
                    "protocol": protocol_key,
                    "key": key,
                    "display_name": display_name,
                    "implementation_fidelity": fidelity,
                    "model_artifact_sha256": artifact_sha,
                    "inference_definition_sha256": data.canonical_sha256(
                        {
                            "protocol": protocol_key,
                            "identity": key,
                            "threshold": artifacts[protocol_key]["thresholds"][key],
                            "gate": artifacts[protocol_key]["gates"].get(key),
                        }
                    ),
                    "status": "valid",
                }
            )
    if len(identities) != 34 or {
        (row["protocol"], row["key"]) for row in identities
    } != {(protocol, identity) for protocol in PROTOCOLS for identity in IDENTITY_KEYS}:
        raise StrictCrossMemberQ0Error("冻结身份未恰好覆盖 34 项")
    freeze_core = {
        "schema_version": "tqhc2-strict-crossmember-training-freeze-v1",
        "config_sha256": _sha256(config_path),
        "code_sha256": _code_hashes(),
        "input_receipt_sha256": _sha256(root / "input_receipt.json"),
        "split_receipt_sha256": _sha256(root / "split_aggregate_receipt.json"),
        "source_calibration_sha256": _sha256(root / "source_calibration_aggregate.json"),
        "identity_count": len(identities),
        "identities": identities,
        "decision_thresholds_sha256": data.canonical_sha256(config["decision_thresholds"]),
        "C_read_count": loader.c_read_count,
        "target_evaluation_writes_aggregate_only": True,
        "per_sample_artifacts_allowed": False,
        **EVIDENCE,
    }
    if freeze_core["C_read_count"] != 0:
        raise StrictCrossMemberQ0Error("生成冻结收据前 C_read_count 必须为 0")
    freeze = {**freeze_core, "freeze_sha256": data.canonical_sha256(freeze_core)}
    _write_json(root / "training_freeze_receipt.json", freeze)
    _status(
        root,
        "frozen",
        "train-freeze-complete",
        C_read_count=0,
        freeze_sha256=freeze["freeze_sha256"],
    )
    return freeze


def _verify_freeze(config_path: Path, root: Path) -> dict[str, Any]:
    freeze = _read_json(root / "training_freeze_receipt.json")
    if (
        freeze.get("C_read_count") != 0
        or freeze.get("identity_count") != 34
        or freeze.get("config_sha256") != _sha256(config_path)
        or freeze.get("code_sha256") != _code_hashes()
        or freeze.get("freeze_sha256")
        != data.canonical_sha256(
            {key: value for key, value in freeze.items() if key != "freeze_sha256"}
        )
    ):
        raise StrictCrossMemberQ0Error("训练冻结哈希、身份或 C 隔离断言失败")
    for row in freeze["identities"]:
        artifact_path = root / row["protocol"] / "models.joblib"
        if _sha256(artifact_path) != row["model_artifact_sha256"]:
            raise StrictCrossMemberQ0Error("冻结后模型制品发生漂移")
    return freeze


def _metric_or_none(y: np.ndarray, score: np.ndarray, threshold: float) -> dict[str, Any]:
    if set(np.unique(y)) != {0, 1}:
        predicted = score >= threshold
        return {
            "npauc_0_01": None,
            "recall_at_fpr_0_01": None,
            "row_count": len(y),
            "alert_rate": float(np.mean(predicted)),
        }
    return models.aggregate_metrics(y, score, threshold)


def evaluate_target(config_path: Path) -> dict[str, Any]:
    config = _load_config(config_path)
    paths = _paths(config_path, config)
    root = _prepare_root(config_path, config, paths)
    freeze = _verify_freeze(config_path, root)
    target_path = root / "target_development_aggregate.json"
    if target_path.exists():
        existing = _read_json(target_path)
        if existing.get("freeze_sha256") == freeze["freeze_sha256"]:
            return existing
        raise StrictCrossMemberQ0Error("目标聚合已存在且冻结哈希不同，拒绝覆盖")
    _status(
        root,
        "running",
        "evaluate-target",
        C_read_count=0,
        freeze_sha256=freeze["freeze_sha256"],
    )
    device = models.device_from_config(str(config["training"]["device"]))
    artifacts = {
        protocol: models.load_artifact(root / protocol / "models.joblib")
        for protocol in PROTOCOLS
    }
    loader = data.StrictCrossMemberLoader(paths["raw_root"])
    accumulated: dict[str, dict[str, list[np.ndarray]]] = {
        protocol: {identity: [] for identity in IDENTITY_KEYS} for protocol in PROTOCOLS
    }
    all_labels = []
    all_label_raw = []
    capture_summaries: dict[str, Any] = {}
    admission_counts: dict[str, dict[str, list[int]]] = {
        protocol: {key: [] for key in ("M2", "M1_M2", "SHUF", "RND")}
        for protocol in PROTOCOLS
    }
    for capture in loader.target_once():
        all_labels.append(capture.y)
        all_label_raw.append(capture.label_raw)
        capture_summaries[capture.descriptor.capture_key] = {}
        for protocol, artifact in artifacts.items():
            scores, diagnostics = _score_artifact(
                artifact,
                capture.x,
                uids=capture.uids,
                capture_key=capture.descriptor.capture_key,
                device=device,
            )
            protocol_summary = {}
            for identity, score in scores.items():
                accumulated[protocol][identity].append(score)
                protocol_summary[identity] = _metric_or_none(
                    capture.y, score, float(artifact["thresholds"][identity])
                )
            capture_summaries[capture.descriptor.capture_key][protocol] = protocol_summary
            for key in admission_counts[protocol]:
                admission_counts[protocol][key].append(
                    int(np.count_nonzero(diagnostics[f"{key}_admission"]))
                )
    if loader.c_read_count != 1:
        raise StrictCrossMemberQ0Error("C 目标评价必须在一个进程中恰好完成一次")
    y = np.concatenate(all_labels)
    label_raw = np.concatenate(all_label_raw)
    protocol_results = {}
    for protocol, artifact in artifacts.items():
        identity_results = {}
        for identity in IDENTITY_KEYS:
            score = np.concatenate(accumulated[protocol][identity])
            threshold = float(artifact["thresholds"][identity])
            subtype = {}
            for label in ("benign", "benign_external", "malicious_recon"):
                mask = label_raw == label
                subtype[label] = {
                    "row_count": int(np.count_nonzero(mask)),
                    "alert_rate": (
                        float(np.mean(score[mask] >= threshold)) if np.any(mask) else None
                    ),
                }
            identity_results[identity] = {
                "overall": models.aggregate_metrics(y, score, threshold),
                "negative_subtypes": subtype,
            }
        protocol_results[protocol] = {
            "identities": identity_results,
            "admission_counts_by_capture": admission_counts[protocol],
            "admission_rate": {
                key: sum(values) / len(y) for key, values in admission_counts[protocol].items()
            },
        }
    target = {
        "schema_version": "tqhc2-strict-crossmember-target-development-v1",
        "freeze_sha256": freeze["freeze_sha256"],
        "C_read_count": loader.c_read_count,
        "target_member": "C",
        "capture_count": len(capture_summaries),
        "row_count": len(y),
        "protocols": protocol_results,
        "captures": capture_summaries,
        "per_sample_outputs_persisted": False,
        **EVIDENCE,
    }
    _write_json(target_path, target)
    del all_labels, all_label_raw, accumulated, y, label_raw
    source_calibration = _read_json(root / "source_calibration_aggregate.json")
    decision = decide(config, target, source_calibration)
    _write_json(root / "decision.json", decision)
    _status(
        root,
        "evaluated",
        "decision-complete",
        C_read_count=1,
        freeze_sha256=freeze["freeze_sha256"],
    )
    return target


def _capture_delta(target: Mapping[str, Any], protocol: str, left: str, right: str) -> list[float]:
    values = []
    for capture in sorted(target["captures"]):
        rows = target["captures"][capture][protocol]
        left_value = rows[left]["npauc_0_01"]
        right_value = rows[right]["npauc_0_01"]
        if left_value is not None and right_value is not None:
            values.append(float(left_value) - float(right_value))
    return values


def decide(
    config: Mapping[str, Any],
    target: Mapping[str, Any],
    source_calibration: Mapping[str, Any],
) -> dict[str, Any]:
    thresholds = config["decision_thresholds"]
    protocol_decisions = {}
    strong_baselines = (
        "HGB",
        "PAIRWISE_PAUC",
        "CORAL",
        "DANN",
        "GROUPDRO",
        "VREX",
        "CVAR",
        "ENSEMBLE",
        "SELECTIVENET",
    )
    for protocol in PROTOCOLS:
        results = target["protocols"][protocol]["identities"]
        metric = {key: value["overall"] for key, value in results.items()}
        source = source_calibration["protocols"][protocol]
        source_metrics = source["metrics"]
        source_members = PROTOCOLS[protocol]["source_members"]
        m1_capture_delta = _capture_delta(target, protocol, "M1", "B")
        full_capture_delta = _capture_delta(target, protocol, "M1_M2", "B")
        m1_source_nonharmful = all(
            source_metrics["M1"]["members"][member]["npauc_0_01"]
            - source_metrics["B"]["members"][member]["npauc_0_01"]
            >= -0.01
            for member in source_members
        )
        m1_replacement_valid = max(source["m1_anchor_band_replacement_rate"].values()) <= 0.50
        m1_saturation_valid = max(
            receipt["residual_saturation_rate"]
            for receipt in source["expert_training"]["M1"]
        ) <= 0.20
        m1 = (
            metric["M1"]["npauc_0_01"] - metric["B"]["npauc_0_01"] >= 0.02
            and metric["M1"]["recall_at_fpr_0_01"] - metric["B"]["recall_at_fpr_0_01"] >= 0.05
            and sum(value >= 0.0 for value in m1_capture_delta) >= 9
            and len(m1_capture_delta) == 12
            and float(np.median(m1_capture_delta)) > 0.0
            and m1_source_nonharmful
            and m1_replacement_valid
            and m1_saturation_valid
        )
        admission_rate = target["protocols"][protocol]["admission_rate"]["M1_M2"]
        open_excess = max(metric["OPEN"]["false_positive_rate"] - 0.01, 0.0)
        reduced_excess = open_excess - max(metric["M1_M2"]["false_positive_rate"] - 0.01, 0.0)
        full_gate = source["gates"]["M1_M2"]
        gate_source_valid = (
            full_gate["u_ext"] <= 0.005 and full_gate["maximum_delta_e"] <= 0.005
        )

        control_passes = {}
        for control in ("RND", "SHUF"):
            control_passes[control] = (
                metric["M1_M2"]["npauc_0_01"] - metric[control]["npauc_0_01"] >= 0.01
                or (
                    metric[control]["false_positive_rate"]
                    - metric["M1_M2"]["false_positive_rate"]
                    >= 0.005
                    and metric[control]["c2_recall"] - metric["M1_M2"]["c2_recall"]
                    <= 0.01
                )
            )

        m2 = (
            gate_source_valid
            and 0.10 <= admission_rate <= 0.90
            and open_excess >= 0.005
            and reduced_excess / open_excess >= 0.25
            and metric["OPEN"]["false_positive_rate"]
            - metric["M1_M2"]["false_positive_rate"]
            >= 0.005
            and metric["OPEN"]["c2_recall"] - metric["M1_M2"]["c2_recall"] <= 0.01
            and control_passes["RND"]
            and control_passes["SHUF"]
        )
        best_baseline_npauc = max(metric[key]["npauc_0_01"] for key in strong_baselines)
        best_baseline_recall = max(metric[key]["recall_at_fpr_0_01"] for key in strong_baselines)
        m1_gain = metric["M1"]["npauc_0_01"] - metric["B"]["npauc_0_01"]
        full_gain = metric["M1_M2"]["npauc_0_01"] - metric["B"]["npauc_0_01"]
        keeps_m1 = full_gain >= 0.90 * m1_gain
        exceeds_m2 = metric["M1_M2"]["npauc_0_01"] - metric["M2"]["npauc_0_01"] >= 0.01
        baseline_gain_valid = (
            (
                metric["M1_M2"]["npauc_0_01"] >= best_baseline_npauc + 0.01
                and metric["M1_M2"]["recall_at_fpr_0_01"] >= best_baseline_recall - 0.01
            )
            or (
                metric["M1_M2"]["recall_at_fpr_0_01"] >= best_baseline_recall + 0.03
                and metric["M1_M2"]["npauc_0_01"] >= best_baseline_npauc - 0.005
            )
        )
        full = (
            metric["M1_M2"]["npauc_0_01"]
            >= max(metric["B"]["npauc_0_01"] + 0.02, 0.05)
            and metric["M1_M2"]["recall_at_fpr_0_01"]
            >= max(metric["B"]["recall_at_fpr_0_01"] + 0.05, 0.10)
            and metric["M1_M2"]["false_positive_rate"] <= 0.02
            and metric["M1_M2"]["c2_recall"] >= 0.05
            and metric["M1_M2"]["macro_f1"] >= max(metric["T0"]["macro_f1"] + 0.05, 0.20)
            and keeps_m1
            and exceeds_m2
            and baseline_gain_valid
            and len(full_capture_delta) == 12
            and sum(value >= 0.0 for value in full_capture_delta) >= 9
            and float(np.median(full_capture_delta)) > 0.0
            and min(full_capture_delta) >= -0.01
        )
        protocol_decisions[protocol] = {
            "data_and_runtime_validity": "PASS",
            "m1_independent_necessity": "PASS" if m1 else "FAIL",
            "m2_independent_necessity": "PASS" if m2 else "FAIL",
            "full_method_absolute_and_baseline_gate": "PASS" if full else "FAIL",
            "capture_non_concentration": "PASS"
            if len(full_capture_delta) == 12
            and sum(value >= 0 for value in full_capture_delta) >= 9
            else "FAIL",
            "protocol_passed": bool(m1 and m2 and full),
        }
    passed = all(value["protocol_passed"] for value in protocol_decisions.values())
    return {
        "schema_version": "tqhc2-strict-crossmember-decision-v1",
        "protocols": protocol_decisions,
        "candidate_advanced": passed,
        "decision": "实验支持进入下一阶段" if passed else "实验否决",
        "seed": 42,
        "single_seed_inference_prohibited": True,
        "thresholds_sha256": data.canonical_sha256(thresholds),
        "C_read_count": 1,
        **EVIDENCE,
    }


def swanlab_publish(
    config_path: Path, authorized_workspace: str, authorized_project: str
) -> dict[str, Any]:
    config = _load_config(config_path)
    paths = _paths(config_path, config)
    root = paths["output_root"]
    destination = config["swanlab"]
    if (
        destination["workspace"] != authorized_workspace
        or destination["project"] != authorized_project
    ):
        raise StrictCrossMemberQ0Error("SwanLab 授权目的地与冻结配置不一致")
    target = _read_json(root / "target_development_aggregate.json")
    decision = _read_json(root / "decision.json")
    scalar = {}
    for protocol, protocol_value in target["protocols"].items():
        for identity, identity_value in protocol_value["identities"].items():
            for metric, value in identity_value["overall"].items():
                if isinstance(value, int | float):
                    scalar[f"{protocol}/{identity}/{metric}"] = float(value)
        scalar[f"{protocol}/candidate_passed"] = float(
            decision["protocols"][protocol]["protocol_passed"]
        )
    import swanlab

    run = swanlab.init(
        workspace=authorized_workspace,
        project=authorized_project,
        name=destination["run_name"],
        mode=destination["mode"],
        config={"seed": 42, "identity_count": 34, **EVIDENCE},
    )
    swanlab.log(scalar)
    run.finish()
    receipt = {
        "schema_version": "tqhc2-strict-crossmember-swanlab-receipt-v1",
        "workspace": authorized_workspace,
        "project": authorized_project,
        "run_name": destination["run_name"],
        "uploaded_scalar_count": len(scalar),
        "sample_artifacts_uploaded": False,
        **EVIDENCE,
    }
    _write_json(root / "swanlab_receipt.json", receipt)
    return receipt


def audit_receipt(config_path: Path) -> dict[str, Any]:
    config = _load_config(config_path)
    root = _paths(config_path, config)["output_root"]
    forbidden_suffixes = {".parquet", ".npy", ".npz", ".csv", ".jsonl"}
    forbidden = [
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in forbidden_suffixes
    ]
    freeze = _verify_freeze(config_path, root)
    target_path = root / "target_development_aggregate.json"
    target = _read_json(target_path) if target_path.exists() else None
    valid = (
        not forbidden
        and freeze["identity_count"] == 34
        and freeze["C_read_count"] == 0
        and (target is None or target.get("C_read_count") == 1)
    )
    receipt = {
        "schema_version": "tqhc2-strict-crossmember-artifact-audit-v1",
        "passed": valid,
        "forbidden_artifacts": forbidden,
        "identity_count": freeze["identity_count"],
        "freeze_C_read_count": freeze["C_read_count"],
        "target_C_read_count": None if target is None else target.get("C_read_count"),
        **EVIDENCE,
    }
    _write_json(root / "artifact_audit_receipt.json", receipt)
    if not valid:
        raise StrictCrossMemberQ0Error("制品、身份或 C 访问审计失败")
    return receipt


def run(config_path: Path) -> None:
    audit(config_path)
    train_freeze(config_path)
    evaluate_target(config_path)
    audit_receipt(config_path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TQH-C2 严格跨成员泛化 Q0")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("audit", "train-freeze", "evaluate-target", "run", "audit-receipt"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--config", type=Path, required=True)
    publish = subparsers.add_parser("swanlab-publish")
    publish.add_argument("--config", type=Path, required=True)
    publish.add_argument("--authorized-workspace", required=True)
    publish.add_argument("--authorized-project", required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "audit":
        audit(args.config)
    elif args.command == "train-freeze":
        train_freeze(args.config)
    elif args.command == "evaluate-target":
        evaluate_target(args.config)
    elif args.command == "run":
        run(args.config)
    elif args.command == "swanlab-publish":
        swanlab_publish(args.config, args.authorized_workspace, args.authorized_project)
    elif args.command == "audit-receipt":
        audit_receipt(args.config)
    else:
        raise StrictCrossMemberQ0Error(f"未知命令：{args.command}")


if __name__ == "__main__":
    main()
