from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class NoteDocument:
    path: Path
    relative_path: str
    title: str
    source_pdf: Optional[str]
    doi: Optional[str]
    arxiv_id: Optional[str]
    body: str
    source_hash: str


@dataclass(frozen=True)
class TextChunk:
    note_position: int
    position: int
    heading: str
    page_hint: Optional[str]
    text: str
    lexical_text: str


@dataclass(frozen=True)
class RankedChunk:
    chunk_id: int
    note_id: int
    score: float


@dataclass(frozen=True)
class RankedNote:
    note_id: int
    score: float
    chunk_id: int
