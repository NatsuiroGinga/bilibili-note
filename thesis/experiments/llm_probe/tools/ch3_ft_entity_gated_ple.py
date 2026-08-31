"""M-E｜实体门控的分段线性数值分词：PLE 编码、箱边界拟合与门控分词器。

对应 `.Codex/docs/RWKV/2026-08-31-M-E机制形式化与复杂度规约.md` 第 3.1、3.3、3.4、6 节：

- 全局通道**保留**现有 FT 骨干的线性分词 `g_j(x) = b_j + x·W_j`（第 6.1 节裁决），
  本模块以持有引用的方式复用 `FeatureTokenizer`，不复制、不重新初始化它的参数。
- M-E 只新增一条位移通道 `γ_θ(s) · Σ_t ε_j(x)_t · u^{(j)}_t`，`γ` 由严格过去实体状态门控。
- `γ ≡ 0` 或位移嵌入为零时，输出在**同一组权重内**逐位退化为现有分词器的输出。

本模块在导入时即需要 PyTorch，因此只应在确实要建模型的分支内导入
（`ch3_ft_transformer_field_token_protocol_a.py` 的 `--validate-config` 路径不经过这里）。
"""

from __future__ import annotations

import math
from typing import Final

import numpy as np
import torch
from torch import nn
from torch.nn import init as nn_init

__all__ = [
    "GATE_MODES",
    "fit_quantile_bin_edges",
    "piecewise_linear_encode",
    "entity_gated_ple_parameter_count",
    "EntityGatedPLETokenizer",
]

#: 允许的门模式。`entity_state` 是完整 M-E（C10），另两个是预注册消融臂 E1／E2。
GATE_MODES: Final[tuple[str, ...]] = ("entity_state", "constant", "binary_indicator")


def fit_quantile_bin_edges(values: np.ndarray, bin_count: int) -> np.ndarray:
    """按训练区经验分位数拟合逐字段 PLE 箱边界，返回 `(F, T+1)` 的 float32 数组。

    重复分位数会产生零宽箱并在编码时除零，故逐字段先去重：

    - 去重后至少有 `T+1` 个边界时，从去重结果中等距抽取 `T+1` 个，**保留分位数间距**。
    - 去重后不足 `T+1` 个时，**放弃该字段的分位数间距**，改用 `[最小分位数, 最大分位数]`
      区间上的 `T+1` 个等距边界；去重后只剩一个值（常数字段）时按最小正间隔向上展开。

    第二条分支实际把该字段的分箱由分位数分箱换成等距分箱。X23 前 20 万行的 81 个数值列
    实测有 `70` 列命中该分支（`T=8`），其中 `27` 列只因单次分位数相等就整列改为等距。
    这是本函数最需要复核的行为，见交付报告的“待裁决”条目。

    去重与严格递增核验都在**转成 float32 之后**进行：分位数在 float64 下互不相同，
    但落到 float32 网格上可能塌缩成同一个数，若只在 float64 上核验，返回的
    float32 边界仍可能出现零宽箱。常数字段的展开间隔按取值量级取相对值，
    使补出的边界在 float32 下也能彼此区分。

    Args:
        values: 训练区取值，形状 `(n, F)`。分位数计算会对该数组做一次排序副本，
            大矩阵调用前需自行确认内存。
        bin_count: 箱数 `T`，需为正整数。

    Returns:
        形状 `(F, T+1)` 的 float32 箱边界，逐行严格递增。

    Raises:
        ValueError: 输入不是二维，或 `bin_count` 非正。
        RuntimeError: 去重与补齐后边界仍未能严格递增（例如取值含 NaN）。
    """
    if values.ndim != 2:
        raise ValueError(f"训练区取值必须是 n×F，实际 {values.shape}")
    if bin_count < 1:
        raise ValueError(f"箱数必须为正整数，实际 {bin_count}")
    quantiles = np.linspace(0.0, 1.0, bin_count + 1)
    # 先落到 float32，后续去重与核验都在最终精度上进行。
    raw = np.quantile(values, quantiles, axis=0).T.astype(np.float32)  # (F, T+1)
    edges = np.empty_like(raw)
    float32_eps = float(np.finfo(np.float32).eps)
    for field in range(raw.shape[0]):
        unique = np.unique(raw[field])
        if unique.size >= bin_count + 1:
            edges[field] = unique[
                np.linspace(0, unique.size - 1, bin_count + 1).round().astype(int)
            ]
            continue
        # 该字段改为 [最小分位数, 最大分位数] 上的等距分箱，分位数间距在此丢失。
        span = float(unique[-1] - unique[0]) if unique.size > 1 else 0.0
        # 相对间隔：8 倍 float32 机器精度乘以取值量级，保证转 float32 后仍严格递增。
        magnitude = max(abs(float(unique[0])), abs(float(unique[-1])), 1.0)
        step = max(span / bin_count, float32_eps * 8.0 * magnitude)
        edges[field] = unique[0] + step * np.arange(bin_count + 1)
    if not np.all(np.diff(edges, axis=1) > 0):
        raise RuntimeError("箱边界未能严格递增，PLE 编码会除零")
    return edges


def piecewise_linear_encode(x: torch.Tensor, edges: torch.Tensor) -> torch.Tensor:
    """PLE 编码，`(n, F)` 与 `(F, T+1)` 进，`(n, F, T)` 出。

    形式化第 3.1 节（Gorishniy 等 2022 式 1）：

        ε_t = 0                                          x < b_{t-1} 且 t > 1
              1                                          x ≥ b_t 且 t < T
              (x − b_{t-1}) / (b_t − b_{t-1})            其余

    等价实现：先算逐箱的线性坐标 `raw`，再对 `t > 1` 的箱下截到 `0`、
    对 `t < T` 的箱上截到 `1`。**第一箱不下截、末箱不上截**，保留原论文对
    训练区范围外取值的线性外推；`T = 1` 时两端都不截，退化为纯线性坐标。

    全程使用 `torch.where` 与 `clamp` 构造新张量，不做任何原地写入。

    Args:
        x: 数值字段取值，形状 `(n, F)`。
        edges: 逐字段箱边界，形状 `(F, T+1)`，须逐行严格递增。

    Returns:
        形状 `(n, F, T)` 的编码张量，dtype 由 `x` 与 `edges` 的类型提升决定。

    Raises:
        RuntimeError: 输入维度不符或字段数不一致。
    """
    if x.ndim != 2:
        raise RuntimeError(f"数值输入必须是 n×F，实际 {tuple(x.shape)}")
    if edges.ndim != 2 or edges.shape[0] != x.shape[1]:
        raise RuntimeError(
            f"箱边界必须是 {x.shape[1]}×(T+1)，实际 {tuple(edges.shape)}"
        )
    lower = edges[:, :-1].unsqueeze(0)  # (1, F, T)
    width = (edges[:, 1:] - edges[:, :-1]).unsqueeze(0)  # (1, F, T)
    raw = (x.unsqueeze(-1) - lower) / width
    bin_count = width.shape[-1]
    index = torch.arange(bin_count, device=x.device).view(1, 1, -1)
    floored = torch.where(index > 0, raw.clamp(min=0.0), raw)
    return torch.where(index < bin_count - 1, floored.clamp(max=1.0), floored)


def entity_gated_ple_parameter_count(
    numeric_field_count: int,
    bin_count: int,
    d_token: int,
    gate_hidden: int,
    gate_mode: str = "entity_state",
) -> int:
    """M-E 专属参数量：位移嵌入 `F·T·d` 加门参数。

    形式化第六节的闭式，冻结取值 `entity_gated_ple_parameter_count(81, 8, 192, 64) == 124673`
    （位移 `81×8×192 = 124416` 加门 `4h + 1 = 257`）。

    消融臂 E1（`constant`）与 E2（`binary_indicator`）的门是单个可学标量 `β`，
    门参数为 `1`，总量为 `124417`；`gate_hidden` 对这两个模式不产生参数
    （形式化第九节的嵌套族，两臂与 C10 的容量差恰为 `256`）。

    Args:
        numeric_field_count: 数值字段数 `F`。
        bin_count: PLE 箱数 `T`。
        d_token: Token 宽度 `d`。
        gate_hidden: 门 MLP 隐藏宽度 `h`，只对 `entity_state` 生效。
        gate_mode: 门模式，取值见 `GATE_MODES`；默认 `entity_state`（完整 M-E）。

    Returns:
        M-E 专属参数量。骨干分词器参数不计入。

    Raises:
        ValueError: 门模式未登记。
    """
    if gate_mode not in GATE_MODES:
        raise ValueError(f"未知门模式：{gate_mode}")
    displacement = numeric_field_count * bin_count * d_token
    if gate_mode == "entity_state":
        # Linear(2, h) 的 2h + h，加 Linear(h, 1) 的 h + 1。
        gate = 2 * gate_hidden + gate_hidden + gate_hidden + 1
    else:
        gate = 1
    return displacement + gate


class EntityGatedPLETokenizer(nn.Module):
    """现有线性分词 ＋ 实体门控的分段线性位移通道。

    Token 布局与 `base_tokenizer` 一致：`[CLS]` 一列、数值 `F` 列、类别 `C` 列，
    共 `F + 1 + C` 列。位移**只作用于数值列**，`[CLS]` 与类别列补零后拼接相加；
    门 `γ` 由严格过去实体状态给出，实体首片段恒为零。

    `base_tokenizer` 以子模块方式持有，其参数属于骨干、不重复计入 M-E，
    也不在本模块内被重新初始化。统计 M-E 专属参数量时须排除 `base.` 前缀的项。
    `bin_edges` 用 `register_buffer` 登记：缓冲区不出现在 `parameters()` 中，
    优化器不会把它当参数，但会随模块一起换设备并进入 `state_dict`。
    """

    bin_edges: torch.Tensor

    def __init__(
        self,
        base_tokenizer: nn.Module,
        bin_edges: torch.Tensor,
        d_token: int,
        gate_hidden: int,
        gate_mode: str,
    ) -> None:
        super().__init__()
        if gate_mode not in GATE_MODES:
            raise ValueError(f"未知门模式：{gate_mode}")
        numeric_field_count = int(base_tokenizer.numeric_field_count)
        if bin_edges.ndim != 2 or bin_edges.shape[0] != numeric_field_count:
            raise ValueError(
                f"箱边界必须是 {numeric_field_count}×(T+1)，实际 {tuple(bin_edges.shape)}"
            )
        if bin_edges.shape[1] < 2:
            raise ValueError(f"箱边界每行至少 2 个，实际 {bin_edges.shape[1]}")
        if int(base_tokenizer.d_token) != int(d_token):
            raise ValueError(
                f"位移通道宽度 {d_token} 与骨干分词器宽度 {base_tokenizer.d_token} 不一致"
            )
        self.base = base_tokenizer
        self.gate_mode = gate_mode
        self.numeric_field_count = numeric_field_count
        self.category_count = len(base_tokenizer.categories)
        self.register_buffer("bin_edges", bin_edges.detach().clone())
        bin_count = int(bin_edges.shape[1]) - 1
        self.bin_count = bin_count
        self.displacement = nn.Parameter(
            torch.empty(numeric_field_count, bin_count, d_token)
        )
        nn_init.kaiming_uniform_(self.displacement, a=math.sqrt(5))
        if gate_mode == "entity_state":
            self.gate_hidden_layer = nn.Linear(2, gate_hidden)
            self.gate_output_layer = nn.Linear(gate_hidden, 1)
        else:
            # E1 与 E2 的常数门：可学标量，初始化 0 使 σ(β) = 0.5，不固定为 1。
            self.gate_scalar = nn.Parameter(torch.zeros(1))

    def gate(self, entity_state: torch.Tensor) -> torch.Tensor:
        """返回 `(n, 1)` 的门值。

        `entity_state` 第 0 列是 `log(1+c)/log(1+C)`，第 1 列是 `log(1+Δ)/log(1+D)`。
        `c = 0` 时第 0 列恰为 `0`，因此 `entity_state[:, :1] > 0` 是形式化第 3.3 节
        指示函数 `𝟙[c ≥ 1]` 的等价实现，不需要额外传指示列。

        Args:
            entity_state: 归一化后的严格过去实体状态，形状 `(n, 2)`。

        Returns:
            形状 `(n, 1)` 的门值，取值落在 `[0, 1)`。
        """
        if self.gate_mode == "entity_state":
            hidden = torch.relu(self.gate_hidden_layer(entity_state))
            value = torch.sigmoid(self.gate_output_layer(hidden))
        else:
            value = torch.sigmoid(self.gate_scalar).expand(entity_state.shape[0], 1)
        if self.gate_mode == "constant":
            return value
        has_history = (entity_state[:, :1] > 0).to(value.dtype)
        return value * has_history

    def forward(
        self,
        x_num: torch.Tensor,
        x_cat: torch.Tensor | None,
        entity_state: torch.Tensor,
    ) -> torch.Tensor:
        """产出 `(n, F+1+C, d)` 的 Token 张量。

        Args:
            x_num: 数值字段，形状 `(n, F)`。
            x_cat: 词表字段，形状 `(n, C)`；本候选无词表字段时为 `None`。
            entity_state: 严格过去实体状态，形状 `(n, 2)`。

        Returns:
            骨干线性分词结果加门控位移，形状与 `base_tokenizer` 的输出逐位同形。

        Raises:
            RuntimeError: 实体状态形状与批量不符。
        """
        tokens = self.base(x_num, x_cat)
        if entity_state.ndim != 2 or entity_state.shape != (x_num.shape[0], 2):
            raise RuntimeError(f"实体状态必须是 n×2，实际 {tuple(entity_state.shape)}")
        encoded = piecewise_linear_encode(x_num, self.bin_edges).to(self.displacement.dtype)
        # (n,F,T) 与 (F,T,d) 沿箱维求和，得每字段的位移向量 (n,F,d)。
        displacement = torch.einsum("nft,ftd->nfd", encoded, self.displacement)
        gated = self.gate(entity_state).unsqueeze(-1) * displacement
        batch_size, _, width = gated.shape
        # [CLS] 与类别列补零：新建零张量后拼接，不对参与 autograd 的张量做原地写入。
        parts = [gated.new_zeros((batch_size, 1, width)), gated]
        if self.category_count:
            parts.append(gated.new_zeros((batch_size, self.category_count, width)))
        return tokens + torch.cat(parts, dim=1).to(tokens.dtype)
