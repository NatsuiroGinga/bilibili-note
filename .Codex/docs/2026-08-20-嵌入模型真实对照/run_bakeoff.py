from __future__ import annotations

import argparse
import csv
import dataclasses
import gc
import hashlib
import json
import math
import os
import pickle
import platform
import resource
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


TASK_DIR = Path(__file__).resolve().parent
REPO_ROOT = TASK_DIR.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.literature_search import build as build_module  # noqa: E402
from scripts.literature_search import search as search_module  # noqa: E402
from scripts.literature_search.config import load_config  # noqa: E402
from scripts.literature_search.documents import (  # noqa: E402
    scan_corpus,
    source_manifest_hash,
)
from scripts.literature_search.storage import connect  # noqa: E402


MODEL_CACHE = REPO_ROOT / ".cache/literature-search/model-cache"
RUN_CACHE = REPO_ROOT / ".cache/literature-search/embedding-bakeoff"
MODEL_MANIFEST_PATH = TASK_DIR / "model_manifest.json"
QRELS_PATH = TASK_DIR / "frozen_qrels.json"
CURATED_PATH = (
    REPO_ROOT
    / ".Codex/docs/2026-08-20-本地文献混合检索效果评估/frozen_queries.json"
)
EXPECTED_QRELS_SHA256 = "d85841be6d65ca667ae84bf7e829cd96e9d5c0817aca90d75114c3ed076abed6"
IMPLEMENTATION_FILES = (
    "scripts/literature_search/build.py",
    "scripts/literature_search/config.py",
    "scripts/literature_search/documents.py",
    "scripts/literature_search/lexical.py",
    "scripts/literature_search/ranking.py",
    "scripts/literature_search/search.py",
    "scripts/literature_search/storage.py",
    "scripts/literature_search/types.py",
)
MODES = ("lexical", "vector", "hybrid")
TOP_K = 10
HOT_REPETITIONS = 3
LOAD_EVENTS: list[dict[str, Any]] = []
ACTIVE_SPEC: dict[str, Any] = {}
ACTIVE_DEVICE = "cpu"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = max(0, math.ceil(fraction * len(ordered)) - 1)
    return ordered[position]


def rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if platform.system() == "Darwin" else value * 1024


def load_manifest() -> list[dict[str, Any]]:
    payload = json.loads(MODEL_MANIFEST_PATH.read_text(encoding="utf-8"))
    return list(payload["candidates"])


def model_snapshot(spec: Mapping[str, Any]) -> Path:
    repository_dir = "models--" + str(spec["model_id"]).replace("/", "--")
    return MODEL_CACHE / repository_dir / "snapshots" / str(spec["revision"])


class CandidateEmbeddingBackend:
    def __init__(
        self,
        model_name: str,
        revision: str,
        cache_folder: Path | None = None,
        local_files_only: bool = False,
        device: str = "cpu",
    ) -> None:
        del revision
        from sentence_transformers import SentenceTransformer

        if device not in {"cpu", "mps"}:
            raise RuntimeError(f"评测驱动不支持的设备：{device}")
        started = time.perf_counter()
        self.requested_device = device
        self.fallback_reason = None
        parameters = {
            "cache_folder": str(cache_folder) if cache_folder else None,
            "local_files_only": local_files_only,
        }
        try:
            self.model = SentenceTransformer(
                model_name,
                device=device,
                **parameters,
            )
        except RuntimeError as error:
            if device != "mps":
                raise
            self.fallback_reason = f"MPS 加载失败，回退中央处理器：{error}"
            self.model = SentenceTransformer(
                model_name,
                device="cpu",
                **parameters,
            )
        self.model.max_seq_length = int(ACTIVE_SPEC["max_tokens"])
        self.event = {
            "load_seconds": time.perf_counter() - started,
            "resolved_model_path": str(model_name),
            "parameter_count": sum(
                parameter.numel() for parameter in self.model.parameters()
            ),
            "embedding_dimension": self.model.get_sentence_embedding_dimension(),
            "max_seq_length": self.model.max_seq_length,
            "requested_device": device,
            "device": str(self.model.device),
            "fallback_reason": self.fallback_reason,
        }
        LOAD_EVENTS.append(self.event)

    @property
    def device(self) -> str:
        return str(self.model.device)

    def _encode(
        self, texts: Sequence[str], prefix: str, batch_size: int
    ) -> np.ndarray:
        values = [prefix + text for text in texts]
        parameters = {
            "batch_size": batch_size,
            "normalize_embeddings": True,
            "convert_to_numpy": True,
            "show_progress_bar": False,
        }
        try:
            vectors = self.model.encode(values, **parameters)
        except RuntimeError as error:
            if self.requested_device != "mps" or not self.device.startswith("mps"):
                raise
            self.fallback_reason = f"MPS 编码失败，回退中央处理器：{error}"
            self.model.to("cpu")
            self.event["device"] = str(self.model.device)
            self.event["fallback_reason"] = self.fallback_reason
            vectors = self.model.encode(values, **parameters)
        return np.asarray(vectors, dtype=np.float32)

    def encode_documents(
        self, texts: Sequence[str], batch_size: int
    ) -> np.ndarray:
        return self._encode(
            texts, str(ACTIVE_SPEC["document_prefix"]), batch_size
        )

    def encode_query(self, text: str) -> np.ndarray:
        return self._encode([text], str(ACTIVE_SPEC["query_prefix"]), 1)[0]


def normalize_curated_queries() -> dict[str, Any]:
    payload = json.loads(CURATED_PATH.read_text(encoding="utf-8"))
    queries = []
    for query in payload["queries"]:
        paths = list(query.get("relevant_paths") or [])
        queries.append(
            {
                "id": query["id"],
                "query": query["query"],
                "expected_collections": ["papers"] if paths else [],
                "relevance": [{"path": path, "grade": 2} for path in paths],
                "negative_type": "curated_negative" if not paths else None,
            }
        )
    return {
        "dataset_id": "curated-regression-v1",
        "dataset_role": "regression_only",
        "tuning_prohibited": False,
        "queries": queries,
    }


def load_query_sets() -> list[dict[str, Any]]:
    payload = json.loads(QRELS_PATH.read_text(encoding="utf-8"))
    return [normalize_curated_queries(), *payload["query_sets"]]


def result_paths(result: Mapping[str, Any]) -> set[str]:
    paths = {str(result["note_path"])}
    paths.update(str(view["note_path"]) for view in result.get("note_views", []))
    return paths


def result_grade(result: Mapping[str, Any], grades: Mapping[str, int]) -> int:
    return max((grades.get(path, 0) for path in result_paths(result)), default=0)


def query_metrics(
    query: Mapping[str, Any], results: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    grades = {
        str(item["path"]): int(item["grade"])
        for item in query.get("relevance", [])
    }
    relevant_paths = set(grades)
    found_at_5: set[str] = set()
    found_at_10: set[str] = set()
    first_rank: int | None = None
    gains: list[int] = []
    for rank, result in enumerate(results[:TOP_K], start=1):
        paths = result_paths(result) & relevant_paths
        if rank <= 5:
            found_at_5.update(paths)
        found_at_10.update(paths)
        grade = result_grade(result, grades)
        gains.append(grade)
        if grade > 0 and first_rank is None:
            first_rank = rank
    ideal_gains = sorted(grades.values(), reverse=True)[:TOP_K]

    def dcg(values: Iterable[int]) -> float:
        return sum(
            (2**value - 1) / math.log2(rank + 1)
            for rank, value in enumerate(values, start=1)
        )

    ideal_dcg = dcg(ideal_gains)
    expected_collections = set(query.get("expected_collections") or [])
    wrong_collection_count = sum(
        1
        for result in results[:TOP_K]
        if expected_collections
        and str(result.get("collection")) not in expected_collections
    )
    returned_count = min(TOP_K, len(results))
    is_negative = not relevant_paths
    return {
        "query_id": query["id"],
        "positive": not is_negative,
        "recall_at_5": (
            len(found_at_5) / len(relevant_paths) if relevant_paths else None
        ),
        "recall_at_10": (
            len(found_at_10) / len(relevant_paths) if relevant_paths else None
        ),
        "reciprocal_rank_at_10": 1.0 / first_rank if first_rank else 0.0,
        "ndcg_at_10": dcg(gains) / ideal_dcg if ideal_dcg else None,
        "negative_rejected": len(results) == 0 if is_negative else None,
        "returned_count": len(results),
        "wrong_collection_count_at_10": wrong_collection_count,
        "wrong_collection_denominator_at_10": (
            returned_count if expected_collections else 0
        ),
    }


def aggregate_metrics(per_query: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    positives = [item for item in per_query if item["positive"]]
    negatives = [item for item in per_query if not item["positive"]]

    def mean(field: str) -> float | None:
        values = [float(item[field]) for item in positives if item[field] is not None]
        return statistics.fmean(values) if values else None

    wrong_count = sum(int(item["wrong_collection_count_at_10"]) for item in positives)
    wrong_denominator = sum(
        int(item["wrong_collection_denominator_at_10"]) for item in positives
    )
    return {
        "positive_queries": len(positives),
        "negative_queries": len(negatives),
        "recall_at_5": mean("recall_at_5"),
        "recall_at_10": mean("recall_at_10"),
        "mrr_at_10": mean("reciprocal_rank_at_10"),
        "ndcg_at_10": mean("ndcg_at_10"),
        "negative_rejection_rate": (
            statistics.fmean(
                1.0 if item["negative_rejected"] else 0.0 for item in negatives
            )
            if negatives
            else None
        ),
        "wrong_collection_rate_at_10": (
            wrong_count / wrong_denominator if wrong_denominator else None
        ),
        "wrong_collection_count_at_10": wrong_count,
        "wrong_collection_denominator_at_10": wrong_denominator,
    }


def verify_contract(contract: Mapping[str, Any]) -> None:
    if file_sha256(QRELS_PATH) != EXPECTED_QRELS_SHA256:
        raise RuntimeError("冻结 qrels 哈希变化，拒绝运行")
    for relative_path, expected_hash in contract["implementation_hashes"].items():
        if file_sha256(REPO_ROOT / relative_path) != expected_hash:
            raise RuntimeError(f"评测期间实现变化，拒绝混跑：{relative_path}")


def run_worker(slug: str, contract_path: Path) -> None:
    global ACTIVE_DEVICE, ACTIVE_SPEC
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    verify_contract(contract)
    spec = next(item for item in load_manifest() if item["slug"] == slug)
    ACTIVE_SPEC = spec
    ACTIVE_DEVICE = "mps" if contract["mps_available"] else "cpu"
    snapshot_path = Path(contract["corpus_snapshot_path"])
    if file_sha256(snapshot_path) != contract["corpus_snapshot_sha256"]:
        raise RuntimeError("语料快照哈希变化，拒绝运行")
    with snapshot_path.open("rb") as handle:
        frozen_scan = pickle.load(handle)
    if source_manifest_hash(frozen_scan.notes) != contract["source_manifest_hash"]:
        raise RuntimeError("语料清单哈希与合同不一致")

    snapshot = model_snapshot(spec)
    if not snapshot.is_dir():
        raise RuntimeError(f"固定模型快照不存在：{snapshot}")
    config = dataclasses.replace(
        load_config(),
        model_name=str(spec["model_id"]),
        model_revision=str(spec["revision"]),
    )
    index_path = RUN_CACHE / f"{slug}.sqlite3"
    if index_path.exists():
        index_path.unlink()

    build_module.scan_corpus = lambda *args, **kwargs: frozen_scan
    build_module.EmbeddingBackend = CandidateEmbeddingBackend
    started = time.perf_counter()
    build_metadata = build_module.build_index(
        REPO_ROOT,
        index_path,
        config,
        lexical_only=False,
        cache_folder=MODEL_CACHE,
        local_files_only=True,
        device=ACTIVE_DEVICE,
    )
    build_wall_seconds = time.perf_counter() - started
    build_load_event = dict(LOAD_EVENTS[-1])
    del started
    gc.collect()

    query_backend = CandidateEmbeddingBackend(
        str(snapshot),
        str(spec["revision"]),
        cache_folder=MODEL_CACHE,
        local_files_only=True,
        device=ACTIVE_DEVICE,
    )
    query_load_event = query_backend.event
    search_module.EmbeddingBackend = lambda *args, **kwargs: query_backend
    warmup_started = time.perf_counter()
    query_backend.encode_query("跨年度加密恶意流量检测的实体级评价")
    warmup_seconds = time.perf_counter() - warmup_started

    connection = connect(index_path, readonly=True)
    datasets: dict[str, Any] = {}
    try:
        for query_set in load_query_sets():
            dataset_id = str(query_set["dataset_id"])
            scope = "paper" if dataset_id == "curated-regression-v1" else "all"
            dataset_payload: dict[str, Any] = {
                "dataset_role": query_set["dataset_role"],
                "tuning_prohibited": bool(query_set["tuning_prohibited"]),
                "scope": scope,
                "modes": {},
            }
            for mode in MODES:
                raw_queries = []
                latencies = []
                per_query = []
                for query in query_set["queries"]:
                    first_results = None
                    repetitions = 1 if mode == "lexical" else HOT_REPETITIONS
                    for _ in range(repetitions):
                        query_started = time.perf_counter()
                        results = search_module.search_federated(
                            connection,
                            str(query["query"]),
                            mode,
                            TOP_K,
                            config,
                            cache_folder=MODEL_CACHE,
                            local_files_only=True,
                            device=ACTIVE_DEVICE,
                            scope=scope,
                            include_history=False,
                        )
                        latencies.append(time.perf_counter() - query_started)
                        if first_results is None:
                            first_results = results
                    assert first_results is not None
                    metrics = query_metrics(query, first_results)
                    per_query.append(metrics)
                    raw_queries.append(
                        {
                            "query_id": query["id"],
                            "query": query["query"],
                            "expected_collections": query.get(
                                "expected_collections", []
                            ),
                            "relevance": query.get("relevance", []),
                            "metrics": metrics,
                            "results": first_results,
                        }
                    )
                dataset_payload["modes"][mode] = {
                    "metrics": aggregate_metrics(per_query),
                    "latency": {
                        "observations": len(latencies),
                        "median_seconds": statistics.median(latencies),
                        "p95_seconds": percentile(latencies, 0.95),
                        "minimum_seconds": min(latencies),
                        "maximum_seconds": max(latencies),
                    },
                    "queries": raw_queries,
                }
            datasets[dataset_id] = dataset_payload
    finally:
        connection.close()

    actual = query_load_event
    for field in ("parameter_count", "embedding_dimension", "max_seq_length"):
        if int(actual[field]) != int(spec[field if field != "max_seq_length" else "max_tokens"]):
            raise RuntimeError(f"模型清单与运行时不一致：{field}")
    payload = {
        "schema": "embedding-bakeoff-candidate-result/v1",
        "model": spec,
        "contract": {
            "source_manifest_hash": contract["source_manifest_hash"],
            "corpus_snapshot_sha256": contract["corpus_snapshot_sha256"],
            "qrels_sha256": EXPECTED_QRELS_SHA256,
            "implementation_hashes": contract["implementation_hashes"],
            "chunk_max_chars": config.chunk_max_chars,
            "chunk_overlap_chars": config.chunk_overlap_chars,
            "rrf_constant": config.rrf_constant,
            "batch_size": config.batch_size,
            "top_k": TOP_K,
            "hot_repetitions": HOT_REPETITIONS,
            "lexical_implementation_shared": True,
        },
        "device": {
            "requested": "mps",
            "mps_built": contract["mps_built"],
            "mps_available": contract["mps_available"],
            "build_used": build_load_event["device"],
            "query_used": query_load_event["device"],
            "build_fallback_reason": build_load_event["fallback_reason"],
            "query_fallback_reason": query_load_event["fallback_reason"],
        },
        "resource": {
            "build_wall_seconds": build_wall_seconds,
            "build_reported_seconds": build_metadata["build_seconds"],
            "build_model_cold_load_seconds": build_load_event["load_seconds"],
            "query_model_cold_load_seconds": query_load_event["load_seconds"],
            "warmup_encode_seconds": warmup_seconds,
            "peak_rss_bytes": rss_bytes(),
            "index_bytes": build_metadata["index_bytes"],
            "index_sha256": build_metadata["index_sha256"],
        },
        "build_metadata": build_metadata,
        "runtime_model": dict(query_load_event),
        "datasets": datasets,
    }
    write_json(RUN_CACHE / f"{slug}-result.json", payload)


def freeze_corpus() -> dict[str, Any]:
    config = load_config()
    scan = scan_corpus(
        REPO_ROOT,
        config.input_glob,
        config.project_input_globs,
        config.experiment_receipt_globs,
        config.max_document_bytes,
    )
    relevant_paths = {
        str(item["path"])
        for query_set in json.loads(QRELS_PATH.read_text(encoding="utf-8"))[
            "query_sets"
        ]
        for query in query_set["queries"]
        for item in query.get("relevance", [])
    }
    indexed_paths = {note.relative_path for note in scan.notes}
    missing = sorted(relevant_paths - indexed_paths)
    if missing:
        raise RuntimeError("冻结 qrels 含未进入生产语料的路径：" + ", ".join(missing))
    RUN_CACHE.mkdir(parents=True, exist_ok=True)
    snapshot_path = RUN_CACHE / "corpus_snapshot.pkl"
    with snapshot_path.open("wb") as handle:
        pickle.dump(scan, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return {
        "corpus_snapshot_path": str(snapshot_path),
        "corpus_snapshot_sha256": file_sha256(snapshot_path),
        "source_manifest_hash": source_manifest_hash(scan.notes),
        "note_count": len(scan.notes),
        "collection_counts": dict(
            sorted(Counter(note.collection for note in scan.notes).items())
        ),
        "excluded_count": len(scan.excluded),
    }


def compare_lexical(candidate_payloads: Sequence[Mapping[str, Any]]) -> bool:
    reference: dict[tuple[str, str], list[str]] | None = None
    for payload in candidate_payloads:
        current = {
            (dataset_id, str(query["query_id"])): [
                str(result["document_id"]) for result in query["results"]
            ]
            for dataset_id, dataset in payload["datasets"].items()
            for query in dataset["modes"]["lexical"]["queries"]
        }
        if reference is None:
            reference = current
        elif current != reference:
            return False
    return True


def write_comparison(candidate_payloads: Sequence[Mapping[str, Any]]) -> None:
    fields = [
        "dataset_id",
        "dataset_role",
        "model",
        "mode",
        "recall_at_5",
        "recall_at_10",
        "mrr_at_10",
        "ndcg_at_10",
        "negative_rejection_rate",
        "wrong_collection_rate_at_10",
        "hot_query_median_seconds",
        "hot_query_p95_seconds",
        "build_wall_seconds",
        "model_cold_load_seconds",
        "peak_rss_bytes",
        "index_bytes",
    ]
    with (TASK_DIR / "comparison.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for payload in candidate_payloads:
            for dataset_id, dataset in payload["datasets"].items():
                for mode in ("vector", "hybrid"):
                    mode_payload = dataset["modes"][mode]
                    metrics = mode_payload["metrics"]
                    writer.writerow(
                        {
                            "dataset_id": dataset_id,
                            "dataset_role": dataset["dataset_role"],
                            "model": payload["model"]["model_id"],
                            "mode": mode,
                            "recall_at_5": metrics["recall_at_5"],
                            "recall_at_10": metrics["recall_at_10"],
                            "mrr_at_10": metrics["mrr_at_10"],
                            "ndcg_at_10": metrics["ndcg_at_10"],
                            "negative_rejection_rate": metrics[
                                "negative_rejection_rate"
                            ],
                            "wrong_collection_rate_at_10": metrics[
                                "wrong_collection_rate_at_10"
                            ],
                            "hot_query_median_seconds": mode_payload["latency"][
                                "median_seconds"
                            ],
                            "hot_query_p95_seconds": mode_payload["latency"][
                                "p95_seconds"
                            ],
                            "build_wall_seconds": payload["resource"][
                                "build_wall_seconds"
                            ],
                            "model_cold_load_seconds": payload["resource"][
                                "query_model_cold_load_seconds"
                            ],
                            "peak_rss_bytes": payload["resource"]["peak_rss_bytes"],
                            "index_bytes": payload["resource"]["index_bytes"],
                        }
                    )


def run_parent() -> None:
    if file_sha256(QRELS_PATH) != EXPECTED_QRELS_SHA256:
        raise RuntimeError("冻结 qrels 哈希与驱动预注册值不一致")
    from torch import backends

    corpus_contract = freeze_corpus()
    contract = {
        "schema": "embedding-bakeoff-run-contract/v1",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "qrels_sha256": EXPECTED_QRELS_SHA256,
        "implementation_hashes": {
            relative_path: file_sha256(REPO_ROOT / relative_path)
            for relative_path in IMPLEMENTATION_FILES
        },
        "mps_built": bool(backends.mps.is_built()),
        "mps_available": bool(backends.mps.is_available()),
        **corpus_contract,
    }
    contract_path = RUN_CACHE / "run_contract.json"
    write_json(contract_path, contract)
    environment = dict(os.environ)
    environment.update(
        {
            "HF_HOME": str(MODEL_CACHE),
            "HF_HUB_CACHE": str(MODEL_CACHE),
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
        }
    )
    for spec in load_manifest():
        verify_contract(contract)
        subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--worker",
                str(spec["slug"]),
                "--contract",
                str(contract_path),
            ],
            cwd=REPO_ROOT,
            env=environment,
            check=True,
        )
    candidate_payloads = [
        json.loads(
            (RUN_CACHE / f"{spec['slug']}-result.json").read_text(encoding="utf-8")
        )
        for spec in load_manifest()
    ]
    lexical_identical = compare_lexical(candidate_payloads)
    if not lexical_identical:
        raise RuntimeError("候选间词法结果不一致，共同通道合同失效")
    combined = {
        "schema": "embedding-bakeoff-results/v1",
        "run_contract": contract,
        "lexical_results_identical_across_candidates": lexical_identical,
        "candidates": candidate_payloads,
    }
    write_json(TASK_DIR / "raw_results.json", combined)
    write_comparison(candidate_payloads)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行固定合同的嵌入模型真实对照")
    parser.add_argument("--worker", choices=[item["slug"] for item in load_manifest()])
    parser.add_argument("--contract", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.worker:
        if args.contract is None:
            raise SystemExit("工作进程缺少 --contract")
        run_worker(args.worker, args.contract)
    else:
        run_parent()


if __name__ == "__main__":
    main()
