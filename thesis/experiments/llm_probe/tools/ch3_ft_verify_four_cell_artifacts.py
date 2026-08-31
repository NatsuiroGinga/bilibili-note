#!/usr/bin/env python3
"""CEM-BER 四格制品完整性与可复核性核验。

对应第三章 Goal 的「配置、模型、日志、状态、哈希、清单和恢复制品完整可复核」一项。
只读：不修改任何制品，不连服务器，不需要 GPU。

核验四类事实：
1. 必需文件是否齐全（配置、身份收据、选轮收据、两份选轮检查点、封印变换）；
2. 检查点能否真正加载，其中的 schema、运行身份、选中轮次是否与选轮收据自洽；
3. 参数量是否与配置声明一致；
4. 逐格记录关键文件的 SHA-256，供跨机器比对。

未完成的臂按缺失如实报告，不阻断——它只是尚未产生制品，不是核验失败。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

CELLS: List[Dict[str, Any]] = [
    {"cell": "C00", "run_id": "ch3-ft-c00-dual-selection-cuda-formal-v1", "display": "裸 FT"},
    {"cell": "C10", "run_id": "ch3-ft-c10-entity-memory-cuda-formal-v1", "display": "＋因果实体记忆"},
    {"cell": "C01", "run_id": "ch3-ft-c01-entity-ranking-cuda-formal-v1", "display": "＋预算感知实体排序"},
    {"cell": "C11", "run_id": "ch3-ft-c11-cem-ber-cuda-formal-v1", "display": "因果状态共享"},
]

# 一个完成的臂必须具备的制品。缺任一项即该臂不可复核。
REQUIRED = [
    "config.json",
    "status.json",
    "science-identity.json",
    "runtime-identity.json",
    "environment-receipt.json",
    "receipts/selection.json",
    "receipts/split.json",
    "receipts/input-transform.json",
    "artifacts/sealed-input-transform.pkl",
    "checkpoints/selected-by-entity.pt",
    "checkpoints/selected-by-flow.pt",
]

# 只对小文件算摘要：检查点最大 810 MiB，逐个哈希会让核验从秒级变成分钟级，
# 而检查点的自洽性已由下面的加载与字段比对覆盖。
HASH_TARGETS = ["config.json", "receipts/selection.json", "science-identity.json"]


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def verify_checkpoints(run_dir: Path, selection: Dict[str, Any], torch_module: Any) -> Dict[str, Any]:
    """加载两份选轮检查点，核对 schema、运行身份、选中轮次与参数量。"""
    outcome: Dict[str, Any] = {"loadable": {}, "consistent": {}, "parameter_count": {}}
    for role, receipt_key in (("entity", "best_by_entity"), ("flow", "best_by_flow")):
        path = run_dir / "checkpoints" / f"selected-by-{role}.pt"
        if not path.is_file():
            outcome["loadable"][role] = False
            continue
        try:
            # weights_only=False：载荷含身份字典等非张量对象，与训练侧一致。
            payload = torch_module.load(path, map_location="cpu", weights_only=False)
        except Exception as error:  # noqa: BLE001 — 核验阶段需报告任何加载失败
            outcome["loadable"][role] = False
            outcome.setdefault("errors", []).append(f"{role}: {type(error).__name__}: {error}")
            continue
        outcome["loadable"][role] = True
        expected_epoch = (selection.get(receipt_key) or {}).get("epoch")
        expected_metric = (selection.get(receipt_key) or {}).get("metric")
        outcome["consistent"][role] = {
            "schema_version": payload.get("schema_version"),
            "run_id_matches": payload.get("run_id") == selection.get("run_id"),
            "selection_role": payload.get("selection_role"),
            "selected_epoch": payload.get("selected_epoch"),
            "epoch_matches_receipt": payload.get("selected_epoch") == expected_epoch,
            "metric_matches_receipt": payload.get("selected_metric") == expected_metric,
        }
        state = payload.get("model_state_dict") or {}
        # state_dict 同时含可训练参数与 buffer，其元素总数天然大于配置里的
        # expected_parameter_count（后者只计可训练参数）。C00 实测两者差 2，
        # 来自 2 个标量 buffer。两个口径不同，不能直接相等比对，
        # 故只记录数值与差值，由下面的容差判定，不把口径差当成制品缺陷。
        outcome["parameter_count"][role] = int(sum(t.numel() for t in state.values()))
        outcome.setdefault("state_dict_entries", {})[role] = len(state)
    return outcome


def verify_cell(runs_root: Path, spec: Dict[str, Any], torch_module: Any) -> Dict[str, Any]:
    run_dir = runs_root / spec["run_id"]
    record: Dict[str, Any] = {
        "cell": spec["cell"],
        "display_name": spec["display"],
        "run_id": spec["run_id"],
        "run_dir_exists": run_dir.is_dir(),
        "missing_files": [],
        "hashes": {},
        "verdict": "未完成",
    }
    if not run_dir.is_dir():
        record["missing_files"] = list(REQUIRED)
        return record

    record["missing_files"] = [name for name in REQUIRED if not (run_dir / name).is_file()]

    status = read_json(run_dir / "status.json") or {}
    record["state"] = status.get("state")
    record["exit_code"] = status.get("exit_code")
    record["target_reads"] = status.get("target_reads")

    selection = read_json(run_dir / "receipts" / "selection.json")
    if selection is None:
        record["verdict"] = "未完成：无选轮收据"
        return record

    config = read_json(run_dir / "config.json") or {}
    declared = (config.get("model") or {}).get("expected_parameter_count")
    record["declared_parameter_count"] = declared

    for name in HASH_TARGETS:
        path = run_dir / name
        if path.is_file():
            record["hashes"][name] = sha256_file(path)

    if torch_module is not None:
        checks = verify_checkpoints(run_dir, selection, torch_module)
        record["checkpoints"] = checks
        counts = set(checks.get("parameter_count", {}).values())
        # 两份选轮检查点必须给出同一个总数（同一模型结构），这是硬条件；
        # 与配置声明的差值只作记录，容差 16 个元素覆盖少量标量 buffer。
        record["two_checkpoints_agree"] = len(counts) == 1
        if counts and declared is not None:
            delta = next(iter(counts)) - int(declared)
            record["state_dict_minus_declared"] = delta
            record["parameter_count_within_tolerance"] = 0 <= delta <= 16
        else:
            record["state_dict_minus_declared"] = None
            record["parameter_count_within_tolerance"] = None
    else:
        record["checkpoints"] = {"skipped": "torch 不可用，跳过检查点加载"}
        record["parameter_count_matches_config"] = None

    complete = (
        not record["missing_files"]
        and record.get("state") == "finished"
        and record.get("exit_code") == 0
        and int(record.get("target_reads", -1)) == 0
    )
    if complete and torch_module is not None:
        checks = record["checkpoints"]
        loadable = all(checks.get("loadable", {}).get(r) for r in ("entity", "flow"))
        consistent = all(
            info.get("run_id_matches") and info.get("epoch_matches_receipt")
            and info.get("metric_matches_receipt")
            for info in checks.get("consistent", {}).values()
        )
        if loadable and consistent and record["two_checkpoints_agree"] and record["parameter_count_within_tolerance"]:
            record["verdict"] = "可复核"
        else:
            reasons = []
            if not loadable:
                reasons.append("检查点无法加载")
            if not consistent:
                reasons.append("身份或选中轮次与收据不符")
            if not record["two_checkpoints_agree"]:
                reasons.append("两份检查点参数量不一致")
            if not record["parameter_count_within_tolerance"]:
                reasons.append(f"参数量与配置差 {record['state_dict_minus_declared']} 超出容差")
            record["verdict"] = "不可复核：" + "；".join(reasons)
    elif complete:
        record["verdict"] = "文件齐全，检查点未验证"
    return record


# 四格比较有效的前提：除机制开关外，一切科学设定必须逐字相同。
# 任何一项漂移都会让「差值归因于机制」不成立，因此这里逐项断言而非抽查。
CONTROLLED_FIELDS: List[tuple] = [
    ("base", "config_sha256"), ("base", "tool_sha256"),
    ("training", "seed"), ("training", "effective_batch_size"),
    ("training", "micro_batch_sequences"), ("training", "gradient_accumulation_steps"),
    ("training", "sequence_length"), ("training", "normalization_unit"),
    ("training", "tie_rule"), ("training", "selection_metrics"),
    ("budget", "epochs"), ("budget", "steps_per_epoch"), ("budget", "validation_every_epochs"),
    ("runtime", "precision_profile_id"), ("runtime", "device_type"),
    ("evaluation", "entity_aggregation"), ("evaluation", "flow_metric"),
    ("evaluation", "entity_metric"),
    ("data", "target_reads"), ("evaluation", "target_reads"),
]

# 期望的 2×2 正交开关。z1 为因果实体记忆，z2 为预算感知实体排序。
EXPECTED_SWITCHES = {
    "C00": (False, False), "C10": (True, False),
    "C01": (False, True), "C11": (True, True),
}


def verify_config_parity(configs_root: Path) -> Dict[str, Any]:
    """核验四格配置的科学一致性与开关正交性。

    与制品核验分开：制品缺失只说明该臂没跑完，而配置漂移会让**已跑完的**臂
    之间不可比——后者更隐蔽，且四格齐备后才发现就意味着全部重跑。
    """
    result: Dict[str, Any] = {"config_files_found": {}, "mismatched_fields": [],
                              "switch_matrix": {}, "switch_matrix_correct": None,
                              "parameter_counts": {}, "verdict": "未核验"}
    loaded: Dict[str, Dict[str, Any]] = {}
    for spec in CELLS:
        cell = spec["cell"]
        path = configs_root / f"{spec['run_id'].replace('ch3-ft-', 'ch3-ft-')}.json"
        result["config_files_found"][cell] = path.is_file()
        if path.is_file():
            try:
                loaded[cell] = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as error:
                result["mismatched_fields"].append(f"{cell} 配置无法解析：{error}")
    if len(loaded) < 2:
        result["verdict"] = "配置不足，无法比较"
        return result

    for section, key in CONTROLLED_FIELDS:
        values = {c: json.dumps(d.get(section, {}).get(key), ensure_ascii=False, sort_keys=True)
                  for c, d in loaded.items()}
        if len(set(values.values())) > 1:
            result["mismatched_fields"].append({f"{section}.{key}": values})

    switches_ok = True
    for cell, doc in loaded.items():
        mech = doc.get("mechanism", {})
        z1 = bool(mech.get("entity_memory", {}).get("enabled", False))
        z2 = bool(mech.get("entity_ranking", {}).get("enabled", False))
        result["switch_matrix"][cell] = {"z1": z1, "z2": z2}
        result["parameter_counts"][cell] = doc.get("model", {}).get("expected_parameter_count")
        if cell in EXPECTED_SWITCHES and (z1, z2) != EXPECTED_SWITCHES[cell]:
            switches_ok = False
    result["switch_matrix_correct"] = switches_ok
    result["controlled_field_count"] = len(CONTROLLED_FIELDS)
    result["verdict"] = (
        "一致" if not result["mismatched_fields"] and switches_ok else "存在漂移"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="CEM-BER 四格制品完整性核验（只读）")
    parser.add_argument("--runs-root", required=True, help="诊断运行根目录")
    parser.add_argument("--configs-root", default=None,
                        help="四格配置目录；给出时额外核验配置一致性与开关正交性")
    parser.add_argument("--output", default=None, help="核验收据落盘路径")
    args = parser.parse_args()

    runs_root = Path(args.runs_root).expanduser().resolve()
    if not runs_root.is_dir():
        print(f"[错误] 运行根目录不存在：{runs_root}", file=sys.stderr)
        return 2

    try:
        import torch as torch_module
    except ImportError:
        torch_module = None
        print("[警告] 未找到 torch，跳过检查点加载核验", file=sys.stderr)

    cells = [verify_cell(runs_root, spec, torch_module) for spec in CELLS]
    report = {
        "schema_version": "ch3-ft-four-cell-artifact-verification-v1",
        "runs_root": str(runs_root),
        "torch_available": torch_module is not None,
        "cells": cells,
    }
    if args.configs_root:
        report["config_parity"] = verify_config_parity(Path(args.configs_root).expanduser().resolve())

    output = Path(args.output) if args.output else runs_root / "ch3-ft-four-cell-artifact-verification.json"
    staging = output.with_suffix(output.suffix + ".partial")
    with staging.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    staging.replace(output)

    for item in cells:
        missing = f"，缺 {len(item['missing_files'])} 项" if item["missing_files"] else ""
        print(f"{item['cell']} {item['display_name']}：{item['verdict']}{missing}", file=sys.stderr)
    parity = report.get("config_parity")
    if parity:
        print(
            f"配置一致性：{parity['verdict']}"
            f"（受控字段 {parity.get('controlled_field_count', '?')} 项，"
            f"漂移 {len(parity['mismatched_fields'])} 项，"
            f"开关矩阵正交={parity['switch_matrix_correct']}）",
            file=sys.stderr,
        )
    print(f"核验收据已写入 {output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
