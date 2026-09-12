#!/usr/bin/env python3
"""只读核查 V4 的 T17 嵌套编辑耦合前提，不训练且不触发 MPS。"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import logging
import random
import sys
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VerificationConfig:
    seed: int
    member_limit: int
    alphabet: str
    data_revision: str
    package_relative: Path
    production_relative: Path
    data_relative: Path


def build_config() -> VerificationConfig:
    package_relative = Path(".Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案")
    revision = "3b31077020cd1c013d0a75cad51042a2327c4521"
    return VerificationConfig(
        seed=42,
        member_limit=30_000,
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
        data_revision=revision,
        package_relative=package_relative,
        production_relative=package_relative / "official_p2p3.py",
        data_relative=(
            Path("thesis/experiments/llm_probe/runs/data-raw")
            / f"drift-dga-2026-rev-{revision}"
            / "DRIFT_input_eSLD"
            / "T17_dga_train.parquet"
        ),
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def member_list_sha256(domains: Iterable[str]) -> str:
    """按筛选行序与字节长度哈希，制品中不保存原始域名。"""
    digest = hashlib.sha256()
    for index, domain in enumerate(domains):
        encoded = domain.encode("utf-8")
        digest.update(index.to_bytes(8, "big"))
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def load_fixed_members(path: Path, config: VerificationConfig) -> tuple[list[str], dict[str, Any]]:
    """精确复现 production ``load_split(30000)`` 的 DGA 行序成员。"""
    parquet = pq.ParquetFile(path)
    if parquet.metadata is None or parquet.metadata.num_rows < config.member_limit:
        raise ValueError(f"T17 DGA 行数不足 {config.member_limit}：{path}")
    domains: list[str] = []
    for batch in parquet.iter_batches(batch_size=4096, columns=["domain"]):
        domains.extend(str(value) for value in batch.column("domain").to_pylist())
        if len(domains) >= config.member_limit:
            break
    domains = domains[:config.member_limit]
    if len(domains) != config.member_limit:
        raise ValueError("未能读取完整固定筛选成员")
    return domains, {
        "source_path": str(config.data_relative),
        "source_split": "T17_dga_train.parquet",
        "source_file_sha256": file_sha256(path),
        "source_row_count": int(parquet.metadata.num_rows),
        "selection_contract": "official_p2p3.py::load_split(30000) 的 DGA 分支：当前 Parquet 行序 [0,30000)，非随机抽样",
        "selection_code_evidence": {"load_split_lines": "140-145", "screening_call_lines": "591-604"},
        "members": len(domains),
        "member_list_sha256": member_list_sha256(domains),
        "domain_column_only": True,
        "labels_read": False,
        "resampling": False,
        "accessed_splits": ["T17_dga_train.parquet"],
    }


def source_segment(source: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(source, node)
    if segment is None:
        raise RuntimeError("无法提取 production 源代码片段")
    return segment


def extract_operators(path: Path) -> tuple[dict[str, Callable[[str, random.Random], str]], dict[str, Any]]:
    """AST 精确提取三个纯字符串函数，避免执行 production 顶层 torch/MPS 选设备。"""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    alpha_node: ast.Assign | ast.AnnAssign | None = None
    functions: dict[str, ast.FunctionDef] = {}
    generator: ast.FunctionDef | None = None
    names = ("perturb1", "perturb2", "perturb_half")
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(item, ast.Name) and item.id == "ALPHA" for item in targets):
                alpha_node = node
        if isinstance(node, ast.FunctionDef):
            if node.name in names:
                functions[node.name] = node
            if node.name == "gen_variants_L":
                generator = node
    if alpha_node is None or set(functions) != set(names) or generator is None:
        raise RuntimeError("production 缺少 V4 所需算子或课程生成函数")
    namespace: dict[str, Any] = {"random": random}
    module = ast.Module(body=[alpha_node, *(functions[name] for name in names)], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(path), "exec"), namespace)
    operators = {name: namespace[name] for name in names}
    if not all(callable(value) for value in operators.values()):
        raise RuntimeError("提取的 production 算子不可调用")
    generator_source = source_segment(source, generator)
    calls = ("perturb1(domain, rng)", "perturb2(domain, rng)", "perturb_half(domain, rng)")
    if not all(call in generator_source for call in calls):
        raise RuntimeError("课程生成函数已偏离冻结三档实现")
    return operators, {
        "production_file": str(path),
        "production_file_sha256": file_sha256(path),
        "operator_extraction": "对同一源文件 AST 精确提取定义；未导入顶层模块，未执行 torch、CUDA 或 MPS 代码",
        "operator_definitions": {
            name: {"lines": f"{functions[name].lineno}-{functions[name].end_lineno}", "source_sha256": sha256_bytes(source_segment(source, functions[name]).encode("utf-8"))}
            for name in names
        },
        "production_generation_semantics": {
            "gen_variants_L_lines": f"{generator.lineno}-{generator.end_lineno}",
            "training_cache_and_callsite_lines": "191-196,263-305",
            "finding": "每个 epoch 仅调用一个预算档并生成四个变体；缓存键为 (样本索引,epoch)，未为同一样本保存跨档三元组或共享编辑流。",
            "same_random_edit_stream_constructed_by_production": False,
        },
    }


def split_sld(domain: str) -> tuple[str, str]:
    if "." not in domain:
        return domain, ""
    body, suffix = domain.rsplit(".", 1)
    return body, "." + suffix


def changed_mapping(base: str, candidate: str) -> dict[int, str]:
    body, suffix = split_sld(base)
    candidate_body, candidate_suffix = split_sld(candidate)
    if suffix != candidate_suffix or len(body) != len(candidate_body):
        raise ValueError("production 算子改变 SLD 长度或后缀，无法按 V4 Hamming 口径核查")
    return {index: value for index, (old, value) in enumerate(zip(body, candidate_body)) if old != value}


def hamming(left: str, right: str) -> int:
    if len(left) != len(right):
        raise ValueError("Hamming 距离要求等长域名")
    return sum(left_char != right_char for left_char, right_char in zip(left, right))


def budgets(domain: str) -> dict[str, int]:
    body, _ = split_sld(domain)
    return {"m1": 1, "m2": 2, "mhalf": max(1, len(body) // 2)}


def replace_body(domain: str, edits: Iterable[tuple[int, str]]) -> str:
    body, suffix = split_sld(domain)
    characters = list(body)
    for index, replacement in edits:
        characters[index] = replacement
    return "".join(characters) + suffix


def shared_prefix_outputs(domain: str, rng: random.Random, config: VerificationConfig) -> tuple[dict[str, str], dict[str, int]]:
    """可构造耦合的解析自检；它不是当前 production 路径。"""
    body, _ = split_sld(domain)
    if not body:
        raise ValueError("发现空 SLD")
    domain_budgets = budgets(domain)
    positions = rng.sample(range(len(body)), min(max(domain_budgets.values()), len(body)))
    edits: list[tuple[int, str]] = []
    for index in positions:
        replacement = rng.choice(config.alphabet)
        while replacement == body[index]:
            replacement = rng.choice(config.alphabet)
        edits.append((index, replacement))
    return {key: replace_body(domain, edits[:budget]) for key, budget in domain_budgets.items()}, domain_budgets


def new_stats() -> dict[str, Any]:
    return {"sample_count": 0, "nested": 0, "hamming": 0, "missing": 0, "character": 0, "both": 0, "distance_sum": 0.0, "bound_sum": 0.0, "max_gap": 0}


def update_pair(stats: dict[str, Any], base: str, outputs: dict[str, str], domain_budgets: dict[str, int], first: str, second: str) -> bool:
    lower, higher = (first, second) if domain_budgets[first] <= domain_budgets[second] else (second, first)
    lower_edits, higher_edits = changed_mapping(base, outputs[lower]), changed_mapping(base, outputs[higher])
    missing = any(index not in higher_edits for index in lower_edits)
    character = any(index in higher_edits and higher_edits[index] != value for index, value in lower_edits.items())
    nested = not missing and not character
    distance, bound = hamming(outputs[first], outputs[second]), abs(domain_budgets[first] - domain_budgets[second])
    body, _ = split_sld(base)
    stats["sample_count"] += 1
    stats["nested"] += int(nested)
    stats["hamming"] += int(distance <= bound)
    stats["missing"] += int(missing and not character)
    stats["character"] += int(character and not missing)
    stats["both"] += int(missing and character)
    stats["distance_sum"] += distance / len(body)
    stats["bound_sum"] += bound / len(body)
    stats["max_gap"] = max(stats["max_gap"], distance - bound)
    return nested


def finish_stats(stats: dict[str, Any]) -> dict[str, Any]:
    count = stats["sample_count"]
    if count == 0:
        raise ValueError("空成员集不能核查 V4")
    nested, hamming_ok = stats["nested"], stats["hamming"]
    return {
        "sample_count": count,
        "observable_nested_output_count": nested,
        "observable_nested_output_failure_count": count - nested,
        "observable_nested_output_rate": nested / count,
        "hamming_bound_satisfied_count": hamming_ok,
        "hamming_bound_failure_count": count - hamming_ok,
        "hamming_bound_satisfied_rate": hamming_ok / count,
        "mean_normalized_hamming": stats["distance_sum"] / count,
        "mean_normalized_budget_gap_bound": stats["bound_sum"] / count,
        "max_integer_hamming_minus_bound": stats["max_gap"],
        "failure_type_counts": {"lower_edit_position_missing_from_higher": stats["missing"], "same_position_replacement_character_conflict": stats["character"], "both_position_and_character_conflict": stats["both"]},
    }


def summarize(domains: list[str], producer: Callable[[str], tuple[dict[str, str], dict[str, int]]]) -> dict[str, Any]:
    pairs = (("m1_vs_m2", "m1", "m2"), ("m1_vs_mhalf", "m1", "mhalf"), ("m2_vs_mhalf", "m2", "mhalf"))
    pair_stats = {name: new_stats() for name, _, _ in pairs}
    edit_counts = {key: {"sum": 0, "exact": 0} for key in ("m1", "m2", "mhalf")}
    all_nested, all_hamming = 0, 0
    for domain in domains:
        outputs, domain_budgets = producer(domain)
        for key in edit_counts:
            edit_count = len(changed_mapping(domain, outputs[key]))
            edit_counts[key]["sum"] += edit_count
            edit_counts[key]["exact"] += int(edit_count == domain_budgets[key])
        flags = [update_pair(pair_stats[name], domain, outputs, domain_budgets, first, second) for name, first, second in pairs]
        hamming_flags = [hamming(outputs[first], outputs[second]) <= abs(domain_budgets[first] - domain_budgets[second]) for _, first, second in pairs]
        all_nested += int(all(flags))
        all_hamming += int(all(hamming_flags))
    count = len(domains)
    return {
        "members": count,
        "operator_edit_budget_check": {key: {"mean_actual_changed_positions": value["sum"] / count, "exact_declared_budget_count": value["exact"], "exact_declared_budget_rate": value["exact"] / count} for key, value in edit_counts.items()},
        "pairwise": {name: finish_stats(value) for name, value in pair_stats.items()},
        "all_three_pairs_observable_nested_count": all_nested,
        "all_three_pairs_observable_nested_failure_count": count - all_nested,
        "all_three_pairs_observable_nested_rate": all_nested / count,
        "all_three_pairs_hamming_bound_satisfied_count": all_hamming,
        "all_three_pairs_hamming_bound_failure_count": count - all_hamming,
        "all_three_pairs_hamming_bound_satisfied_rate": all_hamming / count,
    }


def production_replay(domains: list[str], operators: dict[str, Callable[[str, random.Random], str]], config: VerificationConfig) -> dict[str, Any]:
    """同 RNG 的反事实顺序调用是审计探针，不是 training 的跨档生产路径。"""
    rng = random.Random(config.seed)
    result = summarize(domains, lambda domain: ({"m1": operators["perturb1"](domain, rng), "m2": operators["perturb2"](domain, rng), "mhalf": operators["perturb_half"](domain, rng)}, budgets(domain)))
    result["generation_semantics"] = "反事实联合重放：三次 production 调用只连续共享 Random 状态，各自抽样，不取一条编辑流的前缀。"
    result["is_actual_production_cross_tier_path"] = False
    return result


def constructible_check(domains: list[str], config: VerificationConfig) -> dict[str, Any]:
    rng = random.Random(config.seed)
    result = summarize(domains, lambda domain: shared_prefix_outputs(domain, rng, config))
    result["generation_semantics"] = "后验可构造：先抽一条无重复位置编辑流，三个预算分别取该流前缀。"
    result["is_current_production"] = False
    return result


def build_result(repo_root: Path, domains: list[str], identity: dict[str, Any], config: VerificationConfig) -> dict[str, Any]:
    operators, production_identity = extract_operators(repo_root / config.production_relative)
    replay, constructed = production_replay(domains, operators, config), constructible_check(domains, config)
    return {
        "schema_version": "v4_nested_coupling_verification_v2",
        "verification_status": "completed",
        "scope": {"research_route": "DRIFT", "source_period": "T17 only", "accessed_splits": ["T17_dga_train.parquet"], "t18_to_t25_accessed": False, "training_started": False, "mps_or_cuda_used": False, "execution_mode": "CPU-only：verifier 不导入 torch，只做 pyarrow 扫描与 Python 字符串编辑"},
        "seed": config.seed,
        "input_identity": identity,
        "production_identity": production_identity,
        "interpretation_boundary": {
            "set_inclusion_only": "各预算威胁集合的包含不提供逐样本、逐字符的共同随机流。",
            "posthoc_constructible_coupling": "可另行构造共享前缀，证明 T3 的条件命题可实现，但不追溯改变当前 production。",
            "current_production_shared_randomness": "当前 gen_variants_L 单档生成，未建立跨档三元组或共享编辑流。",
        },
        "posthoc_constructible_shared_prefix_check": constructed,
        "production_counterfactual_joint_replay": replay,
        "v4_precondition": {"required": "同一随机编辑序列；较小预算编辑位置与替换字符是较大预算的前缀。", "current_production_shared_stream_satisfied_count": 0, "current_production_shared_stream_failure_count": len(domains), "current_production_shared_stream_satisfied_rate": 0.0, "basis": "production 静态生成语义未构造共享流；反事实同 RNG 顺序重放亦没有全样本可观测嵌套。", "verdict": "当前 production 不满足 V4 共享前缀前提", "not_a_formula_or_candidate_decision": True},
        "observed_replay_summary": {"all_three_pairs_observable_nested_rate": replay["all_three_pairs_observable_nested_rate"], "all_three_pairs_hamming_bound_satisfied_rate": replay["all_three_pairs_hamming_bound_satisfied_rate"]},
    }


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + f".partial.{time.time_ns()}")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def parse_args(script_path: Path) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="核查 DRIFT V4 的 T17 嵌套编辑耦合")
    parser.add_argument("--output", type=Path, default=script_path.with_name("verify_v4_nested_coupling.json"), help="仅允许写入脚本所在目录")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    script_path = Path(__file__).resolve()
    args, config = parse_args(script_path), build_config()
    output_path = args.output.resolve()
    if output_path.parent != script_path.parent:
        raise ValueError("JSON 输出必须位于 V4 核查脚本目录")
    repo_root, data_path = script_path.parents[3], script_path.parents[3] / config.data_relative
    if not data_path.is_file():
        raise FileNotFoundError(f"固定 T17 输入不存在：{data_path}")
    domains, identity = load_fixed_members(data_path, config)
    result = build_result(repo_root, domains, identity, config)
    atomic_json(output_path, result)
    logger.info("V4 核查完成：%s；成员=%d；判定=%s", output_path.name, len(domains), result["v4_precondition"]["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
