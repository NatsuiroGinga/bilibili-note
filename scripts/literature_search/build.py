from __future__ import annotations

import hashlib
import os
import sqlite3
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import SearchConfig
from .documents import (
    chunk_note,
    excluded_summary,
    scan_corpus,
    source_manifest_hash,
)
from .embeddings import EmbeddingBackend
from .storage import (
    chunk_texts,
    connect,
    collection_source_diffs,
    get_metadata,
    indexed_document_state,
    initialize,
    insert_documents,
    reusable_embeddings,
    set_metadata,
    source_diff,
    write_embedding_blobs,
    write_embeddings,
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _old_index_state(
    index_path: Path, embedding_contract_hash: str
) -> Tuple[Dict[str, Tuple[str, str]], Dict[str, bytes], Optional[str]]:
    if not index_path.exists():
        return {}, {}, None
    connection = connect(index_path, readonly=True)
    try:
        metadata = get_metadata(connection)
        indexed = indexed_document_state(connection)
        saved_contract = metadata.get("embedding_contract_hash")
        reusable = (
            reusable_embeddings(connection, embedding_contract_hash)
            if saved_contract == embedding_contract_hash
            else {}
        )
        return indexed, reusable, str(saved_contract) if saved_contract else None
    finally:
        connection.close()


def _write_vectors(
    connection: sqlite3.Connection,
    reusable: Dict[str, bytes],
    config: SearchConfig,
    cache_folder: Optional[Path],
    local_files_only: bool,
    device: str,
) -> Dict[str, object]:
    reused_values: List[Tuple[int, bytes]] = []
    pending: List[Tuple[int, str]] = []
    for chunk_id, text, chunk_key in chunk_texts(connection):
        blob = reusable.get(chunk_key)
        if blob is None:
            pending.append((chunk_id, text))
        else:
            reused_values.append((chunk_id, blob))
    write_embedding_blobs(connection, reused_values)

    reused_dimensions = {len(item[1]) // 4 for item in reused_values}
    if any(len(item[1]) % 4 for item in reused_values) or len(reused_dimensions) > 1:
        raise RuntimeError("旧索引包含维度不一致的 float32 向量，拒绝复用")
    vector_dimension = next(iter(reused_dimensions), 0)
    vector_device = None
    vector_device_fallback = None
    if pending:
        backend = EmbeddingBackend(
            config.model_name,
            config.model_revision,
            cache_folder=cache_folder,
            local_files_only=local_files_only,
            device=device,
        )
        for offset in range(0, len(pending), config.batch_size):
            batch = pending[offset : offset + config.batch_size]
            vectors = backend.encode_documents(
                [item[1] for item in batch], config.batch_size
            )
            if vector_dimension and vector_dimension != int(vectors.shape[1]):
                raise RuntimeError("复用向量与新嵌入向量维度不一致")
            write_embeddings(connection, [item[0] for item in batch], vectors)
            vector_dimension = int(vectors.shape[1])
        vector_device = backend.device
        vector_device_fallback = backend.fallback_reason
    elif reused_values:
        vector_device = "reused"
    return {
        "vector_count": len(reused_values) + len(pending),
        "vector_dimension": vector_dimension,
        "vector_device": vector_device,
        "vector_device_fallback": vector_device_fallback,
        "reused": len(reused_values),
        "reembedded": len(pending),
    }


def build_index(
    repo_root: Path,
    index_path: Path,
    config: SearchConfig,
    lexical_only: bool = False,
    cache_folder: Optional[Path] = None,
    local_files_only: bool = False,
    device: str = "auto",
) -> Dict[str, object]:
    started = time.monotonic()
    scan = scan_corpus(
        repo_root,
        config.input_glob,
        config.project_input_globs,
        config.experiment_receipt_globs,
        config.max_document_bytes,
    )
    notes = list(scan.notes)
    if not notes:
        raise RuntimeError("未找到符合安全允许清单的项目文档")
    embedding_contract_hash = config.embedding_contract_hash()
    parser_contract_hash = config.parser_contract_hash()
    chunks = [
        chunk
        for note_position, note in enumerate(notes)
        for chunk in chunk_note(
            note,
            note_position,
            config.chunk_max_chars,
            config.chunk_overlap_chars,
            embedding_contract_hash,
        )
    ]
    indexed, reusable, previous_contract = _old_index_state(
        index_path, embedding_contract_hash
    )
    indexed_hashes = {note_id: value[0] for note_id, value in indexed.items()}
    differences = source_diff(indexed_hashes, notes)
    collection_diffs = collection_source_diffs(indexed, notes)
    contract_changed = index_path.exists() and previous_contract != embedding_contract_hash
    exclusions = excluded_summary(scan.excluded)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = index_path.with_suffix(index_path.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    connection = connect(temporary)
    try:
        initialize(connection)
        insert_documents(connection, notes, chunks, parser_contract_hash)
        vector_stats: Dict[str, object] = {
            "vector_count": 0,
            "vector_dimension": 0,
            "vector_device": None,
            "vector_device_fallback": None,
            "reused": 0,
            "reembedded": 0,
        }
        if not lexical_only:
            vector_stats = _write_vectors(
                connection,
                reusable,
                config,
                cache_folder,
                local_files_only,
                device,
            )
        elapsed = time.monotonic() - started
        metadata: Dict[str, object] = {
            "schema_version": config.schema_version,
            "built_at": datetime.now(timezone.utc).isoformat(),
            "build_seconds": round(elapsed, 3),
            "source_manifest_hash": source_manifest_hash(notes),
            "parser_contract_hash": parser_contract_hash,
            "embedding_contract_hash": embedding_contract_hash,
            "embedding_contract_changed": contract_changed,
            "note_count": len(notes),
            "chunk_count": len(chunks),
            "collection_counts": dict(
                sorted(Counter(note.collection for note in notes).items())
            ),
            "collection_chunk_counts": dict(
                sorted(
                    Counter(notes[chunk.note_position].collection for chunk in chunks).items()
                )
            ),
            "collection_diffs": collection_diffs,
            "model_name": config.model_name,
            "model_revision": config.model_revision,
            "config": config.to_dict(),
            **differences,
            **exclusions,
            **vector_stats,
        }
        set_metadata(connection, metadata)
        connection.commit()
    except Exception:
        connection.close()
        if temporary.exists():
            temporary.unlink()
        raise
    connection.close()
    os.replace(temporary, index_path)
    metadata["index_path"] = str(index_path)
    metadata["index_bytes"] = index_path.stat().st_size
    metadata["index_sha256"] = _file_sha256(index_path)
    return metadata
