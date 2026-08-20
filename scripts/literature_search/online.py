from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Type

from .documents import normalize_lexical


USER_AGENT = "note-literature-search/0.1 (local academic metadata discovery)"
PAPER_PROVIDER_ORDER = (
    "openalex",
    "semantic_scholar",
    "crossref",
    "huggingface_papers",
    "google_scholar",
)
PROVIDER_ORDER = (*PAPER_PROVIDER_ORDER, "github", "huggingface_hub")
RETRYABLE_HTTP_STATUS = {403, 429, 503}
CROSSREF_SINGLEFLIGHT = threading.Lock()


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    status: Dict[str, object]
    candidates: List[Dict[str, object]]


@dataclass(frozen=True)
class RequestReceipt:
    payload: Any
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
    expected_type: Type[object] = dict,
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
                if not isinstance(payload, expected_type):
                    raise ValueError(f"JSON 响应根节点不是 {expected_type.__name__}")
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
            "rate_limited": http_status in {403, 429},
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


def _auth_headers(token: Optional[str], provider: str) -> Dict[str, str]:
    if provider == "github":
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    return {"Authorization": f"Bearer {token}"} if token else {}


def search_github(query: str, limit: int, timeout: float) -> ProviderResponse:
    provider = "github"
    token = os.environ.get("GITHUB_TOKEN")
    started = time.perf_counter()
    try:
        receipt = _request_json(
            "https://api.github.com/search/repositories",
            {"q": query, "per_page": limit, "sort": "stars", "order": "desc"},
            _auth_headers(token, provider),
            timeout,
        )
        candidates = []
        for item in receipt.payload.get("items", []):
            license_info = item.get("license") or {}
            candidates.append(
                {
                    "provider": provider,
                    "repo_url": item.get("html_url"),
                    "repo_id": item.get("full_name"),
                    "owner": (item.get("owner") or {}).get("login"),
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "homepage": item.get("homepage"),
                    "license": license_info.get("spdx_id") or license_info.get("name"),
                    "stars": item.get("stargazers_count"),
                    "archived": bool(item.get("archived")),
                    "updated_at": item.get("updated_at"),
                    "default_branch": item.get("default_branch"),
                    "match_basis": "GitHub repository search query",
                    "verification_status": "unverified_code_candidate",
                }
            )
        status = _base_status("ok", True, bool(token), started)
        status.update(
            {
                "result_count": len(candidates),
                "retry_count": receipt.retry_count,
                "backoff_seconds": receipt.backoff_seconds,
                "rate_limit": receipt.headers.get("x-ratelimit-limit"),
                "rate_limit_remaining": receipt.headers.get("x-ratelimit-remaining"),
                "rate_limit_reset": receipt.headers.get("x-ratelimit-reset"),
                "rate_limit_resource": receipt.headers.get("x-ratelimit-resource"),
            }
        )
        return ProviderResponse(provider, status, candidates)
    except RequestFailure as failure:
        return _failure(provider, failure, bool(token), started)


def _hf_headers(token: Optional[str]) -> Dict[str, str]:
    return _auth_headers(token, "huggingface")


def search_huggingface_papers(query: str, limit: int, timeout: float) -> ProviderResponse:
    provider = "huggingface_papers"
    token = os.environ.get("HF_TOKEN")
    started = time.perf_counter()
    try:
        receipt = _request_json(
            "https://huggingface.co/api/papers/search",
            {"q": query},
            _hf_headers(token),
            timeout,
            list,
        )
        candidates = []
        for item in receipt.payload[:limit]:
            paper_id = str(item.get("id") or "")
            published = str(item.get("publishedAt") or item.get("published_at") or "")
            candidates.append(
                _candidate(
                    provider,
                    item.get("title") or "",
                    item.get("authors") or [],
                    int(published[:4]) if published[:4].isdigit() else None,
                    f"https://huggingface.co/papers/{paper_id}" if paper_id else None,
                    None,
                    paper_id or None,
                    bool(item.get("summary")),
                    paper_id or None,
                )
            )
        status = _base_status("ok", True, bool(token), started)
        status.update({"result_count": len(candidates), "retry_count": receipt.retry_count,
                       "backoff_seconds": receipt.backoff_seconds})
        return ProviderResponse(provider, status, candidates)
    except RequestFailure as failure:
        return _failure(provider, failure, bool(token), started)


def _scholar_status(
    state: str,
    ok: bool,
    authenticated: bool,
    started: float,
    mode: str,
) -> Dict[str, object]:
    status = _base_status(state, ok, authenticated, started)
    status.update(
        {
            "command_mode": mode,
            "machine_readable": True,
            "verification_status": "unverified_external_candidate",
        }
    )
    return status


def _scholar_failure_state(output: str) -> Tuple[str, str, bool]:
    normalized = output.casefold()
    if any(marker in normalized for marker in ("captcha", "not a robot", "unusual traffic")):
        return "failed_captcha", "Google Scholar 要求验证码", False
    if any(
        marker in normalized
        for marker in ("rate limit", "rate-limit", "too many requests", "429")
    ):
        return "failed_rate_limited", "Google Scholar 触发限流", True
    if any(
        marker in normalized
        for marker in ("auth", "cookie", "login", "unauthorized", "forbidden", "401")
    ):
        return "failed_missing_auth", "Google Scholar 认证不可用", False
    if any(marker in normalized for marker in ("unknown command", "unsupported", "not supported")):
        return "failed_unsupported_mode", "scholar 不支持请求的检索模式", False
    return "failed", "scholar 命令执行失败", False


def _scholar_items(payload: object) -> List[Mapping[str, Any]]:
    if isinstance(payload, list):
        values = payload
    elif isinstance(payload, Mapping):
        if "results" in payload:
            values = payload["results"]
        elif "data" in payload:
            values = payload["data"]
        else:
            raise ValueError("Scholar JSON 缺少 results/data")
    else:
        raise ValueError("Scholar JSON 根节点必须是数组或对象")
    if not isinstance(values, list):
        raise ValueError("Scholar JSON 结果字段不是数组")
    return [item for item in values if isinstance(item, Mapping)]


def _scholar_authors(value: object) -> List[str]:
    if isinstance(value, str):
        return [
            name.strip()
            for name in re.split(r"\s*(?:,|;|\band\b)\s*", value)
            if name.strip()
        ]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(name).strip() for name in value if str(name).strip()]
    return []


def _scholar_year(value: object) -> Optional[int]:
    match = re.search(r"(?:19|20)\d{2}", str(value or ""))
    return int(match.group(0)) if match else None


def _identifier_from_scholar_urls(
    url: Optional[str], pdf_url: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    values = [value for value in (url, pdf_url) if value]
    doi = next(
        (
            _clean_doi(match.group(0).rstrip(".,;)]}"))
            for value in values
            if (match := re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", value, re.I))
        ),
        None,
    )
    arxiv_id = next(
        (
            _clean_arxiv(match.group(1))
            for value in values
            if (match := re.search(r"arxiv\.org/(?:abs|pdf)/([^?#]+)", value, re.I))
        ),
        None,
    )
    return doi, arxiv_id


def search_google_scholar(query: str, limit: int, timeout: float) -> ProviderResponse:
    provider = "google_scholar"
    started = time.perf_counter()
    executable = shutil.which("scholar")
    requested_mode = os.environ.get("GOOGLE_SCHOLAR_MODE", "lookup").strip().casefold()
    mode = requested_mode if requested_mode in {"lookup", "search"} else "lookup"
    cookies_available = (Path.home() / ".google-scholar" / "cookies").is_file()
    if executable is None:
        status = _scholar_status(
            "unavailable_missing_command", False, cookies_available, started, mode
        )
        status["degradation_reason"] = "scholar 命令不在 PATH 中"
        return ProviderResponse(provider, status, [])
    if requested_mode not in {"lookup", "search"}:
        status = _scholar_status("failed_invalid_mode", False, cookies_available, started, mode)
        status["degradation_reason"] = "GOOGLE_SCHOLAR_MODE 只能是 lookup 或 search"
        return ProviderResponse(provider, status, [])
    if mode == "search" and not cookies_available:
        status = _scholar_status("skipped_missing_auth", False, False, started, mode)
        status["degradation_reason"] = "Scholar Labs search 需要既有认证状态"
        return ProviderResponse(provider, status, [])

    try:
        process = subprocess.run(
            [executable, mode, query, "--json"],
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        status = _scholar_status("failed_timeout", False, cookies_available, started, mode)
        status["degradation_reason"] = "scholar 命令执行超时"
        return ProviderResponse(provider, status, [])
    except OSError:
        status = _scholar_status(
            "unavailable_command_error", False, cookies_available, started, mode
        )
        status["degradation_reason"] = "scholar 命令无法启动"
        return ProviderResponse(provider, status, [])

    if process.returncode != 0:
        state, reason, rate_limited = _scholar_failure_state(
            f"{process.stdout}\n{process.stderr}"
        )
        status = _scholar_status(state, False, cookies_available, started, mode)
        status.update(
            {
                "exit_code": process.returncode,
                "rate_limited": rate_limited,
                "degradation_reason": reason,
            }
        )
        return ProviderResponse(provider, status, [])

    try:
        payload = json.loads(process.stdout)
        items = _scholar_items(payload)
    except (json.JSONDecodeError, ValueError):
        status = _scholar_status("failed_invalid_json", False, cookies_available, started, mode)
        status["degradation_reason"] = "scholar 返回的 JSON 无法解析"
        return ProviderResponse(provider, status, [])

    candidates = []
    for item in items[:limit]:
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        url = str(item.get("url") or "").strip() or None
        pdf_url = str(item.get("pdfUrl") or item.get("pdf_url") or "").strip() or None
        doi, arxiv_id = _identifier_from_scholar_urls(url, pdf_url)
        cluster_id = (
            str(item.get("clusterId") or item.get("cluster_id") or "").strip()
            or None
        )
        candidate = _candidate(
            provider,
            title,
            _scholar_authors(item.get("authors")),
            _scholar_year(item.get("year")),
            url,
            doi,
            arxiv_id,
            bool(item.get("snippet")),
            cluster_id,
        )
        candidate["verification_status"] = "unverified_external_candidate"
        candidate["provider_records"][0].update(
            {
                "cluster_id": cluster_id,
                "citations": item.get("citations"),
                "journal": item.get("journal"),
                "position": item.get("position"),
                "pdf_url": pdf_url,
                "metadata_role": "discovery_only",
                "verification_status": "unverified_external_candidate",
            }
        )
        candidates.append(candidate)

    status = _scholar_status("ok", True, cookies_available, started, mode)
    status["result_count"] = len(candidates)
    return ProviderResponse(provider, status, candidates)


def _hf_license(tags: Sequence[str], card_data: object) -> Optional[str]:
    for tag in tags:
        if tag.startswith("license:"):
            return tag.split(":", 1)[1]
    if isinstance(card_data, Mapping) and card_data.get("license"):
        return str(card_data["license"])
    return None


def _hf_arxiv(tags: Sequence[str]) -> Optional[str]:
    for tag in tags:
        if tag.lower().startswith("arxiv:"):
            return _clean_arxiv(tag.split(":", 1)[1])
    return None


def search_huggingface_hub(query: str, limit: int, timeout: float) -> ProviderResponse:
    provider = "huggingface_hub"
    token = os.environ.get("HF_TOKEN")
    started = time.perf_counter()
    candidates: List[Dict[str, object]] = []
    receipts: List[RequestReceipt] = []
    try:
        for repo_type, endpoint in (
            ("model", "https://huggingface.co/api/models"),
            ("dataset", "https://huggingface.co/api/datasets"),
            ("space", "https://huggingface.co/api/spaces"),
        ):
            receipt = _request_json(
                endpoint,
                {"search": query, "sort": "downloads", "direction": -1, "limit": limit,
                 "full": "true"},
                _hf_headers(token),
                timeout,
                list,
            )
            receipts.append(receipt)
            for item in receipt.payload[:limit]:
                repo_id = str(item.get("id") or "")
                tags = [str(tag) for tag in (item.get("tags") or [])]
                arxiv_id = _hf_arxiv(tags)
                candidates.append(
                    {
                        "provider": provider,
                        "repo_id": repo_id,
                        "repo_type": repo_type,
                        "url": f"https://huggingface.co/{'datasets/' if repo_type == 'dataset' else 'spaces/' if repo_type == 'space' else ''}{repo_id}",
                        "pipeline_tag": item.get("pipeline_tag"),
                        "downloads": item.get("downloads"),
                        "likes": item.get("likes"),
                        "updated_at": item.get("lastModified") or item.get("last_modified"),
                        "gated": item.get("gated", False),
                        "license": _hf_license(tags, item.get("cardData") or item.get("card_data")),
                        "arxiv_id": arxiv_id,
                        "match_basis": f"Hugging Face {repo_type} search query",
                        "verification_status": (
                            "paper_linked_candidate" if arxiv_id else "unverified_hub_candidate"
                        ),
                    }
                )
        status = _base_status("ok", True, bool(token), started)
        status.update(
            {
                "result_count": len(candidates),
                "request_count": len(receipts),
                "retry_count": sum(item.retry_count for item in receipts),
                "backoff_seconds": sum(item.backoff_seconds for item in receipts),
                "rate_limit": receipts[-1].headers.get("ratelimit") if receipts else None,
                "rate_limit_policy": receipts[-1].headers.get("ratelimit-policy") if receipts else None,
            }
        )
        return ProviderResponse(provider, status, candidates)
    except RequestFailure as failure:
        return _failure(provider, failure, bool(token), started)


def _local_inventory(
    connection: Optional[sqlite3.Connection], repo_root: Path
) -> List[Dict[str, object]]:
    if connection is None:
        return []
    inventory = []
    note_columns = {
        str(row["name"]) for row in connection.execute("PRAGMA table_info(notes)")
    }
    collection_filter = " WHERE collection='papers'" if "collection" in note_columns else ""
    for row in connection.execute(
        "SELECT path,title,source_pdf,doi,arxiv_id FROM notes"
        + collection_filter
        + " ORDER BY id"
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


def _deduplicate_channel(
    candidates: Sequence[Dict[str, object]], url_field: str
) -> Tuple[List[Dict[str, object]], int]:
    unique: Dict[str, Dict[str, object]] = {}
    for candidate in candidates:
        url = str(candidate.get(url_field) or "").rstrip("/").casefold()
        key = url or f"{candidate.get('provider')}:{candidate.get('repo_id')}"
        unique.setdefault(key, candidate)
    return list(unique.values()), len(candidates) - len(unique)


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
        "huggingface_papers": search_huggingface_papers,
        "google_scholar": search_google_scholar,
        "github": search_github,
        "huggingface_hub": search_huggingface_hub,
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
    paper_responses = [responses_by_provider[provider] for provider in PAPER_PROVIDER_ORDER]
    raw_candidate_count = sum(len(response.candidates) for response in paper_responses)
    candidates, deduplication = _merge_candidates(paper_responses)
    code_candidates, code_duplicates = _deduplicate_channel(
        responses_by_provider["github"].candidates, "repo_url"
    )
    hub_candidates, hub_duplicates = _deduplicate_channel(
        responses_by_provider["huggingface_hub"].candidates, "url"
    )
    inventory = _local_inventory(connection, repo_root)
    for candidate in candidates:
        _annotate_local(candidate, inventory)
    for response in paper_responses:
        new_count, duplicate_count = deduplication[response.provider]
        response.status["deduplicated_new_count"] = new_count
        response.status["deduplicated_duplicate_count"] = duplicate_count
    responses_by_provider["github"].status["deduplicated_duplicate_count"] = code_duplicates
    responses_by_provider["huggingface_hub"].status["deduplicated_duplicate_count"] = hub_duplicates
    return {
        "provider_status": {response.provider: response.status for response in responses},
        "results": candidates,
        "paper_candidates": candidates,
        "code_candidates": code_candidates,
        "hub_candidates": hub_candidates,
        "raw_candidate_count": raw_candidate_count,
        "candidate_count": len(candidates),
        "deduplicated_count": raw_candidate_count - len(candidates),
        "code_candidate_count": len(code_candidates),
        "hub_candidate_count": len(hub_candidates),
        "cache": {
            "kind": "none",
            "persistent": False,
            "message": "本轮未实现查询缓存；每次调用都会重新请求可用来源。",
        },
        "evidence_warning": "在线结果仅为题录或摘要候选，未核全文，不得直接写入论文结论。",
    }
