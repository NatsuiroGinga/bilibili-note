from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import yaml

from .types import CorpusScan, ExcludedDocument, NoteDocument, TextChunk


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
PAGE_RE = re.compile(
    r"(?:第\s*\d+\s*(?:[-—–至到]\s*\d+\s*)?页|"
    r"(?:pages?|p)\.?\s*\d+(?:\s*[-—–]\s*\d+)?)",
    re.IGNORECASE,
)
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
ARXIV_RE = re.compile(
    r"(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?",
    re.IGNORECASE,
)


def _flatten_values(value: object) -> Iterable[str]:
    if value is None:
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _flatten_values(item)
        return
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _flatten_values(item)
        return
    text = str(value).strip()
    if text:
        yield text


def _strip_wikilink(value: str) -> str:
    value = value.strip().strip('"\'')
    match = re.fullmatch(r"\[\[(.*?)(?:\|.*?)?\]\]", value)
    return match.group(1).strip() if match else value


def _scalar(fields: Mapping[str, object], key: str) -> Optional[str]:
    values = tuple(_flatten_values(fields.get(key)))
    return _strip_wikilink(values[0]) if values else None


def _list_field(fields: Mapping[str, object], *keys: str) -> Tuple[str, ...]:
    values: List[str] = []
    for key in keys:
        if key in fields:
            values.extend(_strip_wikilink(item) for item in _flatten_values(fields[key]))
    return tuple(dict.fromkeys(value for value in values if value))


def parse_frontmatter(text: str) -> Tuple[Dict[str, object], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("缺少 YAML 前言")
    parsed = yaml.safe_load(match.group(1))
    if parsed is None:
        parsed = {}
    if not isinstance(parsed, dict):
        raise ValueError("YAML 前言根节点必须是映射")
    return dict(parsed), text[match.end() :]


def extract_source_pdf(fields: Mapping[str, object]) -> Optional[str]:
    return _scalar(fields, "source_pdf")


def extract_page_hint(text: str) -> Optional[str]:
    match = PAGE_RE.search(text)
    return match.group(0).strip() if match else None


def normalize_lexical(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = re.sub(r"[^\w\u3400-\u4dbf\u4e00-\u9fff]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def normalize_doi(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    candidate = unicodedata.normalize("NFKC", value).strip()
    candidate = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", candidate, flags=re.I)
    candidate = re.sub(r"^doi\s*:\s*", "", candidate, flags=re.I)
    candidate = candidate.rstrip(".,;").strip()
    return candidate.casefold() if DOI_RE.fullmatch(candidate) else None


def normalize_arxiv_id(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    candidate = unicodedata.normalize("NFKC", value).strip()
    candidate = re.sub(r"^https?://arxiv\.org/(?:abs|pdf)/", "", candidate, flags=re.I)
    candidate = re.sub(r"^arxiv\s*:\s*", "", candidate, flags=re.I)
    candidate = re.sub(r"\.pdf$", "", candidate, flags=re.I)
    match = ARXIV_RE.fullmatch(candidate)
    return re.sub(r"v\d+$", "", match.group(0), flags=re.I).casefold() if match else None


def _year(fields: Mapping[str, object]) -> Optional[int]:
    value = fields.get("year")
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d{4}", value.strip()):
        return int(value)
    return None


def _paper_id(title: str, year: Optional[int], doi: Optional[str], arxiv_id: Optional[str]) -> str:
    if doi:
        return f"doi:{doi}"
    if arxiv_id:
        return f"arxiv:{arxiv_id}"
    normalized_title = normalize_lexical(title)
    return f"title:{normalized_title}|year:{year if year is not None else 'unknown'}"


def _cited_dois(body: str, current_doi: Optional[str]) -> Tuple[str, ...]:
    values = {
        normalized
        for match in DOI_RE.finditer(body)
        if (normalized := normalize_doi(match.group(0).rstrip(".,;)")))
        and normalized != current_doi
    }
    return tuple(sorted(values))


def _metadata_text(note: NoteDocument) -> str:
    fields = (
        ("题名", (note.title,)),
        ("中文题名", (note.title_zh,) if note.title_zh else ()),
        ("作者", note.authors),
        ("年份", (str(note.year),) if note.year is not None else ()),
        ("别名", note.aliases),
        ("标签", note.tags),
        ("关键发现", note.key_finding),
        ("任务", note.tasks),
        ("数据集", note.datasets),
        ("方法", note.methods),
        ("指标", note.metrics),
        ("可以支持", note.supports),
        ("不能支持", note.cannot_support),
    )
    return "\n".join(f"{label}：{'；'.join(values)}" for label, values in fields if values)


def scan_notes(repo_root: Path, pattern: str) -> CorpusScan:
    notes: List[NoteDocument] = []
    excluded: List[ExcludedDocument] = []
    for path in sorted(repo_root.glob(pattern)):
        if not path.is_file():
            continue
        relative_path = path.relative_to(repo_root).as_posix()
        if path.name.casefold() == "index.md":
            excluded.append(ExcludedDocument(relative_path, "index_document"))
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        try:
            fields, body = parse_frontmatter(text)
        except (ValueError, yaml.YAMLError) as error:
            excluded.append(
                ExcludedDocument(relative_path, "invalid_yaml", str(error).splitlines()[0])
            )
            continue
        source_pdf = extract_source_pdf(fields)
        if not source_pdf:
            excluded.append(ExcludedDocument(relative_path, "non_paper_missing_source_pdf"))
            continue
        title = _scalar(fields, "title")
        if not title:
            heading = HEADING_RE.search(body)
            title = heading.group(2).strip() if heading else path.stem
        title_zh = _scalar(fields, "title_zh")
        year = _year(fields)
        doi = normalize_doi(_scalar(fields, "doi"))
        arxiv_id = normalize_arxiv_id(_scalar(fields, "arxiv_id"))
        note_id = relative_path
        notes.append(
            NoteDocument(
                path=path,
                relative_path=relative_path,
                note_id=note_id,
                paper_id=_paper_id(title, year, doi, arxiv_id),
                title=title,
                title_zh=title_zh,
                authors=_list_field(fields, "authors"),
                year=year,
                aliases=_list_field(fields, "aliases"),
                tags=_list_field(fields, "tags"),
                key_finding=_list_field(fields, "key_finding"),
                tasks=_list_field(fields, "tasks", "task"),
                datasets=_list_field(fields, "datasets", "dataset"),
                methods=_list_field(fields, "methods", "method"),
                metrics=_list_field(fields, "metrics", "metric"),
                supports=_list_field(fields, "supports"),
                cannot_support=_list_field(fields, "cannot_support"),
                source_pdf=source_pdf,
                doi=doi,
                arxiv_id=arxiv_id,
                cited_dois=_cited_dois(body, doi),
                body=body.strip(),
                source_hash=hashlib.sha256(raw).hexdigest(),
            )
        )
    return CorpusScan(tuple(notes), tuple(excluded))


def load_notes(repo_root: Path, pattern: str) -> List[NoteDocument]:
    return list(scan_notes(repo_root, pattern).notes)


def excluded_summary(excluded: Sequence[ExcludedDocument]) -> Dict[str, object]:
    reasons = Counter(item.reason for item in excluded)
    return {
        "excluded": len(excluded),
        "excluded_reasons": dict(sorted(reasons.items())),
        "excluded_paths": [
            {
                "path": item.relative_path,
                "reason": item.reason,
                "detail": item.detail,
            }
            for item in excluded
        ],
    }


def source_manifest_hash(notes: Sequence[NoteDocument]) -> str:
    digest = hashlib.sha256()
    for note in notes:
        digest.update(note.note_id.encode("utf-8"))
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


def _chunk_key(
    note_id: str,
    heading: str,
    position: int,
    text_hash: str,
    embedding_contract_hash: str,
) -> str:
    payload = json.dumps(
        [note_id, heading, position, text_hash, embedding_contract_hash],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def chunk_note(
    note: NoteDocument,
    note_position: int,
    max_chars: int,
    overlap_chars: int,
    embedding_contract_hash: str = "",
) -> List[TextChunk]:
    if max_chars < 64 or overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("分块参数无效：最大字符数须至少为 64，重叠须非负且小于最大值")
    chunks: List[TextChunk] = []
    units = [("结构化元数据", _metadata_text(note)), *_section_units(note.body)]
    for heading, section in units:
        compact = re.sub(r"\n{3,}", "\n\n", section).strip()
        if not compact:
            continue
        prefix = f"{note.title}\n{heading}\n" if heading else f"{note.title}\n"
        budget = max_chars - min(len(prefix), max_chars // 3)
        for piece in _window_text(compact, budget, overlap_chars):
            text = (prefix + piece).strip()
            text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            position = len(chunks)
            chunks.append(
                TextChunk(
                    note_position=note_position,
                    position=position,
                    heading=heading,
                    page_hint=extract_page_hint(piece),
                    text=text,
                    lexical_text=normalize_lexical(text),
                    text_hash=text_hash,
                    chunk_key=_chunk_key(
                        note.note_id,
                        heading,
                        position,
                        text_hash,
                        embedding_contract_hash,
                    ),
                    embedding_contract_hash=embedding_contract_hash,
                )
            )
    if not chunks:
        text_hash = hashlib.sha256(note.title.encode("utf-8")).hexdigest()
        chunks.append(
            TextChunk(
                note_position,
                0,
                "",
                None,
                note.title,
                normalize_lexical(note.title),
                text_hash,
                _chunk_key(note.note_id, "", 0, text_hash, embedding_contract_hash),
                embedding_contract_hash,
            )
        )
    return chunks
