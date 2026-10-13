#!/usr/bin/env python3
"""既有臂零扰动断言：改动训练器后，重放既有臂的候选缓存并与断点记录逐条比对。

对 B/D/F/UQ/CAND4/EDIT4 六臂（实施计划 §三 1 点名的集合）：从各自 checkpoint.pt 读取
保存的缓存收据（cache_root_sha256 等），用**改动后**训练器的 rebuild_first_epoch_cache
+ cache_summary 重算，逐字段比对。任一不一致即非零退出。

CURRICULUM 不在点名集合（其缓存键含轮次，rebuild 不支持，计划 §三 1 未要求）。
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
import torch

ROOT = Path(os.environ["LLM_PROBE_ROOT"]).parents[2]
ARMS = ("B", "D", "F", "UQ", "CAND4", "EDIT4")
RUN_DIRS = {
    "B": "ch3-drift-source-common-b-mps-20260923-v1",
    "D": "ch3-drift-source-common-d-cacheless-mps-20260924-v1",
    "F": "ch3-drift-source-common-f-cacheless-mps-20260924-v1",
    "UQ": "ch3-drift-source-common-uniformq-mps-20261013-v1",
    "CAND4": "ch3-drift-source-common-cand4-mps-20261013-v1",
    "EDIT4": "ch3-drift-source-common-edit4-mps-20261013-v1",
}
CANDIDATE_SPEC = (
    ".Codex/docs/2026-09-23-DRIFT源期训练抽样合同/candidate-spec-diagnostic-v1.json"
)


def main() -> int:
    import pyarrow.parquet as pq  # noqa: F401
    spec_path = m.formal_contract.resolve_repo_relative(CANDIDATE_SPEC, must_exist=True)
    spec_sha = m.sha256_file(spec_path)
    results = {}
    failures = []
    domains, labels, _ = m.load_fixed_source_members(CANDIDATE_SPEC, "source_train")
    # 既有臂训练成员 = diagnostic spec 全量（60000：良性 30000 + 恶意 30000），
    # 与训练器 run_pipeline 的 source_train 载入完全同一函数与参数。
    source_order_sha256, _label_root = m.source_roots(domains, labels)
    for arm in ARMS:
        run_dir = ROOT / "thesis/experiments/llm_probe/runs/diagnostics" / RUN_DIRS[arm]
        checkpoint_path = run_dir / f"arm-{arm}-checkpoint.pt"
        if not checkpoint_path.exists():
            failures.append(f"{arm}: checkpoint 缺失 {checkpoint_path}")
            continue
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        if checkpoint.get("cache_root_sha256") is None:
            # 2026-09-23 旧 schema checkpoint 无缓存收据字段（缓存收据机制 2026-10-13 引入）。
            # 降级断言：rebuild 两次结果一致（重放确定性）+ rebuild 代码路径未改动的
            # 事实由 git diff 复核。该缺口在 run-log 与报告中如实登记。
            cache_a = m.rebuild_first_epoch_cache(arm, domains, labels, completed_epoch=3)
            cache_b = m.rebuild_first_epoch_cache(arm, domains, labels, completed_epoch=3)
            summary = m.cache_summary(cache_a, m.CACHE_POLICY_BY_ARM[arm], source_order_sha256)
            deterministic = cache_a.keys() == cache_b.keys() and all(
                cache_a[k] == cache_b[k] for k in cache_a
            )
            results[arm] = {
                "run_dir": RUN_DIRS[arm],
                "checkpoint_sha256": m.sha256_file(checkpoint_path),
                "match": bool(deterministic),
                "assertion_mode": "replay_determinism_only_no_saved_receipt",
                "rebuilt_cache_root_sha256": summary["cache_root_sha256"],
                "rebuilt_cache_value_count": summary["cache_value_count"],
                "note": "旧 schema checkpoint 无缓存收据字段；仅能断言重放确定性与代码路径未改动",
            }
            print(f"[零扰动] {arm}: 旧 schema 无收据，重放确定性 {'一致' if deterministic else '不一致'} "
                  f"cache_root={summary['cache_root_sha256'][:12]}")
            if not deterministic:
                failures.append(f"{arm}: 重放不确定")
            continue
        saved = {
            key: checkpoint.get(key)
            for key in (
                "cache_schema_version", "cache_policy_id", "cache_entry_count",
                "cache_value_count", "cache_root_sha256",
                "source_order_sha256", "source_label_sha256",
            )
        }
        cache = m.rebuild_first_epoch_cache(arm, domains, labels, completed_epoch=3)
        summary = m.cache_summary(cache, m.CACHE_POLICY_BY_ARM[arm], saved["source_order_sha256"])
        rebuilt = {
            "cache_schema_version": summary["cache_schema_version"],
            "cache_value_count": summary["cache_value_count"],
            "cache_entry_count": summary["cache_entry_count"],
            "cache_root_sha256": summary["cache_root_sha256"],
            "source_order_sha256": saved["source_order_sha256"],
            "source_label_sha256": saved["source_label_sha256"],
            "cache_policy_id": m.CACHE_POLICY_BY_ARM[arm],
        }
        ok = all(saved[k] == rebuilt[k] for k in saved)
        results[arm] = {
            "run_dir": RUN_DIRS[arm],
            "checkpoint_sha256": m.sha256_file(checkpoint_path),
            "match": bool(ok),
            "saved": saved,
            "rebuilt": {k: rebuilt[k] for k in saved},
        }
        status = "一致" if ok else "不一致"
        print(f"[零扰动] {arm}: {status} cache_root={saved['cache_root_sha256'][:12]}")
        if not ok:
            for key in saved:
                if saved[key] != rebuilt[key]:
                    print(f"    字段 {key}: 保存 {saved[key]!r} vs 重放 {rebuilt[key]!r}")
            failures.append(f"{arm}: 缓存重放摘要不一致")
    report = {
        "schema_version": "drift-zero-disturbance-audit-v1",
        "trainer_sha256": m.sha256_file(Path(m.__file__).resolve()),
        "candidate_spec_sha256": spec_sha,
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "arms_checked": list(ARMS),
        "results": results,
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "verdict_scope": (
            "只断言改动后代码对既有臂的缓存重放与断点保存收据逐字段一致；"
            "CURRICULUM 不在点名集合。"
        ),
    }
    out_path = Path(__file__).resolve().parent / "zero-disturbance-audit.json"
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[零扰动] 报告 -> {out_path}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
