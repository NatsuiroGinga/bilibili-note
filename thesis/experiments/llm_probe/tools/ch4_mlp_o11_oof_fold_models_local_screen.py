# -*- coding: utf-8 -*-
"""第四章 D0 本机筛选支线：全容量 MLP O11 三折折外模型（screening_only）。

服务器 cgroup 内存被压到 2GiB 期间的本机替代：在 Apple 芯片（MPS，回退 CPU）
上以 fp32 训练三折折外 O11 模型，供 D1/D2 病灶再确认的筛选级裁决。

精度选择依据（2026-08-27 本机实测，20 步均值）：fp32 67.0ms/步、bf16-autocast
87.1ms/步（M1 无 bf16 硬件单元，模拟反而慢 30%）、fp16 55.3ms/步（数值偏离最大，
正式合同仅作例外）。故取 fp32——本硬件上快于 bf16 且最贴近正式 profile 的
FP32 敏感岛。

证据边界：``screening_only=true``，结果不进论文正式结果；正式 D0 在服务器资源
恢复后按冻结 CUDA-BF16 合同以 ``ch4-mlp-o11-oof-fold-models-seed42-v1`` 身份重跑。
折分配逻辑与正式 D0 同构（E1 两层哈希构造），落盘折哈希供事后对账。
训练配方数值全部继承冻结 bf16 合同（seed42、8x512、lr 3.162e-4、批 64、
1000 步/epoch、逐 epoch 实体不相交验证集 argmax 选择）；筛选训练预算 10 epoch/折
（对齐父封印 selected_epoch=10）。LSPR24 零读取（目标年文件未拉取到本机）。
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import average_precision_score

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch4_mlp_o11_oof_fold_models as d0

RUN_ID = "ch4-mlp-o11-oof-fold-models-local-screen-v1"
FOLD_COUNT = 3
SEED = 42
SEQ_LEN = 128
BATCH = 64
STEPS_PER_EPOCH = 1000
LEARNING_RATE = 0.0003162277660168379
WEIGHT_DECAY = 0.0
DROPOUT = 0.1
GRAD_CLIP = 1.0
AUX_WEIGHT = 1.0
HIDDEN_DEPTH = 8
HIDDEN_SIZE = 512
PARAM_COUNT = 2_144_258
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


class LocalFullMLP(torch.nn.Module):
    """与正式 bf16 全容量 MLP 同构（fp32、无精度运行时）。"""

    def __init__(self, aggregate: bool):
        super().__init__()
        self.aggregate = aggregate
        layers: list[Any] = []
        size = 83
        for _ in range(HIDDEN_DEPTH - 1):
            layers += [torch.nn.Linear(size, HIDDEN_SIZE), torch.nn.ReLU(), torch.nn.Dropout(DROPOUT)]
            size = HIDDEN_SIZE
        self.encoder = torch.nn.Sequential(*layers)
        self.fusion = torch.nn.Sequential(
            torch.nn.Linear(HIDDEN_SIZE * 2, HIDDEN_SIZE), torch.nn.ReLU(), torch.nn.Dropout(DROPOUT)
        )
        self.output = torch.nn.Linear(HIDDEN_SIZE, 1)
        self.p_log = torch.nn.Parameter(torch.tensor(float(math.log(2.0)), dtype=torch.float32))

    @property
    def p(self) -> torch.Tensor:
        return torch.exp(self.p_log).clamp(1e-3, 1e3)

    def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
        mask = valid.to(values.dtype)
        hidden = self.encoder(values) * mask.unsqueeze(-1)
        if self.aggregate:
            count = torch.cumsum(mask, 1).clamp(min=1.0).unsqueeze(-1)
            context = torch.cumsum(hidden, 1) / count * mask.unsqueeze(-1)
        else:
            context = torch.zeros_like(hidden)
        fused = self.fusion(torch.cat((hidden, context), dim=-1))
        return self.output(fused * mask.unsqueeze(-1)).squeeze(-1)


def lp_pool(scores: torch.Tensor, mask: torch.Tensor, p_value: torch.Tensor) -> torch.Tensor:
    log_scores = torch.log(scores.clamp(min=1e-7))
    count = mask.sum(1).clamp(min=1.0)
    summed = torch.logsumexp((p_value * log_scores).masked_fill(mask < 0.5, -1e30), 1)
    return torch.exp((summed - torch.log(count)) / p_value)


def source_split(entity: np.ndarray, timestamp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """与 legacy.source_split 同构（seed42、10% 验证实体、15% 时间尾排除）。"""
    unique_entity = np.unique(entity)
    permutation = np.random.RandomState(SEED).permutation(len(unique_entity))
    count = max(1, int(len(unique_entity) * 0.1))
    validation_entities = set(unique_entity[permutation[:count]].tolist())
    entity_mask = np.fromiter((value in validation_entities for value in entity), bool, len(entity))
    time_cut = np.quantile(timestamp, 1.0 - 0.15)
    time_mask = timestamp >= time_cut
    train_rows = np.flatnonzero(~(entity_mask | time_mask))
    validation_rows = np.flatnonzero(entity_mask & ~time_mask)
    stats = (len(unique_entity), len(train_rows), len(validation_rows))
    if stats != (150_680, 208_598, 22_444):
        raise RuntimeError(f"协议 A 源年切分统计不符：{stats}")
    return train_rows, validation_rows


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f"{path.name}.partial")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def prepare(cache_root: Path) -> dict[str, Any]:
    source: dict[str, np.ndarray] = {}
    for name in ("y23", "I23", "M23", "E23", "T23"):
        source[name] = np.load(cache_root / f"{name}.npy")
    entity_labels = d0.entity_labels_from_source(source)
    if len(entity_labels) != 150_680 or int(entity_labels.sum()) != 239:
        raise RuntimeError(f"实体规模或正实体数不符：{len(entity_labels)}/{int(entity_labels.sum())}")
    fold_of_entity = d0.make_entity_folds(entity_labels, SEED, FOLD_COUNT)
    inner = json.dumps(
        {
            "dtype": str(fold_of_entity.dtype),
            "shape": list(fold_of_entity.shape),
            "sha256": d0.sha256_array(fold_of_entity),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    import hashlib

    fold_sha = hashlib.sha256(inner.encode("utf-8")).hexdigest()
    train_rows, validation_rows = source_split(source["E23"], source["T23"])
    return {
        "source": source,
        "entity_labels": entity_labels,
        "fold_of_entity": fold_of_entity,
        "fold_sha": fold_sha,
        "train_rows": train_rows,
        "validation_rows": validation_rows,
    }


def train_fold(
    context: dict[str, Any],
    X: np.ndarray,
    fold: int,
    epochs: int,
    device: torch.device,
    output_root: Path,
) -> dict[str, Any]:
    source = context["source"]
    I23, M23, y23, E23 = source["I23"], source["M23"], source["y23"], source["E23"]
    fold_of_entity = context["fold_of_entity"]
    train_rows_all = context["train_rows"]
    validation_rows = context["validation_rows"]
    keep = fold_of_entity[E23[train_rows_all]] != fold
    train_rows = train_rows_all[keep]

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    model = LocalFullMLP(aggregate=True).to(device)
    actual = sum(parameter.numel() for parameter in model.parameters())
    if actual != PARAM_COUNT:
        raise RuntimeError(f"参数量不符：{actual}")
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    generator = torch.Generator().manual_seed(SEED)

    train_indices = I23[train_rows]
    train_mask = M23[train_rows] > 0
    train_labels = y23[train_indices]
    valid_train_labels = train_labels[train_mask]
    sequence_labels = (train_labels * train_mask).max(1) > 0
    sequence_positive_weight = float((1 - sequence_labels.mean()) / max(sequence_labels.mean(), 1e-8))
    flow_positive_rate = float(valid_train_labels.mean())
    positive_weight = torch.tensor([(1 - flow_positive_rate) / flow_positive_rate], device=device)

    best_ap, best_epoch, best_p, best_state = -1.0, 0, float("nan"), None
    history: list[dict[str, Any]] = []
    started = time.time()
    model.train()
    for epoch in range(1, epochs + 1):
        running_loss = 0.0
        for step in range(1, STEPS_PER_EPOCH + 1):
            positions = torch.randint(0, len(train_rows), (BATCH,), generator=generator).numpy()
            rows = train_rows[positions]
            indices = I23[rows][:, :SEQ_LEN]
            valid_np = M23[rows][:, :SEQ_LEN] > 0
            values = torch.from_numpy(X[indices.reshape(-1)]).reshape(BATCH, SEQ_LEN, 83).to(device)
            labels = torch.from_numpy(y23[indices.reshape(-1)].reshape(indices.shape)).to(device)
            valid = torch.from_numpy(valid_np).to(device)
            mask = valid.float()
            valid_units = float(mask.sum())
            optimizer.zero_grad(set_to_none=True)
            logits = model(values, valid)
            flow_loss_sum = torch.nn.functional.binary_cross_entropy_with_logits(
                logits, labels.float(), reduction="none", pos_weight=positive_weight
            ).mul(mask).sum()
            probabilities = torch.sigmoid(logits)
            pooled = lp_pool(probabilities, mask, model.p).clamp(1e-6, 1 - 1e-6)
            auxiliary_labels = (labels.float() * mask).amax(-1)
            weights = 1.0 + (sequence_positive_weight - 1.0) * auxiliary_labels
            auxiliary_sum = torch.nn.functional.binary_cross_entropy(
                pooled, auxiliary_labels, reduction="none"
            ).mul(weights).sum()
            loss = (flow_loss_sum + AUX_WEIGHT * auxiliary_sum * valid_units / weights.sum()) / valid_units
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            optimizer.step()
            running_loss += float(loss.detach())
            if step % 250 == 0:
                elapsed = time.time() - started
                done = (epoch - 1) * STEPS_PER_EPOCH + step
                total = epochs * STEPS_PER_EPOCH
                log(f"fold{fold} epoch={epoch}/{epochs} step={step} 剩余约={(elapsed / done) * (total - done) / 60:.1f}分")
        model.eval()
        predictions: list[np.ndarray] = []
        label_chunks: list[np.ndarray] = []
        with torch.no_grad():
            for start in range(0, len(validation_rows), 1024):
                rows = validation_rows[start : start + 1024]
                indices = I23[rows][:, :SEQ_LEN]
                valid_np = M23[rows][:, :SEQ_LEN] > 0
                values = torch.from_numpy(X[indices.reshape(-1)]).reshape(len(rows), SEQ_LEN, 83).to(device)
                valid = torch.from_numpy(valid_np).to(device)
                probabilities = torch.sigmoid(model(values, valid))
                flat_mask = valid_np.reshape(-1)
                predictions.append(probabilities.reshape(-1).cpu().numpy()[flat_mask])
                label_chunks.append(y23[indices.reshape(-1)][flat_mask])
        model.train()
        validation_ap = float(average_precision_score(np.concatenate(label_chunks), np.concatenate(predictions)))
        p_value = float(model.p.detach())
        history.append({"epoch": epoch, "validation_flow_ap": validation_ap, "p": p_value,
                        "mean_training_loss": running_loss / STEPS_PER_EPOCH})
        log(f"fold{fold} epoch={epoch}/{epochs} 验证逐流AP={validation_ap:.8f} p={p_value:.6f}")
        if validation_ap > best_ap:
            best_ap, best_epoch, best_p = validation_ap, epoch, p_value
            best_state = {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}
    if best_state is None:
        raise RuntimeError(f"fold{fold} 未产生可选检查点")
    checkpoint_path = output_root / "checkpoints" / f"selected-O11-fold{fold}.pt"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"schema_version": "ch4-mlp-o11-local-screen-checkpoint-v1", "run_id": RUN_ID,
                "fold": fold, "model": best_state, "precision": "fp32",
                "device_type": device.type, "screening_only": True}, checkpoint_path)
    return {
        "fold": fold,
        "oof_entities": int((context["fold_of_entity"] == fold).sum()),
        "oof_positive_entities": int(context["entity_labels"][context["fold_of_entity"] == fold].sum()),
        "train_sequences": int(len(train_rows)),
        "selected_epoch": best_epoch,
        "validation_flow_ap": best_ap,
        "p_at_selection": best_p,
        "history": history,
        "training_seconds": time.time() - started,
        "checkpoint": str(checkpoint_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="第四章 D0 本机筛选：O11 三折折外模型（fp32）")
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument("--output-root", default=f"runs/diagnostics/{RUN_ID}")
    parser.add_argument("--fold", type=int, choices=(0, 1, 2))
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--prep-only", action="store_true", help="只验证折分配与切分，不训练")
    args = parser.parse_args()
    cache_root = Path(args.cache_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    context = prepare(cache_root)
    receipt = {
        "schema_version": "ch4-mlp-o11-local-screen-fold-assignment-v1",
        "run_id": RUN_ID,
        "screening_only": True,
        "formal_paper_evidence": False,
        "target_year_arrays_read": 0,
        "precision": "fp32",
        "fold_assignment_sha256": context["fold_sha"],
        "epochs_per_fold": args.epochs,
        "per_fold": {},
    }
    log(f"折分配哈希 {context['fold_sha'][:16]}…；切分核验通过（150680/208598/22444）")
    if args.prep_only:
        atomic_json(output_root / "fold-assignment-receipt.json", receipt)
        print("PREP_OK")
        return 0

    X = np.load(cache_root / "X23.npy")
    if X.shape != (16_353_511, 83):
        raise RuntimeError(f"X23 形状不符：{X.shape}")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    log(f"设备 {device.type}，fp32，X 常驻 CPU 内存逐批上卡")
    folds = (args.fold,) if args.fold is not None else tuple(range(FOLD_COUNT))
    for k in folds:
        receipt["per_fold"][str(k)] = train_fold(context, X, k, args.epochs, device, output_root)
        atomic_json(output_root / "fold-assignment-receipt.json", receipt)
        log(f"fold{k} 完成并落盘收据")
    print("LOCAL_SCREEN_D0_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
