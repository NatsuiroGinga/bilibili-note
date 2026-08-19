from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Sequence

from .types import RankedChunk, RankedNote


def aggregate_chunks(chunks: Iterable[RankedChunk]) -> List[RankedNote]:
    best: Dict[int, RankedNote] = {}
    for item in chunks:
        current = best.get(item.note_id)
        if current is None or item.score > current.score:
            best[item.note_id] = RankedNote(item.note_id, item.score, item.chunk_id)
    return sorted(best.values(), key=lambda item: (-item.score, item.note_id))


def reciprocal_rank_fusion(
    rankings: Mapping[str, Sequence[int]], constant: int
) -> Dict[int, float]:
    if constant <= 0:
        raise ValueError("RRF 常数必须为正数")
    scores: Dict[int, float] = {}
    for ranking in rankings.values():
        for rank, note_id in enumerate(ranking, start=1):
            scores[note_id] = scores.get(note_id, 0.0) + 1.0 / (constant + rank)
    return scores
