from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from flow_probe.e2_physics_auxiliary import (
    AUXILIARY_TABLE_NAME,
    AuxiliaryMaterializationError,
    materialize_e2_physics_auxiliary,
)


def _physics_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "sequence_id": "seq-1",
                "window_index_in_sequence": 0,
                "physics_group_sha256": "a" * 64,
                "split_id": "train-fit",
                "transport_family": "TCP",
                "evaluation_cluster_id": "cluster-1",
                "source_window_index": 4,
                "truth_window_duration_s": 0.1,
                "final_test_visible": False,
                "truth_queue_start_l3_bytes": 10,
                "truth_queue_end_l3_bytes": 20,
                "truth_queue_start_packets": 1,
                "truth_queue_end_packets": 2,
                "truth_qdisc_received_l3_bytes": 30,
                "truth_qdisc_dequeued_l3_bytes": 20,
                "truth_qdisc_drop_before_enqueue_l3_bytes": 0,
                "truth_qdisc_drop_after_dequeue_l3_bytes": 0,
                "truth_qdisc_received_packets": 3,
                "truth_qdisc_dequeued_packets": 2,
                "truth_qdisc_drop_before_enqueue_packets": 0,
                "truth_qdisc_drop_after_dequeue_packets": 0,
            },
            {
                "sequence_id": "seq-1",
                "window_index_in_sequence": 1,
                "physics_group_sha256": "a" * 64,
                "split_id": "train-fit",
                "transport_family": "TCP",
                "evaluation_cluster_id": "cluster-1",
                "source_window_index": 5,
                "truth_window_duration_s": 0.1,
                "final_test_visible": False,
                "truth_queue_start_l3_bytes": 20,
                "truth_queue_end_l3_bytes": 5,
                "truth_queue_start_packets": 2,
                "truth_queue_end_packets": 1,
                "truth_qdisc_received_l3_bytes": 5,
                "truth_qdisc_dequeued_l3_bytes": 20,
                "truth_qdisc_drop_before_enqueue_l3_bytes": 0,
                "truth_qdisc_drop_after_dequeue_l3_bytes": 0,
                "truth_qdisc_received_packets": 1,
                "truth_qdisc_dequeued_packets": 2,
                "truth_qdisc_drop_before_enqueue_packets": 0,
                "truth_qdisc_drop_after_dequeue_packets": 0,
            },
        ]
    )


def _directional_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "sequence_id": "seq-1",
                "window_index_in_sequence": 1,
                "physics_group_sha256": "a" * 64,
                "orig_bytes": 300,
                "resp_bytes": 50,
                "orig_pkts": 3,
                "resp_pkts": 1,
                "orig_ip_bytes": 420,
                "resp_ip_bytes": 90,
            },
            {
                "sequence_id": "seq-1",
                "window_index_in_sequence": 0,
                "physics_group_sha256": "a" * 64,
                "orig_bytes": 100,
                "resp_bytes": 40,
                "orig_pkts": 2,
                "resp_pkts": 1,
                "orig_ip_bytes": 180,
                "resp_ip_bytes": 80,
            },
        ]
    )


def test_missing_directional_source_writes_blocking_receipt(tmp_path: Path) -> None:
    physics_table = tmp_path / "physics.parquet"
    _physics_frame().to_parquet(physics_table, index=False)
    ns3_root = tmp_path / "ns3"
    raw = ns3_root / "shards" / "shard-00" / "runs" / "0000-tcp" / "main.csv"
    raw.parent.mkdir(parents=True)
    raw.write_text(
        "physics_group_sha256,public_total_packets,public_total_l3_bytes\n"
        f"{'a' * 64},3,260\n",
        encoding="utf-8",
    )
    output_root = tmp_path / "output"

    outcome = materialize_e2_physics_auxiliary(
        physics_table=physics_table,
        directional_table=None,
        ns3_root=ns3_root,
        output_root=output_root,
    )

    assert outcome.status == "blocked_missing_directional_source"
    assert outcome.table_path is None
    assert not (output_root / AUXILIARY_TABLE_NAME).exists()
    report = json.loads((output_root / "missing-source-report.json").read_text())
    assert report["missing_directional_fields"] == [
        "orig_bytes",
        "resp_bytes",
        "orig_pkts",
        "resp_pkts",
        "orig_ip_bytes",
        "resp_ip_bytes",
    ]
    assert report["exactly_derivable"] == {"duration": "truth_window_duration_s"}


def test_materializer_binds_features_by_sample_key_and_preserves_order(
    tmp_path: Path,
) -> None:
    physics_table = tmp_path / "physics.parquet"
    directional_table = tmp_path / "directional.parquet"
    _physics_frame().to_parquet(physics_table, index=False)
    _directional_frame().to_parquet(directional_table, index=False)
    output_root = tmp_path / "output"

    outcome = materialize_e2_physics_auxiliary(
        physics_table=physics_table,
        directional_table=directional_table,
        ns3_root=tmp_path / "unused-ns3",
        output_root=output_root,
    )

    assert outcome.status == "published"
    assert outcome.row_count == 2
    published = pd.read_parquet(output_root / AUXILIARY_TABLE_NAME)
    assert published["window_index_in_sequence"].tolist() == [0, 1]
    assert published["duration"].tolist() == [0.1, 0.1]
    assert published["orig_bytes"].tolist() == [100, 300]
    assert published["resp_ip_bytes"].tolist() == [80, 90]
    binding = json.loads((output_root / "binding.json").read_text())
    assert binding["row_count"] == 2
    assert binding["sample_key"] == [
        "sequence_id",
        "window_index_in_sequence",
        "physics_group_sha256",
    ]
    assert binding["binding_sha256"] == outcome.binding_sha256


def test_materializer_rejects_directional_key_mismatch(tmp_path: Path) -> None:
    physics_table = tmp_path / "physics.parquet"
    directional_table = tmp_path / "directional.parquet"
    _physics_frame().to_parquet(physics_table, index=False)
    directional = _directional_frame()
    directional.loc[0, "sequence_id"] = "unknown"
    directional.to_parquet(directional_table, index=False)

    with pytest.raises(AuxiliaryMaterializationError) as error:
        materialize_e2_physics_auxiliary(
            physics_table=physics_table,
            directional_table=directional_table,
            ns3_root=tmp_path / "unused-ns3",
            output_root=tmp_path / "output",
        )

    assert error.value.code == "directional_key_mismatch"
