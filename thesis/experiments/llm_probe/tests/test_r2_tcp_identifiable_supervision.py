from pathlib import Path

import numpy as np
import pandas as pd

from flow_probe import r2_final_physics_fit as physics_fit
from flow_probe import r2_final_distilbert_probe as distilbert_probe
from flow_probe import r2_final_experts as experts


TCP_FIELDS = (
    "truth_tcp_cwnd_start_bytes",
    "truth_tcp_cwnd_end_bytes",
    "truth_tcp_ssthresh_start_bytes",
    "truth_tcp_ssthresh_end_bytes",
    "truth_tcp_bytes_in_flight_start_bytes",
    "truth_tcp_bytes_in_flight_end_bytes",
    "truth_tcp_acked_bytes",
    "truth_tcp_loss_event_count",
    "truth_tcp_timeout_event_count",
    "truth_tcp_rtt_mean_ms",
)

TCP_MASKS = (
    "cwnd_start_observed",
    "cwnd_end_observed",
    "ssthresh_start_observed",
    "ssthresh_end_observed",
    "bytes_in_flight_start_observed",
    "bytes_in_flight_end_observed",
    "acked_bytes_observed",
    "loss_event_count_observed",
    "timeout_event_count_observed",
    "rtt_observed",
)


def _sender_row(sender_index: int) -> dict[str, object]:
    values = {
        "sequence_id": "tcp-sequence-0",
        "source_window_index": 0,
        "sender_index": sender_index,
        "truth_tcp_rtt_sample_count": 1 if sender_index == 0 else 3,
        **dict.fromkeys(TCP_MASKS, True),
    }
    if sender_index == 0:
        values.update(
            {
                "truth_tcp_cwnd_start_bytes": 1_000.0,
                "truth_tcp_cwnd_end_bytes": 2_000.0,
                "truth_tcp_ssthresh_start_bytes": float(2**32 - 1),
                "truth_tcp_ssthresh_end_bytes": 4_000.0,
                "truth_tcp_bytes_in_flight_start_bytes": 500.0,
                "truth_tcp_bytes_in_flight_end_bytes": 600.0,
                "truth_tcp_acked_bytes": 300.0,
                "truth_tcp_loss_event_count": 0,
                "truth_tcp_timeout_event_count": 0,
                "truth_tcp_rtt_mean_ms": 10.0,
            }
        )
    else:
        values.update(
            {
                "truth_tcp_cwnd_start_bytes": 3_000.0,
                "truth_tcp_cwnd_end_bytes": 4_000.0,
                "truth_tcp_ssthresh_start_bytes": 5_000.0,
                "truth_tcp_ssthresh_end_bytes": 5_000.0,
                "truth_tcp_bytes_in_flight_start_bytes": 700.0,
                "truth_tcp_bytes_in_flight_end_bytes": 800.0,
                "truth_tcp_acked_bytes": 400.0,
                "truth_tcp_loss_event_count": 1,
                "truth_tcp_timeout_event_count": 0,
                "truth_tcp_rtt_mean_ms": 30.0,
            }
        )
    return values


def test_tcp_sender_truth_is_aggregated_to_one_identifiable_public_window() -> None:
    truth = pd.DataFrame([_sender_row(0), _sender_row(1)])
    spec = physics_fit.TruthSpec(
        fields=TCP_FIELDS,
        observed_fields=TCP_MASKS,
        scales=(1.0,) * len(TCP_FIELDS),
    )

    aggregated = physics_fit._aggregate_tcp_sender_truth(
        truth,
        spec,
        join_keys=("sequence_id", "source_window_index"),
        ssthresh_unset_value=2**32 - 1,
    )

    assert len(aggregated) == 1
    assert "sender_index" not in aggregated.columns
    row = aggregated.iloc[0]
    assert row["sequence_id"] == "tcp-sequence-0"
    assert row["truth_tcp_sender_count"] == 2
    assert row["truth_tcp_cwnd_start_bytes"] == 4_000.0
    assert row["truth_tcp_acked_bytes"] == 700.0
    assert row["truth_tcp_loss_event_count"] == 1
    assert row["truth_tcp_rtt_mean_ms"] == 25.0
    assert bool(row["ssthresh_start_observed"]) is False
    assert row["truth_tcp_ssthresh_start_bytes"] == 0.0
    assert row["truth_tcp_ssthresh_start_unset_sender_count"] == 1
    assert bool(row["ssthresh_end_observed"]) is True
    assert row["truth_tcp_ssthresh_end_bytes"] == 9_000.0
    assert row["truth_tcp_ssthresh_end_unset_sender_count"] == 0


def test_identifiable_config_removes_sender_suffix_and_sentinel_regression() -> None:
    root = Path(__file__).resolve().parents[1]
    config = physics_fit.load_config(
        root / "configs/r2_final_physics_fit_seed42_identifiable_v2.yaml",
        trusted_root=root,
    )

    frame = physics_fit._load_frame(config)
    tcp = frame.loc[frame[config.data.route_id].astype(str) == "TCP"].copy()
    keys = [config.data.sequence_id, "source_window_index"]

    assert len(tcp) == len(tcp[keys].drop_duplicates())
    assert not tcp[config.data.sequence_id].astype(str).str.contains(":sender-").any()
    assert "sender_index" not in tcp.columns
    for endpoint in ("start", "end"):
        field = f"truth_tcp_ssthresh_{endpoint}_bytes"
        mask = f"ssthresh_{endpoint}_observed"
        unset_count = f"truth_tcp_ssthresh_{endpoint}_unset_sender_count"
        sentinel_windows = tcp[unset_count].astype(int) > 0
        assert not tcp.loc[sentinel_windows, mask].astype(bool).any()
        assert not (tcp.loc[tcp[mask].astype(bool), field] == 2**32 - 1).any()


def test_physics_sidecar_residual_gate_starts_exactly_closed() -> None:
    parameter = np.asarray(0.0, dtype=np.float32)

    strength = distilbert_probe._bounded_residual_strength(parameter, np)

    assert float(strength) == 0.0
    assert abs(float(distilbert_probe._bounded_residual_strength(100.0, np))) <= 0.1


def test_ssthresh_sentinel_disables_only_the_equations_that_need_it() -> None:
    observed = np.ones((2, 10), dtype=bool)
    observed[0, [0, 2, 6, 9]] = False
    observed[1, [3, 4, 5]] = False

    growth, contraction = experts._tcp_phase_observation_availability(observed)

    assert growth.tolist() == [False, True]
    assert contraction.tolist() == [True, False]
