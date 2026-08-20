from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


@dataclass(frozen=True)
class NoteDocument:
    path: Path
    relative_path: str
    note_id: str
    paper_id: str
    collection: str
    doc_type: str
    authority: str
    route: Optional[str]
    chapter: Optional[str]
    status: str
    fact_date: Optional[str]
    evidence_level: str
    sensitivity: str
    title: str
    title_zh: Optional[str]
    authors: Tuple[str, ...]
    year: Optional[int]
    aliases: Tuple[str, ...]
    tags: Tuple[str, ...]
    key_finding: Tuple[str, ...]
    tasks: Tuple[str, ...]
    datasets: Tuple[str, ...]
    methods: Tuple[str, ...]
    metrics: Tuple[str, ...]
    supports: Tuple[str, ...]
    cannot_support: Tuple[str, ...]
    source_pdf: str
    doi: Optional[str]
    arxiv_id: Optional[str]
    cited_dois: Tuple[str, ...]
    body: str
    source_hash: str


@dataclass(frozen=True)
class ExcludedDocument:
    relative_path: str
    reason: str
    detail: Optional[str] = None


@dataclass(frozen=True)
class CorpusScan:
    notes: Tuple[NoteDocument, ...]
    excluded: Tuple[ExcludedDocument, ...]


@dataclass(frozen=True)
class TextChunk:
    note_position: int
    position: int
    heading: str
    page_hint: Optional[str]
    text: str
    lexical_text: str
    text_hash: str
    chunk_key: str
    embedding_contract_hash: str


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
