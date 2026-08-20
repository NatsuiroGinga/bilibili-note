from __future__ import annotations

import json
import os
import re
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .documents import normalize_lexical


USER_AGENT = "note-literature-search/0.1 (local academic metadata discovery)"


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    status: Dict[str, object]
    candidates: List[Dict[str, object]]


def _request_json(
    url: str,
    params: Mapping[str, object],
    headers: Optional[Mapping[str, str]],
    timeout: float,
) -> Tuple[Dict[str, Any], Mapping[str, str]]:
    encoded = urllib.parse.urlencode(
        {key: value for key, value in params.items() if value is not None}
    )
    request = urllib.request.Request(f"{url}?{encoded}")
    request.add_header("User-Agent", USER_AGENT)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
        return payload, dict(response.headers.items())


def _failure(provider: str, error: Exception, degraded: bool = True) -> ProviderResponse:
    if isinstance(error, urllib.error.HTTPError):
        detail = f"HTTP {error.code}"
    elif isinstance(error, urllib.error.URLError):
        detail = f"网络错误：{error.reason}"
    elif isinstance(error, TimeoutError):
        detail = "请求超时"
    else:
        detail = f"响应错误：{type(error).__name__}"
    return ProviderResponse(
        provider,
        {"ok": False, "degraded": degraded, "result_count": 0, "error": detail},
        [],
    )


def _clean_doi(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value.strip(), flags=re.I)
    return value.lower() or None


def _clean_arxiv(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = re.sub(r"^https?://arxiv\.org/(?:abs|pdf)/", "", value.strip(), flags=re.I)
    return value.removesuffix(".pdf") or None


def _candidate(
    provider: str,
    title: str,
    authors: Sequence[str],
    year: Optional[int],
    url: Optional[str],
    doi: Optional[str],
    arxiv_id: Optional[str],
    has_abstract: bool,
    provider_id: Optional[str],
    evidence_label: str = "外部题录候选（未核全文）",
) -> Dict[str, object]:
    return {
        "provider": provider,
        "provider_id": provider_id,
        "title": title.strip(),
        "authors": [name for name in authors if name][:8],
        "year": year,
        "url": url,
        "doi": _clean_doi(doi),
        "arxiv_id": _clean_arxiv(arxiv_id),
        "evidence_level": (
            "外部摘要候选（未核全文）" if has_abstract else evidence_label
        ),
        "full_text_verified": False,
    }


def search_openalex(query: str, limit: int, timeout: float) -> ProviderResponse:
    provider = "openalex"
    api_key = os.environ.get("OPENALEX_API_KEY")
    semantic = bool(api_key)
    params: Dict[str, object] = {
        "per_page": limit,
        "select": "id,doi,display_name,publication_year,authorships,primary_location,ids,abstract_inverted_index",
        "api_key": api_key,
        "search.semantic" if semantic else "search": query,
    }
    try:
        payload, _ = _request_json(
            "https://api.openalex.org/works", params, None, timeout
        )
        candidates = []
        for item in payload.get("results", []):
            authors = [
                entry.get("author", {}).get("display_name", "")
                for entry in item.get("authorships", [])
            ]
            ids = item.get("ids") or {}
            location = item.get("primary_location") or {}
            candidates.append(
                _candidate(
                    provider,
                    item.get("display_name") or "",
                    authors,
                    item.get("publication_year"),
                    location.get("landing_page_url") or item.get("id"),
                    item.get("doi"),
                    ids.get("arxiv"),
                    bool(item.get("abstract_inverted_index")),
                    item.get("id"),
                )
            )
        return ProviderResponse(
            provider,
            {
                "ok": True,
                "degraded": not semantic,
                "semantic": semantic,
                "result_count": len(candidates),
                "message": (
                    "已使用 OpenAlex 语义检索"
                    if semantic
                    else "未设置 OPENALEX_API_KEY，已回退普通作品检索"
                ),
            },
            candidates,
        )
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as error:
        response = _failure(provider, error)
        if not api_key:
            response.status["message"] = "普通作品检索也不可用；OpenAlex 当前语义检索需要 API 密钥"
        return response


def search_semantic_scholar(query: str, limit: int, timeout: float) -> ProviderResponse:
    provider = "semantic_scholar"
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    headers = {"x-api-key": api_key} if api_key else None
    params = {
        "query": query,
        "limit": limit,
        "fields": "paperId,title,abstract,url,externalIds,year,venue,authors",
    }
    try:
        payload, response_headers = _request_json(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params,
            headers,
            timeout,
        )
        candidates = []
        for item in payload.get("data", []):
            external = item.get("externalIds") or {}
            candidates.append(
                _candidate(
                    provider,
                    item.get("title") or "",
                    [author.get("name", "") for author in item.get("authors", [])],
                    item.get("year"),
                    item.get("url"),
                    external.get("DOI"),
                    external.get("ArXiv"),
                    bool(item.get("abstract")),
                    item.get("paperId"),
                )
            )
        return ProviderResponse(
            provider,
            {
                "ok": True,
                "degraded": False,
                "authenticated": bool(api_key),
                "result_count": len(candidates),
                "rate_limit_remaining": response_headers.get("x-ratelimit-remaining"),
            },
            candidates,
        )
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as error:
        return _failure(provider, error)


def _crossref_year(item: Mapping[str, Any]) -> Optional[int]:
    for field in ("published", "published-print", "published-online", "issued"):
        parts = (item.get(field) or {}).get("date-parts") or []
        if parts and parts[0]:
            try:
                return int(parts[0][0])
            except (TypeError, ValueError):
                continue
    return None


def search_crossref(query: str, limit: int, timeout: float) -> ProviderResponse:
    provider = "crossref"
    mailto = os.environ.get("CROSSREF_MAILTO")
    params = {"query.bibliographic": query, "rows": limit, "mailto": mailto}
    try:
        payload, response_headers = _request_json(
            "https://api.crossref.org/works", params, None, timeout
        )
        candidates = []
        for item in (payload.get("message") or {}).get("items", []):
            titles = item.get("title") or []
            authors = [
                " ".join(part for part in (a.get("given"), a.get("family")) if part)
                for a in item.get("author", [])
            ]
            candidates.append(
                _candidate(
                    provider,
                    titles[0] if titles else "",
                    authors,
                    _crossref_year(item),
                    item.get("URL"),
                    item.get("DOI"),
                    None,
                    bool(item.get("abstract")),
                    item.get("DOI"),
                    evidence_label="外部题录核验候选（未核全文）",
                )
            )
        return ProviderResponse(
            provider,
            {
                "ok": True,
                "degraded": False,
                "polite_pool": bool(mailto),
                "result_count": len(candidates),
                "rate_limit": response_headers.get("x-rate-limit-limit"),
                "rate_limit_interval": response_headers.get("x-rate-limit-interval"),
            },
            candidates,
        )
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as error:
        return _failure(provider, error)


def _local_inventory(
    connection: Optional[sqlite3.Connection], repo_root: Path
) -> List[Dict[str, object]]:
    if connection is None:
        return []
    inventory = []
    for row in connection.execute(
        "SELECT path,title,source_pdf,doi,arxiv_id FROM notes ORDER BY id"
    ):
        source_pdf = row["source_pdf"]
        inventory.append(
            {
                "path": row["path"],
                "title_key": normalize_lexical(row["title"]),
                "doi": _clean_doi(row["doi"]),
                "arxiv_id": _clean_arxiv(row["arxiv_id"]),
                "source_pdf": source_pdf,
                "raw_exists": bool(source_pdf and (repo_root / source_pdf).is_file()),
            }
        )
    return inventory


def _annotate_local(candidate: Dict[str, object], inventory: Sequence[Dict[str, object]]) -> None:
    title_key = normalize_lexical(str(candidate.get("title") or ""))
    doi = candidate.get("doi")
    arxiv_id = candidate.get("arxiv_id")
    match = next(
        (
            item
            for item in inventory
            if (doi and item["doi"] == doi)
            or (arxiv_id and item["arxiv_id"] == arxiv_id)
            or (title_key and item["title_key"] == title_key)
        ),
        None,
    )
    candidate["has_wiki"] = match is not None
    candidate["wiki_path"] = match["path"] if match else None
    candidate["has_raw"] = bool(match and match["raw_exists"])
    candidate["raw_path"] = match["source_pdf"] if match else None
    candidate["zotero_status"] = "未检查（任务边界禁止访问 Zotero）"


def discover_online(
    query: str,
    limit: int,
    timeout: float,
    repo_root: Path,
    connection: Optional[sqlite3.Connection] = None,
) -> Dict[str, object]:
    if limit < 1 or limit > 100:
        raise ValueError("在线结果数必须在 1 到 100 之间")
    if timeout <= 0:
        raise ValueError("在线超时必须为正数")
    responses = [
        search_openalex(query, limit, timeout),
        search_semantic_scholar(query, limit, timeout),
        search_crossref(query, limit, timeout),
    ]
    inventory = _local_inventory(connection, repo_root)
    candidates: List[Dict[str, object]] = []
    for response in responses:
        for candidate in response.candidates:
            _annotate_local(candidate, inventory)
            candidates.append(candidate)
    return {
        "provider_status": {response.provider: response.status for response in responses},
        "results": candidates,
        "candidate_count": len(candidates),
        "evidence_warning": "在线结果仅为题录或摘要候选，未核全文，不得直接写入论文结论。",
    }
