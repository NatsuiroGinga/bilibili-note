# -*- coding: utf-8 -*-
"""从第三章原始运行制品机械生成统一指标总表。"""

import argparse
import ast
import csv
import hashlib
import json
import struct
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


FPR_BUDGETS = (
    ("fpr_0.001", "dr_fpr_0.001"),
    ("fpr_0.005", "dr_fpr_0.005"),
    ("fpr_0.01", "dr_fpr_0.01"),
    ("fpr_0.02", "dr_fpr_0.02"),
    ("fpr_0.04", "dr_fpr_0.04"),
    ("fpr_0.08", "dr_fpr_0.08"),
)

CANONICAL_COLUMNS = [
    "display_name",
    "config_type",
    "differentiable",
    "run_id",
    "selection_pool",
    "evaluation_pool",
    "selection_metric",
    "selection_score",
    "selected_epoch",
    "validation_flow_ap",
    "selected_p",
    "selection_protocol",
    "flow_ap",
    "entity_ap",
    "max_entity_ap",
    *(column for _, column in FPR_BUDGETS),
    "dr_curve_summary",
    "dr_curve_artifact",
    "model_scale",
    "parameter_count",
    "training_seconds",
    "inference_seconds",
    "evaluation_seconds",
    "total_seconds",
    "gpu_hours",
    "peak_gpu_mib",
    "peak_rss_mib",
    "time_scope",
    "evidence_level",
    "source_path",
    "pending_reason",
    "missing_reasons",
]

LSPR23_COLUMNS = [
    "display_name",
    "config_type",
    "differentiable",
    "run_id",
    "selection_pool",
    "selection_metric",
    "selection_score",
    "selected_epoch",
    "validation_flow_ap",
    "selected_p",
    "selection_protocol",
    "evidence_level",
    "source_path",
    "pending_reason",
    "missing_reasons",
    "best_flags",
]

LSPR24_COLUMNS = [
    "display_name",
    "config_type",
    "differentiable",
    "run_id",
    "evaluation_pool",
    "flow_ap",
    "entity_ap",
    "max_entity_ap",
    *(column for _, column in FPR_BUDGETS),
    "dr_curve_summary",
    "dr_curve_artifact",
    "evidence_level",
    "source_path",
    "pending_reason",
    "missing_reasons",
    "best_flags",
]

RESOURCE_COLUMNS = [
    "display_name",
    "config_type",
    "differentiable",
    "run_id",
    "model_scale",
    "parameter_count",
    "training_seconds",
    "inference_seconds",
    "evaluation_seconds",
    "total_seconds",
    "gpu_hours",
    "peak_gpu_mib",
    "peak_rss_mib",
    "time_scope",
    "evidence_level",
    "source_path",
    "pending_reason",
    "missing_reasons",
]

COLUMN_LABELS = {
    "display_name": "模型",
    "config_type": "配置类型",
    "differentiable": "可微",
    "run_id": "运行身份",
    "selection_pool": "选择池",
    "evaluation_pool": "评价池",
    "selection_metric": "选择指标",
    "selection_score": "选择分数",
    "selected_epoch": "选定轮次",
    "validation_flow_ap": "验证逐流AP",
    "selected_p": "选定幂指数",
    "selection_protocol": "选择口径",
    "flow_ap": "逐流AP",
    "entity_ap": "实体AP",
    "max_entity_ap": "最大实体AP",
    "dr_fpr_0.001": "DR@0.1%FPR",
    "dr_fpr_0.005": "DR@0.5%FPR",
    "dr_fpr_0.01": "DR@1%FPR",
    "dr_fpr_0.02": "DR@2%FPR",
    "dr_fpr_0.04": "DR@4%FPR",
    "dr_fpr_0.08": "DR@8%FPR",
    "dr_curve_summary": "完整曲线摘要",
    "dr_curve_artifact": "完整曲线制品",
    "model_scale": "模型规模",
    "parameter_count": "参数量",
    "training_seconds": "训练时间/秒",
    "inference_seconds": "纯推理时间/秒",
    "evaluation_seconds": "评价时间/秒",
    "total_seconds": "总时间/秒",
    "gpu_hours": "GPU小时",
    "peak_gpu_mib": "峰值显存/MiB",
    "peak_rss_mib": "峰值主存RSS/MiB",
    "time_scope": "时间口径",
    "evidence_level": "证据等级",
    "source_path": "原始路径",
    "pending_reason": "待补原因",
}

TABLE_TITLES = {
    "lspr23-selection": "LSPR23 源年选择表",
    "lspr24-evaluation": "LSPR24 已访问目标年描述性评价表",
    "resource": "资源开销表",
}


def _blank_result() -> dict[str, Any]:
    metadata = {
        "display_name",
        "config_type",
        "differentiable",
        "run_id",
        "evidence_level",
        "source_path",
        "pending_reason",
        "missing_reasons",
    }
    return {column: None for column in CANONICAL_COLUMNS if column not in metadata}


def _with_target_fields(result: dict[str, Any], dr_curve: dict[str, Any]) -> dict[str, Any]:
    for source_key, column in FPR_BUDGETS:
        result[column] = dr_curve.get(source_key)
    return result


def _adapt_baselines_full(doc: dict[str, Any], cell: str) -> dict[str, Any] | None:
    node: Any = doc
    for part in cell.split("."):
        node = node.get(part, {}) if isinstance(node, dict) else {}
    if not node:
        return None
    validation_score = node.get("val_ap_pred_avg")
    is_neural = node.get("npar") is not None
    result = _blank_result()
    result.update(
        {
            "selection_pool": "LSPR23实体不相交验证集" if validation_score is not None else "LSPR23固定配置训练集",
            "evaluation_pool": "LSPR24已访问目标年描述性评价池",
            "selection_metric": "前5名轮次预测平均的逐流AP" if validation_score is not None else None,
            "selection_score": validation_score,
            "selected_epoch": node.get("topk_epochs"),
            "validation_flow_ap": validation_score,
            "selection_protocol": doc.get("protocol"),
            "flow_ap": node.get("flow_ap"),
            "entity_ap": node.get("ent_ap_max"),
            "max_entity_ap": node.get("ent_ap_max"),
            "dr_curve_summary": "仅持久化4% FPR单点；无完整告警预算曲线",
            "model_scale": node.get("scale"),
            "parameter_count": node.get("npar"),
            "training_seconds": node.get("train_seconds"),
            "time_scope": "训练墙钟；未拆分目标年纯推理与指标计算" if is_neural else "固定树配置训练墙钟；未拆分目标年纯推理与指标计算",
        }
    )
    return _with_target_fields(result, {"fpr_0.04": node.get("dr_at_fpr_max")})


def _adapt_fairsel_2x2(doc: dict[str, Any], cell: str) -> dict[str, Any] | None:
    node = doc.get("cells", {}).get(cell)
    if not node:
        return None
    uses_lp = cell in {"C01", "C11"}
    result = _blank_result()
    result.update(
        {
            "selection_pool": "LSPR23实体不相交验证集",
            "evaluation_pool": "LSPR24已访问目标年描述性评价池",
            "selection_metric": "单轮逐流AP",
            "selection_score": node.get("val_ap"),
            "selected_epoch": node.get("sel_epoch"),
            "validation_flow_ap": node.get("val_ap"),
            "selected_p": node.get("p"),
            "selection_protocol": doc.get("protocol"),
            "flow_ap": node.get("fap"),
            "entity_ap": node.get("e_lp") if uses_lp else node.get("e_max"),
            "max_entity_ap": node.get("e_max"),
            "dr_curve_summary": "仅持久化4% FPR单点；无完整告警预算曲线",
            "model_scale": f"{node.get('npar'):,}个可训练参数" if isinstance(node.get("npar"), int) else None,
            "parameter_count": node.get("npar"),
            "training_seconds": node.get("tr"),
            "evaluation_seconds": node.get("ev"),
            "time_scope": "单格训练墙钟；评价时间含预测与指标计算，不等同纯推理",
        }
    )
    return _with_target_fields(result, {"fpr_0.04": node.get("dr_main")})


def _adapt_protocol_a_v1(doc: dict[str, Any], cell: str) -> dict[str, Any] | None:
    selection = doc.get("source_selection", {}).get("cells", {}).get(cell, {})
    target = doc.get("target_evaluation", {}).get("cells", {}).get(cell, {}).get("target", {})
    resource = doc.get("resource", {})
    if not target:
        return None
    parameter_count = resource.get("parameter_count") or doc.get("model", {}).get("parameter_count")
    result = _blank_result()
    result.update(
        {
            "selection_pool": "LSPR23实体不相交验证集",
            "evaluation_pool": "LSPR24已访问目标年描述性评价池",
            "selection_metric": "单轮逐流AP",
            "selection_score": selection.get("validation_flow_ap"),
            "selected_epoch": selection.get("selected_epoch"),
            "validation_flow_ap": selection.get("validation_flow_ap"),
            "selected_p": selection.get("p_at_selection"),
            "selection_protocol": doc.get("source_selection", {}).get("protocol") or "协议A：源年验证集单轮逐流AP择优",
            "flow_ap": target.get("flow_average_precision"),
            "entity_ap": target.get("entity_average_precision"),
            "max_entity_ap": target.get("maximum_entity_average_precision"),
            "model_scale": f"{parameter_count:,}个可训练参数" if isinstance(parameter_count, int) else None,
            "parameter_count": parameter_count,
            "training_seconds": resource.get("training_wall_seconds_sum"),
            "evaluation_seconds": resource.get("evaluation_wall_seconds_sum"),
            "gpu_hours": resource.get("gpu_hours"),
            "peak_gpu_mib": resource.get("peak_gpu_allocated_mib"),
            "peak_rss_mib": resource.get("peak_process_rss_mib"),
            "time_scope": "四格训练与评价墙钟之和；评价时间含预测与指标计算，不等同纯推理",
        }
    )
    return _with_target_fields(result, dict(target.get("dr_at_fpr", {})))


def _adapt_xgb_cpa_elp(doc: dict[str, Any], cell: str) -> dict[str, Any] | None:
    node = doc.get("cells", {}).get(cell)
    if not node:
        return None
    input_view = node.get("input_view")
    p_selection = doc.get("p_selection", {}).get(input_view, {})
    result = _blank_result()
    result.update(
        {
            "selection_pool": "LSPR23三折实体OOF",
            "evaluation_pool": "LSPR24已访问目标年描述性评价池",
            "selection_metric": "实体OOF AP",
            "selection_score": p_selection.get("oof_ent_ap_at_p"),
            "selected_p": node.get("p"),
            "selection_protocol": doc.get("adapter_selection", {}).get("criterion"),
            "flow_ap": node.get("flow_ap"),
            "entity_ap": node.get("ent_ap"),
            "max_entity_ap": node.get("ent_ap") if node.get("p") is None else None,
            "dr_curve_summary": "持久化六个预设FPR工作点；无全可达预算曲线制品",
            "model_scale": f"{doc.get('num_boost_round')}棵提升树" if doc.get("num_boost_round") is not None else None,
            "total_seconds": doc.get("timing", {}).get("total_seconds"),
            "time_scope": "源年拟合与目标年评价总墙钟；未拆分训练、纯推理和指标计算",
        }
    )
    return _with_target_fields(result, dict(node.get("dr_curve", {})))


ADAPTERS: dict[str, Callable[[dict[str, Any], str], dict[str, Any] | None]] = {
    "baselines_full": _adapt_baselines_full,
    "fairsel_2x2": _adapt_fairsel_2x2,
    "protocol_a_v1": _adapt_protocol_a_v1,
    "xgb_cpa_elp": _adapt_xgb_cpa_elp,
}


def read_source(root_path: str, model_entry: dict[str, Any]) -> dict[str, Any] | None:
    """读取单个JSON来源，并用配置指定的模式适配为统一字段。"""
    relative_path = model_entry.get("relative_path")
    adapter = ADAPTERS.get(model_entry.get("source_schema"))
    cell = model_entry.get("cell")
    if not relative_path or adapter is None or cell is None:
        return None
    source_path = Path(root_path) / relative_path
    if source_path.suffix != ".json" or not source_path.is_file():
        return None
    try:
        document = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return adapter(document, cell) if isinstance(document, dict) else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_provenance(path: Path, role: str, records: dict[str, dict[str, Any]]) -> None:
    absolute = path.resolve()
    key = str(absolute)
    if key not in records:
        records[key] = {
            "absolute_path": key,
            "sha256": _sha256(absolute),
            "bytes": absolute.stat().st_size,
            "read_at_utc": datetime.now(timezone.utc).isoformat(),
            "roles": [],
        }
    if role not in records[key]["roles"]:
        records[key]["roles"].append(role)


def _load_auxiliary_json(path: Path) -> dict[str, Any] | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return document if isinstance(document, dict) else None


def _npy_shape(handle: Any) -> tuple[int, ...]:
    if handle.read(6) != b"\x93NUMPY":
        raise ValueError("NPZ成员不是NPY数组")
    major, _minor = struct.unpack("BB", handle.read(2))
    length_size = 2 if major == 1 else 4
    length_format = "<H" if length_size == 2 else "<I"
    header_length = struct.unpack(length_format, handle.read(length_size))[0]
    header = ast.literal_eval(handle.read(header_length).decode("latin1").strip())
    shape = header.get("shape")
    if not isinstance(shape, tuple):
        raise ValueError("NPY头缺少shape")
    return shape


def _npz_shapes(path: Path, prefix: str) -> dict[str, tuple[int, ...]]:
    shapes: dict[str, tuple[int, ...]] = {}
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.startswith(prefix) and name.endswith(".npy"):
                with archive.open(name) as handle:
                    shapes[name[:-4]] = _npy_shape(handle)
    return shapes


def _enrich_neural_resource(
    result: dict[str, Any],
    root: Path,
    entry: dict[str, Any],
    provenance: dict[str, dict[str, Any]],
) -> None:
    relative = entry.get("selection_relative_path")
    if not relative:
        return
    path = root / relative
    if not path.is_file():
        return
    _record_provenance(path, f"{entry['display_name']}的选择与显存收据", provenance)
    document = _load_auxiliary_json(path)
    if document is None:
        return
    model_key = str(entry.get("cell", "")).split(".")[-1]
    architecture = document.get("architectures", {}).get(model_key, {})
    chosen_lr = architecture.get("chosen_lr")
    candidate = next(
        (item for item in architecture.get("candidates", []) if item.get("lr") == chosen_lr),
        None,
    )
    if candidate and candidate.get("peak_gib") is not None:
        result["peak_gpu_mib"] = candidate["peak_gib"] * 1024.0


def _enrich_complete_curve(
    result: dict[str, Any],
    root: Path,
    entry: dict[str, Any],
    provenance: dict[str, dict[str, Any]],
) -> None:
    receipt_relative = entry.get("curve_receipt_relative_path")
    artifact_relative = entry.get("curve_artifact_relative_path")
    if not receipt_relative or not artifact_relative:
        return
    receipt_path = root / receipt_relative
    artifact_path = root / artifact_relative
    if not receipt_path.is_file() or not artifact_path.is_file():
        return
    _record_provenance(receipt_path, f"{entry['display_name']}的完整曲线收据", provenance)
    _record_provenance(artifact_path, f"{entry['display_name']}的完整曲线NPZ", provenance)
    receipt = _load_auxiliary_json(receipt_path)
    if receipt is None:
        return
    declared = receipt.get("artifact", {})
    actual_hash = provenance[str(artifact_path.resolve())]["sha256"]
    if declared.get("sha256") and declared["sha256"] != actual_hash:
        raise ValueError(f"完整曲线制品哈希与收据不符：{artifact_path}")
    if declared.get("bytes") and declared["bytes"] != artifact_path.stat().st_size:
        raise ValueError(f"完整曲线制品字节数与收据不符：{artifact_path}")
    cell = str(entry.get("cell"))
    shapes = _npz_shapes(artifact_path, f"{cell}__")
    point_counts = {shape[0] for shape in shapes.values() if shape}
    fields = receipt.get("fields", [])
    complete = receipt.get("curve_is_complete_over_all_reachable_negative_entity_budgets") is True
    if len(shapes) == len(fields) and len(point_counts) == 1 and complete:
        point_count = next(iter(point_counts))
        result["dr_curve_summary"] = (
            f"完整可达负实体预算曲线，共{point_count}个预算点；字段："
            + "、".join(str(field) for field in fields)
        )
        result["dr_curve_artifact"] = f"{artifact_path.resolve()}#{cell}"


def _default_missing_reason(column: str, row: dict[str, Any]) -> str:
    if row.get("pending_reason"):
        return str(row["pending_reason"])
    reasons = {
        "selected_epoch": "该来源没有单轮检查点选择，或未持久化选定轮次",
        "validation_flow_ap": "该来源未持久化可比较的源年验证逐流AP",
        "selected_p": "该模型或选择规则不使用幂平均指数",
        "selection_protocol": "原始来源未持久化选择协议说明",
        "selection_score": "固定配置直接训练，或原始制品未持久化选择分数",
        "selection_metric": "固定配置直接训练，不执行开发集择优",
        "parameter_count": "树集成不适用神经网络可训练参数量，规模见模型规模列",
        "inference_seconds": "所有现有来源均未单独持久化纯模型推理墙钟",
        "evaluation_seconds": "原始来源未拆分目标年评价墙钟",
        "training_seconds": "原始来源未拆分训练墙钟",
        "total_seconds": "原始来源未持久化端到端总墙钟",
        "gpu_hours": "原始来源未持久化GPU小时",
        "peak_gpu_mib": "原始来源未持久化峰值显存",
        "peak_rss_mib": "原始来源未持久化峰值进程RSS",
        "max_entity_ap": "原始来源未单独持久化最大池化实体AP",
        "dr_curve_summary": "原始来源未持久化完整曲线或曲线摘要",
        "dr_curve_artifact": "原始来源未持久化完整告警预算曲线制品",
        "model_scale": "原始来源未持久化模型规模描述",
        "time_scope": "原始来源未持久化时间统计口径",
    }
    if column.startswith("dr_fpr_"):
        return "原始来源未持久化该FPR工作点"
    return reasons.get(column, "原始来源未持久化该字段")


def _fill_missing_reasons(row: dict[str, Any]) -> None:
    fields = {
        "selection_metric",
        "selection_score",
        "selected_epoch",
        "validation_flow_ap",
        "selected_p",
        "selection_protocol",
        "flow_ap",
        "entity_ap",
        "max_entity_ap",
        *(column for _, column in FPR_BUDGETS),
        "dr_curve_summary",
        "dr_curve_artifact",
        "model_scale",
        "parameter_count",
        "training_seconds",
        "inference_seconds",
        "evaluation_seconds",
        "total_seconds",
        "gpu_hours",
        "peak_gpu_mib",
        "peak_rss_mib",
        "time_scope",
    }
    row["missing_reasons"] = {
        column: _default_missing_reason(column, row)
        for column in sorted(fields)
        if row.get(column) is None
    }


def _parse_root_args(root_args: list[str]) -> dict[str, str]:
    roots: dict[str, str] = {}
    for item in root_args:
        if "=" not in item:
            raise ValueError(f"--root参数必须为name=path，收到：{item}")
        name, path = item.split("=", 1)
        if not name or not path:
            raise ValueError(f"--root参数必须同时含名称和路径，收到：{item}")
        roots[name] = str(Path(path).resolve())
    return roots


def collect_rows(
    config_path: str,
    roots: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """读取全部配置项，返回统一行及去重后的来源溯源。"""
    config_file = Path(config_path)
    config = json.loads(config_file.read_text(encoding="utf-8"))
    if config.get("schema_version") != "ch3-metrics-table-sources-v1":
        raise ValueError("来源配置schema_version不受支持")
    provenance_records: dict[str, dict[str, Any]] = {}
    _record_provenance(config_file, "来源配置", provenance_records)
    rows: list[dict[str, Any]] = []
    for entry in config.get("models", []):
        root_name = entry.get("root")
        root_value = roots.get(root_name)
        relative_path = entry.get("relative_path")
        source_path = Path(root_value) / relative_path if root_value and relative_path else None
        row = _blank_result()
        row.update(
            {
                "display_name": entry.get("display_name"),
                "config_type": entry.get("config_type"),
                "differentiable": entry.get("differentiable"),
                "run_id": entry.get("run_id"),
                "selection_pool": None,
                "evaluation_pool": None,
                "evidence_level": entry.get("evidence_level"),
                "source_path": str(source_path.resolve()) if source_path else None,
                "pending_reason": entry.get("pending_reason"),
            }
        )
        if source_path and source_path.is_file():
            _record_provenance(source_path, f"{entry['display_name']}的主结果", provenance_records)
            normalized = read_source(str(Path(root_value)), entry)
            if normalized is None:
                row["pending_reason"] = "主结果存在，但JSON或目标模式/单元不可解析"
            else:
                row.update(normalized)
                row["pending_reason"] = None
                root = Path(root_value)
                _enrich_neural_resource(row, root, entry, provenance_records)
                _enrich_complete_curve(row, root, entry, provenance_records)
        elif entry.get("available"):
            row["pending_reason"] = "配置标记为可用，但指定本地原始制品不存在"
        elif not row.get("pending_reason"):
            row["pending_reason"] = "尚无本地原始制品"
        _fill_missing_reasons(row)
        rows.append(row)
    provenance = {
        "schema_version": "ch3-metrics-table-provenance-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_file.resolve()),
        "roots": roots,
        "source_file_count": len(provenance_records),
        "sha256_count": len(provenance_records),
        "files": sorted(provenance_records.values(), key=lambda item: item["absolute_path"]),
    }
    return rows, provenance


def _project_row(row: dict[str, Any], columns: list[str]) -> dict[str, Any]:
    projected = {column: row.get(column) for column in columns}
    if "missing_reasons" in projected:
        projected["missing_reasons"] = {
            column: reason
            for column, reason in row.get("missing_reasons", {}).items()
            if column in columns
        }
    return projected


def mark_best(
    table: list[dict[str, Any]],
    columns: list[str],
    group_columns: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    """在同一评价池中按全精度标记最大值；单行组不标最强。"""
    for row in table:
        row["best_flags"] = {}
    for column in columns:
        groups: dict[tuple[Any, ...], list[tuple[int, float]]] = {}
        for index, row in enumerate(table):
            value = row.get(column)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            group = tuple(row.get(key) for key in group_columns)
            if any(part is None for part in group):
                continue
            groups.setdefault(group, []).append((index, float(value)))
        for values in groups.values():
            if len(values) < 2:
                continue
            top = max(value for _, value in values)
            winners = [index for index, value in values if value == top]
            flag = "best" if len(winners) == 1 else "tied_best"
            for index in winners:
                table[index]["best_flags"][column] = flag
    return table


def build_tables(rows: list[dict[str, Any]]) -> dict[str, tuple[list[dict[str, Any]], list[str]]]:
    """把统一行投影为年度与资源互不混排的三张表。"""
    source_table = [_project_row(row, LSPR23_COLUMNS) for row in rows]
    target_table = [_project_row(row, LSPR24_COLUMNS) for row in rows]
    resource_table = [_project_row(row, RESOURCE_COLUMNS) for row in rows]
    mark_best(source_table, ["selection_score"], ("selection_pool", "selection_metric"))
    mark_best(
        target_table,
        ["flow_ap", "entity_ap", "max_entity_ap", *(column for _, column in FPR_BUDGETS)],
        ("evaluation_pool",),
    )
    return {
        "lspr23-selection": (source_table, LSPR23_COLUMNS),
        "lspr24-evaluation": (target_table, LSPR24_COLUMNS),
        "resource": (resource_table, RESOURCE_COLUMNS),
    }


def _serialize_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return format(value, ".15g")
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value)


def _markdown_cell(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, float):
        return format(value, ".12g")
    if isinstance(value, list):
        return "、".join(str(item) for item in value)
    return str(value).replace("|", "\\|").replace("\n", " ")


def _render_markdown(name: str, rows: list[dict[str, Any]], columns: list[str]) -> str:
    visible = [column for column in columns if column not in {"missing_reasons", "best_flags"}]
    lines = [
        f"# {TABLE_TITLES[name]}",
        "",
        "本表由原始运行制品机械生成；粗体表示同一评价池、同一指标的全精度最强值。",
        "",
    ]
    lines.append("| " + " | ".join(COLUMN_LABELS.get(column, column) for column in visible) + " |")
    lines.append("| " + " | ".join("---" for _ in visible) + " |")
    for row in rows:
        cells = []
        for column in visible:
            value = _markdown_cell(row.get(column))
            if row.get("best_flags", {}).get(column):
                value = f"**{value}**"
            cells.append(value)
        lines.append("| " + " | ".join(cells) + " |")
    lines.extend(["", "## 缺失值说明", ""])
    for row in rows:
        reasons = row.get("missing_reasons", {})
        if not reasons:
            continue
        details = "；".join(f"{COLUMN_LABELS.get(column, column)}：{reason}" for column, reason in reasons.items())
        lines.append(f"- {row['display_name']}：{details}。")
    lines.extend(
        [
            "",
            "## 评价口径",
            "",
            "- LSPR23 表只记录源年选择证据；LSPR24 表只记录已访问目标年的描述性评价，二者不混排。",
            "- 实体 AP 为各运行预先注册的主聚合口径；最大实体 AP 单列，缺失时不反推。",
            "- 评价时间含预测与指标计算时会在时间口径列明示，不能替代纯模型推理时间。",
            "- 资源表不判最强；树集成使用树数、节点数或深度描述规模，不机械折算神经网络参数量。",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    tables: dict[str, tuple[list[dict[str, Any]], list[str]]],
    out_dir: str,
    provenance: dict[str, Any],
) -> list[str]:
    """以JSON、CSV、Markdown写出三表，并落盘唯一溯源清单。"""
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name, (rows, columns) in tables.items():
        json_path = output / f"{name}.json"
        csv_path = output / f"{name}.csv"
        markdown_path = output / f"{name}.md"
        json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=columns,
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writeheader()
            for row in rows:
                writer.writerow({column: _serialize_cell(row.get(column)) for column in columns})
        markdown_path.write_text(_render_markdown(name, rows, columns), encoding="utf-8")
        written.extend(str(path) for path in (json_path, csv_path, markdown_path))
    provenance_path = output / "provenance.json"
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    written.append(str(provenance_path))
    return written


def _run_probe(config_path: str, root_args: list[str]) -> None:
    rows, provenance = collect_rows(config_path, _parse_root_args(root_args))
    for row in rows:
        print(
            f"{row['display_name']}\tflow_ap={row.get('flow_ap')}\t"
            f"entity_ap={row.get('entity_ap')}\tpending_reason={row.get('pending_reason')}"
        )
    print(f"来源文件={provenance['source_file_count']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="第三章全模型统一指标总表构建工具")
    parser.add_argument("--probe", action="store_true", help="只读探测每个来源，不写总表")
    parser.add_argument("--config", required=True, help="来源配置JSON路径")
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        metavar="name=path",
        help="运行根映射，可重复传入",
    )
    parser.add_argument("--out", help="十个总表与溯源产物的输出目录")
    args = parser.parse_args()
    if args.probe:
        _run_probe(args.config, args.root)
        return
    if not args.out:
        parser.error("完整生成需要--out")
    roots = _parse_root_args(args.root)
    rows, provenance = collect_rows(args.config, roots)
    written = write_outputs(build_tables(rows), args.out, provenance)
    available = sum(row.get("pending_reason") is None for row in rows)
    pending = [row for row in rows if row.get("pending_reason")]
    print(f"模型总数={len(rows)} 可用={available} pending={len(pending)} 来源文件={provenance['source_file_count']}")
    for row in pending:
        print(f"pending\t{row['display_name']}\t{row['pending_reason']}")
    for path in written:
        print(f"写出\t{path}")


if __name__ == "__main__":
    main()
