"""R2 ns-3 配对矩阵的后置回归合同。"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from flow_probe.r2_ns3_protocol_matrix import (
    MANIFEST_FIELD_ORDER,
    R2NS3MatrixError,
    expand_protocol_pairs,
    generate_base_configs,
    load_matrix_config,
    write_frozen_manifest,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs/r2_ns3_protocol_matrix_v1.yaml"


def _formal_matrix():
    config = load_matrix_config(CONFIG_PATH)
    base = generate_base_configs(config)
    runs = expand_protocol_pairs(base)
    return config, base, runs


def test_formal_matrix_has_exact_counts_and_pair_identity() -> None:
    config, base, runs = _formal_matrix()
    assert config.tcp_congestion_control == "ns3::TcpNewReno"
    assert config.matrix_config_sha256 == "0adcb49e52a1df156eddf4a3d01dfd51d00fa57752bcc0d04189073ace2edeeb"
    assert config.r2_contract_sha256 == "aa390129e239aa59d1c6963471e1268498a16740a5f11a916f489fa6a7292566"
    assert {item.tcp_congestion_control for item in runs} == {"ns3::TcpNewReno"}
    assert len(base) == 256
    assert len(runs) == 512
    assert Counter(item.split for item in base) == Counter(config.split_base_counts)

    pairs = defaultdict(list)
    for run in runs:
        pairs[run.physics_group_sha256].append(run)
    assert len(pairs) == 256
    for pair in pairs.values():
        assert {item.transport_family for item in pair} == {"TCP", "UDP"}
        assert pair[0].to_base_record() == pair[1].to_base_record()

    mutable_bindings = {
        "matrix_config_sha256",
        "r2_contract_sha256",
        "tcp_congestion_control",
    }
    immutable_payload = b"".join(
        (
            json.dumps(
                {
                    key: value
                    for key, value in item.to_record().items()
                    if key not in mutable_bindings
                },
                allow_nan=False,
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("ascii")
        for item in runs
    )
    assert hashlib.sha256(immutable_payload).hexdigest() == (
        "3cef63f086db8d4ae07d57cf306105a394206701a2da829f9665f03183227a9e"
    )


def test_protocol_cannot_be_recovered_from_old_even_odd_shortcut() -> None:
    _, _, runs = _formal_matrix()
    assert {item.transport_family for item in runs[0::2]} == {"TCP", "UDP"}
    assert {item.transport_family for item in runs[1::2]} == {"TCP", "UDP"}
    for attribute in ("traffic_mode", "binary_label", "physics_group_sha256", "run_seed"):
        conditioned = defaultdict(set)
        for run in runs:
            conditioned[getattr(run, attribute)].add(run.transport_family)
        assert all(value == {"TCP", "UDP"} for value in conditioned.values())


def test_manifest_is_byte_deterministic_and_refuses_overwrite(tmp_path: Path) -> None:
    _, _, runs = _formal_matrix()
    first = write_frozen_manifest(runs, tmp_path / "first")
    second = write_frozen_manifest(runs, tmp_path / "second")
    assert first.manifest_sha256 == second.manifest_sha256
    assert first.manifest_path.read_bytes() == second.manifest_path.read_bytes()
    with pytest.raises(R2NS3MatrixError, match="不得覆盖"):
        write_frozen_manifest(runs, tmp_path / "first")

    first_record = json.loads(first.manifest_path.read_text(encoding="ascii").splitlines()[0])
    assert tuple(first_record) == MANIFEST_FIELD_ORDER
