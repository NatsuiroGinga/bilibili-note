#!/usr/bin/env python3
'''在 DRIFT 源期运行公开 B-ResNet 配方并诊断良性高分尾部。'''
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import sklearn
import torch
from sklearn.metrics import average_precision_score, roc_auc_score
from torch import nn

SCHEMA_VERSION = 'ch3-drift-bresnet-source-tail-diagnostic-v1'
DATASET_REVISION = '3b31077020cd1c013d0a75cad51042a2327c4521'
Z_95 = 1.959963984540054
CHARACTERS = 'abcdefghijklmnopqrstuvwxyz0123456789-_.'
CHAR_TO_ID = {char: index + 1 for index, char in enumerate(CHARACTERS)}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + '.partial')
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    partial.replace(path)


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding='utf-8'))
    if config.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('配置 schema_version 不匹配')
    if config.get('dataset_revision') != DATASET_REVISION:
        raise ValueError('数据 revision 不匹配')
    if config.get('screening_only') is not True:
        raise ValueError('本入口必须保持 screening_only=true')
    model = config['model']
    expected = {
        'max_length': 253,
        'vocabulary_size': 40,
        'embedding_dim': 128,
        'filters': 128,
        'kernel_sizes': [4, 4],
        'pool_size': 4,
    }
    for key, value in expected.items():
        if model.get(key) != value:
            raise ValueError(f'B-ResNet 配方字段不匹配：{key}')
    training = config['training']
    if training['epochs'] != 1 or training['batch_size'] != 128:
        raise ValueError('公开筛选配方固定一轮与 batch_size=128')
    return config


class BResNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.embedding = nn.Embedding(40, 128, padding_idx=0)
        self.conv1 = nn.Conv1d(128, 128, kernel_size=4, padding='same')
        self.conv2 = nn.Conv1d(128, 128, kernel_size=4, padding='same')
        self.pool = nn.MaxPool1d(kernel_size=4, stride=4, ceil_mode=True)
        self.classifier = nn.Linear(128 * 64, 1)
        self.reset_parameters()

    def reset_parameters(self) -> None:
        nn.init.uniform_(self.embedding.weight, -0.05, 0.05)
        with torch.no_grad():
            self.embedding.weight[0].zero_()
        for layer in (self.conv1, self.conv2, self.classifier):
            nn.init.xavier_uniform_(layer.weight)
            nn.init.zeros_(layer.bias)

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        values = self.embedding(token_ids).transpose(1, 2)
        residual = values
        values = self.conv1(values)
        values = torch.relu(values)
        values = self.conv2(values)
        values = torch.relu(values + residual)
        values = self.pool(values)
        if values.shape[-1] != 64:
            raise RuntimeError('B-ResNet 池化长度不为 64')
        return self.classifier(values.flatten(1)).squeeze(1)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def iter_batches(path: Path, rows: int) -> Iterator[list[str]]:
    for batch in pq.ParquetFile(path).iter_batches(batch_size=rows, columns=['domain']):
        yield [
            value.strip().lower()
            for value in batch.column(0).to_pylist()
            if isinstance(value, str) and value.strip()
        ]


def encode_domains(domains: list[str], max_length: int = 253) -> torch.Tensor:
    encoded = np.zeros((len(domains), max_length), dtype=np.int64)
    for row, domain in enumerate(domains):
        ids = np.fromiter(
            (CHAR_TO_ID[char] for char in domain if char in CHAR_TO_ID),
            dtype=np.int64,
        )
        ids = ids[-max_length:]
        if len(ids):
            encoded[row, -len(ids) :] = ids
    return torch.from_numpy(encoded)


def splitmix64(values: np.ndarray) -> np.ndarray:
    values = (values + np.uint64(0x9E3779B97F4A7C15)).astype(np.uint64)
    values = (values ^ (values >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    values = (values ^ (values >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return values ^ (values >> np.uint64(31))


def selected_domains(
    path: Path,
    requested: int,
    seed: int,
    io_rows: int,
    full: bool,
    pilot: int | None,
) -> tuple[list[str], dict[str, Any]]:
    metadata_rows = pq.ParquetFile(path).metadata.num_rows
    target = min(pilot, metadata_rows) if pilot is not None else min(requested, metadata_rows)
    probability = 1.0 if full or pilot is not None else target / metadata_rows
    domains: list[str] = []
    scanned = 0
    for batch in pq.ParquetFile(path).iter_batches(batch_size=io_rows, columns=['domain']):
        if pilot is not None:
            indices = np.arange(min(batch.num_rows, max(target - len(domains), 0)), dtype=np.int64)
        elif probability >= 1.0:
            indices = np.arange(batch.num_rows, dtype=np.int64)
        else:
            row_ids = np.arange(scanned, scanned + batch.num_rows, dtype=np.uint64)
            threshold = np.uint64(min((1 << 64) - 1, int(probability * (1 << 64))))
            indices = np.flatnonzero(splitmix64(row_ids ^ np.uint64(seed)) < threshold)
        values = batch.column(0).take(pa.array(indices)).to_pylist()
        domains.extend(
            value.strip().lower()
            for value in values
            if isinstance(value, str) and value.strip()
        )
        scanned += batch.num_rows
        if pilot is not None and len(domains) >= target:
            break
    return domains, {
        'metadata_rows': metadata_rows,
        'requested': target,
        'actual': len(domains),
        'probability': probability,
        'seed': seed,
        'actual_worst_case_half_width_95': Z_95 * math.sqrt(0.25 / max(len(domains), 1)),
    }


def save_checkpoint(
    path: Path,
    model: BResNet,
    optimizer: torch.optim.Optimizer,
    completed_io_batch: int,
    examples_seen: int,
    config_sha256: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + '.partial')
    torch.save(
        {
            'model': model.state_dict(),
            'optimizer': optimizer.state_dict(),
            'completed_io_batch': completed_io_batch,
            'examples_seen': examples_seen,
            'config_sha256': config_sha256,
        },
        partial,
    )
    partial.replace(path)


def train(
    model: BResNet,
    optimizer: torch.optim.Optimizer,
    benign_path: Path,
    dga_path: Path,
    device: torch.device,
    config: dict[str, Any],
    config_sha256: str,
    checkpoint: Path,
    resume: bool,
    pilot: int | None,
) -> dict[str, Any]:
    start_batch = 0
    examples_seen = 0
    if resume and checkpoint.is_file():
        state = torch.load(checkpoint, map_location='cpu', weights_only=True)
        if state.get('config_sha256') != config_sha256:
            raise ValueError('断点配置哈希不匹配')
        model.load_state_dict(state['model'], strict=True)
        optimizer.load_state_dict(state['optimizer'])
        start_batch = int(state['completed_io_batch']) + 1
        examples_seen = int(state['examples_seen'])
    training = config['training']
    io_rows = int(training['io_rows_per_class'])
    batch_size = int(training['batch_size'])
    use_bf16 = device.type == 'cuda' and bool(training['cuda_bf16_autocast'])
    losses: list[float] = []
    started = time.monotonic()
    benign_iter = iter_batches(benign_path, io_rows)
    dga_iter = iter_batches(dga_path, io_rows)
    for io_index, pair in enumerate(itertools.zip_longest(benign_iter, dga_iter, fillvalue=[])):
        if io_index < start_batch:
            continue
        benign, dga = pair
        if pilot is not None:
            remaining = max(pilot - examples_seen // 2, 0)
            benign = benign[:remaining]
            dga = dga[:remaining]
        domains = benign + dga
        labels = np.concatenate(
            [np.zeros(len(benign), dtype=np.float32), np.ones(len(dga), dtype=np.float32)]
        )
        if not domains:
            break
        order = np.random.default_rng(config['seed'] + io_index).permutation(len(domains))
        encoded = encode_domains([domains[index] for index in order])
        labels_tensor = torch.from_numpy(labels[order])
        for offset in range(0, len(domains), batch_size):
            inputs = encoded[offset : offset + batch_size].to(device, non_blocking=True)
            targets = labels_tensor[offset : offset + batch_size].to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=use_bf16):
                logits = model(inputs)
                loss = nn.functional.binary_cross_entropy_with_logits(logits, targets)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
        examples_seen += len(domains)
        save_checkpoint(checkpoint, model, optimizer, io_index, examples_seen, config_sha256)
        print(
            json.dumps(
                {
                    'stage': 'train',
                    'io_batch': io_index,
                    'examples_seen': examples_seen,
                    'loss': losses[-1],
                    'elapsed_seconds': time.monotonic() - started,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
            flush=True,
        )
        if pilot is not None and examples_seen >= 2 * pilot:
            break
    return {
        'examples_seen': examples_seen,
        'steps': len(losses),
        'mean_loss': float(np.mean(losses)) if losses else None,
        'last_loss': losses[-1] if losses else None,
        'wall_seconds': time.monotonic() - started,
        'resumed_from_io_batch': start_batch if start_batch else None,
    }


def predict(model: BResNet, domains: list[str], device: torch.device, batch_size: int) -> np.ndarray:
    values: list[np.ndarray] = []
    use_bf16 = device.type == 'cuda'
    model.eval()
    with torch.inference_mode():
        for offset in range(0, len(domains), batch_size):
            inputs = encode_domains(domains[offset : offset + batch_size]).to(device, non_blocking=True)
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=use_bf16):
                logits = model(inputs)
            values.append(torch.sigmoid(logits.float()).cpu().numpy())
    model.train()
    return np.concatenate(values) if values else np.empty(0, dtype=np.float32)


def confusion(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, Any]:
    predictions = scores >= threshold
    positive = labels == 1
    negative = ~positive
    tp = int(np.sum(predictions & positive))
    tn = int(np.sum(~predictions & negative))
    fp = int(np.sum(predictions & negative))
    fn = int(np.sum(~predictions & positive))
    return {
        'threshold': threshold,
        'tp': tp,
        'tn': tn,
        'fp': fp,
        'fn': fn,
        'fpr': fp / max(fp + tn, 1),
        'fnr': fn / max(fn + tp, 1),
        'tpr': tp / max(tp + fn, 1),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--pilot-per-class', type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    config = load_config(args.config)
    set_seed(int(config['seed']))
    torch.set_float32_matmul_precision('high')
    root = args.project_root.resolve()
    run_dir = args.run_dir.resolve()
    data_root = root / config['data_root']
    source_code = root / config['source_code']
    config_hash = sha256_file(args.config)
    if not source_code.is_file():
        raise FileNotFoundError(f'公开 B-ResNet 源码不存在：{source_code}')
    train_items = config['data']['train']
    eval_items = config['data']['evaluation']
    all_paths = [data_root / item['path'] for item in [*train_items, *eval_items]]
    for path in all_paths:
        if not path.is_file():
            raise FileNotFoundError(f'数据文件不存在：{path}')
    device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
    model = BResNet().to(device)
    if sum(parameter.numel() for parameter in model.parameters()) >= 1_000_000:
        raise ValueError('本机筛选模型参数量超出一百万上限')
    training = config['training']
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=float(training['learning_rate']),
        betas=tuple(training['betas']),
        eps=float(training['epsilon']),
        weight_decay=float(training['weight_decay']),
    )
    checkpoint = run_dir / 'checkpoint.pt'
    training_result = train(
        model,
        optimizer,
        data_root / train_items[0]['path'],
        data_root / train_items[1]['path'],
        device,
        config,
        config_hash,
        checkpoint,
        args.resume,
        args.pilot_per_class,
    )
    scores_by_year: dict[str, list[np.ndarray]] = {}
    labels_by_year: dict[str, list[np.ndarray]] = {}
    sampling: dict[str, Any] = {}
    for item in eval_items:
        path = data_root / item['path']
        seed_material = f'{DATASET_REVISION}|{item["year"]}|{item["label"]}|{item["path"]}'
        seed = int.from_bytes(hashlib.sha256(seed_material.encode()).digest()[:8], 'little')
        domains, sample = selected_domains(
            path,
            int(config['sampling']['evaluation_per_class']),
            seed,
            int(training['io_rows_per_class']),
            bool(item['full']),
            args.pilot_per_class,
        )
        scores = predict(model, domains, device, int(training['batch_size']))
        scores_by_year.setdefault(item['year'], []).append(scores)
        labels_by_year.setdefault(item['year'], []).append(
            np.full(len(scores), int(item['label']), dtype=np.int8)
        )
        sampling[f'{item["year"]}:{item["label"]}'] = sample
    anchors = [float(value) for value in config['diagnostic_fpr_anchors']['values']]
    source_benign = scores_by_year['T17'][0]
    thresholds = {str(anchor): float(np.quantile(source_benign, 1 - anchor)) for anchor in anchors}
    metrics: dict[str, Any] = {}
    quantiles = [0.5, 0.9, 0.99, 0.999, 0.9999]
    for year in ('T17', 'T18', 'T19'):
        labels = np.concatenate(labels_by_year[year])
        scores = np.concatenate(scores_by_year[year])
        benign_scores = scores[labels == 0]
        dga_scores = scores[labels == 1]
        metrics[year] = {
            'samples': {'benign': len(benign_scores), 'dga': len(dga_scores)},
            'auroc': float(roc_auc_score(labels, scores)),
            'average_precision_balanced_sample': float(average_precision_score(labels, scores)),
            'threshold_0_5': confusion(labels, scores, 0.5),
            'source_threshold_transfer': {
                key: confusion(labels, scores, threshold) for key, threshold in thresholds.items()
            },
            'score_quantiles': {
                'benign': {str(q): float(np.quantile(benign_scores, q)) for q in quantiles},
                'dga': {str(q): float(np.quantile(dga_scores, q)) for q in quantiles},
            },
        }
    output = {
        'schema_version': SCHEMA_VERSION,
        'status': 'completed',
        'run_identity': config['run_identity'],
        'screening_only': True,
        'mechanism_adjudication': args.pilot_per_class is None,
        'dataset_revision': DATASET_REVISION,
        'config_sha256': config_hash,
        'source_code': {
            'path': str(source_code),
            'sha256': sha256_file(source_code),
            'commit': '7efed21b8cf12efaf6b2ffb8de3c939319a54f31',
        },
        'model': {
            'name': 'B-ResNet PyTorch faithful port',
            'parameters': sum(parameter.numel() for parameter in model.parameters()),
            'recipe': config['model'],
        },
        'inputs': [
            {
                'path': str(path),
                'rows': pq.ParquetFile(path).metadata.num_rows,
                'bytes': path.stat().st_size,
                'sha256': sha256_file(path),
            }
            for path in all_paths
        ],
        'training': training_result,
        'sampling': sampling,
        'source_thresholds': thresholds,
        'diagnostic_fpr_anchors': config['diagnostic_fpr_anchors'],
        'metrics': metrics,
        'runtime': {
            'elapsed_seconds': time.monotonic() - started,
            'device': str(device),
            'torch_version': torch.__version__,
            'cuda_version': torch.version.cuda,
            'sklearn_version': sklearn.__version__,
            'bf16_autocast': device.type == 'cuda' and bool(training['cuda_bf16_autocast']),
            'max_memory_allocated_bytes': torch.cuda.max_memory_allocated() if device.type == 'cuda' else None,
        },
        'interpretation_boundary': '本运行只裁决源期病灶与是否值得实现候选损失，不进入论文正式结果。',
    }
    atomic_json(run_dir / 'result.json', output)
    print(json.dumps({'status': 'completed', 'run_dir': str(run_dir)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
