#!/usr/bin/env python3
"""生成 Skills P0 清单、重复分组和 P1 候选。"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - 仅兼容旧 Python
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None


AGENTS_ROOT = Path("/Users/bilibili/.agents/skills")
CODEX_ROOT = Path("/Users/bilibili/.codex/skills")
ACTIVE_LINE_RE = re.compile(
    r"^- (?P<name>[A-Za-z0-9_.-]+(?::[A-Za-z0-9_.-]+)*): "
    r"(?P<description>.*) \(file: (?P<path>.+)\)$"
)
ROOT_LINE_RE = re.compile(r"^- `(?P<alias>r\d+)` = `(?P<root>.+)`$")
FIELD_RE = re.compile(r"^(?P<key>[A-Za-z0-9_-]+):(?:\s*(?P<value>.*))?$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_scalar(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if value[0] in {'"', "'"}:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value.strip("\"'")
        return str(parsed)
    return value


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {
            "valid": False,
            "name": path.parent.name,
            "description": "",
            "error": "缺少起始 frontmatter 分隔符",
        }

    try:
        end = next(
            index for index in range(1, len(lines)) if lines[index].strip() == "---"
        )
    except StopIteration:
        return {
            "valid": False,
            "name": path.parent.name,
            "description": "",
            "error": "缺少结束 frontmatter 分隔符",
        }

    metadata: dict[str, str] = {}
    index = 1
    while index < end:
        match = FIELD_RE.match(lines[index])
        if not match:
            index += 1
            continue
        key = match.group("key")
        value = (match.group("value") or "").strip()
        if value in {">", ">-", "|", "|-"}:
            block: list[str] = []
            index += 1
            while index < end and (not lines[index] or lines[index][0].isspace()):
                block.append(lines[index].strip())
                index += 1
            metadata[key] = (
                " ".join(part for part in block if part)
                if value.startswith(">")
                else "\n".join(block).strip()
            )
            continue
        metadata[key] = parse_scalar(value)
        index += 1

    return {
        "valid": True,
        "name": metadata.get("name") or path.parent.name,
        "description": metadata.get("description", ""),
        "error": None,
    }


def source_details(path: Path) -> tuple[str, str | None]:
    if path.is_relative_to(AGENTS_ROOT):
        relative = path.relative_to(AGENTS_ROOT)
        return "user_agents", relative.parts[0] if len(relative.parts) == 2 else None
    if path.is_relative_to(CODEX_ROOT):
        relative = path.relative_to(CODEX_ROOT)
        directory_key = relative.parts[0] if len(relative.parts) == 2 else None
        return "legacy_codex", directory_key
    return "other", None


def load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if tomllib is None:
        raise RuntimeError("当前 Python 缺少 tomllib，无法安全解析配置")
    with path.open("rb") as stream:
        return tomllib.load(stream)


def sanitize_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    config = load_toml(path)
    skills = config.get("skills", {}).get("config", [])
    plugins = config.get("plugins", {})
    return {
        "exists": True,
        "path": str(path),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "skills_config": [
            {"path": item.get("path"), "enabled": item.get("enabled", True)}
            for item in skills
            if isinstance(item, dict)
        ],
        "plugins": {
            name: {"enabled": value.get("enabled", True)}
            for name, value in plugins.items()
            if isinstance(value, dict)
        },
    }


def parse_active_index(path: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    if not path.exists():
        return entries
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    roots = {
        match.group("alias"): match.group("root")
        for line in lines
        if (match := ROOT_LINE_RE.match(line))
    }
    for line in lines:
        match = ACTIVE_LINE_RE.match(line)
        if match:
            entry = match.groupdict()
            raw_path = entry["path"]
            alias, separator, relative = raw_path.partition("/")
            entry["raw_path"] = raw_path
            entry["root_alias"] = alias if alias in roots else ""
            if separator and alias in roots:
                entry["path"] = str(Path(roots[alias]) / relative)
            entries.append(entry)
    return entries


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", type=Path, required=True)
    parser.add_argument("--active-index", type=Path, required=True)
    parser.add_argument("--user-config", type=Path, required=True)
    parser.add_argument("--project-config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    active_entries = parse_active_index(args.active_index)
    active_paths = {entry["path"] for entry in active_entries}
    user_config = sanitize_config(args.user_config)
    project_config = sanitize_config(args.project_config)
    user_skill_settings = {
        item["path"]: item["enabled"] for item in user_config.get("skills_config", [])
    }
    project_skill_settings = {
        item["path"]: item["enabled"]
        for item in project_config.get("skills_config", [])
    }

    skill_paths = [
        Path(line)
        for line in args.paths.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    inventory: list[dict[str, Any]] = []
    keyed_by_source: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)

    for skill_path in sorted(skill_paths, key=str):
        metadata = parse_frontmatter(skill_path)
        source, directory_key = source_details(skill_path)
        record = {
            "name": metadata["name"],
            "description": metadata["description"],
            "path": str(skill_path),
            "source": source,
            "directory_key": directory_key,
            "sha256": sha256(skill_path),
            "bytes": skill_path.stat().st_size,
            "frontmatter_valid": metadata["valid"],
            "frontmatter_error": metadata["error"],
            "active_index": str(skill_path) in active_paths,
            "user_config_enabled": user_skill_settings.get(str(skill_path)),
            "project_config_enabled": project_skill_settings.get(str(skill_path)),
        }
        inventory.append(record)
        if directory_key is not None:
            keyed_by_source[source][directory_key] = record

    shared_keys = sorted(
        set(keyed_by_source["user_agents"]) & set(keyed_by_source["legacy_codex"])
    )
    duplicate_groups: list[dict[str, Any]] = []
    p1_candidates: list[dict[str, Any]] = []
    for key in shared_keys:
        agents_record = keyed_by_source["user_agents"][key]
        codex_record = keyed_by_source["legacy_codex"][key]
        identical = agents_record["sha256"] == codex_record["sha256"]
        group = {
            "directory_key": key,
            "classification": "identical" if identical else "different",
            "same_declared_name": agents_record["name"] == codex_record["name"],
            "user_agents": agents_record,
            "legacy_codex": codex_record,
        }
        duplicate_groups.append(group)
        if not identical:
            continue

        agents_disabled = agents_record["user_config_enabled"] is False
        codex_disabled = codex_record["user_config_enabled"] is False
        if agents_disabled and codex_disabled:
            action = "blocked_both_disabled"
            canonical = None
            disabled = None
        elif agents_disabled:
            action = "already_deduplicated_user_config"
            canonical = codex_record["path"]
            disabled = agents_record["path"]
        elif codex_disabled:
            action = "already_deduplicated_user_config"
            canonical = agents_record["path"]
            disabled = codex_record["path"]
        else:
            action = "disable_legacy_codex_in_project"
            canonical = agents_record["path"]
            disabled = codex_record["path"]
        p1_candidates.append(
            {
                "directory_key": key,
                "sha256": agents_record["sha256"],
                "action": action,
                "canonical_path": canonical,
                "disabled_path": disabled,
                "canonical_active_before": (
                    canonical in active_paths if canonical else False
                ),
                "disabled_active_before": (
                    disabled in active_paths if disabled else False
                ),
                "reason": (
                    "尊重既有用户配置，当前已只保留一个来源"
                    if action == "already_deduplicated_user_config"
                    else "两份内容逐字节相同，保留当前官方用户目录副本"
                ),
            }
        )

    config_state = {
        "user": user_config,
        "project": project_config,
    }
    summary = {
        "inventory_count": len(inventory),
        "active_index_count": len(active_entries),
        "active_local_inventory_count": sum(item["active_index"] for item in inventory),
        "cross_root_duplicate_groups": len(duplicate_groups),
        "identical_groups": sum(
            group["classification"] == "identical" for group in duplicate_groups
        ),
        "different_groups": sum(
            group["classification"] == "different" for group in duplicate_groups
        ),
        "p1_project_disable_count": sum(
            item["action"] == "disable_legacy_codex_in_project"
            for item in p1_candidates
        ),
        "p1_already_deduplicated_count": sum(
            item["action"] == "already_deduplicated_user_config"
            for item in p1_candidates
        ),
        "p1_blocked_count": sum(
            item["action"] == "blocked_both_disabled" for item in p1_candidates
        ),
        "invalid_frontmatter_count": sum(
            not item["frontmatter_valid"] for item in inventory
        ),
    }

    write_json(output_dir / "skills-inventory.json", inventory)
    write_json(output_dir / "active-index.json", active_entries)
    write_json(output_dir / "duplicate-groups.json", duplicate_groups)
    write_json(output_dir / "p1-candidates.json", p1_candidates)
    write_json(output_dir / "config-state.json", config_state)
    write_json(output_dir / "summary.json", summary)

    with (output_dir / "skills-inventory.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "name",
                "description",
                "source",
                "directory_key",
                "path",
                "sha256",
                "bytes",
                "active_index",
                "user_config_enabled",
                "project_config_enabled",
            ],
            delimiter="\t",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(inventory)

    markdown = [
        "# P0 重复技能分组",
        "",
        "| 目录键 | 分类 | `.agents` 路径 | `.codex` 路径 | SHA-256 | P1 动作 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    p1_by_key = {item["directory_key"]: item for item in p1_candidates}
    for group in duplicate_groups:
        candidate = p1_by_key.get(group["directory_key"])
        markdown.append(
            "| {key} | {classification} | `{agents}` | `{codex}` | `{digest}` | {action} |".format(
                key=group["directory_key"],
                classification=group["classification"],
                agents=group["user_agents"]["path"],
                codex=group["legacy_codex"]["path"],
                digest=(
                    group["user_agents"]["sha256"]
                    if group["classification"] == "identical"
                    else "不同"
                ),
                action=candidate["action"] if candidate else "P1 禁止处理",
            )
        )
    (output_dir / "duplicate-groups.md").write_text(
        "\n".join(markdown) + "\n", encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
