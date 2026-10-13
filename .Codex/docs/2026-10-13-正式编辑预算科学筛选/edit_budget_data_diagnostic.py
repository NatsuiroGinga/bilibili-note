#!/usr/bin/env python3
"""正式共享编辑 v2 预算定义的数据诊断（零训练、不读模型、不访问目标标签）。

问题：v2 规格待定的核心是半替换名义预算按**整串 L** 还是**可编辑位 |E|**取半。
两方案只在 ⌊L/2⌋ ≠ ⌊|E|/2⌋ 时产生差异——即含点（多标签）且长度奇偶错开的样本。
本脚本用**全量 eSLD** 给出：含点率、点数分布、L 与 |E| 的关系、两方案预算的
逐行差异率，并按源年 T17–T19 与目标年 T20–T25、良性与 DGA 分别报告。

口径（保守，与 v2 规格 §十二 一致的部分）：
  - 点号冻结，不参与替换；
  - |E| 暂按"非点位置数"计（IDNA/预留标签冻结在后续合法性审计中另计，本诊断不计）；
  - 恒等替换（替换成原字符）不计入预算，故实际可用位数可能略小于 |E|，本诊断只做上界估计。

只读 `domain` 列，流式 iter_batches，全量扫描不落中间文件。
输出：edit-budget-diagnostic-result.json（原子写）。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]
DATA = (ROOT / "thesis/experiments/llm_probe/runs/data-raw/"
        "drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521/DRIFT_input_eSLD")
OUT = Path(__file__).resolve().parent

SOURCE_FILES = [f"T{y}_{lab}_{split}"
                for y in (17, 18, 19) for lab in ("benign", "dga") for split in ("train", "test", "val")]
TARGET_FILES = [f"T{y}_{lab}" for y in (20, 21, 22, 23, 24, 25) for lab in ("benign", "dga")]

BATCH = 1 << 16


def scan(path: Path) -> dict:
    """流式统计单文件：行数、含点行、点数分布、两份预算的差异。"""
    pf = pq.ParquetFile(path)
    rows = with_dot = 0
    dot_hist: dict[int, int] = {}
    budget_diff = 0          # ⌊L/2⌋ != ⌊|E|/2⌋ 的行数（含点才有意义）
    budget_lt = budget_gt = 0
    len_sum = 0
    for batch in pf.iter_batches(batch_size=BATCH, columns=["domain"]):
        for raw in batch.column(0).to_pylist():
            if not isinstance(raw, str):
                continue
            s = raw.strip()
            if not s:
                continue
            rows += 1
            L = len(s)
            len_sum += L
            d = s.count(".")
            if d:
                with_dot += 1
                dot_hist[d] = dot_hist.get(d, 0) + 1
                E = L - d
                bl, be = L // 2, E // 2
                if bl != be:
                    budget_diff += 1
                    if bl < be:
                        budget_lt += 1
                    else:
                        budget_gt += 1
    return {
        "path": str(path.relative_to(ROOT)),
        "rows": rows,
        "rows_with_dot": with_dot,
        "dot_rate": round(with_dot / rows, 6) if rows else None,
        "mean_len": round(len_sum / rows, 4) if rows else None,
        "dot_count_hist": dict(sorted(dot_hist.items())),
        "budget_diff_rows": budget_diff,
        "budget_diff_rate_of_all": round(budget_diff / rows, 6) if rows else None,
        "budget_diff_rate_of_dotted": round(budget_diff / with_dot, 6) if with_dot else None,
        "budget_L_lt_E": budget_lt,
        "budget_L_gt_E": budget_gt,
    }


def main() -> int:
    started = time.monotonic()
    groups = {"source": SOURCE_FILES, "target": TARGET_FILES}
    result: dict = {"schema_version": "edit-budget-diagnostic-v1", "groups": {}}
    for gname, files in groups.items():
        rows_in_group = [f for f in files if (DATA / f"{f}.parquet").is_file()]
        missing = [f for f in files if not (DATA / f"{f}.parquet").is_file()]
        print(f"[{gname}] {len(rows_in_group)} 文件，缺 {len(missing)}", file=sys.stderr, flush=True)
        per_file: dict = {}
        for f in rows_in_group:
            t0 = time.monotonic()
            per_file[f] = scan(DATA / f"{f}.parquet")
            print(f"  {f}: rows={per_file[f]['rows']} dot={per_file[f]['dot_rate']} "
                  f"diff={per_file[f]['budget_diff_rate_of_all']} ({time.monotonic()-t0:.0f}s)",
                  file=sys.stderr, flush=True)
        # 组汇总
        tot = sum(v["rows"] for v in per_file.values())
        tot_dot = sum(v["rows_with_dot"] for v in per_file.values())
        tot_diff = sum(v["budget_diff_rows"] for v in per_file.values())
        result["groups"][gname] = {
            "missing_files": missing,
            "files": per_file,
            "summary": {
                "rows": tot,
                "rows_with_dot": tot_dot,
                "dot_rate": round(tot_dot / tot, 6) if tot else None,
                "budget_diff_rows": tot_diff,
                "budget_diff_rate_of_all": round(tot_diff / tot, 6) if tot else None,
                "budget_diff_rate_of_dotted": round(tot_diff / tot_dot, 6) if tot_dot else None,
            },
        }
    result["runtime_seconds"] = round(time.monotonic() - started, 1)
    tmp = OUT / "edit-budget-diagnostic-result.json.tmp"
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(OUT / "edit-budget-diagnostic-result.json")
    for g in ("source", "target"):
        s = result["groups"][g]["summary"]
        print(f"[{g} 汇总] rows={s['rows']} 含点率={s['dot_rate']} "
              f"两方案差异率(全体)={s['budget_diff_rate_of_all']} (含点内)={s['budget_diff_rate_of_dotted']}",
              file=sys.stderr, flush=True)
    print(f"[完成] {result['runtime_seconds']}s", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
