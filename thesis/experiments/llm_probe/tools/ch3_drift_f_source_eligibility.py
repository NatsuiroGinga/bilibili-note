#!/usr/bin/env python3
"""用真实源期成员核查 F 的选择与良性补偿作用面。"""

from __future__ import annotations

import argparse
import gc
import hashlib
import heapq
import importlib
import importlib.util
import json
import os
import resource
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Iterator, Mapping


SCHEMA_VERSION = "ch3-drift-f-source-eligibility-v1"
READ_BATCH_SIZE = 8192
MODEL_BATCH_SIZE = 128
GROUP_SIZE = 4
GROUPS_PER_FORWARD = MODEL_BATCH_SIZE // GROUP_SIZE
HEARTBEAT_SECONDS = 30.0


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    partial = path.with_name(path.name + ".partial")
    partial.write_bytes(canonical_json(value))
    os.replace(partial, path)


def length_prefix(value: str) -> bytes:
    raw = value.encode("utf-8")
    return len(raw).to_bytes(8, "big") + raw


def candidate_digest(revision: str, namespace: str, exact_esld: str) -> bytes:
    return hashlib.sha256(b"".join((length_prefix(revision), length_prefix(namespace), length_prefix(exact_esld)))).digest()


def digest_root(digests: list[bytes]) -> str:
    root = hashlib.sha256()
    for digest in sorted(digests):
        root.update(length_prefix(digest.hex()))
    return root.hexdigest()


def rss_max_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def load_spec(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {"corpus_namespace", "roles"}:
        raise ValueError("候选规格顶层必须严格为 corpus_namespace 和 roles")
    namespace = value["corpus_namespace"]
    roles = value["roles"]
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("corpus_namespace 必须为非空字符串")
    if not isinstance(roles, dict) or set(roles) != {"source_train", "source_validation", "target_test"}:
        raise ValueError("候选规格缺少固定用途")
    for purpose, entries in roles.items():
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"{purpose} 必须为非空列表")
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {"role", "count"}:
                raise ValueError(f"{purpose} 条目必须严格为 role,count")
            if not isinstance(entry["role"], str) or not isinstance(entry["count"], int) or entry["count"] <= 0:
                raise ValueError(f"{purpose} 条目非法")
    return value


def role_is_source_train(role: Mapping[str, Any]) -> bool:
    return role["scope"] == "source" and role["split"] in {"train", "test"}


def select_role(
    *,
    parquet: Any,
    path: Path,
    role: Mapping[str, Any],
    count: int,
    revision: str,
    namespace: str,
) -> tuple[list[str], dict[str, Any]]:
    expected_label = 0 if role["class"] == "benign" else 1
    heap: list[tuple[int, str, str]] = []
    retained: dict[str, str] = {}
    digest_domains: dict[str, str] = {}
    raw_rows = 0
    reader = parquet.ParquetFile(path, memory_map=False, pre_buffer=False)
    try:
        for batch in reader.iter_batches(batch_size=READ_BATCH_SIZE, columns=["domain", "label"], use_threads=False):
            if tuple(batch.schema.names) != ("domain", "label"):
                raise ValueError(f"{role['role']} 字段必须严格为 domain,label")
            domains = batch.column(0).to_pylist()
            labels = batch.column(1).to_pylist()
            for domain, label in zip(domains, labels, strict=True):
                raw_rows += 1
                if not isinstance(domain, str) or not domain or not isinstance(label, int) or isinstance(label, bool) or label != expected_label:
                    raise ValueError(f"{role['role']} 出现非法域名或标签")
                digest = candidate_digest(revision, namespace, domain)
                digest_hex = digest.hex()
                digest_int = int.from_bytes(digest, "big")
                if domain in retained:
                    continue
                if len(heap) >= count and digest_int >= -heap[0][0]:
                    continue
                previous = digest_domains.get(digest_hex)
                if previous is not None and previous != domain:
                    raise ValueError(f"{role['role']} 出现成员摘要碰撞")
                heapq.heappush(heap, (-digest_int, digest_hex, domain))
                retained[domain] = digest_hex
                digest_domains[digest_hex] = domain
                if len(heap) > count:
                    _, removed_digest, removed_domain = heapq.heappop(heap)
                    retained.pop(removed_domain, None)
                    digest_domains.pop(removed_digest, None)
    finally:
        reader.close()
    selected = sorted(heap, key=lambda item: item[1])
    if len(selected) != count:
        raise ValueError(f"{role['role']} 未选满请求成员")
    return [item[2] for item in selected], {
        "role": role["role"],
        "class": role["class"],
        "raw_rows": raw_rows,
        "selected_count": len(selected),
        "candidate_root": digest_root([bytes.fromhex(item[1]) for item in selected]),
    }


def disable_nested_tensor(torch: Any, model: Any) -> int:
    encoders = [module for module in model.modules() if isinstance(module, torch.nn.TransformerEncoder)]
    if len(encoders) != 2:
        raise ValueError(f"预期两个TransformerEncoder，实际为{len(encoders)}")
    for encoder in encoders:
        encoder.enable_nested_tensor = False
        encoder.use_nested_tensor = False
    return len(encoders)


def production_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("ch3_drift_f_production_kernel", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法载入生产 F 候选核")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "perturb2", None)):
        raise RuntimeError("生产 F 候选核缺少 perturb2")
    return module


def score_domains(model: Any, tokenizer: Any, official: Any, diag: Any, torch: Any, device: Any, domains: list[str]) -> list[float]:
    values: list[float] = []
    model.eval()
    with torch.inference_mode():
        for start in range(0, len(domains), MODEL_BATCH_SIZE):
            chunk = domains[start : start + MODEL_BATCH_SIZE]
            token_ids = official.encode_subword(chunk, tokenizer).to(device)
            char_ids = official.encode_char(chunk).to(device)
            token_feature, char_feature = diag.branch_features(model, token_ids, char_ids)
            logits = model.classifier_head(torch.cat([token_feature, char_feature], dim=1))
            values.extend(torch.softmax(logits.float(), dim=1)[:, 1].cpu().tolist())
    return [float(value) for value in values]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="仓库相对正式配置")
    parser.add_argument("--candidate-spec", required=True, help="仓库相对源期诊断成员规格")
    parser.add_argument("--run-dir", required=True, help="仓库相对诊断运行目录")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    contract = importlib.import_module("ch3_drift_formal_contract")
    config, config_sha256 = contract.load_config(args.config)
    spec_path = contract.resolve_repo_relative(args.candidate_spec, must_exist=True)
    candidate_spec = load_spec(spec_path)
    run_dir = contract.resolve_run_dir(args.run_dir)
    if run_dir.exists():
        existing = list(run_dir.iterdir())
        if any(entry.name != "console.log" or entry.is_symlink() or not entry.is_file() for entry in existing):
            raise FileExistsError(f"运行目录含既有制品：{run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise RuntimeError("资格筛选需要PyArrow") from exc
    torch = importlib.import_module("torch")
    if not torch.backends.mps.is_available():
        raise RuntimeError("资格筛选只允许可用MPS环境")
    device = torch.device("mps")
    repo_root = Path(__file__).resolve().parents[4]
    probe_root = repo_root / "thesis/experiments/llm_probe"
    reference_root = probe_root / "runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2"
    checkpoint = probe_root / "runs/models/drift-official-dsn2026/finetuning.pt"
    tokenizer_path = reference_root / "artifacts/tokenizer/tokenizer-0-30522-both.json"
    kernel_path = repo_root / ".Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official_p2p3.py"
    for required in (reference_root / "model.py", checkpoint, tokenizer_path, kernel_path):
        if not required.is_file():
            raise FileNotFoundError(f"必需文件不存在：{required}")
    role_map = {role["role"]: role for role in config["input_roles"]}
    selected_entries = candidate_spec["roles"]["source_train"]
    if len(selected_entries) != 12:
        raise ValueError("源训练资格筛选必须严格使用12个源角色")
    state = {"schema_version": SCHEMA_VERSION, "status": "running", "stage": "select_members"}
    atomic_json(run_dir / "status.json", state)
    selected_by_class: dict[str, list[str]] = {"benign": [], "dga": []}
    role_receipts: list[dict[str, Any]] = []
    revision = config["data_revision"]
    for entry in selected_entries:
        role = role_map.get(entry["role"])
        if role is None or not role_is_source_train(role):
            raise ValueError(f"候选角色不符合源训练合同：{entry['role']}")
        path = contract.resolve_repo_relative(role["path"], must_exist=True)
        members, receipt = select_role(parquet=parquet, path=path, role=role, count=entry["count"], revision=revision, namespace=candidate_spec["corpus_namespace"])
        selected_by_class[role["class"]].extend(members)
        role_receipts.append(receipt)
    if len(selected_by_class["benign"]) != 30000 or len(selected_by_class["dga"]) != 30000:
        raise ValueError("源训练成员类别数量不符合诊断规格")
    state["stage"] = "load_model"
    atomic_json(run_dir / "status.json", state)
    sys.path.insert(0, str(probe_root / "tools"))
    official = importlib.import_module("ch3_drift_official_checkpoint_t17_eval")
    diag = importlib.import_module("ch3_drift_official_branch_conflict_diagnostic")
    model = official.load_model(reference_root, checkpoint, device)
    nested_encoder_count = disable_nested_tensor(torch, model)
    tokenizer = official.PreTrainedTokenizerFast(tokenizer_file=str(tokenizer_path))
    kernel = production_module(kernel_path)
    state["stage"] = "benign_gate"
    atomic_json(run_dir / "status.json", state)
    benign_scores = score_domains(model, tokenizer, official, diag, torch, device, selected_by_class["benign"])
    benign_fp = sum(score >= 0.5 for score in benign_scores)
    del benign_scores
    gc.collect()
    state["stage"] = "dga_groups"
    atomic_json(run_dir / "status.json", state)
    import random
    rng = random.Random(42)
    histogram = {str(value): 0 for value in range(GROUP_SIZE + 1)}
    changed_candidates = 0
    unchanged_candidates = 0
    completed_groups = 0
    started = time.monotonic()
    last_heartbeat = started
    dga = selected_by_class["dga"]
    for start in range(0, len(dga), GROUPS_PER_FORWARD):
        parents = dga[start : start + GROUPS_PER_FORWARD]
        candidates: list[str] = []
        for parent in parents:
            base = kernel.perturb2(parent, rng)
            group = [kernel.perturb2(base, rng) for _ in range(GROUP_SIZE)]
            candidates.extend(group)
            changed_candidates += sum(candidate != parent for candidate in group)
            unchanged_candidates += sum(candidate == parent for candidate in group)
        scores = score_domains(model, tokenizer, official, diag, torch, device, candidates)
        for group_offset in range(len(parents)):
            left = group_offset * GROUP_SIZE
            fooled = sum(score < 0.5 for score in scores[left : left + GROUP_SIZE])
            histogram[str(fooled)] += 1
            completed_groups += 1
        now = time.monotonic()
        if now - last_heartbeat >= HEARTBEAT_SECONDS:
            elapsed = now - started
            heartbeat = {
                "stage": "dga_groups",
                "completed_groups": completed_groups,
                "total_groups": len(dga),
                "groups_per_second": completed_groups / max(elapsed, 1e-9),
                "rss_max_bytes": rss_max_bytes(),
                "disk_free_bytes": shutil.disk_usage(run_dir).free,
            }
            atomic_json(run_dir / "heartbeat.json", heartbeat)
            print(json.dumps(heartbeat, ensure_ascii=False), flush=True)
            last_heartbeat = now
    mixed_groups = histogram["1"] + histogram["2"] + histogram["3"]
    output = {
        "schema_version": SCHEMA_VERSION,
        "status": "complete",
        "scope": "source_development_only",
        "config_sha256": config_sha256,
        "candidate_spec_namespace": candidate_spec["corpus_namespace"],
        "member_counts": {"benign": len(selected_by_class["benign"]), "dga": len(dga)},
        "role_receipts": role_receipts,
        "model": {"nested_tensor_disabled": True, "transformer_encoder_count": nested_encoder_count},
        "benign_gate": {"threshold": 0.5, "false_positive_count": benign_fp, "false_positive_rate": benign_fp / len(selected_by_class["benign"])},
        "dga_groups": {"group_size": GROUP_SIZE, "group_count": completed_groups, "fooled_histogram": histogram, "mixed_group_count": mixed_groups, "mixed_group_rate": mixed_groups / completed_groups},
        "edit_integrity": {"candidate_count": changed_candidates + unchanged_candidates, "changed_candidate_count": changed_candidates, "unchanged_candidate_count": unchanged_candidates},
        "qualification": {"selector_nonzero_layer_active": mixed_groups > 0, "benign_reweight_active": benign_fp > 0, "all_candidates_edited": unchanged_candidates == 0},
        "materialization": {"member_dataset_written": False, "attacked_esld_written": False, "predictions_written": False},
        "runtime": {"elapsed_seconds": time.monotonic() - started, "rss_max_bytes": rss_max_bytes(), "disk_free_bytes": shutil.disk_usage(run_dir).free},
    }
    atomic_json(run_dir / "f-source-eligibility.json", output)
    atomic_json(run_dir / "status.json", {"schema_version": SCHEMA_VERSION, "status": "complete", "stage": None})
    print(json.dumps({"status": "complete", "run_dir": str(run_dir)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
