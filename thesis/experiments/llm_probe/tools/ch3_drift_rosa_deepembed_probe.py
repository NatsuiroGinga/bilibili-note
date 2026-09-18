#!/usr/bin/env python3
"""DRIFT T17 到 T25 的离线 ROSA/DeepEmbed 数据病灶探针。"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np

SCHEMA_VERSION = "ch3-drift-rosa-deepembed-probe-v1"
Z_95 = 1.959963984540054
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class InputItem:
    path: Path
    year: str
    role: str
    label: int


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    partial.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("配置 schema_version 不匹配")
    if value.get("dataset_revision") != "3b31077020cd1c013d0a75cad51042a2327c4521":
        raise ValueError("数据 revision 不匹配")
    if value.get("inputs", {}).get("raw", {}).get("enabled"):
        raise ValueError("raw 审计路径尚未验收，本轮配置必须保持 disabled")
    return value


def parse_items(config: dict[str, Any]) -> list[InputItem]:
    root = Path(config["input_root"])
    result = []
    for value in config["inputs"]["esld"]:
        if set(value) != {"path", "year", "role", "label"}:
            raise ValueError("eSLD 输入项必须显式包含 path/year/role/label")
        if value["year"] not in {"T17", "T25"} or value["role"] not in {"source", "target"} or value["label"] not in {0, 1}:
            raise ValueError("输入项年份、角色或标签不符合冻结合同")
        result.append(InputItem(root / value["path"], value["year"], value["role"], value["label"]))
    if {(item.year, item.label) for item in result} != {("T17", 0), ("T17", 1), ("T25", 0), ("T25", 1)}:
        raise ValueError("必须恰有 T17/T25 与 benign/dga 四个明确分面")
    return result


def receipt(item: InputItem) -> dict[str, Any]:
    if not item.path.is_file():
        raise FileNotFoundError(f"输入不存在：{item.path}")
    parquet = pq.ParquetFile(item.path)
    if "domain" not in parquet.schema_arrow.names:
        raise ValueError(f"输入缺少 domain 列：{item.path}")
    return {"path": str(item.path), "year": item.year, "role": item.role, "label": item.label, "bytes": item.path.stat().st_size, "rows": parquet.metadata.num_rows, "sha256": sha256_file(item.path), "columns": parquet.schema_arrow.names}


def domains(item: InputItem, batch_size: int, limit: int | None = None) -> Iterator[str]:
    yielded = 0
    for batch in pq.ParquetFile(item.path).iter_batches(batch_size=batch_size, columns=["domain"]):
        for value in batch.column(0).to_pylist():
            if isinstance(value, str) and (domain := value.strip().lower()):
                yield domain; yielded += 1
                if limit is not None and yielded >= limit: return


def hist(counter: Counter[int]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter)}


def facets(domain: str, lengths: Counter[int], composition: Counter[str]) -> None:
    lengths[len(domain)] += 1
    digit, hyphen = any(char.isdigit() for char in domain), "-" in domain
    composition["contains_digit"] += int(digit); composition["contains_hyphen"] += int(hyphen); composition["pure_alpha"] += int(domain.isalpha()); composition["other"] += int(not domain.isalpha() and not digit and not hyphen)


def tokens(domain: str, order: int) -> list[str]:
    return list(domain) if order == 1 else [domain[i:i + order] for i in range(max(0, len(domain) - order + 1))]


def tail(counter: Counter[str]) -> dict[str, Any]:
    freq = Counter(counter.values())
    return {"unique_keys": len(counter), "occurrences": int(sum(counter.values())), "frequency_histogram": hist(freq), "singleton_keys": int(freq.get(1, 0)), "max_frequency": int(max(counter.values(), default=0))}


def vocab_hash(counter: Counter[str]) -> str:
    digest = hashlib.sha256()
    for token in sorted(counter): digest.update(token.encode("utf-8") + b"\0" + str(counter[token]).encode("ascii") + b"\n")
    return digest.hexdigest()


def scan_source(item: InputItem, batch_size: int, beat: int, beats: list[dict[str, Any]], start: float) -> tuple[dict[int, Counter[str]], dict[str, Any]]:
    vocab = {1: Counter(), 2: Counter(), 3: Counter()}; lengths: Counter[int] = Counter(); composition: Counter[str] = Counter(); rows = 0
    for domain in domains(item, batch_size):
        rows += 1; facets(domain, lengths, composition)
        for order in vocab: vocab[order].update(tokens(domain, order))
        if rows % beat == 0: beats.append({"stage": "deepembed_source", "stratum": f"{item.year}:{item.label}", "rows": rows, "elapsed_seconds": time.monotonic() - start})
    return vocab, {"valid_domains": rows, "length_histogram": hist(lengths), "composition": dict(composition)}


def scan_target(item: InputItem, source: dict[int, Counter[str]], batch_size: int, beat: int, beats: list[dict[str, Any]], start: float) -> dict[str, Any]:
    rows = 0; lengths: Counter[int] = Counter(); composition: Counter[str] = Counter(); target = {1: Counter(), 2: Counter(), 3: Counter()}; pos: Counter[int] = Counter(); oov: Counter[int] = Counter(); domain_oov: Counter[int] = Counter(); seen_sum: Counter[int] = Counter(); seen_count: Counter[int] = Counter()
    for domain in domains(item, batch_size):
        rows += 1; facets(domain, lengths, composition)
        for order in target:
            current = tokens(domain, order); target[order].update(current); pos[order] += len(current); missing = 0
            for token in current:
                frequency = source[order].get(token, 0)
                if frequency: seen_sum[order] += frequency; seen_count[order] += 1
                else: missing += 1
            oov[order] += missing; domain_oov[order] += int(missing > 0)
        if rows % beat == 0: beats.append({"stage": "deepembed_target", "stratum": f"{item.year}:{item.label}", "rows": rows, "elapsed_seconds": time.monotonic() - start})
    result = {}
    for order in target:
        result[str(order)] = {"positions": int(pos[order]), "oov_positions": int(oov[order]), "position_oov_rate": oov[order] / max(pos[order], 1), "domains_with_oov": int(domain_oov[order]), "domain_oov_rate": domain_oov[order] / max(rows, 1), "known_token_frequency_mean": seen_sum[order] / max(seen_count[order], 1), "target_frequency_tail": tail(target[order]), "new_unique_keys": len(set(target[order]) - set(source[order])), "disappeared_source_keys": len(set(source[order]) - set(target[order])), "shared_unique_keys": len(set(source[order]) & set(target[order]))}
    return {"valid_domains": rows, "length_histogram": hist(lengths), "composition": dict(composition), "per_order": result}


def sample_plan(items: list[InputItem], config: dict[str, Any], pilot_domains: int | None) -> dict[str, Any]:
    if pilot_domains is not None:
        if pilot_domains <= 0: raise ValueError("pilot_domains 必须为正数")
        return {"mode": "pilot", "mechanism_adjudication": False, "strata": {f"{item.year}:{item.label}": {"per_stratum_limit": pilot_domains} for item in items}}
    sampling = config["rosa_sampling"]; half_width = sampling["worst_case_binomial_half_width"]
    if half_width is None: raise ValueError("默认半宽为 null；请用 --pilot-domains 测吞吐，或由主代理冻结半宽后才可正式抽样")
    if not 0 < half_width < 1: raise ValueError("最坏二项比例半宽必须在 (0,1)")
    requested = math.ceil((Z_95 ** 2) * 0.25 / (half_width ** 2))
    strata = {}
    for item in items:
        rows = pq.ParquetFile(item.path).metadata.num_rows; required = min(requested, rows)
        seed_material = f"{config['dataset_revision']}|{item.year}|{item.label}|{item.path}"
        seed = int.from_bytes(hashlib.sha256(seed_material.encode("utf-8")).digest()[:8], "little")
        strata[f"{item.year}:{item.label}"] = {"requested_sample_size": requested, "required_sample_size": required, "metadata_rows": rows, "probability": min(1.0, required / rows), "algorithm": "SplitMix64(row_index xor seed)", "seed_derivation": "SHA256(revision|year|label|path) 前64位小端", "seed": seed, "row_order": "Parquet 冻结文件物理行顺序；由输入 SHA256 与 revision 收据冻结"}
    return {"mode": "deterministic_hash", "confidence": 0.95, "requested_half_width": half_width, "mechanism_adjudication": True, "strata": strata}


def splitmix64(values: np.ndarray) -> np.ndarray:
    values = (values + np.uint64(0x9E3779B97F4A7C15)).astype(np.uint64)
    values = (values ^ (values >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    values = (values ^ (values >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return values ^ (values >> np.uint64(31))


def heartbeat(stage: str, item: InputItem, scanned: int, selected_rows: int, start: float) -> None:
    print(json.dumps({"stage": stage, "stratum": f"{item.year}:{item.label}", "scanned_rows": scanned, "selected_rows": selected_rows, "elapsed_seconds": time.monotonic() - start}, ensure_ascii=False), file=sys.stderr, flush=True)


def rosa_domain(domain: str) -> tuple[list[tuple[int, int, bool]], dict[int, tuple[int, int, int, int]]]:
    seq = list(domain); cap = 2 * len(seq) + 1; trans: list[dict[str, int] | None] = [None] * cap; link = [-1] * cap; length = [0] * cap; end = [-1] * cap; trans[0] = {}; state = 0; nxt = 1; rosa = []; fixed: dict[int, tuple[int, int, int, int]] = {}
    for order in range(1, len(seq)):
        seen: dict[str, str] = {}; eligible = predictable = hits = entries = 0
        for index in range(order - 1, len(seq) - 1):
            context = "".join(seq[index - order + 1:index + 1]); eligible += 1
            if context in seen: predictable += 1; hits += int(seen[context] == seq[index + 1])
            else: entries += 1
            seen[context] = seq[index + 1]
        fixed[order] = (eligible, predictable, hits, entries)
    for index, token in enumerate(seq):
        current = nxt; nxt += 1; trans[current] = {}; length[current] = length[state] + 1; previous = state
        while previous != -1 and token not in trans[previous]: trans[previous][token] = current; previous = link[previous]
        if previous == -1: link[current] = 0
        else:
            candidate = trans[previous][token]
            if length[previous] + 1 == length[candidate]: link[current] = candidate
            else:
                clone = nxt; nxt += 1; trans[clone] = trans[candidate].copy(); length[clone] = length[previous] + 1; link[clone] = link[candidate]; end[clone] = end[candidate]
                while previous != -1 and trans[previous].get(token) == candidate: trans[previous][token] = clone; previous = link[previous]
                link[candidate] = link[current] = clone
        state = current; match = state
        while match != -1 and not (length[match] > 0 and end[match] >= 0): match = link[match]
        if match != -1 and index + 1 < len(seq): rosa.append((length[match], index - end[match], seq[end[match] + 1] == seq[index + 1]))
        update = state
        while update != -1 and end[update] < index: end[update] = index; update = link[update]
    return rosa, fixed


def scan_rosa(item: InputItem, batch_size: int, plan: dict[str, Any], start: float) -> dict[str, Any]:
    scan_start = time.monotonic(); lengths: Counter[int] = Counter(); composition: Counter[str] = Counter(); match: Counter[int] = Counter(); distance: Counter[int] = Counter(); hits: Counter[int] = Counter(); fixed: dict[int, Counter[str]] = {}; sampled = eligible = predictable = scanned = selected_rows = duplicate_rows = 0; selected_domains: set[str] = set(); limit = plan.get("per_stratum_limit")
    for batch in pq.ParquetFile(item.path).iter_batches(batch_size=batch_size, columns=["domain"]):
        raw_values = batch.column(0).to_pylist() if plan["mode"] == "pilot" else None; batch_rows = batch.num_rows
        if plan["mode"] == "pilot": indices = np.arange(min(batch_rows, max(limit - scanned, 0)), dtype=np.int64)
        else:
            row_indices = np.arange(scanned, scanned + batch_rows, dtype=np.uint64)
            probability = float(plan["probability"])
            if probability >= 1.0:
                indices = np.arange(batch_rows, dtype=np.int64)
            else:
                threshold_value = min((1 << 64) - 1, int(probability * (1 << 64)))
                threshold = np.uint64(threshold_value)
                indices = np.flatnonzero(splitmix64(row_indices ^ np.uint64(plan["seed"])) < threshold)
        selected_rows += len(indices); values = raw_values if raw_values is not None else batch.column(0).take(pa.array(indices)).to_pylist()
        for value in values:
            if not isinstance(value, str) or not (domain := value.strip().lower()): continue
            duplicate_rows += int(domain in selected_domains); selected_domains.add(domain); sampled += 1; facets(domain, lengths, composition); result, curve = rosa_domain(domain); eligible += max(len(domain) - 1, 0); predictable += len(result)
            for size, gap, hit in result: match[size] += 1; distance[gap] += 1; hits[size] += int(hit)
            for order, counts in curve.items():
                bucket = fixed.setdefault(order, Counter()); bucket["eligible_positions"] += counts[0]; bucket["predictable_positions"] += counts[1]; bucket["successor_hits"] += counts[2]; bucket["state_entries"] += counts[3]; bucket["key_utf8_bytes"] += counts[3] * order
        scanned += batch_rows
        if scanned % 1000000 < batch_rows: heartbeat("rosa", item, scanned, selected_rows, scan_start)
        if plan["mode"] == "pilot" and scanned >= limit: break
    curve = {str(order): {**dict(counter), "coverage_rate": counter["predictable_positions"] / max(counter["eligible_positions"], 1), "successor_hit_rate": counter["successor_hits"] / max(counter["predictable_positions"], 1)} for order, counter in sorted(fixed.items())}
    elapsed = time.monotonic() - scan_start
    heartbeat("rosa_complete", item, scanned, selected_rows, scan_start)
    return {"scanned_rows": scanned, "selected_rows": selected_rows, "sampled_domains": sampled, "sampled_unique_domains": len(selected_domains), "duplicate_sample_rows": duplicate_rows, "actual_sampling_rate": selected_rows / max(scanned, 1), "length_histogram": hist(lengths), "composition": dict(composition), "eligible_positions": eligible, "predictable_positions": predictable, "coverage_rate": predictable / max(eligible, 1), "match_length_histogram": hist(match), "history_distance_histogram": hist(distance), "successor_hits_by_match_length": hist(hits), "successor_hit_rate": sum(hits.values()) / max(predictable, 1), "state_reset": "每域名重置", "fixed_ngram_cost_curve": curve, "elapsed_seconds": elapsed, "domains_per_second": sampled / max(elapsed, 1e-12)}


def aggregate_rosa(strata: dict[str, dict[str, Any]]) -> dict[str, Any]:
    eligible = sum(value["eligible_positions"] for value in strata.values()); predictable = sum(value["predictable_positions"] for value in strata.values())
    fixed: dict[str, Counter[str]] = {}; match: Counter[int] = Counter(); distance: Counter[int] = Counter(); hits: Counter[int] = Counter()
    for value in strata.values():
        match.update({int(key): count for key, count in value["match_length_histogram"].items()}); distance.update({int(key): count for key, count in value["history_distance_histogram"].items()}); hits.update({int(key): count for key, count in value["successor_hits_by_match_length"].items()})
        for order, curve in value["fixed_ngram_cost_curve"].items():
            bucket = fixed.setdefault(order, Counter())
            for key in ("eligible_positions", "predictable_positions", "successor_hits", "state_entries", "key_utf8_bytes"): bucket[key] += curve.get(key, 0)
    return {"sampled_domains": sum(value["sampled_domains"] for value in strata.values()), "eligible_positions": eligible, "predictable_positions": predictable, "coverage_rate": predictable / max(eligible, 1), "match_length_histogram": hist(match), "history_distance_histogram": hist(distance), "successor_hits_by_match_length": hist(hits), "successor_hits": sum(hits.values()), "successor_hit_rate": sum(hits.values()) / max(predictable, 1), "fixed_ngram_cost_curve": {order: {**dict(value), "coverage_rate": value["predictable_positions"] / max(value["eligible_positions"], 1), "successor_hit_rate": value["successor_hits"] / max(value["predictable_positions"], 1)} for order, value in fixed.items()}, "aggregation": "由四个已扫描分面计数相加，不重复扫描"}


def aggregate_deepembed(source: dict[str, dict[str, Any]], target: dict[str, dict[str, Any]]) -> dict[str, Any]:
    per_order = {}
    for order in ("1", "2", "3"):
        positions = sum(value["per_order"][order]["positions"] for value in target.values()); oov = sum(value["per_order"][order]["oov_positions"] for value in target.values()); domains_count = sum(value["valid_domains"] for value in target.values()); domains_oov = sum(value["per_order"][order]["domains_with_oov"] for value in target.values())
        per_order[order] = {"positions": positions, "oov_positions": oov, "position_oov_rate": oov / max(positions, 1), "domains": domains_count, "domains_with_oov": domains_oov, "domain_oov_rate": domains_oov / max(domains_count, 1)}
    return {"source_domains": sum(value["valid_domains"] for value in source.values()), "target_domains": sum(value["valid_domains"] for value in target.values()), "per_order": per_order, "aggregation": "由四个已扫描分面计数相加，不重复扫描"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--config", required=True, type=Path); parser.add_argument("--output", required=True, type=Path); parser.add_argument("--pilot-domains", type=int, help="每个分面的 ROSA/固定阶吞吐测量域名数")
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    start = time.monotonic(); config = load_config(args.config); items = parse_items(config); batch_size = int(config["batch_size"]); beat = int(config["heartbeat_rows"])
    if batch_size <= 0 or beat <= 0: raise ValueError("batch_size 与 heartbeat_rows 必须为正数")
    receipts = [receipt(item) for item in items]; plan = sample_plan(items, config, args.pilot_domains); beats: list[dict[str, Any]] = []
    runtime = {"elapsed_seconds": 0.0, "heartbeats": beats, "python_version": sys.version, "python_executable": sys.executable, "pyarrow_version": pa.__version__}
    if plan["mode"] == "pilot": deepembed: dict[str, Any] = {"status": "未运行；pilot 只测 ROSA/固定阶吞吐，不裁决机制"}
    else:
        source_parts = {}; pooled = {1: Counter(), 2: Counter(), 3: Counter()}
        for item in items:
            if item.role == "source":
                vocab, summary = scan_source(item, batch_size, beat, beats, start); source_parts[f"{item.year}:{item.label}"] = summary
                for order in pooled: pooled[order].update(vocab[order])
        target_parts = {f"{item.year}:{item.label}": scan_target(item, pooled, batch_size, beat, beats, start) for item in items if item.role == "target"}
        deepembed = {"source_strata": source_parts, "target_strata": target_parts, "source_vocabularies": {str(order): {**tail(counter), "vocabulary_sha256": vocab_hash(counter)} for order, counter in pooled.items()}, "interpretation_boundary": "字符表只是下界；结合 2/3-gram、频数长尾与新生/消失质量，不构成机制通过。"}
    runtime["elapsed_seconds"] = time.monotonic() - start
    atomic_json(args.output, {"schema_version": SCHEMA_VERSION, "status": "running", "completed_stage": "deepembed", "run_identity": config["run_identity"], "dataset_revision": config["dataset_revision"], "config_sha256": sha256_file(args.config), "input_files": receipts, "sampling": plan, "deepembed": deepembed, "rosa": {"strata": {}}, "runtime": runtime})
    rosa_strata = {}
    for item in items:
        key = f"{item.year}:{item.label}"; rosa_strata[key] = scan_rosa(item, batch_size, {"mode": plan["mode"], **plan["strata"][key]}, start)
        runtime["elapsed_seconds"] = time.monotonic() - start
        atomic_json(args.output, {"schema_version": SCHEMA_VERSION, "status": "running", "completed_stage": f"rosa:{key}", "run_identity": config["run_identity"], "dataset_revision": config["dataset_revision"], "config_sha256": sha256_file(args.config), "input_files": receipts, "sampling": plan, "deepembed": deepembed, "rosa": {"strata": rosa_strata}, "runtime": runtime})
    if plan["mode"] == "deterministic_hash":
        for key, value in rosa_strata.items():
            detail = plan["strata"][key]; actual = value["sampled_domains"]; detail["actual_sample_size"] = actual; detail["actual_worst_case_half_width"] = Z_95 * math.sqrt(0.25 / max(actual, 1)); detail["hash_sampling_deviation"] = actual - detail["required_sample_size"]
    if plan["mode"] != "pilot": deepembed["overall"] = aggregate_deepembed(deepembed["source_strata"], deepembed["target_strata"])
    runtime["elapsed_seconds"] = time.monotonic() - start
    atomic_json(args.output, {"schema_version": SCHEMA_VERSION, "status": "completed", "run_identity": config["run_identity"], "dataset_revision": config["dataset_revision"], "config_sha256": sha256_file(args.config), "input_files": receipts, "filter_rules": {"domain": "strip + lower；空字符串跳过；不保存逐域名标签、预测或样本"}, "sampling": plan, "deepembed": deepembed, "rosa": {"strata": rosa_strata, "overall": aggregate_rosa(rosa_strata)}, "raw_audit": {"enabled": False, "status": "机械拒绝；当前 SQLite 路径未验收"}, "runtime": runtime})


if __name__ == "__main__":
    arguments = parse_args()
    try: run(arguments)
    except Exception as error:
        failure: dict[str, Any] = {}
        try:
            existing = json.loads(arguments.output.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                failure.update(existing)
        except Exception:
            pass
        try:
            parsed = json.loads(arguments.config.read_text(encoding="utf-8")); failure.update({"run_identity": parsed.get("run_identity"), "dataset_revision": parsed.get("dataset_revision"), "config_sha256": sha256_file(arguments.config)})
        except Exception: pass
        failure.update({"schema_version": SCHEMA_VERSION, "status": "failed", "error_type": type(error).__name__, "error": str(error)})
        atomic_json(arguments.output, failure); raise
