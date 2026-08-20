from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Set, Tuple

import numpy as np

from .config import SearchConfig, resolve_model_reference
from .embeddings import EmbeddingBackend, vector_scores
from .lexical import lexical_search
from .ranking import RankedPaper, aggregate_chunks, aggregate_papers, reciprocal_rank_fusion
from .storage import fetch_chunks, fetch_note_views, fetch_notes, load_embeddings
from .types import RankedChunk, RankedNote


SCOPE_COLLECTIONS: Dict[str, Tuple[str, ...]] = {
    "paper": ("papers",),
    "project": ("route-control", "recovery", "plans", "reports", "research-notes"),
    "experiment": ("experiment-receipts",),
    "thesis": ("thesis-chapters", "output-deliverables"),
    "all": (
        "papers",
        "route-control",
        "recovery",
        "plans",
        "reports",
        "research-notes",
        "experiment-receipts",
        "thesis-chapters",
        "output-deliverables",
    ),
}
CURRENT_STATUSES = {"current", "active", "completed"}


def scope_collections(
    scope: str, requested: Optional[Sequence[str]] = None
) -> Tuple[str, ...]:
    normalized_scope = "paper" if scope == "local" else scope
    if normalized_scope not in SCOPE_COLLECTIONS:
        raise ValueError(f"未知本地检索作用域：{scope}")
    allowed = SCOPE_COLLECTIONS[normalized_scope]
    if not requested:
        return allowed
    unknown = sorted(set(requested) - set(allowed))
    if unknown:
        raise ValueError(
            f"collection 不属于作用域 {normalized_scope}：{', '.join(unknown)}"
        )
    return tuple(dict.fromkeys(requested))


def _vector_ranking(
    connection: sqlite3.Connection,
    query_vector: np.ndarray,
    allowed_note_ids: Set[int],
) -> List[RankedNote]:
    chunk_ids, note_ids, vectors = load_embeddings(connection)
    if not len(chunk_ids):
        return []
    scores = vector_scores(query_vector, vectors)
    order = np.argsort(-scores, kind="stable")
    chunks = [
        RankedChunk(int(chunk_ids[index]), int(note_ids[index]), float(scores[index]))
        for index in order
        if int(note_ids[index]) in allowed_note_ids
    ]
    return aggregate_chunks(chunks)


def _note_to_identity(
    connection: sqlite3.Connection, allowed_note_ids: Set[int]
) -> Dict[int, str]:
    return {
        int(row["id"]): (
            str(row["paper_id"])
            if str(row["collection"]) == "papers"
            else str(row["note_id"])
        )
        for row in connection.execute("SELECT id,paper_id,note_id,collection FROM notes")
        if int(row["id"]) in allowed_note_ids
    }


def _allowed_notes(
    connection: sqlite3.Connection,
    collections: Sequence[str],
    include_history: bool,
) -> Tuple[Set[int], Dict[int, sqlite3.Row]]:
    marks = ",".join("?" for _ in collections)
    rows = list(
        connection.execute(
            f"SELECT * FROM notes WHERE collection IN ({marks}) ORDER BY id",
            tuple(collections),
        )
    )
    if not include_history:
        rows = [row for row in rows if str(row["status"]) in CURRENT_STATUSES]
    return {int(row["id"]) for row in rows}, {int(row["id"]): row for row in rows}


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
    scope: str = "paper",
    collections: Optional[Sequence[str]] = None,
    include_history: bool = False,
    query_vector: Optional[np.ndarray] = None,
) -> List[Dict[str, object]]:
    if mode not in {"lexical", "vector", "hybrid"}:
        raise ValueError(f"未知检索模式：{mode}")
    selected_collections = scope_collections(scope, collections)
    allowed_note_ids, allowed_note_rows = _allowed_notes(
        connection, selected_collections, include_history
    )
    if not allowed_note_ids:
        return []
    note_to_paper = _note_to_identity(connection, allowed_note_ids)
    lexical_notes = (
        aggregate_chunks(
            item
            for item in lexical_search(connection, query)
            if item.note_id in allowed_note_ids
        )
        if mode != "vector"
        else []
    )
    lexical = aggregate_papers(lexical_notes, note_to_paper)
    vector_notes: List[RankedNote] = []
    if mode != "lexical":
        if backend is None:
            backend = EmbeddingBackend(
                resolve_model_reference(
                    config.model_name,
                    config.model_revision,
                    cache_folder,
                    local_files_only,
                ),
                config.model_revision,
                cache_folder=cache_folder,
                local_files_only=local_files_only,
                device=device,
            )
        if query_vector is None:
            query_vector = backend.encode_query(query)
        vector_notes = _vector_ranking(connection, query_vector, allowed_note_ids)
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
        document_metadata = allowed_note_rows[evidence.note_id]
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
        is_paper = str(document_metadata["collection"]) == "papers"
        results.append(
            {
                "rank": display_rank,
                "scope": "paper" if is_paper else scope,
                "document_id": document_metadata["note_id"],
                "paper_id": paper_id if is_paper else None,
                "collection": document_metadata["collection"],
                "doc_type": document_metadata["doc_type"],
                "authority": document_metadata["authority"],
                "route": document_metadata["route"],
                "chapter": document_metadata["chapter"],
                "status": document_metadata["status"],
                "date": document_metadata["fact_date"],
                "sensitivity": document_metadata["sensitivity"],
                "title": evidence_note["title"],
                "note_id": evidence_note["note_id"],
                "note_path": evidence_note["path"],
                "note_views": note_views,
                "note_view_count": len(note_views),
                "source_pdf": evidence_note["source_pdf"] if is_paper else None,
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
                "evidence_level": document_metadata["evidence_level"],
            }
        )
    return results


def search_federated(
    connection: sqlite3.Connection,
    query: str,
    mode: str,
    top_k: int,
    config: SearchConfig,
    cache_folder: Optional[Path] = None,
    local_files_only: bool = False,
    device: str = "auto",
    scope: str = "paper",
    collections: Optional[Sequence[str]] = None,
    include_history: bool = False,
) -> List[Dict[str, object]]:
    selected_collections = scope_collections(scope, collections)
    if len(selected_collections) == 1:
        return search_local(
            connection,
            query,
            mode,
            top_k,
            config,
            cache_folder=cache_folder,
            local_files_only=local_files_only,
            device=device,
            scope=scope,
            collections=selected_collections,
            include_history=include_history,
        )

    backend = None
    query_vector = None
    if mode != "lexical":
        backend = EmbeddingBackend(
            resolve_model_reference(
                config.model_name,
                config.model_revision,
                cache_folder,
                local_files_only,
            ),
            config.model_revision,
            cache_folder=cache_folder,
            local_files_only=local_files_only,
            device=device,
        )
        query_vector = backend.encode_query(query)
    collection_results = {
        collection: search_local(
            connection,
            query,
            mode,
            top_k,
            config,
            cache_folder=cache_folder,
            local_files_only=local_files_only,
            device=device,
            backend=backend,
            scope=scope,
            collections=(collection,),
            include_history=include_history,
            query_vector=query_vector,
        )
        for collection in selected_collections
    }
    fused = reciprocal_rank_fusion(
        {
            collection: [str(item["document_id"]) for item in results]
            for collection, results in collection_results.items()
        },
        config.rrf_constant,
    )
    payloads = {
        str(item["document_id"]): item
        for results in collection_results.values()
        for item in results
    }
    ordered = sorted(fused.items(), key=lambda item: (-item[1], item[0]))[:top_k]
    output: List[Dict[str, object]] = []
    for rank, (document_id, score) in enumerate(ordered, start=1):
        item = dict(payloads[document_id])
        item["rank"] = rank
        item["collection_rrf_score"] = score
        output.append(item)
    return output
