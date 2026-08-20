from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .types import NoteDocument, RankedChunk, TextChunk


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
            path TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            source_pdf TEXT,
            doi TEXT,
            arxiv_id TEXT,
            source_hash TEXT NOT NULL
        );
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY,
            note_id INTEGER NOT NULL REFERENCES notes(id),
            position INTEGER NOT NULL,
            heading TEXT NOT NULL,
            page_hint TEXT,
            text TEXT NOT NULL,
            lexical_text TEXT NOT NULL,
            embedding BLOB,
            UNIQUE(note_id, position)
        );
        CREATE INDEX chunks_note_id ON chunks(note_id);
        CREATE VIRTUAL TABLE chunks_fts USING fts5(
            title, heading, text,
            content='', tokenize='trigram'
        );
        """
    )


def insert_documents(
    connection: sqlite3.Connection,
    notes: Sequence[NoteDocument],
    chunks: Sequence[TextChunk],
) -> None:
    for position, note in enumerate(notes):
        connection.execute(
            "INSERT INTO notes(id,path,title,source_pdf,doi,arxiv_id,source_hash) "
            "VALUES(?,?,?,?,?,?,?)",
            (
                position + 1,
                note.relative_path,
                note.title,
                note.source_pdf,
                note.doi,
                note.arxiv_id,
                note.source_hash,
            ),
        )
    for chunk_id, chunk in enumerate(chunks, start=1):
        note = notes[chunk.note_position]
        cursor = connection.execute(
            "INSERT INTO chunks(id,note_id,position,heading,page_hint,text,lexical_text) "
            "VALUES(?,?,?,?,?,?,?)",
            (
                chunk_id,
                chunk.note_position + 1,
                chunk.position,
                chunk.heading,
                chunk.page_hint,
                chunk.text,
                chunk.lexical_text,
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


def write_embeddings(
    connection: sqlite3.Connection, chunk_ids: Sequence[int], vectors: np.ndarray
) -> None:
    if vectors.dtype != np.float32:
        vectors = vectors.astype(np.float32)
    connection.executemany(
        "UPDATE chunks SET embedding=? WHERE id=?",
        [
            (sqlite3.Binary(np.ascontiguousarray(vector).tobytes()), chunk_id)
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


def chunk_texts(connection: sqlite3.Connection) -> Iterable[Tuple[int, str]]:
    for row in connection.execute("SELECT id,text FROM chunks ORDER BY id"):
        yield int(row["id"]), str(row["text"])


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
