# -*- coding: utf-8 -*-
"""N14 表格预归一化残差多层感知机协议 A 四格生产入口。

数据只从共享 Raw83 ``dataset-manifest.json`` 进入。源年完成 A/B 输入选择、两个
AdamW 候选选择和 C00/C01/C10/C11 四格后才签发资格封印；当前配置禁止目标评价。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
TOOL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOL_DIR.parent
for root in (TOOL_DIR, PROJECT_ROOT / "src"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

SCHEMA_VERSION = "ch3-tabular-resnet-paper-recipe-protocol-a-config-v2"
RUN_ID = "ch3-tabular-resnet-paper-recipe-protocol-a-seed42-v2"
MODEL_KEY = "tabular-resnet-paper-recipe"
DISPLAY_NAME = "表格预归一化残差多层感知机骨干专属论文配方协议A四格"
FROZEN_RECIPE_SHA256 = "3b1e3103c9a8d37afe55c5e055cfcc4b84c72af3054b4cd20ec1dc4e5554d359"
PRECISION_PROFILE_ID = "cuda-bf16-amp-fp32-sensitive-v1"
CELL_ORDER = ("C00", "C01", "C10", "C11")
CELLS = {
    "C00": {"causal_prefix_aggregation": False, "block_auxiliary_objective": False},
    "C01": {"causal_prefix_aggregation": False, "block_auxiliary_objective": True},
    "C10": {"causal_prefix_aggregation": True, "block_auxiliary_objective": False},
    "C11": {"causal_prefix_aggregation": True, "block_auxiliary_objective": True},
}
ARM_ORDER = ("A", "B")
OPTIMIZER_ORDER = ("resmlp-paper-logmid", "resmlp-paper-logq75")
DR_FPR_GRID = (0.001, 0.005, 0.01, 0.02, 0.04, 0.08)
EXPECTED_PARAMETER_COUNT = 387_074
EXPECTED_PARAMETER_DECOMPOSITION = {
    "input_projection": 16_128,
    "residual_blocks": 296_832,
    "causal_prefix_fusion": 73_920,
    "output_head_and_p_log": 194,
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(16 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def process_peak_rss_mib() -> float:
    import resource

    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value / 1024.0 if sys.platform != "darwin" else value / 2**20


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON 顶层必须是对象：{path}")
    return value


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_bytes(canonical_bytes(value) + b"\n")
    os.replace(temporary, path)


def atomic_torch(path: Path, value: dict[str, Any]) -> None:
    import torch

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    torch.save(value, temporary)
    os.replace(temporary, path)


def precision_module() -> Any:
    import neural_precision_runtime

    return neural_precision_runtime


def precision_contract_path() -> Path:
    return PROJECT_ROOT / "configs" / "neural-precision-profiles-v1.json"


def expected_parameter_count() -> int:
    return sum(EXPECTED_PARAMETER_DECOMPOSITION.values())


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("配置模式版本不符")
    if (config.get("run_id"), config.get("model_key"), config.get("display_name")) != (
        RUN_ID,
        MODEL_KEY,
        DISPLAY_NAME,
    ):
        raise ValueError("N14 运行身份不符")
    if config.get("frozen_recipe_sha256") != FROZEN_RECIPE_SHA256:
        raise ValueError("冻结配方 SHA-256 不符")
    if config.get("precision_profile_id") != PRECISION_PROFILE_ID:
        raise ValueError("必须使用统一 BF16 精度配置")
    if config.get("cells") != CELLS or tuple(config.get("cell_order", [])) != CELL_ORDER:
        raise ValueError("四格身份必须严格为 C00/C01/C10/C11")
    paths = config.get("paths", {})
    for key in ("source_dataset_manifest", "output_root", "source_qualification_seal"):
        if not isinstance(paths.get(key), str) or not paths[key]:
            raise ValueError(f"paths.{key} 缺失")
    if Path(paths["source_dataset_manifest"]).name != "dataset-manifest.json":
        raise ValueError("源数据只能从 dataset-manifest.json 发现")
    if Path(paths["output_root"]).name != RUN_ID:
        raise ValueError("输出根末级目录必须等于运行身份")
    if tuple(config.get("input_arm_order", [])) != ARM_ORDER:
        raise ValueError("输入选择必须按 A/B 固定顺序")
    optimizers = config.get("optimizer_candidates", [])
    if tuple(item.get("key") for item in optimizers) != OPTIMIZER_ORDER:
        raise ValueError("优化器候选顺序不符")
    if [item.get("learning_rate") for item in optimizers] != [
        0.00031622776601683794,
        0.0017782794100389228,
    ]:
        raise ValueError("两个预注册学习率不符")
    if any(item.get("optimizer") != "adamw" or item.get("weight_decay") != 0.0 for item in optimizers):
        raise ValueError("两个优化器必须为零权重衰减 AdamW")
    expected_architecture = {
        "input_dimension": 83,
        "main_width": 192,
        "hidden_width": 384,
        "residual_blocks": 2,
        "hidden_dropout": 0.15,
        "residual_dropout": 0.0,
        "fusion_dropout": 0.1,
        "normalization": "per-token-layer-norm",
        "normalization_deviates_from_paper_batch_norm": True,
        "parameter_count": EXPECTED_PARAMETER_COUNT,
    }
    if config.get("architecture") != expected_architecture:
        raise ValueError("模型结构或 LayerNorm 偏离登记不符")
    expected_training = {
        "seed": 42,
        "sequence_length": 128,
        "effective_batch_size": 64,
        "micro_batch_sequences": 64,
        "gradient_accumulation_steps": 1,
        "epochs": 20,
        "steps_per_epoch": 1000,
        "checkpoint_every_optimizer_steps": 20,
        "gradient_clip_norm": 1.0,
        "auxiliary_loss_weight": 1.0,
        "selection_metric": "lspr23-entity-disjoint-validation-flow-ap",
        "selection_rule": "single-epoch-argmax-earliest-tie-no-early-stopping",
        "wall_clock_limit_seconds": None,
    }
    if config.get("training") != expected_training:
        raise ValueError("训练、选择、恢复或无墙钟上限合同不符")
    tokens = config.get("label_stage_token_env", {})
    if set(tokens) != {"train", "validate", "target-evaluate"}:
        raise ValueError("标签用途令牌环境变量合同不完整")
    if tuple(config.get("evaluation", {}).get("dr_fpr_grid", [])) != DR_FPR_GRID:
        raise ValueError("六档 FPR 网格不符")
    if config["evaluation"].get("persist_scores_labels_or_members") is not False:
        raise ValueError("禁止持久化分数、标签或成员")
    target = config.get("target_gate", {})
    if target.get("qualification_status") != "blocked-until-external-source-qualification":
        raise ValueError("当前配置必须保持目标资格阻塞")
    if target.get("winning_arm") is not None or paths.get("target_dataset_manifest") is not None:
        raise ValueError("当前配置不得预填胜出臂或目标清单")
    if config.get("swanlab", {}).get("maximum_init_attempts") != 2:
        raise ValueError("SwanLab 初始化状态机必须限制为两次")
    if expected_parameter_count() != EXPECTED_PARAMETER_COUNT:
        raise ValueError("闭式参数量不等于 387074")
    profile = precision_module().get_profile(load_json(precision_contract_path()), PRECISION_PROFILE_ID)
    if profile.get("compute_dtype") != "bfloat16" or profile.get("grad_scaler") is not False:
        raise ValueError("统一精度配置必须为 BF16 且不使用 GradScaler")


def raw83_module() -> Any:
    from flow_probe import protocol_a_raw83

    return protocol_a_raw83


def artifact_path(dataset: Any, key: str) -> Path:
    item = dataset.manifest.get("artifacts", {}).get(key)
    if not isinstance(item, dict):
        raise RuntimeError(f"Raw83 清单缺少制品：{key}")
    path = Path(item["path"]).resolve(strict=True)
    root = dataset.manifest_path.parent.resolve(strict=True)
    if path.is_symlink() or not path.is_relative_to(root):
        raise RuntimeError(f"Raw83 清单制品越界或为符号链接：{key}")
    if path.stat().st_size != int(item["bytes"]) or sha256_file(path) != item["sha256"]:
        raise RuntimeError(f"Raw83 清单制品身份不匹配：{key}")
    return path


def stage_token(config: dict[str, Any], purpose: str) -> str:
    env_name = config["label_stage_token_env"][purpose]
    token = os.environ.get(env_name)
    if not token:
        raise RuntimeError(f"缺少 {purpose} 标签用途令牌环境变量：{env_name}")
    return token


class SourceView:
    def __init__(self, config: dict[str, Any], arm: str) -> None:
        import numpy as np

        api = raw83_module()
        manifest = config["paths"]["source_dataset_manifest"]
        self.arm = arm
        self.train = api.open_protocol_a_dataset(manifest, "LSPR23", "train", arm=arm)
        self.validate = api.open_protocol_a_dataset(manifest, "LSPR23", "validate", arm=arm)
        self.train_rows = np.load(artifact_path(self.train, "train_rows"), mmap_mode="r", allow_pickle=False)
        self.validation_rows = np.load(
            artifact_path(self.validate, "validation_rows"), mmap_mode="r", allow_pickle=False
        )
        self.train_resolver = self.train.open_label_resolver(stage_token(config, "train"))
        self.validation_resolver = self.validate.open_label_resolver(stage_token(config, "validate"))
        self.weights = self.train.training_weight_aggregate()
        self.transform_state_hash = self.train.manifest["transform_state_hashes"][arm]
        self.view_content_sha256 = self.train.manifest["view_content_sha256"][arm]

    def gather(self, purpose: str, rows: Any) -> tuple[Any, Any, Any, Any]:
        import numpy as np

        dataset = self.train if purpose == "train" else self.validate
        resolver = self.train_resolver if purpose == "train" else self.validation_resolver
        batch = dataset.gather_sequences(rows, columns="all83")
        valid = np.asarray(batch["valid_mask"], dtype=bool)
        raw_rows = np.asarray(batch["raw_row_indices"], dtype=np.int64)
        labels = np.zeros(raw_rows.shape, dtype=np.float32)
        labels[valid] = resolver.resolve(raw_rows[valid]).astype(np.float32, copy=False)
        return np.ascontiguousarray(batch["features"], dtype=np.float32), valid, labels, raw_rows


def backbone_classes() -> dict[str, Any]:
    import torch

    class ResidualBlock(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.norm = torch.nn.LayerNorm(192)
            self.linear1 = torch.nn.Linear(192, 384)
            self.linear2 = torch.nn.Linear(384, 192)
            self.dropout = torch.nn.Dropout(0.15)

        def forward(self, values: Any) -> Any:
            residual = values
            values = self.norm(values.float()).to(residual.dtype)
            values = self.dropout(torch.relu(self.linear1(values)))
            return residual + self.linear2(values)

    class TabularResNet(torch.nn.Module):
        def __init__(self, cell: str) -> None:
            super().__init__()
            self.cell = cell
            self.input_projection = torch.nn.Linear(83, 192)
            self.blocks = torch.nn.ModuleList([ResidualBlock(), ResidualBlock()])
            self.fusion = torch.nn.Linear(384, 192)
            self.fusion_dropout = torch.nn.Dropout(0.1)
            self.output = torch.nn.Linear(192, 1)
            self.p_log = torch.nn.Parameter(torch.zeros((), dtype=torch.float32))

        @property
        def p(self) -> Any:
            return 1.0 + torch.nn.functional.softplus(self.p_log.float())

        def forward(self, values: Any, valid: Any) -> Any:
            hidden = self.input_projection(values)
            for block in self.blocks:
                hidden = block(hidden)
            mask = valid.unsqueeze(-1).float()
            if CELLS[self.cell]["causal_prefix_aggregation"]:
                context = torch.cumsum(hidden.float() * mask, dim=1) / torch.cumsum(
                    mask, dim=1
                ).clamp_min(1.0)
            else:
                context = torch.zeros_like(hidden.float())
            fused = self.fusion(torch.cat((hidden.float(), context), dim=-1).to(hidden.dtype))
            return self.output(self.fusion_dropout(torch.relu(fused))).squeeze(-1)

    return {"TabularResNet": TabularResNet}


def build_model(cell: str) -> Any:
    model = backbone_classes()["TabularResNet"](cell)
    actual = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    if (EXPECTED_PARAMETER_COUNT, expected_parameter_count(), actual) != (
        EXPECTED_PARAMETER_COUNT,
        EXPECTED_PARAMETER_COUNT,
        EXPECTED_PARAMETER_COUNT,
    ):
        raise RuntimeError(
            f"参数量三方核对失败：配置={EXPECTED_PARAMETER_COUNT} 闭式={expected_parameter_count()} 实例={actual}"
        )
    return model


def learned_lp_pool(probability: Any, valid: Any, p_value: Any) -> Any:
    mask = valid.float()
    numerator = (probability.float().clamp_min(1e-12).pow(p_value) * mask).sum(dim=1)
    return (numerator / mask.sum(dim=1).clamp_min(1.0)).pow(1.0 / p_value)


def optimizer_record(config: dict[str, Any], key: str) -> dict[str, Any]:
    return next(item for item in config["optimizer_candidates"] if item["key"] == key)


def resolve_device() -> Any:
    import torch

    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("N14 生产训练需要支持 BF16 的 CUDA 设备")
    return torch.device("cuda")


def runtime_identity(config: dict[str, Any], arm: str, optimizer_key: str, cell: str) -> dict[str, Any]:
    manifest_path = Path(config["paths"]["source_dataset_manifest"])
    manifest = load_json(manifest_path)
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_content_sha256"}
    if manifest.get("manifest_content_sha256") != canonical_sha256(unsigned):
        raise RuntimeError("Raw83 源清单内容 SHA-256 不匹配")
    return {
        "run_id": RUN_ID,
        "cell": cell,
        "input_arm": arm,
        "optimizer": optimizer_key,
        "source_manifest_file_sha256": sha256_file(manifest_path),
        "source_manifest_content_sha256": manifest["manifest_content_sha256"],
        "field_list_sha256": manifest["field_list_sha256"],
        "sequence_split_state_hash": manifest["sequence_split_state_hash"],
        "transform_state_hash": manifest["transform_state_hashes"][arm],
        "view_content_sha256": manifest["view_content_sha256"][arm],
        "training_weight_aggregate_sha256": canonical_sha256(manifest["training_weight_aggregate"]),
        "architecture_sha256": canonical_sha256(config["architecture"]),
        "tool_sha256": sha256_file(Path(__file__)),
        "config_sha256": sha256_file(Path(config["_config_path"])),
        "frozen_recipe_sha256": FROZEN_RECIPE_SHA256,
    }


def move_optimizer_state(optimizer: Any, device: Any) -> None:
    import torch

    for state in optimizer.state.values():
        for key, value in state.items():
            if torch.is_tensor(value):
                state[key] = value.to(device)


def evaluate_flow_ap(config: dict[str, Any], model: Any, view: SourceView, device: Any, profile: Any) -> tuple[float, int]:
    import numpy as np
    import torch
    from sklearn.metrics import average_precision_score

    scores: list[Any] = []
    labels: list[Any] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(view.validation_rows), 64):
            features, valid, targets, _ = view.gather("validate", view.validation_rows[start : start + 64])
            with precision_module().autocast_context(profile, device.type, torch):
                logits = model(torch.from_numpy(features).to(device), torch.from_numpy(valid).to(device))
            flat = valid.reshape(-1)
            scores.append(torch.sigmoid(logits.float()).cpu().numpy().reshape(-1)[flat])
            labels.append(targets.reshape(-1)[flat])
    model.train()
    score_array = np.concatenate(scores)
    label_array = np.concatenate(labels)
    return float(average_precision_score(label_array, score_array)), int(label_array.size)


def checkpoint_state(
    config: dict[str, Any],
    identity: dict[str, Any],
    model: Any,
    optimizer: Any,
    sampler: Any,
    profile: Any,
    epoch: int,
    step: int,
    optimizer_step: int,
    history: list[dict[str, Any]],
    best: dict[str, Any],
    recovery_count: int,
    epoch_loss_sum: float,
    processed_valid_flows: int,
    elapsed_seconds: float,
) -> dict[str, Any]:
    import numpy as np
    import torch

    return {
        "schema_version": "ch3-tabular-resnet-atomic-step-checkpoint-v2",
        "identity": identity,
        "model_state_dict": {key: value.detach().cpu().clone() for key, value in model.state_dict().items()},
        "optimizer_state_dict": optimizer.state_dict(),
        "epoch": epoch,
        "step_in_epoch": step,
        "optimizer_step": optimizer_step,
        "optimizer_step_boundary": True,
        "history": history,
        "best": best,
        "sampler_state": sampler.get_state(),
        "rng_state": {
            "python": random.getstate(),
            "numpy": np.random.get_state(),
            "torch_cpu": torch.get_rng_state(),
            "torch_cuda_all": torch.cuda.get_rng_state_all(),
        },
        "precision_profile_id": PRECISION_PROFILE_ID,
        "precision_profile_sha256": canonical_sha256(profile),
        "effective_batch_size": config["training"]["effective_batch_size"],
        "micro_batch_sequences": config["training"]["micro_batch_sequences"],
        "gradient_accumulation_steps": config["training"]["gradient_accumulation_steps"],
        "recovery_count": recovery_count,
        "epoch_loss_sum": epoch_loss_sum,
        "processed_valid_flows": processed_valid_flows,
        "elapsed_seconds": elapsed_seconds,
    }


def train_cell(
    config: dict[str, Any], cell: str, arm: str, optimizer_key: str, output_root: Path, resume: bool
) -> dict[str, Any]:
    import numpy as np
    import torch

    identity = runtime_identity(config, arm, optimizer_key, cell)
    identity_key = canonical_sha256(identity)[:16]
    selected_path = output_root / "checkpoints" / f"selected-{cell}-{identity_key}.pt"
    receipt_path = output_root / "receipts" / f"selection-{cell}-{identity_key}.json"
    inflight_path = output_root / "inflight" / f"{cell}-{identity_key}.pt"
    if selected_path.is_file() and receipt_path.is_file():
        receipt = load_json(receipt_path)
        if resume and receipt.get("identity") == identity and receipt["checkpoint"]["sha256"] == sha256_file(selected_path):
            return receipt
        raise RuntimeError("完成制品存在但恢复身份或摘要不符")
    if not resume and any(path.exists() for path in (selected_path, receipt_path, inflight_path)):
        raise RuntimeError("全新运行存在历史制品，拒绝覆盖")

    view = SourceView(config, arm)
    training = config["training"]
    device = resolve_device()
    precision = precision_module()
    profile = precision.get_profile(load_json(precision_contract_path()), PRECISION_PROFILE_ID)
    model = build_model(cell).to(device)
    optimizer_config = optimizer_record(config, optimizer_key)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=optimizer_config["learning_rate"], weight_decay=0.0
    )
    precision.validate_model_optimizer_fp32(model, optimizer, torch)
    if precision.create_grad_scaler(profile, torch) is not None:
        raise RuntimeError("BF16 配置禁止 GradScaler")
    flow_weight = float(view.weights["train_flow_positive_weight"])
    block_weight = float(view.weights["train_sequence_positive_weight"])
    flow_loss = torch.nn.BCEWithLogitsLoss(
        reduction="none", pos_weight=torch.tensor([flow_weight], device=device, dtype=torch.float32)
    )
    block_loss = torch.nn.BCELoss(reduction="none")
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    sampler = torch.Generator().manual_seed(42)
    history: list[dict[str, Any]] = []
    best = {"ap": -1.0, "epoch": 0, "p": None, "model_state_dict": None}
    optimizer_step = 0
    start_epoch = 1
    start_step = 1
    recovery_count = 0
    epoch_loss_sum = 0.0
    processed_valid_flows = 0
    elapsed_before = 0.0
    if resume and inflight_path.is_file():
        state = torch.load(inflight_path, map_location="cpu", weights_only=False)
        runtime = (
            state.get("precision_profile_id"),
            state.get("precision_profile_sha256"),
            state.get("effective_batch_size"),
            state.get("micro_batch_sequences"),
            state.get("gradient_accumulation_steps"),
        )
        expected = (
            PRECISION_PROFILE_ID,
            canonical_sha256(profile),
            training["effective_batch_size"],
            training["micro_batch_sequences"],
            training["gradient_accumulation_steps"],
        )
        if state.get("identity") != identity or state.get("optimizer_step_boundary") is not True or runtime != expected:
            raise RuntimeError("在途检查点身份、边界、精度或微批合同不符")
        model.load_state_dict(state["model_state_dict"])
        optimizer.load_state_dict(state["optimizer_state_dict"])
        move_optimizer_state(optimizer, device)
        sampler.set_state(state["sampler_state"])
        random.setstate(state["rng_state"]["python"])
        np.random.set_state(state["rng_state"]["numpy"])
        torch.set_rng_state(state["rng_state"]["torch_cpu"])
        torch.cuda.set_rng_state_all(state["rng_state"]["torch_cuda_all"])
        history = state["history"]
        best = state["best"]
        optimizer_step = int(state["optimizer_step"])
        start_epoch = int(state["epoch"])
        start_step = int(state["step_in_epoch"]) + 1
        recovery_count = int(state["recovery_count"]) + 1
        epoch_loss_sum = float(state["epoch_loss_sum"])
        processed_valid_flows = int(state["processed_valid_flows"])
        elapsed_before = float(state["elapsed_seconds"])
        if start_step > training["steps_per_epoch"]:
            start_epoch += 1
            start_step = 1
            epoch_loss_sum = 0.0
    started = time.time()
    model.train()
    for epoch in range(start_epoch, training["epochs"] + 1):
        first_step = start_step if epoch == start_epoch else 1
        if first_step == 1:
            epoch_loss_sum = 0.0
        for step in range(first_step, training["steps_per_epoch"] + 1):
            positions = torch.randperm(len(view.train_rows), generator=sampler)[:64]
            rows = view.train_rows[positions.numpy()]
            features, valid, labels, _ = view.gather("train", rows)
            valid_flows = int(valid.sum())
            block_labels = ((labels * valid).max(axis=1) > 0).astype(np.float32)
            block_weights = (1.0 + (block_weight - 1.0) * block_labels).astype(np.float32)
            optimizer.zero_grad(set_to_none=True)
            values_t = torch.from_numpy(features).to(device)
            valid_t = torch.from_numpy(valid).to(device)
            labels_t = torch.from_numpy(labels).to(device)
            with precision.autocast_context(profile, device.type, torch):
                logits = model(values_t, valid_t)
            logits32 = logits.float()
            mask32 = valid_t.float()
            loss_sum = (flow_loss(logits32, labels_t.float()) * mask32).sum()
            if CELLS[cell]["block_auxiliary_objective"]:
                pooled = learned_lp_pool(torch.sigmoid(logits32), mask32, model.p).clamp(1e-6, 1 - 1e-6)
                auxiliary = block_loss(
                    pooled, torch.from_numpy(block_labels).to(device)
                ) * torch.from_numpy(block_weights).to(device)
                loss_sum = loss_sum + training["auxiliary_loss_weight"] * auxiliary.sum()
            normalized = loss_sum / valid_flows
            normalized.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), training["gradient_clip_norm"])
            optimizer.step()
            optimizer_step += 1
            epoch_loss_sum += float(normalized.detach())
            processed_valid_flows += valid_flows
            if optimizer_step == 1:
                precision.validate_model_optimizer_fp32(model, optimizer, torch)
                atomic_json(
                    output_root / "receipts" / f"first-step-resource-{cell}-{identity_key}.json",
                    {
                        "identity": identity,
                        "allocated_mib": torch.cuda.memory_allocated(device) / 2**20,
                        "reserved_mib": torch.cuda.memory_reserved(device) / 2**20,
                        "max_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
                        "max_reserved_mib": torch.cuda.max_memory_reserved(device) / 2**20,
                    },
                )
            if (
                optimizer_step % training["checkpoint_every_optimizer_steps"] == 0
                and step != training["steps_per_epoch"]
            ):
                atomic_torch(
                    inflight_path,
                    checkpoint_state(
                        config,
                        identity,
                        model,
                        optimizer,
                        sampler,
                        profile,
                        epoch,
                        step,
                        optimizer_step,
                        history,
                        best,
                        recovery_count,
                        epoch_loss_sum,
                        processed_valid_flows,
                        elapsed_before + time.time() - started,
                    ),
                )
        validation_ap, validation_flows = evaluate_flow_ap(config, model, view, device, profile)
        p_value = float(model.p.detach())
        history.append(
            {
                "epoch": epoch,
                "validation_flow_ap": validation_ap,
                "validation_flows": validation_flows,
                "mean_training_loss": epoch_loss_sum / training["steps_per_epoch"],
                "p": p_value,
            }
        )
        if validation_ap > best["ap"]:
            best = {
                "ap": validation_ap,
                "epoch": epoch,
                "p": p_value,
                "model_state_dict": {
                    key: value.detach().cpu().clone() for key, value in model.state_dict().items()
                },
            }
        atomic_torch(
            inflight_path,
            checkpoint_state(
                config,
                identity,
                model,
                optimizer,
                sampler,
                profile,
                epoch,
                training["steps_per_epoch"],
                optimizer_step,
                history,
                best,
                recovery_count,
                epoch_loss_sum,
                processed_valid_flows,
                elapsed_before + time.time() - started,
            ),
        )
    if best["model_state_dict"] is None:
        raise RuntimeError("未产生可选择检查点")
    atomic_torch(
        selected_path,
        {
            "schema_version": "ch3-tabular-resnet-selected-checkpoint-v2",
            "identity": identity,
            "cell": cell,
            "selected_epoch": best["epoch"],
            "selected_p": best["p"],
            "model_state_dict": best["model_state_dict"],
            "optimizer_steps": optimizer_step,
            "precision_profile_id": PRECISION_PROFILE_ID,
        },
    )
    receipt = {
        "schema_version": "ch3-tabular-resnet-selection-receipt-v2",
        "identity": identity,
        "input_arm": arm,
        "optimizer_candidate": optimizer_key,
        "cell": cell,
        "selected_epoch": best["epoch"],
        "validation_flow_ap": best["ap"],
        "selected_p": best["p"],
        "history": history,
        "optimizer_steps": optimizer_step,
        "recovery_count": recovery_count,
        "training_seconds": elapsed_before + time.time() - started,
        "processed_valid_flows": processed_valid_flows,
        "valid_flows_per_second": processed_valid_flows
        / max(elapsed_before + time.time() - started, 1e-9),
        "parameter_count": EXPECTED_PARAMETER_COUNT,
        "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
        "peak_gpu_reserved_mib": torch.cuda.max_memory_reserved(device) / 2**20,
        "peak_process_rss_mib": process_peak_rss_mib(),
        "checkpoint_every_optimizer_steps": training["checkpoint_every_optimizer_steps"],
        "replayed_partial_effective_batches": 0,
        "checkpoint": {
            "path": str(selected_path),
            "bytes": selected_path.stat().st_size,
            "sha256": sha256_file(selected_path),
        },
        "training_weight_aggregate_sha256": canonical_sha256(view.weights),
        "flow_positive_weight_source": "Raw83 training_weight_aggregate.train_flow_positive_weight",
        "block_positive_weight_source": "Raw83 training_weight_aggregate.train_sequence_positive_weight",
        "block_target_semantics": "块内有效逐流标签的最大值，不是完整实体目标",
    }
    atomic_json(receipt_path, receipt)
    inflight_path.unlink(missing_ok=True)
    return receipt


def selected_model(receipt: dict[str, Any], device: Any) -> Any:
    import torch

    path = Path(receipt["checkpoint"]["path"])
    if sha256_file(path) != receipt["checkpoint"]["sha256"]:
        raise RuntimeError("选择检查点 SHA-256 不符")
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    model = build_model(receipt["cell"])
    model.load_state_dict(checkpoint["model_state_dict"])
    return model.to(device)


def score_source(config: dict[str, Any], receipt: dict[str, Any], view: SourceView, device: Any, profile: Any) -> dict[str, Any]:
    import numpy as np
    import torch

    model = selected_model(receipt, device)
    scores: list[Any] = []
    labels: list[Any] = []
    raw_rows: list[Any] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(view.validation_rows), 64):
            features, valid, targets, indices = view.gather("validate", view.validation_rows[start : start + 64])
            with precision_module().autocast_context(profile, device.type, torch):
                logits = model(torch.from_numpy(features).to(device), torch.from_numpy(valid).to(device))
            flat = valid.reshape(-1)
            scores.append(torch.sigmoid(logits.float()).cpu().numpy().reshape(-1)[flat])
            labels.append(targets.reshape(-1)[flat])
            raw_rows.append(indices.reshape(-1)[flat])
    return {
        "scores": np.concatenate(scores),
        "labels": np.concatenate(labels).astype(np.uint8, copy=False),
        "raw_rows": np.concatenate(raw_rows).astype(np.int64, copy=False),
    }


def entity_aggregate(scores: Any, labels: Any, entities: Any, p_value: float | None) -> tuple[Any, Any, Any]:
    import numpy as np

    unique, inverse = np.unique(entities, return_inverse=True)
    entity_labels = np.zeros(unique.size, dtype=np.uint8)
    np.maximum.at(entity_labels, inverse, labels)
    if p_value is None:
        entity_scores = np.full(unique.size, -np.inf, dtype=np.float64)
        np.maximum.at(entity_scores, inverse, scores)
    else:
        numerator = np.zeros(unique.size, dtype=np.float64)
        count = np.zeros(unique.size, dtype=np.int64)
        np.add.at(numerator, inverse, np.clip(scores, 1e-12, 1.0) ** p_value)
        np.add.at(count, inverse, 1)
        entity_scores = (numerator / count) ** (1.0 / p_value)
    return unique, entity_labels, entity_scores


def terminal_curve(entity_scores: Any, entity_labels: Any) -> list[dict[str, Any]]:
    import numpy as np

    negative = entity_scores[entity_labels == 0]
    positive = entity_scores[entity_labels == 1]
    points = [
        {
            "threshold": None,
            "false_positive_entities": 0,
            "negative_entities": int(negative.size),
            "actual_fpr": 0.0,
            "detected_positive_entities": 0,
            "positive_entities": int(positive.size),
            "detection_rate": 0.0,
        }
    ]
    for threshold in np.unique(negative)[::-1]:
        false_positive = int(np.count_nonzero(negative >= threshold))
        detected = int(np.count_nonzero(positive >= threshold))
        points.append(
            {
                "threshold": float(threshold),
                "false_positive_entities": false_positive,
                "negative_entities": int(negative.size),
                "actual_fpr": false_positive / negative.size,
                "detected_positive_entities": detected,
                "positive_entities": int(positive.size),
                "detection_rate": detected / positive.size,
            }
        )
    return points


def budget_points(curve: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    negative_count = curve[0]["negative_entities"]
    for nominal in DR_FPR_GRID:
        budget = int(negative_count * nominal)
        point = [item for item in curve if item["false_positive_entities"] <= budget][-1]
        result[f"fpr_{nominal:g}"] = {
            **point,
            "nominal_fpr": nominal,
            "integer_false_positive_budget": budget,
            "strictly_within_budget": True,
        }
    return result


def first_alert_curve(
    curve: list[dict[str, Any]],
    scores: Any,
    labels: Any,
    entities: Any,
    times: Any,
    p_value: float | None,
) -> list[dict[str, Any]]:
    import numpy as np

    positive_entities = np.unique(entities[labels == 1])
    output: list[dict[str, Any]] = []
    for point in curve:
        threshold = point["threshold"]
        histogram: dict[int, int] = {}
        for entity in positive_entities:
            positions = np.flatnonzero(entities == entity)
            order = positions[np.argsort(times[positions], kind="stable")]
            ordered_scores = scores[order]
            if threshold is None:
                alerts = np.empty(0, dtype=np.int64)
            elif p_value is None:
                prefix_scores = np.maximum.accumulate(ordered_scores)
                alerts = np.flatnonzero(prefix_scores >= threshold)
            else:
                prefix_scores = (
                    np.cumsum(np.clip(ordered_scores, 1e-12, 1.0) ** p_value)
                    / np.arange(1, ordered_scores.size + 1)
                ) ** (1.0 / p_value)
                alerts = np.flatnonzero(prefix_scores >= threshold)
            if alerts.size:
                exposure = int(alerts[0]) + 1
                histogram[exposure] = histogram.get(exposure, 0) + 1
        cumulative = 0
        staircase = []
        for exposure in sorted(histogram):
            cumulative += histogram[exposure]
            staircase.append(
                {
                    "exposure_index": exposure,
                    "detected_positive_entities": cumulative,
                    "detection_rate": cumulative / len(positive_entities),
                }
            )
        output.append(
            {
                "threshold": threshold,
                "false_positive_entities": point["false_positive_entities"],
                "actual_fpr": point["actual_fpr"],
                "positive_entities": int(len(positive_entities)),
                "detected_positive_entities": cumulative,
                "undetected_positive_entities": int(len(positive_entities) - cumulative),
                "exposure_index_origin": 1,
                "exposure_staircase": staircase,
            }
        )
    return output


def source_metrics(config: dict[str, Any], receipt: dict[str, Any], view: SourceView, device: Any, profile: Any) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import average_precision_score

    started = time.time()
    scored = score_source(config, receipt, view, device, profile)
    entities = np.load(
        artifact_path(view.validate, "source_flow_entity_id"), mmap_mode="r", allow_pickle=False
    )[scored["raw_rows"]]
    times = np.load(
        artifact_path(view.validate, "source_start_time_ns"), mmap_mode="r", allow_pickle=False
    )[scored["raw_rows"]]
    main_p = receipt["selected_p"] if CELLS[receipt["cell"]]["block_auxiliary_objective"] else None
    _, entity_labels, entity_scores = entity_aggregate(scored["scores"], scored["labels"], entities, main_p)
    _, max_labels, max_scores = entity_aggregate(scored["scores"], scored["labels"], entities, None)
    curve = terminal_curve(entity_scores, entity_labels)
    return {
        "flow_average_precision": float(average_precision_score(scored["labels"], scored["scores"])),
        "entity_average_precision": float(average_precision_score(entity_labels, entity_scores)),
        "maximum_entity_average_precision": float(average_precision_score(max_labels, max_scores)),
        "complete_integer_fp_terminal_curve": curve,
        "six_actual_fpr_points": budget_points(curve),
        "first_alert_curve": first_alert_curve(
            curve, scored["scores"], scored["labels"], entities, times, main_p
        ),
        "exposure_index_origin": 1,
        "exposure_semantics": "同一实体稳定时间排序后的有效流序号，不是严格在线墙钟延迟",
        "evaluation_seconds": time.time() - started,
        "pure_inference_and_aggregation_seconds": time.time() - started,
        "peak_process_rss_mib": process_peak_rss_mib(),
        "scores_persisted": False,
        "labels_persisted": False,
        "members_persisted": False,
    }


def write_status(output_root: Path, state: str, stage: str, detail: str) -> None:
    atomic_json(
        output_root / "status.json",
        {
            "schema_version": "ch3-tabular-resnet-status-v2",
            "run_id": RUN_ID,
            "state": state,
            "stage": stage,
            "detail": detail,
            "updated_at_unix": time.time(),
            "target_feature_rows_read": 0,
            "target_label_rows_read": 0,
        },
    )


def build_manifest(output_root: Path) -> None:
    manifest_path = output_root / "manifest.json"
    files: dict[str, Any] = {}
    for path in sorted(output_root.rglob("*")):
        if path.is_file() and path != manifest_path and ".partial." not in path.name:
            relative = str(path.relative_to(output_root))
            files[relative] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    manifest = {
        "schema_version": "ch3-tabular-resnet-manifest-v2",
        "run_id": RUN_ID,
        "files": files,
        "scores_persisted": False,
        "labels_persisted": False,
        "members_persisted": False,
    }
    manifest["manifest_content_sha256"] = canonical_sha256(manifest)
    atomic_json(manifest_path, manifest)
    verified = load_json(manifest_path)
    unsigned = {key: value for key, value in verified.items() if key != "manifest_content_sha256"}
    if verified["manifest_content_sha256"] != canonical_sha256(unsigned):
        raise RuntimeError("末写清单内容 SHA-256 复核失败")
    for relative, item in verified["files"].items():
        path = output_root / relative
        if path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            raise RuntimeError(f"末写清单制品全哈希复核失败：{relative}")


def save_config(config: dict[str, Any], output_root: Path) -> None:
    source = Path(config["_config_path"])
    destination = output_root / "config.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and sha256_file(destination) != sha256_file(source):
        raise RuntimeError("运行配置快照内容 SHA-256 不同")
    if not destination.exists():
        destination.write_bytes(source.read_bytes())


def choose(records: list[dict[str, Any]], field: str) -> dict[str, Any]:
    best = records[0]
    for record in records[1:]:
        if record["validation_flow_ap"] > best["validation_flow_ap"]:
            best = record
    return {"selected": best[field], "records": records, "tie_break": "fixed-table-order"}


def run_select_input(config: dict[str, Any], args: argparse.Namespace) -> None:
    output_root = Path(config["paths"]["output_root"])
    seal_path = output_root / "input-selection-sealed.json"
    if seal_path.is_file():
        if args.resume:
            return
        raise RuntimeError("输入选择封印已存在")
    save_config(config, output_root)
    records = [train_cell(config, "C00", arm, OPTIMIZER_ORDER[0], output_root, args.resume) for arm in ARM_ORDER]
    decision = choose(records, "input_arm")
    decision.update({"schema_version": "ch3-tabular-resnet-input-selection-v2", "target_feature_rows_read": 0, "target_label_rows_read": 0})
    atomic_json(seal_path, decision)
    write_status(output_root, "sealed", "select-input", f"输入臂已封印：{decision['selected']}")
    build_manifest(output_root)


def run_select_optimizer(config: dict[str, Any], args: argparse.Namespace) -> None:
    output_root = Path(config["paths"]["output_root"])
    arm = load_json(output_root / "input-selection-sealed.json")["selected"]
    seal_path = output_root / "optimizer-selection-sealed.json"
    if seal_path.is_file():
        if args.resume:
            return
        raise RuntimeError("优化器选择封印已存在")
    records = [train_cell(config, "C00", arm, key, output_root, args.resume) for key in OPTIMIZER_ORDER]
    decision = choose(records, "optimizer_candidate")
    decision.update({"schema_version": "ch3-tabular-resnet-optimizer-selection-v2", "sealed_input_arm": arm, "target_feature_rows_read": 0, "target_label_rows_read": 0})
    atomic_json(seal_path, decision)
    write_status(output_root, "sealed", "select-optimizer", f"优化器已封印：{decision['selected']}")
    build_manifest(output_root)


def run_cells(config: dict[str, Any], args: argparse.Namespace) -> None:
    output_root = Path(config["paths"]["output_root"])
    arm = load_json(output_root / "input-selection-sealed.json")["selected"]
    optimizer_key = load_json(output_root / "optimizer-selection-sealed.json")["selected"]
    cells_path = output_root / "source-cells-sealed.json"
    qualification_path = Path(config["paths"]["source_qualification_seal"])
    if cells_path.is_file() and qualification_path.is_file():
        if args.resume:
            return
        raise RuntimeError("四格与源资格封印已存在")
    view = SourceView(config, arm)
    device = resolve_device()
    profile = precision_module().get_profile(load_json(precision_contract_path()), PRECISION_PROFILE_ID)
    cells: dict[str, Any] = {}
    for cell in CELL_ORDER:
        selection = train_cell(config, cell, arm, optimizer_key, output_root, args.resume)
        cells[cell] = {"selection": selection, "source_validation": source_metrics(config, selection, view, device, profile)}
    cell_seal = {
        "schema_version": "ch3-tabular-resnet-source-cells-sealed-v2",
        "run_id": RUN_ID,
        "input_arm": arm,
        "optimizer_candidate": optimizer_key,
        "cells": cells,
        "all_four_cells_sealed": set(cells) == set(CELL_ORDER),
        "target_feature_rows_read": 0,
        "target_label_rows_read": 0,
    }
    atomic_json(cells_path, cell_seal)
    input_payload = {
        "arm": arm,
        "source_manifest_sha256": view.train.receipt()["manifest_sha256"],
        "transform_state_sha256": view.transform_state_hash,
        "view_content_sha256": view.view_content_sha256,
    }
    input_arm_sha = canonical_sha256(input_payload)
    atomic_json(
        output_root / "source-input-arm-receipt.json",
        {"schema_version": "ch3-tabular-resnet-source-input-arm-receipt-v2", **input_payload, "source_input_arm_sha256": input_arm_sha},
    )
    qualification = {
        "schema_version": "ch3-protocol-a-source-qualification-seal-v1",
        "source_input_arm_sha256": input_arm_sha,
        "recipe_sha256": FROZEN_RECIPE_SHA256,
        "capacity_sha256": canonical_sha256({"architecture": config["architecture"], "parameter_count": EXPECTED_PARAMETER_COUNT}),
        "checkpoint_sha256": canonical_sha256({cell: cells[cell]["selection"]["checkpoint"]["sha256"] for cell in CELL_ORDER}),
        "mechanism_sha256": canonical_sha256(CELLS),
        "evaluation_code_sha256": sha256_file(Path(__file__)),
        "target_feature_rows_read": 0,
        "target_label_rows_read": 0,
    }
    qualification["seal_sha256"] = canonical_sha256(qualification)
    atomic_json(qualification_path, qualification)
    atomic_json(
        output_root / "source-qualification-seal-receipt.json",
        {
            "schema_version": "ch3-tabular-resnet-source-qualification-seal-receipt-v2",
            "path": str(qualification_path),
            "bytes": qualification_path.stat().st_size,
            "sha256": sha256_file(qualification_path),
            "seal_content_sha256": qualification["seal_sha256"],
        },
    )
    write_status(output_root, "source-qualified", "cells", "四格源年指标已封印并签发源资格封印")
    build_manifest(output_root)


def run_target_evaluate(config: dict[str, Any], _args: argparse.Namespace) -> None:
    raise RuntimeError(
        "当前配置保持目标阻塞；必须由外部主进程注入胜出 Raw 臂、目标清单与资格绑定后生成后续配置，当前入口不得执行"
    )


def validate_swanlab_state_machine(config: dict[str, Any]) -> dict[str, Any]:
    """返回两次上限状态机模板；后续外部目标配置只能按此推进。"""
    return {
        "schema_version": "ch3-tabular-resnet-swanlab-state-v2",
        "maximum_init_attempts": config["swanlab"]["maximum_init_attempts"],
        "allowed_states": ["not-started", "initializing", "failed", "complete"],
        "third_initialization_forbidden": True,
        "label_alias_contract_commit": "89ddecf",
        "resume_state_machine_commits": ["d6313ca", "70a8a2b"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=DISPLAY_NAME)
    parser.add_argument("--config", required=True)
    parser.add_argument(
        "--stage", choices=("select-input", "select-optimizer", "cells", "target-evaluate")
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--validate-config", action="store_true")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = load_json(config_path)
    config["_config_path"] = str(config_path)
    validate_config(config)
    validate_swanlab_state_machine(config)
    if args.validate_config:
        print("配置核验通过")
        return 0
    if args.stage is None:
        print("必须指定 --stage", file=sys.stderr)
        return 2
    dispatch = {
        "select-input": run_select_input,
        "select-optimizer": run_select_optimizer,
        "cells": run_cells,
        "target-evaluate": run_target_evaluate,
    }
    try:
        dispatch[args.stage](config, args)
    except Exception:
        logger.exception("N14 阶段执行失败：%s", args.stage)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
