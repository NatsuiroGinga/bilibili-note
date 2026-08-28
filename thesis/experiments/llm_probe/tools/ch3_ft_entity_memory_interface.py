# -*- coding: utf-8 -*-
"""机制一（因果实体记忆交叉注意力）严格过去接口构建器。

只产出 ``previous_segment_row``／``is_entity_start``／``segment_ordinal``／``role_id``
四个逐片段数组及其因果断言，不含任何模型代码，供
``ch3_ft_causal_entity_memory.py`` 与 ``ch3_ft_c00_dual_selection.py`` 消费。

依据：``.Codex/docs/RWKV/2026-08-28-因果实体记忆交叉注意力与低误报实体排序/
机制设计与实验计划.md`` 第 3.0 节实测结论——``previous_segment_row``、
``source_record_id``、``role_id`` 三项可从冻结缓存派生，``available_ns`` 仍缺失
（只影响“实现满足部署严格因果”这一论证，不阻断本接口实现）。

因果序两级：**片段内**由 ``I23`` 的列位置给出（本文件不处理，留给消费方）；
**片段间**由本文件基于 ``(E23, T23)`` 字典序建立的 ``previous_segment_row`` 给出。
``X23`` 行号唯一但非时间序，本文件不使用它排序。

角色（``role_id``）口径：本任务只读 LSPR23 源年，从未加载
``X24/y24/I24/M24/E24/T24``，因此角色空间只有训练实体与验证实体两档
（0＝训练实体，1＝验证实体），与
``ch3_ft_transformer_field_token_protocol_a.source_split`` 内部的
``entity_mask`` 计算逐字一致——用同一随机种子与验证占比对 ``np.unique(E23)``
重放同一置换，不落地成新的持久化“角色收据”文件，因为角色完全由
``(seed, validation_fraction)`` 决定性给出，不存在信息损失。这保证了角色按
**实体**（而不是按片段）恒定，同实体的全部片段——含被 ``time_tail_fraction``
排除出训练/验证使用范围的尾部片段——角色标签仍然一致，``same_role`` 断言因此
是对实现正确性的真实检验，而不是靠定义自动满足。

目标年读取：``0``。本文件任何函数都不触碰 ``X24/y24/I24/M24/E24/T24``。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

RUN_ID = "ch3-ft-entity-segment-interface-v1"
SCHEMA_VERSION = "ch3-ft-entity-segment-interface-receipt-v1"
DEFAULT_CACHE_ROOT = "runs/diagnostics/dijk-repro/cache"
DEFAULT_SPLIT_CONFIG = "configs/ch3-ft-transformer-field-token-protocol-a-seed42-v1.json"
DEFAULT_OUTPUT_ROOT = f"runs/diagnostics/{RUN_ID}"
TARGET_ARRAY_NAMES: tuple[str, ...] = ("X24", "y24", "I24", "M24", "E24", "T24")

T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:7.1f}s] {message}", flush=True)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    """原子写 JSON，避免中断产生半份收据（与既有诊断工具同一写法）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def load_role_ids(split_receipt: Path, entity: np.ndarray) -> np.ndarray:
    """从冻结的 FT 基础配置重建训练/验证实体集合，得到逐片段角色标签。

    ``split_receipt`` 在本实现中指向冻结的 FT 基础配置 JSON（含
    ``training.seed`` 与 ``training.validation_fraction``），而不是一份单独
    持久化的逐行角色文件——角色完全由这两个数值决定性给出，与
    ``base.source_split`` 内部的 ``entity_mask`` 计算逐字一致（同一
    ``np.random.RandomState(seed).permutation`` 调用），因此按需重放即可，
    不必另建一份可能与源实现漂移的副本。

    返回 ``int8`` 数组，0＝训练实体，1＝验证实体；不存在第三档，因为本任务
    从不加载目标年数组。
    """
    config = json.loads(split_receipt.read_text(encoding="utf-8"))
    training = config["training"]
    seed = int(training["seed"])
    validation_fraction = float(training["validation_fraction"])
    unique_entity = np.unique(entity)
    permutation = np.random.RandomState(seed).permutation(len(unique_entity))
    count = max(1, int(len(unique_entity) * validation_fraction))
    validation_entities = set(unique_entity[permutation[:count]].tolist())
    # 与 base.source_split 的 entity_mask 计算同一写法：逐元素成员测试。
    is_validation = np.fromiter(
        (value in validation_entities for value in entity), bool, len(entity)
    )
    return is_validation.astype(np.int8)


def _causal_order(
    entity: np.ndarray, stamp: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """按 ``(实体, 片段时间戳)`` 字典序建立同实体前驱片段索引，全向量化实现。

    因果序两级：片段内由列位置给出（此处不处理），片段间由 ``T23`` 给出。
    ``X23`` 行号唯一但非时间序，不参与本函数。

    返回 ``(previous_segment_row, is_entity_start, segment_ordinal)``。
    """
    # np.lexsort 以最后一个键为主键：先按 entity 分组，组内再按 stamp 升序。
    order = np.lexsort((stamp, entity))
    ordered_entity = entity[order]
    # same[i] 表示排序后第 i 个位置与第 i-1 个位置同属一个实体（i=0 恒为 False）。
    same = np.r_[False, ordered_entity[1:] == ordered_entity[:-1]]

    previous = np.full(len(entity), -1, dtype=np.int64)
    same_positions = np.flatnonzero(same)
    previous[order[same_positions]] = order[same_positions - 1]
    is_entity_start = previous < 0

    # segment_ordinal：实体内从 0 开始的片段序号，用前缀最大值向量化替代逐实体
    # Python 循环——150,680 个实体的逐个切片赋值不属于机械必须的逐行扫描，
    # 按仓库规则应先向量化。
    positions = np.arange(len(order), dtype=np.int64)
    reset_positions = np.where(~same, positions, np.int64(-1))
    block_start = np.maximum.accumulate(reset_positions)
    ordinal_in_sorted = positions - block_start
    segment_ordinal = np.empty(len(order), dtype=np.int64)
    segment_ordinal[order] = ordinal_in_sorted

    return previous, is_entity_start, segment_ordinal


def build_interface(cache_root: Path, split_receipt: Path) -> dict[str, np.ndarray]:
    """按 ``(实体, 片段时间戳)`` 建立同实体前驱片段索引。

    因果序两级：片段内由列位置给出，片段间由 T23 给出。X23 行号唯一但非时间序，
    不得用于比较先后。只读 ``E23.npy``、``T23.npy`` 与 ``split_receipt`` 三个
    输入，从不触碰目标年数组。
    """
    entity = np.load(cache_root / "E23.npy")
    stamp = np.load(cache_root / "T23.npy")
    previous, is_entity_start, segment_ordinal = _causal_order(entity, stamp)
    role_id = load_role_ids(split_receipt, entity)
    return {
        "previous_segment_row": previous,
        "is_entity_start": is_entity_start,
        "segment_ordinal": segment_ordinal,
        "role_id": role_id,
    }


def assert_causality(interface: dict[str, np.ndarray], entity: np.ndarray, stamp: np.ndarray) -> dict[str, bool]:
    """四条必须全过的断言；任一失败即抛错，不静默降级。"""
    previous = interface["previous_segment_row"]
    linked = previous >= 0
    checks = {
        "same_entity": bool(np.all(entity[previous[linked]] == entity[linked])),
        "strictly_increasing_time": bool(np.all(stamp[previous[linked]] < stamp[linked])),
        "same_role": bool(np.all(interface["role_id"][previous[linked]] == interface["role_id"][linked])),
        "no_self_reference": bool(np.all(previous[linked] != np.flatnonzero(linked))),
    }
    if not all(checks.values()):
        raise RuntimeError(f"因果接口断言失败：{checks}")
    return checks


def write_receipt(
    interface: dict[str, np.ndarray],
    checks: dict[str, bool],
    entity_count: int,
    cache_root: Path,
    output_root: Path,
) -> None:
    """写 ``receipts/entity-segment-interface.json``，含字段形状/dtype 与断言结果。

    附带 ``checks``（由 ``assert_causality`` 产出）与 ``entity_count``——
    这两项不在 ``interface`` 返回字典本身内（前者依赖 ``E23``/``T23``，
    后者是全局统计量），故作为独立参数传入，而不是塞进 ``interface``
    污染其“只含四个模型消费字段”的单一职责。
    """
    linked = int((interface["previous_segment_row"] >= 0).sum())
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "cache_root": str(cache_root),
        "target_reads": 0,
        "segment_count": int(len(interface["previous_segment_row"])),
        "entity_count": entity_count,
        "is_entity_start_count": int(interface["is_entity_start"].sum()),
        "linked_segment_count": linked,
        "role_id_value_counts": {
            "train_entity_segments": int((interface["role_id"] == 0).sum()),
            "validation_entity_segments": int((interface["role_id"] == 1).sum()),
        },
        "fields": {
            name: {"dtype": str(array.dtype), "shape": list(array.shape)}
            for name, array in interface.items()
        },
        "causality_assertions": checks,
    }
    atomic_json(output_root / "receipts" / "entity-segment-interface.json", payload)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", default=DEFAULT_CACHE_ROOT)
    parser.add_argument(
        "--split-receipt",
        default=DEFAULT_SPLIT_CONFIG,
        help="冻结的 FT 基础配置，提供 seed 与 validation_fraction 以重建训练/验证实体角色",
    )
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()

    cache_root = Path(args.cache_root).resolve()
    split_receipt = Path(args.split_receipt).resolve()
    output_root = Path(args.output_root).resolve()

    for name in TARGET_ARRAY_NAMES:
        assert not (cache_root / f"{name}.npy").resolve() == split_receipt, "配置路径异常指向目标年数组"

    atomic_json(output_root / "status.json", {"run_id": RUN_ID, "state": "running", "target_reads": 0})
    log(f"开始构建严格过去接口：cache_root={cache_root}")

    interface = build_interface(cache_root, split_receipt)
    entity = np.load(cache_root / "E23.npy")
    stamp = np.load(cache_root / "T23.npy")
    log(f"接口构建完成：{len(entity):,} 个片段")

    checks = assert_causality(interface, entity, stamp)
    log(f"四条因果断言：{checks}")

    entity_count = int(entity.max()) + 1
    is_entity_start_count = int(interface["is_entity_start"].sum())
    if is_entity_start_count != entity_count:
        raise RuntimeError(
            f"is_entity_start 为真的行数 {is_entity_start_count} 与实体数 {entity_count} 不符"
        )

    write_receipt(interface, checks, entity_count, cache_root, output_root)
    atomic_json(
        output_root / "status.json",
        {"run_id": RUN_ID, "state": "finished", "exit_code": 0, "target_reads": 0},
    )
    log(f"收据写出：{output_root / 'receipts' / 'entity-segment-interface.json'}")
    print(
        json.dumps(
            {
                "run_id": RUN_ID,
                "segment_count": len(entity),
                "entity_count": entity_count,
                "is_entity_start_count": is_entity_start_count,
                "causality_assertions": checks,
                "target_reads": 0,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    print("CH3_FT_ENTITY_MEMORY_INTERFACE_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
