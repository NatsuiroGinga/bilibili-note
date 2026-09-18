#!/usr/bin/env python3
"""T17-only DRIFT N10 缩容双支 P0/P1 先导入口。"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pyarrow.parquet as pq
import torch
from sklearn.metrics import average_precision_score, roc_auc_score
from tokenizers import Tokenizer, models, normalizers, pre_tokenizers, processors, trainers
from torch import Tensor, nn

SCHEMA_VERSION = "ch3-drift-n10-conservative-fusion-pilot-v1"
ARMS = ("c00", "dynamic", "qmf", "conservative_correction", "constant")
CHARACTERS = "abcdefghijklmnopqrstuvwxyz0123456789-."


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


@dataclass(frozen=True)
class InputPart:
    path: Path
    label: int
    expected_rows: int
    role: str


def load_config(path: Path, root: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("配置 schema_version 不匹配")
    if config.get("approved_scope") != "p0_p1_only" or config.get("screening_only") is not True:
        raise ValueError("配置未保持批准范围或 screening_only")
    if config.get("seed") != 42:
        raise ValueError("训练种子必须为 42")
    model = config["model"]
    if (model["d_model"], model["nhead"], model["num_layers"], model["dim_feedforward"]) != (128, 4, 6, 384):
        raise ValueError("缩容 profile 与冻结合同不符")
    if int(config["training"]["batch_size"]) != 1024:
        raise ValueError("batch_size 必须为 1024")
    if config["data"].get("schema") != ["domain", "label"]:
        raise ValueError("输入模式必须为 domain,label")
    if config["data"]["fit"].get("year") != "T17" or config["data"]["validation"].get("year") != "T17":
        raise ValueError("本入口只允许 T17")
    if config["pretraining"].get("tasks") != ["MTP", "TPP", "TOV"]:
        raise ValueError("预训练任务必须保留 MTP、TPP、TOV")
    if tuple(config["p1"]["arms"]) != ARMS[1:]:
        raise ValueError("P1 实验臂清单不匹配")
    if float(config["p1"]["qmf_temperature"]) != 1.0 or float(config["p1"]["qmf_regularization"]) != 0.1:
        raise ValueError("QMF 来源超参数不匹配")
    if float(config["p1"]["source_fpr"]) != 0.01 or float(config["p1"]["harm_limit"]) != 1.0:
        raise ValueError("源阈值或伤害边界不匹配")
    if config["pretraining"].get("use_bert_pretokenizer") is not False:
        raise ValueError("分词器必须保持官方默认的 use_bert_pretokenizer=false")
    if int(config["evaluation"]["ece_bins"]) != 15:
        raise ValueError("ECE 必须使用冻结的 15 分箱口径")
    required_basis = {"seed", "data_members", "model_profile", "sequence_vocabularies", "dropout", "batch_size", "learning_rate", "backbone_learning_rate", "frozen_head_fraction", "pretraining_probabilities", "checkpoint_every_io_batches", "source_fpr", "qmf_temperature", "qmf_regularization", "harm_limit", "use_bert_pretokenizer", "evaluation_per_class", "ece_bins"}
    if set(config.get("numeric_basis", {})) != required_basis:
        raise ValueError("科研数值必须有完整 numeric_basis 台账")
    if Path(config["data"]["raw_root"]).is_absolute():
        raise ValueError("raw_root 必须是项目内相对路径")
    return config


def input_parts(config: dict[str, Any], root: Path, split: str) -> tuple[InputPart, InputPart]:
    section = config["data"][split]
    raw_root = (root / config["data"]["raw_root"]).resolve()
    output: list[InputPart] = []
    for key, label in (("benign", 0), ("dga", 1)):
        item = section[key]
        path = (raw_root / item["path"]).resolve()
        if path.parent != raw_root or path.name != item["path"] or not path.name.startswith("T17_"):
            raise ValueError("输入发现仅允许显式 T17 文件名")
        output.append(InputPart(path, label, int(item["expected_rows"]), split))
    return tuple(output)  # type: ignore[return-value]


def verify_inputs(parts: tuple[InputPart, InputPart]) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for part in parts:
        if not part.path.is_file():
            raise FileNotFoundError(f"输入文件不存在：{part.path}")
        parquet = pq.ParquetFile(part.path)
        columns = parquet.schema_arrow.names
        rows = int(parquet.metadata.num_rows)
        if columns != ["domain", "label"]:
            raise ValueError(f"输入字段不匹配：{part.path}")
        if rows != part.expected_rows:
            raise ValueError(f"输入行数不匹配：{part.path}")
        receipts[str(part.path)] = {
            "role": part.role,
            "label": part.label,
            "rows": rows,
            "columns": columns,
            "sha256": sha256_file(part.path),
        }
    return receipts


def iter_part_domains(part: InputPart) -> Iterator[str]:
    for record_batch in pq.ParquetFile(part.path).iter_batches(batch_size=32768, columns=["domain", "label"]):
        frame = record_batch.to_pydict()
        if any(value != part.label for value in frame["label"]):
            raise ValueError(f"输入标签与冻结成员不匹配：{part.path}")
        yield from (str(value) for value in frame["domain"])


def iter_labeled_batches(parts: tuple[InputPart, InputPart], batch_size: int, seed: int) -> Iterator[tuple[list[str], Tensor]]:
    if batch_size <= 0 or batch_size % 2:
        raise ValueError("平衡批大小必须是正偶数")
    per_class = batch_size // 2
    benign, dga = iter_part_domains(parts[0]), iter_part_domains(parts[1])
    emitted = [0, 0]
    for index in itertools.count():
        benign_batch = list(itertools.islice(benign, per_class))
        dga_batch = list(itertools.islice(dga, per_class))
        if not benign_batch and not dga_batch:
            break
        if not benign_batch or not dga_batch or len(benign_batch) != len(dga_batch):
            raise RuntimeError("两类 T17 成员无法组成对称平衡批")
        domains = benign_batch + dga_batch
        labels = np.asarray([0] * len(benign_batch) + [1] * len(dga_batch), dtype=np.int64)
        order = np.random.default_rng(seed + index).permutation(len(domains))
        emitted[0] += len(benign_batch)
        emitted[1] += len(dga_batch)
        yield [domains[item] for item in order], torch.from_numpy(labels[order])
    if emitted != [parts[0].expected_rows, parts[1].expected_rows]:
        raise RuntimeError(f"平衡迭代成员不完整：{emitted}")


def iter_domain_batches(parts: tuple[InputPart, InputPart], batch_size: int, seed: int) -> Iterator[list[str]]:
    for domains, _ in iter_labeled_batches(parts, batch_size, seed):
        yield domains


def train_tokenizer(parts: tuple[InputPart, InputPart], output: Path, vocab_size: int) -> None:
    tokenizer = Tokenizer(models.WordPiece(unk_token="[UNK]"))
    tokenizer.normalizer = normalizers.Sequence([normalizers.NFD(), normalizers.Lowercase(), normalizers.StripAccents()])
    trainer = trainers.WordPieceTrainer(vocab_size=vocab_size, min_frequency=0, special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"])
    tokenizer.train_from_iterator(iter_domain_batches(parts, 8192, 42), trainer=trainer)
    tokenizer.post_processor = processors.TemplateProcessing(
        single="[CLS]:0 $A:0 [SEP]:0",
        special_tokens=[("[CLS]", tokenizer.token_to_id("[CLS]")), ("[SEP]", tokenizer.token_to_id("[SEP]"))],
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(output.name + ".partial")
    tokenizer.save(str(partial))
    os.replace(partial, output)


def pad_ids(token_ids: list[int], max_len: int) -> list[int]:
    values = [2, *token_ids[: max_len - 2], 3]
    return values + [0] * (max_len - len(values))


def encode_char(domains: list[str], max_len: int, device: torch.device) -> Tensor:
    return encode_char_cpu(domains, max_len).to(device, non_blocking=device.type == "cuda")


def encode_char_cpu(domains: list[str], max_len: int) -> Tensor:
    mapping = {char: index + 5 for index, char in enumerate(CHARACTERS)}
    values = [pad_ids([mapping.get(char, 1) for char in domain.lower()], max_len) for domain in domains]
    return torch.tensor(values, dtype=torch.long)


def encode_subword(domains: list[str], tokenizer: Tokenizer, max_len: int, device: torch.device) -> Tensor:
    return encode_subword_cpu(domains, tokenizer, max_len).to(device, non_blocking=device.type == "cuda")


def encode_subword_cpu(domains: list[str], tokenizer: Tokenizer, max_len: int) -> Tensor:
    values = [pad_ids(encoding.ids, max_len) for encoding in tokenizer.encode_batch([domain.lower() for domain in domains], add_special_tokens=False)]
    return torch.tensor(values, dtype=torch.long)


class PretrainedBranch(nn.Module):
    def __init__(self, vocab_size: int, model: dict[str, Any], max_len: int) -> None:
        super().__init__()
        width = int(model["d_model"])
        self.padding_idx = 0
        self.embedding = nn.Embedding(vocab_size, width, padding_idx=self.padding_idx)
        self.position = nn.Embedding(max_len, width)
        layer = nn.TransformerEncoderLayer(
            d_model=width, nhead=int(model["nhead"]), dim_feedforward=int(model["dim_feedforward"]),
            dropout=float(model["dropout"]), batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=int(model["num_layers"]))
        self.dropout = nn.Dropout(float(model["dropout"]))
        self.mtp_head = nn.Linear(width, vocab_size)
        self.tpp_head = nn.Linear(width, vocab_size)
        self.tov_head = nn.Linear(width * 2, 2)
        nn.init.xavier_normal_(self.embedding.weight)
        nn.init.xavier_normal_(self.position.weight)

    def encoded(self, input_ids: Tensor) -> tuple[Tensor, Tensor]:
        positions = torch.arange(input_ids.shape[1], device=input_ids.device).unsqueeze(0)
        padding = input_ids.eq(self.padding_idx)
        hidden = self.embedding(input_ids) + self.position(positions)
        hidden = self.dropout(self.encoder(hidden, src_key_padding_mask=padding))
        return hidden.masked_fill(padding.unsqueeze(-1), 0.0), padding

    def pooled(self, input_ids: Tensor) -> Tensor:
        hidden, padding = self.encoded(input_ids)
        valid = (~padding).unsqueeze(-1)
        mean = hidden.sum(dim=1) / valid.sum(dim=1).clamp_min(1)
        maximum = hidden.masked_fill(~valid, -1e9).max(dim=1).values
        return torch.cat((maximum, mean), dim=1)

    def forward(self, input_ids: Tensor, task: str) -> Tensor:
        hidden, padding = self.encoded(input_ids)
        if task == "MTP":
            return self.mtp_head(hidden)
        if task == "TPP":
            return self.tpp_head(hidden)
        if task == "TOV":
            valid = (~padding).unsqueeze(-1)
            mean = hidden.sum(dim=1) / valid.sum(dim=1).clamp_min(1)
            maximum = hidden.masked_fill(~valid, -1e9).max(dim=1).values
            return self.tov_head(torch.cat((maximum, mean), dim=1))
        raise ValueError("未知预训练任务")


class EncoderBranch(nn.Module):
    def __init__(self, source: PretrainedBranch) -> None:
        super().__init__()
        self.padding_idx = source.padding_idx
        self.embedding = source.embedding
        self.position = source.position
        self.encoder = source.encoder
        self.dropout = source.dropout

    def pooled(self, input_ids: Tensor) -> Tensor:
        positions = torch.arange(input_ids.shape[1], device=input_ids.device).unsqueeze(0)
        padding = input_ids.eq(self.padding_idx)
        hidden = self.dropout(self.encoder(self.embedding(input_ids) + self.position(positions), src_key_padding_mask=padding))
        valid = (~padding).unsqueeze(-1)
        mean = hidden.masked_fill(~valid, 0.0).sum(dim=1) / valid.sum(dim=1).clamp_min(1)
        maximum = hidden.masked_fill(~valid, -1e9).max(dim=1).values
        return torch.cat((maximum, mean), dim=1)


class StaticDual(nn.Module):
    def __init__(self, token: PretrainedBranch, char: PretrainedBranch, width: int, dropout: float) -> None:
        super().__init__()
        self.token = token
        self.char = char
        self.classifier = nn.Sequential(nn.Dropout(dropout), nn.Linear(width * 4, width * 2), nn.ReLU(), nn.Dropout(dropout), nn.Linear(width * 2, 2))

    def encode_branches(self, input_ids_t: Tensor, input_ids_c: Tensor) -> tuple[Tensor, Tensor]:
        return self.token.pooled(input_ids_t), self.char.pooled(input_ids_c)

    def static_logits(self, token_feature: Tensor, char_feature: Tensor) -> Tensor:
        return self.classifier(torch.cat((token_feature, char_feature), dim=1))

    def forward(self, input_ids_t: Tensor, input_ids_c: Tensor) -> Tensor:
        token_feature, char_feature = self.encode_branches(input_ids_t, input_ids_c)
        return self.static_logits(token_feature, char_feature)

    def set_backbone_freezing(self, freeze: bool) -> None:
        for module in (self.token.embedding, self.token.position, self.token.encoder, self.char.embedding, self.char.position, self.char.encoder):
            for parameter in module.parameters():
                parameter.requires_grad = not freeze


class FusionAdapter(nn.Module):
    def __init__(self, width: int) -> None:
        super().__init__()
        self.token_head = nn.Linear(width * 2, 2)
        self.char_head = nn.Linear(width * 2, 2)
        self.gate = nn.Linear(4, 3)

    def forward(self, token_feature: Tensor, char_feature: Tensor, baseline_logits: Tensor, constant: bool) -> tuple[Tensor, dict[str, Tensor]]:
        token_logits = self.token_head(token_feature)
        char_logits = self.char_head(char_feature)
        quality = torch.stack((-torch.logsumexp(token_logits, dim=1), -torch.logsumexp(char_logits, dim=1), (token_logits[:, 1] - token_logits[:, 0]).abs(), (char_logits[:, 1] - char_logits[:, 0]).abs()), dim=1)
        gate_values = self.gate(torch.zeros_like(quality) if constant else quality)
        weights = torch.softmax(gate_values[:, :2], dim=1)
        deviation = torch.sigmoid(gate_values[:, 2:3])
        weighted_branch_logits = weights[:, :1] * token_logits + weights[:, 1:] * char_logits
        residual = weighted_branch_logits - baseline_logits
        logits = baseline_logits + deviation * residual
        return logits, {"branch_weights": weights, "deviation_strength": deviation, "residual": residual, "token_logits": token_logits, "char_logits": char_logits, "quality": quality}


def fusion_logits(token_feature: Tensor, char_feature: Tensor, baseline_logits: Tensor, mode: str, adapter: FusionAdapter) -> tuple[Tensor, dict[str, Tensor]]:
    if mode not in ARMS[1:]:
        raise ValueError("动态融合模式不合法")
    return adapter(token_feature, char_feature, baseline_logits, constant=mode == "constant")


def correction_risk(candidate_logits: Tensor, baseline_logits: Tensor, labels: Tensor, source_threshold: np.float32) -> dict[str, float]:
    candidate = candidate_logits.float()[:, 1] - candidate_logits.float()[:, 0]
    baseline = (baseline_logits[:, 1] - baseline_logits[:, 0]).float()
    output: dict[str, float] = {}
    for label, name, wrong, margin in ((0, "negative", baseline >= source_threshold, candidate - source_threshold), (1, "positive", baseline < source_threshold, source_threshold - candidate)):
        subset = labels.eq(label)
        base_error = wrong & subset
        base_ok = ~wrong & subset
        baseline_margin = (baseline - source_threshold) if label == 0 else (source_threshold - baseline)
        error_denominator = nn.functional.softplus(baseline_margin[base_error]).mean()
        harm_denominator = nn.functional.softplus(baseline_margin[base_ok]).mean()
        output[f"e_{name}"] = float((nn.functional.softplus(margin[base_error]).mean() / error_denominator).cpu()) if bool(base_error.any()) else math.nan
        output[f"h_{name}"] = float((nn.functional.softplus(margin[base_ok]).mean() / harm_denominator).cpu()) if bool(base_ok.any()) else math.nan
        output[f"baseline_errors_{name}"] = int(base_error.sum().item())
        output[f"baseline_correct_{name}"] = int(base_ok.sum().item())
    return output


def build_static(config: dict[str, Any], tokenizer_size: int) -> StaticDual:
    model = config["model"]
    token = PretrainedBranch(tokenizer_size, model, int(model["max_len_token"]))
    char = PretrainedBranch(int(model["vocab_size_char"]), model, int(model["max_len_char"]))
    return StaticDual(token, char, int(model["d_model"]), float(model["dropout"]))


def pretraining_views(ids: Tensor, seed: int, ignore_index: int, mask_ratio: float, shuffle_probability: float) -> tuple[Tensor, Tensor, Tensor, Tensor, Tensor, Tensor]:
    rng = np.random.default_rng(seed)
    source = ids.detach().cpu().numpy()
    mtp_input, mtp_target = source.copy(), np.full(source.shape, ignore_index, dtype=np.int64)
    tpp_input, tpp_target = source.copy(), source.copy()
    tov_input, tov_target = source.copy(), np.zeros(source.shape[0], dtype=np.int64)
    for row in range(source.shape[0]):
        active = np.flatnonzero(source[row] != 0)[1:-1]
        tpp_target[row, source[row] == 0] = ignore_index
        if active.size <= 1:
            continue
        chosen = rng.choice(active, size=max(1, int(active.size * mask_ratio)), replace=False)
        mtp_target[row, chosen] = source[row, chosen]
        mtp_input[row, chosen] = 4
        permutation = rng.permutation(active)
        tpp_input[row, permutation] = source[row, active]
        if rng.random() < shuffle_probability:
            tov_input[row, active] = source[row, rng.permutation(active)]
            tov_target[row] = 1
    device = ids.device
    return tuple(torch.as_tensor(value, device=device) for value in (mtp_input, mtp_target, tpp_input, tpp_target, tov_input, tov_target))  # type: ignore[return-value]


def device_for_run() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def save_checkpoint(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    torch.save(value, partial)
    os.replace(partial, path)


def load_checkpoint(path: Path) -> dict[str, Any]:
    return torch.load(path, map_location="cpu", weights_only=False)


def checkpoint_interval(config: dict[str, Any]) -> int:
    return 32768 // int(config["training"]["batch_size"]) * int(config["training"]["checkpoint_every_io_batches"])


def verify_checkpoint_identity(state: dict[str, Any], identity: dict[str, str]) -> None:
    if any(state.get(key) != value for key, value in identity.items()):
        raise ValueError("断点的配置或代码哈希不匹配")


def capture_rng_state() -> dict[str, Any]:
    return {"python": random.getstate(), "numpy": np.random.get_state(), "torch_cpu": torch.get_rng_state(), "torch_cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None}


def restore_rng_state(state: dict[str, Any]) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch_cpu"])
    if torch.cuda.is_available() and state.get("torch_cuda") is not None:
        torch.cuda.set_rng_state_all(state["torch_cuda"])


def save_training_checkpoint(path: Path, value: dict[str, Any], identity: dict[str, str]) -> None:
    save_checkpoint(path, {**value, **identity, "rng_state": capture_rng_state()})


def train_pretraining_branch(branch: PretrainedBranch, kind: str, tokenizer: Tokenizer | None, config: dict[str, Any], parts: tuple[InputPart, InputPart], device: torch.device, checkpoint: Path, resume_state: dict[str, Any] | None, identity: dict[str, str]) -> dict[str, Any]:
    training = config["training"]
    settings = config["pretraining"]
    optimizer = torch.optim.Adam(branch.parameters(), lr=float(training["learning_rate"]))
    completed = -1
    seen = 0
    if resume_state is not None:
        verify_checkpoint_identity(resume_state, identity)
        restore_rng_state(resume_state["rng_state"])
        branch.load_state_dict(resume_state["branch"], strict=True)
        optimizer.load_state_dict(resume_state["optimizer"])
        completed, seen = int(resume_state["completed_batch"]), int(resume_state["examples_seen"])
    branch.train()
    started = time.monotonic()
    losses: list[float] = []
    for index, domains in enumerate(iter_domain_batches(parts, int(training["batch_size"]), int(config["seed"]))):
        if index <= completed:
            continue
        ids_cpu = encode_char_cpu(domains, int(config["model"]["max_len_char"])) if kind == "char" else encode_subword_cpu(domains, tokenizer, int(config["model"]["max_len_token"]))  # type: ignore[arg-type]
        views_cpu = pretraining_views(ids_cpu, int(config["seed"]) + index, int(settings["ignore_index"]), float(settings["mask_ratio"]), float(settings["shuffle_probability"]))
        views = tuple((value.pin_memory() if device.type == "cuda" else value).to(device, non_blocking=device.type == "cuda") for value in views_cpu)
        optimizer.zero_grad(set_to_none=True)
        autocast = device.type == "cuda" and bool(training["cuda_bf16_autocast"])
        with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=autocast):
            loss = nn.functional.cross_entropy(branch(views[0], "MTP").flatten(0, 1), views[1].flatten(), ignore_index=int(settings["ignore_index"]))
            loss = loss + nn.functional.cross_entropy(branch(views[2], "TPP").flatten(0, 1), views[3].flatten(), ignore_index=int(settings["ignore_index"]))
            loss = loss + nn.functional.cross_entropy(branch(views[4], "TOV"), views[5])
        loss.backward()
        torch.nn.utils.clip_grad_norm_(branch.parameters(), max_norm=1.0)
        optimizer.step()
        seen += len(domains)
        losses.append(float(loss.detach().cpu()))
        if (index + 1) % checkpoint_interval(config) == 0:
            save_training_checkpoint(checkpoint, {"phase": f"pretrain_{kind}", "branch": branch.state_dict(), "optimizer": optimizer.state_dict(), "completed_batch": index, "examples_seen": seen}, identity)
            print(json.dumps({"phase": f"pretrain_{kind}", "io_batches": (index + 1) // checkpoint_interval(config), "examples_seen": seen}, ensure_ascii=False), flush=True)
    if losses:
        save_training_checkpoint(checkpoint, {"phase": f"pretrain_{kind}", "branch": branch.state_dict(), "optimizer": optimizer.state_dict(), "completed_batch": index, "examples_seen": seen}, identity)
    expected = sum(item.expected_rows for item in parts)
    if seen != expected:
        raise RuntimeError(f"{kind} 预训练成员遍历不完整：{seen} != {expected}")
    wall_seconds = time.monotonic() - started
    return {"examples_seen": seen, "batches": len(losses), "mean_loss": float(np.mean(losses)) if losses else None, "pretraining_parameter_count": sum(parameter.numel() for parameter in branch.parameters()), "wall_seconds": wall_seconds, "throughput_examples_per_second": seen / wall_seconds if wall_seconds else None}


def train_static(model: StaticDual, tokenizer: Tokenizer, config: dict[str, Any], parts: tuple[InputPart, InputPart], device: torch.device, checkpoint: Path, resume_state: dict[str, Any] | None, identity: dict[str, str]) -> dict[str, Any]:
    training = config["training"]
    optimizer = torch.optim.Adam([
        {"params": model.classifier.parameters(), "lr": float(training["learning_rate"])},
        {"params": itertools.chain(model.token.parameters(), model.char.parameters()), "lr": float(training["backbone_learning_rate"])},
    ])
    completed, seen = -1, 0
    if resume_state is not None:
        verify_checkpoint_identity(resume_state, identity)
        restore_rng_state(resume_state["rng_state"])
        model.load_state_dict(resume_state["static_model"], strict=True)
        optimizer.load_state_dict(resume_state["optimizer"])
        completed, seen = int(resume_state["completed_batch"]), int(resume_state["examples_seen"])
    model.train()
    started = time.monotonic()
    losses: list[float] = []
    freeze_until = sum(item.expected_rows for item in parts) * float(training["frozen_head_fraction"])
    for index, (domains, labels) in enumerate(iter_labeled_batches(parts, int(training["batch_size"]), int(config["seed"]))):
        if index <= completed:
            continue
        model.set_backbone_freezing(seen < freeze_until)
        token_ids = encode_subword(domains, tokenizer, int(config["model"]["max_len_token"]), device)
        char_ids = encode_char(domains, int(config["model"]["max_len_char"]), device)
        labels = labels.to(device)
        optimizer.zero_grad(set_to_none=True)
        autocast = device.type == "cuda" and bool(training["cuda_bf16_autocast"])
        with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=autocast):
            loss = nn.functional.cross_entropy(model(token_ids, char_ids), labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        seen += len(domains)
        losses.append(float(loss.detach().cpu()))
        if (index + 1) % checkpoint_interval(config) == 0:
            save_training_checkpoint(checkpoint, {"phase": "static", "static_model": model.state_dict(), "optimizer": optimizer.state_dict(), "completed_batch": index, "examples_seen": seen}, identity)
            print(json.dumps({"phase": "static", "io_batches": (index + 1) // checkpoint_interval(config), "examples_seen": seen}, ensure_ascii=False), flush=True)
    if losses:
        save_training_checkpoint(checkpoint, {"phase": "static", "static_model": model.state_dict(), "optimizer": optimizer.state_dict(), "completed_batch": index, "examples_seen": seen}, identity)
    expected = sum(item.expected_rows for item in parts)
    if seen != expected:
        raise RuntimeError(f"静态微调成员遍历不完整：{seen} != {expected}")
    wall_seconds = time.monotonic() - started
    return {"examples_seen": seen, "batches": len(losses), "mean_loss": float(np.mean(losses)) if losses else None, "wall_seconds": wall_seconds, "throughput_examples_per_second": seen / wall_seconds if wall_seconds else None}


def parameter_receipt(module: nn.Module) -> list[dict[str, Any]]:
    return [{"name": name, "shape": list(parameter.shape), "count": parameter.numel()} for name, parameter in module.named_parameters()]


def resource_receipt() -> dict[str, Any]:
    if torch.cuda.is_available():
        return {"peak_allocated_bytes": int(torch.cuda.max_memory_allocated()), "peak_reserved_bytes": int(torch.cuda.max_memory_reserved())}
    return {"peak_allocated_bytes": None, "peak_reserved_bytes": None}


def binary_metrics(logits: Tensor, labels: Tensor, source_threshold: np.float32, ece_bins: int) -> dict[str, Any]:
    values = logits.detach().cpu()
    target = labels.detach().cpu().numpy().astype(np.int64)
    scores = (values[:, 1] - values[:, 0]).float().numpy()
    probabilities = torch.softmax(values, dim=1)[:, 1].numpy().astype(np.float32, copy=False)
    if set(np.unique(target)) != {0, 1}:
        raise ValueError("源验证指标必须同时包含两类")
    def rates(predicted: np.ndarray) -> dict[str, float]:
        negative, positive = target == 0, target == 1
        return {"fpr": float(predicted[negative].mean()), "fnr": float((~predicted[positive]).mean()), "tpr": float(predicted[positive].mean())}
    boundaries = np.linspace(0.0, 1.0, ece_bins + 1)
    ece = 0.0
    for index in range(ece_bins):
        lower, upper = boundaries[index], boundaries[index + 1]
        in_bin = (probabilities >= lower) & ((probabilities <= upper) if index == ece_bins - 1 else (probabilities < upper))
        if in_bin.any():
            ece += float(in_bin.mean() * abs(probabilities[in_bin].mean() - target[in_bin].mean()))
    return {
        "auroc": float(roc_auc_score(target, scores)),
        "average_precision": float(average_precision_score(target, scores)),
        "default_threshold": {"logit_difference": 0.0, **rates(scores >= np.float32(0.0))},
        "source_fpr_threshold": {"logit_difference_float32": float(source_threshold), **rates(scores >= source_threshold)},
        "brier": float(np.mean((probabilities - target) ** 2)),
        "ece": {"bins": ece_bins, "value": ece},
    }


def calibrate_source(model: StaticDual, tokenizer: Tokenizer, config: dict[str, Any], parts: tuple[InputPart, InputPart], device: torch.device, input_hashes: dict[str, Any], receipt_path: Path) -> dict[str, Any]:
    benign_scores: list[np.float32] = []
    all_scores: list[np.float32] = []
    all_labels: list[int] = []
    position = 0
    model.eval()
    partial = receipt_path.with_name(receipt_path.name + ".partial")
    with partial.open("w", encoding="utf-8") as receipt, torch.inference_mode():
        for domains, labels in iter_labeled_batches(parts, int(config["training"]["batch_size"]), int(config["seed"])):
            token_ids = encode_subword(domains, tokenizer, int(config["model"]["max_len_token"]), device)
            char_ids = encode_char(domains, int(config["model"]["max_len_char"]), device)
            logits = model(token_ids, char_ids)
            probabilities = torch.softmax(logits, dim=1)[:, 1].detach().to(torch.float32).cpu().numpy()
            scores = (logits[:, 1] - logits[:, 0]).detach().to(torch.float32).cpu().numpy()
            for domain, label, probability, score in zip(domains, labels.tolist(), probabilities, scores, strict=True):
                if label == 0:
                    benign_scores.append(np.float32(score))
                all_scores.append(np.float32(score))
                all_labels.append(int(label))
                receipt.write(json.dumps({"sample_key_sha256": hashlib.sha256(f"{position}:{domain}".encode("utf-8")).hexdigest(), "sequence_position": position, "probability_float32": float(np.float32(probability)), "logit_difference_float32": float(np.float32(score)), "score_dtype": "float32"}, ensure_ascii=False) + "\n")
                position += 1
    os.replace(partial, receipt_path)
    scores = np.sort(np.asarray(benign_scores, dtype=np.float32))[::-1]
    permitted = int(math.floor(len(scores) * float(config["p1"]["source_fpr"])))
    raw = np.float32(scores[max(permitted - 1, 0)])
    threshold = np.nextafter(raw, np.float32(np.inf), dtype=np.float32)
    benign_values = np.asarray(benign_scores, dtype=np.float32)
    above = int(np.sum(benign_values >= threshold, dtype=np.int64))
    tied = int(np.sum(benign_values == raw, dtype=np.int64))
    score_tensor = torch.tensor(np.asarray(all_scores, dtype=np.float32))
    synthetic_logits = torch.stack((torch.zeros_like(score_tensor), score_tensor), dim=1)
    metrics = binary_metrics(synthetic_logits, torch.tensor(all_labels, dtype=torch.long), threshold, int(config["evaluation"]["ece_bins"]))
    aggregate = {"threshold_float32": float(threshold), "threshold_space": "logit_difference", "threshold_dtype": "float32", "fpr_target": float(config["p1"]["source_fpr"]), "benign_rows": len(benign_scores), "allowed_above": permitted, "actual_above": above, "tie_group_count": tied, "prediction_rows": position, "threshold_receipt_sha256": sha256_file(receipt_path), "metrics": metrics}
    aggregate["input_hashes"] = input_hashes
    aggregate_hash = hashlib.sha256(json.dumps(aggregate, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    aggregate["aggregate_sha256"] = aggregate_hash
    aggregate["result_sha256"] = aggregate_hash
    aggregate["interpretation_boundary"] = "逐样本阈值收据仅受控保存样本键、位置、float32概率、float32 logit差和总哈希；标签由冻结成员清单恢复，不与 QMF 历史损失混同，也不构成论文结果。"
    return aggregate


def qmf_objective(candidate_logits: Tensor, token_logits: Tensor, char_logits: Tensor, branch_weights: Tensor, labels: Tensor, temperature: float, regularization: float) -> Tensor:
    fusion_loss = nn.functional.cross_entropy(candidate_logits, labels, reduction="none")
    token_loss = nn.functional.cross_entropy(token_logits, labels, reduction="none")
    char_loss = nn.functional.cross_entropy(char_logits, labels, reduction="none")
    token_energy = -torch.logsumexp(token_logits / temperature, dim=1)
    char_energy = -torch.logsumexp(char_logits / temperature, dim=1)
    energy_scale = torch.softmax(torch.stack((-token_energy, -char_energy), dim=1), dim=1)
    weighted_branch_loss = energy_scale[:, 0] * token_loss + energy_scale[:, 1] * char_loss
    token_covariance = ((branch_weights[:, 0] - branch_weights[:, 0].mean()) * (token_loss - token_loss.mean())).mean()
    char_covariance = ((branch_weights[:, 1] - branch_weights[:, 1].mean()) * (char_loss - char_loss.mean())).mean()
    positive_covariance_penalty = torch.relu(token_covariance) + torch.relu(char_covariance)
    return fusion_loss.mean() + weighted_branch_loss.mean() + regularization * positive_covariance_penalty


def m1_objective(candidate_logits: Tensor, baseline_logits: Tensor, labels: Tensor, threshold: np.float32) -> tuple[Tensor | None, dict[str, float]]:
    candidate = candidate_logits.float()[:, 1] - candidate_logits.float()[:, 0]
    baseline = (baseline_logits[:, 1] - baseline_logits[:, 0]).float()
    remaining_terms: list[Tensor] = []
    activity: dict[str, float] = {"empty_negative": 0.0, "empty_positive": 0.0, "empty_both": 0.0}
    for label, name, baseline_wrong, margin in ((0, "negative", baseline >= threshold, candidate - threshold), (1, "positive", baseline < threshold, threshold - candidate)):
        error_subset = labels.eq(label) & baseline_wrong
        baseline_margin = (baseline - threshold) if label == 0 else (threshold - baseline)
        if not bool(error_subset.any()):
            activity[f"empty_{name}"] = 1.0
        else:
            denominator = nn.functional.softplus(baseline_margin[error_subset]).mean().detach()
            remaining = nn.functional.softplus(margin[error_subset]).mean() / denominator
            remaining_terms.append(remaining)
            activity[f"remaining_{name}"] = float(remaining.detach().cpu())
    if not remaining_terms:
        activity["empty_both"] = 1.0
        return None, activity
    objective = torch.stack(remaining_terms).mean()
    activity["remaining_objective"] = float(objective.detach().cpu())
    return objective, activity


def train_adapter(static: StaticDual, adapter: FusionAdapter, mode: str, tokenizer: Tokenizer, config: dict[str, Any], parts: tuple[InputPart, InputPart], threshold: float, device: torch.device, checkpoint: Path, resume_state: dict[str, Any] | None, identity: dict[str, str]) -> dict[str, Any]:
    optimizer = torch.optim.Adam(adapter.parameters(), lr=float(config["training"]["learning_rate"]))
    completed, seen = -1, 0
    m1_activity: dict[str, float] = {}
    if resume_state is not None:
        verify_checkpoint_identity(resume_state, identity)
        restore_rng_state(resume_state["rng_state"])
        adapter.load_state_dict(resume_state["adapter"], strict=True)
        optimizer.load_state_dict(resume_state["optimizer"])
        completed, seen = int(resume_state["completed_batch"]), int(resume_state["examples_seen"])
        m1_activity.update(resume_state.get("m1_training_activity", {}))
    static.eval()
    for parameter in static.parameters():
        parameter.requires_grad = False
    adapter.train()
    started = time.monotonic()
    losses: list[float] = []
    skipped = 0
    for index, (domains, labels) in enumerate(iter_labeled_batches(parts, int(config["training"]["batch_size"]), int(config["seed"]))):
        if index <= completed:
            continue
        token_ids = encode_subword(domains, tokenizer, int(config["model"]["max_len_token"]), device)
        char_ids = encode_char(domains, int(config["model"]["max_len_char"]), device)
        labels = labels.to(device)
        with torch.inference_mode(), torch.autocast(device_type=device.type, enabled=False):
            token_feature, char_feature = static.encode_branches(token_ids, char_ids)
            baseline_logits = static.static_logits(token_feature, char_feature)
        autocast = device.type == "cuda" and bool(config["training"]["cuda_bf16_autocast"])
        with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=autocast):
            candidate_logits, fusion_diagnostics = fusion_logits(token_feature, char_feature, baseline_logits, mode, adapter)
            if mode == "qmf":
                loss: Tensor | None = qmf_objective(candidate_logits, fusion_diagnostics["token_logits"], fusion_diagnostics["char_logits"], fusion_diagnostics["branch_weights"], labels, float(config["p1"]["qmf_temperature"]), float(config["p1"]["qmf_regularization"]))
            elif mode == "conservative_correction":
                loss, batch_activity = m1_objective(candidate_logits, baseline_logits, labels, threshold)
                for key, value in batch_activity.items():
                    m1_activity[key] = m1_activity.get(key, 0.0) + value
            else:
                loss = nn.functional.cross_entropy(candidate_logits, labels)
        if loss is None:
            skipped += 1
            seen += len(domains)
            if (index + 1) % checkpoint_interval(config) == 0:
                save_training_checkpoint(checkpoint, {"phase": "p1", "adapter": adapter.state_dict(), "optimizer": optimizer.state_dict(), "completed_batch": index, "examples_seen": seen, "m1_training_activity": m1_activity}, identity)
                print(json.dumps({"phase": "p1", "arm": mode, "io_batches": (index + 1) // checkpoint_interval(config), "examples_seen": seen, "skipped_updates": skipped}, ensure_ascii=False), flush=True)
            continue
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(adapter.parameters(), max_norm=1.0)
        optimizer.step()
        seen += len(domains)
        losses.append(float(loss.detach().cpu()))
        if (index + 1) % checkpoint_interval(config) == 0:
            save_training_checkpoint(checkpoint, {"phase": "p1", "adapter": adapter.state_dict(), "optimizer": optimizer.state_dict(), "completed_batch": index, "examples_seen": seen, "m1_training_activity": m1_activity}, identity)
            print(json.dumps({"phase": "p1", "arm": mode, "io_batches": (index + 1) // checkpoint_interval(config), "examples_seen": seen, "skipped_updates": skipped}, ensure_ascii=False), flush=True)
    if losses or skipped:
        save_training_checkpoint(checkpoint, {"phase": "p1", "adapter": adapter.state_dict(), "optimizer": optimizer.state_dict(), "completed_batch": index, "examples_seen": seen, "m1_training_activity": m1_activity}, identity)
    expected = sum(item.expected_rows for item in parts)
    if seen != expected:
        raise RuntimeError(f"P1 成员遍历不完整：{seen} != {expected}")
    wall_seconds = time.monotonic() - started
    return {"examples_seen": seen, "updates": len(losses), "skipped_updates": skipped, "mean_loss": float(np.mean(losses)) if losses else None, "m1_training_activity": m1_activity if mode == "conservative_correction" else None, "precision": {"baseline_static_forward": "float32", "gate_autocast": "bfloat16" if device.type == "cuda" and bool(config["training"]["cuda_bf16_autocast"]) else "float32"}, "wall_seconds": wall_seconds, "throughput_examples_per_second": seen / wall_seconds if wall_seconds else None}


def validate_adapter(static: StaticDual, adapter: FusionAdapter, mode: str, tokenizer: Tokenizer, config: dict[str, Any], parts: tuple[InputPart, InputPart], threshold: float, device: torch.device) -> dict[str, Any]:
    static.eval()
    adapter.eval()
    base_logits: list[Tensor] = []
    candidate_logits: list[Tensor] = []
    labels_all: list[Tensor] = []
    gate_entropy: list[float] = []
    residual_magnitude: list[float] = []
    with torch.inference_mode():
        for domains, labels in iter_labeled_batches(parts, int(config["training"]["batch_size"]), int(config["seed"])):
            token_ids = encode_subword(domains, tokenizer, int(config["model"]["max_len_token"]), device)
            char_ids = encode_char(domains, int(config["model"]["max_len_char"]), device)
            token_feature, char_feature = static.encode_branches(token_ids, char_ids)
            baseline = static.static_logits(token_feature, char_feature)
            candidate, diagnostics = fusion_logits(token_feature, char_feature, baseline, mode, adapter)
            base_logits.append(baseline.cpu())
            candidate_logits.append(candidate.cpu())
            labels_all.append(labels)
            weights = diagnostics["branch_weights"]
            gate_entropy.append(float((-(weights * weights.clamp_min(1e-12).log()).sum(dim=1).mean()).cpu()))
            residual_magnitude.append(float(diagnostics["residual"].abs().mean().cpu()))
    baseline = torch.cat(base_logits)
    candidate = torch.cat(candidate_logits)
    labels = torch.cat(labels_all)
    if labels.numel() != sum(item.expected_rows for item in parts):
        raise RuntimeError("T17 验证成员未完整遍历")
    risks = correction_risk(candidate, baseline, labels, threshold)
    harms_ok = risks["h_negative"] <= float(config["p1"]["harm_limit"]) and risks["h_positive"] <= float(config["p1"]["harm_limit"])
    return {"source_threshold": threshold, "correction": risks, "h_guardrail_passed": harms_ok, "metrics": binary_metrics(candidate, labels, threshold, int(config["evaluation"]["ece_bins"])), "mechanism_activity": {"mean_gate_entropy": float(np.mean(gate_entropy)), "mean_residual_magnitude": float(np.mean(residual_magnitude))}}


def common_result(config: dict[str, Any], args: argparse.Namespace, input_hashes: dict[str, Any], config_hash: str, script_hash: str, checkpoint: Path, started: float) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION, "status": "completed", "run_identity": f"{config['run_identity']}-{args.stage}-{args.arm}",
        "screening_only": True, "approved_scope": "p0_p1_only", "stage": args.stage, "arm": args.arm, "seed": 42,
        "data_revision": config["data_revision"], "input_hashes": input_hashes, "code_hashes": {"runner": script_hash},
        "config_hash": config_hash, "checkpoint_hash": sha256_file(checkpoint),
        "time_roles": config["time_roles"], "source_threshold": None, "metrics_by_year": {}, "conditional_metrics": {},
        "calibration": {}, "mechanism_activity": {}, "runtime": {"wall_seconds": time.monotonic() - started, "selected_batch_size": int(config["training"]["batch_size"]), "resource_profile": config["training"]["resource_profile"], "resource_contention": bool(config["training"]["resource_contention"]), "device": str(device_for_run()), "resources": resource_receipt()},
        "interpretation_boundary": config["interpretation_boundary"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--stage", required=True, choices=("p0_c00", "p1_gate"))
    parser.add_argument("--arm", required=True, choices=ARMS)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if (args.stage == "p0_c00") != (args.arm == "c00"):
        raise ValueError("P0 只接受 c00，P1 只接受四个门臂")
    root = args.project_root.resolve()
    config = load_config(args.config.resolve(), root)
    run_root = args.run_dir.resolve()
    stage_dir = run_root / args.stage if args.stage == "p0_c00" else run_root / args.stage / args.arm
    checkpoint = stage_dir / "checkpoint.pt"
    started = time.monotonic()
    config_hash, script_hash = sha256_file(args.config.resolve()), sha256_file(Path(__file__).resolve())
    identity = {"config_hash": config_hash, "script_hash": script_hash}
    torch.set_float32_matmul_precision("high")
    fit_parts, validation_parts = input_parts(config, root, "fit"), input_parts(config, root, "validation")
    input_hashes = {"fit": verify_inputs(fit_parts), "validation": verify_inputs(validation_parts)}
    status_path = stage_dir / "status.json"
    try:
        if checkpoint.exists() and not args.resume:
            raise FileExistsError("已有检查点；只允许使用 --resume 继续同一身份")
        stage_dir.mkdir(parents=True, exist_ok=True)
        atomic_json(status_path, {"status": "running", "run_identity": f"{config['run_identity']}-{args.stage}-{args.arm}", "stage": args.stage, "arm": args.arm, "config_hash": config_hash, "script_hash": script_hash, "input_hashes": input_hashes})
        atomic_json(stage_dir / "effective-config.json", {"config": config, "stage": args.stage, "arm": args.arm, "config_hash": config_hash, "script_hash": script_hash})
        atomic_json(stage_dir / "manifest.json", {"run_identity": f"{config['run_identity']}-{args.stage}-{args.arm}", "approved_scope": "p0_p1_only", "stage": args.stage, "arm": args.arm, "input_hashes": input_hashes, "config_hash": config_hash, "script_hash": script_hash, "resource_contention": bool(config["training"]["resource_contention"])})
        set_seed(42)
        device = device_for_run()
        if args.stage == "p0_c00":
            tokenizer_path = stage_dir / "tokenizer.json"
            state = load_checkpoint(checkpoint) if args.resume and checkpoint.exists() else None
            if state is None:
                train_tokenizer(fit_parts, tokenizer_path, int(config["model"]["vocab_size_subword"]))
                identity["tokenizer_sha256"] = sha256_file(tokenizer_path)
                save_training_checkpoint(checkpoint, {"phase": "tokenizer", "tokenizer_sha256": identity["tokenizer_sha256"]}, identity)
                state = load_checkpoint(checkpoint)
            elif state.get("phase") == "tokenizer":
                if not tokenizer_path.is_file():
                    raise FileNotFoundError("tokenizer 阶段断点缺少 tokenizer.json")
                identity["tokenizer_sha256"] = sha256_file(tokenizer_path)
                if state.get("tokenizer_sha256") != identity["tokenizer_sha256"]:
                    raise ValueError("tokenizer 阶段断点与 tokenizer.json 哈希不匹配")
                verify_checkpoint_identity(state, identity)
            else:
                if not tokenizer_path.is_file():
                    raise FileNotFoundError("P0 断点缺少 tokenizer.json")
                identity["tokenizer_sha256"] = sha256_file(tokenizer_path)
                verify_checkpoint_identity(state, identity)
            tokenizer = Tokenizer.from_file(str(tokenizer_path))
            static = build_static(config, tokenizer.get_vocab_size()).to(device)
            if state is not None and state.get("phase") == "pretrain_char":
                char_state = state
            else:
                char_state = None
            if state is None or state.get("phase") in {"tokenizer", "pretrain_char"}:
                char_receipt = train_pretraining_branch(static.char, "char", None, config, fit_parts, device, checkpoint, char_state, identity)
                save_training_checkpoint(stage_dir / "char-backbone.pt", {"branch": EncoderBranch(static.char).state_dict()}, identity)
                save_training_checkpoint(checkpoint, {"phase": "char_done", "char": static.char.state_dict()}, identity)
                state = load_checkpoint(checkpoint)
            else:
                char_receipt = {"status": "already_completed"}
            char_checkpoint = stage_dir / "char-backbone.pt"
            if char_checkpoint.is_file():
                char_saved = load_checkpoint(char_checkpoint)
                verify_checkpoint_identity(char_saved, identity)
                static.char.load_state_dict(char_saved["branch"], strict=False)
            if state is not None and "char" in state:
                static.char.load_state_dict(state["char"], strict=True)
            subword_state = state if state is not None and state.get("phase") == "pretrain_subword" else None
            if state is None or state.get("phase") in {"char_done", "pretrain_subword"}:
                if state is not None and state.get("phase") == "char_done":
                    restore_rng_state(state["rng_state"])
                token_receipt = train_pretraining_branch(static.token, "subword", tokenizer, config, fit_parts, device, checkpoint, subword_state, identity)
                save_training_checkpoint(stage_dir / "token-backbone.pt", {"branch": EncoderBranch(static.token).state_dict()}, identity)
                save_training_checkpoint(checkpoint, {"phase": "subword_done", "char": static.char.state_dict(), "token": static.token.state_dict()}, identity)
                state = load_checkpoint(checkpoint)
            else:
                token_receipt = {"status": "already_completed"}
            token_checkpoint = stage_dir / "token-backbone.pt"
            if token_checkpoint.is_file():
                token_saved = load_checkpoint(token_checkpoint)
                verify_checkpoint_identity(token_saved, identity)
                static.token.load_state_dict(token_saved["branch"], strict=False)
            if state is not None and "token" in state:
                static.token.load_state_dict(state["token"], strict=True)
            static.token = EncoderBranch(static.token)
            static.char = EncoderBranch(static.char)
            static_state = state if state is not None and state.get("phase") == "static" else None
            if state is None or state.get("phase") in {"subword_done", "static"}:
                if state is not None and state.get("phase") == "subword_done":
                    restore_rng_state(state["rng_state"])
                static_receipt = train_static(static, tokenizer, config, fit_parts, device, checkpoint, static_state, identity)
            else:
                static_receipt = {"status": "already_completed"}
            final_state = load_checkpoint(checkpoint)
            verify_checkpoint_identity(final_state, identity)
            if "static_model" not in final_state:
                raise RuntimeError("P0 未生成静态模型状态")
            result = common_result(config, args, input_hashes, config_hash, script_hash, checkpoint, started)
            result["parameter_receipt"] = parameter_receipt(static)
            result["tokenizer_sha256"] = sha256_file(tokenizer_path)
            result["runtime"]["p0_checkpoint_phase"] = final_state["phase"]
            result["runtime"]["training_activity"] = {"char": char_receipt, "subword": token_receipt, "static": static_receipt}
            result["mechanism_activity"] = {"static_fusion": "frozen_anchor", "trainable_parameters": sum(parameter.numel() for parameter in static.parameters() if parameter.requires_grad)}
            source = calibrate_source(static, tokenizer, config, validation_parts, device, input_hashes["validation"], stage_dir / "source-validation-threshold-receipt.jsonl")
            result["source_threshold"] = source
            result["metrics_by_year"] = {"T17": {"source_validation": source["metrics"]}}
            result["calibration"] = {"brier": source["metrics"]["brier"], "ece": source["metrics"]["ece"]}
        else:
            p0_checkpoint = run_root / "p0_c00" / "checkpoint.pt"
            p0_tokenizer = run_root / "p0_c00" / "tokenizer.json"
            p0_status_path, p0_result_path, p0_manifest_path = run_root / "p0_c00" / "status.json", run_root / "p0_c00" / "result.json", run_root / "p0_c00" / "manifest.json"
            if not p0_checkpoint.is_file() or not p0_tokenizer.is_file() or not p0_status_path.is_file() or not p0_result_path.is_file() or not p0_manifest_path.is_file():
                raise FileNotFoundError("P1 需要同一运行根目录中已完成的 P0 制品")
            p0_status = json.loads(p0_status_path.read_text(encoding="utf-8"))
            p0_result = json.loads(p0_result_path.read_text(encoding="utf-8"))
            p0_manifest = json.loads(p0_manifest_path.read_text(encoding="utf-8"))
            p0_hash = sha256_file(p0_checkpoint)
            if p0_status.get("status") != "completed" or p0_result.get("status") != "completed" or p0_result.get("approved_scope") != "p0_p1_only":
                raise ValueError("P0 状态或批准范围未完成")
            if p0_result.get("config_hash") != config_hash or p0_result.get("checkpoint_hash") != p0_hash or p0_status.get("checkpoint_hash") != p0_hash or p0_result.get("input_hashes") != input_hashes:
                raise ValueError("P0 配置或检查点哈希不匹配")
            tokenizer_hash = sha256_file(p0_tokenizer)
            if p0_result.get("tokenizer_sha256") != tokenizer_hash or p0_status.get("tokenizer_sha256") != tokenizer_hash or p0_manifest.get("tokenizer_sha256") != tokenizer_hash:
                raise ValueError("P0 tokenizer 哈希不匹配")
            identity["tokenizer_sha256"] = tokenizer_hash
            p0_state = load_checkpoint(p0_checkpoint)
            verify_checkpoint_identity(p0_state, identity)
            tokenizer = Tokenizer.from_file(str(p0_tokenizer))
            static = build_static(config, tokenizer.get_vocab_size()).to(device)
            static.token = EncoderBranch(static.token)
            static.char = EncoderBranch(static.char)
            static.load_state_dict(p0_state["static_model"], strict=True)
            adapter = FusionAdapter(int(config["model"]["d_model"])).to(device)
            source = p0_result.get("source_threshold")
            if not isinstance(source, dict) or source.get("input_hashes") != input_hashes["validation"] or source.get("threshold_space") != "logit_difference" or source.get("threshold_dtype") != "float32":
                raise ValueError("P0 源阈值收据或验证输入哈希不匹配")
            aggregate = {key: value for key, value in source.items() if key not in {"aggregate_sha256", "result_sha256", "interpretation_boundary"}}
            if hashlib.sha256(json.dumps(aggregate, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest() != source.get("aggregate_sha256") or source.get("aggregate_sha256") != source.get("result_sha256"):
                raise ValueError("P0 源阈值聚合收据哈希不匹配")
            receipt_path = run_root / "p0_c00" / "source-validation-threshold-receipt.jsonl"
            if not receipt_path.is_file() or sha256_file(receipt_path) != source.get("threshold_receipt_sha256"):
                raise ValueError("P0 源阈值逐样本收据哈希不匹配")
            threshold = np.float32(source["threshold_float32"])
            if float(threshold) != float(source["threshold_float32"]):
                raise ValueError("P0 源阈值无法保持 float32")
            if not (0 <= int(source.get("actual_above", -1)) <= int(source.get("allowed_above", -1)) and int(source.get("tie_group_count", 0)) > 0):
                raise ValueError("P0 源阈值并列计数不满足冻结口径")
            prior = load_checkpoint(checkpoint) if args.resume and checkpoint.exists() else None
            training_receipt = train_adapter(static, adapter, args.arm, tokenizer, config, fit_parts, threshold, device, checkpoint, prior, identity)
            validation = validate_adapter(static, adapter, args.arm, tokenizer, config, validation_parts, threshold, device)
            result = common_result(config, args, input_hashes, config_hash, script_hash, checkpoint, started)
            result["source_threshold"] = source
            result["qmf_component"] = "QMF 风格来源组件；未持久化逐样本历史损失，不是完整 QMF 复现。" if args.arm == "qmf" else None
            result["metrics_by_year"] = {"T17": {"source_validation": validation}}
            result["conditional_metrics"] = validation["correction"]
            result["calibration"] = {"brier": validation["metrics"]["brier"], "ece": validation["metrics"]["ece"]}
            result["mechanism_activity"] = validation["mechanism_activity"]
            result["runtime"]["training"] = training_receipt
            result["p0_checkpoint_hash"] = p0_hash
            result["p0_tokenizer_sha256"] = tokenizer_hash
            result["parameter_receipt"] = parameter_receipt(adapter)
            result["mechanism_activity"]["trainable_parameters"] = sum(parameter.numel() for parameter in adapter.parameters() if parameter.requires_grad)
        atomic_json(stage_dir / "result.json", result)
        manifest_path = stage_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if args.stage == "p0_c00":
            manifest["tokenizer_sha256"] = result["tokenizer_sha256"]
        else:
            manifest["p0_tokenizer_sha256"] = result["p0_tokenizer_sha256"]
        atomic_json(manifest_path, manifest)
        status = {"status": "completed", "run_identity": result["run_identity"], "stage": args.stage, "arm": args.arm, "result": "result.json", "config_hash": config_hash, "script_hash": script_hash, "checkpoint_hash": sha256_file(checkpoint)}
        status["tokenizer_sha256" if args.stage == "p0_c00" else "p0_tokenizer_sha256"] = result["tokenizer_sha256" if args.stage == "p0_c00" else "p0_tokenizer_sha256"]
        atomic_json(status_path, status)
        print(json.dumps({"status": "completed", "run_dir": str(stage_dir)}, ensure_ascii=False))
        return 0
    except Exception as error:
        atomic_json(status_path, {"status": "failed", "run_identity": f"{config['run_identity']}-{args.stage}-{args.arm}", "stage": args.stage, "arm": args.arm, "config_hash": config_hash, "script_hash": script_hash, "error_type": type(error).__name__, "error": str(error)})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
