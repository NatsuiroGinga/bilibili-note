from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .documents import normalize_lexical


USER_AGENT = "note-literature-search/0.1 (local academic metadata discovery)"
PROVIDER_ORDER = ("openalex", "semantic_scholar", "crossref")
RETRYABLE_HTTP_STATUS = {429, 503}
CROSSREF_SINGLEFLIGHT = threading.Lock()


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    status: Dict[str, object]
    candidates: List[Dict[str, object]]


@dataclass(frozen=True)
class RequestReceipt:
    payload: Dict[str, Any]
    headers: Mapping[str, str]
    retry_count: int
    backoff_seconds: float


class RequestFailure(Exception):
    def __init__(
        self, error: Exception, retry_count: int = 0, backoff_seconds: float = 0.0
    ) -> None:
        super().__init__(str(error))
        self.error = error
        self.retry_count = retry_count
        self.backoff_seconds = backoff_seconds


def _retry_after_seconds(error: urllib.error.HTTPError, timeout: float) -> Optional[float]:
    value = error.headers.get("Retry-After") if error.headers else None
    if value is None:
        return None
    try:
        seconds = float(value)
    except ValueError:
        return None
    return seconds if 0.0 < seconds <= timeout else None


def _request_json(
    url: str,
    params: Mapping[str, object],
    headers: Optional[Mapping[str, str]],
    timeout: float,
) -> RequestReceipt:
    encoded = urllib.parse.urlencode(
        {key: value for key, value in params.items() if value is not None}
    )
    request = urllib.request.Request(f"{url}?{encoded}")
    request.add_header("User-Agent", USER_AGENT)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    retry_count = 0
    backoff_seconds = 0.0
    while True:
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("JSON 响应根节点不是对象")
                return RequestReceipt(
                    payload,
                    {key.casefold(): value for key, value in response.headers.items()},
                    retry_count,
                    backoff_seconds,
                )
        except urllib.error.HTTPError as error:
            delay = _retry_after_seconds(error, timeout)
            if error.code in RETRYABLE_HTTP_STATUS and retry_count == 0 and delay:
                time.sleep(delay)
                retry_count = 1
                backoff_seconds = delay
                continue
            raise RequestFailure(error, retry_count, backoff_seconds) from error
        except (
            urllib.error.URLError,
            TimeoutError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            raise RequestFailure(error, retry_count, backoff_seconds) from error


def _base_status(
    state: str,
    ok: bool,
    authenticated: bool,
    started: float,
) -> Dict[str, object]:
    return {
        "state": state,
        "ok": ok,
        "authenticated": authenticated,
        "latency_ms": round((time.perf_counter() - started) * 1000.0, 3),
        "cache_kind": "none",
        "cache_hit": False,
        "rate_limited": False,
        "retry_count": 0,
        "backoff_seconds": 0.0,
        "degraded": not ok,
        "degradation_reason": None if ok else state,
        "result_count": 0,
    }


def _failure(
    provider: str,
    failure: RequestFailure,
    authenticated: bool,
    started: float,
) -> ProviderResponse:
    error = failure.error
    http_status = error.code if isinstance(error, urllib.error.HTTPError) else None
    if isinstance(error, urllib.error.HTTPError):
        detail = f"HTTP {error.code}"
    elif isinstance(error, urllib.error.URLError):
        detail = f"网络错误：{error.reason}"
    elif isinstance(error, TimeoutError):
        detail = "请求超时"
    else:
        detail = f"响应错误：{type(error).__name__}"
    status = _base_status("failed", False, authenticated, started)
    status.update(
        {
            "http_status": http_status,
            "rate_limited": http_status == 429,
            "retry_count": failure.retry_count,
            "backoff_seconds": failure.backoff_seconds,
            "degradation_reason": detail,
            "error": detail,
        }
    )
    return ProviderResponse(provider, status, [])


def _clean_doi(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value.strip(), flags=re.I)
    return value.lower() or None


def _clean_arxiv(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = re.sub(r"^https?://arxiv\.org/(?:abs|pdf)/", "", value.strip(), flags=re.I)
    return re.sub(r"v\d+$", "", value.removesuffix(".pdf"), flags=re.I).lower() or None


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
        "providers": [provider],
        "provider_id": provider_id,
        "provider_records": [
            {"provider": provider, "provider_id": provider_id, "url": url}
        ],
        "title": title.strip(),
        "authors": [name for name in authors if name],
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
    started = time.perf_counter()
    if not api_key:
        status = _base_status("skipped_missing_key", False, False, started)
        status["degradation_reason"] = "OPENALEX_API_KEY 未设置"
        return ProviderResponse(provider, status, [])
    params: Dict[str, object] = {
        "per_page": limit,
        "select": "id,doi,display_name,publication_year,authorships,primary_location,ids,abstract_inverted_index",
        "api_key": api_key,
        "search.semantic": query,
    }
    try:
        receipt = _request_json("https://api.openalex.org/works", params, None, timeout)
        candidates = []
        for item in receipt.payload.get("results", []):
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
        status = _base_status("ok", True, True, started)
        status.update(
            {
                "semantic": True,
                "result_count": len(candidates),
                "retry_count": receipt.retry_count,
                "backoff_seconds": receipt.backoff_seconds,
            }
        )
        return ProviderResponse(provider, status, candidates)
    except RequestFailure as failure:
        return _failure(provider, failure, True, started)


def search_semantic_scholar(query: str, limit: int, timeout: float) -> ProviderResponse:
    provider = "semantic_scholar"
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    started = time.perf_counter()
    headers = {"x-api-key": api_key} if api_key else None
    params = {
        "query": query,
        "limit": limit,
        "fields": "paperId,title,abstract,url,externalIds,year,venue,authors",
    }
    try:
        receipt = _request_json(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params,
            headers,
            timeout,
        )
        candidates = []
        for item in receipt.payload.get("data", []):
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
        status = _base_status("ok", True, bool(api_key), started)
        status.update(
            {
                "result_count": len(candidates),
                "retry_count": receipt.retry_count,
                "backoff_seconds": receipt.backoff_seconds,
                "rate_limit_remaining": receipt.headers.get("x-ratelimit-remaining"),
            }
        )
        return ProviderResponse(provider, status, candidates)
    except RequestFailure as failure:
        return _failure(provider, failure, bool(api_key), started)


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
    started = time.perf_counter()
    params = {"query.bibliographic": query, "rows": limit, "mailto": mailto}
    try:
        with CROSSREF_SINGLEFLIGHT:
            receipt = _request_json("https://api.crossref.org/works", params, None, timeout)
        candidates = []
        for item in (receipt.payload.get("message") or {}).get("items", []):
            titles = item.get("title") or []
            authors = [
                " ".join(part for part in (author.get("given"), author.get("family")) if part)
                for author in item.get("author", [])
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
        status = _base_status("ok", True, bool(mailto), started)
        status.update(
            {
                "polite_pool": bool(mailto),
                "singleflight": True,
                "result_count": len(candidates),
                "retry_count": receipt.retry_count,
                "backoff_seconds": receipt.backoff_seconds,
                "rate_limit": receipt.headers.get("x-rate-limit-limit"),
                "rate_limit_interval": receipt.headers.get("x-rate-limit-interval"),
            }
        )
        return ProviderResponse(provider, status, candidates)
    except RequestFailure as failure:
        response = _failure(provider, failure, bool(mailto), started)
        response.status["polite_pool"] = bool(mailto)
        response.status["singleflight"] = True
        return response


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


def _candidate_key(candidate: Mapping[str, object]) -> str:
    if candidate.get("doi"):
        return f"doi:{candidate['doi']}"
    if candidate.get("arxiv_id"):
        return f"arxiv:{candidate['arxiv_id']}"
    title = normalize_lexical(str(candidate.get("title") or ""))
    if title:
        return f"title:{title}|year:{candidate.get('year') or 'unknown'}"
    return f"provider:{candidate['provider']}:{candidate.get('provider_id') or 'unknown'}"


def _merge_candidates(
    responses: Sequence[ProviderResponse],
) -> Tuple[List[Dict[str, object]], Dict[str, Tuple[int, int]]]:
    merged: Dict[str, Dict[str, object]] = {}
    provider_counts: Dict[str, List[int]] = {
        provider: [0, 0] for provider in PROVIDER_ORDER
    }
    for response in responses:
        for candidate in response.candidates:
            key = _candidate_key(candidate)
            existing = merged.get(key)
            if existing is None:
                merged[key] = candidate
                provider_counts[response.provider][0] += 1
                continue
            provider_counts[response.provider][1] += 1
            existing["providers"] = list(
                dict.fromkeys([*existing["providers"], *candidate["providers"]])
            )
            existing["provider_records"] = [
                *existing["provider_records"],
                *candidate["provider_records"],
            ]
            existing["authors"] = list(
                dict.fromkeys([*existing["authors"], *candidate["authors"]])
            )
            for field in ("year", "url", "doi", "arxiv_id"):
                if not existing.get(field) and candidate.get(field):
                    existing[field] = candidate[field]
            if candidate["evidence_level"] == "外部摘要候选（未核全文）":
                existing["evidence_level"] = candidate["evidence_level"]
    return list(merged.values()), {
        provider: (counts[0], counts[1]) for provider, counts in provider_counts.items()
    }


def discover_online(
    query: str,
    limit: int,
    timeout: float,
    repo_root: Path,
    connection: Optional[sqlite3.Connection] = None,
    offline: bool = False,
) -> Dict[str, object]:
    if limit < 1 or limit > 100:
        raise ValueError("在线结果数必须在 1 到 100 之间")
    if timeout <= 0:
        raise ValueError("在线超时必须为正数")
    providers = {
        "openalex": search_openalex,
        "semantic_scholar": search_semantic_scholar,
        "crossref": search_crossref,
    }
    responses_by_provider: Dict[str, ProviderResponse] = {}
    if offline:
        for provider in PROVIDER_ORDER:
            status = _base_status("skipped_offline", False, False, time.perf_counter())
            status["degradation_reason"] = "命令启用了 --offline"
            responses_by_provider[provider] = ProviderResponse(provider, status, [])
    else:
        with ThreadPoolExecutor(max_workers=len(providers)) as executor:
            futures = {
                executor.submit(function, query, limit, timeout): provider
                for provider, function in providers.items()
            }
            for future in as_completed(futures):
                provider = futures[future]
                try:
                    responses_by_provider[provider] = future.result()
                except Exception as error:
                    failure = RequestFailure(error)
                    responses_by_provider[provider] = _failure(
                        provider, failure, False, time.perf_counter()
                    )
    responses = [responses_by_provider[provider] for provider in PROVIDER_ORDER]
    raw_candidate_count = sum(len(response.candidates) for response in responses)
    candidates, deduplication = _merge_candidates(responses)
    inventory = _local_inventory(connection, repo_root)
    for candidate in candidates:
        _annotate_local(candidate, inventory)
    for response in responses:
        new_count, duplicate_count = deduplication[response.provider]
        response.status["deduplicated_new_count"] = new_count
        response.status["deduplicated_duplicate_count"] = duplicate_count
    return {
        "provider_status": {response.provider: response.status for response in responses},
        "results": candidates,
        "raw_candidate_count": raw_candidate_count,
        "candidate_count": len(candidates),
        "deduplicated_count": raw_candidate_count - len(candidates),
        "cache": {
            "kind": "none",
            "persistent": False,
            "message": "本轮未实现查询缓存；每次调用都会重新请求可用来源。",
        },
        "evidence_warning": "在线结果仅为题录或摘要候选，未核全文，不得直接写入论文结论。",
    }
