#!/usr/bin/env python3
'''复用 B-ResNet 源期检查点，诊断良恶域名形态组错误。'''
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

import ch3_drift_bresnet_source_tail_diagnostic as base

SCHEMA_VERSION = 'ch3-drift-bresnet-morphology-diagnostic-v1'


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + '.partial')
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    partial.replace(path)


def composition_group(domain: str) -> str:
    if domain.isalpha():
        return 'pure_alpha'
    if any(char.isdigit() for char in domain):
        return 'contains_digit'
    if '-' in domain:
        return 'contains_hyphen_without_digit'
    return 'other'


def length_group(length: int, boundaries: tuple[int, int, int]) -> str:
    q25, q50, q75 = boundaries
    if length <= q25:
        return 'q1_shortest'
    if length <= q50:
        return 'q2'
    if length <= q75:
        return 'q3'
    return 'q4_longest'


def summarize_group(
    scores: np.ndarray,
    label: int,
    thresholds: dict[str, float],
) -> dict[str, Any]:
    if not len(scores):
        return {'count': 0}
    result: dict[str, Any] = {
        'count': len(scores),
        'score_mean': float(np.mean(scores)),
        'score_quantiles': {
            '0.5': float(np.quantile(scores, 0.5)),
            '0.9': float(np.quantile(scores, 0.9)),
            '0.99': float(np.quantile(scores, 0.99)),
            '0.999': float(np.quantile(scores, 0.999)),
        },
    }
    if label == 0:
        result['fpr_at_0_5'] = float(np.mean(scores >= 0.5))
        result['fpr_at_source_threshold'] = {
            key: float(np.mean(scores >= threshold))
            for key, threshold in thresholds.items()
        }
    else:
        result['fnr_at_0_5'] = float(np.mean(scores < 0.5))
        result['fnr_at_source_threshold'] = {
            key: float(np.mean(scores < threshold))
            for key, threshold in thresholds.items()
        }
    return result


def grouped_summary(
    domains: list[str],
    scores: np.ndarray,
    label: int,
    thresholds: dict[str, float],
    boundaries: tuple[int, int, int],
) -> dict[str, Any]:
    composition = np.asarray([composition_group(domain) for domain in domains])
    length_groups = np.asarray([length_group(len(domain), boundaries) for domain in domains])
    return {
        'composition': {
            group: summarize_group(scores[composition == group], label, thresholds)
            for group in sorted(set(composition.tolist()))
        },
        'source_length_quantile_bins': {
            group: summarize_group(scores[length_groups == group], label, thresholds)
            for group in ('q1_shortest', 'q2', 'q3', 'q4_longest')
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--checkpoint', required=True, type=Path)
    parser.add_argument('--baseline-result', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    config = base.load_config(args.config)
    root = args.project_root.resolve()
    data_root = root / config['data_root']
    checkpoint = args.checkpoint.resolve()
    baseline_result = json.loads(args.baseline_result.read_text(encoding='utf-8'))
    thresholds = {
        key: float(value) for key, value in baseline_result['source_thresholds'].items()
    }
    device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
    model = base.BResNet().to(device)
    state = torch.load(checkpoint, map_location='cpu', weights_only=True)
    model.load_state_dict(state['model'], strict=True)
    model.eval()
    training = config['training']
    evaluations = config['data']['evaluation']
    collected: dict[tuple[str, int], tuple[list[str], np.ndarray]] = {}
    sampling: dict[str, Any] = {}
    for item in evaluations:
        path = data_root / item['path']
        material = f'{base.DATASET_REVISION}|{item["year"]}|{item["label"]}|{item["path"]}'
        seed = int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], 'little')
        domains, receipt = base.selected_domains(
            path,
            int(config['sampling']['evaluation_per_class']),
            seed,
            int(training['io_rows_per_class']),
            bool(item['full']),
            None,
        )
        scores = base.predict(model, domains, device, int(training['batch_size']))
        collected[(item['year'], int(item['label']))] = (domains, scores)
        sampling[f'{item["year"]}:{item["label"]}'] = receipt
    source_benign_domains = collected[('T17', 0)][0]
    source_lengths = np.asarray([len(domain) for domain in source_benign_domains])
    boundaries = tuple(
        int(value)
        for value in np.quantile(source_lengths, [0.25, 0.5, 0.75], method='nearest')
    )
    groups = {
        year: {
            str(label): grouped_summary(
                collected[(year, label)][0],
                collected[(year, label)][1],
                label,
                thresholds,
                boundaries,
            )
            for label in (0, 1)
        }
        for year in ('T17', 'T18', 'T19')
    }
    output = {
        'schema_version': SCHEMA_VERSION,
        'status': 'completed',
        'run_identity': 'ch3-drift-bresnet-source-morphology-diagnostic-v1',
        'screening_only': True,
        'mechanism_adjudication': True,
        'dataset_revision': base.DATASET_REVISION,
        'checkpoint': {
            'path': str(checkpoint),
            'sha256': base.sha256_file(checkpoint),
            'examples_seen': int(state['examples_seen']),
        },
        'baseline_result': {
            'path': str(args.baseline_result.resolve()),
            'sha256': base.sha256_file(args.baseline_result),
        },
        'source_benign_length_boundaries': {
            'q25': boundaries[0],
            'q50': boundaries[1],
            'q75': boundaries[2],
            'derivation': '只用 T17 良性验证域名长度分位数冻结，再应用到 T18/T19。',
        },
        'sampling': sampling,
        'groups': groups,
        'runtime': {
            'elapsed_seconds': time.monotonic() - started,
            'device': str(device),
            'torch_version': torch.__version__,
            'max_memory_allocated_bytes': torch.cuda.max_memory_allocated() if device.type == 'cuda' else None,
        },
        'interpretation_boundary': '形态组只用于源期病灶裁决；组名不是机制，不能替代后续单机制实验。',
    }
    atomic_json(args.output, output)
    print(json.dumps({'status': 'completed', 'output': str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
