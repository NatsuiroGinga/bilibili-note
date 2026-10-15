#!/usr/bin/env python
"""按固定 revision 拉取 LAMDA 数据集的 Baseline 视图（第三章 Domain-IL 复现所需）。

## 为什么需要这个脚本

数据集（341 MB / 28 文件）不入版本控制——它可从上游按固定 revision 重新获取，
而 Git 不适合存大文件。换机器后先跑本脚本，再跑实验脚本。

## 来源（取自已下载制品的 `manifest.json`，非记忆）

- 仓库：`IQSeC-Lab/LAMDA`
- revision：`ad9614bdd5556767f97ced2fce797c2f06408ebf`（2026-09-08 核验）
- DOI：`10.57967/hf/5563`
- 只取 `Baseline/**` 与 `README.md`；排除 `NPZ_Version/**`、`var_thresh_*/**`

## 落点

默认写到 `<仓库根>/thesis/experiments/llm_probe/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767`，
与实验脚本的 `DATA_ROOT` 约定一致。可用 `LAMDA_DATA_ROOT` 覆盖。

## 用法

    /opt/miniconda3/envs/rwkv/bin/python \
        thesis/experiments/llm_probe/scripts/download_lamda_baseline.py

    # 只验证落点与参数、不实际下载：
    ... download_lamda_baseline.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# ---- 上游来源（与 manifest.json 一致；改动前须核对上游） ----
REPO_ID = "IQSeC-Lab/LAMDA"
REVISION = "ad9614bdd5556767f97ced2fce797c2f06408ebf"
INCLUDE_PATTERNS = ["Baseline/**", "README.md"]
DATASET_DIRNAME = "lamda-iclr2026-baseline-ad9614bdd5556767"

# 实验脚本读的是 <repo>/thesis/experiments/llm_probe/runs/data-raw/<DATASET_DIRNAME>
# 本文件在 <repo>/thesis/experiments/llm_probe/scripts/ 下
#   parents[0]=scripts  parents[1]=llm_probe  ⇒ 取 parents[1]
DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "runs" / "data-raw" / DATASET_DIRNAME


def resolve_target() -> Path:
    """数据落点：环境变量优先，其次仓库内相对路径（不得硬编码本机绝对路径）。"""
    override = os.environ.get("LAMDA_DATA_ROOT")
    return Path(override).expanduser() if override else DEFAULT_ROOT


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="只打印将要执行的下载参数与落点，不实际下载")
    args = ap.parse_args()

    target = resolve_target()
    print(f"[repo]   {REPO_ID} @ {REVISION}")
    print(f"[取]     {', '.join(INCLUDE_PATTERNS)}")
    print(f"[落点]   {target}")

    if args.dry_run:
        print("[dry-run] 不执行下载。")
        return 0

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("[错误] 缺少 huggingface_hub。本机实验环境：\n"
              "  /opt/miniconda3/envs/rwkv/bin/python -m pip install huggingface_hub",
              file=sys.stderr)
        return 2

    target.mkdir(parents=True, exist_ok=True)
    # 注意：huggingface_hub 1.x 已移除 local_dir_use_symlinks，不要传该参数。
    snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        revision=REVISION,
        local_dir=str(target),
        allow_patterns=INCLUDE_PATTERNS,
    )

    parquet = sorted(target.glob("Baseline/*/*.parquet"))
    print(f"[完成] 落盘 {len(parquet)} 个 parquet 文件")
    if not parquet:
        print("[警告] 未找到 Baseline/**/*.parquet —— 上游结构可能已变，请核对 manifest.json",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
