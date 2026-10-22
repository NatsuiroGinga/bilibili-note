"""评测服务用的 tabm4 结构镜像（只依赖 torch，不导入训练工具链）。

与 `thesis/experiments/llm_probe/tools/ch4_lamda_tabm_pilot.py` 中的
`BatchEnsembleLinear` / `TabMMLP` 逐行一致；镜像的目的是让 Python 服务只加载
PyTorch，而不把 pyarrow/sklearn 等训练依赖算进服务 RSS 与启动时间。
参数键与形状由 `verify_model_parity.py` 用冻结权重和真实 2024 面板批次对照。
"""

from __future__ import annotations

import torch
import torch.nn as nn


class BatchEnsembleLinear(nn.Module):
    """共享主权重 W/b ＋成员专属 r（输入缩放）、s（输出缩放）、β（成员偏置）。

    等价于逐成员 `W_eff_i = W ⊙ (r_i s_i^T)`：`y_i = s_i ⊙ (W(r_i ⊙ x_i) + b) + β_i`，
    不物化 W_eff。输入 (B, k, in) → 输出 (B, k, out)。
    """

    def __init__(self, in_dim: int, out_dim: int, k: int, first: bool) -> None:
        super().__init__()
        self.k = k
        self.weight = nn.Parameter(torch.empty(out_dim, in_dim))
        self.bias = nn.Parameter(torch.zeros(out_dim))
        nn.init.kaiming_uniform_(self.weight, a=5 ** 0.5)
        self.r = nn.Parameter(torch.ones(k, in_dim))
        self.s = nn.Parameter(torch.ones(k, out_dim))
        self.beta = nn.Parameter(torch.zeros(k, out_dim))
        if first:
            signs = torch.randint(0, 2, (k, in_dim)).float() * 2.0 - 1.0
            with torch.no_grad():
                self.r.copy_(signs)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = torch.matmul(x, self.weight.t()) + self.bias
        return self.s * h + self.beta


class TabMMLP(nn.Module):
    """官方 ChenEncoderMLP 的逐层 BatchEnsemble 化（同宽同深同 Dropout 位置）。"""

    def __init__(self, input_dim: int, k: int) -> None:
        super().__init__()
        self.k = k
        self.enc1 = BatchEnsembleLinear(input_dim, 512, k, first=True)
        self.enc2 = BatchEnsembleLinear(512, 384, k, first=False)
        self.enc3 = BatchEnsembleLinear(384, 256, k, first=False)
        self.enc4 = BatchEnsembleLinear(256, 128, k, first=False)
        self.cls1 = BatchEnsembleLinear(128, 100, k, first=False)
        self.cls2 = BatchEnsembleLinear(100, 100, k, first=False)
        self.cls3 = BatchEnsembleLinear(100, 1, k, first=False)
        self.drop = nn.Dropout(0.2)

    def forward(self, x: torch.Tensor, return_members: bool = False) -> torch.Tensor:
        if x.dim() == 2:
            b = x.shape[0]
            h = x.unsqueeze(1).expand(b, self.k, x.shape[1]) * self.enc1.r
        else:
            h = x
        for layer in (self.enc1, self.enc2, self.enc3, self.enc4):
            h = torch.relu(layer(h))
        h = self.drop(torch.relu(self.cls1(h)))
        h = self.drop(torch.relu(self.cls2(h)))
        out = torch.sigmoid(self.cls3(h))
        if return_members:
            return out
        return out.mean(dim=1)
