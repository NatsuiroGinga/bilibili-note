"""生成 R2 ns-3 TCP/普通 UDP 严格配对配置矩阵。"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields
from pathlib import Path, PurePosixPath
from typing import Final

import yaml

SCHEMA_VERSION: Final = "flow_probe_r2_ns3_protocol_matrix_v1"
EXPECTED_TCP_CONGESTION_CONTROL: Final = "ns3::TcpNewReno"
# 任务04R只修正运行身份，不得改变已预注册的随机种子与协议顺序。
FROZEN_ASSIGNMENT_MATRIX_CONFIG_SHA256: Final = (
    "971e91659e6c1cc00b575823d384bfaf2975139cb022dd924a96ccc6dda22565"
)
FROZEN_ASSIGNMENT_R2_CONTRACT_SHA256: Final = (
    "0793d00a3b67a20960b32efb33c5a5e45cd5bae04d2e7bb24d5e7cd629c5a935"
)
FROZEN_ASSIGNMENT_TCP_CONGESTION_CONTROL: Final = "ns3::TcpCubic"
PROTOCOLS: Final = ("TCP", "UDP")
SPLIT_ORDER: Final = (
    "train-fit",
    "calibration",
    "validation",
    "test",
    "unseen-configuration",
)
SPLIT_BASE_COUNTS: Final = {
    "train-fit": 128,
    "calibration": 32,
    "validation": 32,
    "test": 32,
    "unseen-configuration": 32,
}
REPLICAS_PER_FACTOR_CELL: Final = {
    "train-fit": 4,
    "calibration": 1,
    "validation": 1,
    "test": 1,
    "unseen-configuration": 2,
}
TRAFFIC_MODES: Final = ("benign", "dos")
ARRIVAL_MODELS: Final = ("constant", "bursty")
IN_DISTRIBUTION_QUEUE_MODELS: Final = ("fifo", "codel")
UNSEEN_QUEUE_MODELS: Final = ("red",)
OFFERED_LOAD_RATIOS: Final = (0.35, 0.70, 1.05, 1.40)

BASE_FIELD_ORDER: Final = (
    "schema_version",
    "matrix_config_sha256",
    "r2_contract_sha256",
    "physics_group_sha256",
    "seed_basis_sha256",
    "split",
    "replicate_key_sha256",
    "run_seed",
    "matrix_seed",
    "topology_id",
    "ns3_version",
    "tcp_congestion_control",
    "duration_seconds",
    "window_seconds",
    "windows_per_run",
    "sequence_length_windows",
    "sequences_per_run",
    "traffic_mode",
    "binary_label",
    "arrival_model",
    "queue_model",
    "offered_load_ratio",
    "initial_capacity_mbps",
    "capacity_change_multiplier",
    "shifted_capacity_mbps",
    "capacity_change_time_seconds",
    "access_delay_ms",
    "bottleneck_delay_ms",
    "queue_limit_packets",
    "downstream_loss_rate",
    "sender_count",
    "benign_sender_count",
    "attack_sender_count",
    "total_offered_load_mbps",
    "per_sender_offered_load_mbps",
    "packet_size_bytes",
    "burst_on_seconds",
    "burst_off_seconds",
)
MANIFEST_FIELD_ORDER: Final = (*BASE_FIELD_ORDER, "transport_family")
DERIVED_IDENTITY_FIELDS: Final = {
    "physics_group_sha256",
    "seed_basis_sha256",
    "run_seed",
}


class R2NS3MatrixError(ValueError):
    """矩阵配置、配对关系或冻结输出违反 R2 合同。"""


@dataclass(frozen=True)
class ParameterGrid:
    """一个矩阵范围内可独立哈希选择的环境参数网格。"""

    initial_capacity_mbps: tuple[float, ...]
    capacity_change_multiplier: tuple[float, ...]
    access_delay_ms: tuple[float, ...]
    bottleneck_delay_ms: tuple[float, ...]
    queue_limit_packets: tuple[int, ...]
    downstream_loss_rate: tuple[float, ...]


@dataclass(frozen=True)
class R2NS3MatrixConfig:
    """通过共享 R2 合同核验后的完整 ns-3 矩阵配置。"""

    schema_version: str
    matrix_seed: int
    matrix_config_sha256: str
    r2_contract_sha256: str
    project_root: Path
    output_directory: PurePosixPath
    manifest_filename: str
    checksum_filename: str
    manifest_field_order: tuple[str, ...]
    protocols: tuple[str, ...]
    split_order: tuple[str, ...]
    split_base_counts: Mapping[str, int]
    replicas_per_factor_cell: Mapping[str, int]
    traffic_modes: tuple[str, ...]
    binary_labels: Mapping[str, int]
    arrival_models: tuple[str, ...]
    in_distribution_queue_models: tuple[str, ...]
    unseen_queue_models: tuple[str, ...]
    offered_load_ratios: tuple[float, ...]
    duration_seconds: float
    window_seconds: float
    windows_per_run: int
    sequence_length_windows: int
    sequences_per_run: int
    topology_id: str
    ns3_version: str
    tcp_congestion_control: str
    capacity_change_time_seconds: float
    packet_size_bytes: int
    burst_on_seconds: float
    burst_off_seconds: float
    sender_composition: Mapping[str, tuple[int, int]]
    parameter_grids: Mapping[str, ParameterGrid]
    paired_completion_minimum: float
    tcp_cwnd_window_coverage_minimum: float
    factor_cell_minimums: Mapping[str, int]
    sequence_minimums: Mapping[str, int]


@dataclass(frozen=True)
class BaseProtocolConfig:
    """不含传输协议维度的基础配置。"""

    schema_version: str
    matrix_config_sha256: str
    r2_contract_sha256: str
    physics_group_sha256: str
    seed_basis_sha256: str
    split: str
    replicate_key_sha256: str
    run_seed: int
    matrix_seed: int
    topology_id: str
    ns3_version: str
    tcp_congestion_control: str
    duration_seconds: float
    window_seconds: float
    windows_per_run: int
    sequence_length_windows: int
    sequences_per_run: int
    traffic_mode: str
    binary_label: int
    arrival_model: str
    queue_model: str
    offered_load_ratio: float
    initial_capacity_mbps: float
    capacity_change_multiplier: float
    shifted_capacity_mbps: float
    capacity_change_time_seconds: float
    access_delay_ms: float
    bottleneck_delay_ms: float
    queue_limit_packets: int
    downstream_loss_rate: float
    sender_count: int
    benign_sender_count: int
    attack_sender_count: int
    total_offered_load_mbps: float
    per_sender_offered_load_mbps: float
    packet_size_bytes: int
    burst_on_seconds: float
    burst_off_seconds: float

    @property
    def config_id(self) -> str:
        """返回不含协议、标签文本或顺序编号的不可逆配置标识。"""
        return self.physics_group_sha256

    def to_record(self) -> dict[str, object]:
        """按冻结字段顺序返回基础记录。"""
        record = asdict(self)
        if tuple(record) != BASE_FIELD_ORDER:
            raise R2NS3MatrixError("基础配置字段顺序偏离冻结合同")
        return record


@dataclass(frozen=True)
class ProtocolRunConfig(BaseProtocolConfig):
    """基础配置增加最后一个协议笛卡尔维度后的运行配置。"""

    transport_family: str

    def to_record(self) -> dict[str, object]:
        """按冻结字段顺序返回公开运行记录。"""
        record = asdict(self)
        if tuple(record) != MANIFEST_FIELD_ORDER:
            raise R2NS3MatrixError("运行配置字段顺序偏离冻结合同")
        return record

    def to_base_record(self) -> dict[str, object]:
        """移除唯一允许变化的协议维度。"""
        record = self.to_record()
        del record["transport_family"]
        return record


@dataclass(frozen=True)
class MatrixReceipt:
    """正式冻结清单的确定性回执。"""

    manifest_path: Path
    checksum_path: Path
    manifest_sha256: str
    checksum_sha256: str
    manifest_size_bytes: int
    matrix_config_sha256: str
    r2_contract_sha256: str
    base_configuration_count: int
    protocol_run_count: int
    split_base_configuration_counts: Mapping[str, int]
    split_protocol_run_counts: Mapping[str, int]

    def to_record(self) -> dict[str, object]:
        """转换为可打印回执。"""
        return {
            "manifest_path": str(self.manifest_path),
            "checksum_path": str(self.checksum_path),
            "manifest_sha256": self.manifest_sha256,
            "checksum_sha256": self.checksum_sha256,
            "manifest_size_bytes": self.manifest_size_bytes,
            "matrix_config_sha256": self.matrix_config_sha256,
            "r2_contract_sha256": self.r2_contract_sha256,
            "base_configuration_count": self.base_configuration_count,
            "protocol_run_count": self.protocol_run_count,
            "split_base_configuration_counts": dict(self.split_base_configuration_counts),
            "split_protocol_run_counts": dict(self.split_protocol_run_counts),
        }


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise R2NS3MatrixError(f"{name} 必须是映射")
    return value


def _require_keys(value: Mapping[str, object], expected: set[str], name: str) -> None:
    actual = set(value)
    if actual != expected:
        raise R2NS3MatrixError(
            f"{name} 键集合不符，缺少 {sorted(expected - actual)}，多出 {sorted(actual - expected)}"
        )


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise R2NS3MatrixError(f"{name} 必须是非空列表")
    result = tuple(value)
    if any(not isinstance(item, str) or not item for item in result):
        raise R2NS3MatrixError(f"{name} 只能包含非空字符串")
    if len(result) != len(set(result)):
        raise R2NS3MatrixError(f"{name} 包含重复值")
    return result


def _number_tuple(value: object, name: str, *, integral: bool = False) -> tuple[float, ...] | tuple[int, ...]:
    if not isinstance(value, list) or not value:
        raise R2NS3MatrixError(f"{name} 必须是非空列表")
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        raise R2NS3MatrixError(f"{name} 只能包含数值")
    if integral:
        if any(not isinstance(item, int) for item in value):
            raise R2NS3MatrixError(f"{name} 只能包含整数")
        result_int = tuple(int(item) for item in value)
        if any(item <= 0 for item in result_int):
            raise R2NS3MatrixError(f"{name} 只能包含正整数")
        return result_int
    result_float = tuple(float(item) for item in value)
    if any(item < 0 for item in result_float):
        raise R2NS3MatrixError(f"{name} 不能包含负数")
    return result_float


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise R2NS3MatrixError(f"{name} 必须是正整数")
    return value


def _positive_float(value: object, name: str, *, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise R2NS3MatrixError(f"{name} 必须是数值")
    result = float(value)
    if result < 0 or (result == 0 and not allow_zero):
        relation = "非负" if allow_zero else "正"
        raise R2NS3MatrixError(f"{name} 必须是{relation}数")
    return result


def _relative_path(value: object, name: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise R2NS3MatrixError(f"{name} 必须是正斜杠相对路径")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise R2NS3MatrixError(f"{name} 不得是绝对路径或包含路径穿越")
    return path


def _parse_grid(value: object, name: str) -> ParameterGrid:
    mapping = _mapping(value, name)
    expected = {
        "initial_capacity_mbps",
        "capacity_change_multiplier",
        "access_delay_ms",
        "bottleneck_delay_ms",
        "queue_limit_packets",
        "downstream_loss_rate",
    }
    _require_keys(mapping, expected, name)
    queue_limits = _number_tuple(mapping["queue_limit_packets"], f"{name}.queue_limit_packets", integral=True)
    return ParameterGrid(
        initial_capacity_mbps=tuple(
            float(item)
            for item in _number_tuple(mapping["initial_capacity_mbps"], f"{name}.initial_capacity_mbps")
        ),
        capacity_change_multiplier=tuple(
            float(item)
            for item in _number_tuple(
                mapping["capacity_change_multiplier"], f"{name}.capacity_change_multiplier"
            )
        ),
        access_delay_ms=tuple(
            float(item)
            for item in _number_tuple(mapping["access_delay_ms"], f"{name}.access_delay_ms")
        ),
        bottleneck_delay_ms=tuple(
            float(item)
            for item in _number_tuple(
                mapping["bottleneck_delay_ms"], f"{name}.bottleneck_delay_ms"
            )
        ),
        queue_limit_packets=tuple(int(item) for item in queue_limits),
        downstream_loss_rate=tuple(
            float(item)
            for item in _number_tuple(
                mapping["downstream_loss_rate"], f"{name}.downstream_loss_rate"
            )
        ),
    )


def _read_count_mapping(value: object, name: str) -> dict[str, int]:
    mapping = _mapping(value, name)
    if set(mapping) != set(SPLIT_ORDER):
        raise R2NS3MatrixError(f"{name} 必须精确覆盖五个冻结划分")
    return {split: _positive_int(mapping[split], f"{name}.{split}") for split in SPLIT_ORDER}


def _validate_shared_contract(raw: Mapping[str, object], config: R2NS3MatrixConfig) -> None:
    if raw.get("schema_version") != "flow_probe_r2_protocol_contract_v1":
        raise R2NS3MatrixError("共享 R2 配置模式版本不符")
    protocol = _mapping(raw.get("protocol"), "共享配置 protocol")
    enums = _mapping(protocol.get("enums"), "共享配置 protocol.enums")
    transports = _string_tuple(enums.get("transport_family"), "共享传输族枚举")
    if transports[:2] != config.protocols:
        raise R2NS3MatrixError("TCP/UDP 枚举顺序与共享 R2 配置不一致")
    matrix = _mapping(raw.get("ns3_matrix"), "共享配置 ns3_matrix")
    exact_values: dict[str, object] = {
        "seed": config.matrix_seed,
        "run_duration_seconds": config.duration_seconds,
        "window_seconds": config.window_seconds,
        "windows_per_run": config.windows_per_run,
        "sequence_length_windows": config.sequence_length_windows,
        "sequences_per_run": config.sequences_per_run,
        "split_base_configuration_counts": dict(config.split_base_counts),
        "base_configuration_count": 256,
        "protocol_run_count": 512,
        "window_count": 61_440,
        "sequence_count": 15_360,
        "paired_completion_minimum": config.paired_completion_minimum,
        "tcp_cwnd_window_coverage_minimum": config.tcp_cwnd_window_coverage_minimum,
        "factor_cell_minimums": dict(config.factor_cell_minimums),
        "sequence_minimums_per_transport_and_label": dict(config.sequence_minimums),
    }
    for key, expected in exact_values.items():
        if matrix.get(key) != expected:
            raise R2NS3MatrixError(
                f"任务04配置与共享 R2 配置的 ns3_matrix.{key} 不一致"
            )


def _validate_matrix_config(config: R2NS3MatrixConfig) -> None:
    if config.schema_version != SCHEMA_VERSION:
        raise R2NS3MatrixError(f"矩阵模式版本必须为 {SCHEMA_VERSION}")
    if config.matrix_seed != 20_260_731:
        raise R2NS3MatrixError("矩阵主种子必须为 20260731")
    if config.tcp_congestion_control != EXPECTED_TCP_CONGESTION_CONTROL:
        raise R2NS3MatrixError(
            f"第一轮 TCP 拥塞控制必须为 {EXPECTED_TCP_CONGESTION_CONTROL}"
        )
    if config.protocols != PROTOCOLS:
        raise R2NS3MatrixError("协议维度必须依次为 TCP 与普通 UDP")
    if config.split_order != SPLIT_ORDER:
        raise R2NS3MatrixError("划分顺序偏离冻结合同")
    if dict(config.split_base_counts) != SPLIT_BASE_COUNTS:
        raise R2NS3MatrixError("基础配置数量偏离 128/32/32/32/32 合同")
    if dict(config.replicas_per_factor_cell) != REPLICAS_PER_FACTOR_CELL:
        raise R2NS3MatrixError("各因子单元的重复数偏离冻结合同")
    if config.traffic_modes != TRAFFIC_MODES or config.binary_labels != {"benign": 0, "dos": 1}:
        raise R2NS3MatrixError("流量模式或二元标签映射偏离冻结合同")
    if config.arrival_models != ARRIVAL_MODELS:
        raise R2NS3MatrixError("到达过程枚举偏离冻结合同")
    if config.in_distribution_queue_models != IN_DISTRIBUTION_QUEUE_MODELS:
        raise R2NS3MatrixError("同分布队列必须为 fifo/codel")
    if config.unseen_queue_models != UNSEEN_QUEUE_MODELS:
        raise R2NS3MatrixError("未见配置队列必须只含 red")
    if config.offered_load_ratios != OFFERED_LOAD_RATIOS:
        raise R2NS3MatrixError("负载带必须为 0.35/0.70/1.05/1.40")
    if (config.duration_seconds, config.window_seconds) != (12.0, 0.1):
        raise R2NS3MatrixError("运行时长或窗口宽度偏离冻结合同")
    if (config.windows_per_run, config.sequence_length_windows, config.sequences_per_run) != (
        120,
        4,
        30,
    ):
        raise R2NS3MatrixError("窗口数或四窗序列数偏离冻结合同")
    if config.manifest_filename != "ns3-config-manifest.jsonl":
        raise R2NS3MatrixError("正式清单文件名偏离冻结合同")
    if config.checksum_filename != "ns3-config-manifest.sha256":
        raise R2NS3MatrixError("正式校验文件名偏离冻结合同")
    if config.manifest_field_order != MANIFEST_FIELD_ORDER:
        raise R2NS3MatrixError("配置声明的清单字段顺序偏离实现合同")
    if tuple(field.name for field in fields(ProtocolRunConfig)) != MANIFEST_FIELD_ORDER:
        raise R2NS3MatrixError("运行数据类字段顺序偏离实现合同")

    in_grid = config.parameter_grids.get("in_distribution")
    unseen_grid = config.parameter_grids.get("unseen_configuration")
    if in_grid != ParameterGrid(
        (10.0, 20.0),
        (0.5, 1.0),
        (1.0, 5.0),
        (5.0, 20.0),
        (32, 128),
        (0.0, 0.01),
    ):
        raise R2NS3MatrixError("同分布环境参数网格偏离冻结合同")
    if unseen_grid != ParameterGrid(
        (5.0, 40.0),
        (0.25, 1.5),
        (0.25, 8.0),
        (50.0, 100.0),
        (8, 256),
        (0.03, 0.05),
    ):
        raise R2NS3MatrixError("未见配置环境参数网格偏离冻结合同")

    for split in SPLIT_ORDER:
        queues = UNSEEN_QUEUE_MODELS if split == "unseen-configuration" else IN_DISTRIBUTION_QUEUE_MODELS
        expected = (
            len(TRAFFIC_MODES)
            * len(ARRIVAL_MODELS)
            * len(queues)
            * len(OFFERED_LOAD_RATIOS)
            * config.replicas_per_factor_cell[split]
        )
        if expected != config.split_base_counts[split]:
            raise R2NS3MatrixError(f"{split} 的因子积与冻结基础配置数不一致")

    sender_totals = set()
    for traffic_mode in TRAFFIC_MODES:
        benign_count, attack_count = config.sender_composition[traffic_mode]
        if benign_count < 0 or attack_count < 0 or benign_count + attack_count <= 0:
            raise R2NS3MatrixError("发送者组成必须为非负计数且总数为正")
        sender_totals.add(benign_count + attack_count)
    if len(sender_totals) != 1:
        raise R2NS3MatrixError("良性与攻击配置必须保持相同发送者总数")
    if config.sender_composition["benign"][1] != 0:
        raise R2NS3MatrixError("良性配置不得包含攻击发送者")
    if config.sender_composition["dos"][1] <= 0:
        raise R2NS3MatrixError("DoS 配置必须包含攻击发送者")


def load_matrix_config(path: Path) -> R2NS3MatrixConfig:
    """加载矩阵配置并在正式路径中核验共享任务01合同。"""
    config_path = Path(path).expanduser().resolve()
    if not config_path.is_file():
        raise R2NS3MatrixError(f"矩阵配置不存在：{config_path}")
    raw_bytes = config_path.read_bytes()
    loaded = yaml.safe_load(raw_bytes)
    raw = _mapping(loaded, "矩阵配置")
    top_keys = {
        "schema_version",
        "matrix_seed",
        "shared_contract",
        "manifest",
        "protocols",
        "split_order",
        "split_base_configuration_counts",
        "replicas_per_factor_cell",
        "factors",
        "timing",
        "topology",
        "sender_composition",
        "parameter_grids",
        "coverage",
    }
    _require_keys(raw, top_keys, "矩阵配置")

    shared = _mapping(raw["shared_contract"], "shared_contract")
    _require_keys(shared, {"path", "schema_version"}, "shared_contract")
    if shared["schema_version"] != "flow_probe_r2_protocol_contract_v1":
        raise R2NS3MatrixError("shared_contract.schema_version 不符")
    shared_relative = _relative_path(shared["path"], "shared_contract.path")

    manifest = _mapping(raw["manifest"], "manifest")
    _require_keys(
        manifest,
        {"output_directory", "manifest_filename", "checksum_filename", "field_order"},
        "manifest",
    )
    output_directory = _relative_path(manifest["output_directory"], "manifest.output_directory")
    field_order = _string_tuple(manifest["field_order"], "manifest.field_order")

    factors = _mapping(raw["factors"], "factors")
    _require_keys(
        factors,
        {
            "traffic_modes",
            "binary_labels",
            "arrival_models",
            "in_distribution_queue_models",
            "unseen_queue_models",
            "offered_load_ratios",
        },
        "factors",
    )
    binary_raw = _mapping(factors["binary_labels"], "factors.binary_labels")
    binary_labels = {
        key: _positive_int(value + 1, f"factors.binary_labels.{key}") - 1
        if isinstance(value, int) and not isinstance(value, bool)
        else -1
        for key, value in binary_raw.items()
    }
    if any(value not in (0, 1) for value in binary_labels.values()):
        raise R2NS3MatrixError("二元标签只能为 0 或 1")

    timing = _mapping(raw["timing"], "timing")
    _require_keys(
        timing,
        {
            "duration_seconds",
            "window_seconds",
            "windows_per_run",
            "sequence_length_windows",
            "sequences_per_run",
        },
        "timing",
    )
    topology = _mapping(raw["topology"], "topology")
    _require_keys(
        topology,
        {
            "topology_id",
            "ns3_version",
            "tcp_congestion_control",
            "capacity_change_time_seconds",
            "packet_size_bytes",
            "burst_on_seconds",
            "burst_off_seconds",
        },
        "topology",
    )
    for key in ("topology_id", "ns3_version", "tcp_congestion_control"):
        if not isinstance(topology[key], str) or not topology[key]:
            raise R2NS3MatrixError(f"topology.{key} 必须是非空字符串")

    composition_raw = _mapping(raw["sender_composition"], "sender_composition")
    sender_composition: dict[str, tuple[int, int]] = {}
    for traffic_mode, value in composition_raw.items():
        item = _mapping(value, f"sender_composition.{traffic_mode}")
        _require_keys(item, {"benign_senders", "attack_senders"}, f"sender_composition.{traffic_mode}")
        counts: list[int] = []
        for key in ("benign_senders", "attack_senders"):
            count = item[key]
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise R2NS3MatrixError(f"sender_composition.{traffic_mode}.{key} 必须是非负整数")
            counts.append(count)
        sender_composition[traffic_mode] = (counts[0], counts[1])

    grids_raw = _mapping(raw["parameter_grids"], "parameter_grids")
    _require_keys(grids_raw, {"in_distribution", "unseen_configuration"}, "parameter_grids")
    parameter_grids = {
        name: _parse_grid(value, f"parameter_grids.{name}") for name, value in grids_raw.items()
    }

    coverage = _mapping(raw["coverage"], "coverage")
    _require_keys(
        coverage,
        {
            "paired_completion_minimum",
            "tcp_cwnd_window_coverage_minimum",
            "factor_cell_minimums",
            "sequence_minimums_per_transport_and_label",
        },
        "coverage",
    )

    project_root = config_path.parent.parent
    shared_path = project_root / Path(*shared_relative.parts)
    if not shared_path.is_file():
        raise R2NS3MatrixError(f"共享 R2 配置不存在：{shared_path}")
    shared_bytes = shared_path.read_bytes()
    shared_raw = _mapping(yaml.safe_load(shared_bytes), "共享 R2 配置")

    config = R2NS3MatrixConfig(
        schema_version=str(raw["schema_version"]),
        matrix_seed=_positive_int(raw["matrix_seed"], "matrix_seed"),
        matrix_config_sha256=_sha256_bytes(raw_bytes),
        r2_contract_sha256=_sha256_bytes(shared_bytes),
        project_root=project_root,
        output_directory=output_directory,
        manifest_filename=str(manifest["manifest_filename"]),
        checksum_filename=str(manifest["checksum_filename"]),
        manifest_field_order=field_order,
        protocols=_string_tuple(raw["protocols"], "protocols"),
        split_order=_string_tuple(raw["split_order"], "split_order"),
        split_base_counts=_read_count_mapping(
            raw["split_base_configuration_counts"], "split_base_configuration_counts"
        ),
        replicas_per_factor_cell=_read_count_mapping(
            raw["replicas_per_factor_cell"], "replicas_per_factor_cell"
        ),
        traffic_modes=_string_tuple(factors["traffic_modes"], "factors.traffic_modes"),
        binary_labels=binary_labels,
        arrival_models=_string_tuple(factors["arrival_models"], "factors.arrival_models"),
        in_distribution_queue_models=_string_tuple(
            factors["in_distribution_queue_models"], "factors.in_distribution_queue_models"
        ),
        unseen_queue_models=_string_tuple(
            factors["unseen_queue_models"], "factors.unseen_queue_models"
        ),
        offered_load_ratios=tuple(
            float(item)
            for item in _number_tuple(
                factors["offered_load_ratios"], "factors.offered_load_ratios"
            )
        ),
        duration_seconds=_positive_float(timing["duration_seconds"], "timing.duration_seconds"),
        window_seconds=_positive_float(timing["window_seconds"], "timing.window_seconds"),
        windows_per_run=_positive_int(timing["windows_per_run"], "timing.windows_per_run"),
        sequence_length_windows=_positive_int(
            timing["sequence_length_windows"], "timing.sequence_length_windows"
        ),
        sequences_per_run=_positive_int(
            timing["sequences_per_run"], "timing.sequences_per_run"
        ),
        topology_id=str(topology["topology_id"]),
        ns3_version=str(topology["ns3_version"]),
        tcp_congestion_control=str(topology["tcp_congestion_control"]),
        capacity_change_time_seconds=_positive_float(
            topology["capacity_change_time_seconds"],
            "topology.capacity_change_time_seconds",
            allow_zero=True,
        ),
        packet_size_bytes=_positive_int(topology["packet_size_bytes"], "topology.packet_size_bytes"),
        burst_on_seconds=_positive_float(topology["burst_on_seconds"], "topology.burst_on_seconds"),
        burst_off_seconds=_positive_float(topology["burst_off_seconds"], "topology.burst_off_seconds"),
        sender_composition=sender_composition,
        parameter_grids=parameter_grids,
        paired_completion_minimum=_positive_float(
            coverage["paired_completion_minimum"], "coverage.paired_completion_minimum"
        ),
        tcp_cwnd_window_coverage_minimum=_positive_float(
            coverage["tcp_cwnd_window_coverage_minimum"],
            "coverage.tcp_cwnd_window_coverage_minimum",
        ),
        factor_cell_minimums=_read_count_mapping(
            coverage["factor_cell_minimums"], "coverage.factor_cell_minimums"
        ),
        sequence_minimums=_read_count_mapping(
            coverage["sequence_minimums_per_transport_and_label"],
            "coverage.sequence_minimums_per_transport_and_label",
        ),
    )
    _validate_matrix_config(config)
    _validate_shared_contract(shared_raw, config)
    return config


def _replicate_key(config: R2NS3MatrixConfig, split: str, replica_slot: int) -> str:
    payload = {
        "domain": "r2-ns3-replicate-key-v1",
        "matrix_seed": config.matrix_seed,
        "split": split,
        "replica_slot": replica_slot,
    }
    return _sha256_bytes(_canonical_json(payload).encode("ascii"))


def _select_grid_value(
    selection_basis: Mapping[str, object], field_name: str, values: Sequence[int | float]
) -> int | float:
    payload = {
        "domain": "r2-ns3-independent-grid-selection-v1",
        "basis": dict(selection_basis),
        "field": field_name,
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("ascii")).digest()
    return values[int.from_bytes(digest[:8], "big") % len(values)]


def _derive_run_seed(seed_basis_sha256: str) -> int:
    run_seed = int.from_bytes(bytes.fromhex(seed_basis_sha256)[:8], "big") & 0x7FFF_FFFF
    return run_seed or 1


def _seed_payload_from_record(record: Mapping[str, object]) -> dict[str, object]:
    payload = {
        key: value
        for key, value in record.items()
        if key not in DERIVED_IDENTITY_FIELDS and key != "transport_family"
    }
    payload["matrix_config_sha256"] = FROZEN_ASSIGNMENT_MATRIX_CONFIG_SHA256
    payload["r2_contract_sha256"] = FROZEN_ASSIGNMENT_R2_CONTRACT_SHA256
    payload["tcp_congestion_control"] = FROZEN_ASSIGNMENT_TCP_CONGESTION_CONTROL
    return payload


def _group_payload_from_record(record: Mapping[str, object]) -> dict[str, object]:
    payload = {
        key: value
        for key, value in record.items()
        if key != "physics_group_sha256" and key != "transport_family"
    }
    payload["matrix_config_sha256"] = FROZEN_ASSIGNMENT_MATRIX_CONFIG_SHA256
    payload["r2_contract_sha256"] = FROZEN_ASSIGNMENT_R2_CONTRACT_SHA256
    payload["tcp_congestion_control"] = FROZEN_ASSIGNMENT_TCP_CONGESTION_CONTROL
    return payload


def _make_base_config(
    config: R2NS3MatrixConfig,
    *,
    split: str,
    traffic_mode: str,
    arrival_model: str,
    queue_model: str,
    offered_load_ratio: float,
    replica_slot: int,
) -> BaseProtocolConfig:
    replicate_key = _replicate_key(config, split, replica_slot)
    grid_name = "unseen_configuration" if split == "unseen-configuration" else "in_distribution"
    grid = config.parameter_grids[grid_name]
    selection_basis = {
        "matrix_seed": config.matrix_seed,
        "split": split,
        "replicate_key_sha256": replicate_key,
        "arrival_model": arrival_model,
        "queue_model": queue_model,
        "offered_load_ratio": offered_load_ratio,
    }
    initial_capacity = float(
        _select_grid_value(selection_basis, "initial_capacity_mbps", grid.initial_capacity_mbps)
    )
    capacity_multiplier = float(
        _select_grid_value(
            selection_basis,
            "capacity_change_multiplier",
            grid.capacity_change_multiplier,
        )
    )
    access_delay = float(
        _select_grid_value(selection_basis, "access_delay_ms", grid.access_delay_ms)
    )
    bottleneck_delay = float(
        _select_grid_value(selection_basis, "bottleneck_delay_ms", grid.bottleneck_delay_ms)
    )
    queue_limit = int(
        _select_grid_value(selection_basis, "queue_limit_packets", grid.queue_limit_packets)
    )
    downstream_loss = float(
        _select_grid_value(selection_basis, "downstream_loss_rate", grid.downstream_loss_rate)
    )
    benign_senders, attack_senders = config.sender_composition[traffic_mode]
    sender_count = benign_senders + attack_senders
    total_offered_load = round(initial_capacity * offered_load_ratio, 6)

    record_payload: dict[str, object] = {
        "schema_version": config.schema_version,
        "matrix_config_sha256": config.matrix_config_sha256,
        "r2_contract_sha256": config.r2_contract_sha256,
        "split": split,
        "replicate_key_sha256": replicate_key,
        "matrix_seed": config.matrix_seed,
        "topology_id": config.topology_id,
        "ns3_version": config.ns3_version,
        "tcp_congestion_control": config.tcp_congestion_control,
        "duration_seconds": config.duration_seconds,
        "window_seconds": config.window_seconds,
        "windows_per_run": config.windows_per_run,
        "sequence_length_windows": config.sequence_length_windows,
        "sequences_per_run": config.sequences_per_run,
        "traffic_mode": traffic_mode,
        "binary_label": config.binary_labels[traffic_mode],
        "arrival_model": arrival_model,
        "queue_model": queue_model,
        "offered_load_ratio": offered_load_ratio,
        "initial_capacity_mbps": initial_capacity,
        "capacity_change_multiplier": capacity_multiplier,
        "shifted_capacity_mbps": round(initial_capacity * capacity_multiplier, 6),
        "capacity_change_time_seconds": config.capacity_change_time_seconds,
        "access_delay_ms": access_delay,
        "bottleneck_delay_ms": bottleneck_delay,
        "queue_limit_packets": queue_limit,
        "downstream_loss_rate": downstream_loss,
        "sender_count": sender_count,
        "benign_sender_count": benign_senders,
        "attack_sender_count": attack_senders,
        "total_offered_load_mbps": total_offered_load,
        "per_sender_offered_load_mbps": round(total_offered_load / sender_count, 6),
        "packet_size_bytes": config.packet_size_bytes,
        "burst_on_seconds": config.burst_on_seconds,
        "burst_off_seconds": config.burst_off_seconds,
    }
    seed_payload = _seed_payload_from_record(record_payload)
    seed_basis_sha256 = _sha256_bytes(_canonical_json(seed_payload).encode("ascii"))
    run_seed = _derive_run_seed(seed_basis_sha256)
    group_payload = {
        **seed_payload,
        "seed_basis_sha256": seed_basis_sha256,
        "run_seed": run_seed,
    }
    physics_group_sha256 = _sha256_bytes(_canonical_json(group_payload).encode("ascii"))
    return BaseProtocolConfig(
        physics_group_sha256=physics_group_sha256,
        seed_basis_sha256=seed_basis_sha256,
        run_seed=run_seed,
        **record_payload,
    )


def _validate_base_configs(
    configs: Sequence[BaseProtocolConfig], matrix_config: R2NS3MatrixConfig | None = None
) -> None:
    if len(configs) != 256:
        raise R2NS3MatrixError(f"基础配置必须恰为 256 条，实际为 {len(configs)}")
    group_ids = [item.physics_group_sha256 for item in configs]
    seed_bases = [item.seed_basis_sha256 for item in configs]
    run_seeds = [item.run_seed for item in configs]
    if len(set(group_ids)) != len(group_ids):
        raise R2NS3MatrixError("physics_group_sha256 存在重复")
    if len(set(seed_bases)) != len(seed_bases):
        raise R2NS3MatrixError("种子哈希基底存在重复")
    if len(set(run_seeds)) != len(run_seeds):
        raise R2NS3MatrixError("31 位运行种子发生碰撞")

    split_counts = Counter(item.split for item in configs)
    if dict(split_counts) != SPLIT_BASE_COUNTS:
        raise R2NS3MatrixError(f"基础配置划分数量不符：{dict(split_counts)}")
    factor_counts = Counter(
        (
            item.split,
            item.traffic_mode,
            item.arrival_model,
            item.queue_model,
            item.offered_load_ratio,
        )
        for item in configs
    )
    for key, count in factor_counts.items():
        if count != REPLICAS_PER_FACTOR_CELL[key[0]]:
            raise R2NS3MatrixError(f"因子单元 {key} 的重复数不符：{count}")
    expected_cell_count = 32 * 4 + 32 + 32 + 32 + 16 * 2
    if sum(factor_counts.values()) != expected_cell_count:
        raise R2NS3MatrixError("因子单元总量不符")

    matched_labels: dict[tuple[object, ...], list[BaseProtocolConfig]] = defaultdict(list)
    for item in configs:
        record = item.to_record()
        seed_payload = _seed_payload_from_record(record)
        expected_seed_basis = _sha256_bytes(_canonical_json(seed_payload).encode("ascii"))
        if item.seed_basis_sha256 != expected_seed_basis:
            raise R2NS3MatrixError("seed_basis_sha256 无法从基础配置复算")
        if item.run_seed != _derive_run_seed(expected_seed_basis):
            raise R2NS3MatrixError("运行种子未按哈希前 8 字节映射为非零 31 位整数")
        expected_group = _sha256_bytes(
            _canonical_json(_group_payload_from_record(record)).encode("ascii")
        )
        if item.physics_group_sha256 != expected_group:
            raise R2NS3MatrixError("physics_group_sha256 无法从基础配置复算")
        if item.binary_label != (0 if item.traffic_mode == "benign" else 1):
            raise R2NS3MatrixError("流量模式与二元标签不一致")
        if item.sender_count != item.benign_sender_count + item.attack_sender_count:
            raise R2NS3MatrixError("发送者组成与总数不一致")
        if item.total_offered_load_mbps != round(
            item.initial_capacity_mbps * item.offered_load_ratio, 6
        ):
            raise R2NS3MatrixError("提供负载未按初始容量与负载带计算")
        matched_labels[
            (
                item.split,
                item.replicate_key_sha256,
                item.arrival_model,
                item.queue_model,
                item.offered_load_ratio,
            )
        ].append(item)

    excluded = {
        "physics_group_sha256",
        "seed_basis_sha256",
        "run_seed",
        "traffic_mode",
        "binary_label",
        "benign_sender_count",
        "attack_sender_count",
    }
    for key, pair in matched_labels.items():
        if len(pair) != 2 or {item.traffic_mode for item in pair} != set(TRAFFIC_MODES):
            raise R2NS3MatrixError(f"标签配平条件 {key} 未同时包含良性与攻击")
        left = {name: value for name, value in pair[0].to_record().items() if name not in excluded}
        right = {name: value for name, value in pair[1].to_record().items() if name not in excluded}
        if left != right:
            raise R2NS3MatrixError(f"标签配平条件 {key} 除发送者组成外仍有参数差异")

    if matrix_config is not None:
        for grid_name, split_filter in (
            ("in_distribution", lambda split: split != "unseen-configuration"),
            ("unseen_configuration", lambda split: split == "unseen-configuration"),
        ):
            grid = matrix_config.parameter_grids[grid_name]
            scoped = [item for item in configs if split_filter(item.split)]
            for field_name in (
                "initial_capacity_mbps",
                "capacity_change_multiplier",
                "access_delay_ms",
                "bottleneck_delay_ms",
                "queue_limit_packets",
                "downstream_loss_rate",
            ):
                actual = {getattr(item, field_name) for item in scoped}
                expected = set(getattr(grid, field_name))
                if actual != expected:
                    raise R2NS3MatrixError(
                        f"{grid_name}.{field_name} 的哈希选择未覆盖完整冻结网格"
                    )


def generate_base_configs(config: R2NS3MatrixConfig) -> Sequence[BaseProtocolConfig]:
    """精确生成 256 个不含协议的基础配置。"""
    _validate_matrix_config(config)
    result: list[BaseProtocolConfig] = []
    for split in config.split_order:
        queue_models = (
            config.unseen_queue_models
            if split == "unseen-configuration"
            else config.in_distribution_queue_models
        )
        for traffic_mode in config.traffic_modes:
            for arrival_model in config.arrival_models:
                for queue_model in queue_models:
                    for offered_load_ratio in config.offered_load_ratios:
                        for replica_slot in range(config.replicas_per_factor_cell[split]):
                            result.append(
                                _make_base_config(
                                    config,
                                    split=split,
                                    traffic_mode=traffic_mode,
                                    arrival_model=arrival_model,
                                    queue_model=queue_model,
                                    offered_load_ratio=offered_load_ratio,
                                    replica_slot=replica_slot,
                                )
                            )
    _validate_base_configs(result, config)
    return tuple(result)


def _protocol_order(base: BaseProtocolConfig) -> tuple[str, str]:
    digest = hashlib.sha256(
        b"r2-ns3-protocol-order-v1\0" + bytes.fromhex(base.physics_group_sha256)
    ).digest()
    return PROTOCOLS if digest[0] & 1 == 0 else tuple(reversed(PROTOCOLS))


def _validate_protocol_runs(configs: Sequence[ProtocolRunConfig]) -> None:
    if len(configs) != 512:
        raise R2NS3MatrixError(f"协议运行必须恰为 512 条，实际为 {len(configs)}")
    by_group: dict[str, list[ProtocolRunConfig]] = defaultdict(list)
    for item in configs:
        if item.transport_family not in PROTOCOLS:
            raise R2NS3MatrixError("协议运行只能使用 TCP 或普通 UDP")
        if tuple(item.to_record()) != MANIFEST_FIELD_ORDER:
            raise R2NS3MatrixError("清单记录字段顺序不符")
        by_group[item.physics_group_sha256].append(item)
    if len(by_group) != 256:
        raise R2NS3MatrixError("协议运行未形成 256 个配对组")
    for group_id, pair in by_group.items():
        if len(pair) != 2 or {item.transport_family for item in pair} != set(PROTOCOLS):
            raise R2NS3MatrixError(f"配对组 {group_id} 未恰含一个 TCP 和一个普通 UDP")
        if pair[0].to_base_record() != pair[1].to_base_record():
            raise R2NS3MatrixError(f"配对组 {group_id} 除协议外仍有字段差异")

    if Counter(item.transport_family for item in configs) != Counter({"TCP": 256, "UDP": 256}):
        raise R2NS3MatrixError("TCP/UDP 运行数未严格配平")
    for attribute in ("physics_group_sha256", "run_seed", "traffic_mode", "binary_label"):
        conditioned: dict[object, set[str]] = defaultdict(set)
        for item in configs:
            conditioned[getattr(item, attribute)].add(item.transport_family)
        if any(protocols != set(PROTOCOLS) for protocols in conditioned.values()):
            raise R2NS3MatrixError(f"协议可由 {attribute} 唯一预测")
    even_protocols = {item.transport_family for item in configs[0::2]}
    odd_protocols = {item.transport_family for item in configs[1::2]}
    if even_protocols != set(PROTOCOLS) or odd_protocols != set(PROTOCOLS):
        raise R2NS3MatrixError("协议可由清单奇偶位置预测，复现了旧捷径")


def expand_protocol_pairs(base: Sequence[BaseProtocolConfig]) -> Sequence[ProtocolRunConfig]:
    """以协议作为最后维度，为每个基础配置派生严格 TCP/UDP 配对。"""
    _validate_base_configs(base)
    result: list[ProtocolRunConfig] = []
    for item in base:
        base_record = item.to_record()
        for transport_family in _protocol_order(item):
            result.append(ProtocolRunConfig(**base_record, transport_family=transport_family))
    _validate_protocol_runs(result)
    return tuple(result)


def write_frozen_manifest(
    configs: Sequence[ProtocolRunConfig], output_dir: Path
) -> MatrixReceipt:
    """拒绝覆盖并写出固定字段顺序的正式 JSONL 清单和 SHA-256。"""
    _validate_protocol_runs(configs)
    normalized_output = Path(output_dir).expanduser().resolve()
    if normalized_output.is_symlink():
        raise R2NS3MatrixError("输出目录不得是符号链接")
    normalized_output.mkdir(parents=True, exist_ok=True)
    manifest_path = normalized_output / "ns3-config-manifest.jsonl"
    checksum_path = normalized_output / "ns3-config-manifest.sha256"
    manifest_partial = normalized_output / ".ns3-config-manifest.jsonl.partial"
    checksum_partial = normalized_output / ".ns3-config-manifest.sha256.partial"
    for path in (manifest_path, checksum_path, manifest_partial, checksum_partial):
        if path.exists() or path.is_symlink():
            raise R2NS3MatrixError(f"冻结输出已存在，不得覆盖：{path}")

    try:
        with manifest_partial.open("x", encoding="ascii", newline="\n") as destination:
            for item in configs:
                destination.write(
                    json.dumps(
                        item.to_record(),
                        allow_nan=False,
                        ensure_ascii=True,
                        separators=(",", ":"),
                    )
                    + "\n"
                )
        manifest_sha256 = _file_sha256(manifest_partial)
        checksum_partial.write_text(
            f"{manifest_sha256}  {manifest_path.name}\n",
            encoding="ascii",
            newline="\n",
        )
        if manifest_path.exists() or checksum_path.exists():
            raise R2NS3MatrixError("冻结输出在写入期间被其他进程占用")
        manifest_partial.rename(manifest_path)
        checksum_partial.rename(checksum_path)
    finally:
        for partial in (manifest_partial, checksum_partial):
            if partial.exists() and not partial.is_symlink():
                partial.unlink()

    split_base_counts = {
        split: len(
            {
                item.physics_group_sha256
                for item in configs
                if item.split == split
            }
        )
        for split in SPLIT_ORDER
    }
    split_run_counts = {
        split: sum(item.split == split for item in configs) for split in SPLIT_ORDER
    }
    return MatrixReceipt(
        manifest_path=manifest_path,
        checksum_path=checksum_path,
        manifest_sha256=manifest_sha256,
        checksum_sha256=_file_sha256(checksum_path),
        manifest_size_bytes=manifest_path.stat().st_size,
        matrix_config_sha256=configs[0].matrix_config_sha256,
        r2_contract_sha256=configs[0].r2_contract_sha256,
        base_configuration_count=len({item.physics_group_sha256 for item in configs}),
        protocol_run_count=len(configs),
        split_base_configuration_counts=split_base_counts,
        split_protocol_run_counts=split_run_counts,
    )


def build_parser() -> argparse.ArgumentParser:
    """构造正式配置生成入口。"""
    parser = argparse.ArgumentParser(description="生成 R2 ns-3 TCP/普通 UDP 严格配对矩阵")
    parser.add_argument("--config", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """加载冻结配置、执行全部合同断言并写出正式清单。"""
    args = build_parser().parse_args(argv)
    config = load_matrix_config(args.config)
    base_configs = generate_base_configs(config)
    protocol_runs = expand_protocol_pairs(base_configs)
    output_dir = config.project_root / Path(*config.output_directory.parts)
    receipt = write_frozen_manifest(protocol_runs, output_dir)
    print(json.dumps(receipt.to_record(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
