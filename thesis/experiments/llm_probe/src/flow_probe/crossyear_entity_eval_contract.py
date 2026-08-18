"""跨年度实体级评价与决策层适应 Q0：冻结合同、预注册判据与实体聚合。

本模块只保存**在看到目标年度结果之前**冻结的定义：实体键、聚合函数、实体标签、
预注册门禁阈值、封存与隔离断言。任何依赖结果的调整都属于违规，禁止修改本文件的
`PREREGISTERED` 与实体键定义。

冻结合同：`.Codex/docs/RWKV/candidates/任务方案册-跨年度实体级评价与决策层适应.md`
实施计划：`.Codex/docs/RWKV/2026-08-12-跨年度实体级评价Q0实施计划.md`
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

logger = logging.getLogger(__name__)

RUN_NAME = "crossyear-entity-level-eval-q0-seed42-v1"
CONTRACT_VERSION = "crossyear-entity-eval-contract-v1"

ROLES: tuple[str, ...] = ("source-train", "source-validation", "target-prefix", "target-development")
LABELLED_ROLES: tuple[str, ...] = ("source-train", "source-validation", "target-development")

#: 共同输入定义与既有共享 XGBoost 锚完全一致，保证 `B0` 与锚可比。
FEATURE_DEFINITION = "x_value(77)+x_missing(77)+log1p(max(delta_t_us,0))"
FEATURE_FIELD_COUNT = 77
FEATURE_DIMENSION = 2 * FEATURE_FIELD_COUNT + 1

#: 实体键：冻结有界缓存中唯一可在两个年度一致构造的受保护实体标识。
#: 方案册 §2.1 首选源 IP，但源 IP 未进入冻结缓存（缓存只保留密钥化的 2-IP 分组指纹）。
#: 因此本运行采用方案册明确列出的**预注册备选**：`2-IP` 无向密钥化分组。
#: 两种实体键不得混入同一比较表。
ENTITY_KEY_NAME = "group_key_ref_2ip_undirected_keyed"
ENTITY_KEY_COLUMN = "group_key_ref"
ENTITY_KEY_BYTES = 32
ENTITY_KEY_RATIONALE = (
    "冻结有界缓存 lspr23-lspr24-bounded-quick-q0-v1 的四个角色均只保存 "
    "group_key_ref(fixed_size_binary[32])，不含原始源 IP；方案册 §2.1 已把 2-IP "
    "无向密钥化分组登记为预注册备选实体键，故本运行使用该备选并禁止与源 IP 口径混排。"
)

#: 预注册判据。写入 `config.json` 后不得修改。
PREREGISTERED: Mapping[str, Any] = {
    "alignment_gate": {"flow_ap_target": 0.2416, "tolerance": 0.05},
    "main_gate": {"entity_fpr_max": 0.04, "entity_recall_pass": 0.50, "entity_recall_reject": 0.20},
    "aggregation_n": [1, 5, 10, 100],
    "seeds": [42, 43, 44],
    "bootstrap": {"unit": "entity", "paired": True, "n": 1000},
    "screening_only": True,
    "formal_paper_evidence": False,
    "final_accessed": False,
}

#: `B0` 复现 Dijk 2026 §5.6 的 XGBoost 配置（PDF 第 24 页）。
DIJK_XGBOOST_PARAMS: Mapping[str, Any] = {
    "learning_rate": 0.05,
    "max_depth": 8,
    "n_estimators": 800,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "min_child_weight": 1.0,
    "max_bin": 256,
    "objective": "binary:logistic",
    "tree_method": "hist",
    "eval_metric": "logloss",
}

#: Dijk 2026 表 8 报告的 LSPR24 `OP` 构造诱导阳性率，仅作协议差异审计的参照量。
DIJK_LSPR24_OP_POSITIVE_RATE = 0.0707

VARIANTS: tuple[str, ...] = ("B0", "B1", "B2", "M1", "M1+B1", "M3-同期", "M3-冻结")


class EntityEvalError(RuntimeError):
    """输入、切分或运行状态不符合跨年度实体级评价冻结合同。"""


# --------------------------------------------------------------------------------------
# 基础工具
# --------------------------------------------------------------------------------------


def read_json(path: Path) -> Mapping[str, Any]:
    """读取 JSON 顶层对象。"""
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EntityEvalError(f"JSON 顶层必须是对象：{path}")
    return value


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    """稳定顺序写出 JSON，便于哈希与逐字段核对。"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    """流式计算文件 SHA-256，避免整文件驻留。"""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_array(array: np.ndarray) -> str:
    """对连续内存数组按字节求 SHA-256。"""
    contiguous = np.ascontiguousarray(array)
    return hashlib.sha256(contiguous.tobytes()).hexdigest()


# --------------------------------------------------------------------------------------
# 内存观测：容器内只允许 cgroup 与 /proc/self/status
# --------------------------------------------------------------------------------------


def cgroup_memory_gib() -> dict[str, float | None]:
    """读取容器 cgroup 内存上限与用量。禁用 free/psutil//proc/meminfo（宿主机数值）。"""
    candidates = (
        (Path("/sys/fs/cgroup/memory.max"), Path("/sys/fs/cgroup/memory.current")),
        (Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"), Path("/sys/fs/cgroup/memory/memory.usage_in_bytes")),
    )
    for limit_path, usage_path in candidates:
        if not limit_path.is_file():
            continue
        try:
            raw_limit = limit_path.read_text(encoding="utf-8").strip()
            raw_usage = usage_path.read_text(encoding="utf-8").strip() if usage_path.is_file() else "0"
        except OSError as error:
            logger.warning("读取 cgroup 内存失败：%s", error)
            return {"limit_gib": None, "used_gib": None, "available_gib": None}
        if raw_limit == "max":
            return {"limit_gib": None, "used_gib": None, "available_gib": None}
        limit = int(raw_limit) / 1073741824.0
        used = int(raw_usage) / 1073741824.0
        return {"limit_gib": round(limit, 3), "used_gib": round(used, 3), "available_gib": round(limit - used, 3)}
    return {"limit_gib": None, "used_gib": None, "available_gib": None}


def vmrss_gib() -> float | None:
    """读取本进程 VmRSS（GiB）。"""
    status = Path("/proc/self/status")
    if not status.is_file():
        return None
    try:
        for line in status.read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return round(int(line.split()[1]) / 1048576.0, 3)
    except (OSError, ValueError, IndexError) as error:
        logger.warning("读取 VmRSS 失败：%s", error)
    return None


def memory_snapshot(stage: str) -> dict[str, Any]:
    """阶段级内存快照，写入日志与收据。"""
    snapshot = {"stage": stage, "vmrss_gib": vmrss_gib(), **cgroup_memory_gib()}
    logger.info(
        "[内存] 阶段=%s VmRSS=%s GiB cgroup 可用=%s GiB",
        stage,
        snapshot["vmrss_gib"],
        snapshot["available_gib"],
    )
    return snapshot


# --------------------------------------------------------------------------------------
# 标签、实体键与聚合
# --------------------------------------------------------------------------------------


def binary_label_mask(labels: np.ndarray) -> np.ndarray:
    """强制 `np.isin(label, (0, 1))` 过滤（登记册 §2.1：`label=-1` 占 60.4075%）。"""
    array = np.asarray(labels)
    if array.ndim != 1:
        raise EntityEvalError("标签必须是一维数组")
    return np.isin(array, (0, 1))


def entity_codes(raw_keys: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """把 32 字节实体键映射为紧凑整数码。

    实体键**只用于分组**：本函数的输出仅进入聚合、分簇自助与标签统计，
    不得编码、计数、分桶或作为模型特征。

    Args:
        raw_keys: 形状 `(n, 32)` 的 uint8 数组，或长度 `n` 的 bytes 序列。

    Returns:
        `(codes, unique_keys)`，`codes` 为 int64 组码，`unique_keys` 为去重后的键。
    """
    array = np.asarray(raw_keys)
    if array.ndim != 2 or array.shape[1] != ENTITY_KEY_BYTES or array.dtype != np.uint8:
        raise EntityEvalError(f"实体键必须是 (n, {ENTITY_KEY_BYTES}) 的 uint8 数组")
    # 逐字节精确去重：不做 |S32 视图，避免尾部 0x00 被截断而误合并两个不同实体键。
    unique, inverse = np.unique(np.ascontiguousarray(array), axis=0, return_inverse=True)
    codes = np.asarray(inverse).reshape(-1).astype(np.int64)
    if codes.shape[0] != array.shape[0]:
        raise EntityEvalError("实体码长度与输入行数不一致")
    return codes, unique


def entity_labels(codes: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """实体级标签：实体内存在任一恶意流即为正。仅用于离线评价。"""
    codes = np.asarray(codes, dtype=np.int64)
    labels = np.asarray(labels, dtype=np.uint8)
    if codes.shape != labels.shape:
        raise EntityEvalError("实体码与标签长度不一致")
    count = int(codes.max()) + 1 if codes.size else 0
    result = np.zeros(count, dtype=np.uint8)
    np.maximum.at(result, codes, labels)
    return np.arange(count, dtype=np.int64), result


def aggregate_entity_scores(codes: np.ndarray, scores: np.ndarray, n: int) -> np.ndarray:
    """实体聚合 `S_e^(n) = 第 n 大的 {s_f : f ∈ e}`。

    实体内有效流少于 `n` 时取该实体最小分数（即全部流都低于第 `n` 名的保守取值）。
    `n=1` 即 max 聚合。
    """
    if n < 1:
        raise EntityEvalError("聚合阶数 n 必须为正整数")
    codes = np.asarray(codes, dtype=np.int64)
    scores = np.asarray(scores, dtype=np.float64)
    if codes.shape != scores.shape:
        raise EntityEvalError("实体码与分数长度不一致")
    count = int(codes.max()) + 1 if codes.size else 0
    order = np.lexsort((-scores, codes))
    sorted_codes = codes[order]
    sorted_scores = scores[order]
    starts = np.searchsorted(sorted_codes, np.arange(count), side="left")
    ends = np.searchsorted(sorted_codes, np.arange(count), side="right")
    sizes = ends - starts
    take = starts + np.minimum(sizes - 1, n - 1)
    result = np.full(count, -np.inf, dtype=np.float64)
    non_empty = sizes > 0
    result[non_empty] = sorted_scores[take[non_empty]]
    return result


def entity_first_positive_time(
    codes: np.ndarray, labels: np.ndarray, available_ns: np.ndarray, entity_count: int
) -> np.ndarray:
    """每个实体首个恶意流的可观测时间（纳秒）；无恶意流时为 -1。"""
    codes = np.asarray(codes, dtype=np.int64)
    labels = np.asarray(labels, dtype=np.uint8)
    times = np.asarray(available_ns, dtype=np.int64)
    result = np.full(entity_count, np.iinfo(np.int64).max, dtype=np.int64)
    mask = labels == 1
    np.minimum.at(result, codes[mask], times[mask])
    result[result == np.iinfo(np.int64).max] = -1
    return result


def entity_first_alert_time(
    codes: np.ndarray, scores: np.ndarray, available_ns: np.ndarray, threshold: float, entity_count: int
) -> np.ndarray:
    """每个实体首次越过阈值的时间（纳秒）；未越界时为 -1。"""
    codes = np.asarray(codes, dtype=np.int64)
    scores = np.asarray(scores, dtype=np.float64)
    times = np.asarray(available_ns, dtype=np.int64)
    result = np.full(entity_count, np.iinfo(np.int64).max, dtype=np.int64)
    mask = scores >= threshold
    np.minimum.at(result, codes[mask], times[mask])
    result[result == np.iinfo(np.int64).max] = -1
    return result


# --------------------------------------------------------------------------------------
# 封存与隔离断言
# --------------------------------------------------------------------------------------


def seal_array(path: Path, array: np.ndarray, *, kind: str) -> dict[str, Any]:
    """落盘并封存分数数组。封存后才允许连接目标开发标签。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, array, allow_pickle=False)
    return {
        "kind": kind,
        "path": str(path),
        "row_count": int(array.shape[0]),
        "dtype": str(array.dtype),
        "array_sha256": sha256_array(array),
        "file_sha256": sha256_file(path),
    }


def assert_no_final_region(
    *,
    consumed_paths: Iterable[Path],
    max_available_ns: int,
    target_final_cut_ns: int,
    dataset_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """机械断言运行未触及 LSPR24 最后 20% 最终封存区。

    三重检查：路径不含 final 角色、消费到的最大可观测时间严格早于最终切点、
    数据集收据自身声明 `final_accessed=false` 且无 final 制品登记。
    """
    offending = [str(p) for p in consumed_paths if "final" in Path(p).name.lower() or "role=target-final" in str(p)]
    if offending:
        raise EntityEvalError(f"运行触及最终封存区路径：{offending}")
    if int(max_available_ns) >= int(target_final_cut_ns):
        raise EntityEvalError(
            f"消费数据的最大 available_ns={max_available_ns} 未严格早于最终切点 {target_final_cut_ns}"
        )
    if dataset_manifest.get("final_accessed") is not False:
        raise EntityEvalError("数据集收据未声明 final_accessed=false")
    for key in ("final_feature_artifacts", "final_label_artifacts", "final_member_artifacts", "final_specific_statistics"):
        if dataset_manifest.get(key):
            raise EntityEvalError(f"数据集收据登记了最终区制品：{key}")
    return {
        "final_accessed": False,
        "max_consumed_available_ns": int(max_available_ns),
        "target_final_cut_ns": int(target_final_cut_ns),
        "margin_seconds": (int(target_final_cut_ns) - int(max_available_ns)) / 1e9,
        "checked_paths": [str(p) for p in consumed_paths],
    }


def assert_entity_key_not_in_features(feature_matrix: np.ndarray, definition: str) -> None:
    """断言实体键未进入模型输入：维度与定义必须与冻结的 155 维共同输入完全一致。"""
    if feature_matrix.ndim != 2 or feature_matrix.shape[1] != FEATURE_DIMENSION:
        raise EntityEvalError(f"共同输入必须是 {FEATURE_DIMENSION} 维，实际 {feature_matrix.shape}")
    if definition != FEATURE_DEFINITION:
        raise EntityEvalError(f"共同输入定义漂移：{definition}")


def alignment_gate_decision(flow_ap: float) -> dict[str, Any]:
    """协议对齐门：`B0` 的跨年度逐流 AP 必须落在 0.2416 ± 0.05。"""
    target = float(PREREGISTERED["alignment_gate"]["flow_ap_target"])
    tolerance = float(PREREGISTERED["alignment_gate"]["tolerance"])
    lower, upper = target - tolerance, target + tolerance
    passed = bool(lower <= float(flow_ap) <= upper)
    return {
        "flow_ap": float(flow_ap),
        "target": target,
        "tolerance": tolerance,
        "interval": [lower, upper],
        "passed": passed,
        "action": "继续阶段二" if passed else "停止，先做协议差异审计，不进入 M1/M2/M3",
    }


def main_gate_decision(entity_recall: float) -> dict[str, Any]:
    """主门禁：≤4% 实体 FPR 下的实体级召回。"""
    gate = PREREGISTERED["main_gate"]
    recall = float(entity_recall)
    if recall >= float(gate["entity_recall_pass"]):
        verdict = "方向成立：决策粒度层有效"
    elif recall < float(gate["entity_recall_reject"]):
        verdict = "方向作废：失效在表示层，Gehri 与 Känzig 机制均不可迁移"
    else:
        verdict = "部分有效：须报告并缩小主张"
    return {"entity_recall": recall, "thresholds": dict(gate), "verdict": verdict}


def frozen_config(extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """产出写入 `config.json` 的冻结配置。"""
    config: dict[str, Any] = {
        "run_name": RUN_NAME,
        "contract_version": CONTRACT_VERSION,
        "research_route": "RWKV",
        "preregistered": dict(PREREGISTERED),
        "entity_key": {
            "name": ENTITY_KEY_NAME,
            "column": ENTITY_KEY_COLUMN,
            "bytes": ENTITY_KEY_BYTES,
            "rationale": ENTITY_KEY_RATIONALE,
            "used_for": "分组、聚合、分簇自助与实体标签统计",
            "never_used_for": "特征、编码、计数、分桶、阈值选择",
        },
        "features": {"definition": FEATURE_DEFINITION, "dimension": FEATURE_DIMENSION},
        "b0_xgboost": dict(DIJK_XGBOOST_PARAMS),
        "variants": list(VARIANTS),
        "swanlab": {"enabled": False, "reason": "本轮用户未授权 SwanLab 目的地，按局部规则不上报"},
    }
    if extra:
        config.update(dict(extra))
    return config


def variant_slug(variant: str) -> str:
    """变体名到文件系统安全的目录名（保留可读展示名）。"""
    mapping = {"M1+B1": "M1-plus-B1", "M3-同期": "M3-concurrent-calibration", "M3-冻结": "M3-frozen-transfer"}
    return mapping.get(variant, variant)


def describe_variants() -> Sequence[Mapping[str, str]]:
    """变体展示名与机制说明，供日志、汇总表与配置同时使用。"""
    return (
        {"key": "B0", "display": "逐流XGBoost-Dijk配置复现", "role": "协议对齐锚点"},
        {"key": "B1", "display": "逐流XGBoost+实体max聚合", "role": "决策粒度单独效应"},
        {"key": "B2", "display": "逐流XGBoost+实体第n大聚合", "role": "聚合深度敏感性"},
        {"key": "M1", "display": "时间无关特征筛选-逐流", "role": "特征筛选单独效应"},
        {"key": "M1+B1", "display": "时间无关特征筛选+实体max聚合", "role": "组合增益是否可加"},
        {"key": "M3-同期", "display": "组合方案+同期标定阈值", "role": "上界口径"},
        {"key": "M3-冻结", "display": "组合方案+前缀冻结阈值迁移", "role": "可部署口径，必须报告"},
    )
