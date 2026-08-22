#!/usr/bin/env python3
"""扫描 JSON/YAML 最终合同，并机械阻断尚未迁移的 SwanLab 入口。"""

from __future__ import annotations

import argparse
import importlib.metadata
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
    parser = argparse.ArgumentParser(description="扫描 JSON/YAML 中的 SwanLab 最终合同")
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
    output = run_checked(["fd", "-e", "json", "-e", "yaml", "-e", "yml", ".", str(root)])
    return sorted(Path(line) for line in output.splitlines() if line.strip())


def load_documents(path: Path) -> tuple[list[object], str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return [json.loads(text)], "json-stdlib"
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise RuntimeError("扫描 YAML 需要锁定依赖 PyYAML 6.0.3") from exc
    actual_version = importlib.metadata.version("pyyaml")
    if actual_version != "6.0.3":
        raise RuntimeError(f"PyYAML 实际版本必须为 6.0.3，当前为 {actual_version}")
    return list(yaml.safe_load_all(text)), f"pyyaml-{actual_version}-safe_load_all"


def tracking_mappings(
    node: object, location: str = "$"
) -> Iterator[tuple[str, str, Mapping[str, object]]]:
    if isinstance(node, Mapping):
        for key, value in node.items():
            child_location = f"{location}.{key}"
            if key in ("swanlab", "tracking") and isinstance(value, Mapping):
                yield child_location, key, value
            yield from tracking_mappings(value, child_location)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from tracking_mappings(value, f"{location}[{index}]")


def final_destination(
    document: object, node_type: str, destination: Mapping[str, object]
) -> tuple[dict[str, object], list[str]]:
    final = dict(destination)
    derived_fields: list[str] = []
    if node_type == "tracking" and "name" not in final and "run_name" in final:
        final["name"] = final["run_name"]
        derived_fields.append("name<-run_name")
    if node_type == "tracking" and "group" not in final and "run_name" in final:
        final["group"] = final["run_name"]
        derived_fields.append("group<-run_name")
    if isinstance(document, Mapping):
        if "name" not in final and "display_name" in document:
            final["name"] = document["display_name"]
            derived_fields.append("name<-$document.display_name")
        if "group" not in final and "run_id" in document:
            final["group"] = document["run_id"]
            derived_fields.append("group<-$document.run_id")
    return final, derived_fields


def scan_configs(
    root: Path,
    aliases: Mapping[str, str],
    authorized_workspace: str | None,
    authorized_project: str | None,
) -> dict[str, object]:
    valid: list[dict[str, object]] = []
    invalid: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []
    files = config_paths(root)
    parser_counts: dict[str, int] = {}
    document_count = 0
    mapping_count = 0
    for path in files:
        try:
            documents, parser_name = load_documents(path)
        except (OSError, json.JSONDecodeError, RuntimeError) as exc:
            invalid.append(
                {
                    "path": str(path),
                    "document_index": None,
                    "location": "$",
                    "node_type": None,
                    "error": str(exc),
                }
            )
            continue
        parser_counts[parser_name] = parser_counts.get(parser_name, 0) + 1
        document_count += len(documents)
        for document_index, document in enumerate(documents):
            for location, node_type, destination in tracking_mappings(document):
                mapping_count += 1
                final, derived_fields = final_destination(document, node_type, destination)
                missing = [
                    field
                    for field in ("workspace", "project", "name", "group", "mode", "tags")
                    if field not in final
                ]
                identity = {
                    "path": str(path),
                    "document_index": document_index,
                    "location": location,
                    "node_type": node_type,
                    "derived_fields": derived_fields,
                }
                if missing:
                    unresolved.append(
                        {
                            **identity,
                            "missing_final_fields": missing,
                            "reason": "静态配置未包含可机械确定的最终 SwanLab 目的地",
                        }
                    )
                    continue
                try:
                    receipt = validate_swanlab_contract(
                        final,
                        aliases=aliases,
                        authorized_workspace=authorized_workspace,
                        authorized_project=authorized_project,
                    )
                except TrackingConfigError as exc:
                    invalid.append({**identity, "error": str(exc)})
                    continue
                valid.append(
                    {
                        **identity,
                        "contract_sha256": receipt["contract_sha256"],
                        "original_tags": receipt["original_tags"],
                        "effective_tags": receipt["effective_tags"],
                        "alias_applications": receipt["alias_applications"],
                        "requested_destination": receipt["requested_destination"],
                        "effective_destination": receipt["effective_destination"],
                    }
                )
    return {
        "config_file_count": len(files),
        "document_count": document_count,
        "tracking_mapping_count": mapping_count,
        "valid_contracts": valid,
        "invalid_contracts": invalid,
        "unresolved_runtime_destinations": unresolved,
        "parser_file_counts": parser_counts,
        "yaml_parser_contract": {
            "package": "PyYAML",
            "locked_version": "6.0.3",
            "api": "yaml.safe_load_all",
        },
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
    migration_blocked = bool(
        config_scan["invalid_contracts"]
        or config_scan["unresolved_runtime_destinations"]
        or initializer_scan["remaining_direct_init_count"]
    )
    report = {
        "schema_version": "swanlab-contract-migration-gate-v2",
        "config_root": str(args.config_root),
        "alias_config": str(args.alias_config),
        "alias_count": len(aliases),
        "config_scan": config_scan,
        "initializer_scan": initializer_scan,
        "migration_blocked": migration_blocked,
        "exit_contract": {"ready": 0, "migration_blocked": 2},
    }
    atomic_json(args.output, report)
    print(
        "SWANLAB_CONTRACT_MIGRATION_GATE "
        f"files={config_scan['config_file_count']} mappings={config_scan['tracking_mapping_count']} "
        f"valid={len(config_scan['valid_contracts'])} "
        f"invalid={len(config_scan['invalid_contracts'])} "
        f"unresolved={len(config_scan['unresolved_runtime_destinations'])} "
        f"remaining_direct_init={initializer_scan['remaining_direct_init_count']} "
        f"migration_blocked={str(migration_blocked).lower()} output={args.output}"
    )
    return 2 if migration_blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
