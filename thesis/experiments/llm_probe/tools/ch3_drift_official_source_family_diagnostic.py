#!/usr/bin/env python3
"""诊断 DRIFT 官方检查点在 T17--T19 非歧义家族上的源期错误。"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
import torch

import ch3_drift_official_checkpoint_t17_eval as official

SCHEMA_VERSION = "ch3-drift-official-source-family-diagnostic-v1"
DATASET_REVISION = "3b31077020cd1c013d0a75cad51042a2327c4521"
PROGRESS_ROWS = 100_000


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    partial.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("配置 schema_version 不匹配")
    if config.get("dataset_revision") != DATASET_REVISION:
        raise ValueError("数据 revision 不匹配")
    if config.get("screening_only") is not True:
        raise ValueError("本入口必须保持 screening_only=true")
    years = [item["year"] for item in config["inputs"]]
    if years != ["T17", "T18", "T19"]:
        raise ValueError("家族诊断仅允许 T17、T18、T19")
    if int(config["batch_size"]) <= 0:
        raise ValueError("batch_size 必须为正整数")
    if not isinstance(config.get("resource_basis"), dict):
        raise ValueError("缺少 batch_size 的资源依据收据")
    if int(config.get("cpu_prefetch_depth", 0)) != 0:
        raise ValueError("cpu_prefetch_depth 必须冻结为 0")
    return config


def source_thresholds(path: Path) -> dict[str, float]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("status") != "completed":
        raise ValueError("三支路源阈值结果未完成")
    values = result["source_thresholds"]["static_fusion"]
    return {str(key): float(value) for key, value in values.items()}


def family_mapping(path: Path) -> tuple[list[tuple[str, str]], dict[str, Any]]:
    grouped: dict[str, set[str]] = {}
    families: set[str] = set()
    for batch in pq.ParquetFile(path).iter_batches(
        batch_size=100_000, columns=["domain", "family"]
    ):
        for domain, family in zip(
            batch.column(0).to_pylist(), batch.column(1).to_pylist(), strict=True
        ):
            if not isinstance(domain, str) or not isinstance(family, str):
                continue
            key = domain.strip().lower().split(".", 1)[0]
            value = family.strip().lower()
            if not key or not value:
                continue
            grouped.setdefault(key, set()).add(value)
            families.add(value)
    valid = sorted(
        (key, next(iter(values)))
        for key, values in grouped.items()
        if len(values) == 1
    )
    ambiguous_pairs: dict[str, int] = {}
    for values in grouped.values():
        if len(values) > 1:
            key = " || ".join(sorted(values))
            ambiguous_pairs[key] = ambiguous_pairs.get(key, 0) + 1
    return valid, {
        "raw_rows": pq.ParquetFile(path).metadata.num_rows,
        "unique_esld_keys": len(grouped),
        "non_ambiguous_esld_keys": len(valid),
        "ambiguous_esld_keys": sum(len(values) > 1 for values in grouped.values()),
        "max_families_per_key": max((len(values) for values in grouped.values()), default=0),
        "unique_families": len(families),
        "ambiguous_family_pairs": [
            {"family_pair": key, "len": value}
            for key, value in sorted(ambiguous_pairs.items(), key=lambda item: (-item[1], item[0]))
        ],
    }


def predict_scores(
    model: torch.nn.Module,
    tokenizer: Any,
    domains: list[str],
    device: torch.device,
) -> np.ndarray:
    token_ids = official.encode_subword(domains, tokenizer).to(device, non_blocking=True)
    char_ids = official.encode_char(domains).to(device, non_blocking=True)
    with torch.inference_mode(), torch.autocast(
        device_type=device.type,
        dtype=torch.bfloat16,
        enabled=device.type == "cuda",
    ):
        logits = model(token_ids, char_ids)
    return torch.softmax(logits.float(), dim=1)[:, 1].cpu().numpy()


def evaluate_year(
    model: torch.nn.Module,
    tokenizer: Any,
    rows_data: list[tuple[str, str]],
    thresholds: dict[str, float],
    device: torch.device,
    batch_size: int,
    year: str,
) -> dict[str, Any]:
    families = sorted({family for _, family in rows_data})
    family_to_id = {family: index for index, family in enumerate(families)}
    count = np.zeros(len(families), dtype=np.int64)
    score_sum = np.zeros(len(families), dtype=np.float64)
    default_false_negative = np.zeros(len(families), dtype=np.int64)
    threshold_false_negative = {
        key: np.zeros(len(families), dtype=np.int64) for key in thresholds
    }
    processed = 0
    next_progress = PROGRESS_ROWS
    started = time.monotonic()
    for offset in range(0, len(rows_data), batch_size):
        batch = rows_data[offset : offset + batch_size]
        domains = [domain for domain, _ in batch]
        family_ids = np.fromiter((family_to_id[family] for _, family in batch), dtype=np.int64, count=len(domains))
        scores = predict_scores(model, tokenizer, domains, device)
        count += np.bincount(family_ids, minlength=len(families))
        score_sum += np.bincount(family_ids, weights=scores.astype(np.float64), minlength=len(families))
        default_false_negative += np.bincount(family_ids, weights=(scores < 0.5).astype(np.int64), minlength=len(families)).astype(np.int64)
        for key, threshold in thresholds.items():
            threshold_false_negative[key] += np.bincount(family_ids, weights=(scores < threshold).astype(np.int64), minlength=len(families)).astype(np.int64)
        processed += len(domains)
        if processed >= next_progress:
            print(json.dumps({"stage": "family_eval", "year": year, "rows": processed, "total": len(rows_data), "elapsed_seconds": time.monotonic() - started}, ensure_ascii=False), file=sys.stderr, flush=True)
            next_progress += PROGRESS_ROWS
    rows: dict[str, Any] = {}
    for family, index in family_to_id.items():
        support = int(count[index])
        false_negative = int(default_false_negative[index])
        rows[family] = {
            "support": support,
            "score_mean": float(score_sum[index] / max(support, 1)),
            "threshold_0_5": {
                "fn": false_negative,
                "fnr": false_negative / max(support, 1),
                "tp": support - false_negative,
                "tpr": 1.0 - false_negative / max(support, 1),
            },
            "source_threshold_transfer": {
                key: {
                    "threshold": threshold,
                    "fn": int(threshold_false_negative[key][index]),
                    "fnr": int(threshold_false_negative[key][index]) / max(support, 1),
                    "tp": support - int(threshold_false_negative[key][index]),
                    "tpr": 1.0
                    - int(threshold_false_negative[key][index]) / max(support, 1),
                }
                for key, threshold in thresholds.items()
            },
        }
    total_false_negative = int(default_false_negative.sum())
    total = int(count.sum())
    return {
        "samples": total,
        "families": rows,
        "overall_threshold_0_5": {
            "fn": total_false_negative,
            "fnr": total_false_negative / max(total, 1),
            "tp": total - total_false_negative,
            "tpr": 1.0 - total_false_negative / max(total, 1),
        },
        "overall_source_threshold_transfer": {
            key: {
                "threshold": threshold,
                "fn": int(values.sum()),
                "fnr": int(values.sum()) / max(total, 1),
                "tp": total - int(values.sum()),
                "tpr": 1.0 - int(values.sum()) / max(total, 1),
            }
            for (key, threshold), values in zip(
                thresholds.items(), threshold_false_negative.values(), strict=True
            )
        },
        "elapsed_seconds": time.monotonic() - started,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--mapping-only", action="store_true")
    parser.add_argument("--only-year", choices=("T17", "T18", "T19"))
    parser.add_argument("--parallel-years", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    root = args.project_root.resolve()
    run_dir = args.run_dir.resolve()
    config = load_config(args.config.resolve())
    config_sha256 = sha256_file(args.config.resolve())
    script_sha256 = sha256_file(Path(__file__))
    raw_root = root / config["raw_root"]
    reference_root = root / config["reference_root"]
    checkpoint = root / config["checkpoint"]
    tokenizer_path = reference_root / config["tokenizer"]
    threshold_result = root / config["source_threshold_result"]
    paths = [raw_root / item["path"] for item in config["inputs"]]
    for path in [
        reference_root / "model.py",
        checkpoint,
        tokenizer_path,
        threshold_result,
        *paths,
    ]:
        if not path.is_file():
            raise FileNotFoundError(f"必需输入不存在：{path}")
    if args.mapping_only:
        receipts: dict[str, Any] = {}
        for item, path in zip(config["inputs"], paths, strict=True):
            _, mapping = family_mapping(path)
            if mapping["ambiguous_esld_keys"] != int(item["ambiguous_esld_keys"]):
                raise ValueError(f"{item['year']} 多 family eSLD 键数与冻结合同不符")
            receipts[item["year"]] = mapping
        print(json.dumps({"status": "mapping_checked", "mapping": receipts}, ensure_ascii=False))
        return 0
    if args.parallel_years:
        children = []
        for year in ("T17", "T18", "T19"):
            children.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "--config", str(args.config.resolve()),
                        "--project-root", str(root),
                        "--run-dir", str(run_dir),
                        "--only-year", year,
                        "--resume",
                    ]
                )
            )
        failed = [process.wait() for process in children]
        if any(code != 0 for code in failed):
            raise RuntimeError(f"年度子进程失败：{failed}")
    thresholds = source_thresholds(threshold_result)
    torch.set_float32_matmul_precision("high")
    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    tokenizer = official.PreTrainedTokenizerFast(tokenizer_file=str(tokenizer_path))
    model = official.load_model(reference_root, checkpoint, device)
    results: dict[str, Any] = {}
    mapping_receipts: dict[str, Any] = {}
    selected = [(item, path) for item, path in zip(config["inputs"], paths, strict=True) if args.only_year is None or item["year"] == args.only_year]
    for item, path in selected:
        year = item["year"]
        year_path = run_dir / "years" / f"{year}.json"
        if args.resume and year_path.is_file():
            saved = json.loads(year_path.read_text(encoding="utf-8"))
            if (
                saved.get("status") == "completed"
                and saved.get("config_sha256") == config_sha256
                and saved.get("script_sha256") == script_sha256
            ):
                results[year] = saved["evaluation"]
                mapping_receipts[year] = saved["mapping"]
                continue
        frame, mapping = family_mapping(path)
        if mapping["ambiguous_esld_keys"] != int(item["ambiguous_esld_keys"]):
            raise ValueError(f"{year} 多 family eSLD 键数与冻结合同不符")
        evaluation = evaluate_year(
            model,
            tokenizer,
            frame,
            thresholds,
            device,
            int(config["batch_size"]),
            year,
        )
        state = {
            "status": "completed",
            "year": year,
            "config_sha256": config_sha256,
            "script_sha256": script_sha256,
            "mapping": mapping,
            "evaluation": evaluation,
        }
        atomic_json(year_path, state)
        results[year] = evaluation
        mapping_receipts[year] = mapping
    if args.only_year is not None:
        print(json.dumps({"status": "partial_completed", "year": args.only_year, "resource_contention": True}, ensure_ascii=False))
        return 0
    family_sets = {
        year: set(value["families"]) for year, value in results.items()
    }
    output = {
        "schema_version": SCHEMA_VERSION,
        "status": "completed",
        "run_identity": config["run_identity"],
        "screening_only": True,
        "mechanism_adjudication": False,
        "dataset_revision": DATASET_REVISION,
        "config_sha256": config_sha256,
        "script_sha256": script_sha256,
        "inputs": [
            {
                "year": item["year"],
                "path": str(path),
                "rows": pq.ParquetFile(path).metadata.num_rows,
                "sha256": sha256_file(path),
            }
            for item, path in zip(config["inputs"], paths, strict=True)
        ],
        "artifacts": {
            "checkpoint_sha256": sha256_file(checkpoint),
            "tokenizer_sha256": sha256_file(tokenizer_path),
            "reference_model_sha256": sha256_file(reference_root / "model.py"),
            "source_threshold_result_sha256": sha256_file(threshold_result),
        },
        "source_thresholds": thresholds,
        "resource_basis": config["resource_basis"],
        "cpu_prefetch_depth": config["cpu_prefetch_depth"],
        "resource_contention": True,
        "mapping": mapping_receipts,
        "results": results,
        "new_family_names": {
            "T18_vs_T17": sorted(family_sets["T18"] - family_sets["T17"]),
            "T19_vs_T17_T18": sorted(
                family_sets["T19"] - family_sets["T17"] - family_sets["T18"]
            ),
        },
        "runtime": {
            "elapsed_seconds": time.monotonic() - started,
            "device": str(device),
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "batch_size": int(config["batch_size"]),
            "bf16_autocast": device.type == "cuda",
            "max_memory_allocated_bytes": (
                torch.cuda.max_memory_allocated() if device.type == "cuda" else None
            ),
        },
        "interpretation_boundary": (
            "family 仅为 raw 元数据标签，不等于底层生成器。"
            "多 family eSLD 全部隔离，结果只用于源期病灶与候选分组资格。"
        ),
    }
    atomic_json(run_dir / "result.json", output)
    print(json.dumps({"status": "completed", "run_dir": str(run_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
