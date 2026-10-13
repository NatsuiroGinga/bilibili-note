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
}
# 既有语义保持不变：主判据臂仍是 B/D/F。
PRIMARY_ARMS = ("B", "D", "F")
# 追加臂：仅作归因参照，不进 P0 支持门。
ATTRIBUTION_ARMS = ("UQ",)
PAIRED_ARMS = (("B", "D"), ("B", "F"), ("B", "A"), ("B", "UQ"), ("D", "UQ"), ("F", "UQ"))
EXPECTED_CODE_SHA256 = {
    "A": "8ab6307f18142aae829a96565c46206f6ca8a70cfef09804b1e9e21411c5b44b",
    "B": "8ab6307f18142aae829a96565c46206f6ca8a70cfef09804b1e9e21411c5b44b",
    "D": "0705c24be7e5cbc0716a99f360781bb9394378d34e2ed96103077961d4bbacef",
    "F": "0705c24be7e5cbc0716a99f360781bb9394378d34e2ed96103077961d4bbacef",
    # UQ 只改选择规则，代码哈希与 D/F 必然不同（已知项，不视为阻塞）。
    "UQ": "59d50aaf71d19b9ff796b1785b5f053d0b1bf68da49e6f226201d0666903155b",
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

    for arm, run_name in RUNS.items():
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
        if identity.get("code_sha256") != EXPECTED_CODE_SHA256[arm]:
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

    return identities, payloads, sha256_json(expected_members), checkpoint_hashes


# ------------------------------------------------------------------ 攻击生成


def build_attacks(
    operator: Any, dga_domains: list[str], stream_id: str, log
) -> dict[str, Any]:
    """用 v2 算子在源 DGA 成员上生成三档攻击，并机械核验合法性。"""
    syntax_pass = 0
    per_tier: dict[str, list[str]] = {tier: [] for tier in operator.TIERS}
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
    n_e_array = np.asarray(n_e_values, dtype=np.int64)
    length_array = np.asarray(lengths, dtype=np.int64)
    return {
        "attacked": per_tier,
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
    predictions: dict[str, np.ndarray]
) -> dict[str, dict[str, int]]:
    lengths = {len(values) for values in predictions.values()}
    if lengths != {EXPECTED_CLASS_COUNT}:
        raise ValueError("配对计数输入长度必须同为 30,000")
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
    log(
        f"[P0] 启动 run={args.run_name} 臂={','.join(RUNS)} 算子={operator_sha[:12]} "
        f"stream_id={args.stream_id}"
    )

    candidate_spec = root / CANDIDATE_SPEC_RELATIVE
    candidate_spec_relative = candidate_spec.relative_to(root)
    concurrent_tasks = detect_concurrent_tasks()
    if concurrent_tasks:
        log(f"[P0] 检测到并发任务 {len(concurrent_tasks)} 个："
            + "; ".join(task["command"] for task in concurrent_tasks))
    identities, payloads, member_sha, checkpoint_hashes = validate_arms(
        root, candidate_spec, official, diag, eligibility
    )
    log_stage("冻结身份核验", len(RUNS), len(RUNS))

    v3_path = root / "thesis/experiments/llm_probe/runs/diagnostics" / V3_RUN_NAME / "source-low-fpr-probe.json"
    v3 = read_json(v3_path)
    reference_member_sha = v3["members"]["receipt_sha256"]
    if member_sha != reference_member_sha:
        raise ValueError("本次源成员收据与 v3 已冻结收据不一致")

    status: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_name": args.run_name,
        "arm_set": list(RUNS),
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
                for arm in RUNS
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
    if int(np.count_nonzero(labels == 0)) != EXPECTED_CLASS_COUNT:
        raise ValueError("源验证良性成员数不等于冻结的 30,000")
    if int(np.count_nonzero(labels == 1)) != EXPECTED_CLASS_COUNT:
        raise ValueError("源验证 DGA 成员数不等于冻结的 30,000")
    if sha256_json({"train": train_receipts, "validation": validation_receipts}) != member_sha:
        raise ValueError("重新读取的源成员收据与各臂不一致")
    log_stage("源成员读取", len(validation_domains), len(validation_domains))

    benign_domains = [domain for domain, label in zip(validation_domains, labels) if label == 0]
    dga_domains = [domain for domain, label in zip(validation_domains, labels) if label == 1]
    if len(benign_domains) != EXPECTED_CLASS_COUNT or len(dga_domains) != EXPECTED_CLASS_COUNT:
        raise ValueError("源验证良性／DGA 成员拆分数量不符")

    attacks = build_attacks(operator, dga_domains, args.stream_id, log)
    if attacks["summary"]["failure_count"]:
        raise RuntimeError(f"攻击生成失败 {attacks['summary']['failure_count']} 例，评价无效")
    if attacks["summary"]["source_syntax_pass"] != EXPECTED_CLASS_COUNT:
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
    for index, arm in enumerate(RUNS, start=1):
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
        scores_by_arm[arm] = arm_scores
        del model
        gc.collect()
        torch.mps.empty_cache()
        log_stage(f"{arm} 模型完成", index, len(RUNS))

    # 阈值重算（应与 v3 已冻结值逐位一致）
    thresholds: dict[str, dict[str, Any]] = {}
    threshold_match: dict[str, Any] = {}
    for arm in RUNS:
        benign_scores = scores_by_arm[arm]["benign"]
        arm_thresholds: dict[str, Any] = {}
        for key, alpha in ALPHAS:
            threshold, fp, budget = freeze_group_threshold(benign_scores, alpha)
            arm_thresholds[key] = {
                "alpha": alpha, "threshold": threshold, "fp": fp, "fp_budget": budget,
                "fpr": fp / len(benign_scores),
            }
        thresholds[arm] = arm_thresholds
        if arm in V3_FROZEN:
            threshold_match[arm] = {
                key: {
                    "threshold_equal": arm_thresholds[key]["threshold"] == V3_FROZEN[arm][key]["threshold"],
                    "fp_equal": arm_thresholds[key]["fp"] == V3_FROZEN[arm][key]["fp"],
                }
                for key, _ in ALPHAS
            }

    # 逐臂／逐档漏检与干净侧复核
    metrics: dict[str, Any] = {}
    predictions: dict[str, dict[str, np.ndarray]] = {}
    clean_check: dict[str, Any] = {}
    for arm in RUNS:
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
                "dga_fnr": clean_fn / EXPECTED_CLASS_COUNT,
                "v3_dga_fn": V3_FROZEN[arm][key]["dga_fn"] if arm in V3_FROZEN else None,
                "matches_v3": (clean_fn == V3_FROZEN[arm][key]["dga_fn"]) if arm in V3_FROZEN else None,
            }
            arm_predictions[key] = clean_pred
            tier_metrics: dict[str, Any] = {}
            for tier in operator.TIERS:
                attacked_pred = scores_by_arm[arm][tier] >= threshold
                attacked_fn = int(np.count_nonzero(~attacked_pred))
                tier_metrics[tier] = {
                    "dga_fn": attacked_fn,
                    "dga_fnr": attacked_fn / EXPECTED_CLASS_COUNT,
                    "dga_tp": EXPECTED_CLASS_COUNT - attacked_fn,
                }
                arm_predictions[f"{key}|{tier}"] = attacked_pred
            arm_metrics[key] = tier_metrics
        clean_check[arm] = clean_entry
        metrics[arm] = arm_metrics
        predictions[arm] = arm_predictions

    paired: dict[str, Any] = {THRESHOLD_0_5: paired_error_counts(
        {arm: predictions[arm][THRESHOLD_0_5] for arm in RUNS}
    )}
    for key, _ in ALPHAS:
        paired[key] = paired_error_counts(
            {arm: predictions[arm][key] for arm in RUNS}
        )
        for tier in operator.TIERS:
            paired[f"{key}|{tier}"] = paired_error_counts(
                {arm: predictions[arm][f"{key}|{tier}"] for arm in RUNS}
            )

    # 机械判据对照（只做事实比对，不下结论）
    gate: dict[str, Any] = {}
    for key, _ in ALPHAS:
        for tier in operator.TIERS:
            baseline_fn = metrics["B"][key][tier]["dga_fn"]
            gate[f"{key}|{tier}"] = {
                "baseline_B_dga_fn": baseline_fn,
                "D_dga_fn": metrics["D"][key][tier]["dga_fn"],
                "F_dga_fn": metrics["F"][key][tier]["dga_fn"],
                "A_dga_fn": metrics["A"][key][tier]["dga_fn"],
                "D_strictly_lower_misses_than_B": metrics["D"][key][tier]["dga_fn"] < baseline_fn,
                "F_strictly_lower_misses_than_B": metrics["F"][key][tier]["dga_fn"] < baseline_fn,
                "A_strictly_lower_misses_than_B": metrics["A"][key][tier]["dga_fn"] < baseline_fn,
                "UQ_dga_fn": metrics["UQ"][key][tier]["dga_fn"],
                "UQ_strictly_lower_misses_than_B": metrics["UQ"][key][tier]["dga_fn"] < baseline_fn,
            }
    primary_key = f"{PRIMARY_ALPHA}|{PRIMARY_TIER}"
    gate["primary_reading"] = {
        "tier": PRIMARY_TIER,
        "alpha_key": PRIMARY_ALPHA,
        "basis": "既有预登记将 maskdga 半替换标为「强攻击，主判据面板」；§八 P0 未点名档位，故同时报告三档",
        "result": gate[primary_key],
        "one_percent_reporting": {
            "tiers": list(operator.TIERS),
            "arms": list(RUNS),
            "all_readings_present": all(
                "fpr_0_01" in metrics[arm] and set(metrics[arm]["fpr_0_01"]) == set(operator.TIERS)
                for arm in RUNS
            ),
            "readings": {arm: metrics[arm]["fpr_0_01"] for arm in RUNS},
        },
    }

    # D-5 归因：UQ（D/F 同候选核 ＋ 均匀同配额选择）相对 B／D／F 的机械对照。
    # 只报方向与量级；「最近簇」按绝对差量判定，属本任务新增的操作化定义，
    # 不是预注册判据，也不构成晋级／淘汰结论。
    attribution_rows: dict[str, Any] = {}
    for key, _ in ALPHAS:
        for tier in operator.TIERS:
            baseline_fn = metrics["B"][key][tier]["dga_fn"]
            d_fn = metrics["D"][key][tier]["dga_fn"]
            f_fn = metrics["F"][key][tier]["dga_fn"]
            uq_fn = metrics["UQ"][key][tier]["dga_fn"]
            attribution_rows[f"{key}|{tier}"] = {
                "UQ_dga_fn": uq_fn,
                "B_dga_fn": baseline_fn,
                "D_dga_fn": d_fn,
                "F_dga_fn": f_fn,
                "delta_UQ_minus_B": uq_fn - baseline_fn,
                "delta_UQ_minus_D": uq_fn - d_fn,
                "delta_UQ_minus_F": uq_fn - f_fn,
                "UQ_strictly_lower_misses_than_B": uq_fn < baseline_fn,
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
            ("B", "D", "F"),
            key=lambda arm: abs(primary_row["UQ_dga_fn"] - primary_row[f"{arm}_dga_fn"]),
        ),
        "all_budget_tier_rows": attribution_rows,
    }

    result = {
        "schema_version": SCHEMA_VERSION,
        "run_name": args.run_name,
        "arm_set": list(RUNS),
        "stream_anchor": STREAM_ANCHOR,
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
            "matches_v3_receipt": member_sha == reference_member_sha,
            "benign_sha256": sha256_sequence(benign_domains),
            "dga_sha256": sha256_sequence(dga_domains),
        },
        "identities": {
            arm: {
                "run_name": RUNS[arm],
                "arm_checkpoint_sha256": checkpoint_hashes[arm],
                "code_sha256": identities[arm]["code_sha256"],
                "official_checkpoint_sha256": identities[arm]["checkpoint_sha256"],
            }
            for arm in RUNS
        },
        "attacks": attacks["summary"],
        "thresholds": thresholds,
        "threshold_match_v3": threshold_match,
        "clean_side_recheck": clean_check,
        "attack_metrics": metrics,
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
