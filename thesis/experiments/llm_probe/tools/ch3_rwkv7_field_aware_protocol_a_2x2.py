"""N-08：RWKV-7 字段感知输入选择与协议 A 单次四格。

选择阶段严格使用 LSPR23 固定实体不相交训练/验证。输入适配器与四格全部封印后，
才允许每格一次 LSPR24 描述性评价。该入口不包含三折、OOF 或嵌套选择。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import resource
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


SCHEMA_VERSION = "ch3-rwkv7-field-aware-protocol-a-2x2-config-v1"
RESULT_SCHEMA_VERSION = "ch3-rwkv7-field-aware-protocol-a-2x2-results-v1"
RUN_ID = "ch3-rwkv7-field-aware-protocol-a-2x2-seed42-v1"
SOURCE_ARRAYS = ("X23", "y23", "I23", "M23", "E23", "T23")
TARGET_ARRAYS = ("X24", "y24", "I24", "M24", "s24", "d24", "t24")
ADAPTER_ORDER = ("R0", "R1", "R2")
CAPACITY_ORDER = ("K0", "K1", "K2")
CELL_ORDER = ("C00", "C01", "C10", "C11")
DR_FPR_GRID = (0.001, 0.005, 0.01, 0.02, 0.04, 0.08)
PARAMETER_COUNTS = {
    "K0": {"R0": 91_730, "R1": 104_274, "R2": 104_274},
    "K1": {"R0": 5_126_978, "R1": 5_185_458, "R2": 5_458_754},
    "K2": {"R0": 8_900_354, "R1": 8_977_842, "R2": 9_490_178},
}
FIELD_CONTRACT_SHA256 = "e622f059d2295c8740daeb7d29fe92761c68c17a78b3d57ad65821d9137f105d"
T0 = time.time()
average_precision_score: Any = None
roc_auc_score: Any = None


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def atomic_torch(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    torch.save(value, temporary)
    os.replace(temporary, path)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def process_peak_rss_mib() -> float:
    peak = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak / 1024.0 if sys.platform != "darwin" else peak / (1024.0 * 1024.0)


def write_status(
    output_root: Path,
    state: str,
    stage: str,
    exit_code: int | None,
    detail: str,
) -> None:
    atomic_json(
        output_root / "status.json",
        {
            "schema_version": "ch3-rwkv7-field-aware-status-v1",
            "run_id": RUN_ID,
            "state": state,
            "stage": stage,
            "exit_code": exit_code,
            "detail": detail,
            "updated_at_unix": time.time(),
        },
    )


def expected_cells() -> dict[str, dict[str, bool]]:
    return {
        "C00": {"causal_prefix_aggregation": False, "learned_lp_pooling": False},
        "C01": {"causal_prefix_aggregation": False, "learned_lp_pooling": True},
        "C10": {"causal_prefix_aggregation": True, "learned_lp_pooling": False},
        "C11": {"causal_prefix_aggregation": True, "learned_lp_pooling": True},
    }


def validate_config(config: Mapping[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION or config.get("run_id") != RUN_ID:
        raise ValueError("配置模式或运行身份不符")
    if config.get("source_arrays") != list(SOURCE_ARRAYS):
        raise ValueError("源年数组白名单不符")
    if config.get("target_arrays") != list(TARGET_ARRAYS):
        raise ValueError("目标年数组白名单不符")
    if config.get("adapter_order") != list(ADAPTER_ORDER):
        raise ValueError("输入适配器顺序不符")
    if config.get("capacity_order") != list(CAPACITY_ORDER):
        raise ValueError("容量候选顺序不符")
    if config.get("cells") != expected_cells():
        raise ValueError("协议 A 四格不符")
    if config.get("target_year_arrays_read_before_selection_frozen") != 0:
        raise ValueError("目标数组必须在全部选择封印前保持零读取")
    input_contract = config.get("input_contract", {})
    if input_contract != {
        "flow_count_23": 16_353_511,
        "sequence_count_23": 271_815,
        "entity_count_23": 150_680,
        "feature_count": 83,
        "sequence_length": 128,
        "train_sequences": 208_598,
        "validation_sequences": 22_444,
        "flow_count_24": 20_227_356,
        "entity_count_24": 47_115,
        "positive_entity_count_24": 752,
    }:
        raise ValueError("输入形状合同不符")
    training = config.get("training", {})
    expected_training = {
        "seed": 42,
        "batch_size": 64,
        "epochs": 20,
        "steps_per_epoch": 1000,
        "learning_rate": 0.002,
        "w0_learning_rate_scale": 2.0,
        "weight_decay": 0.01,
        "gradient_clip_norm": 1.0,
        "auxiliary_loss_weight": 1.0,
        "dropout": 0.1,
        "validation_fraction": 0.1,
        "time_tail_fraction": 0.15,
        "maximum_gpu_hours": 4.5,
        "actual_parallelism": 1,
        "precision": "float32",
    }
    if training != expected_training:
        raise ValueError("训练或资源合同不符")
    candidate = config.get("candidate", {})
    if candidate.get("official_source_commit") != "952102498e9ed367ea0a59ee64106916d474d30f":
        raise ValueError("RWKV-7 官方源码提交不符")
    if candidate.get("official_license") != "Apache-2.0":
        raise ValueError("RWKV-7 许可证不符")
    adapters = config.get("adapters", {})
    if set(adapters) != set(ADAPTER_ORDER):
        raise ValueError("输入适配器集合不符")
    capacities = config.get("capacities", {})
    if list(capacities) != list(CAPACITY_ORDER):
        raise ValueError("容量候选集合或顺序不符")
    expected_shapes = {
        "K0": (112, 16, 8, 1, "legacy_single_time_mix"),
        "K1": (576, 64, 32, 3, "preln_value_residual_time_mix_stack"),
        "K2": (768, 64, 32, 3, "preln_value_residual_time_mix_stack"),
    }
    for capacity_key, expected in expected_shapes.items():
        capacity = capacities[capacity_key]
        actual = (
            capacity.get("hidden_size"),
            capacity.get("head_size"),
            capacity.get("lora_size"),
            capacity.get("time_mix_layers"),
            capacity.get("structure"),
        )
        if actual != expected:
            raise ValueError(f"{capacity_key} 结构合同不符")
        if capacity.get("parameter_counts") != PARAMETER_COUNTS[capacity_key]:
            raise ValueError(f"{capacity_key} 参数量台账不符")
    fields = config.get("field_contract", {})
    names = fields.get("names")
    groups = fields.get("groups")
    if not isinstance(names, list) or len(names) != 83 or len(set(names)) != 83:
        raise ValueError("83 字段名清单无效")
    if not isinstance(groups, list) or len(groups) != 12:
        raise ValueError("字段语义组必须恰为 12 组")
    flattened = [index for group in groups for index in group["indices"]]
    if sorted(flattened) != list(range(83)) or len(flattened) != 83:
        raise ValueError("字段语义组必须无重无漏覆盖 83 列")
    if fields.get("canonical_sha256") != FIELD_CONTRACT_SHA256 or fields.get(
        "canonical_sha256"
    ) != canonical_sha256({"names": names, "groups": groups}):
        raise ValueError("字段合同摘要不符")
    policy = config.get("artifact_policy", {})
    if not all(
        policy.get(key) is value
        for key, value in {
            "persist_all_epoch_model_weights": True,
            "persist_latest_complete_inflight": True,
            "delete_inflight_after_completion": False,
            "persist_per_flow_scores": False,
            "persist_per_entity_scores": False,
            "persist_split_member_arrays": False,
        }.items()
    ):
        raise ValueError("检查点或逐样本制品策略不符")
    resource_contract = config.get("resource_contract", {})
    if resource_contract.get("capacity_resource_anchors") != {
        "gru_parameters": 5_355_649,
        "transformer_parameters": 10_729_345,
    }:
        raise ValueError("已发表神经基线资源锚不符")
    evaluation = config.get("evaluation", {})
    if (
        evaluation.get("sequence_batch_size") != 512
        or evaluation.get("target_evaluation_calls") != 4
        or evaluation.get("dr_fpr_grid") != list(DR_FPR_GRID)
        or not evaluation.get("target_load_after_all_source_selections_sealed")
    ):
        raise ValueError("评价合同不符")
    for capacity_key in CAPACITY_ORDER:
        for adapter_key in ADAPTER_ORDER:
            model = build_model(config, adapter_key, capacity_key, "C00")
            del model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RWKV-7 字段感知输入选择与协议 A 单次四格"
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--resource-receipt")
    parser.add_argument("--publish-only", action="store_true")
    parser.add_argument("--authorized-swanlab-workspace")
    parser.add_argument("--authorized-swanlab-project")
    return parser.parse_args()


def rwkv7_op(
    r: torch.Tensor,
    w: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    a: torch.Tensor,
    b: torch.Tensor,
    head_size: int,
) -> torch.Tensor:
    """固定官方提交的纯 PyTorch RWKV-7 递归；矩阵状态始终 FP32。"""
    batch, length, channels = r.shape
    heads = channels // head_size
    r = r.view(batch, length, heads, head_size).float()
    k = k.view(batch, length, heads, head_size).float()
    v = v.view(batch, length, heads, head_size).float()
    a = a.view(batch, length, heads, head_size).float()
    b = b.view(batch, length, heads, head_size).float()
    w = torch.exp(-torch.exp(w.view(batch, length, heads, head_size).float()))
    output = torch.zeros_like(r, dtype=torch.float32)
    state = torch.zeros(
        batch,
        heads,
        head_size,
        head_size,
        dtype=torch.float32,
        device=r.device,
    )
    for position in range(length):
        kk = k[:, position].view(batch, heads, 1, head_size)
        rr = r[:, position].view(batch, heads, head_size, 1)
        vv = v[:, position].view(batch, heads, head_size, 1)
        aa = a[:, position].view(batch, heads, head_size, 1)
        bb = b[:, position].view(batch, heads, 1, head_size)
        state = state * w[:, position, :, None, :] + state @ aa @ bb + vv @ kk
        output[:, position] = (state @ rr).view(batch, heads, head_size)
    return output.view(batch, length, channels)


class RWKV7TimeMix(nn.Module):
    """固定官方提交的时间混合块，含多层 value residual。"""

    def __init__(
        self,
        channels: int,
        head_size: int,
        lora_size: int,
        layer_id: int,
        layer_count: int,
    ) -> None:
        super().__init__()
        if channels % head_size != 0:
            raise ValueError("RWKV-7 通道数必须能被头大小整除")
        heads = channels // head_size
        self.channels = channels
        self.head_size = head_size
        self.heads = heads
        ratio_0_to_1 = layer_id / max(layer_count - 1, 1)
        ratio_1_to_almost0 = 1.0 - layer_id / layer_count
        self.layer_id = layer_id
        with torch.no_grad():
            ddd = torch.arange(channels, dtype=torch.float32).reshape(
                1, 1, channels
            ) / channels
            self.x_r = nn.Parameter(1.0 - torch.pow(ddd, 0.2 * ratio_1_to_almost0))
            self.x_w = nn.Parameter(1.0 - torch.pow(ddd, 0.9 * ratio_1_to_almost0))
            self.x_k = nn.Parameter(1.0 - torch.pow(ddd, 0.7 * ratio_1_to_almost0))
            self.x_v = nn.Parameter(1.0 - torch.pow(ddd, 0.7 * ratio_1_to_almost0))
            self.x_a = nn.Parameter(1.0 - torch.pow(ddd, 0.9 * ratio_1_to_almost0))
            self.x_g = nn.Parameter(1.0 - torch.pow(ddd, 0.2 * ratio_1_to_almost0))
            www = torch.zeros(channels)
            zigzag = torch.zeros(channels)
            linear = torch.zeros(channels)
            for index in range(channels):
                linear[index] = index / (channels - 1) - 0.5
                zigzag[index] = (
                    (index % head_size) - ((head_size - 1) / 2)
                ) / ((head_size - 1) / 2)
                zigzag[index] = zigzag[index] * abs(zigzag[index])
                if layer_count == 1:
                    www[index] = -6 + 6 * (index / (channels - 1))
                else:
                    www[index] = -7 + 5 * (index / (channels - 1)) ** (
                        0.85 + 1.0 * math.sqrt(ratio_0_to_1)
                    )

            def ortho_init(value: torch.Tensor, scale: float) -> torch.Tensor:
                gain = (
                    math.sqrt(value.shape[0] / value.shape[1])
                    if value.shape[0] > value.shape[1]
                    else 1.0
                )
                nn.init.orthogonal_(value, gain=gain * scale)
                return value

            self.w1 = nn.Parameter(torch.zeros(channels, lora_size))
            self.w2 = nn.Parameter(
                ortho_init(torch.zeros(lora_size, channels), 0.1)
            )
            self.w0 = nn.Parameter(
                www.reshape(1, 1, channels) + 0.5 + zigzag * 2.5
            )
            self.a1 = nn.Parameter(torch.zeros(channels, lora_size))
            self.a2 = nn.Parameter(
                ortho_init(torch.zeros(lora_size, channels), 0.1)
            )
            self.a0 = nn.Parameter(
                torch.zeros(1, 1, channels)
                - 0.19
                + zigzag * 0.3
                + linear * 0.4
            )
            self.g1 = nn.Parameter(torch.zeros(channels, lora_size))
            self.g2 = nn.Parameter(
                ortho_init(torch.zeros(lora_size, channels), 0.1)
            )
            self.k_k = nn.Parameter(
                torch.zeros(1, 1, channels) + 0.71 - linear * 0.1
            )
            self.k_a = nn.Parameter(torch.zeros(1, 1, channels) + 1.02)
            self.r_k = nn.Parameter(torch.zeros(heads, head_size) - 0.04)
            if layer_id > 0:
                self.v0 = nn.Parameter(
                    torch.zeros(1, 1, channels) + 0.73 - linear * 0.4
                )
                self.v1 = nn.Parameter(torch.zeros(channels, lora_size))
                self.v2 = nn.Parameter(
                    ortho_init(torch.zeros(lora_size, channels), 0.1)
                )
            self.time_shift = nn.ZeroPad2d((0, 0, 1, -1))
            self.receptance = nn.Linear(channels, channels, bias=False)
            self.key = nn.Linear(channels, channels, bias=False)
            self.value = nn.Linear(channels, channels, bias=False)
            self.output = nn.Linear(channels, channels, bias=False)
            self.ln_x = nn.GroupNorm(heads, channels, eps=64e-5)
            self.receptance.weight.data.uniform_(
                -0.5 / math.sqrt(channels), 0.5 / math.sqrt(channels)
            )
            self.key.weight.data.uniform_(
                -0.05 / math.sqrt(channels), 0.05 / math.sqrt(channels)
            )
            self.value.weight.data.uniform_(
                -0.5 / math.sqrt(channels), 0.5 / math.sqrt(channels)
            )
            self.output.weight.data.zero_()

    def forward(
        self, values: torch.Tensor, value_first: torch.Tensor | None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        batch, length, channels = values.shape
        shifted = self.time_shift(values) - values
        xr = values + shifted * self.x_r
        xw = values + shifted * self.x_w
        xk = values + shifted * self.x_k
        xv = values + shifted * self.x_v
        xa = values + shifted * self.x_a
        xg = values + shifted * self.x_g
        r = self.receptance(xr)
        w = -F.softplus(
            -(self.w0 + torch.tanh(xw @ self.w1) @ self.w2)
        ) - 0.5
        k = self.key(xk)
        v = self.value(xv)
        if self.layer_id == 0:
            value_first = v
        else:
            if value_first is None:
                raise RuntimeError("多层 RWKV-7 缺少首层 value residual")
            v = v + (value_first - v) * torch.sigmoid(
                self.v0 + (xv @ self.v1) @ self.v2
            )
        a = torch.sigmoid(self.a0 + (xa @ self.a1) @ self.a2)
        g = torch.sigmoid(xg @ self.g1) @ self.g2
        kk = k * self.k_k
        kk = F.normalize(
            kk.view(batch, length, self.heads, -1), dim=-1, p=2.0
        ).view(batch, length, channels)
        k = k * (1 + (a - 1) * self.k_a)
        output = rwkv7_op(r, w, k, v, -kk, kk * a, self.head_size)
        output = self.ln_x(output.view(batch * length, channels)).view(
            batch, length, channels
        )
        bonus = (
            (
                r.view(batch, length, self.heads, -1)
                * k.view(batch, length, self.heads, -1)
                * self.r_k
            ).sum(dim=-1, keepdim=True)
            * v.view(batch, length, self.heads, -1)
        ).view(batch, length, channels)
        return self.output((output + bonus) * g), value_first


class RWKV7TimeMixLayer(nn.Module):
    def __init__(
        self,
        channels: int,
        head_size: int,
        lora_size: int,
        layer_id: int,
        layer_count: int,
        residual: bool,
    ) -> None:
        super().__init__()
        self.residual = residual
        self.normalization = nn.LayerNorm(channels) if residual else nn.Identity()
        self.time_mix = RWKV7TimeMix(
            channels, head_size, lora_size, layer_id, layer_count
        )

    def forward(
        self, values: torch.Tensor, value_first: torch.Tensor | None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        update, value_first = self.time_mix(self.normalization(values), value_first)
        return (values + update if self.residual else update), value_first


class LinearInputAdapter(nn.Module):
    def __init__(self, hidden_size: int) -> None:
        super().__init__()
        self.projection = nn.Linear(83, hidden_size)

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.projection(values)


class FieldAwareInputAdapter(nn.Module):
    def __init__(
        self, groups: Sequence[Mapping[str, Any]], hidden_size: int
    ) -> None:
        super().__init__()
        self.scalar_projection = nn.Linear(1, 15)
        self.field_embedding = nn.Parameter(torch.empty(83, 15))
        self.group_embedding = nn.Embedding(12, 15)
        self.composition = nn.Linear(180, hidden_size)
        self.normalization = nn.LayerNorm(hidden_size)
        self.output_scale = nn.Parameter(torch.ones(()))
        group_ids = torch.empty(83, dtype=torch.long)
        buffer_names = []
        for group_id, group in enumerate(groups):
            indices = torch.tensor(group["indices"], dtype=torch.long)
            group_ids[indices] = group_id
            name = f"group_indices_{group_id:02d}"
            self.register_buffer(name, indices, persistent=True)
            buffer_names.append(name)
        self.register_buffer("field_group_ids", group_ids, persistent=True)
        self._group_index_buffer_names = tuple(buffer_names)
        nn.init.normal_(self.field_embedding, mean=0.0, std=0.02)
        nn.init.normal_(self.group_embedding.weight, mean=0.0, std=0.02)

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        tokens = self.scalar_projection(values.unsqueeze(-1))
        identity = self.field_embedding + self.group_embedding(
            self.field_group_ids
        )
        tokens = tokens + identity.view(1, 1, 83, 15)
        pooled = [
            tokens.index_select(2, getattr(self, name)).mean(2)
            for name in self._group_index_buffer_names
        ]
        composed = self.composition(torch.cat(pooled, dim=-1))
        return self.normalization(composed) * self.output_scale


class MatchedProjectionInputAdapter(nn.Module):
    def __init__(self, hidden_size: int) -> None:
        super().__init__()
        self.first = nn.Linear(83, hidden_size)
        self.second = nn.Linear(hidden_size, hidden_size, bias=False)

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.second(F.relu(self.first(values)))


class RWKV7ProtocolAModel(nn.Module):
    def __init__(
        self,
        adapter_key: str,
        capacity: Mapping[str, Any],
        groups: Sequence[Mapping[str, Any]],
        aggregate: bool,
        learned_lp: bool,
        dropout: float,
    ) -> None:
        super().__init__()
        self.adapter_key = adapter_key
        self.aggregate = aggregate
        self.learned_lp = learned_lp
        self.capacity_key = str(capacity["key"])
        hidden_size = int(capacity["hidden_size"])
        layer_count = int(capacity["time_mix_layers"])
        residual = capacity["structure"] == "preln_value_residual_time_mix_stack"
        # 共同模块先构造，保证各适配器在相同种子下共享同一初始化。
        self.time_mix_layers = nn.ModuleList(
            RWKV7TimeMixLayer(
                hidden_size,
                int(capacity["head_size"]),
                int(capacity["lora_size"]),
                layer_id,
                layer_count,
                residual,
            )
            for layer_id in range(layer_count)
        )
        self.fusion_layer = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.output_layer = nn.Linear(hidden_size, 1)
        self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))
        if adapter_key == "R0":
            self.input_adapter = LinearInputAdapter(hidden_size)
        elif adapter_key == "R1":
            self.input_adapter = FieldAwareInputAdapter(groups, hidden_size)
        elif adapter_key == "R2":
            self.input_adapter = MatchedProjectionInputAdapter(hidden_size)
        else:
            raise ValueError(f"未知输入适配器：{adapter_key}")

    @property
    def p(self) -> torch.Tensor:
        return torch.exp(self.p_log).clamp(1e-3, 1e3)

    def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
        if values.dtype != torch.float32:
            raise RuntimeError("N-08 正式首跑要求输入与 RWKV 状态均为 FP32")
        mask = valid.to(values.dtype)
        hidden = self.input_adapter(values * mask.unsqueeze(-1))
        value_first = None
        for layer in self.time_mix_layers:
            hidden, value_first = layer(hidden * mask.unsqueeze(-1), value_first)
            hidden = hidden * mask.unsqueeze(-1)
        if self.aggregate:
            count = torch.cumsum(mask, dim=1).clamp(min=1.0).unsqueeze(-1)
            context = torch.cumsum(hidden, dim=1) / count
            context = context * mask.unsqueeze(-1)
        else:
            context = torch.zeros_like(hidden)
        fused = self.fusion_layer(torch.cat((hidden, context), dim=-1))
        fused = fused * mask.unsqueeze(-1)
        return self.output_layer(fused).squeeze(-1)


def build_model(
    config: Mapping[str, Any], adapter_key: str, capacity_key: str, cell: str
) -> RWKV7ProtocolAModel:
    cell_config = config["cells"][cell]
    capacity = {"key": capacity_key, **config["capacities"][capacity_key]}
    model = RWKV7ProtocolAModel(
        adapter_key,
        capacity,
        config["field_contract"]["groups"],
        cell_config["causal_prefix_aggregation"],
        cell_config["learned_lp_pooling"],
        config["training"]["dropout"],
    )
    actual = sum(parameter.numel() for parameter in model.parameters())
    expected = PARAMETER_COUNTS[capacity_key][adapter_key]
    if actual != expected:
        raise RuntimeError(
            f"{capacity_key}/{adapter_key} 参数量不符：实际 {actual}，冻结 {expected}"
        )
    return model


def make_optimizer(
    config: Mapping[str, Any], model: nn.Module
) -> tuple[torch.optim.Optimizer, list[dict[str, Any]]]:
    training = config["training"]
    groups: dict[str, list[tuple[str, nn.Parameter]]] = {
        "no_decay_1x": [],
        "w0_no_decay_2x": [],
        "matrix_decay_1x": [],
    }
    for name, parameter in model.named_parameters():
        if name.endswith(".time_mix.w0"):
            groups["w0_no_decay_2x"].append((name, parameter))
        elif parameter.squeeze().ndim >= 2 and ".weight" in name:
            groups["matrix_decay_1x"].append((name, parameter))
        else:
            groups["no_decay_1x"].append((name, parameter))
    named = []
    optimizer_groups = []
    for group_name, learning_rate, weight_decay in (
        ("no_decay_1x", training["learning_rate"], 0.0),
        (
            "w0_no_decay_2x",
            training["learning_rate"] * training["w0_learning_rate_scale"],
            0.0,
        ),
        ("matrix_decay_1x", training["learning_rate"], training["weight_decay"]),
    ):
        items = groups[group_name]
        if not items:
            raise RuntimeError(f"优化器参数组为空：{group_name}")
        optimizer_groups.append(
            {
                "params": [parameter for _, parameter in items],
                "lr": learning_rate,
                "weight_decay": weight_decay,
            }
        )
        named.append(
            {
                "name": group_name,
                "parameter_names": [name for name, _ in items],
                "parameter_count": sum(parameter.numel() for _, parameter in items),
                "learning_rate": learning_rate,
                "weight_decay": weight_decay,
            }
        )
    covered = {name for group in named for name in group["parameter_names"]}
    expected = {name for name, _ in model.named_parameters()}
    if covered != expected:
        raise RuntimeError("优化器参数组未无重无漏覆盖模型参数")
    optimizer = torch.optim.AdamW(optimizer_groups)
    return optimizer, named


def lp_pool(probabilities: torch.Tensor, valid: torch.Tensor, p: torch.Tensor) -> torch.Tensor:
    logs = torch.log(probabilities.clamp(min=1e-7))
    count = valid.sum(1).clamp(min=1.0)
    powered = (p * logs).masked_fill(~valid, -1e30)
    return torch.exp((torch.logsumexp(powered, 1) - torch.log(count)) / p)


def move_optimizer_state(
    optimizer: torch.optim.Optimizer, device: torch.device
) -> None:
    for state in optimizer.state.values():
        for key, value in state.items():
            if torch.is_tensor(value):
                state[key] = value.to(device)


def data_inventory(cache_root: Path, names: Sequence[str]) -> dict[str, Any]:
    files: dict[str, Any] = {}
    for name in names:
        path = cache_root / f"{name}.npy"
        if not path.is_file():
            raise FileNotFoundError(f"缺少冻结缓存：{path}")
        files[name] = {
            "filename": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return {"files": files, "sha256": canonical_sha256(files)}


def load_arrays(cache_root: Path, names: Sequence[str]) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for name in names:
        path = cache_root / f"{name}.npy"
        mmap_mode = None if name in {"s24", "d24"} else "r"
        arrays[name] = np.load(
            path,
            mmap_mode=mmap_mode,
            allow_pickle=name in {"s24", "d24"},
        )
    return arrays


def source_split(
    source: Mapping[str, np.ndarray], config: Mapping[str, Any]
) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    seed = int(config["training"]["seed"])
    entity = source["E23"]
    timestamp = source["T23"]
    unique_entity = np.unique(entity)
    permutation = np.random.RandomState(seed).permutation(len(unique_entity))
    count = max(
        1,
        int(len(unique_entity) * config["training"]["validation_fraction"]),
    )
    validation_entities = set(unique_entity[permutation[:count]].tolist())
    entity_mask = np.fromiter(
        (value in validation_entities for value in entity), bool, len(entity)
    )
    time_cut = np.quantile(
        timestamp, 1.0 - config["training"]["time_tail_fraction"]
    )
    time_mask = timestamp >= time_cut
    train_rows = np.flatnonzero(~(entity_mask | time_mask))
    validation_rows = np.flatnonzero(entity_mask & ~time_mask)
    stats = {
        "entity_count": int(len(unique_entity)),
        "train_sequences": int(len(train_rows)),
        "validation_sequences": int(len(validation_rows)),
        "train_validation_row_intersection": int(
            np.intersect1d(train_rows, validation_rows).size
        ),
    }
    expected = {
        "entity_count": 150_680,
        "train_sequences": 208_598,
        "validation_sequences": 22_444,
        "train_validation_row_intersection": 0,
    }
    if stats != expected:
        raise RuntimeError(f"协议 A 源年切分统计不符：{stats}")
    return train_rows, validation_rows, stats


def gather_sequence_batch(
    arrays: Mapping[str, np.ndarray],
    prefix: str,
    rows: np.ndarray,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, np.ndarray]:
    indices_np = np.asarray(arrays[f"I{prefix}"][rows], dtype=np.int64)
    valid_np = np.asarray(arrays[f"M{prefix}"][rows] > 0.5, dtype=bool)
    values_np = np.asarray(arrays[f"X{prefix}"][indices_np], dtype=np.float32)
    labels_np = np.asarray(arrays[f"y{prefix}"][indices_np], dtype=np.float32)
    return (
        torch.from_numpy(values_np).to(device, non_blocking=True),
        torch.from_numpy(valid_np).to(device, non_blocking=True),
        torch.from_numpy(labels_np).to(device, non_blocking=True),
        indices_np,
    )


def source_loss_weights(
    source: Mapping[str, np.ndarray], train_rows: np.ndarray
) -> tuple[float, float]:
    positive_flows = 0.0
    valid_flows = 0
    positive_sequences = 0
    for start in range(0, len(train_rows), 4096):
        rows = train_rows[start : start + 4096]
        indices = np.asarray(source["I23"][rows], dtype=np.int64)
        valid = np.asarray(source["M23"][rows] > 0.5, dtype=bool)
        labels = np.asarray(source["y23"][indices], dtype=np.float32)
        positive_flows += float(labels[valid].sum())
        valid_flows += int(valid.sum())
        positive_sequences += int(((labels * valid).max(1) > 0).sum())
    negative_flows = valid_flows - positive_flows
    negative_sequences = len(train_rows) - positive_sequences
    if positive_flows <= 0 or positive_sequences <= 0:
        raise RuntimeError("源年训练切分缺少正类")
    return (
        float(negative_flows / positive_flows),
        float(negative_sequences / positive_sequences),
    )


@torch.no_grad()
def predict_source_rows(
    model: RWKV7ProtocolAModel,
    source: Mapping[str, np.ndarray],
    rows: np.ndarray,
    device: torch.device,
    batch_size: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    model.eval()
    predictions: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    entities: list[np.ndarray] = []
    for start in range(0, len(rows), batch_size):
        selected_rows = rows[start : start + batch_size]
        values, valid, targets, _ = gather_sequence_batch(
            source, "23", selected_rows, device
        )
        probabilities = torch.sigmoid(model(values, valid))
        flat_valid = valid.reshape(-1)
        predictions.append(probabilities.reshape(-1)[flat_valid].cpu().numpy())
        labels.append(targets.reshape(-1)[flat_valid].cpu().numpy())
        repeated_entities = np.repeat(
            np.asarray(source["E23"][selected_rows]), valid.shape[1]
        )
        entities.append(repeated_entities[flat_valid.cpu().numpy()])
    model.train()
    return (
        np.concatenate(predictions),
        np.concatenate(labels),
        np.concatenate(entities),
    )


def gradient_receipt(model: nn.Module, require_elp: bool) -> dict[str, Any]:
    entries: dict[str, Any] = {}
    for name, parameter in model.named_parameters():
        gradient = parameter.grad
        entries[name] = {
            "present": gradient is not None,
            "finite": bool(gradient is not None and torch.isfinite(gradient).all()),
            "nonzero": bool(gradient is not None and torch.count_nonzero(gradient) > 0),
            "l2_norm": float(gradient.float().norm().detach().cpu())
            if gradient is not None
            else None,
        }
    groups = {
        "input_adapter": any(
            value["finite"] and value["nonzero"]
            for name, value in entries.items()
            if name.startswith("input_adapter.")
        ),
        "rwkv_time_mix": any(
            value["finite"] and value["nonzero"]
            for name, value in entries.items()
            if ".time_mix." in name
        ),
        "classifier": any(
            value["finite"] and value["nonzero"]
            for name, value in entries.items()
            if name.startswith("output_layer.")
        ),
    }
    for suffix in (
        "receptance.weight",
        "key.weight",
        "value.weight",
        "output.weight",
        "w0",
        "a0",
    ):
        groups[f"rwkv_{suffix.replace('.', '_')}"] = any(
            value["finite"] and value["nonzero"]
            for name, value in entries.items()
            if ".time_mix." in name and name.endswith(suffix)
        )
    if require_elp:
        groups["elp_p_log"] = entries["p_log"]["finite"] and entries["p_log"][
            "nonzero"
        ]
    return {
        "groups": groups,
        "parameters": entries,
        "all_required_groups_pass": all(groups.values()),
    }


class BudgetLimit(RuntimeError):
    def __init__(self, message: str, elapsed_seconds: float) -> None:
        super().__init__(message)
        self.elapsed_seconds = elapsed_seconds


def train_candidate(
    config: Mapping[str, Any],
    task_key: str,
    adapter_key: str,
    capacity_key: str,
    cell: str,
    output_root: Path,
    run_identity: Mapping[str, Any],
    source: Mapping[str, np.ndarray],
    train_rows: np.ndarray,
    validation_rows: np.ndarray,
    loss_weights: tuple[float, float],
    consumed_seconds: float,
    reserve_equivalent_runs: int,
    device: torch.device,
    resume: bool,
) -> dict[str, Any]:
    receipt_path = output_root / "receipts" / f"selection-{task_key}.json"
    inflight_path = output_root / "inflight" / f"{task_key}.pt"
    epoch_root = output_root / "checkpoints" / "epochs" / task_key
    identity = {
        "schema_version": "ch3-rwkv7-protocol-a-task-identity-v1",
        **run_identity,
        "task_key": task_key,
        "adapter_key": adapter_key,
        "capacity_key": capacity_key,
        "cell": cell,
    }
    if receipt_path.is_file():
        receipt = load_json(receipt_path)
        checkpoint_path = output_root / receipt["selection"]["checkpoint"]["filename"]
        valid = (
            checkpoint_path.is_file()
            and
            receipt.get("identity") == identity
            and receipt.get("selection", {}).get("checkpoint", {}).get("sha256")
            == sha256_file(checkpoint_path)
        )
        if not resume or not valid:
            raise RuntimeError(f"{task_key} 已有检查点但不可合法复用")
        return receipt["selection"]
    if not resume and (
        receipt_path.exists() or inflight_path.exists() or epoch_root.exists()
    ):
        raise RuntimeError(f"全新运行存在 {task_key} 历史制品")

    training = config["training"]
    seed = int(training["seed"])
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    model = build_model(config, adapter_key, capacity_key, cell).to(device)
    optimizer, optimizer_groups = make_optimizer(config, model)
    generator = torch.Generator().manual_seed(seed)
    history: list[dict[str, Any]] = []
    best_ap = -1.0
    best_epoch = 0
    best_p = float("nan")
    best_state: dict[str, torch.Tensor] | None = None
    gradient_gate: dict[str, Any] | None = None
    elapsed_before = 0.0
    start_epoch = 1
    start_step = 1
    partial_running_loss = 0.0
    partial_epoch_seconds = 0.0
    processed_valid_flows = 0
    if resume and inflight_path.is_file():
        inflight = torch.load(inflight_path, map_location="cpu", weights_only=False)
        if inflight.get("identity") != identity or not inflight.get("complete_step"):
            raise RuntimeError(f"{task_key} 在途检查点不是最新完整优化步")
        model.load_state_dict(inflight["model"])
        optimizer.load_state_dict(inflight["optimizer"])
        move_optimizer_state(optimizer, device)
        history = inflight["history"]
        best_ap = float(inflight["best_ap"])
        best_epoch = int(inflight["best_epoch"])
        best_p = float(inflight["best_p"])
        best_state = inflight["best_state"]
        gradient_gate = inflight["gradient_gate"]
        elapsed_before = float(inflight["elapsed_seconds"])
        generator.set_state(inflight["generator_state"])
        torch.set_rng_state(inflight["torch_rng_state"])
        torch.cuda.set_rng_state_all(inflight["cuda_rng_state_all"])
        np.random.set_state(inflight["numpy_rng_state"])
        random.setstate(inflight["python_rng_state"])
        processed_valid_flows = int(inflight["processed_valid_flows"])
        if inflight.get("complete_epoch"):
            start_epoch = int(inflight["epoch"]) + 1
        else:
            start_epoch = int(inflight["epoch"])
            start_step = int(inflight["step"]) + 1
            partial_running_loss = float(inflight["partial_running_loss"])
            partial_epoch_seconds = float(inflight["partial_epoch_seconds"])

    flow_positive_weight, sequence_positive_weight = loss_weights
    flow_loss = nn.BCEWithLogitsLoss(
        reduction="none",
        pos_weight=torch.tensor(flow_positive_weight, device=device),
    )
    sequence_loss = nn.BCELoss(reduction="none")
    uses_lp = bool(config["cells"][cell]["learned_lp_pooling"])
    torch.cuda.reset_peak_memory_stats(device)
    started = time.time()
    epoch_started = started
    for epoch in range(start_epoch, int(training["epochs"]) + 1):
        running_loss = partial_running_loss if epoch == start_epoch else 0.0
        step_first = start_step if epoch == start_epoch else 1
        model.train()
        for step in range(step_first, int(training["steps_per_epoch"]) + 1):
            positions = torch.randint(
                0, len(train_rows), (int(training["batch_size"]),), generator=generator
            ).numpy()
            rows = train_rows[positions]
            values, valid, labels, _ = gather_sequence_batch(
                source, "23", rows, device
            )
            logits = model(values, valid)
            mask = valid.to(logits.dtype)
            loss = (flow_loss(logits, labels) * mask).sum() / mask.sum().clamp(min=1.0)
            entity_component: torch.Tensor | None = None
            if uses_lp:
                pooled = lp_pool(torch.sigmoid(logits), valid, model.p).clamp(
                    1e-6, 1 - 1e-6
                )
                sequence_labels = (labels * mask).amax(-1)
                weights = 1.0 + (sequence_positive_weight - 1.0) * sequence_labels
                entity_component = float(training["auxiliary_loss_weight"]) * (
                    (sequence_loss(pooled, sequence_labels) * weights).sum()
                    / weights.sum()
                )
                loss = loss + entity_component
            optimizer.zero_grad(set_to_none=True)
            if cell == "C11" and gradient_gate is None:
                if entity_component is None:
                    raise RuntimeError("C11 缺少 ELP 实体辅助损失")
                entity_component.backward(retain_graph=True)
                current_gradient = gradient_receipt(model, require_elp=True)
                if epoch == 1 and step == 1:
                    atomic_json(
                        output_root
                        / "receipts"
                        / f"gradient-first-step-entity-only-{task_key}.json",
                        {
                            "identity": identity,
                            "loss_scope": "ELP_entity_auxiliary_only",
                            "official_zero_output_initialization_may_delay_upstream_reachability": True,
                            **current_gradient,
                        },
                    )
                if current_gradient["all_required_groups_pass"]:
                    gradient_gate = {
                        "first_reachable_step": step,
                        "loss_scope": "ELP_entity_auxiliary_only",
                        **current_gradient,
                    }
                    atomic_json(
                        output_root / "receipts" / f"gradient-{task_key}.json",
                        {"identity": identity, **gradient_gate},
                    )
                elif step >= 3:
                    raise RuntimeError(
                        f"{task_key} 三步内实体损失梯度门未通过："
                        f"{current_gradient['groups']}"
                    )
                optimizer.zero_grad(set_to_none=True)
            loss.backward()
            if gradient_gate is None and cell != "C11":
                current_gradient = gradient_receipt(model, require_elp=False)
                if epoch == 1 and step == 1:
                    atomic_json(
                        output_root / "receipts" / f"gradient-first-step-{task_key}.json",
                        {
                            "identity": identity,
                            "official_zero_output_initialization_may_delay_upstream_reachability": True,
                            **current_gradient,
                        },
                    )
                if current_gradient["all_required_groups_pass"]:
                    gradient_gate = {"first_reachable_step": step, **current_gradient}
                    atomic_json(
                        output_root / "receipts" / f"gradient-{task_key}.json",
                        {"identity": identity, **gradient_gate},
                    )
                elif step >= 3:
                    raise RuntimeError(
                        f"{task_key} 三步内端到端梯度门未通过："
                        f"{current_gradient['groups']}"
                    )
            gradient_norm = float(
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(), float(training["gradient_clip_norm"])
                )
            )
            if not math.isfinite(gradient_norm):
                raise RuntimeError(f"{task_key} 出现非有限梯度")
            optimizer.step()
            running_loss += float(loss.detach())
            processed_valid_flows += int(mask.sum().detach())
            if step % 20 == 0 and step < int(training["steps_per_epoch"]):
                elapsed = elapsed_before + time.time() - started
                atomic_torch(
                    inflight_path,
                    {
                        "schema_version": "ch3-rwkv7-complete-inflight-v1",
                        "identity": identity,
                        "epoch": epoch,
                        "step": step,
                        "complete_step": True,
                        "complete_epoch": False,
                        "completed": False,
                        "model": {
                            name: tensor.detach().cpu().clone()
                            for name, tensor in model.state_dict().items()
                        },
                        "optimizer": optimizer.state_dict(),
                        "scheduler_state": {"name": "none", "state": None},
                        "history": history,
                        "best_ap": best_ap,
                        "best_epoch": best_epoch,
                        "best_p": best_p,
                        "best_state": best_state,
                        "best_epoch_weight_sha256": sha256_file(
                            epoch_root / f"epoch-{best_epoch:02d}.pt"
                        )
                        if best_epoch
                        else None,
                        "current_p": float(model.p.detach()),
                        "gradient_gate": gradient_gate,
                        "elapsed_seconds": elapsed,
                        "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(
                            device
                        )
                        / 2**20,
                        "peak_process_rss_mib": process_peak_rss_mib(),
                        "partial_running_loss": running_loss,
                        "partial_epoch_seconds": partial_epoch_seconds
                        + time.time()
                        - epoch_started,
                        "processed_valid_flows": processed_valid_flows,
                        "generator_state": generator.get_state(),
                        "torch_rng_state": torch.get_rng_state(),
                        "cuda_rng_state_all": torch.cuda.get_rng_state_all(),
                        "numpy_rng_state": np.random.get_state(),
                        "python_rng_state": random.getstate(),
                    },
                )
            if step % 250 == 0:
                elapsed = elapsed_before + time.time() - started
                log(
                    f"{task_key} epoch={epoch}/{training['epochs']} "
                    f"step={step}/{training['steps_per_epoch']} 累计={elapsed / 60:.1f}分"
                )
        predictions, labels_np, _ = predict_source_rows(
            model,
            source,
            validation_rows,
            device,
            int(config["evaluation"]["sequence_batch_size"]),
        )
        validation_ap = float(average_precision_score(labels_np, predictions))
        p_value = float(model.p.detach())
        epoch_seconds = partial_epoch_seconds + time.time() - epoch_started
        epoch_started = time.time()
        partial_epoch_seconds = 0.0
        history.append(
            {
                "epoch": epoch,
                "validation_flow_ap": validation_ap,
                "p": p_value,
                "mean_training_loss": running_loss / int(training["steps_per_epoch"]),
                "epoch_seconds": epoch_seconds,
            }
        )
        current_state = {
            name: tensor.detach().cpu().clone()
            for name, tensor in model.state_dict().items()
        }
        if validation_ap > best_ap:
            best_ap = validation_ap
            best_epoch = epoch
            best_p = p_value
            best_state = current_state
        epoch_path = epoch_root / f"epoch-{epoch:02d}.pt"
        atomic_torch(
            epoch_path,
            {
                "schema_version": "ch3-rwkv7-model-epoch-v1",
                "identity": identity,
                "epoch": epoch,
                "model": current_state,
            },
        )
        elapsed = elapsed_before + time.time() - started
        atomic_torch(
            inflight_path,
            {
                "schema_version": "ch3-rwkv7-complete-inflight-v1",
                "identity": identity,
                "epoch": epoch,
                "step": int(training["steps_per_epoch"]),
                "complete_step": True,
                "complete_epoch": True,
                "completed": epoch == int(training["epochs"]),
                "model": current_state,
                "optimizer": optimizer.state_dict(),
                "scheduler_state": {"name": "none", "state": None},
                "history": history,
                "best_ap": best_ap,
                "best_epoch": best_epoch,
                "best_p": best_p,
                "best_state": best_state,
                "best_epoch_weight_sha256": sha256_file(
                    epoch_root / f"epoch-{best_epoch:02d}.pt"
                ),
                "current_p": float(model.p.detach()),
                "gradient_gate": gradient_gate,
                "elapsed_seconds": elapsed,
                "processed_valid_flows": processed_valid_flows,
                "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(device)
                / 2**20,
                "peak_process_rss_mib": process_peak_rss_mib(),
                "generator_state": generator.get_state(),
                "torch_rng_state": torch.get_rng_state(),
                "cuda_rng_state_all": torch.cuda.get_rng_state_all(),
                "numpy_rng_state": np.random.get_state(),
                "python_rng_state": random.getstate(),
            },
        )
        estimated_run_seconds = elapsed * int(training["epochs"]) / epoch
        projected = consumed_seconds + estimated_run_seconds * (
            1 + reserve_equivalent_runs
        )
        if projected > float(training["maximum_gpu_hours"]) * 3600:
            raise BudgetLimit(
                f"{task_key} 含后续{reserve_equivalent_runs}个等价单元的投影累计"
                f" {projected / 3600:.3f} GPU小时，"
                f"超过 {training['maximum_gpu_hours']} GPU小时停止门",
                elapsed,
            )
        log(f"{task_key} epoch={epoch} 验证逐流AP={validation_ap:.8f}")
    if best_state is None or gradient_gate is None:
        raise RuntimeError(f"{task_key} 未产生可选检查点")
    training_seconds = elapsed_before + time.time() - started
    checkpoint_path = epoch_root / f"epoch-{best_epoch:02d}.pt"
    model.load_state_dict(best_state)
    validation_scores, validation_labels, validation_entities = predict_source_rows(
        model,
        source,
        validation_rows,
        device,
        int(config["evaluation"]["sequence_batch_size"]),
    )
    _, validation_flow_entity = np.unique(validation_entities, return_inverse=True)
    validation_entity_labels = np.zeros(
        int(validation_flow_entity.max()) + 1, dtype=np.float32
    )
    np.maximum.at(
        validation_entity_labels, validation_flow_entity, validation_labels
    )
    validation_seen = np.ones(len(validation_scores), dtype=bool)
    main_p = best_p if uses_lp else None
    validation_entity_scores = entity_scores(
        validation_scores,
        validation_seen,
        validation_flow_entity,
        len(validation_entity_labels),
        main_p,
    )
    validation_maximum_scores = entity_scores(
        validation_scores,
        validation_seen,
        validation_flow_entity,
        len(validation_entity_labels),
        None,
    )
    validation_metrics = {
        "flow_average_precision": float(
            average_precision_score(validation_labels, validation_scores)
        ),
        "flow_roc_auc": float(roc_auc_score(validation_labels, validation_scores)),
        "entity_average_precision": float(
            average_precision_score(
                validation_entity_labels, validation_entity_scores
            )
        ),
        "maximum_entity_average_precision": float(
            average_precision_score(
                validation_entity_labels, validation_maximum_scores
            )
        ),
        "dr_at_fpr": {
            f"fpr_{value:g}": dr_at_fpr(
                validation_entity_scores, validation_entity_labels, value
            )
            for value in DR_FPR_GRID
        },
        "maximum_dr_at_fpr": {
            f"fpr_{value:g}": dr_at_fpr(
                validation_maximum_scores, validation_entity_labels, value
            )
            for value in DR_FPR_GRID
        },
        "flow_count": len(validation_scores),
        "entity_count": len(validation_entity_labels),
    }
    if abs(validation_metrics["flow_average_precision"] - best_ap) > 1e-12:
        raise RuntimeError("选中轮复算逐流 AP 与选择历史不一致")
    source_curve = complete_budget_curve(
        validation_entity_scores, validation_entity_labels
    )
    source_curve_path = output_root / "receipts" / f"source-budget-{task_key}.npz"
    temporary_curve = source_curve_path.with_name(
        f"{source_curve_path.name}.partial.{os.getpid()}"
    )
    source_curve_path.parent.mkdir(parents=True, exist_ok=True)
    with temporary_curve.open("wb") as handle:
        np.savez_compressed(handle, **source_curve)
    os.replace(temporary_curve, source_curve_path)
    selection = {
        "task_key": task_key,
        "adapter_key": adapter_key,
        "capacity_key": capacity_key,
        "cell": cell,
        "selected_epoch": best_epoch,
        "validation_flow_ap": best_ap,
        "p_at_selection": best_p,
        "history": history,
        "training_seconds": training_seconds,
        "processed_valid_flows": processed_valid_flows,
        "effective_training_flow_throughput_per_second": processed_valid_flows
        / training_seconds,
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "optimizer_groups": optimizer_groups,
        "gradient_gate": gradient_gate,
        "selected_validation_metrics": validation_metrics,
        "selected_validation_complete_budget_curve": {
            "filename": str(source_curve_path.relative_to(output_root)),
            "bytes": source_curve_path.stat().st_size,
            "sha256": sha256_file(source_curve_path),
        },
        "epoch_model_weight_count": len(history),
        "epoch_model_weight_bytes": sum(
            (epoch_root / f"epoch-{number:02d}.pt").stat().st_size
            for number in range(1, int(training["epochs"]) + 1)
        ),
        "latest_complete_inflight": str(inflight_path.relative_to(output_root)),
        "checkpoint": {
            "filename": str(checkpoint_path.relative_to(output_root)),
            "bytes": checkpoint_path.stat().st_size,
            "sha256": sha256_file(checkpoint_path),
        },
        "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
        "peak_gpu_reserved_mib": torch.cuda.max_memory_reserved(device) / 2**20,
        "peak_process_rss_mib": process_peak_rss_mib(),
        "nonfinite_gradient_or_loss_count": 0,
    }
    atomic_json(receipt_path, {"identity": identity, "selection": selection})
    del model, optimizer
    torch.cuda.empty_cache()
    return selection


def entity_scores(
    flow_scores: np.ndarray,
    seen: np.ndarray,
    flow_entity: np.ndarray,
    entity_count: int,
    p_value: float | None,
) -> np.ndarray:
    usable = seen & (flow_entity >= 0)
    if p_value is None:
        scores = np.full(entity_count, -np.inf, dtype=np.float32)
        np.maximum.at(scores, flow_entity[usable], flow_scores[usable])
        return scores
    numerator = np.zeros(entity_count, dtype=np.float64)
    count = np.zeros(entity_count, dtype=np.float64)
    np.add.at(
        numerator,
        flow_entity[usable],
        np.clip(flow_scores[usable], 1e-7, 1.0).astype(np.float64) ** p_value,
    )
    np.add.at(count, flow_entity[usable], 1.0)
    return np.where(
        count > 0,
        (numerator / np.maximum(count, 1.0)) ** (1.0 / p_value),
        -np.inf,
    ).astype(np.float32)


def dr_at_fpr(scores: np.ndarray, labels: np.ndarray, target_fpr: float) -> float:
    valid = np.isfinite(scores)
    values = scores[valid]
    target = labels[valid]
    negative = np.sort(values[target == 0])[::-1]
    positive = values[target == 1]
    if len(negative) == 0 or len(positive) == 0:
        raise RuntimeError("检测率计算缺少正类或负类实体")
    threshold = negative[min(int(len(negative) * target_fpr), len(negative) - 1)]
    return float((positive >= threshold).mean())


def complete_budget_curve(
    scores: np.ndarray, labels: np.ndarray
) -> dict[str, np.ndarray]:
    valid = np.isfinite(scores)
    values = scores[valid]
    target = labels[valid]
    positive = np.sort(values[target == 1])
    negative = np.sort(values[target == 0])[::-1]
    detection_rate = (
        len(positive) - np.searchsorted(positive, negative, side="left")
    ) / len(positive)
    false_positive = len(negative) - np.searchsorted(
        negative[::-1], negative, side="left"
    )
    return {
        "n_false_positive_entity": false_positive.astype(np.int64),
        "nominal_fpr": np.arange(len(negative), dtype=np.float64) / len(negative),
        "realized_fpr": false_positive.astype(np.float64) / len(negative),
        "detection_rate": detection_rate.astype(np.float64),
    }


def build_target_entity_map(
    target: Mapping[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    flow_entity = np.full(len(target["y24"]), -1, dtype=np.int32)
    representative_ids = np.empty(len(target["I24"]), dtype=np.int64)
    for start in range(0, len(target["I24"]), 4096):
        indices = np.asarray(target["I24"][start : start + 4096], dtype=np.int64)
        valid = np.asarray(target["M24"][start : start + 4096] > 0.5, dtype=bool)
        if np.any(~valid.any(1)):
            raise RuntimeError("目标序列存在零个有效流")
        local_rows = np.arange(len(indices))
        representative_ids[start : start + len(indices)] = indices[
            local_rows, valid.argmax(1)
        ]
    left = np.asarray(target["s24"][representative_ids], dtype=str)
    right = np.asarray(target["d24"][representative_ids], dtype=str)
    canonical_left = np.where(left <= right, left, right)
    canonical_right = np.where(left <= right, right, left)
    entity_keys = np.char.add(np.char.add(canonical_left, "\x1f"), canonical_right)
    _, sequence_entity = np.unique(entity_keys, return_inverse=True)
    sequence_entity = sequence_entity.astype(np.int32, copy=False)
    entity_count = int(sequence_entity.max()) + 1
    labels = np.zeros(entity_count, dtype=np.float32)
    for start in range(0, len(target["I24"]), 4096):
        indices = np.asarray(target["I24"][start : start + 4096], dtype=np.int64)
        valid = np.asarray(target["M24"][start : start + 4096] > 0.5, dtype=bool)
        entity_matrix = np.broadcast_to(
            sequence_entity[start : start + len(indices), None], indices.shape
        )
        valid_ids = indices[valid]
        valid_entities = entity_matrix[valid]
        existing = flow_entity[valid_ids]
        if np.any((existing >= 0) & (existing != valid_entities)):
            raise RuntimeError("同一目标流被映射到冲突实体")
        flow_entity[valid_ids] = valid_entities
        np.maximum.at(labels, valid_entities, target["y24"][valid_ids])
    stats = {
        "entity_count": entity_count,
        "positive_entity_count": int(labels.sum()),
        "unmapped_flow_count": int((flow_entity < 0).sum()),
    }
    if stats["entity_count"] != 47_115 or stats["positive_entity_count"] != 752:
        raise RuntimeError(f"LSPR24 实体合同不符：{stats}")
    return flow_entity, labels, stats


@torch.no_grad()
def score_target(
    config: Mapping[str, Any],
    model: RWKV7ProtocolAModel,
    target: Mapping[str, np.ndarray],
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    scores = np.zeros(len(target["y24"]), dtype=np.float32)
    seen = np.zeros(len(target["y24"]), dtype=bool)
    batch_size = int(config["evaluation"]["sequence_batch_size"])
    model.eval()
    for start in range(0, len(target["I24"]), batch_size):
        rows = np.arange(start, min(start + batch_size, len(target["I24"])))
        values, valid, _, indices = gather_sequence_batch(
            target, "24", rows, device
        )
        probabilities = torch.sigmoid(model(values, valid)).cpu().numpy()
        valid_np = valid.cpu().numpy()
        scores[indices[valid_np]] = probabilities[valid_np]
        seen[indices[valid_np]] = True
    return scores, seen


def save_target_evaluation(
    output_root: Path,
    cell: str,
    identity: Mapping[str, Any],
    cell_result: Mapping[str, Any],
    curve: Mapping[str, np.ndarray],
) -> None:
    receipt_root = output_root / "receipts" / f"target-evaluation-{cell}"
    if receipt_root.exists():
        raise RuntimeError(f"{cell} 目标评价完成目录已存在，拒绝覆盖")
    temporary_root = receipt_root.with_name(
        f"{receipt_root.name}.partial.{os.getpid()}"
    )
    temporary_root.mkdir(parents=True, exist_ok=False)
    curve_path = temporary_root / "complete-alert-budget-curve.npz"
    with curve_path.open("wb") as handle:
        np.savez_compressed(handle, **curve)
    atomic_json(
        temporary_root / "receipt.json",
        {
            "schema_version": "ch3-rwkv7-target-cell-receipt-v1",
            "identity": identity,
            "cell_result": cell_result,
            "curve": {
                "filename": curve_path.name,
                "bytes": curve_path.stat().st_size,
                "sha256": sha256_file(curve_path),
                "fields": list(curve),
            },
            "complete": True,
        },
    )
    os.replace(temporary_root, receipt_root)


def load_target_evaluation(
    output_root: Path, cell: str, identity: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, np.ndarray]] | None:
    receipt_root = output_root / "receipts" / f"target-evaluation-{cell}"
    if not receipt_root.exists():
        return None
    receipt = load_json(receipt_root / "receipt.json")
    curve_path = receipt_root / receipt["curve"]["filename"]
    if (
        receipt.get("identity") != identity
        or not receipt.get("complete")
        or sha256_file(curve_path) != receipt["curve"]["sha256"]
    ):
        raise RuntimeError(f"{cell} 目标评价完成收据身份或摘要不符")
    with np.load(curve_path) as payload:
        curve = {name: payload[name] for name in payload.files}
    return receipt["cell_result"], curve


def choose_candidate(
    selections: Mapping[str, Mapping[str, Any]], order: Sequence[str]
) -> str:
    return max(
        order,
        key=lambda key: (
            float(selections[key]["validation_flow_ap"]),
            -int(selections[key]["parameter_count"]),
            -order.index(key),
        ),
    )


def build_manifest(output_root: Path) -> None:
    files: dict[str, Any] = {}
    for path in sorted(output_root.rglob("*")):
        if path.is_file() and ".partial." not in path.name:
            relative = str(path.relative_to(output_root))
            files[relative] = {
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
    atomic_json(
        output_root / "manifest.json",
        {
            "schema_version": "ch3-rwkv7-field-aware-manifest-v1",
            "run_id": RUN_ID,
            "files": files,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
        },
    )


def evaluate_target(
    config: Mapping[str, Any],
    output_root: Path,
    run_identity: Mapping[str, Any],
    selections: Mapping[str, Mapping[str, Any]],
    adapter_key: str,
    capacity_key: str,
    source_training_seconds: float,
    target_inventory: Mapping[str, Any],
    target: Mapping[str, np.ndarray],
) -> tuple[dict[str, Any], dict[str, np.ndarray], dict[str, int]]:
    flow_entity, entity_labels, entity_stats = build_target_entity_map(target)
    device = torch.device("cuda")
    cells: dict[str, Any] = {}
    curves: dict[str, np.ndarray] = {}
    calls = 0
    reused = 0
    target_consumed_seconds = 0.0
    for cell in CELL_ORDER:
        selection = selections[cell]
        checkpoint_path = output_root / selection["checkpoint"]["filename"]
        if sha256_file(checkpoint_path) != selection["checkpoint"]["sha256"]:
            raise RuntimeError(f"{cell} 选择检查点摘要不符")
        identity = {
            **run_identity,
            "target_data_inventory_sha256": target_inventory["sha256"],
            "cell": cell,
            "checkpoint_sha256": selection["checkpoint"]["sha256"],
        }
        restored = load_target_evaluation(output_root, cell, identity)
        if restored is not None:
            cell_result, curve = restored
            cells[cell] = cell_result
            for name, values in curve.items():
                curves[f"{cell}__{name}"] = values
            reused += 1
            target_consumed_seconds += float(
                cell_result["target"]["evaluation_seconds"]
            )
            completed = len(cells)
            projected = source_training_seconds + (
                target_consumed_seconds / completed * len(CELL_ORDER)
            )
            if projected > float(config["training"]["maximum_gpu_hours"]) * 3600:
                raise BudgetLimit(
                    f"目标评价按已完成{completed}格投影累计"
                    f" {projected / 3600:.3f} GPU小时，超过"
                    f" {config['training']['maximum_gpu_hours']} GPU小时停止门",
                    target_consumed_seconds,
                )
            continue
        model = build_model(config, adapter_key, capacity_key, cell).to(device)
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        model.load_state_dict(checkpoint["model"])
        selected_p = float(model.p.detach())
        if abs(selected_p - float(selection["p_at_selection"])) > 1e-9:
            raise RuntimeError(f"{cell} 回载 p 与源年选择封印不符")
        torch.cuda.reset_peak_memory_stats(device)
        started = time.time()
        flow_scores, seen = score_target(config, model, target, device)
        elapsed = time.time() - started
        calls += 1
        main_p = selected_p if config["cells"][cell]["learned_lp_pooling"] else None
        main_scores = entity_scores(
            flow_scores, seen, flow_entity, len(entity_labels), main_p
        )
        maximum_scores = entity_scores(
            flow_scores, seen, flow_entity, len(entity_labels), None
        )
        valid_entity = np.isfinite(main_scores)
        valid_maximum = np.isfinite(maximum_scores)
        metrics = {
            "flow_average_precision": float(
                average_precision_score(target["y24"][seen], flow_scores[seen])
            ),
            "flow_roc_auc": float(
                roc_auc_score(target["y24"][seen], flow_scores[seen])
            ),
            "entity_average_precision": float(
                average_precision_score(
                    entity_labels[valid_entity], main_scores[valid_entity]
                )
            ),
            "maximum_entity_average_precision": float(
                average_precision_score(
                    entity_labels[valid_maximum], maximum_scores[valid_maximum]
                )
            ),
            "dr_at_fpr": {
                f"fpr_{value:g}": dr_at_fpr(main_scores, entity_labels, value)
                for value in DR_FPR_GRID
            },
            "maximum_dr_at_fpr": {
                f"fpr_{value:g}": dr_at_fpr(maximum_scores, entity_labels, value)
                for value in DR_FPR_GRID
            },
            "flows_scored": int(seen.sum()),
            "entities_scored": int(valid_entity.sum()),
            "evaluation_seconds": elapsed,
            "effective_flow_throughput_per_second": int(seen.sum()) / elapsed,
            "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
            "peak_gpu_reserved_mib": torch.cuda.max_memory_reserved(device) / 2**20,
            "target_evaluation_call": CELL_ORDER.index(cell) + 1,
        }
        curve = complete_budget_curve(main_scores, entity_labels)
        cell_result = {
            "mechanisms": config["cells"][cell],
            "selection": selection,
            "selected_p": selected_p,
            "target": metrics,
        }
        save_target_evaluation(output_root, cell, identity, cell_result, curve)
        cells[cell] = cell_result
        target_consumed_seconds += elapsed
        for name, values in curve.items():
            curves[f"{cell}__{name}"] = values
        del model, checkpoint, flow_scores, seen, main_scores, maximum_scores
        torch.cuda.empty_cache()
        completed = len(cells)
        projected = source_training_seconds + (
            target_consumed_seconds / completed * len(CELL_ORDER)
        )
        if projected > float(config["training"]["maximum_gpu_hours"]) * 3600:
            raise BudgetLimit(
                f"目标评价按已完成{completed}格投影累计 {projected / 3600:.3f} GPU小时，"
                f"超过 {config['training']['maximum_gpu_hours']} GPU小时停止门",
                target_consumed_seconds,
            )
    if calls + reused != 4:
        raise RuntimeError("目标四格评价次数不符")
    return cells, curves, {"calls_this_process": calls, "receipts_reused": reused, **entity_stats}


def run_experiment(
    config: Mapping[str, Any], args: argparse.Namespace, config_path: Path
) -> None:
    global average_precision_score, roc_auc_score
    from sklearn.metrics import average_precision_score as sklearn_average_precision_score
    from sklearn.metrics import roc_auc_score as sklearn_roc_auc_score

    average_precision_score = sklearn_average_precision_score
    roc_auc_score = sklearn_roc_auc_score
    if not torch.cuda.is_available():
        raise RuntimeError("协议 A 正式运行要求可用 CUDA")
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    config_sha = sha256_file(config_path)
    code_sha = sha256_file(Path(__file__).resolve())
    cache_root = Path(config["paths"]["cache_root"])
    source_inventory = data_inventory(cache_root, SOURCE_ARRAYS)
    run_identity = {
        "run_id": RUN_ID,
        "config_sha256": config_sha,
        "code_sha256": code_sha,
        "source_data_inventory_sha256": source_inventory["sha256"],
    }
    frozen_config_path = output_root / "config.json"
    if frozen_config_path.is_file():
        if not args.resume or load_json(frozen_config_path) != config:
            raise RuntimeError("输出根已有不兼容冻结配置")
    else:
        atomic_json(frozen_config_path, config)
    selection_path = output_root / "selection_frozen.json"
    if selection_path.is_file():
        if not args.resume:
            raise RuntimeError("全新运行已存在选择封印")
        seal = load_json(selection_path)
        if seal.get("identity") != run_identity or not seal.get("all_selections_sealed"):
            raise RuntimeError("选择封印身份不符")
        adapter_key = seal["selected_adapter"]
        capacity_key = seal["selected_capacity"]
        selections = seal["cells"]
        split_stats = seal["source_split"]
        capacity_upper_bound_verified = seal["capacity_upper_bound_verified"]
        source_training_seconds = float(seal["source_training_seconds"])
    else:
        write_status(
            output_root,
            "running",
            "source-input-selection",
            None,
            "目标数组读取计数为零；先在 LSPR23 C00 选择输入适配器",
        )
        source = load_arrays(cache_root, SOURCE_ARRAYS)
        if source["X23"].shape != (16_353_511, 83) or source["I23"].shape != (
            271_815,
            128,
        ):
            raise RuntimeError("LSPR23 冻结缓存形状不符")
        train_rows, validation_rows, split_stats = source_split(source, config)
        weights = source_loss_weights(source, train_rows)
        device = torch.device("cuda")
        consumed = 0.0
        adapter_selections: dict[str, Any] = {}
        for adapter_index, current_adapter in enumerate(ADAPTER_ORDER):
            task_key = f"adapter-{current_adapter}-K0-C00"
            adapter_selections[current_adapter] = train_candidate(
                config,
                task_key,
                current_adapter,
                "K0",
                "C00",
                output_root,
                run_identity,
                source,
                train_rows,
                validation_rows,
                weights,
                consumed,
                len(ADAPTER_ORDER) - adapter_index - 1 + 3,
                device,
                args.resume,
            )
            consumed += float(adapter_selections[current_adapter]["training_seconds"])
        adapter_key = choose_candidate(adapter_selections, ADAPTER_ORDER)
        atomic_json(
            output_root / "adapter_selection_frozen.json",
            {
                "schema_version": "ch3-rwkv7-adapter-selection-v1",
                "identity": run_identity,
                "selection_metric": "LSPR23_C00_validation_flow_average_precision",
                "tie_break": "fewer_parameters_then_frozen_order",
                "selected_adapter": adapter_key,
                "candidates": adapter_selections,
                "target_arrays_loaded": 0,
            },
        )

        write_status(
            output_root,
            "running",
            "source-capacity-selection",
            None,
            f"输入适配器 {adapter_key} 已封印；顺序筛选 K0/K1/K2",
        )
        capacity_selections: dict[str, Any] = {
            "K0": adapter_selections[adapter_key]
        }
        capacity_blocks: list[dict[str, Any]] = []
        for current_capacity in ("K1", "K2"):
            task_key = f"capacity-{current_capacity}-{adapter_key}-C00"
            try:
                selection = train_candidate(
                    config,
                    task_key,
                    adapter_key,
                    current_capacity,
                    "C00",
                    output_root,
                    run_identity,
                    source,
                    train_rows,
                    validation_rows,
                    weights,
                    consumed,
                    3,
                    device,
                    args.resume,
                )
            except BudgetLimit as error:
                consumed += error.elapsed_seconds
                capacity_blocks.append(
                    {
                        "capacity_key": current_capacity,
                        "reason": str(error),
                        "capacity_upper_bound_not_verified_due_to_resource_cap": True,
                    }
                )
                log(str(error))
                torch.cuda.empty_cache()
                break
            capacity_selections[current_capacity] = selection
            consumed += float(selection["training_seconds"])
        maximum_seconds = float(config["training"]["maximum_gpu_hours"]) * 3600
        eligible_capacity_keys = tuple(
            key
            for key in CAPACITY_ORDER
            if key in capacity_selections
            and consumed
            + 3 * float(capacity_selections[key]["training_seconds"])
            <= maximum_seconds
        )
        if not eligible_capacity_keys:
            raise BudgetLimit(
                "容量筛选后没有候选能在剩余预算内完成协议A三格",
                consumed,
            )
        capacity_key = choose_candidate(
            capacity_selections,
            eligible_capacity_keys,
        )
        capacity_upper_bound_verified = set(capacity_selections) == set(CAPACITY_ORDER)
        atomic_json(
            output_root / "capacity_selection_frozen.json",
            {
                "schema_version": "ch3-rwkv7-capacity-selection-v1",
                "identity": run_identity,
                "selected_adapter": adapter_key,
                "selection_metric": "LSPR23_C00_validation_flow_average_precision",
                "tie_break": "fewer_parameters_then_frozen_order",
                "selected_capacity": capacity_key,
                "candidates": capacity_selections,
                "resource_blocks": capacity_blocks,
                "resource_eligible_capacity_keys": list(eligible_capacity_keys),
                "capacity_upper_bound_verified": capacity_upper_bound_verified,
                "rwkv_family_failure_claim_allowed": False,
                "target_arrays_loaded": 0,
            },
        )

        write_status(
            output_root,
            "running",
            "source-four-cell-selection",
            None,
            f"源年胜出 {capacity_key}/{adapter_key}；训练协议 A 剩余三格",
        )
        selections = {"C00": capacity_selections[capacity_key]}
        for cell_index, cell in enumerate(CELL_ORDER[1:]):
            task_key = f"protocol-{cell}-{capacity_key}-{adapter_key}"
            selections[cell] = train_candidate(
                config,
                task_key,
                adapter_key,
                capacity_key,
                cell,
                output_root,
                run_identity,
                source,
                train_rows,
                validation_rows,
                weights,
                consumed,
                len(CELL_ORDER[1:]) - cell_index - 1,
                device,
                args.resume,
            )
            consumed += float(selections[cell]["training_seconds"])
        source_training_seconds = consumed
        seal = {
            "schema_version": "ch3-rwkv7-all-source-selections-frozen-v1",
            "identity": run_identity,
            "source_data_inventory": source_inventory,
            "source_split": split_stats,
            "adapter_candidates": adapter_selections,
            "selected_adapter": adapter_key,
            "capacity_candidates": capacity_selections,
            "selected_capacity": capacity_key,
            "capacity_resource_blocks": capacity_blocks,
            "capacity_upper_bound_verified": capacity_upper_bound_verified,
            "cells": selections,
            "all_selections_sealed": True,
            "target_arrays_loaded_before_seal": 0,
            "source_training_seconds": source_training_seconds,
            "sealed_at_unix": time.time(),
        }
        atomic_json(selection_path, seal)
        del source, train_rows, validation_rows
        torch.cuda.empty_cache()
    if not load_json(selection_path).get("all_selections_sealed"):
        raise RuntimeError("源年选择未全部封印，禁止加载 LSPR24")

    write_status(
        output_root,
        "running",
        "target-evaluation",
        None,
        "选择封印后首次加载 LSPR24，每格只作一次描述性评价",
    )
    target_inventory = data_inventory(cache_root, TARGET_ARRAYS)
    target = load_arrays(cache_root, TARGET_ARRAYS)
    if target["X24"].shape != (20_227_356, 83):
        raise RuntimeError("LSPR24 冻结缓存形状不符")
    target_started = time.time()
    cells, curves, evaluation_counts = evaluate_target(
        config,
        output_root,
        run_identity,
        selections,
        adapter_key,
        capacity_key,
        source_training_seconds,
        target_inventory,
        target,
    )
    curve_path = output_root / "complete-alert-budget-curves.npz"
    temporary_curve = curve_path.with_name(
        f"{curve_path.name}.partial.{os.getpid()}"
    )
    with temporary_curve.open("wb") as handle:
        np.savez_compressed(handle, **curves)
    os.replace(temporary_curve, curve_path)
    curve_receipt = {
        "schema_version": "ch3-rwkv7-complete-alert-budget-curves-v1",
        "artifact": {
            "filename": curve_path.name,
            "bytes": curve_path.stat().st_size,
            "sha256": sha256_file(curve_path),
        },
        "cells": list(CELL_ORDER),
        "fields": [
            "n_false_positive_entity",
            "nominal_fpr",
            "realized_fpr",
            "detection_rate",
        ],
        "complete_over_all_reachable_negative_entity_budgets": True,
    }
    atomic_json(
        output_root / "complete-alert-budget-curves-receipt.json", curve_receipt
    )
    interaction: dict[str, Any] = {}
    for metric in (
        "flow_average_precision",
        "entity_average_precision",
        "maximum_entity_average_precision",
    ):
        values = {cell: cells[cell]["target"][metric] for cell in CELL_ORDER}
        interaction[metric] = {
            **values,
            "causal_prefix_effect": values["C10"] - values["C00"],
            "elp_effect": values["C01"] - values["C00"],
            "combined_effect": values["C11"] - values["C00"],
            "interaction": values["C11"] - values["C10"] - values["C01"] + values["C00"],
        }
    target_seconds = time.time() - target_started
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "run_id": RUN_ID,
        "model": {
            "display_name": config["display_name"],
            "selected_adapter": adapter_key,
            "selected_capacity": capacity_key,
            "parameter_count": PARAMETER_COUNTS[capacity_key][adapter_key],
            "official_source_commit": config["candidate"]["official_source_commit"],
            "official_license": config["candidate"]["official_license"],
            "pytorch_version": torch.__version__,
        },
        "evidence": {
            "design_feasible": True,
            "experiment_status": "computed_not_yet_analyzed",
            "formal_paper_evidence": False,
            "target_previously_accessed": True,
            "independent_test": False,
            "target_metrics_used_for_selection_or_tuning": False,
            "capacity_upper_bound_verified": capacity_upper_bound_verified,
            "rwkv_family_failure_claim_allowed": False,
        },
        "source_selection": load_json(selection_path),
        "target_evaluation": {
            "dataset": "LSPR24",
            "flow_count": int(len(target["y24"])),
            "flow_positive_rate": float(np.mean(target["y24"], dtype=np.float64)),
            "cells": cells,
            "data_inventory": target_inventory,
            "counts": evaluation_counts,
        },
        "interaction": interaction,
        "isolation": {
            "all_source_selections_sealed_before_target_load": True,
            "target_disk_loads": 1,
            "target_evaluation_calls": 4,
            "one_call_per_cell_or_matching_complete_receipt": True,
        },
        "artifact_policy": {
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "all_epoch_model_weights_persisted": True,
            "latest_complete_inflight_persisted": True,
            "complete_alert_budget_curve": curve_receipt,
        },
        "resource": {
            "source_training_wall_seconds": source_training_seconds,
            "target_stage_wall_seconds": target_seconds,
            "gpu_hours": (source_training_seconds + target_seconds) / 3600.0,
            "maximum_gpu_hours": config["training"]["maximum_gpu_hours"],
            "peak_process_rss_mib": process_peak_rss_mib(),
            "launcher_admission_receipt": load_json(Path(args.resource_receipt))
            if args.resource_receipt
            else None,
        },
    }
    atomic_json(output_root / "aggregate-results.json", result)
    write_status(
        output_root,
        "computed",
        "publish-pending",
        0,
        "源年选择与目标四格评价完成，等待聚合发布",
    )
    build_manifest(output_root)


def publish_aggregate(config: Mapping[str, Any], args: argparse.Namespace) -> None:
    destination = config["swanlab"]
    if (
        args.authorized_swanlab_workspace != destination["workspace"]
        or args.authorized_swanlab_project != destination["project"]
    ):
        raise RuntimeError("SwanLab 授权目的地与冻结配置不一致")
    output_root = Path(config["paths"]["output_root"])
    result = load_json(output_root / "aggregate-results.json")
    import swanlab

    swanlab.init(
        workspace=destination["workspace"],
        project=destination["project"],
        name=RUN_ID,
        mode=destination["mode"],
        group=destination["group"],
        tags=destination["tags"],
        log_dir=str(output_root / "swanlog"),
        config={
            "run_id": RUN_ID,
            "seed": config["training"]["seed"],
            "protocol": "protocol_a_field_aware_capacity_then_2x2",
            "selected_adapter": result["model"]["selected_adapter"],
            "selected_capacity": result["model"]["selected_capacity"],
            "target_previously_accessed": True,
            "independent_test": False,
        },
    )
    metrics: dict[str, float] = {}
    for cell in CELL_ORDER:
        selection = result["source_selection"]["cells"][cell]
        target = result["target_evaluation"]["cells"][cell]["target"]
        metrics[f"source/{cell}_selected_epoch"] = float(
            selection["selected_epoch"]
        )
        metrics[f"source/{cell}_validation_flow_ap"] = float(
            selection["validation_flow_ap"]
        )
        metrics[f"target/{cell}_flow_ap"] = target["flow_average_precision"]
        metrics[f"target/{cell}_entity_ap"] = target["entity_average_precision"]
        metrics[f"target/{cell}_maximum_entity_ap"] = target[
            "maximum_entity_average_precision"
        ]
        for key, value in target["dr_at_fpr"].items():
            metrics[f"target/{cell}_dr_{key}"] = value
    metrics["resource/gpu_hours"] = result["resource"]["gpu_hours"]
    metrics["resource/peak_process_rss_mib"] = result["resource"][
        "peak_process_rss_mib"
    ]
    swanlab.log(metrics, step=0)
    swanlab.finish()
    atomic_json(
        output_root / "swanlab-receipt.json",
        {
            "schema_version": "ch3-rwkv7-field-aware-swanlab-receipt-v1",
            "completed": True,
            "workspace": destination["workspace"],
            "project": destination["project"],
            "metric_count": len(metrics),
            "per_sample_values_uploaded": False,
        },
    )
    write_status(output_root, "complete", "finished", 0, "聚合指标发布完成")
    build_manifest(output_root)


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = load_json(config_path)
    validate_config(config)
    if args.validate_config:
        print("配置核验通过")
        return 0
    try:
        if args.publish_only:
            publish_aggregate(config, args)
        else:
            run_experiment(config, args, config_path)
    except Exception as error:
        output_root = Path(config["paths"]["output_root"])
        output_root.mkdir(parents=True, exist_ok=True)
        write_status(
            output_root,
            "failed",
            "runtime",
            1,
            f"{type(error).__name__}: {error}"[:1000],
        )
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
