#!/usr/bin/env python3
"""核验 R2 处理制品并调用任务 01 正式源预检接口。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq

from flow_probe.r2_protocol_contract import (
    ExternalSourceRoots,
    load_r2_config,
    verify_frozen_inputs,
    verify_genis_archive,
    write_source_lock,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json_exclusive(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as output:
        json.dump(value, output, ensure_ascii=False, indent=2, sort_keys=True)
        output.write("\n")


def verify_processed_artifacts(project_root: Path, config: object) -> dict[str, object]:
    profiles: dict[str, object] = {}
    total_file_count = 1
    total_size_bytes = 0
    for profile in ("A", "B", "C"):
        spec = config.tqhc2_profiles[profile]
        root = project_root / spec.logical_root
        manifest_path = root / config.tqhc2_artifact_manifest_path
        manifest_sha256 = sha256_file(manifest_path)
        if manifest_sha256 != spec.artifact_manifest_sha256:
            raise RuntimeError(f"{profile} 制品清单 SHA-256 不一致")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows = manifest["files"]
        if len(rows) != 8:
            raise RuntimeError(f"{profile} 制品清单不是 8 项")
        payload_size = manifest_path.stat().st_size
        for row in rows:
            path = root / row["path"]
            size_bytes = path.stat().st_size
            if size_bytes != row["size_bytes"]:
                raise RuntimeError(f"{profile} 制品大小不一致：{row['path']}")
            if sha256_file(path) != row["sha256"]:
                raise RuntimeError(f"{profile} 制品 SHA-256 不一致：{row['path']}")
            payload_size += size_bytes
        master_rows = pq.ParquetFile(root / "master_records.parquet").metadata.num_rows
        packet_rows = pq.ParquetFile(
            root / "views/packet_observations.parquet"
        ).metadata.num_rows
        if master_rows != spec.master_rows or packet_rows != spec.packet_rows:
            raise RuntimeError(f"{profile} Parquet 行数不一致")
        source_manifest = root / config.tqhc2_source_manifest_path
        source_document = json.loads(source_manifest.read_text(encoding="utf-8"))
        source_count = len(source_document["files"])
        if source_count != 73:
            raise RuntimeError(f"{profile} 来源记录数不是 73")
        tree_file_count = sum(1 for path in root.rglob("*") if path.is_file())
        if tree_file_count != 9:
            raise RuntimeError(f"{profile} 处理制品文件数不是 9")
        profiles[profile] = {
            "artifact_manifest_sha256": manifest_sha256,
            "artifact_count": len(rows),
            "tree_file_count": tree_file_count,
            "tree_size_bytes": payload_size,
            "master_rows": master_rows,
            "packet_rows": packet_rows,
            "source_record_count": source_count,
            "source_manifest_text_lines": source_manifest.read_text(
                encoding="utf-8"
            ).count("\n"),
            "extractor_evidence_mode": spec.extractor_evidence_mode,
        }
        total_file_count += tree_file_count
        total_size_bytes += payload_size

    approved = project_root / config.tqhc2_approved_inputs_path
    approved_sha256 = sha256_file(approved)
    if approved_sha256 != config.tqhc2_approved_inputs_sha256:
        raise RuntimeError("approved-inputs.json SHA-256 不一致")
    total_size_bytes += approved.stat().st_size
    if total_file_count != 28:
        raise RuntimeError("处理制品总文件数不是 28")
    return {
        "status": "verified",
        "file_count": total_file_count,
        "total_size_bytes": total_size_bytes,
        "approved_inputs_sha256": approved_sha256,
        "profiles": profiles,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--genis-archive", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--source-lock-output", type=Path, required=True)
    parser.add_argument("--log-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt_path = args.log_dir / "source-preflight-receipt.json"
    inventory_path = args.log_dir / "processed-artifact-inventory.json"
    receipt: dict[str, object] = {
        "schema_version": 1,
        "status": "failed",
        "source_lock_written": False,
    }
    try:
        config = load_r2_config(args.config)
        inventory = verify_processed_artifacts(args.project_root, config)
        write_json_exclusive(inventory_path, inventory)
        genis = verify_genis_archive(args.genis_archive, config.genis)
        receipt["processed_artifacts"] = inventory
        receipt["genis_archive"] = genis.summary_dict()
        receipt["server_tqhc2_raw_root_exists"] = (
            args.repository_root / "raw/datasets/TQH-C2-2026"
        ).exists()
        source_lock = verify_frozen_inputs(
            args.project_root,
            ExternalSourceRoots(
                genis_archive=args.genis_archive,
                repository_root=args.repository_root,
            ),
            config,
        )
        write_source_lock(source_lock, args.source_lock_output)
        blocked = [
            row.as_dict()
            for row in source_lock.tqhc2_artifacts
            if row.evidence_status == "blocked"
        ]
        receipt["blocked_evidence"] = blocked
        receipt["source_lock_written"] = True
        receipt["status"] = "blocked" if blocked else "passed"
        exit_code = 20 if blocked else 0
    except Exception as error:
        receipt["error_type"] = type(error).__name__
        receipt["error"] = str(error)
        exit_code = 20
    write_json_exclusive(receipt_path, receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
