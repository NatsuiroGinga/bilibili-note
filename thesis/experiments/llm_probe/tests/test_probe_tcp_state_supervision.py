"""TCP 状态监督证伪探针脚本（probe_tcp_state_supervision.py）的最小回归测试。

全部用构造的小 DataFrame 验证，不依赖任何真实制品。覆盖点：

1. D1/D2 判据阈值、随机种子与模型超参数均为模块级冻结常量，且命令行
   参数解析器不暴露任何覆盖这些常量的选项——防止事后调参。
2. 跨发送者聚合：cwnd/在途字节按观测掩码求和与均值；ssthresh 剔除
   Linux TCP_INFINITE_SSTHRESH 哨兵值后再聚合；RTT 按样本数加权平均；
   全部发送者未观测时对应通道判为无效（NaN + valid=False）。
3. 无固定点置换辅助函数：结果确实没有固定点，且是原索引的一个置换；
   元素数 < 2 时必须拒绝（无固定点置换不存在）。
4. 分组五折交叉验证确实不跨组泄漏：用构造的分组数组断言训练折与测试折
   的分组集合互不相交，折数与模块冻结常量 N_GROUP_FOLDS 一致。
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import GroupKFold

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

import probe_tcp_state_supervision as probe  # noqa: E402

# ---------------------------------------------------------------------------
# 1. 冻结常量与命令行覆盖入口。
# ---------------------------------------------------------------------------


def test_threshold_constants_exist_with_frozen_values() -> None:
    """全部判据阈值、随机种子与交叉验证折数须存在且等于任务派发时冻结的取值。"""
    expected = {
        "RANDOM_SEED": 42,
        "N_GROUP_FOLDS": 5,
        "RIDGE_INNER_FOLDS": 3,
        "MIN_OBSERVED_VALID_RATIO": 0.90,
        "MIN_STRATUM_TARGET_STD_MEDIAN_Z": 0.2,
        "MIN_PERMUTATION_MEAN_ABS_DELTA_Z": 0.1,
        "MIN_DYNAMICS_EVIDENCE_WINDOW_RATIO": 0.30,
        "D2_DEGENERATE_R2_THRESHOLD": 0.1,
        "D2_NEAR_DETERMINISTIC_R2_THRESHOLD": 0.9,
        "TCP_SSTHRESH_UNSET_VALUE": 4294967295.0,
    }
    for name, value in expected.items():
        assert getattr(probe, name) == pytest.approx(value), name


def test_cli_parser_does_not_expose_threshold_overrides() -> None:
    """命令行解析器只能暴露数据路径、运行范围与输出路径，不得暴露阈值覆盖选项。"""
    parser = probe.build_arg_parser()
    option_strings: set[str] = set()
    # argparse 无公开遍历 API，只能访问内部 _actions。
    for action in parser._actions:  # noqa: SLF001
        option_strings.update(action.option_strings)

    allowed = {"-h", "--help", "--e2-path", "--tcp-path", "--which", "--output-json"}
    assert option_strings == allowed

    forbidden_substrings = (
        "seed",
        "fold",
        "ratio",
        "threshold",
        "alpha",
        "hidden",
        "sentinel",
        "ssthresh",
    )
    for option in option_strings - {"-h", "--help"}:
        lowered = option.lower()
        assert not any(token in lowered for token in forbidden_substrings), option


# ---------------------------------------------------------------------------
# 2. 跨发送者聚合。
# ---------------------------------------------------------------------------

_BASE_KEYS: dict[str, object] = {
    "physics_group_sha256": "group-0",
    "evaluation_cluster_id": "cluster-0",
    "transport_family": "TCP",
    "split_id": "train-fit",
}


def _sender_row(
    *,
    sequence_id: str,
    window_index: int,
    sender_index: int,
    cwnd_end: float,
    cwnd_end_observed: bool,
    ssthresh_end: float,
    ssthresh_end_observed: bool,
    bif_end: float,
    bif_end_observed: bool,
    rtt_mean_ms: float,
    rtt_observed: bool,
    rtt_sample_count: int,
) -> dict[str, object]:
    return {
        **_BASE_KEYS,
        "sequence_id": sequence_id,
        "window_index_in_sequence": window_index,
        "sender_index": sender_index,
        "truth_tcp_cwnd_end_bytes": cwnd_end,
        "cwnd_end_observed": cwnd_end_observed,
        "truth_tcp_ssthresh_end_bytes": ssthresh_end,
        "ssthresh_end_observed": ssthresh_end_observed,
        "truth_tcp_bytes_in_flight_end_bytes": bif_end,
        "bytes_in_flight_end_observed": bif_end_observed,
        "truth_tcp_rtt_mean_ms": rtt_mean_ms,
        "rtt_observed": rtt_observed,
        "truth_tcp_rtt_sample_count": rtt_sample_count,
    }


def test_aggregate_sums_means_and_masks_ssthresh_sentinel() -> None:
    """cwnd/在途字节按求和与均值聚合；ssthresh 的哨兵值必须被剔除；RTT 按样本数加权。"""
    frame = pd.DataFrame(
        [
            _sender_row(
                sequence_id="seq-0",
                window_index=0,
                sender_index=0,
                cwnd_end=1_000.0,
                cwnd_end_observed=True,
                ssthresh_end=probe.TCP_SSTHRESH_UNSET_VALUE,
                ssthresh_end_observed=True,
                bif_end=200.0,
                bif_end_observed=True,
                rtt_mean_ms=10.0,
                rtt_observed=True,
                rtt_sample_count=5,
            ),
            _sender_row(
                sequence_id="seq-0",
                window_index=0,
                sender_index=1,
                cwnd_end=3_000.0,
                cwnd_end_observed=True,
                ssthresh_end=5_000.0,
                ssthresh_end_observed=True,
                bif_end=400.0,
                bif_end_observed=True,
                rtt_mean_ms=30.0,
                rtt_observed=True,
                rtt_sample_count=15,
            ),
        ]
    )
    aggregated = probe.aggregate_tcp_state_channels(frame)
    assert len(aggregated) == 1
    row = aggregated.iloc[0]

    assert row["cwnd_end_bytes_sum"] == pytest.approx(4_000.0)
    assert row["cwnd_end_bytes_mean"] == pytest.approx(2_000.0)
    assert bool(row["cwnd_end_bytes_valid"]) is True

    # 发送者 0 的 ssthresh 是哨兵值（未设置），只有发送者 1 的 5000 计入。
    assert row["ssthresh_end_bytes_sum"] == pytest.approx(5_000.0)
    assert row["ssthresh_end_bytes_mean"] == pytest.approx(5_000.0)
    assert bool(row["ssthresh_end_bytes_valid"]) is True

    assert row["bytes_in_flight_end_bytes_sum"] == pytest.approx(600.0)
    assert row["bytes_in_flight_end_bytes_mean"] == pytest.approx(300.0)

    # RTT 按样本数加权：(10*5 + 30*15) / (5+15) = 25.0，不是简单均值 20.0。
    assert row["rtt_mean_ms"] == pytest.approx(25.0)
    assert bool(row["rtt_mean_ms_valid"]) is True


def test_aggregate_all_unobserved_channel_is_invalid_and_nan() -> None:
    """通道内全部发送者未观测（或全为哨兵值）时，聚合结果须为 NaN 且 valid=False。"""
    frame = pd.DataFrame(
        [
            _sender_row(
                sequence_id="seq-1",
                window_index=0,
                sender_index=0,
                cwnd_end=1_000.0,
                cwnd_end_observed=False,
                ssthresh_end=probe.TCP_SSTHRESH_UNSET_VALUE,
                ssthresh_end_observed=True,
                bif_end=200.0,
                bif_end_observed=False,
                rtt_mean_ms=10.0,
                rtt_observed=False,
                rtt_sample_count=0,
            )
        ]
    )
    aggregated = probe.aggregate_tcp_state_channels(frame)
    row = aggregated.iloc[0]

    assert bool(row["cwnd_end_bytes_valid"]) is False
    assert pd.isna(row["cwnd_end_bytes_sum"])
    assert pd.isna(row["cwnd_end_bytes_mean"])

    # 唯一的发送者观测值恰好是哨兵值，剔除后该通道无有效观测。
    assert bool(row["ssthresh_end_bytes_valid"]) is False

    assert bool(row["rtt_mean_ms_valid"]) is False
    assert pd.isna(row["rtt_mean_ms"])


# ---------------------------------------------------------------------------
# 3. 无固定点置换。
# ---------------------------------------------------------------------------


def test_derangement_has_no_fixed_points_and_is_a_permutation() -> None:
    rng = np.random.default_rng(0)
    permutation = probe._derangement(6, rng)  # noqa: SLF001
    assert not bool(np.any(permutation == np.arange(6)))
    assert sorted(permutation.tolist()) == list(range(6))


def test_derangement_rejects_fewer_than_two_elements() -> None:
    rng = np.random.default_rng(0)
    with pytest.raises(probe.TcpStateProbeError):
        probe._derangement(1, rng)  # noqa: SLF001


# ---------------------------------------------------------------------------
# 4. 分组五折交叉验证不跨组泄漏。
# ---------------------------------------------------------------------------


def test_group_kfold_with_module_fold_count_does_not_leak_groups() -> None:
    """用构造的 30 组数据验证：任一折的训练组集合与测试组集合互不相交。"""
    groups = np.repeat(np.arange(30), 4)
    features = np.zeros((groups.shape[0], 1))
    cv = GroupKFold(n_splits=probe.N_GROUP_FOLDS)

    fold_count = 0
    seen_test_groups: set[int] = set()
    for train_idx, test_idx in cv.split(features, groups=groups):
        fold_count += 1
        train_groups = set(groups[train_idx].tolist())
        test_groups = set(groups[test_idx].tolist())
        assert train_groups.isdisjoint(test_groups)
        seen_test_groups.update(test_groups)

    assert fold_count == probe.N_GROUP_FOLDS
    # 每个分组恰好在且仅在一折的测试集中出现过。
    assert seen_test_groups == set(range(30))
