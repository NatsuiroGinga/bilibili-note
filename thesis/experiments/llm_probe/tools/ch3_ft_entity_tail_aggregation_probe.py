#!/usr/bin/env python3
"""实体内尾部聚合（经验 CVaR_α，ATk 形式）的源年零训练重聚合诊断。

问题：把实体分数从「实体内取最大值」改成「实体内 top-⌈α·m⌉ 均值」后，
LSPR23 验证集上的实体 AP 相对 max 聚合有没有改善？

做法：加载 C00 已选检查点，对源验证集做一次前向，在内存里按 α 网格重聚合，
只落盘标量指标。零训练、零 LSPR24 读取（``target_reads = 0``）。

硬约束（与仓库规则一致）：
- 不持久化逐流分数、标签或实体 ID 数组，α 网格全部在内存里算完；
- 复用 ``ch3_ft_c00_dual_selection`` 的数据加载、切分、模型构造与前向函数，
  本文件不重写数据管线，也不修改被复用的文件；
- max 基线同时用「``validation_metrics`` 原函数」和「本文件的向量化 top-k 在 k≡1」
  两条路径算出，两者必须逐位一致，这是口径正确性的自检；
- 该运行是 ``screening_only`` 级诊断：不创建 SwanLab 运行，不创建正式运行身份。
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import shutil
import sys
import time
from pathlib import Path
from typing import Any


TOOL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOL_DIR.parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch3_ft_c00_dual_selection as dual  # noqa: E402  复用其配置、数据、模型与前向

LOGGER = logging.getLogger("ch3_ft_entity_tail_aggregation_probe")

PROBE_SCHEMA_VERSION = "ch3-ft-entity-tail-aggregation-probe-v1"

# α 网格：任务简报给定的敏感性扫描网格，不是冻结的科研阈值。用途是判断
# 「实体内尾部聚合方向是否存在信号」，不进入任何模型、损失或阈值配置；
# 因此不触发魔法数字门禁的冻结登记，只在收据里记录用途与来源。
DEFAULT_ALPHA_GRID = (0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0)

# 按实体有效流数 m 的分层边界。良性实体流数中位数 2、恶意 112（仓库既有诊断），
# 四层用于区分「改善是否只来自大袋实体」。边界只切分已算好的实体，不参与任何
# 选择或阈值决定。
STRATUM_BOUNDS: tuple[tuple[str, int, int | None], ...] = (
    ("m_eq_1", 1, 2),
    ("m_2_to_9", 2, 10),
    ("m_10_to_99", 10, 100),
    ("m_ge_100", 100, None),
)


def build_probe_config(
    source_config: dict[str, Any],
    *,
    run_id: str,
    output_root: Path,
    cache_root: Path,
    cardinality_receipt: Path,
    device_type: str,
    precision_profile_id: str,
    concurrent_with: list[str],
) -> dict[str, Any]:
    """由 C00 冻结配置派生本机诊断配置。

    只改 ``identity.run_id``、``identity.run_tier``、``runtime``、``paths``、
    ``tracking`` 与 ``checkpoint.formal_resume_eligible``。前五项落在
    ``runtime_projection`` 里，最后一项两个投影都不含（``science_projection`` 只取
    ``checkpoint.schema_version``），因此派生配置与检查点共享同一科学身份，
    由 ``run_probe`` 机械断言。``evaluation.entity_aggregation`` 保持
    ``maximum_over_validation_flows`` 不动——α 网格是事后在内存里的重聚合诊断，
    不改变该检查点被选出时的评价合同。
    """
    config = copy.deepcopy(source_config)
    config["identity"]["run_id"] = run_id
    # screening_only：本运行只做信号筛选，其制品不得进入论文正式结果或帕累托比较。
    config["identity"]["run_tier"] = "screening_only"
    config["checkpoint"]["formal_resume_eligible"] = False
    config["runtime"]["device_type"] = device_type
    config["runtime"]["precision_profile_id"] = precision_profile_id
    # 本机没有 CUDA inductor，且本诊断只做前向；关闭编译属于运行配置差异，
    # 与 CUDA 正式运行的数值路径因此不同，收据里显式记录。
    config["runtime"]["torch_compile"] = {
        "enabled": False,
        "mode": "default",
        "evidence": "本机 MPS 诊断只做前向，不启用 torch.compile；数值路径与 CUDA 正式运行不同。",
    }
    config["paths"]["cache_root"] = str(cache_root)
    config["paths"]["cardinality_receipt"] = str(cardinality_receipt)
    config["paths"]["output_root"] = str(output_root)
    config["tracking"] = {"mode": "disabled", "aggregate_only": True, "group": run_id}
    # 与其他运行共享同一块加速器时，耗时与峰值显存都是并发条件实测，不得当作独占效率。
    config["resource"] = dict(config["resource"])
    config["resource"]["resource_contention"] = bool(concurrent_with)
    config["resource"]["concurrent_runs"] = list(concurrent_with)
    return config


def install_sealed_transform(sealed_transform: Path, output_root: Path) -> dict[str, Any]:
    """把 C00 冻结的输入变换装进本次运行的 artifacts 目录。

    ``prepare_data`` 只在 ``output_root/artifacts/sealed-input-transform.pkl`` 不存在时
    才重新拟合。诊断必须用与检查点同一份变换，故先原样拷入并记录哈希。
    """
    destination = output_root / "artifacts" / "sealed-input-transform.pkl"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.is_file():
        shutil.copyfile(sealed_transform, destination)
    source_sha = dual.sha256_file(sealed_transform)
    destination_sha = dual.sha256_file(destination)
    dual.require(
        source_sha == destination_sha,
        f"冻结输入变换拷贝后哈希不符：{source_sha} 对 {destination_sha}",
        dual.EXIT_INPUT,
    )
    return {"source_path": str(sealed_transform), "sha256": source_sha}


def scan_validation_scores(
    config: dict[str, Any], model: Any, view: Any, arrays: dict[str, Any], validation_rows: Any,
    device: Any, profile: dict[str, Any], precision: Any, torch_module: Any,
) -> dict[str, Any]:
    """完整源验证扫描，返回逐流分数、标签与实体 ID（只在内存中存在）。

    循环体与 ``dual.validation_metrics`` 的扫描段逐项对应：同一批次划分、同一
    ``gather_sequences``/``features``/``forward_bare`` 调用、同一 ``sigmoid`` 后转
    ``float32`` numpy、同一「验证流不得重复计分」断言、同一实体广播方式。
    本函数只是把该函数丢弃的三个逐流数组交回调用方，供 α 网格在内存里重聚合。

    ``forward_bare`` 只按位置与 ``site`` 调用，不传 ``entity_state``：该关键字是
    M-E（z1 = entity_gated_ple）随后才加入的，服务器上冻结的宿主版本没有它。
    本诊断只走 C00 的 z1=0 路径，两版行为逐字一致（新版默认 ``entity_state=None``）。
    """
    import numpy as np

    batch_sequences = config["training"]["validation_batch_sequences"]
    predictions: list[Any] = []
    targets: list[Any] = []
    entity_ids: list[Any] = []
    seen = np.zeros(dual.base.LSPR23_FLOW_COUNT, dtype=bool)
    model.eval()
    started = time.time()
    heartbeat = max(1, len(validation_rows) // 10)
    LOGGER.info(
        "开始重聚合用源验证扫描：序列=%d，验证批=%d，设备=%s",
        len(validation_rows), batch_sequences, device.type,
    )
    with torch_module.no_grad():
        for start in range(0, len(validation_rows), batch_sequences):
            rows = validation_rows[start : start + batch_sequences]
            indices, valid, labels = view.gather_sequences(rows, config["training"]["sequence_length"])
            numeric, categorical = view.features(indices)
            logits, _ = dual.forward_bare(
                model, numeric, categorical, valid, device, profile, precision, torch_module,
                site="flow_forward_bare_validation",
            )
            scores = torch_module.sigmoid(logits.to(torch_module.float32)).cpu().numpy()
            selected_indices = indices[valid]
            dual.require(not bool(seen[selected_indices].any()), "验证流被重复计分", dual.EXIT_INPUT)
            seen[selected_indices] = True
            predictions.append(scores[valid])
            targets.append(labels[valid])
            repeated_entities = np.broadcast_to(np.asarray(arrays["E23"][rows])[:, None], indices.shape)
            entity_ids.append(repeated_entities[valid])
            completed = min(start + len(rows), len(validation_rows))
            if completed == len(validation_rows) or completed // heartbeat != start // heartbeat:
                elapsed = time.time() - started
                throughput = completed / max(elapsed, 1e-9)
                remaining = (len(validation_rows) - completed) / max(throughput, 1e-9)
                LOGGER.info(
                    "源验证扫描进度=%d/%d，吞吐=%.1f序列/秒，预计剩余=%.1f秒",
                    completed, len(validation_rows), throughput, remaining,
                )
    dual.synchronize_device(torch_module, device)
    model.train()
    return {
        "scores": np.concatenate(predictions).astype(np.float64, copy=False),
        "labels": np.concatenate(targets).astype(np.float32, copy=False),
        "entities": np.concatenate(entity_ids).astype(np.int64, copy=False),
        "seconds": time.time() - started,
    }


def reference_max_aggregation(
    scores: Any, labels: Any, entities: Any, entity_count: int,
) -> dict[str, Any]:
    """逐字复用 ``dual.validation_metrics`` 的 max 聚合六行，作为口径基准。"""
    import numpy as np

    entity_scores = np.full(entity_count, -np.inf, dtype=np.float64)
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_scores, entities, scores)
    np.maximum.at(entity_labels, entities, labels)
    scored_entities = np.isfinite(entity_scores)
    return {
        "entity_scores": entity_scores[scored_entities],
        "entity_labels": entity_labels[scored_entities],
        "scored_mask": scored_entities,
    }


class EntityGrouping:
    """实体内按分数降序排好的分组视图，供全部 α 档共用一次排序。

    ``np.lexsort((-scores, entities))`` 以 ``entities`` 为主键升序、``-scores`` 为
    次键升序（即实体内分数降序）。由此得到组起点、组内秩与组大小，top-k 掩码即
    ``组内秩 < k``，全部为向量化操作，不对实体做 Python 循环。
    """

    def __init__(self, scores: Any, labels: Any, entities: Any) -> None:
        import numpy as np

        order = np.lexsort((-scores, entities))
        self.sorted_scores = scores[order]
        sorted_labels = labels[order]
        sorted_entities = entities[order]
        total = sorted_entities.shape[0]
        is_group_start = np.empty(total, dtype=bool)
        is_group_start[0] = True
        np.not_equal(sorted_entities[1:], sorted_entities[:-1], out=is_group_start[1:])
        self.group_start = np.flatnonzero(is_group_start)
        self.group_index = np.cumsum(is_group_start) - 1
        self.group_size = np.diff(np.append(self.group_start, total)).astype(np.int64)
        self.group_entity = sorted_entities[self.group_start]
        # 实体标签＝该实体全部流标签的最大值，与 ``np.maximum.at`` 同语义。
        self.group_label = np.maximum.reduceat(sorted_labels, self.group_start)
        self.rank_in_group = np.arange(total, dtype=np.int64) - self.group_start[self.group_index]
        self.group_count = int(self.group_start.shape[0])

    def aggregate(self, alpha: float | None) -> Any:
        """``alpha is None`` 取 k≡1（max 基线）；否则 ``k = max(1, ceil(α·m))``。"""
        import numpy as np

        if alpha is None:
            k_of_group = np.ones(self.group_count, dtype=np.int64)
        else:
            k_of_group = np.maximum(1, np.ceil(alpha * self.group_size).astype(np.int64))
        take = self.rank_in_group < k_of_group[self.group_index]
        totals = np.bincount(
            self.group_index[take], weights=self.sorted_scores[take], minlength=self.group_count,
        )
        return totals / k_of_group.astype(np.float64), k_of_group


def stratified_average_precision(
    entity_scores: Any, entity_labels: Any, group_size: Any,
) -> dict[str, Any]:
    """按实体有效流数 m 分层计算实体 AP。

    某层没有正类实体时 AP 无定义，此处返回 ``None`` 并保留该层的实体数与正类数，
    不用任何替代值填充。
    """
    import numpy as np
    from sklearn.metrics import average_precision_score

    result: dict[str, Any] = {}
    for name, low, high in STRATUM_BOUNDS:
        mask = group_size >= low
        if high is not None:
            mask &= group_size < high
        selected_labels = entity_labels[mask]
        positives = int((selected_labels == 1).sum())
        entry: dict[str, Any] = {
            "entity_count": int(mask.sum()),
            "positive_entity_count": positives,
            "entity_ap": None,
        }
        if positives > 0 and positives < int(mask.sum()):
            entry["entity_ap"] = float(
                average_precision_score(selected_labels, entity_scores[mask])
            )
        result[name] = entry
    return result


def build_alpha_row(
    grouping: EntityGrouping, alpha: float | None, label: str,
) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import average_precision_score

    entity_scores, k_of_group = grouping.aggregate(alpha)
    entity_ap = float(average_precision_score(grouping.group_label, entity_scores))
    tail_fraction = float(np.mean(k_of_group / grouping.group_size.astype(np.float64)))
    return {
        "label": label,
        "alpha": alpha,
        "entity_ap": entity_ap,
        "inner_tail_fraction_mean": tail_fraction,
        "entities_with_k_gt_1": int((k_of_group > 1).sum()),
        "mean_k": float(k_of_group.mean()),
        "max_k": int(k_of_group.max()),
        "strata": stratified_average_precision(
            entity_scores, grouping.group_label, grouping.group_size
        ),
    }


def run_probe(arguments: argparse.Namespace) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import average_precision_score

    source_config_path = dual.resolve_project_path(arguments.config)
    checkpoint_path = dual.resolve_project_path(arguments.checkpoint)
    output_root = dual.resolve_project_path(arguments.output_root)
    source_config = dual.load_json(source_config_path)
    config = build_probe_config(
        source_config,
        run_id=arguments.run_id,
        output_root=output_root,
        cache_root=dual.resolve_project_path(arguments.cache_root),
        cardinality_receipt=dual.resolve_project_path(arguments.cardinality_receipt),
        device_type=arguments.device_type,
        precision_profile_id=arguments.precision_profile_id,
        concurrent_with=list(arguments.concurrent_with),
    )
    dual.validate_config(config)
    output_root.mkdir(parents=True, exist_ok=True)
    dual.atomic_json(output_root / "config.json", config)

    import torch

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    science = dual.science_projection(config)
    science_sha = dual.canonical_sha256(science)
    checkpoint_science_sha = checkpoint["science_identity"]["science_identity_sha256"]
    dual.require(
        science_sha == checkpoint_science_sha,
        f"科学身份与检查点不符：本运行 {science_sha}，检查点 {checkpoint_science_sha}",
        dual.EXIT_CONFIG,
    )
    dual.require(
        checkpoint["schema_version"] == dual.CHECKPOINT_SCHEMA_VERSION, "检查点模式不符", dual.EXIT_INPUT
    )
    LOGGER.info(
        "检查点身份已核验：run_id=%s，selection_role=%s，selected_epoch=%s，selected_metric=%r",
        checkpoint["run_id"], checkpoint["selection_role"],
        checkpoint["selected_epoch"], checkpoint["selected_metric"],
    )
    dual.atomic_json(output_root / "status.json", {
        "run_id": config["identity"]["run_id"], "state": "running", "stage": "probe",
        "exit_code": None, "target_reads": 0,
    })

    transform_receipt = install_sealed_transform(
        dual.resolve_project_path(arguments.sealed_transform), output_root
    )
    torch_module, device, profile, precision = dual.resolve_runtime(config)
    base_config = dual.effective_base_config(config)
    arrays, train_rows, validation_rows, view = dual.prepare_data(config, base_config, output_root)
    model, _optimizer, _optimizer_receipt = dual.build_model_optimizer(
        config, base_config, view, torch_module, device
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    LOGGER.info("检查点权重已加载，进入前向阶段")

    started = time.time()
    reference_metrics: dict[str, Any] | None = None
    if arguments.cross_check_validation_metrics:
        # 直接调用未被修改的 ``validation_metrics``，得到本设备上的权威口径读数。
        LOGGER.info("交叉核验：调用未修改的 validation_metrics 取本设备权威读数")
        reference_metrics = dual.validation_metrics(
            config, model, view, arrays, validation_rows, device, profile, precision, torch_module,
        )
        LOGGER.info(
            "validation_metrics 读数：flow_ap=%r，entity_ap=%r",
            reference_metrics["validation_flow_ap"], reference_metrics["validation_entity_ap"],
        )

    scan = scan_validation_scores(
        config, model, view, arrays, validation_rows, device, profile, precision, torch_module,
    )
    scores, labels, entities = scan["scores"], scan["labels"], scan["entities"]
    flow_ap = float(average_precision_score(labels, scores))
    entity_count = int(np.max(arrays["E23"])) + 1
    reference = reference_max_aggregation(scores, labels, entities, entity_count)
    reference_entity_ap = float(
        average_precision_score(reference["entity_labels"], reference["entity_scores"])
    )

    grouping = EntityGrouping(scores, labels, entities)
    # 口径自检一：分组视图的实体集合、顺序与标签必须与参考实现逐位一致。
    dual.require(
        bool(np.array_equal(np.flatnonzero(reference["scored_mask"]), grouping.group_entity)),
        "分组实体集合或顺序与 np.maximum.at 参考实现不符",
        dual.EXIT_RUNTIME,
    )
    dual.require(
        bool(np.array_equal(reference["entity_labels"], grouping.group_label)),
        "分组实体标签与 np.maximum.at 参考实现不符",
        dual.EXIT_RUNTIME,
    )
    max_row = build_alpha_row(grouping, None, "max")
    max_entity_scores, _ = grouping.aggregate(None)
    # 口径自检二：k≡1 的 top-k 均值必须与 max 聚合逐位相同（选元素、除以 1.0，无算术误差）。
    bitwise_scores_equal = bool(np.array_equal(reference["entity_scores"], max_entity_scores))
    bitwise_ap_equal = max_row["entity_ap"] == reference_entity_ap
    dual.require(
        bitwise_scores_equal and bitwise_ap_equal,
        "k≡1 的 top-k 聚合与 np.maximum.at 不逐位一致，口径实现有误",
        dual.EXIT_RUNTIME,
    )

    rows = [max_row]
    for alpha in arguments.alpha:
        rows.append(build_alpha_row(grouping, float(alpha), f"alpha={alpha:g}"))
        LOGGER.info(
            "α=%g 重聚合完成：实体 AP=%.10f（max 基线 %.10f）",
            alpha, rows[-1]["entity_ap"], max_row["entity_ap"],
        )

    recorded_cuda_entity_ap = float(checkpoint["selected_metric"])
    payload: dict[str, Any] = {
        "schema_version": PROBE_SCHEMA_VERSION,
        "run_id": config["identity"]["run_id"],
        "run_tier": "screening_only",
        "target_reads": 0,
        "question": "源年 LSPR23 验证集上，实体内 top-⌈α·m⌉ 均值聚合相对 max 聚合的实体 AP 变化",
        "source": {
            "config_path": str(source_config_path),
            "config_sha256": dual.sha256_file(source_config_path),
            "checkpoint_path": str(checkpoint_path),
            "checkpoint_sha256": dual.sha256_file(checkpoint_path),
            "checkpoint_run_id": checkpoint["run_id"],
            "selection_role": checkpoint["selection_role"],
            "selected_epoch": int(checkpoint["selected_epoch"]),
            "recorded_cuda_entity_ap": recorded_cuda_entity_ap,
            "sealed_input_transform": transform_receipt,
        },
        "identity": {
            "science_identity_sha256": science_sha,
            "checkpoint_science_identity_sha256": checkpoint_science_sha,
            "science_identity_match": science_sha == checkpoint_science_sha,
            "runtime_identity_sha256": dual.canonical_sha256(dual.runtime_projection(config)),
            "runtime_differs_from_checkpoint": True,
            "runtime_difference_note": (
                "检查点在 CUDA、cuda-bf16-amp-fp32-sensitive-v1、torch.compile 启用下产生；"
                f"本诊断在 {device.type}、{config['runtime']['precision_profile_id']}、未编译下重放前向。"
                "科学身份相同，数值路径不同。"
            ),
        },
        "environment": dual.environment_receipt(config, torch_module, device, profile),
        "resource": {
            "resource_contention": bool(arguments.concurrent_with),
            "concurrent_runs": list(arguments.concurrent_with),
            "measurement_note": (
                "与上列运行共享同一加速器时，本收据中的耗时与显存是并发条件实测，"
                "不得冒充独占效率，也不得用于严格效率支配比较。"
                if arguments.concurrent_with else
                "本次运行未登记并发对象。"
            ),
            "sampling_source": "torch 设备内存接口与进程 RSS（见 environment 块）",
        },
        "scan": {
            "validation_sequences": int(len(validation_rows)),
            "scored_flows": int(scores.shape[0]),
            "scored_entities": grouping.group_count,
            "positive_entities": int((grouping.group_label == 1).sum()),
            "movable_entities_m_ge_2": int((grouping.group_size >= 2).sum()),
            "flow_count_median": float(np.median(grouping.group_size)),
            "scan_seconds": scan["seconds"],
        },
        "flow_ap": {
            "value": flow_ap,
            "note": "逐流 AP 不随 α 变化，作恒定性自检",
            "validation_metrics_value": (
                None if reference_metrics is None else reference_metrics["validation_flow_ap"]
            ),
        },
        "calibration_self_check": {
            "reference_max_entity_ap": reference_entity_ap,
            "topk_k_equals_one_entity_ap": max_row["entity_ap"],
            "entity_scores_bitwise_equal": bitwise_scores_equal,
            "entity_ap_bitwise_equal": bitwise_ap_equal,
            "validation_metrics_entity_ap": (
                None if reference_metrics is None else reference_metrics["validation_entity_ap"]
            ),
            "validation_metrics_bitwise_equal": (
                None if reference_metrics is None
                else reference_metrics["validation_entity_ap"] == reference_entity_ap
            ),
            "recorded_cuda_entity_ap": recorded_cuda_entity_ap,
            "matches_recorded_cuda_reading": max_row["entity_ap"] == recorded_cuda_entity_ap,
            "delta_versus_recorded_cuda": max_row["entity_ap"] - recorded_cuda_entity_ap,
        },
        "numeric_provenance": {
            "alpha_grid": {
                "values": [float(value) for value in arguments.alpha],
                "purpose": "敏感性扫描，判断实体内尾部聚合方向是否存在信号",
                "frozen": False,
                "touches_target_labels": False,
                "source": "任务简报给定的诊断网格，不进入任何模型、损失或阈值配置",
            },
            "stratum_bounds": [
                {"name": name, "m_low": low, "m_high": high} for name, low, high in STRATUM_BOUNDS
            ],
        },
        "aggregation_grid": rows,
    }
    payload["wall_seconds"] = time.time() - started
    dual.atomic_json(output_root / "probe.json", payload)
    dual.atomic_json(output_root / "status.json", {
        "run_id": config["identity"]["run_id"], "state": "finished", "stage": "probe",
        "exit_code": 0, "target_reads": 0,
    })
    return payload


def summarize(payload: dict[str, Any]) -> None:
    check = payload["calibration_self_check"]
    LOGGER.info("=" * 78)
    LOGGER.info(
        "口径自检：k≡1 与 np.maximum.at 逐位一致=%s；与 validation_metrics 逐位一致=%s",
        check["entity_ap_bitwise_equal"], check["validation_metrics_bitwise_equal"],
    )
    LOGGER.info(
        "max 基线本机读数=%.16f；CUDA 记录读数=%.16f；差=%+.3e；逐位一致=%s",
        check["topk_k_equals_one_entity_ap"], check["recorded_cuda_entity_ap"],
        check["delta_versus_recorded_cuda"], check["matches_recorded_cuda_reading"],
    )
    baseline = payload["aggregation_grid"][0]["entity_ap"]
    LOGGER.info("%-12s %-14s %-12s %-10s", "聚合", "实体 AP", "相对 max", "平均 k")
    for row in payload["aggregation_grid"]:
        LOGGER.info(
            "%-12s %-14.10f %+-12.6f %-10.2f",
            row["label"], row["entity_ap"], row["entity_ap"] - baseline, row["mean_k"],
        )
    LOGGER.info("=" * 78)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/ch3-ft-c00-dual-selection-cuda-formal-v1.json")
    parser.add_argument(
        "--checkpoint",
        default="runs/diagnostics/ch3-ft-c00-dual-selection-cuda-formal-v1/checkpoints/selected-by-entity.pt",
    )
    parser.add_argument(
        "--sealed-transform",
        default="runs/diagnostics/ch3-ft-c00-dual-selection-cuda-formal-v1/artifacts/sealed-input-transform.pkl",
    )
    parser.add_argument("--run-id", default="ch3-ft-entity-tail-aggregation-probe-v1")
    parser.add_argument("--output-root", default="runs/diagnostics/ch3-ft-entity-tail-aggregation-probe-v1")
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument(
        "--cardinality-receipt",
        default="runs/diagnostics/ch3-lspr23-field-cardinality-receipt-v1/field-cardinality-receipt.json",
    )
    parser.add_argument("--device-type", default="mps", choices=("mps", "cuda"))
    parser.add_argument("--precision-profile-id", default="mps-fp32-v1")
    parser.add_argument("--alpha", type=float, nargs="+", default=list(DEFAULT_ALPHA_GRID))
    parser.add_argument(
        "--concurrent-with", nargs="*", default=[],
        help="同机同加速器上并发运行的运行身份；给出即在收据里置 resource_contention=true",
    )
    parser.add_argument(
        "--no-cross-check", dest="cross_check_validation_metrics", action="store_false",
        help="跳过对未修改 validation_metrics 的交叉核验（省一次完整前向）",
    )
    parser.set_defaults(cross_check_validation_metrics=True)
    arguments = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    for value in arguments.alpha:
        if not 0.0 < value <= 1.0:
            LOGGER.error("α 必须落在 (0, 1]，收到 %r", value)
            return dual.EXIT_CONFIG
    try:
        payload = run_probe(arguments)
    except dual.ExperimentError as error:
        LOGGER.error("诊断失败：%s", error)
        return error.exit_code
    except Exception:  # noqa: BLE001  保留原始堆栈供诊断
        LOGGER.error("诊断异常终止：\n%s", "".join(__import__("traceback").format_exc()))
        return dual.EXIT_RUNTIME
    summarize(payload)
    print(json.dumps(
        {
            "run_id": payload["run_id"],
            "target_reads": payload["target_reads"],
            "calibration_self_check": payload["calibration_self_check"],
            "aggregation_grid": [
                {"label": row["label"], "entity_ap": row["entity_ap"]}
                for row in payload["aggregation_grid"]
            ],
        },
        ensure_ascii=False, indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
