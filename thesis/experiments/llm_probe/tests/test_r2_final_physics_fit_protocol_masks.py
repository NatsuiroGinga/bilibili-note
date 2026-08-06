from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from flow_probe.r2_final_experts import EXPERT_TCP, EXPERT_UDP
from flow_probe.r2_final_physics_fit import (
    R2FinalPhysicsFitError,
    _build_split,
    _load_frame,
    load_config,
)


def test_cross_protocol_masks_allow_na_but_applicable_masks_remain_strict() -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_config(
        root / "configs/r2_final_physics_fit_seed42.yaml",
        trusted_root=root,
    )
    frame = _load_frame(config)
    train = frame.loc[frame[config.data.split_id].astype(str) == "train-fit"].copy()
    selected = []
    for route_name in ("TCP", "UDP"):
        route = train.loc[train[config.data.route_id].astype(str) == route_name]
        sequence_id = str(route.iloc[0][config.data.sequence_id])
        selected.append(
            route.loc[route[config.data.sequence_id].astype(str) == sequence_id].copy()
        )
    paired = pd.concat(selected, ignore_index=True, sort=False)
    tcp_rows = paired[config.data.route_id].astype(str) == "TCP"
    udp_rows = paired[config.data.route_id].astype(str) == "UDP"
    tcp_truth = config.data.truths[EXPERT_TCP]
    udp_truth = config.data.truths[EXPERT_UDP]
    udp_columns = list(dict.fromkeys((*udp_truth.fields, *udp_truth.observed_fields)))
    tcp_columns = list(dict.fromkeys((*tcp_truth.fields, *tcp_truth.observed_fields)))
    paired[udp_columns] = paired[udp_columns].astype(object)
    paired[tcp_columns] = paired[tcp_columns].astype(object)
    paired.loc[tcp_rows, udp_columns] = np.nan
    paired.loc[udp_rows, tcp_columns] = np.nan

    split = _build_split(paired, config, "train-fit")

    assert not split.truth_masks[EXPERT_UDP][split.route_index == 0].any()
    assert not split.truth_masks[EXPERT_TCP][split.route_index == 1].any()

    invalid = paired.copy()
    invalid.loc[udp_rows, udp_truth.observed_fields[0]] = np.nan
    with pytest.raises(R2FinalPhysicsFitError, match="truth_udp_observed"):
        _build_split(invalid, config, "train-fit")
