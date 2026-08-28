"""变体 V4：把「分块→笔记」的聚合从取单块最高分改为 Top-N 分块得分求和。

用于检验 ranking.aggregate_chunks 的 max 池化是否是精度瓶颈。
不修改生产文件，只在本脚本内实现替代聚合并重跑同一测试集。
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from scripts.literature_search.config import load_config  # noqa: E402
from scripts.literature_search.lexical import lexical_search  # noqa: E402
from scripts.literature_search.storage import connect, fetch_notes  # noqa: E402
from scripts.literature_search.types import RankedChunk  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_real import ndcg_at_k, recall_at_k, reciprocal_rank  # noqa: E402

QUERY_PATH = REPO_ROOT / "scripts/literature_search/evaluation_queries_real.json"


def aggregate_top_n(chunks: Sequence[RankedChunk], top_n: int) -> List[tuple]:
    """每篇笔记取分数最高的 top_n 个分块求和，作为该笔记的得分。"""
    grouped: Dict[int, List[RankedChunk]] = defaultdict(list)
    for item in chunks:
        grouped[item.note_id].append(item)
    scored = []
    for note_id, items in grouped.items():
        items.sort(key=lambda c: -c.score)
        scored.append((note_id, sum(c.score for c in items[:top_n])))
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return scored


def run(index_path: Path, top_n: int, top_k: int = 10) -> dict:
    load_config()
    specification = json.loads(QUERY_PATH.read_text(encoding="utf-8"))
    connection = connect(index_path, readonly=True)
    totals = {"recall_at_5": 0.0, "recall_at_10": 0.0, "mrr": 0.0, "ndcg_at_10": 0.0}
    for case in specification["queries"]:
        relevant = set(case["relevant_paths"])
        chunks = lexical_search(connection, case["query"])
        ordered = aggregate_top_n(chunks, top_n)[:top_k]
        rows = fetch_notes(connection, [note_id for note_id, _ in ordered])
        ranked = [str(rows[note_id]["path"]) for note_id, _ in ordered]
        totals["recall_at_5"] += recall_at_k(ranked, relevant, 5)
        totals["recall_at_10"] += recall_at_k(ranked, relevant, 10)
        totals["mrr"] += reciprocal_rank(ranked, relevant)
        totals["ndcg_at_10"] += ndcg_at_k(ranked, relevant, 10)
    connection.close()
    count = len(specification["queries"])
    return {key: value / count for key, value in totals.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-path", required=True)
    parser.add_argument("--top-n", default="1,2,3,5", help="逗号分隔的候选 N")
    arguments = parser.parse_args()

    print(f"索引：{arguments.index_path}")
    print(f"{'聚合':<14}{'Recall@5':>11}{'Recall@10':>12}{'MRR':>9}{'nDCG@10':>10}")
    print("-" * 56)
    for raw in arguments.top_n.split(","):
        n = int(raw.strip())
        values = run(Path(arguments.index_path), n)
        label = "max(现状)" if n == 1 else f"top{n}求和"
        print(
            f"{label:<14}{values['recall_at_5']:>11.4f}{values['recall_at_10']:>12.4f}"
            f"{values['mrr']:>9.4f}{values['ndcg_at_10']:>10.4f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
