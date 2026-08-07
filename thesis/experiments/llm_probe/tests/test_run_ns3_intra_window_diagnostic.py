"""ns-3 窗内观测诊断批量驱动（run_ns3_intra_window_diagnostic.py）的最小回归测试。

全部使用构造数据与打桩替身，不依赖真实 ns-3、不真正执行子进程。覆盖点：

1. ``select_runs(only_gdiag_subset=True)`` 正确排除 benign 与
   ``offered_load_ratio < 阈值`` 的运行，且保留边界值；
2. ``select_runs(only_gdiag_subset=False)`` 原样返回全量清单；
3. G-diag 阈值确实来自 ``analyze_ns3_intra_window_diagnostic.MIN_LOAD_RATIO``，
   驱动脚本内不存在独立定义，避免两处阈值漂移；
4. 单个运行抛异常时不中断整批，``run-state.json`` 记为 ``partial`` 并含
   失败清单（打桩替换 ``_run_one`` 与 ``_load_manifest``）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

import analyze_ns3_intra_window_diagnostic as diag  # noqa: E402
import run_ns3_intra_window_diagnostic as driver  # noqa: E402

from flow_probe.r2_ns3_protocol_matrix import ProtocolRunConfig  # noqa: E402


def _make_run(
    *,
    traffic_mode: str,
    offered_load_ratio: float,
    physics_group_sha256: str,
    transport_family: str = "TCP",
) -> ProtocolRunConfig:
    """按 ProtocolRunConfig 的冻结字段顺序构造最小合法运行配置。

    只有 traffic_mode、offered_load_ratio、physics_group_sha256、
    transport_family 在各测试用例间变化，其余字段固定为类型合法的占位值。
    """
    return ProtocolRunConfig(
        schema_version="test-schema",
        matrix_config_sha256="a" * 64,
        r2_contract_sha256="b" * 64,
        physics_group_sha256=physics_group_sha256,
        seed_basis_sha256="c" * 64,
        split="train-fit",
        replicate_key_sha256="d" * 64,
        run_seed=1,
        matrix_seed=1,
        topology_id="topo",
        ns3_version="3.48",
        tcp_congestion_control="ns3::TcpNewReno",
        duration_seconds=12.0,
        window_seconds=0.1,
        windows_per_run=120,
        sequence_length_windows=4,
        sequences_per_run=30,
        traffic_mode=traffic_mode,
        binary_label=0 if traffic_mode == "benign" else 1,
        arrival_model="constant",
        queue_model="fifo",
        offered_load_ratio=offered_load_ratio,
        initial_capacity_mbps=10.0,
        capacity_change_multiplier=1.0,
        shifted_capacity_mbps=10.0,
        capacity_change_time_seconds=6.0,
        access_delay_ms=1.0,
        bottleneck_delay_ms=5.0,
        queue_limit_packets=32,
        downstream_loss_rate=0.0,
        sender_count=8,
        benign_sender_count=8 if traffic_mode == "benign" else 4,
        attack_sender_count=0 if traffic_mode == "benign" else 4,
        total_offered_load_mbps=3.5,
        per_sender_offered_load_mbps=0.4375,
        packet_size_bytes=1200,
        burst_on_seconds=0.2,
        burst_off_seconds=0.1,
        transport_family=transport_family,
    )


def _sample_runs() -> list[ProtocolRunConfig]:
    return [
        _make_run(
            traffic_mode="benign",
            offered_load_ratio=1.40,
            physics_group_sha256="0" * 64,
        ),
        _make_run(
            traffic_mode="dos",
            offered_load_ratio=0.70,
            physics_group_sha256="1" * 64,
        ),
        _make_run(
            traffic_mode="dos",
            offered_load_ratio=diag.MIN_LOAD_RATIO,
            physics_group_sha256="2" * 64,
        ),
        _make_run(
            traffic_mode="dos",
            offered_load_ratio=1.40,
            physics_group_sha256="3" * 64,
        ),
    ]


def test_select_runs_gdiag_subset_excludes_benign_and_low_ratio_keeps_boundary() -> None:
    runs = _sample_runs()

    selected = driver.select_runs(runs, only_gdiag_subset=True)

    assert selected == [(2, runs[2]), (3, runs[3])]


def test_select_runs_full_returns_all_runs_with_original_index() -> None:
    runs = _sample_runs()

    selected = driver.select_runs(runs, only_gdiag_subset=False)

    assert selected == list(enumerate(runs))


def test_min_load_ratio_is_reused_from_analysis_module_not_redefined() -> None:
    assert driver.MIN_LOAD_RATIO is diag.MIN_LOAD_RATIO

    source_text = Path(driver.__file__).read_text(encoding="utf-8")
    assert "from analyze_ns3_intra_window_diagnostic import MIN_LOAD_RATIO" in source_text
    assert "1.05" not in source_text


def test_run_diagnostic_matrix_isolates_single_run_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = _sample_runs()
    monkeypatch.setattr(driver, "_load_manifest", lambda path: tuple(runs))

    failing_index = 2

    def fake_run_one(
        ns3_root: Path,
        runs_root: Path,
        coverage: str,
        run: ProtocolRunConfig,
        contract_sha: str,
        source_sha: str,
        executable: Path,
    ) -> dict[str, object]:
        if run.physics_group_sha256 == runs[failing_index].physics_group_sha256:
            raise driver.TcpTruthV2Error("模拟运行失败")
        return {"status": "pass", "coverage": coverage}

    monkeypatch.setattr(driver, "_run_one", fake_run_one)

    contract_path = tmp_path / "contract.json"
    contract_path.write_text("{}", encoding="utf-8")
    scenario_source_path = tmp_path / "scenario.cc"
    scenario_source_path.write_text("// stub scenario\n", encoding="utf-8")
    output_root = tmp_path / "diag-output"

    state = driver.run_diagnostic_matrix(
        ns3_root=tmp_path,
        executable=tmp_path / "fake-executable",
        output_root=output_root,
        manifest_path=tmp_path / "manifest.jsonl",
        contract_path=contract_path,
        scenario_source_path=scenario_source_path,
        workers=2,
        only_gdiag_subset=True,
        queue_trace_interval_ms=0,
    )

    assert state["status"] == "partial"
    assert state["planned_run_count"] == 2
    assert state["completed_run_count"] == 1
    assert state["failed_run_count"] == 1
    failures = state["failures"]
    assert len(failures) == 1
    assert failures[0]["manifest_index"] == failing_index
    assert failures[0]["physics_group_sha256"] == runs[failing_index].physics_group_sha256

    on_disk = json.loads((output_root / "run-state.json").read_text(encoding="utf-8"))
    assert on_disk["status"] == "partial"
    assert on_disk["failed_run_count"] == 1
    assert on_disk["failures"][0]["manifest_index"] == failing_index


def test_run_diagnostic_matrix_rejects_nonzero_queue_trace_interval(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        driver.run_diagnostic_matrix(
            ns3_root=tmp_path,
            executable=tmp_path / "fake-executable",
            output_root=tmp_path / "diag-output",
            manifest_path=tmp_path / "manifest.jsonl",
            contract_path=tmp_path / "contract.json",
            scenario_source_path=tmp_path / "scenario.cc",
            workers=1,
            only_gdiag_subset=True,
            queue_trace_interval_ms=50,
        )
