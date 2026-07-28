"""把原始流记录转换为可训练、可审计的 JSONL 数据。"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path

from flow_probe.adapters.ciciot import adapt_row as adapt_ciciot
from flow_probe.adapters.genis import adapt_row as adapt_genis
from flow_probe.adapters.hikari import adapt_row as adapt_hikari
from flow_probe.manifest import build_manifest
from flow_probe.schemas import FlowSample
from flow_probe.serialize import serialize_flow
from flow_probe.split import grouped_split

Adapter = Callable[[Mapping[str, object], str, int], FlowSample]
ADAPTERS: dict[str, Adapter] = {
    "genis": adapt_genis,
    "hikari": adapt_hikari,
    "ciciot": adapt_ciciot,
}


def _iter_rows(path: Path) -> Iterable[Mapping[str, object]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            yield from csv.DictReader(source)
        return
    if suffix in {".jsonl", ".json"}:
        with path.open("r", encoding="utf-8") as source:
            for line in source:
                if line.strip():
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError(f"JSONL 行必须是对象：{path}")
                    yield value
        return
    if suffix == ".parquet":
        import pandas as pd

        yield from pd.read_parquet(path).to_dict(orient="records")
        return
    raise ValueError(f"不支持的数据格式：{path}")


def _record(sample: FlowSample) -> dict[str, object]:
    return {
        "sample_id": sample.sample_id,
        "group_id": sample.group_id,
        "source_dataset": sample.source_dataset,
        "binary_label": sample.binary_label,
        "attack_family": sample.attack_family,
        "prompt": serialize_flow(sample),
        "completion": json.dumps(
            {"label": sample.binary_label}, ensure_ascii=False, separators=(",", ":")
        ),
    }


def _write_jsonl(path: Path, samples: Sequence[FlowSample]) -> None:
    with path.open("w", encoding="utf-8") as output:
        for sample in samples:
            output.write(json.dumps(_record(sample), ensure_ascii=False, sort_keys=True) + "\n")


def prepare_dataset(
    dataset_name: str,
    input_paths: Sequence[Path],
    output_dir: Path,
    ratios: tuple[float, float, float],
    seed: int,
    reliable_groups: bool,
    group_basis: str,
) -> dict[str, object]:
    """适配、划分并持久化一个数据集。"""
    try:
        adapter = ADAPTERS[dataset_name]
    except KeyError as error:
        raise ValueError(f"未知数据集：{dataset_name}") from error
    paths = [Path(path) for path in input_paths]
    if not paths:
        raise ValueError("至少需要一个输入文件")

    samples: list[FlowSample] = []
    for path in paths:
        for row_number, row in enumerate(_iter_rows(path), start=1):
            samples.append(adapter(row, str(path), row_number))
    splits = grouped_split(
        samples,
        ratios=ratios,
        seed=seed,
        reliable_groups=reliable_groups,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    split_map = {
        "train": splits.train,
        "validation": splits.validation,
        "test": splits.test,
    }
    for name, split_samples in split_map.items():
        _write_jsonl(output_dir / f"{name}.jsonl", split_samples)

    split_summary: dict[str, object] = {
        **{name: len(split_samples) for name, split_samples in split_map.items()},
        "group_basis": group_basis,
        "evidence_level": splits.evidence_level,
        "seed": seed,
        "ratios": list(ratios),
    }
    manifest = build_manifest(samples, paths, split_summary)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成式恶意流量探针数据预处理")
    parser.add_argument("--dataset", choices=sorted(ADAPTERS), required=True)
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ratios", nargs=3, type=float, default=(0.8, 0.1, 0.1))
    parser.add_argument("--group-basis", required=True)
    parser.add_argument("--diagnostic", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    manifest = prepare_dataset(
        dataset_name=args.dataset,
        input_paths=args.input,
        output_dir=args.output_dir,
        ratios=tuple(args.ratios),
        seed=args.seed,
        reliable_groups=not args.diagnostic,
        group_basis=args.group_basis,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
