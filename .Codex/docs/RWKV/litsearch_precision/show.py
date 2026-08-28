"""只读查看：按路径子串显示笔记的标题、标签、key_finding，用于人工核对相关性判定。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

INVENTORY = Path(__file__).resolve().parent / "notes_inventory.jsonl"


def main(argv: list[str]) -> int:
    records = [json.loads(line) for line in INVENTORY.open(encoding="utf-8")]
    for pattern in argv:
        print(f"\n########## 匹配 {pattern!r} ##########")
        for record in records:
            haystack = record["path"] + " " + str(record["title"])
            if pattern.lower() not in haystack.lower():
                continue
            print(f"\n路径: {record['path']}")
            print(f"标题: {record['title']}")
            print(f"标签: {record['tags']}")
            kf = str(record["key_finding"])
            print(f"要点: {kf[:400]}")
            print(f"正文字数: {record['body_chars']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
