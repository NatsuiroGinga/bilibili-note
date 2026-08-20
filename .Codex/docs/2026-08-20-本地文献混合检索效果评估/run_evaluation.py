"""在冻结查询集上比较本地词法、向量和混合检索。"""

from __future__ import annotations

import json
import math
import statistics
import sys
import time
from pathlib import Path
from typing import Any

EVALUATION_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALUATION_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.literature_search.config import load_config
from scripts.literature_search.embeddings import EmbeddingBackend
from scripts.literature_search.search import search_local
from scripts.literature_search.storage import connect


QUERY_PATH = EVALUATION_DIR / "frozen_queries.json"
INDEX_PATH = REPO_ROOT / ".cache/literature-search/eval-final-index.sqlite3"
MODEL_CACHE = REPO_ROOT / ".cache/literature-search/model-cache"
RAW_OUTPUT = EVALUATION_DIR / "raw_results.json"
METRICS_OUTPUT = EVALUATION_DIR / "metrics.json"
MODES = ("lexical", "vector", "hybrid")


def percentile(values: list[float], probability: float) -> float:
    """用线性插值计算百分位数，避免引入额外依赖。"""
    ordered = sorted(values)
    if not ordered:
        return math.nan
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def source_path_exists(source_pdf: Any) -> bool:
    if not isinstance(source_pdf, str) or not source_pdf.strip():
        return False
    value = source_pdf.strip().strip('"').strip("'")
    if value.startswith("[[") and value.endswith("]]" ):
        value = value[2:-2]
    value = value.split("|", maxsplit=1)[0]
    path = Path(value).expanduser()
    return (path if path.is_absolute() else REPO_ROOT / path).is_file()


def summarize(raw: dict[str, Any]) -> dict[str, Any]:
    positive = [case for case in raw["queries"] if case["relevant_paths"]]
    negative = [case for case in raw["queries"] if not case["relevant_paths"]]
    total_relevance = sum(len(case["relevant_paths"]) for case in positive)
    summary: dict[str, Any] = {
        "positive_query_count": len(positive),
        "negative_query_count": len(negative),
        "total_relevance_judgments": total_relevance,
        "modes": {},
    }
    for mode in MODES:
        recalls_at_5: list[float] = []
        recalls_at_10: list[float] = []
        reciprocal_ranks: list[float] = []
        latencies: list[float] = []
        hit_queries_at_5 = 0
        hit_queries_at_10 = 0
        retrieved_relevant_at_5 = 0
        retrieved_relevant_at_10 = 0
        source_pdf_nonempty = 0
        source_pdf_existing = 0
        page_hint_nonempty = 0
        for case in raw["queries"]:
            mode_result = case["modes"][mode]
            latencies.append(mode_result["latency_ms"])
            if not case["relevant_paths"]:
                continue
            relevant = set(case["relevant_paths"])
            top_5 = {item["note_path"] for item in mode_result["results"][:5]}
            top_10 = {item["note_path"] for item in mode_result["results"][:10]}
            hit_5 = len(relevant & top_5)
            hit_10 = len(relevant & top_10)
            retrieved_relevant_at_5 += hit_5
            retrieved_relevant_at_10 += hit_10
            recalls_at_5.append(hit_5 / len(relevant))
            recalls_at_10.append(hit_10 / len(relevant))
            hit_queries_at_5 += int(hit_5 > 0)
            hit_queries_at_10 += int(hit_10 > 0)
            first_rank = mode_result["first_relevant_rank"]
            reciprocal_ranks.append(0.0 if first_rank is None else 1.0 / first_rank)
            for item in mode_result["results"]:
                if item["note_path"] not in relevant:
                    continue
                source_pdf_nonempty += int(bool(item["source_pdf"]))
                source_pdf_existing += int(source_path_exists(item["source_pdf"]))
                page_hint_nonempty += int(bool(item["page_hint"]))
        negative_counts = [len(case["modes"][mode]["results"]) for case in negative]
        summary["modes"][mode] = {
            "macro_recall_at_5": statistics.fmean(recalls_at_5),
            "macro_recall_at_10": statistics.fmean(recalls_at_10),
            "micro_recall_at_5": retrieved_relevant_at_5 / total_relevance,
            "micro_recall_at_10": retrieved_relevant_at_10 / total_relevance,
            "mrr_at_10": statistics.fmean(reciprocal_ranks),
            "hit_rate_at_5": hit_queries_at_5 / len(positive),
            "hit_rate_at_10": hit_queries_at_10 / len(positive),
            "latency_ms": {
                "count": len(latencies),
                "mean": statistics.fmean(latencies),
                "median": statistics.median(latencies),
                "p95": percentile(latencies, 0.95),
                "min": min(latencies),
                "max": max(latencies),
            },
            "relevant_top10_source_pdf_nonempty": source_pdf_nonempty,
            "relevant_top10_source_pdf_existing": source_pdf_existing,
            "relevant_top10_page_hint_nonempty": page_hint_nonempty,
            "negative_query_return_counts": negative_counts,
            "negative_query_abstention_count": sum(count == 0 for count in negative_counts),
        }
    return summary


def main() -> None:
    specification = json.loads(QUERY_PATH.read_text(encoding="utf-8"))
    config = load_config()
    connection = connect(INDEX_PATH, readonly=True)
    backend_started = time.perf_counter()
    backend = EmbeddingBackend(
        config.model_name,
        config.model_revision,
        cache_folder=MODEL_CACHE,
        local_files_only=True,
        device="cpu",
    )
    backend_load_seconds = time.perf_counter() - backend_started

    # 预热不使用冻结查询，仅排除首次线性代数调用的一次性开销。
    search_local(
        connection,
        "retrieval latency warmup",
        "hybrid",
        1,
        config,
        cache_folder=MODEL_CACHE,
        local_files_only=True,
        device="cpu",
        backend=backend,
    )

    raw: dict[str, Any] = {
        "evaluation_version": specification["version"],
        "frozen_at": specification["frozen_at"],
        "index_path": str(INDEX_PATH.relative_to(REPO_ROOT)),
        "model_name": config.model_name,
        "model_revision": config.model_revision,
        "device": backend.device,
        "device_fallback": backend.fallback_reason,
        "backend_load_seconds": backend_load_seconds,
        "latency_protocol": "单进程、CPU、模型只加载一次，一条非评测查询预热后记录 search_local 墙钟；模式顺序按查询循环轮转。",
        "queries": [],
    }
    for query_index, case in enumerate(specification["queries"]):
        case_result: dict[str, Any] = {
            "id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "relevant_paths": case["relevant_paths"],
            "modes": {},
        }
        ordered_modes = MODES[query_index % len(MODES) :] + MODES[: query_index % len(MODES)]
        for mode in ordered_modes:
            started = time.perf_counter()
            results = search_local(
                connection,
                case["query"],
                mode,
                specification["top_k"],
                config,
                cache_folder=MODEL_CACHE,
                local_files_only=True,
                device="cpu",
                backend=backend if mode != "lexical" else None,
            )
            latency_ms = (time.perf_counter() - started) * 1000.0
            relevant = set(case["relevant_paths"])
            relevant_ranks = [
                int(item["rank"])
                for item in results
                if item["note_path"] in relevant
            ]
            case_result["modes"][mode] = {
                "latency_ms": latency_ms,
                "first_relevant_rank": min(relevant_ranks) if relevant_ranks else None,
                "relevant_ranks": relevant_ranks,
                "results": results,
            }
        raw["queries"].append(case_result)
    connection.close()

    metrics = summarize(raw)
    RAW_OUTPUT.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    METRICS_OUTPUT.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
