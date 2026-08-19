from __future__ import annotations

from pathlib import Path
from typing import Dict

from .config import SearchConfig
from .documents import load_notes, source_manifest_hash
from .storage import connect, get_metadata


def index_status(repo_root: Path, index_path: Path, config: SearchConfig) -> Dict[str, object]:
    if not index_path.exists():
        return {
            "exists": False,
            "index_path": str(index_path),
            "stale": None,
            "message": "索引不存在，请先运行 build",
        }
    connection = connect(index_path, readonly=True)
    try:
        metadata = get_metadata(connection)
    finally:
        connection.close()
    current_hash = source_manifest_hash(load_notes(repo_root, config.input_glob))
    return {
        "exists": True,
        "index_path": str(index_path),
        "index_bytes": index_path.stat().st_size,
        "stale": metadata.get("source_manifest_hash") != current_hash,
        **metadata,
    }
