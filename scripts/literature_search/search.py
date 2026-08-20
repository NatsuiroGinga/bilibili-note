from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .config import SearchConfig
from .embeddings import EmbeddingBackend, vector_scores
from .lexical import lexical_search
from .ranking import aggregate_chunks, reciprocal_rank_fusion
from .storage import fetch_chunks, fetch_notes, load_embeddings
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


def search_local(
    connection: sqlite3.Connection,
    query: str,
    mode: str,
    top_k: int,
    config: SearchConfig,
    cache_folder: Optional[Path] = None,
    local_files_only: bool = False,
) -> List[Dict[str, object]]:
    if mode not in {"lexical", "vector", "hybrid"}:
        raise ValueError(f"未知检索模式：{mode}")
    lexical = aggregate_chunks(lexical_search(connection, query)) if mode != "vector" else []
    vector: List[RankedNote] = []
    if mode != "lexical":
        backend = EmbeddingBackend(
            config.model_name,
            config.model_revision,
            cache_folder=cache_folder,
            local_files_only=local_files_only,
        )
        vector = _vector_ranking(connection, backend.encode_query(query))
        if not vector:
            raise RuntimeError("索引没有向量；请执行完整 build，不能以纯词法索引运行向量检索")

    lexical_rank = {item.note_id: rank for rank, item in enumerate(lexical, start=1)}
    vector_rank = {item.note_id: rank for rank, item in enumerate(vector, start=1)}
    lexical_map = {item.note_id: item for item in lexical}
    vector_map = {item.note_id: item for item in vector}
    if mode == "lexical":
        ordered = [(item.note_id, item.score) for item in lexical]
    elif mode == "vector":
        ordered = [(item.note_id, item.score) for item in vector]
    else:
        fused = reciprocal_rank_fusion(
            {
                "lexical": [item.note_id for item in lexical],
                "vector": [item.note_id for item in vector],
            },
            config.rrf_constant,
        )
        ordered = sorted(fused.items(), key=lambda item: (-item[1], item[0]))
    ordered = ordered[:top_k]
    note_rows = fetch_notes(connection, [item[0] for item in ordered])
    best_chunk_ids = []
    for note_id, _ in ordered:
        if note_id in lexical_map:
            best_chunk_ids.append(lexical_map[note_id].chunk_id)
        elif note_id in vector_map:
            best_chunk_ids.append(vector_map[note_id].chunk_id)
    chunk_rows = fetch_chunks(connection, best_chunk_ids)
    results: List[Dict[str, object]] = []
    for display_rank, (note_id, score) in enumerate(ordered, start=1):
        note = note_rows[note_id]
        selected = lexical_map.get(note_id) or vector_map.get(note_id)
        chunk = chunk_rows[selected.chunk_id] if selected else None
        snippet = str(chunk["text"])[:280].replace("\n", " ") if chunk else ""
        results.append(
            {
                "rank": display_rank,
                "title": note["title"],
                "note_path": note["path"],
                "source_pdf": note["source_pdf"],
                "page_hint": chunk["page_hint"] if chunk else None,
                "doi": note["doi"],
                "arxiv_id": note["arxiv_id"],
                "lexical_rank": lexical_rank.get(note_id),
                "lexical_score": lexical_map[note_id].score if note_id in lexical_map else None,
                "vector_rank": vector_rank.get(note_id),
                "vector_score": vector_map[note_id].score if note_id in vector_map else None,
                "fusion_score": score if mode == "hybrid" else None,
                "snippet": snippet,
                "evidence_level": "本地结构化全文笔记",
            }
        )
    return results
