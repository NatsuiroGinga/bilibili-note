#!/usr/bin/env python3
'''评价 DRIFT 官方检查点在 T17 源验证集上的分数与良性尾部。'''
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pyarrow.parquet as pq
import torch
from sklearn.metrics import average_precision_score, roc_auc_score
from transformers import PreTrainedTokenizerFast

SCHEMA_VERSION = 'ch3-drift-official-checkpoint-t17-eval-v1'
CHARACTERS = 'abcdefghijklmnopqrstuvwxyz0123456789-.'
CHAR_TO_ID = {char: index + 5 for index, char in enumerate(CHARACTERS)}


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


def iter_domains(path: Path, batch_size: int, limit: int | None) -> Iterator[list[str]]:
    emitted = 0
    for batch in pq.ParquetFile(path).iter_batches(batch_size=batch_size, columns=['domain']):
        values = [
            value.strip().lower()
            for value in batch.column(0).to_pylist()
            if isinstance(value, str) and value.strip()
        ]
        if limit is not None:
            values = values[: max(limit - emitted, 0)]
        if values:
            yield values
            emitted += len(values)
        if limit is not None and emitted >= limit:
            return


def encode_char(domains: list[str]) -> torch.Tensor:
    result = np.zeros((len(domains), 77), dtype=np.int64)
    for row, domain in enumerate(domains):
        token_ids = [CHAR_TO_ID.get(char, 1) for char in domain[:75]]
        result[row, 0] = 2
        result[row, 1 : 1 + len(token_ids)] = token_ids
        result[row, 1 + len(token_ids)] = 3
    return torch.from_numpy(result)


def encode_subword(
    domains: list[str], tokenizer: PreTrainedTokenizerFast
) -> torch.Tensor:
    encoded = tokenizer(domains, add_special_tokens=False)['input_ids']
    result = np.zeros((len(domains), 30), dtype=np.int64)
    for row, token_ids in enumerate(encoded):
        token_ids = token_ids[:28]
        result[row, 0] = 2
        result[row, 1 : 1 + len(token_ids)] = token_ids
        result[row, 1 + len(token_ids)] = 3
    return torch.from_numpy(result)


def load_model(reference_root: Path, checkpoint: Path, device: torch.device):
    sys.path.insert(0, str(reference_root))
    from model import FineTuningModel, PretrainedModel

    token_backbone = PretrainedModel(30522, 256, 8, 768, 12, 30)
    char_backbone = PretrainedModel(43, 256, 8, 768, 12, 77)
    model = FineTuningModel(token_backbone, char_backbone, clf_norm='pool')
    state = torch.load(checkpoint, map_location='cpu', weights_only=True)
    model.load_state_dict(state, strict=True)
    model.eval().to(device)
    return model


def evaluate(
    model,
    tokenizer: PreTrainedTokenizerFast,
    files: list[tuple[Path, int]],
    device: torch.device,
    batch_size: int,
    limit: int | None,
) -> tuple[np.ndarray, np.ndarray, int]:
    scores: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    rows = 0
    use_bf16 = device.type == 'cuda'
    with torch.inference_mode():
        for path, label in files:
            for domains in iter_domains(path, batch_size, limit):
                token_ids = encode_subword(domains, tokenizer).to(device, non_blocking=True)
                char_ids = encode_char(domains).to(device, non_blocking=True)
                with torch.autocast(
                    device_type=device.type,
                    dtype=torch.bfloat16,
                    enabled=use_bf16,
                ):
                    logits = model(token_ids, char_ids)
                probabilities = torch.softmax(logits.float(), dim=1)[:, 1]
                scores.append(probabilities.cpu().numpy())
                labels.append(np.full(len(domains), label, dtype=np.int8))
                rows += len(domains)
                if rows % 100000 < len(domains):
                    print(
                        json.dumps({'stage': 'eval', 'rows': rows}, ensure_ascii=False),
                        file=sys.stderr,
                        flush=True,
                    )
    return np.concatenate(labels), np.concatenate(scores), rows


def binary_metrics(labels: np.ndarray, scores: np.ndarray) -> dict[str, Any]:
    predictions = scores >= 0.5
    positive = labels == 1
    negative = ~positive
    tp = int(np.sum(predictions & positive))
    tn = int(np.sum(~predictions & negative))
    fp = int(np.sum(predictions & negative))
    fn = int(np.sum(~predictions & positive))
    quantiles = [0.5, 0.9, 0.99, 0.999, 0.9999]
    return {
        'auroc': float(roc_auc_score(labels, scores)),
        'average_precision': float(average_precision_score(labels, scores)),
        'threshold_0_5': {
            'tp': tp,
            'tn': tn,
            'fp': fp,
            'fn': fn,
            'fpr': fp / max(fp + tn, 1),
            'fnr': fn / max(fn + tp, 1),
        },
        'score_quantiles': {
            'benign': {str(q): float(np.quantile(scores[negative], q)) for q in quantiles},
            'dga': {str(q): float(np.quantile(scores[positive], q)) for q in quantiles},
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--batch-size', type=int, default=1024)
    parser.add_argument('--max-per-class', type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = time.monotonic()
    root = args.project_root.resolve()
    data_root = root / 'runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521/DRIFT_input_eSLD'
    reference_root = root / 'runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2'
    checkpoint = root / 'runs/models/drift-official-dsn2026/finetuning.pt'
    tokenizer_path = reference_root / 'artifacts/tokenizer/tokenizer-0-30522-both.json'
    files = [
        (data_root / 'T17_benign_val.parquet', 0),
        (data_root / 'T17_dga_val.parquet', 1),
    ]
    for path in [reference_root / 'model.py', checkpoint, tokenizer_path, *(x[0] for x in files)]:
        if not path.is_file():
            raise FileNotFoundError(f'必需文件不存在：{path}')
    if args.batch_size <= 0:
        raise ValueError('batch-size 必须为正数')
    if args.max_per_class is not None and args.max_per_class <= 0:
        raise ValueError('max-per-class 必须为正数')
    device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
    tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(tokenizer_path))
    model = load_model(reference_root, checkpoint, device)
    labels, scores, rows = evaluate(
        model, tokenizer, files, device, args.batch_size, args.max_per_class
    )
    output = {
        'schema_version': SCHEMA_VERSION,
        'status': 'completed',
        'run_identity': 'ch3-drift-official-checkpoint-t17-source-eval-v1',
        'screening_only': True,
        'data_role': 'T17 source validation only; no T20-T25 access',
        'inputs': [
            {
                'path': str(path),
                'label': label,
                'rows': pq.ParquetFile(path).metadata.num_rows,
                'sha256': sha256_file(path),
            }
            for path, label in files
        ],
        'artifacts': {
            'reference_model_py': str(reference_root / 'model.py'),
            'reference_model_py_sha256': sha256_file(reference_root / 'model.py'),
            'checkpoint': str(checkpoint),
            'checkpoint_sha256': sha256_file(checkpoint),
            'tokenizer': str(tokenizer_path),
            'tokenizer_sha256': sha256_file(tokenizer_path),
        },
        'model': {
            'parameters': sum(parameter.numel() for parameter in model.parameters()),
            'strict_checkpoint_load': True,
        },
        'evaluation': {
            'rows': rows,
            'labels': {
                'benign': int(np.sum(labels == 0)),
                'dga': int(np.sum(labels == 1)),
            },
            'metrics': binary_metrics(labels, scores),
        },
        'runtime': {
            'elapsed_seconds': time.monotonic() - start,
            'device': str(device),
            'torch_version': torch.__version__,
            'cuda_version': torch.version.cuda,
            'batch_size': args.batch_size,
            'bf16_autocast': device.type == 'cuda',
            'max_memory_allocated_bytes': torch.cuda.max_memory_allocated() if device.type == 'cuda' else None,
        },
    }
    atomic_json(args.output, output)
    print(json.dumps({'status': 'completed', 'output': str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
