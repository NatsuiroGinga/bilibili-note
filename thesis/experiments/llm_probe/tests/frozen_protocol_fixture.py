"""冻结协议测试所用的隔离临时夹具。"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from flow_probe.frozen_protocol import (
    FINAL_TUNING_STAGE,
    FROZEN_PROTOCOL_VERSION,
    file_sha256,
)


def _write_yaml(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        yaml.safe_dump(value, allow_unicode=True, sort_keys=True),
        encoding="utf-8",
    )


def _write_manifest(
    path: Path,
    *,
    sample_ids: list[str],
    split_id: str,
    samples_sha256: str,
    protocol_version: str,
) -> None:
    with path.open("w", encoding="utf-8") as output:
        for sample_id in sample_ids:
            output.write(
                json.dumps(
                    {
                        "protocol_version": protocol_version,
                        "sample_id": sample_id,
                        "samples_sha256": samples_sha256,
                        "split_id": split_id,
                        "suite_id": "fixture_binary_suite",
                    },
                    sort_keys=True,
                )
                + "\n"
            )


def write_frozen_protocol_fixture(
    root: Path,
    *,
    protocol_version: str = FROZEN_PROTOCOL_VERSION,
    status: str = "frozen",
    phase: str = FINAL_TUNING_STAGE,
) -> dict[str, list[str]]:
    """生成与真实下载目录完全隔离的最小冻结协议。"""
    root.mkdir()
    (root / "splits").mkdir()
    train_ids = [
        *(f"train-benign-{index}" for index in range(8)),
        *(f"train-malicious-{index}" for index in range(8)),
    ]
    validation_ids = [
        "validation-malicious-2",
        "validation-benign-0",
        "validation-unseen-0",
        "validation-malicious-0",
        "validation-benign-1",
        "validation-malicious-1",
    ]

    records: list[dict[str, object]] = []
    for index, sample_id in enumerate(train_ids):
        malicious = "malicious" in sample_id
        center = 10.0 if malicious else 0.0
        records.append(
            {
                "protocol_version": protocol_version,
                "sample_id": sample_id,
                "binary_label": "malicious" if malicious else "benign",
                "feature_a": center + index / 100,
                "feature_b": center * 2 + index / 100,
                "audit_token": f"audit-train-{index}",
            }
        )
    validation_labels = {
        "validation-malicious-2": "malicious",
        "validation-benign-0": "benign",
        "validation-unseen-0": "novel_attack",
        "validation-malicious-0": "malicious",
        "validation-benign-1": "benign",
        "validation-malicious-1": "malicious",
    }
    for index, sample_id in enumerate(validation_ids):
        label = validation_labels[sample_id]
        center = {"benign": 0.0, "malicious": 10.0, "novel_attack": 20.0}[label]
        records.append(
            {
                "protocol_version": protocol_version,
                "sample_id": sample_id,
                "binary_label": label,
                "feature_a": center + index / 100,
                "feature_b": center * 2 + index / 100,
                "audit_token": f"audit-validation-{index}",
            }
        )
    pd.DataFrame(list(reversed(records))).to_parquet(root / "samples.parquet", index=False)

    field_roles: dict[str, object] = {
        "protocol_version": protocol_version,
        "fields": {
            "protocol_version": {"role": "audit_only"},
            "sample_id": {"role": "audit_only"},
            "binary_label": {"role": "label_target"},
            "feature_a": {"role": "model_input", "views": ["tree_flat_view"]},
            "feature_b": {"role": "model_input", "views": ["tree_flat_view"]},
            "audit_token": {"role": "audit_only"},
        },
        "views": {
            "tree_flat_view": {"feature_fields": ["feature_a", "feature_b"]},
        },
    }
    _write_yaml(root / "field-roles.yaml", field_roles)
    samples_sha256 = file_sha256(root / "samples.parquet")
    _write_manifest(
        root / "splits" / "fixture-train.jsonl",
        sample_ids=train_ids,
        split_id="train",
        samples_sha256=samples_sha256,
        protocol_version=protocol_version,
    )
    _write_manifest(
        root / "splits" / "fixture-validation.jsonl",
        sample_ids=validation_ids,
        split_id="validation",
        samples_sha256=samples_sha256,
        protocol_version=protocol_version,
    )
    artifacts = {
        relative_path: file_sha256(root / relative_path)
        for relative_path in (
            "samples.parquet",
            "field-roles.yaml",
            "splits/fixture-train.jsonl",
            "splits/fixture-validation.jsonl",
        )
    }
    _write_yaml(
        root / "protocol.yaml",
        {
            "phase": phase,
            "protocol_version": protocol_version,
            "status": status,
            "artifacts": artifacts,
        },
    )
    return {"train": train_ids, "validation": validation_ids}


def refresh_artifact_hash(root: Path, relative_path: str) -> None:
    """测试主动改写制品后，仅刷新协议登记哈希。"""
    protocol_path = root / "protocol.yaml"
    protocol = yaml.safe_load(protocol_path.read_text(encoding="utf-8"))
    protocol["artifacts"][relative_path] = file_sha256(root / relative_path)
    _write_yaml(protocol_path, protocol)
