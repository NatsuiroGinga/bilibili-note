"""避免采集场景泄漏的确定性分组划分。"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from flow_probe.schemas import FlowSample


class SplitError(ValueError):
    """数据无法在不泄漏分组的前提下划分。"""


@dataclass(frozen=True)
class DatasetSplits:
    """训练、验证与测试集合及其证据等级。"""

    train: tuple[FlowSample, ...]
    validation: tuple[FlowSample, ...]
    test: tuple[FlowSample, ...]
    evidence_level: Literal["primary", "diagnostic"]


def _group_quotas(group_count: int, ratios: tuple[float, float, float]) -> list[int]:
    quotas = [1 if ratio > 0 else 0 for ratio in ratios]
    remaining = group_count - sum(quotas)
    targets = [group_count * ratio for ratio in ratios]
    while remaining:
        index = max(range(3), key=lambda item: (targets[item] - quotas[item], -item))
        quotas[index] += 1
        remaining -= 1
    return quotas


def _assignment_score(
    current_size: int,
    current_labels: Mapping[str, int],
    group_size: int,
    group_labels: Mapping[str, int],
    target_size: float,
    target_labels: Mapping[str, float],
) -> float:
    new_size = current_size + group_size
    score = abs(new_size - target_size) / max(target_size, 1.0)
    for label, target in target_labels.items():
        new_count = current_labels.get(label, 0) + group_labels.get(label, 0)
        score += abs(new_count - target) / max(target, 1.0)
    return score


def grouped_split(
    samples: Sequence[FlowSample],
    ratios: tuple[float, float, float],
    seed: int,
    reliable_groups: bool = True,
) -> DatasetSplits:
    """按完整分组分配样本，绝不回退为逐行随机划分。"""
    if len(ratios) != 3 or any(ratio <= 0 for ratio in ratios):
        raise SplitError("ratios 必须包含三个正数")
    if abs(sum(ratios) - 1.0) > 1e-9:
        raise SplitError("ratios 之和必须为 1")
    sample_ids = [sample.sample_id for sample in samples]
    if len(sample_ids) != len(set(sample_ids)):
        raise SplitError("样本标识重复")

    grouped: dict[str, list[FlowSample]] = defaultdict(list)
    for sample in samples:
        grouped[sample.group_id].append(sample)
    if len(grouped) < 3:
        raise SplitError("至少需要 3 个分组，不能回退为逐行划分")

    group_keys = sorted(grouped)
    random.Random(seed).shuffle(group_keys)
    group_keys.sort(key=lambda key: len(grouped[key]), reverse=True)
    groups = {key: sorted(grouped[key], key=lambda sample: sample.sample_id) for key in group_keys}
    group_labels = {
        key: Counter(sample.binary_label for sample in group) for key, group in groups.items()
    }
    quotas = _group_quotas(len(group_keys), ratios)
    partitions: list[list[FlowSample]] = [[], [], []]
    partition_sizes = [0, 0, 0]
    partition_labels: list[Counter[str]] = [Counter(), Counter(), Counter()]
    assigned_group_counts = [0, 0, 0]
    total_labels = Counter(sample.binary_label for sample in samples)
    target_labels = [
        {label: count * ratio for label, count in total_labels.items()} for ratio in ratios
    ]
    assigned_keys: set[str] = set()

    def assign(key: str, index: int) -> None:
        partitions[index].extend(groups[key])
        partition_sizes[index] += len(groups[key])
        partition_labels[index].update(group_labels[key])
        assigned_group_counts[index] += 1
        assigned_keys.add(key)

    label_group_counts = {
        label: sum(group_labels[key][label] > 0 for key in group_keys) for label in total_labels
    }
    coverable_labels = {
        label for label, group_count in label_group_counts.items() if group_count >= 3
    }
    group_order = {key: index for index, key in enumerate(group_keys)}
    for label in sorted(coverable_labels, key=lambda item: (label_group_counts[item], item)):
        missing_partitions = [index for index in range(3) if partition_labels[index][label] == 0]
        available_groups = [
            key for key in group_keys if key not in assigned_keys and group_labels[key][label] > 0
        ]
        available_groups.sort(key=lambda key: (-len(groups[key]), group_order[key]))
        missing_partitions.sort(key=lambda index: (-ratios[index], index))
        for index, key in zip(missing_partitions, available_groups, strict=False):
            assign(key, index)

    for key in group_keys:
        if key in assigned_keys:
            continue
        candidates = [index for index in range(3) if assigned_group_counts[index] < quotas[index]]
        index = min(
            candidates,
            key=lambda item: (
                _assignment_score(
                    current_size=partition_sizes[item],
                    current_labels=partition_labels[item],
                    group_size=len(groups[key]),
                    group_labels=group_labels[key],
                    target_size=len(samples) * ratios[item],
                    target_labels=target_labels[item],
                ),
                item,
            ),
        )
        assign(key, index)

    result = DatasetSplits(
        train=tuple(partitions[0]),
        validation=tuple(partitions[1]),
        test=tuple(partitions[2]),
        evidence_level="primary" if reliable_groups else "diagnostic",
    )
    assert_no_group_overlap(result)
    return result


def assert_no_group_overlap(splits: DatasetSplits) -> None:
    """确认任意两个集合不共享分组或样本标识。"""
    partitions = {
        "train": splits.train,
        "validation": splits.validation,
        "test": splits.test,
    }
    names = tuple(partitions)
    for left_index, left_name in enumerate(names):
        left_groups = {sample.group_id for sample in partitions[left_name]}
        left_ids = {sample.sample_id for sample in partitions[left_name]}
        for right_name in names[left_index + 1 :]:
            right_groups = {sample.group_id for sample in partitions[right_name]}
            overlap = sorted(left_groups.intersection(right_groups))
            if overlap:
                raise SplitError(f"分组交叉：{left_name}/{right_name}：{', '.join(overlap)}")
            right_ids = {sample.sample_id for sample in partitions[right_name]}
            duplicate_ids = sorted(left_ids.intersection(right_ids))
            if duplicate_ids:
                raise SplitError(
                    f"样本标识交叉：{left_name}/{right_name}：{', '.join(duplicate_ids)}"
                )
