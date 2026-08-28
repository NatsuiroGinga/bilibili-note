"""在真实测试集上评测本地检索的 Recall@5 / Recall@10 / MRR / nDCG@10。

独立脚本，不修改冻结的 scripts/literature_search/evaluate.py，
以避免与并行进行的向量修复任务发生文件冲突。

用法：
    python3 .Codex/docs/RWKV/litsearch_precision/evaluate_real.py --modes lexical
    python3 .Codex/docs/RWKV/litsearch_precision/evaluate_real.py --modes lexical,vector,hybrid
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from scripts.literature_search.config import load_config  # noqa: E402
from scripts.literature_search.search import search_local  # noqa: E402
from scripts.literature_search.storage import connect  # noqa: E402

QUERY_PATH = REPO_ROOT / "scripts/literature_search/evaluation_queries_real.json"


def recall_at_k(ranked: Sequence[str], relevant: set, k: int) -> float:
    """Recall@k：前 k 条中命中的相关文档数除以相关文档总数。"""
    if not relevant:
        return 0.0
    return len(set(ranked[:k]) & relevant) / len(relevant)


def reciprocal_rank(ranked: Sequence[str], relevant: set) -> float:
    """第一条相关文档排名的倒数。"""
    for position, path in enumerate(ranked, start=1):
        if path in relevant:
            return 1.0 / position
    return 0.0


def ndcg_at_k(ranked: Sequence[str], relevant: set, k: int) -> float:
    """二元增益的 nDCG@k，折损为 1/log2(rank+1)。"""
    if not relevant:
        return 0.0
    dcg = sum(
        1.0 / math.log2(position + 1)
        for position, path in enumerate(ranked[:k], start=1)
        if path in relevant
    )
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(position + 1) for position in range(1, ideal_hits + 1))
    return dcg / idcg if idcg else 0.0


def validate_paths(specification: dict) -> List[str]:
    """核验测试集中登记的每条路径都真实存在。"""
    missing: List[str] = []
    for case in specification["queries"]:
        for path in case["relevant_paths"]:
            if not (REPO_ROOT / path).is_file():
                missing.append(f"{case['id']}: {path}")
    return missing


def evaluate(
    modes: Sequence[str],
    index_path: Optional[Path] = None,
    cache_folder: Optional[Path] = None,
    local_files_only: bool = False,
    top_k: int = 10,
) -> dict:
    config = load_config()
    resolved = index_path or config.resolve_index_path(REPO_ROOT)
    specification = json.loads(QUERY_PATH.read_text(encoding="utf-8"))

    missing = validate_paths(specification)
    if missing:
        raise RuntimeError("测试集登记了不存在的路径：\n  " + "\n  ".join(missing))

    connection = connect(resolved, readonly=True)
    details: List[Dict[str, object]] = []
    totals = {
        mode: {"recall_at_5": 0.0, "recall_at_10": 0.0, "mrr": 0.0, "ndcg_at_10": 0.0}
        for mode in modes
    }
    by_intent: Dict[str, Dict[str, Dict[str, float]]] = {}

    for case in specification["queries"]:
        relevant = set(case["relevant_paths"])
        record: Dict[str, object] = {
            "id": case["id"],
            "intent": case["intent"],
            "query": case["query"],
            "relevant_count": len(relevant),
            "modes": {},
        }
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
            ranked = [str(item["note_path"]) for item in results]
            scores = {
                "recall_at_5": recall_at_k(ranked, relevant, 5),
                "recall_at_10": recall_at_k(ranked, relevant, 10),
                "mrr": reciprocal_rank(ranked, relevant),
                "ndcg_at_10": ndcg_at_k(ranked, relevant, 10),
            }
            record["modes"][mode] = {
                **scores,
                "first_hit_rank": next(
                    (i for i, p in enumerate(ranked, start=1) if p in relevant), None
                ),
                "top_paths": ranked,
                "hit_ranks": [
                    i for i, p in enumerate(ranked, start=1) if p in relevant
                ],
            }
            for key, value in scores.items():
                totals[mode][key] += value
            slot = by_intent.setdefault(case["intent"], {})
            bucket = slot.setdefault(mode, {"n": 0.0, **{k: 0.0 for k in scores}})
            bucket["n"] += 1
            for key, value in scores.items():
                bucket[key] += value
        details.append(record)

    connection.close()
    count = len(details)
    summary = {
        mode: {key: value / count for key, value in totals[mode].items()}
        for mode in modes
    }
    for intent, per_mode in by_intent.items():
        for mode, bucket in per_mode.items():
            n = bucket.pop("n")
            for key in list(bucket):
                bucket[key] /= n
            bucket["query_count"] = int(n)

    return {
        "query_count": count,
        "top_k": top_k,
        "index_path": str(resolved),
        "summary": summary,
        "by_intent": by_intent,
        "queries": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modes", default="lexical")
    parser.add_argument("--index-path", default=None)
    parser.add_argument("--model-cache", default=None)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--out", default=None)
    arguments = parser.parse_args()

    modes = [m.strip() for m in arguments.modes.split(",") if m.strip()]
    report = evaluate(
        modes,
        index_path=Path(arguments.index_path) if arguments.index_path else None,
        cache_folder=Path(arguments.model_cache) if arguments.model_cache else None,
        local_files_only=arguments.offline,
    )

    print(f"测试集查询数：{report['query_count']}  索引：{report['index_path']}")
    print()
    print(f"{'模式':<10}{'Recall@5':>11}{'Recall@10':>12}{'MRR':>9}{'nDCG@10':>10}")
    print("-" * 52)
    for mode, values in report["summary"].items():
        print(
            f"{mode:<10}{values['recall_at_5']:>11.4f}{values['recall_at_10']:>12.4f}"
            f"{values['mrr']:>9.4f}{values['ndcg_at_10']:>10.4f}"
        )

    print()
    print("按意图分组：")
    for intent, per_mode in sorted(report["by_intent"].items()):
        for mode, values in per_mode.items():
            print(
                f"  {intent:<18}{mode:<9}n={values['query_count']:<3}"
                f"R@5={values['recall_at_5']:.3f} R@10={values['recall_at_10']:.3f} "
                f"MRR={values['mrr']:.3f} nDCG@10={values['ndcg_at_10']:.3f}"
            )

    if arguments.out:
        Path(arguments.out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\n明细已写入 {arguments.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
