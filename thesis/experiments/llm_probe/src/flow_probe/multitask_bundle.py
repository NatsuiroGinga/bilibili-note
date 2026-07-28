"""把分层家族与子类样本合并为可复现的生成式多任务训练集。"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import Path

SOURCE_SCHEMA = "flow_probe_hierarchical_sample_v2"
BUNDLE_SCHEMA = "flow_probe_multitask_bundle_v1"
SPLITS = ("train", "validation")
TASK_SOURCES = {
    "family": "attack_family",
    "subtype": "attack_subtype",
}


class MultitaskBundleError(ValueError):
    """分层样本不能构成可信的多任务数据包。"""


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _derived_seed(seed: int, split: str) -> int:
    digest = sha256(f"{seed}\0multitask\0{split}".encode())
    return int.from_bytes(digest.digest()[:8], "big")


def _load_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MultitaskBundleError(f"无法读取 JSON：{path}") from error
    if not isinstance(value, dict):
        raise MultitaskBundleError(f"JSON 顶层必须是对象：{path}")
    return value


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    try:
        with path.open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise MultitaskBundleError(f"JSONL 行必须是对象：{path}:{line_number}")
                records.append(value)
    except (OSError, json.JSONDecodeError) as error:
        raise MultitaskBundleError(f"无法读取 JSONL：{path}") from error
    if not records:
        raise MultitaskBundleError(f"JSONL 不能为空：{path}")
    return records


def _source_set_info(
    manifest: Mapping[str, object], scope: str, split: str
) -> Mapping[str, object]:
    try:
        sets = manifest["sets"]
        scope_sets = sets[scope]  # type: ignore[index]
        info = scope_sets[split]  # type: ignore[index]
    except (KeyError, TypeError) as error:
        raise MultitaskBundleError(f"清单缺少集合定义：{scope}/{split}") from error
    if not isinstance(info, Mapping):
        raise MultitaskBundleError(f"集合定义必须是对象：{scope}/{split}")
    return info


def _validate_records(
    records: Sequence[Mapping[str, object]], expected_task: str, path: Path
) -> None:
    seen: set[str] = set()
    for record in records:
        sample_id = str(record.get("sample_id", ""))
        task = str(record.get("task", ""))
        label = str(record.get("task_label", ""))
        if not sample_id or not label:
            raise MultitaskBundleError(f"样本标识和任务标签不能为空：{path}")
        if task != expected_task:
            raise MultitaskBundleError(f"任务类型不一致：{path}/{task}")
        if label == "unknown_attack":
            raise MultitaskBundleError(f"未知攻击不得进入监督训练：{path}")
        if sample_id in seen:
            raise MultitaskBundleError(f"同一任务内样本重复：{path}/{sample_id}")
        seen.add(sample_id)
        try:
            completion = json.loads(str(record["completion"]))
        except (KeyError, json.JSONDecodeError) as error:
            raise MultitaskBundleError(f"完成标签无法解析：{path}/{sample_id}") from error
        if completion != {"label": label}:
            raise MultitaskBundleError(f"完成标签与任务标签冲突：{path}/{sample_id}")


def _write_jsonl(path: Path, records: Sequence[Mapping[str, object]]) -> str:
    with path.open("w", encoding="utf-8") as output:
        for record in records:
            output.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return _file_sha256(path)


def _distribution(records: Sequence[Mapping[str, object]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(record[field]) for record in records).items()))


def build_multitask_bundle(sample_dir: Path, output_dir: Path, seed: int) -> dict[str, object]:
    """验证 v2 清单，并确定性合并家族与子类训练、验证记录。"""
    sample_dir = Path(sample_dir)
    output_dir = Path(output_dir)
    manifest_path = sample_dir / "sample_manifest.json"
    manifest = _load_json(manifest_path)
    if manifest.get("schema_version") != SOURCE_SCHEMA:
        raise MultitaskBundleError("只接受分层样本 v2 清单")
    if manifest.get("seed") != seed:
        raise MultitaskBundleError("打包种子必须与分层样本种子一致")
    if output_dir.exists():
        raise MultitaskBundleError(f"输出目录已存在，拒绝覆盖：{output_dir}")

    bundled: dict[str, list[dict[str, object]]] = {split: [] for split in SPLITS}
    source_files: dict[str, dict[str, object]] = {}
    for scope, expected_task in TASK_SOURCES.items():
        for split in SPLITS:
            path = sample_dir / scope / f"{split}.jsonl"
            info = _source_set_info(manifest, scope, split)
            actual_sha256 = _file_sha256(path)
            if info.get("sha256") != actual_sha256:
                raise MultitaskBundleError(f"源文件 SHA-256 与清单不一致：{path}")
            records = _load_jsonl(path)
            if info.get("row_count") != len(records):
                raise MultitaskBundleError(f"源文件行数与清单不一致：{path}")
            _validate_records(records, expected_task, path)
            bundled[split].extend(records)
            source_files[f"{scope}_{split}"] = {
                "path": str(path),
                "row_count": len(records),
                "sha256": actual_sha256,
            }

    output_dir.mkdir(parents=True, exist_ok=False)
    set_manifest: dict[str, object] = {}
    for split in SPLITS:
        records = bundled[split]
        random.Random(_derived_seed(seed, split)).shuffle(records)
        path = output_dir / f"{split}.jsonl"
        set_manifest[split] = {
            "row_count": len(records),
            "task_distribution": _distribution(records, "task"),
            "label_distribution": _distribution(records, "task_label"),
            "sha256": _write_jsonl(path, records),
        }

    result = {
        "schema_version": BUNDLE_SCHEMA,
        "seed": seed,
        "shuffle": "sha256_derived_seed_python_random_v1",
        "source_manifest": {
            "path": str(manifest_path),
            "sha256": _file_sha256(manifest_path),
            "schema_version": SOURCE_SCHEMA,
        },
        "source_files": dict(sorted(source_files.items())),
        "sets": set_manifest,
        "unknown_attacks_in_supervised_data": False,
    }
    (output_dir / "bundle_manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构造生成式家族/子类多任务训练数据包")
    parser.add_argument("--sample-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = build_multitask_bundle(args.sample_dir, args.output_dir, args.seed)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
