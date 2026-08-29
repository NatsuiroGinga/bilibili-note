#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CEM-BER 四格在 LSPR24 上的封印后描述性评价。

本入口**不训练、不选择、不改阈值、不碰源年封印**：四格的检查点与选轮结果在源年
已经冻结，本步只把它们各自跑一遍目标年，产出跨年度描述性读数。

**目标年特征取 `dijk-repro/cache/X24.npy`，不读 Parquet raw83**（2026-08-29 实测裁决）。
判据只有一条：**先问模型训练在哪份视图上，再决定评价读哪份数组，两侧必须同源**
（见 `.Codex/docs/RWKV/archive/基础设施/数据目录身份说明/
README-runs-diagnostics-dijk-repro-cache.md` 第六节第 2 条）。

该 README 里"X 数组不是 raw83、不能直接喂模型"的警告**对训练在 raw83 上的模型成立**
（表格 ResNet、CUDA-RWKV 走 `raw83 → 候选A → 候选B`，所以它们的目标年必须直读冻结
Parquet），**对本 FT 四格不成立**：FT 的源年训练与输入变换拟合全部消费
`dijk-repro/cache/X23.npy`（`ch3_ft_c00_dual_selection.prepare_data` →
`load_source_arrays_mmap(config["paths"]["cache_root"])`，四份配置的 `cache_root`
均为该缓存目录），因此它的同源目标年输入只能是同一管线、同一套 LSPR23 统计量产出的
`X24.npy`。把 raw83 送进按标准化取值拟合的 FT，才是那份 README 警告的失效模式本身。

实测反证（`receipts/input-transform.json`，四格 `state_hash` 同为 `72f3b712…`）：
封印变换的二值字段真值为 `Int/Ext Dst IP: true=1.205568790435791 /
false=-0.7505650520324707`，raw83 下应为 `1.0 / 0.0`；`field_integer_like` 中
`SrcPort=false`、`Protocol=false`，raw83 下这两列是整数型。已跑过的基础 FT 目标年评价
（`ch3-ft-transformer-field-token-protocol-a-seed42-v1/receipts/target-evaluation-C00`）
用同一份封印变换读 `X24.npy`，目标年词表越界率 `Protocol=0.000364`、`L3/L4 Protocol=0`；
若改喂 raw83 协议号（1/6/17），两个词表字段会整体越界、78 个分位数列全部撞训练端点。

序列结构取被 `configs/ch3-protocol-a-raw83-target-v1.json` 以 SHA-256 登记的
`I24.npy` / `M24.npy`；标签取 `y24.npy`；实体分组键取 `s24.npy` / `d24.npy`
（无向地址对，与 `base.run_evaluate_stage` 同口径）。

选轮口径：四格统一取源年实体 AP 择优的 `selected-by-entity.pt`（2026-08-28 冻结裁决）；
`selected-by-flow.pt` 一并评价，作协议敏感性对照，不作主口径。

输入变换：复用源年封印的 `sealed-input-transform.pkl`——目标年**不重新拟合**，
否则等于让模型见到目标年分布，破坏封印。

机制一（CEM）目标年记忆：从零开始，按目标年实体链顺序重新累积，与源年验证扫描
（`entity_memory_validation_metrics` 每轮先 `reset_role`）同一语义；**不从检查点恢复
源年累积的记忆状态**——那是源年实体的状态，目标年是另一批实体。只有模型权重来自检查点。

机制二（BER）ξ 是训练私有状态，推理期不参与，故 C01/C11 的目标年前向与 C00/C10
在这一点上没有差别，本工具不加载 ξ。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np

TOOL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOL_DIR.parent
for _root in (TOOL_DIR, PROJECT_ROOT / "src"):
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

import ch3_ft_c00_dual_selection as dual  # noqa: E402
import ch3_ft_transformer_field_token_protocol_a as base  # noqa: E402

RUN_ID = "ch3-ft-lspr24-descriptive-eval-v1"
SCHEMA_VERSION = "ch3-ft-lspr24-descriptive-eval-receipt-v1"
CELLS = ("c00", "c10", "c01", "c11")
SELECTION_ROLES = ("entity", "flow")

# 目标年只有一档数据角色：源年的 0＝训练实体／1＝验证实体划分在目标年不存在。
# 角色数组置该常量后，EntityMemoryState.reset_role(TARGET_ENTITY_ROLE) 命中全部实体，
# 语义等于"重置全部目标年实体"，与源年验证每轮重置验证角色一致（2026-08-29 裁决 2）。
TARGET_ENTITY_ROLE = 0

# 目标年数组白名单：与 base.TARGET_ARRAYS 同一清单，全部取自四格训练消费的同一缓存根。
TARGET_ARRAY_NAMES = ("X24", "y24", "I24", "M24", "s24", "d24", "t24")

T0 = time.time()
_LAST_BEAT = [T0]


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def beat(stage: str, done: int, total: int, started: float, every: float = 30.0) -> None:
    """限频心跳：已处理量、总量、百分比、吞吐、累计耗时与剩余时间估计。"""
    now = time.time()
    if now - _LAST_BEAT[0] < every and done < total:
        return
    _LAST_BEAT[0] = now
    elapsed = now - started
    rate = done / max(elapsed, 1e-9)
    remaining = (total - done) / max(rate, 1e-9)
    log(
        f"[{stage}] {done:,}/{total:,} ({done / max(total, 1):.1%}) "
        f"吞吐 {rate:,.0f}/s 累计 {elapsed:.0f}s 预计剩余 {remaining:.0f}s"
    )


def sha256_file(path: Path, chunk_bytes: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_bytes):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    """规范化 JSON 摘要。

    带 ``default=str``：本工具的收据混有 numpy 标量（形状、计数经 ``int()``/``float()``
    转换后本应为原生类型，但任一处遗漏都会让摘要在八次前向全部跑完之后才抛
    ``TypeError``）。``default`` 对 JSON 原生类型不改变输出，故不影响摘要稳定性，
    只把一个纯属浪费的末端崩溃换成可读字符串。
    """
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON 顶层必须是对象：{path}")
    return value


def atomic_json(path: Path, payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def write_status(output_root: Path, state: str, stage: str, exit_code: int | None,
                 detail: str, target_reads: dict[str, int]) -> None:
    """写运行级状态；``target_reads`` 如实记录目标年读取，不写 0。"""
    atomic_json(output_root / "status.json", {
        "schema_version": f"{SCHEMA_VERSION}-status-v1",
        "run_id": RUN_ID,
        "state": state,
        "stage": stage,
        "exit_code": exit_code,
        "detail": detail,
        "updated_at_unix": time.time(),
        "training_runs": 0,
        "optimizer_steps": 0,
        "parameter_updates": 0,
        "new_checkpoints_written": 0,
        "target_data_products_materialized": 0,
        "target_used_for_selection": False,
        "target_reads": target_reads,
    })


# ---------------------------------------------------------------------------
# 源年封印预检（既有逻辑，未改动语义）
# ---------------------------------------------------------------------------


def resolve_cell_runs(runs_root: Path) -> dict[str, Path]:
    """把四格短键映射到各自的正式运行目录；缺任一格即报错，不做部分评价。

    部分评价没有意义：四格判据要求同时比较 C00/C10/C01/C11，缺一格则交互项无法计算。
    """
    mapping = {
        "c00": "ch3-ft-c00-dual-selection-cuda-formal-v1",
        "c10": "ch3-ft-c10-entity-memory-cuda-formal-v1",
        "c01": "ch3-ft-c01-entity-ranking-cuda-formal-v1",
        "c11": "ch3-ft-c11-cem-ber-cuda-formal-v1",
    }
    resolved: dict[str, Path] = {}
    missing: list[str] = []
    for cell, run_id in mapping.items():
        root = runs_root / run_id
        selection = root / "receipts" / "selection.json"
        if not selection.is_file():
            missing.append(f"{cell}({run_id})")
            continue
        resolved[cell] = root
    if missing:
        raise SystemExit(f"四格未齐备，缺：{', '.join(missing)}；不做部分评价")
    return resolved


def load_sealed_selection(run_root: Path) -> dict[str, Any]:
    """读取源年封印的选轮收据，确认其为已完成运行。"""
    receipt = json.loads((run_root / "receipts" / "selection.json").read_text(encoding="utf-8"))
    status = json.loads((run_root / "status.json").read_text(encoding="utf-8"))
    if status.get("state") != "finished" or status.get("exit_code") != 0:
        raise SystemExit(f"{run_root.name} 未正常完成，拒绝评价：{status}")
    if int(status.get("target_reads", -1)) != 0:
        raise SystemExit(f"{run_root.name} 源年运行的 target_reads 非零，封印已破")
    return receipt


# ---------------------------------------------------------------------------
# 四格运行配置一致性与同源核验
# ---------------------------------------------------------------------------


def load_cell_configs(cell_runs: dict[str, Path]) -> dict[str, dict[str, Any]]:
    """读取四格各自 ``initialize_run`` 落盘的冻结配置副本。"""
    return {cell: load_json(root / "config.json") for cell, root in cell_runs.items()}


def assert_cross_cell_agreement(configs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """四格必须共享同一缓存根、输入候选、序列长度、设备精度与编译开关。

    这些是"同一比较集"的前提：缓存根不同即两侧数据不同源；``torch_compile`` 不同即
    数值路径分叉（服务器实测编译前后 logits 最大绝对差 8.940697e-07），四格读数不可比。
    """
    shared = {
        "cache_root": lambda c: c["paths"]["cache_root"],
        "input_candidate": lambda c: c["data"]["input_candidate"],
        "sequence_length": lambda c: c["training"]["sequence_length"],
        "device_type": lambda c: c["runtime"]["device_type"],
        "precision_profile_id": lambda c: c["runtime"]["precision_profile_id"],
        "torch_compile": lambda c: c["runtime"].get("torch_compile"),
        "entity_aggregation": lambda c: c["evaluation"]["entity_aggregation"],
        "base_config_sha256": lambda c: c["base"]["config_sha256"],
        "base_tool_sha256": lambda c: c["base"]["tool_sha256"],
    }
    agreement: dict[str, Any] = {}
    for name, getter in shared.items():
        values = {cell: getter(config) for cell, config in configs.items()}
        distinct = {canonical_sha256(value) for value in values.values()}
        if len(distinct) != 1:
            raise SystemExit(f"四格在 {name} 上不一致，拒绝并列评价：{values}")
        agreement[name] = values[CELLS[0]]
    if agreement["entity_aggregation"] != "maximum_over_validation_flows":
        raise SystemExit(f"实体聚合口径不符：{agreement['entity_aggregation']}")
    # 逐格记录各自的验证批（C00=128、C10=64 已实测不同）：它只影响分批，不影响数值，
    # 但按各格源年验证使用的同一取值执行，读数才与已封印源年扫描同路径。
    agreement["validation_batch_sequences"] = {
        cell: int(config["training"]["validation_batch_sequences"]) for cell, config in configs.items()
    }
    agreement["entity_memory_enabled"] = {
        cell: dual.entity_memory_enabled_from_config(config) for cell, config in configs.items()
    }
    agreement["entity_ranking_enabled"] = {
        cell: dual.entity_ranking_enabled_from_config(config) for cell, config in configs.items()
    }
    return agreement


def load_shared_transform(cell_runs: dict[str, Path]) -> tuple[Any, dict[str, Any]]:
    """载入源年封印输入变换，并断言四格 ``state_hash`` 完全一致。

    四格共享同一份封印变换是"同一比较集"的另一前提；实测四格同为
    ``72f3b712f16ca8c1462313eb20445d0436bb90099c22153ac1d67aca79d14b36``。
    """
    hashes: dict[str, str] = {}
    for cell, root in cell_runs.items():
        receipt = load_json(root / "receipts" / "input-transform.json")
        hashes[cell] = str(receipt["state_hash"])
    if len(set(hashes.values())) != 1:
        raise SystemExit(f"四格封印输入变换 state_hash 不一致，拒绝评价：{hashes}")
    transform_path = cell_runs[CELLS[0]] / "artifacts" / "sealed-input-transform.pkl"
    transform = base.load_input_transform(transform_path)
    if transform.state_hash != hashes[CELLS[0]]:
        raise SystemExit(
            f"封印变换对象 state_hash 与收据不符：{transform.state_hash} vs {hashes[CELLS[0]]}"
        )
    # 目标年计数分区：只影响诊断计数器，绝不改变任何冻结状态（FieldTokenTransform.switch_region）。
    transform.switch_region("target")
    return transform, {
        "sealed_transform_path": str(transform_path),
        "sealed_transform_file_sha256": sha256_file(transform_path),
        "state_hash": transform.state_hash,
        "state_hash_identical_across_cells": True,
        "per_cell_state_hash": hashes,
        "refitted_on_target": False,
        "numeric_field_count": int(transform.numeric_field_count),
        "vocabulary_field_count": int(transform.vocabulary_field_count),
        "categories": list(transform.categories),
    }


def verify_target_arrays(cache_root: Path, target_config_path: Path) -> dict[str, Any]:
    """核验目标年数组身份：I24/M24 对冻结合同的 SHA-256，其余数组登记路径与摘要。

    同时登记训练侧 ``X23.npy`` 的摘要——它与 ``X24.npy`` 出自同一 dijk 复现管线、
    同一套 LSPR23 统计量，是"两侧同源"这一裁决的直接字节级留痕。
    """
    target_config = load_json(target_config_path)
    product = target_config["year_product"]
    sequence_arrays = product["sequence_arrays"]

    checks: list[dict[str, Any]] = []
    arrays: dict[str, Any] = {}
    log("核验：目标年数组路径、字节数与内容摘要")
    for name in TARGET_ARRAY_NAMES:
        path = cache_root / f"{name}.npy"
        if not path.is_file():
            raise SystemExit(f"缺目标年数组：{path}")
        arrays[name] = {
            "path": str(path),
            "bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }
        log(f"  {name}: {arrays[name]['bytes']:,} 字节 sha256={arrays[name]['sha256'][:16]}…")

    for name in ("I24", "M24"):
        declared = Path(sequence_arrays[f"{name}_path"])
        local = cache_root / f"{name}.npy"
        if declared.resolve() != local.resolve():
            raise SystemExit(f"{name} 缓存路径与目标物化配置声明不一致：{declared} vs {local}")
        checks.append({
            "check": f"frozen_{name}_sha256",
            "observed": arrays[name]["sha256"],
            "expected": str(sequence_arrays[f"{name}_sha256"]),
            "passed": arrays[name]["sha256"] == str(sequence_arrays[f"{name}_sha256"]),
            "blocking": True,
            "note": "目标年物化配置把该缓存文件登记为冻结序列数组",
        })

    training_matrix = cache_root / "X23.npy"
    if not training_matrix.is_file():
        raise SystemExit(f"缺训练侧矩阵：{training_matrix}")
    log("核验：训练侧 X23.npy 摘要（同源留痕，文件较大耗时约数十秒）")
    training_side = {
        "path": str(training_matrix),
        "bytes": int(training_matrix.stat().st_size),
        "sha256": sha256_file(training_matrix),
        "note": "四格源年训练与输入变换拟合消费的就是这份矩阵，与 X24 同管线同统计量",
    }

    for item in checks:
        log(f"  {item['check']}（阻断项）: {'通过' if item['passed'] else '不通过'}")
    if not all(item["passed"] for item in checks if item["blocking"]):
        failed = [item["check"] for item in checks if item["blocking"] and not item["passed"]]
        raise SystemExit(f"目标年数组身份阻断核验不通过：{failed}")

    return {
        "cache_root": str(cache_root),
        "target_materialization_config": str(target_config_path),
        "target_materialization_config_sha256": sha256_file(target_config_path),
        "target_arrays": arrays,
        "training_side_matrix": training_side,
        "same_source_rationale": (
            "两侧同源判据：X23 与 X24 同为 dijk 复现管线标准化输出（非有限值置0 → "
            "LSPR23 逐列均值方差标准化 → 裁剪[-10,10]），四格训练消费 X23，故目标年只能读 X24；"
            "Parquet raw83 是训练在 raw83 上的模型（表格ResNet/CUDA-RWKV）的路径，不是本模型的"
        ),
        "parquet_raw83_opened_by_this_run": False,
        "checks": checks,
        "blocking_passed": True,
    }


# ---------------------------------------------------------------------------
# 目标年数据：实体、逐序列实体与时间、严格过去接口
# ---------------------------------------------------------------------------


def build_flow_entity(cache_root: Path) -> tuple[Any, int]:
    """按无向源目地址对归并逐流实体，与 ``base.run_evaluate_stage`` 逐字同口径。"""
    log("载入 s24/d24 并按无向地址对归并逐流实体（20,227,356 条，需数分钟）")
    source_ip = np.load(cache_root / "s24.npy", allow_pickle=True)
    destination_ip = np.load(cache_root / "d24.npy", allow_pickle=True)
    key = np.array(
        [
            left + "|" + right if left <= right else right + "|" + left
            for left, right in zip(source_ip, destination_ip)
        ],
        dtype=object,
    )
    del source_ip, destination_ip
    _, flow_entity = np.unique(key, return_inverse=True)
    del key
    flow_entity = flow_entity.astype(np.int64, copy=False)
    entity_count = int(flow_entity.max()) + 1
    log(f"目标年实体数={entity_count:,}")
    return flow_entity, entity_count


def assert_sequence_entity_contract(indices: Any, valid: Any, flow_entity: Any,
                                    n_flow: int) -> dict[str, Any]:
    """裁决 2 授权的目标年序列合同断言，全部通过才允许推导逐序列实体与时间。

    四条：序列索引恰好覆盖每条流一次；掩码为前缀形态（``_segment_summary_from_injected``
    取"最后一个有效流"依赖该形态）；每条序列的全部有效流同属一个实体；首个有效流的
    实体即该序列的唯一实体。任一不成立即停止——跨实体序列会破坏 CEM 的严格过去语义。
    """
    log("断言：目标年序列合同（覆盖唯一、前缀掩码、序列不跨实体）")
    occurrence = np.zeros(n_flow, dtype=np.int32)
    np.add.at(occurrence, indices[valid], 1)
    covered_once = int((occurrence == 1).sum())
    del occurrence

    per_row_valid = valid.sum(axis=1)
    columns = np.arange(valid.shape[1])[None, :]
    prefix_mask_ok = bool(np.array_equal(columns < per_row_valid[:, None], valid))

    sequence_entity = flow_entity[indices]
    largest = np.int64(np.iinfo(np.int64).max)
    masked_min = np.where(valid, sequence_entity, largest).min(axis=1)
    masked_max = np.where(valid, sequence_entity, np.int64(-1)).max(axis=1)
    violating = int((masked_min != masked_max).sum())
    del sequence_entity, masked_max

    if not bool(valid[:, 0].all()):
        raise SystemExit("存在首列即无效的序列，前缀掩码假设不成立")
    first_flow_entity = flow_entity[indices[:, 0]]
    first_flow_agrees = bool(np.array_equal(first_flow_entity, masked_min))
    del masked_min

    receipt = {
        "sequence_count": int(indices.shape[0]),
        "flow_count": int(n_flow),
        "valid_positions": int(valid.sum()),
        "flows_covered_exactly_once": covered_once,
        "coverage_exactly_once": covered_once == n_flow,
        "prefix_mask": prefix_mask_ok,
        "sequences_spanning_multiple_entities": violating,
        "no_sequence_spans_multiple_entities": violating == 0,
        "first_valid_flow_entity_equals_sequence_entity": first_flow_agrees,
        "minimum_valid_flows_per_sequence": int(per_row_valid.min()),
        "maximum_valid_flows_per_sequence": int(per_row_valid.max()),
        "derivation_rule": (
            "逐流实体＝无向 s24|d24 地址对的 np.unique 归并；逐序列实体与时间＝该序列"
            "首个有效流的实体与 t24；角色数组置单一常量（目标年不存在训练/验证角色之分）"
        ),
    }
    for key in ("coverage_exactly_once", "prefix_mask", "no_sequence_spans_multiple_entities",
                "first_valid_flow_entity_equals_sequence_entity"):
        log(f"  {key}: {receipt[key]}")
    if not all(receipt[key] for key in (
        "coverage_exactly_once", "prefix_mask", "no_sequence_spans_multiple_entities",
        "first_valid_flow_entity_equals_sequence_entity",
    )):
        raise SystemExit(f"目标年序列合同断言不通过，停止评价：{receipt}")
    return receipt


def build_target_entity_memory_interface(sequence_entity: Any, sequence_time: Any) -> dict[str, Any]:
    """用与源年同一个 ``_causal_order`` 建立目标年逐序列严格过去接口。

    源年的 ``build_interface`` 硬编码读 ``E23/T23`` 并重放训练/验证实体划分得到
    ``role_id``；目标年既没有 ``E24/T24`` 物化数组，也不存在这两档角色，因此这里直接
    调用不含角色逻辑的 ``_causal_order``，再把 ``role_id`` 置单一常量。
    ``assert_causality`` 的 ``same_role`` 在常量角色下定义上必然成立，本收据显式标注
    该项在目标年不构成独立检验（源年才是真实检验）。
    """
    import ch3_ft_entity_memory_interface as entity_interface

    previous, is_entity_start, segment_ordinal = entity_interface._causal_order(
        sequence_entity, sequence_time
    )
    interface = {
        "previous_segment_row": previous,
        "is_entity_start": is_entity_start,
        "segment_ordinal": segment_ordinal,
        "role_id": np.full(len(sequence_entity), TARGET_ENTITY_ROLE, dtype=np.int8),
    }
    checks = entity_interface.assert_causality(interface, sequence_entity, sequence_time)
    entity_count = int(sequence_entity.max()) + 1
    starts = int(is_entity_start.sum())
    if starts != entity_count:
        raise SystemExit(f"链首片段数 {starts} 与实体数 {entity_count} 不符")
    receipt = {
        "segment_count": int(len(previous)),
        "entity_count": entity_count,
        "is_entity_start_count": starts,
        "linked_segment_count": int((previous >= 0).sum()),
        "causality_assertions": checks,
        "same_role_is_definitional_on_target": True,
        "same_role_note": "目标年角色为单一常量，same_role 必然成立，不构成独立检验",
    }
    log(f"目标年严格过去接口：片段={receipt['segment_count']:,} 链首={starts:,} "
        f"断言={checks}")
    return {"interface": interface, "receipt": receipt}


def load_target_year(cache_root: Path) -> dict[str, Any]:
    """载入目标年数组并推导实体、逐序列实体与时间、严格过去接口。

    ``X24`` 整体载入主机（6.7 GiB），与 ``base.load_target_arrays`` 同一做法；随后的
    逐微批取值走 ``ProtocolASourceView.features``，与源年完全同一段代码。
    """
    log("载入目标年 X24/y24/I24/M24/t24")
    matrix = np.load(cache_root / "X24.npy", allow_pickle=False)
    labels = np.load(cache_root / "y24.npy", allow_pickle=False)
    indices = np.load(cache_root / "I24.npy", allow_pickle=False)
    mask = np.load(cache_root / "M24.npy", allow_pickle=False)
    flow_time = np.load(cache_root / "t24.npy", allow_pickle=False)
    n_flow = int(labels.shape[0])
    n_sequence = int(indices.shape[0])
    if matrix.shape != (n_flow, base.DIJK_FEATURE_COUNT):
        raise SystemExit(f"X24 形状不符：{matrix.shape}")
    if matrix.shape[0] != base.LSPR24_FLOW_COUNT:
        raise SystemExit(f"X24 流数与冻结身份不符：{matrix.shape[0]}")
    if mask.shape != indices.shape:
        raise SystemExit(f"M24 形状与 I24 不符：{mask.shape}")
    if flow_time.shape != (n_flow,):
        raise SystemExit(f"t24 形状不符：{flow_time.shape}")
    valid = mask > 0.5

    flow_entity, entity_count = build_flow_entity(cache_root)
    if flow_entity.shape != (n_flow,):
        raise SystemExit(f"逐流实体形状不符：{flow_entity.shape}")
    contract = assert_sequence_entity_contract(indices, valid, flow_entity, n_flow)

    sequence_entity = flow_entity[indices[:, 0]].astype(np.int64, copy=False)
    sequence_time = flow_time[indices[:, 0]]
    built = build_target_entity_memory_interface(sequence_entity, sequence_time)

    entity_labels = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_labels, flow_entity, labels)
    positive_entities = int(entity_labels.sum())
    flow_positive_rate = float(labels.astype(np.float64).mean())
    log(f"目标年：流={n_flow:,} 序列={n_sequence:,} 实体={entity_count:,} "
        f"正实体={positive_entities:,} 逐流正例率={flow_positive_rate:.14f}")

    return {
        "matrix": matrix,
        "labels": labels,
        "indices": indices,
        "mask": mask,
        "flow_time": flow_time,
        "flow_entity": flow_entity,
        "entity_labels": entity_labels,
        "entity_count": entity_count,
        "sequence_entity": sequence_entity,
        "sequence_time": sequence_time,
        "interface": built["interface"],
        "n_flow": n_flow,
        "n_sequence": n_sequence,
        "receipt": {
            "flow_count": n_flow,
            "sequence_count": n_sequence,
            "entity_count": entity_count,
            "positive_entity_count": positive_entities,
            "flow_positive_rate": flow_positive_rate,
            "sequence_entity_contract": contract,
            "strict_past_interface": built["receipt"],
            "entity_key_recipe": "unordered_source_destination_ip_pair_grouping_only",
            "derived_arrays_persisted": 0,
            "note": "E24/T24 无物化数组，按裁决 2 口径从 I24 首个有效流推导，只驻内存",
        },
    }


def build_target_view(target: dict[str, Any], transform: Any) -> Any:
    """复用 ``ProtocolASourceView`` 承载目标年数组。

    该类按 ``X23/y23/I23/M23`` 四个键取数组，本身不含任何"源年专有"逻辑；直接以目标年
    数组按同名键构造，可保证 ``gather_sequences`` 与 ``features`` 与源年**逐字同一段代码**，
    不另写一份可能悄悄漂移的目标年取数实现。
    """
    return base.ProtocolASourceView(
        {
            "X23": target["matrix"],
            "y23": target["labels"],
            "I23": target["indices"],
            "M23": target["mask"],
        },
        transform,
    )


# ---------------------------------------------------------------------------
# 模型与打分
# ---------------------------------------------------------------------------


def load_cell_model(config: dict[str, Any], base_config: dict[str, Any], view: Any,
                    checkpoint_path: Path, torch_module: Any, device: Any) -> tuple[Any, dict[str, Any]]:
    """按格构造模型并回载封印权重。

    ``weights_only`` 取舍（2026-08-29 服务器实测后选定）：``selected-by-*.pt`` 的载荷只有
    ``model_state_dict`` 与 JSON 型身份字段，实测 ``weights_only=True`` 可直接载入，故这里
    用安全默认值 ``True``。**不要照抄 ``run_training`` 的 ``weights_only=False``**——那里读的是
    ``inflight.pt``，载荷含 numpy RNG 状态与调度器游标等非张量对象，必须关掉该保护；
    本工具只需权重，没有理由承担同样的反序列化面。

    模型构造复用 ``dual.build_model_optimizer``：它同时做骨干参数量、机制一参数量闭式
    交叉核验与 ``expected_parameter_count`` 断言，并按配置施加 ``torch.compile``（四格
    统一启用，编译改变数值路径，源年验证扫描也走同一条），返回的优化器在评价中不使用。
    """
    model, unused_optimizer, optimizer_receipt = dual.build_model_optimizer(
        config, base_config, view, torch_module, device
    )
    del unused_optimizer  # 评价不训练：不做 zero_grad、不做 step，优化器只是构造副产物
    payload = torch_module.load(checkpoint_path, map_location="cpu", weights_only=True)
    if payload.get("schema_version") != dual.CHECKPOINT_SCHEMA_VERSION:
        raise SystemExit(f"选择检查点模式不符：{payload.get('schema_version')}")
    if payload.get("run_id") != config["identity"]["run_id"]:
        raise SystemExit(f"检查点运行身份不符：{payload.get('run_id')}")
    model.load_state_dict(payload["model_state_dict"])
    model = model.to(device)
    model.eval()
    for parameter in model.parameters():
        if parameter.dtype != torch_module.float32:
            raise SystemExit("回载参数未保持 FP32")
    return model, {
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": sha256_file(checkpoint_path),
        "selection_role": payload.get("selection_role"),
        "selected_epoch": payload.get("selected_epoch"),
        "selected_source_metric": payload.get("selected_metric"),
        "weights_only_load": True,
        "parameter_count": int(sum(p.numel() for p in model.parameters())),
        "optimizer_candidate": optimizer_receipt["key"],
    }


def score_target_bare(config: dict[str, Any], model: Any, view: Any, device: Any,
                      profile: dict[str, Any], precision: Any, torch_module: Any,
                      n_flow: int, n_sequence: int, stage: str) -> tuple[Any, Any, dict[str, Any]]:
    """z1=0（C00/C01）目标年打分：与源年 ``validation_metrics`` 同一前向路径。

    ``dual.forward_bare`` 内含 ``precision.autocast_context``，与源年 z1=0 验证扫描一致。
    """
    batch_sequences = int(config["training"]["validation_batch_sequences"])
    length = int(config["training"]["sequence_length"])
    scores = np.zeros(n_flow, dtype=np.float32)
    seen = np.zeros(n_flow, dtype=bool)
    rows_all = np.arange(n_sequence, dtype=np.int64)
    if device.type == "cuda":
        torch_module.cuda.reset_peak_memory_stats(device)
    started = time.time()
    with torch_module.no_grad():
        for start in range(0, n_sequence, batch_sequences):
            rows = rows_all[start : start + batch_sequences]
            indices, valid, _labels = view.gather_sequences(rows, length)
            numeric, categorical = view.features(indices)
            logits, _ = dual.forward_bare(
                model, numeric, categorical, valid, device, profile, precision, torch_module
            )
            probabilities = torch_module.sigmoid(logits.to(torch_module.float32)).cpu().numpy()
            selected = indices[valid]
            if bool(seen[selected].any()):
                raise SystemExit("目标年流被重复计分")
            seen[selected] = True
            scores[selected] = probabilities[valid]
            beat(stage, min(start + batch_sequences, n_sequence), n_sequence, started)
    dual.synchronize_device(torch_module, device)
    return scores, seen, forward_resources(model, device, torch_module, started, n_flow, n_sequence)


def score_target_entity_memory(config: dict[str, Any], model: Any, view: Any, scheduler: Any,
                               memory_state: Any, interface: dict[str, Any], entity_of_row: Any,
                               device: Any, profile: dict[str, Any], precision: Any,
                               torch_module: Any, n_flow: int, n_sequence: int,
                               stage: str) -> tuple[Any, Any, dict[str, Any]]:
    """z1=1（C10/C11）目标年打分：与源年 ``entity_memory_validation_metrics`` 同一语义。

    记忆从零开始（先 ``reset_role``，目标年角色为单一常量故等价于重置全部实体），按实体链
    顺序逐轮推进，严格过去顺序为"读记忆 → 前向 → 写回"；**不从检查点恢复源年记忆**。

    精度路径按源年验证扫描逐字复刻：源年 z1=1 的验证前向**不套 autocast**（
    ``entity_memory_validation_metrics`` 直接调 ``encode``/``inject``/``predict``），
    与 z1=0 经 ``forward_bare`` 进 autocast 的路径本就不同。这里保持同一不对称，
    否则目标年读数与已封印源年读数不再同源。改动它需要先重跑源年，不是本工具的范围。
    """
    batch_sequences = int(config["training"]["validation_batch_sequences"])
    length = int(config["training"]["sequence_length"])
    scores = np.zeros(n_flow, dtype=np.float32)
    seen = np.zeros(n_flow, dtype=bool)
    memory_state.reset_role(TARGET_ENTITY_ROLE)
    gate_means: list[float] = []
    valid_slot_means: list[float] = []
    reset_count = 0
    recovery_count = 0
    no_history_flow_count = 0
    total_flow_count = 0
    processed_sequences = 0
    if device.type == "cuda":
        torch_module.cuda.reset_peak_memory_stats(device)
    started = time.time()
    with torch_module.no_grad():
        for round_rows, round_entities in scheduler.validation_rounds():
            dual.assert_recovery_adjacency(round_rows, interface, entity_of_row)
            is_start_np = interface["is_entity_start"][round_rows]
            for start in range(0, len(round_rows), batch_sequences):
                stop = start + batch_sequences
                micro_rows = round_rows[start:stop]
                micro_entity_ids = torch_module.from_numpy(
                    round_entities[start:stop].astype(np.int64)
                ).to(device)
                micro_is_start = torch_module.from_numpy(is_start_np[start:stop]).to(device)

                if bool(micro_is_start.any()):
                    memory_state.reset_entities(micro_entity_ids[micro_is_start])
                    reset_count += int(micro_is_start.sum().item())
                recovery_count += int(micro_rows.shape[0]) - int(micro_is_start.sum().item())

                segment_memory = memory_state.read(micro_entity_ids)
                segment_valid = memory_state.valid(micro_entity_ids)
                no_history_flow_count += int((~segment_valid.any(dim=1)).sum().item())

                indices, valid, _labels = view.gather_sequences(micro_rows, length)
                numeric, categorical = view.features(indices)
                numeric_t = torch_module.from_numpy(numeric).to(device)
                categorical_t = (
                    torch_module.from_numpy(categorical).to(device) if categorical is not None else None
                )
                batch, sequence_length = valid.shape
                flat_num = numeric_t.reshape(batch * sequence_length, numeric_t.shape[-1])
                flat_cat = (
                    categorical_t.reshape(batch * sequence_length, categorical_t.shape[-1])
                    if categorical_t is not None else None
                )

                representation = model.encode(flat_num, flat_cat)
                width = representation.shape[-1]
                broadcast_memory, broadcast_valid = dual._broadcast_segment_memory(
                    segment_memory, segment_valid, batch, sequence_length
                )
                injected = model.inject(representation, broadcast_memory, broadcast_valid)
                logits = model.predict(injected).reshape(batch, sequence_length)
                gate_means.append(model.memory.gate_statistics()["gate_mean"])
                valid_slot_means.append(
                    float(segment_valid.sum(dim=1).to(torch_module.float32).mean().item())
                )

                summary = dual._segment_summary_from_injected(
                    injected, valid, batch, sequence_length, width, torch_module, device
                )
                memory_state.write(micro_entity_ids, summary)

                probabilities = torch_module.sigmoid(logits.to(torch_module.float32)).cpu().numpy()
                selected = indices[valid]
                if bool(seen[selected].any()):
                    raise SystemExit("目标年流被重复计分")
                seen[selected] = True
                scores[selected] = probabilities[valid]
                total_flow_count += int(valid.sum())
                processed_sequences += int(micro_rows.shape[0])
                beat(stage, processed_sequences, n_sequence, started)
    dual.synchronize_device(torch_module, device)
    if processed_sequences != n_sequence:
        raise SystemExit(f"实体链扫描覆盖序列数不符：{processed_sequences} != {n_sequence}")
    resources = forward_resources(model, device, torch_module, started, n_flow, n_sequence)
    resources["mechanism_diagnostics"] = {
        "gate_mean": float(np.mean(gate_means)) if gate_means else None,
        "mean_valid_memory_slots": float(np.mean(valid_slot_means)) if valid_slot_means else None,
        "state_reset_count": reset_count,
        "cross_segment_recovery_count": recovery_count,
        "no_history_flow_ratio": (no_history_flow_count / total_flow_count) if total_flow_count else None,
        "memory_initialized_from_checkpoint": False,
        "memory_initialization": "zero_then_accumulate_in_target_entity_chain_order",
    }
    return scores, seen, resources


def forward_resources(model: Any, device: Any, torch_module: Any, started: float,
                      n_flow: int, n_sequence: int) -> dict[str, Any]:
    wall_seconds = time.time() - started
    resources = {
        "pure_inference_wall_seconds": wall_seconds,
        "inference_gpu_hours": wall_seconds / 3600.0,
        "sequences_scored": n_sequence,
        "flows_scored": n_flow,
        "flows_per_second": n_flow / max(wall_seconds, 1e-12),
        "parameter_count": int(sum(item.numel() for item in model.parameters())),
        "resource_contention_note": "同卡可能存在其他进程，时间与显存按并发条件实测记录",
    }
    if device.type == "cuda":
        resources["peak_gpu_allocated_mib"] = torch_module.cuda.max_memory_allocated(device) / 2**20
        resources["peak_gpu_reserved_mib"] = torch_module.cuda.max_memory_reserved(device) / 2**20
    return resources


# ---------------------------------------------------------------------------
# 指标：全部复用 base FT 模块，与已封印源年读数同源
# ---------------------------------------------------------------------------


def cell_metrics(cell: str, scores: Any, seen: Any, target: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """按 base FT 模块的实体聚合与曲线函数计算目标年读数。

    四格 ``evaluation.entity_aggregation`` 均为 ``maximum_over_validation_flows``，没有
    可学 Lp 池化（那是 CPA-ELP 家族的口径），故 ``entity_scores`` 一律传 ``p_value=None``，
    主口径实体分数与最大池化实体分数在构造上就是同一组数。
    """
    from sklearn.metrics import average_precision_score, roc_auc_score

    started = time.time()
    labels = target["labels"]
    entity_labels = target["entity_labels"]
    aggregated = base.entity_scores(scores, seen, target["flow_entity"], target["entity_count"], None)
    scored_entities = np.isfinite(aggregated)
    metrics = {
        "cell": cell,
        "entity_aggregation": "maximum_over_validation_flows",
        "entity_aggregation_p": None,
        "entity_and_maximum_entity_identical_by_construction": True,
        "flow_count": int(seen.sum()),
        "positive_flow_count": int(labels[seen].sum()),
        "flow_average_precision": float(average_precision_score(labels[seen], scores[seen])),
        "flow_roc_auc": float(roc_auc_score(labels[seen], scores[seen])),
        "entity_average_precision": float(
            average_precision_score(entity_labels[scored_entities], aggregated[scored_entities])
        ),
        "maximum_entity_average_precision": float(
            average_precision_score(entity_labels[scored_entities], aggregated[scored_entities])
        ),
        "dr_at_fpr": {
            f"fpr_{value:g}": base.dr_at_fpr(aggregated, entity_labels, value)
            for value in base.DR_FPR_GRID
        },
        "entity_count": int(target["entity_count"]),
        "scored_entity_count": int(scored_entities.sum()),
        "positive_entity_count": int(entity_labels.sum()),
        "negative_entity_count": int((entity_labels == 0).sum()),
        "dr_fpr_grid": list(base.DR_FPR_GRID),
        "readout_rule": (
            "base.dr_at_fpr：负类实体分数降序后取下标 int(len(negative)*nominal_fpr)，"
            "在该阈值上统计正类实体检出比例；nominal_fpr 不等于实际可达 FPR"
        ),
        "aggregation_wall_seconds": time.time() - started,
        "scores_persisted": False,
        "entity_scores_persisted": False,
    }
    curve = base.complete_budget_curve(aggregated, entity_labels)
    del aggregated
    return metrics, curve


# ---------------------------------------------------------------------------
# 单元制品与清单
# ---------------------------------------------------------------------------


def unit_name(cell: str, role: str) -> str:
    return f"{cell}-by-{role}"


def save_unit(output_root: Path, cell: str, role: str, identity: dict[str, Any],
              checkpoint: dict[str, Any], metrics: dict[str, Any], curve: dict[str, Any],
              resources: dict[str, Any]) -> dict[str, Any]:
    """落盘一个 (格, 选轮口径) 评价单元。

    ``identity`` 必须与 ``load_completed_unit`` 的比较对象**逐字相同**，因此检查点收据
    单列在 ``checkpoint`` 键下，不并进 ``identity``——否则复用路径会因多出一个键而
    永远判定"身份不符"，把断点续跑变成必然重跑八次全量前向。
    """
    unit_root = output_root / "target-cells" / unit_name(cell, role)
    if unit_root.exists():
        raise SystemExit(f"{unit_name(cell, role)} 单元目录已存在，拒绝覆盖")
    temporary_root = unit_root.with_name(f"{unit_name(cell, role)}.partial.{os.getpid()}")
    temporary_root.mkdir(parents=True, exist_ok=False)
    curve_path = temporary_root / "complete-alert-budget-curve.npz"
    with curve_path.open("wb") as handle:
        np.savez_compressed(handle, **curve)
    aggregate = {
        "schema_version": f"{SCHEMA_VERSION}-unit-v1",
        "cell": cell,
        "selection_role": role,
        "identity": identity,
        "checkpoint": checkpoint,
        "metrics": metrics,
        "resource": resources,
        "isolation": {
            "training_runs": 0,
            "optimizer_steps": 0,
            "parameter_updates": 0,
            "new_checkpoints_written": 0,
            "target_forward_passes": 1,
            "one_forward_pass_over_all_sequences": True,
            "target_data_products_materialized": 0,
            "source_run_directories_modified": 0,
        },
        "curve_artifact": {
            "filename": curve_path.name,
            "bytes": curve_path.stat().st_size,
            "sha256": sha256_file(curve_path),
            "fields": sorted(curve),
        },
        "complete": True,
    }
    atomic_json(temporary_root / "aggregate.json", aggregate)
    unit_root.parent.mkdir(parents=True, exist_ok=True)
    os.replace(temporary_root, unit_root)
    return aggregate


def load_completed_unit(output_root: Path, cell: str, role: str,
                        identity: dict[str, Any]) -> dict[str, Any] | None:
    unit_root = output_root / "target-cells" / unit_name(cell, role)
    if not unit_root.exists():
        return None
    aggregate_path = unit_root / "aggregate.json"
    curve_path = unit_root / "complete-alert-budget-curve.npz"
    if not aggregate_path.is_file() or not curve_path.is_file():
        raise SystemExit(f"{unit_name(cell, role)} 存在不完整单元目录")
    aggregate = load_json(aggregate_path)
    if aggregate.get("identity") != identity or aggregate.get("complete") is not True:
        raise SystemExit(f"{unit_name(cell, role)} 完成单元身份不符，拒绝伪装完成")
    if aggregate.get("curve_artifact", {}).get("sha256") != sha256_file(curve_path):
        raise SystemExit(f"{unit_name(cell, role)} 曲线制品摘要不符")
    log(f"{unit_name(cell, role)} 复用身份与摘要一致的完成单元，不重复前向")
    return aggregate


def build_manifest(output_root: Path) -> None:
    """重写制品清单；逐流与逐实体分数一律不落盘，出现即报错。"""
    forbidden = ("flow-score", "flow_score", "entity-score", "entity_score", ".pt", ".pth",
                 ".ckpt", ".npy", ".parquet", ".pkl")
    files: dict[str, Any] = {}
    for path in sorted(item for item in output_root.rglob("*")
                       if item.is_file() and item.name != "artifact-manifest.json"):
        relative = str(path.relative_to(output_root))
        if any(token in relative.lower() for token in forbidden):
            raise SystemExit(f"运行根出现禁止制品：{relative}")
        files[relative] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    atomic_json(output_root / "artifact-manifest.json", {
        "schema_version": f"{SCHEMA_VERSION}-manifest-v1",
        "run_id": RUN_ID,
        "files": files,
        "cells": list(CELLS),
        "selection_roles": list(SELECTION_ROLES),
        "training_runs": 0,
        "new_checkpoints_written": 0,
        "target_data_products_materialized": 0,
        "per_flow_scores_persisted": False,
        "per_entity_scores_persisted": False,
        "forbidden_artifacts_absent": True,
        "complete": True,
    })


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def run_preflight(runs_root: Path) -> tuple[dict[str, Path], dict[str, Any], dict[str, Any]]:
    log("核验四格齐备与源年封印状态")
    cell_runs = resolve_cell_runs(runs_root)
    sealed: dict[str, Any] = {}
    for cell in CELLS:
        root = cell_runs[cell]
        receipt = load_sealed_selection(root)
        best_entity = receipt["best_by_entity"]
        best_flow = receipt["best_by_flow"]
        sealed[cell] = {
            "run_id": receipt["run_id"],
            "source_entity_ap": best_entity["metric"],
            "source_entity_epoch": best_entity["epoch"],
            "source_flow_ap": best_flow["metric"],
            "source_flow_epoch": best_flow["epoch"],
            "epochs": len(receipt["history"]),
        }
        for role in SELECTION_ROLES:
            checkpoint = root / "checkpoints" / f"selected-by-{role}.pt"
            if not checkpoint.is_file():
                raise SystemExit(f"{cell} 缺 selected-by-{role}.pt，无法评价")
        log(f"  {cell}: 源年实体AP={best_entity['metric']:.6f}（轮{best_entity['epoch']}）"
            f" 逐流AP={best_flow['metric']:.6f}（轮{best_flow['epoch']}）")

    interaction = (
        sealed["c11"]["source_entity_ap"] - sealed["c10"]["source_entity_ap"]
        - sealed["c01"]["source_entity_ap"] + sealed["c00"]["source_entity_ap"]
    )
    baseline = sealed["c00"]["source_entity_ap"]
    verdict = {
        "c10_over_c00": sealed["c10"]["source_entity_ap"] - baseline,
        "c01_over_c00": sealed["c01"]["source_entity_ap"] - baseline,
        "c11_is_best": sealed["c11"]["source_entity_ap"] >= max(
            sealed[c]["source_entity_ap"] for c in ("c00", "c10", "c01")
        ),
        "interaction": interaction,
        "note": "以上为源年读数，仅用于确认四格结构；目标年读数在下方 target 段",
    }
    log(f"源年四格判据：C10−C00={verdict['c10_over_c00']:+.6f} "
        f"C01−C00={verdict['c01_over_c00']:+.6f} "
        f"C11最佳={verdict['c11_is_best']} 交互={interaction:+.6f}")
    return cell_runs, sealed, verdict


def evaluate(args: argparse.Namespace, cell_runs: dict[str, Path], sealed: dict[str, Any],
             verdict: dict[str, Any]) -> dict[str, Any]:
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    target_reads = {
        "definition": "目标年读取＝数组载入次数 + 全量前向打分次数；本运行不做任何目标年物化",
        "target_array_loads": 0,
        "target_forward_passes_this_process": 0,
        "target_forward_units_reused": 0,
        "total": 0,
    }
    write_status(output_root, "running", "cross-cell-agreement", None,
                 "核验四格配置一致性与封印输入变换", target_reads)

    configs = load_cell_configs(cell_runs)
    agreement = assert_cross_cell_agreement(configs)
    log(f"四格一致：缓存根={agreement['cache_root']} 编译={agreement['torch_compile']}")
    transform, transform_receipt = load_shared_transform(cell_runs)
    log(f"封印输入变换 state_hash={transform_receipt['state_hash']}（四格一致）")

    cache_root = Path(agreement["cache_root"])
    write_status(output_root, "running", "data-verification", None,
                 "核验目标年数组身份与训练侧同源留痕", target_reads)
    data_receipt = verify_target_arrays(cache_root, Path(args.target_config).resolve())
    atomic_json(output_root / "data-verification.json", {
        "schema_version": f"{SCHEMA_VERSION}-data-verification-v1",
        "run_id": RUN_ID,
        **data_receipt,
        "cross_cell_agreement": agreement,
        "sealed_input_transform": transform_receipt,
    })

    write_status(output_root, "running", "target-context", None,
                 "载入目标年数组并推导实体链", target_reads)
    target = load_target_year(cache_root)
    target_reads["target_array_loads"] = len(TARGET_ARRAY_NAMES)
    target_reads["total"] = target_reads["target_array_loads"]
    atomic_json(output_root / "target-year-read.json", {
        "schema_version": f"{SCHEMA_VERSION}-target-year-read-v1",
        "run_id": RUN_ID,
        "cache_root": str(cache_root),
        **target["receipt"],
    })

    torch_module, device, profile, precision = dual.resolve_runtime(configs[CELLS[0]])
    log(f"运行时：设备={device.type} 精度profile={configs[CELLS[0]]['runtime']['precision_profile_id']} "
        f"torch={torch_module.__version__}")
    view = build_target_view(target, transform)

    identity_common = {
        "schema_version": f"{SCHEMA_VERSION}-unit-identity-v1",
        "run_id": RUN_ID,
        "evaluation_code_sha256": sha256_file(Path(__file__).resolve()),
        "host_tool_sha256": sha256_file(Path(dual.__file__).resolve()),
        "base_tool_sha256": sha256_file(Path(base.__file__).resolve()),
        "sealed_transform_state_hash": transform_receipt["state_hash"],
        "target_array_sha256": {
            name: item["sha256"] for name, item in data_receipt["target_arrays"].items()
        },
        "training_side_matrix_sha256": data_receipt["training_side_matrix"]["sha256"],
        "sequence_entity_contract_sha256": canonical_sha256(
            target["receipt"]["sequence_entity_contract"]
        ),
    }

    completed: dict[str, dict[str, Any]] = {}
    run_started = time.time()
    for cell in CELLS:
        config = configs[cell]
        base_config = dual.effective_base_config(config)
        entity_memory_enabled = bool(agreement["entity_memory_enabled"][cell])
        scheduler = None
        memory_state = None
        interface = None
        if entity_memory_enabled:
            scheduler = dual.EntityChainScheduler(
                np.arange(target["n_sequence"], dtype=np.int64),
                target["sequence_entity"],
                target["interface"]["segment_ordinal"],
            )
            interface = target["interface"]
            log(f"{cell}: 目标年实体链调度器实体数={scheduler.entity_count:,}")

        for role in SELECTION_ROLES:
            checkpoint_path = cell_runs[cell] / "checkpoints" / f"selected-by-{role}.pt"
            identity = {
                **identity_common,
                "cell": cell,
                "selection_role": role,
                "source_run_id": sealed[cell]["run_id"],
                "checkpoint_sha256": sha256_file(checkpoint_path),
                "validation_batch_sequences": agreement["validation_batch_sequences"][cell],
            }
            restored = load_completed_unit(output_root, cell, role, identity)
            if restored is not None:
                completed[unit_name(cell, role)] = restored
                target_reads["target_forward_units_reused"] += 1
                continue

            write_status(output_root, "running", "target-evaluation", None,
                         f"{unit_name(cell, role)} 单次全量前向", target_reads)
            model, checkpoint_receipt = load_cell_model(
                config, base_config, view, checkpoint_path, torch_module, device
            )
            if entity_memory_enabled:
                memory_state = dual.build_entity_memory_state(
                    config, base_config,
                    {
                        "entity_count": target["entity_count"],
                        "role_of_entity": np.full(
                            target["entity_count"], TARGET_ENTITY_ROLE, dtype=np.int8
                        ),
                    },
                    torch_module, device,
                )
                if int((memory_state.role_of_entity == TARGET_ENTITY_ROLE).sum()) != target["entity_count"]:
                    raise SystemExit("目标年角色数组不是单一常量，reset_role 不等价于全量重置")
                scores, seen, resources = score_target_entity_memory(
                    config, model, view, scheduler, memory_state, interface,
                    target["sequence_entity"], device, profile, precision, torch_module,
                    target["n_flow"], target["n_sequence"], f"LSPR24/{unit_name(cell, role)}打分",
                )
            else:
                scores, seen, resources = score_target_bare(
                    config, model, view, device, profile, precision, torch_module,
                    target["n_flow"], target["n_sequence"], f"LSPR24/{unit_name(cell, role)}打分",
                )
            target_reads["target_forward_passes_this_process"] += 1
            target_reads["total"] = (
                target_reads["target_array_loads"] + target_reads["target_forward_passes_this_process"]
            )
            if int(seen.sum()) != target["n_flow"]:
                raise SystemExit(f"打分覆盖流数不符：{int(seen.sum())} != {target['n_flow']}")

            metrics, curve = cell_metrics(cell, scores, seen, target)
            log(f"{unit_name(cell, role)} 实体AP={metrics['entity_average_precision']:.12f} "
                f"逐流AP={metrics['flow_average_precision']:.12f} "
                f"逐流ROC-AUC={metrics['flow_roc_auc']:.12f}")
            completed[unit_name(cell, role)] = save_unit(
                output_root, cell, role, identity, checkpoint_receipt, metrics, curve, resources,
            )
            del model, scores, seen, curve, metrics
            memory_state = None
            if device.type == "cuda":
                torch_module.cuda.empty_cache()

    expected_units = {unit_name(cell, role) for cell in CELLS for role in SELECTION_ROLES}
    if set(completed) != expected_units:
        raise SystemExit(f"八个评价单元未全部完成：缺 {sorted(expected_units - set(completed))}")

    primary = {
        cell: completed[unit_name(cell, "entity")]["metrics"] for cell in CELLS
    }
    target_interaction = (
        primary["c11"]["entity_average_precision"] - primary["c10"]["entity_average_precision"]
        - primary["c01"]["entity_average_precision"] + primary["c00"]["entity_average_precision"]
    )
    result = {
        "schema_version": f"{SCHEMA_VERSION}-target-descriptive-evaluation-v1",
        "run_id": RUN_ID,
        "dataset": "LSPR24",
        "evaluation_role": "previously_accessed_target_year_descriptive_evaluation",
        "primary_selection_role": "entity",
        "secondary_selection_role": "flow",
        "selection_protocol_note": (
            "主口径为源年实体 AP 择优的 selected-by-entity（2026-08-28 冻结裁决）；"
            "selected-by-flow 一并评价，作协议敏感性对照，不作主口径、不参与排名"
        ),
        "cell_order": list(CELLS),
        "dr_fpr_grid": list(base.DR_FPR_GRID),
        "source_sealed": sealed,
        "source_verdict": verdict,
        "cross_cell_agreement": agreement,
        "sealed_input_transform": transform_receipt,
        "input_transform_runtime_receipt": transform.receipt(),
        "data_verification": data_receipt,
        "target_year_read": target["receipt"],
        "units": {name: completed[name] for name in sorted(completed)},
        "target_primary_verdict": {
            "c10_over_c00": primary["c10"]["entity_average_precision"] - primary["c00"]["entity_average_precision"],
            "c01_over_c00": primary["c01"]["entity_average_precision"] - primary["c00"]["entity_average_precision"],
            "c11_is_best": primary["c11"]["entity_average_precision"] >= max(
                primary[c]["entity_average_precision"] for c in ("c00", "c10", "c01")
            ),
            "interaction": target_interaction,
        },
        "selection": {
            "selection_performed": False,
            "winner": None,
            "target_used_for_selection": False,
            "reporting_rule": "四格并列描述，不排名不晋级",
        },
        "isolation": {
            "training_runs": 0,
            "optimizer_steps": 0,
            "parameter_updates": 0,
            "new_checkpoints_written": 0,
            "thresholds_modified": 0,
            "source_seals_modified": 0,
            "source_run_directories_modified": 0,
            "target_data_products_materialized": 0,
            "input_transform_refitted_on_target": False,
            "entity_memory_restored_from_checkpoint": False,
            "cvar_threshold_state_loaded": False,
            "cvar_threshold_note": (
                "机制二 ξ（CvarThresholdState）只在训练的 _ranking_phase 出现，推理期"
                "不参与前向；C01/C11 的目标年前向与 C00/C10 在这一点上没有差别，故不加载"
            ),
            "entity_ranking_enabled_per_cell": agreement["entity_ranking_enabled"],
        },
        "target_reads": target_reads,
        "resource": {"controller_wall_seconds": time.time() - run_started},
    }
    result["result_sha256"] = canonical_sha256(result)
    atomic_json(output_root / "target-results.json", result)
    atomic_json(output_root / "target-summary.json", {
        "schema_version": f"{SCHEMA_VERSION}-summary-v1",
        "run_id": RUN_ID,
        "target_reads": target_reads,
        "rows": [
            {
                "cell": cell,
                "selection_role": role,
                "source_metric": sealed[cell][
                    "source_entity_ap" if role == "entity" else "source_flow_ap"
                ],
                "target_entity_average_precision":
                    completed[unit_name(cell, role)]["metrics"]["entity_average_precision"],
                "target_flow_average_precision":
                    completed[unit_name(cell, role)]["metrics"]["flow_average_precision"],
                "target_dr_at_fpr": completed[unit_name(cell, role)]["metrics"]["dr_at_fpr"],
            }
            for cell in CELLS for role in SELECTION_ROLES
        ],
        "target_primary_verdict": result["target_primary_verdict"],
        "result_sha256": result["result_sha256"],
    })
    write_status(output_root, "complete", "complete", 0,
                 "四格双选轮 LSPR24 描述性评价完成", target_reads)
    build_manifest(output_root)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", default="runs/diagnostics")
    parser.add_argument("--target-config", default="configs/ch3-protocol-a-raw83-target-v1.json")
    parser.add_argument("--output-root", default=f"runs/diagnostics/{RUN_ID}")
    parser.add_argument("--dry-run", action="store_true",
                        help="只核验四格齐备与封印状态，不做前向；用于四格跑完前的预检")
    args = parser.parse_args()

    runs_root = Path(args.runs_root).resolve()
    output_root = Path(args.output_root).resolve()

    try:
        cell_runs, sealed, verdict = run_preflight(runs_root)
        if args.dry_run:
            atomic_json(output_root / "preflight.json", {
                "schema_version": SCHEMA_VERSION, "run_id": RUN_ID, "stage": "preflight",
                "source_sealed": sealed, "source_verdict": verdict, "target_reads": 0,
            })
            log("预检完成（--dry-run），未做目标年前向")
            return 0
        evaluate(args, cell_runs, sealed, verdict)
        log("目标年描述性评价完成")
        return 0
    except SystemExit as error:
        if error.code in (0, None):
            return 0
        print(f"评价停止：{error}", file=sys.stderr, flush=True)
        try:
            write_status(output_root, "failed", "failed", 1, str(error),
                         {"definition": "失败前未完成计数", "total": None})
        except Exception:  # noqa: BLE001  状态落盘失败不应掩盖原始错误
            pass
        return 1
    except Exception as error:  # noqa: BLE001
        traceback.print_exc()
        try:
            write_status(output_root, "failed", "failed", 1, f"{type(error).__name__}: {error}",
                         {"definition": "失败前未完成计数", "total": None})
        except Exception:  # noqa: BLE001
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
