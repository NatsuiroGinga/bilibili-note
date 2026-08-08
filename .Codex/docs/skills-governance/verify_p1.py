#!/usr/bin/env python3
"""验证 Skills-P1 隔离档案没有越过授权边界。"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 兼容。
    import tomli as tomllib


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def divergent_projection(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    projection = []
    for group in groups:
        if group["classification"] != "different":
            continue
        projection.append(
            {
                "directory_key": group["directory_key"],
                "classification": group["classification"],
                "user_agents": {
                    key: group["user_agents"][key]
                    for key in (
                        "path",
                        "sha256",
                        "bytes",
                        "active_index",
                        "user_config_enabled",
                    )
                },
                "legacy_codex": {
                    key: group["legacy_codex"][key]
                    for key in (
                        "path",
                        "sha256",
                        "bytes",
                        "active_index",
                        "user_config_enabled",
                    )
                },
            }
        )
    return projection


def stable_plugins(payload: dict[str, Any]) -> list[dict[str, Any]]:
    fields = (
        "pluginId",
        "version",
        "installed",
        "enabled",
        "installPolicy",
        "authPolicy",
    )
    return sorted(
        ({key: plugin.get(key) for key in fields} for plugin in payload["installed"]),
        key=lambda item: item["pluginId"],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p0-dir", type=Path, required=True)
    parser.add_argument("--p1-audit-dir", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--user-config", type=Path, required=True)
    parser.add_argument("--expected-user-config-sha256", required=True)
    parser.add_argument("--project-config", type=Path, required=True)
    parser.add_argument("--explicit-message", type=Path, required=True)
    parser.add_argument("--plugin-before", type=Path, required=True)
    parser.add_argument("--plugin-after", type=Path, required=True)
    parser.add_argument("--marketplaces-before", type=Path, required=True)
    parser.add_argument("--marketplaces-after", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    p0_summary = load_json(args.p0_dir / "summary.json")
    p1_summary = load_json(args.p1_audit_dir / "summary.json")
    p0_inventory = load_json(args.p0_dir / "skills-inventory.json")
    p1_inventory = load_json(args.p1_audit_dir / "skills-inventory.json")
    p0_groups = load_json(args.p0_dir / "duplicate-groups.json")
    p1_groups = load_json(args.p1_audit_dir / "duplicate-groups.json")
    candidates = load_json(args.p0_dir / "p1-candidates.json")

    profile_data = tomllib.loads(args.profile.read_text(encoding="utf-8"))
    profile_entries = profile_data["skills"]["config"]
    disabled_paths = {entry["path"] for entry in profile_entries}
    expected_disabled_paths = {
        item["disabled_path"]
        for item in candidates
        if item["action"] == "disable_legacy_codex_in_project"
    }

    p0_hashes = {item["path"]: item["sha256"] for item in p0_inventory}
    p1_hashes = {item["path"]: item["sha256"] for item in p1_inventory}
    identical_groups = [
        group for group in p1_groups if group["classification"] == "identical"
    ]
    one_active_per_identical_group = all(
        sum(
            bool(group[source]["active_index"])
            for source in ("user_agents", "legacy_codex")
        )
        == 1
        for group in identical_groups
    )

    explicit_message = load_json(args.explicit_message)
    expected_explicit = {
        "planning-with-files": (
            "/Users/bilibili/.agents/skills/planning-with-files/SKILL.md"
        ),
        "results-analysis": (
            "/Users/bilibili/.agents/skills/results-analysis/SKILL.md"
        ),
        "nature-data": "/Users/bilibili/.agents/skills/nature-data/SKILL.md",
    }

    plugin_before = load_json(args.plugin_before)
    plugin_after = load_json(args.plugin_after)
    marketplaces_before = load_json(args.marketplaces_before)
    marketplaces_after = load_json(args.marketplaces_after)

    checks = {
        "inventory_count_unchanged": (
            p0_summary["inventory_count"] == p1_summary["inventory_count"] == 175
        ),
        "all_skill_file_hashes_unchanged": p0_hashes == p1_hashes,
        "active_count_reduced_by_13": (
            p0_summary["active_index_count"] == 134
            and p1_summary["active_index_count"] == 121
        ),
        "profile_has_exactly_13_unique_entries": (
            len(profile_entries) == len(disabled_paths) == 13
        ),
        "profile_entries_all_disabled": all(
            entry.get("enabled") is False for entry in profile_entries
        ),
        "profile_paths_match_p1_candidates": disabled_paths == expected_disabled_paths,
        "twenty_identical_groups_have_one_active_source": (
            len(identical_groups) == 20 and one_active_per_identical_group
        ),
        "seventeen_divergent_groups_unchanged": (
            len(divergent_projection(p0_groups)) == 17
            and divergent_projection(p0_groups) == divergent_projection(p1_groups)
        ),
        "explicit_skill_invocation_resolves_canonical_paths": (
            explicit_message == expected_explicit
        ),
        "plugin_install_enable_policy_unchanged": (
            stable_plugins(plugin_before) == stable_plugins(plugin_after)
        ),
        "plugin_marketplace_set_unchanged": marketplaces_before == marketplaces_after,
        "user_config_restored": (
            sha256(args.user_config) == args.expected_user_config_sha256
        ),
        "project_config_absent": not args.project_config.exists(),
        "profile_permissions_are_0600": stat.S_IMODE(args.profile.stat().st_mode)
        == 0o600,
    }

    result = {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "counts": {
            "inventory": p1_summary["inventory_count"],
            "active_before": p0_summary["active_index_count"],
            "active_after": p1_summary["active_index_count"],
            "identical_groups": p1_summary["identical_groups"],
            "divergent_groups": p1_summary["different_groups"],
            "profile_entries": len(profile_entries),
        },
        "notes": {
            "plugin_exact_json_equal": plugin_before == plugin_after,
            "plugin_exact_json_difference": (
                "市场查询刷新了 chrome-devtools-mcp 的来源提交哈希；"
                "插件安装、启用、版本与策略未变。"
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if result["status"] != "passed":
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"P1 验收失败：{', '.join(failed)}")


if __name__ == "__main__":
    main()
