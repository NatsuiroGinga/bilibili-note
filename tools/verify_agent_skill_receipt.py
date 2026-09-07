#!/usr/bin/env python3
"""只读验证编码代理 Skill 收据，不执行被收据列出的命令。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def required_string(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"缺少非空字段：{field}")


def validate(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("task", "agent", "model", "effort", "status"):
        required_string(receipt.get(field), field, errors)
    skills = receipt.get("required_skills")
    if not isinstance(skills, list) or not skills:
        errors.append("required_skills 必须是非空列表")
    else:
        for index, skill in enumerate(skills):
            if not isinstance(skill, dict):
                errors.append(f"required_skills[{index}] 必须是对象"); continue
            for field in ("name", "path", "sha256", "read_at"):
                required_string(skill.get(field), f"required_skills[{index}].{field}", errors)
            path = Path(skill.get("path", ""))
            if path.is_file() and isinstance(skill.get("sha256"), str) and sha256(path) != skill["sha256"]:
                errors.append(f"Skill 哈希漂移：{path}")
            elif not path.is_file():
                errors.append(f"Skill 路径不可读：{path}")
            checklist = skill.get("checklist")
            if not isinstance(checklist, list) or not checklist:
                errors.append(f"required_skills[{index}].checklist 必须非空")
            elif any(not isinstance(item, dict) or not str(item.get("item", "")).strip() or not str(item.get("evidence", "")).strip() for item in checklist):
                errors.append(f"required_skills[{index}].checklist 缺少 item/evidence")
    owned = receipt.get("owned_files"); changed = receipt.get("actual_changed_files")
    if not isinstance(owned, list) or not all(isinstance(item, str) and item for item in owned): errors.append("owned_files 必须是字符串列表")
    if not isinstance(changed, list) or not all(isinstance(item, str) and item for item in changed): errors.append("actual_changed_files 必须是字符串列表")
    elif isinstance(owned, list) and not set(changed).issubset(set(owned)): errors.append("actual_changed_files 含越权文件")
    checks = receipt.get("verification")
    if not isinstance(checks, list) or not checks: errors.append("verification 必须非空")
    elif any(not isinstance(item, dict) or not str(item.get("command", "")).strip() or item.get("exit_code") != 0 for item in checks): errors.append("verification 缺命令或存在非零退出码")
    run = receipt.get("real_run")
    if not isinstance(run, dict) or not isinstance(run.get("applicable"), bool): errors.append("real_run 必须含 applicable 布尔值")
    elif not run["applicable"] and not str(run.get("reason", "")).strip(): errors.append("不适用真实运行须说明原因")
    elif run["applicable"] and not run.get("evidence"): errors.append("适用真实运行须给 evidence")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--receipt", required=True, type=Path); args = parser.parse_args()
    try: receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error: print(f"收据不可读：{error}"); return 2
    errors = validate(receipt)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
