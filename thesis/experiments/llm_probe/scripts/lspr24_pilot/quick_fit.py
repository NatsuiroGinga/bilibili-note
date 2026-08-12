"""开发区流级诊断拟合：时间有序切分 + HGB，报告 PR-AUC / ROC-AUC / F1。

结果仅为字段可分性诊断，不是合同定义的公平基线，不得写入论文。
"""

from __future__ import annotations

import logging
import sys
import time

import numpy as np
import pyarrow.parquet as pq
import pyarrow.compute as pc
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score, precision_recall_curve

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

PARQUET = "/Users/bilibili/personal/note/thesis/experiments/llm_probe/data/raw/lspr24-v1/lspr24_v2.parquet"
CUT_US = 1709802623 * 1_000_000  # 由无标签活动秒秩算出的 80% 切点
TARGET_ROWS = 1_500_000

FORBIDDEN = {
    "Flow ID", "SrcIP", "DstIP", "SrcPort", "DstPort",
    "mTimestampStart", "mTimestampLast",
    "Label", "Label_src", "Label_dst",
    "SigID revision", "Category", "Severity", "Anomaly_event",
    "External_src", "External_dst", "Segment_src", "Segment_dst",
    "Expoid_src", "Expoid_dst", "Int/Ext Dst IP", "Service",
    "L3/L4 Protocol",
}


def main() -> None:
    pf = pq.ParquetFile(PARQUET)
    feature_cols = [
        f.name for f in pf.schema_arrow
        if f.name not in FORBIDDEN and str(f.type).startswith(("int", "uint", "float", "double"))
    ]
    assert not (set(feature_cols) & FORBIDDEN)
    logger.info("合法特征列 %d 个", len(feature_cols))

    need = feature_cols + ["mTimestampLast", "Label"]
    xs, ys, ts = [], [], []
    step = max(1, (pf.metadata.num_rows * 8 // 10) // TARGET_ROWS)
    for rg in range(pf.metadata.num_row_groups):
        batch = pf.read_row_group(rg, columns=need)
        batch = batch.filter(pc.less(batch.column("mTimestampLast"), CUT_US))
        if batch.num_rows == 0:
            continue
        sub = batch.take(np.arange(0, batch.num_rows, step))
        xs.append(np.column_stack([
            sub.column(c).to_numpy(zero_copy_only=False).astype(np.float32) for c in feature_cols
        ]))
        ys.append(sub.column("Label").to_numpy(zero_copy_only=False).astype(np.int8))
        ts.append(sub.column("mTimestampLast").to_numpy(zero_copy_only=False))

    x = np.vstack(xs); y = np.concatenate(ys); t = np.concatenate(ts)
    order = np.argsort(t, kind="stable")
    x, y, t = x[order], y[order], t[order]
    assert t.max() < CUT_US, "样本越过 80% 切点"

    split = int(len(y) * 0.75)
    xtr, ytr = x[:split], y[:split]
    xva, yva = x[split:], y[split:]
    logger.info("训练 %d 行（正类 %.4f） / 验证 %d 行（正类 %.4f），按时间有序切分",
                len(ytr), ytr.mean(), len(yva), yva.mean())

    t0 = time.time()
    clf = HistGradientBoostingClassifier(
        max_iter=200, learning_rate=0.1, max_leaf_nodes=31,
        early_stopping=True, validation_fraction=0.1, random_state=42,
    )
    clf.fit(xtr, ytr)
    logger.info("拟合完成，耗时 %.1fs，实际迭代 %d", time.time() - t0, clf.n_iter_)

    p = clf.predict_proba(xva)[:, 1]
    pr_auc = average_precision_score(yva, p)
    roc_auc = roc_auc_score(yva, p)
    prec, rec, thr = precision_recall_curve(yva, p)
    f1 = 2 * prec * rec / np.maximum(prec + rec, 1e-12)
    best = int(np.nanargmax(f1))

    base_rate = yva.mean()
    print("\n" + "=" * 62)
    print("LSPR24 开发区流级诊断基线（非论文证据）")
    print("=" * 62)
    print(f"验证集正类基线率      {base_rate:.4f}")
    print(f"PR-AUC               {pr_auc:.4f}   （随机 = {base_rate:.4f}，提升 {pr_auc/base_rate:.1f}x）")
    print(f"ROC-AUC              {roc_auc:.4f}")
    print(f"最佳 F1              {f1[best]:.4f}  (P={prec[best]:.4f}, R={rec[best]:.4f}, thr={thr[min(best, len(thr)-1)]:.4f})")
    print("=" * 62)

    imp_idx = np.argsort(clf.feature_importances_)[::-1][:15] if hasattr(clf, "feature_importances_") else []
    if len(imp_idx):
        print("\n特征重要度 top15：")
        for i in imp_idx:
            print(f"  {feature_cols[i]:32} {clf.feature_importances_[i]:.4f}")


if __name__ == "__main__":
    main()
