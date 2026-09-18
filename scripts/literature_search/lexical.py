from __future__ import annotations

import sqlite3
from typing import List

from .documents import normalize_lexical
from .types import RankedChunk


def _trigram_query(text: str) -> str:
    normalized = normalize_lexical(text)
    if len(normalized) < 3:
        return ""
    grams = []
    seen = set()
    for offset in range(len(normalized) - 2):
        gram = normalized[offset : offset + 3]
        if gram.strip() and gram not in seen:
            seen.add(gram)
            grams.append('"' + gram.replace('"', '""') + '"')
    return " OR ".join(grams)


def lexical_search(connection: sqlite3.Connection, query: str) -> List[RankedChunk]:
    normalized = normalize_lexical(query)
    if not normalized:
        return []
    match_query = _trigram_query(query)
    if not match_query:
        rows = connection.execute(
            "SELECT id,note_id,CASE WHEN instr(lexical_text, ?) > 0 THEN 1.0 ELSE 0.0 END score "
            "FROM chunks WHERE instr(lexical_text, ?) > 0 ORDER BY score DESC,id",
            (normalized, normalized),
        )
        return [RankedChunk(int(r["id"]), int(r["note_id"]), float(r["score"])) for r in rows]
    rows = connection.execute(
        "SELECT c.id,c.note_id,-bm25(chunks_fts) score "
        "FROM chunks_fts JOIN chunks c ON c.id=chunks_fts.rowid "
        "WHERE chunks_fts MATCH ? ORDER BY score DESC,c.id",
        (match_query,),
    )
    return [RankedChunk(int(r["id"]), int(r["note_id"]), float(r["score"])) for r in rows]
