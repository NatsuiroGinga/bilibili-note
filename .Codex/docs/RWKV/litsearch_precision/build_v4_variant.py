"""V4 探索性变体：在已落地的 V3（生产 documents.py）基础上，额外排除重定向页。

不修改生产代码，只复用生产的 load_notes（已内置 V1+V2 默认行为），
在其输出上再按 frontmatter 的 status/tags 过滤重定向页，写到独立索引路径。

排除依据：`.Codex/docs/RWKV/2026-08-28-文献知识图谱构建报告.md` 第 29 行，
重定向页判据为 `status: 重定向` 或 tags 含 `类型/跳转页`，全库 28 篇。

这是协调者要求的可选探索，只在四项指标不劣于 V3 时才考虑采纳；
本脚本本身不改变任何生产文件或默认索引。
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from scripts.literature_search.config import load_config  # noqa: E402
from scripts.literature_search.documents import (  # noqa: E402
    chunk_note,
    load_notes,
    parse_metadata_fields,
    source_manifest_hash,
)
from scripts.literature_search.storage import (  # noqa: E402
    connect,
    initialize,
    insert_documents,
    set_metadata,
)
from scripts.literature_search.types import NoteDocument  # noqa: E402


def is_redirect_page(note: NoteDocument) -> bool:
    raw = note.path.read_text(encoding="utf-8", errors="replace")
    fields = parse_metadata_fields(raw)
    if str(fields.get("status", "")).strip() == "重定向":
        return True
    tags = fields.get("tags", [])
    if isinstance(tags, list) and "类型/跳转页" in tags:
        return True
    return False


def main() -> int:
    config = load_config()
    started = time.monotonic()
    notes = load_notes(REPO_ROOT, config.input_glob)  # 已含 V1+V2（生产默认）
    kept: List[NoteDocument] = [n for n in notes if not is_redirect_page(n)]
    excluded = len(notes) - len(kept)
    chunks = [
        chunk
        for position, note in enumerate(kept)
        for chunk in chunk_note(note, position, config.chunk_max_chars, config.chunk_overlap_chars)
    ]
    index_path = REPO_ROOT / ".cache/literature-search/index_V4.sqlite3"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = index_path.with_suffix(index_path.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    connection = connect(temporary)
    try:
        initialize(connection)
        insert_documents(connection, kept, chunks)
        metadata = {
            "schema_version": config.schema_version,
            "built_at": datetime.now(timezone.utc).isoformat(),
            "build_seconds": round(time.monotonic() - started, 3),
            "source_manifest_hash": source_manifest_hash(kept),
            "note_count": len(kept),
            "chunk_count": len(chunks),
            "vector_count": 0,
            "vector_dimension": 0,
            "model_name": config.model_name,
            "model_revision": config.model_revision,
            "config": config.to_dict(),
            "variant": "V4 = V3 + 排除重定向页",
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
    print(
        f"V4: 笔记={len(kept)}（排除重定向页 {excluded} 篇） 分块={len(chunks)} "
        f"耗时={round(time.monotonic() - started, 3)}s\n  -> {index_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
