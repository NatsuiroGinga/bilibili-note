"""SwanLab 在线实验跟踪配置与生命周期管理。"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

REQUIRED_SWANLAB_PROJECT = "malicious-traffic-llm"
REQUIRED_SWANLAB_WORKSPACE = "mortiswang"


class TrackingConfigError(ValueError):
    """实验跟踪配置不满足在线记录协议。"""


@dataclass(frozen=True)
class TrackingSettings:
    """一次实验所需的 SwanLab 项目与运行标识。"""

    project: str
    workspace: str
    run_name: str
    description: str
    mode: str
    tags: tuple[str, ...]

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> TrackingSettings:
        required = {
            "project",
            "workspace",
            "run_name",
            "description",
            "mode",
            "tags",
        }
        missing = sorted(required.difference(data))
        if missing:
            raise TrackingConfigError(f"缺少跟踪字段：{', '.join(missing)}")

        strings = {}
        for field in ("project", "workspace", "run_name", "description", "mode"):
            value = str(data[field]).strip()
            if not value:
                raise TrackingConfigError(f"{field} 不能为空")
            strings[field] = value
        if strings["mode"] != "online":
            raise TrackingConfigError("服务器实验必须使用 SwanLab online 模式")
        if strings["project"] != REQUIRED_SWANLAB_PROJECT:
            raise TrackingConfigError(f"SwanLab 项目必须为 {REQUIRED_SWANLAB_PROJECT}")
        if strings["workspace"] != REQUIRED_SWANLAB_WORKSPACE:
            raise TrackingConfigError(f"SwanLab 工作区必须为 {REQUIRED_SWANLAB_WORKSPACE}")

        raw_tags = data["tags"]
        if not isinstance(raw_tags, (list, tuple)):
            raise TrackingConfigError("tags 必须是字符串列表")
        tags = tuple(str(tag).strip() for tag in raw_tags)
        if not tags or any(not tag for tag in tags):
            raise TrackingConfigError("tags 不能为空且不得包含空标签")
        if any(len(tag) > 20 for tag in tags):
            raise TrackingConfigError("每个 SwanLab 标签不得超过 20 个字符")

        return cls(
            project=strings["project"],
            workspace=strings["workspace"],
            run_name=strings["run_name"],
            description=strings["description"],
            mode=strings["mode"],
            tags=tags,
        )


def build_init_kwargs(
    settings: TrackingSettings,
    phase: str,
    config: Mapping[str, object],
    log_dir: Path | None = None,
) -> dict[str, object]:
    """构造显式在线、可分组的 SwanLab 初始化参数。"""
    cleaned_phase = phase.strip()
    if not cleaned_phase:
        raise TrackingConfigError("phase 不能为空")
    kwargs: dict[str, object] = {
        "project": settings.project,
        "workspace": settings.workspace,
        "name": f"{settings.run_name}-{cleaned_phase}",
        "description": settings.description,
        "config": dict(config),
        "mode": settings.mode,
        "tags": list(settings.tags),
        "group": settings.run_name,
        "job_type": cleaned_phase,
    }
    if log_dir is not None:
        kwargs["log_dir"] = str(log_dir)
    return kwargs


def flatten_scalar_metrics(data: Mapping[str, object], prefix: str = "") -> dict[str, int | float]:
    """把嵌套摘要展开为 SwanLab 可记录的数值指标。"""
    flattened: dict[str, int | float] = {}
    for key, value in data.items():
        path = f"{prefix}/{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            flattened.update(flatten_scalar_metrics(value, path))
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            flattened[path] = value
    return flattened


def build_artifact_manifest(
    settings: TrackingSettings,
    phase: str,
    run_id: str,
    artifact_dir: Path,
    data_files: Mapping[str, Path],
    status: str,
) -> dict[str, object]:
    """构造可定位云端运行和本地全部制品的清单。"""
    artifact_dir = Path(artifact_dir)
    files = {
        "artifact_manifest": artifact_dir / "artifact_manifest.json",
        "console_log": artifact_dir / "console.log",
        "swanlab_log_dir": artifact_dir / "swanlog" / phase,
        **data_files,
    }
    return {
        "schema_version": "flow_probe_run_artifacts_v1",
        "status": status,
        "tracking_mode": settings.mode,
        "workspace": settings.workspace,
        "project": settings.project,
        "run_name": f"{settings.run_name}-{phase}",
        "phase": phase,
        "run_id": run_id,
        "run_url": (
            f"https://swanlab.cn/@{settings.workspace}/{settings.project}" f"/runs/{run_id}/chart"
        ),
        "data_files": {name: str(path) for name, path in sorted(files.items())},
    }


class _TeeStream:
    """把文本同时写入原始终端和实验日志文件。"""

    def __init__(self, terminal: TextIO, log_file: TextIO) -> None:
        self.terminal = terminal
        self.log_file = log_file

    @property
    def encoding(self) -> str | None:
        return self.terminal.encoding

    def write(self, text: str) -> int:
        self.terminal.write(text)
        self.log_file.write(text)
        return len(text)

    def flush(self) -> None:
        self.terminal.flush()
        self.log_file.flush()

    def isatty(self) -> bool:
        return self.terminal.isatty()

    def fileno(self) -> int:
        return self.terminal.fileno()


@contextmanager
def capture_console_log(path: Path) -> Iterator[None]:
    """在保留终端输出的同时，把标准输出和错误写入运行目录。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with (
        path.open("a", encoding="utf-8") as log_file,
        redirect_stdout(_TeeStream(sys.stdout, log_file)),
        redirect_stderr(_TeeStream(sys.stderr, log_file)),
    ):
        yield


@contextmanager
def swanlab_run(
    settings: TrackingSettings,
    phase: str,
    config: Mapping[str, object],
    artifact_dir: Path,
    data_files: Mapping[str, Path],
) -> Iterator[object]:
    """启动在线运行，并在异常时显式标记失败。"""
    import swanlab

    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_dir / "artifact_manifest.json"
    if manifest_path.exists():
        raise TrackingConfigError(f"运行目录已有制品清单，不得复用：{artifact_dir}")
    log_dir = artifact_dir / "swanlog" / phase
    run = swanlab.init(**build_init_kwargs(settings, phase, config, log_dir=log_dir))
    status = "running"
    try:
        yield swanlab
    except BaseException as exc:
        status = "crashed"
        swanlab.finish(state="crashed", error=str(exc))
        raise
    else:
        status = "finished"
        swanlab.finish()
    finally:
        manifest = build_artifact_manifest(
            settings=settings,
            phase=phase,
            run_id=str(run.id),
            artifact_dir=artifact_dir,
            data_files=data_files,
            status=status,
        )
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
