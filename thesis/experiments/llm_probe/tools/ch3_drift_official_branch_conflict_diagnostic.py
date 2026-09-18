#!/usr/bin/env python3
'''诊断 DRIFT 官方静态双分支融合的源期互补与负迁移。'''
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
import torch
from sklearn.metrics import average_precision_score, roc_auc_score

import ch3_drift_bresnet_source_tail_diagnostic as sampling_tools
import ch3_drift_official_checkpoint_t17_eval as official

SCHEMA_VERSION = 'ch3-drift-official-branch-conflict-diagnostic-v1'


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + '.partial')
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    partial.replace(path)


def load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if value.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('配置 schema_version 不匹配')
    if value.get('dataset_revision') != sampling_tools.DATASET_REVISION:
        raise ValueError('数据 revision 不匹配')
    if value.get('screening_only') is not True:
        raise ValueError('本入口必须保持 screening_only=true')
    return value


def branch_features(
    model, token_ids: torch.Tensor, char_ids: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor]:
    token_embedding = model.embedding_t(token_ids)
    token_values = model.positional_encoding_t(token_embedding)
    token_mask = model.create_padding_mask(token_ids)
    token_output = model.transformer_encoder_t(token_values, mask=token_mask)
    token_valid = (~token_mask).float().unsqueeze(-1)
    token_mean = (token_output * token_valid).sum(dim=1) / token_valid.sum(dim=1).clamp(min=1)
    token_max = token_output.masked_fill(token_valid == 0, -1e9).max(dim=1).values
    token_feature = torch.cat([token_max, token_mean], dim=1)

    char_embedding = model.embedding_c(char_ids)
    char_values = model.positional_encoding_c(char_embedding)
    char_mask = model.create_padding_mask(char_ids)
    char_output = model.transformer_encoder_c(char_values, mask=char_mask)
    char_valid = (~char_mask).float().unsqueeze(-1)
    char_mean = (char_output * char_valid).sum(dim=1) / char_valid.sum(dim=1).clamp(min=1)
    char_max = char_output.masked_fill(char_valid == 0, -1e9).max(dim=1).values
    char_feature = torch.cat([char_max, char_mean], dim=1)
    return token_feature.float(), char_feature.float()


def extract_features(
    model,
    tokenizer,
    domains: list[str],
    device: torch.device,
    batch_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    token_parts: list[np.ndarray] = []
    char_parts: list[np.ndarray] = []
    with torch.inference_mode():
        for offset in range(0, len(domains), batch_size):
            current = domains[offset : offset + batch_size]
            token_ids = official.encode_subword(current, tokenizer).to(device, non_blocking=True)
            char_ids = official.encode_char(current).to(device, non_blocking=True)
            with torch.autocast(
                device_type=device.type,
                dtype=torch.bfloat16,
                enabled=device.type == 'cuda',
            ):
                token_feature, char_feature = branch_features(model, token_ids, char_ids)
            token_parts.append(token_feature.cpu().numpy())
            char_parts.append(char_feature.cpu().numpy())
    return np.concatenate(token_parts), np.concatenate(char_parts)


def probabilities(
    model,
    token_feature: np.ndarray,
    char_feature: np.ndarray,
    token_mean: np.ndarray,
    char_mean: np.ndarray,
    device: torch.device,
    batch_size: int,
) -> dict[str, np.ndarray]:
    values = {
        'static_fusion': [],
        'char_counterfactual': [],
        'subword_counterfactual': [],
    }
    with torch.inference_mode():
        for offset in range(0, len(token_feature), batch_size):
            token = torch.from_numpy(token_feature[offset : offset + batch_size]).to(device)
            char = torch.from_numpy(char_feature[offset : offset + batch_size]).to(device)
            token_neutral = torch.from_numpy(
                np.repeat(token_mean[None, :], len(token), axis=0)
            ).to(device)
            char_neutral = torch.from_numpy(
                np.repeat(char_mean[None, :], len(char), axis=0)
            ).to(device)
            logits = {
                'static_fusion': model.classifier_head(torch.cat([token, char], dim=1)),
                'char_counterfactual': model.classifier_head(torch.cat([token_neutral, char], dim=1)),
                'subword_counterfactual': model.classifier_head(torch.cat([token, char_neutral], dim=1)),
            }
            for name, current in logits.items():
                values[name].append(torch.softmax(current.float(), dim=1)[:, 1].cpu().numpy())
    result = {name: np.concatenate(parts) for name, parts in values.items()}
    char_confidence = np.abs(result['char_counterfactual'] - 0.5)
    subword_confidence = np.abs(result['subword_counterfactual'] - 0.5)
    result['confidence_selector'] = np.where(
        char_confidence >= subword_confidence,
        result['char_counterfactual'],
        result['subword_counterfactual'],
    )
    return result


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
        'fpr': fp / max(fp + tn, 1),
        'fnr': fn / max(fn + tp, 1),
        'tpr': tp / max(tp + fn, 1),
        'tp': tp,
        'tn': tn,
        'fp': fp,
        'fn': fn,
    }


def metrics(
    labels: np.ndarray,
    scores: np.ndarray,
    thresholds: dict[str, float],
) -> dict[str, Any]:
    return {
        'auroc': float(roc_auc_score(labels, scores)),
        'average_precision_balanced_sample': float(average_precision_score(labels, scores)),
        'threshold_0_5': confusion(labels, scores, 0.5),
        'source_threshold_transfer': {
            key: confusion(labels, scores, threshold)
            for key, threshold in thresholds.items()
        },
    }


def error_interactions(labels: np.ndarray, paths: dict[str, np.ndarray]) -> dict[str, Any]:
    truth = labels == 1
    full = paths['static_fusion'] >= 0.5
    char = paths['char_counterfactual'] >= 0.5
    subword = paths['subword_counterfactual'] >= 0.5
    full_wrong = full != truth
    char_correct = char == truth
    subword_correct = subword == truth
    selector = paths['confidence_selector'] >= 0.5
    return {
        'samples': len(labels),
        'char_subword_disagreement': int(np.sum(char != subword)),
        'char_subword_disagreement_rate': float(np.mean(char != subword)),
        'full_errors': int(np.sum(full_wrong)),
        'full_error_rate': float(np.mean(full_wrong)),
        'full_error_char_recovers': int(np.sum(full_wrong & char_correct)),
        'full_error_subword_recovers': int(np.sum(full_wrong & subword_correct)),
        'full_error_either_recovers': int(np.sum(full_wrong & (char_correct | subword_correct))),
        'full_error_both_recover': int(np.sum(full_wrong & char_correct & subword_correct)),
        'full_correct_both_counterfactual_wrong': int(
            np.sum((~full_wrong) & (~char_correct) & (~subword_correct))
        ),
        'confidence_selector_errors': int(np.sum(selector != truth)),
        'oracle_branch_error_lower_bound': int(np.sum((~char_correct) & (~subword_correct))),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--output', required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    config = load_config(args.config)
    root = args.project_root.resolve()
    data_root = root / config['data_root']
    reference_root = root / config['reference_root']
    checkpoint = root / config['checkpoint']
    tokenizer_path = reference_root / config['tokenizer']
    paths = [data_root / item['path'] for item in config['inputs']]
    for path in [checkpoint, tokenizer_path, reference_root / 'model.py', *paths]:
        if not path.is_file():
            raise FileNotFoundError(f'必需文件不存在：{path}')
    device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
    tokenizer = official.PreTrainedTokenizerFast(tokenizer_file=str(tokenizer_path))
    model = official.load_model(reference_root, checkpoint, device)
    batch_size = int(config['batch_size'])
    source_domains: list[str] = []
    for item in config['inputs']:
        if item['year'] == 'T17':
            source_domains.extend(
                domain
                for batch in official.iter_domains(data_root / item['path'], batch_size, None)
                for domain in batch
            )
    source_token, source_char = extract_features(
        model, tokenizer, source_domains, device, batch_size
    )
    token_mean = source_token.mean(axis=0, dtype=np.float64).astype(np.float32)
    char_mean = source_char.mean(axis=0, dtype=np.float64).astype(np.float32)
    del source_domains, source_token, source_char
    scores_by_year: dict[str, dict[str, list[np.ndarray]]] = {}
    labels_by_year: dict[str, list[np.ndarray]] = {}
    sampling: dict[str, Any] = {}
    for item in config['inputs']:
        path = data_root / item['path']
        material = f'{config["dataset_revision"]}|{item["year"]}|{item["label"]}|{item["path"]}'
        seed = int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], 'little')
        domains, receipt = sampling_tools.selected_domains(
            path,
            int(config['evaluation_per_class']),
            seed,
            batch_size * 8,
            bool(item['full']),
            None,
        )
        token_feature, char_feature = extract_features(
            model, tokenizer, domains, device, batch_size
        )
        paths_scores = probabilities(
            model, token_feature, char_feature, token_mean, char_mean, device, batch_size
        )
        year = item['year']
        for name, values in paths_scores.items():
            scores_by_year.setdefault(year, {}).setdefault(name, []).append(values)
        labels_by_year.setdefault(year, []).append(
            np.full(len(domains), int(item['label']), dtype=np.int8)
        )
        sampling[f'{year}:{item["label"]}'] = receipt
    anchors = [float(value) for value in config['diagnostic_fpr_anchors']]
    source_thresholds: dict[str, dict[str, float]] = {}
    for name, parts in scores_by_year['T17'].items():
        benign = parts[0]
        source_thresholds[name] = {
            str(anchor): float(np.quantile(benign, 1 - anchor)) for anchor in anchors
        }
    results: dict[str, Any] = {}
    for year in ('T17', 'T18', 'T19'):
        labels = np.concatenate(labels_by_year[year])
        paths_scores = {
            name: np.concatenate(parts) for name, parts in scores_by_year[year].items()
        }
        results[year] = {
            'metrics': {
                name: metrics(labels, values, source_thresholds[name])
                for name, values in paths_scores.items()
            },
            'error_interactions_at_0_5': error_interactions(labels, paths_scores),
        }
    output = {
        'schema_version': SCHEMA_VERSION,
        'status': 'completed',
        'run_identity': config['run_identity'],
        'screening_only': True,
        'mechanism_adjudication': True,
        'dataset_revision': config['dataset_revision'],
        'config_sha256': official.sha256_file(args.config),
        'artifacts': {
            'checkpoint_sha256': official.sha256_file(checkpoint),
            'reference_model_sha256': official.sha256_file(reference_root / 'model.py'),
            'tokenizer_sha256': official.sha256_file(tokenizer_path),
            'script_sha256': official.sha256_file(Path(__file__)),
        },
        'counterfactual': config['counterfactual'],
        'neutral_feature': {
            'token_mean_l2': float(np.linalg.norm(token_mean)),
            'char_mean_l2': float(np.linalg.norm(char_mean)),
        },
        'sampling': sampling,
        'source_thresholds': source_thresholds,
        'results': results,
        'runtime': {
            'elapsed_seconds': time.monotonic() - started,
            'device': str(device),
            'torch_version': torch.__version__,
            'batch_size': batch_size,
            'bf16_autocast': device.type == 'cuda',
            'max_memory_allocated_bytes': torch.cuda.max_memory_allocated() if device.type == 'cuda' else None,
        },
        'interpretation_boundary': '均值中和是同头反事实诊断，不等价于独立训练的单支模型；结果只决定是否支付可靠性融合短训成本。',
    }
    atomic_json(args.output, output)
    print(json.dumps({'status': 'completed', 'output': str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
