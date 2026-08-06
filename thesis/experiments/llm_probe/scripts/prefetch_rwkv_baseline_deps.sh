#!/usr/bin/env bash
set -Eeuo pipefail

prepare_output_root() {
    local output_root="$1"
    mkdir -p -- "$output_root"
    if [[ ! -d "$output_root" || ! -w "$output_root" ]]; then
        printf '输出根目录不可写：%s\n' "$output_root" >&2
        return 1
    fi
}

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    return 0
fi

if [[ $# -ne 1 ]]; then
    printf '%s\n' '用法：bash scripts/prefetch_rwkv_baseline_deps.sh <参数JSON>' >&2
    exit 2
fi

cleanup_proxy() {
    unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
}
trap cleanup_proxy EXIT

if [[ "${RWKV_PREFETCH_VALIDATE_ONLY:-0}" != "1" && -f /etc/network_turbo ]]; then
    # 网络加速仅在本脚本进程内生效，退出时统一清除代理变量。
    source /etc/network_turbo >/dev/null 2>&1
fi

if [[ "${RWKV_PREFETCH_VALIDATE_ONLY:-0}" != "1" ]]; then
    prepare_output_root \
        "/root/autodl-tmp/thesis/experiments/llm_probe/artifacts/rwkv-baseline-deps"
fi

python3 - "$1" <<'PY'
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path


EXPECTED_ROOT = Path(
    "/root/autodl-tmp/thesis/experiments/llm_probe/artifacts/rwkv-baseline-deps"
)
RUN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{7,95}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
PACKAGE_NAME_PATTERN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.-]*)")
LICENSE_NAMES = {"LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING"}
DEPENDENCY_FILES = {
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: object) -> None:
    temporary = path.with_name(f".{path.name}.partial")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def first_line(arguments: list[str]) -> str | None:
    try:
        result = subprocess.run(arguments, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    lines = result.stdout.strip().splitlines()
    return lines[0] if lines else None


def canonical_package_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def requirement_name(value: str) -> str:
    match = PACKAGE_NAME_PATTERN.match(value.strip())
    if match is None:
        raise ValueError(f"无法识别依赖名称：{value}")
    return canonical_package_name(match.group(1))


def validate_config(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("参数必须是 schema_version=1 的 JSON 对象。")
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id 格式无效。")
    if Path(str(payload.get("output_root"))) != EXPECTED_ROOT:
        raise ValueError("输出根目录偏离冻结服务端路径。")
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("sources 必须是非空列表。")
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("源码锁条目必须是对象。")
        repository = source.get("repository")
        commit = source.get("commit")
        if not isinstance(repository, str) or not repository.startswith(
            "https://github.com/"
        ):
            raise ValueError("源码仓库必须是 GitHub HTTPS 地址。")
        if not isinstance(commit, str) or not COMMIT_PATTERN.fullmatch(commit):
            raise ValueError("源码提交必须是完整的 40 位小写哈希。")
    audit_packages = payload.get("audit_packages")
    requirements = payload.get("download_requirements")
    if not isinstance(audit_packages, list) or not all(
        isinstance(item, str) for item in audit_packages
    ):
        raise ValueError("audit_packages 必须是字符串列表。")
    if not isinstance(requirements, list) or not all(
        isinstance(item, str) for item in requirements
    ):
        raise ValueError("download_requirements 必须是字符串列表。")
    if any(requirement_name(item) == "torch" for item in requirements):
        raise ValueError("禁止把 torch 放入下载清单。")
    return payload


config_path = Path(sys.argv[1])
config = validate_config(json.loads(config_path.read_text(encoding="utf-8")))

if os.environ.get("RWKV_PREFETCH_VALIDATE_ONLY") == "1":
    print(
        json.dumps(
            {
                "status": "validated",
                "run_id": config["run_id"],
                "source_count": len(config["sources"]),
                "audit_package_count": len(config["audit_packages"]),
                "download_requirement_count": len(config["download_requirements"]),
                "missing_command_probe": first_line(
                    ["rwkv-prefetch-command-that-does-not-exist"]
                ),
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(0)

output_root = EXPECTED_ROOT
run_id = str(config["run_id"])
run_dir = output_root / run_id
state_path = run_dir / "state.json"
log_path = run_dir / "prefetch.log"
partial_root = run_dir / ".partial"
source_root = run_dir / "sources"
metadata_root = run_dir / "source-metadata"
package_root = run_dir / "packages"

disk_before = shutil.disk_usage(output_root.parent)
resumed_from_failure = False
if run_dir.exists():
    if not state_path.is_file():
        raise SystemExit(f"既有运行目录缺少状态，拒绝复用：{run_dir}")
    previous_state = json.loads(state_path.read_text(encoding="utf-8"))
    if previous_state.get("run_id") != run_id or previous_state.get("status") != "failed":
        raise SystemExit(f"既有运行目录不是同一失败任务，拒绝复用：{run_dir}")
    preserved_state = run_dir / "state-before-codeload-resume.json"
    if not preserved_state.exists():
        shutil.copy2(state_path, preserved_state)
    resumed_from_failure = True
else:
    run_dir.mkdir(parents=True)
partial_root.mkdir(exist_ok=True)
source_root.mkdir(exist_ok=True)
metadata_root.mkdir(exist_ok=True)
package_root.mkdir(exist_ok=True)


def emit(event: str, **values: object) -> None:
    payload = {"at": utc_now(), "event": event, **values}
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def run_command(arguments: list[str], *, cwd: Path | None = None) -> str:
    emit("command_start", command=arguments[0], arguments=arguments[1:])
    process = subprocess.Popen(
        arguments,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert process.stdout is not None
    collected: list[str] = []
    for line in process.stdout:
        text = line.rstrip("\n")
        collected.append(text)
        emit("command_output", command=arguments[0], output=text)
    return_code = process.wait()
    emit("command_end", command=arguments[0], exit_code=return_code)
    if return_code != 0:
        raise RuntimeError(f"命令失败（{return_code}）：{arguments[0]}")
    return "\n".join(collected).strip()


def classify_license(content: str) -> str:
    lowered = content.lower()
    if "apache license" in lowered and "version 2.0" in lowered:
        return "Apache-2.0"
    if "mit license" in lowered:
        return "MIT"
    if "redistribution and use in source and binary forms" in lowered:
        return "BSD-3-Clause"
    if "gnu general public license" in lowered:
        return "GPL"
    return "UNKNOWN"


installed_versions: dict[str, str] = {}
installed_snapshot: list[dict[str, str]] = []
for distribution in importlib.metadata.distributions():
    name = distribution.metadata.get("Name")
    if not name:
        continue
    normalized = canonical_package_name(name)
    installed_versions[normalized] = distribution.version
    installed_snapshot.append({"name": name, "version": distribution.version})
installed_snapshot.sort(key=lambda item: item["name"].lower())
atomic_json(run_dir / "installed-packages.json", installed_snapshot)

torch_runtime: dict[str, object]
torch_probe = subprocess.run(
    [
        "python3",
        "-c",
        (
            "import json, torch; "
            "print(json.dumps({'version': torch.__version__, "
            "'cuda_version': torch.version.cuda, "
            "'cuda_available': torch.cuda.is_available()}))"
        ),
    ],
    text=True,
    capture_output=True,
    check=False,
)
if torch_probe.returncode == 0:
    torch_runtime = json.loads(torch_probe.stdout)
else:
    torch_runtime = {"error": torch_probe.stderr.strip(), "exit_code": torch_probe.returncode}

environment = {
    "captured_at": utc_now(),
    "architecture": platform.machine(),
    "platform": platform.platform(),
    "python": platform.python_version(),
    "uv": first_line(["uv", "--version"]),
    "gcc": first_line(["gcc", "--version"]),
    "glibc": first_line(["ldd", "--version"]),
    "nvcc": first_line(["nvcc", "--version"]),
    "nvidia_smi": first_line(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader",
        ]
    ),
    "torch_runtime": torch_runtime,
}
atomic_json(run_dir / "environment.json", environment)

audit: list[dict[str, object]] = []
for package in config["audit_packages"]:
    normalized = canonical_package_name(str(package))
    audit.append(
        {
            "package": package,
            "normalized_name": normalized,
            "installed": normalized in installed_versions,
            "version": installed_versions.get(normalized),
        }
    )
atomic_json(run_dir / "package-audit.json", audit)

state = {
    "schema_version": 1,
    "run_id": run_id,
    "status": "running",
    "created_at": utc_now(),
    "output_root": str(output_root),
    "resumed_from_failure": resumed_from_failure,
}
atomic_json(state_path, state)
emit("prefetch_started", run_id=run_id, disk_free_bytes=disk_before.free)

source_records: list[dict[str, object]] = []
package_records: list[dict[str, object]] = []
try:
    for source in config["sources"]:
        name = str(source["name"])
        commit = str(source["commit"])
        repository = str(source["repository"])
        archive_path = source_root / f"{name}-{commit}.tar.gz"
        repository_match = re.fullmatch(
            r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?", repository
        )
        if repository_match is None:
            raise RuntimeError(f"{name} 仓库地址无法转换为官方 codeload 地址。")
        owner, repository_name = repository_match.groups()
        codeload_url = (
            f"https://codeload.github.com/{owner}/{repository_name}/tar.gz/{commit}"
        )
        partial_archive = partial_root / f"{name}-{commit}.tar.gz.partial"
        if not archive_path.exists():
            run_command(
                [
                    "curl",
                    "--fail",
                    "--location",
                    "--retry",
                    "8",
                    "--retry-all-errors",
                    "--retry-delay",
                    "5",
                    "--continue-at",
                    "-",
                    "--output",
                    str(partial_archive),
                    codeload_url,
                ]
            )
            partial_archive.replace(archive_path)

        with tarfile.open(archive_path, "r:gz") as archive:
            regular_members = [member for member in archive.getmembers() if member.isfile()]
            roots = {member.name.split("/", 1)[0] for member in regular_members}
            if len(roots) != 1:
                raise RuntimeError(f"{name} 官方归档顶层目录不唯一。")
            archive_root = next(iter(roots))
            if commit not in archive_root:
                raise RuntimeError(f"{name} 官方归档顶层目录未绑定完整提交。")
            top_level_members = {
                member.name.split("/", 1)[1]: member
                for member in regular_members
                if "/" in member.name and "/" not in member.name.split("/", 1)[1]
            }
            license_paths = [
                item for item in top_level_members if Path(item).name in LICENSE_NAMES
            ]
            dependency_paths = [
                item for item in top_level_members if Path(item).name in DEPENDENCY_FILES
            ]
            extracted_content: dict[str, str] = {}
            for relative in [*license_paths, *dependency_paths]:
                extracted = archive.extractfile(top_level_members[relative])
                if extracted is None:
                    raise RuntimeError(f"{name} 无法读取归档成员：{relative}")
                extracted_content[relative] = extracted.read().decode("utf-8")
        saved_licenses: list[dict[str, object]] = []
        detected_licenses: list[str] = []
        for relative in license_paths:
            content = extracted_content[relative]
            target = metadata_root / f"{name}__{Path(relative).name}"
            target.write_text(content, encoding="utf-8")
            classification = classify_license(content)
            detected_licenses.append(classification)
            saved_licenses.append(
                {
                    "repository_path": relative,
                    "backup_path": target.relative_to(run_dir).as_posix(),
                    "classification": classification,
                    "sha256": sha256_file(target),
                    "size_bytes": target.stat().st_size,
                }
            )
        saved_specs: list[dict[str, object]] = []
        for relative in dependency_paths:
            content = extracted_content[relative]
            target = metadata_root / f"{name}__{Path(relative).name}"
            target.write_text(content, encoding="utf-8")
            saved_specs.append(
                {
                    "repository_path": relative,
                    "backup_path": target.relative_to(run_dir).as_posix(),
                    "sha256": sha256_file(target),
                    "size_bytes": target.stat().st_size,
                }
            )
        source_records.append(
            {
                "name": name,
                "repository": repository,
                "commit": commit,
                "transport": "github_codeload_resumable",
                "download_url": codeload_url,
                "archive_root": archive_root,
                "archive": archive_path.relative_to(run_dir).as_posix(),
                "archive_sha256": sha256_file(archive_path),
                "archive_size_bytes": archive_path.stat().st_size,
                "licenses": saved_licenses,
                "license_classifications": sorted(set(detected_licenses)),
                "dependency_specs": saved_specs,
            }
        )
        emit(
            "source_archived",
            name=name,
            commit=commit,
            size_bytes=archive_path.stat().st_size,
        )

    for requirement in config["download_requirements"]:
        requirement = str(requirement)
        normalized = requirement_name(requirement)
        if normalized in installed_versions:
            package_records.append(
                {
                    "requirement": requirement,
                    "decision": "already_installed",
                    "installed_version": installed_versions[normalized],
                    "artifacts": [],
                }
            )
            continue
        before = {item.name for item in package_root.iterdir()}
        run_command(
            [
                "python3",
                "-m",
                "pip",
                "download",
                "--disable-pip-version-check",
                "--no-deps",
                "--dest",
                str(package_root),
                requirement,
            ]
        )
        artifacts = sorted(
            item for item in package_root.iterdir() if item.is_file() and item.name not in before
        )
        if not artifacts:
            raise RuntimeError(f"依赖下载未产生新文件：{requirement}")
        package_records.append(
            {
                "requirement": requirement,
                "decision": "downloaded_for_offline_install",
                "installed_version": None,
                "artifacts": [
                    {
                        "path": item.relative_to(run_dir).as_posix(),
                        "sha256": sha256_file(item),
                        "size_bytes": item.stat().st_size,
                        "kind": "wheel" if item.suffix == ".whl" else "source_distribution",
                    }
                    for item in artifacts
                ],
            }
        )
        emit("requirement_downloaded", requirement=requirement, file_count=len(artifacts))

    shutil.rmtree(partial_root)
    disk_after_payload = shutil.disk_usage(output_root.parent)
    state.update(
        {
            "status": "finished",
            "finished_at": utc_now(),
            "archive_name": f"{run_id}.tar.gz",
            "disk_free_bytes_before": disk_before.free,
            "disk_free_bytes_after_payload": disk_after_payload.free,
        }
    )
    atomic_json(state_path, state)
    emit(
        "prefetch_finished",
        source_count=len(source_records),
        dependency_count=len(package_records),
        disk_free_bytes=disk_after_payload.free,
    )

    manifest = {
        "schema_version": "rwkv-baseline-deps-v1",
        "run_id": run_id,
        "created_at": utc_now(),
        "status": "finished",
        "environment": environment,
        "disk": {
            "free_bytes_before": disk_before.free,
            "free_bytes_after_payload": disk_after_payload.free,
            "payload_bytes": disk_before.free - disk_after_payload.free,
        },
        "source_snapshots": source_records,
        "package_audit": audit,
        "dependency_decisions": package_records,
        "mamba_build_policy": {
            "prebuilt_wheel_trusted": False,
            "reason": (
                "未发现可证明同时匹配 Python 3.10、PyTorch 2.13.0+cu130、"
                "Linux x86_64 与 glibc 2.35 的官方轮子；仅保存官方源码与构建依赖。"
            ),
            "installation_mode": "server_source_build",
            "torch_redownloaded": False,
            "pretrained_weights_downloaded": False,
        },
    }
    files_before_manifest = sorted(
        item for item in run_dir.rglob("*") if item.is_file()
    )
    manifest["files"] = [
        {
            "path": item.relative_to(run_dir).as_posix(),
            "sha256": sha256_file(item),
            "size_bytes": item.stat().st_size,
        }
        for item in files_before_manifest
    ]
    manifest_path = run_dir / "manifest.json"
    atomic_json(manifest_path, manifest)

    checksum_files = sorted(
        item
        for item in run_dir.rglob("*")
        if item.is_file() and item.name != "manifest.sha256"
    )
    checksum_path = run_dir / "manifest.sha256"
    checksum_path.write_text(
        "".join(
            f"{sha256_file(item)}  {item.relative_to(run_dir).as_posix()}\n"
            for item in checksum_files
        ),
        encoding="utf-8",
    )

    archive_path = output_root / f"{run_id}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(run_dir, arcname=run_id, recursive=True)
    archive_hash = sha256_file(archive_path)
    archive_checksum = output_root / f"{run_id}.tar.gz.sha256"
    archive_checksum.write_text(f"{archive_hash}  {archive_path.name}\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "finished",
                "run_dir": str(run_dir),
                "manifest": str(manifest_path),
                "archive": str(archive_path),
                "archive_sha256": archive_hash,
            },
            ensure_ascii=False,
        )
    )
except Exception as error:
    state.update(
        {
            "status": "failed",
            "failed_at": utc_now(),
            "error": str(error),
        }
    )
    atomic_json(state_path, state)
    emit("prefetch_failed", error=str(error))
    raise
PY
