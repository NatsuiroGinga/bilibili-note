"""LSPR 双轨基线矩阵的独立模型实现。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final

import torch
from torch import nn

NEURAL_MODELS: Final[tuple[str, ...]] = (
    "leoste_1d_cnn_nearest_text",
    "dijk2026_gru",
    "dijk2026_full_attention_transformer",
    "dijk2026_bigbird",
    "dijk2026_longformer",
)


class BaselineModelError(ValueError):
    """模型配置或输入违反冻结合同。"""


@dataclass(frozen=True)
class SequenceModelConfig:
    input_size: int = 155
    hidden_size: int = 384
    num_layers: int = 6
    num_heads: int = 8
    dropout: float = 0.1
    intermediate_size: int = 1536
    maximum_sequence_length: int = 128
    bigbird_block_size: int = 16
    bigbird_random_blocks: int = 2
    longformer_attention_window: int = 32

    def validate(self) -> None:
        if self.input_size != 155:
            raise BaselineModelError("序列模型输入必须为 77 数值、77 缺失位和 1 个相对时间通道")
        if self.hidden_size % self.num_heads:
            raise BaselineModelError("隐藏维度必须能被注意力头数整除")
        if self.maximum_sequence_length != 128:
            raise BaselineModelError("Dijk 2026 模型的最大序列长度必须为 128")
        if self.longformer_attention_window <= 0 or self.longformer_attention_window % 2:
            raise BaselineModelError("Longformer 注意力窗口必须为正偶数")

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


class PerFlowInputProjection(nn.Module):
    def __init__(self, config: SequenceModelConfig) -> None:
        super().__init__()
        self.projection = nn.Sequential(
            nn.Linear(config.input_size, config.hidden_size),
            nn.LayerNorm(config.hidden_size),
            nn.GELU(),
        )

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.projection(values)


class DijkGruClassifier(nn.Module):
    """Dijk 2026 公共规模的单向 GRU 逐流分类器。"""

    def __init__(self, config: SequenceModelConfig) -> None:
        super().__init__()
        self.input_projection = PerFlowInputProjection(config)
        self.encoder = nn.GRU(
            config.hidden_size,
            config.hidden_size,
            num_layers=config.num_layers,
            dropout=config.dropout,
            batch_first=True,
        )
        self.classifier = nn.Linear(config.hidden_size, 1)

    def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
        encoded, _ = self.encoder(self.input_projection(values))
        return self.classifier(encoded).squeeze(-1).masked_fill(~valid, 0.0)


class DijkFullAttentionClassifier(nn.Module):
    """Dijk 2026 BERT 式全注意力逐流分类器。"""

    def __init__(self, config: SequenceModelConfig) -> None:
        super().__init__()
        self.input_projection = PerFlowInputProjection(config)
        self.position = nn.Parameter(
            torch.zeros(1, config.maximum_sequence_length, config.hidden_size)
        )
        layer = nn.TransformerEncoderLayer(
            d_model=config.hidden_size,
            nhead=config.num_heads,
            dim_feedforward=config.intermediate_size,
            dropout=config.dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(
            layer,
            num_layers=config.num_layers,
            enable_nested_tensor=False,
        )
        self.classifier = nn.Linear(config.hidden_size, 1)

    def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
        length = values.shape[1]
        encoded = self.input_projection(values) + self.position[:, :length]
        encoded = self.encoder(encoded, src_key_padding_mask=~valid)
        return self.classifier(encoded).squeeze(-1).masked_fill(~valid, 0.0)


class LeosteNearestTextCnnClassifier(nn.Module):
    """只保留 Leoste 正文可恢复拓扑的逐流一维卷积实现。"""

    def __init__(self, config: SequenceModelConfig) -> None:
        super().__init__()
        self.convolutions = nn.Sequential(
            nn.Conv1d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveMaxPool1d(16),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(config.dropout),
            nn.Linear(32 * 16, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

    def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
        batch, length, width = values.shape
        flattened = values.reshape(batch * length, 1, width)
        logits = self.classifier(self.convolutions(flattened)).reshape(batch, length)
        return logits.masked_fill(~valid, 0.0)


class HuggingFaceSequenceClassifier(nn.Module):
    def __init__(self, model_name: str, config: SequenceModelConfig) -> None:
        super().__init__()
        try:
            from transformers import BigBirdConfig, BigBirdModel, LongformerConfig, LongformerModel
        except ImportError as error:
            raise BaselineModelError("BigBird/Longformer 需要正式环境中的 transformers") from error
        self.model_name = model_name
        self.input_projection = PerFlowInputProjection(config)
        if model_name == "dijk2026_bigbird":
            encoder_config = BigBirdConfig(
                vocab_size=2,
                hidden_size=config.hidden_size,
                num_hidden_layers=config.num_layers,
                num_attention_heads=config.num_heads,
                intermediate_size=config.intermediate_size,
                hidden_dropout_prob=config.dropout,
                attention_probs_dropout_prob=config.dropout,
                max_position_embeddings=config.maximum_sequence_length + 2,
                block_size=config.bigbird_block_size,
                num_random_blocks=config.bigbird_random_blocks,
                attention_type="block_sparse",
            )
            self.encoder = BigBirdModel(encoder_config, add_pooling_layer=False)
        elif model_name == "dijk2026_longformer":
            encoder_config = LongformerConfig(
                vocab_size=2,
                hidden_size=config.hidden_size,
                num_hidden_layers=config.num_layers,
                num_attention_heads=config.num_heads,
                intermediate_size=config.intermediate_size,
                hidden_dropout_prob=config.dropout,
                attention_probs_dropout_prob=config.dropout,
                max_position_embeddings=config.maximum_sequence_length + 2,
                attention_window=[config.longformer_attention_window] * config.num_layers,
            )
            self.encoder = LongformerModel(encoder_config, add_pooling_layer=False)
        else:
            raise BaselineModelError(f"未知 Hugging Face 序列模型：{model_name}")
        self.classifier = nn.Linear(config.hidden_size, 1)

    def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
        encoded = self.encoder(
            inputs_embeds=self.input_projection(values),
            attention_mask=valid.to(dtype=torch.long),
            return_dict=True,
        ).last_hidden_state
        return self.classifier(encoded).squeeze(-1).masked_fill(~valid, 0.0)


def build_neural_model(model_name: str, config: SequenceModelConfig) -> nn.Module:
    config.validate()
    if model_name == "leoste_1d_cnn_nearest_text":
        return LeosteNearestTextCnnClassifier(config)
    if model_name == "dijk2026_gru":
        return DijkGruClassifier(config)
    if model_name == "dijk2026_full_attention_transformer":
        return DijkFullAttentionClassifier(config)
    if model_name in ("dijk2026_bigbird", "dijk2026_longformer"):
        return HuggingFaceSequenceClassifier(model_name, config)
    raise BaselineModelError(f"未知神经基线：{model_name}")


def trainable_parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
