"""为 E2 共享 PINN 构造与检测编码器同语义的物理辅助表。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from flow_probe.e2_hard_domain_data import E2_FEATURE_FIELDS

AUXILIARY_SCHEMA_VERSION = "flow_probe_e2_physics_auxiliary_v1"
AUXILIARY_TABLE_NAME = "e2-physics-auxiliary-v1.parquet"
DEFAULT_OUTPUT_ROOT = Path("runs/data-prepared/e2-physics-auxiliary-v1")
DEFAULT_PHYSICS_TABLE = Path(
    "runs/data-prepared/r2-final-tcp-udp-physics-v2/physics-targets-ns3-v2.parquet"
)
DEFAULT_NS3_ROOT = Path(
    "runs/ns3-data/r2-protocol-dynamics-v2-formal-attempt4-event-pairing-v1"
)

PHYSICS_SAMPLE_KEY = (
    "sequence_id",
    "window_index_in_sequence",
    "physics_group_sha256",
)
PHYSICS_IDENTITY_COLUMNS = (
    "split_id",
    "transport_family",
    "evaluation_cluster_id",
    "source_window_index",
    "truth_window_duration_s",
    "final_test_visible",
)
STATE_TRUTH_COLUMNS = (
    "truth_queue_start_l3_bytes",
    "truth_queue_end_l3_bytes",
    "truth_queue_start_packets",
    "truth_queue_end_packets",
)
CONSERVATION_TRUTH_COLUMNS = (
    "truth_qdisc_received_l3_bytes",
    "truth_qdisc_dequeued_l3_bytes",
    "truth_qdisc_drop_before_enqueue_l3_bytes",
    "truth_qdisc_drop_after_dequeue_l3_bytes",
    "truth_qdisc_received_packets",
    "truth_qdisc_dequeued_packets",
    "truth_qdisc_drop_before_enqueue_packets",
    "truth_qdisc_drop_after_dequeue_packets",
)
BOUNDARY_TRUTH_COLUMNS = STATE_TRUTH_COLUMNS
PHYSICS_TRUTH_COLUMNS = tuple(
    dict.fromkeys((*STATE_TRUTH_COLUMNS, *CONSERVATION_TRUTH_COLUMNS))
)
DIRECTIONAL_FEATURE_FIELDS = tuple(
    field for field in E2_FEATURE_FIELDS if field != "duration"
)
LEGACY_AGGREGATE_FIELDS = (
    "public_total_packets",
    "public_total_l3_bytes",
    "public_packet_rate_pps",
    "public_byte_rate_Bps",
)
DIAGNOSTIC_FILES = frozenset({"missing-source-report.json", "run-state.json"})


class AuxiliaryMaterializationError(RuntimeError):
    """物理辅助表物化失败。"""

    def __init__(self, code: str, message: str, **details: object) -> None:
        super().__init__(message)
        self.code = code
        self.details = details

    def to_record(self) -> dict[str, object]:
        return {"code": self.code, "message": str(self), "details": self.details}


@dataclass(frozen=True)
class MaterializationOutcome:
    status: str
    output_root: str
    table_path: str | None
    row_count: int
    binding_sha256: str | None
    missing_fields: tuple[str, ...]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalise_scalar(value: object) -> object:
    if value is None or bool(pd.isna(value)):
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float):
        if not math.isfinite(value):
            raise AuxiliaryMaterializationError(
                "non_finite_semantic_value", "语义哈希输入包含非有限浮点数"
            )
        return format(value, ".17g")
    if isinstance(value, (bool, int, str)):
        return value
    return str(value)


def _frame_semantic_sha256(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for row in frame.loc[:, list(columns)].itertuples(index=False, name=None):
        payload = [_normalise_scalar(value) for value in row]
        digest.update(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _table_columns(path: Path) -> tuple[str, ...]:
    if not path.is_file():
        raise AuxiliaryMaterializationError(
            "missing_source_table", "输入表不存在", path=str(path)
        )
    if path.suffix == ".parquet":
        return tuple(pq.read_schema(path).names)
    if path.suffix == ".csv":
        return tuple(pd.read_csv(path, nrows=0).columns)
    raise AuxiliaryMaterializationError(
        "unsupported_source_format",
        "输入表只允许 Parquet 或 CSV",
        path=str(path),
    )


def _read_table(path: Path, columns: Sequence[str]) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path, columns=list(columns))
    return pd.read_csv(path, usecols=list(columns))


def _prepare_output_root(output_root: Path) -> None:
    if not output_root.exists():
        output_root.mkdir(parents=True)
        return
    if not output_root.is_dir():
        raise AuxiliaryMaterializationError(
            "invalid_output_root", "输出路径不是目录", path=str(output_root)
        )
    existing = {path.name for path in output_root.iterdir()}
    unexpected = sorted(existing.difference(DIAGNOSTIC_FILES))
    if unexpected:
        raise AuxiliaryMaterializationError(
            "output_root_not_empty",
            "输出目录已包含非诊断制品，拒绝覆盖",
            path=str(output_root),
            entries=unexpected,
        )


def _representative_raw_header(ns3_root: Path) -> dict[str, object]:
    candidates = sorted(ns3_root.glob("shards/shard-*/runs/*/main.csv"))
    if not candidates:
        return {"status": "missing", "path": None, "columns": []}
    path = candidates[0]
    with path.open("r", encoding="utf-8", newline="") as source:
        columns = next(csv.reader(source), [])
    return {
        "status": "observed",
        "path": str(path),
        "columns": columns,
        "sha256": _sha256_file(path),
    }


def _missing_source_report(
    *,
    physics_table: Path,
    physics_columns: Sequence[str],
    ns3_root: Path,
) -> dict[str, object]:
    missing = tuple(
        field for field in DIRECTIONAL_FEATURE_FIELDS if field not in physics_columns
    )
    legacy_present = [field for field in LEGACY_AGGREGATE_FIELDS if field in physics_columns]
    return {
        "schema_version": AUXILIARY_SCHEMA_VERSION,
        "status": "blocked_missing_directional_source",
        "physics_table": {
            "path": str(physics_table),
            "sha256": _sha256_file(physics_table),
            "columns": list(physics_columns),
        },
        "exactly_derivable": {
            "duration": "truth_window_duration_s",
        },
        "missing_directional_fields": list(missing),
        "insufficient_existing_fields": legacy_present,
        "insufficiency_reason": (
            "无方向聚合包数、三层字节数、TCP 已确认字节或 UDP 应用发送量均不能唯一恢复"
            "发起方向与响应方向的载荷字节、IP 包数和 IP 字节数。"
        ),
        "representative_raw_main": _representative_raw_header(ns3_root),
        "required_directional_source": {
            "sample_key": list(PHYSICS_SAMPLE_KEY),
            "fields": list(DIRECTIONAL_FEATURE_FIELDS),
            "orientation": "发起端到响应端为 orig，反向为 resp；每个运行内必须固定",
            "window_binding": (
                "与 physics-targets-ns3-v2 的 0.1 秒窗口边界和复合样本键一致"
            ),
            "field_semantics": {
                "orig_bytes": "窗口内发起方向传输层载荷字节，不含 IP 与传输层首部",
                "resp_bytes": "窗口内响应方向传输层载荷字节，不含 IP 与传输层首部",
                "orig_pkts": "窗口内发起方向实际观测到的 IP 包数",
                "resp_pkts": "窗口内响应方向实际观测到的 IP 包数",
                "orig_ip_bytes": "窗口内发起方向包含 IP 首部的 IP 字节总数",
                "resp_ip_bytes": "窗口内响应方向包含 IP 首部的 IP 字节总数",
            },
        },
        "minimum_recovery_or_rerun": {
            "preferred": (
                "若服务器保留同一运行的双向 PCAP，按 physics_group_sha256、transport_family、"
                "source_window_index 回收 PCAP 与逐运行收据，在固定窗口内解析六个方向字段。"
            ),
            "otherwise": (
                "修改同一 ns-3 场景，在固定观测点按 orig/resp 分方向累计传输层载荷、IP 包数和"
                "IP 字节数；使用原 512 项冻结配置重跑，并回收新增 main.csv、receipt.json、"
                "matrix-state.json、matrix-summary.json、source-lock.json 与 artifact-manifest.json。"
            ),
            "forbidden": [
                "按比例拆分 public_total_packets 或 public_total_l3_bytes",
                "把 TCP acked_bytes 或 acked_segments 当作响应方向流量",
                "把 UDP 实际发送量复制为双向流量",
                "按行号关联 TQH-C2 与 ns-3 样本",
            ],
        },
        "final_test_visible": False,
    }


def _validate_physics_frame(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise AuxiliaryMaterializationError("empty_physics_table", "物理真值表为空")
    if bool(frame["final_test_visible"].astype(bool).any()):
        raise AuxiliaryMaterializationError(
            "physics_final_test_visible", "物理辅助表包含最终测试记录"
        )
    keys = frame.loc[:, list(PHYSICS_SAMPLE_KEY)].astype(str)
    if bool(keys.duplicated().any()):
        raise AuxiliaryMaterializationError(
            "duplicate_physics_sample_key", "物理真值表复合样本键不唯一"
        )
    numeric = frame.loc[:, ["truth_window_duration_s", *PHYSICS_TRUTH_COLUMNS]].apply(
        pd.to_numeric, errors="coerce"
    )
    if not np.isfinite(numeric.to_numpy(dtype=np.float64)).all():
        raise AuxiliaryMaterializationError(
            "invalid_physics_truth", "状态、守恒或边界真值包含非有限值"
        )
    if bool((numeric["truth_window_duration_s"] <= 0).any()) or bool(
        (numeric.loc[:, list(PHYSICS_TRUTH_COLUMNS)] < 0).any().any()
    ):
        raise AuxiliaryMaterializationError(
            "invalid_physics_truth", "窗口时长必须为正且物理真值必须非负"
        )


def _validate_directional_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        raise AuxiliaryMaterializationError("empty_directional_table", "方向源表为空")
    keys = frame.loc[:, list(PHYSICS_SAMPLE_KEY)].astype(str)
    if bool(keys.duplicated().any()):
        raise AuxiliaryMaterializationError(
            "duplicate_directional_sample_key", "方向源表复合样本键不唯一"
        )
    if "final_test_visible" in frame.columns and bool(
        frame["final_test_visible"].astype(bool).any()
    ):
        raise AuxiliaryMaterializationError(
            "directional_final_test_visible", "方向源表包含最终测试记录"
        )
    numeric = frame.loc[:, list(DIRECTIONAL_FEATURE_FIELDS)].apply(
        pd.to_numeric, errors="coerce"
    )
    values = numeric.to_numpy(dtype=np.float64)
    if not np.isfinite(values).all() or bool((values < 0).any()):
        raise AuxiliaryMaterializationError(
            "invalid_directional_features", "方向字段必须是有限非负数"
        )
    integral_fields = (
        "orig_pkts",
        "resp_pkts",
        "orig_ip_bytes",
        "resp_ip_bytes",
    )
    integral = numeric.loc[:, list(integral_fields)].to_numpy(dtype=np.float64)
    if not np.equal(integral, np.floor(integral)).all():
        raise AuxiliaryMaterializationError(
            "non_integral_directional_counts", "方向包数和 IP 字节数必须是整数"
        )
    if bool((numeric["orig_ip_bytes"] < numeric["orig_bytes"]).any()) or bool(
        (numeric["resp_ip_bytes"] < numeric["resp_bytes"]).any()
    ):
        raise AuxiliaryMaterializationError(
            "directional_byte_semantics_violation",
            "IP 字节数不得小于同方向传输层载荷字节数",
        )
    normalized = frame.copy()
    for field in DIRECTIONAL_FEATURE_FIELDS:
        normalized[field] = numeric[field]
    if "duration" in normalized.columns:
        normalized["duration"] = pd.to_numeric(normalized["duration"], errors="coerce")
    return normalized


def _bind_directional_features(
    physics: pd.DataFrame,
    directional: pd.DataFrame,
) -> pd.DataFrame:
    physics_keys = physics.loc[:, list(PHYSICS_SAMPLE_KEY)].astype(str)
    directional_keys = directional.loc[:, list(PHYSICS_SAMPLE_KEY)].astype(str)
    physics_key_set = set(physics_keys.itertuples(index=False, name=None))
    directional_key_set = set(directional_keys.itertuples(index=False, name=None))
    if physics_key_set != directional_key_set:
        raise AuxiliaryMaterializationError(
            "directional_key_mismatch",
            "方向源与物理真值表的复合样本键集合不一致",
            missing_in_directional=len(physics_key_set - directional_key_set),
            extra_in_directional=len(directional_key_set - physics_key_set),
        )
    selected = directional.loc[
        :, [*PHYSICS_SAMPLE_KEY, *DIRECTIONAL_FEATURE_FIELDS]
    ].copy()
    order_column = "__e2_physics_stable_order"
    if order_column in physics.columns:
        raise AuxiliaryMaterializationError(
            "reserved_column_collision", "物理真值表占用了内部稳定顺序字段"
        )
    ordered_physics = physics.copy()
    ordered_physics[order_column] = np.arange(len(physics), dtype=np.int64)
    merged = ordered_physics.merge(
        selected,
        how="left",
        on=list(PHYSICS_SAMPLE_KEY),
        sort=False,
        validate="one_to_one",
    )
    if len(merged) != len(physics):
        raise AuxiliaryMaterializationError(
            "directional_binding_row_count_mismatch", "方向源关联改变了物理样本数量"
        )
    merged = merged.sort_values(order_column, kind="stable").drop(columns=[order_column])
    expected_keys = tuple(
        physics.loc[:, list(PHYSICS_SAMPLE_KEY)].astype(str).itertuples(
            index=False, name=None
        )
    )
    observed_keys = tuple(
        merged.loc[:, list(PHYSICS_SAMPLE_KEY)].astype(str).itertuples(
            index=False, name=None
        )
    )
    if observed_keys != expected_keys:
        raise AuxiliaryMaterializationError(
            "directional_binding_order_mismatch", "方向源关联改变了物理样本稳定顺序"
        )
    merged.insert(
        len(physics.columns),
        "duration",
        pd.to_numeric(merged["truth_window_duration_s"], errors="raise"),
    )
    ordered = [*physics.columns, *E2_FEATURE_FIELDS]
    return merged.loc[:, ordered]


def _publish_missing_source(
    *,
    output_root: Path,
    physics_table: Path,
    physics_columns: Sequence[str],
    ns3_root: Path,
) -> MaterializationOutcome:
    _prepare_output_root(output_root)
    report = _missing_source_report(
        physics_table=physics_table,
        physics_columns=physics_columns,
        ns3_root=ns3_root,
    )
    _atomic_json(output_root / "missing-source-report.json", report)
    state = {
        "schema_version": AUXILIARY_SCHEMA_VERSION,
        "status": "blocked_missing_directional_source",
        "output_table_published": False,
        "missing_fields": report["missing_directional_fields"],
        "final_test_visible": False,
    }
    _atomic_json(output_root / "run-state.json", state)
    return MaterializationOutcome(
        status="blocked_missing_directional_source",
        output_root=str(output_root),
        table_path=None,
        row_count=0,
        binding_sha256=None,
        missing_fields=tuple(report["missing_directional_fields"]),
    )


def materialize_e2_physics_auxiliary(
    *,
    physics_table: Path,
    output_root: Path,
    ns3_root: Path,
    directional_table: Path | None = None,
) -> MaterializationOutcome:
    """物化 E2 物理辅助表；方向源不足时只发布结构化阻断收据。"""
    physics_table = Path(physics_table).resolve()
    output_root = Path(output_root).resolve()
    ns3_root = Path(ns3_root).resolve()
    physics_columns = _table_columns(physics_table)
    required_physics = (
        *PHYSICS_SAMPLE_KEY,
        *PHYSICS_IDENTITY_COLUMNS,
        *PHYSICS_TRUTH_COLUMNS,
    )
    missing_physics = sorted(set(required_physics).difference(physics_columns))
    if missing_physics:
        raise AuxiliaryMaterializationError(
            "missing_physics_truth_columns",
            "物理真值表缺少 E2 状态、守恒或边界字段",
            missing_columns=missing_physics,
        )

    source_path: Path
    if directional_table is None:
        if not set(DIRECTIONAL_FEATURE_FIELDS).issubset(physics_columns):
            return _publish_missing_source(
                output_root=output_root,
                physics_table=physics_table,
                physics_columns=physics_columns,
                ns3_root=ns3_root,
            )
        source_path = physics_table
    else:
        source_path = Path(directional_table).resolve()

    directional_columns = _table_columns(source_path)
    required_directional = (*PHYSICS_SAMPLE_KEY, *DIRECTIONAL_FEATURE_FIELDS)
    missing_directional = sorted(
        set(required_directional).difference(directional_columns)
    )
    if missing_directional:
        raise AuxiliaryMaterializationError(
            "missing_directional_columns",
            "显式方向源缺少必需字段",
            path=str(source_path),
            missing_columns=missing_directional,
        )

    physics = _read_table(physics_table, list(dict.fromkeys(required_physics)))
    directional_read_columns = list(required_directional)
    if "final_test_visible" in directional_columns:
        directional_read_columns.append("final_test_visible")
    if "duration" in directional_columns:
        directional_read_columns.append("duration")
    directional = _read_table(source_path, directional_read_columns)
    _validate_physics_frame(physics)
    directional = _validate_directional_frame(directional)

    if "duration" in directional.columns:
        expected = physics.loc[:, [*PHYSICS_SAMPLE_KEY, "truth_window_duration_s"]]
        observed = directional.loc[:, [*PHYSICS_SAMPLE_KEY, "duration"]]
        duration_check = expected.merge(
            observed,
            on=list(PHYSICS_SAMPLE_KEY),
            how="inner",
            validate="one_to_one",
        )
        if len(duration_check) != len(physics) or not np.allclose(
            duration_check["truth_window_duration_s"].to_numpy(dtype=np.float64),
            duration_check["duration"].to_numpy(dtype=np.float64),
            rtol=1e-9,
            atol=1e-12,
        ):
            raise AuxiliaryMaterializationError(
                "duration_semantics_mismatch",
                "方向源 duration 与物理窗口真实时长不一致",
            )

    auxiliary = _bind_directional_features(physics, directional)
    key_sha256 = _frame_semantic_sha256(auxiliary, PHYSICS_SAMPLE_KEY)
    feature_sha256 = _frame_semantic_sha256(auxiliary, E2_FEATURE_FIELDS)
    state_sha256 = _frame_semantic_sha256(auxiliary, STATE_TRUTH_COLUMNS)
    conservation_sha256 = _frame_semantic_sha256(
        auxiliary, CONSERVATION_TRUTH_COLUMNS
    )
    boundary_sha256 = _frame_semantic_sha256(auxiliary, BOUNDARY_TRUTH_COLUMNS)
    binding = {
        "sample_key": list(PHYSICS_SAMPLE_KEY),
        "sample_key_ordering_sha256": key_sha256,
        "feature_fields": list(E2_FEATURE_FIELDS),
        "feature_semantic_sha256": feature_sha256,
        "state_semantic_sha256": state_sha256,
        "conservation_semantic_sha256": conservation_sha256,
        "boundary_semantic_sha256": boundary_sha256,
        "physics_source_sha256": _sha256_file(physics_table),
        "directional_source_sha256": _sha256_file(source_path),
        "row_count": len(auxiliary),
        "final_test_visible": False,
    }
    binding_sha256 = _canonical_sha256(binding)
    binding["binding_sha256"] = binding_sha256

    _prepare_output_root(output_root)
    table_path = output_root / AUXILIARY_TABLE_NAME
    temporary = table_path.with_suffix(table_path.suffix + f".partial.{os.getpid()}")
    auxiliary.to_parquet(temporary, index=False)
    os.replace(temporary, table_path)
    table_sha256 = _sha256_file(table_path)
    schema = {
        "schema_version": AUXILIARY_SCHEMA_VERSION,
        "columns": [
            {"name": name, "dtype": str(dtype)}
            for name, dtype in auxiliary.dtypes.items()
        ],
    }
    source_lock = {
        "schema_version": AUXILIARY_SCHEMA_VERSION,
        "physics_table": str(physics_table),
        "physics_table_sha256": binding["physics_source_sha256"],
        "directional_table": str(source_path),
        "directional_table_sha256": binding["directional_source_sha256"],
        "public_detection_final_test_read": False,
    }
    artifact_manifest = {
        "schema_version": AUXILIARY_SCHEMA_VERSION,
        "artifacts": [
            {
                "path": AUXILIARY_TABLE_NAME,
                "size_bytes": table_path.stat().st_size,
                "sha256": table_sha256,
            }
        ],
    }
    run_state = {
        "schema_version": AUXILIARY_SCHEMA_VERSION,
        "status": "published",
        "output_table_published": True,
        "table": AUXILIARY_TABLE_NAME,
        "table_sha256": table_sha256,
        "row_count": len(auxiliary),
        "binding_sha256": binding_sha256,
        "final_test_visible": False,
    }
    _atomic_json(output_root / "binding.json", binding)
    _atomic_json(output_root / "schema.json", schema)
    _atomic_json(output_root / "source-lock.json", source_lock)
    _atomic_json(output_root / "artifact-manifest.json", artifact_manifest)
    _atomic_json(output_root / "run-state.json", run_state)
    return MaterializationOutcome(
        status="published",
        output_root=str(output_root),
        table_path=str(table_path),
        row_count=len(auxiliary),
        binding_sha256=binding_sha256,
        missing_fields=(),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="物化 E2 七字段物理辅助表")
    parser.add_argument("--physics-table", type=Path, default=DEFAULT_PHYSICS_TABLE)
    parser.add_argument("--directional-table", type=Path)
    parser.add_argument("--ns3-root", type=Path, default=DEFAULT_NS3_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        outcome = materialize_e2_physics_auxiliary(
            physics_table=args.physics_table,
            directional_table=args.directional_table,
            ns3_root=args.ns3_root,
            output_root=args.output_root,
        )
    except AuxiliaryMaterializationError as error:
        print(json.dumps(error.to_record(), ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(asdict(outcome), ensure_ascii=False, sort_keys=True))
    return 0 if outcome.status == "published" else 2


if __name__ == "__main__":
    raise SystemExit(main())
