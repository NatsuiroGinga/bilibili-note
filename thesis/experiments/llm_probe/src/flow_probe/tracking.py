"""SwanLab 在线实验跟踪配置与生命周期管理。"""

from __future__ import annotations

import json
import hashlib
import importlib.metadata
import os
import re
import sys
import unicodedata
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

REQUIRED_SWANLAB_PROJECT = "malicious-traffic-llm"
REQUIRED_SWANLAB_WORKSPACE = "mortiswang"
EXPECTED_SWANLAB_VERSION = "0.9.0"
SWANLAB_TAG_MAX_CODEPOINTS = 20
SWANLAB_TAG_MAX_COUNT = 50
SWANLAB_PROJECT_PATTERN = re.compile(r"[0-9A-Za-z_+.-]{1,100}\Z")
SWANLAB_WORKSPACE_PATTERN = re.compile(r"[0-9A-Za-z_-]{1,25}\Z")
SWANLAB_NAME_GROUP_MAX_CODEPOINTS = 512
SWANLAB_REQUESTED_MODES = frozenset(("cloud", "online", "local", "disabled"))
DEFAULT_SWANLAB_TAG_ALIAS_PATH = (
    Path(__file__).resolve().parents[2] / "configs" / "swanlab-tag-aliases-v1.json"
)


class TrackingConfigError(ValueError):
    """实验跟踪配置不满足在线记录协议。"""


def _require_exact_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TrackingConfigError(f"{field} 必须严格为字符串")
    if not value or value != value.strip():
        raise TrackingConfigError(f"{field} 不能为空且首尾不得包含空白")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_swanlab_tag_aliases(path: Path) -> dict[str, str]:
    """读取并验证预注册的一对一 SwanLab 标签别名表。"""
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TrackingConfigError(f"无法读取 SwanLab 标签别名表：{path}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "swanlab-tag-aliases-v1":
        raise TrackingConfigError("SwanLab 标签别名表模式不符")
    raw_aliases = payload.get("aliases")
    if not isinstance(raw_aliases, dict):
        raise TrackingConfigError("SwanLab 标签别名 aliases 必须为对象")
    aliases: dict[str, str] = {}
    for raw, effective in raw_aliases.items():
        original = _require_exact_text(raw, "标签别名原值")
        alias = _require_exact_text(effective, f"标签别名 {original}")
        if alias != unicodedata.normalize("NFC", alias):
            raise TrackingConfigError(f"标签别名必须为 NFC：{original}")
        if len(alias) > SWANLAB_TAG_MAX_CODEPOINTS:
            raise TrackingConfigError(f"标签别名超过 {SWANLAB_TAG_MAX_CODEPOINTS} 个码点：{original}")
        aliases[original] = alias
    effective_values = list(aliases.values())
    if len(effective_values) != len(set(effective_values)):
        raise TrackingConfigError("SwanLab 标签别名表必须为单射")
    normalized_values = [unicodedata.normalize("NFC", value) for value in effective_values]
    if len(normalized_values) != len(set(normalized_values)):
        raise TrackingConfigError("SwanLab 标签别名在 NFC 规范化后发生冲突")
    return aliases


def _environment_tags(raw: str) -> list[str]:
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise TrackingConfigError("SWANLAB_TAGS 不是合法 JSON 列表") from exc
        if not isinstance(parsed, list):
            raise TrackingConfigError("SWANLAB_TAGS JSON 必须是列表")
        return [_require_exact_text(item, "SWANLAB_TAGS 标签") for item in parsed]
    return [_require_exact_text(item, "SWANLAB_TAGS 标签") for item in raw.split(",")]


def validate_swanlab_contract(
    destination: Mapping[str, object],
    *,
    aliases: Mapping[str, str] | None = None,
    authorized_workspace: str | None = None,
    authorized_project: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """对最终目的地和最终有效标签执行唯一机械合同。"""
    aliases = dict(aliases or {})
    fields = {
        key: _require_exact_text(destination.get(key), f"SwanLab {key}")
        for key in ("workspace", "project", "name", "group", "mode")
    }
    if SWANLAB_WORKSPACE_PATTERN.fullmatch(fields["workspace"]) is None:
        raise TrackingConfigError(
            "SwanLab workspace 必须为 1 至 25 位且只含字母、数字、下划线或连字符"
        )
    if SWANLAB_PROJECT_PATTERN.fullmatch(fields["project"]) is None:
        raise TrackingConfigError(
            "SwanLab project 必须为 1 至 100 位且只含字母、数字、下划线、加号、点或连字符"
        )
    for field in ("name", "group"):
        if len(fields[field]) > SWANLAB_NAME_GROUP_MAX_CODEPOINTS:
            raise TrackingConfigError(
                f"SwanLab {field} 不得超过 {SWANLAB_NAME_GROUP_MAX_CODEPOINTS} 个码点"
            )
    if fields["mode"] not in SWANLAB_REQUESTED_MODES:
        raise TrackingConfigError(
            f"SwanLab mode 必须属于：{', '.join(sorted(SWANLAB_REQUESTED_MODES))}"
        )
    if authorized_workspace is not None and fields["workspace"] != authorized_workspace:
        raise TrackingConfigError("SwanLab 工作区与本轮授权不一致")
    if authorized_project is not None and fields["project"] != authorized_project:
        raise TrackingConfigError("SwanLab 项目与本轮授权不一致")

    raw_tags = destination.get("tags")
    if not isinstance(raw_tags, (list, tuple)):
        raise TrackingConfigError("最终 tags 必须显式为 list 或 tuple")
    if not raw_tags:
        raise TrackingConfigError("最终 tags 不能为空")
    if len(raw_tags) > SWANLAB_TAG_MAX_COUNT:
        raise TrackingConfigError(f"最终 tags 不得超过 {SWANLAB_TAG_MAX_COUNT} 项")
    original_tags = [_require_exact_text(tag, "SwanLab 标签") for tag in raw_tags]
    if len(original_tags) != len(set(original_tags)):
        raise TrackingConfigError("最终 tags 不得包含重复原标签")
    original_nfc = [unicodedata.normalize("NFC", tag) for tag in original_tags]
    if len(original_nfc) != len(set(original_nfc)):
        raise TrackingConfigError("最终 tags 在 NFC 规范化后存在原标签冲突")

    effective_tags: list[str] = []
    applications: list[dict[str, str]] = []
    for original, normalized in zip(original_tags, original_nfc, strict=True):
        effective = aliases.get(original, original)
        if original != normalized and original not in aliases:
            raise TrackingConfigError(f"非 NFC 标签必须通过预注册别名修正：{original}")
        _require_exact_text(effective, f"SwanLab 有效标签 {original}")
        if effective != unicodedata.normalize("NFC", effective):
            raise TrackingConfigError(f"SwanLab 有效标签必须为 NFC：{original}")
        if len(effective) > SWANLAB_TAG_MAX_CODEPOINTS:
            raise TrackingConfigError(
                f"SwanLab 有效标签超过 {SWANLAB_TAG_MAX_CODEPOINTS} 个码点且无合法别名：{original}"
            )
        effective_tags.append(effective)
        if effective != original:
            applications.append({"original": original, "effective": effective})
    if len(effective_tags) != len(set(effective_tags)):
        raise TrackingConfigError("最终有效标签不得重复")
    effective_nfc = [unicodedata.normalize("NFC", tag) for tag in effective_tags]
    if len(effective_nfc) != len(set(effective_nfc)):
        raise TrackingConfigError("最终有效标签在 NFC 规范化后发生冲突")

    active_environment = os.environ if environment is None else environment
    raw_environment_tags = active_environment.get("SWANLAB_TAGS")
    if raw_environment_tags is not None:
        parsed_environment_tags = _environment_tags(raw_environment_tags)
        if parsed_environment_tags != effective_tags:
            raise TrackingConfigError("SWANLAB_TAGS 与最终有效标签发生漂移")

    effective_fields = {**fields, "mode": "online" if fields["mode"] == "cloud" else fields["mode"]}
    canonical = {
        "requested_destination": fields,
        "effective_destination": effective_fields,
        "original_tags": original_tags,
        "effective_tags": effective_tags,
        "alias_applications": applications,
    }
    digest = hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "swanlab-effective-tag-receipt-v1",
        **canonical,
        "requested_mode": fields["mode"],
        "effective_mode": effective_fields["mode"],
        "nfc_original_tags": original_nfc,
        "nfc_effective_tags": effective_nfc,
        "tag_count": len(effective_tags),
        "maximum_tag_codepoints": max(map(len, effective_tags)),
        "limits": {
            "maximum_tag_codepoints": SWANLAB_TAG_MAX_CODEPOINTS,
            "maximum_tag_count": SWANLAB_TAG_MAX_COUNT,
        },
        "swanlab_tags_environment_present": raw_environment_tags is not None,
        "contract_sha256": digest,
    }


def write_swanlab_tag_receipt(path: Path, receipt: Mapping[str, object]) -> None:
    """原子写入最终有效标签收据。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(dict(receipt), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def initialize_swanlab_run(
    destination: Mapping[str, object],
    *,
    aliases: Mapping[str, str] | None = None,
    alias_config_path: Path = DEFAULT_SWANLAB_TAG_ALIAS_PATH,
    expected_alias_config_sha256: str | None = None,
    config: Mapping[str, object],
    log_dir: Path,
    tag_receipt_path: Path,
    authorized_workspace: str,
    authorized_project: str,
    extra_init_kwargs: Mapping[str, object] | None = None,
) -> tuple[object, object, dict[str, object]]:
    """先执行统一合同并写收据，再创建唯一 SwanLab 在线运行。"""
    alias_config_path = Path(alias_config_path).resolve()
    alias_config_sha256 = _sha256_file(alias_config_path)
    if (
        expected_alias_config_sha256 is not None
        and alias_config_sha256 != expected_alias_config_sha256
    ):
        raise TrackingConfigError("SwanLab 标签别名文件哈希与冻结值不一致")
    file_aliases = load_swanlab_tag_aliases(alias_config_path)
    if aliases and dict(aliases) != file_aliases:
        raise TrackingConfigError("显式标签别名不得偏离冻结别名文件")
    receipt = validate_swanlab_contract(
        destination,
        aliases=file_aliases,
        authorized_workspace=authorized_workspace,
        authorized_project=authorized_project,
    )
    actual_swanlab_version = importlib.metadata.version("swanlab")
    if actual_swanlab_version != EXPECTED_SWANLAB_VERSION:
        raise TrackingConfigError(
            f"SwanLab 实际版本必须为 {EXPECTED_SWANLAB_VERSION}，当前为 {actual_swanlab_version}"
        )
    receipt.update(
        {
            "expected_swanlab_version": EXPECTED_SWANLAB_VERSION,
            "actual_swanlab_version": actual_swanlab_version,
            "alias_config_path": str(alias_config_path),
            "alias_config_sha256": alias_config_sha256,
        }
    )
    write_swanlab_tag_receipt(tag_receipt_path, receipt)
    protected = {"workspace", "project", "name", "group", "mode", "tags", "config", "log_dir"}
    extra = dict(extra_init_kwargs or {})
    overlap = sorted(protected.intersection(extra))
    if overlap:
        raise TrackingConfigError(f"额外初始化参数不得覆盖统一字段：{', '.join(overlap)}")
    kwargs: dict[str, object] = {
        **receipt["effective_destination"],
        "tags": list(receipt["effective_tags"]),
        "config": dict(config),
        "log_dir": str(log_dir),
        **extra,
    }
    import swanlab

    run = swanlab.init(**kwargs)
    return swanlab, run, receipt


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

        strings: dict[str, str] = {}
        for field in ("project", "workspace", "run_name", "description", "mode"):
            strings[field] = _require_exact_text(data[field], field)
        if strings["mode"] != "online":
            raise TrackingConfigError("服务器实验必须使用 SwanLab online 模式")
        if strings["project"] != REQUIRED_SWANLAB_PROJECT:
            raise TrackingConfigError(f"SwanLab 项目必须为 {REQUIRED_SWANLAB_PROJECT}")
        if strings["workspace"] != REQUIRED_SWANLAB_WORKSPACE:
            raise TrackingConfigError(f"SwanLab 工作区必须为 {REQUIRED_SWANLAB_WORKSPACE}")

        receipt = validate_swanlab_contract(
            {
                "project": strings["project"],
                "workspace": strings["workspace"],
                "name": strings["run_name"],
                "group": strings["run_name"],
                "mode": strings["mode"],
                "tags": data["tags"],
            },
            authorized_project=REQUIRED_SWANLAB_PROJECT,
            authorized_workspace=REQUIRED_SWANLAB_WORKSPACE,
        )

        return cls(
            project=strings["project"],
            workspace=strings["workspace"],
            run_name=strings["run_name"],
            description=strings["description"],
            mode=strings["mode"],
            tags=tuple(receipt["effective_tags"]),
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
        "swanlab_tag_receipt": artifact_dir / "swanlab-tag-receipt.json",
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
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_dir / "artifact_manifest.json"
    if manifest_path.exists():
        raise TrackingConfigError(f"运行目录已有制品清单，不得复用：{artifact_dir}")
    log_dir = artifact_dir / "swanlog" / phase
    init_kwargs = build_init_kwargs(settings, phase, config, log_dir=log_dir)
    destination = {key: init_kwargs.pop(key) for key in ("workspace", "project", "name", "group", "mode", "tags")}
    init_kwargs.pop("config")
    init_kwargs.pop("log_dir")
    swanlab, run, _ = initialize_swanlab_run(
        destination,
        config=config,
        log_dir=log_dir,
        tag_receipt_path=artifact_dir / "swanlab-tag-receipt.json",
        authorized_workspace=settings.workspace,
        authorized_project=settings.project,
        extra_init_kwargs=init_kwargs,
    )
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
