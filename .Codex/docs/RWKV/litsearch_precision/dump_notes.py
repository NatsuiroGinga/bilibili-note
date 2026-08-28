"""只读导出：把 wiki/papers 下每篇笔记的标题、标签、key_finding 导出为 TSV，
供人工构造检索测试集时挑选与核对。不修改任何笔记。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
OUT_PATH = Path(__file__).resolve().parent / "notes_inventory.jsonl"

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)


def parse_full_frontmatter(text: str) -> tuple[dict, str]:
    """解析 frontmatter，支持单行标量与 YAML 列表两种形式。"""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    fields: dict[str, object] = {}
    current_key: str | None = None
    for line in match.group(1).splitlines():
        list_item = re.match(r"^\s+-\s+(.*)$", line)
        if list_item and current_key is not None:
            value = list_item.group(1).strip().strip("\"'")
            fields.setdefault(current_key, [])
            if isinstance(fields[current_key], list):
                fields[current_key].append(value)
            continue
        scalar = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if scalar:
            key, raw = scalar.group(1), scalar.group(2).strip()
            if not raw:
                fields[key] = []
                current_key = key
                continue
            if raw.startswith("[") and raw.endswith("]"):
                # 内联 YAML 数组：tags: [类型/论文, 主题/xxx]
                fields[key] = [
                    piece.strip().strip("\"'")
                    for piece in raw[1:-1].split(",")
                    if piece.strip()
                ]
            else:
                fields[key] = raw.strip("\"'")
            current_key = None
    return fields, text[match.end() :]


def main() -> int:
    records = []
    for path in sorted(REPO_ROOT.glob("wiki/papers/**/*.md")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        fields, body = parse_full_frontmatter(text)
        heading = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
        records.append(
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "title": fields.get("title") or (heading.group(1) if heading else path.stem),
                "year": fields.get("year"),
                "venue": fields.get("venue"),
                "tags": fields.get("tags", []),
                "key_finding": fields.get("key_finding", ""),
                "body_chars": len(body),
            }
        )
    with OUT_PATH.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"导出 {len(records)} 篇 -> {OUT_PATH}")

    # 统计 frontmatter 字段覆盖率，用于评估「索引 frontmatter」这项改进的潜在收益
    with_tags = sum(1 for r in records if r["tags"])
    with_kf = sum(1 for r in records if r["key_finding"])
    with_venue = sum(1 for r in records if r["venue"])
    total = len(records)
    print(f"有 tags 的笔记：{with_tags}/{total} = {with_tags / total:.1%}")
    print(f"有 key_finding 的笔记：{with_kf}/{total} = {with_kf / total:.1%}")
    print(f"有 venue 的笔记：{with_venue}/{total} = {with_venue / total:.1%}")
    tag_chars = sum(len("".join(r["tags"])) for r in records)
    kf_chars = sum(len(str(r["key_finding"])) for r in records)
    print(f"被排除在索引外的 tags 总字符：{tag_chars}")
    print(f"被排除在索引外的 key_finding 总字符：{kf_chars}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
