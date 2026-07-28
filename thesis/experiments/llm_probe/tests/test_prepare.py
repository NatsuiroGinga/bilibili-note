import csv
import json

from flow_probe.prepare import prepare_dataset

GENIS_FIELDS = [
    "BinaryLabel",
    "CategoryLabel",
    "SubCategoryLabel",
    "TotPkts",
    "SrcPkts",
    "DstPkts",
    "TotBytes",
    "sMinPktSz",
    "dMinPktSz",
    "sMaxPktSz",
    "dMaxPktSz",
    "SIntPkt",
    "DIntPkt",
    "Rate",
    "Load",
]


def write_genis_file(path, label: int) -> None:
    category = "benign" if label == 0 else "recon"
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=GENIS_FIELDS)
        writer.writeheader()
        writer.writerow(
            {
                "BinaryLabel": label,
                "CategoryLabel": category,
                "SubCategoryLabel": category,
                "TotPkts": 10,
                "SrcPkts": 6,
                "DstPkts": 4,
                "TotBytes": 1000,
                "sMinPktSz": 40,
                "dMinPktSz": 50,
                "sMaxPktSz": 200,
                "dMaxPktSz": 300,
                "SIntPkt": 2,
                "DIntPkt": 4,
                "Rate": 5,
                "Load": 8000,
            }
        )


def read_jsonl(path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_prepare_dataset_writes_split_records_and_manifest(tmp_path) -> None:
    source_paths = []
    for index in range(6):
        path = tmp_path / f"capture-{index}.csv"
        write_genis_file(path, index % 2)
        source_paths.append(path)
    output_dir = tmp_path / "prepared"

    result = prepare_dataset(
        dataset_name="genis",
        input_paths=source_paths,
        output_dir=output_dir,
        ratios=(0.5, 0.25, 0.25),
        seed=42,
        reliable_groups=True,
        group_basis="source_file",
    )

    records = {
        split: read_jsonl(output_dir / f"{split}.jsonl")
        for split in ("train", "validation", "test")
    }
    assert sum(len(items) for items in records.values()) == 6
    assert result["sample_count"] == 6
    assert result["split_summary"]["evidence_level"] == "primary"
    assert (output_dir / "manifest.json").is_file()
    for items in records.values():
        for item in items:
            assert item["completion"] in {
                '{"label":"benign"}',
                '{"label":"malicious"}',
            }
            assert "genis" not in item["prompt"]


def test_prepare_dataset_rejects_unknown_dataset(tmp_path) -> None:
    path = tmp_path / "source.csv"
    path.write_text("label\n0\n", encoding="utf-8")

    try:
        prepare_dataset(
            dataset_name="unknown",
            input_paths=[path],
            output_dir=tmp_path / "prepared",
            ratios=(0.5, 0.25, 0.25),
            seed=42,
            reliable_groups=False,
            group_basis="unknown",
        )
    except ValueError as error:
        assert "未知数据集" in str(error)
    else:
        raise AssertionError("未知数据集必须被拒绝")
