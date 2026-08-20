from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List, Mapping, Optional

import numpy as np

from .config import SearchConfig
from .embeddings import EmbeddingBackend, vector_scores
from .lexical import lexical_search
from .ranking import RankedPaper, aggregate_chunks, aggregate_papers, reciprocal_rank_fusion
from .storage import fetch_chunks, fetch_note_views, fetch_notes, load_embeddings
from .types import RankedChunk, RankedNote


def _vector_ranking(
    connection: sqlite3.Connection, query_vector: np.ndarray
) -> List[RankedNote]:
    chunk_ids, note_ids, vectors = load_embeddings(connection)
    if not len(chunk_ids):
        return []
    scores = vector_scores(query_vector, vectors)
    order = np.argsort(-scores, kind="stable")
    chunks = [
        RankedChunk(int(chunk_ids[index]), int(note_ids[index]), float(scores[index]))
        for index in order
    ]
    return aggregate_chunks(chunks)


def _note_to_paper(connection: sqlite3.Connection) -> Dict[int, str]:
    return {
        int(row["id"]): str(row["paper_id"])
        for row in connection.execute("SELECT id,paper_id FROM notes")
    }


def _rrf_contribution(rank: Optional[int], constant: int) -> Optional[float]:
    return 1.0 / (constant + rank) if rank is not None else None


def _select_evidence(
    mode: str,
    lexical: Optional[RankedPaper],
    vector: Optional[RankedPaper],
    lexical_contribution: Optional[float],
    vector_contribution: Optional[float],
) -> RankedPaper:
    if mode == "lexical":
        if lexical is None:
            raise RuntimeError("词法结果缺少证据块")
        return lexical
    if mode == "vector":
        if vector is None:
            raise RuntimeError("向量结果缺少证据块")
        return vector
    if lexical is None:
        if vector is None:
            raise RuntimeError("混合结果缺少证据块")
        return vector
    if vector is None:
        return lexical
    return (
        vector
        if (vector_contribution or 0.0) > (lexical_contribution or 0.0)
        else lexical
    )


def _block_payload(
    channel: str,
    ranked: Optional[RankedPaper],
    chunks: Mapping[int, sqlite3.Row],
    notes: Mapping[int, sqlite3.Row],
) -> Optional[Dict[str, object]]:
    if ranked is None:
        return None
    chunk = chunks[ranked.chunk_id]
    note = notes[ranked.note_id]
    return {
        "channel": channel,
        "chunk_id": ranked.chunk_id,
        "chunk_key": chunk["chunk_key"],
        "note_id": note["note_id"],
        "note_path": note["path"],
        "heading": chunk["heading"],
        "page_hint": chunk["page_hint"],
        "score": ranked.score,
        "snippet": str(chunk["text"])[:280].replace("\n", " "),
    }


def search_local(
    connection: sqlite3.Connection,
    query: str,
    mode: str,
    top_k: int,
    config: SearchConfig,
    cache_folder: Optional[Path] = None,
    local_files_only: bool = False,
    device: str = "auto",
    backend: Optional[EmbeddingBackend] = None,
) -> List[Dict[str, object]]:
    if mode not in {"lexical", "vector", "hybrid"}:
        raise ValueError(f"未知检索模式：{mode}")
    note_to_paper = _note_to_paper(connection)
    lexical_notes = (
        aggregate_chunks(lexical_search(connection, query)) if mode != "vector" else []
    )
    lexical = aggregate_papers(lexical_notes, note_to_paper)
    vector_notes: List[RankedNote] = []
    if mode != "lexical":
        if backend is None:
            backend = EmbeddingBackend(
                config.model_name,
                config.model_revision,
                cache_folder=cache_folder,
                local_files_only=local_files_only,
                device=device,
            )
        vector_notes = _vector_ranking(connection, backend.encode_query(query))
        if not vector_notes:
            raise RuntimeError("索引没有向量；请执行完整 build，不能以纯词法索引运行向量检索")
    vector = aggregate_papers(vector_notes, note_to_paper)

    lexical_rank = {item.paper_id: rank for rank, item in enumerate(lexical, start=1)}
    vector_rank = {item.paper_id: rank for rank, item in enumerate(vector, start=1)}
    lexical_map = {item.paper_id: item for item in lexical}
    vector_map = {item.paper_id: item for item in vector}
    if mode == "lexical":
        ordered = [(item.paper_id, item.score) for item in lexical]
    elif mode == "vector":
        ordered = [(item.paper_id, item.score) for item in vector]
    else:
        fused = reciprocal_rank_fusion(
            {
                "lexical": [item.paper_id for item in lexical],
                "vector": [item.paper_id for item in vector],
            },
            config.rrf_constant,
        )
        ordered = sorted(fused.items(), key=lambda item: (-item[1], item[0]))
    ordered = ordered[:top_k]

    selected: Dict[str, RankedPaper] = {}
    channel_by_paper: Dict[str, str] = {}
    for paper_id, _ in ordered:
        lexical_contribution = _rrf_contribution(
            lexical_rank.get(paper_id), config.rrf_constant
        )
        vector_contribution = _rrf_contribution(
            vector_rank.get(paper_id), config.rrf_constant
        )
        evidence = _select_evidence(
            mode,
            lexical_map.get(paper_id),
            vector_map.get(paper_id),
            lexical_contribution,
            vector_contribution,
        )
        selected[paper_id] = evidence
        channel_by_paper[paper_id] = (
            "lexical" if evidence is lexical_map.get(paper_id) else "vector"
        )

    ranked_blocks = [
        item
        for paper_id, _ in ordered
        for item in (lexical_map.get(paper_id), vector_map.get(paper_id))
        if item is not None
    ]
    chunk_rows = fetch_chunks(connection, [item.chunk_id for item in ranked_blocks])
    note_rows = fetch_notes(connection, [item.note_id for item in ranked_blocks])
    views = fetch_note_views(connection, [paper_id for paper_id, _ in ordered])

    results: List[Dict[str, object]] = []
    for display_rank, (paper_id, score) in enumerate(ordered, start=1):
        evidence = selected[paper_id]
        evidence_note = note_rows[evidence.note_id]
        lexical_contribution = _rrf_contribution(
            lexical_rank.get(paper_id), config.rrf_constant
        )
        vector_contribution = _rrf_contribution(
            vector_rank.get(paper_id), config.rrf_constant
        )
        lexical_block = _block_payload(
            "lexical", lexical_map.get(paper_id), chunk_rows, note_rows
        )
        vector_block = _block_payload(
            "vector", vector_map.get(paper_id), chunk_rows, note_rows
        )
        evidence_block = (
            lexical_block if channel_by_paper[paper_id] == "lexical" else vector_block
        )
        if evidence_block is None:
            raise RuntimeError("最终证据块不存在")
        note_views = [
            {
                "note_id": row["note_id"],
                "note_path": row["path"],
                "title": row["title"],
                "source_pdf": row["source_pdf"],
                "is_evidence_view": int(row["id"]) == evidence.note_id,
            }
            for row in views[paper_id]
        ]
        results.append(
            {
                "rank": display_rank,
                "paper_id": paper_id,
                "title": evidence_note["title"],
                "note_id": evidence_note["note_id"],
                "note_path": evidence_note["path"],
                "note_views": note_views,
                "note_view_count": len(note_views),
                "source_pdf": evidence_note["source_pdf"],
                "page_hint": evidence_block["page_hint"],
                "doi": evidence_note["doi"],
                "arxiv_id": evidence_note["arxiv_id"],
                "lexical_rank": lexical_rank.get(paper_id),
                "lexical_score": (
                    lexical_map[paper_id].score if paper_id in lexical_map else None
                ),
                "lexical_rrf_contribution": lexical_contribution if mode == "hybrid" else None,
                "vector_rank": vector_rank.get(paper_id),
                "vector_score": (
                    vector_map[paper_id].score if paper_id in vector_map else None
                ),
                "vector_rrf_contribution": vector_contribution if mode == "hybrid" else None,
                "fusion_score": score if mode == "hybrid" else None,
                "lexical_block": lexical_block,
                "vector_block": vector_block,
                "evidence_channel": channel_by_paper[paper_id],
                "evidence_block": evidence_block,
                "snippet": evidence_block["snippet"],
                "evidence_level": "本地结构化全文笔记",
            }
        )
    return results
