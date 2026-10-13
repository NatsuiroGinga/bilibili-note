#!/usr/bin/env python3
"""在既有 B/D/F 源冻结低误报复评口径上，加入 UQ（Uniform-q）对照臂的干净源验证复评。

口径与 `source_low_fpr_probe.py`（v3，SHA-256
`a11622bf99addfea0131520be2566620654cd6be35ad1ee0ef2a1ef15e7f324e`）逐项相同：
同一源训练／源验证成员、同一初始模型源特征均值、同一 0.5 基线复算门、
同一整同分组阈值冻结规则（FP ≤ floor(alpha × 30,000)）、同两档预算 0.001／0.01。

为避免口径分歧，本脚本直接 `import source_low_fpr_probe` 复用其
`score_domains`／`freeze_group_threshold`／`baseline_counts`／`sha256_json`／
`atomic_json`／`ALPHAS`／`EXPECTED_CLASS_COUNT`，不复制评分与阈值数学。
仅新增：四臂（B/D/F/UQ）身份校验、UQ 候选池与 D 的逐位同一性核验、四臂配对计数。

本诊断只评分干净成员，不生成攻击、不读取 T20–T25、不重训。
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

SCHEMA_VERSION = "ch3-drift-source-low-fpr-probe-uniformq-v1"

RUNS = {
    "B": "ch3-drift-source-common-b-mps-20260923-v1",
    "D": "ch3-drift-source-common-d-cacheless-mps-20260924-v1",
    "F": "ch3-drift-source-common-f-cacheless-mps-20260924-v1",
    "UQ": "ch3-drift-source-common-uniformq-mps-20261013-v1",
}
# B 与 D/F 为已登记的历史源期筛选代码版本；UQ 为本对照臂新增选择分支后的版本。
EXPECTED_CODE_SHA256 = {
    "B": "8ab6307f18142aae829a96565c46206f6ca8a70cfef09804b1e9e21411c5b44b",
    "D": "0705c24be7e5cbc0716a99f360781bb9394378d34e2ed96103077961d4bbacef",
    "F": "0705c24be7e5cbc0716a99f360781bb9394378d34e2ed96103077961d4bbacef",
    "UQ": "59d50aaf71d19b9ff796b1785b5f053d0b1bf68da49e6f226201d0666903155b",
}
# UQ 相对 D/F 的唯一差量声明（写入结果，供主代理核对）
ARM_DIFFERENCE = {
    "reference_arms": ["D", "F"],
    "same_as_D": [
        "候选核：共享 base 上的两阶段复合四候选（每组 K=4，累积 4 位编辑）",
        "每批入损失的变体配额：min(64, |候选池|)",
        "源训练／源验证成员、初始 checkpoint、分层 lr、优化器、3 轮、batch 128、seed 42",
        "损失：恶意变体与干净主样本同权 plain CE（无良性误报加权）",
        "候选评分前向保留（不参与 UQ 选择），使候选生成与候选评分路径与 D 逐行相同",
    ],
    "only_difference_vs_D": (
        "选择规则：D 用组内中心化优势（fooled − 组均值）跨组 top-64 竞争；"
        "UQ 在同一候选池上均匀随机取同配额 64（无组内中心化、无跨组配额竞争）"
    ),
    "only_difference_vs_F": (
        "F 相对 D 另含「良性误报加权 ×3.0」，UQ 不含该分量 ⇒ UQ vs F 同时差"
        "「选择规则」与「良性补偿」两项，不是纯选择规则对照；纯选择规则对照为 UQ vs D"
    ),
    "uniform_rng_stream": "UQ 选择使用独立 random.Random(SEED+13)，不扰动攻击 RNG，候选池与 D 逐条相同",
}
# v3 已发布读数，用于复算一致性对照（不作为硬门）
V3_RESULT = (
    "thesis/experiments/llm_probe/runs/diagnostics/"
    "ch3-drift-source-low-fpr-bdf-mps-20260924-v3/source-low-fpr-probe.json"
)


def paired_error_counts(
    left: str, right: str, dga_predictions: dict[str, np.ndarray]
) -> dict[str, int]:
    """同一 DGA 成员顺序下的两臂错误交叉计数（与 v3 同字段名）。"""
    left_pred = dga_predictions[left]
    right_pred = dga_predictions[right]
    if left_pred.ndim != 1 or right_pred.ndim != 1 or len(left_pred) != len(right_pred):
        raise ValueError(f"{left}-{right} 配对输入必须等长一维 DGA 预测")
    left_wrong = ~left_pred
    right_wrong = ~right_pred
    return {
        f"{left}_only_wrong": int(np.count_nonzero(left_wrong & ~right_wrong)),
        f"{right}_only_wrong": int(np.count_nonzero(~left_wrong & right_wrong)),
        "both_wrong": int(np.count_nonzero(left_wrong & right_wrong)),
        "both_correct": int(np.count_nonzero(~left_wrong & ~right_wrong)),
        "n_dga": len(left_wrong),
    }


def parse_args() -> argparse.Namespace:
    default_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=default_root)
    parser.add_argument(
        "--candidate-spec",
        type=Path,
        default=Path(".Codex/docs/2026-09-23-DRIFT源期训练抽样合同/candidate-spec-diagnostic-v1.json"),
    )
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:  # noqa: C901 - 线性诊断流程，与 v3 入口同构
    args = parse_args()
    root = args.project_root.resolve()
    candidate_spec = args.candidate_spec
    if not candidate_spec.is_absolute():
        candidate_spec = root / candidate_spec
    candidate_spec = candidate_spec.resolve()
    if not candidate_spec.is_file():
        raise FileNotFoundError(f"候选规格不存在：{candidate_spec}")
    candidate_spec_relative = candidate_spec.relative_to(root)

    output = args.output if args.output.is_absolute() else root / args.output
    output = output.resolve()
    if output.exists() or output.with_name(output.name + ".partial").exists():
        raise FileExistsError(f"输出或原子临时文件已存在：{output}")

    tool_root = root / "thesis/experiments/llm_probe/tools"
    official_root = root / ".Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案"
    probe_root = root / ".Codex/docs/2026-09-23-DRIFT源期训练抽样合同"
    for path in (tool_root, official_root, probe_root):
        if not path.is_dir():
            raise FileNotFoundError(f"DRIFT 工具目录不存在：{path}")
    os.environ["LLM_PROBE_ROOT"] = str(root / "thesis/experiments/llm_probe")
    sys.path.insert(0, str(tool_root))
    sys.path.insert(0, str(official_root))
    sys.path.insert(0, str(probe_root))

    import source_low_fpr_probe as probe
    import official_p2p3 as official
    import ch3_drift_official_branch_conflict_diagnostic as diag
    import ch3_drift_f_source_eligibility as eligibility

    if not torch.backends.mps.is_available():
        raise RuntimeError("本诊断固定使用 MPS；当前环境未提供 MPS")
    official.DEVICE = torch.device("mps")
    official.EVAL_BATCH = 128

    candidate_sha = probe.sha256_file(candidate_spec)
    expected_artifact_hashes = {
        "checkpoint_sha256": probe.sha256_file(official.CKPT),
        "model_loader_sha256": probe.sha256_file(Path(official.official.__file__)),
        "feature_adapter_sha256": probe.sha256_file(Path(diag.__file__)),
        "member_selector_sha256": probe.sha256_file(Path(eligibility.__file__)),
    }

    identities: dict[str, dict[str, Any]] = {}
    payloads: dict[str, dict[str, Any]] = {}
    common_fields = (
        "batch", "candidate_spec_sha256", "checkpoint_sha256", "device", "dry_run",
        "epochs", "feature_adapter_sha256", "member_selector_sha256",
        "model_loader_sha256", "precision", "seed", "source_revision",
    )
    expected_common: dict[str, Any] | None = None
    expected_members: dict[str, Any] | None = None
    for arm, run_name in RUNS.items():
        run_dir = root / "thesis/experiments/llm_probe/runs/diagnostics" / run_name
        status_path = run_dir / "run-status.json"
        checkpoint_path = run_dir / f"arm-{arm}-checkpoint.pt"
        arm_result_path = run_dir / f"arm-{arm}-result.json"
        total_result_path = run_dir / f"source-common-{arm.lower()}-result.json"
        for path in (status_path, checkpoint_path, arm_result_path, total_result_path):
            if not path.is_file():
                raise FileNotFoundError(f"缺少已完成运行制品：{path.relative_to(root)}")

        status = probe.read_json(status_path)
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

        common = {key: identity.get(key) for key in common_fields}
        if expected_common is None:
            expected_common = common
        elif common != expected_common:
            raise ValueError(f"{arm} 与其他臂的冻结运行身份不一致")

        arm_result = probe.read_json(arm_result_path)
        if arm_result.get("arm") != arm or arm_result.get("identity") != identity:
            raise ValueError(f"{arm} 单臂结果与运行身份不一致")
        total_result = probe.read_json(total_result_path)
        source_members = total_result.get("source_members")
        if not isinstance(source_members, dict):
            raise ValueError(f"{arm} 总结果缺源成员收据")
        if expected_members is None:
            expected_members = source_members
        elif source_members != expected_members:
            raise ValueError("四臂源成员收据不一致")
        if total_result.get("results", {}).get(arm) != arm_result.get("result"):
            raise ValueError(f"{arm} 总结果与单臂结果不一致")

        identities[arm] = identity
        payloads[arm] = {
            "run_dir": run_dir,
            "checkpoint_path": checkpoint_path,
            "arm_result": arm_result,
        }
    probe.log_stage("冻结身份核验", len(RUNS), len(RUNS))
    member_sha = probe.sha256_json(expected_members)

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
    if int(np.count_nonzero(labels == 0)) != probe.EXPECTED_CLASS_COUNT:
        raise ValueError("源验证良性成员数不等于冻结的 30,000")
    if int(np.count_nonzero(labels == 1)) != probe.EXPECTED_CLASS_COUNT:
        raise ValueError("源验证 DGA 成员数不等于冻结的 30,000")
    if probe.sha256_json({"train": train_receipts, "validation": validation_receipts}) != member_sha:
        raise ValueError("重新读取的源成员收据与四臂不一致")
    probe.log_stage("源成员读取", len(validation_domains), len(validation_domains))

    initial_model = official.load_mps_model()
    tok_mean, char_mean = official.source_feature_means(initial_model, tokenizer, train_domains)
    del initial_model
    gc.collect()
    torch.mps.empty_cache()
    probe.log_stage("初始模型源训练特征均值", len(train_domains), len(train_domains))

    # ---- UQ 候选池与 D 的逐位同一性核验（同核硬门）----
    d_checkpoint = torch.load(
        payloads["D"]["checkpoint_path"], map_location="cpu", weights_only=True
    )
    if d_checkpoint.get("cache_policy_id") != "source_screen_d_base4_if_missing_v1":
        raise ValueError("D 断点缓存策略不是已登记的 D 策略")
    d_order_sha = d_checkpoint.get("source_order_sha256")
    d_cache_root = d_checkpoint.get("cache_root_sha256")
    d_entry_count = int(d_checkpoint.get("cache_entry_count", -1))
    d_value_count = int(d_checkpoint.get("cache_value_count", -1))
    del d_checkpoint

    uq_checkpoint = torch.load(
        payloads["UQ"]["checkpoint_path"], map_location="cpu", weights_only=True
    )
    if uq_checkpoint.get("cache_policy_id") != official.CACHE_POLICY_BY_ARM["UQ"]:
        raise ValueError("UQ 断点缓存策略不是已登记的 UQ 策略")
    if int(uq_checkpoint.get("cache_entry_count", -1)) != d_entry_count:
        raise ValueError("UQ 候选池组数与 D 不一致，同核前提不成立")
    if int(uq_checkpoint.get("cache_value_count", -1)) != d_value_count:
        raise ValueError("UQ 候选池候选数与 D 不一致，同核前提不成立")
    if uq_checkpoint.get("source_order_sha256") != d_order_sha:
        raise ValueError("UQ 源顺序根与 D 不一致，同核前提不成立")
    if "uniform_rng" not in uq_checkpoint:
        raise ValueError("UQ 断点缺均匀选择 RNG 状态，选择规则无法复现")
    uq_rebuilt = official.rebuild_first_epoch_cache("UQ", train_domains, train_labels, 3)
    # 以 D 的策略标识重算 UQ 重放池摘要：若与 D 记录的缓存根相同，则两臂候选池逐条相同。
    uq_pool_as_d = official.cache_summary(
        uq_rebuilt, "source_screen_d_base4_if_missing_v1", d_order_sha
    )
    pool_identity = {
        "uq_entry_count": int(uq_checkpoint.get("cache_entry_count", -1)),
        "uq_value_count": int(uq_checkpoint.get("cache_value_count", -1)),
        "d_entry_count": d_entry_count,
        "d_value_count": d_value_count,
        "source_order_sha256": d_order_sha,
        "uq_pool_under_d_policy_root_sha256": uq_pool_as_d["cache_root_sha256"],
        "d_recorded_cache_root_sha256": d_cache_root,
        "identical": uq_pool_as_d["cache_root_sha256"] == d_cache_root,
    }
    del uq_rebuilt, uq_checkpoint
    gc.collect()
    if not pool_identity["identical"]:
        raise ValueError(
            "UQ 候选池与 D 的重放根不一致，无法复现 D/F 候选核，按阻塞条件停止"
        )
    probe.log_stage("UQ 候选池同核核验", 1, 1)

    scores_by_arm: dict[str, np.ndarray] = {}
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "scoring",
        "screening_only": True,
        "source_overlap_unresolved": True,
        "data_role": "仅 T17-T19 源训练和源验证；不访问 T20-T25，不生成攻击",
        "arm_difference_uq_vs_df": ARM_DIFFERENCE,
        "isolation_map": {
            "UQ_vs_D": "纯选择规则（同候选核、同配额、同 plain CE 损失）",
            "UQ_vs_F": "选择规则 + 良性误报加权（F 另含 ×3.0），非纯选择规则对照",
            "UQ_vs_B": "候选核 + 装配规则（B 为原串一次二位编辑且全量入批），非纯候选核对照",
        },
        "members": {
            "source_train": len(train_domains),
            "source_validation": len(validation_domains),
            "source_benign": int(np.count_nonzero(labels == 0)),
            "source_dga": int(np.count_nonzero(labels == 1)),
            "receipt_sha256": member_sha,
        },
        "identities": {
            arm: {
                "code_sha256": identity["code_sha256"],
                "candidate_spec_sha256": identity["candidate_spec_sha256"],
                "checkpoint_sha256": identity["checkpoint_sha256"],
                "arms": identity["arms"],
                "run_name": RUNS[arm],
            }
            for arm, identity in identities.items()
        },
        "uq_candidate_pool_identity_vs_D": pool_identity,
    }

    baseline_check: dict[str, Any] = {}
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
        scores = probe.score_domains(
            arm, validation_domains, model, tokenizer, tok_mean, char_mean, official, diag
        )
        counts = probe.baseline_counts(scores, labels)
        original_clean = payloads[arm]["arm_result"].get("result", {}).get("clean", {})
        expected = {
            "FP": int(original_clean.get("FP", -1)),
            "FN": int(original_clean.get("FN", -1)),
            "n_benign": int(np.count_nonzero(labels == 0)),
            "n_dga": int(np.count_nonzero(labels == 1)),
        }
        baseline_check[arm] = {
            "recomputed_0_5": counts,
            "original_0_5": expected,
            "match": counts == expected,
        }
        if counts["n_benign"] != probe.EXPECTED_CLASS_COUNT or counts["n_dga"] != probe.EXPECTED_CLASS_COUNT:
            raise ValueError("0.5 基线覆盖样本量与冻结源成员数不符")
        scores_by_arm[arm] = scores
        del model
        gc.collect()
        torch.mps.empty_cache()
        probe.log_stage(f"{arm} 模型完成", index, len(RUNS))

    result["baseline_0_5"] = baseline_check
    mismatches = [arm for arm, value in baseline_check.items() if not value["match"]]
    if mismatches:
        result["status"] = "baseline_mismatch_low_fpr_skipped"
        result["baseline_mismatch_arms"] = mismatches
        probe.atomic_json(output, result)
        print(f"已保存 0.5 对照差异；低误报比较停止：{','.join(mismatches)}", file=sys.stderr)
        return 2

    low_fpr: dict[str, Any] = {}
    predictions: dict[str, dict[str, np.ndarray]] = {}
    for arm, scores in scores_by_arm.items():
        benign_scores = scores[labels == 0]
        dga_scores = scores[labels == 1]
        arm_metrics: dict[str, Any] = {}
        arm_predictions = {"threshold_0_5": dga_scores >= 0.5}
        for key, alpha in probe.ALPHAS:
            threshold, fp, budget = probe.freeze_group_threshold(benign_scores, alpha)
            dga_pred = dga_scores >= threshold
            fn = int(np.count_nonzero(~dga_pred))
            arm_metrics[key] = {
                "alpha": alpha,
                "threshold": threshold,
                "fp": fp,
                "fp_budget": budget,
                "fpr": fp / len(benign_scores),
                "dga_fn": fn,
                "dga_fnr": fn / len(dga_scores),
            }
            arm_predictions[key] = dga_pred
        low_fpr[arm] = arm_metrics
        predictions[arm] = arm_predictions
    result["status"] = "scored_pending_pairing"
    result["low_fpr_source_validation"] = low_fpr
    probe.atomic_json(output, result)

    threshold_keys = ("threshold_0_5", *(name for name, _ in probe.ALPHAS))
    pairs = (("UQ", "D"), ("UQ", "F"), ("UQ", "B"), ("B", "D"), ("B", "F"))
    paired = {
        key: {
            f"{left}-{right}": paired_error_counts(
                left, right, {arm: predictions[arm][key] for arm in RUNS}
            )
            for left, right in pairs
        }
        for key in threshold_keys
    }
    result["paired_dga_error_cross_counts"] = paired
    result["paired_pairs"] = [f"{l}-{r}" for l, r in pairs]

    # 与 v3 已发布读数的复算一致性对照（诊断项，不作硬门）
    v3_path = root / V3_RESULT
    if v3_path.is_file():
        v3 = probe.read_json(v3_path)
        v3_check: dict[str, Any] = {}
        for arm in ("B", "D", "F"):
            published = v3.get("low_fpr_source_validation", {}).get(arm, {})
            recomputed = low_fpr.get(arm, {})
            v3_check[arm] = {
                key: {
                    "published_dga_fn": published.get(key, {}).get("dga_fn"),
                    "recomputed_dga_fn": recomputed.get(key, {}).get("dga_fn"),
                    "dga_fn_equal": published.get(key, {}).get("dga_fn")
                    == recomputed.get(key, {}).get("dga_fn"),
                    "published_threshold": published.get(key, {}).get("threshold"),
                    "recomputed_threshold": recomputed.get(key, {}).get("threshold"),
                }
                for key, _ in probe.ALPHAS
            }
        result["v3_reproduction_diagnostic"] = v3_check
        result["v3_reproduction_all_dga_fn_equal"] = all(
            cell["dga_fn_equal"]
            for arm_cell in v3_check.values()
            for cell in arm_cell.values()
        )
        published_members = v3.get("members", {}).get("receipt_sha256")
        result["v3_member_receipt_match"] = published_members == member_sha

    result["status"] = "completed"
    probe.atomic_json(output, result)
    probe.log_stage("聚合 JSON 写入", 1, 1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
