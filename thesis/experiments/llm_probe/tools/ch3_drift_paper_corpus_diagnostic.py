#!/usr/bin/env python3
"""生成 DRIFT 论文语料候选并执行受限内存的流式候选审计。"""

from __future__ import annotations

import argparse
import heapq
import hashlib
import importlib
import json
import os
import resource
import time
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "ch3-drift-paper-corpus-diagnostic-v1"
PURPOSES = ("source_train", "source_validation", "target_test")
FORBIDDEN_KEY_PARTS = ("member_seed", "model", "attack", "threshold", "sample", "path")
READ_BATCH_SIZE = 8192
HEARTBEAT_SECONDS = 30.0


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    partial = path.with_name(path.name + ".partial")
    partial.write_bytes(canonical_json(value))
    os.replace(partial, path)


def length_prefix(value: str) -> bytes:
    encoded = value.encode("utf-8")
    return len(encoded).to_bytes(8, "big") + encoded


def member_digest(revision: str, namespace: str, exact_esld: str) -> bytes:
    return hashlib.sha256(b"".join((length_prefix(revision), length_prefix(namespace), length_prefix(exact_esld)))).digest()


def digest_root(digests: list[bytes]) -> str:
    root = hashlib.sha256()
    for digest in sorted(digests):
        root.update(length_prefix(digest.hex()))
    return root.hexdigest()


def rss_max_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if os.uname().sysname == "Darwin" else value * 1024


def selected_statistics(exact_eslds: list[str]) -> dict[str, Any]:
    length_histogram: dict[str, int] = {}
    character_categories = {"ascii_alnum": 0, "ascii_hyphen": 0, "ascii_dot": 0, "non_ascii": 0, "other": 0}
    for exact_esld in exact_eslds:
        key = str(len(exact_esld))
        length_histogram[key] = length_histogram.get(key, 0) + 1
        for char in exact_esld:
            if char.isascii() and char.isalnum():
                character_categories["ascii_alnum"] += 1
            elif char == "-":
                character_categories["ascii_hyphen"] += 1
            elif char == ".":
                character_categories["ascii_dot"] += 1
            elif not char.isascii():
                character_categories["non_ascii"] += 1
            else:
                character_categories["other"] += 1
    return {"length_histogram": length_histogram, "character_categories": character_categories}


def reject_forbidden_keys(value: Any, where: str = "candidate-spec") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                raise ValueError(f"{where} 禁止字段：{key}")
            reject_forbidden_keys(nested, f"{where}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            reject_forbidden_keys(nested, f"{where}[{index}]")


def load_candidate_spec(path: Path) -> dict[str, Any]:
    """读取已由合同层解析并限制边界的候选规范路径。"""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {"corpus_namespace", "roles"}:
        raise ValueError("candidate-spec 顶层只能包含 corpus_namespace 和 roles")
    reject_forbidden_keys(value)
    namespace = value["corpus_namespace"]
    roles = value["roles"]
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("corpus_namespace 必须是非空字符串")
    if not isinstance(roles, dict) or set(roles) != set(PURPOSES):
        raise ValueError(f"roles 必须严格包含：{list(PURPOSES)}")
    normalized: dict[str, Any] = {"corpus_namespace": namespace, "roles": {}}
    for purpose in PURPOSES:
        entries = roles[purpose]
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"roles.{purpose} 必须是非空列表")
        normalized_entries = []
        seen: set[str] = set()
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or set(entry) != {"role", "count"}:
                raise ValueError(f"roles.{purpose}[{index}] 只能包含 role 和 count")
            role = entry["role"]
            count = entry["count"]
            if not isinstance(role, str) or not role or role in seen:
                raise ValueError(f"roles.{purpose}[{index}].role 必须非空且不重复")
            if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
                raise ValueError(f"roles.{purpose}[{index}].count 必须为正整数")
            seen.add(role)
            normalized_entries.append({"role": role, "count": count})
        normalized["roles"][purpose] = normalized_entries
    return normalized


def role_purpose_ok(purpose: str, role: Mapping[str, Any]) -> bool:
    if purpose == "source_train":
        return role["scope"] == "source" and role["split"] in {"train", "test"}
    if purpose == "source_validation":
        return role["scope"] == "source" and role["split"] == "val"
    return role["scope"] == "target" and role["split"] == "target"


def parquet_row_count(path: Path, parquet: Any) -> int:
    reader = parquet.ParquetFile(path, memory_map=False, pre_buffer=False)
    try:
        return int(reader.metadata.num_rows)
    finally:
        reader.close()


def update_role_status(run_dir: Path, statuses: Mapping[str, Any]) -> None:
    atomic_json(run_dir / "role-status.json", {"schema_version": SCHEMA_VERSION, "roles": dict(statuses)})


def validate_startup_run_dir(run_dir: Path) -> None:
    """启动前只允许启动器预创建的普通 console.log。"""
    if run_dir.is_symlink():
        raise FileExistsError(f"运行目录是符号链接，拒绝覆盖：{run_dir}")
    if not run_dir.exists():
        return
    if not run_dir.is_dir():
        raise FileExistsError(f"运行路径不是目录，拒绝覆盖：{run_dir}")
    existing_entries = list(run_dir.iterdir())
    if any(
        entry.name != "console.log" or entry.is_symlink() or not entry.is_file()
        for entry in existing_entries
    ):
        raise FileExistsError(f"运行目录含非 console.log 既有制品，拒绝覆盖：{run_dir}")


def audit_role(
    *,
    run_dir: Path,
    role_entry: Mapping[str, Any],
    purpose: str,
    revision: str,
    namespace: str,
    count: int,
    row_count: int,
    path: Path,
    parquet: Any,
    statuses: dict[str, Any],
) -> dict[str, Any]:
    role_name = str(role_entry["role"])
    started = time.monotonic()
    statuses[role_name] = {"status": "running", "purpose": purpose, "rows_read": 0, "row_count": row_count, "candidate_count": 0}
    update_role_status(run_dir, statuses)
    heap: list[tuple[int, str, str, int]] = []
    candidate_by_esld: dict[str, tuple[str, int]] = {}
    candidate_by_digest: dict[str, str] = {}
    raw_rows = 0
    duplicate_rows = 0
    invalid_rows = 0
    last_heartbeat = started
    reader = parquet.ParquetFile(path, memory_map=False, pre_buffer=False)
    try:
        for batch in reader.iter_batches(batch_size=READ_BATCH_SIZE, columns=["domain", "label"], use_threads=False):
            if tuple(batch.schema.names) != ("domain", "label"):
                raise ValueError(f"{role_name} 字段必须严格为 domain,label")
            exact_eslds = batch.column(batch.schema.get_field_index("domain")).to_pylist()
            labels = batch.column(batch.schema.get_field_index("label")).to_pylist()
            expected_label = 0 if role_entry["class"] == "benign" else 1
            for exact_esld, label in zip(exact_eslds, labels, strict=True):
                raw_rows += 1
                if not isinstance(exact_esld, str) or not exact_esld or not isinstance(label, int) or isinstance(label, bool) or label not in (0, 1) or label != expected_label:
                    invalid_rows += 1
                    raise ValueError(f"{role_name} 存在空值、非法类型或标签不符记录")
                if exact_esld in candidate_by_esld:
                    duplicate_rows += 1
                    continue
                digest = member_digest(revision, namespace, exact_esld)
                digest_hex = digest.hex()
                digest_int = int.from_bytes(digest, "big")
                if len(heap) >= count and digest_int >= -heap[0][0]:
                    continue
                previous_esld = candidate_by_digest.get(digest_hex)
                if previous_esld is not None and previous_esld != exact_esld:
                    raise ValueError(f"{role_name} 发生摘要碰撞")
                heapq.heappush(heap, (-digest_int, digest_hex, exact_esld, label))
                candidate_by_esld[exact_esld] = (digest_hex, label)
                candidate_by_digest[digest_hex] = exact_esld
                if len(heap) > count:
                    _, removed_digest, removed_esld, _ = heapq.heappop(heap)
                    candidate_by_esld.pop(removed_esld, None)
                    candidate_by_digest.pop(removed_digest, None)
            now = time.monotonic()
            if now - last_heartbeat >= HEARTBEAT_SECONDS:
                elapsed = max(now - started, 1e-9)
                heartbeat = {"role": role_name, "status": "running", "rows_read": raw_rows, "row_count": row_count, "candidate_count": len(heap), "rss_max_bytes": rss_max_bytes(), "elapsed_seconds": elapsed, "rows_per_second": raw_rows / elapsed}
                atomic_json(run_dir / "heartbeat.json", heartbeat)
                print(json.dumps(heartbeat, ensure_ascii=False), flush=True)
                last_heartbeat = now
    finally:
        reader.close()
    selected = sorted(heap, key=lambda item: item[1])
    selected_eslds = [item[2] for item in selected]
    selected_digests = [bytes.fromhex(item[1]) for item in selected]
    selected_member_counts = {exact_esld: 0 for exact_esld in selected_eslds}
    statuses[role_name] = {
        "status": "running",
        "phase": "selected_member_validation",
        "purpose": purpose,
        "rows_read": raw_rows,
        "row_count": row_count,
        "candidate_count": len(selected_eslds),
    }
    update_role_status(run_dir, statuses)
    second_started = time.monotonic()
    second_rows = 0
    second_last_heartbeat = second_started
    reader = parquet.ParquetFile(path, memory_map=False, pre_buffer=False)
    try:
        for batch in reader.iter_batches(batch_size=READ_BATCH_SIZE, columns=["domain", "label"], use_threads=False):
            if tuple(batch.schema.names) != ("domain", "label"):
                raise ValueError(f"{role_name} 字段必须严格为 domain,label")
            exact_eslds = batch.column(batch.schema.get_field_index("domain")).to_pylist()
            labels = batch.column(batch.schema.get_field_index("label")).to_pylist()
            expected_label = 0 if role_entry["class"] == "benign" else 1
            for exact_esld, label in zip(exact_eslds, labels, strict=True):
                second_rows += 1
                if not isinstance(exact_esld, str) or not exact_esld or not isinstance(label, int) or isinstance(label, bool) or label not in (0, 1) or label != expected_label:
                    invalid_rows += 1
                    raise ValueError(f"{role_name} 第二遍核验发现空值、非法类型或标签不符记录")
                if exact_esld in selected_member_counts:
                    selected_member_counts[exact_esld] += 1
            now = time.monotonic()
            if now - second_last_heartbeat >= HEARTBEAT_SECONDS:
                elapsed = max(now - second_started, 1e-9)
                heartbeat = {"role": role_name, "phase": "selected_member_validation", "status": "running", "rows_read": second_rows, "row_count": row_count, "candidate_count": len(selected_eslds), "rss_max_bytes": rss_max_bytes(), "elapsed_seconds": elapsed, "rows_per_second": second_rows / elapsed}
                atomic_json(run_dir / "heartbeat.json", heartbeat)
                print(json.dumps(heartbeat, ensure_ascii=False), flush=True)
                second_last_heartbeat = now
    finally:
        reader.close()
    selected_member_raw_rows = sum(selected_member_counts.values())
    selected_member_duplicate_rows = sum(max(value - 1, 0) for value in selected_member_counts.values())
    elapsed = max(time.monotonic() - started, 1e-9)
    result = {
        "status": "complete",
        "purpose": purpose,
        "role": role_name,
        "raw_rows": raw_rows,
        "row_count": row_count,
        "requested_count": count,
        "selected_count": len(selected),
        "selected_member_raw_rows": selected_member_raw_rows,
        "selected_member_duplicate_rows": selected_member_duplicate_rows,
        "topk_retained_duplicate_rows": duplicate_rows,
        "invalid_rows": invalid_rows,
        "candidate_root": digest_root(selected_digests),
        "statistics": selected_statistics(selected_eslds),
        "elapsed_seconds": elapsed,
        "rss_max_bytes": rss_max_bytes(),
    }
    statuses[role_name] = result
    update_role_status(run_dir, statuses)
    return {**result, "_candidate_eslds": {exact_esld: label for exact_esld, (_, label) in candidate_by_esld.items()}, "_candidate_digests": {exact_esld: digest for exact_esld, (digest, _) in candidate_by_esld.items()}}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="仓库相对评价配置")
    parser.add_argument("--run-dir", required=True, help="仓库相对诊断目录")
    parser.add_argument("--candidate-spec", required=True, help="仓库相对候选规范 JSON")
    parser.add_argument("--audit", action="store_true", help="执行只读 domain,label 流式候选审计")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.audit:
        raise ValueError("必须显式指定 --audit；本工具不提供真实读取模式")
    contract = importlib.import_module("ch3_drift_formal_contract")
    config, config_sha256 = contract.load_config(args.config)
    candidate_path = contract.resolve_repo_relative(args.candidate_spec, must_exist=True)
    spec = load_candidate_spec(candidate_path)
    run_dir = contract.resolve_run_dir(args.run_dir)
    validate_startup_run_dir(run_dir)
    configured_roles = {entry["role"] for entry in config["input_roles"]}
    role_metadata = {entry["role"]: entry for entry in config["input_roles"]}
    seen_purposes: dict[str, str] = {}
    revision = config["data_revision"]
    role_results: list[dict[str, Any]] = []
    statuses: dict[str, Any] = {}
    atomic_json(run_dir / "audit-status.json", {"schema_version": SCHEMA_VERSION, "status": "running", "current_role": None})
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise RuntimeError("流式候选审计需要 PyArrow") from exc
    for purpose in PURPOSES:
        for entry in spec["roles"][purpose]:
            if entry["role"] not in configured_roles:
                raise ValueError(f"候选角色不在配置中：{entry['role']}")
            if entry["role"] in seen_purposes:
                raise ValueError(f"同一 role 不得跨用途：{entry['role']}")
            seen_purposes[entry["role"]] = purpose
            role_metadata_entry = role_metadata[entry["role"]]
            if not role_purpose_ok(purpose, role_metadata_entry):
                raise ValueError(f"role {entry['role']} 不符合用途 {purpose} 的 scope/split 约束")
            path = contract.resolve_repo_relative(role_metadata_entry["path"], must_exist=True)
            row_count = parquet_row_count(path, parquet)
            if entry["count"] > row_count:
                raise ValueError(f"{entry['role']} requested count 大于元数据行数")
            atomic_json(run_dir / "audit-status.json", {"schema_version": SCHEMA_VERSION, "status": "running", "current_role": entry["role"]})
            role_results.append(audit_role(run_dir=run_dir, role_entry=role_metadata_entry, purpose=purpose, revision=revision, namespace=spec["corpus_namespace"], count=entry["count"], row_count=row_count, path=path, parquet=parquet, statuses=statuses))

    overlaps: list[dict[str, Any]] = []
    conflict_total = 0
    for index, left in enumerate(role_results):
        for right in role_results[index + 1 :]:
            if left["purpose"] == right["purpose"]:
                continue
            left_eslds = left["_candidate_eslds"]
            right_eslds = right["_candidate_eslds"]
            shared = set(left_eslds).intersection(right_eslds)
            same_label = sum(left_eslds[exact_esld] == right_eslds[exact_esld] for exact_esld in shared)
            conflicts = len(shared) - same_label
            conflict_total += conflicts
            overlaps.append({"left_role": left["role"], "right_role": right["role"], "left_purpose": left["purpose"], "right_purpose": right["purpose"], "overlap_count": len(shared), "same_label_count": same_label, "label_conflict_count": conflicts})

    public_roles = []
    for result in role_results:
        public_roles.append({key: value for key, value in result.items() if not key.startswith("_")})
    status = "blocked" if conflict_total else "complete"
    output = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "data_revision": revision,
        "config_sha256": config_sha256,
        "candidate_spec": {"corpus_namespace": spec["corpus_namespace"], "roles": spec["roles"]},
        "roles": public_roles,
        "cross_purpose_overlaps": overlaps,
        "label_conflict_count": conflict_total,
        "read_executed": True,
        "domains_or_members_written": False,
    }
    atomic_json(run_dir / "candidate-audit.json", output)
    atomic_json(run_dir / "audit-status.json", {"schema_version": SCHEMA_VERSION, "status": status, "current_role": None, "label_conflict_count": conflict_total})
    if conflict_total:
        raise ValueError(f"跨用途标签冲突：{conflict_total}")
    print(json.dumps({"status": status, "run_dir": str(run_dir)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
