#!/usr/bin/env python3
"""将 P2 技能裁剪候选安全合并到 Codex 用户配置。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path


SKILL_HEADER = re.compile(r"^\[\[skills\.config\]\]\s*$")
PLUGIN_HEADER = re.compile(r'^\[plugins\."([^"]+)"\]\s*$')
ANY_HEADER = re.compile(r"^\s*\[")
SKILL_PATH = re.compile(r'^path = "([^"]+/SKILL\.md)"\s*$')
ENABLED = re.compile(r"^enabled = (true|false)\s*$")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def section_blocks(text: str, header: re.Pattern[str]) -> list[list[str]]:
    lines = text.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if header.match(line.rstrip("\n"))]
    blocks: list[list[str]] = []
    for start in starts:
        end = start + 1
        while end < len(lines) and not ANY_HEADER.match(lines[end]):
            end += 1
        blocks.append(lines[start:end])
    return blocks


def parse_skills(text: str, source: str) -> dict[str, bool]:
    skills: dict[str, bool] = {}
    for block in section_blocks(text, SKILL_HEADER):
        path_matches = [SKILL_PATH.match(line.rstrip("\n")) for line in block]
        enabled_matches = [ENABLED.match(line.rstrip("\n")) for line in block]
        paths = [match.group(1) for match in path_matches if match]
        states = [match.group(1) == "true" for match in enabled_matches if match]
        if len(paths) != 1 or len(states) != 1:
            raise ValueError(f"{source} 中存在无法唯一解析的 skills.config 块")
        if paths[0] in skills:
            raise ValueError(f"{source} 中存在重复技能路径：{paths[0]}")
        skills[paths[0]] = states[0]
    return skills


def parse_plugins(text: str, source: str) -> dict[str, bool]:
    plugins: dict[str, bool] = {}
    for block in section_blocks(text, PLUGIN_HEADER):
        header = PLUGIN_HEADER.match(block[0].rstrip("\n"))
        states = [
            match.group(1) == "true"
            for line in block
            if (match := ENABLED.match(line.rstrip("\n")))
        ]
        if header is None or len(states) != 1:
            raise ValueError(f"{source} 中存在无法唯一解析的插件块")
        name = header.group(1)
        if name in plugins:
            raise ValueError(f"{source} 中存在重复插件表：{name}")
        plugins[name] = states[0]
    return plugins


def update_plugins(base: str, overlay: dict[str, bool]) -> tuple[str, list[str]]:
    lines = base.splitlines(keepends=True)
    current: str | None = None
    changed: list[str] = []
    seen: set[str] = set()

    for index, line in enumerate(lines):
        stripped = line.rstrip("\n")
        plugin_match = PLUGIN_HEADER.match(stripped)
        if plugin_match:
            current = plugin_match.group(1)
            continue
        if ANY_HEADER.match(line):
            current = None
            continue
        if current not in overlay:
            continue
        enabled_match = ENABLED.match(stripped)
        if not enabled_match:
            continue
        if current in seen:
            raise ValueError(f"主配置插件 {current} 存在多个 enabled 字段")
        seen.add(current)
        desired = overlay[current]
        current_state = enabled_match.group(1) == "true"
        if current_state != desired:
            newline = "\n" if line.endswith("\n") else ""
            lines[index] = f"enabled = {str(desired).lower()}{newline}"
            changed.append(current)

    missing = sorted(set(overlay) - seen)
    if missing:
        suffix = "" if not lines or lines[-1].endswith("\n") else "\n"
        lines.append(suffix)
        lines.append("\n# P2 毕业论文作用域插件裁剪\n")
        for name in missing:
            lines.append(f'[plugins."{name}"]\n')
            lines.append(f"enabled = {str(overlay[name]).lower()}\n\n")
            changed.append(name)

    return "".join(lines), sorted(changed)


def append_missing_skills(
    base: str, base_skills: dict[str, bool], overlay_skills: dict[str, bool]
) -> tuple[str, list[str]]:
    for path in sorted(set(base_skills) & set(overlay_skills)):
        if base_skills[path] != overlay_skills[path]:
            raise ValueError(f"技能状态冲突，拒绝自动覆盖：{path}")

    missing = sorted(set(overlay_skills) - set(base_skills))
    if not missing:
        return base, []

    chunks = [base]
    if base and not base.endswith("\n"):
        chunks.append("\n")
    chunks.append("\n# P2 毕业论文作用域技能裁剪\n")
    for path in missing:
        chunks.extend(
            [
                "[[skills.config]]\n",
                f'path = "{path}"\n',
                f"enabled = {str(overlay_skills[path]).lower()}\n\n",
            ]
        )
    return "".join(chunks), missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    base = args.base.read_text(encoding="utf-8")
    overlay = args.overlay.read_text(encoding="utf-8")
    base_skills = parse_skills(base, "主配置")
    overlay_skills = parse_skills(overlay, "P2 候选")
    overlay_plugins = parse_plugins(overlay, "P2 候选")

    if any(overlay_skills.values()) or any(overlay_plugins.values()):
        raise ValueError("P2 候选只能包含 enabled = false 的裁剪项")

    merged, changed_plugins = update_plugins(base, overlay_plugins)
    merged, added_skills = append_missing_skills(
        merged, base_skills, overlay_skills
    )
    final_skills = parse_skills(merged, "合并候选")
    final_plugins = parse_plugins(merged, "合并候选")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(merged, encoding="utf-8")
    os.chmod(args.output, 0o600)

    summary = {
        "base_sha256": sha256_text(base),
        "merged_sha256": sha256_text(merged),
        "base_skill_entries": len(base_skills),
        "overlay_skill_entries": len(overlay_skills),
        "added_skill_entries": len(added_skills),
        "final_skill_entries": len(final_skills),
        "changed_plugins": changed_plugins,
        "final_disabled_candidate_plugins": sorted(
            name for name in overlay_plugins if final_plugins.get(name) is False
        ),
        "added_skill_paths": added_skills,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"新增技能禁用项 {len(added_skills)} 个，变更插件 {len(changed_plugins)} 个，"
        f"最终技能配置项 {len(final_skills)} 个。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
