#!/usr/bin/env python3
"""ESAT 选择器：用 A 臂逐 epoch 快照的跨快照平均预测熵，在全源训练集上排序并冻结子集。

接口（ESAT 原文式(3)、§4.2 任务化迁移）：
- 熵 H(x) = −Σ σ_i log σ_i（两类：−p log p − (1−p) log(1−p)，自然对数）
- 平均跨 M=3 个快照（A 臂 3 轮逐 epoch 快照）
- 全源训练集（60000）降序排序，取熵最高 |A| = ceil(ρ·N)（ρ=0.5 → 30000）
- 并列按索引升序（np.argsort stable）
- 落盘 JSON：schema drift-esat-subset-v1，含 subset_indices、身份哈希、统计
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault(
    "LLM_PROBE_ROOT",
    "/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe",
)
sys.path.insert(
    0,
    "/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案",
)

import official_p2p3 as m
import numpy as np
import torch

ROOT = Path(os.environ["LLM_PROBE_ROOT"]).parents[2]
SNAPSHOT_DIR = ROOT / "thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-source-common-a-snapshot-mps-20261013-v1"
SPEC = ".Codex/docs/2026-09-23-DRIFT源期训练抽样合同/candidate-spec-diagnostic-v1.json"
RHO = 0.5  # ESAT 子集比例：原文 CIFAR 中点配置（25000/50000）的同比例映射；登记待主代理确认
OUT_PATH = ROOT / "thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-source-common-esat-mps-20261013-v1/esat-subset-rho0.5-v1.json"


def main() -> int:
    t0 = time.time()
    import pyarrow.parquet as pq  # noqa: F401
    spec_path = m.formal_contract.resolve_repo_relative(SPEC, must_exist=True)
    spec_sha = m.sha256_file(spec_path)
    domains, labels, _ = m.load_fixed_source_members(SPEC, "source_train")
    n = len(domains)
    subset_size = int(np.ceil(RHO * n))
    snapshot_dir = SNAPSHOT_DIR
    if not snapshot_dir.is_dir():
        raise FileNotFoundError(f"选择器快照目录不存在：{snapshot_dir}")
    snapshot_paths = sorted(snapshot_dir.glob("selector-snapshot-ep*.pt"))
    if len(snapshot_paths) != 3:
        raise FileNotFoundError(f"预期 3 个快照，实际 {len(snapshot_paths)}")
    tokenizer = m.official.PreTrainedTokenizerFast(
        tokenizer_file=str(m.REF / "artifacts/tokenizer/tokenizer-0-30522-both.json")
    )
    # 特征均值与训练时同一来源（源训练成员均值，供 probabilities 的 static_fusion 融合）
    tok_mean, char_mean = None, None
    entropies = []
    with torch.inference_mode():
        for snap_path in snapshot_paths:
            payload = torch.load(snap_path, map_location="cpu", weights_only=True)
            if payload.get("arm") != "A":
                raise ValueError(f"快照 arm 字段不符：{snap_path}")
            model = m.load_mps_model()
            model.load_state_dict(payload["model"])
            model.eval()
            if tok_mean is None:
                tok_mean, char_mean = m.source_feature_means(model, tokenizer, domains)
            scores_all = []
            for off in range(0, n, m.EVAL_BATCH):
                chunk = domains[off:off + m.EVAL_BATCH]
                tk = m.official.encode_subword(chunk, tokenizer).to(m.DEVICE)
                ch = m.official.encode_char(chunk).to(m.DEVICE)
                with m.autocast_ctx():
                    tf, cf = m.diag.branch_features(model, tk, ch)
                s = m.diag.probabilities(
                    model, tf.cpu().numpy(), cf.cpu().numpy(),
                    tok_mean, char_mean, m.DEVICE, m.EVAL_BATCH,
                )["static_fusion"]
                scores_all.append(np.asarray(s, dtype=np.float64))
            p = np.concatenate(scores_all)
            if len(p) != n:
                raise RuntimeError(f"熵评分未覆盖全部样本：{len(p)} vs {n}")
            eps = 1e-12
            p_c = np.clip(p, eps, 1 - eps)
            h = -(p_c * np.log(p_c) + (1 - p_c) * np.log(1 - p_c))
            entropies.append(h)
            print(f"[ESAT 选择器] 快照 {snap_path.name} 熵计算完成（{time.time()-t0:.0f}s）", flush=True)
    if len(entropies) != 3:
        raise RuntimeError("快照熵数量不符")
    mean_entropy = np.mean(entropies, axis=0)
    # 降序排序取 top（并列按索引升序：np.argsort stable）
    order = np.argsort(-mean_entropy, kind="stable")
    subset = sorted(int(i) for i in order[:subset_size])
    n_mal = int(np.count_nonzero(labels == 1))
    subset_mal = int(labels[subset].sum())
    payload = {
        "schema_version": "drift-esat-subset-v1",
        "rho": RHO,
        "subset_size": subset_size,
        "n_train": n,
        "n_mal_train": n_mal,
        "subset_mal_count": subset_mal,
        "subset_benign_count": subset_size - subset_mal,
        "snapshot_files": [p.name for p in snapshot_paths],
        "snapshot_sha256": [m.sha256_file(p) for p in snapshot_paths],
        "candidate_spec_sha256": spec_sha,
        "entropy_definition": "-p*log(p)-(1-p)*log(1-p)，自然对数，跨 3 快照平均",
        "tie_break": "np.argsort stable（熵并列按索引升序）",
        "rho_provenance": (
            "ESAT 原文 CIFAR 中点配置 25000/50000=50% 的同比例映射；"
            "原文未给通用比例，该值登记待主代理确认（实施计划未给出比例数值）"
        ),
        "subset_indices": subset,
        "trainer_sha256": m.sha256_file(Path(m.__file__).resolve()),
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
    }
    out_path = OUT_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"[ESAT 选择器] 子集 |A|={subset_size}（恶意 {subset_mal} / 良性 {subset_size - subset_mal}）"
        f" -> {out_path}（{time.time()-t0:.0f}s）",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
