from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .config import SearchConfig
from .documents import chunk_note, load_notes, source_manifest_hash
from .embeddings import EmbeddingBackend
from .storage import (
    chunk_texts,
    connect,
    initialize,
    insert_documents,
    set_metadata,
    write_embeddings,
)


def build_index(
    repo_root: Path,
    index_path: Path,
    config: SearchConfig,
    lexical_only: bool = False,
    cache_folder: Optional[Path] = None,
    local_files_only: bool = False,
) -> Dict[str, object]:
    started = time.monotonic()
    notes = load_notes(repo_root, config.input_glob)
    if not notes:
        raise RuntimeError(f"未找到输入笔记：{config.input_glob}")
    chunks = [
        chunk
        for note_position, note in enumerate(notes)
        for chunk in chunk_note(
            note,
            note_position,
            config.chunk_max_chars,
            config.chunk_overlap_chars,
        )
    ]
    index_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = index_path.with_suffix(index_path.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    connection = connect(temporary)
    try:
        initialize(connection)
        insert_documents(connection, notes, chunks)
        vector_count = 0
        vector_dimension = 0
        if not lexical_only:
            backend = EmbeddingBackend(
                config.model_name,
                config.model_revision,
                cache_folder=cache_folder,
                local_files_only=local_files_only,
            )
            batch_ids: List[int] = []
            batch_texts: List[str] = []
            for chunk_id, text in chunk_texts(connection):
                batch_ids.append(chunk_id)
                batch_texts.append(text)
                if len(batch_texts) >= config.batch_size:
                    vectors = backend.encode_documents(batch_texts, config.batch_size)
                    write_embeddings(connection, batch_ids, vectors)
                    vector_count += len(batch_ids)
                    vector_dimension = int(vectors.shape[1])
                    batch_ids, batch_texts = [], []
            if batch_texts:
                vectors = backend.encode_documents(batch_texts, config.batch_size)
                write_embeddings(connection, batch_ids, vectors)
                vector_count += len(batch_ids)
                vector_dimension = int(vectors.shape[1])
        elapsed = time.monotonic() - started
        metadata = {
            "schema_version": config.schema_version,
            "built_at": datetime.now(timezone.utc).isoformat(),
            "build_seconds": round(elapsed, 3),
            "source_manifest_hash": source_manifest_hash(notes),
            "note_count": len(notes),
            "chunk_count": len(chunks),
            "vector_count": vector_count,
            "vector_dimension": vector_dimension,
            "model_name": config.model_name,
            "model_revision": config.model_revision,
            "config": config.to_dict(),
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
    return metadata
