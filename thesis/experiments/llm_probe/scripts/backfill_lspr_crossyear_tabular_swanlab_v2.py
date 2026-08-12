"""把已完成的 LSPR 跨年度表格基线指标补传到 SwanLab。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import swanlab


MODELS = ("hgb", "random_forest", "xgboost")
WORKSPACE = "mortiswang"
PROJECT = "malicious-traffic-llm"


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def backfill(model_dir: Path) -> dict[str, object]:
    receipt_path = model_dir / "swanlab-backfill.json"
    if receipt_path.is_file():
        return load_json(receipt_path)

    metrics = load_json(model_dir / "metrics.json")
    target = metrics["target_development"]
    source = metrics["source_validation"]
    if not isinstance(target, dict) or not isinstance(source, dict):
        raise ValueError(f"指标结构不完整：{model_dir}")
    threshold_key = "source_validation_macro_f1_optimal"
    target_selected = target[threshold_key]
    source_selected = source[threshold_key]
    target_half = target["0.5"]
    if not all(isinstance(item, dict) for item in (target_selected, source_selected, target_half)):
        raise ValueError(f"阈值指标结构不完整：{model_dir}")

    matrix = target_half["confusion_matrix"]
    total = sum(sum(int(value) for value in row) for row in matrix)
    positives = int(matrix[1][0]) + int(matrix[1][1])
    model_name = str(metrics["model"])
    seed = int(metrics["seed"])
    run_name = f"c12-q0-crossyear-{model_name}-seed{seed}"
    run = swanlab.init(
        project=PROJECT,
        workspace=WORKSPACE,
        name=run_name,
        config={
            "model": model_name,
            "seed": seed,
            "input_dimension": int(metrics["input_dimension"]),
            "row_counts": metrics["row_counts"],
            "source": "已封存的 metrics.json 回填",
            "final_accessed": False,
        },
        mode="online",
        log_dir=str(model_dir / "swanlog-backfill"),
    )
    swanlab.log(
        {
            "source_validation/pr_auc": float(source_selected["pr_auc"]),
            "source_validation/macro_f1": float(source_selected["macro_f1"]),
            "target_development/pr_auc": float(target_selected["pr_auc"]),
            "target_development/macro_f1": float(target_selected["macro_f1"]),
            "target_development/malicious_f1": float(target_selected["malicious_f1"]),
            "target_development/precision": float(target_selected["precision"]),
            "target_development/recall": float(target_selected["recall"]),
            "target_development/prevalence": positives / total,
            "runtime/training_seconds": float(metrics["resource"]["training_seconds"]),
            "runtime/inference_seconds": float(metrics["resource"]["inference_seconds"]),
        },
        step=0,
    )
    run_id = str(run.id)
    run.finish()
    receipt = {
        "workspace": WORKSPACE,
        "project": PROJECT,
        "run_name": run_name,
        "run_id": run_id,
        "url": f"https://swanlab.cn/@{WORKSPACE}/{PROJECT}/runs/{run_id}",
        "source": str(model_dir / "metrics.json"),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "final_accessed": False,
    }
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="补传 C12 Q0 表格基线指标到 SwanLab")
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--model", choices=MODELS, required=True)
    args = parser.parse_args()
    receipt = backfill(args.run_root / args.model)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
