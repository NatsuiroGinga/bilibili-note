from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from .config import SearchConfig
from .search import search_local


def evaluate_queries(
    connection: sqlite3.Connection,
    query_path: Path,
    config: SearchConfig,
    cache_folder: Optional[Path] = None,
    local_files_only: bool = False,
) -> Dict[str, object]:
    specification = json.loads(query_path.read_text(encoding="utf-8"))
    top_k = int(specification["top_k"])
    modes = ("lexical", "vector", "hybrid")
    details: List[Dict[str, object]] = []
    summary = {mode: {"hits": 0, "reciprocal_rank_sum": 0.0} for mode in modes}
    for case in specification["queries"]:
        case_result: Dict[str, object] = {
            "query": case["query"],
            "relevant_paths": case["relevant_paths"],
            "basis": case["basis"],
            "modes": {},
        }
        relevant = set(case["relevant_paths"])
        for mode in modes:
            results = search_local(
                connection,
                case["query"],
                mode,
                top_k,
                config,
                cache_folder=cache_folder,
                local_files_only=local_files_only,
            )
            hit_rank = next(
                (int(item["rank"]) for item in results if item["note_path"] in relevant),
                None,
            )
            case_result["modes"][mode] = {
                "hit": hit_rank is not None,
                "rank": hit_rank,
                "top_paths": [item["note_path"] for item in results],
            }
            if hit_rank is not None:
                summary[mode]["hits"] += 1
                summary[mode]["reciprocal_rank_sum"] += 1.0 / hit_rank
        details.append(case_result)
    count = len(details)
    for values in summary.values():
        values["query_count"] = count
        values["hit_rate_at_k"] = values["hits"] / count if count else 0.0
        values["mean_reciprocal_rank"] = (
            values.pop("reciprocal_rank_sum") / count if count else 0.0
        )
    return {
        "evaluation_version": specification["version"],
        "frozen_before_first_run": specification["frozen_before_first_run"],
        "top_k": top_k,
        "summary": summary,
        "queries": details,
        "interpretation": "该小型集合只检查已登记目标能否进入 Top-k，不构成方法有效性实验。",
    }
