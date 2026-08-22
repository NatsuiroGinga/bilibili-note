#!/usr/bin/env python3
"""扫描真实配置的 SwanLab 合同，并登记尚未迁移的直接初始化入口。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from flow_probe.tracking import (  # noqa: E402
    TrackingConfigError,
    load_swanlab_tag_aliases,
    validate_swanlab_contract,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="扫描真实配置中的 SwanLab 最终合同")
    parser.add_argument("--config-root", type=Path, default=PROJECT_ROOT / "configs")
    parser.add_argument("--alias-config", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--authorized-workspace")
    parser.add_argument("--authorized-project")
    return parser.parse_args()


def run_checked(command: list[str]) -> str:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode not in (0, 1):
        raise RuntimeError(
            f"命令执行失败，退出码 {completed.returncode}：{' '.join(command)}\n{completed.stderr}"
        )
    return completed.stdout


def config_paths(root: Path) -> list[Path]:
    output = run_checked(["fd", "-e", "json", ".", str(root)])
    return sorted(Path(line) for line in output.splitlines() if line.strip())


def swanlab_mappings(node: object, location: str = "$") -> Iterator[tuple[str, Mapping[str, object]]]:
    if isinstance(node, Mapping):
        for key, value in node.items():
            child_location = f"{location}.{key}"
            if key == "swanlab" and isinstance(value, Mapping):
                yield child_location, value
            yield from swanlab_mappings(value, child_location)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from swanlab_mappings(value, f"{location}[{index}]")


def scan_configs(
    root: Path,
    aliases: Mapping[str, str],
    authorized_workspace: str | None,
    authorized_project: str | None,
) -> dict[str, object]:
    checked: list[dict[str, object]] = []
    invalid: list[dict[str, str]] = []
    unresolved: list[dict[str, object]] = []
    files = config_paths(root)
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            invalid.append({"path": str(path), "location": "$", "error": str(exc)})
            continue
        for location, destination in swanlab_mappings(payload):
            final_destination = dict(destination)
            derived_fields: list[str] = []
            if location == "$.swanlab" and isinstance(payload, Mapping):
                if "name" not in final_destination and "display_name" in payload:
                    final_destination["name"] = payload["display_name"]
                    derived_fields.append("name<-$.display_name")
                if "group" not in final_destination and "run_id" in payload:
                    final_destination["group"] = payload["run_id"]
                    derived_fields.append("group<-$.run_id")
            missing_final_fields = [
                field
                for field in ("workspace", "project", "name", "group", "mode", "tags")
                if field not in final_destination
            ]
            if missing_final_fields:
                unresolved.append(
                    {
                        "path": str(path),
                        "location": location,
                        "missing_final_fields": missing_final_fields,
                        "derived_fields": derived_fields,
                        "reason": "静态配置未包含可由通用扫描器确定的最终 SwanLab 目的地",
                    }
                )
                continue
            try:
                receipt = validate_swanlab_contract(
                    final_destination,
                    aliases=aliases,
                    authorized_workspace=authorized_workspace,
                    authorized_project=authorized_project,
                )
            except TrackingConfigError as exc:
                invalid.append({"path": str(path), "location": location, "error": str(exc)})
                continue
            checked.append(
                {
                    "path": str(path),
                    "location": location,
                    "contract_sha256": receipt["contract_sha256"],
                    "original_tags": receipt["original_tags"],
                    "effective_tags": receipt["effective_tags"],
                    "alias_applications": receipt["alias_applications"],
                    "destination": receipt["destination"],
                    "derived_fields": derived_fields,
                }
            )
    return {
        "json_file_count": len(files),
        "swanlab_mapping_count": len(checked) + len(invalid) + len(unresolved),
        "swanlab_contract_count": len(checked) + len(invalid),
        "valid_contracts": checked,
        "invalid_contracts": invalid,
        "unresolved_runtime_destinations": unresolved,
    }


def scan_direct_initializers(source_root: Path) -> dict[str, object]:
    command = [
        "rg",
        "--line-number",
        "swanlab[.]init[(]",
        str(source_root / "src"),
        str(source_root / "tools"),
        str(source_root / "scripts"),
        "--glob",
        "!vendor/**",
        "--glob",
        "!runs/**",
        "--glob",
        "!cache/**",
        "--glob",
        "!archive/**",
    ]
    lines = [line for line in run_checked(command).splitlines() if line.strip()]
    centralized: list[str] = []
    remaining: list[str] = []
    for line in lines:
        if line.split(":", 1)[0].endswith("src/flow_probe/tracking.py"):
            centralized.append(line)
        else:
            remaining.append(line)
    return {
        "centralized_entry": centralized,
        "remaining_direct_init_count": len(remaining),
        "remaining_direct_init_entries": remaining,
        "migration_blocked": bool(remaining),
        "blocking_reason": (
            "仍有直接 swanlab.init 入口未迁移；本轮只扫描，不修改未授权文件"
            if remaining
            else None
        ),
    }


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def main() -> int:
    args = parse_args()
    aliases = load_swanlab_tag_aliases(args.alias_config)
    config_scan = scan_configs(
        args.config_root,
        aliases,
        args.authorized_workspace,
        args.authorized_project,
    )
    initializer_scan = scan_direct_initializers(args.source_root)
    report = {
        "schema_version": "swanlab-contract-scan-report-v1",
        "config_root": str(args.config_root),
        "alias_config": str(args.alias_config),
        "alias_count": len(aliases),
        "config_scan": config_scan,
        "initializer_scan": initializer_scan,
        "migration_blocked": bool(
            config_scan["invalid_contracts"]
            or config_scan["unresolved_runtime_destinations"]
            or initializer_scan["remaining_direct_init_count"]
        ),
    }
    atomic_json(args.output, report)
    invalid_count = len(config_scan["invalid_contracts"])
    unresolved_count = len(config_scan["unresolved_runtime_destinations"])
    print(
        "SWANLAB_CONTRACT_SCAN "
        f"contracts={config_scan['swanlab_contract_count']} invalid={invalid_count} "
        f"unresolved={unresolved_count} "
        f"remaining_direct_init={initializer_scan['remaining_direct_init_count']} output={args.output}"
    )
    return 0 if invalid_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
