#!/usr/bin/env python3
"""在上下文压缩前原子刷新两份强制恢复文档的自动快照区块。"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, TextIO

START_MARKER = "<!-- PRECOMPACT_SNAPSHOT_START -->"
END_MARKER = "<!-- PRECOMPACT_SNAPSHOT_END -->"
CONFIG_PATH = Path(".codex/precompact_snapshot.json")
RECOVERY_DOCUMENTS = (
    Path("output/开题改进交接文档.md"),
    Path("output/第一创新点实验总控.md"),
)
STATUS_HEADING = "## 当前状态"
ALLOWED_CONFIG_KEYS = {"enabled", "active_plan"}
REQUIRED_INPUT_KEYS = {
    "cwd",
    "hook_event_name",
    "session_id",
    "transcript_path",
    "trigger",
}
OPTIONAL_INPUT_KEYS = {
    "model",
    "turn_id",
}


class SnapshotError(RuntimeError):
    """表示可安全报告且不应破坏恢复文档的错误。"""


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _project_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def _parse_payload(stream: TextIO, project_root: Path) -> dict[str, Any]:
    try:
        payload = json.load(stream)
    except (json.JSONDecodeError, OSError) as error:
        raise SnapshotError(f"PreCompact 输入不是合法 JSON：{error}") from error

    if not isinstance(payload, dict):
        raise SnapshotError("PreCompact 输入必须是 JSON 对象")

    missing = sorted(REQUIRED_INPUT_KEYS.difference(payload))
    if missing:
        raise SnapshotError(f"PreCompact 输入缺少字段：{', '.join(missing)}")
    if payload.get("hook_event_name") != "PreCompact":
        raise SnapshotError("Hook 事件不是 PreCompact")
    if payload.get("trigger") not in {"manual", "auto"}:
        raise SnapshotError("PreCompact trigger 只能是 manual 或 auto")

    cwd_value = payload.get("cwd")
    if not isinstance(cwd_value, str):
        raise SnapshotError("PreCompact cwd 必须是字符串")
    cwd = Path(cwd_value).expanduser().resolve()
    if not _is_within(cwd, project_root):
        raise SnapshotError("PreCompact 工作目录不属于当前项目")
    return payload


def _load_config(project_root: Path) -> tuple[bool, Path | None, str | None]:
    config_file = project_root / CONFIG_PATH
    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SnapshotError(f"快照配置不存在：{CONFIG_PATH.as_posix()}") from error
    except (json.JSONDecodeError, OSError) as error:
        raise SnapshotError(f"无法读取快照配置：{error}") from error

    if not isinstance(config, dict):
        raise SnapshotError("快照配置必须是 JSON 对象")
    unknown = sorted(set(config).difference(ALLOWED_CONFIG_KEYS))
    if unknown:
        raise SnapshotError(f"快照配置包含未知字段：{', '.join(unknown)}")

    enabled = config.get("enabled", True)
    if not isinstance(enabled, bool):
        raise SnapshotError("快照配置 enabled 必须是布尔值")

    active_plan_value = config.get("active_plan")
    if active_plan_value is None or active_plan_value == "":
        return enabled, None, None
    if not isinstance(active_plan_value, str):
        return enabled, None, None
    if any(character in active_plan_value for character in "\r\n`"):
        return enabled, None, None

    relative_plan = PurePosixPath(active_plan_value)
    if relative_plan.is_absolute() or ".." in relative_plan.parts:
        return enabled, None, None
    active_plan = (project_root / Path(*relative_plan.parts)).resolve()
    if not _is_within(active_plan, project_root):
        return enabled, None, None
    return enabled, active_plan, relative_plan.as_posix()


def _extract_current_status(plan_text: str) -> str:
    heading_pattern = re.compile(
        r"^##(?:[ \t]+\d+\.)?[ \t]+当前状态[ \t]*$", re.MULTILINE
    )
    matches = list(heading_pattern.finditer(plan_text))
    if len(matches) != 1:
        raise SnapshotError("活动计划必须且只能包含一个“## 当前状态”章节")

    content_start = matches[0].end()
    next_heading = re.search(r"^##[ \t]+\S", plan_text[content_start:], re.MULTILINE)
    content_end = (
        content_start + next_heading.start()
        if next_heading is not None
        else len(plan_text)
    )
    status = plan_text[content_start:content_end].strip()
    if not status:
        raise SnapshotError("活动计划的“## 当前状态”章节为空")
    if START_MARKER in status or END_MARKER in status:
        raise SnapshotError("活动计划状态包含保留的快照边界标记")
    return status


def _build_snapshot(
    *,
    active_plan_relative: str | None,
    status: str | None,
    now: dt.datetime,
) -> str:
    trigger_time = now.astimezone().isoformat(timespec="seconds")
    plan_display = (
        f"`{active_plan_relative}`" if active_plan_relative is not None else "未设置"
    )
    status_display = status if status is not None else "未设置"
    return "\n".join(
        [
            START_MARKER,
            "## PreCompact 自动快照",
            "",
            "> 此区块由项目级 Hook 自动维护；服务器事实需实时核验。",
            "",
            f"- **触发时间**：`{trigger_time}`",
            f"- **当前活动计划**：{plan_display}",
            "",
            "### 当前执行态摘要",
            "",
            status_display,
            END_MARKER,
        ]
    )


def _replace_snapshot_block(document: str, snapshot: str, document_name: str) -> str:
    start_count = document.count(START_MARKER)
    end_count = document.count(END_MARKER)
    if start_count != end_count or start_count > 1:
        raise SnapshotError(f"{document_name} 的快照边界标记不完整或重复")

    if start_count == 1:
        start = document.index(START_MARKER)
        end = document.index(END_MARKER, start) + len(END_MARKER)
        return f"{document[:start]}{snapshot}{document[end:]}"

    first_line_end = document.find("\n")
    if first_line_end < 0:
        return f"{document}\n\n{snapshot}\n"
    insert_at = first_line_end + 1
    return f"{document[:insert_at]}\n{snapshot}\n{document[insert_at:]}"


def _write_temp(target: Path, content: str) -> Path:
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.precompact-", suffix=".tmp", dir=target.parent
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp_path, stat.S_IMODE(target.stat().st_mode))
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return temp_path


def _replace_atomically(target: Path, content: str) -> None:
    temp_path = _write_temp(target, content)
    try:
        os.replace(temp_path, target)
    finally:
        temp_path.unlink(missing_ok=True)


def _commit_documents(updates: dict[Path, str], originals: dict[Path, str]) -> None:
    prepared: dict[Path, Path] = {}
    replaced: list[Path] = []
    try:
        for target, content in updates.items():
            prepared[target] = _write_temp(target, content)
        for target, temp_path in prepared.items():
            os.replace(temp_path, target)
            replaced.append(target)
    except Exception as error:
        rollback_errors: list[str] = []
        for target in reversed(replaced):
            try:
                _replace_atomically(target, originals[target])
            except Exception as rollback_error:
                rollback_errors.append(f"{target.name}: {rollback_error}")
        detail = f"；回滚失败：{'；'.join(rollback_errors)}" if rollback_errors else ""
        raise SnapshotError(f"原子写入恢复文档失败：{error}{detail}") from error
    finally:
        for temp_path in prepared.values():
            temp_path.unlink(missing_ok=True)


@contextlib.contextmanager
def _project_lock(project_root: Path, timeout_seconds: float = 2.0) -> Iterator[None]:
    digest = hashlib.sha256(str(project_root).encode("utf-8")).hexdigest()[:16]
    lock_path = Path(tempfile.gettempdir()) / f"codex-precompact-{digest}.lock"
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    deadline = time.monotonic() + timeout_seconds
    try:
        while True:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise SnapshotError("等待并发 PreCompact 快照写入锁超时")
                time.sleep(0.05)
        yield
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _success_output() -> dict[str, Any]:
    return {"continue": True, "suppressOutput": True}


def _failure_output(error: Exception) -> dict[str, Any]:
    return {
        "continue": True,
        "suppressOutput": False,
        "systemMessage": (
            f"PreCompact 自动快照更新失败：{error}。"
            "已保留两份强制恢复文档的原内容，压缩继续执行。"
        ),
    }


def handle_event(
    payload: dict[str, Any],
    project_root: Path,
    *,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """处理一个已解析的 PreCompact 事件，供命令入口和测试复用。"""

    try:
        project_root = project_root.resolve()
        enabled, active_plan, active_plan_relative = _load_config(project_root)
        if not enabled:
            return _success_output()
        if payload.get("hook_event_name") != "PreCompact":
            raise SnapshotError("Hook 事件不是 PreCompact")
        if payload.get("trigger") not in {"manual", "auto"}:
            raise SnapshotError("PreCompact trigger 只能是 manual 或 auto")

        status = None
        if active_plan is not None and active_plan.is_file():
            try:
                plan_text = active_plan.read_text(encoding="utf-8")
                status = _extract_current_status(plan_text)
            except (OSError, UnicodeError, SnapshotError):
                active_plan_relative = None
                status = None
        else:
            active_plan_relative = None
        snapshot = _build_snapshot(
            active_plan_relative=active_plan_relative,
            status=status,
            now=now or dt.datetime.now().astimezone(),
        )

        targets = [project_root / relative for relative in RECOVERY_DOCUMENTS]
        missing_targets = [
            relative.as_posix()
            for relative, target in zip(RECOVERY_DOCUMENTS, targets)
            if not target.is_file()
        ]
        if missing_targets:
            raise SnapshotError(f"恢复文档不存在：{', '.join(missing_targets)}")

        with _project_lock(project_root):
            originals = {
                target: target.read_text(encoding="utf-8") for target in targets
            }
            updates = {
                target: _replace_snapshot_block(
                    originals[target],
                    snapshot,
                    target.relative_to(project_root).as_posix(),
                )
                for target in targets
            }
            _commit_documents(updates, originals)
        return _success_output()
    except (OSError, UnicodeError, SnapshotError) as error:
        return _failure_output(error)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="仅供隔离测试使用；默认从脚本位置推导项目根目录。",
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    project_root = (
        arguments.project_root.resolve()
        if arguments.project_root is not None
        else _project_root_from_script()
    )
    try:
        payload = _parse_payload(sys.stdin, project_root)
        output = handle_event(payload, project_root)
    except SnapshotError as error:
        output = _failure_output(error)
    except Exception as error:
        output = _failure_output(
            SnapshotError(f"发生未预期错误：{type(error).__name__}: {error}")
        )
    json.dump(output, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
