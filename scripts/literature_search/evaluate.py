from __future__ import annotations

import json
import math
import sqlite3
import statistics
import time
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Set

from .config import REPO_ROOT, SearchConfig
from .embeddings import EmbeddingBackend
from .search import search_local


MODES = ("lexical", "vector", "hybrid")


def _percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _latency_summary(values: Sequence[float]) -> Dict[str, float | int]:
    return {
        "count": len(values),
        "mean": statistics.fmean(values) if values else 0.0,
        "median": statistics.median(values) if values else 0.0,
        "p95": _percentile(values, 0.95),
        "min": min(values) if values else 0.0,
        "max": max(values) if values else 0.0,
    }


def _ndcg(results: Sequence[Mapping[str, object]], relevant: Set[str], k: int) -> float:
    if not relevant:
        return 0.0
    gains = [1.0 if str(item["paper_id"]) in relevant else 0.0 for item in results[:k]]
    dcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, start=1))
    ideal_count = min(len(relevant), k)
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_count + 1))
    return dcg / ideal if ideal else 0.0


def _relevant_papers(
    case: Mapping[str, object], path_to_paper: Mapping[str, str]
) -> tuple[Set[str], List[str]]:
    papers = {str(value) for value in case.get("relevant_paper_ids", [])}
    missing_paths: List[str] = []
    for path in case.get("relevant_paths", []):
        paper_id = path_to_paper.get(str(path))
        if paper_id is None:
            missing_paths.append(str(path))
        else:
            papers.add(paper_id)
    return papers, missing_paths


def _source_exists(repo_root: Path, source_pdf: object) -> bool:
    if not source_pdf:
        return False
    path = Path(str(source_pdf)).expanduser()
    return path.is_file() if path.is_absolute() else (repo_root / path).is_file()


def _block_hit(
    result: Mapping[str, object], chunk_ids: Set[int], chunk_keys: Set[str]
) -> Optional[bool]:
    if not chunk_ids and not chunk_keys:
        return None
    evidence = result.get("evidence_block")
    if not isinstance(evidence, Mapping):
        return False
    return int(evidence["chunk_id"]) in chunk_ids or str(evidence["chunk_key"]) in chunk_keys


def evaluate_queries(
    connection: sqlite3.Connection,
    query_path: Path,
    config: SearchConfig,
    cache_folder: Optional[Path] = None,
    local_files_only: bool = False,
    device: str = "auto",
    repo_root: Optional[Path] = None,
) -> Dict[str, object]:
    specification = json.loads(query_path.read_text(encoding="utf-8"))
    requested_top_k = int(specification.get("top_k", 10))
    evaluation_depth = max(requested_top_k, 10)
    actual_repo_root = (repo_root or REPO_ROOT).resolve()
    path_to_paper = {
        str(row["path"]): str(row["paper_id"])
        for row in connection.execute("SELECT path,paper_id FROM notes")
    }
    backend = EmbeddingBackend(
        config.model_name,
        config.model_revision,
        cache_folder=cache_folder,
        local_files_only=local_files_only,
        device=device,
    )
    accumulators: Dict[str, Dict[str, object]] = {
        mode: {
            "recall_5": [],
            "recall_10": [],
            "reciprocal_ranks": [],
            "ndcg_10": [],
            "latencies": [],
            "retrieved_5": 0,
            "retrieved_10": 0,
            "total_relevance": 0,
            "negative_return_counts": [],
            "duplicate_paper_results": 0,
            "relevant_top10": 0,
            "source_pdf_nonempty": 0,
            "source_pdf_existing": 0,
            "page_hint_nonempty": 0,
            "block_labeled": 0,
            "block_hits": 0,
            "evidence_explanation_mismatches": 0,
            "evidence_channels": {"lexical": 0, "vector": 0},
        }
        for mode in MODES
    }
    details: List[Dict[str, object]] = []
    channel_coverage = {"lexical_only": 0, "vector_only": 0, "both": 0, "neither": 0}
    positive_count = 0
    negative_count = 0

    for position, case in enumerate(specification["queries"], start=1):
        relevant, missing_paths = _relevant_papers(case, path_to_paper)
        chunk_ids = {int(value) for value in case.get("relevant_chunk_ids", [])}
        chunk_keys = {str(value) for value in case.get("relevant_chunk_keys", [])}
        case_result: Dict[str, object] = {
            "id": case.get("id", f"Q{position:02d}"),
            "query": case["query"],
            "category": case.get("category"),
            "relevant_paths": case.get("relevant_paths", []),
            "relevant_paper_ids": sorted(relevant),
            "missing_relevant_paths": missing_paths,
            "basis": case.get("basis"),
            "modes": {},
        }
        mode_results: Dict[str, List[Dict[str, object]]] = {}
        if relevant:
            positive_count += 1
        else:
            negative_count += 1
        for mode in MODES:
            started = time.perf_counter()
            results = search_local(
                connection,
                str(case["query"]),
                mode,
                evaluation_depth,
                config,
                cache_folder=cache_folder,
                local_files_only=local_files_only,
                device=device,
                backend=backend if mode != "lexical" else None,
            )
            latency_ms = (time.perf_counter() - started) * 1000.0
            mode_results[mode] = results
            accumulator = accumulators[mode]
            accumulator["latencies"].append(latency_ms)
            paper_ids = [str(item["paper_id"]) for item in results]
            duplicate_count = len(paper_ids) - len(set(paper_ids))
            accumulator["duplicate_paper_results"] += duplicate_count
            ranks = [
                rank
                for rank, paper_id in enumerate(paper_ids, start=1)
                if paper_id in relevant
            ]
            first_rank = ranks[0] if ranks else None
            hit_5 = sum(1 for paper_id in paper_ids[:5] if paper_id in relevant)
            hit_10 = sum(1 for paper_id in paper_ids[:10] if paper_id in relevant)
            if relevant:
                accumulator["recall_5"].append(hit_5 / len(relevant))
                accumulator["recall_10"].append(hit_10 / len(relevant))
                accumulator["reciprocal_ranks"].append(
                    1.0 / first_rank if first_rank and first_rank <= 10 else 0.0
                )
                accumulator["ndcg_10"].append(_ndcg(results, relevant, 10))
                accumulator["retrieved_5"] += hit_5
                accumulator["retrieved_10"] += hit_10
                accumulator["total_relevance"] += len(relevant)
            else:
                accumulator["negative_return_counts"].append(len(results))

            top_results = []
            query_block_hits: List[bool] = []
            for item in results:
                is_relevant = str(item["paper_id"]) in relevant
                block_hit = _block_hit(item, chunk_ids, chunk_keys)
                if block_hit is not None:
                    query_block_hits.append(block_hit)
                if is_relevant:
                    accumulator["relevant_top10"] += 1
                    accumulator["source_pdf_nonempty"] += int(bool(item.get("source_pdf")))
                    accumulator["source_pdf_existing"] += int(
                        _source_exists(actual_repo_root, item.get("source_pdf"))
                    )
                    accumulator["page_hint_nonempty"] += int(bool(item.get("page_hint")))
                channel = str(item["evidence_channel"])
                accumulator["evidence_channels"][channel] += 1
                lexical_contribution = item.get("lexical_rrf_contribution")
                vector_contribution = item.get("vector_rrf_contribution")
                if mode == "hybrid" and lexical_contribution is not None and vector_contribution is not None:
                    expected = (
                        "vector"
                        if float(vector_contribution) > float(lexical_contribution)
                        else "lexical"
                    )
                    accumulator["evidence_explanation_mismatches"] += int(channel != expected)
                top_results.append(
                    {
                        "rank": item["rank"],
                        "paper_id": item["paper_id"],
                        "note_path": item["note_path"],
                        "note_views": [view["note_path"] for view in item["note_views"]],
                        "relevant": is_relevant,
                        "lexical_rank": item["lexical_rank"],
                        "vector_rank": item["vector_rank"],
                        "evidence_channel": channel,
                        "evidence_chunk_id": item["evidence_block"]["chunk_id"],
                        "evidence_chunk_key": item["evidence_block"]["chunk_key"],
                        "block_hit": block_hit,
                        "page_hint": item["page_hint"],
                        "source_pdf": item["source_pdf"],
                    }
                )
            query_block_hit = any(query_block_hits) if query_block_hits else None
            if query_block_hit is not None:
                accumulator["block_labeled"] += 1
                accumulator["block_hits"] += int(query_block_hit)
            case_result["modes"][mode] = {
                "first_relevant_rank": first_rank,
                "recall_at_5": hit_5 / len(relevant) if relevant else None,
                "recall_at_10": hit_10 / len(relevant) if relevant else None,
                "reciprocal_rank_at_10": (
                    1.0 / first_rank if first_rank and first_rank <= 10 else 0.0
                )
                if relevant
                else None,
                "ndcg_at_10": _ndcg(results, relevant, 10) if relevant else None,
                "latency_ms": latency_ms,
                "duplicate_paper_results": duplicate_count,
                "block_hit_at_k": query_block_hit,
                "top_results": top_results,
            }
        if relevant:
            lexical_top = {str(item["paper_id"]) for item in mode_results["lexical"][:10]}
            vector_top = {str(item["paper_id"]) for item in mode_results["vector"][:10]}
            per_case_coverage = {
                "lexical_only": sorted((relevant & lexical_top) - vector_top),
                "vector_only": sorted((relevant & vector_top) - lexical_top),
                "both": sorted(relevant & lexical_top & vector_top),
                "neither": sorted(relevant - lexical_top - vector_top),
            }
            case_result["channel_relevance_coverage"] = per_case_coverage
            for key, values in per_case_coverage.items():
                channel_coverage[key] += len(values)
        details.append(case_result)

    summary: Dict[str, Dict[str, object]] = {}
    for mode, accumulator in accumulators.items():
        total_relevance = int(accumulator["total_relevance"])
        block_labeled = int(accumulator["block_labeled"])
        summary[mode] = {
            "positive_query_count": positive_count,
            "negative_query_count": negative_count,
            "total_relevance_judgments": total_relevance,
            "macro_recall_at_5": statistics.fmean(accumulator["recall_5"])
            if accumulator["recall_5"]
            else 0.0,
            "macro_recall_at_10": statistics.fmean(accumulator["recall_10"])
            if accumulator["recall_10"]
            else 0.0,
            "micro_recall_at_5": int(accumulator["retrieved_5"]) / total_relevance
            if total_relevance
            else 0.0,
            "micro_recall_at_10": int(accumulator["retrieved_10"]) / total_relevance
            if total_relevance
            else 0.0,
            "mrr_at_10": statistics.fmean(accumulator["reciprocal_ranks"])
            if accumulator["reciprocal_ranks"]
            else 0.0,
            "ndcg_at_10": statistics.fmean(accumulator["ndcg_10"])
            if accumulator["ndcg_10"]
            else 0.0,
            "duplicate_paper_results": accumulator["duplicate_paper_results"],
            "latency_ms": _latency_summary(accumulator["latencies"]),
            "relevant_top10_count": accumulator["relevant_top10"],
            "relevant_top10_source_pdf_nonempty": accumulator["source_pdf_nonempty"],
            "relevant_top10_source_pdf_existing": accumulator["source_pdf_existing"],
            "relevant_top10_page_hint_nonempty": accumulator["page_hint_nonempty"],
            "block_judgment_count": block_labeled,
            "block_hit_rate": int(accumulator["block_hits"]) / block_labeled
            if block_labeled
            else None,
            "negative_query_return_counts": accumulator["negative_return_counts"],
            "negative_reliable_rejection_gate": False,
            "evidence_channel_counts": accumulator["evidence_channels"],
            "evidence_explanation_mismatch_count": accumulator[
                "evidence_explanation_mismatches"
            ],
        }
    summary["hybrid"]["relevant_channel_coverage_at_10"] = channel_coverage
    return {
        "evaluation_version": specification.get("version"),
        "frozen_before_first_run": specification.get("frozen_before_first_run"),
        "requested_top_k": requested_top_k,
        "evaluation_depth": evaluation_depth,
        "vector_device": backend.device,
        "vector_device_fallback": backend.fallback_reason,
        "latency_scope": "嵌入后端初始化完成后的单次 search_local 墙钟时间",
        "summary": summary,
        "queries": details,
        "negative_query_policy": (
            "当前没有经独立开发集冻结的可靠拒答门；负例只报告返回数量，"
            "不得使用本冻结查询集事后选择阈值。"
        ),
        "block_judgment_policy": (
            "仅当查询显式提供 relevant_chunk_ids 或 relevant_chunk_keys 时计算块级命中；"
            "缺少块标注时返回 null，不用相关笔记路径冒充块级真值。"
        ),
        "interpretation": "该目的性小样本只作回归门禁，不构成普遍检索有效性结论。",
    }
