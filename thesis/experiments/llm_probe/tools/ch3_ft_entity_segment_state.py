#!/usr/bin/env python3
"""M-E 严格过去实体状态的预计算与归一化常数拟合。

M-E 的门 `γ_θ(s)` 只依赖严格过去的实体状态 `s = [log(1+c), log(1+Δ)]`：
- `c`：该片段之前，该实体已出现的片段数（形式化第 3.2 节的 `c_{e,t}`）；
- `Δ`：距同实体上一片段的时间间隔，首片段取 `0`。

严格过去状态的向量化计算已在 `tools/ch3_ft_me_gate_scope_probe.py` 的
`strict_past_segment_state` 中实现并在真实数据上通过 8 项冻结数字核验，
本模块直接导入复用，不重写第二份可能漂移的实现。

本模块新增的是归一化：尺度常数只由训练区拟合，验证区与目标年 LSPR24 零参与；
归一化必须取对数，因为源年实测 `c` 的前后半段均值 `402.74 → 1519.58`，
源年内部即漂移 `3.8` 倍，绝对值入模会重蹈已被否决的 CEM 路径。
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ch3_ft_me_gate_scope_probe import strict_past_segment_state as compute_segment_state

__all__ = [
    "compute_segment_state",
    "fit_state_normalizers",
    "normalize_state",
]


def fit_state_normalizers(
    prior_segments: np.ndarray, gap: np.ndarray, train_rows: np.ndarray
) -> Dict[str, float]:
    """拟合状态归一化的尺度常数。

    尺度常数取训练区（`train_rows` 索引出的行）的 `p99` 分位数，验证区与目标年
    LSPR24 零参与。下限钳制到 `1.0`，避免训练区退化（如极小样本或常数列）时
    尺度过小导致归一化后的值异常放大。

    Args:
        prior_segments: 片段级的严格过去片段计数 `c`，形状 `(n,)`。
        gap: 片段级的距上一片段时间间隔 `Δ`，形状 `(n,)`。
        train_rows: 训练区行索引，只用这些行拟合尺度常数。

    Returns:
        含 `c_scale` 与 `gap_scale` 两个键的字典。
    """
    c_scale = float(np.quantile(prior_segments[train_rows], 0.99))
    gap_scale = float(np.quantile(gap[train_rows], 0.99))
    return {
        "c_scale": max(c_scale, 1.0),
        "gap_scale": max(gap_scale, 1.0),
    }


def normalize_state(
    prior_segments: np.ndarray, gap: np.ndarray, normalizers: Dict[str, float]
) -> np.ndarray:
    """按训练区拟合的尺度常数对严格过去状态取对数归一化。

    `s = [log(1+c)/log(1+C), log(1+Δ)/log(1+D)]`，其中 `C`、`D` 为训练区拟合的
    `c_scale`、`gap_scale`。`c = 0` 时 `log1p(0) = 0`，故输出第 0 列恰为 `0`，
    这是形式化第 3.3 节 `𝟙[c≥1]` 判据的等价实现，下游门直接用
    `entity_state[:, :1] > 0` 判定有无历史，不需要额外的指示列。

    Args:
        prior_segments: 片段级的严格过去片段计数 `c`，形状 `(n,)`。
        gap: 片段级的距上一片段时间间隔 `Δ`，形状 `(n,)`。
        normalizers: `fit_state_normalizers` 产出的尺度常数字典。

    Returns:
        形状 `(n, 2)` 的 float32 数组，第 0 列为 `c` 分量，第 1 列为 `Δ` 分量。
    """
    c_component = np.log1p(prior_segments) / np.log1p(normalizers["c_scale"])
    gap_component = np.log1p(np.maximum(gap, 0.0)) / np.log1p(normalizers["gap_scale"])
    return np.stack([c_component, gap_component], axis=1).astype(np.float32)
