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

# MOC 导航页判定：文件名字面量为 INDEX.md。
# 依据：2026-08-28 检索精度评测（.Codex/docs/RWKV/2026-08-28-文献检索精度评测与改进方案.md）
# 实测这批页面在语料中占 15/525=2.9%，却占据 40% 的查询第 1 名命中，超额表征约 14 倍——
# 因为其正文是论文标题清单，几乎匹配所有主题查询的字符三元组，并借标题字段的 BM25 权重占位。
# 用 Path.name（而非从相对路径字符串裁剪）判定，避免与其他代理踩过的“裸文件名做字典键”
# 陷阱同类的路径拼装错误；此处只是逐文件布尔判定，不涉及按文件名建字典，因此该陷阱不适用，
# 但仍统一用 Path.name 以保持判定方式单一、可读。
NAVIGATION_PAGE_FILENAME = "INDEX.md"

# frontmatter 中并入可检索正文的字段，按对检索有用的顺序排列。
# 依据：同一份评测报告实测 tags 覆盖率 100.0%、key_finding 覆盖率 96.6%，
# 且 parse_frontmatter 当前把整段 frontmatter（含这些字段）剥离后丢弃，全库 0 命中。
METADATA_FIELDS = ("tags", "key_finding", "venue", "authors", "year", "aliases")


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


def is_navigation_page(path: Path) -> bool:
    """判定笔记文件是否为 MOC 导航页（文件名字面量为 INDEX.md）。

    用 `Path.name` 取文件名，不依赖相对路径字符串裁剪，见模块顶部常量注释。
    """
    return path.name == NAVIGATION_PAGE_FILENAME


def parse_metadata_fields(text: str) -> Dict[str, object]:
    """解析 frontmatter 中的元数据字段，支持单行标量、缩进列表与内联数组三种写法。

    与 parse_frontmatter 相互独立：parse_frontmatter 的返回契约（Dict[str, str] 简单标量、
    以及剥离 frontmatter 后的正文）保持不变，供其余调用方（如 doi/arxiv 识别、标题回退）
    继续使用；本函数只服务于“把 tags/key_finding 等字段并入可检索正文”这一新用途，
    返回值可以是 list，因此不能复用同一份解析结果。
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: Dict[str, object] = {}
    current_key: Optional[str] = None
    for line in match.group(1).splitlines():
        list_item = re.match(r"^\s+-\s+(.*)$", line)
        if list_item and current_key is not None:
            value = list_item.group(1).strip().strip("\"'")
            bucket = fields.setdefault(current_key, [])
            if isinstance(bucket, list):
                bucket.append(value)
            continue
        scalar = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if scalar:
            key, raw_value = scalar.group(1), scalar.group(2).strip()
            if not raw_value:
                fields[key] = []
                current_key = key
                continue
            if raw_value.startswith("[") and raw_value.endswith("]"):
                fields[key] = [
                    piece.strip().strip("\"'")
                    for piece in raw_value[1:-1].split(",")
                    if piece.strip()
                ]
            else:
                fields[key] = raw_value.strip("\"'")
            current_key = None
    return fields


def render_metadata_section(fields: Dict[str, object]) -> str:
    """把 METADATA_FIELDS 涉及的 frontmatter 字段渲染成一个可检索的正文小节。"""
    lines: List[str] = []
    for key in METADATA_FIELDS:
        value = fields.get(key)
        if not value:
            continue
        if isinstance(value, list):
            rendered = "、".join(str(item) for item in value if str(item).strip())
        else:
            rendered = str(value)
        if not rendered.strip():
            continue
        lines.append(f"{key}：{rendered}")
    if not lines:
        return ""
    return "## 条目元数据\n\n" + "\n".join(lines) + "\n\n"


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
        if is_navigation_page(path):
            # 排除 MOC 导航页，见 NAVIGATION_PAGE_FILENAME 处的实测依据。
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        fields, body = parse_frontmatter(text)
        title = fields.get("title")
        if not title:
            heading = HEADING_RE.search(body)
            title = heading.group(2).strip() if heading else path.stem
        doi, arxiv_id = _extract_identifier(fields, body)
        # 把 tags / key_finding 等人工标注渲染成正文小节，走既有分块通路使其可检索；
        # parse_frontmatter 的返回契约保持不变，见 parse_metadata_fields 的说明。
        metadata_section = render_metadata_section(parse_metadata_fields(text))
        body = (metadata_section + body.strip()).strip()
        notes.append(
            NoteDocument(
                path=path,
                relative_path=path.relative_to(repo_root).as_posix(),
                title=title,
                source_pdf=extract_source_pdf(fields),
                doi=doi,
                arxiv_id=arxiv_id,
                body=body,
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
    title_prefix: bool = True,
) -> List[TextChunk]:
    """把一篇笔记切成分块。

    ``title_prefix`` 控制是否把「笔记标题＋小节标题」拼在每块开头。默认 True，
    与既有索引一致。置 False 时只保留小节标题，用于量化标题重复的影响——
    一篇 20 块的笔记会让标题词在索引中出现 20 次，这对词法通道是超额表征，
    也是 2026-08-31 发现「查询取自笔记字段时评测饱和」的成因之一。
    """
    if max_chars < 64 or overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("分块参数无效：最大字符数须至少为 64，重叠须非负且小于最大值")
    chunks: List[TextChunk] = []
    for heading, section in _section_units(note.body):
        compact = re.sub(r"\n{3,}", "\n\n", section).strip()
        if not compact:
            continue
        if title_prefix:
            prefix = f"{note.title}\n{heading}\n" if heading else f"{note.title}\n"
        else:
            prefix = f"{heading}\n" if heading else ""
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
