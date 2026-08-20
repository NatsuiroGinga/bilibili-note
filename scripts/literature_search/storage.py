from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np

from .types import NoteDocument, TextChunk


def connect(path: Path, readonly: bool = False) -> sqlite3.Connection:
    if readonly:
        connection = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
    else:
        connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode = DELETE;
        PRAGMA synchronous = NORMAL;
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY,
            note_id TEXT NOT NULL UNIQUE,
            paper_id TEXT NOT NULL,
            collection TEXT NOT NULL,
            doc_type TEXT NOT NULL,
            authority TEXT NOT NULL,
            route TEXT,
            chapter TEXT,
            status TEXT NOT NULL,
            fact_date TEXT,
            evidence_level TEXT NOT NULL,
            sensitivity TEXT NOT NULL,
            parser_contract_hash TEXT NOT NULL,
            path TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            title_zh TEXT,
            authors TEXT NOT NULL,
            year INTEGER,
            aliases TEXT NOT NULL,
            tags TEXT NOT NULL,
            key_finding TEXT NOT NULL,
            tasks TEXT NOT NULL,
            datasets TEXT NOT NULL,
            methods TEXT NOT NULL,
            metrics TEXT NOT NULL,
            supports TEXT NOT NULL,
            cannot_support TEXT NOT NULL,
            source_pdf TEXT NOT NULL,
            doi TEXT,
            arxiv_id TEXT,
            cited_dois TEXT NOT NULL,
            source_hash TEXT NOT NULL
        );
        CREATE INDEX notes_paper_id ON notes(paper_id);
        CREATE INDEX notes_collection ON notes(collection, status);
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY,
            note_id INTEGER NOT NULL REFERENCES notes(id),
            position INTEGER NOT NULL,
            heading TEXT NOT NULL,
            page_hint TEXT,
            text TEXT NOT NULL,
            lexical_text TEXT NOT NULL,
            text_hash TEXT NOT NULL,
            chunk_key TEXT NOT NULL UNIQUE,
            embedding_contract_hash TEXT NOT NULL,
            embedding BLOB,
            UNIQUE(note_id, position)
        );
        CREATE INDEX chunks_note_id ON chunks(note_id);
        CREATE INDEX chunks_reuse_key ON chunks(chunk_key, embedding_contract_hash);
        CREATE VIRTUAL TABLE chunks_fts USING fts5(
            title, heading, text,
            content='', tokenize='trigram'
        );
        """
    )


def _json_list(values: Sequence[str]) -> str:
    return json.dumps(list(values), ensure_ascii=False, separators=(",", ":"))


def insert_documents(
    connection: sqlite3.Connection,
    notes: Sequence[NoteDocument],
    chunks: Sequence[TextChunk],
    parser_contract_hash: str,
) -> None:
    for position, note in enumerate(notes):
        connection.execute(
            """INSERT INTO notes(
                id,note_id,paper_id,collection,doc_type,authority,route,chapter,
                status,fact_date,evidence_level,sensitivity,parser_contract_hash,
                path,title,title_zh,authors,year,aliases,tags,
                key_finding,tasks,datasets,methods,metrics,supports,cannot_support,
                source_pdf,doi,arxiv_id,cited_dois,source_hash
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                position + 1,
                note.note_id,
                note.paper_id,
                note.collection,
                note.doc_type,
                note.authority,
                note.route,
                note.chapter,
                note.status,
                note.fact_date,
                note.evidence_level,
                note.sensitivity,
                parser_contract_hash,
                note.relative_path,
                note.title,
                note.title_zh,
                _json_list(note.authors),
                note.year,
                _json_list(note.aliases),
                _json_list(note.tags),
                _json_list(note.key_finding),
                _json_list(note.tasks),
                _json_list(note.datasets),
                _json_list(note.methods),
                _json_list(note.metrics),
                _json_list(note.supports),
                _json_list(note.cannot_support),
                note.source_pdf,
                note.doi,
                note.arxiv_id,
                _json_list(note.cited_dois),
                note.source_hash,
            ),
        )
    for chunk_id, chunk in enumerate(chunks, start=1):
        note = notes[chunk.note_position]
        cursor = connection.execute(
            """INSERT INTO chunks(
                id,note_id,position,heading,page_hint,text,lexical_text,text_hash,
                chunk_key,embedding_contract_hash
            ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                chunk_id,
                chunk.note_position + 1,
                chunk.position,
                chunk.heading,
                chunk.page_hint,
                chunk.text,
                chunk.lexical_text,
                chunk.text_hash,
                chunk.chunk_key,
                chunk.embedding_contract_hash,
            ),
        )
        connection.execute(
            "INSERT INTO chunks_fts(rowid,title,heading,text) VALUES(?,?,?,?)",
            (cursor.lastrowid, note.title, chunk.heading, chunk.lexical_text),
        )


def set_metadata(connection: sqlite3.Connection, values: Mapping[str, object]) -> None:
    connection.executemany(
        "INSERT OR REPLACE INTO metadata(key,value) VALUES(?,?)",
        [(key, json.dumps(value, ensure_ascii=False)) for key, value in values.items()],
    )


def get_metadata(connection: sqlite3.Connection) -> Dict[str, object]:
    return {
        row["key"]: json.loads(row["value"])
        for row in connection.execute("SELECT key,value FROM metadata")
    }


def table_columns(connection: sqlite3.Connection, table: str) -> Tuple[str, ...]:
    return tuple(str(row["name"]) for row in connection.execute(f"PRAGMA table_info({table})"))


def indexed_source_hashes(connection: sqlite3.Connection) -> Dict[str, str]:
    columns = table_columns(connection, "notes")
    identity_column = "note_id" if "note_id" in columns else "path"
    return {
        str(row["identity"]): str(row["source_hash"])
        for row in connection.execute(
            f"SELECT {identity_column} AS identity,source_hash FROM notes"
        )
    }


def indexed_document_state(
    connection: sqlite3.Connection,
) -> Dict[str, Tuple[str, str]]:
    columns = table_columns(connection, "notes")
    identity_column = "note_id" if "note_id" in columns else "path"
    collection_expression = "collection" if "collection" in columns else "'papers'"
    return {
        str(row["identity"]): (str(row["source_hash"]), str(row["collection"]))
        for row in connection.execute(
            f"SELECT {identity_column} AS identity,source_hash,"
            f"{collection_expression} AS collection FROM notes"
        )
    }


def source_diff(
    indexed: Mapping[str, str], notes: Sequence[NoteDocument]
) -> Dict[str, object]:
    current = {note.note_id: note.source_hash for note in notes}
    indexed_paths = set(indexed)
    current_paths = set(current)
    added_paths = sorted(current_paths - indexed_paths)
    deleted_paths = sorted(indexed_paths - current_paths)
    shared_paths = indexed_paths & current_paths
    changed_paths = sorted(path for path in shared_paths if indexed[path] != current[path])
    unchanged_paths = sorted(path for path in shared_paths if indexed[path] == current[path])
    return {
        "added": len(added_paths),
        "changed": len(changed_paths),
        "deleted": len(deleted_paths),
        "unchanged": len(unchanged_paths),
        "added_paths": added_paths,
        "changed_paths": changed_paths,
        "deleted_paths": deleted_paths,
    }


def collection_source_diffs(
    indexed: Mapping[str, Tuple[str, str]], notes: Sequence[NoteDocument]
) -> Dict[str, Dict[str, object]]:
    current_collections = {note.collection for note in notes}
    indexed_collections = {collection for _, collection in indexed.values()}
    differences: Dict[str, Dict[str, object]] = {}
    for collection in sorted(current_collections | indexed_collections):
        indexed_hashes = {
            note_id: source_hash
            for note_id, (source_hash, indexed_collection) in indexed.items()
            if indexed_collection == collection
        }
        collection_notes = [note for note in notes if note.collection == collection]
        differences[collection] = source_diff(indexed_hashes, collection_notes)
    return differences


def reusable_embeddings(
    connection: sqlite3.Connection, embedding_contract_hash: str
) -> Dict[str, bytes]:
    columns = table_columns(connection, "chunks")
    required = {"chunk_key", "embedding_contract_hash", "embedding"}
    if not required.issubset(columns):
        return {}
    return {
        str(row["chunk_key"]): bytes(row["embedding"])
        for row in connection.execute(
            """SELECT chunk_key,embedding FROM chunks
               WHERE embedding IS NOT NULL AND embedding_contract_hash=?""",
            (embedding_contract_hash,),
        )
    }


def write_embedding_blobs(
    connection: sqlite3.Connection, values: Sequence[Tuple[int, bytes]]
) -> None:
    connection.executemany(
        "UPDATE chunks SET embedding=? WHERE id=?",
        [(sqlite3.Binary(blob), chunk_id) for chunk_id, blob in values],
    )


def write_embeddings(
    connection: sqlite3.Connection, chunk_ids: Sequence[int], vectors: np.ndarray
) -> None:
    if vectors.dtype != np.float32:
        vectors = vectors.astype(np.float32)
    write_embedding_blobs(
        connection,
        [
            (chunk_id, np.ascontiguousarray(vector).tobytes())
            for chunk_id, vector in zip(chunk_ids, vectors)
        ],
    )


def load_embeddings(connection: sqlite3.Connection) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = list(
        connection.execute(
            "SELECT id,note_id,embedding FROM chunks WHERE embedding IS NOT NULL ORDER BY id"
        )
    )
    if not rows:
        return (
            np.empty((0,), dtype=np.int64),
            np.empty((0,), dtype=np.int64),
            np.empty((0, 0), dtype=np.float32),
        )
    vectors = np.stack([np.frombuffer(row["embedding"], dtype=np.float32) for row in rows])
    return (
        np.asarray([row["id"] for row in rows], dtype=np.int64),
        np.asarray([row["note_id"] for row in rows], dtype=np.int64),
        vectors,
    )


def chunk_texts(connection: sqlite3.Connection) -> Iterable[Tuple[int, str, str]]:
    for row in connection.execute("SELECT id,text,chunk_key FROM chunks ORDER BY id"):
        yield int(row["id"]), str(row["text"]), str(row["chunk_key"])


def fetch_notes(connection: sqlite3.Connection, note_ids: Sequence[int]) -> Dict[int, sqlite3.Row]:
    if not note_ids:
        return {}
    marks = ",".join("?" for _ in note_ids)
    return {
        int(row["id"]): row
        for row in connection.execute(
            f"SELECT * FROM notes WHERE id IN ({marks})", tuple(note_ids)
        )
    }


def fetch_note_views(
    connection: sqlite3.Connection, paper_ids: Sequence[str]
) -> Dict[str, List[sqlite3.Row]]:
    if not paper_ids:
        return {}
    marks = ",".join("?" for _ in paper_ids)
    views: Dict[str, List[sqlite3.Row]] = {paper_id: [] for paper_id in paper_ids}
    for row in connection.execute(
        f"SELECT * FROM notes WHERE paper_id IN ({marks}) ORDER BY note_id", tuple(paper_ids)
    ):
        views[str(row["paper_id"])].append(row)
    return views


def fetch_chunks(connection: sqlite3.Connection, chunk_ids: Sequence[int]) -> Dict[int, sqlite3.Row]:
    if not chunk_ids:
        return {}
    marks = ",".join("?" for _ in chunk_ids)
    return {
        int(row["id"]): row
        for row in connection.execute(
            f"SELECT * FROM chunks WHERE id IN ({marks})", tuple(chunk_ids)
        )
    }
