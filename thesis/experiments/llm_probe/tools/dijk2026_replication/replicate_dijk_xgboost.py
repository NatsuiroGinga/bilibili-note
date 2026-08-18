#!/usr/bin/env python
"""Dijk 2026（SSRN 6597680）XGBoost 跨年度结果复现主流程。

协议：LSPR23 训练 → LSPR24 零样本评价，目标数字为表 5 第 1 行 XGB 的 AP next = 0.2416。
本运行使用论文的 83 维字段（含 6 个本课题防泄漏臂禁用字段），因此标记
`paper_constrained_replication=true`，与本课题 77 维臂严格分开，不混排。

阶段：
  train    读取 LSPR23 全量 → OP 序列切分 → 训练 XGBoost → 同年验证 AP
  score    对 LSPR24 开放池只读特征打分（绝不读取 Label），落盘并封存哈希
  label    分数封存后单独读取 LSPR24 开放池标签
  metrics  连接分数与标签，计算逐流 AP、AUROC、π 与 AP Lift
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import xgboost as xgb
from sklearn.metrics import average_precision_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dijk_fields import (  # noqa: E402
    DIJK_FEATURES,
    DIJK_ONLY_FIELDS,
    LABEL_COLUMN,
    RANDOM_SEED,
    SEQUENCE_LENGTH,
    TARGET_FINAL_CUT_NS,
    XGBOOST_NUM_BOOST_ROUND,
    XGBOOST_PARAMS,
)
from dijk_ingest import (  # noqa: E402
    iter_lspr24_open_pool,
    log_memory,
    payload_to_matrix,
    read_lspr23,
)

PROJECT_ROOT = Path("/root/autodl-tmp/thesis/experiments/llm_probe")
RUN_ROOT = PROJECT_ROOT / "runs/candidates/dijk2026-xgboost-replication-v1"
LSPR23_ZIP = PROJECT_ROOT / "data/raw/lspr23-v1/ls23pr_flows.zip"
LSPR23_MEMBER = "ls23pr_v1.csv"
LSPR24_PARQUET = PROJECT_ROOT / "data/raw/lspr24-v1/lspr24_v2.parquet"

# 冻结数据合同 lspr23-lspr24-bounded-quick-q0-v1 已记录的输入哈希，用于交叉核对。
KNOWN_LSPR23_SHA256 = "4c39f29a2e99ec58f6c167863d49d944ab5e46dc78a28afe78cc57ba85cd2885"
KNOWN_LSPR24_SHA256 = "1d96f0a023de583397cc300143ba98b84b9e9bd2270f0b8b61346ca19963057a"

# 论文未报告 train:val 比例。以表 8 的 LSPR24 OP「Train seq.=126,421」反推：
# 126421 × 128 / 20,227,356 = 0.79999...，故取 0.80。该值为推导所得，非论文明写。
TRAIN_FRACTION = 0.80

TARGET_AP_NEXT = 0.2416

# 训练设备可由 DIJK_DEVICE 覆盖；预测固定在 CPU 上执行以避免主机数组回退开销。
PREDICT_DEVICE = "cpu"

logger = logging.getLogger("dijk2026")


def setup_logging(stage: str) -> None:
    """同时输出到控制台与唯一运行目录日志。"""
    (RUN_ROOT / "logs").mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(RUN_ROOT / "logs" / f"{stage}.log", encoding="utf-8"),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=handlers,
        force=True,
    )


def sha256_file(path: Path) -> str:
    """流式计算文件 sha256。"""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1 << 22)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict) -> None:
    """原子写 JSON。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
    temporary.replace(path)


def update_status(stage: str, state: str, extra: dict | None = None) -> None:
    """更新运行状态收据。"""
    path = RUN_ROOT / "status.json"
    payload: dict = {}
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    payload.setdefault("run_name", "dijk2026-xgboost-replication-v1")
    payload.setdefault("stages", {})
    payload["stages"][stage] = {
        "state": state,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        **(extra or {}),
    }
    payload["screening_only"] = True
    payload["formal_paper_evidence"] = False
    payload["final_accessed"] = False
    payload["paper_constrained_replication"] = True
    write_json(path, payload)


def stage_config() -> None:
    """落盘运行配置与输入收据。"""
    write_json(RUN_ROOT / "config.json", {
        "run_name": "dijk2026-xgboost-replication-v1",
        "display_name": "Dijk2026-XGBoost跨年度AP复现-83字段论文约束臂",
        "research_route": "RWKV",
        "paper": {
            "citation": "Dijk 2026, SSRN 6597680, DOI 10.2139/ssrn.6597680",
            "local_pdf": "raw/papers/datasets/LSPR24/ssrn-6597680.pdf",
            "target_metric": "Table 5 row 1, XGB, AP next",
            "target_value": TARGET_AP_NEXT,
        },
        "features": {
            "definition": "Dijk 2026 附录 A 的 83 个字段，原序",
            "dimension": len(DIJK_FEATURES),
            "fields": list(DIJK_FEATURES),
            "fields_forbidden_in_project_77d_arm": list(DIJK_ONLY_FIELDS),
        },
        "xgboost": {**XGBOOST_PARAMS, "num_boost_round": XGBOOST_NUM_BOOST_ROUND,
                    "source": "Dijk 2026 §5.6（印刷第 23 页）"},
        "split": {
            "unit": "OP 序列（全局时间排序后每 128 条流一个不重叠块）",
            "sequence_length": SEQUENCE_LENGTH,
            "train_fraction": TRAIN_FRACTION,
            "seed": RANDOM_SEED,
        },
        "evaluation": {
            "dataset": "LSPR24 开放池（valid time 且 available_ns < target_final_cut_ns）",
            "zero_shot": True,
            "row_cap": 0,
            "pair_hash_prescreen": False,
            "stratified_sampling": False,
        },
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
        "paper_constrained_replication": True,
    })

    receipt = {
        "lspr23_zip": {
            "path": str(LSPR23_ZIP),
            "member": LSPR23_MEMBER,
            "sha256": sha256_file(LSPR23_ZIP),
            "expected_sha256": KNOWN_LSPR23_SHA256,
        },
        "lspr24_parquet": {
            "path": str(LSPR24_PARQUET),
            "sha256": sha256_file(LSPR24_PARQUET),
            "expected_sha256": KNOWN_LSPR24_SHA256,
        },
        "target_final_cut_ns": TARGET_FINAL_CUT_NS,
        "final_accessed": False,
    }
    receipt["lspr23_zip"]["match"] = (
        receipt["lspr23_zip"]["sha256"] == KNOWN_LSPR23_SHA256)
    receipt["lspr24_parquet"]["match"] = (
        receipt["lspr24_parquet"]["sha256"] == KNOWN_LSPR24_SHA256)
    write_json(RUN_ROOT / "input-receipt.json", receipt)
    logger.info("输入收据：lspr23 匹配=%s lspr24 匹配=%s",
                receipt["lspr23_zip"]["match"], receipt["lspr24_parquet"]["match"])


def stage_train() -> None:
    """LSPR23 全量读取、OP 序列切分与 XGBoost 训练。"""
    update_status("train", "running")
    log_memory("train 起始")
    bundle = read_lspr23(str(LSPR23_ZIP), LSPR23_MEMBER)
    log_memory("LSPR23 读取完成")

    n_rows = bundle.features.shape[0]
    positives = int(bundle.labels.sum())
    logger.info("LSPR23 保留 %d 行，阳性 %d，π=%.10f", n_rows, positives, positives / n_rows)

    # OP：按全局起始时间稳定排序，同值按原始行序；每 128 条流一个不重叠块。
    order = np.argsort(bundle.time_start_us, kind="stable")
    sequence_of_sorted = np.arange(n_rows, dtype=np.int64) // SEQUENCE_LENGTH
    sequence_id = np.empty(n_rows, dtype=np.int64)
    sequence_id[order] = sequence_of_sorted
    del order, sequence_of_sorted
    n_sequences = int(sequence_id.max()) + 1

    generator = np.random.default_rng(RANDOM_SEED)
    permutation = generator.permutation(n_sequences)
    n_train_sequences = int(round(n_sequences * TRAIN_FRACTION))
    is_train_sequence = np.zeros(n_sequences, dtype=bool)
    is_train_sequence[permutation[:n_train_sequences]] = True
    train_mask = is_train_sequence[sequence_id]
    del permutation, is_train_sequence, sequence_id

    x_train = bundle.features[train_mask]
    y_train = bundle.labels[train_mask].astype(np.float32)
    x_valid = bundle.features[~train_mask]
    y_valid = bundle.labels[~train_mask].astype(np.float32)
    bundle.features = np.empty((0, len(DIJK_FEATURES)), dtype=np.float32)
    log_memory("切分完成")

    split_receipt = {
        "algorithm": "dijk-op-sequence-random-split-v1",
        "description": "全局按 mTimestampStart 稳定排序后每 128 条流成一个 OP 序列，"
                       "对序列做 seed=42 随机置换，前 80% 序列进训练集",
        "sequence_length": SEQUENCE_LENGTH,
        "seed": RANDOM_SEED,
        "generator": "numpy.random.default_rng(42).permutation",
        "train_fraction": TRAIN_FRACTION,
        "train_fraction_source": "论文未报告；由表 8 LSPR24 OP Train seq.=126421 反推 "
                                 "126421*128/20227356=0.79999 得到",
        "sequences_total": n_sequences,
        "sequences_train": n_train_sequences,
        "sequences_validation": n_sequences - n_train_sequences,
        "rows_total": n_rows,
        "rows_train": int(x_train.shape[0]),
        "rows_validation": int(x_valid.shape[0]),
        "pi_total": positives / n_rows,
        "pi_train": float(y_train.mean()),
        "pi_validation": float(y_valid.mean()),
        "lspr23_rows_read": bundle.rows_total,
        "lspr23_rows_invalid_time": bundle.rows_invalid_time,
        "lspr23_rows_invalid_label": bundle.rows_invalid_label,
        "conn_key_note": "论文按 conn_key 做序列级切分；XGBoost 的对应表示是 OP，"
                         "OP 的分组键 Φ_OP(f)={1} 退化为单一全局流，"
                         "因此切分单元落到 OP 序列本身",
        "screening_only": True,
        "final_accessed": False,
    }
    write_json(RUN_ROOT / "split-receipt.json", split_receipt)
    logger.info("切分收据：训练 %d 行 / 验证 %d 行，π_train=%.6f π_val=%.6f",
                x_train.shape[0], x_valid.shape[0],
                split_receipt["pi_train"], split_receipt["pi_validation"])

    params = dict(XGBOOST_PARAMS)
    params["device"] = os.environ.get("DIJK_DEVICE", "cuda")
    params["seed"] = RANDOM_SEED
    feature_names = [name.replace("[", "(").replace("]", ")").replace("<", "lt")
                     for name in DIJK_FEATURES]

    logger.info("构建 QuantileDMatrix：%d 行 × %d 列，device=%s",
                x_train.shape[0], x_train.shape[1], params["device"])
    started = time.monotonic()
    booster = None
    for attempt_device in (params["device"], "cpu"):
        params["device"] = attempt_device
        try:
            with xgb.config_context(device=attempt_device):
                d_train = xgb.QuantileDMatrix(
                    x_train, label=y_train, max_bin=int(params["max_bin"]),
                    feature_names=feature_names,
                )
                log_memory(f"训练矩阵构建完成（device={attempt_device}）")
                booster = xgb.train(params, d_train, num_boost_round=XGBOOST_NUM_BOOST_ROUND)
            break
        except xgb.core.XGBoostError as error:
            logger.warning("device=%s 训练失败：%r", attempt_device, error)
            if attempt_device == "cpu":
                raise
    if booster is None:
        raise RuntimeError("XGBoost 训练未产出模型")
    logger.info("训练完成，用时 %.0f s，device=%s", time.monotonic() - started, params["device"])
    del d_train, x_train
    log_memory("训练完成")

    (RUN_ROOT / "artifacts").mkdir(parents=True, exist_ok=True)
    model_path = RUN_ROOT / "artifacts" / "model.ubj"
    booster.save_model(str(model_path))

    # 预测统一在 CPU 上执行：避免主机数组与 cuda 上下文不匹配时逐批回退 DMatrix 的开销。
    booster.set_param({"device": PREDICT_DEVICE})
    scores_validation = booster.inplace_predict(x_valid)
    ap_same = float(average_precision_score(y_valid, scores_validation))
    auroc_same = float(roc_auc_score(y_valid, scores_validation))
    logger.info("同年（LSPR23 验证切分）AP=%.6f AUROC=%.6f  论文表 5 报 1.0000",
                ap_same, auroc_same)

    write_json(RUN_ROOT / "metrics" / "same-year.json", {
        "dataset": "LSPR23 validation split (OP sequence split, seed 42)",
        "rows": int(x_valid.shape[0]),
        "positives": int(y_valid.sum()),
        "pi": float(y_valid.mean()),
        "flow_ap": ap_same,
        "flow_auroc": auroc_same,
        "ap_lift": ap_same / float(y_valid.mean()) if y_valid.mean() > 0 else None,
        "paper_reported_ap_same": 1.0000,
        "screening_only": True,
        "final_accessed": False,
    })
    update_status("train", "succeeded", {
        "model_sha256": sha256_file(model_path),
        "ap_same_year": ap_same,
        "train_device": params["device"],
        "predict_device": PREDICT_DEVICE,
    })


def _feature_names() -> list[str]:
    return [name.replace("[", "(").replace("]", ")").replace("<", "lt")
            for name in DIJK_FEATURES]


def stage_score() -> None:
    """对 LSPR24 开放池逐流打分。本阶段绝不读取 Label 列。"""
    update_status("score", "running")
    if LABEL_COLUMN in DIJK_FEATURES:
        raise RuntimeError("断言失败：标签列不得出现在特征清单中")

    booster = xgb.Booster()
    booster.load_model(str(RUN_ROOT / "artifacts" / "model.ubj"))
    booster.set_param({"device": PREDICT_DEVICE})

    row_index_chunks: list[np.ndarray] = []
    score_chunks: list[np.ndarray] = []
    for row_index, payload in iter_lspr24_open_pool(str(LSPR24_PARQUET), list(DIJK_FEATURES)):
        matrix = payload_to_matrix(payload)
        del payload
        scores = booster.inplace_predict(matrix)
        del matrix
        row_index_chunks.append(row_index)
        score_chunks.append(np.asarray(scores, dtype=np.float32))

    all_rows = np.concatenate(row_index_chunks)
    all_scores = np.concatenate(score_chunks)
    del row_index_chunks, score_chunks
    log_memory("打分完成")

    table = pa.table({
        "source_row_index": pa.array(all_rows, pa.int64()),
        "score": pa.array(all_scores, pa.float32()),
    })
    path = RUN_ROOT / "predictions" / "target-scores.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path, compression="zstd")

    digest = sha256_file(path)
    write_json(RUN_ROOT / "predictions" / "score-seal-receipt.json", {
        "schema_version": "dijk2026-score-seal-v1",
        "path": str(path),
        "sha256": digest,
        "rows": int(all_rows.shape[0]),
        "score_min": float(all_scores.min()),
        "score_max": float(all_scores.max()),
        "score_mean": float(all_scores.mean()),
        "sealed_before_label_join": True,
        "label_columns_read_in_this_stage": [],
        "final_accessed": False,
    })
    logger.info("分数已封存：%d 行 sha256=%s", all_rows.shape[0], digest)
    update_status("score", "succeeded", {"rows": int(all_rows.shape[0]), "sha256": digest})


def stage_label() -> None:
    """分数封存后单独读取 LSPR24 开放池标签。"""
    update_status("label", "running")
    seal = json.loads((RUN_ROOT / "predictions" / "score-seal-receipt.json").read_text("utf-8"))
    if sha256_file(Path(seal["path"])) != seal["sha256"]:
        raise RuntimeError("断言失败：分数文件哈希与封存收据不一致")

    row_index_chunks: list[np.ndarray] = []
    label_chunks: list[np.ndarray] = []
    for row_index, payload in iter_lspr24_open_pool(str(LSPR24_PARQUET), [LABEL_COLUMN]):
        labels = payload.column(LABEL_COLUMN).to_numpy(zero_copy_only=False)
        row_index_chunks.append(row_index)
        label_chunks.append(labels.astype(np.int8))

    all_rows = np.concatenate(row_index_chunks)
    all_labels = np.concatenate(label_chunks)
    table = pa.table({
        "source_row_index": pa.array(all_rows, pa.int64()),
        "label": pa.array(all_labels, pa.int8()),
    })
    path = RUN_ROOT / "predictions" / "target-labels.parquet"
    pq.write_table(table, path, compression="zstd")
    logger.info("标签已落盘：%d 行，阳性 %d", all_rows.shape[0], int(all_labels.sum()))
    update_status("label", "succeeded", {
        "rows": int(all_rows.shape[0]),
        "positives": int(all_labels.sum()),
        "sha256": sha256_file(path),
    })


def stage_metrics() -> None:
    """连接封存分数与标签，计算逐流 AP、AUROC、π 与 AP Lift。"""
    update_status("metrics", "running")
    seal = json.loads((RUN_ROOT / "predictions" / "score-seal-receipt.json").read_text("utf-8"))
    score_path = Path(seal["path"])
    if sha256_file(score_path) != seal["sha256"]:
        raise RuntimeError("断言失败：分数文件哈希与封存收据不一致")

    scores_table = pq.read_table(score_path)
    labels_table = pq.read_table(RUN_ROOT / "predictions" / "target-labels.parquet")
    score_rows = scores_table.column("source_row_index").to_numpy(zero_copy_only=False)
    label_rows = labels_table.column("source_row_index").to_numpy(zero_copy_only=False)
    if not np.array_equal(score_rows, label_rows):
        raise RuntimeError("断言失败：分数与标签的全局行号序列不一致")

    scores = scores_table.column("score").to_numpy(zero_copy_only=False)
    labels = labels_table.column("label").to_numpy(zero_copy_only=False).astype(np.int8)
    del scores_table, labels_table
    log_memory("指标计算前")

    n_rows = int(labels.shape[0])
    positives = int(labels.sum())
    prevalence = positives / n_rows
    flow_ap = float(average_precision_score(labels, scores))
    flow_auroc = float(roc_auc_score(labels, scores))

    payload = {
        "dataset": "LSPR24 开放池（valid time 且 available_ns < target_final_cut_ns）",
        "protocol": "零样本迁移：LSPR23 训练，LSPR24 直接评价，不重训",
        "metric_unit": "逐流",
        "rows": n_rows,
        "positives": positives,
        "prevalence_pi": prevalence,
        "flow_ap": flow_ap,
        "flow_auroc": flow_auroc,
        "ap_lift": flow_ap / prevalence if prevalence > 0 else None,
        "paper_ap_next": TARGET_AP_NEXT,
        "paper_pi_op": 0.0707,
        "paper_ap_lift": TARGET_AP_NEXT / 0.0707,
        "gap_to_paper_ap": flow_ap - TARGET_AP_NEXT,
        "score_seal_sha256": seal["sha256"],
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
        "paper_constrained_replication": True,
    }
    write_json(RUN_ROOT / "metrics" / "next-year.json", payload)
    logger.info("次年评价：行=%d 阳性=%d π=%.10f AP=%.10f AUROC=%.10f Lift=%.6f（论文 0.2416）",
                n_rows, positives, prevalence, flow_ap, flow_auroc, payload["ap_lift"])
    update_status("metrics", "succeeded", {"flow_ap": flow_ap, "prevalence": prevalence})


STAGES = {
    "config": stage_config,
    "train": stage_train,
    "score": stage_score,
    "label": stage_label,
    "metrics": stage_metrics,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Dijk 2026 XGBoost 跨年度复现")
    parser.add_argument("--stages", default="config,train,score,label,metrics",
                        help="逗号分隔的阶段名")
    args = parser.parse_args()
    stages = [s.strip() for s in args.stages.split(",") if s.strip()]
    unknown = [s for s in stages if s not in STAGES]
    if unknown:
        raise SystemExit(f"未知阶段：{unknown}")

    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    setup_logging("+".join(stages))
    logger.info("运行根=%s 阶段=%s", RUN_ROOT, stages)
    for name in stages:
        logger.info("===== 阶段 %s 开始 =====", name)
        try:
            STAGES[name]()
        except Exception as error:  # noqa: BLE001 - 保留状态收据后再抛出
            logger.exception("阶段 %s 失败：%s", name, error)
            update_status(name, "failed", {"error": repr(error)})
            raise
        logger.info("===== 阶段 %s 结束 =====", name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
