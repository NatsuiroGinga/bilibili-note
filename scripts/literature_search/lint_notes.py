from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Sequence

import yaml

from .documents import extract_source_pdf, normalize_arxiv_id, normalize_doi, parse_frontmatter


SCHEMA = "paper-note-search/v1"
LIST_FIELDS = (
    "authors", "aliases", "tags", "key_finding", "tasks", "datasets", "methods",
    "metrics", "supports", "cannot_support", "related",
)
REQUIRED_FIELDS = (
    "title", "title_zh", "authors", "year", "date", "journal", "doi", "arxiv_id",
    "source_pdf", "fulltext_verified", "aliases", "tags", "key_finding", "tasks",
    "datasets", "methods", "metrics", "supports", "cannot_support", "related",
)
REQUIRED_SECTIONS = ("论文可以支持", "论文不能支持", "实验结果与负证据", "与本课题的关系")
PAGE_ANCHOR_RE = re.compile(
    r"(?:印刷|物理|PDF)\s*(?:p\.?|第)?\s*\d+\s*(?:页)?|第\s*\d+\s*页",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LintIssue:
    severity: str
    code: str
    message: str


def _issue(issues: List[LintIssue], strict: bool, code: str, message: str) -> None:
    issues.append(LintIssue("error" if strict else "warning", code, message))


def _nonempty_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def lint_note(repo_root: Path, path: Path, force_strict: bool = False) -> Dict[str, object]:
    resolved = path.resolve()
    if not resolved.is_relative_to(repo_root.resolve()):
        return {"path": str(path), "schema": None, "mode": "invalid", "valid": False,
                "issues": [asdict(LintIssue("error", "outside_repo", "路径必须位于仓库内"))]}
    relative = resolved.relative_to(repo_root.resolve()).as_posix()
    issues: List[LintIssue] = []
    try:
        text = resolved.read_text(encoding="utf-8")
        fields, body = parse_frontmatter(text)
    except (OSError, ValueError, yaml.YAMLError) as error:
        return {"path": relative, "schema": None, "mode": "invalid", "valid": False,
                "issues": [asdict(LintIssue("error", "yaml_invalid", str(error).splitlines()[0]))]}

    schema = fields.get("schema")
    strict = force_strict or schema == SCHEMA
    mode = "strict" if strict else "legacy_compatibility"
    if schema != SCHEMA:
        _issue(issues, strict, "schema_missing", f"schema 应为 {SCHEMA}")
    for field in REQUIRED_FIELDS:
        if field not in fields:
            _issue(issues, strict, "field_missing", f"缺少字段：{field}")
    for field in LIST_FIELDS:
        if field in fields and not _nonempty_list(fields[field]):
            _issue(issues, strict, "field_type", f"{field} 必须是非空字符串列表")
    for field in ("title", "title_zh", "journal", "source_pdf"):
        if field in fields and not (
            isinstance(fields[field], str) and fields[field].strip()
        ):
            _issue(issues, strict, "field_type", f"{field} 必须是非空字符串")
    if "year" in fields and (isinstance(fields["year"], bool) or not isinstance(fields["year"], int)):
        _issue(issues, strict, "year_type", "year 必须是整数")
    if "fulltext_verified" in fields and fields["fulltext_verified"] is not True:
        _issue(issues, strict, "fulltext_unverified", "fulltext_verified 必须为 true")
    if "tags" in fields and isinstance(fields["tags"], list) and "类型/论文" not in fields["tags"]:
        _issue(issues, strict, "paper_tag_missing", "tags 必须包含 类型/论文")

    doi_value = fields.get("doi")
    arxiv_value = fields.get("arxiv_id")
    normalized_doi = normalize_doi(str(doi_value)) if doi_value is not None else None
    normalized_arxiv = (
        normalize_arxiv_id(str(arxiv_value)) if arxiv_value is not None else None
    )
    if doi_value is not None and normalized_doi is None:
        _issue(issues, strict, "doi_invalid", "doi 不是规范 DOI")
    if arxiv_value is not None and normalized_arxiv is None:
        _issue(issues, strict, "arxiv_invalid", "arxiv_id 不是规范 arXiv 标识")
    if not normalized_doi and not normalized_arxiv:
        if not (isinstance(fields.get("title"), str) and isinstance(fields.get("year"), int)):
            _issue(issues, strict, "identity_missing", "无 DOI/arXiv 时必须用题名和年份生成身份")

    source_pdf = extract_source_pdf(fields)
    if not source_pdf:
        _issue(issues, strict, "source_pdf_missing", "source_pdf 不能为空")
    else:
        source_path = (repo_root / source_pdf).resolve()
        raw_root = (repo_root / "raw/papers").resolve()
        if not source_path.is_relative_to(raw_root):
            _issue(issues, strict, "source_pdf_scope", "source_pdf 必须位于 raw/papers/")
        elif not source_path.is_file():
            _issue(issues, strict, "source_pdf_not_found", f"原件不存在：{source_pdf}")

    if not PAGE_ANCHOR_RE.search(body):
        _issue(issues, strict, "page_anchor_missing", "正文缺少印刷页、物理页或 PDF 页锚点")
    for section in REQUIRED_SECTIONS:
        if not re.search(rf"^#+\s+.*{re.escape(section)}", body, re.MULTILINE):
            _issue(issues, strict, "section_missing", f"缺少正文分区：{section}")
    errors = sum(issue.severity == "error" for issue in issues)
    warnings = sum(issue.severity == "warning" for issue in issues)
    return {"path": relative, "schema": schema, "mode": mode, "valid": errors == 0,
            "error_count": errors, "warning_count": warnings,
            "issues": [asdict(issue) for issue in issues]}


def lint_paths(
    repo_root: Path, paths: Sequence[Path], strict: bool = False
) -> Dict[str, object]:
    results = [lint_note(repo_root, path if path.is_absolute() else repo_root / path, strict) for path in paths]
    return {
        "schema": SCHEMA,
        "strict_requested": strict,
        "file_count": len(results),
        "error_count": sum(int(item.get("error_count", not item["valid"])) for item in results),
        "warning_count": sum(int(item.get("warning_count", 0)) for item in results),
        "valid": all(bool(item["valid"]) for item in results),
        "results": results,
        "auto_modified": False,
    }
