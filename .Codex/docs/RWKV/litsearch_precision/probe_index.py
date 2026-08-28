"""只读探针：核验索引里到底存了什么，用于诊断精度问题。

不修改任何仓库文件与索引；只做 SELECT 查询与统计。
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
INDEX_PATH = REPO_ROOT / ".cache/literature-search/index.sqlite3"


def main() -> int:
    connection = sqlite3.connect(f"file:{INDEX_PATH}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row

    print("=== 断言 1：frontmatter 的 key_finding / tags 是否进入索引 ===")
    target = "wiki/papers/attack-detection/2023-Han-OWAD正常性漂移适应.md"
    row = connection.execute("SELECT id,title FROM notes WHERE path=?", (target,)).fetchone()
    if row is None:
        print(f"  未找到笔记 {target}")
        return 1
    note_id = int(row["id"])
    print(f"  note_id={note_id} title={row['title']}")

    # key_finding 中的独有短语
    for probe in ("标签节省型批次模型重训", "逐前缀固定维状态和污染影响约束"):
        hits = connection.execute(
            "SELECT COUNT(*) c FROM chunks WHERE note_id=? AND instr(text, ?)>0",
            (note_id, probe),
        ).fetchone()["c"]
        print(f"  正文/索引中含短语 {probe!r} 的分块数：{hits}")

    # tags 中的词
    for tag in ("正常性漂移", "网络入侵检测", "分布适应"):
        hits = connection.execute(
            "SELECT COUNT(*) c FROM chunks WHERE note_id=? AND instr(text, ?)>0",
            (note_id, tag),
        ).fetchone()["c"]
        print(f"  含标签词 {tag!r} 的分块数：{hits}")

    print()
    print("=== 断言 2：第一个分块的开头（看 frontmatter 是否被剥离） ===")
    first = connection.execute(
        "SELECT position,heading,text FROM chunks WHERE note_id=? ORDER BY position LIMIT 1",
        (note_id,),
    ).fetchone()
    print(f"  position={first['position']} heading={first['heading']!r}")
    print("  text[:300]=", repr(str(first["text"])[:300]))

    print()
    print("=== 断言 3：全库是否有任何分块含 'authors:' 或 'key_finding:' 字面量 ===")
    for literal in ("key_finding:", "authors:", "venue:", "tags:"):
        c = connection.execute(
            "SELECT COUNT(*) c FROM chunks WHERE instr(text, ?)>0", (literal,)
        ).fetchone()["c"]
        print(f"  含 {literal!r} 的分块数：{c}")

    print()
    print("=== 断言 4：分块规模统计 ===")
    stats = connection.execute(
        "SELECT COUNT(*) n, AVG(LENGTH(text)) avg_len, MIN(LENGTH(text)) min_len, "
        "MAX(LENGTH(text)) max_len FROM chunks"
    ).fetchone()
    print(
        f"  分块数={stats['n']} 平均字符={stats['avg_len']:.1f} "
        f"最短={stats['min_len']} 最长={stats['max_len']}"
    )
    per_note = connection.execute(
        "SELECT AVG(c) avg_c, MIN(c) min_c, MAX(c) max_c FROM "
        "(SELECT COUNT(*) c FROM chunks GROUP BY note_id)"
    ).fetchone()
    print(
        f"  每篇分块数：平均={per_note['avg_c']:.1f} 最少={per_note['min_c']} "
        f"最多={per_note['max_c']}"
    )

    print()
    print("=== 断言 5：向量数 ===")
    v = connection.execute(
        "SELECT COUNT(*) c FROM chunks WHERE embedding IS NOT NULL"
    ).fetchone()["c"]
    print(f"  已写入向量的分块数：{v}")

    connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
