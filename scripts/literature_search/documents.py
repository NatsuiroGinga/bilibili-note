from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .types import NoteDocument, TextChunk


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
PAGE_RE = re.compile(
    r"(?:第\s*\d+\s*(?:[-—–至到]\s*\d+\s*)?页|"
    r"(?:pages?|p)\.?\s*\d+(?:\s*[-—–]\s*\d+)?)",
    re.IGNORECASE,
)
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
ARXIV_RE = re.compile(
    r"(?:arxiv\s*:\s*)?((?:\d{2})(?:0[1-9]|1[0-2])\.\d{4,5}(?:v\d+)?)",
    re.IGNORECASE,
)


def _strip_scalar(value: str) -> str:
    value = value.strip().strip('"\'')
    link = re.fullmatch(r"\[\[(.*?)\]\]", value)
    return link.group(1).strip() if link else value


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    fields: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        item = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if item and item.group(2).strip():
            fields[item.group(1)] = _strip_scalar(item.group(2))
    return fields, text[match.end() :]


def extract_source_pdf(fields: Dict[str, str]) -> Optional[str]:
    value = fields.get("source_pdf", "").strip()
    return value or None


def extract_page_hint(text: str) -> Optional[str]:
    match = PAGE_RE.search(text)
    return match.group(0).strip() if match else None


def normalize_lexical(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = re.sub(r"[^\w\u3400-\u4dbf\u4e00-\u9fff]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _extract_identifier(fields: Dict[str, str], body: str) -> Tuple[Optional[str], Optional[str]]:
    doi_source = fields.get("doi", "")
    doi_match = DOI_RE.search(doi_source)
    arxiv_match = ARXIV_RE.search(doi_source)
    if not doi_match:
        doi_match = DOI_RE.search(body[:4000])
    if not arxiv_match:
        arxiv_match = ARXIV_RE.search(body[:4000])
    doi = doi_match.group(0).rstrip(".,;)") if doi_match else None
    arxiv_id = arxiv_match.group(1) if arxiv_match else None
    return doi, arxiv_id


def load_notes(repo_root: Path, pattern: str) -> List[NoteDocument]:
    notes: List[NoteDocument] = []
    for path in sorted(repo_root.glob(pattern)):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        fields, body = parse_frontmatter(text)
        title = fields.get("title")
        if not title:
            heading = HEADING_RE.search(body)
            title = heading.group(2).strip() if heading else path.stem
        doi, arxiv_id = _extract_identifier(fields, body)
        notes.append(
            NoteDocument(
                path=path,
                relative_path=path.relative_to(repo_root).as_posix(),
                title=title,
                source_pdf=extract_source_pdf(fields),
                doi=doi,
                arxiv_id=arxiv_id,
                body=body.strip(),
                source_hash=hashlib.sha256(raw).hexdigest(),
            )
        )
    return notes


def source_manifest_hash(notes: Sequence[NoteDocument]) -> str:
    digest = hashlib.sha256()
    for note in notes:
        digest.update(note.relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(note.source_hash.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _section_units(body: str) -> Iterable[Tuple[str, str]]:
    matches = list(HEADING_RE.finditer(body))
    if not matches:
        yield "", body
        return
    if matches[0].start() > 0:
        yield "", body[: matches[0].start()]
    for position, match in enumerate(matches):
        end = matches[position + 1].start() if position + 1 < len(matches) else len(body)
        yield match.group(2).strip(), body[match.end() : end]


def _window_text(text: str, maximum: int, overlap: int) -> Iterable[str]:
    start = 0
    while start < len(text):
        end = min(start + maximum, len(text))
        if end < len(text):
            boundary = max(text.rfind("\n", start, end), text.rfind("。", start, end))
            if boundary > start + maximum // 2:
                end = boundary + 1
        piece = text[start:end].strip()
        if piece:
            yield piece
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)


def chunk_note(
    note: NoteDocument,
    note_position: int,
    max_chars: int,
    overlap_chars: int,
) -> List[TextChunk]:
    if max_chars < 64 or overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("分块参数无效：最大字符数须至少为 64，重叠须非负且小于最大值")
    chunks: List[TextChunk] = []
    for heading, section in _section_units(note.body):
        compact = re.sub(r"\n{3,}", "\n\n", section).strip()
        if not compact:
            continue
        prefix = f"{note.title}\n{heading}\n" if heading else f"{note.title}\n"
        budget = max_chars - min(len(prefix), max_chars // 3)
        for piece in _window_text(compact, budget, overlap_chars):
            text = (prefix + piece).strip()
            chunks.append(
                TextChunk(
                    note_position=note_position,
                    position=len(chunks),
                    heading=heading,
                    page_hint=extract_page_hint(piece),
                    text=text,
                    lexical_text=normalize_lexical(text),
                )
            )
    if not chunks:
        text = note.title
        chunks.append(
            TextChunk(note_position, 0, "", None, text, normalize_lexical(text))
        )
    return chunks
