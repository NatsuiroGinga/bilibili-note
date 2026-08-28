# -*- coding: utf-8 -*-
"""机制二：实体分层采样器（spec 5.4 节「每步按实体均匀抽正实体与负实体」）。

背景（已实测，见 `.Codex/docs/RWKV/2026-08-28-机制二梯度信号实测裁决.md` 第四节）：
LSPR23 训练区恶意片段仅 92/271,815 = 0.0338%，随机 64 片段批零恶意的概率高达
97.86%。若不按实体分层抽正负实体，绝大多数优化步排序损失根本无定义。本模块因此
把「每步至少一个正实体」做成运行断言，而不是可选的批构造策略。

本模块只负责：
1. 从 LSPR23 冻结缓存（`E23`/`I23`/`M23`/`T23`/`y23`）建立实体索引与标签
   （标签只用于采样分层，不进入模型输入或状态更新，与既有诊断脚本
   `ch3_lspr23_entity_history_availability.py` 的口径一致）；
2. 按正实体不放回轮转、负实体每步独立无放回的策略抽取一批实体；
3. 汇总被抽实体的全部片段行，按 `(entity, T23)` 升序排列，供下游（机制二任务 2）
   计算实体路径最大分数；
4. 输出批构成收据，用于运行诊断（正实体数、负实体数、总片段数、总有效流数、
   最长袋流数、按诊断阈值统计的被截断实体数）。

本模块不接入宿主 `ch3_ft_c00_dual_selection.py`，不构造模型输入，不读取目标年
（`X24/y24/I24/M24/E24/T24`）任何数组。
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

_CHUNK = 20_000
_TARGET_YEAR_NAMES = ("X24", "y24", "I24", "M24", "E24", "T24")


def require(condition: bool, message: str) -> None:
    """运行断言：条件不满足即视为无效结果，立即停止，不吞掉错误。"""
    if not condition:
        raise RuntimeError(message)


def _segment_valid_counts(mask: np.ndarray, chunk: int = _CHUNK) -> np.ndarray:
    """逐片段有效流数，分块读取以兼容 mmap 数组。"""
    segment_count = mask.shape[0]
    counts = np.zeros(segment_count, dtype=np.int64)
    for start in range(0, segment_count, chunk):
        block = np.asarray(mask[start : start + chunk]) > 0
        counts[start : start + chunk] = block.sum(axis=1)
    return counts


def _entity_positive_flags(
    flow_indices: np.ndarray,
    valid_mask: np.ndarray,
    entity_of_segment: np.ndarray,
    flow_labels: np.ndarray,
    entity_count: int,
    chunk: int = _CHUNK,
) -> np.ndarray:
    """实体标签：其任一有效流为恶意（y>0.5）即为恶意实体。

    只用于本采样器的分层，不参与任何模型输入、状态更新或选择——与
    `ch3_lspr23_entity_history_availability.py` 的口径一致，本函数独立实现，
    不导入该脚本，避免与其形成隐式耦合。
    """
    segment_count = len(entity_of_segment)
    flags = np.zeros(entity_count, dtype=bool)
    for start in range(0, segment_count, chunk):
        index_block = np.asarray(flow_indices[start : start + chunk])
        mask_block = np.asarray(valid_mask[start : start + chunk]) > 0
        owners = entity_of_segment[start : start + chunk]
        if not mask_block.any():
            continue
        segment_ids = np.repeat(np.arange(len(owners)), mask_block.sum(axis=1))
        positive_flat = flow_labels[index_block[mask_block]] > 0.5
        segment_positive = np.zeros(len(owners), dtype=bool)
        np.logical_or.at(segment_positive, segment_ids, positive_flat)
        np.logical_or.at(flags, owners, segment_positive)
    return flags


@dataclass(frozen=True)
class EntityStratifiedSamplerConfig:
    """采样器配置。

    n_pos / n_neg：每步抽取的正／负实体数，无默认值——具体数值属训练配置，
    须由未来宿主接入时按共同预算合同冻结，本模块不代其选择。
    max_bag_flows：仅用于 `batch_composition_receipt` 诊断「被截断实体数」的参照阈值，
    本采样器本身不做截断（截断属机制二任务 2 的因果前缀截断处置）。
    """

    n_pos: int
    n_neg: int
    max_bag_flows: int | None = None


class EntityStratifiedSampler:
    """实体分层采样器：保证每步至少一个正实体，避免排序损失在绝大多数步无定义。"""

    def __init__(
        self,
        entity_of_segment: np.ndarray,
        segment_flow_indices: np.ndarray,
        segment_valid_mask: np.ndarray,
        segment_timestamp: np.ndarray,
        flow_labels: np.ndarray,
        config: EntityStratifiedSamplerConfig,
    ) -> None:
        self.config = config
        self._entity_of_segment = np.asarray(entity_of_segment)
        self._segment_timestamp = np.asarray(segment_timestamp)
        entity_count = int(self._entity_of_segment.max()) + 1

        valid_counts = _segment_valid_counts(segment_valid_mask)
        flows_per_entity = np.bincount(
            self._entity_of_segment, weights=valid_counts, minlength=entity_count
        ).astype(np.int64)
        positive_entity = _entity_positive_flags(
            segment_flow_indices,
            segment_valid_mask,
            self._entity_of_segment,
            flow_labels,
            entity_count,
        )

        # 按 (entity, T23) 升序建立全局片段行序，供 sample() 直接切片使用。
        order = np.lexsort((self._segment_timestamp, self._entity_of_segment))
        counts_per_entity = np.bincount(self._entity_of_segment, minlength=entity_count)
        offsets = np.zeros(entity_count + 1, dtype=np.int64)
        np.cumsum(counts_per_entity, out=offsets[1:])

        self._order = order
        self._offsets = offsets
        self._flows_per_entity = flows_per_entity
        self._positive_entity = positive_entity
        self._entity_count = entity_count

        alive = flows_per_entity > 0
        self._positive_pool = np.flatnonzero(positive_entity & alive)
        self._negative_pool = np.flatnonzero((~positive_entity) & alive)
        require(self._positive_pool.size > 0, "源区不存在任何恶意实体，无法构建实体分层采样器")
        require(self._negative_pool.size > 0, "源区不存在任何良性实体，无法构建实体分层采样器")
        require(
            config.n_pos <= self._positive_pool.size,
            f"n_pos={config.n_pos} 超过正实体基数 {self._positive_pool.size}",
        )
        require(
            config.n_neg <= self._negative_pool.size,
            f"n_neg={config.n_neg} 超过负实体基数 {self._negative_pool.size}",
        )

        self._positive_queue: list[int] = []

    @property
    def positive_pool_size(self) -> int:
        return int(self._positive_pool.size)

    @property
    def negative_pool_size(self) -> int:
        return int(self._negative_pool.size)

    @property
    def flows_per_entity(self) -> np.ndarray:
        """只读视图：每个实体（含无流实体，值为 0）的有效流总数。"""
        return self._flows_per_entity

    @property
    def positive_entity_flags(self) -> np.ndarray:
        """只读视图：每个实体是否为恶意实体（`Y_e=max_t y_{e,t}`）。"""
        return self._positive_entity

    def _draw_positive_entities(self, rng: np.random.Generator) -> np.ndarray:
        """不放回轮转：一轮（正实体基数 239 个量级）内不重复抽同一正实体；
        轮次边界处若重洗后立刻撞上本次已抽出的实体，放回队尾重抽，避免同批重复。
        """
        n = self.config.n_pos
        drawn: list[int] = []
        drawn_set: set[int] = set()
        guard = 0
        max_guard = (self._positive_pool.size + n) * 4
        while len(drawn) < n:
            guard += 1
            require(guard <= max_guard, "正实体轮转抽样异常：超出防御性重试上限")
            if not self._positive_queue:
                order = self._positive_pool.copy()
                rng.shuffle(order)
                self._positive_queue = order.tolist()
            candidate = self._positive_queue.pop(0)
            if candidate in drawn_set:
                self._positive_queue.append(candidate)
                continue
            drawn.append(candidate)
            drawn_set.add(candidate)
        return np.asarray(drawn, dtype=self._entity_of_segment.dtype)

    def sample(self, rng: np.random.Generator) -> dict[str, np.ndarray]:
        """每步抽 n_pos 个正实体与 n_neg 个负实体；正实体基数仅 239（源区），
        用不放回轮转避免同一轮内过度重复抽取。"""
        positives = self._draw_positive_entities(rng)
        negatives = rng.choice(self._negative_pool, size=self.config.n_neg, replace=False)
        require(positives.size >= 1, "每步至少一个正实体")

        entity_ids = np.concatenate([positives, negatives])
        sorted_entities = np.sort(entity_ids)
        parts = [
            self._order[self._offsets[e] : self._offsets[e + 1]] for e in sorted_entities
        ]
        segment_rows = (
            np.concatenate(parts) if parts else np.empty(0, dtype=self._order.dtype)
        )

        return {
            "positive_entities": positives,
            "negative_entities": negatives,
            "segment_rows": segment_rows,
        }

    def batch_composition_receipt(self, batch: dict[str, np.ndarray]) -> dict[str, int]:
        """正实体数、负实体数、总片段数、总有效流数、最长袋流数、被截断实体数。"""
        positive_entities = batch["positive_entities"]
        negative_entities = batch["negative_entities"]
        segment_rows = batch["segment_rows"]
        entity_ids = np.concatenate([positive_entities, negative_entities])

        per_entity_flows = self._flows_per_entity[entity_ids]
        longest_bag_flow_count = int(per_entity_flows.max()) if per_entity_flows.size else 0
        truncated_entity_count = 0
        if self.config.max_bag_flows is not None:
            truncated_entity_count = int((per_entity_flows > self.config.max_bag_flows).sum())

        return {
            "positive_entity_count": int(positive_entities.size),
            "negative_entity_count": int(negative_entities.size),
            "total_segment_count": int(segment_rows.size),
            "total_valid_flow_count": int(per_entity_flows.sum()),
            "longest_bag_flow_count": longest_bag_flow_count,
            "truncated_entity_count": truncated_entity_count,
        }


def _load_cache(cache_root: Path) -> dict[str, np.ndarray]:
    """只加载源年数组；目标年数组存在即拒绝运行。"""
    for name in _TARGET_YEAR_NAMES:
        require(
            not (cache_root / f"{name}.npy").is_file(),
            f"检测到目标年文件 {name}.npy，本工具禁止读取目标年数组",
        )
    return {
        "E23": np.load(cache_root / "E23.npy"),
        "I23": np.load(cache_root / "I23.npy", mmap_mode="r"),
        "M23": np.load(cache_root / "M23.npy", mmap_mode="r"),
        "T23": np.load(cache_root / "T23.npy"),
        "y23": np.load(cache_root / "y23.npy"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument("--n-pos", type=int, default=2, help="诊断用，非冻结训练配置")
    parser.add_argument("--n-neg", type=int, default=64, help="诊断用，非冻结训练配置")
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--max-bag-flows",
        type=int,
        default=8192,
        help="诊断阈值，取自 5.3.1 节记录的单步流预算，仅用于批构成收据",
    )
    args = parser.parse_args()

    cache_root = Path(args.cache_root).resolve()
    cache = _load_cache(cache_root)
    print(f"缓存就绪：{len(cache['E23']):,} 片段", flush=True)

    config = EntityStratifiedSamplerConfig(
        n_pos=args.n_pos, n_neg=args.n_neg, max_bag_flows=args.max_bag_flows
    )
    sampler = EntityStratifiedSampler(
        entity_of_segment=cache["E23"],
        segment_flow_indices=cache["I23"],
        segment_valid_mask=cache["M23"],
        segment_timestamp=cache["T23"],
        flow_labels=cache["y23"],
        config=config,
    )
    print(
        f"实体索引就绪：正实体池 {sampler.positive_pool_size:,} 个，"
        f"负实体池 {sampler.negative_pool_size:,} 个",
        flush=True,
    )

    rng = np.random.default_rng(args.seed)
    receipts: list[dict[str, int]] = []
    for round_index in range(args.rounds):
        batch = sampler.sample(rng)
        receipt = sampler.batch_composition_receipt(batch)
        receipts.append(receipt)
        print(f"批 {round_index + 1}/{args.rounds}: {receipt}", flush=True)

    def median(key: str) -> float:
        return float(np.median([r[key] for r in receipts]))

    print(f"=== 批构成中位数（{args.rounds} 批）===", flush=True)
    for key in (
        "positive_entity_count",
        "negative_entity_count",
        "total_segment_count",
        "total_valid_flow_count",
        "longest_bag_flow_count",
        "truncated_entity_count",
    ):
        print(f"  {key} 中位数 = {median(key):g}", flush=True)

    zero_positive_batches = sum(1 for r in receipts if r["positive_entity_count"] == 0)
    print(
        f"零正实体批数 = {zero_positive_batches}/{args.rounds}"
        "（对照：随机 64 片段批零恶意概率 97.86%，"
        "见 .Codex/docs/RWKV/2026-08-28-机制二梯度信号实测裁决.md 第四节）",
        flush=True,
    )
    print("CH3_FT_ENTITY_STRATIFIED_SAMPLER_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
