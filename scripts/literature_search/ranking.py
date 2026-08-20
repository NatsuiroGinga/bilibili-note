from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Hashable, Iterable, List, Mapping, Sequence, TypeVar

from .types import RankedChunk, RankedNote


RankingKey = TypeVar("RankingKey", bound=Hashable)


@dataclass(frozen=True)
class RankedPaper:
    paper_id: str
    note_id: int
    score: float
    chunk_id: int


def aggregate_chunks(chunks: Iterable[RankedChunk]) -> List[RankedNote]:
    best: Dict[int, RankedNote] = {}
    for item in chunks:
        current = best.get(item.note_id)
        if current is None or item.score > current.score:
            best[item.note_id] = RankedNote(item.note_id, item.score, item.chunk_id)
    return sorted(best.values(), key=lambda item: (-item.score, item.note_id))


def aggregate_papers(
    notes: Iterable[RankedNote], note_to_paper: Mapping[int, str]
) -> List[RankedPaper]:
    best: Dict[str, RankedPaper] = {}
    for item in notes:
        paper_id = note_to_paper[item.note_id]
        current = best.get(paper_id)
        candidate = RankedPaper(paper_id, item.note_id, item.score, item.chunk_id)
        if current is None or (candidate.score, -candidate.note_id) > (
            current.score,
            -current.note_id,
        ):
            best[paper_id] = candidate
    return sorted(best.values(), key=lambda item: (-item.score, item.paper_id))


def reciprocal_rank_fusion(
    rankings: Mapping[str, Sequence[RankingKey]], constant: int
) -> Dict[RankingKey, float]:
    if constant <= 0:
        raise ValueError("RRF 常数必须为正数")
    scores: Dict[RankingKey, float] = {}
    for ranking in rankings.values():
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (constant + rank)
    return scores
