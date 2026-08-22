"""独立 CUDA-RWKV Raw83 模型。"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F

from cuda_rwkv_official_backend import cuda_rwkv_fused
from neural_precision_runtime import fp32_island


SEQUENCE_LENGTH = 128
FIELD_COUNT = 83
ADAPTERS = ("R1", "R2")
CAPACITIES = {
    "small": {
        "channels": 112,
        "head_size": 16,
        "low_rank": 8,
        "layers": 1,
        "preln": False,
    },
    "large": {
        "channels": 768,
        "head_size": 64,
        "low_rank": 32,
        "layers": 3,
        "preln": True,
    },
}
EXPECTED_PARAMETER_COUNTS = {
    "small": {"R1": 104_274, "R2": 104_274},
    "large": {"R1": 8_977_842, "R2": 9_490_178},
}
SEMANTIC_GROUPS = (
    {"name": "G00", "indices": (0, 1, 2, 79, 80, 81, 82)},
    {"name": "G01", "indices": tuple(range(3, 10))},
    {"name": "G02", "indices": tuple(range(10, 18))},
    {"name": "G03", "indices": tuple(range(18, 22))},
    {"name": "G04", "indices": tuple(range(22, 32))},
    {"name": "G05", "indices": tuple(range(32, 40))},
    {"name": "G06", "indices": (*range(40, 45), *range(53, 57))},
    {"name": "G07", "indices": tuple(range(45, 53))},
    {"name": "G08", "indices": tuple(range(57, 63))},
    {"name": "G09", "indices": tuple(range(63, 67))},
    {"name": "G10", "indices": tuple(range(67, 71))},
    {"name": "G11", "indices": tuple(range(71, 79))},
)


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def semantic_group_contract() -> dict[str, Any]:
    flattened = [index for group in SEMANTIC_GROUPS for index in group["indices"]]
    if len(SEMANTIC_GROUPS) != 12:
        raise RuntimeError("R1 语义组数必须为 12")
    if len(flattened) != FIELD_COUNT or sorted(flattened) != list(range(FIELD_COUNT)):
        raise RuntimeError("R1 语义组必须不重不漏覆盖 0..82")
    if len(set(flattened)) != FIELD_COUNT:
        raise RuntimeError("R1 语义组中存在重复字段")
    groups = [
        {"name": str(group["name"]), "indices": list(group["indices"])}
        for group in SEMANTIC_GROUPS
    ]
    return {
        "schema_version": "cuda-rwkv-semantic-groups-v1",
        "groups": groups,
        "coverage": list(range(FIELD_COUNT)),
        "groups_sha256": canonical_sha256(groups),
    }


class FieldSemanticAdapter(nn.Module):
    def __init__(self, channels: int, embedding_size: int = 15) -> None:
        super().__init__()
        semantic_group_contract()
        self.scalar_projection = nn.Linear(1, embedding_size)
        self.field_embedding = nn.Parameter(torch.empty(FIELD_COUNT, embedding_size))
        self.group_embedding = nn.Embedding(12, embedding_size)
        self.composition = nn.Linear(12 * embedding_size, channels)
        self.normalization = nn.LayerNorm(channels)
        self.output_scale = nn.Parameter(torch.ones(()))
        group_ids = torch.empty(FIELD_COUNT, dtype=torch.long)
        buffer_names: list[str] = []
        for group_id, group in enumerate(SEMANTIC_GROUPS):
            indices = torch.tensor(group["indices"], dtype=torch.long)
            group_ids[indices] = group_id
            buffer_name = f"group_indices_{group_id:02d}"
            self.register_buffer(buffer_name, indices, persistent=True)
            buffer_names.append(buffer_name)
        self.register_buffer("field_group_ids", group_ids, persistent=True)
        self._group_index_buffer_names = tuple(buffer_names)
        nn.init.normal_(self.field_embedding, mean=0.0, std=0.02)
        nn.init.normal_(self.group_embedding.weight, mean=0.0, std=0.02)

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        tokens = self.scalar_projection(values.unsqueeze(-1))
        identity = self.field_embedding + self.group_embedding(self.field_group_ids)
        tokens = tokens + identity.view(1, 1, FIELD_COUNT, -1)
        pooled = [
            tokens.index_select(2, getattr(self, name)).mean(2)
            for name in self._group_index_buffer_names
        ]
        composed = self.composition(torch.cat(pooled, dim=-1))
        with fp32_island(
            composed, device_type="cuda", torch_module=torch
        ) as (composed32,):
            normalized = self.normalization(composed32)
        return normalized * self.output_scale.float()


class MatchedProjectionAdapter(nn.Module):
    def __init__(self, channels: int) -> None:
        super().__init__()
        self.first = nn.Linear(FIELD_COUNT, channels)
        self.second = nn.Linear(channels, channels, bias=False)

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.second(F.relu(self.first(values)))


class CudaRwkvTimeMix(nn.Module):
    def __init__(
        self,
        channels: int,
        head_size: int,
        low_rank: int,
        layer_id: int,
        layer_count: int,
        capacity_key: str,
        build_root: Path,
        expected_environment: Mapping[str, Any],
    ) -> None:
        super().__init__()
        if channels % head_size != 0:
            raise ValueError("CUDA-RWKV 通道数必须能被头大小整除")
        self.channels = channels
        self.head_size = head_size
        self.heads = channels // head_size
        self.layer_id = layer_id
        self.capacity_key = capacity_key
        self.build_root = Path(build_root)
        self.expected_environment = dict(expected_environment)
        ratio_0_to_1 = layer_id / max(layer_count - 1, 1)
        ratio_1_to_almost0 = 1.0 - layer_id / layer_count
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
            linear = torch.arange(channels, dtype=torch.float32) / (channels - 1) - 0.5
            zigzag = (
                torch.arange(channels, dtype=torch.float32) % head_size
                - ((head_size - 1) / 2)
            ) / ((head_size - 1) / 2)
            zigzag = zigzag * zigzag.abs()
            if layer_count == 1:
                decay = -6 + 6 * (torch.arange(channels) / (channels - 1))
            else:
                decay = -7 + 5 * (
                    torch.arange(channels) / (channels - 1)
                ) ** (0.85 + math.sqrt(ratio_0_to_1))

            def orthogonal(value: torch.Tensor, scale: float) -> torch.Tensor:
                gain = (
                    math.sqrt(value.shape[0] / value.shape[1])
                    if value.shape[0] > value.shape[1]
                    else 1.0
                )
                nn.init.orthogonal_(value, gain=gain * scale)
                return value

            self.w1 = nn.Parameter(torch.zeros(channels, low_rank))
            self.w2 = nn.Parameter(orthogonal(torch.zeros(low_rank, channels), 0.1))
            self.w0 = nn.Parameter(
                decay.reshape(1, 1, channels) + 0.5 + zigzag * 2.5
            )
            self.a1 = nn.Parameter(torch.zeros(channels, low_rank))
            self.a2 = nn.Parameter(orthogonal(torch.zeros(low_rank, channels), 0.1))
            self.a0 = nn.Parameter(
                torch.zeros(1, 1, channels) - 0.19 + zigzag * 0.3 + linear * 0.4
            )
            self.g1 = nn.Parameter(torch.zeros(channels, low_rank))
            self.g2 = nn.Parameter(orthogonal(torch.zeros(low_rank, channels), 0.1))
            self.k_k = nn.Parameter(
                torch.zeros(1, 1, channels) + 0.71 - linear * 0.1
            )
            self.k_a = nn.Parameter(torch.zeros(1, 1, channels) + 1.02)
            self.r_k = nn.Parameter(torch.zeros(self.heads, head_size) - 0.04)
            if layer_id > 0:
                self.v0 = nn.Parameter(
                    torch.zeros(1, 1, channels) + 0.73 - linear * 0.4
                )
                self.v1 = nn.Parameter(torch.zeros(channels, low_rank))
                self.v2 = nn.Parameter(
                    orthogonal(torch.zeros(low_rank, channels), 0.1)
                )
            self.receptance = nn.Linear(channels, channels, bias=False)
            self.key = nn.Linear(channels, channels, bias=False)
            self.value = nn.Linear(channels, channels, bias=False)
            self.output = nn.Linear(channels, channels, bias=False)
            self.normalization = nn.GroupNorm(self.heads, channels, eps=64e-5)
            self.receptance.weight.data.uniform_(
                -0.5 / math.sqrt(channels), 0.5 / math.sqrt(channels)
            )
            self.key.weight.data.uniform_(
                -0.05 / math.sqrt(channels), 0.05 / math.sqrt(channels)
            )
            self.value.weight.data.uniform_(
                -0.5 / math.sqrt(channels), 0.5 / math.sqrt(channels)
            )
            self.output.weight.data.uniform_(
                -0.01 / math.sqrt(channels), 0.01 / math.sqrt(channels)
            )

    def forward(
        self,
        values: torch.Tensor,
        valid_mask: torch.Tensor,
        value_first: torch.Tensor | None,
        *,
        capture_kernel_inputs: bool,
    ) -> tuple[torch.Tensor, torch.Tensor, tuple[torch.Tensor, ...]]:
        batch, length, channels = values.shape
        if length != SEQUENCE_LENGTH or channels != self.channels:
            raise RuntimeError("CUDA-RWKV 块输入形状与冻结容量不符")
        shifted = torch.cat((torch.zeros_like(values[:, :1]), values[:, :-1]), dim=1)
        delta = shifted - values
        xr = values + delta * self.x_r
        xw = values + delta * self.x_w
        xk = values + delta * self.x_k
        xv = values + delta * self.x_v
        xa = values + delta * self.x_a
        xg = values + delta * self.x_g
        r = self.receptance(xr)
        k = self.key(xk)
        v = self.value(xv)
        if self.layer_id == 0:
            value_first = v
        else:
            if value_first is None:
                raise RuntimeError("CUDA-RWKV 多层块缺少首层值残差")
            with fp32_island(
                xv, value_first, v, device_type="cuda", torch_module=torch
            ) as (xv32, value_first32, v32):
                value_gate = torch.sigmoid(self.v0 + (xv32 @ self.v1) @ self.v2)
                v = v32 + (value_first32 - v32) * value_gate
        with fp32_island(xw, device_type="cuda", torch_module=torch) as (xw32,):
            w_raw = self.w0 + torch.tanh(xw32 @ self.w1) @ self.w2
        with fp32_island(xa, device_type="cuda", torch_module=torch) as (xa32,):
            gate_a = torch.sigmoid(self.a0 + (xa32 @ self.a1) @ self.a2)
        with fp32_island(xg, device_type="cuda", torch_module=torch) as (xg32,):
            gate_g32 = torch.sigmoid(xg32 @ self.g1.float()) @ self.g2.float()
        g = gate_g32.to(dtype=r.dtype)
        with fp32_island(k, gate_a, device_type="cuda", torch_module=torch) as (
            k32,
            gate_a32,
        ):
            normalized_key = F.normalize(
                (k32 * self.k_k).view(batch, length, self.heads, self.head_size),
                dim=-1,
                p=2.0,
            ).view(batch, length, channels)
            recurrent_key = k32 * (1.0 + (gate_a32 - 1.0) * self.k_a)
        mask = valid_mask.unsqueeze(-1)
        kernel_inputs = tuple(
            (tensor * mask)
            .to(dtype=torch.bfloat16)
            .contiguous()
            for tensor in (
                r,
                w_raw,
                recurrent_key,
                v,
                -normalized_key,
                normalized_key * gate_a,
            )
        )
        if capture_kernel_inputs:
            for tensor in kernel_inputs:
                if tensor.requires_grad:
                    tensor.retain_grad()
        recurrent = cuda_rwkv_fused(
            *kernel_inputs,
            capacity_key=self.capacity_key,
            build_root=self.build_root,
            expected_environment=self.expected_environment,
        )
        with fp32_island(
            recurrent, r, recurrent_key, v, g, device_type="cuda", torch_module=torch
        ) as (recurrent32, r32, key32, value32, g32):
            normalized = self.normalization(
                recurrent32.view(batch * length, channels)
            ).view(batch, length, channels)
            bonus = (
                (
                    r32.view(batch, length, self.heads, self.head_size)
                    * key32.view(batch, length, self.heads, self.head_size)
                    * self.r_k
                ).sum(dim=-1, keepdim=True)
                * value32.view(batch, length, self.heads, self.head_size)
            ).view(batch, length, channels)
            mixed = (normalized + bonus) * g32
        output = self.output(mixed) * mask
        return output, value_first, kernel_inputs


class CudaRwkvBlock(nn.Module):
    def __init__(
        self,
        capacity: Mapping[str, Any],
        layer_id: int,
        capacity_key: str,
        build_root: Path,
        expected_environment: Mapping[str, Any],
    ) -> None:
        super().__init__()
        channels = int(capacity["channels"])
        self.preln = bool(capacity["preln"])
        self.normalization = nn.LayerNorm(channels) if self.preln else nn.Identity()
        self.time_mix = CudaRwkvTimeMix(
            channels=channels,
            head_size=int(capacity["head_size"]),
            low_rank=int(capacity["low_rank"]),
            layer_id=layer_id,
            layer_count=int(capacity["layers"]),
            capacity_key=capacity_key,
            build_root=build_root,
            expected_environment=expected_environment,
        )

    def forward(
        self,
        values: torch.Tensor,
        valid_mask: torch.Tensor,
        value_first: torch.Tensor | None,
        *,
        capture_kernel_inputs: bool,
    ) -> tuple[torch.Tensor, torch.Tensor, tuple[torch.Tensor, ...]]:
        if self.preln:
            with fp32_island(
                values, device_type="cuda", torch_module=torch
            ) as (values32,):
                normalized = self.normalization(values32)
        else:
            normalized = values
        update, value_first, kernel_inputs = self.time_mix(
            normalized,
            valid_mask,
            value_first,
            capture_kernel_inputs=capture_kernel_inputs,
        )
        output = values + update if self.preln else update
        return output * valid_mask.unsqueeze(-1), value_first, kernel_inputs


@dataclass(frozen=True)
class ModelIdentity:
    spec: dict[str, Any]
    sha256: str


class CudaRwkvRaw83Model(nn.Module):
    def __init__(
        self,
        *,
        adapter_key: str,
        capacity_key: str,
        cell: str,
        use_causal_prefix: bool,
        use_learned_entity_pooling: bool,
        dropout: float,
        build_root: Path,
        expected_environment: Mapping[str, Any],
        precision_profile_id: str,
    ) -> None:
        super().__init__()
        if adapter_key not in ADAPTERS or capacity_key not in CAPACITIES:
            raise ValueError("CUDA-RWKV 输入适配或容量未预注册")
        if cell not in {"C00", "C01", "C10", "C11"}:
            raise ValueError("CUDA-RWKV 四格标识非法")
        self.adapter_key = adapter_key
        self.capacity_key = capacity_key
        self.cell = cell
        self.use_causal_prefix = use_causal_prefix
        self.use_learned_entity_pooling = use_learned_entity_pooling
        self.precision_profile_id = precision_profile_id
        capacity = CAPACITIES[capacity_key]
        channels = int(capacity["channels"])
        self.blocks = nn.ModuleList(
            CudaRwkvBlock(
                capacity,
                layer_id,
                capacity_key,
                Path(build_root) / capacity_key,
                expected_environment,
            )
            for layer_id in range(int(capacity["layers"]))
        )
        self.fusion = nn.Sequential(
            nn.Linear(channels * 2, channels),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.flow_head = nn.Linear(channels, 1)
        self.p_log = nn.Parameter(torch.tensor(float(math.log(2.0))))
        self.input_adapter: nn.Module
        if adapter_key == "R1":
            self.input_adapter = FieldSemanticAdapter(channels)
        else:
            self.input_adapter = MatchedProjectionAdapter(channels)
        self.last_kernel_inputs: tuple[tuple[torch.Tensor, ...], ...] = ()

    @property
    def pooling_power(self) -> torch.Tensor:
        return torch.exp(self.p_log.float()).clamp(1e-3, 1e3)

    def forward(
        self,
        values: torch.Tensor,
        valid_mask: torch.Tensor,
        *,
        capture_kernel_inputs: bool = False,
    ) -> torch.Tensor:
        if values.ndim != 3 or values.shape[1:] != (SEQUENCE_LENGTH, FIELD_COUNT):
            raise RuntimeError("CUDA-RWKV Raw83 输入形状必须为 [B,128,83]")
        if valid_mask.shape != values.shape[:2] or valid_mask.dtype != torch.bool:
            raise RuntimeError("CUDA-RWKV Raw83 有效位掩码形状或精度非法")
        mask = valid_mask.unsqueeze(-1)
        hidden = self.input_adapter(values * mask)
        hidden = hidden * mask
        value_first: torch.Tensor | None = None
        captured: list[tuple[torch.Tensor, ...]] = []
        for block in self.blocks:
            hidden, value_first, kernel_inputs = block(
                hidden,
                valid_mask,
                value_first,
                capture_kernel_inputs=capture_kernel_inputs,
            )
            captured.append(kernel_inputs)
        if self.use_causal_prefix:
            with fp32_island(
                hidden, device_type="cuda", torch_module=torch
            ) as (hidden32,):
                mask32 = valid_mask.float()
                counts = torch.cumsum(mask32, dim=1).clamp(min=1.0).unsqueeze(-1)
                context = torch.cumsum(hidden32 * mask32.unsqueeze(-1), dim=1) / counts
                context = context * mask32.unsqueeze(-1)
        else:
            context = torch.zeros_like(hidden)
        fused = self.fusion(torch.cat((hidden, context), dim=-1)) * mask
        logits = self.flow_head(fused).squeeze(-1)
        self.last_kernel_inputs = tuple(captured) if capture_kernel_inputs else ()
        return logits.masked_fill(~valid_mask, 0.0)

    def pool_entity_probabilities(
        self, probabilities: torch.Tensor, valid_mask: torch.Tensor
    ) -> torch.Tensor:
        with fp32_island(
            probabilities, device_type="cuda", torch_module=torch
        ) as (probabilities32,):
            power = self.pooling_power
            logs = torch.log(probabilities32.clamp(min=1e-7))
            count = valid_mask.float().sum(1).clamp(min=1.0)
            powered = (power * logs).masked_fill(~valid_mask, -1e30)
            return torch.exp(
                (torch.logsumexp(powered, dim=1) - torch.log(count)) / power
            )

    def module_parameter_groups(self) -> dict[str, list[nn.Parameter]]:
        groups = {
            "input_adapter": list(self.input_adapter.parameters()),
            "flow_head": list(self.flow_head.parameters()),
            "causal_prefix": list(self.fusion.parameters()) if self.use_causal_prefix else [],
            "entity_pooling": [self.p_log] if self.use_learned_entity_pooling else [],
        }
        for index, block in enumerate(self.blocks):
            groups[f"cuda_rwkv_block_{index}"] = list(block.parameters())
        return groups


def common_parameter_formula(channels: int, low_rank: int, layers: int) -> int:
    if layers == 1:
        return 6 * channels * channels + 6 * channels * low_rank + 15 * channels + 2
    if layers == 3:
        return 14 * channels * channels + 22 * channels * low_rank + 49 * channels + 2
    raise ValueError("CUDA-RWKV 只登记一层或三层容量")


def adapter_parameter_formula(adapter_key: str, channels: int) -> int:
    if adapter_key == "R1":
        embedding_size = 15
        return 97 * embedding_size + 12 * embedding_size * channels + 3 * channels + 1
    if adapter_key == "R2":
        return channels * channels + 84 * channels
    raise ValueError(f"未知 CUDA-RWKV 输入适配：{adapter_key}")


def build_model(
    config: Mapping[str, Any],
    *,
    adapter_key: str,
    capacity_key: str,
    cell: str,
    build_root: Path,
) -> tuple[CudaRwkvRaw83Model, ModelIdentity]:
    cell_contract = config["cells"][cell]
    expected_flags = {
        "C00": (False, False),
        "C01": (False, True),
        "C10": (True, False),
        "C11": (True, True),
    }
    actual_flags = (
        bool(cell_contract["causal_prefix_module"]),
        bool(cell_contract["learned_entity_pooling_module"]),
    )
    if actual_flags != expected_flags[cell]:
        raise RuntimeError(f"{cell} 四格模块位与冻结定义不符")
    model = CudaRwkvRaw83Model(
        adapter_key=adapter_key,
        capacity_key=capacity_key,
        cell=cell,
        use_causal_prefix=actual_flags[0],
        use_learned_entity_pooling=actual_flags[1],
        dropout=float(config["training"]["dropout"]),
        build_root=build_root,
        expected_environment=config["cuda"]["environment"],
        precision_profile_id=str(config["precision"]["profile_id"]),
    )
    capacity = CAPACITIES[capacity_key]
    formula = common_parameter_formula(
        int(capacity["channels"]),
        int(capacity["low_rank"]),
        int(capacity["layers"]),
    ) + adapter_parameter_formula(adapter_key, int(capacity["channels"]))
    measured = sum(parameter.numel() for parameter in model.parameters())
    expected = EXPECTED_PARAMETER_COUNTS[capacity_key][adapter_key]
    if formula != expected or measured != expected:
        raise RuntimeError(
            f"{capacity_key}/{adapter_key} 参数量不符："
            f"公式 {formula}，实测 {measured}，冻结 {expected}"
        )
    group_contract = semantic_group_contract()
    spec = {
        "schema_version": "cuda-rwkv-model-spec-v1",
        "field_list_sha256": config["data"]["field_list_sha256"],
        "semantic_groups_sha256": group_contract["groups_sha256"],
        "semantic_groups": group_contract["groups"],
        "view": None,
        "adapter": adapter_key,
        "capacity": capacity_key,
        "cell": cell,
        "channels": int(capacity["channels"]),
        "head_size": int(capacity["head_size"]),
        "low_rank": int(capacity["low_rank"]),
        "layers": int(capacity["layers"]),
        "sequence_length": SEQUENCE_LENGTH,
        "causal_prefix_module": actual_flags[0],
        "learned_entity_pooling_module": actual_flags[1],
        "parameter_formula": formula,
        "parameter_measured": measured,
        "precision_profile_id": config["precision"]["profile_id"],
    }
    return model, ModelIdentity(spec=spec, sha256=canonical_sha256(spec))


def validate_all_parameter_formulas(config: Mapping[str, Any]) -> dict[str, int]:
    """不运行前向即机械核对四个容量与适配组合。"""

    measured: dict[str, int] = {}
    build_root = Path(config["paths"]["run_root"]) / "build"
    for capacity_key in ("small", "large"):
        for adapter_key in ADAPTERS:
            model, _ = build_model(
                config,
                adapter_key=adapter_key,
                capacity_key=capacity_key,
                cell="C00",
                build_root=build_root,
            )
            key = f"{capacity_key}/{adapter_key}"
            measured[key] = sum(parameter.numel() for parameter in model.parameters())
            del model
    return measured
