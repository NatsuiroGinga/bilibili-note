from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from typing import Dict, List

from .config import SearchConfig
from .documents import excluded_summary, scan_corpus, source_manifest_hash
from .storage import (
    collection_source_diffs,
    connect,
    get_metadata,
    indexed_document_state,
    source_diff,
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def index_status(repo_root: Path, index_path: Path, config: SearchConfig) -> Dict[str, object]:
    scan = scan_corpus(
        repo_root,
        config.input_glob,
        config.project_input_globs,
        config.experiment_receipt_globs,
        config.max_document_bytes,
    )
    notes = list(scan.notes)
    exclusions = excluded_summary(scan.excluded)
    current_manifest = source_manifest_hash(notes)
    current_parser_contract = config.parser_contract_hash()
    current_contract = config.embedding_contract_hash()
    if not index_path.exists():
        return {
            "exists": False,
            "index_path": str(index_path),
            "stale": None,
            "stale_reasons": ["missing_index"],
            "message": "索引不存在，请先运行 build",
            "current_note_count": len(notes),
            "current_collection_counts": dict(
                sorted(Counter(note.collection for note in notes).items())
            ),
            "collection_diffs": collection_source_diffs({}, notes),
            "current_source_manifest_hash": current_manifest,
            "current_parser_contract_hash": current_parser_contract,
            "current_embedding_contract_hash": current_contract,
            "parser_contract_changed": False,
            "added": len(notes),
            "changed": 0,
            "deleted": 0,
            "unchanged": 0,
            "embedding_contract_changed": False,
            **exclusions,
        }
    connection = connect(index_path, readonly=True)
    try:
        metadata = get_metadata(connection)
        indexed = indexed_document_state(connection)
    finally:
        connection.close()
    indexed_hashes = {note_id: value[0] for note_id, value in indexed.items()}
    differences = source_diff(indexed_hashes, notes)
    collection_diffs = collection_source_diffs(indexed, notes)
    contract_changed = metadata.get("embedding_contract_hash") != current_contract
    parser_contract_changed = (
        metadata.get("parser_contract_hash") != current_parser_contract
    )
    stale_reasons: List[str] = []
    for reason in ("added", "changed", "deleted"):
        if differences[reason]:
            stale_reasons.append(f"source_{reason}")
    if contract_changed:
        stale_reasons.append("embedding_contract_changed")
    if parser_contract_changed:
        stale_reasons.append("parser_contract_changed")
    return {
        **metadata,
        "exists": True,
        "index_path": str(index_path),
        "index_bytes": index_path.stat().st_size,
        "index_sha256": _file_sha256(index_path),
        "stale": bool(stale_reasons),
        "stale_reasons": stale_reasons,
        "current_note_count": len(notes),
        "current_collection_counts": dict(
            sorted(Counter(note.collection for note in notes).items())
        ),
        "collection_diffs": collection_diffs,
        "current_source_manifest_hash": current_manifest,
        "current_parser_contract_hash": current_parser_contract,
        "current_embedding_contract_hash": current_contract,
        "parser_contract_changed": parser_contract_changed,
        "embedding_contract_changed": contract_changed,
        **differences,
        **exclusions,
    }
