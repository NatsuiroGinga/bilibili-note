#!/usr/bin/env python3
"""DRIFT 第三章 P0：B／D／F（＋A 参照）源冻结检查点的零训练合法共享编辑攻击复评。

判据与交付见 ``thesis/methods/第三章-数据模型机制统一候选筛选台账.md`` §八 P0 段；
算子与预算规格见 ``thesis/methods/第三章-正式攻击与目标抽样合同裁决.md`` §十二；
源成员、阈值与评分口径与 ``ch3-drift-source-low-fpr-bdf-mps-20260924-v3`` 完全一致。

零训练：只做前向评分；不训练、不重标阈值、不改成员与分母；不访问 T20–T25。
本脚本只报告读数与机械判据对照，不做晋级／淘汰裁决。
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

SCHEMA_VERSION = "ch3-drift-source-p0-legal-attack-v1"
RUN_NAME = "ch3-drift-source-p0-legal-attack-bdf-mps-20261013-v1"
# 攻击流锚点：D-4 已产出的流身份。D-5 追加 UQ 臂时必须复用同一 stream_id，
# 否则攻击串改变、A/B/D/F 读数无法逐位复现。
STREAM_ANCHOR = RUN_NAME
RUNS = {
    "A": "ch3-drift-source-common-a-mps-20260923-v1",
    "B": "ch3-drift-source-common-b-mps-20260923-v1",
    "D": "ch3-drift-source-common-d-cacheless-mps-20260924-v1",
    "F": "ch3-drift-source-common-f-cacheless-mps-20260924-v1",
    "UQ": "ch3-drift-source-common-uniformq-mps-20261013-v1",
    # D-6/D-7 追加臂（2026-10-13）
    "CAND4": "ch3-drift-source-common-cand4-mps-20261013-v1",
    "EDIT4": "ch3-drift-source-common-edit4-mps-20261013-v1",
    "CURRICULUM": "ch3-drift-source-common-curriculum-mps-20261013-v1",
    # P1 近邻/内部对照五臂（2026-10-13，实施计划 .Codex/docs/2026-10-13-外部基准与第二骨干/）
    "C1R": "ch3-drift-source-common-c1r-mps-20261013-v1",
    "ESAT": "ch3-drift-source-common-esat-mps-20261013-v1",
    "DRICHEL": "ch3-drift-source-common-drichel-mps-20261013-v1",
    "CEQ": "ch3-drift-source-common-ceq-mps-20261013-v1",
    "CBN": "ch3-drift-source-common-cbn-mps-20261013-v1",
}
# 既有语义保持不变：主判据臂仍是 B/D/F。
PRIMARY_ARMS = ("B", "D", "F")
# 追加臂：仅作归因参照，不进 P0 支持门。
ATTRIBUTION_ARMS = ("UQ",)
PAIRED_ARMS = (
    ("B", "D"), ("B", "F"), ("B", "A"), ("B", "UQ"), ("D", "UQ"), ("F", "UQ"),
    # D-6 单因素链：cand4 对照 D/F（同固定 64 入批），edit4 对照 B（同 n_mal 入批分布）
    ("D", "CAND4"), ("F", "CAND4"), ("B", "CAND4"),
    ("B", "EDIT4"), ("D", "EDIT4"), ("F", "EDIT4"),
    # D-7 课程臂对照：恒定弱核 B、恒定中核 EDIT4、恒定强核 D/F
    ("B", "CURRICULUM"), ("EDIT4", "CURRICULUM"), ("D", "CURRICULUM"), ("F", "CURRICULUM"),
    # 两个新核之间的对照（候选数 vs 编辑位数）
    ("CAND4", "EDIT4"),
    # P1 近邻/内部对照五臂（2026-10-13）：配比、排序分数、静态权重、固定子集、白盒生成
    ("B", "C1R"), ("D", "CEQ"), ("F", "CEQ"), ("F", "CBN"),
    ("B", "ESAT"), ("F", "ESAT"), ("B", "DRICHEL"), ("F", "DRICHEL"),
    ("C1R", "ESAT"), ("C1R", "DRICHEL"),
)
EXPECTED_CODE_SHA256 = {
    "A": "8ab6307f18142aae829a96565c46206f6ca8a70cfef09804b1e9e21411c5b44b",
    "B": "8ab6307f18142aae829a96565c46206f6ca8a70cfef09804b1e9e21411c5b44b",
    "D": "0705c24be7e5cbc0716a99f360781bb9394378d34e2ed96103077961d4bbacef",
    "F": "0705c24be7e5cbc0716a99f360781bb9394378d34e2ed96103077961d4bbacef",
    # UQ 只改选择规则，代码哈希与 D/F 必然不同（已知项，不视为阻塞）。
    "UQ": "59d50aaf71d19b9ff796b1785b5f053d0b1bf68da49e6f226201d0666903155b",
    # CAND4/EDIT4 用追加 D-6 两臂时的训练器代码（同一份），CURRICULUM 用 D-7 参数化课程核版本。
    "CAND4": "123fd0638f290e8ed4b67040f41fe86832c6811134f0c8a89fd417cd5850d8b8",
    "EDIT4": "123fd0638f290e8ed4b67040f41fe86832c6811134f0c8a89fd417cd5850d8b8",
    "CURRICULUM": "1fdf6dda29e7c0559793253364bf75c7fa4d53fba7bab8269bb60aa6706e6174",
    "C1R": "e7fced237668a1b6a671c5bc88b45c4badd821d8a9b15eec828bfde939974743",
    "ESAT": "e7fced237668a1b6a671c5bc88b45c4badd821d8a9b15eec828bfde939974743",
    "DRICHEL": "e7fced237668a1b6a671c5bc88b45c4badd821d8a9b15eec828bfde939974743",
    "CEQ": "e7fced237668a1b6a671c5bc88b45c4badd821d8a9b15eec828bfde939974743",
    "CBN": "e7fced237668a1b6a671c5bc88b45c4badd821d8a9b15eec828bfde939974743",
}
COMMON_IDENTITY_FIELDS = (
    "batch",
    "candidate_spec_sha256",
    "checkpoint_sha256",
    "device",
    "dry_run",
    "epochs",
    "feature_adapter_sha256",
    "member_selector_sha256",
    "model_loader_sha256",
    "precision",
    "seed",
    "source_revision",
)
ALPHAS = (("fpr_0_001", 0.001), ("fpr_0_01", 0.01))
THRESHOLD_0_5 = "threshold_0_5"
EXPECTED_CLASS_COUNT = 30_000
OPERATOR_RELATIVE = "thesis/experiments/llm_probe/tools/ch3_drift_formal_edit_v2.py"
EXPECTED_OPERATOR_SHA256 = "fb6f54294cd5795df3fd92076bce9cc30f918cb32e02c69971687765db77927e"
CANDIDATE_SPEC_RELATIVE = (
    ".Codex/docs/2026-09-23-DRIFT源期训练抽样合同/candidate-spec-diagnostic-v1.json"
)
V3_RUN_NAME = "ch3-drift-source-low-fpr-bdf-mps-20260924-v3"
# v3 已冻结源阈值与干净 DGA 漏检，用于复核「干净侧读数保持不变」。
V3_FROZEN = {
    "B": {
        "fpr_0_001": {"threshold": 0.9962557554244995, "dga_fn": 7457, "fp": 30},
        "fpr_0_01": {"threshold": 0.8804716467857361, "dga_fn": 1943, "fp": 300},
    },
    "D": {
        "fpr_0_001": {"threshold": 0.9951802492141724, "dga_fn": 7878, "fp": 30},
        "fpr_0_01": {"threshold": 0.8792877197265625, "dga_fn": 2149, "fp": 300},
    },
    "F": {
        "fpr_0_001": {"threshold": 0.9890807867050171, "dga_fn": 7703, "fp": 30},
        "fpr_0_01": {"threshold": 0.7487272620201111, "dga_fn": 2134, "fp": 300},
    },
}
# 主攻击档：既有预登记把 `maskdga` 半替换标为「强攻击，主判据面板」、`k2` 标为弱攻击；
# §八 P0 只写「预先指定的主攻击档」未点名档位，故同时机械报告三档，主读数为 random_half。
PRIMARY_TIER = "random_half"
PRIMARY_ALPHA = "fpr_0_001"
# 变更 B（D-6 追加）：固定预算梯度 q = 1/2/4/8/16（对应 Tramer 意义的威胁集梯度），
# 用于「漏检率 vs 攻击预算」曲线；q=1/2 与既有 k1/k2 档逐位相同，评分直接复用不重算。
LADDER_Q = (1, 2, 4, 8, 16)
LADDER_REUSE = {1: "k1", 2: "k2"}
# 长度分面（按 exact eSLD 长度分档；|E| 与长度同源，源年含点率为 0）
LENGTH_BUCKETS = (("le8", 1, 8), ("9to20", 9, 20), ("gt20", 21, 10 ** 9))



def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sha256_sequence(values: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for value in values:
        raw = value.encode("utf-8")
        digest.update(len(raw).to_bytes(8, "big", signed=False))
        digest.update(raw)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"JSON 根节点不是对象：{path.name}")
    return value


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    with partial.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(partial, path)


def detect_concurrent_tasks(self_pid: int | None = None) -> list[dict[str, Any]]:
    """记录本机同时运行的其他重任务（只读快照，用于并发披露）。"""
    import subprocess

    self_pid = os.getpid() if self_pid is None else self_pid
    try:
        output = subprocess.run(
            ["ps", "-Axo", "pid,%cpu,rss,command"],
            capture_output=True, text=True, timeout=15, check=False,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    found: list[dict[str, Any]] = []
    for line in output.splitlines()[1:]:
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        pid_text, cpu_text, rss_text, command = parts
        try:
            pid = int(pid_text)
            cpu = float(cpu_text)
            rss = int(rss_text)
        except ValueError:
            continue
        if pid == self_pid or cpu < 5.0:
            continue
        if "python" not in command:
            continue
        found.append({"pid": pid, "cpu_percent": cpu, "rss_kib": rss, "command": command[:300]})
    return found


def log_stage(stage: str, processed: int, total: int) -> None:
    print(
        json.dumps({"阶段": stage, "已处理": processed, "总数": total}, ensure_ascii=False),
        file=sys.stderr,
        flush=True,
    )


# ------------------------------------------------------------------ 身份核验


def validate_arms(
    root: Path,
    candidate_spec: Path,
    official: Any,
    diag: Any,
    eligibility: Any,
    arms: Sequence[str] = tuple(RUNS),
    run_map: dict[str, str] | None = None,
    expected_code_by_arm: dict[str, str] | None = EXPECTED_CODE_SHA256,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], str, dict[str, str]]:
    candidate_sha = sha256_file(candidate_spec)
    expected_artifact_hashes = {
        "checkpoint_sha256": sha256_file(official.CKPT),
        "model_loader_sha256": sha256_file(Path(official.official.__file__)),
        "feature_adapter_sha256": sha256_file(Path(diag.__file__)),
        "member_selector_sha256": sha256_file(Path(eligibility.__file__)),
    }
    identities: dict[str, dict[str, Any]] = {}
    payloads: dict[str, dict[str, Any]] = {}
    checkpoint_hashes: dict[str, str] = {}
    expected_members: Any = None
    expected_common: Any = None
    observed_code_hashes: dict[str, list[str]] = {}

    run_map = dict(RUNS) if run_map is None else dict(run_map)
    for arm in arms:
        run_name = run_map[arm]
        run_dir = root / "thesis/experiments/llm_probe/runs/diagnostics" / run_name
        status_path = run_dir / "run-status.json"
        checkpoint_path = run_dir / f"arm-{arm}-checkpoint.pt"
        arm_result_path = run_dir / f"arm-{arm}-result.json"
        total_result_path = run_dir / f"source-common-{arm.lower()}-result.json"
        for path in (status_path, checkpoint_path, arm_result_path, total_result_path):
            if not path.is_file():
                raise FileNotFoundError(f"缺少已完成运行制品：{path.relative_to(root)}")

        status = read_json(status_path)
        identity = status.get("identity")
        if not isinstance(identity, dict):
            raise ValueError(f"{arm} 运行身份缺失")
        if status.get("phase") != "completed":
            raise ValueError(f"{arm} 运行状态不是 completed")
        arm_status = status.get("arms", {}).get(arm, {})
        if arm_status.get("phase") != "completed" or arm_status.get("epoch") != 3:
            raise ValueError(f"{arm} 臂未完成第三轮")
        if identity.get("arms") != [arm] or identity.get("epochs") != 3:
            raise ValueError(f"{arm} 运行身份的臂或轮次不符")
        if expected_code_by_arm is None:
            # 小规模复评：各臂由同一份训练器代码训练，要求四臂代码哈希完全一致。
            observed_code_hashes.setdefault(str(identity.get("code_sha256")), []).append(arm)
        elif identity.get("code_sha256") != expected_code_by_arm[arm]:
            raise ValueError(f"{arm} 运行代码哈希不属于已登记版本")
        if identity.get("candidate_spec_sha256") != candidate_sha:
            raise ValueError(f"{arm} 候选规格哈希不符")
        for key, expected in expected_artifact_hashes.items():
            if identity.get(key) != expected:
                raise ValueError(f"{arm} 运行依赖身份不符：{key}")
        if identity.get("device") != "mps" or identity.get("precision") != "fp32":
            raise ValueError(f"{arm} 运行设备或精度不符")
        if identity.get("batch") != 128 or identity.get("seed") != 42:
            raise ValueError(f"{arm} 运行批量或随机种子不符")
        if identity.get("dry_run") != 0 or identity.get("source_revision") != official.DATA.name:
            raise ValueError(f"{arm} 运行模式或源数据版本不符")

        common = {key: identity.get(key) for key in COMMON_IDENTITY_FIELDS}
        if expected_common is None:
            expected_common = common
        elif common != expected_common:
            raise ValueError(f"{arm} 与其他臂的冻结运行身份不一致")

        arm_result = read_json(arm_result_path)
        if arm_result.get("arm") != arm or arm_result.get("identity") != identity:
            raise ValueError(f"{arm} 单臂结果与运行身份不一致")
        total_result = read_json(total_result_path)
        source_members = total_result.get("source_members")
        if not isinstance(source_members, dict):
            raise ValueError(f"{arm} 总结果缺源成员收据")
        if expected_members is None:
            expected_members = source_members
        elif source_members != expected_members:
            raise ValueError("各臂源成员收据不一致")
        if total_result.get("results", {}).get(arm) != arm_result.get("result"):
            raise ValueError(f"{arm} 总结果与单臂结果不一致")

        identities[arm] = identity
        checkpoint_hashes[arm] = sha256_file(checkpoint_path)
        payloads[arm] = {
            "run_dir": run_dir,
            "checkpoint_path": checkpoint_path,
            "arm_result": arm_result,
            "source_members": source_members,
        }

    if expected_code_by_arm is None and len(observed_code_hashes) != 1:
        raise ValueError(f"小规模各臂训练器代码哈希不一致：{observed_code_hashes}")
    return identities, payloads, sha256_json(expected_members), checkpoint_hashes


# ------------------------------------------------------------------ 攻击生成


def ladder_outputs(operator: Any, domain: str, stream_id: str) -> tuple[dict[int, str], int]:
    """固定预算梯度输出：用冻结 v2 算子的共享 plan 取前 min(q, |E|) 项。

    只读取算子的原语（不修改算子），因此与 k1/k2/random_half 使用**同一条流**，
    q=1/2 的输出与 k1/k2 逐位相同。
    """
    detail, _ = operator._editable_detail(domain)
    plan, _ = operator._shared_edit_plan(domain, stream_id, detail)
    outputs: dict[int, str] = {}
    for q in LADDER_Q:
        applied = plan[: min(q, len(plan))]
        outputs[q] = operator._apply_plan(domain, applied) if applied else domain
    return outputs, len(plan)


def length_bucket(length: int) -> str:
    for name, low, high in LENGTH_BUCKETS:
        if low <= length <= high:
            return name
    raise ValueError(f"长度 {length} 不属于任何分面")


def build_attacks(
    operator: Any, dga_domains: list[str], stream_id: str, log
) -> dict[str, Any]:
    """用 v2 算子在源 DGA 成员上生成三档攻击，并机械核验合法性。"""
    syntax_pass = 0
    per_tier: dict[str, list[str]] = {tier: [] for tier in operator.TIERS}
    per_ladder: dict[int, list[str]] = {q: [] for q in LADDER_Q}
    ladder_hamming: dict[int, list[int]] = {q: [] for q in LADDER_Q}
    ladder_q_actual: dict[int, list[int]] = {q: [] for q in LADDER_Q}
    ladder_equal_to_tier = {q: 0 for q in LADDER_Q}
    bucket_names = [name for name, _, _ in LENGTH_BUCKETS]
    bucket_counts: dict[str, int] = {name: 0 for name in bucket_names}
    bucket_ladder: dict[str, dict[int, int]] = {name: {q: 0 for q in LADDER_Q} for name in bucket_names}
    q_values: dict[str, list[int]] = {tier: [] for tier in operator.TIERS}
    n_e_values: list[int] = []
    lengths: list[int] = []
    output_syntax_pass = {tier: 0 for tier in operator.TIERS}
    failures: list[dict[str, Any]] = []
    error_counts = {tier: 0 for tier in operator.TIERS}

    for index, domain in enumerate(dga_domains):
        if not operator.validate_basic_syntax(domain)["ok"]:
            failures.append({"index": index, "domain": domain, "reason": "invalid_source_syntax"})
            continue
        syntax_pass += 1
        detail = operator.editable_positions(domain)
        n_e_values.append(detail["n_e"])
        lengths.append(detail["L"])
        for tier in operator.TIERS:
            result = operator.generate(domain, tier, stream_id)
            if not result["ok"]:
                error_counts[tier] += 1
                failures.append({"index": index, "domain": domain, "tier": tier,
                                 "reason": result["reason"]})
                per_tier[tier].append(domain)
                continue
            if not operator.validate_basic_syntax(result["output"])["ok"]:
                failures.append({"index": index, "domain": domain, "tier": tier,
                                 "reason": "illegal_output"})
                per_tier[tier].append(domain)
                continue
            output_syntax_pass[tier] += 1
            per_tier[tier].append(result["output"])
            q_values[tier].append(int(result["q_actual"]))
        outputs, n_e = ladder_outputs(operator, domain, stream_id)
        for q in LADDER_Q:
            text = outputs[q]
            per_ladder[q].append(text)
            ladder_hamming[q].append(sum(1 for a, b in zip(domain, text) if a != b))
            ladder_q_actual[q].append(min(q, n_e))
            if not operator.validate_basic_syntax(text)["ok"]:
                failures.append({"index": index, "domain": domain, "q": q,
                                 "reason": "illegal_ladder_output"})
            reuse = LADDER_REUSE.get(q)
            if reuse is not None and text == per_tier[reuse][-1]:
                ladder_equal_to_tier[q] += 1
        name = length_bucket(len(domain))
        bucket_counts[name] += 1
        for q in LADDER_Q:
            if ladder_hamming[q][-1] == min(q, n_e):
                bucket_ladder[name][q] += 1
        if index and index % 10_000 == 0:
            log(f"攻击生成 {index}/{len(dga_domains)}")

    tier_summary: dict[str, Any] = {}
    for tier in operator.TIERS:
        values = np.asarray(q_values[tier], dtype=np.int64)
        tier_summary[tier] = {
            "n_outputs": len(per_tier[tier]),
            "q_actual_mean": float(values.mean()) if len(values) else None,
            "q_actual_min": int(values.min()) if len(values) else None,
            "q_actual_max": int(values.max()) if len(values) else None,
            "q_actual_quantiles": {
                key: float(np.quantile(values, value))
                for key, value in (("p10", 0.10), ("p25", 0.25), ("p50", 0.50),
                                   ("p75", 0.75), ("p90", 0.90), ("p99", 0.99))
            } if len(values) else {},
            "output_syntax_pass": output_syntax_pass[tier],
            "output_syntax_pass_rate": (
                output_syntax_pass[tier] / len(per_tier[tier]) if per_tier[tier] else None
            ),
            "generation_errors": error_counts[tier],
            "attacked_sha256": sha256_sequence(per_tier[tier]),
        }
    ladder_summary: dict[str, Any] = {}
    for q in LADDER_Q:
        values = np.asarray(ladder_hamming[q], dtype=np.int64)
        ladder_summary[str(q)] = {
            "n_outputs": len(per_ladder[q]),
            "nominal_q": q,
            "hamming_mean": float(values.mean()) if len(values) else None,
            "hamming_min": int(values.min()) if len(values) else None,
            "hamming_max": int(values.max()) if len(values) else None,
            "hamming_quantiles": {
                key: float(np.quantile(values, value))
                for key, value in (("p10", 0.10), ("p50", 0.50), ("p90", 0.90))
            } if len(values) else {},
            # 算子从不欠账：Hamming 恒等于 min(q, |E|)（下表应为 0）
            "undershoot_share": (
                float(np.mean(np.asarray(ladder_hamming[q]) < np.asarray(ladder_q_actual[q])))
                if len(values) else None
            ),
            # |E| < q 的成员占比（名义预算不可行，实际被 min(q, |E|) 截断）
            "capped_share": (
                float(np.mean(np.asarray(ladder_q_actual[q]) < q)) if len(values) else None
            ),
            "q_actual_mean": (
                float(np.mean(np.asarray(ladder_q_actual[q]))) if len(values) else None
            ),
            "q_actual_min": (
                int(np.min(np.asarray(ladder_q_actual[q]))) if len(values) else None
            ),
            "equals_tier_outputs": (
                ladder_equal_to_tier[q] / len(per_ladder[q]) if per_ladder[q] else None
            ),
            "attacked_sha256": sha256_sequence(per_ladder[q]),
        }
    n_e_array = np.asarray(n_e_values, dtype=np.int64)
    length_array = np.asarray(lengths, dtype=np.int64)
    return {
        "attacked": per_tier,
        "ladder": per_ladder,
        "ladder_hamming": {q: list(map(int, ladder_hamming[q])) for q in LADDER_Q},
        "ladder_bucket_counts": bucket_counts,
        "ladder_bucket_saturated": bucket_ladder,
        "ladder_summary": ladder_summary,
        "summary": {
            "source_members": len(dga_domains),
            "source_syntax_pass": syntax_pass,
            "source_syntax_pass_rate": syntax_pass / len(dga_domains) if dga_domains else None,
            "source_length_mean": float(length_array.mean()) if len(length_array) else None,
            "source_length_min": int(length_array.min()) if len(length_array) else None,
            "source_length_max": int(length_array.max()) if len(length_array) else None,
            "source_n_e_mean": float(n_e_array.mean()) if len(n_e_array) else None,
            "source_n_e_min": int(n_e_array.min()) if len(n_e_array) else None,
            "tiers": tier_summary,
            "failures": failures[:50],
            "failure_count": len(failures),
        },
    }


# ------------------------------------------------------------------ 评分与指标


def freeze_group_threshold(scores: np.ndarray, alpha: float) -> tuple[float, int, int]:
    """按并列概率组整体选择阈值，实际 FP 不超过预算（与 v3 同一算法）。"""
    if scores.ndim != 1 or not len(scores):
        raise ValueError("阈值输入必须是非空一维源良性分数")
    budget = math.floor(alpha * len(scores))
    values, counts = np.unique(scores, return_counts=True)
    accepted = 0
    threshold: float | None = None
    for value, count in zip(values[::-1], counts[::-1], strict=True):
        if accepted + int(count) > budget:
            break
        accepted += int(count)
        threshold = float(value)
    if threshold is None:
        threshold = math.nextafter(float(values[-1]), math.inf)
    actual_fp = int(np.count_nonzero(scores >= threshold))
    if actual_fp != accepted or actual_fp > budget:
        raise RuntimeError("整同分组阈值未满足冻结 FP 预算")
    return threshold, actual_fp, budget


def score_domains(
    label: str,
    domains: list[str],
    model: Any,
    tokenizer: Any,
    tok_mean: np.ndarray,
    char_mean: np.ndarray,
    official: Any,
    diag: Any,
) -> np.ndarray:
    scores: list[np.ndarray] = []
    total = len(domains)
    model.eval()
    with torch.inference_mode():
        for offset in range(0, total, official.EVAL_BATCH):
            chunk = domains[offset : offset + official.EVAL_BATCH]
            token_ids = official.official.encode_subword(chunk, tokenizer).to(official.DEVICE)
            char_ids = official.official.encode_char(chunk).to(official.DEVICE)
            with official.autocast_ctx():
                token_features, char_features = diag.branch_features(model, token_ids, char_ids)
            probabilities = diag.probabilities(
                model,
                token_features.cpu().numpy(),
                char_features.cpu().numpy(),
                tok_mean,
                char_mean,
                official.DEVICE,
                official.EVAL_BATCH,
            )["static_fusion"]
            scores.append(np.asarray(probabilities, dtype=np.float64))
            processed = min(offset + len(chunk), total)
            if processed == total or processed % (official.EVAL_BATCH * 20) < len(chunk):
                log_stage(f"{label} 评分", processed, total)
    result = np.concatenate(scores)
    if len(result) != total or not np.isfinite(result).all():
        raise ValueError(f"{label} 分数数量不符或包含非有限值")
    if np.any((result < 0.0) | (result > 1.0)):
        raise ValueError(f"{label} 概率超出 [0, 1]")
    return result


def paired_error_counts(
    predictions: dict[str, np.ndarray], expected: int = EXPECTED_CLASS_COUNT
) -> dict[str, dict[str, int]]:
    lengths = {len(values) for values in predictions.values()}
    if lengths != {expected}:
        raise ValueError(f"配对计数输入长度必须同为 {expected}")
    output: dict[str, dict[str, int]] = {}
    for left, right in PAIRED_ARMS:
        if left not in predictions or right not in predictions:
            continue
        left_wrong = ~predictions[left]
        right_wrong = ~predictions[right]
        output[f"{left}-{right}"] = {
            f"{left}_only_wrong": int(np.count_nonzero(left_wrong & ~right_wrong)),
            f"{right}_only_wrong": int(np.count_nonzero(~left_wrong & right_wrong)),
            "both_wrong": int(np.count_nonzero(left_wrong & right_wrong)),
            "both_correct": int(np.count_nonzero(~left_wrong & ~right_wrong)),
            "n_dga": int(len(left_wrong)),
        }
    return output


def parse_args() -> argparse.Namespace:
    default_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=default_root)
    parser.add_argument(
        "--stream-id",
        default=f"p0-legal-attack|shared_prefix_edit_v2|{STREAM_ANCHOR}",
        help="攻击流身份；追加臂必须复用 D-4 的同一值",
    )
    parser.add_argument("--run-name", default=RUN_NAME, help="本次运行的可读身份名")
    parser.add_argument(
        "--candidate-spec",
        default=CANDIDATE_SPEC_RELATIVE,
        help="仓库相对候选规格路径；小规模一致性验证改用 1/4 规格",
    )
    parser.add_argument(
        "--arms",
        default=",".join(RUNS),
        help="逗号分隔的臂子集（默认全部）；小规模验证只需 B,D,F,UQ",
    )
    parser.add_argument(
        "--run-map",
        default=None,
        help="可选：逗号分隔的 ARM=运行目录名 覆盖（默认用 RUNS 的全规模映射）；"
             "缩样本验证时指向 1/4 规模运行目录",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("thesis/experiments/llm_probe/runs/diagnostics") / RUN_NAME,
    )
    parser.add_argument("--resume", action="store_true",
                        help="允许在已有 run-status.json 显示 running 时续跑（仅调试用）")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.project_root.resolve()
    run_dir = args.run_dir if args.run_dir.is_absolute() else root / args.run_dir
    run_dir = run_dir.resolve()
    status_path = run_dir / "run-status.json"
    result_path = run_dir / "p0-legal-attack-result.json"
    log_path = run_dir / "console.log"
    if status_path.exists() and not args.resume:
        raise FileExistsError(f"运行目录已有 run-status.json，拒绝覆盖：{status_path}")

    llm_root = root / "thesis/experiments/llm_probe"
    tool_root = llm_root / "tools"
    official_root = root / ".Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案"
    if not tool_root.is_dir() or not official_root.is_dir():
        raise FileNotFoundError("DRIFT 评分工具目录不存在")
    os.environ["LLM_PROBE_ROOT"] = str(llm_root)
    sys.path.insert(0, str(tool_root))
    sys.path.insert(0, str(official_root))

    run_dir.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("a", encoding="utf-8")

    def log(line: str) -> None:
        print(line, file=sys.stderr, flush=True)
        log_handle.write(line + "\n")
        log_handle.flush()

    started = utc_now()
    started_monotonic = time.monotonic()

    import official_p2p3 as official
    import ch3_drift_official_branch_conflict_diagnostic as diag
    import ch3_drift_f_source_eligibility as eligibility
    import ch3_drift_formal_edit_v2 as operator

    operator_path = root / OPERATOR_RELATIVE
    operator_sha = sha256_file(operator_path)
    if operator_sha != EXPECTED_OPERATOR_SHA256:
        raise ValueError(f"v2 算子哈希与已验收版本不符：{operator_sha}")
    if not torch.backends.mps.is_available():
        raise RuntimeError("本诊断固定使用 MPS；当前环境未提供 MPS")
    official.DEVICE = torch.device("mps")
    official.EVAL_BATCH = 128
    candidate_spec = Path(args.candidate_spec)
    if not candidate_spec.is_absolute():
        candidate_spec = root / candidate_spec
    candidate_spec = candidate_spec.resolve()
    candidate_spec_relative = candidate_spec.relative_to(root)
    if not candidate_spec.is_file():
        raise EditContractError(f"候选规格不存在：{candidate_spec}")
    run_map = dict(RUNS)
    if args.run_map:
        for item in args.run_map.split(","):
            if "=" not in item:
                raise EditContractError(f"--run-map 项必须形如 ARM=RUNDIR：{item}")
            arm_key, run_value = item.split("=", 1)
            if arm_key not in RUNS:
                raise EditContractError(f"--run-map 含未知臂：{arm_key}")
            run_map[arm_key] = run_value
    selected_arms = tuple(part for part in args.arms.split(",") if part)
    unknown_arms = sorted(set(selected_arms) - set(RUNS))
    if unknown_arms:
        raise EditContractError(f"未知臂：{unknown_arms}")
    if len(set(selected_arms)) != len(selected_arms) or not selected_arms:
        raise EditContractError("臂子集不得为空或重复")
    is_full_scale = candidate_spec_relative.as_posix() == CANDIDATE_SPEC_RELATIVE
    log(
        f"[P0] 启动 run={args.run_name} 臂={','.join(selected_arms)} 算子={operator_sha[:12]} "
        f"stream_id={args.stream_id}"
    )
    concurrent_tasks = detect_concurrent_tasks()
    if concurrent_tasks:
        log(f"[P0] 检测到并发任务 {len(concurrent_tasks)} 个："
            + "; ".join(task["command"] for task in concurrent_tasks))
    identities, payloads, member_sha, checkpoint_hashes = validate_arms(
        root, candidate_spec, official, diag, eligibility, arms=selected_arms,
        run_map=run_map,
        expected_code_by_arm=EXPECTED_CODE_SHA256 if is_full_scale else None,
    )
    log_stage("冻结身份核验", len(selected_arms), len(selected_arms))

    v3_path = root / "thesis/experiments/llm_probe/runs/diagnostics" / V3_RUN_NAME / "source-low-fpr-probe.json"
    v3 = read_json(v3_path)
    reference_member_sha = v3["members"]["receipt_sha256"]
    member_receipt_matches_v3 = member_sha == reference_member_sha
    if is_full_scale and not member_receipt_matches_v3:
        raise ValueError("本次源成员收据与 v3 已冻结收据不一致")

    status: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_name": args.run_name,
        "arm_set": list(selected_arms),
        "candidate_spec": str(candidate_spec_relative),
        "is_full_scale": is_full_scale,
        "stream_anchor_note": (
            "攻击流身份复用 D-4 锚点，保证追加臂与既有臂使用逐字节相同的攻击串"
            if args.stream_id == f"p0-legal-attack|shared_prefix_edit_v2|{STREAM_ANCHOR}"
            else "攻击流身份与 D-4 锚点不同，既有臂读数不可直接逐位比较"
        ),
        "phase": "running",
        "purpose": "P0 零训练合法共享编辑攻击复评（B/D/F；A 为附加参照臂）",
        "data_role": "仅 T17-T19 源训练与源验证；不访问 T20-T25",
        "training": {"trained": False, "threshold_recalibrated": False},
        "identity": {
            "operator": {"path": OPERATOR_RELATIVE, "sha256": operator_sha},
            "candidate_spec": {"path": str(candidate_spec_relative), "sha256": sha256_file(candidate_spec)},
            "data_revision": official.DATA.name,
            "member_receipt_sha256": member_sha,
            "stream_id": args.stream_id,
            "attack_tiers": list(operator.TIERS),
            "namespace": operator.NAMESPACE,
            "device": "mps",
            "precision": "fp32",
            "eval_batch": 128,
            "resource_contention": {
                "detected_at_start": concurrent_tasks,
                "resource_contention": bool(concurrent_tasks),
                "note": "读数（漏检计数／阈值／语法通过率）与并发无关；并发只影响墙钟。"
                        "若 detected_at_start 非空，本运行墙钟与其他任务墙钟均为并发条件读数。",
            },
            "arms": {
                arm: {
                    "run_name": RUNS[arm],
                    "arm_checkpoint_sha256": checkpoint_hashes[arm],
                    "code_sha256": identities[arm]["code_sha256"],
                    "official_checkpoint_sha256": identities[arm]["checkpoint_sha256"],
                }
                for arm in selected_arms
            },
        },
        "started_at": started,
    }
    atomic_json(status_path, status)
    log(f"[P0] 源成员收据 {member_sha[:12]}（与 v3 一致）；检查点 SHA 已登记")

    tokenizer = official.official.PreTrainedTokenizerFast(
        tokenizer_file=str(official.REF / "artifacts/tokenizer/tokenizer-0-30522-both.json")
    )
    train_domains, train_labels, train_receipts = official.load_fixed_source_members(
        candidate_spec_relative.as_posix(), "source_train"
    )
    validation_domains, labels, validation_receipts = official.load_fixed_source_members(
        candidate_spec_relative.as_posix(), "source_validation"
    )
    if len(train_domains) != len(train_labels) or not len(train_domains):
        raise ValueError("源训练成员与标签数量不符")
    if len(validation_domains) != len(labels) or not len(validation_domains):
        raise ValueError("源验证成员与标签数量不符")
    n_benign = int(np.count_nonzero(labels == 0))
    n_dga = int(np.count_nonzero(labels == 1))
    if n_benign != n_dga or n_benign == 0:
        raise ValueError("源验证良性／DGA 成员数不相等或为空")
    if is_full_scale and n_benign != EXPECTED_CLASS_COUNT:
        raise ValueError("全规模源验证良性成员数不等于冻结的 30,000")
    if sha256_json({"train": train_receipts, "validation": validation_receipts}) != member_sha:
        raise ValueError("重新读取的源成员收据与各臂不一致")
    log_stage("源成员读取", len(validation_domains), len(validation_domains))

    benign_domains = [domain for domain, label in zip(validation_domains, labels) if label == 0]
    dga_domains = [domain for domain, label in zip(validation_domains, labels) if label == 1]
    dga_buckets = np.asarray([length_bucket(len(domain)) for domain in dga_domains])
    bucket_masks = {name: (dga_buckets == name) for name, _, _ in LENGTH_BUCKETS}
    if len(benign_domains) != n_benign or len(dga_domains) != n_dga:
        raise ValueError("源验证良性／DGA 成员拆分数量不符")

    attacks = build_attacks(operator, dga_domains, args.stream_id, log)
    if attacks["summary"]["failure_count"]:
        raise RuntimeError(f"攻击生成失败 {attacks['summary']['failure_count']} 例，评价无效")
    if attacks["summary"]["source_syntax_pass"] != n_dga:
        raise RuntimeError("源 DGA 成员未全部通过基础语法，评价无效")
    log(f"[P0] 攻击生成完成 三档输出 {attacks['summary']['tiers']['random_half']['n_outputs']} 例")

    status["phase"] = "scoring"
    status["attack_summary"] = attacks["summary"]
    atomic_json(status_path, status)

    initial_model = official.load_mps_model()
    tok_mean, char_mean = official.source_feature_means(initial_model, tokenizer, train_domains)
    del initial_model
    gc.collect()
    torch.mps.empty_cache()
    log_stage("初始模型源训练特征均值", len(train_domains), len(train_domains))

    scores_by_arm: dict[str, dict[str, np.ndarray]] = {}
    for index, arm in enumerate(selected_arms, start=1):
        checkpoint = torch.load(
            payloads[arm]["checkpoint_path"], map_location="cpu", weights_only=True
        )
        if checkpoint.get("identity") != identities[arm] or checkpoint.get("arm") != arm:
            raise ValueError(f"{arm} 断点身份或臂键不符")
        if checkpoint.get("completed_epoch") != 3:
            raise ValueError(f"{arm} 断点未完成第三轮")
        model = official.load_mps_model()
        model.load_state_dict(checkpoint["model"], strict=True)
        del checkpoint
        arm_scores = {
            "benign": score_domains(f"{arm} 源良性", benign_domains, model, tokenizer,
                                    tok_mean, char_mean, official, diag),
            "clean_dga": score_domains(f"{arm} 干净DGA", dga_domains, model, tokenizer,
                                       tok_mean, char_mean, official, diag),
        }
        for tier in operator.TIERS:
            arm_scores[tier] = score_domains(
                f"{arm} 攻击{tier}", attacks["attacked"][tier], model, tokenizer,
                tok_mean, char_mean, official, diag,
            )
        for q in LADDER_Q:
            reuse_tier = LADDER_REUSE.get(q)
            if reuse_tier is not None:
                # q=1/2 与 k1/k2 逐位相同（生成阶段已机械核对），直接复用同一预测
                arm_scores[f"q{q}"] = arm_scores[reuse_tier]
            else:
                arm_scores[f"q{q}"] = score_domains(
                    f"{arm} 预算梯度q{q}", attacks["ladder"][q], model, tokenizer,
                    tok_mean, char_mean, official, diag,
                )
        scores_by_arm[arm] = arm_scores
        del model
        gc.collect()
        torch.mps.empty_cache()
        log_stage(f"{arm} 模型完成", index, len(selected_arms))
        # 逐臂增量落盘：长任务中途可核验，且前五臂完成即可核 A/B/D/F/UQ 身份旁证门
        partial_metrics: dict[str, Any] = {}
        for done_arm in scores_by_arm:
            entry: dict[str, Any] = {}
            for key, _ in ALPHAS:
                threshold = freeze_group_threshold(
                    scores_by_arm[done_arm]["benign"], dict(ALPHAS)[key]
                )[0]
                tier_entry: dict[str, Any] = {}
                for tier in operator.TIERS:
                    fn = int(np.count_nonzero(~(scores_by_arm[done_arm][tier] >= threshold)))
                    tier_entry[tier] = {"dga_fn": fn, "dga_fnr": fn / n_dga}
                ladder_entry: dict[str, Any] = {}
                for q in LADDER_Q:
                    fn = int(np.count_nonzero(~(scores_by_arm[done_arm][f"q{q}"] >= threshold)))
                    ladder_entry[str(q)] = {"dga_fn": fn, "dga_fnr": fn / n_dga}
                entry[key] = {"tiers": tier_entry, "ladder": ladder_entry}
            partial_metrics[done_arm] = entry
        atomic_json(run_dir / "p0-legal-attack-partial.json", {
            "schema_version": SCHEMA_VERSION,
            "run_name": args.run_name,
            "status": "scoring_partial",
            "arms_scored": sorted(scores_by_arm),
            "identity": {"operator_sha256": operator_sha, "stream_id": args.stream_id,
                         "member_receipt_sha256": member_sha},
            "partial_metrics": partial_metrics,
            "note": "增量落盘；阈值与最终口径同源（freeze_group_threshold），最终结果以完整收据为准",
        })

    # 阈值重算（应与 v3 已冻结值逐位一致）
    thresholds: dict[str, dict[str, Any]] = {}
    threshold_match: dict[str, Any] = {}
    for arm in selected_arms:
        benign_scores = scores_by_arm[arm]["benign"]
        arm_thresholds: dict[str, Any] = {}
        for key, alpha in ALPHAS:
            threshold, fp, budget = freeze_group_threshold(benign_scores, alpha)
            arm_thresholds[key] = {
                "alpha": alpha, "threshold": threshold, "fp": fp, "fp_budget": budget,
                "fpr": fp / len(benign_scores),
            }
        thresholds[arm] = arm_thresholds
        if is_full_scale and arm in V3_FROZEN:
            threshold_match[arm] = {
                key: {
                    "threshold_equal": arm_thresholds[key]["threshold"] == V3_FROZEN[arm][key]["threshold"],
                    "fp_equal": arm_thresholds[key]["fp"] == V3_FROZEN[arm][key]["fp"],
                }
                for key, _ in ALPHAS
            }

    # 逐臂／逐档漏检与干净侧复核
    metrics: dict[str, Any] = {}
    ladder_metrics: dict[str, Any] = {}
    predictions: dict[str, dict[str, np.ndarray]] = {}
    clean_check: dict[str, Any] = {}
    for arm in selected_arms:
        arm_metrics: dict[str, Any] = {}
        arm_predictions: dict[str, np.ndarray] = {
            THRESHOLD_0_5: scores_by_arm[arm]["clean_dga"] >= 0.5
        }
        clean_entry: dict[str, Any] = {}
        for key, _ in ALPHAS:
            threshold = thresholds[arm][key]["threshold"]
            clean_pred = scores_by_arm[arm]["clean_dga"] >= threshold
            clean_fn = int(np.count_nonzero(~clean_pred))
            clean_entry[key] = {
                "dga_fn": clean_fn,
                "dga_fnr": clean_fn / n_dga,
                "v3_dga_fn": V3_FROZEN[arm][key]["dga_fn"] if (is_full_scale and arm in V3_FROZEN) else None,
                "matches_v3": (clean_fn == V3_FROZEN[arm][key]["dga_fn"]) if (is_full_scale and arm in V3_FROZEN) else None,
            }
            arm_predictions[key] = clean_pred
            tier_metrics: dict[str, Any] = {}
            for tier in operator.TIERS:
                attacked_pred = scores_by_arm[arm][tier] >= threshold
                attacked_fn = int(np.count_nonzero(~attacked_pred))
                tier_metrics[tier] = {
                    "dga_fn": attacked_fn,
                    "dga_fnr": attacked_fn / n_dga,
                    "dga_tp": n_dga - attacked_fn,
                }
                arm_predictions[f"{key}|{tier}"] = attacked_pred
            arm_metrics[key] = tier_metrics
            ladder_entry: dict[str, Any] = {}
            for q in LADDER_Q:
                pred = scores_by_arm[arm][f"q{q}"] >= threshold
                fn = int(np.count_nonzero(~pred))
                ladder_entry[str(q)] = {
                    "nominal_q": q,
                    "dga_fn": fn,
                    "dga_fnr": fn / n_dga,
                    "dga_tp": n_dga - fn,
                    "by_length": {
                        name: {
                            "n": int(mask.sum()),
                            "dga_fn": int(np.count_nonzero(~pred & mask)),
                            "dga_fnr": (
                                float(np.count_nonzero(~pred & mask) / mask.sum())
                                if mask.sum() else None
                            ),
                        }
                        for name, mask in bucket_masks.items()
                    },
                }
                arm_predictions[f"{key}|q{q}"] = pred
            ladder_metrics.setdefault(arm, {})[key] = ladder_entry
        clean_check[arm] = clean_entry
        metrics[arm] = arm_metrics
        predictions[arm] = arm_predictions

    paired: dict[str, Any] = {THRESHOLD_0_5: paired_error_counts(
        {arm: predictions[arm][THRESHOLD_0_5] for arm in selected_arms}, n_dga
    )}
    for key, _ in ALPHAS:
        paired[key] = paired_error_counts(
            {arm: predictions[arm][key] for arm in selected_arms}, n_dga
        )
        for tier in operator.TIERS:
            paired[f"{key}|{tier}"] = paired_error_counts(
                {arm: predictions[arm][f"{key}|{tier}"] for arm in selected_arms}, n_dga
            )
        for q in LADDER_Q:
            paired[f"{key}|q{q}"] = paired_error_counts(
                {arm: predictions[arm][f"{key}|q{q}"] for arm in selected_arms}, n_dga
            )

    # 机械判据对照（只做事实比对，不下结论）；缺少的臂记 None，不越权比较。
    def _fn(arm: str, key: str, tier: str) -> int | None:
        return metrics[arm][key][tier]["dga_fn"] if arm in metrics else None

    gate: dict[str, Any] = {}
    for key, _ in ALPHAS:
        for tier in operator.TIERS:
            baseline_fn = _fn("B", key, tier)
            row: dict[str, Any] = {"baseline_B_dga_fn": baseline_fn}
            for arm in ("D", "F", "A", "UQ", "CAND4", "EDIT4", "CURRICULUM"):
                value = _fn(arm, key, tier)
                row[f"{arm}_dga_fn"] = value
                row[f"{arm}_strictly_lower_misses_than_B"] = (
                    None if value is None else value < baseline_fn
                )
            gate[f"{key}|{tier}"] = row
    primary_key = f"{PRIMARY_ALPHA}|{PRIMARY_TIER}"
    gate["primary_reading"] = {
        "tier": PRIMARY_TIER,
        "alpha_key": PRIMARY_ALPHA,
        "basis": "既有预登记将 maskdga 半替换标为「强攻击，主判据面板」；§八 P0 未点名档位，故同时报告三档",
        "result": gate[primary_key],
        "one_percent_reporting": {
            "tiers": list(operator.TIERS),
            "arms": list(selected_arms),
            "all_readings_present": all(
                "fpr_0_01" in metrics[arm] and set(metrics[arm]["fpr_0_01"]) == set(operator.TIERS)
                for arm in selected_arms
            ),
            "readings": {arm: metrics[arm]["fpr_0_01"] for arm in selected_arms},
        },
    }

    # D-5 归因：UQ（D/F 同候选核 ＋ 均匀同配额选择）相对 B／D／F 的机械对照。
    # 只报方向与量级；「最近簇」按绝对差量判定，属本任务新增的操作化定义，
    # 不是预注册判据，也不构成晋级／淘汰结论。
    attribution_rows: dict[str, Any] = {}
    for key, _ in ALPHAS:
        for tier in operator.TIERS:
            baseline_fn = _fn("B", key, tier)
            d_fn = _fn("D", key, tier)
            f_fn = _fn("F", key, tier)
            uq_fn = _fn("UQ", key, tier)
            have_all = None not in (baseline_fn, d_fn, f_fn, uq_fn)
            attribution_rows[f"{key}|{tier}"] = {
                "UQ_dga_fn": uq_fn,
                "B_dga_fn": baseline_fn,
                "D_dga_fn": d_fn,
                "F_dga_fn": f_fn,
                "delta_UQ_minus_B": (uq_fn - baseline_fn) if have_all else None,
                "delta_UQ_minus_D": (uq_fn - d_fn) if have_all else None,
                "delta_UQ_minus_F": (uq_fn - f_fn) if have_all else None,
                "UQ_strictly_lower_misses_than_B": (
                    uq_fn < baseline_fn if have_all else None
                ),
            }
    primary_row = attribution_rows[primary_key]
    gate["uq_attribution"] = {
        "note": "只报方向与量级；最近簇按绝对差量判定，为 D-5 新增操作化定义，非预注册判据",
        "tier": PRIMARY_TIER,
        "alpha_key": PRIMARY_ALPHA,
        "primary_deltas": {
            key: primary_row[key]
            for key in ("UQ_dga_fn", "B_dga_fn", "D_dga_fn", "F_dga_fn",
                        "delta_UQ_minus_B", "delta_UQ_minus_D", "delta_UQ_minus_F",
                        "UQ_strictly_lower_misses_than_B")
        },
        "nearest_cluster_by_absolute_delta": min(
            (arm for arm in ("B", "D", "F") if primary_row[f"{arm}_dga_fn"] is not None),
            key=lambda arm: abs(primary_row["UQ_dga_fn"] - primary_row[f"{arm}_dga_fn"]),
        ),
        "all_budget_tier_rows": attribution_rows,
    }

    # D-6/D-7 机械对照：新增三臂相对 B／D／F／EDIT4 的漏检差量。
    # 入批预算口径（实测，见报告）：B 与 EDIT4 为 n_mal（min 37/max 82/mean 63.97），
    # D/F/UQ/CAND4 为固定 64，CURRICULUM 第 1 轮随池（mean 61.75）、第 2–3 轮固定 64。
    new_arm_rows: dict[str, Any] = {}
    for key, _ in ALPHAS:
        for tier in operator.TIERS:
            row: dict[str, Any] = {}
            for arm in ("B", "D", "F", "CAND4", "EDIT4", "CURRICULUM",
                        "C1R", "ESAT", "DRICHEL", "CEQ", "CBN"):
                value = _fn(arm, key, tier)
                row[f"{arm}_dga_fn"] = value
                b_fn = _fn("B", key, tier)
                if value is not None and arm != "B" and b_fn is not None:
                    row[f"{arm}_minus_B"] = value - b_fn
            new_arm_rows[f"{key}|{tier}"] = row
    for key, _ in ALPHAS:
        for q in LADDER_Q:
            row = {}
            for arm in ("B", "D", "F", "CAND4", "EDIT4", "CURRICULUM",
                        "C1R", "ESAT", "DRICHEL", "CEQ", "CBN"):
                if arm not in ladder_metrics:
                    row[f"{arm}_dga_fn"] = None
                    continue
                value = ladder_metrics[arm][key][str(q)]["dga_fn"]
                row[f"{arm}_dga_fn"] = value
                b_ladder = ladder_metrics.get("B", {}).get(key, {}).get(str(q), {}).get("dga_fn")
                if arm != "B" and b_ladder is not None:
                    row[f"{arm}_minus_B"] = value - b_ladder
            new_arm_rows[f"{key}|q{q}"] = row
    gate["new_arm_mechanical_comparison"] = {
        "note": "只报差量，不下结论；训练层 vs 评价层的比较须按【实际 Hamming】口径"
                "（评价算子 Hamming==min(q,|E|) 精确，训练核名义位数会因位置碰撞饱和）",
        "probation_caliber": {
            "B": "入批变体 = n_mal（mean 63.97，min 37，max 82）",
            "EDIT4": "入批变体 = min(64, n_mal)（mean 61.72）",
            "D/F/UQ/CAND4": "入批变体 = 固定 64",
            "CURRICULUM": "第 1 轮随池（mean 61.75），第 2–3 轮固定 64",
        },
        "rows": new_arm_rows,
    }

    result = {
        "schema_version": SCHEMA_VERSION,
        "run_name": args.run_name,
        "arm_set": list(selected_arms),
        "stream_anchor": STREAM_ANCHOR,
        "candidate_spec": str(candidate_spec_relative),
        "is_full_scale": is_full_scale,
        "status": "completed",
        "screening_only": True,
        "zero_training": True,
        "source_overlap_unresolved": True,
        "data_role": "仅 T17-T19 源训练与源验证；不访问 T20-T25",
        "operator": {"path": OPERATOR_RELATIVE, "sha256": operator_sha,
                     "namespace": operator.NAMESPACE, "schema_version": operator.SCHEMA_VERSION},
        "stream_id": args.stream_id,
        "members": {
            "source_train": len(train_domains),
            "source_validation": len(validation_domains),
            "source_benign": len(benign_domains),
            "source_dga": len(dga_domains),
            "receipt_sha256": member_sha,
            "matches_v3_receipt": member_receipt_matches_v3,
            "benign_sha256": sha256_sequence(benign_domains),
            "dga_sha256": sha256_sequence(dga_domains),
        },
        "identities": {
            arm: {
                "run_name": run_map[arm],
                "arm_checkpoint_sha256": checkpoint_hashes[arm],
                "code_sha256": identities[arm]["code_sha256"],
                "official_checkpoint_sha256": identities[arm]["checkpoint_sha256"],
            }
            for arm in selected_arms
        },
        "attacks": attacks["summary"],
        "ladder_attacks": attacks["ladder_summary"],
        "ladder_buckets": {
            "definition": {name: [low, high if high < 10 ** 9 else None]
                           for name, low, high in LENGTH_BUCKETS},
            "counts": attacks["ladder_bucket_counts"],
            "exact_budget_share": attacks["ladder_bucket_saturated"],
        },
        "thresholds": thresholds,
        "threshold_match_v3": threshold_match,
        "clean_side_recheck": clean_check,
        "attack_metrics": metrics,
        "ladder_budget_metrics": ladder_metrics,
        "paired_dga_error_cross_counts": paired,
        "gate_mechanical": gate,
        "runtime": {
            "started_at": started,
            "finished_at": utc_now(),
            "elapsed_seconds": time.monotonic() - started_monotonic,
            "python_executable": sys.executable,
            "python_version": sys.version,
        },
    }
    atomic_json(result_path, result)

    status["phase"] = "completed"
    status["finished_at"] = utc_now()
    status["elapsed_seconds"] = time.monotonic() - started_monotonic
    status["outputs"] = {"result": result_path.name, "console": log_path.name}
    status["readings_digest"] = sha256_json({
        "thresholds": thresholds,
        "attack_metrics": metrics,
        "paired": paired,
        "gate": gate,
    })
    atomic_json(status_path, status)
    log(f"[P0] 完成 status=completed 用时 {time.monotonic() - started_monotonic:.1f}s")
    log_handle.close()
    print(json.dumps({
        "status": "completed",
        "run_dir": str(run_dir.relative_to(root)),
        "gate_primary": gate["primary_reading"]["result"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
