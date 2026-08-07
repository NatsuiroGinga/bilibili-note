"""ns-3 窗内观测诊断分析脚本（analyze_ns3_intra_window_diagnostic.py）的最小回归测试。

全部用构造的小 DataFrame 验证，不依赖任何真实 ns-3 运行产物。覆盖点：

1. G-diag 子集筛选正确排除 benign 与 offered_load_ratio < 1.05 的窗口；
2. peak_nonzero_fraction 恰好等于阈值 0.50 时判为通过（边界含等号）；
3. nonzero_seconds_median == 0 时判为不通过，即使峰值占比达标；
4. suggest_k 在中位数 0.02 时返回候选 K=6，在中位数 0.001 时返回 None；
5. G-diag 子集为空时必须抛出异常，不得静默返回通过或不通过。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

import analyze_ns3_intra_window_diagnostic as diag  # noqa: E402


def _make_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    """按测试用例组装最小诊断 DataFrame，只含 G-diag 计算所需的列。"""
    return pd.DataFrame(rows)


def _row(
    *,
    traffic_mode: str,
    offered_load_ratio: float,
    peak_l3_bytes: int,
    nonzero_seconds: float,
) -> dict[str, object]:
    return {
        "traffic_mode": traffic_mode,
        "offered_load_ratio": offered_load_ratio,
        "diag_queue_peak_l3_bytes": peak_l3_bytes,
        "diag_queue_nonzero_seconds": nonzero_seconds,
    }


def test_subset_excludes_benign_and_low_load_ratio() -> None:
    """子集筛选必须排除 benign 行与 offered_load_ratio < 1.05 的行。"""
    frame = _make_frame(
        [
            # benign：即使过载比达标也必须被排除。
            _row(
                traffic_mode="benign",
                offered_load_ratio=1.4,
                peak_l3_bytes=100,
                nonzero_seconds=0.05,
            ),
            # dos 但过载比不足 1.05：必须被排除。
            _row(
                traffic_mode="dos",
                offered_load_ratio=0.7,
                peak_l3_bytes=100,
                nonzero_seconds=0.05,
            ),
            # dos 且过载比恰好等于阈值：必须纳入（边界含等号）。
            _row(
                traffic_mode="dos",
                offered_load_ratio=1.05,
                peak_l3_bytes=100,
                nonzero_seconds=0.05,
            ),
            # dos 且过载比超过阈值：必须纳入。
            _row(
                traffic_mode="dos",
                offered_load_ratio=1.4,
                peak_l3_bytes=0,
                nonzero_seconds=0.0,
            ),
        ]
    )
    verdict = diag.evaluate_g_diag(frame)
    assert verdict["subset_rows"] == 2


def test_peak_nonzero_fraction_exactly_threshold_passes() -> None:
    """peak_nonzero_fraction 恰好等于 0.50 时必须判为通过（含等号）。"""
    frame = _make_frame(
        [
            _row(
                traffic_mode="dos",
                offered_load_ratio=1.05,
                peak_l3_bytes=100,
                nonzero_seconds=0.05,
            ),
            _row(
                traffic_mode="dos",
                offered_load_ratio=1.4,
                peak_l3_bytes=100,
                nonzero_seconds=0.06,
            ),
            _row(
                traffic_mode="dos",
                offered_load_ratio=1.05,
                peak_l3_bytes=0,
                nonzero_seconds=0.0,
            ),
            _row(
                traffic_mode="dos",
                offered_load_ratio=1.4,
                peak_l3_bytes=0,
                nonzero_seconds=0.0,
            ),
        ]
    )
    verdict = diag.evaluate_g_diag(frame)
    assert verdict["subset_rows"] == 4
    assert verdict["peak_nonzero_fraction"] == pytest.approx(0.50)
    assert verdict["nonzero_seconds_median"] > 0.0
    assert verdict["passed"] is True


def test_zero_nonzero_seconds_median_fails_even_if_peak_fraction_ok() -> None:
    """nonzero_seconds_median == 0 时必须判为不通过，即使峰值占比达标（100%）。"""
    frame = _make_frame(
        [
            _row(
                traffic_mode="dos",
                offered_load_ratio=1.05,
                peak_l3_bytes=100,
                nonzero_seconds=0.0,
            ),
            _row(
                traffic_mode="dos",
                offered_load_ratio=1.4,
                peak_l3_bytes=200,
                nonzero_seconds=0.0,
            ),
        ]
    )
    verdict = diag.evaluate_g_diag(frame)
    assert verdict["peak_nonzero_fraction"] == pytest.approx(1.0)
    assert verdict["nonzero_seconds_median"] == 0.0
    assert verdict["passed"] is False


def test_suggest_k_picks_smallest_feasible_candidate() -> None:
    """中位数 0.02 时应选出最小可行候选 K=6（0.1 / 5 = 0.02 <= 0.02）。"""
    frame = _make_frame(
        [
            _row(
                traffic_mode="dos",
                offered_load_ratio=1.05,
                peak_l3_bytes=100,
                nonzero_seconds=0.02,
            ),
            _row(
                traffic_mode="dos",
                offered_load_ratio=1.4,
                peak_l3_bytes=100,
                nonzero_seconds=0.02,
            ),
        ]
    )
    result = diag.suggest_k(frame)
    assert result["nonzero_seconds_median"] == pytest.approx(0.02)
    assert result["suggested_k"] == 6


def test_suggest_k_returns_none_when_no_candidate_feasible() -> None:
    """中位数 0.001 时任何候选 K 都不可行，必须返回 None 而非近似值。"""
    frame = _make_frame(
        [
            _row(
                traffic_mode="dos",
                offered_load_ratio=1.05,
                peak_l3_bytes=100,
                nonzero_seconds=0.001,
            ),
            _row(
                traffic_mode="dos",
                offered_load_ratio=1.4,
                peak_l3_bytes=100,
                nonzero_seconds=0.001,
            ),
        ]
    )
    result = diag.suggest_k(frame)
    assert result["nonzero_seconds_median"] == pytest.approx(0.001)
    assert result["suggested_k"] is None


def test_empty_subset_raises() -> None:
    """G-diag 子集为空时必须抛出异常，不得静默返回通过或不通过。"""
    frame = _make_frame(
        [
            _row(
                traffic_mode="benign",
                offered_load_ratio=1.4,
                peak_l3_bytes=100,
                nonzero_seconds=0.05,
            ),
            _row(
                traffic_mode="dos",
                offered_load_ratio=0.7,
                peak_l3_bytes=100,
                nonzero_seconds=0.05,
            ),
        ]
    )
    with pytest.raises(ValueError):
        diag.evaluate_g_diag(frame)
