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


# ---------------------------------------------------------------------------
# 5. V1/V2/V3 判据阈值均为模块级冻结常量。
# ---------------------------------------------------------------------------


def test_v1_v2_v3_threshold_constants_exist_with_frozen_values() -> None:
    """V1/V2/V3 判据阈值、随机森林与逻辑回归超参数须存在且等于冻结取值。"""
    expected = {
        "D2_BEST_CHANNEL_REFERENCE_R2": 0.8412,
        "V1_WITHIN_R2_STRONG_FORM_THRESHOLD": 0.1,
        "V1_WITHIN_R2_REJECT_THRESHOLD": 0.3,
        "V1_BETWEEN_R2_STRONG_FORM_FRACTION": 0.7,
        "V1_BETWEEN_R2_STRONG_FORM_THRESHOLD": 0.58884,
        "V2_FIELD_TOP1_ACCURACY_THRESHOLD": 0.5,
        "V2_STATE_NEAR_PERFECT_TOP1_ACCURACY_THRESHOLD": 0.9,
        "V2_CHANCE_LEVEL_TOP1_ACCURACY": 1.0 / 128.0,
        "V2_TRAIN_WINDOW_FRACTION": 0.8,
        "V2_RANDOM_FOREST_N_ESTIMATORS": 300,
        "V2_LOGISTIC_REGRESSION_MAX_ITER": 2000,
        "V3_DYNAMICS_NOT_DOMINATED_RATIO_THRESHOLD": 10.0,
        "V3_DYNAMICS_STRONG_FORM_RATIO_THRESHOLD": 70.0,
    }
    for name, value in expected.items():
        assert getattr(probe, name) == pytest.approx(value), name


# ---------------------------------------------------------------------------
# 6. V1 双侧中心化：特征必须与目标一起按同一分组键中心化。
# ---------------------------------------------------------------------------


def test_center_within_group_centers_features_and_target_together() -> None:
    """双侧中心化：目标与特征都要按同一分组键中心化，不能只中心化其中一个。

    这是 V1 最容易出错的一点：只中心化目标而不中心化特征，场景身份会从
    特征侧漏回来，R²_within 会被人为拉高，结论就废了。
    """
    groups = np.array(["a", "a", "a", "b", "b", "b"])
    target = np.array([10.0, 12.0, 14.0, 100.0, 102.0, 104.0])
    features = np.array(
        [
            [1.0, 5.0],
            [2.0, 5.0],
            [3.0, 5.0],
            [50.0, 5.0],
            [51.0, 5.0],
            [52.0, 5.0],
        ]
    )

    centered_target = probe._center_within_group(target, groups)  # noqa: SLF001
    centered_features = probe._center_within_group(features, groups)  # noqa: SLF001

    # 中心化后每个分组内目标与特征的均值都必须精确为零。
    for group_id in ("a", "b"):
        mask = groups == group_id
        assert centered_target[mask].mean() == pytest.approx(0.0, abs=1e-9)
        assert centered_features[mask].mean(axis=0) == pytest.approx([0.0, 0.0], abs=1e-9)

    # 中心化前，特征第一列的组间均值相差约 49（组 a 约 2，组 b 约 51）；
    # 中心化后这一差异必须被完全消除，否则场景身份仍能从特征侧被模型学到。
    assert abs(features[groups == "a", 0].mean() - features[groups == "b", 0].mean()) > 40.0
    assert abs(
        centered_features[groups == "a", 0].mean() - centered_features[groups == "b", 0].mean()
    ) < 1e-9

    # 中心化不改变组内相对结构：同一分组内元素间的差值应保持不变。
    assert np.allclose(np.diff(centered_target[:3]), np.diff(target[:3]))


# ---------------------------------------------------------------------------
# 7. V3 场景间/场景内方差比。
# ---------------------------------------------------------------------------


def test_between_within_variance_ratio_detects_scene_dominated_vs_balanced() -> None:
    """场景均值差异远大于场景内离散时比值应远大于 1；场景内外方差相当时比值应接近 1。"""
    rng = np.random.default_rng(0)
    groups = np.repeat(np.arange(20), 50)

    # 场景主导：组均值间隔很大（0, 100, 200, ...），组内噪声很小。
    dominated_means = np.repeat(np.arange(20) * 100.0, 50)
    dominated_values = dominated_means + rng.normal(scale=0.1, size=groups.shape[0])
    dominated_stats = probe._between_within_variance_ratio(  # noqa: SLF001
        dominated_values, groups
    )
    assert dominated_stats["ratio"] > 1000.0

    # 场景不主导：全部组共享同一分布，组均值只因采样噪声而略有差异。
    balanced_values = rng.normal(loc=0.0, scale=1.0, size=groups.shape[0])
    balanced_stats = probe._between_within_variance_ratio(balanced_values, groups)  # noqa: SLF001
    assert balanced_stats["ratio"] < 1.0


def test_between_within_variance_ratio_rejects_zero_within_variance() -> None:
    """全部组内部完全无变化（组内方差为零）时必须报错，而不是返回无穷大掩盖问题。"""
    groups = np.array(["a", "a", "b", "b"])
    values = np.array([1.0, 1.0, 2.0, 2.0])
    with pytest.raises(probe.TcpStateProbeError):
        probe._between_within_variance_ratio(values, groups)  # noqa: SLF001


# ---------------------------------------------------------------------------
# 8. V2 按窗口序号（非随机）切分训练/测试。
# ---------------------------------------------------------------------------


def test_prepare_v2_window_split_uses_window_index_not_random() -> None:
    """按场景内窗口序号切分：每个场景前 80% 的窗口序号进训练集，其余进测试集。"""
    clusters = np.repeat(np.array(["c0", "c1"]), 10)
    window_index = np.tile(np.arange(10), 2)

    train_mask = probe._prepare_v2_window_split(window_index, clusters)  # noqa: SLF001

    # 阈值 = floor(0.8 * 10) = 8，序号 0..7 训练，8..9 测试。
    expected_train = window_index < 8
    assert np.array_equal(train_mask, expected_train)
    # 两个场景在训练集与测试集中都必须出现，不能因切分丢掉某个场景。
    assert set(clusters[train_mask]) == {"c0", "c1"}
    assert set(clusters[~train_mask]) == {"c0", "c1"}


def test_prepare_v2_window_split_rejects_inconsistent_cluster_ranges() -> None:
    """各场景内窗口序号范围不一致时必须报错，否则统一阈值无法保证跨场景比例一致。"""
    clusters = np.array(["a", "a", "b", "b", "b"])
    window_index = np.array([0, 1, 0, 1, 2])
    with pytest.raises(probe.TcpStateProbeError):
        probe._prepare_v2_window_split(window_index, clusters)  # noqa: SLF001
