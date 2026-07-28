"""将 TQH-C2 C 包临时观测物化为仅用于理论筛选的候选协议。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from itertools import permutations
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

PROTOCOL_VERSION = "data-protocol-v1.0-rc1"
PROTOCOL_STATUS = "provisional"
PROTOCOL_PHASE = "theory_selection"
REVIEW_STATUS = "review_pending"
CANDIDATE_ID = "dataset-candidate-c-v0"
SUITE_ID = "tqhc2_c_development"
TREE_VIEW_NAME = "tree_flat_view"

SPLIT_FILENAMES = {
    "train": "splits/tqhc2-c-development-train.jsonl",
    "validation": "splits/tqhc2-c-development-validation.jsonl",
    "test": "splits/tqhc2-c-development-test.jsonl",
}
TARGET_SPLIT_FRACTIONS = {"train": 0.8, "validation": 0.1, "test": 0.1}
LABEL_CONTRACT = {
    "malicious_c2": ("malicious", "mapped"),
    "benign": ("benign", "mapped"),
    "benign_external": ("benign", "mapped"),
    "malicious_lateral": (None, "auxiliary"),
    "malicious_recon": (None, "auxiliary"),
    "unknown": (None, "unresolved"),
}

MODEL_FEATURE_FIELDS = (
    "packet_count",
    "flow_duration_us",
    "network_bytes_total",
    "network_bytes_mean",
    "network_bytes_std",
    "network_bytes_min",
    "network_bytes_max",
    "network_bytes_p50",
    "network_bytes_p90",
    "payload_bytes_total",
    "payload_bytes_mean",
    "payload_bytes_std",
    "payload_bytes_max",
    "payload_bytes_p50",
    "payload_bytes_p90",
    "delta_time_us_mean",
    "delta_time_us_std",
    "delta_time_us_max",
    "delta_time_us_p50",
    "delta_time_us_p90",
    "positive_direction_fraction",
    "direction_balance_abs",
    "direction_change_count",
    "burst_count",
    "tcp_packet_fraction",
    "udp_packet_fraction",
    "icmp_packet_fraction",
    "other_transport_packet_fraction",
    "tcp_syn_packet_fraction",
    "tcp_ack_packet_fraction",
    "tcp_fin_packet_fraction",
    "tcp_rst_packet_fraction",
    "tcp_psh_packet_fraction",
    "payload_observed_fraction",
    "tcp_flags_applicable_fraction",
    "truncation_fraction",
    "zero_delta_fraction",
)

SAMPLE_METADATA_FIELDS = (
    "protocol_version",
    "protocol_status",
    "protocol_phase",
    "candidate_id",
    "suite_id",
    "split_id",
    "domain_role",
    "sample_id",
    "candidate_record_sha256",
    "source_record_sha256",
    "observation_sequence_sha256",
    "dataset_id",
    "dataset_version",
    "source_artifact_id",
    "source_capture_sha256",
    "extractor_contract_sha256",
    "allocation_group_id",
    "parent_session_id",
    "capture_group_id",
    "scenario_group_id",
    "topology_group_id",
    "time_block_id",
    "sample_unit",
    "window_start_ns",
    "window_end_ns",
    "window_ordinal",
    "packet_count_raw",
    "packet_count_kept",
    "native_label",
    "binary_label",
    "family_label",
    "subtype_label",
    "label_status",
    "unknown_role",
    "label_schema_version",
    "profile",
    "interval_s",
    "jitter_pct",
    "capture_id",
    "join_status",
)

REQUIRED_MASTER_COLUMNS = frozenset(
    {
        "sample_id",
        "record_sha256",
        "dataset_id",
        "dataset_version",
        "source_artifact_id",
        "source_capture_sha256",
        "extractor_contract_sha256",
        "allocation_group_id",
        "parent_session_id",
        "capture_group_id",
        "sample_unit",
        "window_start_ns",
        "window_end_ns",
        "window_ordinal",
        "packet_count_raw",
        "packet_count_kept",
        "native_label",
        "binary_label",
        "family_label",
        "subtype_label",
        "label_status",
        "unknown_role",
        "profile",
        "interval_s",
        "jitter_pct",
        "capture_id",
        "join_status",
    }
)
REQUIRED_PACKET_COLUMNS = frozenset(
    {
        "sample_id",
        "packet_index",
        "relative_time_ns",
        "delta_time_us",
        "direction",
        "network_length_bytes",
        "payload_length_bytes",
        "transport_family",
        "tcp_flags",
        "burst_id",
        "is_first_packet",
        "payload_length_observed",
        "tcp_flags_applicable",
        "truncation_mask",
    }
)
SENSITIVE_FIELD_TOKENS = frozenset(
    {
        "address",
        "capture",
        "cell",
        "config",
        "dataset",
        "encryption",
        "filename",
        "framework",
        "host",
        "ip",
        "label",
        "path",
        "port",
        "profile",
        "source",
        "topology",
        "uid",
    }
)
_SHA256_LENGTH = 64


class TQHC2CandidateError(ValueError):
    """候选协议输入、划分或制品未满足约束。"""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_scalar(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, (str, bool, int, float)):
        return value
    raise TypeError(f"无法规范化 JSON 标量：{type(value).__name__}")


def _stable_hash(value: Mapping[str, object]) -> str:
    payload = json.dumps(
        {key: _json_scalar(item) for key, item in sorted(value.items())},
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(
                json.dumps(row, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
            )


def _write_yaml(path: Path, value: Mapping[str, object]) -> None:
    path.write_text(
        yaml.safe_dump(dict(value), allow_unicode=True, sort_keys=True),
        encoding="utf-8",
    )


def _require_columns(frame: pd.DataFrame, required: frozenset[str], description: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise TQHC2CandidateError(f"{description}缺少字段：{','.join(missing)}")


def _load_and_validate_inputs(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    master_path = input_dir / "master_records.parquet"
    packet_path = input_dir / "views" / "packet_observations.parquet"
    if not master_path.is_file() or not packet_path.is_file():
        raise TQHC2CandidateError(f"缺少 C 包暂定主记录或包观测：{input_dir}")
    try:
        master = pd.read_parquet(master_path)
        packets = pd.read_parquet(packet_path)
    except Exception as error:
        raise TQHC2CandidateError(f"无法读取 C 包暂定 Parquet：{input_dir}") from error

    _require_columns(master, REQUIRED_MASTER_COLUMNS, "主记录")
    _require_columns(packets, REQUIRED_PACKET_COLUMNS, "包观测")
    if master.empty or packets.empty:
        raise TQHC2CandidateError("主记录和包观测均不得为空")
    if master["sample_id"].isna().any() or master["sample_id"].duplicated().any():
        raise TQHC2CandidateError("主记录 sample_id 必须非空且全局唯一")
    if packets[["sample_id", "packet_index"]].duplicated().any():
        raise TQHC2CandidateError("包观测的 sample_id/packet_index 必须唯一")

    dataset_ids = set(master["dataset_id"].astype(str))
    profiles = set(master["profile"].astype(str))
    if dataset_ids != {"TQH-C2"} or profiles != {"C"}:
        raise TQHC2CandidateError(
            f"候选输入必须仅含 TQH-C2 C profile：{sorted(dataset_ids)}/{sorted(profiles)}"
        )
    for sample_id, native_label, binary_label, label_status in master.loc[
        :, ["sample_id", "native_label", "binary_label", "label_status"]
    ].itertuples(index=False, name=None):
        native_label = str(native_label)
        if native_label not in LABEL_CONTRACT:
            raise TQHC2CandidateError(f"标签映射包含未知原生标签：{sample_id}:{native_label}")
        expected_binary, expected_status = LABEL_CONTRACT[native_label]
        actual_binary = None if pd.isna(binary_label) else str(binary_label)
        actual_status = str(label_status)
        if (actual_binary, actual_status) != (expected_binary, expected_status):
            raise TQHC2CandidateError(
                "标签映射不符合固定契约："
                f"{sample_id}:{native_label}:"
                f"{actual_binary}/{actual_status} != {expected_binary}/{expected_status}"
            )

    mapped = master["label_status"].eq("mapped")
    if set(master.loc[mapped, "binary_label"].astype(str)) != {"benign", "malicious"}:
        raise TQHC2CandidateError("映射样本必须同时包含 benign 与 malicious")

    packet_ids = set(packets["sample_id"].astype(str))
    master_ids = set(master["sample_id"].astype(str))
    if packet_ids != master_ids:
        raise TQHC2CandidateError(
            f"包观测与主记录样本集合不一致：包侧独有 {len(packet_ids - master_ids)}，"
            f"主记录侧独有 {len(master_ids - packet_ids)}"
        )
    actual_counts = packets.groupby("sample_id", sort=False).size()
    expected_counts = master.set_index("sample_id")["packet_count_kept"].astype("int64")
    actual_counts = actual_counts.reindex(expected_counts.index, fill_value=-1).astype("int64")
    mismatched = expected_counts.ne(actual_counts)
    if mismatched.any():
        sample_id = str(mismatched[mismatched].index[0])
        raise TQHC2CandidateError(f"包观测计数未绑定主记录：{sample_id}")

    numeric_packet_fields = (
        "packet_index",
        "relative_time_ns",
        "delta_time_us",
        "direction",
        "network_length_bytes",
        "burst_id",
    )
    numeric = packets.loc[:, list(numeric_packet_fields)].to_numpy(dtype=np.float64)
    if not np.isfinite(numeric).all():
        raise TQHC2CandidateError("包观测数值字段含空值或非有限值")
    if not set(packets["direction"].astype(int)).issubset({-1, 1}):
        raise TQHC2CandidateError("包方向只能为 -1 或 1")
    if (packets["packet_index"] < 0).any() or (packets["delta_time_us"] < 0).any():
        raise TQHC2CandidateError("包序号和相邻间隔不得为负")
    invalid_payload_mask = (
        packets["payload_length_bytes"].isna() & packets["payload_length_observed"]
    )
    invalid_tcp_mask = packets["tcp_flags"].isna() & packets["tcp_flags_applicable"]
    if invalid_payload_mask.any() or invalid_tcp_mask.any():
        raise TQHC2CandidateError("掩码声明字段可用时，对应观测不得为空")
    if packets["payload_length_bytes"].dropna().lt(0).any():
        raise TQHC2CandidateError("载荷长度不得为负")
    mask_fields = (
        "payload_length_observed",
        "tcp_flags_applicable",
        "truncation_mask",
    )
    if packets.loc[:, list(mask_fields)].isna().any().any():
        raise TQHC2CandidateError("包观测适用掩码不得为空")
    transport = packets["transport_family"].astype(str).str.upper()
    if not set(transport).issubset({"TCP", "UDP", "ICMP"}):
        raise TQHC2CandidateError("包观测包含未知传输族")
    flags_applicable = packets["tcp_flags_applicable"].astype(bool)
    if not flags_applicable.eq(transport.eq("TCP")).all():
        raise TQHC2CandidateError("TCP 标志适用掩码与传输族不一致")
    flags = packets["tcp_flags"]
    if flags.dropna().lt(0).any() or flags.dropna().gt(0x1FF).any():
        raise TQHC2CandidateError("TCP 标志超出 9 位字段范围")
    if ((~flags_applicable) & flags.fillna(0).ne(0)).any():
        raise TQHC2CandidateError("TCP 标志掩码为假时不得携带非零值")

    packet_order = packets.sort_values(["sample_id", "packet_index"], kind="mergesort")
    order_audit = packet_order.groupby("sample_id", sort=False)["packet_index"].agg(
        ["min", "max", "count", "nunique"]
    )
    contiguous = (
        order_audit["min"].eq(0)
        & order_audit["max"].eq(order_audit["count"] - 1)
        & order_audit["count"].eq(order_audit["nunique"])
    )
    if not contiguous.all():
        raise TQHC2CandidateError(f"包序号不连续：{contiguous[~contiguous].index[0]}")
    return master.sort_values("sample_id", kind="mergesort"), packet_order


def _sequence_hashes(packets: pd.DataFrame) -> dict[str, str]:
    fields = (
        "relative_time_ns",
        "delta_time_us",
        "direction",
        "network_length_bytes",
        "payload_length_bytes",
        "transport_family",
        "tcp_flags",
        "burst_id",
        "is_first_packet",
        "payload_length_observed",
        "tcp_flags_applicable",
        "truncation_mask",
    )
    hashes: dict[str, str] = {}
    for sample_id, frame in packets.groupby("sample_id", sort=True, observed=True):
        digest = hashlib.sha256()
        for row in frame.loc[:, list(fields)].itertuples(index=False, name=None):
            values = [_json_scalar(value) for value in row]
            digest.update(
                json.dumps(
                    values,
                    allow_nan=False,
                    ensure_ascii=True,
                    separators=(",", ":"),
                ).encode("ascii")
            )
            digest.update(b"\n")
        hashes[str(sample_id)] = digest.hexdigest()
    return hashes


def _aggregate_features(packets: pd.DataFrame) -> pd.DataFrame:
    working = packets.copy()
    working["payload_length_bytes"] = working["payload_length_bytes"].fillna(0).astype("int64")
    working["tcp_flags"] = working["tcp_flags"].fillna(0).astype("int64")
    transport = working["transport_family"].astype(str).str.upper()
    working["tcp_indicator"] = transport.eq("TCP").astype("float64")
    working["udp_indicator"] = transport.eq("UDP").astype("float64")
    working["icmp_indicator"] = transport.eq("ICMP").astype("float64")
    working["other_transport_indicator"] = (~transport.isin({"TCP", "UDP", "ICMP"})).astype(
        "float64"
    )
    working["positive_direction_indicator"] = working["direction"].eq(1).astype("float64")
    working["zero_delta_indicator"] = working["delta_time_us"].eq(0).astype("float64")
    flags = working["tcp_flags"].astype("int64")
    flags_applicable = working["tcp_flags_applicable"].astype(bool)
    for name, bit in (("fin", 0x01), ("syn", 0x02), ("rst", 0x04), ("psh", 0x08), ("ack", 0x10)):
        working[f"tcp_{name}_indicator"] = (flags_applicable & (flags & bit).ne(0)).astype(
            "float64"
        )

    grouped = working.groupby("sample_id", sort=True, observed=True)
    features = grouped.agg(
        packet_count=("packet_index", "size"),
        flow_duration_us=("relative_time_ns", "max"),
        network_bytes_total=("network_length_bytes", "sum"),
        network_bytes_mean=("network_length_bytes", "mean"),
        network_bytes_std=("network_length_bytes", "std"),
        network_bytes_min=("network_length_bytes", "min"),
        network_bytes_max=("network_length_bytes", "max"),
        payload_bytes_total=("payload_length_bytes", "sum"),
        payload_bytes_mean=("payload_length_bytes", "mean"),
        payload_bytes_std=("payload_length_bytes", "std"),
        payload_bytes_max=("payload_length_bytes", "max"),
        delta_time_us_mean=("delta_time_us", "mean"),
        delta_time_us_std=("delta_time_us", "std"),
        delta_time_us_max=("delta_time_us", "max"),
        positive_direction_fraction=("positive_direction_indicator", "mean"),
        burst_count=("burst_id", "max"),
        tcp_packet_fraction=("tcp_indicator", "mean"),
        udp_packet_fraction=("udp_indicator", "mean"),
        icmp_packet_fraction=("icmp_indicator", "mean"),
        other_transport_packet_fraction=("other_transport_indicator", "mean"),
        tcp_syn_packet_fraction=("tcp_syn_indicator", "mean"),
        tcp_ack_packet_fraction=("tcp_ack_indicator", "mean"),
        tcp_fin_packet_fraction=("tcp_fin_indicator", "mean"),
        tcp_rst_packet_fraction=("tcp_rst_indicator", "mean"),
        tcp_psh_packet_fraction=("tcp_psh_indicator", "mean"),
        payload_observed_fraction=("payload_length_observed", "mean"),
        tcp_flags_applicable_fraction=("tcp_flags_applicable", "mean"),
        truncation_fraction=("truncation_mask", "mean"),
        zero_delta_fraction=("zero_delta_indicator", "mean"),
    )
    quantiles = {
        "network_length_bytes": "network_bytes",
        "payload_length_bytes": "payload_bytes",
        "delta_time_us": "delta_time_us",
    }
    for source_field, output_prefix in quantiles.items():
        values = grouped[source_field].quantile([0.5, 0.9]).unstack(level=-1)
        features[f"{output_prefix}_p50"] = values[0.5]
        features[f"{output_prefix}_p90"] = values[0.9]

    features["flow_duration_us"] = features["flow_duration_us"] / 1_000.0
    features["burst_count"] = features["burst_count"] + 1
    features["direction_change_count"] = features["burst_count"] - 1
    features["direction_balance_abs"] = (features["positive_direction_fraction"] * 2.0 - 1.0).abs()
    features = features.fillna(0.0)
    features["packet_count"] = features["packet_count"].astype("int64")
    features["burst_count"] = features["burst_count"].astype("int64")
    features["direction_change_count"] = features["direction_change_count"].astype("int64")
    features = features.loc[:, list(MODEL_FEATURE_FIELDS)]
    numeric = features.to_numpy(dtype=np.float64)
    if not np.isfinite(numeric).all():
        raise TQHC2CandidateError("聚合模型字段含非有限值")
    return features


def _build_groups(master: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for capture_group_id, frame in master.groupby("capture_group_id", sort=True, observed=True):
        unique_fields = (
            "allocation_group_id",
            "profile",
            "interval_s",
            "jitter_pct",
            "source_capture_sha256",
        )
        for field_name in unique_fields:
            if frame[field_name].nunique(dropna=False) != 1:
                raise TQHC2CandidateError(f"完整 cell 的 {field_name} 不唯一：{capture_group_id}")
        status_counts = Counter(frame["label_status"].astype(str))
        mapped = frame[frame["label_status"].eq("mapped")]
        label_counts = Counter(mapped["binary_label"].astype(str))
        rows.append(
            {
                "allocation_group_id": str(frame["allocation_group_id"].iloc[0]),
                "capture_group_id": str(capture_group_id),
                "profile": str(frame["profile"].iloc[0]),
                "interval_s": int(frame["interval_s"].iloc[0]),
                "jitter_pct": int(frame["jitter_pct"].iloc[0]),
                "source_capture_sha256": str(frame["source_capture_sha256"].iloc[0]),
                "record_count": int(len(frame)),
                "mapped_count": int(status_counts["mapped"]),
                "auxiliary_count": int(status_counts["auxiliary"]),
                "unresolved_count": int(status_counts["unresolved"]),
                "benign_count": int(label_counts["benign"]),
                "malicious_count": int(label_counts["malicious"]),
            }
        )
    groups = pd.DataFrame(rows).sort_values("capture_group_id", kind="mergesort")
    if len(groups) != 12 or groups["allocation_group_id"].duplicated().any():
        raise TQHC2CandidateError(f"C profile 必须恰有 12 个互异 allocation_group：{len(groups)}")
    return groups.reset_index(drop=True)


def _select_group_splits(groups: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    total = int(groups["mapped_count"].sum())
    candidates: list[tuple[float, str, str, str, dict[str, int]]] = []
    rows = list(groups.to_dict(orient="records"))
    for validation, test in permutations(rows, 2):
        if int(validation["interval_s"]) == int(test["interval_s"]):
            continue
        if (
            min(
                int(validation["benign_count"]),
                int(validation["malicious_count"]),
                int(test["benign_count"]),
                int(test["malicious_count"]),
            )
            <= 0
        ):
            continue
        counts = {
            "validation": int(validation["mapped_count"]),
            "test": int(test["mapped_count"]),
        }
        counts["train"] = total - counts["validation"] - counts["test"]
        objective = sum(
            abs(counts[split_id] / total - TARGET_SPLIT_FRACTIONS[split_id])
            for split_id in TARGET_SPLIT_FRACTIONS
        )
        tie_break = hashlib.sha256(
            (
                f"{CANDIDATE_ID}|{validation['capture_group_id']}|" f"{test['capture_group_id']}"
            ).encode("ascii")
        ).hexdigest()
        candidates.append(
            (
                objective,
                tie_break,
                str(validation["capture_group_id"]),
                str(test["capture_group_id"]),
                counts,
            )
        )
    if not candidates:
        raise TQHC2CandidateError("无法找到标签覆盖完整且跨 interval 的开发划分")
    objective, _, validation_group, test_group, counts = min(candidates)
    split_by_group = {
        str(group_id): (
            "validation"
            if str(group_id) == validation_group
            else "test" if str(group_id) == test_group else "train"
        )
        for group_id in groups["capture_group_id"]
    }
    result = groups.copy()
    result["split_id"] = result["capture_group_id"].map(split_by_group)
    fractions = {split_id: counts[split_id] / total for split_id in counts}
    audit = {
        "assignment_method": "完整 cell 穷举；验证与测试使用不同 interval；最小化 80/10/10 偏差",
        "candidate_count": len(candidates),
        "mapped_sample_count": total,
        "sample_counts": counts,
        "sample_fractions": fractions,
        "target_fractions": TARGET_SPLIT_FRACTIONS,
        "l1_fraction_deviation": objective,
        "validation_group": validation_group,
        "test_group": test_group,
    }
    return result, audit


def _build_samples(
    master: pd.DataFrame,
    packets: pd.DataFrame,
    groups: pd.DataFrame,
) -> pd.DataFrame:
    mapped_master = master[master["label_status"].eq("mapped")].copy()
    mapped_ids = set(mapped_master["sample_id"].astype(str))
    mapped_packets = packets[packets["sample_id"].astype(str).isin(mapped_ids)].copy()
    features = _aggregate_features(mapped_packets)
    sequence_hashes = _sequence_hashes(mapped_packets)
    if set(features.index.astype(str)) != mapped_ids or set(sequence_hashes) != mapped_ids:
        raise TQHC2CandidateError("聚合字段或序列哈希未覆盖全部映射样本")

    split_by_group = dict(zip(groups["capture_group_id"], groups["split_id"], strict=True))
    mapped_master = mapped_master.rename(columns={"record_sha256": "source_record_sha256"})
    mapped_master["protocol_version"] = PROTOCOL_VERSION
    mapped_master["protocol_status"] = PROTOCOL_STATUS
    mapped_master["protocol_phase"] = PROTOCOL_PHASE
    mapped_master["candidate_id"] = CANDIDATE_ID
    mapped_master["suite_id"] = SUITE_ID
    mapped_master["split_id"] = mapped_master["capture_group_id"].map(split_by_group)
    mapped_master["domain_role"] = "development_only"
    mapped_master["scenario_group_id"] = "tqhc2_c_http_aes"
    mapped_master["topology_group_id"] = "tqhc2_c_source_topology"
    mapped_master["time_block_id"] = mapped_master["capture_group_id"].astype(str)
    mapped_master["label_schema_version"] = "tqhc2-label-v1"
    mapped_master["observation_sequence_sha256"] = mapped_master["sample_id"].map(sequence_hashes)
    mapped_master["family_label"] = mapped_master["family_label"].fillna("").astype(str)
    mapped_master["subtype_label"] = mapped_master["subtype_label"].fillna("").astype(str)
    mapped_master["unknown_role"] = mapped_master["unknown_role"].fillna("").astype(str)

    samples = mapped_master.merge(
        features.reset_index(), on="sample_id", how="left", validate="one_to_one"
    )
    samples["candidate_record_sha256"] = ""
    samples = samples.loc[:, [*SAMPLE_METADATA_FIELDS, *MODEL_FEATURE_FIELDS]]

    string_fields = [
        field_name
        for field_name in SAMPLE_METADATA_FIELDS
        if field_name
        not in {
            "window_start_ns",
            "window_end_ns",
            "window_ordinal",
            "packet_count_raw",
            "packet_count_kept",
            "interval_s",
            "jitter_pct",
        }
    ]
    for field_name in string_fields:
        samples[field_name] = samples[field_name].fillna("").astype(str)
    integer_fields = (
        "window_start_ns",
        "window_end_ns",
        "window_ordinal",
        "packet_count_raw",
        "packet_count_kept",
        "interval_s",
        "jitter_pct",
        "packet_count",
        "direction_change_count",
        "burst_count",
    )
    for field_name in integer_fields:
        samples[field_name] = samples[field_name].astype("int64")
    for field_name in set(MODEL_FEATURE_FIELDS).difference(integer_fields):
        samples[field_name] = samples[field_name].astype("float64")

    samples = samples.sort_values("sample_id", kind="mergesort").reset_index(drop=True)
    record_fields = [
        field_name for field_name in samples.columns if field_name != "candidate_record_sha256"
    ]
    candidate_hashes = []
    for row in samples.loc[:, record_fields].to_dict(orient="records"):
        candidate_hashes.append(_stable_hash(row))
    samples["candidate_record_sha256"] = candidate_hashes
    samples = samples.loc[:, [*SAMPLE_METADATA_FIELDS, *MODEL_FEATURE_FIELDS]]
    if samples["sample_id"].duplicated().any() or samples["split_id"].isna().any():
        raise TQHC2CandidateError("候选主记录主键或划分无效")
    if not np.isfinite(samples.loc[:, list(MODEL_FEATURE_FIELDS)].to_numpy(dtype=float)).all():
        raise TQHC2CandidateError("候选模型字段含非有限值")
    return samples


def _field_roles() -> dict[str, object]:
    label_fields = {"native_label", "binary_label", "family_label", "subtype_label"}
    split_fields = {
        "suite_id",
        "split_id",
        "domain_role",
        "allocation_group_id",
        "capture_group_id",
        "scenario_group_id",
        "topology_group_id",
        "time_block_id",
        "profile",
        "interval_s",
        "jitter_pct",
    }
    fields: dict[str, object] = {}
    for field_name in SAMPLE_METADATA_FIELDS:
        role = (
            "label_target"
            if field_name in label_fields
            else "split_metadata" if field_name in split_fields else "audit_only"
        )
        fields[field_name] = {"role": role}
    for field_name in MODEL_FEATURE_FIELDS:
        fields[field_name] = {"role": "model_input", "views": [TREE_VIEW_NAME]}
    return {
        "protocol_version": PROTOCOL_VERSION,
        "fields": fields,
        "views": {TREE_VIEW_NAME: {"feature_fields": list(MODEL_FEATURE_FIELDS)}},
    }


def _source_artifacts(input_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    source_checks_path = input_dir / "source_checksums.json"
    if source_checks_path.is_file():
        try:
            source_checks = json.loads(source_checks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise TQHC2CandidateError("source_checksums.json 不是合法 JSON") from error
        for raw_row in source_checks.get("files", []):
            if not isinstance(raw_row, Mapping):
                raise TQHC2CandidateError("source_checksums.json 的 files 行必须是对象")
            digest = str(raw_row.get("sha256", ""))
            if len(digest) != _SHA256_LENGTH:
                raise TQHC2CandidateError("上游来源记录缺少 SHA-256")
            rows.append(
                {
                    "lineage_level": "upstream_source",
                    "role": str(raw_row.get("role", "")),
                    "source_path": str(raw_row.get("path", "")),
                    "sha256": digest,
                    "size_bytes": int(raw_row.get("size_bytes", 0)),
                }
            )

    derived_paths = (
        "master_records.parquet",
        "views/packet_observations.parquet",
        "source_checksums.json",
        "run_manifest.provisional.json",
        "schema.provisional.json",
        "artifact_checksums.provisional.json",
        "audit/cell-audit.json",
        "audit/label-coverage.json",
        "audit/leakage-audit.json",
    )
    for relative_path in derived_paths:
        path = input_dir / relative_path
        if path.is_file():
            rows.append(
                {
                    "lineage_level": "candidate_input",
                    "role": "derived_input",
                    "source_path": relative_path,
                    "sha256": _sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    module_path = Path(__file__)
    rows.append(
        {
            "lineage_level": "candidate_builder",
            "role": "materializer_source",
            "source_path": "src/flow_probe/tqh_c2_candidate.py",
            "sha256": _sha256_file(module_path),
            "size_bytes": module_path.stat().st_size,
        }
    )
    return sorted(
        rows,
        key=lambda row: (
            str(row["lineage_level"]),
            str(row["source_path"]),
            str(row["role"]),
            str(row["sha256"]),
        ),
    )


def _duplicate_screen(samples: pd.DataFrame) -> dict[str, object]:
    exact = samples.groupby("observation_sequence_sha256", sort=True).agg(
        split_count=("split_id", "nunique"),
        sample_count=("sample_id", "size"),
        label_count=("binary_label", "nunique"),
    )
    exact_cross_split = exact[exact["split_count"] > 1]
    exact_samples = samples[samples["observation_sequence_sha256"].isin(exact_cross_split.index)]
    exact_packet_counts = Counter(exact_samples["packet_count"].astype(int))
    exact_label_counts = Counter(exact_samples["binary_label"].astype(str))
    lineage_independent = all(
        frame["source_capture_sha256"].nunique() > 1
        for _, frame in exact_samples.groupby(
            "observation_sequence_sha256", sort=True, observed=True
        )
    )
    short_flow_only = bool(exact_samples["packet_count"].le(2).all())
    label_consistent = not exact_cross_split["label_count"].gt(1).any()

    coarse_signatures: list[str] = []
    for row in samples.loc[:, list(MODEL_FEATURE_FIELDS)].itertuples(index=False, name=None):
        rounded = [round(float(value), 3) for value in row]
        payload = json.dumps(rounded, allow_nan=False, separators=(",", ":")).encode("ascii")
        coarse_signatures.append(hashlib.sha256(payload).hexdigest())
    coarse = samples.loc[:, ["sample_id", "split_id", "binary_label"]].copy()
    coarse["signature"] = coarse_signatures
    coarse_audit = coarse.groupby("signature", sort=True).agg(
        split_count=("split_id", "nunique"),
        sample_count=("sample_id", "size"),
        label_count=("binary_label", "nunique"),
    )
    coarse_cross_split = coarse_audit[coarse_audit["split_count"] > 1]

    exact_examples = list(exact_cross_split.index[:10])
    coarse_examples = list(coarse_cross_split.index[:10])
    return {
        "exact_observation_sequence": {
            "cross_split_hash_count": int(len(exact_cross_split)),
            "cross_split_sample_count": int(exact_cross_split["sample_count"].sum()),
            "conflicting_label_hash_count": int(exact_cross_split["label_count"].gt(1).sum()),
            "sample_counts_by_packet_count": {
                str(key): value for key, value in sorted(exact_packet_counts.items())
            },
            "sample_counts_by_label": dict(sorted(exact_label_counts.items())),
            "all_cross_split_hashes_use_distinct_source_captures": lineage_independent,
            "all_cross_split_hashes_are_one_or_two_packet_flows": short_flow_only,
            "all_cross_split_hashes_are_label_consistent": label_consistent,
            "example_hashes": exact_examples,
            "interpretation": (
                "残余来自不同 cell 中可观测字段完全相同的极短流；"
                "完整 cell 分组约束下不删除或跨组移动样本。"
                "基线报告必须增加去除这些哈希后的敏感性分析，不得把残余解释为来源对象重复。"
            ),
            "status": (
                "documented_residual_requires_sensitivity"
                if len(exact_cross_split)
                and lineage_independent
                and short_flow_only
                and label_consistent
                else "review_required" if len(exact_cross_split) else "pass"
            ),
        },
        "coarse_aggregate_signature": {
            "rounding_decimals": 3,
            "cross_split_hash_count": int(len(coarse_cross_split)),
            "cross_split_sample_count": int(coarse_cross_split["sample_count"].sum()),
            "conflicting_label_hash_count": int(coarse_cross_split["label_count"].gt(1).sum()),
            "example_hashes": coarse_examples,
            "status": "screen_only",
        },
        "scope_note": "这是候选阶段的固定签名筛查，不替代完整 dataset-v1 的近重复距离审计。",
    }


def _build_audits(
    master: pd.DataFrame,
    samples: pd.DataFrame,
    groups: pd.DataFrame,
    split_selection: Mapping[str, object],
    manifest_hashes: Mapping[str, str],
) -> dict[str, object]:
    label_status_counts = Counter(master["label_status"].astype(str))
    native_counts = Counter(master["native_label"].astype(str))
    binary_counts = Counter(samples["binary_label"].astype(str))
    split_counts = Counter(samples["split_id"].astype(str))
    split_label_counts = {
        split_id: dict(sorted(Counter(frame["binary_label"].astype(str)).items()))
        for split_id, frame in samples.groupby("split_id", sort=True, observed=True)
    }
    label_coverage = {
        "source_record_count": int(len(master)),
        "candidate_record_count": int(len(samples)),
        "excluded_record_count": int(len(master) - len(samples)),
        "source_native_label_counts": dict(sorted(native_counts.items())),
        "source_label_status_counts": dict(sorted(label_status_counts.items())),
        "candidate_binary_label_counts": dict(sorted(binary_counts.items())),
        "split_binary_label_counts": split_label_counts,
        "mapping": {
            "malicious_c2": "malicious",
            "benign": "benign",
            "benign_external": "benign",
            "malicious_recon": "auxiliary_excluded",
            "unknown": "unresolved_excluded",
        },
        "status": "pass",
    }

    group_memberships = samples.groupby("allocation_group_id")["split_id"].nunique()
    group_split_audit = {
        **dict(split_selection),
        "allocation_group_count": int(len(groups)),
        "allocation_groups_by_split": {
            split_id: sorted(frame["allocation_group_id"].astype(str).tolist())
            for split_id, frame in groups.groupby("split_id", sort=True, observed=True)
        },
        "capture_groups_by_split": {
            split_id: sorted(frame["capture_group_id"].astype(str).tolist())
            for split_id, frame in groups.groupby("split_id", sort=True, observed=True)
        },
        "sample_counts_from_manifests": dict(sorted(split_counts.items())),
        "cross_split_allocation_group_count": int(group_memberships.gt(1).sum()),
        "all_mapped_samples_assigned_once": int(sum(split_counts.values())) == len(samples),
        "status": (
            "pass"
            if group_memberships.le(1).all() and int(sum(split_counts.values())) == len(samples)
            else "fail"
        ),
    }

    sensitive_hits = [
        field_name
        for field_name in MODEL_FEATURE_FIELDS
        if set(field_name.lower().split("_")).intersection(SENSITIVE_FIELD_TOKENS)
    ]
    field_budget = {
        "view_name": TREE_VIEW_NAME,
        "model_input_fields": list(MODEL_FEATURE_FIELDS),
        "model_input_field_count": len(MODEL_FEATURE_FIELDS),
        "sensitive_field_hits": sensitive_hits,
        "training_fitted_transformations": [],
        "status": "pass" if not sensitive_hits else "fail",
    }

    duplicate_screen = _duplicate_screen(samples)
    required_labels_present = all(
        set(counts) == {"benign", "malicious"} for counts in split_label_counts.values()
    )
    p0_subset = {
        "protocol_version": PROTOCOL_VERSION,
        "protocol_status": PROTOCOL_STATUS,
        "protocol_phase": PROTOCOL_PHASE,
        "review_status": REVIEW_STATUS,
        "formal_protocol_gate_complete": False,
        "checks": {
            "identity_nonempty": {
                "status": (
                    "pass" if samples["sample_id"].astype(str).str.len().gt(0).all() else "fail"
                )
            },
            "sample_id_uniqueness": {
                "duplicate_count": int(samples["sample_id"].duplicated().sum()),
                "status": "pass" if not samples["sample_id"].duplicated().any() else "fail",
            },
            "group_exclusivity": {
                "cross_split_group_count": int(group_memberships.gt(1).sum()),
                "status": "pass" if group_memberships.le(1).all() else "fail",
            },
            "label_coverage": {
                "all_development_splits_have_both_labels": required_labels_present,
                "status": "pass" if required_labels_present else "fail",
            },
            "field_budget": {"status": field_budget["status"]},
            "manifest_binding": {
                "artifact_hashes": dict(sorted(manifest_hashes.items())),
                "status": "pass",
            },
            "exact_and_near_duplicate_screen": duplicate_screen,
            "reproducibility": {
                "status": "pending_external_rerun",
                "required_comparison": "两个新输出目录的全部非自引用制品逐字节一致",
            },
        },
        "overall_status": "provisional_candidate",
        "remaining_blockers": [
            "A/B 大包尚未完成，当前不含完整 TQH-C2 profile",
            "尚未合并 GeNIS 与 ns-3 的完整 dataset-v1",
            "尚未执行完整 P0 门禁和独立重复物化验收",
        ],
        "use_restriction": "仅允许 theory_selection，不得冻结最终超参数或形成最终测试结论。",
    }
    return {
        "label-coverage.json": label_coverage,
        "group-split-audit.json": group_split_audit,
        "field-budget.json": field_budget,
        "p0-subset.json": p0_subset,
    }


def materialize_candidate(*, input_dir: Path, output_dir: Path) -> dict[str, object]:
    """生成 TQH-C2 C profile 的开发候选协议目录。"""
    input_dir = Path(input_dir).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise TQHC2CandidateError(f"输出目录已存在，拒绝覆盖：{output_dir}")
    output_dir.mkdir(parents=True)
    incomplete_marker = output_dir / "_INCOMPLETE"
    incomplete_marker.write_text('{"status":"incomplete"}\n', encoding="utf-8")
    (output_dir / "splits").mkdir()
    (output_dir / "audit").mkdir()

    master, packets = _load_and_validate_inputs(input_dir)
    groups = _build_groups(master)
    groups, split_selection = _select_group_splits(groups)
    samples = _build_samples(master, packets, groups)

    samples_path = output_dir / "samples.parquet"
    groups_path = output_dir / "groups.parquet"
    samples.to_parquet(samples_path, index=False, engine="pyarrow", compression="zstd")
    groups.to_parquet(groups_path, index=False, engine="pyarrow", compression="zstd")
    _write_yaml(output_dir / "field-roles.yaml", _field_roles())
    _write_jsonl(output_dir / "source-artifacts.jsonl", _source_artifacts(input_dir))

    samples_sha256 = _sha256_file(samples_path)
    for split_id, relative_path in SPLIT_FILENAMES.items():
        split_samples = samples[samples["split_id"].eq(split_id)].sort_values(
            "sample_id", kind="mergesort"
        )
        if split_samples.empty:
            raise TQHC2CandidateError(f"开发划分不得为空：{split_id}")
        rows = [
            {
                "protocol_version": PROTOCOL_VERSION,
                "suite_id": SUITE_ID,
                "split_id": split_id,
                "sample_id": str(sample_id),
                "samples_sha256": samples_sha256,
            }
            for sample_id in split_samples["sample_id"]
        ]
        _write_jsonl(output_dir / relative_path, rows)

    manifest_hashes = {
        "samples.parquet": samples_sha256,
        **{
            relative_path: _sha256_file(output_dir / relative_path)
            for relative_path in SPLIT_FILENAMES.values()
        },
    }
    _write_json(output_dir / "audit" / "manifest-hashes.json", manifest_hashes)
    audits = _build_audits(master, samples, groups, split_selection, manifest_hashes)
    for filename, value in audits.items():
        _write_json(output_dir / "audit" / filename, value)

    artifact_list_path = output_dir / "audit" / "artifact-sha256.txt"
    artifact_paths = sorted(
        (
            path
            for path in output_dir.rglob("*")
            if path.is_file()
            and path not in {incomplete_marker, artifact_list_path, output_dir / "protocol.yaml"}
        ),
        key=lambda path: path.relative_to(output_dir).as_posix(),
    )
    artifact_list_path.write_text(
        "".join(
            f"{_sha256_file(path)}  {path.relative_to(output_dir).as_posix()}\n"
            for path in artifact_paths
        ),
        encoding="utf-8",
    )
    all_artifact_paths = [*artifact_paths, artifact_list_path]
    artifact_hashes = {
        path.relative_to(output_dir).as_posix(): _sha256_file(path)
        for path in sorted(
            all_artifact_paths, key=lambda item: item.relative_to(output_dir).as_posix()
        )
    }
    protocol = {
        "protocol_version": PROTOCOL_VERSION,
        "status": PROTOCOL_STATUS,
        "phase": PROTOCOL_PHASE,
        "review_status": REVIEW_STATUS,
        "candidate_id": CANDIDATE_ID,
        "scope": "TQH-C2 profile C only",
        "suite_id": SUITE_ID,
        "final_tuning_allowed": False,
        "final_test_claim_allowed": False,
        "artifacts": artifact_hashes,
        "limitations": [
            "这是 C+GeNIS+ns-3 理论筛选阶段的 TQH-C2 C 来源组件，不是三源完整候选集。",
            "A/B 完成并生成完整 dataset-v1 后，胜出方法必须在完整训练/验证清单上重新调参。",
            "最终测试 cell、GeNIS U_test 和留一 profile 测试域不得参与调参。",
        ],
    }
    _write_yaml(output_dir / "protocol.yaml", protocol)
    incomplete_marker.unlink()
    return {
        "candidate_id": CANDIDATE_ID,
        "protocol_version": PROTOCOL_VERSION,
        "review_status": REVIEW_STATUS,
        "protocol_sha256": _sha256_file(output_dir / "protocol.yaml"),
        "sample_count": int(len(samples)),
        "group_count": int(len(groups)),
        "split_counts": dict(sorted(Counter(samples["split_id"]).items())),
        "output_dir": str(output_dir),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="物化 TQH-C2 C 理论筛选候选协议")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = materialize_candidate(input_dir=args.input_dir, output_dir=args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
