#!/usr/bin/env python3
"""以非阻断提示提醒主代理核验并更新当前路线恢复卡。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, TextIO


SCRIPT_ROOT = Path(__file__).resolve().parents[2]
ROUTES_PATH = Path(__file__).with_name("recovery_card_routes.json")
TERMINAL_VALUES = frozenset({"completed", "failed", "rejected", "cancelled", "blocked"})
SENSITIVE_MARKERS = ("token", "secret", "password", "authorization", "cookie", "apikey", "api_key")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def append_event(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(value), ensure_ascii=False, sort_keys=True) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON 顶层必须是对象")
    return value


def route_for_payload(payload: Mapping[str, Any], routes: Mapping[str, Any], root: Path) -> str | None:
    cwd = payload.get("cwd")
    if not isinstance(cwd, str):
        return None
    try:
        Path(cwd).resolve().relative_to(root)
    except (OSError, ValueError):
        return None
    text = "\n".join(str(payload.get(key, "")) for key in ("prompt", "last_assistant_message", "goal", "objective", "thread_goal"))
    matches = [name for name, spec in routes.items() if any(marker in text for marker in spec.get("sentinels", []))]
    return matches[0] if len(matches) == 1 else None


def relative_entry(path: Path, root: Path) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "mtime_ns": path.stat().st_mtime_ns, "sha256": sha256_file(path)}


def newest_paths(root: Path, relatives: Iterable[str], wanted_names: set[str], limit: int) -> list[Path]:
    values: list[Path] = []
    for relative in relatives:
        base = root / relative
        if not base.is_dir():
            continue
        for current, directories, names in os.walk(base):
            directories[:] = [item for item in directories if item not in {".git", "__pycache__", "cache", "archive"}]
            for name in names:
                if name in wanted_names:
                    values.append(Path(current) / name)
    return sorted(values, key=lambda path: path.stat().st_mtime_ns, reverse=True)[:limit]


def terminal_status(path: Path) -> str | None:
    try:
        value = load_json(path)
    except Exception:
        return None
    status = value.get("status")
    return str(status).lower() if isinstance(status, str) and str(status).lower() in TERMINAL_VALUES else None


def digest_goal(payload: Mapping[str, Any]) -> str | None:
    values = {key: payload.get(key) for key in ("goal", "objective", "thread_goal") if isinstance(payload.get(key), str)}
    if not values:
        return None
    return sha256_bytes(json.dumps(values, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def route_snapshot(root: Path, name: str, spec: Mapping[str, Any], config: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any] | None:
    card = root / str(spec["recovery_card"])
    if not card.is_file():
        return None
    method_paths: list[Path] = []
    for relative in spec.get("method_roots", []):
        base = root / relative
        if base.is_dir():
            method_paths.extend(sorted(base.glob("*.md"), key=lambda path: path.stat().st_mtime_ns, reverse=True))
    method_paths = method_paths[:int(config["max_method_candidates"])]
    status_paths = newest_paths(root, spec.get("run_roots", []), set(spec.get("status_names", [])), int(config["max_status_candidates"]))
    terminal = [{**relative_entry(path, root), "terminal_status": terminal_status(path)} for path in status_paths]
    terminal = [item for item in terminal if item["terminal_status"] is not None]
    return {
        "route": name,
        "recovery_card": relative_entry(card, root),
        "methods": [relative_entry(path, root) for path in method_paths],
        "terminal_runs": terminal,
        "goal_digest": digest_goal(payload),
        "subagent_digest": sha256_bytes(str(payload.get("last_assistant_message", "")).encode("utf-8")) if payload.get("hook_event_name") == "SubagentStop" and isinstance(payload.get("last_assistant_message"), str) else None,
    }


def changes(previous: Mapping[str, Any] | None, current: Mapping[str, Any]) -> list[str]:
    found: list[str] = []
    newest_fact = max([entry["mtime_ns"] for entry in current["methods"] + current["terminal_runs"]] or [0])
    if previous is None:
        if newest_fact > int(current["recovery_card"]["mtime_ns"]):
            found.append("恢复卡登记哈希或时间滞后")
        return found
    if previous.get("goal_digest") != current.get("goal_digest") and current.get("goal_digest"):
        found.append("目标文本变化")
    if previous.get("subagent_digest") != current.get("subagent_digest") and current.get("subagent_digest"):
        found.append("子代理最终交付")
    if previous.get("terminal_runs") != current.get("terminal_runs"):
        found.append("受管运行出现新终态")
    if previous.get("methods") != current.get("methods"):
        found.append("关键方法文档更新")
    old_card = previous.get("recovery_card", {})
    new_card = current["recovery_card"]
    if old_card.get("sha256") != new_card.get("sha256"):
        found.append("恢复卡已被人工更新")
    if newest_fact > int(new_card["mtime_ns"]):
        found.append("恢复卡登记哈希或时间滞后")
    return sorted(set(found))


def safe_error(error: Exception) -> dict[str, str]:
    return {"error_type": type(error).__name__, "message": "hook 观察失败，已静默放行"}


def build_context(route: str, reason: list[str]) -> str:
    return (
        f"[恢复卡状态提醒:{route}] 检测到{'、'.join(reason)}。先核原始 status/result、方法文档与路径；"
        "仅将已核的新确定事实、否决、当前动作和代理状态委派文档代理写回当前路线恢复卡。"
        "文档不得阻塞实验；进行中或未核事实不得写成完成。"
    )


def handle_payload(payload: Mapping[str, Any], root: Path, routes_path: Path) -> dict[str, Any] | None:
    config = load_json(routes_path)
    routes = config.get("routes")
    if not isinstance(routes, Mapping):
        return None
    route = route_for_payload(payload, routes, root)
    if route is None:
        return None
    snapshot = route_snapshot(root, route, routes[route], config, payload)
    if snapshot is None:
        return None
    state_dir = root / str(config["state_directory"])
    state_path = state_dir / "state.json"
    previous = None
    try:
        previous = load_json(state_path).get("routes", {}).get(route)
    except Exception:
        previous = None
    found = changes(previous if isinstance(previous, Mapping) else None, snapshot)
    state: dict[str, Any] = {"schema_version": "recovery-card-state-v1", "routes": {}}
    try:
        state = load_json(state_path)
    except Exception:
        pass
    state.setdefault("routes", {})[route] = snapshot
    atomic_json(state_path, state)
    event = str(payload.get("hook_event_name", ""))
    if found:
        append_event(state_dir / "events.jsonl", {"route": route, "event": event, "reasons": found, "snapshot_sha256": sha256_bytes(json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode("utf-8"))})
    if event not in {"UserPromptSubmit", "PreCompact"} or not found:
        return None
    cooldown = int(config["cooldown_seconds"])
    now = time.time()
    last = state.get("last_injection", {})
    snapshot_hash = sha256_bytes(json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    signature = sha256_bytes((route + "|" + snapshot_hash).encode("utf-8"))
    if last.get("signature") == signature and now - float(last.get("at", 0.0)) < cooldown:
        return None
    state["last_injection"] = {"signature": signature, "at": now}
    atomic_json(state_path, state)
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": build_context(route, found)}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=SCRIPT_ROOT)
    parser.add_argument("--routes", type=Path, default=ROUTES_PATH)
    arguments = parser.parse_args()
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, Mapping):
            return 0
        output = handle_payload(payload, arguments.project_root.resolve(), arguments.routes.resolve())
        if output is not None:
            json.dump(output, sys.stdout, ensure_ascii=False)
            sys.stdout.write("\n")
    except Exception as error:
        try:
            root = arguments.project_root.resolve()
            append_event(root / ".Codex/docs/2026-09-08-恢复卡自动更新Hook/runtime-state/errors.jsonl", safe_error(error))
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
