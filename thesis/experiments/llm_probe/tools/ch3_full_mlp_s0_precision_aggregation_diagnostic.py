# -*- coding: utf-8 -*-
"""全容量多层感知机 S0 双精度×双聚合空间零训练诊断。

本入口只读复用已封印的 ``B00/B10/O01/O11`` 选中检查点，对同一份权重执行
BF16 与 FP32 两条推理路径，并在概率空间与对数几率空间两种无参数聚合下重算
实体决策。它不训练、不更新任何参数、不写新检查点，也不改动任何冻结机制。

四个候选臂（候选文档第四节）：

* ``S0-PB`` BF16 推理 + 概率空间算术均值；
* ``S0-LB`` BF16 推理 + 对数几率空间算术均值；
* ``S0-PF`` FP32 推理 + 概率空间算术均值；
* ``S0-LF`` FP32 推理 + 对数几率空间算术均值。

同一精度的前向只执行一次，全部聚合分支共享同一份预 sigmoid 对数几率；聚合算术
统一在 ``float64`` 完成，唯一变化的是对数几率本身。

顶层只导入标准库：``numpy``、``torch``、``swanlab`` 与本仓库既有模块全部延迟到函数
内部导入，使 ``--validate-config`` 在缺少数值依赖的开发机上仍然可以退出 0。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

TOOL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOL_DIR.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

SCHEMA_VERSION = "ch3-full-mlp-s0-precision-aggregation-diagnostic-config-v1"
RESULT_SCHEMA_VERSION = "ch3-full-mlp-s0-precision-aggregation-diagnostic-results-v1"
UNIT_SCHEMA_VERSION = "ch3-full-mlp-s0-unit-aggregate-v1"
CURVE_SCHEMA_VERSION = "ch3-full-mlp-s0-complete-tied-budget-curves-v1"
SEAL_SCHEMA_VERSION = "ch3-full-mlp-s0-source-seal-v1"
MANIFEST_SCHEMA_VERSION = "ch3-full-mlp-s0-precision-aggregation-diagnostic-manifest-v1"

RUN_ID = "ch3-full-mlp-s0-precision-aggregation-diagnostic-seed42-v1"
DISPLAY_NAME = "全容量多层感知机S0双精度双聚合空间零训练诊断"
PARENT_RUN_ID = "ch3-full-mlp-complete-entity-lp-protocol-a-q0-seed42-v1-bf16-v1"
CELL_ORDER = ("B00", "B10", "O01", "O11")
PRECISION_ORDER = ("bf16", "fp32")
STAGES = ("source", "seal", "target", "finalize")

EXIT_OK = 0
EXIT_UNEXPECTED = 1
EXIT_CONFIG = 2
EXIT_INPUT = 3
EXIT_DEPENDENCY = 4
EXIT_STAGE_PRECONDITION = 5
EXIT_RETRYABLE_SWANLAB_INIT_401 = 91

FORBIDDEN_ARTIFACT_TOKENS = (
    "per-flow",
    "per_flow",
    "flow-score",
    "flow_score",
    "entity-score",
    "entity_score",
    "per-entity",
    "per_entity",
    "exposure-matrix",
    "exposure_matrix",
    "entity-mapping",
    "entity_mapping",
    ".pt",
    ".pth",
    ".ckpt",
)

T0 = time.time()
_LAST_BEAT = 0.0


class StageError(RuntimeError):
    """携带退出码的可操作中文错误。"""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def beat(stage: str, done: int, total: int, started: float, every: float = 30.0) -> None:
    """限频心跳：输出已处理量、总量、吞吐与可计算的剩余时间。"""

    global _LAST_BEAT
    now = time.time()
    if now - _LAST_BEAT < every and done < total:
        return
    _LAST_BEAT = now
    elapsed = max(now - started, 1e-9)
    rate = done / elapsed
    remaining = (total - done) / rate if rate > 0 else float("nan")
    log(f"{stage} 进度={done}/{total} 吞吐={rate:.1f}/秒 已用={elapsed:.1f}秒 预计剩余={remaining:.1f}秒")


# --------------------------------------------------------------------------------------
# 依赖与既有模块的延迟导入
# --------------------------------------------------------------------------------------


def require_numpy() -> Any:
    try:
        import numpy as np
    except ModuleNotFoundError as error:
        raise StageError(
            "缺少 numpy：本阶段需要数值依赖。请在服务器项目根执行 "
            "`source tools/env/activate.sh` 后使用 `uv run --no-sync python` 运行；"
            "开发机只支持 `--validate-config` 与纯 JSON 阶段。",
            EXIT_DEPENDENCY,
        ) from error
    return np


def require_metrics() -> Any:
    try:
        from sklearn.metrics import average_precision_score
    except ModuleNotFoundError as error:
        raise StageError(
            "缺少 scikit-learn：平均精度指标不可用。请在服务器已激活的项目环境中运行。",
            EXIT_DEPENDENCY,
        ) from error
    return average_precision_score


def require_torch() -> Any:
    try:
        import torch
    except ModuleNotFoundError as error:
        raise StageError(
            "缺少 torch：S0 推理反事实需要 GPU 版 PyTorch。请在服务器已激活的项目环境中运行。",
            EXIT_DEPENDENCY,
        ) from error
    if not torch.cuda.is_available():
        raise StageError(
            "当前进程没有可用 CUDA 设备：S0 必须复现封印检查点的 CUDA 推理路径，"
            "不接受 CPU 回退（回退会改变 BF16 语义并使精度反事实失效）。",
            EXIT_DEPENDENCY,
        )
    return torch


def require_project_modules() -> tuple[Any, Any, Any]:
    """只读导入既有的划分、实体构造、模型结构与精度运行时，不复制算法。"""

    if str(TOOL_DIR) not in sys.path:
        sys.path.insert(0, str(TOOL_DIR))
    try:
        import ch3_full_mlp_complete_entity_lp_protocol_a_q0 as legacy
        import ch3_full_mlp_complete_entity_lp_protocol_a_q0_bf16 as bf16_entry
        import neural_precision_runtime as precision
    except ModuleNotFoundError as error:
        raise StageError(
            f"无法导入既有全容量 MLP 模块：{error}。S0 必须复用父运行的模型结构与精度运行时，"
            "不允许在本工具内复制一份模型定义。",
            EXIT_DEPENDENCY,
        ) from error
    return legacy, bf16_entry, precision


# --------------------------------------------------------------------------------------
# 基础输入输出
# --------------------------------------------------------------------------------------


def sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise StageError(f"必需的 JSON 不存在：{path}", EXIT_INPUT) from error
    except json.JSONDecodeError as error:
        raise StageError(f"JSON 解析失败：{path}：{error}", EXIT_INPUT) from error


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def atomic_npz(path: Path, arrays: dict[str, Any]) -> dict[str, Any]:
    np = require_numpy()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.replace(temporary, path)
    return {
        "filename": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "fields": {name: {"shape": list(values.shape), "dtype": str(values.dtype)} for name, values in arrays.items()},
    }


def ensure_output_root(config: dict[str, Any]) -> Path:
    output_root = Path(config["paths"]["output_root"])
    try:
        output_root.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise StageError(
            f"无法创建或访问运行根 {output_root}：{error}。该路径属于服务器项目根，"
            "开发机不执行本阶段；请由 Codex 主进程在服务器通过启动器运行。",
            EXIT_INPUT,
        ) from error
    return output_root


def existing_output_root(config: dict[str, Any], stage: str) -> Path:
    output_root = Path(config["paths"]["output_root"])
    if not output_root.is_dir():
        raise StageError(
            f"运行根不存在：{output_root}。`--stage {stage}` 只消费已有制品，"
            "请先在服务器执行 `--stage source`（必要时再执行 `--stage target`）。",
            EXIT_STAGE_PRECONDITION,
        )
    return output_root


def write_status(output_root: Path, state: str, stage: str, detail: str, exit_code: int | None) -> None:
    atomic_json(
        output_root / "status.json",
        {
            "schema_version": "ch3-full-mlp-s0-status-v1",
            "run_id": RUN_ID,
            "display_name": DISPLAY_NAME,
            "state": state,
            "stage": stage,
            "detail": detail,
            "exit_code": exit_code,
            "updated_at_unix": time.time(),
            "training_runs": 0,
            "parameter_updates": 0,
            "new_checkpoints_written": 0,
            "wall_clock_limit": None,
        },
    )


# --------------------------------------------------------------------------------------
# 配置核验（纯标准库）
# --------------------------------------------------------------------------------------


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StageError(f"配置核验失败：{message}", EXIT_CONFIG)


def tracking_alias_config_path(config: dict[str, Any]) -> Path:
    path = Path(config["tracking"]["alias_config_path"])
    return path if path.is_absolute() else TOOL_DIR.parent / path


def tracking_destination(config: dict[str, Any]) -> dict[str, Any]:
    tracking = config["tracking"]
    return {
        key: tracking[key]
        for key in ("workspace", "project", "name", "group", "mode", "tags")
    }


def validate_tracking_contract(config: dict[str, Any]) -> dict[str, Any]:
    """只调用中央稳定接口；本工具不复制 20 码点规则。"""

    try:
        from flow_probe.tracking import load_swanlab_tag_aliases, validate_swanlab_contract
    except ImportError as error:
        raise StageError("无法导入中央 SwanLab 合同接口", EXIT_CONFIG) from error
    alias_path = tracking_alias_config_path(config).resolve()
    if not alias_path.is_file():
        raise StageError(f"SwanLab 标签别名文件不存在：{alias_path}", EXIT_CONFIG)
    actual_alias_sha = sha256_file(alias_path)
    expected_alias_sha = config["tracking"]["alias_config_sha256"]
    if actual_alias_sha != expected_alias_sha:
        raise StageError("SwanLab 标签别名文件哈希与冻结配置不符", EXIT_CONFIG)
    try:
        aliases = load_swanlab_tag_aliases(alias_path)
        return validate_swanlab_contract(
            tracking_destination(config),
            aliases=aliases,
            authorized_workspace=config["tracking"]["workspace"],
            authorized_project=config["tracking"]["project"],
        )
    except ValueError as error:
        raise StageError(f"SwanLab 中央合同核验失败：{error}", EXIT_CONFIG) from error


def resolve_precision_contract(config: dict[str, Any]) -> Path:
    configured = Path(config.get("paths", {}).get("precision_contract", ""))
    if configured.is_file():
        return configured
    local = TOOL_DIR.parent / "configs" / configured.name
    if configured.name == "neural-precision-profiles-v1.json" and local.is_file():
        return local
    raise StageError(f"统一精度合同不存在：{configured}", EXIT_CONFIG)


def validate_config(config: dict[str, Any]) -> None:
    """逐项拒绝并给出中文原因；不导入 numpy 与 torch。"""

    _require(config.get("schema_version") == SCHEMA_VERSION, "配置模式版本不符")
    _require(config.get("run_id") == RUN_ID, "运行身份不符")
    _require(config.get("display_name") == DISPLAY_NAME, "展示名不符")
    _require(config.get("model_key") == "full_mlp", "模型键必须是 full_mlp")
    _require(config.get("evidence_level") == "zero_train_screening", "证据等级必须是零训练筛选")

    _require(config.get("source_arrays") == ["X23", "y23", "I23", "M23", "E23", "T23"], "源年数组白名单不符")
    _require(config.get("target_arrays") == ["X24", "y24", "I24", "M24", "s24", "d24"], "目标年数组白名单不符；t24 不参与曝光序号轴")

    parent = config.get("parent_selection", {})
    _require(parent.get("run_id") == PARENT_RUN_ID, "父运行身份不符")
    _require(parent.get("seal_filename") == "selection_frozen.json", "父封印文件名不符")
    identity = parent.get("identity", {})
    _require(
        set(identity) == {"config_sha256", "code_sha256", "source_data_inventory_sha256"}
        and all(isinstance(value, str) and len(value) == 64 for value in identity.values()),
        "父封印身份三项摘要缺失或长度不是 64",
    )
    _require(
        parent.get("source_inventory_json_pointer") == "/source_data_inventory",
        "父源年 inventory JSON 指针不符",
    )
    split = parent.get("source_split", {})
    _require(
        split
        == {
            "entity_count": 150680,
            "train_sequences": 208598,
            "validation_sequences": 22444,
            "train_validation_row_intersection": 0,
        },
        "源年划分统计与父封印不符",
    )
    checkpoints = parent.get("checkpoints", {})
    _require(tuple(checkpoints) == CELL_ORDER, "四个检查点键或顺序不符")
    for cell in CELL_ORDER:
        item = checkpoints[cell]
        _require(item.get("filename") == f"checkpoints/selected-{cell}.pt", f"{cell} 检查点相对路径不符")
        _require(isinstance(item.get("bytes"), int) and item["bytes"] > 0, f"{cell} 检查点字节数无效")
        _require(isinstance(item.get("sha256"), str) and len(item["sha256"]) == 64, f"{cell} 检查点摘要无效")
        _require(isinstance(item.get("causal_prefix_aggregation"), bool), f"{cell} 因果前缀开关无效")
        _require(isinstance(item.get("learned_lp_pooling"), bool), f"{cell} 学习幂平均开关无效")
        _require(
            isinstance(item.get("frozen_power_mean_p"), (int, float)) and float(item["frozen_power_mean_p"]) > 0,
            f"{cell} 冻结幂平均指数无效",
        )
        _require(isinstance(item.get("frozen_power_mean_source"), str), f"{cell} 冻结幂平均来源未登记")

    model = config.get("model", {})
    _require(model.get("feature_count") == 83, "字段数必须是 83")
    _require(model.get("hidden_depth") == 8 and model.get("hidden_size") == 512, "容量必须复用父封印的 8x512")
    _require(model.get("activation") == "relu" and model.get("dropout") == 0.1, "激活或 dropout 与父封印不符")
    _require(model.get("sequence_length") == 128, "序列长度必须是 128")
    _require(model.get("parameter_count") == 2_144_258, "参数量与父封印不符")
    depth, width, features = model["hidden_depth"], model["hidden_size"], model["feature_count"]
    _require(
        depth * width**2 + (depth + features + 1) * width + 2 == model["parameter_count"],
        "参数量与公式闭式不一致",
    )

    reproduction = config.get("split_reproduction", {})
    _require(reproduction.get("seed") == 42, "划分种子不符")
    _require(reproduction.get("validation_fraction") == 0.1, "验证比例不符")
    _require(reproduction.get("time_tail_fraction") == 0.15, "时间尾部比例不符")
    _require(
        reproduction.get("source_evaluation_rows") == "lspr23_entity_disjoint_validation_rows",
        "源年评价行集合必须是实体不相交验证行",
    )

    precision_config = config.get("precision", {})
    _require(precision_config.get("bf16_profile_id") == "cuda-bf16-amp-fp32-sensitive-v1", "BF16 精度档案不符")
    _require(precision_config.get("fp32_profile_id") == "cuda-fp32-numerical-fallback-v1", "FP32 精度档案不符")
    _require(isinstance(precision_config.get("fp32_profile_receipt_reason"), str), "FP32 例外收据理由缺失")
    _require(precision_config.get("assert_bf16_forward_output_dtype") == "bfloat16", "BF16 输出 dtype 断言缺失")
    _require(precision_config.get("assert_fp32_forward_output_dtype") == "float32", "FP32 输出 dtype 断言缺失")
    _require(precision_config.get("assert_identical_weights_across_arms") is True, "必须断言两臂权重同一")

    arms = config.get("arms", [])
    expected_arms = [
        ("bf16_probability_mean", "bf16", "probability", "S0-PB"),
        ("bf16_logit_mean", "bf16", "logit", "S0-LB"),
        ("fp32_probability_mean", "fp32", "probability", "S0-PF"),
        ("fp32_logit_mean", "fp32", "logit", "S0-LF"),
    ]
    _require(len(arms) == 4, "候选臂必须恰好四个")
    for arm, (key, precision_name, space, label) in zip(arms, expected_arms):
        _require(arm.get("key") == key, f"候选臂键不符：期望 {key}")
        _require(arm.get("precision") == precision_name, f"{key} 精度不符")
        _require(arm.get("aggregation_space") == space, f"{key} 聚合空间不符")
        _require(arm.get("candidate_label") == label, f"{key} 候选标签不符")
        _require(arm.get("clip") is False, f"{key} 候选臂禁止裁剪概率")
        _require(arm.get("is_candidate_arm") is True, f"{key} 必须标记为候选臂")
        _require(isinstance(arm.get("display_name"), str) and arm["display_name"], f"{key} 缺少可读展示名")

    controls = {item.get("key"): item for item in config.get("controls", [])}
    _require(
        set(controls) == {"max_control", "frozen_power_mean_control", "probability_mean_clipped_control"},
        "控制算子集合不符",
    )
    _require(controls["max_control"]["clip"] is False, "最大值控制算子不得裁剪")
    _require(controls["frozen_power_mean_control"]["clip"] is True, "冻结幂平均强基线必须沿用历史裁剪")
    _require(controls["probability_mean_clipped_control"]["clip"] is True, "加裁剪对照必须裁剪")
    _require(config.get("strong_baseline_arm_key") == "bf16_frozen_power_mean_control", "强基线分支键不符")

    evaluation = config.get("evaluation", {})
    _require(evaluation.get("dr_fpr_grid") == [0.001, 0.005, 0.01, 0.02, 0.04, 0.08], "六档误报预算不符")
    _require(evaluation.get("curve_maximum_fpr") == 0.08, "阶梯面积上界不符")
    _require(
        evaluation.get("tie_policy") == "all_reachable_complete_negative_tie_groups",
        "并列策略必须是完整良性并列组",
    )
    _require(evaluation.get("interpolation_allowed") is False, "禁止插值")
    _require(evaluation.get("first_alert_axis") == "exposure_index", "首次告警轴必须是曝光序号")
    _require(evaluation.get("exposure_index_base") == 1, "曝光序号必须 1 基")
    _require(
        evaluation.get("first_alert_exposure_order") == "ascending_frozen_flow_index_within_entity",
        "曝光顺序与父运行不一致",
    )
    _require(
        evaluation.get("first_alert_threshold_sources")
        == ["common_actual_fp_budget", "actual_reachable_terminal", "nominal_quantile"],
        "首次告警阈值来源必须登记公共整数 FP、终端实际可达与名义分位",
    )
    _require(
        evaluation.get("common_integer_fp_budget_formula")
        == "floor(nominal_target_fpr*negative_entity_denominator)",
        "公共整数 FP 预算公式不符",
    )
    _require(evaluation.get("first_alert_quantiles") == [0.25, 0.5, 0.75, 0.9, 0.95], "曝光分位合同不符")
    _require(evaluation.get("control_clip_epsilon") == 1e-07, "控制算子裁剪下界不符")
    _require(evaluation.get("candidate_arm_clip_applied") is False, "候选臂不得应用裁剪")
    _require(evaluation.get("time_delay_available") is False, "本数据不具备秒级时延")
    _require(evaluation.get("aggregation_dtype") == "float64", "聚合算术必须是 float64")
    branches = evaluation.get("first_alert_branches", [])
    _require(isinstance(branches, list) and len(branches) == len(set(branches)) and branches, "首次告警分支列表无效")
    for key in ("bf16_probability_mean", "bf16_logit_mean", "fp32_probability_mean", "fp32_logit_mean"):
        _require(key in branches, f"首次告警必须覆盖候选臂 {key}")

    inference = config.get("inference", {})
    _require(isinstance(inference.get("sequence_batch"), int) and inference["sequence_batch"] > 0, "推理批无效")
    _require(inference.get("torch_no_grad") is True and inference.get("model_eval_mode") is True, "推理必须无梯度且 eval")

    selfcheck = config.get("data_selfcheck", {})
    _require(selfcheck.get("source_x_shape") == [16353511, 83], "源年特征形状不符")
    _require(selfcheck.get("source_index_shape") == [271815, 128], "源年索引形状不符")
    _require(selfcheck.get("target_x_shape") == [20227356, 83], "目标年特征形状不符")
    _require(selfcheck.get("target_entity_count") == 47115, "目标年实体数不符")
    _require(selfcheck.get("target_positive_entity_count") == 752, "目标年正实体数不符")
    _require(abs(float(selfcheck.get("target_flow_positive_rate", 0.0)) - 0.0257073138) < 1e-12, "目标年逐流正例率不符")

    lesion = config.get("lesion_classification", {})
    _require(lesion.get("reference_arm") == "bf16_probability_mean", "病灶分类基准臂必须是 S0-PB")
    _require(
        lesion.get("labels")
        == [
            "inference_quantization_dominant",
            "aggregation_space_dominant",
            "interaction",
            "upstream_unresolved",
        ],
        "病灶分类标签集合不符",
    )
    _require(lesion.get("upstream_unresolved_forbids_training_bf16_verdict") is True, "未分解时禁止判训练期 BF16")

    gate = config.get("source_gate", {})
    _require(gate.get("forbid_larger_tie_cliff") is True, "源年门必须禁止更大并列悬崖")
    _require(gate.get("forbid_nominal_only_improvement") is True, "源年门必须禁止只在名义点改善")
    _require(gate.get("float_tolerance") == 0.0, "源年门不得设置事后数值容差")

    artifact = config.get("artifact_policy", {})
    for key in (
        "persist_per_flow_scores",
        "persist_per_entity_scores",
        "persist_per_entity_first_alert",
        "persist_entity_mapping",
        "persist_exposure_matrix",
        "persist_new_checkpoints",
    ):
        _require(artifact.get(key) is False, f"制品合同必须禁止 {key}")
    _require(artifact.get("persist_complete_tied_curve_aggregate") is True, "必须保存完整整组曲线")
    _require(artifact.get("persist_first_alert_aggregate_only") is True, "首次告警只保存聚合")

    resources = config.get("resource_contract", {})
    _require(resources.get("minimum_free_gpu_memory_mib") == 20480, "GPU 空闲准入门不符")
    _require(resources.get("minimum_cgroup_available_memory_gib") == 30, "控制组主存门不符")
    _require(resources.get("minimum_free_disk_gib") == 10, "磁盘门不符")
    _require(resources.get("wall_clock_limit") is None, "禁止设置墙钟上限")

    tracking = config.get("tracking", {})
    _require(isinstance(tracking.get("workspace"), str) and tracking["workspace"], "跟踪工作区缺失")
    _require(isinstance(tracking.get("project"), str) and tracking["project"], "跟踪项目缺失")
    _require(tracking.get("mode") == "cloud", "跟踪必须是在线模式")
    _require(tracking.get("aggregate_only") is True, "跟踪只允许上报聚合指标")
    _require(tracking.get("group") == RUN_ID, "跟踪分组与运行身份不符")
    _require(isinstance(tracking.get("tags"), list) and tracking["tags"], "跟踪标签必须是非空列表")
    _require(tracking.get("alias_config_path") == "configs/swanlab-tag-aliases-v1.json", "标签别名文件路径不符")
    _require(
        tracking.get("alias_config_sha256")
        == "d2bf7212068e6d7ced2fa916cd327dd24fea26bbb3bd3cbd9fd241c77a3f7a16",
        "标签别名文件冻结哈希不符",
    )
    _require(tracking.get("central_api_commit") == "89ddecf", "SwanLab 中央 API 提交不符")
    validate_tracking_contract(config)
    _require(
        config.get("tracking_lifecycle")
        == {
            "maximum_online_init_attempts": 2,
            "retryable_first_attempt_error": "zero_step_init_401",
            "retry_exit_code": EXIT_RETRYABLE_SWANLAB_INIT_401,
            "second_attempt_requires_fresh_python_process": True,
            "health_gate_required_per_attempt": True,
            "unknown_inflight_forbids_new_init": True,
            "completed_receipt_allows_local_seal_only": True,
        },
        "SwanLab 两次上限恢复合同不符",
    )

    isolation = config.get("isolation", {})
    _require(isolation.get("training_runs") == 0, "本任务禁止训练")
    _require(isolation.get("parameter_updates") == 0, "本任务禁止参数更新")
    _require(isolation.get("optimizer_steps") == 0, "本任务禁止优化器步")
    _require(isolation.get("new_checkpoints_written") == 0, "本任务禁止写新检查点")
    _require(isolation.get("target_year_arrays_read_before_seal") == 0, "封印前目标年读取必须为 0")
    _require(isolation.get("target_load_after_source_seal") is True, "目标年必须在源年封印后加载")
    _require(isolation.get("formal_paper_evidence") is False, "零训练筛选不得标记正式论文证据")
    _require(isolation.get("independent_test") is False, "目标年已被访问，不得标记独立测试")

    _require(Path(config["paths"]["output_root"]).name == RUN_ID, "输出根目录名与运行身份不符")
    resolve_precision_contract(config)


def validate_precision_profiles(config: dict[str, Any]) -> dict[str, Any]:
    """核验两个精度档案确实一个开 autocast、一个不开，且参数都保持 FP32。"""

    _, _, precision = require_project_modules()
    contract = precision.load_and_validate_contract(resolve_precision_contract(config))
    bf16 = precision.get_profile(contract, config["precision"]["bf16_profile_id"])
    fp32 = precision.get_profile(contract, config["precision"]["fp32_profile_id"])
    if bf16["compute_dtype"] != "bfloat16" or bf16["autocast"] is not True or bf16["grad_scaler"] is not False:
        raise StageError("BF16 精度档案不满足 autocast=真、GradScaler=假", EXIT_CONFIG)
    if fp32["compute_dtype"] != "float32" or fp32["autocast"] is not False:
        raise StageError("FP32 精度档案不满足 autocast=假", EXIT_CONFIG)
    for name, profile in (("bf16", bf16), ("fp32", fp32)):
        if profile["parameter_dtype"] != "float32":
            raise StageError(f"{name} 精度档案的参数 dtype 不是 float32", EXIT_CONFIG)
        if profile["device_type"] != "cuda":
            raise StageError(f"{name} 精度档案不是 CUDA 档案", EXIT_CONFIG)
    return {"bf16": bf16, "fp32": fp32}


# --------------------------------------------------------------------------------------
# 输入门：父封印、四个检查点与冻结缓存
# --------------------------------------------------------------------------------------


def validate_inputs(config: dict[str, Any], arrays: tuple[str, ...]) -> dict[str, Any]:
    parent_root = Path(config["paths"]["parent_run_root"])
    seal_path = parent_root / config["parent_selection"]["seal_filename"]
    if not seal_path.is_file():
        raise StageError(
            f"父运行封印不存在：{seal_path}。S0 必须消费已封印的四格选择，不允许重建。",
            EXIT_INPUT,
        )
    seal = load_json(seal_path)
    if seal.get("run_id") != PARENT_RUN_ID or seal.get("all_four_cells_sealed") is not True:
        raise StageError("父封印身份不符或四格未全部封印，拒绝继续", EXIT_INPUT)
    if seal.get("identity") != config["parent_selection"]["identity"]:
        raise StageError("父封印的配置/代码/数据摘要与本配置登记值不符，拒绝继续", EXIT_INPUT)
    if seal.get("source_split") != config["parent_selection"]["source_split"]:
        raise StageError("父封印的源年划分统计与本配置登记值不符，拒绝继续", EXIT_INPUT)

    derived = seal.get("derived_p", {})
    checkpoint_receipts: dict[str, Any] = {}
    for cell in CELL_ORDER:
        registered = config["parent_selection"]["checkpoints"][cell]
        sealed = seal["cells"][cell]["checkpoint"]
        if sealed.get("sha256") != registered["sha256"] or sealed.get("bytes") != registered["bytes"]:
            raise StageError(f"{cell} 的封印检查点摘要或字节数与本配置登记值不符", EXIT_INPUT)
        expected_p = float(registered["frozen_power_mean_p"])
        if cell == "B00":
            actual_p = float(derived.get("N01", float("nan")))
        elif cell == "B10":
            actual_p = float(derived.get("N11", float("nan")))
        else:
            actual_p = float(seal["cells"][cell]["p_at_selection"])
        if actual_p != expected_p:
            raise StageError(
                f"{cell} 的冻结幂平均指数不符：封印={actual_p!r}，配置={expected_p!r}。"
                "S0 只复算封印 p，禁止新选 p。",
                EXIT_INPUT,
            )
        checkpoint_path = parent_root / registered["filename"]
        if not checkpoint_path.is_file():
            raise StageError(
                f"{cell} 的封印检查点不存在：{checkpoint_path}。该文件只存在于服务器父运行根，"
                "开发机无法执行本阶段。",
                EXIT_INPUT,
            )
        actual_bytes = checkpoint_path.stat().st_size
        if actual_bytes != registered["bytes"]:
            raise StageError(f"{cell} 检查点字节数不符：实测={actual_bytes}，期望={registered['bytes']}", EXIT_INPUT)
        actual_sha = sha256_file(checkpoint_path)
        if actual_sha != registered["sha256"]:
            raise StageError(f"{cell} 检查点摘要不符，拒绝加载被改写的权重", EXIT_INPUT)
        checkpoint_receipts[cell] = {
            "path": str(checkpoint_path),
            "bytes": actual_bytes,
            "sha256": actual_sha,
            "frozen_power_mean_p": expected_p,
            "frozen_power_mean_source": registered["frozen_power_mean_source"],
        }

    cache_root = Path(config["paths"]["cache_root"])
    is_source = list(arrays) == config["source_arrays"]
    is_target = list(arrays) == config["target_arrays"]
    if not (is_source or is_target):
        raise StageError("输入数组集合既不是源年也不是目标年白名单", EXIT_INPUT)
    array_receipts: list[dict[str, Any]] = []
    for name in arrays:
        path = cache_root / f"{name}.npy"
        if not path.is_file():
            raise StageError(
                f"冻结缓存缺失：{path}。S0 不重建缓存，请在服务器核对 `dijk-repro/cache`。",
                EXIT_INPUT,
            )
        stat = path.stat()
        array_receipts.append(
            {
                "name": f"{name}.npy",
                "bytes": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": sha256_file(path),
            }
        )

    stat_inventory = [
        {"name": item["name"], "bytes": item["bytes"], "mtime_ns": item["mtime_ns"]}
        for item in array_receipts
    ]
    parent_inventory_binding = None
    if is_source:
        parent_inventory = seal.get("source_data_inventory")
        if not isinstance(parent_inventory, dict):
            raise StageError("父封印缺少 source_data_inventory，源数组无法绑定父 inventory", EXIT_INPUT)
        parent_inventory_sha = canonical_sha256(parent_inventory.get("files"))
        registered_sha = config["parent_selection"]["identity"]["source_data_inventory_sha256"]
        if (
            parent_inventory.get("schema_version") != "ch3-protocol-a-data-inventory-v1"
            or parent_inventory.get("cache_root") != str(cache_root)
            or parent_inventory.get("files") != stat_inventory
            or parent_inventory.get("sha256") != registered_sha
            or parent_inventory_sha != registered_sha
        ):
            raise StageError("源年数组与父封印 inventory 或其 SHA-256 不符，拒绝继续", EXIT_INPUT)
        inventory_sha = registered_sha
        parent_inventory_binding = {
            "seal_path": str(seal_path),
            "json_pointer": config["parent_selection"]["source_inventory_json_pointer"],
            "schema_version": parent_inventory["schema_version"],
            "declared_sha256": registered_sha,
            "recomputed_sha256": parent_inventory_sha,
            "matched": True,
        }
    else:
        inventory_sha = canonical_sha256(stat_inventory)
    return {
        "schema_version": "ch3-full-mlp-s0-input-validation-v1",
        "run_id": RUN_ID,
        "year": "source" if is_source else "target",
        "parent_run_id": PARENT_RUN_ID,
        "parent_seal": {"path": str(seal_path), "sha256": sha256_file(seal_path)},
        "parent_source_inventory_binding": parent_inventory_binding,
        "checkpoints": checkpoint_receipts,
        "cache_root": str(cache_root),
        "arrays": array_receipts,
        "array_inventory_sha256": inventory_sha,
        "array_content_inventory_sha256": canonical_sha256(
            [{"name": item["name"], "bytes": item["bytes"], "sha256": item["sha256"]} for item in array_receipts]
        ),
    }


# --------------------------------------------------------------------------------------
# 数值内核
# --------------------------------------------------------------------------------------


def stable_sigmoid(values: Any) -> Any:
    """数值稳定的 float64 sigmoid：正负分支分别计算，避免 exp 溢出与告警。"""

    np = require_numpy()
    values = np.asarray(values, dtype=np.float64)
    result = np.empty_like(values)
    positive = values >= 0.0
    result[positive] = 1.0 / (1.0 + np.exp(-values[positive]))
    exponent = np.exp(values[~positive])
    result[~positive] = exponent / (1.0 + exponent)
    return result


def ordered_exposures(seen: Any, flow_entity: Any) -> dict[str, Any]:
    """实体内按冻结数组下标升序的已打分流顺序，与父入口 ``_ordered_exposures`` 同一语义。"""

    np = require_numpy()
    flow_ids = np.flatnonzero(seen).astype(np.int64, copy=False)
    entities = flow_entity[flow_ids]
    order = np.lexsort((flow_ids, entities))
    ordered_flow_ids = flow_ids[order]
    ordered_entities = entities[order]
    starts = np.flatnonzero(np.r_[True, ordered_entities[1:] != ordered_entities[:-1]])
    lengths = np.diff(np.r_[starts, len(ordered_entities)]).astype(np.int64)
    exposure_index = np.arange(len(ordered_entities), dtype=np.int64) - np.repeat(starts, lengths) + 1
    return {
        "flow_ids": ordered_flow_ids,
        "entities": ordered_entities,
        "starts": starts,
        "lengths": lengths,
        "ends": starts + lengths,
        "exposure_index": exposure_index,
        "entity_ids": ordered_entities[starts],
    }


def prefix_group_sums(ordered_values: Any, order: dict[str, Any]) -> Any:
    """实体内前缀和；终端值由同一份前缀和取末位，保证终端与在线读数逐位一致。"""

    np = require_numpy()
    cumulative = np.cumsum(ordered_values, dtype=np.float64)
    previous = np.zeros(len(order["starts"]), dtype=np.float64)
    previous[1:] = cumulative[order["starts"][1:] - 1]
    return cumulative - np.repeat(previous, order["lengths"])


def branch_transform(branch: dict[str, Any], ordered_logits: Any, clip_epsilon: float) -> tuple[Any, Any]:
    """返回（用于求和的逐流量, 后处理函数标识）。"""

    np = require_numpy()
    space = branch["aggregation_space"]
    if space == "logit":
        return np.asarray(ordered_logits, dtype=np.float64), None
    probabilities = stable_sigmoid(ordered_logits)
    if space == "probability":
        return probabilities, None
    if space in ("power_mean", "power_mean_p1", "max"):
        if branch.get("clip"):
            probabilities = np.clip(probabilities, clip_epsilon, 1.0)
        if space == "max":
            return probabilities, None
        exponent = float(branch["p"])
        return probabilities**exponent, exponent
    raise StageError(f"未知聚合空间：{space}", EXIT_CONFIG)


def branch_postprocess(branch: dict[str, Any], values: Any, exponent: float | None) -> Any:
    np = require_numpy()
    if branch["aggregation_space"] == "logit":
        return stable_sigmoid(values)
    if exponent is not None and exponent != 1.0:
        return np.asarray(values, dtype=np.float64) ** (1.0 / exponent)
    return np.asarray(values, dtype=np.float64)


def entity_terminal_scores(
    branch: dict[str, Any],
    ordered_logits: Any,
    order: dict[str, Any],
    entity_count: int,
    clip_epsilon: float,
) -> tuple[Any, Any]:
    """返回（长度为实体数的终端分数, 该分支的有序在线原始量），未打分实体为 NaN。"""

    np = require_numpy()
    values, exponent = branch_transform(branch, ordered_logits, clip_epsilon)
    scores = np.full(entity_count, np.nan, dtype=np.float64)
    if branch["aggregation_space"] == "max":
        group_max = np.maximum.reduceat(values, order["starts"])
        scores[order["entity_ids"]] = group_max
        return scores, values
    group_sums = prefix_group_sums(values, order)
    terminal_mean = group_sums[order["ends"] - 1] / order["lengths"].astype(np.float64)
    scores[order["entity_ids"]] = branch_postprocess(branch, terminal_mean, exponent)
    return scores, values


def branch_running_scores(branch: dict[str, Any], values: Any, order: dict[str, Any]) -> Any:
    """实体内前缀在线分数；最大值分支使用实体内前缀最大。"""

    np = require_numpy()
    if branch["aggregation_space"] == "max":
        raise StageError("最大值控制算子不参与首次告警轴", EXIT_CONFIG)
    exponent = float(branch["p"]) if branch["aggregation_space"] in ("power_mean", "power_mean_p1") else None
    group_sums = prefix_group_sums(values, order)
    running_mean = group_sums / order["exposure_index"].astype(np.float64)
    return branch_postprocess(branch, running_mean, exponent)


def complete_tied_budget_curve(scores: Any, labels: Any) -> dict[str, Any]:
    """完整良性并列组曲线，语义与 ch3_xgb_cpa_elp_operational_backfill 一致。"""

    np = require_numpy()
    valid = np.isfinite(scores)
    values = scores[valid].astype(np.float64)
    targets = labels[valid]
    negative = values[targets == 0]
    positive = np.sort(values[targets == 1])
    if not len(negative) or not len(positive):
        raise StageError("完整预算曲线缺少正类或负类实体", EXIT_INPUT)
    unique_ascending, tie_ascending = np.unique(negative, return_counts=True)
    thresholds = unique_ascending[::-1]
    tie_counts = tie_ascending[::-1].astype(np.int64)
    zero_threshold = np.nextafter(float(thresholds[0]), float("inf"))
    thresholds = np.concatenate(([zero_threshold], thresholds)).astype(np.float64)
    tie_counts = np.concatenate(([0], tie_counts)).astype(np.int64)
    false_positive = np.concatenate(([0], np.cumsum(tie_counts[1:], dtype=np.int64)))
    detection = (len(positive) - np.searchsorted(positive, thresholds, side="left")) / len(positive)
    realized = false_positive.astype(np.float64) / len(negative)
    return {
        "threshold": thresholds,
        "negative_tie_group_size": tie_counts,
        "n_false_positive_entity": false_positive,
        "realized_fpr": realized,
        "detection_rate": detection.astype(np.float64),
        "negative_entity_count": int(len(negative)),
        "positive_entity_count": int(len(positive)),
    }


def actual_reachable_readouts(curve: dict[str, Any], grid: list[float]) -> dict[str, Any]:
    np = require_numpy()
    realized = curve["realized_fpr"]
    results: dict[str, Any] = {}
    for budget in grid:
        index = int(np.searchsorted(realized, budget, side="right") - 1)
        if index < 0:
            raise StageError("完整曲线缺少零误报可达点", EXIT_INPUT)
        following = index + 1
        results[f"fpr_{budget:g}"] = {
            "nominal_target_fpr": float(budget),
            "actual_reachable_fpr": float(realized[index]),
            "detection_rate": float(curve["detection_rate"][index]),
            "threshold": float(curve["threshold"][index]),
            "false_positive_entity_count": int(curve["n_false_positive_entity"][index]),
            "negative_tie_group_size": int(curve["negative_tie_group_size"][index]),
            "negative_entity_denominator": curve["negative_entity_count"],
            "positive_entity_denominator": curve["positive_entity_count"],
            "interpolated": False,
            "next_reachable_point": None
            if following >= len(realized)
            else {
                "actual_reachable_fpr": float(realized[following]),
                "detection_rate": float(curve["detection_rate"][following]),
                "false_positive_entity_count": int(curve["n_false_positive_entity"][following]),
                "negative_tie_group_size": int(curve["negative_tie_group_size"][following]),
            },
        }
    return results


def common_integer_fp_budget_readouts(curve: dict[str, Any], grid: list[float]) -> dict[str, Any]:
    """把六档名义锚投影到共同整数 FP 预算，再取不超预算的最后完整并列组。"""

    np = require_numpy()
    false_positive = curve["n_false_positive_entity"]
    negative_count = int(curve["negative_entity_count"])
    results: dict[str, Any] = {}
    for nominal in grid:
        budget = math.floor(float(nominal) * negative_count)
        key = f"fp_{budget}"
        if key in results:
            raise StageError("六档锚点投影到重复整数 FP 预算，无法保持独立比较", EXIT_INPUT)
        index = int(np.searchsorted(false_positive, budget, side="right") - 1)
        if index < 0 or int(false_positive[index]) > budget:
            raise StageError("公共整数 FP 投影没有选中合法的零误报起点", EXIT_INPUT)
        following = index + 1
        if following < len(false_positive) and int(false_positive[following]) <= budget:
            raise StageError("公共整数 FP 投影不是最后可达完整并列组", EXIT_INPUT)
        results[key] = {
            "nominal_target_fpr": float(nominal),
            "common_integer_false_positive_budget": budget,
            "actual_reachable_fpr": float(curve["realized_fpr"][index]),
            "detection_rate": float(curve["detection_rate"][index]),
            "threshold": float(curve["threshold"][index]),
            "false_positive_entity_count": int(false_positive[index]),
            "negative_tie_group_size": int(curve["negative_tie_group_size"][index]),
            "negative_entity_denominator": negative_count,
            "positive_entity_denominator": int(curve["positive_entity_count"]),
            "selection_rule": "last_complete_tie_group_with_false_positive_count_not_greater_than_budget",
            "interpolated": False,
            "next_reachable_point": None
            if following >= len(false_positive)
            else {
                "actual_reachable_fpr": float(curve["realized_fpr"][following]),
                "detection_rate": float(curve["detection_rate"][following]),
                "false_positive_entity_count": int(false_positive[following]),
                "negative_tie_group_size": int(curve["negative_tie_group_size"][following]),
            },
        }
    return results


def nominal_quantile_readouts(scores: Any, labels: Any, grid: list[float]) -> dict[str, Any]:
    """历史分位阈值读数，并同时给出该名义阈值实际达到的 FPR 与 FP 数。"""

    np = require_numpy()
    valid = np.isfinite(scores)
    values = scores[valid].astype(np.float64)
    targets = labels[valid]
    negative = np.sort(values[targets == 0])[::-1]
    positive = values[targets == 1]
    if not len(negative) or not len(positive):
        raise StageError("名义读数缺少正类或负类实体", EXIT_INPUT)
    results: dict[str, Any] = {}
    for budget in grid:
        index = min(int(len(negative) * budget), len(negative) - 1)
        threshold = float(negative[index])
        false_positive = int((negative >= threshold).sum())
        results[f"fpr_{budget:g}"] = {
            "nominal_target_fpr": float(budget),
            "threshold": threshold,
            "detection_rate": float((positive >= threshold).mean()),
            "actual_fpr_at_nominal_threshold": false_positive / len(negative),
            "false_positive_entity_count": false_positive,
            "negative_entity_denominator": int(len(negative)),
            "rule": "sorted_descending_negative_quantile_index",
        }
    return results


def normalized_curve_area(curve: dict[str, Any], maximum_fpr: float) -> dict[str, Any]:
    """0 到上界的阶梯面积，沿用父入口 curve_summary 的右连续矩形累计。"""

    np = require_numpy()
    x = curve["realized_fpr"]
    y = curve["detection_rate"]
    selected = x <= maximum_fpr
    selected_x = np.concatenate(([0.0], x[selected], [maximum_fpr]))
    selected_y = np.concatenate(([0.0], y[selected], [y[selected][-1] if selected.any() else 0.0]))
    area = float(np.sum(np.diff(selected_x) * selected_y[:-1]) / maximum_fpr)
    return {"normalized_area_0_8_fpr": area, "points_0_8_fpr": int(selected.sum())}


def tie_profile(scores: Any, labels: Any) -> dict[str, Any]:
    """唯一值数量、最大并列组规模与其良性/恶意构成。"""

    np = require_numpy()
    valid = np.isfinite(scores)
    values = scores[valid].astype(np.float64)
    targets = labels[valid]
    unique_values, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    largest = int(np.argmax(counts))
    members = inverse == largest
    return {
        "scored_entities": int(valid.sum()),
        "unique_entity_scores": int(len(unique_values)),
        "largest_tie_group_size": int(counts[largest]),
        "largest_tie_group_value": float(unique_values[largest]),
        "largest_tie_group_benign_entities": int((targets[members] == 0).sum()),
        "largest_tie_group_malicious_entities": int((targets[members] == 1).sum()),
        "tie_groups_with_more_than_one_member": int((counts > 1).sum()),
    }


def largest_tie_group_mask(scores: Any) -> Any:
    np = require_numpy()
    valid = np.isfinite(scores)
    values = scores.astype(np.float64)
    unique_values, inverse, counts = np.unique(values[valid], return_inverse=True, return_counts=True)
    largest = int(np.argmax(counts))
    mask = np.zeros(len(scores), dtype=bool)
    mask[np.flatnonzero(valid)[inverse == largest]] = True
    return mask


def count_discordant_pairs(first: Any, second: Any) -> int:
    """精确逆序对：按第一向量升序（同值按第二向量升序）后统计第二向量的逆序数。"""

    np = require_numpy()
    order = np.lexsort((second, first))
    ranked = np.unique(second[order], return_inverse=True)[1].astype(np.int64) + 1
    size = int(ranked.max()) if len(ranked) else 0
    tree = [0] * (size + 1)
    inserted = 0
    discordant = 0
    for value in ranked.tolist():
        prefix = 0
        index = value
        while index > 0:
            prefix += tree[index]
            index -= index & (-index)
        discordant += inserted - prefix
        index = value
        while index <= size:
            tree[index] += 1
            index += index & (-index)
        inserted += 1
    return int(discordant)


def compare_score_vectors(reference: Any, candidate: Any, reference_group: Any) -> dict[str, Any]:
    """同一实体集合上的并列拆分与排序反转统计。"""

    np = require_numpy()
    both = np.isfinite(reference) & np.isfinite(candidate)
    left = reference[both].astype(np.float64)
    right = candidate[both].astype(np.float64)
    group = reference_group[both]
    reference_unique, reference_inverse, reference_counts = np.unique(left, return_inverse=True, return_counts=True)
    split_groups = 0
    for index in np.flatnonzero(reference_counts > 1).tolist():
        members = reference_inverse == index
        if len(np.unique(right[members])) > 1:
            split_groups += 1
    return {
        "compared_entities": int(both.sum()),
        "reference_unique_values": int(len(reference_unique)),
        "candidate_unique_values": int(len(np.unique(right))),
        "reference_tie_groups_with_more_than_one_member": int((reference_counts > 1).sum()),
        "reference_tie_groups_split_by_candidate": int(split_groups),
        "reference_largest_group_members": int(group.sum()),
        "reference_largest_group_distinct_values_under_candidate": int(len(np.unique(right[group]))),
        "discordant_entity_pairs": count_discordant_pairs(left, right),
    }


def first_alert_aggregate(
    branch: dict[str, Any],
    running_scores: Any,
    order: dict[str, Any],
    entity_labels: Any,
    scored_entities: Any,
    readouts: dict[str, Any],
    threshold_source: str,
    quantiles: list[float],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """按 1 基实体内曝光序号统计首次告警；只输出聚合，不落逐实体位置。"""

    np = require_numpy()
    positive = scored_entities & (entity_labels == 1)
    benign = scored_entities & (entity_labels == 0)
    positive_count = int(positive.sum())
    benign_count = int(benign.sum())
    if positive_count == 0 or benign_count == 0:
        raise StageError("首次告警统计缺少正类或负类实体", EXIT_INPUT)
    summaries: dict[str, Any] = {}
    vectors: dict[str, Any] = {}
    for key, readout in readouts.items():
        threshold = float(readout["threshold"])
        crossing = np.flatnonzero(running_scores >= threshold)
        crossing_entities = order["entities"][crossing]
        unique_entities, first_positions = np.unique(crossing_entities, return_index=True)
        first_crossing = crossing[first_positions]
        first_alert = np.zeros(len(entity_labels), dtype=np.int64)
        first_alert[unique_entities] = order["exposure_index"][first_crossing]
        alerted_positive = positive & (first_alert > 0)
        alerted_benign = benign & (first_alert > 0)
        positions = first_alert[alerted_positive]
        if len(positions):
            quantile_values = np.quantile(positions.astype(np.float64), quantiles)
            unique_deadlines, detected = np.unique(positions, return_counts=True)
            cumulative = np.cumsum(detected, dtype=np.int64)
            axis = np.r_[0, unique_deadlines].astype(np.int64)
            rate = np.r_[0.0, cumulative / positive_count].astype(np.float64)
        else:
            quantile_values = np.full(len(quantiles), np.nan)
            axis = np.array([0], dtype=np.int64)
            rate = np.array([0.0], dtype=np.float64)
        summaries[key] = {
            "threshold_source": threshold_source,
            "nominal_target_fpr": float(readout["nominal_target_fpr"]),
            "terminal_reference_fpr": float(
                readout.get("actual_reachable_fpr", readout.get("actual_fpr_at_nominal_threshold", float("nan")))
            ),
            "common_integer_false_positive_budget": readout.get("common_integer_false_positive_budget"),
            "threshold_false_positive_entity_count": readout.get("false_positive_entity_count"),
            "threshold": threshold,
            "threshold_comparison": "score_greater_equal_threshold",
            "tied_group_kept_complete": True,
            "axis": "exposure_index",
            "exposure_index_base": 1,
            "positive_entity_count": positive_count,
            "alerted_positive_entity_count": int(alerted_positive.sum()),
            "never_alerted_positive_entity_count": int((positive & (first_alert == 0)).sum()),
            "positive_unalerted_rate": float((positive & (first_alert == 0)).sum() / positive_count),
            "benign_entity_count": benign_count,
            "alerted_benign_entity_count": int(alerted_benign.sum()),
            "first_alert_actual_fpr": float(alerted_benign.sum() / benign_count),
            "first_alert_exposure_quantiles": {
                f"q{int(round(quantile * 100)):02d}": None if not np.isfinite(value) else float(value)
                for quantile, value in zip(quantiles, quantile_values)
            },
            "on_time_detection_curve_points": int(len(axis)),
            "on_time_detection_fixed_positive_denominator": positive_count,
            "time_delay_available": False,
        }
        prefix = f"{branch['key']}__{threshold_source}__{key}"
        vectors[f"{prefix}__exposure_index"] = axis
        vectors[f"{prefix}__on_time_detection_rate"] = rate
        del first_alert
    return summaries, vectors


def compare_first_alert_on_common_axis(
    candidate_key: str,
    baseline_key: str,
    first_alert: dict[str, Any],
    curves: dict[str, Any],
) -> dict[str, Any]:
    """在同一整数 FP 预算与曝光断点并集上比较首次告警阶梯。"""

    np = require_numpy()
    candidate = first_alert[candidate_key]["common_actual_fp_budget"]
    baseline = first_alert[baseline_key]["common_actual_fp_budget"]
    if set(candidate) != set(baseline):
        raise StageError("候选臂与强基线的首次告警公共 FP 预算键不一致", EXIT_INPUT)
    comparisons: dict[str, Any] = {}
    for budget_key, baseline_summary in baseline.items():
        candidate_summary = candidate[budget_key]
        if (
            candidate_summary["common_integer_false_positive_budget"]
            != baseline_summary["common_integer_false_positive_budget"]
        ):
            raise StageError("候选臂与强基线的首次告警整数 FP 预算不同", EXIT_INPUT)
        candidate_prefix = f"{candidate_key}__common_actual_fp_budget__{budget_key}"
        baseline_prefix = f"{baseline_key}__common_actual_fp_budget__{budget_key}"
        candidate_axis = curves[f"{candidate_prefix}__exposure_index"]
        candidate_rate = curves[f"{candidate_prefix}__on_time_detection_rate"]
        baseline_axis = curves[f"{baseline_prefix}__exposure_index"]
        baseline_rate = curves[f"{baseline_prefix}__on_time_detection_rate"]
        common_axis = np.union1d(candidate_axis, baseline_axis)
        candidate_index = np.searchsorted(candidate_axis, common_axis, side="right") - 1
        baseline_index = np.searchsorted(baseline_axis, common_axis, side="right") - 1
        if int(candidate_index.min()) < 0 or int(baseline_index.min()) < 0:
            raise StageError("首次告警阶梯缺少曝光轴零起点", EXIT_INPUT)
        delta = candidate_rate[candidate_index] - baseline_rate[baseline_index]
        unalerted_delta = (
            candidate_summary["positive_unalerted_rate"] - baseline_summary["positive_unalerted_rate"]
        )
        not_worse = bool((delta >= 0.0).all() and unalerted_delta <= 0.0)
        strictly_better = bool((delta > 0.0).any() or unalerted_delta < 0.0)
        comparisons[budget_key] = {
            "common_integer_false_positive_budget": candidate_summary[
                "common_integer_false_positive_budget"
            ],
            "comparison_axis": "union_of_exact_exposure_breakpoints",
            "comparison_axis_points": int(len(common_axis)),
            "candidate_first_alert_actual_fp": candidate_summary["alerted_benign_entity_count"],
            "baseline_first_alert_actual_fp": baseline_summary["alerted_benign_entity_count"],
            "candidate_first_alert_actual_fpr": candidate_summary["first_alert_actual_fpr"],
            "baseline_first_alert_actual_fpr": baseline_summary["first_alert_actual_fpr"],
            "minimum_on_time_detection_rate_delta": float(delta.min()),
            "maximum_on_time_detection_rate_delta": float(delta.max()),
            "positive_unalerted_rate_delta": float(unalerted_delta),
            "not_worse_on_common_exposure_axis": not_worse,
            "strictly_better_on_common_exposure_axis": strictly_better,
        }
    return comparisons


# --------------------------------------------------------------------------------------
# 前向：同一权重的两条精度路径
# --------------------------------------------------------------------------------------


def build_frozen_model(config: dict[str, Any], cell: str, checkpoint_path: Path, device: Any) -> tuple[Any, str, dict[str, Any]]:
    """加载封印检查点，返回（模型, 权重摘要, dtype 收据）。不训练、不改权重。"""

    torch = require_torch()
    _, bf16_entry, _ = require_project_modules()
    model_config = config["model"]
    cell_config = config["parent_selection"]["checkpoints"][cell]
    model = bf16_entry.FullCapacityMLPBF16(
        model_config["feature_count"],
        model_config["hidden_depth"],
        model_config["hidden_size"],
        model_config["dropout"],
        cell_config["causal_prefix_aggregation"],
    )
    actual = sum(parameter.numel() for parameter in model.parameters())
    if actual != model_config["parameter_count"]:
        raise StageError(f"{cell} 框架实测参数量不符：{actual}", EXIT_INPUT)
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if checkpoint.get("identity", {}).get("cell") != cell:
        raise StageError(f"{cell} 检查点内部身份不符", EXIT_INPUT)
    state = checkpoint["model"]
    dtypes = sorted({str(tensor.dtype) for tensor in state.values()})
    if dtypes != ["torch.float32"]:
        raise StageError(
            f"{cell} 检查点权重不是全 FP32（实测 {dtypes}）：无法证明 FP32 臂不是由 BF16 权重事后扩展",
            EXIT_INPUT,
        )
    digest = hashlib.sha256()
    for name in sorted(state):
        digest.update(name.encode("utf-8"))
        digest.update(state[name].detach().cpu().contiguous().numpy().tobytes())
    weights_sha256 = digest.hexdigest()
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    receipt = {
        "checkpoint_schema_version": checkpoint.get("schema_version"),
        "checkpoint_precision_profile_id": checkpoint.get("precision_profile_id"),
        "state_dict_dtypes": dtypes,
        "parameter_count": actual,
        "weights_sha256": weights_sha256,
        "loaded_once_for_both_precision_arms": True,
    }
    del checkpoint
    return model, weights_sha256, receipt


def forward_logits(
    config: dict[str, Any],
    model: Any,
    precision_name: str,
    profile: dict[str, Any],
    device: Any,
    gX: Any,
    gI: Any,
    gM: Any,
    row_selection: Any,
    flow_count: int,
    stage: str,
) -> tuple[Any, Any, dict[str, Any]]:
    """一次前向产出全部已见流的预 sigmoid 对数几率。"""

    np = require_numpy()
    torch = require_torch()
    _, _, precision = require_project_modules()
    length = config["model"]["sequence_length"]
    batch = config["inference"]["sequence_batch"]
    logits_buffer = np.full(flow_count, np.nan, dtype=np.float32)
    seen = np.zeros(flow_count, dtype=bool)
    total_rows = int(gI.shape[0]) if row_selection is None else int(len(row_selection))
    observed_dtype: str | None = None
    processed = 0
    started = time.time()
    torch.cuda.reset_peak_memory_stats(device)
    with torch.no_grad():
        for start in range(0, total_rows, batch):
            if row_selection is None:
                indices = gI[start : start + batch][:, :length]
                valid = gM[start : start + batch][:, :length] > 0.5
            else:
                rows = torch.from_numpy(row_selection[start : start + batch]).to(device)
                indices = gI[rows][:, :length]
                valid = gM[rows][:, :length] > 0.5
            count = indices.shape[0]
            values = gX[indices.reshape(-1)].reshape(count, length, gX.shape[1])
            with precision.autocast_context(profile, device.type, torch):
                logits = model(values, valid)
            if observed_dtype is None:
                observed_dtype = str(logits.dtype)
            mask = valid.reshape(-1)
            flow_ids = indices.reshape(-1)[mask]
            logits_buffer[flow_ids.cpu().numpy()] = logits.reshape(-1)[mask].float().cpu().numpy()
            seen[flow_ids.cpu().numpy()] = True
            processed += count
            beat(f"{stage}/{precision_name} 前向", processed, total_rows, started)
    seconds = time.time() - started
    expected = f"torch.{config['precision']['assert_' + precision_name + '_forward_output_dtype']}"
    if observed_dtype != expected:
        raise StageError(
            f"{precision_name} 臂的模型输出 dtype 实测为 {observed_dtype}，期望 {expected}："
            "精度反事实没有真实生效，拒绝把两臂当作不同精度报告。",
            EXIT_INPUT,
        )
    receipt = {
        "precision": precision_name,
        "profile_id": profile["profile_id"] if "profile_id" in profile else None,
        "autocast_enabled": bool(profile["autocast"]),
        "compute_dtype": profile["compute_dtype"],
        "forward_output_dtype": observed_dtype,
        "forward_seconds": seconds,
        "scored_flows": int(seen.sum()),
        "flows_per_second": float(int(seen.sum()) / max(seconds, 1e-9)),
        "peak_gpu_allocated_mib": float(torch.cuda.max_memory_allocated(device) / 2**20),
        "peak_gpu_reserved_mib": float(torch.cuda.max_memory_reserved(device) / 2**20),
    }
    return logits_buffer, seen, receipt


# --------------------------------------------------------------------------------------
# 单元执行：一个年度 × 一个检查点
# --------------------------------------------------------------------------------------


def branch_definitions(config: dict[str, Any], cell: str) -> list[dict[str, Any]]:
    """展开该检查点在两个精度下的全部分支；候选臂在前，控制算子在后。"""

    definitions: list[dict[str, Any]] = []
    frozen_p = float(config["parent_selection"]["checkpoints"][cell]["frozen_power_mean_p"])
    for arm in config["arms"]:
        definitions.append(
            {
                "key": arm["key"],
                "display_name": arm["display_name"],
                "candidate_label": arm["candidate_label"],
                "precision": arm["precision"],
                "aggregation_space": arm["aggregation_space"],
                "clip": False,
                "p": None,
                "role": "candidate_arm",
            }
        )
    for precision_name in PRECISION_ORDER:
        for control in config["controls"]:
            definitions.append(
                {
                    "key": f"{precision_name}_{control['key']}",
                    "display_name": f"{precision_name.upper()}推理·{control['display_name']}",
                    "candidate_label": None,
                    "precision": precision_name,
                    "aggregation_space": control["aggregation_space"],
                    "clip": bool(control["clip"]),
                    "p": frozen_p if control["key"] == "frozen_power_mean_control" else 1.0,
                    "role": "control",
                    "purpose": control["purpose"],
                }
            )
    return definitions


def run_unit(
    config: dict[str, Any],
    year: str,
    cell: str,
    device: Any,
    profiles: dict[str, Any],
    checkpoint_receipt: dict[str, Any],
    tensors: dict[str, Any],
    entity: dict[str, Any],
    order: dict[str, Any],
    flow_labels: Any,
    row_selection: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    np = require_numpy()
    torch = require_torch()
    average_precision_score = require_metrics()
    evaluation = config["evaluation"]
    grid = evaluation["dr_fpr_grid"]
    clip_epsilon = float(evaluation["control_clip_epsilon"])
    quantiles = evaluation["first_alert_quantiles"]
    entity_labels = entity["labels"]
    entity_count = int(entity["count"])
    scored_entities = entity["scored"]

    model, weights_sha256, model_receipt = build_frozen_model(
        config, cell, Path(checkpoint_receipt["path"]), device
    )
    definitions = branch_definitions(config, cell)
    unit_started = time.time()
    branch_metrics: dict[str, Any] = {}
    branch_scores: dict[str, Any] = {}
    forward_receipts: dict[str, Any] = {}
    flow_metrics: dict[str, Any] = {}
    curves: dict[str, Any] = {}
    first_alert: dict[str, Any] = {}
    max_equivalence: dict[str, bool] = {}
    aggregation_seconds = 0.0

    for precision_name in PRECISION_ORDER:
        profile = dict(profiles[precision_name])
        profile["profile_id"] = config["precision"][f"{precision_name}_profile_id"]
        logits, seen, forward_receipt = forward_logits(
            config,
            model,
            precision_name,
            profile,
            device,
            tensors["X"],
            tensors["I"],
            tensors["M"],
            row_selection,
            len(flow_labels),
            f"{year}/{cell}",
        )
        forward_receipt["weights_sha256"] = weights_sha256
        forward_receipts[precision_name] = forward_receipt
        if not np.array_equal(seen, entity["seen"]):
            raise StageError(
                f"{year}/{cell}/{precision_name} 的已打分流集合与共享曝光顺序不一致，拒绝继续",
                EXIT_INPUT,
            )
        aggregation_started = time.time()
        ordered_logits = logits[order["flow_ids"]].astype(np.float64)
        finite = np.isfinite(ordered_logits)
        if not bool(finite.all()):
            raise StageError(f"{year}/{cell}/{precision_name} 出现非有限对数几率", EXIT_INPUT)
        ordered_probabilities = stable_sigmoid(ordered_logits)
        flow_metrics[precision_name] = {
            "flow_average_precision": float(
                average_precision_score(flow_labels[order["flow_ids"]], ordered_probabilities)
            ),
            "scored_flows": int(len(ordered_logits)),
            "unique_logits": int(len(np.unique(ordered_logits))),
            "unique_probabilities": int(len(np.unique(ordered_probabilities))),
            "logit_minimum": float(ordered_logits.min()),
            "logit_maximum": float(ordered_logits.max()),
            "probability_minimum": float(ordered_probabilities.min()),
            "probability_maximum": float(ordered_probabilities.max()),
        }
        del ordered_probabilities

        for branch in definitions:
            if branch["precision"] != precision_name:
                continue
            scores, ordered_values = entity_terminal_scores(
                branch, ordered_logits, order, entity_count, clip_epsilon
            )
            curve = complete_tied_budget_curve(scores, entity_labels)
            metrics = {
                "display_name": branch["display_name"],
                "candidate_label": branch["candidate_label"],
                "role": branch["role"],
                "precision": precision_name,
                "aggregation_space": branch["aggregation_space"],
                "clip_applied": bool(branch["clip"]),
                "p": branch["p"],
                "flow_average_precision": flow_metrics[precision_name]["flow_average_precision"],
                "entity_average_precision": float(
                    average_precision_score(entity_labels[scored_entities], scores[scored_entities])
                ),
                "actual_reachable_dr_at_fpr": actual_reachable_readouts(curve, grid),
                "common_actual_dr_at_integer_fp_budget": common_integer_fp_budget_readouts(curve, grid),
                "nominal_dr_at_fpr": nominal_quantile_readouts(scores, entity_labels, grid),
                "tie_profile": tie_profile(scores, entity_labels),
                **normalized_curve_area(curve, float(evaluation["curve_maximum_fpr"])),
            }
            for field in ("threshold", "negative_tie_group_size", "n_false_positive_entity", "realized_fpr", "detection_rate"):
                curves[f"{branch['key']}__{field}"] = curve[field]
            if branch["key"] in evaluation["first_alert_branches"]:
                running = branch_running_scores(branch, ordered_values, order)
                path_scores = np.full(len(entity_labels), np.nan, dtype=np.float64)
                path_scores[order["entity_ids"]] = np.maximum.reduceat(running, order["starts"])
                path_curve = complete_tied_budget_curve(path_scores, entity_labels)
                common_path_readouts = common_integer_fp_budget_readouts(path_curve, grid)
                for source_name, readouts in (
                    ("common_actual_fp_budget", common_path_readouts),
                    ("actual_reachable_terminal", metrics["actual_reachable_dr_at_fpr"]),
                    ("nominal_quantile", metrics["nominal_dr_at_fpr"]),
                ):
                    summaries, vectors = first_alert_aggregate(
                        branch, running, order, entity_labels, scored_entities, readouts, source_name, quantiles
                    )
                    first_alert.setdefault(branch["key"], {})[source_name] = summaries
                    curves.update(vectors)
                for field in (
                    "threshold",
                    "negative_tie_group_size",
                    "n_false_positive_entity",
                    "realized_fpr",
                    "detection_rate",
                ):
                    curves[f"{branch['key']}__first_alert_path__{field}"] = path_curve[field]
                for budget_key, summary in first_alert[branch["key"]]["common_actual_fp_budget"].items():
                    if summary["alerted_benign_entity_count"] != common_path_readouts[budget_key][
                        "false_positive_entity_count"
                    ]:
                        raise StageError(
                            f"{year}/{cell}/{branch['key']}/{budget_key} 首次告警 FP 与路径曲线不一致",
                            EXIT_INPUT,
                        )
                del running, path_scores, path_curve
            branch_metrics[branch["key"]] = metrics
            branch_scores[branch["key"]] = scores
            del ordered_values, curve
        # 实现一致性锚：最大值算子必须满足 max_i sigmoid(z_i) == sigmoid(max_i z_i)（严格单调等价）。
        expected_max = stable_sigmoid(np.maximum.reduceat(ordered_logits, order["starts"]))
        observed_max = branch_scores[f"{precision_name}_max_control"][order["entity_ids"]]
        if not np.array_equal(expected_max, observed_max):
            raise StageError(
                f"{year}/{cell}/{precision_name} 的最大值算子不满足单调变换等价，聚合实现有误",
                EXIT_INPUT,
            )
        max_equivalence[precision_name] = True
        del expected_max, observed_max
        aggregation_seconds += time.time() - aggregation_started
        del logits, seen, ordered_logits

    if forward_receipts["bf16"]["weights_sha256"] != forward_receipts["fp32"]["weights_sha256"]:
        raise StageError("两个精度臂的权重摘要不相等，权重在两次前向之间被改写", EXIT_INPUT)

    baseline_key = config["strong_baseline_arm_key"]
    common_first_alert_comparisons = {
        arm["key"]: compare_first_alert_on_common_axis(
            arm["key"], baseline_key, first_alert, curves
        )
        for arm in config["arms"]
    }

    reference = branch_scores[config["lesion_classification"]["reference_arm"]]
    reference_group = largest_tie_group_mask(reference)
    comparisons = {
        "bf16_to_fp32_in_probability_space": compare_score_vectors(
            reference, branch_scores["fp32_probability_mean"], reference_group
        ),
        "probability_to_logit_in_bf16": compare_score_vectors(
            reference, branch_scores["bf16_logit_mean"], reference_group
        ),
        "bf16_probability_to_fp32_logit": compare_score_vectors(
            reference, branch_scores["fp32_logit_mean"], reference_group
        ),
        "bf16_to_fp32_in_logit_space": compare_score_vectors(
            branch_scores["bf16_logit_mean"], branch_scores["fp32_logit_mean"], largest_tie_group_mask(branch_scores["bf16_logit_mean"])
        ),
    }
    consistency = {
        "max_operator_monotone_equivalence_verified": max_equivalence,
        "max_entity_average_precision_bf16": branch_metrics["bf16_max_control"]["entity_average_precision"],
        "max_entity_average_precision_fp32": branch_metrics["fp32_max_control"]["entity_average_precision"],
        "frozen_power_mean_p": config["parent_selection"]["checkpoints"][cell]["frozen_power_mean_p"],
        "frozen_power_mean_source": config["parent_selection"]["checkpoints"][cell]["frozen_power_mean_source"],
    }

    del model
    torch.cuda.empty_cache()
    unit = {
        "schema_version": UNIT_SCHEMA_VERSION,
        "run_id": RUN_ID,
        "year": year,
        "cell": cell,
        "cell_display_name": config["parent_selection"]["checkpoints"][cell]["display_name"],
        "mechanisms": {
            "causal_prefix_aggregation": config["parent_selection"]["checkpoints"][cell]["causal_prefix_aggregation"],
            "learned_lp_pooling": config["parent_selection"]["checkpoints"][cell]["learned_lp_pooling"],
        },
        "checkpoint": checkpoint_receipt,
        "model_receipt": model_receipt,
        "forward_receipts": forward_receipts,
        "flow_level": flow_metrics,
        "branches": branch_metrics,
        "first_alert": first_alert,
        "common_first_alert_comparisons": {
            "baseline": baseline_key,
            "candidates": common_first_alert_comparisons,
        },
        "tie_comparisons": comparisons,
        "control_consistency": consistency,
        "entity_denominators": {
            "entity_count": entity_count,
            "scored_entities": int(scored_entities.sum()),
            "scored_positive_entities": int((scored_entities & (entity_labels == 1)).sum()),
            "scored_benign_entities": int((scored_entities & (entity_labels == 0)).sum()),
        },
        "timing": {
            "unit_wall_seconds": time.time() - unit_started,
            "aggregation_seconds": aggregation_seconds,
            "forward_seconds_sum": sum(item["forward_seconds"] for item in forward_receipts.values()),
        },
        "training_runs": 0,
        "parameter_updates": 0,
        "persisted_per_flow_scores": False,
        "persisted_per_entity_scores": False,
    }
    return unit, curves


# --------------------------------------------------------------------------------------
# 阶段：源年
# --------------------------------------------------------------------------------------


def unit_identity(config: dict[str, Any], year: str, cell: str, inputs: dict[str, Any], config_sha: str, code_sha: str) -> str:
    return canonical_sha256(
        {
            "run_id": RUN_ID,
            "year": year,
            "cell": cell,
            "config_sha256": config_sha,
            "code_sha256": code_sha,
            "checkpoint_sha256": inputs["checkpoints"][cell]["sha256"],
            "array_inventory_sha256": inputs["array_inventory_sha256"],
            "array_content_inventory_sha256": inputs["array_content_inventory_sha256"],
        }
    )


def build_source_context(config: dict[str, Any], arrays: dict[str, Any]) -> tuple[dict[str, Any], Any, Any]:
    """复用父入口的划分与实体构造，只在实体不相交验证行上评价。"""

    np = require_numpy()
    legacy, _, _ = require_project_modules()
    shape = config["data_selfcheck"]
    if list(arrays["X23"].shape) != shape["source_x_shape"] or list(arrays["I23"].shape) != shape["source_index_shape"]:
        raise StageError("LSPR23 冻结缓存形状不符，拒绝继续", EXIT_INPUT)
    split_config = {
        "training": {
            "seed": config["split_reproduction"]["seed"],
            "validation_fraction": config["split_reproduction"]["validation_fraction"],
            "time_tail_fraction": config["split_reproduction"]["time_tail_fraction"],
        }
    }
    _, validation_rows, stats = legacy.source_split(arrays, split_config)
    if stats != config["parent_selection"]["source_split"]:
        raise StageError(f"源年划分统计与父封印不符：{stats}", EXIT_INPUT)
    flow_entity = legacy.build_flow_entity(arrays["I23"], arrays["M23"], arrays["E23"], len(arrays["y23"]))
    entity_count = int(flow_entity.max()) + 1
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_labels, flow_entity, arrays["y23"])
    return {"flow_entity": flow_entity, "count": entity_count, "labels": entity_labels}, validation_rows, stats


def build_target_context(config: dict[str, Any], arrays: dict[str, Any]) -> dict[str, Any]:
    """目标年实体键为无序 IP 对，与父入口逐字一致；原始地址只作实体键。"""

    np = require_numpy()
    shape = config["data_selfcheck"]
    if list(arrays["X24"].shape) != shape["target_x_shape"]:
        raise StageError("LSPR24 冻结缓存形状不符，拒绝继续", EXIT_INPUT)
    key = np.array(
        [
            left + "|" + right if left <= right else right + "|" + left
            for left, right in zip(arrays["s24"], arrays["d24"])
        ],
        dtype=object,
    )
    _, flow_entity = np.unique(key, return_inverse=True)
    del key
    entity_count = int(flow_entity.max()) + 1
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_labels, flow_entity, arrays["y24"])
    flow_positive_rate = float(arrays["y24"].astype(np.float64).mean())
    if (
        entity_count != shape["target_entity_count"]
        or int(entity_labels.sum()) != shape["target_positive_entity_count"]
        or abs(flow_positive_rate - shape["target_flow_positive_rate"]) >= shape["target_flow_positive_rate_tolerance"]
    ):
        raise StageError("LSPR24 实体与标签自检失败，拒绝继续", EXIT_INPUT)
    return {"flow_entity": flow_entity, "count": entity_count, "labels": entity_labels}


def run_year_stage(config: dict[str, Any], args: argparse.Namespace, year: str) -> None:
    np = require_numpy()
    torch = require_torch()
    legacy, _, _ = require_project_modules()
    profiles = validate_precision_profiles(config)
    arrays_names = tuple(config["source_arrays"] if year == "source" else config["target_arrays"])
    output_root = ensure_output_root(config)
    write_status(output_root, "running", year, "输入门与依赖门核验", None)
    inputs = validate_inputs(config, arrays_names)
    input_receipt_path = output_root / f"input-validation-receipt-{year}.json"
    if input_receipt_path.is_file():
        if load_json(input_receipt_path) != inputs:
            raise StageError(f"{year} 输入收据已存在但 inventory 或逐数组哈希漂移，拒绝覆盖", EXIT_INPUT)
    else:
        atomic_json(input_receipt_path, inputs)
    atomic_json(output_root / "config.json", config)

    config_sha = sha256_file(Path(args.config).resolve())
    code_sha = sha256_file(Path(__file__).resolve())
    pending = []
    for cell in CELL_ORDER:
        unit_path = output_root / "unit-aggregates" / year / f"{cell}.json"
        identity = unit_identity(config, year, cell, inputs, config_sha, code_sha)
        if unit_path.is_file():
            existing = load_json(unit_path)
            if existing.get("unit_identity") == identity:
                log(f"{year}/{cell} 身份一致的完成单元存在，幂等跳过")
                continue
            raise StageError(
                f"{year}/{cell} 已有单元产物但身份不符（配置、代码、检查点或数据清单之一已变）。"
                "拒绝覆盖既有制品；请人工裁决后使用新运行身份，不得在原身份上伪装恢复。",
                EXIT_STAGE_PRECONDITION,
            )
        pending.append((cell, identity))
    if not pending:
        write_status(output_root, "running", year, "全部单元已完成，无需重算", None)
        log(f"{year} 阶段四个单元均已完成")
        return

    cache_root = Path(config["paths"]["cache_root"])
    arrays = {name: np.load(cache_root / f"{name}.npy", allow_pickle=name in {"s24", "d24"}) for name in arrays_names}
    if set(arrays) != set(arrays_names):
        raise StageError("加载的数组集合超出白名单", EXIT_INPUT)

    if year == "source":
        entity_base, row_selection, _ = build_source_context(config, arrays)
        feature_key, index_key, mask_key, label_key = "X23", "I23", "M23", "y23"
    else:
        entity_base = build_target_context(config, arrays)
        row_selection = None
        feature_key, index_key, mask_key, label_key = "X24", "I24", "M24", "y24"

    device = torch.device("cuda")
    flow_labels = arrays[label_key]
    seen = np.zeros(len(flow_labels), dtype=bool)
    length = config["model"]["sequence_length"]
    index_array = arrays[index_key][:, :length] if row_selection is None else arrays[index_key][row_selection][:, :length]
    mask_array = arrays[mask_key][:, :length] if row_selection is None else arrays[mask_key][row_selection][:, :length]
    seen[index_array[mask_array > 0.5]] = True
    del index_array, mask_array
    tensors = {
        "X": torch.from_numpy(arrays[feature_key]).to(device),
        "I": torch.from_numpy(arrays[index_key]).to(device),
        "M": torch.from_numpy(arrays[mask_key]).to(device),
    }
    # GPU 端已持有唯一计算副本，释放同名主存数组以给聚合阶段留出 float64 工作区。
    for name in (feature_key, index_key, mask_key):
        arrays.pop(name, None)
    for name in ("E23", "T23", "s24", "d24"):
        arrays.pop(name, None)
    order = ordered_exposures(seen, entity_base["flow_entity"])
    scored_entities = np.zeros(entity_base["count"], dtype=bool)
    scored_entities[order["entity_ids"]] = True
    entity = {
        "flow_entity": entity_base["flow_entity"],
        "count": entity_base["count"],
        "labels": entity_base["labels"],
        "seen": seen,
        "scored": scored_entities,
    }

    for cell, identity in pending:
        write_status(output_root, "running", year, f"{cell} 双精度前向与聚合", None)
        unit, curves = run_unit(
            config,
            year,
            cell,
            device,
            profiles,
            inputs["checkpoints"][cell],
            tensors,
            entity,
            order,
            flow_labels,
            row_selection,
        )
        curve_receipt = atomic_npz(output_root / "curves" / year / f"{cell}.npz", curves)
        curve_receipt.update({"schema_version": CURVE_SCHEMA_VERSION, "year": year, "cell": cell})
        atomic_json(output_root / "curves" / year / f"{cell}-receipt.json", curve_receipt)
        unit["unit_identity"] = identity
        unit["curve_artifact"] = {"filename": f"curves/{year}/{cell}.npz", "sha256": curve_receipt["sha256"]}
        unit["target_year_arrays_read"] = 0 if year == "source" else 1
        atomic_json(output_root / "unit-aggregates" / year / f"{cell}.json", unit)
        log(f"{year}/{cell} 单元完成，曲线摘要 {curve_receipt['sha256'][:16]}")
        del unit, curves

    for tensor in tensors.values():
        del tensor
    torch.cuda.empty_cache()
    write_status(output_root, "running", year, "四个单元全部完成", None)


# --------------------------------------------------------------------------------------
# 阶段：源年封印
# --------------------------------------------------------------------------------------


def load_units(output_root: Path, year: str) -> dict[str, Any]:
    units: dict[str, Any] = {}
    for cell in CELL_ORDER:
        path = output_root / "unit-aggregates" / year / f"{cell}.json"
        if not path.is_file():
            raise StageError(
                f"缺少 {year} 单元产物：{path}。请先在服务器执行 `--stage {year}`。",
                EXIT_STAGE_PRECONDITION,
            )
        units[cell] = load_json(path)
    return units


def classify_lesion(config: dict[str, Any], unit: dict[str, Any]) -> dict[str, Any]:
    """按并列组成员关系机械判断病灶，不设事后数值容差。"""

    comparisons = unit["tie_comparisons"]
    branches = unit["branches"]
    reference_key = config["lesion_classification"]["reference_arm"]
    baseline = branches[reference_key]
    splits = {
        "fp32_probability_mean": comparisons["bf16_to_fp32_in_probability_space"][
            "reference_largest_group_distinct_values_under_candidate"
        ],
        "bf16_logit_mean": comparisons["probability_to_logit_in_bf16"][
            "reference_largest_group_distinct_values_under_candidate"
        ],
        "fp32_logit_mean": comparisons["bf16_probability_to_fp32_logit"][
            "reference_largest_group_distinct_values_under_candidate"
        ],
    }
    improved: dict[str, bool] = {}
    for key in splits:
        candidate = branches[key]
        area_better = candidate["normalized_area_0_8_fpr"] > baseline["normalized_area_0_8_fpr"]
        point_better = any(
            candidate["common_actual_dr_at_integer_fp_budget"][budget]["detection_rate"]
            > baseline["common_actual_dr_at_integer_fp_budget"][budget]["detection_rate"]
            for budget in baseline["common_actual_dr_at_integer_fp_budget"]
        )
        improved[key] = bool(area_better or point_better)

    if splits["fp32_probability_mean"] > 1 and splits["bf16_logit_mean"] == 1:
        label = "inference_quantization_dominant"
        supporting_arm = "fp32_probability_mean"
    elif splits["bf16_logit_mean"] > 1 and splits["fp32_probability_mean"] == 1:
        label = "aggregation_space_dominant"
        supporting_arm = "bf16_logit_mean"
    elif (
        splits["fp32_probability_mean"] == 1
        and splits["bf16_logit_mean"] == 1
        and splits["fp32_logit_mean"] > 1
    ):
        label = "interaction"
        supporting_arm = "fp32_logit_mean"
    else:
        label = "upstream_unresolved"
        supporting_arm = None
    if supporting_arm is not None and not improved[supporting_arm]:
        label = "upstream_unresolved"
    return {
        "label": label,
        "reference_arm": reference_key,
        "reference_largest_tie_group_size": baseline["tie_profile"]["largest_tie_group_size"],
        "reference_largest_tie_group_benign_entities": baseline["tie_profile"]["largest_tie_group_benign_entities"],
        "reference_largest_tie_group_malicious_entities": baseline["tie_profile"]["largest_tie_group_malicious_entities"],
        "distinct_values_of_reference_group_under_arm": splits,
        "arm_improves_actual_reachable_curve": improved,
        "classification_supporting_arm": supporting_arm,
        "supporting_arm_improved": None if supporting_arm is None else improved[supporting_arm],
        "forbidden_conclusion": "upstream_unresolved 只表示训练期精度、表示与辅助目标仍未区分，不得单独判为训练期 BF16",
    }


def evaluate_source_gate(config: dict[str, Any], unit: dict[str, Any]) -> dict[str, Any]:
    """候选文档 4.8 的四条源年门，强基线固定为同检查点的 BF16 冻结幂平均。"""

    branches = unit["branches"]
    baseline_key = config["strong_baseline_arm_key"]
    baseline = branches[baseline_key]
    first_alert_comparisons = unit["common_first_alert_comparisons"]
    if first_alert_comparisons.get("baseline") != baseline_key:
        raise StageError("源门首次告警强基线身份不符", EXIT_INPUT)
    results: dict[str, Any] = {}
    for arm in config["arms"]:
        key = arm["key"]
        candidate = branches[key]
        candidate_alert_comparison = first_alert_comparisons["candidates"][key]
        entity_ap_better = candidate["entity_average_precision"] > baseline["entity_average_precision"]
        area_better = candidate["normalized_area_0_8_fpr"] > baseline["normalized_area_0_8_fpr"]
        baseline_common = baseline["common_actual_dr_at_integer_fp_budget"]
        candidate_common = candidate["common_actual_dr_at_integer_fp_budget"]
        if set(candidate_common) != set(baseline_common):
            raise StageError(f"{key} 与强基线的公共整数 FP 预算键不一致", EXIT_INPUT)
        for budget_key in baseline_common:
            if (
                candidate_common[budget_key]["common_integer_false_positive_budget"]
                != baseline_common[budget_key]["common_integer_false_positive_budget"]
            ):
                raise StageError(f"{key}/{budget_key} 与强基线的整数 FP 预算不同", EXIT_INPUT)
        reachable_better = any(
            candidate_common[budget]["detection_rate"] > baseline_common[budget]["detection_rate"]
            for budget in baseline_common
        )
        alert_better = any(
            item["strictly_better_on_common_exposure_axis"]
            for item in candidate_alert_comparison.values()
        )
        not_worse_on_common_budgets = all(
            candidate_common[budget]["detection_rate"] >= baseline_common[budget]["detection_rate"]
            for budget in baseline_common
        )
        first_alert_not_worse = all(
            item["not_worse_on_common_exposure_axis"] for item in candidate_alert_comparison.values()
        )
        flow_not_worse = candidate["flow_average_precision"] >= baseline["flow_average_precision"]
        no_larger_cliff = (
            candidate["tie_profile"]["largest_tie_group_size"] <= baseline["tie_profile"]["largest_tie_group_size"]
        )
        alert_fpr_disclosed = all(
            isinstance(item.get("candidate_first_alert_actual_fpr"), float)
            and isinstance(item.get("baseline_first_alert_actual_fpr"), float)
            and item["candidate_first_alert_actual_fp"] <= item["common_integer_false_positive_budget"]
            and item["baseline_first_alert_actual_fp"] <= item["common_integer_false_positive_budget"]
            for item in candidate_alert_comparison.values()
        )
        criteria = {
            "strict_improvement_on_at_least_one_axis": bool(
                entity_ap_better or area_better or reachable_better or alert_better
            ),
            "no_detection_rate_loss_on_common_reachable_budgets": bool(not_worse_on_common_budgets),
            "no_first_alert_loss_on_common_fp_budget_and_exposure_axis": bool(first_alert_not_worse),
            "flow_average_precision_not_lower": bool(flow_not_worse),
            "no_larger_tie_cliff": bool(no_larger_cliff),
            "first_alert_actual_fpr_disclosed": bool(alert_fpr_disclosed),
            "improvement_not_nominal_only": bool(entity_ap_better or area_better or reachable_better or alert_better),
        }
        results[key] = {
            "display_name": arm["display_name"],
            "candidate_label": arm["candidate_label"],
            "baseline": baseline_key,
            "criteria": criteria,
            "passed": all(criteria.values()),
            "entity_average_precision_delta": candidate["entity_average_precision"]
            - baseline["entity_average_precision"],
            "normalized_area_delta": candidate["normalized_area_0_8_fpr"] - baseline["normalized_area_0_8_fpr"],
            "flow_average_precision_delta": candidate["flow_average_precision"] - baseline["flow_average_precision"],
            "largest_tie_group_size_delta": candidate["tie_profile"]["largest_tie_group_size"]
            - baseline["tie_profile"]["largest_tie_group_size"],
            "common_integer_fp_budget_terminal_readouts": candidate_common,
            "common_integer_fp_budget_first_alert_comparison": candidate_alert_comparison,
        }
    return results


def stage_seal(config: dict[str, Any], args: argparse.Namespace) -> None:
    output_root = existing_output_root(config, "source")
    units = load_units(output_root, "source")
    seal_path = output_root / "s0-seal.json"
    if seal_path.is_file():
        existing = load_json(seal_path)
        if existing.get("unit_identities") == {cell: units[cell].get("unit_identity") for cell in CELL_ORDER}:
            log("源年封印已存在且单元身份一致，幂等跳过")
            return
        raise StageError(
            f"源年封印已存在但单元身份不符：{seal_path}。重复封印会制造新的选择机会，拒绝覆盖。",
            EXIT_STAGE_PRECONDITION,
        )
    lesions = {cell: classify_lesion(config, units[cell]) for cell in CELL_ORDER}
    gates = {cell: evaluate_source_gate(config, units[cell]) for cell in CELL_ORDER}
    promotable = sorted(
        {arm_key for cell in CELL_ORDER for arm_key, item in gates[cell].items() if item["passed"]}
    )
    seal = {
        "schema_version": SEAL_SCHEMA_VERSION,
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "evidence_level": "zero_train_screening",
        "sealed_at_unix": time.time(),
        "config_sha256": sha256_file(Path(args.config).resolve()),
        "code_sha256": sha256_file(Path(__file__).resolve()),
        "unit_identities": {cell: units[cell]["unit_identity"] for cell in CELL_ORDER},
        "unit_curve_sha256": {cell: units[cell]["curve_artifact"]["sha256"] for cell in CELL_ORDER},
        "frozen_operators": {
            "probability_space": "s_P = mean_i sigmoid(z_i)，不裁剪",
            "logit_space": "s_L = sigmoid(mean_i z_i)，不裁剪",
            "max_control": "max_i sigmoid(z_i) = sigmoid(max_i z_i)",
            "frozen_power_mean_control": "(mean_i clip(sigmoid(z_i),1e-7,1)^p)^(1/p)，p 取自父封印",
        },
        "frozen_tie_rule": config["evaluation"]["tie_policy"],
        "frozen_budget_grid": config["evaluation"]["dr_fpr_grid"],
        "frozen_first_alert_axis": {
            "axis": config["evaluation"]["first_alert_axis"],
            "base": config["evaluation"]["exposure_index_base"],
            "order": config["evaluation"]["first_alert_exposure_order"],
        },
        "lesion_classification": lesions,
        "source_gate": gates,
        "promotable_arms": promotable,
        "verdict": "source_gate_passed" if promotable else "source_gate_rejected_all_arms",
        "next_action": (
            "四臂均未通过源年门；S0 完成根因排除，转入第一主候选（独立因果实体排序头）；"
            "不得添加无依据池化公式，也不得以 LSPR24 救回。"
            if not promotable
            else "存在源年可晋级臂；后续采用仍须按分级合同进入 S1，不得直接写入正文。"
        ),
        "target_year_arrays_read": 0,
        "target_evaluation_authorized": True,
    }
    atomic_json(seal_path, seal)
    write_status(output_root, "running", "seal", "源年封印完成，目标年描述性评价获授权", None)
    log(f"源年封印完成：裁决={seal['verdict']}，可晋级臂={promotable or '无'}")


# --------------------------------------------------------------------------------------
# 阶段：目标年与收尾
# --------------------------------------------------------------------------------------


def require_source_seal(config: dict[str, Any], config_path: Path | None = None) -> tuple[Path, dict[str, Any]]:
    output_root = existing_output_root(config, "source")
    seal_path = output_root / "s0-seal.json"
    if not seal_path.is_file():
        raise StageError(
            f"源年封印不存在：{seal_path}。按分级合同与统一合同 §5.4，"
            "必须先完成 `--stage source` 与 `--stage seal`，封印后才允许读取 LSPR24。",
            EXIT_STAGE_PRECONDITION,
        )
    seal = load_json(seal_path)
    if seal.get("schema_version") != SEAL_SCHEMA_VERSION or seal.get("run_id") != RUN_ID:
        raise StageError("源年封印模式或运行身份不符，拒绝读取目标年", EXIT_STAGE_PRECONDITION)
    if seal.get("target_evaluation_authorized") is not True or seal.get("target_year_arrays_read") != 0:
        raise StageError("源年封印未授权目标年评价，拒绝读取 LSPR24", EXIT_STAGE_PRECONDITION)
    if config_path is not None and (
        seal.get("config_sha256") != sha256_file(config_path.resolve())
        or seal.get("code_sha256") != sha256_file(Path(__file__).resolve())
    ):
        raise StageError("当前配置或代码摘要与源年封印不符，拒绝读目标年或收尾", EXIT_STAGE_PRECONDITION)
    units = load_units(output_root, "source")
    for cell in CELL_ORDER:
        if seal["unit_identities"].get(cell) != units[cell].get("unit_identity"):
            raise StageError(f"{cell} 的源年单元身份与封印不符，拒绝读取目标年", EXIT_STAGE_PRECONDITION)
    return output_root, seal


def stage_target(config: dict[str, Any], args: argparse.Namespace) -> None:
    require_source_seal(config, Path(args.config))
    run_year_stage(config, args, "target")


def collect_resource_summary(years: list[str], units: dict[str, dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "schema_version": "ch3-full-mlp-s0-compute-resource-v1",
        "run_id": RUN_ID,
        "wall_clock_limit": None,
        "years": {},
    }
    for year in years:
        forward_seconds = 0.0
        aggregation_seconds = 0.0
        peak_allocated = 0.0
        peak_reserved = 0.0
        scored_flows = 0
        for cell in CELL_ORDER:
            unit = units[year][cell]
            forward_seconds += unit["timing"]["forward_seconds_sum"]
            aggregation_seconds += unit["timing"]["aggregation_seconds"]
            for receipt in unit["forward_receipts"].values():
                peak_allocated = max(peak_allocated, receipt["peak_gpu_allocated_mib"])
                peak_reserved = max(peak_reserved, receipt["peak_gpu_reserved_mib"])
                scored_flows += receipt["scored_flows"]
        summary["years"][year] = {
            "pure_forward_seconds": forward_seconds,
            "aggregation_seconds": aggregation_seconds,
            "scored_flow_forwards": scored_flows,
            "flows_per_second": float(scored_flows / max(forward_seconds, 1e-9)),
            "peak_gpu_allocated_mib": peak_allocated,
            "peak_gpu_reserved_mib": peak_reserved,
        }
    try:
        import resource as resource_module

        summary["peak_process_rss_mib"] = float(resource_module.getrusage(resource_module.RUSAGE_SELF).ru_maxrss) / (
            1024.0 if sys.platform != "darwin" else 1024.0 * 1024.0
        )
    except ImportError:
        summary["peak_process_rss_mib"] = None
    return summary


def production_identity_paths(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Path]:
    return {
        "tool": Path(__file__).resolve(),
        "config": Path(args.config).resolve(),
        "launcher": TOOL_DIR.parent
        / "scripts/remote_launchers/run_ch3_full_mlp_s0_precision_aggregation_diagnostic_seed42_v1.sh",
        "tracking_module": SRC_ROOT / "flow_probe/tracking.py",
        "tag_aliases": tracking_alias_config_path(config).resolve(),
    }


def production_identity_receipts(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    receipts: dict[str, Any] = {}
    for name, path in production_identity_paths(config, args).items():
        if not path.is_file():
            raise StageError(f"SwanLab 生产身份文件缺失：{path}", EXIT_INPUT)
        receipts[name] = {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return receipts


def validate_swanlab_health_receipt(path: Path, attempt: int) -> dict[str, Any]:
    if not path.is_file():
        raise StageError(f"第 {attempt} 次 SwanLab 健康门收据不存在：{path}", EXIT_STAGE_PRECONDITION)
    receipt = load_json(path)
    if (
        receipt.get("schema_version") != "ch3-full-mlp-s0-swanlab-health-v2"
        or receipt.get("run_id") != RUN_ID
        or receipt.get("attempt") != attempt
        or receipt.get("passed") is not True
        or receipt.get("ping_exit_code") != 0
        or receipt.get("verify_exit_code") != 0
    ):
        raise StageError(f"第 {attempt} 次 SwanLab 健康门收据不合法", EXIT_STAGE_PRECONDITION)
    expected = {"ping": "swanlab-ping.log", "verify": "swanlab-verify.log"}
    if set(receipt.get("logs", {})) != set(expected):
        raise StageError("SwanLab 健康门日志集合不符", EXIT_STAGE_PRECONDITION)
    for key, filename in expected.items():
        log_path = path.parent / filename
        item = receipt["logs"][key]
        if (
            item.get("relative_path") != filename
            or not log_path.is_file()
            or log_path.stat().st_size != item.get("bytes")
            or sha256_file(log_path) != item.get("sha256")
        ):
            raise StageError(f"SwanLab 健康门日志漂移：{filename}", EXIT_STAGE_PRECONDITION)
    return receipt


def validate_swanlab_success(
    config: dict[str, Any], args: argparse.Namespace, output_root: Path, attempt: int
) -> dict[str, Any] | None:
    attempt_root = output_root / "swanlab-attempts" / f"attempt-{attempt}"
    success_path = attempt_root / "success-receipt.json"
    if not success_path.is_file():
        return None
    success = load_json(success_path)
    inflight = load_json(attempt_root / "inflight-receipt.json")
    tag_path = attempt_root / "swanlab-tag-receipt.json"
    health_path = attempt_root / "tracking-gate" / "health-receipt.json"
    if (
        success.get("schema_version") != "ch3-full-mlp-s0-swanlab-attempt-success-v1"
        or success.get("run_id") != RUN_ID
        or success.get("attempt") != attempt
        or success.get("completed") is not True
        or not isinstance(success.get("cloud_run_id"), str)
        or not success["cloud_run_id"]
        or inflight.get("cloud_run_id") != success["cloud_run_id"]
        or inflight.get("stage") != "finished"
        or success.get("tag_receipt_sha256") != sha256_file(tag_path)
        or success.get("health_receipt_sha256") != sha256_file(health_path)
        or success.get("production_identity") != production_identity_receipts(config, args)
    ):
        raise StageError(f"第 {attempt} 次 SwanLab 成功收据不完整或身份漂移", EXIT_STAGE_PRECONDITION)
    validate_swanlab_health_receipt(health_path, attempt)
    return success


def recover_completed_swanlab_publish(
    config: dict[str, Any], args: argparse.Namespace, output_root: Path
) -> dict[str, Any] | None:
    successes = [
        success
        for attempt in (1, 2)
        if (success := validate_swanlab_success(config, args, output_root, attempt)) is not None
    ]
    if len(successes) > 1:
        raise StageError("同一生产身份出现多个 SwanLab 成功运行，拒绝猜测封口", EXIT_STAGE_PRECONDITION)
    if not successes:
        return None
    success = successes[0]
    if args.swanlab_attempt != success["attempt"]:
        raise StageError("本地封口尝试编号与成功收据不一致", EXIT_STAGE_PRECONDITION)
    for number in (1, 2):
        root = output_root / "swanlab-attempts" / f"attempt-{number}"
        if number != success["attempt"] and (root / "inflight-receipt.json").is_file():
            raise StageError("成功收据之外仍有未知在途运行，拒绝本地封口", EXIT_STAGE_PRECONDITION)
    attempt_root = output_root / "swanlab-attempts" / f"attempt-{success['attempt']}"
    atomic_json(output_root / "swanlab-tag-receipt.json", load_json(attempt_root / "swanlab-tag-receipt.json"))
    atomic_json(output_root / "swanlab-receipt.json", success["swanlab_receipt"])
    return success["swanlab_receipt"]


def validate_new_swanlab_attempt(output_root: Path, attempt: int) -> Path:
    attempts_root = output_root / "swanlab-attempts"
    first_root = attempts_root / "attempt-1"
    second_root = attempts_root / "attempt-2"
    for number, root in ((1, first_root), (2, second_root)):
        if (root / "inflight-receipt.json").is_file() and not (root / "success-receipt.json").is_file():
            raise StageError(
                f"第 {number} 次 SwanLab 运行已初始化但云端终态未知，拒绝重复 init",
                EXIT_STAGE_PRECONDITION,
            )
    first_failure = first_root / "failure-receipt.json"
    if attempt == 1:
        if first_failure.is_file() or second_root.exists():
            raise StageError("首次 SwanLab 尝试已经留下终态证据，拒绝重复执行", EXIT_STAGE_PRECONDITION)
        return first_root
    if not first_failure.is_file():
        raise StageError("缺少首次零步 401 失败收据，禁止第二次 SwanLab 初始化", EXIT_STAGE_PRECONDITION)
    failure = load_json(first_failure)
    if (
        failure.get("attempt") != 1
        or failure.get("stage") != "swanlab-init"
        or failure.get("retryable_zero_step_init_401") is not True
        or failure.get("production_identity")
        != production_identity_receipts_from_attempt(first_root)
    ):
        raise StageError("首次失败不是可重试的零步初始化 401", EXIT_STAGE_PRECONDITION)
    if (second_root / "failure-receipt.json").is_file() or (second_root / "success-receipt.json").is_file():
        raise StageError("第二次 SwanLab 尝试已完成，禁止第三次初始化", EXIT_STAGE_PRECONDITION)
    return second_root


def production_identity_receipts_from_attempt(attempt_root: Path) -> dict[str, Any]:
    failure = load_json(attempt_root / "failure-receipt.json")
    identity = failure.get("production_identity")
    if not isinstance(identity, dict) or set(identity) != {
        "tool",
        "config",
        "launcher",
        "tracking_module",
        "tag_aliases",
    }:
        raise StageError("SwanLab 失败收据缺少生产身份", EXIT_STAGE_PRECONDITION)
    for name, item in identity.items():
        path = Path(str(item.get("path", "")))
        if (
            not path.is_file()
            or path.stat().st_size != item.get("bytes")
            or sha256_file(path) != item.get("sha256")
        ):
            raise StageError(f"SwanLab 首次失败后的生产身份漂移：{name}", EXIT_STAGE_PRECONDITION)
    return identity


def publish_tracking(config: dict[str, Any], args: argparse.Namespace, output_root: Path, results: dict[str, Any]) -> None:
    tracking = config["tracking"]
    if args.authorized_swanlab_workspace is None or args.authorized_swanlab_project is None:
        raise StageError(
            "缺少跟踪授权参数：请通过 `--authorized-swanlab-workspace` 与 "
            "`--authorized-swanlab-project` 传入本轮授权的工作区与项目；"
            "工具不会凭配置自行创建在线运行。",
            EXIT_STAGE_PRECONDITION,
        )
    if (
        args.authorized_swanlab_workspace != tracking["workspace"]
        or args.authorized_swanlab_project != tracking["project"]
    ):
        raise StageError("跟踪目的地与本轮授权不一致，拒绝创建在线运行", EXIT_STAGE_PRECONDITION)
    completed = recover_completed_swanlab_publish(config, args, output_root)
    if completed is not None:
        log("已有完整合法 SwanLab 成功收据，仅恢复本地封口")
        return
    attempt = args.swanlab_attempt
    attempt_root = validate_new_swanlab_attempt(output_root, attempt)
    health_path = Path(args.swanlab_health_receipt).resolve() if args.swanlab_health_receipt else None
    expected_health_path = (attempt_root / "tracking-gate" / "health-receipt.json").resolve()
    if health_path != expected_health_path:
        raise StageError("SwanLab 健康门收据路径与尝试身份不符", EXIT_STAGE_PRECONDITION)
    validate_swanlab_health_receipt(expected_health_path, attempt)
    try:
        from flow_probe.tracking import initialize_swanlab_run
    except ImportError as error:
        raise StageError("无法导入中央 SwanLab 初始化接口", EXIT_DEPENDENCY) from error
    tracking_config = {
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "parent_run_id": PARENT_RUN_ID,
        "evidence_level": "zero_train_screening",
        "training_runs": 0,
        "parameter_updates": 0,
        "config_sha256": results["identity"]["config_sha256"],
        "code_sha256": results["identity"]["code_sha256"],
    }
    values: dict[str, float] = {}
    for year, table in results["years"].items():
        for cell in CELL_ORDER:
            for arm in config["arms"]:
                branch = table[cell]["branches"][arm["key"]]
                values[f"{year}/{cell}/{arm['key']}/entity_ap"] = branch["entity_average_precision"]
                values[f"{year}/{cell}/{arm['key']}/area_0_8"] = branch["normalized_area_0_8_fpr"]
                values[f"{year}/{cell}/{arm['key']}/largest_tie_group"] = float(
                    branch["tie_profile"]["largest_tie_group_size"]
                )
                for budget, readout in branch["actual_reachable_dr_at_fpr"].items():
                    values[f"{year}/{cell}/{arm['key']}/actual_dr_{budget}"] = readout["detection_rate"]
                    values[f"{year}/{cell}/{arm['key']}/actual_fpr_{budget}"] = readout["actual_reachable_fpr"]
    attempt_root.mkdir(parents=True, exist_ok=True)
    try:
        swanlab, run, tag_receipt = initialize_swanlab_run(
            tracking_destination(config),
            alias_config_path=tracking_alias_config_path(config),
            expected_alias_config_sha256=tracking["alias_config_sha256"],
            config=tracking_config,
            log_dir=attempt_root / "swanlog",
            tag_receipt_path=attempt_root / "swanlab-tag-receipt.json",
            authorized_workspace=args.authorized_swanlab_workspace,
            authorized_project=args.authorized_swanlab_project,
        )
    except ModuleNotFoundError as error:
        raise StageError("缺少 swanlab：正式 GPU 实验需要在线跟踪，请在服务器环境中运行", EXIT_DEPENDENCY) from error
    except BaseException as error:
        retryable = attempt == 1 and "401" in str(error)
        atomic_json(
            attempt_root / "failure-receipt.json",
            {
                "schema_version": "ch3-full-mlp-s0-swanlab-attempt-failure-v1",
                "run_id": RUN_ID,
                "attempt": attempt,
                "stage": "swanlab-init",
                "zero_step": True,
                "retryable_zero_step_init_401": retryable,
                "error_type": type(error).__name__,
                "error": str(error),
                "production_identity": production_identity_receipts(config, args),
            },
        )
        if retryable:
            raise StageError(
                "首次 SwanLab 零步初始化返回 401；已保留证据，允许启动器以新进程重试一次",
                EXIT_RETRYABLE_SWANLAB_INIT_401,
            ) from error
        raise StageError(f"SwanLab 中央初始化合同失败：{error}", EXIT_STAGE_PRECONDITION) from error
    atomic_json(
        attempt_root / "inflight-receipt.json",
        {
            "schema_version": "ch3-full-mlp-s0-swanlab-inflight-v1",
            "run_id": RUN_ID,
            "attempt": attempt,
            "cloud_run_id": str(run.id),
            "stage": "initialized",
            "production_identity": production_identity_receipts(config, args),
        },
    )
    try:
        swanlab.log(values, step=0)
        inflight = load_json(attempt_root / "inflight-receipt.json")
        inflight["stage"] = "logged"
        atomic_json(attempt_root / "inflight-receipt.json", inflight)
        swanlab.finish()
    except BaseException as error:
        atomic_json(
            attempt_root / "failure-receipt.json",
            {
                "schema_version": "ch3-full-mlp-s0-swanlab-attempt-failure-v1",
                "run_id": RUN_ID,
                "attempt": attempt,
                "stage": "initialized-or-later",
                "zero_step": False,
                "retryable_zero_step_init_401": False,
                "error_type": type(error).__name__,
                "error": str(error),
                "cloud_run_id": str(run.id),
                "production_identity": production_identity_receipts(config, args),
            },
        )
        raise StageError("SwanLab 初始化后的云端终态未知，拒绝自动重试", EXIT_STAGE_PRECONDITION) from error
    inflight = load_json(attempt_root / "inflight-receipt.json")
    inflight["stage"] = "finished"
    atomic_json(attempt_root / "inflight-receipt.json", inflight)
    attempt_tag_receipt_sha256 = sha256_file(attempt_root / "swanlab-tag-receipt.json")
    swanlab_receipt = {
            "schema_version": "ch3-full-mlp-s0-swanlab-v1",
            "run_id": RUN_ID,
            "display_name": DISPLAY_NAME,
            "workspace": tracking["workspace"],
            "project": tracking["project"],
            "group": tracking["group"],
            "requested_tags": tracking["tags"],
            "effective_tags": tag_receipt["effective_tags"],
            "tag_contract_sha256": tag_receipt["contract_sha256"],
            "tag_receipt_sha256": attempt_tag_receipt_sha256,
            "alias_config_sha256": tag_receipt["alias_config_sha256"],
            "central_api_commit": tracking["central_api_commit"],
            "mode": tracking["mode"],
            "aggregate_only": True,
            "logged_metric_count": len(values),
            "per_flow_scores_logged": False,
            "per_entity_scores_logged": False,
            "completed": True,
            "attempt": attempt,
            "cloud_run_id": str(run.id),
        }
    atomic_json(
        attempt_root / "success-receipt.json",
        {
            "schema_version": "ch3-full-mlp-s0-swanlab-attempt-success-v1",
            "run_id": RUN_ID,
            "attempt": attempt,
            "cloud_run_id": str(run.id),
            "completed": True,
            "health_receipt_sha256": sha256_file(expected_health_path),
            "tag_receipt_sha256": attempt_tag_receipt_sha256,
            "production_identity": production_identity_receipts(config, args),
            "swanlab_receipt": swanlab_receipt,
        },
    )
    recover_completed_swanlab_publish(config, args, output_root)


def build_manifest(config: dict[str, Any], args: argparse.Namespace, output_root: Path) -> None:
    files: dict[str, Any] = {}
    for path in sorted(output_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(output_root).as_posix()
        if relative == "manifest.json":
            continue
        lowered = relative.lower()
        if any(token in lowered for token in FORBIDDEN_ARTIFACT_TOKENS):
            raise StageError(f"运行根出现禁止语义的制品：{relative}，拒绝生成清单", EXIT_INPUT)
        files[relative] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    atomic_json(
        output_root / "manifest.json",
        {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "run_id": RUN_ID,
            "display_name": DISPLAY_NAME,
            "complete": True,
            "training_runs": 0,
            "parameter_updates": 0,
            "new_checkpoints_written": 0,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "per_entity_first_alert_persisted": False,
            "exposure_matrix_persisted": False,
            "complete_negative_tie_groups": True,
            "time_delay_available": False,
            "forbidden_artifacts_absent": True,
            "files": files,
            "production_identity": production_identity_receipts(config, args),
        },
    )


def stage_finalize(config: dict[str, Any], args: argparse.Namespace) -> None:
    output_root, seal = require_source_seal(config, Path(args.config))
    units = {"source": load_units(output_root, "source")}
    target_receipt_path = output_root / "input-validation-receipt-target.json"
    if not target_receipt_path.is_file():
        raise StageError("目标年输入收据不存在，不得在无 target 单元时标记 complete", EXIT_STAGE_PRECONDITION)
    target_inputs = load_json(target_receipt_path)
    if target_inputs.get("year") != "target":
        raise StageError("目标年输入收据年度身份不符", EXIT_STAGE_PRECONDITION)
    units["target"] = load_units(output_root, "target")
    years = ["source", "target"]
    config_sha = sha256_file(Path(args.config).resolve())
    code_sha = sha256_file(Path(__file__).resolve())
    for cell in CELL_ORDER:
        target_unit = units["target"][cell]
        source_unit = units["source"][cell]
        expected_identity = unit_identity(config, "target", cell, target_inputs, config_sha, code_sha)
        if target_unit.get("unit_identity") != expected_identity:
            raise StageError(f"target/{cell} 单元身份与目标年输入收据不符", EXIT_STAGE_PRECONDITION)
        if (
            target_unit.get("target_year_arrays_read") != 1
            or target_unit["checkpoint"]["sha256"] != source_unit["checkpoint"]["sha256"]
            or target_unit["model_receipt"]["weights_sha256"]
            != source_unit["model_receipt"]["weights_sha256"]
            or seal["unit_identities"].get(cell) != source_unit.get("unit_identity")
        ):
            raise StageError(f"target/{cell} 与源年封印的检查点或权重身份不一致", EXIT_STAGE_PRECONDITION)
    precision_receipt = {
        "schema_version": "ch3-full-mlp-s0-precision-receipt-v1",
        "run_id": RUN_ID,
        "bf16_profile_id": config["precision"]["bf16_profile_id"],
        "fp32_profile_id": config["precision"]["fp32_profile_id"],
        "fp32_profile_receipt_reason": config["precision"]["fp32_profile_receipt_reason"],
        "units": {
            year: {
                cell: {
                    "weights_sha256": units[year][cell]["model_receipt"]["weights_sha256"],
                    "state_dict_dtypes": units[year][cell]["model_receipt"]["state_dict_dtypes"],
                    "forward_output_dtype": {
                        name: receipt["forward_output_dtype"]
                        for name, receipt in units[year][cell]["forward_receipts"].items()
                    },
                    "autocast_enabled": {
                        name: receipt["autocast_enabled"]
                        for name, receipt in units[year][cell]["forward_receipts"].items()
                    },
                }
                for cell in CELL_ORDER
            }
            for year in years
        },
    }
    atomic_json(output_root / "precision-receipt.json", precision_receipt)
    atomic_json(output_root / "compute-resource-receipt.json", collect_resource_summary(years, units))

    if args.resource_receipt:
        receipt_path = Path(args.resource_receipt)
        if not receipt_path.is_file():
            raise StageError(f"启动器资源收据不存在：{receipt_path}", EXIT_INPUT)
        launcher_receipt = load_json(receipt_path)
        if launcher_receipt.get("run_id") != RUN_ID:
            raise StageError("启动器资源收据运行身份不符", EXIT_INPUT)

    results = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "evidence_level": "zero_train_screening",
        "identity": {
            "config_sha256": sha256_file(Path(args.config).resolve()),
            "code_sha256": sha256_file(Path(__file__).resolve()),
            "parent_run_id": PARENT_RUN_ID,
        },
        "arms": [
            {"key": arm["key"], "display_name": arm["display_name"], "candidate_label": arm["candidate_label"]}
            for arm in config["arms"]
        ],
        "controls": [{"key": item["key"], "display_name": item["display_name"]} for item in config["controls"]],
        "source_seal": seal,
        "years": units,
        "years_evaluated": years,
        "isolation": {
            **config["isolation"],
            "target_year_units_present": "target" in units,
            "target_evaluation_is_descriptive_only": True,
            "target_used_for_selection": False,
        },
        "evidence_statement": (
            "本结果等级为零训练筛选：只能用于精度/聚合病灶归因与是否进入 S1 的判断，"
            "不构成机制有效性结论，也不得写入论文正式结果。"
        ),
    }
    atomic_json(output_root / "aggregate-results.json", results)
    publish_tracking(config, args, output_root, results)
    write_status(output_root, "complete", "finalize", "S0 诊断制品齐备", 0)
    build_manifest(config, args, output_root)
    log("收尾完成：聚合结果、精度收据、资源收据、跟踪收据与清单已生成")


# --------------------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="全容量多层感知机 S0 双精度×双聚合空间零训练诊断")
    parser.add_argument("--config", required=True, help="冻结 JSON 配置")
    parser.add_argument("--validate-config", action="store_true", help="只核验配置与精度合同后退出")
    parser.add_argument("--stage", choices=STAGES, help="执行阶段：source/seal/target/finalize")
    parser.add_argument("--resume", action="store_true", help="跳过身份一致的已完成单元")
    parser.add_argument("--resource-receipt", help="启动器资源准入收据路径")
    parser.add_argument("--authorized-swanlab-workspace", help="本轮授权的跟踪工作区")
    parser.add_argument("--authorized-swanlab-project", help="本轮授权的跟踪项目")
    parser.add_argument("--swanlab-attempt", type=int, choices=(1, 2), default=1, help="最终发布尝试编号")
    parser.add_argument("--swanlab-health-receipt", help="本次尝试的 ping/verify 健康门收据")
    return parser.parse_args()


def dispatch(config: dict[str, Any], args: argparse.Namespace) -> None:
    if args.stage == "source":
        run_year_stage(config, args, "source")
    elif args.stage == "seal":
        stage_seal(config, args)
    elif args.stage == "target":
        stage_target(config, args)
    elif args.stage == "finalize":
        stage_finalize(config, args)
    else:
        raise StageError("必须指定 `--stage`（source/seal/target/finalize）或 `--validate-config`", EXIT_CONFIG)


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    if not config_path.is_file():
        print(f"配置不存在：{config_path}", file=sys.stderr, flush=True)
        return EXIT_CONFIG
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"配置解析失败：{config_path}：{error}", file=sys.stderr, flush=True)
        return EXIT_CONFIG
    try:
        validate_config(config)
    except StageError as error:
        print(str(error), file=sys.stderr, flush=True)
        return error.exit_code
    if args.validate_config:
        print("配置核验通过", flush=True)
        return EXIT_OK
    try:
        dispatch(config, args)
    except StageError as error:
        print(f"阶段 {args.stage} 失败：{error}", file=sys.stderr, flush=True)
        output_root = Path(config["paths"]["output_root"])
        if output_root.is_dir():
            write_status(output_root, "failed", args.stage or "unknown", str(error), error.exit_code)
        return error.exit_code
    except Exception as error:  # noqa: BLE001 - 顶层兜底，保留原始堆栈到日志
        traceback.print_exc()
        print(f"阶段 {args.stage} 出现未预期错误：{error}", file=sys.stderr, flush=True)
        output_root = Path(config["paths"]["output_root"])
        if output_root.is_dir():
            write_status(output_root, "failed", args.stage or "unknown", str(error), EXIT_UNEXPECTED)
        return EXIT_UNEXPECTED
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
