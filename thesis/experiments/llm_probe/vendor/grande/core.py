"""
GRANDE 官方 PyTorch 核心的 Q0 最小提取版。

来源：https://github.com/s-marton/GRANDE
固定提交：07f7278b30ab9ebbbdc544e5f9a91f1b5df7fecb
原文件：GRANDE/GRANDE.py 中 GRANDE_Module
许可证：MIT，见同目录 LICENSE。

本提取版只保留二分类硬轴对齐树的直接 PyTorch 前向，删除
DataFrame、AutoGluon、类别编码、内部预处理、高层 fit/predict 包装和本 Q0 禁用的嵌入。
"""

from __future__ import annotations

import random
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class GrandeCore(nn.Module):
    """二分类 GRANDE 硬分裂树集成核心。"""

    def __init__(
        self,
        *,
        number_of_variables: int,
        depth: int,
        n_estimators: int,
        dropout: float,
        selected_variables: float,
        random_seed: int,
    ) -> None:
        super().__init__()
        self.number_of_variables = number_of_variables
        self.depth = depth
        self.n_estimators = n_estimators
        self.dropout = dropout
        self.random_seed = random_seed
        self.internal_node_num = 2**depth - 1
        self.leaf_node_num = 2**depth
        selected_count = int(number_of_variables * selected_variables)
        self.selected_variables = min(max(selected_count, 10), min(50, number_of_variables))

        set_seed(random_seed)
        features = torch.stack(
            [
                torch.tensor(
                    np.random.choice(number_of_variables, size=self.selected_variables, replace=False),
                    dtype=torch.int64,
                )
                for _ in range(n_estimators)
            ]
        )
        self.register_buffer("features_by_estimator", features)

        path_identifiers: list[int] = []
        internal_indices: list[int] = []
        for leaf_index in range(self.leaf_node_num):
            for current_depth in range(1, depth + 1):
                path_identifiers.append((leaf_index // (2 ** (depth - current_depth))) % 2)
                internal_indices.append(
                    (2 ** (current_depth - 1))
                    + (leaf_index // 2 ** (depth - (current_depth - 1)))
                    - 1
                )
        self.register_buffer(
            "path_identifier_list",
            torch.tensor(path_identifiers, dtype=torch.long).reshape(self.leaf_node_num, depth),
        )
        self.register_buffer(
            "internal_node_index_list",
            torch.tensor(internal_indices, dtype=torch.long).reshape(self.leaf_node_num, depth),
        )

        shape = (n_estimators, self.internal_node_num, self.selected_variables)
        self.split_values = nn.Parameter(torch.empty(shape))
        self.split_index_array = nn.Parameter(torch.empty(shape))
        self.estimator_weights = nn.Parameter(torch.empty(n_estimators, self.leaf_node_num))
        self.leaf_classes_array = nn.Parameter(torch.empty(n_estimators, self.leaf_node_num))
        for parameter in (
            self.split_values,
            self.split_index_array,
            self.estimator_weights,
            self.leaf_classes_array,
        ):
            nn.init.normal_(parameter, mean=0.0, std=0.05)

    def forward(
        self,
        inputs: torch.Tensor,
        *,
        return_per_estimator_logits: bool = False,
        return_diagnostics: bool = False,
    ) -> Any:
        if inputs.ndim != 2 or inputs.shape[1] != self.number_of_variables:
            raise ValueError("输入必须是 N×83 的二维张量")
        selected_inputs = inputs[:, self.features_by_estimator]

        soft_indices = F.softmax(self.split_index_array, dim=-1)
        hard_indices = F.one_hot(
            torch.argmax(soft_indices, dim=-1),
            num_classes=soft_indices.shape[-1],
        ).to(soft_indices.dtype)
        split_indices = soft_indices - (soft_indices - hard_indices).detach()

        split_threshold = torch.einsum("ein,ein->ei", self.split_values, split_indices)
        split_input = torch.einsum("ben,ein->bei", selected_inputs, split_indices)
        soft_route = (F.softsign(split_threshold - split_input) + 1.0) / 2.0
        hard_route = torch.round(soft_route)
        route = soft_route - (soft_route - hard_route).detach()

        selected_route = route[..., self.internal_node_index_list]
        left = selected_route
        right = 1.0 - selected_route
        path_probability = torch.prod(
            (1 - self.path_identifier_list) * left + self.path_identifier_list * right,
            dim=3,
        )
        selected_estimator_weight = torch.einsum(
            "el,bel->be",
            self.estimator_weights,
            path_probability,
        )
        estimator_weight = F.softmax(selected_estimator_weight, dim=-1)
        if self.training and self.dropout > 0.0:
            estimator_weight = F.dropout(estimator_weight, p=self.dropout, training=True)
            estimator_weight = estimator_weight / estimator_weight.sum(dim=1, keepdim=True).clamp_min(1e-8)
        weighted_path = torch.einsum("bel,be->bel", path_probability, estimator_weight)
        per_estimator = torch.einsum("el,bel->be", self.leaf_classes_array, weighted_path)
        logits = torch.einsum("be->b", per_estimator)

        diagnostics = None
        if return_diagnostics:
            selected_leaf = torch.argmax(path_probability, dim=-1)
            leaf_counts = torch.zeros(
                self.n_estimators,
                self.leaf_node_num,
                dtype=torch.int64,
                device=inputs.device,
            )
            leaf_counts.scatter_add_(1, selected_leaf.t(), torch.ones_like(selected_leaf.t(), dtype=torch.int64))
            entropy = -(soft_indices.clamp_min(1e-12) * soft_indices.clamp_min(1e-12).log()).sum(-1)
            diagnostics = {
                "split_selection_entropy": entropy.mean(),
                "left_route_fraction": route.mean(),
                "right_route_fraction": 1.0 - route.mean(),
                "empty_leaf_fraction": (leaf_counts == 0).to(torch.float32).mean(),
                "valid_tree_fraction": (leaf_counts.sum(1) > 0).to(torch.float32).mean(),
            }
        if return_per_estimator_logits or return_diagnostics:
            return logits, per_estimator * self.n_estimators, estimator_weight, diagnostics
        return logits

    def parameter_groups(self) -> dict[str, list[nn.Parameter]]:
        return {
            "split_index": [self.split_index_array],
            "split_values": [self.split_values],
            "leaf_values": [self.leaf_classes_array],
            "instance_leaf_weights": [self.estimator_weights],
        }
