#!/usr/bin/env python3
'''DRIFT 源冻结可变阶后缀记忆的快速真实性探针。'''
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import sklearn
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve

SCHEMA_VERSION = 'ch3-drift-source-frozen-suffix-probe-v1'
DATASET_REVISION = '3b31077020cd1c013d0a75cad51042a2327c4521'
Z_95 = 1.959963984540054


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


def splitmix64(values: np.ndarray) -> np.ndarray:
    values = (values + np.uint64(0x9E3779B97F4A7C15)).astype(np.uint64)
    values = (values ^ (values >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    values = (values ^ (values >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return values ^ (values >> np.uint64(31))


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding='utf-8'))
    if config.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('配置 schema_version 不匹配')
    if config.get('dataset_revision') != DATASET_REVISION:
        raise ValueError('数据 revision 不匹配')
    if config.get('max_context_order') != 3:
        raise ValueError('快速探针固定 max_context_order=3')
    if config.get('smoothing', {}).get('alpha') != 1:
        raise ValueError('快速探针固定 add-one alpha=1')
    if config.get('screening_only') is not True:
        raise ValueError('快速探针必须标记 screening_only=true')
    return config


def input_receipts(config: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(config['input_root'])
    receipts: list[dict[str, Any]] = []
    for role in ('source', 'target'):
        for item in config['inputs'][role]:
            path = root / item['path']
            if not path.is_file():
                raise FileNotFoundError(f'输入文件不存在：{path}')
            parquet = pq.ParquetFile(path)
            actual = {
                'path': str(path),
                'role': role,
                'year': item['year'],
                'label': int(item['label']),
                'rows': int(parquet.metadata.num_rows),
                'bytes': int(path.stat().st_size),
                'sha256': sha256_file(path),
                'columns': parquet.schema_arrow.names,
            }
            if actual['rows'] != int(item['rows']):
                raise ValueError(f'输入行数不匹配：{path}')
            if actual['sha256'] != item['sha256']:
                raise ValueError(f'输入 SHA256 不匹配：{path}')
            if 'domain' not in actual['columns']:
                raise ValueError(f'输入缺少 domain 列：{path}')
            receipts.append(actual)
    identities = {(x['role'], x['year'], x['label']) for x in receipts}
    expected = {('source', 'T17', 0), ('source', 'T17', 1), ('target', 'T18', 0), ('target', 'T18', 1)}
    if identities != expected:
        raise ValueError('必须恰有 T17 来源与 T18 目标的良性/DGA 四个分面')
    return receipts


def iter_domains(path: Path, batch_size: int, limit: int | None = None) -> Iterator[str]:
    emitted = 0
    for batch in pq.ParquetFile(path).iter_batches(batch_size=batch_size, columns=['domain']):
        for value in batch.column(0).to_pylist():
            if isinstance(value, str) and (domain := value.strip().lower()):
                yield domain
                emitted += 1
                if limit is not None and emitted >= limit:
                    return


class ConditionalMemory:
    def __init__(self, max_order: int, alpha: float) -> None:
        self.max_order = max_order
        self.alpha = alpha
        self.transitions = {label: [Counter() for _ in range(max_order + 1)] for label in (0, 1)}
        self.contexts = {label: [Counter() for _ in range(max_order + 1)] for label in (0, 1)}
        self.characters: set[str] = set()
        self.domains = Counter()
        self.positions = Counter()

    def update(self, domain: str, label: int) -> None:
        self.domains[label] += 1
        self.positions[label] += len(domain)
        self.characters.update(domain)
        for index, token in enumerate(domain):
            for order in range(min(self.max_order, index) + 1):
                context = domain[index - order:index] if order else ''
                self.contexts[label][order][context] += 1
                self.transitions[label][order][(context, token)] += 1

    def available_order(self, domain: str, index: int) -> int:
        for order in range(min(self.max_order, index), -1, -1):
            context = domain[index - order:index] if order else ''
            if self.contexts[0][order].get(context, 0) + self.contexts[1][order].get(context, 0) > 0:
                return order
        return 0

    def log_probability(self, context: str, token: str, order: int, label: int) -> float:
        vocabulary_size = max(len(self.characters), 1)
        count = self.transitions[label][order].get((context, token), 0)
        total = self.contexts[label][order].get(context, 0)
        return math.log((count + self.alpha) / (total + self.alpha * vocabulary_size))

    def score(self, domain: str, method: str) -> float:
        if not domain:
            return 0.0
        total = 0.0
        for index, token in enumerate(domain):
            if method == 'adaptive_backoff':
                order = self.available_order(domain, index)
            else:
                requested = int(method.rsplit('_', 1)[1])
                order = min(requested, index)
            context = domain[index - order:index] if order else ''
            total += self.log_probability(context, token, order, 1)
            total -= self.log_probability(context, token, order, 0)
        return total / len(domain)

    def summary(self) -> dict[str, Any]:
        return {
            'vocabulary_size': len(self.characters),
            'characters': ''.join(sorted(self.characters)),
            'source_domains': {str(k): int(v) for k, v in self.domains.items()},
            'source_positions': {str(k): int(v) for k, v in self.positions.items()},
            'per_label_order': {
                str(label): {
                    str(order): {
                        'contexts': len(self.contexts[label][order]),
                        'transitions': len(self.transitions[label][order]),
                    }
                    for order in range(self.max_order + 1)
                }
                for label in (0, 1)
            },
        }


def build_memory(
    config: dict[str, Any],
    root: Path,
    limit: int | None,
    start: float,
) -> ConditionalMemory:
    memory = ConditionalMemory(
        max_order=int(config['max_context_order']),
        alpha=float(config['smoothing']['alpha']),
    )
    heartbeat = int(config['heartbeat_rows'])
    for item in config['inputs']['source']:
        rows = 0
        path = root / item['path']
        for domain in iter_domains(path, int(config['batch_size']), limit):
            memory.update(domain, int(item['label']))
            rows += 1
            if rows % heartbeat == 0:
                print(
                    json.dumps(
                        {
                            'stage': 'build_source_memory',
                            'label': item['label'],
                            'rows': rows,
                            'elapsed_seconds': time.monotonic() - start,
                        },
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                    flush=True,
                )
    return memory


def sample_indices(
    row_offset: int,
    batch_rows: int,
    probability: float,
    seed: int,
) -> np.ndarray:
    if probability >= 1.0:
        return np.arange(batch_rows, dtype=np.int64)
    rows = np.arange(row_offset, row_offset + batch_rows, dtype=np.uint64)
    threshold = np.uint64(min((1 << 64) - 1, int(probability * (1 << 64))))
    return np.flatnonzero(splitmix64(rows ^ np.uint64(seed)) < threshold)


def score_target(
    config: dict[str, Any],
    root: Path,
    memory: ConditionalMemory,
    limit: int | None,
    start: float,
) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, Any]]:
    methods = ['fixed_context_1', 'fixed_context_2', 'fixed_context_3', 'adaptive_backoff']
    labels: list[int] = []
    score_lists = {method: [] for method in methods}
    sample_size = int(config['sampling']['requested_per_stratum'])
    details: dict[str, Any] = {}
    heartbeat = int(config['heartbeat_rows'])
    for item in config['inputs']['target']:
        path = root / item['path']
        total_rows = int(item['rows'])
        seed_material = f'{DATASET_REVISION}|{item["year"]}|{item["label"]}|{item["path"]}'
        seed = int.from_bytes(hashlib.sha256(seed_material.encode('utf-8')).digest()[:8], 'little')
        probability = 1.0 if limit is not None else min(1.0, sample_size / total_rows)
        scanned = selected = valid = 0
        for batch in pq.ParquetFile(path).iter_batches(batch_size=int(config['batch_size']), columns=['domain']):
            batch_rows = batch.num_rows
            if limit is not None:
                remaining = max(limit - selected, 0)
                indices = np.arange(min(batch_rows, remaining), dtype=np.int64)
            else:
                indices = sample_indices(scanned, batch_rows, probability, seed)
            values = batch.column(0).take(pa.array(indices)).to_pylist()
            selected += len(indices)
            for value in values:
                if not isinstance(value, str) or not (domain := value.strip().lower()):
                    continue
                labels.append(int(item['label']))
                for method in methods:
                    score_lists[method].append(memory.score(domain, method))
                valid += 1
            scanned += batch_rows
            if scanned % heartbeat < batch_rows:
                print(
                    json.dumps(
                        {
                            'stage': 'score_target',
                            'label': item['label'],
                            'scanned_rows': scanned,
                            'selected_rows': selected,
                            'elapsed_seconds': time.monotonic() - start,
                        },
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                    flush=True,
                )
            if limit is not None and selected >= limit:
                break
        actual_half_width = Z_95 * math.sqrt(0.25 / max(valid, 1))
        details[f'{item["year"]}:{item["label"]}'] = {
            'metadata_rows': total_rows,
            'requested_sample_size': limit if limit is not None else sample_size,
            'selected_rows': selected,
            'valid_domains': valid,
            'sampling_probability': probability,
            'actual_worst_case_half_width_95': actual_half_width,
            'seed': seed,
            'algorithm': 'SplitMix64(row_index xor derived_seed)',
        }
    return (
        np.asarray(labels, dtype=np.int8),
        {name: np.asarray(values, dtype=np.float64) for name, values in score_lists.items()},
        details,
    )


def tpr_at_fpr(labels: np.ndarray, scores: np.ndarray, budget: float) -> dict[str, float]:
    fpr, tpr, thresholds = roc_curve(labels, scores)
    eligible = np.flatnonzero(fpr <= budget)
    index = int(eligible[np.argmax(tpr[eligible])]) if len(eligible) else 0
    return {
        'budget': budget,
        'tpr': float(tpr[index]),
        'actual_fpr': float(fpr[index]),
        'threshold': float(thresholds[index]),
    }


def evaluate(labels: np.ndarray, scores: dict[str, np.ndarray]) -> dict[str, Any]:
    if len(np.unique(labels)) != 2:
        raise ValueError('评价必须同时包含良性与 DGA')
    result: dict[str, Any] = {}
    for name, values in scores.items():
        result[name] = {
            'auroc': float(roc_auc_score(labels, values)),
            'average_precision_balanced_sample': float(average_precision_score(labels, values)),
            'tpr_at_fpr': {
                str(budget): tpr_at_fpr(labels, values, budget)
                for budget in (0.0001, 0.001, 0.01)
            },
            'score_mean_benign': float(values[labels == 0].mean()),
            'score_mean_dga': float(values[labels == 1].mean()),
        }
    adaptive = result['adaptive_backoff']
    for fixed in ('fixed_context_1', 'fixed_context_2', 'fixed_context_3'):
        result[fixed]['adaptive_delta'] = {
            'auroc': adaptive['auroc'] - result[fixed]['auroc'],
            'average_precision_balanced_sample': adaptive['average_precision_balanced_sample']
            - result[fixed]['average_precision_balanced_sample'],
            'tpr_at_fpr': {
                key: adaptive['tpr_at_fpr'][key]['tpr'] - result[fixed]['tpr_at_fpr'][key]['tpr']
                for key in adaptive['tpr_at_fpr']
            },
        }
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--pilot-domains', type=int)
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    start = time.monotonic()
    config = load_config(args.config)
    if args.pilot_domains is not None and args.pilot_domains <= 0:
        raise ValueError('pilot-domains 必须为正数')
    receipts = input_receipts(config)
    root = Path(config['input_root'])
    memory = build_memory(config, root, args.pilot_domains, start)
    labels, scores, sampling = score_target(
        config, root, memory, args.pilot_domains, start
    )
    metrics = evaluate(labels, scores)
    value = {
        'schema_version': SCHEMA_VERSION,
        'status': 'completed',
        'run_identity': config['run_identity'],
        'screening_only': True,
        'target_informed': True,
        'mechanism_adjudication': args.pilot_domains is None,
        'dataset_revision': DATASET_REVISION,
        'config_sha256': sha256_file(args.config),
        'input_files': receipts,
        'design': {
            'memory': 'T17 类条件源冻结可变阶字符后缀记忆',
            'domain_boundary': '每个域名独立，不跨域拼接上下文',
            'max_context_order': config['max_context_order'],
            'smoothing': config['smoothing'],
            'selection': 'adaptive 使用两类合并支持下最长已见上下文',
            'interpretation_boundary': '该探针只测试可变阶源记忆相对固定阶统计是否有信号，不证明神经机制有效或具备原创性。',
        },
        'memory_summary': memory.summary(),
        'sampling': sampling,
        'evaluation': {
            'labels': {
                'benign': int((labels == 0).sum()),
                'dga': int((labels == 1).sum()),
            },
            'balanced_sample_warning': 'AP 基于近似均衡抽样，不代表部署先验下 AP。',
            'metrics': metrics,
        },
        'runtime': {
            'elapsed_seconds': time.monotonic() - start,
            'python_executable': sys.executable,
            'python_version': sys.version,
            'numpy_version': np.__version__,
            'pyarrow_version': pa.__version__,
            'sklearn_version': sklearn.__version__,
        },
    }
    atomic_json(args.output, value)


if __name__ == '__main__':
    arguments = parse_args()
    try:
        run(arguments)
    except Exception as error:
        failure = {
            'schema_version': SCHEMA_VERSION,
            'status': 'failed',
            'error_type': type(error).__name__,
            'error': str(error),
        }
        try:
            failure['config_sha256'] = sha256_file(arguments.config)
        except OSError:
            pass
        atomic_json(arguments.output, failure)
        raise
