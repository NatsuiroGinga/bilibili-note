from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn import __version__ as sklearn_version
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split


PROJECT = "malicious-traffic-llm"
WORKSPACE = "mortiswang"
VISIBLE_ROLES = (
    "source-train",
    "source-validation",
    "target-prefix",
    "target-development",
)
VISIBLE_PROTOCOLS = (
    "leoste-2025-rf-with-packet-iat",
    "leoste-2025-rf-without-packet-iat",
    "dijk-2026-xgboost-op",
)
AUTHOR_EXAMPLE_PROTOCOL = "dijk-2024-author-code-example-rf80k"
BLOCKED_TRAINING_REPLICATION_CLASSES = frozenset({"paper-constrained-independent-replication"})
BLOCKED_TRAINING_IMPLEMENTATION_STATUSES = frozenset({"blocked-no-guessing"})
EVIDENCE_FLAGS = {
    "screening_only": True,
    "formal_paper_evidence": False,
    "formal_paper_evidence_candidate": False,
    "final_accessed": False,
}


class PublishedProtocolReplicationError(ValueError):
    """复现协议、输入清单或运行状态不满足门禁。"""


def _read_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise PublishedProtocolReplicationError(f"JSON 顶层必须是对象：{path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _require_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PublishedProtocolReplicationError(f"{name} 必须是非空字符串")
    return value


def _require_bool(value: object, expected: bool, name: str) -> None:
    if value is not expected:
        expected_text = "true" if expected else "false"
        raise PublishedProtocolReplicationError(f"{name} 必须逐字声明为 {expected_text}")


def _load_config(config_path: Path) -> Mapping[str, Any]:
    config = _read_json(config_path)
    if config.get("schema_version") != "lspr-published-protocol-replication-v1":
        raise PublishedProtocolReplicationError("复现配置 schema_version 不受支持")
    evidence = config.get("evidence_identity")
    if not isinstance(evidence, Mapping):
        raise PublishedProtocolReplicationError("复现配置缺少 evidence_identity")
    for key, expected in EVIDENCE_FLAGS.items():
        _require_bool(evidence.get(key), expected, f"evidence_identity.{key}")
    protocols = config.get("protocols")
    if not isinstance(protocols, Mapping) or not protocols:
        raise PublishedProtocolReplicationError("复现配置缺少 protocols")
    for protocol_id, protocol in protocols.items():
        if not isinstance(protocol_id, str) or not isinstance(protocol, Mapping):
            raise PublishedProtocolReplicationError("protocols 必须是字符串到对象的映射")
        if protocol.get("protocol_id") != protocol_id:
            raise PublishedProtocolReplicationError(f"协议键与 protocol_id 不一致：{protocol_id}")
        if (
            protocol.get("replication_class") == "paper-constrained-independent-replication"
            and protocol.get("implementation_status") != "blocked-no-guessing"
        ):
            raise PublishedProtocolReplicationError(
                f"论文约束独立复现必须标记 blocked-no-guessing：{protocol_id}"
            )
        if protocol.get("replication_class") == "author-code-example-replay":
            _require_bool(
                protocol.get("formal_comparison_forbidden"),
                True,
                f"protocols.{protocol_id}.formal_comparison_forbidden",
            )
    formal_gate = config.get("formal_paper_admission_gate")
    if not isinstance(formal_gate, Mapping):
        raise PublishedProtocolReplicationError("复现配置缺少正式论文纳入门禁")
    if formal_gate.get("required_seeds") != [42, 43, 44]:
        raise PublishedProtocolReplicationError("正式论文纳入门禁必须固定种子 42/43/44")
    _require_bool(
        formal_gate.get("current_visible_runs_admissible"),
        False,
        "formal_paper_admission_gate.current_visible_runs_admissible",
    )
    return config


def _protocol(config: Mapping[str, Any], protocol_id: str) -> Mapping[str, Any]:
    protocols = config.get("protocols")
    if not isinstance(protocols, Mapping):
        raise PublishedProtocolReplicationError("复现配置 protocols 无效")
    value = protocols.get(protocol_id)
    if not isinstance(value, Mapping):
        raise PublishedProtocolReplicationError(f"未知复现协议：{protocol_id}")
    if value.get("protocol_id") != protocol_id:
        raise PublishedProtocolReplicationError(f"协议键与 protocol_id 不一致：{protocol_id}")
    return value


def _training_block_reasons(protocol: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    replication_class = protocol.get("replication_class")
    implementation_status = protocol.get("implementation_status")
    if replication_class in BLOCKED_TRAINING_REPLICATION_CLASSES:
        reasons.append(f"replication_class={replication_class}")
    if implementation_status in BLOCKED_TRAINING_IMPLEMENTATION_STATUSES:
        reasons.append(f"implementation_status={implementation_status}")
    return reasons


def _require_training_entry_allowed(*, protocol_id: str, protocol: Mapping[str, Any]) -> None:
    reasons = _training_block_reasons(protocol)
    if reasons:
        raise PublishedProtocolReplicationError(
            f"严格模式拒绝训练协议 {protocol_id}：{'；'.join(reasons)}"
        )


def _dependency_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scikit_learn": sklearn_version,
    }


def _protocol_receipt(
    *,
    protocol_id: str,
    protocol: Mapping[str, Any],
    config_path: Path,
    run_kind: str,
) -> dict[str, Any]:
    return {
        "protocol_id": protocol_id,
        "display_name": _require_string(protocol.get("display_name"), "display_name"),
        "paper": protocol.get("paper"),
        "run_kind": run_kind,
        "replication_class": protocol.get("replication_class"),
        "implementation_status": protocol.get("implementation_status"),
        "disclosure_status": protocol.get("disclosure_status"),
        "formal_comparison_forbidden": protocol.get("formal_comparison_forbidden", False),
        "paper_reported_experiment_reproduced": False,
        "author_code_example_behavior_replayed": run_kind == "author-code-example",
        "independent_replication": run_kind == "visible-development",
        "paper_protocol": protocol.get("paper_protocol"),
        "implementation_differences": protocol.get("implementation_differences"),
        "blocking_reasons": protocol.get("blocking_reasons"),
        "formal_paper_admission_gate": protocol.get("formal_paper_admission_gate"),
        "config_path": str(config_path.resolve()),
        "config_sha256": _sha256(config_path),
        **EVIDENCE_FLAGS,
    }


def audit_protocols(*, config_path: Path, output_dir: Path) -> Mapping[str, Any]:
    if output_dir.exists():
        raise PublishedProtocolReplicationError(f"审计输出目录已存在，拒绝覆盖：{output_dir}")
    config = _load_config(config_path)
    protocols = config.get("protocols")
    assert isinstance(protocols, Mapping)
    matrix: dict[str, Any] = {}
    blocked_protocols: dict[str, list[str]] = {}
    strict_trainable_protocol_ids: list[str] = []
    author_example_protocol_ids: list[str] = []
    for protocol_id, raw_protocol in protocols.items():
        if not isinstance(protocol_id, str) or not isinstance(raw_protocol, Mapping):
            raise PublishedProtocolReplicationError("protocols 必须是字符串到对象的映射")
        receipt = _protocol_receipt(
            protocol_id=protocol_id,
            protocol=raw_protocol,
            config_path=config_path,
            run_kind="audit-only",
        )
        training_block_reasons = _training_block_reasons(raw_protocol)
        receipt["training_entry_allowed"] = not training_block_reasons
        receipt["training_block_reasons"] = training_block_reasons
        matrix[protocol_id] = receipt
        if training_block_reasons:
            blocked_protocols[protocol_id] = training_block_reasons
        if (
            raw_protocol.get("replication_class") == "strict-paper-experiment-reproduction"
            and not training_block_reasons
        ):
            strict_trainable_protocol_ids.append(protocol_id)
        if raw_protocol.get("replication_class") == "author-code-example-replay":
            author_example_protocol_ids.append(protocol_id)
    output_dir.mkdir(parents=True, exist_ok=False)
    strict_training_gate = {
        "schema_version": "lspr-published-protocol-strict-training-gate-v1",
        "state": "ready" if strict_trainable_protocol_ids else "blocked",
        "decision": (
            "strict-paper-training-available"
            if strict_trainable_protocol_ids
            else "no-trainable-strict-paper-experiment"
        ),
        "strict_trainable_protocol_count": len(strict_trainable_protocol_ids),
        "strict_trainable_protocol_ids": strict_trainable_protocol_ids,
        "blocked_protocol_count": len(blocked_protocols),
        "blocked_protocols": blocked_protocols,
        "author_code_example_protocol_ids": author_example_protocol_ids,
        "author_examples_are_not_strict_paper_experiments": True,
        "author_examples_formal_comparison_forbidden": True,
        **EVIDENCE_FLAGS,
    }
    result = {
        "schema_version": "lspr-published-protocol-audit-v1",
        "protocol_count": len(matrix),
        "protocols": matrix,
        "strict_paper_experiment_reproduction_count": sum(
            1
            for item in matrix.values()
            if item.get("replication_class") == "strict-paper-experiment-reproduction"
        ),
        "author_code_example_count": sum(
            1
            for item in matrix.values()
            if item.get("replication_class") == "author-code-example-replay"
        ),
        "independent_replication_candidate_count": sum(
            1
            for item in matrix.values()
            if item.get("replication_class") == "paper-constrained-independent-replication"
        ),
        "strict_training_gate": strict_training_gate,
        **EVIDENCE_FLAGS,
    }
    _write_json(output_dir / "protocol_matrix.json", result)
    _write_json(output_dir / "strict_training_gate_receipt.json", strict_training_gate)
    _write_json(
        output_dir / "status.json",
        {
            "state": "finished",
            "stage": "protocol-audit",
            **EVIDENCE_FLAGS,
        },
    )
    return result


def _array_from_record(
    record: object,
    *,
    cache_root: Path,
    description: str,
) -> np.ndarray:
    if not isinstance(record, Mapping):
        raise PublishedProtocolReplicationError(f"{description} 登记不是对象")
    path = Path(_require_string(record.get("path"), f"{description}.path")).resolve()
    if not _within(path, cache_root) or path.is_symlink() or not path.is_file():
        raise PublishedProtocolReplicationError(f"{description} 不在缓存根内或不是普通文件")
    expected_sha256 = _require_string(record.get("sha256"), f"{description}.sha256")
    actual_sha256 = _sha256(path)
    if actual_sha256 != expected_sha256:
        raise PublishedProtocolReplicationError(f"{description} SHA256 不匹配")
    array = np.load(path, mmap_mode="r", allow_pickle=False)
    expected_shape = record.get("shape")
    if isinstance(expected_shape, list) and list(array.shape) != expected_shape:
        raise PublishedProtocolReplicationError(f"{description} 形状与清单不一致")
    return array


def _load_visible_cache(
    cache_manifest: Path,
) -> tuple[Path, Mapping[str, Any], dict[str, dict[str, np.ndarray]], Mapping[str, Any]]:
    manifest = _read_json(cache_manifest)
    _require_bool(manifest.get("final_accessed"), False, "cache_manifest.final_accessed")
    cache_root = Path(
        _require_string(manifest.get("formal_cache_root"), "cache_manifest.formal_cache_root")
    ).resolve()
    if cache_manifest.resolve().parent != cache_root:
        raise PublishedProtocolReplicationError("缓存清单不在其声明的缓存根目录内")
    fields = manifest.get("model_fields")
    if not isinstance(fields, list) or len(fields) != 77:
        raise PublishedProtocolReplicationError("可见开发缓存必须含 77 个有序合法字段")
    if len(set(fields)) != len(fields) or not all(isinstance(item, str) for item in fields):
        raise PublishedProtocolReplicationError("可见开发缓存字段必须为互异字符串")
    raw_arrays = manifest.get("arrays")
    if not isinstance(raw_arrays, Mapping) or set(raw_arrays) != set(VISIBLE_ROLES):
        raise PublishedProtocolReplicationError("可见开发缓存角色集合不符合冻结合同")
    loaded: dict[str, dict[str, np.ndarray]] = {}
    for role in VISIBLE_ROLES:
        entries = raw_arrays.get(role)
        if not isinstance(entries, Mapping):
            raise PublishedProtocolReplicationError(f"缓存角色 {role} 登记无效")
        required = {"x_value", "x_missing"}
        if role in {"source-train", "source-validation"}:
            required.update(("labels", "sample_id"))
        if role == "target-development":
            required.add("sample_id")
            if "labels" in entries:
                raise PublishedProtocolReplicationError("目标可见标签不得与特征数组同处一组")
        missing = required.difference(entries)
        if missing:
            raise PublishedProtocolReplicationError(f"缓存角色 {role} 缺少数组：{sorted(missing)}")
        loaded[role] = {
            name: _array_from_record(
                entries[name],
                cache_root=cache_root,
                description=f"{role}.{name}",
            )
            for name in required
        }
        values = loaded[role]["x_value"]
        missing_mask = loaded[role]["x_missing"]
        if values.ndim != 2 or missing_mask.shape != values.shape or values.shape[1] != 77:
            raise PublishedProtocolReplicationError(f"缓存角色 {role} 特征形状无效")
    target_evaluation = manifest.get("target_development_evaluation")
    if not isinstance(target_evaluation, Mapping) or "labels" not in target_evaluation:
        raise PublishedProtocolReplicationError("缓存清单缺少目标可见标签旁车")
    return cache_root, manifest, loaded, target_evaluation


def _resolve_visible_fields(
    *,
    config: Mapping[str, Any],
    manifest: Mapping[str, Any],
    protocol: Mapping[str, Any],
) -> tuple[list[int], list[str]]:
    legal_fields = config.get("legal_visible_fields")
    manifest_fields = manifest.get("model_fields")
    if not isinstance(legal_fields, list) or len(legal_fields) != 77:
        raise PublishedProtocolReplicationError("配置必须含 77 个 legal_visible_fields")
    if manifest_fields != legal_fields:
        raise PublishedProtocolReplicationError("缓存字段顺序与复现配置不完全一致")
    packet_iat_fields = config.get("packet_interarrival_fields")
    if not isinstance(packet_iat_fields, list) or not packet_iat_fields:
        raise PublishedProtocolReplicationError("配置缺少 packet_interarrival_fields")
    positions = {name: index for index, name in enumerate(legal_fields)}
    missing_packet_iat = [name for name in packet_iat_fields if name not in positions]
    if missing_packet_iat:
        raise PublishedProtocolReplicationError(
            f"包到达间隔字段不在合法字段清单：{missing_packet_iat}"
        )
    field_view = protocol.get("field_view")
    if field_view == "legal-fields-with-packet-iat" or field_view == "legal-fields-op":
        indices = list(range(len(legal_fields)))
    elif field_view == "legal-fields-without-packet-iat":
        excluded = {positions[name] for name in packet_iat_fields}
        indices = [index for index in range(len(legal_fields)) if index not in excluded]
    else:
        raise PublishedProtocolReplicationError(f"不支持的可见字段视图：{field_view}")
    return indices, [legal_fields[index] for index in indices]


def _features(arrays: Mapping[str, np.ndarray], field_indices: Sequence[int]) -> np.ndarray:
    indices = list(field_indices)
    values = np.asarray(arrays["x_value"][:, indices], dtype=np.float32)
    missing = np.asarray(arrays["x_missing"][:, indices], dtype=np.float32)
    if values.shape != missing.shape:
        raise PublishedProtocolReplicationError("数值特征与缺失掩码形状不一致")
    if not np.isfinite(values).all() or not np.isfinite(missing).all():
        raise PublishedProtocolReplicationError("可见开发特征含非有限值")
    return np.concatenate((values, missing), axis=1)


def _build_visible_model(protocol: Mapping[str, Any], seed: int) -> Any:
    model_family = protocol.get("model_family")
    params = protocol.get("model_params")
    if not isinstance(params, Mapping):
        raise PublishedProtocolReplicationError("协议缺少 model_params")
    if model_family == "random-forest":
        expected = {
            "n_estimators": 128,
            "max_depth": 10,
            "bootstrap": True,
            "class_weight": None,
        }
        if dict(params) != expected:
            raise PublishedProtocolReplicationError("Leoste RF 超参与冻结配置不一致")
        return RandomForestClassifier(
            n_estimators=128,
            max_depth=10,
            bootstrap=True,
            class_weight=None,
            random_state=seed,
            n_jobs=-1,
        )
    if model_family == "xgboost":
        expected = {
            "n_estimators": 800,
            "learning_rate": 0.05,
            "max_depth": 8,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_lambda": 1.0,
            "min_child_weight": 1.0,
            "max_bin": 256,
        }
        if dict(params) != expected:
            raise PublishedProtocolReplicationError("Dijk 2026 XGBoost 超参与冻结配置不一致")
        try:
            from xgboost import XGBClassifier
        except Exception as error:
            raise PublishedProtocolReplicationError(
                f"XGBoost 不可导入：{type(error).__name__}:{error}"
            ) from error
        return XGBClassifier(
            **expected,
            objective="binary:logistic",
            eval_metric="logloss",
            tree_method="hist",
            random_state=seed,
            n_jobs=-1,
        )
    raise PublishedProtocolReplicationError(f"不支持的模型族：{model_family}")


def _binary_metrics(
    labels: np.ndarray, probabilities: np.ndarray, threshold: float
) -> dict[str, Any]:
    predictions = (probabilities >= threshold).astype(np.uint8)
    return {
        "threshold": float(threshold),
        "average_precision": float(average_precision_score(labels, probabilities)),
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(labels, predictions, average="weighted", zero_division=0)),
        "true_positive": int(np.sum((predictions == 1) & (labels == 1))),
        "false_positive": int(np.sum((predictions == 1) & (labels == 0))),
        "true_negative": int(np.sum((predictions == 0) & (labels == 0))),
        "false_negative": int(np.sum((predictions == 0) & (labels == 1))),
    }


def _macro_f1_threshold(labels: np.ndarray, probabilities: np.ndarray) -> float:
    order = np.argsort(-probabilities, kind="stable")
    sorted_labels = labels[order].astype(np.int64)
    sorted_probabilities = probabilities[order]
    total_positive = int(sorted_labels.sum())
    total_negative = int(sorted_labels.size - total_positive)
    true_positive = np.cumsum(sorted_labels)
    false_positive = np.arange(1, sorted_labels.size + 1) - true_positive
    boundaries = np.r_[sorted_probabilities[:-1] != sorted_probabilities[1:], True]
    candidates = np.flatnonzero(boundaries)
    tp = true_positive[candidates].astype(np.float64)
    fp = false_positive[candidates].astype(np.float64)
    fn = total_positive - tp
    tn = total_negative - fp
    positive_denominator = 2.0 * tp + fp + fn
    negative_denominator = 2.0 * tn + fp + fn
    positive_f1 = np.divide(
        2.0 * tp,
        positive_denominator,
        out=np.zeros_like(tp),
        where=positive_denominator > 0,
    )
    negative_f1 = np.divide(
        2.0 * tn,
        negative_denominator,
        out=np.zeros_like(tn),
        where=negative_denominator > 0,
    )
    macro_f1 = (positive_f1 + negative_f1) / 2.0
    best = int(np.argmax(macro_f1))
    return float(sorted_probabilities[candidates[best]])


def _false_positive_budget_threshold(
    labels: np.ndarray,
    probabilities: np.ndarray,
    *,
    false_positives_per_million_benign: int,
) -> float:
    benign_count = int(np.sum(labels == 0))
    allowed = int(np.floor(benign_count * false_positives_per_million_benign / 1_000_000.0))
    benign_probability = np.sort(probabilities[labels == 0])[::-1]
    if benign_probability.size == 0:
        raise PublishedProtocolReplicationError("源验证集没有良性样本")
    if allowed <= 0:
        return float(np.nextafter(benign_probability[0], np.inf))
    if allowed >= benign_probability.size:
        return 0.0
    return float(np.nextafter(benign_probability[allowed], np.inf))


def _validate_probabilities(
    labels: np.ndarray, probabilities: np.ndarray, description: str
) -> None:
    if labels.ndim != 1 or probabilities.ndim != 1 or labels.shape != probabilities.shape:
        raise PublishedProtocolReplicationError(f"{description} 标签与概率形状不一致")
    if not np.isfinite(probabilities).all():
        raise PublishedProtocolReplicationError(f"{description} 概率含非有限值")
    if np.any((probabilities < 0.0) | (probabilities > 1.0)):
        raise PublishedProtocolReplicationError(f"{description} 概率超出 [0,1]")


def _validate_binary_labels(labels: np.ndarray, description: str) -> None:
    if labels.ndim != 1 or labels.size == 0:
        raise PublishedProtocolReplicationError(f"{description} 标签必须是非空一维数组")
    unique = set(np.unique(labels).tolist())
    if not unique.issubset({0, 1}) or len(unique) != 2:
        raise PublishedProtocolReplicationError(
            f"{description} 标签必须同时包含二元类别 0 和 1，实际为 {sorted(unique)}"
        )


def _track_online(
    *,
    run_name: str,
    config: Mapping[str, Any],
    metrics: Mapping[str, float | int],
) -> Mapping[str, Any]:
    try:
        import swanlab

        run = swanlab.init(
            project=PROJECT,
            workspace=WORKSPACE,
            experiment_name=run_name,
            config=dict(config),
            logdir="./swanlog",
        )
        swanlab.log(dict(metrics))
        run.finish()
        return {"project": PROJECT, "workspace": WORKSPACE, "run_name": run_name, "mode": "cloud"}
    except Exception as error:
        raise PublishedProtocolReplicationError(
            f"SwanLab 在线记录失败：{type(error).__name__}:{error}"
        ) from error


def _prepare_output(output_dir: Path, *, stage: str, protocol_id: str) -> None:
    if output_dir.exists():
        raise PublishedProtocolReplicationError(f"运行输出目录已存在，拒绝覆盖：{output_dir}")
    output_dir.mkdir(parents=True, exist_ok=False)
    _write_json(
        output_dir / "status.json",
        {
            "state": "running",
            "stage": stage,
            "protocol_id": protocol_id,
            **EVIDENCE_FLAGS,
        },
    )


def _mark_failed(output_dir: Path, *, stage: str, protocol_id: str, error: Exception) -> None:
    if not output_dir.exists():
        return
    _write_json(
        output_dir / "status.json",
        {
            "state": "failed",
            "stage": stage,
            "protocol_id": protocol_id,
            "error_type": type(error).__name__,
            "error": str(error),
            **EVIDENCE_FLAGS,
        },
    )


def run_visible_development(
    *,
    cache_manifest: Path,
    config_path: Path,
    output_dir: Path,
    protocol_id: str,
    seed: int,
) -> Mapping[str, Any]:
    if protocol_id not in VISIBLE_PROTOCOLS:
        raise PublishedProtocolReplicationError(f"协议不能在可见开发入口运行：{protocol_id}")
    if seed != 42:
        raise PublishedProtocolReplicationError("可见开发门禁只允许预注册种子 42")
    config = _load_config(config_path)
    protocol = _protocol(config, protocol_id)
    _require_training_entry_allowed(protocol_id=protocol_id, protocol=protocol)
    if protocol.get("implementation_status") != "visible-development-runnable":
        raise PublishedProtocolReplicationError("协议未通过可见开发实现门禁")
    _prepare_output(
        output_dir,
        stage="visible-development",
        protocol_id=protocol_id,
    )
    try:
        cache_root, manifest, arrays, target_evaluation = _load_visible_cache(cache_manifest)
        field_indices, included_fields = _resolve_visible_fields(
            config=config,
            manifest=manifest,
            protocol=protocol,
        )
        receipt = _protocol_receipt(
            protocol_id=protocol_id,
            protocol=protocol,
            config_path=config_path,
            run_kind="visible-development",
        )
        receipt.update(
            {
                "seed": seed,
                "cache_manifest": str(cache_manifest.resolve()),
                "cache_manifest_sha256": _sha256(cache_manifest),
                "included_fields": included_fields,
                "included_field_count": len(included_fields),
                "feature_representation": "source-frozen-value-plus-missing-mask",
                "input_dimension": len(included_fields) * 2,
                "target_labels_connected_after_probability_seal": True,
            }
        )
        _write_json(output_dir / "protocol_receipt.json", receipt)
        train_x = _features(arrays["source-train"], field_indices)
        validation_x = _features(arrays["source-validation"], field_indices)
        target_x = _features(arrays["target-development"], field_indices)
        train_labels = np.asarray(arrays["source-train"]["labels"])
        validation_labels = np.asarray(arrays["source-validation"]["labels"])
        _validate_binary_labels(train_labels, "源训练")
        _validate_binary_labels(validation_labels, "源验证")
        train_y = train_labels.astype(np.uint8, copy=False)
        validation_y = validation_labels.astype(np.uint8, copy=False)
        if train_x.shape[0] != train_y.shape[0] or validation_x.shape[0] != validation_y.shape[0]:
            raise PublishedProtocolReplicationError("源训练或源验证的特征与标签行数不一致")
        model = _build_visible_model(protocol, seed)
        training_started = time.perf_counter()
        model.fit(train_x, train_y)
        training_seconds = time.perf_counter() - training_started
        validation_probability = model.predict_proba(validation_x)[:, 1].astype(np.float32)
        target_started = time.perf_counter()
        target_probability = model.predict_proba(target_x)[:, 1].astype(np.float32)
        target_seconds = time.perf_counter() - target_started
        _validate_probabilities(validation_y, validation_probability, "源验证")
        np.save(
            output_dir / "source_validation_probability.npy",
            validation_probability,
            allow_pickle=False,
        )
        np.save(
            output_dir / "target_development_probability.npy",
            target_probability,
            allow_pickle=False,
        )
        probability_seal = {
            "sealed_before_target_labels_opened": True,
            "source_validation_probability_sha256": _sha256(
                output_dir / "source_validation_probability.npy"
            ),
            "target_development_probability_sha256": _sha256(
                output_dir / "target_development_probability.npy"
            ),
            "target_development_sample_id_sha256": hashlib.sha256(
                np.asarray(arrays["target-development"]["sample_id"]).tobytes()
            ).hexdigest(),
            "source_validation_row_count": int(validation_probability.shape[0]),
            "target_development_row_count": int(target_probability.shape[0]),
            **EVIDENCE_FLAGS,
        }
        _write_json(output_dir / "probability_seal.json", probability_seal)
        target_labels = _array_from_record(
            target_evaluation["labels"],
            cache_root=cache_root,
            description="target-development.labels",
        )
        target_labels_array = np.asarray(target_labels)
        _validate_binary_labels(target_labels_array, "目标可见开发")
        target_y = target_labels_array.astype(np.uint8, copy=False)
        _validate_probabilities(target_y, target_probability, "目标可见开发")
        thresholds = {
            "default_0_5": 0.5,
            "source_validation_macro_f1": _macro_f1_threshold(validation_y, validation_probability),
            "source_validation_fp100_per_million_benign": _false_positive_budget_threshold(
                validation_y,
                validation_probability,
                false_positives_per_million_benign=100,
            ),
        }
        source_metrics = {
            name: _binary_metrics(validation_y, validation_probability, threshold)
            for name, threshold in thresholds.items()
        }
        target_metrics = {
            name: _binary_metrics(target_y, target_probability, threshold)
            for name, threshold in thresholds.items()
        }
        run_name = f"published-protocol-visible-{protocol_id}-seed{seed}"
        tracking = _track_online(
            run_name=run_name,
            config={
                "protocol_id": protocol_id,
                "display_name": protocol.get("display_name"),
                "seed": seed,
                "included_fields": included_fields,
                "cache_manifest_sha256": _sha256(cache_manifest),
                **EVIDENCE_FLAGS,
            },
            metrics={
                "target/average_precision": target_metrics["default_0_5"]["average_precision"],
                "target/default_f1": target_metrics["default_0_5"]["f1"],
                "target/default_macro_f1": target_metrics["default_0_5"]["macro_f1"],
                "target/source_threshold_macro_f1": target_metrics["source_validation_macro_f1"][
                    "macro_f1"
                ],
                "resource/training_seconds": training_seconds,
                "resource/target_inference_seconds": target_seconds,
            },
        )
        result = {
            "protocol": receipt,
            "thresholds": thresholds,
            "source_validation": source_metrics,
            "target_development": target_metrics,
            "probability_seal": probability_seal,
            "resources": {
                "training_seconds": training_seconds,
                "target_inference_seconds": target_seconds,
                "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
            },
            "dependencies": _dependency_versions(),
            "swanlab": tracking,
            **EVIDENCE_FLAGS,
        }
        _write_json(output_dir / "metrics.json", result)
        _write_json(
            output_dir / "status.json",
            {
                "state": "finished",
                "stage": "visible-development",
                "protocol_id": protocol_id,
                **EVIDENCE_FLAGS,
            },
        )
        return result
    except Exception as error:
        _mark_failed(
            output_dir,
            stage="visible-development",
            protocol_id=protocol_id,
            error=error,
        )
        raise


def _hash_author_text(value: object) -> int:
    is_nan_number = isinstance(value, (float, np.floating)) and bool(np.isnan(value))
    text = "" if value is None or is_nan_number else str(value)
    return int(hashlib.sha256(text.encode()).hexdigest(), 16) % (10**8)


def run_author_code_example(
    *,
    flow_csv: Path,
    config_path: Path,
    output_dir: Path,
) -> Mapping[str, Any]:
    config = _load_config(config_path)
    protocol = _protocol(config, AUTHOR_EXAMPLE_PROTOCOL)
    _require_training_entry_allowed(
        protocol_id=AUTHOR_EXAMPLE_PROTOCOL,
        protocol=protocol,
    )
    if protocol.get("implementation_status") != "author-example-runnable":
        raise PublishedProtocolReplicationError("作者代码示例未通过实现门禁")
    _require_bool(
        protocol.get("formal_comparison_forbidden"),
        True,
        "作者代码示例 formal_comparison_forbidden",
    )
    if not flow_csv.is_file() or flow_csv.is_symlink():
        raise PublishedProtocolReplicationError("LSPR23 流 CSV 不存在或不是普通文件")
    _prepare_output(
        output_dir,
        stage="author-code-example",
        protocol_id=AUTHOR_EXAMPLE_PROTOCOL,
    )
    try:
        import pandas as pd

        n_flows = protocol.get("n_flows")
        if n_flows != 80_000:
            raise PublishedProtocolReplicationError("作者示例成员数必须固定为前 80,000 行")
        text_columns = protocol.get("text_columns")
        if not isinstance(text_columns, list) or len(text_columns) != 9:
            raise PublishedProtocolReplicationError("作者示例文本字段清单无效")
        dtype = {column: "str" for column in text_columns}
        dataframe = pd.read_csv(flow_csv, nrows=n_flows, dtype=dtype)
        if dataframe.shape[0] != n_flows:
            raise PublishedProtocolReplicationError(
                f"作者示例要求前 80,000 行，实际读取 {dataframe.shape[0]} 行"
            )
        required = set(text_columns) | {"Label_src", "Label_dst", "Label"}
        missing = sorted(required.difference(dataframe.columns))
        if missing:
            raise PublishedProtocolReplicationError(f"作者示例输入缺少字段：{missing}")
        for column in text_columns:
            dataframe[f"{column}_hash"] = dataframe[column].apply(_hash_author_text)
        dataframe = dataframe.drop(text_columns, axis=1)
        features = dataframe.drop(["Label_src", "Label_dst", "Label"], axis=1)
        features.replace([np.inf, -np.inf], np.nan, inplace=True)
        labels = dataframe["Label"]
        label_array = np.asarray(labels)
        _validate_binary_labels(label_array, "作者示例全体")
        receipt = _protocol_receipt(
            protocol_id=AUTHOR_EXAMPLE_PROTOCOL,
            protocol=protocol,
            config_path=config_path,
            run_kind="author-code-example",
        )
        receipt.update(
            {
                "flow_csv": str(flow_csv.resolve()),
                "flow_csv_sha256": _sha256(flow_csv),
                "member_rule": "CSV 前 80,000 行",
                "feature_columns": list(features.columns),
                "feature_count": int(features.shape[1]),
                "identity_hash_fields_used": text_columns,
                "nan_cell_count": int(features.isna().sum().sum()),
                "strict_environment_reproduction": False,
                "formal_comparison_forbidden": True,
            }
        )
        _write_json(output_dir / "protocol_receipt.json", receipt)
        train_x, test_x, train_y, test_y = train_test_split(
            features,
            labels,
            test_size=0.2,
            random_state=42,
        )
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        started = time.perf_counter()
        model.fit(train_x, train_y)
        training_seconds = time.perf_counter() - started
        predictions = model.predict(test_x)
        probabilities = model.predict_proba(test_x)[:, 1].astype(np.float32)
        np.save(output_dir / "test_probability.npy", probabilities, allow_pickle=False)
        weighted_f1 = float(f1_score(test_y, predictions, average="weighted"))
        receipt.update(
            {
                "train_row_count": int(train_x.shape[0]),
                "test_row_count": int(test_x.shape[0]),
            }
        )
        _write_json(output_dir / "protocol_receipt.json", receipt)
        _write_json(output_dir / "protocol_receipt.json", receipt)
        test_labels = np.asarray(test_y, dtype=np.uint8)
        metrics = _binary_metrics(test_labels, probabilities, 0.5)
        metrics["author_reported_weighted_f1_from_hard_predictions"] = weighted_f1
        run_name = "dijk-2024-author-code-example-rf80k-seed42"
        tracking = _track_online(
            run_name=run_name,
            config={
                "protocol_id": AUTHOR_EXAMPLE_PROTOCOL,
                "n_flows": n_flows,
                "random_state": 42,
                "identity_hash_fields_used": text_columns,
                **EVIDENCE_FLAGS,
            },
            metrics={
                "example/weighted_f1": weighted_f1,
                "example/average_precision": metrics["average_precision"],
                "resource/training_seconds": training_seconds,
            },
        )
        result = {
            "protocol": receipt,
            "test": metrics,
            "test_probability_sha256": _sha256(output_dir / "test_probability.npy"),
            "resources": {
                "training_seconds": training_seconds,
                "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
            },
            "dependencies": {**_dependency_versions(), "pandas": pd.__version__},
            "swanlab": tracking,
            **EVIDENCE_FLAGS,
        }
        _write_json(output_dir / "metrics.json", result)
        _write_json(
            output_dir / "status.json",
            {
                "state": "finished",
                "stage": "author-code-example",
                "protocol_id": AUTHOR_EXAMPLE_PROTOCOL,
                **EVIDENCE_FLAGS,
            },
        )
        return result
    except Exception as error:
        _mark_failed(
            output_dir,
            stage="author-code-example",
            protocol_id=AUTHOR_EXAMPLE_PROTOCOL,
            error=error,
        )
        raise


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="审计并运行 LSPR 已发表论文原协议复现")
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit", help="物化论文、作者代码和独立复现三方矩阵")
    audit.add_argument("--config", type=Path, required=True)
    audit.add_argument("--output-dir", type=Path, required=True)
    visible = subparsers.add_parser(
        "run-visible-development",
        help="在可见开发缓存运行论文约束独立复现",
    )
    visible.add_argument("--cache-manifest", type=Path, required=True)
    visible.add_argument("--config", type=Path, required=True)
    visible.add_argument("--output-dir", type=Path, required=True)
    visible.add_argument("--protocol", choices=VISIBLE_PROTOCOLS, required=True)
    visible.add_argument("--seed", type=int, default=42)
    author = subparsers.add_parser(
        "run-author-code-example",
        help="复跑 Dijk 2024 作者后续 80k 代码示例行为",
    )
    author.add_argument("--flow-csv", type=Path, required=True)
    author.add_argument("--config", type=Path, required=True)
    author.add_argument("--output-dir", type=Path, required=True)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        if args.command == "audit":
            audit_protocols(config_path=args.config, output_dir=args.output_dir)
        elif args.command == "run-visible-development":
            run_visible_development(
                cache_manifest=args.cache_manifest,
                config_path=args.config,
                output_dir=args.output_dir,
                protocol_id=args.protocol,
                seed=args.seed,
            )
        elif args.command == "run-author-code-example":
            run_author_code_example(
                flow_csv=args.flow_csv,
                config_path=args.config,
                output_dir=args.output_dir,
            )
        else:
            raise PublishedProtocolReplicationError(f"未知命令：{args.command}")
    except (OSError, ValueError, PublishedProtocolReplicationError) as error:
        print(f"LSPR 已发表论文原协议复现失败：{error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
