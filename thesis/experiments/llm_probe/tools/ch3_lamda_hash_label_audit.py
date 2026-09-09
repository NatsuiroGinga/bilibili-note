#!/usr/bin/env python3
"""用 CPU 审计 LAMDA 的跨年份哈希重复与标签时序，不读取特征列。"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


PROJECTED_COLUMNS = ["hash", "label", "year_month"]
SPLIT_BITS = {"train": 1, "test": 2}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=65_536)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def discover_files(data_root: Path) -> list[tuple[int, str, Path]]:
    files: list[tuple[int, str, Path]] = []
    for path in sorted((data_root / "Baseline").glob("*/*_*.parquet")):
        try:
            year = int(path.parent.name)
        except ValueError as exc:
            raise ValueError(f"年度目录不是整数：{path}") from exc
        stem = path.stem
        if stem.endswith("_train"):
            split = "train"
        elif stem.endswith("_test"):
            split = "test"
        else:
            raise ValueError(f"无法识别切分：{path}")
        files.append((year, split, path))
    files.sort(key=lambda item: (item[0], SPLIT_BITS[item[1]]))
    return files


def update_state(
    state: list[Any],
    *,
    year: int,
    split: str,
    label: int,
    year_bit: int,
) -> None:
    label_bit = 1 << label
    if state is None:
        raise AssertionError("状态不应为空")
    if state[0] & year_bit == 0 and state[0] != 0:
        state[6] |= state[5]
        state[4] = year
        state[5] = label_bit
        if state[6] & 1 and label_bit == 2 or state[6] & 2 and label_bit == 1:
            state[7] = True
    else:
        if state[5] and state[5] != label_bit:
            state[8] = True
        state[5] |= label_bit
    state[0] |= year_bit
    state[1] |= SPLIT_BITS[split]
    state[2] |= label_bit
    state[3] += 1


def audit(data_root: Path, output_dir: Path, batch_size: int) -> dict[str, Any]:
    started = time.monotonic()
    manifest_path = data_root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"缺少数据清单：{manifest_path}")
    manifest_sha256 = sha256_file(manifest_path)
    files = discover_files(data_root)
    if not files:
        raise FileNotFoundError(f"未找到年度 Parquet：{data_root / 'Baseline'}")

    years = sorted({year for year, _, _ in files})
    year_bits = {year: 1 << index for index, year in enumerate(years)}
    hash_state: dict[str, list[Any]] = {}
    train_hashes: dict[int, set[str]] = {}
    test_hashes: dict[int, set[str]] = {}
    per_file: list[dict[str, Any]] = []
    total_rows = 0
    nonnull_hash_rows = 0
    null_hash_rows = 0
    invalid_label_rows = 0
    null_month_rows = 0
    year_month_mismatch_rows = 0
    month_values: dict[int, set[str]] = {year: set() for year in years}
    duplicate_rows_within_file = 0

    for year, split, path in files:
        schema_names = set(pq.read_schema(path).names)
        missing = sorted(set(PROJECTED_COLUMNS) - schema_names)
        if missing:
            raise ValueError(f"{path} 缺少审计字段：{missing}")
        file_hashes: set[str] = set()
        file_rows = 0
        file_null_hash_rows = 0
        file_invalid_label_rows = 0
        parquet_file = pq.ParquetFile(path)
        for batch in parquet_file.iter_batches(
            batch_size=batch_size,
            columns=PROJECTED_COLUMNS,
            use_threads=False,
        ):
            hashes = batch.column(0).to_pylist()
            labels = batch.column(1).to_pylist()
            months = batch.column(2).to_pylist()
            for raw_hash, raw_label, raw_month in zip(hashes, labels, months):
                file_rows += 1
                total_rows += 1
                if raw_hash is None:
                    null_hash_rows += 1
                    file_null_hash_rows += 1
                    continue
                hash_value = str(raw_hash)
                nonnull_hash_rows += 1
                file_hashes.add(hash_value)
                if raw_label not in (0, 1):
                    invalid_label_rows += 1
                    file_invalid_label_rows += 1
                    continue
                label = int(raw_label)
                if raw_month is None:
                    null_month_rows += 1
                else:
                    month = str(raw_month)
                    month_values[year].add(month)
                    if not month.startswith(f"{year}-"):
                        year_month_mismatch_rows += 1
                state = hash_state.setdefault(
                    hash_value,
                    [0, 0, 0, 0, year, 0, 0, False, False],
                )
                update_state(
                    state,
                    year=year,
                    split=split,
                    label=label,
                    year_bit=year_bits[year],
                )
        duplicate_rows_within_file += file_rows - len(file_hashes)
        (train_hashes if split == "train" else test_hashes).setdefault(year, set()).update(
            file_hashes
        )
        per_file.append(
            {
                "path": str(path.relative_to(data_root)),
                "year": year,
                "split": split,
                "rows": file_rows,
                "unique_non_null_hashes": len(file_hashes),
                "null_hash_rows": file_null_hash_rows,
                "invalid_label_rows": file_invalid_label_rows,
                "bytes": path.stat().st_size,
            }
        )

    duplicate_hashes = sum(1 for state in hash_state.values() if state[3] > 1)
    cross_year_hashes = sum(
        1 for state in hash_state.values() if state[0].bit_count() > 1
    )
    cross_year_rows = sum(
        state[3] for state in hash_state.values() if state[0].bit_count() > 1
    )
    label_conflict_hashes = sum(1 for state in hash_state.values() if state[2] == 3)
    within_year_label_conflict_hashes = sum(1 for state in hash_state.values() if state[8])
    cross_year_label_conflict_hashes = sum(1 for state in hash_state.values() if state[7])
    split_overlap_by_year = {
        str(year): len(train_hashes.get(year, set()) & test_hashes.get(year, set()))
        for year in years
    }
    cross_year_split_overlap_hashes = sum(
        1
        for state in hash_state.values()
        if state[0].bit_count() > 1 and state[1] == 3
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "audit_version": 1,
        "audit_scope": {
            "mode": "screening_only",
            "cpu_only": True,
            "projected_columns": PROJECTED_COLUMNS,
            "feature_columns_read": False,
            "future_feature_access": False,
            "raw_hash_values_written": False,
        },
        "input": {
            "dataset_id": manifest.get("dataset_id"),
            "revision": manifest.get("source", {}).get("revision"),
            "manifest_sha256": manifest_sha256,
            "data_root": str(data_root),
            "file_count": len(files),
            "years": years,
            "rows_declared_by_manifest": manifest.get("content", {}).get("rows"),
        },
        "counts": {
            "total_rows": total_rows,
            "nonnull_hash_rows": nonnull_hash_rows,
            "null_hash_rows": null_hash_rows,
            "unique_non_null_hashes": len(hash_state),
            "duplicate_rows_global": nonnull_hash_rows - len(hash_state),
            "duplicate_hashes_global": duplicate_hashes,
            "duplicate_rows_within_file": duplicate_rows_within_file,
            "cross_year_hashes": cross_year_hashes,
            "cross_year_rows": cross_year_rows,
            "cross_year_split_overlap_hashes": cross_year_split_overlap_hashes,
            "label_conflict_hashes_any_year": label_conflict_hashes,
            "within_year_label_conflict_hashes": within_year_label_conflict_hashes,
            "cross_year_label_conflict_hashes": cross_year_label_conflict_hashes,
            "invalid_label_rows": invalid_label_rows,
            "null_year_month_rows": null_month_rows,
            "year_month_directory_mismatch_rows": year_month_mismatch_rows,
        },
        "split_overlap_by_year": split_overlap_by_year,
        "year_month_cardinality": {
            str(year): len(month_values[year]) for year in years
        },
        "files": per_file,
        "runtime": {
            "batch_size": batch_size,
            "wall_seconds": round(time.monotonic() - started, 3),
        },
    }


def write_markdown(result: dict[str, Any], output_path: Path) -> None:
    counts = result["counts"]
    lines = [
        "# LAMDA 跨年份哈希与标签时序审计",
        "",
        "> 本审计仅投影 `hash`、`label`、`year_month` 三列，在 CPU 上运行；未读取特征列，也未把任何原始哈希写入报告。",
        "",
        "## 输入与范围",
        f"- 数据集：`{result['input']['dataset_id']}`，修订：`{result['input']['revision']}`",
        f"- 清单 SHA-256：`{result['input']['manifest_sha256']}`",
        f"- 年份：{', '.join(str(year) for year in result['input']['years'])}",
        f"- 文件数：{result['input']['file_count']}，总行数：{counts['total_rows']}",
        "- 数据用途：`screening_only`；本结果不是正式测试集性能结论。",
        "",
        "## 审计结果",
        f"- 非空哈希唯一值：{counts['unique_non_null_hashes']}；全局重复行：{counts['duplicate_rows_global']}。",
        f"- 跨年份重复哈希：{counts['cross_year_hashes']} 个，涉及 {counts['cross_year_rows']} 行。",
        f"- 同年训练/测试重叠哈希：{sum(result['split_overlap_by_year'].values())} 个（按年见 JSON）。",
        f"- 同一哈希跨年份标签冲突：{counts['cross_year_label_conflict_hashes']} 个；仅同年标签冲突：{counts['within_year_label_conflict_hashes']} 个。",
        f"- 任意年份标签冲突哈希：{counts['label_conflict_hashes_any_year']} 个。",
        f"- 标签非法行：{counts['invalid_label_rows']}；时间字段为空：{counts['null_year_month_rows']}；目录年份不匹配：{counts['year_month_directory_mismatch_rows']}。",
        "",
        "## 解释边界",
        "- 跨年份重复哈希说明同一对象可能在多个年度出现，不能把跨年样本简单视为独立对象。",
        "- 跨年份标签冲突需要在训练/评价合同中明确处理；本审计只报告事实，不据此修改切分或标签。",
        "- 同年训练/测试重叠是数据泄漏风险信号；若非零，正式实验必须先回到数据合同裁决。",
        "",
        "## 运行收据",
        f"- CPU 审计墙钟：{result['runtime']['wall_seconds']} 秒；批大小：{result['runtime']['batch_size']}。",
        "- 原始明细与哈希值未写入输出；完整文件级信息见同目录 JSON。",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.batch_size <= 0:
        raise ValueError("--batch-size 必须为正数")
    result = audit(args.data_root, args.output_dir, args.batch_size)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "hash-label-audit.json"
    markdown_path = args.output_dir / "hash-label-audit.md"
    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_markdown(result, markdown_path)
    print(json.dumps(result["counts"], ensure_ascii=False, sort_keys=True))
    print(f"JSON={json_path}")
    print(f"MARKDOWN={markdown_path}")


if __name__ == "__main__":
    main()
