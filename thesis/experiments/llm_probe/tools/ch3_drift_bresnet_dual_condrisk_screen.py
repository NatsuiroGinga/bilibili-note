#!/usr/bin/env python3
'''筛选 B-ResNet 类别内最坏形态组风险的训练信号。'''
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

import ch3_drift_bresnet_morphology_diagnostic as morphology
import ch3_drift_bresnet_source_tail_diagnostic as base

PROBE_SCHEMA_VERSION = 'ch3-drift-bresnet-dual-condrisk-screen-v1'
GROUP_NAMES = ('q1_shortest', 'q2', 'q3', 'q4_longest')
ARM_DISPLAY_NAMES = {
    'c00': '普通逐样本交叉熵基线',
    'c10': '仅恶意侧条件最坏组风险',
    'c01': '仅良性侧条件最坏组风险',
}


def load_probe_config(path: Path, project_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    probe = json.loads(path.read_text(encoding='utf-8'))
    if probe.get('schema_version') != PROBE_SCHEMA_VERSION:
        raise ValueError('资格探针配置 schema_version 不匹配')
    if probe.get('screening_only') is not True:
        raise ValueError('资格探针必须保持 screening_only=true')
    base_path = project_root / probe['base_config']
    base_config = base.load_config(base_path)
    boundaries = tuple(int(value) for value in probe['source_benign_length_boundaries'])
    if len(boundaries) != 3:
        raise ValueError('源冻结长度边界必须恰好包含三个值')
    receipt_path = project_root / probe['boundary_receipt']
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    recorded = receipt['source_benign_length_boundaries']
    receipt_boundaries = (int(recorded['q25']), int(recorded['q50']), int(recorded['q75']))
    if boundaries != receipt_boundaries:
        raise ValueError('配置长度边界与源期形态诊断收据不一致')
    return probe, base_config


def group_ids(domains: list[str], boundaries: tuple[int, int, int]) -> torch.Tensor:
    q25, q50, q75 = boundaries
    lengths = np.fromiter((len(domain) for domain in domains), dtype=np.int16)
    groups = np.full(len(domains), 3, dtype=np.int64)
    groups[lengths <= q75] = 2
    groups[lengths <= q50] = 1
    groups[lengths <= q25] = 0
    return torch.from_numpy(groups)


def conditional_risk(
    per_sample: torch.Tensor,
    targets: torch.Tensor,
    groups: torch.Tensor,
    arm: str,
) -> tuple[torch.Tensor, dict[str, Any]]:
    if arm == 'c00':
        return per_sample.mean(), {
            'positive': {'count': int((targets == 1).sum()), 'active_groups': 0},
            'negative': {'count': int((targets == 0).sum()), 'active_groups': 0},
        }

    total = per_sample.numel()
    loss = per_sample.new_zeros(())
    diagnostics: dict[str, Any] = {}
    for label, key, use_worst in (
        (1, 'positive', arm == 'c10'),
        (0, 'negative', arm == 'c01'),
    ):
        class_mask = targets == label
        count = int(class_mask.sum())
        if count == 0:
            diagnostics[key] = {'count': 0, 'active_groups': 0, 'worst_group': None}
            continue
        ordinary = per_sample[class_mask].mean()
        active = torch.unique(groups[class_mask], sorted=True)
        selected = ordinary
        worst_group: int | None = None
        if use_worst:
            risks = torch.stack(
                [per_sample[class_mask & (groups == group)].mean() for group in active]
            )
            position = int(torch.argmax(risks).detach().cpu())
            selected = risks[position]
            worst_group = int(active[position].detach().cpu())
        loss = loss + (count / total) * selected
        diagnostics[key] = {
            'count': count,
            'active_groups': int(active.numel()),
            'worst_group': worst_group,
        }
    return loss, diagnostics


def train_arm(
    model: base.BResNet,
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
    arm = config['loss_probe']['arm']
    boundaries = tuple(int(value) for value in config['loss_probe']['boundaries'])
    start_io_batch = 0
    examples_seen = 0
    if resume and checkpoint.is_file():
        state = torch.load(checkpoint, map_location='cpu', weights_only=True)
        if state.get('config_sha256') != config_sha256:
            raise ValueError('断点配置哈希不匹配')
        model.load_state_dict(state['model'], strict=True)
        optimizer.load_state_dict(state['optimizer'])
        start_io_batch = int(state['completed_io_batch']) + 1
        examples_seen = int(state['examples_seen'])

    training = config['training']
    io_rows = int(training['io_rows_per_class'])
    batch_size = int(training['batch_size'])
    use_bf16 = device.type == 'cuda' and bool(training['cuda_bf16_autocast'])
    losses: list[float] = []
    ordinary_losses: list[float] = []
    empty_class_steps = {'positive': 0, 'negative': 0}
    multi_group_steps = {'positive': 0, 'negative': 0}
    worst_group_counts = {
        'positive': {name: 0 for name in GROUP_NAMES},
        'negative': {name: 0 for name in GROUP_NAMES},
    }
    started = time.monotonic()
    benign_iter = base.iter_batches(benign_path, io_rows)
    dga_iter = base.iter_batches(dga_path, io_rows)
    for io_index, pair in enumerate(itertools.zip_longest(benign_iter, dga_iter, fillvalue=[])):
        if io_index < start_io_batch:
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
        ordered_domains = [domains[index] for index in order]
        encoded = base.encode_domains(ordered_domains)
        labels_tensor = torch.from_numpy(labels[order])
        groups_tensor = group_ids(ordered_domains, boundaries)
        for offset in range(0, len(domains), batch_size):
            inputs = encoded[offset : offset + batch_size].to(device, non_blocking=True)
            targets = labels_tensor[offset : offset + batch_size].to(device, non_blocking=True)
            groups = groups_tensor[offset : offset + batch_size].to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=use_bf16):
                logits = model(inputs)
                per_sample = nn.functional.binary_cross_entropy_with_logits(
                    logits, targets, reduction='none'
                )
                loss, diagnostics = conditional_risk(per_sample, targets, groups, arm)
            ordinary_loss = per_sample.mean()
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
            ordinary_losses.append(float(ordinary_loss.detach().cpu()))
            for key in ('positive', 'negative'):
                item = diagnostics[key]
                if item['count'] == 0:
                    empty_class_steps[key] += 1
                if item['active_groups'] > 1:
                    multi_group_steps[key] += 1
                selected_group = item.get('worst_group')
                if selected_group is not None:
                    worst_group_counts[key][GROUP_NAMES[selected_group]] += 1
        examples_seen += len(domains)
        base.save_checkpoint(
            checkpoint,
            model,
            optimizer,
            io_index,
            examples_seen,
            config_sha256,
        )
        print(
            json.dumps(
                {
                    'stage': 'train',
                    'arm': arm,
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
        'mean_ordinary_bce': float(np.mean(ordinary_losses)) if ordinary_losses else None,
        'empty_class_steps': empty_class_steps,
        'multi_group_steps': multi_group_steps,
        'worst_group_counts': worst_group_counts,
        'wall_seconds': time.monotonic() - started,
        'resumed_from_io_batch': start_io_batch if start_io_batch else None,
    }


def run_entrypoint(entrypoint, arguments: list[str]) -> int:
    previous = sys.argv
    try:
        sys.argv = arguments
        return int(entrypoint())
    finally:
        sys.argv = previous


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--arm', choices=tuple(ARM_DISPLAY_NAMES), required=True)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--pilot-per-class', type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.project_root.resolve()
    run_dir = args.run_dir.resolve()
    probe, base_config = load_probe_config(args.config.resolve(), root)
    if args.arm not in probe['arms']:
        raise ValueError('请求的实验臂未在资格探针配置中登记')
    boundaries = tuple(int(value) for value in probe['source_benign_length_boundaries'])
    effective = dict(base_config)
    effective['run_identity'] = f'{probe["run_identity_prefix"]}-{args.arm}'
    effective['loss_probe'] = {
        'schema_version': PROBE_SCHEMA_VERSION,
        'arm': args.arm,
        'arm_display_name': ARM_DISPLAY_NAMES[args.arm],
        'boundaries': list(boundaries),
        'probe_config_sha256': base.sha256_file(args.config.resolve()),
    }
    effective_path = run_dir / 'effective-config.json'
    base.atomic_json(effective_path, effective)

    base.train = train_arm
    base_arguments = [
        str(Path(__file__)),
        '--config',
        str(effective_path),
        '--project-root',
        str(root),
        '--run-dir',
        str(run_dir),
    ]
    if args.resume:
        base_arguments.append('--resume')
    if args.pilot_per_class is not None:
        base_arguments.extend(['--pilot-per-class', str(args.pilot_per_class)])
    status = run_entrypoint(base.main, base_arguments)
    if status != 0:
        return status

    result_path = run_dir / 'result.json'
    result = json.loads(result_path.read_text(encoding='utf-8'))
    result.update(
        {
            'schema_version': PROBE_SCHEMA_VERSION,
            'qualification_probe_only': True,
            'arm': args.arm,
            'arm_display_name': ARM_DISPLAY_NAMES[args.arm],
            'probe_config_sha256': base.sha256_file(args.config.resolve()),
            'probe_script_sha256': base.sha256_file(Path(__file__)),
            'source_benign_length_boundaries': list(boundaries),
            'interpretation_boundary': (
                '本运行仅筛选标准类别内最坏组风险是否存在训练信号；'
                '它不是最终 N02/N09，也不能作为原创算法或论文正式结果。'
            ),
        }
    )
    base.atomic_json(result_path, result)

    if args.pilot_per_class is None:
        morphology_path = run_dir / 'morphology.json'
        morphology_arguments = [
            str(Path(__file__)),
            '--config',
            str(effective_path),
            '--project-root',
            str(root),
            '--checkpoint',
            str(run_dir / 'checkpoint.pt'),
            '--baseline-result',
            str(result_path),
            '--output',
            str(morphology_path),
        ]
        status = run_entrypoint(morphology.main, morphology_arguments)
        if status != 0:
            return status
        grouped = json.loads(morphology_path.read_text(encoding='utf-8'))
        grouped['arm'] = args.arm
        grouped['arm_display_name'] = ARM_DISPLAY_NAMES[args.arm]
        grouped['qualification_probe_only'] = True
        base.atomic_json(morphology_path, grouped)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
