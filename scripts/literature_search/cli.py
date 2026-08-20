from __future__ import annotations

import argparse
import fcntl
import json
import sqlite3
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, Optional, Sequence

from .build import build_index
from .config import REPO_ROOT, SearchConfig, load_config
from .evaluate import evaluate_queries
from .lint_notes import lint_paths
from .online import discover_online
from .search import SCOPE_COLLECTIONS, search_federated
from .status import index_status
from .storage import connect, get_metadata


DEFAULT_MODEL_CACHE = Path(".cache/literature-search/model-cache")


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _print_results(results: Sequence[Dict[str, object]]) -> None:
    for item in results:
        print(f"{item['rank']}. {item['title']}")
        if item.get("paper_id"):
            print(f"   论文身份：{item['paper_id']}")
        else:
            print(f"   文档身份：{item['document_id']}")
        print(
            "   分区：scope={scope} collection={collection} 类型={doc_type}".format(
                scope=item["scope"],
                collection=item["collection"],
                doc_type=item["doc_type"],
            )
        )
        print(
            "   证据元数据：权威={authority} 状态={status} 等级={level}".format(
                authority=item["authority"],
                status=item["status"],
                level=item["evidence_level"],
            )
        )
        print(f"   路径：{item['note_path']}")
        if int(item.get("note_view_count") or 0) > 1:
            paths = "、".join(str(view["note_path"]) for view in item["note_views"])
            print(f"   笔记视图：{paths}")
        if item.get("paper_id"):
            print(f"   原件：{item.get('source_pdf') or '未记录'}")
            print(f"   页码：{item.get('page_hint') or '当前分块未提取'}")
        print(
            "   排名：词法={lexical} 向量={vector} 融合分={fusion}".format(
                lexical=item.get("lexical_rank") or "-",
                vector=item.get("vector_rank") or "-",
                fusion=(
                    f"{item['fusion_score']:.8f}"
                    if item.get("fusion_score") is not None
                    else "-"
                ),
            )
        )
        print(
            "   证据：通道={channel} 块={chunk} 标题={heading}".format(
                channel=item["evidence_channel"],
                chunk=item["evidence_block"]["chunk_id"],
                heading=item["evidence_block"].get("heading") or "-",
            )
        )
        print(f"   片段：{item['snippet']}")


def _print_online(result: Dict[str, object]) -> None:
    print("在线来源状态：")
    for provider, status in result["provider_status"].items():
        print(f"- {provider}: {json.dumps(status, ensure_ascii=False)}")
    print("外部候选：")
    for position, item in enumerate(result["results"], start=1):
        print(f"{position}. [{'/'.join(item['providers'])}] {item['title']}")
        print(f"   证据：{item['evidence_level']}")
        print(f"   URL：{item.get('url') or '未记录'}")
        print(f"   DOI/arXiv：{item.get('doi') or '-'} / {item.get('arxiv_id') or '-'}")
        print(
            f"   本地：wiki={item['has_wiki']} raw={item['has_raw']} "
            f"Zotero={item['zotero_status']}"
        )
    print("GitHub 代码候选：")
    for position, item in enumerate(result.get("code_candidates", []), start=1):
        print(f"{position}. {item['repo_id']} {item['repo_url']}")
        print(f"   核验：{item['verification_status']} 许可证：{item.get('license') or '-'}")
    print("Hugging Face Hub 候选：")
    for position, item in enumerate(result.get("hub_candidates", []), start=1):
        print(f"{position}. [{item['repo_type']}] {item['repo_id']} {item['url']}")
        print(f"   核验：{item['verification_status']} arXiv：{item.get('arxiv_id') or '-'}")
    print(result["evidence_warning"])


def _index_config(connection: sqlite3.Connection, fallback: SearchConfig) -> SearchConfig:
    metadata = get_metadata(connection)
    saved = metadata.get("config")
    return SearchConfig.from_dict(saved) if isinstance(saved, dict) else fallback


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="仓库根目录")
    parser.add_argument("--config", type=Path, default=None, help="配置 JSON 路径")
    parser.add_argument("--index", default=None, help="覆盖索引路径")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="全项目文档关键词与向量混合检索")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="构建或原子重建索引")
    _add_common(build_parser)
    build_parser.add_argument("--lexical-only", action="store_true", help="只构建词法索引")
    build_parser.add_argument("--model-cache", type=Path, default=None, help="模型缓存目录")
    build_parser.add_argument("--offline", action="store_true", help="禁止模型联网下载")
    build_parser.add_argument(
        "--device", choices=["auto", "cpu", "mps"], default="auto", help="向量计算设备"
    )
    build_parser.add_argument("--json", action="store_true", help="输出 JSON")

    query_parser = subparsers.add_parser("query", help="查询本地索引")
    _add_common(query_parser)
    query_parser.add_argument("text", help="查询文本")
    query_parser.add_argument(
        "--mode", choices=["lexical", "vector", "hybrid"], default="hybrid"
    )
    query_parser.add_argument(
        "--scope",
        choices=["paper", "project", "experiment", "thesis", "all", "local", "online"],
        default="paper",
    )
    query_parser.add_argument(
        "--collection",
        action="append",
        choices=list(SCOPE_COLLECTIONS["all"]),
        help="在所选本地作用域内进一步过滤 collection，可重复指定",
    )
    query_parser.add_argument(
        "--include-history",
        action="store_true",
        help="显式纳入 superseded、rejected 和 archive 状态",
    )
    query_parser.add_argument("--top-k", type=int, default=None)
    query_parser.add_argument("--online-limit", type=int, default=None)
    query_parser.add_argument("--online-timeout", type=float, default=None)
    query_parser.add_argument("--model-cache", type=Path, default=None)
    query_parser.add_argument(
        "--offline", action="store_true", help="禁止模型下载与在线来源网络请求"
    )
    query_parser.add_argument(
        "--device", choices=["auto", "cpu", "mps"], default="auto"
    )
    query_parser.add_argument(
        "--no-auto-build",
        action="store_false",
        dest="auto_build",
        help="索引不存在或陈旧时拒绝查询，不自动构建",
    )
    query_parser.set_defaults(auto_build=True)
    query_parser.add_argument(
        "--auto-build-device",
        choices=["auto", "cpu", "mps"],
        default="auto",
        help="自动构建的嵌入设备，auto 在 Apple 芯片上优先 MPS 后回退 CPU",
    )
    query_parser.add_argument("--json", action="store_true")

    status_parser = subparsers.add_parser("status", help="显示索引状态")
    _add_common(status_parser)
    status_parser.add_argument("--json", action="store_true")

    evaluate_parser = subparsers.add_parser("evaluate", help="运行冻结真实查询对照")
    _add_common(evaluate_parser)
    evaluate_parser.add_argument(
        "--queries",
        type=Path,
        default=Path(__file__).resolve().parent / "evaluation_queries.json",
    )
    evaluate_parser.add_argument("--model-cache", type=Path, default=None)
    evaluate_parser.add_argument("--offline", action="store_true")
    evaluate_parser.add_argument(
        "--device", choices=["auto", "cpu", "mps"], default="auto"
    )
    lint_parser = subparsers.add_parser("lint", help="检查论文笔记检索合同")
    lint_parser.add_argument("paths", nargs="+", type=Path, help="待检查 Markdown 路径")
    lint_parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="仓库根目录")
    lint_parser.add_argument("--strict", action="store_true", help="对旧模板也执行严格检查")
    lint_parser.add_argument("--json", action="store_true", help="输出 JSON")
    return parser


def _paths(args: argparse.Namespace) -> tuple[Path, SearchConfig, Path]:
    repo_root = args.repo_root.expanduser().resolve()
    config = load_config(args.config)
    index_path = config.resolve_index_path(repo_root, args.index)
    return repo_root, config, index_path


def _model_cache(args: argparse.Namespace, repo_root: Path) -> Path:
    override = getattr(args, "model_cache", None)
    value = override.expanduser() if override else repo_root / DEFAULT_MODEL_CACHE
    return value if value.is_absolute() else repo_root / value


@contextmanager
def _index_build_lock(index_path: Path) -> Iterator[None]:
    lock_path = index_path.with_suffix(index_path.suffix + ".build.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"索引构建中，等待锁：{lock_path}", file=sys.stderr)
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _build_if_needed(
    repo_root: Path,
    index_path: Path,
    config: SearchConfig,
    args: argparse.Namespace,
) -> Optional[Dict[str, object]]:
    with _index_build_lock(index_path):
        status = index_status(repo_root, index_path, config)
        if status["exists"] and not status["stale"]:
            return None
        reasons = "、".join(status["stale_reasons"])
        rebuild_kind = (
            "全量重嵌入"
            if "embedding_contract_changed" in status["stale_reasons"]
            else "增量构建"
        )
        print(
            f"索引需要{rebuild_kind}（{reasons}）；预计耗时：未知（无可比历史记录）",
            file=sys.stderr,
        )
        started = time.monotonic()
        result = build_index(
            repo_root,
            index_path,
            config,
            cache_folder=_model_cache(args, repo_root),
            local_files_only=args.offline,
            device=args.auto_build_device,
        )
        elapsed = round(time.monotonic() - started, 3)
        final_status = index_status(repo_root, index_path, config)
        if not final_status["exists"] or final_status["stale"]:
            final_reasons = "、".join(final_status["stale_reasons"])
            raise RuntimeError(f"自动构建后索引仍不可用（{final_reasons}），拒绝查询")
        result["auto_build_kind"] = rebuild_kind
        result["auto_build_elapsed_seconds"] = elapsed
        print(f"索引自动构建完成，实际耗时：{elapsed} 秒", file=sys.stderr)
        return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        if args.command == "lint":
            repo_root = args.repo_root.expanduser().resolve()
            result = lint_paths(repo_root, args.paths, strict=args.strict)
            _print_json(result)
            return 0 if result["valid"] else 1
        repo_root, config, index_path = _paths(args)
        if args.command == "build":
            with _index_build_lock(index_path):
                result = build_index(
                    repo_root,
                    index_path,
                    config,
                    lexical_only=args.lexical_only,
                    cache_folder=_model_cache(args, repo_root),
                    local_files_only=args.offline,
                    device=args.device,
                )
            if args.json:
                _print_json(result)
            else:
                print(
                    f"索引完成：{result['note_count']} 篇笔记，{result['chunk_count']} 个分块，"
                    f"{result['vector_count']} 个向量，耗时 {result['build_seconds']} 秒"
                )
                print(f"索引路径：{result['index_path']}")
            return 0
        if args.command == "status":
            result = index_status(repo_root, index_path, config)
            _print_json(result)
            return 0 if result["exists"] else 1
        if args.command == "query" and args.scope != "online":
            status = index_status(repo_root, index_path, config)
            auto_build_result = None
            if not status["exists"] or status["stale"]:
                if args.auto_build:
                    auto_build_result = _build_if_needed(
                        repo_root, index_path, config, args
                    )
                else:
                    reasons = "、".join(status["stale_reasons"])
                    raise RuntimeError(
                        f"索引不可用（{reasons}）；已使用 --no-auto-build，拒绝查询"
                    )
        connection = connect(index_path, readonly=True) if index_path.exists() else None
        try:
            actual_config = _index_config(connection, config) if connection else config
            if args.command == "evaluate":
                if connection is None:
                    raise RuntimeError(f"索引不存在：{index_path}；请先运行 build")
                result = evaluate_queries(
                    connection,
                    args.queries,
                    actual_config,
                    cache_folder=_model_cache(args, repo_root),
                    local_files_only=args.offline,
                    device=args.device,
                    repo_root=repo_root,
                )
                _print_json(result)
                return 0
            if args.command == "query" and args.scope == "online":
                online = discover_online(
                    args.text,
                    args.online_limit or actual_config.online_limit,
                    args.online_timeout or actual_config.online_timeout_seconds,
                    repo_root,
                    connection=connection,
                    offline=args.offline,
                )
                if args.json:
                    _print_json({"scope": "online", "online": online})
                else:
                    _print_online(online)
                return 0
            top_k = args.top_k or actual_config.default_top_k
            if top_k <= 0:
                raise ValueError("top-k 必须为正数")
            if connection is None:
                raise RuntimeError(f"索引不存在：{index_path}；请先运行 build")
            requested_scope = "paper" if args.scope == "local" else args.scope
            results_by_scope: Dict[str, Sequence[Dict[str, object]]] = {}
            local_scopes = (
                ("paper", "project", "experiment", "thesis")
                if requested_scope == "all"
                else (requested_scope,)
            )
            for local_scope in local_scopes:
                selected_collections = None
                if args.collection:
                    selected_collections = [
                        value
                        for value in args.collection
                        if value in SCOPE_COLLECTIONS[local_scope]
                    ]
                    if not selected_collections:
                        results_by_scope[local_scope] = []
                        continue
                results_by_scope[local_scope] = search_federated(
                    connection,
                    args.text,
                    args.mode,
                    top_k,
                    actual_config,
                    cache_folder=_model_cache(args, repo_root),
                    local_files_only=args.offline,
                    device=args.device,
                    scope=local_scope,
                    collections=selected_collections,
                    include_history=args.include_history,
                )
            results = [
                item
                for local_scope in local_scopes
                for item in results_by_scope[local_scope]
            ]
            online = None
            if args.scope == "all":
                online = discover_online(
                    args.text,
                    args.online_limit or actual_config.online_limit,
                    args.online_timeout or actual_config.online_timeout_seconds,
                    repo_root,
                    connection=connection,
                    offline=args.offline,
                )
        finally:
            if connection is not None:
                connection.close()
        if args.json:
            output = {
                "scope": "paper" if args.scope == "local" else args.scope,
                "mode": args.mode,
                "collections": args.collection,
                "include_history": args.include_history,
                "local_results": results,
            }
            if len(results_by_scope) > 1:
                output["local_results_by_scope"] = results_by_scope
            if online is not None:
                output["online"] = online
            if auto_build_result is not None:
                output["auto_build"] = auto_build_result
            _print_json(output)
        else:
            if len(results_by_scope) > 1:
                for local_scope, scoped_results in results_by_scope.items():
                    print(f"本地作用域：{local_scope}")
                    _print_results(scoped_results)
            else:
                _print_results(results)
            if online is not None:
                _print_online(online)
        return 0
    except (RuntimeError, ValueError, OSError, sqlite3.Error, json.JSONDecodeError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2
