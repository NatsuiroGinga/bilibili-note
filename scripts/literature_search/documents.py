from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from datetime import date, datetime
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
DATE_RE = re.compile(r"(?<!\d)(20\d{2})[-_/](0[1-9]|1[0-2])[-_/](0[1-9]|[12]\d|3[01])(?!\d)")
PRIVATE_ADDRESS_RE = re.compile(
    r"(?<!\d)(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
    r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})(?!\d)"
)
SECRET_VALUE_RE = re.compile(
    r"(?im)\b(?:api[_-]?key|access[_-]?token|auth(?:orization)?|password|passwd|secret)"
    r"\s*[:=]\s*[\"']?[A-Za-z0-9_./+\-=]{8,}"
)
PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
BLOCKED_PATH_PARTS = {
    ".git",
    ".cache",
    ".codex-pycache",
    ".codex-validation-cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "vendor",
    "bin",
    "pkg",
    "runs",
}
BLOCKED_RECEIPT_PARTS = BLOCKED_PATH_PARTS - {"runs"}
BLOCKED_PATH_WORDS = (
    "archive",
    "备份",
    "backup",
    "checkpoint",
    "prediction",
    "sample",
    "member",
    "最终测试",
    "private",
    "credential",
    "secret",
)
RECEIPT_ALLOWED_KEY_RE = re.compile(
    r"(?:^|[._])(?:status|state|run_id|name|metric|accuracy|f1|precision|recall|auc|"
    r"loss|latency|memory|duration|epoch|seed|dataset|model|started|completed|"
    r"timestamp|count|size|hash|sha256)(?:$|[._])",
    re.IGNORECASE,
)
RECEIPT_BLOCKED_KEY_RE = re.compile(
    r"token|password|secret|authorization|credential|host|address|command|"
    r"prediction|sample|member|label|array|checkpoint|path",
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
    governance_fields = (
        (
            ("文档集合", (note.collection,)),
            ("文档类型", (note.doc_type,)),
            ("权威类型", (note.authority,)),
            ("路线", (note.route,) if note.route else ()),
            ("章节", (note.chapter,) if note.chapter else ()),
            ("状态", (note.status,)),
            ("证据等级", (note.evidence_level,)),
        )
        if note.collection != "papers"
        else ()
    )
    fields = (
        ("题名", (note.title,)),
        *governance_fields,
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
        content_reason = _credential_content_exclusion(text)
        if content_reason:
            excluded.append(ExcludedDocument(relative_path, content_reason))
            continue
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
                collection="papers",
                doc_type="paper-note",
                authority="source",
                route=None,
                chapter=None,
                status="current",
                fact_date=str(year) if year is not None else None,
                evidence_level="本地结构化全文笔记",
                sensitivity="project",
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


def _path_exclusion(path: Path, blocked_parts: set[str]) -> Optional[str]:
    folded_parts = {part.casefold() for part in path.parts}
    if folded_parts & blocked_parts:
        return "ignored_directory"
    folded_path = path.as_posix().casefold()
    if any(word in folded_path for word in BLOCKED_PATH_WORDS):
        return "archive_backup_or_sensitive_path"
    if path.name.casefold() == "index.md":
        return "index_document"
    return None


def _content_exclusion(text: str) -> Optional[str]:
    credential_reason = _credential_content_exclusion(text)
    if credential_reason:
        return credential_reason
    if PRIVATE_ADDRESS_RE.search(text):
        return "private_address_content"
    return None


def _credential_content_exclusion(text: str) -> Optional[str]:
    if PRIVATE_KEY_RE.search(text) or SECRET_VALUE_RE.search(text):
        return "suspected_credential_content"
    return None


def _document_date(fields: Mapping[str, object], relative_path: str) -> Optional[str]:
    for key in ("date", "created", "updated", "built_at", "timestamp"):
        value = fields.get(key)
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, str) and value.strip():
            match = DATE_RE.search(value)
            if match:
                return "-".join(match.groups())
    match = DATE_RE.search(relative_path)
    return "-".join(match.groups()) if match else None


def _route(relative_path: str) -> Optional[str]:
    folded = relative_path.casefold()
    if "rwkv" in folded:
        return "RWKV"
    if "pinn" in folded or re.search(r"(?:^|[-_/])r2(?:[-_/]|$)", folded):
        return "PINN-R2"
    return None


def _chapter(relative_path: str) -> Optional[str]:
    folded = relative_path.casefold()
    for value, patterns in {
        "3": ("第三章", "第3章", "ch3", "chapter-3", "chapter_3"),
        "4": ("第四章", "第4章", "ch4", "chapter-4", "chapter_4"),
    }.items():
        if any(pattern in folded for pattern in patterns):
            return value
    return None


def _title(fields: Mapping[str, object], body: str, path: Path) -> str:
    title = _scalar(fields, "title")
    if title:
        return title
    heading = HEADING_RE.search(body)
    return heading.group(2).strip() if heading else path.stem


def _classify_markdown(
    relative_path: str, body: str
) -> Tuple[str, str, str, str, str]:
    path = Path(relative_path)
    folded = relative_path.casefold()
    name = path.name.casefold()
    if name in {"agents.md", "claude.md"}:
        return "route-control", "control", "current-control", "current", "项目规则或路线合同"
    if name == "readme.md":
        return "research-notes", "readme", "requirement", "current", "项目说明"
    if relative_path in {
        "output/开题改进交接文档.md",
        "output/第一创新点实验总控.md",
    }:
        return "recovery", "recovery-card", "history", "superseded", "历史路线状态合同"
    if folded.startswith("thesis/chapters/"):
        return "thesis-chapters", "thesis-chapter", "public-draft", "active", "论文正文草稿"
    if folded.startswith("output/"):
        return "output-deliverables", "deliverable", "public-draft", "active", "高层交付文档"
    if "恢复卡" in path.name:
        status = "superseded" if path.name == "RWKV当前恢复卡.md" else "current"
        return "recovery", "recovery-card", "current-control", status, "当前状态合同"
    if "总控" in path.name:
        return "route-control", "control", "current-control", "current", "项目规则或路线合同"
    if name == "task_plan.md" or "实施计划" in path.name or "计划" in path.stem:
        status = "active" if "- [ ]" in body else "completed"
        return "plans", "plan", "requirement", status, "实施计划"
    if any(word in path.stem for word in ("报告", "审计", "审查", "复审", "评估")):
        return "reports", "report", "review", "completed", "审查或实施报告"
    evidence = "结构化知识笔记" if folded.startswith("wiki/") else "研究过程笔记"
    return "research-notes", "research-note", "working-note", "active", evidence


def _generic_markdown_document(path: Path, repo_root: Path) -> NoteDocument:
    relative_path = path.relative_to(repo_root).as_posix()
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    fields: Dict[str, object] = {}
    body = text
    if FRONTMATTER_RE.match(text):
        try:
            fields, body = parse_frontmatter(text)
        except (ValueError, yaml.YAMLError):
            fields = {}
            body = text
    collection, doc_type, authority, status, evidence_level = _classify_markdown(
        relative_path, body
    )
    title = _title(fields, body, path)
    return NoteDocument(
        path=path,
        relative_path=relative_path,
        note_id=relative_path,
        paper_id=f"document:{relative_path}",
        collection=collection,
        doc_type=doc_type,
        authority=authority,
        route=(
            "PINN-R2"
            if relative_path
            in {"output/开题改进交接文档.md", "output/第一创新点实验总控.md"}
            else _route(relative_path)
        ),
        chapter=_chapter(relative_path),
        status=status,
        fact_date=_document_date(fields, relative_path),
        evidence_level=evidence_level,
        sensitivity="project",
        title=title,
        title_zh=None,
        authors=(),
        year=None,
        aliases=(),
        tags=(),
        key_finding=(),
        tasks=(),
        datasets=(),
        methods=(),
        metrics=(),
        supports=(),
        cannot_support=(),
        source_pdf="",
        doi=None,
        arxiv_id=None,
        cited_dois=(),
        body=body.strip(),
        source_hash=hashlib.sha256(raw).hexdigest(),
    )


def _receipt_values(value: object, prefix: str = "", depth: int = 0) -> List[str]:
    if depth > 5:
        return []
    values: List[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            name = str(key)
            full_name = f"{prefix}.{name}" if prefix else name
            if RECEIPT_BLOCKED_KEY_RE.search(name):
                continue
            values.extend(_receipt_values(item, full_name, depth + 1))
        return values
    if isinstance(value, list):
        if len(value) <= 16 and prefix and RECEIPT_ALLOWED_KEY_RE.search(prefix):
            scalars = [str(item) for item in value if isinstance(item, (str, int, float, bool))]
            if len(scalars) == len(value):
                values.append(f"{prefix}: {', '.join(scalars)}")
        return values
    if (
        prefix
        and RECEIPT_ALLOWED_KEY_RE.search(prefix)
        and isinstance(value, (str, int, float, bool))
        and len(str(value)) <= 400
    ):
        values.append(f"{prefix}: {value}")
    return values


def _receipt_document(path: Path, repo_root: Path, payload: object, raw: bytes) -> NoteDocument:
    relative_path = path.relative_to(repo_root).as_posix()
    values = _receipt_values(payload)
    body = "\n".join(values)
    status_value = next(
        (
            line.split(":", 1)[1].strip().casefold()
            for line in values
            if line.split(":", 1)[0].casefold().split(".")[-1] == "status"
        ),
        "completed",
    )
    status = "active" if status_value in {"active", "running", "pending"} else "completed"
    fields = payload if isinstance(payload, Mapping) else {}
    return NoteDocument(
        path=path,
        relative_path=relative_path,
        note_id=relative_path,
        paper_id=f"document:{relative_path}",
        collection="experiment-receipts",
        doc_type="experiment-receipt",
        authority="run-fact",
        route=_route(relative_path),
        chapter=_chapter(relative_path),
        status=status,
        fact_date=_document_date(fields, relative_path),
        evidence_level="聚合运行收据",
        sensitivity="restricted",
        title=f"运行收据 {path.parent.name} {path.name}",
        title_zh=None,
        authors=(),
        year=None,
        aliases=(),
        tags=(),
        key_finding=(),
        tasks=(),
        datasets=(),
        methods=(),
        metrics=(),
        supports=(),
        cannot_support=(),
        source_pdf="",
        doi=None,
        arxiv_id=None,
        cited_dois=(),
        body=body,
        source_hash=hashlib.sha256(raw).hexdigest(),
    )


def scan_corpus(
    repo_root: Path,
    paper_pattern: str,
    project_patterns: Sequence[str],
    receipt_patterns: Sequence[str],
    max_document_bytes: int,
) -> CorpusScan:
    paper_scan = scan_notes(repo_root, paper_pattern)
    notes = list(paper_scan.notes)
    excluded = list(paper_scan.excluded)
    seen = {note.relative_path for note in notes}

    markdown_paths = {
        path
        for pattern in project_patterns
        for path in repo_root.glob(pattern)
        if path.is_file()
    }
    for path in sorted(markdown_paths):
        relative_path = path.relative_to(repo_root).as_posix()
        if relative_path in seen or relative_path.startswith("wiki/papers/"):
            continue
        reason = _path_exclusion(Path(relative_path), BLOCKED_PATH_PARTS)
        if reason:
            excluded.append(ExcludedDocument(relative_path, reason))
            continue
        if path.stat().st_size > max_document_bytes:
            excluded.append(ExcludedDocument(relative_path, "document_too_large"))
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        reason = _content_exclusion(text)
        if reason:
            excluded.append(ExcludedDocument(relative_path, reason))
            continue
        notes.append(_generic_markdown_document(path, repo_root))
        seen.add(relative_path)

    receipt_paths = {
        path
        for pattern in receipt_patterns
        for path in repo_root.glob(pattern)
        if path.is_file()
    }
    for path in sorted(receipt_paths):
        relative_path = path.relative_to(repo_root).as_posix()
        if relative_path in seen:
            continue
        reason = _path_exclusion(Path(relative_path), BLOCKED_RECEIPT_PARTS)
        if reason:
            excluded.append(ExcludedDocument(relative_path, reason))
            continue
        if path.stat().st_size > max_document_bytes:
            excluded.append(ExcludedDocument(relative_path, "receipt_too_large"))
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        reason = _content_exclusion(text)
        if reason:
            excluded.append(ExcludedDocument(relative_path, reason))
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            excluded.append(
                ExcludedDocument(relative_path, "invalid_receipt_json", str(error).splitlines()[0])
            )
            continue
        document = _receipt_document(path, repo_root, payload, raw)
        if not document.body:
            excluded.append(ExcludedDocument(relative_path, "receipt_without_allowlisted_fields"))
            continue
        notes.append(document)
        seen.add(relative_path)
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
