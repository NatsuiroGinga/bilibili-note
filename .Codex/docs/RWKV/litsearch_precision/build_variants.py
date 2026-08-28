"""构建改进变体索引，用于在同一真实测试集上与基线做对照实验。

不修改 scripts/literature_search 下任何生产文件，只复用其函数；
变体索引写到独立路径，不覆盖默认索引。

变体：
  V1  排除 MOC 导航页（INDEX.md）
  V2  把 frontmatter 的 tags / key_finding / venue / authors 作为元数据段并入正文
  V3  V1 + V2
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from scripts.literature_search.config import load_config  # noqa: E402
from scripts.literature_search.documents import (  # noqa: E402
    chunk_note,
    load_notes,
    source_manifest_hash,
)
from scripts.literature_search.storage import (  # noqa: E402
    connect,
    initialize,
    insert_documents,
    set_metadata,
)
from scripts.literature_search.types import NoteDocument  # noqa: E402

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
# 元数据段里保留的字段，按对检索有用的顺序排列
METADATA_FIELDS = ("tags", "key_finding", "venue", "authors", "year", "aliases")


def parse_full_frontmatter(text: str) -> dict:
    """解析 frontmatter，支持单行标量、缩进列表与内联数组三种写法。"""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, object] = {}
    current_key: Optional[str] = None
    for line in match.group(1).splitlines():
        list_item = re.match(r"^\s+-\s+(.*)$", line)
        if list_item and current_key is not None:
            value = list_item.group(1).strip().strip("\"'")
            bucket = fields.setdefault(current_key, [])
            if isinstance(bucket, list):
                bucket.append(value)
            continue
        scalar = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if scalar:
            key, raw = scalar.group(1), scalar.group(2).strip()
            if not raw:
                fields[key] = []
                current_key = key
                continue
            if raw.startswith("[") and raw.endswith("]"):
                fields[key] = [
                    piece.strip().strip("\"'")
                    for piece in raw[1:-1].split(",")
                    if piece.strip()
                ]
            else:
                fields[key] = raw.strip("\"'")
            current_key = None
    return fields


def metadata_section(fields: dict) -> str:
    """把 frontmatter 关键字段渲染成一个可检索的正文小节。"""
    lines: List[str] = []
    for key in METADATA_FIELDS:
        value = fields.get(key)
        if not value:
            continue
        if isinstance(value, list):
            rendered = "、".join(str(item) for item in value if str(item).strip())
        else:
            rendered = str(value)
        if not rendered.strip():
            continue
        lines.append(f"{key}：{rendered}")
    if not lines:
        return ""
    return "## 条目元数据\n\n" + "\n".join(lines) + "\n\n"


def is_navigation_page(note: NoteDocument) -> bool:
    """MOC 导航页判定：文件名为 INDEX.md。"""
    return note.relative_path.rsplit("/", 1)[-1] == "INDEX.md"


def prepare_notes(
    repo_root: Path, pattern: str, drop_navigation: bool, add_metadata: bool
) -> List[NoteDocument]:
    notes = load_notes(repo_root, pattern)
    prepared: List[NoteDocument] = []
    for note in notes:
        if drop_navigation and is_navigation_page(note):
            continue
        if add_metadata:
            raw = note.path.read_text(encoding="utf-8", errors="replace")
            section = metadata_section(parse_full_frontmatter(raw))
            if section:
                note = replace(note, body=(section + note.body).strip())
        prepared.append(note)
    return prepared


def build(
    index_path: Path, drop_navigation: bool, add_metadata: bool
) -> dict:
    config = load_config()
    started = time.monotonic()
    notes = prepare_notes(REPO_ROOT, config.input_glob, drop_navigation, add_metadata)
    if not notes:
        raise RuntimeError("没有可索引的笔记")
    chunks = [
        chunk
        for position, note in enumerate(notes)
        for chunk in chunk_note(
            note, position, config.chunk_max_chars, config.chunk_overlap_chars
        )
    ]
    index_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = index_path.with_suffix(index_path.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    connection = connect(temporary)
    try:
        initialize(connection)
        insert_documents(connection, notes, chunks)
        metadata = {
            "schema_version": config.schema_version,
            "built_at": datetime.now(timezone.utc).isoformat(),
            "build_seconds": round(time.monotonic() - started, 3),
            "source_manifest_hash": source_manifest_hash(notes),
            "note_count": len(notes),
            "chunk_count": len(chunks),
            "vector_count": 0,
            "vector_dimension": 0,
            "model_name": config.model_name,
            "model_revision": config.model_revision,
            "config": config.to_dict(),
            "variant_drop_navigation": drop_navigation,
            "variant_add_metadata": add_metadata,
        }
        set_metadata(connection, metadata)
        connection.commit()
    except Exception:
        connection.close()
        if temporary.exists():
            temporary.unlink()
        raise
    connection.close()
    os.replace(temporary, index_path)
    metadata["index_path"] = str(index_path)
    metadata["index_bytes"] = index_path.stat().st_size
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--variant", required=True, choices=["V1", "V2", "V3"]
    )
    parser.add_argument("--out-dir", default=str(REPO_ROOT / ".cache/literature-search"))
    arguments = parser.parse_args()

    settings = {
        "V1": (True, False),
        "V2": (False, True),
        "V3": (True, True),
    }[arguments.variant]
    target = Path(arguments.out_dir) / f"index_{arguments.variant}.sqlite3"
    metadata = build(target, *settings)
    print(
        f"{arguments.variant}: 笔记={metadata['note_count']} 分块={metadata['chunk_count']} "
        f"耗时={metadata['build_seconds']}s 大小={metadata['index_bytes']}B\n  -> {target}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
