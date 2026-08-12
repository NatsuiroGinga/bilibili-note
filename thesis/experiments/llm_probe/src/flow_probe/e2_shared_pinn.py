"""E2 困难域最小共享 PINN 的四组因果对照。"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import torch
import torch.nn.functional as functional

from flow_probe.e2_hard_domain_data import E2_FEATURE_FIELDS

E2_PINN_VARIANTS = ("E2-A", "E2-S", "E2-P", "E2-X")


class E2SharedPinnError(ValueError):
    """E2 共享 PINN 的结构、监督或训练合同不满足时抛出。"""


@dataclass(frozen=True)
class E2PinnBudget:
    """四组共用的训练预算与损失权重。"""

    max_steps: int
    batch_size: int
    physics_batch_size: int | None = None
    lambda_state: float = 1.0
    lambda_conservation: float = 0.01
    lambda_boundary: float = 0.01
    constraint_tolerance: float = 0.05

    def validate(self) -> None:
        if self.max_steps < 1 or self.batch_size < 1 or self.resolved_physics_batch_size < 1:
            raise E2SharedPinnError("训练步数和批大小必须为正整数")
        weights = (
            self.lambda_state,
            self.lambda_conservation,
            self.lambda_boundary,
        )
        if any(not math.isfinite(value) or value < 0.0 for value in weights):
            raise E2SharedPinnError("辅助损失权重必须是有限非负数")
        if not math.isfinite(self.constraint_tolerance) or self.constraint_tolerance <= 0.0:
            raise E2SharedPinnError("约束违反阈值必须是有限正数")

    @property
    def detection_batch_size(self) -> int:
        """检测批大小；保留 batch_size 名称以兼容已落盘配置。"""
        return self.batch_size

    @property
    def resolved_physics_batch_size(self) -> int:
        """物理批大小；未单独指定时与检测批相同。"""
        return self.batch_size if self.physics_batch_size is None else self.physics_batch_size


@dataclass(frozen=True)
class E2VariantContract:
    """只改变监督开关，不改变结构或参数预算的变体合同。"""

    variant: str
    uses_state_supervision: bool
    uses_conservation: bool
    uses_boundary: bool
    requires_permuted_physics: bool


def build_e2_variant_contract(variant: str) -> E2VariantContract:
    """返回 E2-A/S/P/X 的冻结因果角色。"""
    name = str(variant).upper()
    if name not in E2_PINN_VARIANTS:
        raise E2SharedPinnError(f"未知 E2 PINN 变体：{variant}")
    return E2VariantContract(
        variant=name,
        uses_state_supervision=name != "E2-A",
        uses_conservation=name in {"E2-P", "E2-X"},
        uses_boundary=name in {"E2-P", "E2-X"},
        requires_permuted_physics=name == "E2-X",
    )


def _validate_variant_budget(
    contract: E2VariantContract,
    budget: E2PinnBudget,
) -> None:
    budget.validate()
    if contract.uses_state_supervision and budget.lambda_state <= 0.0:
        raise E2SharedPinnError("E2-S/E2-P/E2-X 的状态监督权重必须为正数")
    if contract.uses_conservation and budget.lambda_conservation <= 0.0:
        raise E2SharedPinnError("E2-P/E2-X 的共享守恒权重必须为正数")
    if contract.uses_boundary and budget.lambda_boundary <= 0.0:
        raise E2SharedPinnError("E2-P/E2-X 的状态边界权重必须为正数")


class E2NumericEncoder(torch.nn.Module):
    """共同七字段的最小数值编码器；也可由任务 4 注入其他编码器。"""

    def __init__(self, input_size: int, hidden_size: int) -> None:
        super().__init__()
        if input_size < 1 or hidden_size < 1:
            raise E2SharedPinnError("编码器输入维度和隐藏维度必须为正整数")
        self.network = torch.nn.Sequential(
            torch.nn.Linear(input_size, hidden_size),
            torch.nn.GELU(),
            torch.nn.Linear(hidden_size, hidden_size),
            torch.nn.LayerNorm(hidden_size),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        first_linear = self.network[0]
        assert isinstance(first_linear, torch.nn.Linear)
        return self.network(features.to(dtype=first_linear.weight.dtype))


class E2SharedStateHead(torch.nn.Module):
    """从共享表示预测非负、无量纲的多通道时间状态。"""

    def __init__(self, hidden_size: int, state_channels: int, state_points: int) -> None:
        super().__init__()
        if min(hidden_size, state_channels, state_points) < 1 or state_points < 2:
            raise E2SharedPinnError("状态头至少需要一个通道和两个时间锚点")
        self.state_channels = state_channels
        self.state_points = state_points
        self.network = torch.nn.Sequential(
            torch.nn.Linear(hidden_size, hidden_size),
            torch.nn.SiLU(),
            torch.nn.Linear(hidden_size, state_channels * state_points),
            torch.nn.Softplus(),
        )

    def forward(self, hidden: torch.Tensor) -> torch.Tensor:
        first_linear = self.network[0]
        assert isinstance(first_linear, torch.nn.Linear)
        state = self.network(hidden.to(dtype=first_linear.weight.dtype))
        return state.reshape(hidden.shape[0], self.state_channels, self.state_points)


@dataclass(frozen=True)
class E2ModelOutput:
    """共享检测头和状态头的前向输出。"""

    logits: torch.Tensor
    state: torch.Tensor


class E2SharedPinnModel(torch.nn.Module):
    """四个变体共用的编码器、检测头和同参数量状态分支。"""

    def __init__(
        self,
        *,
        input_size: int,
        hidden_size: int,
        state_channels: int,
        state_points: int,
        encoder: torch.nn.Module | None = None,
        feature_fields: Sequence[str] = E2_FEATURE_FIELDS,
    ) -> None:
        super().__init__()
        if tuple(feature_fields) != E2_FEATURE_FIELDS or input_size != len(E2_FEATURE_FIELDS):
            raise E2SharedPinnError("共享 PINN 检测输入必须精确为冻结七字段")
        self.feature_fields = E2_FEATURE_FIELDS
        self.encoder = encoder or E2NumericEncoder(input_size, hidden_size)
        self.hidden_size = hidden_size
        self.detection_head = torch.nn.Linear(hidden_size, 2)
        self.state_head = E2SharedStateHead(hidden_size, state_channels, state_points)

    def forward_hidden(self, hidden: torch.Tensor) -> E2ModelOutput:
        if hidden.ndim != 2 or hidden.shape[1] != self.hidden_size:
            raise E2SharedPinnError("共享编码器必须输出[批量, 隐藏维度]二维张量")
        if not torch.isfinite(hidden).all():
            raise E2SharedPinnError("共享编码器输出包含非有限值")
        detection_hidden = hidden.to(dtype=self.detection_head.weight.dtype)
        return E2ModelOutput(
            logits=self.detection_head(detection_hidden),
            state=self.state_head(hidden),
        )

    def forward(self, features: torch.Tensor) -> E2ModelOutput:
        if features.ndim != 2 or features.shape[1] != len(E2_FEATURE_FIELDS):
            raise E2SharedPinnError("模型输入必须是[批量, 7]的冻结七字段张量")
        hidden = self.encoder(features)
        if not isinstance(hidden, torch.Tensor):
            raise E2SharedPinnError("共享编码器必须直接返回隐藏张量")
        return self.forward_hidden(hidden)


@dataclass(frozen=True)
class E2ParameterBudgetSignature:
    """模型结构和可训练参数预算的稳定摘要。"""

    trainable_parameters: int
    total_parameters: int
    parameter_shapes_sha256: str


@dataclass(frozen=True)
class E2TrainingBudgetSignature:
    """结构、实际训练用量与共同初始权重的稳定摘要。"""

    parameter_budget: E2ParameterBudgetSignature
    max_steps: int
    detection_batch_size: int
    physics_batch_size: int
    initial_weights_sha256: str


def parameter_budget_signature(model: torch.nn.Module) -> E2ParameterBudgetSignature:
    """摘要只绑定参数名、形状和可训练状态，不绑定随机初值。"""
    records = [
        {
            "name": name,
            "shape": list(parameter.shape),
            "trainable": bool(parameter.requires_grad),
        }
        for name, parameter in model.named_parameters()
    ]
    payload = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return E2ParameterBudgetSignature(
        trainable_parameters=sum(
            parameter.numel() for parameter in model.parameters() if parameter.requires_grad
        ),
        total_parameters=sum(parameter.numel() for parameter in model.parameters()),
        parameter_shapes_sha256=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    )


def ordered_sample_ids_sha256(sample_ids: Sequence[str]) -> str:
    """计算样本标识有序序列的稳定摘要。"""
    payload = json.dumps(tuple(sample_ids), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _tensor_sha256(value: torch.Tensor) -> str:
    tensor = value.detach().cpu().contiguous()
    digest = hashlib.sha256()
    digest.update(str(tensor.dtype).encode("ascii"))
    digest.update(json.dumps(list(tensor.shape), separators=(",", ":")).encode("ascii"))
    digest.update(tensor.view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def _model_weights_sha256(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, parameter in sorted(model.named_parameters()):
        digest.update(name.encode("utf-8"))
        digest.update(_tensor_sha256(parameter).encode("ascii"))
    return digest.hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def training_budget_signature(
    model: torch.nn.Module,
    budget: E2PinnBudget,
) -> E2TrainingBudgetSignature:
    """把训练步数、双批量和实际初始权重纳入共同预算。"""
    budget.validate()
    return E2TrainingBudgetSignature(
        parameter_budget=parameter_budget_signature(model),
        max_steps=budget.max_steps,
        detection_batch_size=budget.detection_batch_size,
        physics_batch_size=budget.resolved_physics_batch_size,
        initial_weights_sha256=_model_weights_sha256(model),
    )


_DETECTION_BATCH_BINDING_TOKEN = object()


@dataclass(frozen=True)
class E2DetectionBatchBinding:
    """由冻结源域清单签发的检测批身份收据。"""

    sample_ids: tuple[str, ...]
    profiles: tuple[str, ...]
    split_ids: tuple[str, ...]
    source_binding_sha256: str
    _verification_token: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class E2DetectionSourceBinding:
    """冻结源域训练清单；批次样本必须可追溯到该清单。"""

    sample_ids: tuple[str, ...]
    profiles: tuple[str, ...]
    split_ids: tuple[str, ...]
    data_view_sha256: str
    feature_fields: tuple[str, ...] = E2_FEATURE_FIELDS

    def validate(self) -> None:
        if tuple(self.feature_fields) != E2_FEATURE_FIELDS:
            raise E2SharedPinnError("检测源域绑定必须精确使用冻结七字段")
        size = len(self.sample_ids)
        if size < 1 or len(self.profiles) != size or len(self.split_ids) != size:
            raise E2SharedPinnError("检测源域绑定的样本、域和划分数量不一致")
        if any(not sample_id for sample_id in self.sample_ids) or len(set(self.sample_ids)) != size:
            raise E2SharedPinnError("检测源域清单 sample_id 必须非空且唯一")
        if any(profile not in {"A", "B", "D"} for profile in self.profiles):
            raise E2SharedPinnError("检测训练只允许 A/B/D 源域，禁止 C 目标域")
        if any(split_id != "train" for split_id in self.split_ids):
            raise E2SharedPinnError("检测源域绑定只允许冻结 train 划分")
        if not _is_sha256(self.data_view_sha256):
            raise E2SharedPinnError("检测源域绑定缺少合法数据视图 SHA-256")

    @property
    def binding_sha256(self) -> str:
        self.validate()
        payload = {
            "sample_ids": self.sample_ids,
            "profiles": self.profiles,
            "split_ids": self.split_ids,
            "feature_fields": self.feature_fields,
            "data_view_sha256": self.data_view_sha256,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def bind_batch(self, sample_ids: Sequence[str]) -> E2DetectionBatchBinding:
        """从冻结清单签发包含 sample_id/profile/split_id 的批次收据。"""
        self.validate()
        ids = tuple(sample_ids)
        if any(not sample_id for sample_id in ids):
            raise E2SharedPinnError("检测批 sample_id 不得为空")
        metadata = {
            sample_id: (profile, split_id)
            for sample_id, profile, split_id in zip(
                self.sample_ids, self.profiles, self.split_ids, strict=True
            )
        }
        if any(sample_id not in metadata for sample_id in ids):
            raise E2SharedPinnError("检测批含未绑定的样本或 C 目标域样本")
        return E2DetectionBatchBinding(
            sample_ids=ids,
            profiles=tuple(metadata[sample_id][0] for sample_id in ids),
            split_ids=tuple(metadata[sample_id][1] for sample_id in ids),
            source_binding_sha256=self.binding_sha256,
            _verification_token=_DETECTION_BATCH_BINDING_TOKEN,
        )

    def validate_batch(
        self,
        binding: E2DetectionBatchBinding,
        features: torch.Tensor,
    ) -> None:
        self.validate()
        if binding._verification_token is not _DETECTION_BATCH_BINDING_TOKEN:
            raise E2SharedPinnError("检测批必须由冻结源域清单签发")
        if len(binding.sample_ids) != int(features.shape[0]):
            raise E2SharedPinnError("检测批身份收据与特征行数不一致")
        expected = self.bind_batch(binding.sample_ids)
        if binding != expected or binding.source_binding_sha256 != self.binding_sha256:
            raise E2SharedPinnError("检测批 sample_id/profile/split_id 与冻结源域绑定不一致")


@dataclass(frozen=True)
class E2PhysicsFeatureBinding:
    """物理特征批的样本顺序与张量摘要。"""

    sample_ids: tuple[str, ...]
    sample_order_sha256: str
    feature_tensor_sha256: str
    feature_fields: tuple[str, ...] = E2_FEATURE_FIELDS

    @property
    def binding_sha256(self) -> str:
        payload = {
            "sample_ids": self.sample_ids,
            "sample_order_sha256": self.sample_order_sha256,
            "feature_tensor_sha256": self.feature_tensor_sha256,
            "feature_fields": self.feature_fields,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def validate(self, features: torch.Tensor) -> None:
        if tuple(self.feature_fields) != E2_FEATURE_FIELDS:
            raise E2SharedPinnError("物理特征必须精确使用冻结七字段")
        if features.ndim != 2 or features.shape[1] != len(E2_FEATURE_FIELDS):
            raise E2SharedPinnError("物理特征必须是[批量, 7]张量")
        if len(self.sample_ids) != int(features.shape[0]) or any(
            not sample_id for sample_id in self.sample_ids
        ):
            raise E2SharedPinnError("物理特征样本标识与特征行数不一致")
        if self.sample_order_sha256 != ordered_sample_ids_sha256(self.sample_ids):
            raise E2SharedPinnError("物理特征样本顺序摘要不一致")
        if self.feature_tensor_sha256 != _tensor_sha256(features):
            raise E2SharedPinnError("物理特征张量与绑定摘要不一致")


def build_e2_physics_feature_binding(
    features: torch.Tensor,
    sample_ids: Sequence[str],
    *,
    feature_fields: Sequence[str] = E2_FEATURE_FIELDS,
) -> E2PhysicsFeatureBinding:
    """从实际特征张量构建物理批绑定。"""
    binding = E2PhysicsFeatureBinding(
        sample_ids=tuple(sample_ids),
        sample_order_sha256=ordered_sample_ids_sha256(sample_ids),
        feature_tensor_sha256=_tensor_sha256(features),
        feature_fields=tuple(feature_fields),
    )
    binding.validate(features)
    return binding


_PERMUTATION_RECEIPT_TOKEN = object()


@dataclass(frozen=True)
class E2PermutationReceipt:
    """由分层置换构造器生成的不透明可验证收据。"""

    source_sample_ids: tuple[str, ...]
    permuted_sample_ids: tuple[str, ...]
    permutation_indices: tuple[int, ...]
    source_order_sha256: str
    permuted_order_sha256: str
    permutation_sha256: str
    source_supervision_sha256: str
    permuted_supervision_sha256: str
    stratification_fields: tuple[str, ...]
    seed: int
    _verification_token: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class E2PhysicsSupervision:
    """训练期物理真值；状态、边界均无量纲，通量由 scale 归一化。"""

    state_targets: torch.Tensor
    state_supervision_mask: torch.Tensor
    state_evaluation_mask: torch.Tensor
    arrivals: torch.Tensor
    departures: torch.Tensor
    losses: torch.Tensor
    normalization_scale: torch.Tensor
    conservation_mask: torch.Tensor
    lower_bound: torch.Tensor
    upper_bound: torch.Tensor
    boundary_mask: torch.Tensor
    sample_ids: tuple[str, ...] = ()
    sample_order_sha256: str = ""
    feature_binding_sha256: str = ""
    provenance: str = "aligned"
    permutation_receipt: E2PermutationReceipt | None = None

    def validate(self) -> None:
        state_shape = tuple(self.state_targets.shape)
        if len(state_shape) != 3 or state_shape[0] < 1 or state_shape[1] < 1 or state_shape[2] < 2:
            raise E2SharedPinnError("状态真值必须采用[批量, 通道, 时间锚点]三维形状")
        if tuple(self.state_supervision_mask.shape) != state_shape:
            raise E2SharedPinnError("状态监督掩码与状态真值形状不一致")
        if tuple(self.state_evaluation_mask.shape) != state_shape:
            raise E2SharedPinnError("状态评价掩码与状态真值形状不一致")
        if tuple(self.lower_bound.shape) != state_shape or tuple(self.upper_bound.shape) != state_shape:
            raise E2SharedPinnError("状态边界与状态真值形状不一致")
        if tuple(self.boundary_mask.shape) != state_shape:
            raise E2SharedPinnError("边界掩码与状态真值形状不一致")
        transition_shape = (state_shape[0], state_shape[1], state_shape[2] - 1)
        transition_tensors = (
            self.arrivals,
            self.departures,
            self.losses,
            self.conservation_mask,
        )
        if any(tuple(value.shape) != transition_shape for value in transition_tensors):
            raise E2SharedPinnError("通量与守恒掩码必须采用[批量, 通道, 状态转移]形状")
        scale_shape = tuple(self.normalization_scale.shape)
        if scale_shape not in {(state_shape[0], state_shape[1]), (state_shape[0], state_shape[1], 1)}:
            raise E2SharedPinnError("归一化尺度必须按样本和状态通道提供")
        masks = (
            self.state_supervision_mask,
            self.state_evaluation_mask,
            self.conservation_mask,
            self.boundary_mask,
        )
        if any(mask.dtype != torch.bool for mask in masks):
            raise E2SharedPinnError("所有物理掩码必须是布尔张量")
        numeric = (
            self.state_targets,
            self.arrivals,
            self.departures,
            self.losses,
            self.normalization_scale,
            self.lower_bound,
            self.upper_bound,
        )
        if any(not torch.isfinite(value).all() for value in numeric):
            raise E2SharedPinnError("物理监督包含非有限值")
        if torch.any(self.state_targets < 0) or torch.any(self.arrivals < 0):
            raise E2SharedPinnError("状态真值和到达量不得为负")
        if torch.any(self.departures < 0) or torch.any(self.losses < 0):
            raise E2SharedPinnError("离开量和损失量不得为负")
        if torch.any(self.normalization_scale <= 0):
            raise E2SharedPinnError("归一化尺度必须为有限正数")
        if torch.any(self.lower_bound > self.upper_bound):
            raise E2SharedPinnError("状态下界不得高于上界")
        if torch.any(self.state_supervision_mask & ~self.state_evaluation_mask):
            raise E2SharedPinnError("状态监督位置必须包含在状态评价位置中")
        if len(self.sample_ids) != state_shape[0] or any(not value for value in self.sample_ids):
            raise E2SharedPinnError("物理监督 sample_id 与批量行数不一致")
        if self.sample_order_sha256 != ordered_sample_ids_sha256(self.sample_ids):
            raise E2SharedPinnError("物理监督样本顺序摘要不一致")
        if not _is_sha256(self.feature_binding_sha256):
            raise E2SharedPinnError("物理监督缺少特征绑定 SHA-256")
        if self.provenance not in {"aligned", "stratified_permuted"}:
            raise E2SharedPinnError("物理监督来源只能是对齐或分层置换")
        if self.provenance == "aligned" and self.permutation_receipt is not None:
            raise E2SharedPinnError("对齐物理监督不得携带置换收据")
        if self.provenance == "stratified_permuted":
            _validate_permutation_receipt(self)

    @property
    def batch_size(self) -> int:
        return int(self.state_targets.shape[0])

    def scale_for_transitions(self) -> torch.Tensor:
        scale = self.normalization_scale
        return scale.unsqueeze(-1) if scale.ndim == 2 else scale


def _physics_supervision_sha256(supervision: E2PhysicsSupervision) -> str:
    digest = hashlib.sha256()
    tensors = (
        supervision.state_targets,
        supervision.state_supervision_mask,
        supervision.state_evaluation_mask,
        supervision.arrivals,
        supervision.departures,
        supervision.losses,
        supervision.normalization_scale,
        supervision.conservation_mask,
        supervision.lower_bound,
        supervision.upper_bound,
        supervision.boundary_mask,
    )
    for value in tensors:
        digest.update(_tensor_sha256(value).encode("ascii"))
    return digest.hexdigest()


def _permutation_sha256(indices: Sequence[int]) -> str:
    payload = json.dumps(tuple(int(value) for value in indices), separators=(",", ":"))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def _validate_permutation_receipt(supervision: E2PhysicsSupervision) -> None:
    receipt = supervision.permutation_receipt
    if receipt is None or receipt._verification_token is not _PERMUTATION_RECEIPT_TOKEN:
        raise E2SharedPinnError("E2-X 必须使用置换构造器签发的可验证收据")
    size = supervision.batch_size
    indices = receipt.permutation_indices
    if len(indices) != size or sorted(indices) != list(range(size)):
        raise E2SharedPinnError("E2-X 置换收据的索引不是完整排列")
    if any(source == destination for destination, source in enumerate(indices)):
        raise E2SharedPinnError("E2-X 置换收据不得包含固定点")
    expected_permuted_ids = tuple(receipt.source_sample_ids[index] for index in indices)
    if receipt.permuted_sample_ids != expected_permuted_ids:
        raise E2SharedPinnError("E2-X 置换 sample_id 与索引收据不一致")
    if supervision.sample_ids != receipt.permuted_sample_ids:
        raise E2SharedPinnError("E2-X 物理监督顺序与置换收据不一致")
    if receipt.source_order_sha256 != ordered_sample_ids_sha256(receipt.source_sample_ids):
        raise E2SharedPinnError("E2-X 原始样本顺序摘要不一致")
    if receipt.permuted_order_sha256 != ordered_sample_ids_sha256(receipt.permuted_sample_ids):
        raise E2SharedPinnError("E2-X 置换样本顺序摘要不一致")
    if receipt.permutation_sha256 != _permutation_sha256(indices):
        raise E2SharedPinnError("E2-X 置换索引摘要不一致")
    if receipt.source_supervision_sha256 == receipt.permuted_supervision_sha256:
        raise E2SharedPinnError("E2-X 置换后物理监督未实际改变")
    if receipt.permuted_supervision_sha256 != _physics_supervision_sha256(supervision):
        raise E2SharedPinnError("E2-X 当前物理监督与置换摘要不一致")


@dataclass(frozen=True)
class E2PermutationRecord:
    """仅用于构造负对照的显式分层键，不进入检测模型。"""

    sample_id: str
    source_domain: str
    protocol: str
    scene_condition: str
    missing_pattern: tuple[bool, ...]
    label: int | None = None
    capture_id: str | None = None


def e2_x_stratification_fields(
    records: Sequence[E2PermutationRecord],
) -> tuple[str, ...]:
    """返回真实可用的分层字段，禁止为辅助源伪造标签或捕获组。"""
    if not records:
        raise E2SharedPinnError("E2-X 置换记录不得为空")
    label_availability = [record.label is not None for record in records]
    capture_availability = [record.capture_id is not None for record in records]
    if any(label_availability) and not all(label_availability):
        raise E2SharedPinnError("物理批标签可用性不一致，禁止部分伪造分层标签")
    if any(capture_availability) and not all(capture_availability):
        raise E2SharedPinnError("物理批捕获组可用性不一致，禁止部分伪造捕获组")
    fields = ["source_domain", "protocol", "scene_condition", "missing_pattern"]
    if all(label_availability):
        fields.append("label")
    if all(capture_availability):
        fields.append("capture_id")
    return tuple(fields)


def _e2_x_stratum(
    record: E2PermutationRecord,
    fields: Sequence[str],
) -> tuple[object, ...]:
    return tuple(getattr(record, field) for field in fields)


def build_e2_x_permutation(
    records: Sequence[E2PermutationRecord],
    supervision: E2PhysicsSupervision,
    *,
    seed: int,
) -> tuple[int, ...]:
    """在联合分层内生成确定性无固定点置换，破坏样本与物理真值对应。"""
    supervision.validate()
    if supervision.provenance != "aligned" or supervision.permutation_receipt is not None:
        raise E2SharedPinnError("E2-X 只能从对齐的原始物理监督构造置换")
    if len(records) != supervision.batch_size:
        raise E2SharedPinnError("置换记录数量与物理监督批量不一致")
    sample_ids = [record.sample_id for record in records]
    if any(not sample_id for sample_id in sample_ids) or len(sample_ids) != len(set(sample_ids)):
        raise E2SharedPinnError("置换记录 sample_id 必须非空且唯一")
    if tuple(sample_ids) != supervision.sample_ids:
        raise E2SharedPinnError("置换记录与原始物理监督 sample_id 顺序不一致")
    stratification_fields = e2_x_stratification_fields(records)
    strata: dict[tuple[object, ...], list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        if record.label is not None and record.label not in {0, 1}:
            raise E2SharedPinnError("置换分层标签必须为 0 或 1")
        actual_pattern = tuple(
            bool(value)
            for value in supervision.state_supervision_mask[index].detach().cpu().flatten().tolist()
        )
        if record.missing_pattern != actual_pattern:
            raise E2SharedPinnError("置换记录的缺失模式与状态监督掩码不一致")
        if not record.source_domain or not record.protocol or not record.scene_condition:
            raise E2SharedPinnError("置换的物理源、协议和场景条件不得为空")
        if record.capture_id is not None and not record.capture_id:
            raise E2SharedPinnError("已声明可用的捕获组不得为空")
        strata[_e2_x_stratum(record, stratification_fields)].append(index)
    singleton_count = sum(len(indices) == 1 for indices in strata.values())
    if singleton_count:
        raise E2SharedPinnError(
            f"E2-X 存在 {singleton_count} 个单样本分层，无法构造无固定点负对照"
        )
    permutation = list(range(len(records)))
    for indices in strata.values():
        ordered = sorted(
            indices,
            key=lambda index: hashlib.sha256(
                f"{seed}|{records[index].sample_id}".encode("utf-8")
            ).hexdigest(),
        )
        for position, destination in enumerate(ordered):
            permutation[destination] = ordered[(position + 1) % len(ordered)]
    if any(source == destination for destination, source in enumerate(permutation)):
        raise E2SharedPinnError("E2-X 置换不得保留任何样本自身的物理监督")
    if sorted(permutation) != list(range(len(records))):
        raise E2SharedPinnError("E2-X 置换必须保持物理监督边际分布不变")
    return tuple(permutation)


def _permute_batch_tensor(value: torch.Tensor, permutation: Sequence[int]) -> torch.Tensor:
    index = torch.as_tensor(permutation, dtype=torch.long, device=value.device)
    return value.index_select(0, index)


def permute_e2_physics_supervision(
    supervision: E2PhysicsSupervision,
    permutation: Sequence[int],
    *,
    records: Sequence[E2PermutationRecord],
    seed: int,
) -> E2PhysicsSupervision:
    """核验分层计划后置换物理监督并签发不透明收据。"""
    supervision.validate()
    indices = tuple(int(index) for index in permutation)
    if len(indices) != supervision.batch_size or sorted(indices) != list(
        range(supervision.batch_size)
    ):
        raise E2SharedPinnError("物理监督置换索引必须覆盖整个批量且不重复")
    if any(source == destination for destination, source in enumerate(indices)):
        raise E2SharedPinnError("E2-X 物理监督置换不得包含固定点")
    expected = build_e2_x_permutation(records, supervision, seed=seed)
    if indices != expected:
        raise E2SharedPinnError("E2-X 置换索引与预注册分层计划不一致")
    source_ids = supervision.sample_ids
    permuted_ids = tuple(source_ids[index] for index in indices)
    source_supervision_sha256 = _physics_supervision_sha256(supervision)
    result = E2PhysicsSupervision(
        state_targets=_permute_batch_tensor(supervision.state_targets, indices),
        state_supervision_mask=_permute_batch_tensor(
            supervision.state_supervision_mask, indices
        ),
        state_evaluation_mask=_permute_batch_tensor(
            supervision.state_evaluation_mask, indices
        ),
        arrivals=_permute_batch_tensor(supervision.arrivals, indices),
        departures=_permute_batch_tensor(supervision.departures, indices),
        losses=_permute_batch_tensor(supervision.losses, indices),
        normalization_scale=_permute_batch_tensor(supervision.normalization_scale, indices),
        conservation_mask=_permute_batch_tensor(supervision.conservation_mask, indices),
        lower_bound=_permute_batch_tensor(supervision.lower_bound, indices),
        upper_bound=_permute_batch_tensor(supervision.upper_bound, indices),
        boundary_mask=_permute_batch_tensor(supervision.boundary_mask, indices),
        sample_ids=permuted_ids,
        sample_order_sha256=ordered_sample_ids_sha256(permuted_ids),
        feature_binding_sha256=supervision.feature_binding_sha256,
        provenance="stratified_permuted",
    )
    permuted_supervision_sha256 = _physics_supervision_sha256(result)
    receipt = E2PermutationReceipt(
        source_sample_ids=source_ids,
        permuted_sample_ids=permuted_ids,
        permutation_indices=indices,
        source_order_sha256=supervision.sample_order_sha256,
        permuted_order_sha256=result.sample_order_sha256,
        permutation_sha256=_permutation_sha256(indices),
        source_supervision_sha256=source_supervision_sha256,
        permuted_supervision_sha256=permuted_supervision_sha256,
        stratification_fields=e2_x_stratification_fields(records),
        seed=int(seed),
        _verification_token=_PERMUTATION_RECEIPT_TOKEN,
    )
    object.__setattr__(result, "permutation_receipt", receipt)
    result.validate()
    return result


def _masked_mean(values: torch.Tensor, mask: torch.Tensor, name: str) -> torch.Tensor:
    count = int(mask.sum().item())
    if count < 1:
        raise E2SharedPinnError(f"{name}没有有效监督位置")
    return values.masked_select(mask).mean()


def state_supervision_loss(
    predicted_state: torch.Tensor,
    supervision: E2PhysicsSupervision,
) -> torch.Tensor:
    """只在训练期可观测状态位置计算无量纲均方误差。"""
    supervision.validate()
    if tuple(predicted_state.shape) != tuple(supervision.state_targets.shape):
        raise E2SharedPinnError("预测状态与状态真值形状不一致")
    return _masked_mean(
        (predicted_state - supervision.state_targets).square(),
        supervision.state_supervision_mask,
        "状态监督",
    )


def shared_conservation_residual(
    predicted_state: torch.Tensor,
    supervision: E2PhysicsSupervision,
) -> torch.Tensor:
    """计算攻击不改变的共享守恒：状态增量等于归一化净流入。"""
    supervision.validate()
    if tuple(predicted_state.shape) != tuple(supervision.state_targets.shape):
        raise E2SharedPinnError("预测状态与物理通量形状不一致")
    predicted_change = predicted_state[:, :, 1:] - predicted_state[:, :, :-1]
    normalized_net_input = (
        supervision.arrivals - supervision.departures - supervision.losses
    ) / supervision.scale_for_transitions()
    return predicted_change - normalized_net_input


def shared_boundary_violation(
    predicted_state: torch.Tensor,
    supervision: E2PhysicsSupervision,
) -> torch.Tensor:
    """返回无量纲状态超出上下界的单边距离。"""
    supervision.validate()
    if tuple(predicted_state.shape) != tuple(supervision.state_targets.shape):
        raise E2SharedPinnError("预测状态与边界形状不一致")
    below = functional.relu(supervision.lower_bound - predicted_state)
    above = functional.relu(predicted_state - supervision.upper_bound)
    return below + above


@dataclass(frozen=True)
class E2LossBreakdown:
    """四组共用的联合目标分解。"""

    total: torch.Tensor
    detection: torch.Tensor
    state: torch.Tensor | None
    conservation: torch.Tensor | None
    boundary: torch.Tensor | None


def compose_e2_variant_loss(
    *,
    variant: str,
    detection_output: E2ModelOutput,
    physics_state: torch.Tensor,
    labels: torch.Tensor,
    supervision: E2PhysicsSupervision,
    budget: E2PinnBudget,
) -> E2LossBreakdown:
    """用独立检测批和物理批切换 E2-A/S/P/X 的监督项。"""
    contract = build_e2_variant_contract(variant)
    _validate_variant_budget(contract, budget)
    supervision.validate()
    if detection_output.logits.ndim != 2 or detection_output.logits.shape[1] != 2:
        raise E2SharedPinnError("检测头必须输出[检测批量, 2]二分类 logits")
    detection_batch_size = int(detection_output.logits.shape[0])
    if labels.shape != (detection_batch_size,) or labels.dtype != torch.long:
        raise E2SharedPinnError("检测标签必须是与检测批量等长的 long 张量")
    if tuple(physics_state.shape) != tuple(supervision.state_targets.shape):
        raise E2SharedPinnError("物理批预测状态与物理监督形状不一致")
    if torch.any((labels < 0) | (labels > 1)):
        raise E2SharedPinnError("检测标签必须为 0 或 1")
    if contract.requires_permuted_physics and supervision.provenance != "stratified_permuted":
        raise E2SharedPinnError("E2-X 必须使用已完成联合分层置换的物理监督")
    if contract.variant in {"E2-S", "E2-P"} and supervision.provenance != "aligned":
        raise E2SharedPinnError("E2-S/E2-P 必须使用样本一一对齐的真实物理监督")

    detection = functional.cross_entropy(detection_output.logits, labels)
    state = None
    conservation = None
    boundary = None
    # 中性零项使 E2-A 保留同一个可训练状态分支，但不读取任何物理真值。
    total = detection + physics_state.sum() * 0.0
    if contract.uses_state_supervision:
        state = state_supervision_loss(physics_state, supervision)
        total = total + budget.lambda_state * state
    if contract.uses_conservation:
        residual = shared_conservation_residual(physics_state, supervision)
        conservation = _masked_mean(
            residual.square(), supervision.conservation_mask, "共享守恒"
        )
        total = total + budget.lambda_conservation * conservation
    if contract.uses_boundary:
        violation = shared_boundary_violation(physics_state, supervision)
        boundary = _masked_mean(
            violation.square(), supervision.boundary_mask, "状态边界"
        )
        total = total + budget.lambda_boundary * boundary
    return E2LossBreakdown(
        total=total,
        detection=detection,
        state=state,
        conservation=conservation,
        boundary=boundary,
    )


def module_gradient_norm(
    physics_loss: torch.Tensor,
    module: torch.nn.Module,
    *,
    module_name: str,
    require_nonzero: bool,
) -> float:
    """不污染 .grad 地测量物理项到指定可训练模块的梯度。"""
    parameters = tuple(parameter for parameter in module.parameters() if parameter.requires_grad)
    if not parameters or not physics_loss.requires_grad:
        raise E2SharedPinnError(f"物理损失未连接到可训练{module_name}")
    gradients = torch.autograd.grad(
        physics_loss,
        parameters,
        retain_graph=True,
        create_graph=False,
        allow_unused=True,
    )
    squared_norm = 0.0
    for gradient in gradients:
        if gradient is not None:
            squared_norm += float(gradient.detach().float().square().sum().item())
    norm = math.sqrt(squared_norm)
    if not math.isfinite(norm):
        raise E2SharedPinnError(f"{module_name}物理梯度范数不是有限数")
    if require_nonzero and norm <= 0.0:
        raise E2SharedPinnError(f"E2-P/E2-X 的物理残差对{module_name}梯度必须非零")
    return norm


def state_head_gradient_norm(
    physics_loss: torch.Tensor,
    state_head: torch.nn.Module,
    *,
    require_nonzero: bool,
) -> float:
    """兼容旧调用的状态头梯度诊断。"""
    return module_gradient_norm(
        physics_loss,
        state_head,
        module_name="状态头",
        require_nonzero=require_nonzero,
    )


@dataclass(frozen=True)
class E2PhysicsDiagnostics:
    """E2 路线裁决所需的独立物理诊断。"""

    state_normalized_rmse: float
    unobserved_state_error: float | None
    dimensionless_residual: float
    constraint_violation_rate: float
    shared_encoder_gradient_norm: float
    state_head_gradient_norm: float


def compute_e2_physics_diagnostics(
    predicted_state: torch.Tensor,
    supervision: E2PhysicsSupervision,
    *,
    state_head_gradient_norm: float,
    shared_encoder_gradient_norm: float,
    constraint_tolerance: float,
) -> E2PhysicsDiagnostics:
    """计算状态、守恒、边界和梯度诊断，不替代检测指标。"""
    supervision.validate()
    gradient_norms = (state_head_gradient_norm, shared_encoder_gradient_norm)
    if any(not math.isfinite(value) or value < 0.0 for value in gradient_norms):
        raise E2SharedPinnError("共享编码器和状态头梯度范数必须为有限非负数")
    if not math.isfinite(constraint_tolerance) or constraint_tolerance <= 0.0:
        raise E2SharedPinnError("约束违反阈值必须为有限正数")
    with torch.no_grad():
        squared_error = (predicted_state - supervision.state_targets).square()
        evaluation_error = _masked_mean(
            squared_error, supervision.state_evaluation_mask, "状态评价"
        )
        target_energy = _masked_mean(
            supervision.state_targets.square(),
            supervision.state_evaluation_mask,
            "状态评价",
        )
        state_nrmse = torch.sqrt(evaluation_error / target_energy.clamp_min(1e-12))
        unobserved_mask = supervision.state_evaluation_mask & ~supervision.state_supervision_mask
        unobserved = (
            torch.sqrt(_masked_mean(squared_error, unobserved_mask, "未观测状态"))
            if bool(unobserved_mask.any())
            else None
        )
        residual = shared_conservation_residual(predicted_state, supervision)
        residual_rms = torch.sqrt(
            _masked_mean(residual.square(), supervision.conservation_mask, "共享守恒")
        )
        boundary_violation = shared_boundary_violation(predicted_state, supervision)
        conservation_violations = (
            residual.abs() > constraint_tolerance
        ) & supervision.conservation_mask
        boundary_violations = (
            boundary_violation > constraint_tolerance
        ) & supervision.boundary_mask
        valid_count = int(supervision.conservation_mask.sum().item()) + int(
            supervision.boundary_mask.sum().item()
        )
        if valid_count < 1:
            raise E2SharedPinnError("约束诊断没有有效位置")
        violation_rate = (
            int(conservation_violations.sum().item())
            + int(boundary_violations.sum().item())
        ) / valid_count
    return E2PhysicsDiagnostics(
        state_normalized_rmse=float(state_nrmse.item()),
        unobserved_state_error=float(unobserved.item()) if unobserved is not None else None,
        dimensionless_residual=float(residual_rms.item()),
        constraint_violation_rate=float(violation_rate),
        shared_encoder_gradient_norm=float(shared_encoder_gradient_norm),
        state_head_gradient_norm=float(state_head_gradient_norm),
    )


@dataclass(frozen=True)
class E2TrainingStepResult:
    """单次训练更新的损失和物理诊断。"""

    variant: str
    total_loss: float
    detection_loss: float
    state_loss: float | None
    conservation_loss: float | None
    boundary_loss: float | None
    diagnostics: E2PhysicsDiagnostics


class E2SharedPinnTrainer:
    """任务 4 可复用的最小单步训练器；运行循环和日志由包装器负责。"""

    def __init__(
        self,
        *,
        model: E2SharedPinnModel,
        optimizer: torch.optim.Optimizer,
        variant: str,
        budget: E2PinnBudget,
        detection_source_binding: E2DetectionSourceBinding | None = None,
    ) -> None:
        self.model = model
        self.optimizer = optimizer
        self.contract = build_e2_variant_contract(variant)
        self.budget = budget
        self.detection_source_binding = detection_source_binding
        _validate_variant_budget(self.contract, self.budget)
        if self.detection_source_binding is not None:
            self.detection_source_binding.validate()
        self.training_budget = training_budget_signature(self.model, self.budget)
        self._step_count = 0

    def train_step(
        self,
        *,
        detection_features: torch.Tensor,
        physics_features: torch.Tensor,
        labels: torch.Tensor,
        supervision: E2PhysicsSupervision,
        detection_binding: E2DetectionBatchBinding | None = None,
        physics_binding: E2PhysicsFeatureBinding | None = None,
    ) -> E2TrainingStepResult:
        """在独立检测批和辅助物理批上执行一次共享编码器联合更新。"""
        if self._step_count >= self.budget.max_steps:
            raise E2SharedPinnError("实际优化步数不得超过冻结 max_steps")
        if self._step_count == 0 and _model_weights_sha256(
            self.model
        ) != self.training_budget.initial_weights_sha256:
            raise E2SharedPinnError("训练启动前模型权重已偏离共同初始权重摘要")
        if detection_features.ndim != 2 or int(detection_features.shape[0]) != (
            self.budget.detection_batch_size
        ):
            raise E2SharedPinnError("检测批大小与冻结训练预算不一致")
        if physics_features.ndim != 2 or int(physics_features.shape[0]) != (
            self.budget.resolved_physics_batch_size
        ):
            raise E2SharedPinnError("物理批大小与冻结训练预算不一致")
        if self.detection_source_binding is None or detection_binding is None:
            raise E2SharedPinnError("正式训练必须携带冻结检测源域绑定")
        self.detection_source_binding.validate_batch(detection_binding, detection_features)
        if physics_binding is None:
            raise E2SharedPinnError("正式训练必须携带物理特征与监督顺序绑定")
        physics_binding.validate(physics_features)
        supervision.validate()
        if supervision.feature_binding_sha256 != physics_binding.binding_sha256:
            raise E2SharedPinnError("物理监督与实际特征批绑定不一致")
        if self.contract.requires_permuted_physics:
            receipt = supervision.permutation_receipt
            if receipt is None or receipt.source_sample_ids != physics_binding.sample_ids:
                raise E2SharedPinnError("E2-X 置换源顺序与物理特征样本顺序不一致")
        elif supervision.sample_ids != physics_binding.sample_ids:
            raise E2SharedPinnError("对齐物理监督与物理特征 sample_id 顺序不一致")
        self.model.train()
        self.optimizer.zero_grad(set_to_none=True)
        detection_output = self.model(detection_features)
        physics_output = self.model(physics_features)
        losses = compose_e2_variant_loss(
            variant=self.contract.variant,
            detection_output=detection_output,
            physics_state=physics_output.state,
            labels=labels,
            supervision=supervision,
            budget=self.budget,
        )
        state_gradient_norm = 0.0
        encoder_gradient_norm = 0.0
        physics_terms: list[torch.Tensor] = []
        if losses.state is not None:
            physics_terms.append(self.budget.lambda_state * losses.state)
        if losses.conservation is not None:
            physics_terms.append(self.budget.lambda_conservation * losses.conservation)
        if losses.boundary is not None:
            physics_terms.append(self.budget.lambda_boundary * losses.boundary)
        if physics_terms:
            physics_objective = sum(physics_terms[1:], start=physics_terms[0])
            state_gradient_norm = module_gradient_norm(
                physics_objective,
                self.model.state_head,
                module_name="状态头",
                require_nonzero=True,
            )
            encoder_gradient_norm = module_gradient_norm(
                physics_objective,
                self.model.encoder,
                module_name="共享编码器",
                require_nonzero=True,
            )
        losses.total.backward()
        self.optimizer.step()
        self._step_count += 1
        diagnostics = compute_e2_physics_diagnostics(
            physics_output.state.detach(),
            supervision,
            state_head_gradient_norm=state_gradient_norm,
            shared_encoder_gradient_norm=encoder_gradient_norm,
            constraint_tolerance=self.budget.constraint_tolerance,
        )
        return E2TrainingStepResult(
            variant=self.contract.variant,
            total_loss=float(losses.total.detach().item()),
            detection_loss=float(losses.detection.detach().item()),
            state_loss=float(losses.state.detach().item()) if losses.state is not None else None,
            conservation_loss=(
                float(losses.conservation.detach().item())
                if losses.conservation is not None
                else None
            ),
            boundary_loss=(
                float(losses.boundary.detach().item()) if losses.boundary is not None else None
            ),
            diagnostics=diagnostics,
        )


def assert_shared_parameter_budget(models: Mapping[str, torch.nn.Module]) -> None:
    """拒绝四组因结构变化获得不同参数预算。"""
    if set(models) != set(E2_PINN_VARIANTS):
        raise E2SharedPinnError("参数预算核验必须同时提供 E2-A/S/P/X")
    signatures = {variant: parameter_budget_signature(model) for variant, model in models.items()}
    if len(set(signatures.values())) != 1:
        raise E2SharedPinnError("E2-A/S/P/X 的结构或可训练参数预算不一致")


def assert_shared_training_budget(
    models: Mapping[str, torch.nn.Module],
    budgets: Mapping[str, E2PinnBudget],
) -> None:
    """拒绝四组使用不同初值、步数或检测/物理批量。"""
    if set(models) != set(E2_PINN_VARIANTS) or set(budgets) != set(E2_PINN_VARIANTS):
        raise E2SharedPinnError("训练预算核验必须同时提供 E2-A/S/P/X")
    signatures = {
        variant: training_budget_signature(models[variant], budgets[variant])
        for variant in E2_PINN_VARIANTS
    }
    if len(set(signatures.values())) != 1:
        raise E2SharedPinnError("E2-A/S/P/X 的初始权重或实际训练预算不一致")
