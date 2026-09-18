#!/usr/bin/env python3
"""检验 DRIFT 条件记忆轴在 T17--T19 源期是否具有真实病灶资格。"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
import warnings
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import torch
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from tokenizers import Tokenizer

import ch3_drift_n10_conservative_fusion_pilot as pilot


SCHEMA_VERSION = "ch3-drift-condmem-source-qualification-v1"
ALLOWED_YEARS = ("T17", "T18", "T19")
KEY_KINDS = ("char1", "word1", "char2", "char3")
MODES = ("real", "frequency_control", "key_control")
D0_FEATURES = (
    "length_log1p",
    "digit_ratio",
    "hyphen_ratio",
    "alpha_ratio",
    "wordpiece_length_log1p",
    "wordpiece_unk_ratio",
    "char1_u",
    "word1_u",
    "char2_u",
    "char3_u",
    "char1_q",
    "word1_q",
    "char2_q",
    "char3_q",
)
DE_SIGNALS = ("char1_s", "char1_a", "word1_s", "word1_a")
ENGRAM_SIGNALS = (
    "char2_s",
    "char2_a",
    "char2_c",
    "char3_s",
    "char3_a",
    "char3_c",
)


@dataclass(frozen=True)
class InputSpec:
    year: str
    role: str
    label: int | None
    path: Path
    rows: int
    sha256: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(partial, path)


def atomic_npz(path: Path, arrays: Mapping[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    with partial.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.replace(partial, path)


def atomic_parquet(path: Path, table: pa.Table) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    pq.write_table(table, partial, compression="zstd")
    os.replace(partial, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sample_digest(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


def normalize_esld(value: Any) -> str:
    return str(value).strip().lower()


def raw_to_esld(value: Any) -> str:
    return normalize_esld(value).split(".", 1)[0]


def progress(stage: str, processed: int, total: int, started: float, **extra: Any) -> None:
    payload = {
        "stage": stage,
        "processed": processed,
        "total": total,
        "elapsed_seconds": time.monotonic() - started,
        **extra,
    }
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr, flush=True)


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("配置 schema_version 不匹配")
    if config.get("approved_scope") != "t17_t18_t19_source_qualification_only":
        raise ValueError("配置未保持源期资格诊断范围")
    if config.get("screening_only") is not True or config.get("seed") != 42:
        raise ValueError("配置必须保持 screening_only 与冻结种子 42")
    if config.get("dataset_revision") != "3b31077020cd1c013d0a75cad51042a2327c4521":
        raise ValueError("DRIFT 数据 revision 不匹配")
    if config["keys"] != {
        "char_orders": [1, 2, 3],
        "wordpiece_orders": [1],
        "jeffreys_pseudocount": 0.5,
        "exclude": ["full_esld_hash", "raw_domain", "tld", "family", "year", "row_index"],
    }:
        raise ValueError("安全键合同不匹配")
    analysis = config["analysis"]
    if analysis["required_future_years"] != ["T18", "T19"]:
        raise ValueError("源期确认年份不匹配")
    if analysis["required_labels"] != [0, 1]:
        raise ValueError("诊断必须覆盖良性与 DGA")
    runtime = config["runtime"]
    if runtime.get("cuda_bf16_autocast") is not False:
        raise ValueError("P0 验证路径必须保持 FP32")
    return config


def input_specs(config: Mapping[str, Any], root: Path, key: str) -> tuple[InputSpec, ...]:
    data_root = root / str(config["data_root"])
    output: list[InputSpec] = []
    for item in config[key]:
        year = str(item["year"])
        if year not in ALLOWED_YEARS:
            raise ValueError(f"发现未授权年份：{year}")
        path_text = str(item["path"])
        if any(token in path_text for token in ("T20", "T21", "T22", "T23", "T24", "T25")):
            raise ValueError("配置发现目标期路径")
        path = data_root / path_text
        if path.is_absolute() and data_root not in path.parents:
            raise ValueError("输入路径越出冻结数据根")
        output.append(
            InputSpec(
                year=year,
                role=str(item.get("role", "raw_family")),
                label=int(item["label"]) if "label" in item else None,
                path=path,
                rows=int(item["rows"]),
                sha256=str(item["sha256"]),
            )
        )
    return tuple(output)


def verify_spec(spec: InputSpec, expected_columns: Sequence[str]) -> dict[str, Any]:
    if not spec.path.is_file():
        raise FileNotFoundError(f"输入文件不存在：{spec.path}")
    parquet = pq.ParquetFile(spec.path)
    columns = parquet.schema_arrow.names
    rows = int(parquet.metadata.num_rows)
    if list(expected_columns) != columns:
        raise ValueError(f"输入字段不匹配：{spec.path} -> {columns}")
    if rows != spec.rows:
        raise ValueError(f"输入行数不匹配：{spec.path} -> {rows} != {spec.rows}")
    digest = sha256_file(spec.path)
    if digest != spec.sha256:
        raise ValueError(f"输入 SHA-256 不匹配：{spec.path}")
    return {
        "year": spec.year,
        "role": spec.role,
        "label": spec.label,
        "path": str(spec.path),
        "rows": rows,
        "columns": columns,
        "sha256": digest,
    }


def verify_all_inputs(
    fit: Sequence[InputSpec], validation: Sequence[InputSpec], raw: Sequence[InputSpec]
) -> dict[str, list[dict[str, Any]]]:
    if [(item.year, item.label) for item in fit] != [("T17", 0), ("T17", 1)]:
        raise ValueError("T17 拟合成员清单不匹配")
    expected_validation = [(year, label) for year in ALLOWED_YEARS for label in (0, 1)]
    if [(item.year, item.label) for item in validation] != expected_validation:
        raise ValueError("T17--T19 验证成员清单不匹配")
    if [item.year for item in raw] != list(ALLOWED_YEARS):
        raise ValueError("raw family 成员清单不匹配")
    return {
        "fit": [verify_spec(item, ("domain", "label")) for item in fit],
        "validation": [verify_spec(item, ("domain", "label")) for item in validation],
        "raw_family": [verify_spec(item, ("domain", "label", "family")) for item in raw],
    }


def verify_file(path: Path, expected_hash: str, description: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"{description}不存在：{path}")
    digest = sha256_file(path)
    if digest != expected_hash:
        raise ValueError(f"{description} SHA-256 不匹配")
    return digest


def verify_p0(config: Mapping[str, Any], root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    p0 = config["p0"]
    p0_root = root / str(p0["root"])
    receipts: dict[str, Any] = {}
    for key, hash_key, description in (
        ("checkpoint", "checkpoint_sha256", "P0 检查点"),
        ("tokenizer", "tokenizer_sha256", "P0 tokenizer"),
        ("effective_config", "effective_config_sha256", "P0 有效配置"),
        ("result", "result_sha256", "P0 结果"),
        ("status", "status_sha256", "P0 状态"),
    ):
        path = p0_root / str(p0[key])
        receipts[key] = {"path": str(path), "sha256": verify_file(path, str(p0[hash_key]), description)}
    source_code = root / str(p0["source_code"])
    receipts["source_code"] = {
        "path": str(source_code),
        "sha256": verify_file(source_code, str(p0["source_code_sha256"]), "P0 源代码"),
    }
    result = json.loads((p0_root / str(p0["result"])).read_text(encoding="utf-8"))
    status = json.loads((p0_root / str(p0["status"])).read_text(encoding="utf-8"))
    if result.get("status") != "completed" or status.get("status") != "completed":
        raise ValueError("P0 未完成")
    state = pilot.load_checkpoint(p0_root / str(p0["checkpoint"]))
    if state.get("phase") != "static":
        raise ValueError("P0 检查点不是 static 完成阶段")
    effective = json.loads((p0_root / str(p0["effective_config"])).read_text(encoding="utf-8"))
    p0_config = effective.get("config")
    if not isinstance(p0_config, dict):
        raise ValueError("P0 有效配置缺少 config")
    return p0_config, {"receipts": receipts, "result": result, "state": state}


def iter_labeled_domains(spec: InputSpec, batch_rows: int) -> Iterator[list[str]]:
    processed = 0
    started = time.monotonic()
    for batch in pq.ParquetFile(spec.path).iter_batches(
        batch_size=batch_rows, columns=["domain", "label"]
    ):
        frame = batch.to_pydict()
        if spec.label is None or any(int(value) != spec.label for value in frame["label"]):
            raise ValueError(f"成员标签与配置不一致：{spec.path}")
        domains = [normalize_esld(value) for value in frame["domain"]]
        processed += len(domains)
        yield domains
        if processed % 100_000 < len(domains):
            progress("scan_domains", processed, spec.rows, started, year=spec.year, label=spec.label)
    if processed != spec.rows:
        raise RuntimeError(f"输入未完整遍历：{spec.path}")


def ngrams(values: Sequence[Any], order: int) -> list[Any]:
    if order <= 0 or len(values) < order:
        return []
    if order == 1:
        return list(values)
    if isinstance(values, str):
        return [values[index : index + order] for index in range(len(values) - order + 1)]
    return [tuple(values[index : index + order]) for index in range(len(values) - order + 1)]


def tokenizer_special_ids(tokenizer: Tokenizer) -> set[int]:
    names = ("[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]")
    return {value for name in names if (value := tokenizer.token_to_id(name)) is not None}


def document_keys(domain: str, encoding_ids: Sequence[int], special_ids: set[int]) -> dict[str, set[Any]]:
    word_ids = [int(value) for value in encoding_ids if int(value) not in special_ids]
    return {
        "char1": set(ngrams(domain, 1)),
        "word1": set(word_ids),
        "char2": set(ngrams(domain, 2)),
        "char3": set(ngrams(domain, 3)),
    }


def build_frequency_store(
    specs: Sequence[InputSpec], tokenizer: Tokenizer, batch_rows: int
) -> tuple[dict[str, tuple[Counter[Any], Counter[Any]]], dict[str, Any]]:
    counters = {kind: (Counter(), Counter()) for kind in KEY_KINDS}
    seen: dict[int, set[bytes]] = {0: set(), 1: set()}
    documents = {0: 0, 1: 0}
    duplicates = {0: 0, 1: 0}
    special_ids = tokenizer_special_ids(tokenizer)
    started = time.monotonic()
    for spec in specs:
        assert spec.label is not None
        for domains in iter_labeled_domains(spec, batch_rows):
            encodings = tokenizer.encode_batch(domains, add_special_tokens=False)
            for domain, encoding in zip(domains, encodings, strict=True):
                digest = sample_digest(domain)
                if digest in seen[spec.label]:
                    duplicates[spec.label] += 1
                    continue
                seen[spec.label].add(digest)
                documents[spec.label] += 1
                for kind, keys in document_keys(domain, encoding.ids, special_ids).items():
                    counters[kind][spec.label].update(keys)
    overlap = len(seen[0].intersection(seen[1]))
    receipt = {
        "documents_by_label": {str(key): value for key, value in documents.items()},
        "duplicates_within_label": {str(key): value for key, value in duplicates.items()},
        "cross_label_esld_overlap": overlap,
        "unique_keys": {
            kind: len(set(pair[0]).union(pair[1])) for kind, pair in counters.items()
        },
        "wall_seconds": time.monotonic() - started,
    }
    return counters, receipt


def frequency_arrays(
    counters: Mapping[str, tuple[Counter[Any], Counter[Any]]]
) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for kind in KEY_KINDS:
        negative, positive = counters[kind]
        keys = sorted(set(negative).union(positive))
        if kind == "word1":
            arrays[f"{kind}_keys"] = np.asarray(keys, dtype=np.int64)
        else:
            arrays[f"{kind}_keys"] = np.asarray(keys, dtype=np.str_)
        arrays[f"{kind}_d0"] = np.fromiter((negative[key] for key in keys), dtype=np.int64)
        arrays[f"{kind}_d1"] = np.fromiter((positive[key] for key in keys), dtype=np.int64)
    return arrays


def load_frequency_maps(path: Path) -> dict[str, dict[Any, tuple[int, int]]]:
    output: dict[str, dict[Any, tuple[int, int]]] = {}
    with np.load(path, allow_pickle=False) as values:
        for kind in KEY_KINDS:
            keys = values[f"{kind}_keys"].tolist()
            d0 = values[f"{kind}_d0"]
            d1 = values[f"{kind}_d1"]
            output[kind] = {
                key: (int(negative), int(positive))
                for key, negative, positive in zip(keys, d0, d1, strict=True)
            }
    return output


def deterministic_offset(config_hash: str, name: str, size: int) -> int:
    if size <= 1:
        return 0
    digest = hashlib.sha256(f"{config_hash}:{name}".encode("utf-8")).digest()
    return 1 + int.from_bytes(digest[:8], "big") % (size - 1)


def build_control_maps(
    real: Mapping[str, dict[Any, tuple[int, int]]], config_hash: str
) -> dict[str, dict[str, dict[Any, tuple[int, int]]]]:
    modes: dict[str, dict[str, dict[Any, tuple[int, int]]]] = {
        "real": {kind: dict(values) for kind, values in real.items()},
        "frequency_control": {},
        "key_control": {},
    }
    for kind, values in real.items():
        keys = sorted(values)
        offset = deterministic_offset(config_hash, f"frequency:{kind}", len(keys))
        shifted = keys[offset:] + keys[:offset]
        modes["frequency_control"][kind] = {
            key: values[source] for key, source in zip(keys, shifted, strict=True)
        }
        by_total: dict[int, list[Any]] = defaultdict(list)
        for key in keys:
            by_total[sum(values[key])].append(key)
        controlled: dict[Any, tuple[int, int]] = {}
        for total, group in by_total.items():
            group.sort()
            group_offset = deterministic_offset(config_hash, f"key:{kind}:{total}", len(group))
            group_shifted = group[group_offset:] + group[:group_offset]
            for key, source in zip(group, group_shifted, strict=True):
                source_positive = values[source][1]
                controlled[key] = (total - source_positive, source_positive)
        modes["key_control"][kind] = controlled
    return modes


def entropy_bernoulli(probability: float) -> float:
    if probability <= 0.0 or probability >= 1.0:
        return 0.0
    return -probability * math.log(probability) - (1.0 - probability) * math.log(1.0 - probability)


def key_metrics(
    keys: Sequence[Any],
    kind: str,
    maps: Mapping[str, Mapping[str, Mapping[Any, tuple[int, int]]]],
    document_total: int,
    pseudocount: float,
) -> dict[str, float]:
    output: dict[str, float] = {}
    real_map = maps["real"][kind]
    output[f"{kind}_u"] = (
        float(sum(key not in real_map for key in keys) / len(keys)) if keys else 0.0
    )
    for mode in MODES:
        values = maps[mode][kind]
        known = [(key, values[key]) for key in keys if key in values]
        if not known:
            support = ambiguity = score = combination = 0.0
        else:
            support_values: list[float] = []
            ambiguity_values: list[float] = []
            score_values: list[float] = []
            combination_values: list[float] = []
            unigram = maps[mode]["char1"]
            for key, (negative, positive) in known:
                total = negative + positive
                support_values.append(-math.log(total / document_total))
                probability = (positive + pseudocount) / (total + 2.0 * pseudocount)
                ambiguity_values.append(entropy_bernoulli(probability))
                score_values.append(math.log((positive + pseudocount) / (negative + pseudocount)))
                if kind in {"char2", "char3"}:
                    denominator = 1.0
                    for token in str(key):
                        token_total = sum(unigram.get(token, (0, 0)))
                        denominator *= max(token_total / document_total, np.finfo(np.float64).tiny)
                    numerator = total / document_total
                    combination_values.append(-math.log(numerator / denominator))
            support = float(np.mean(support_values))
            ambiguity = float(np.mean(ambiguity_values))
            score = float(np.mean(score_values))
            combination = float(np.mean(combination_values)) if combination_values else 0.0
        suffix = "" if mode == "real" else f"_{mode}"
        output[f"{kind}_s{suffix}"] = support
        output[f"{kind}_a{suffix}"] = ambiguity
        output[f"{kind}_c{suffix}"] = combination
        if mode == "real":
            output[f"{kind}_q"] = score
    return output


def domain_features(
    domain: str,
    token_ids: Sequence[int],
    special_ids: set[int],
    unk_id: int | None,
    maps: Mapping[str, Mapping[str, Mapping[Any, tuple[int, int]]]],
    document_total: int,
    pseudocount: float,
) -> dict[str, float]:
    length = len(domain)
    word_ids = [int(value) for value in token_ids if int(value) not in special_ids]
    features = {
        "length_log1p": math.log1p(length),
        "digit_ratio": sum(char.isdigit() for char in domain) / max(length, 1),
        "hyphen_ratio": domain.count("-") / max(length, 1),
        "alpha_ratio": sum(char.isalpha() for char in domain) / max(length, 1),
        "wordpiece_length_log1p": math.log1p(len(word_ids)),
        "wordpiece_unk_ratio": (
            sum(value == unk_id for value in token_ids) / max(len(token_ids), 1)
            if unk_id is not None
            else 0.0
        ),
    }
    sequences: dict[str, Sequence[Any]] = {
        "char1": ngrams(domain, 1),
        "word1": word_ids,
        "char2": ngrams(domain, 2),
        "char3": ngrams(domain, 3),
    }
    for kind, keys in sequences.items():
        features.update(key_metrics(keys, kind, maps, document_total, pseudocount))
    return features


def load_p0_model(
    config: Mapping[str, Any], root: Path, p0_config: dict[str, Any], state: Mapping[str, Any]
) -> tuple[pilot.StaticDual, Tokenizer, torch.device]:
    p0_root = root / str(config["p0"]["root"])
    tokenizer = Tokenizer.from_file(str(p0_root / str(config["p0"]["tokenizer"])))
    device = pilot.device_for_run()
    model = pilot.build_static(p0_config, tokenizer.get_vocab_size()).to(device)
    model.token = pilot.EncoderBranch(model.token)
    model.char = pilot.EncoderBranch(model.char)
    model.load_state_dict(state["static_model"], strict=True)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad = False
    return model, tokenizer, device


def source_threshold(p0_result: Mapping[str, Any]) -> float:
    receipt = p0_result.get("source_threshold")
    if not isinstance(receipt, dict):
        raise ValueError("P0 结果缺少源阈值")
    if receipt.get("threshold_space") != "logit_difference":
        raise ValueError("P0 源阈值空间不匹配")
    return float(receipt["threshold_float32"])


def predict_spec(
    spec: InputSpec,
    model: pilot.StaticDual,
    tokenizer: Tokenizer,
    device: torch.device,
    model_config: Mapping[str, Any],
    maps: Mapping[str, Mapping[str, Mapping[Any, tuple[int, int]]]],
    document_total: int,
    pseudocount: float,
    threshold: float,
    batch_size: int,
    batch_rows: int,
) -> tuple[dict[str, list[Any]], list[str]]:
    if spec.label is None:
        raise ValueError("验证成员缺少标签")
    special_ids = tokenizer_special_ids(tokenizer)
    unk_id = tokenizer.token_to_id("[UNK]")
    columns: dict[str, list[Any]] = defaultdict(list)
    dga_domains: list[str] = []
    processed = 0
    started = time.monotonic()
    with torch.inference_mode():
        for domains_block in iter_labeled_domains(spec, batch_rows):
            for offset in range(0, len(domains_block), batch_size):
                domains = domains_block[offset : offset + batch_size]
                encodings = tokenizer.encode_batch(domains, add_special_tokens=False)
                token_cpu = torch.tensor(
                    [
                        pilot.pad_ids(
                            encoding.ids,
                            int(model_config["model"]["max_len_token"]),
                        )
                        for encoding in encodings
                    ],
                    dtype=torch.long,
                )
                char_cpu = pilot.encode_char_cpu(
                    domains, int(model_config["model"]["max_len_char"])
                )
                logits = model(
                    token_cpu.to(device, non_blocking=device.type == "cuda"),
                    char_cpu.to(device, non_blocking=device.type == "cuda"),
                ).float()
                differences = (logits[:, 1] - logits[:, 0]).cpu().numpy().astype(np.float32)
                probabilities = torch.sigmoid(logits[:, 1] - logits[:, 0]).cpu().numpy().astype(np.float32)
                for local_index, (domain, encoding, difference, probability) in enumerate(
                    zip(domains, encodings, differences, probabilities, strict=True)
                ):
                    margin = float((2 * spec.label - 1) * difference)
                    loss = float(np.logaddexp(0.0, -margin))
                    values = domain_features(
                        domain,
                        encoding.ids,
                        special_ids,
                        unk_id,
                        maps,
                        document_total,
                        pseudocount,
                    )
                    columns["year"].append(spec.year)
                    columns["label"].append(spec.label)
                    columns["row_index"].append(processed + local_index)
                    columns["esld_sha256"].append(sample_digest(domain))
                    columns["probability_float32"].append(float(probability))
                    columns["logit_difference_float32"].append(float(difference))
                    columns["signed_margin"].append(margin)
                    columns["c00_loss"].append(loss)
                    columns["c00_error"].append(int(margin <= 0.0))
                    columns["source_threshold_error"].append(
                        int((difference >= threshold) != bool(spec.label))
                    )
                    for name, value in values.items():
                        columns[name].append(float(value))
                    if spec.label == 1:
                        dga_domains.append(domain)
                processed += len(domains)
                if processed % 100_000 < len(domains):
                    progress(
                        "p0_forward",
                        processed,
                        spec.rows,
                        started,
                        year=spec.year,
                        label=spec.label,
                    )
    if processed != spec.rows:
        raise RuntimeError(f"验证成员未完整前向：{spec.path}")
    return dict(columns), dga_domains


def family_mapping(
    spec: InputSpec, target_domains: Iterable[str], batch_rows: int
) -> tuple[dict[str, set[str]], dict[str, Any]]:
    targets = set(target_domains)
    mapped: dict[str, set[str]] = defaultdict(set)
    processed = 0
    started = time.monotonic()
    for batch in pq.ParquetFile(spec.path).iter_batches(
        batch_size=batch_rows, columns=["domain", "family", "label"]
    ):
        frame = batch.to_pydict()
        for domain, family, label in zip(
            frame["domain"], frame["family"], frame["label"], strict=True
        ):
            if int(label) != 1:
                raise ValueError(f"raw DGA 成员含非恶意标签：{spec.path}")
            key = raw_to_esld(domain)
            if key in targets:
                value = str(family).strip().lower()
                if value:
                    mapped[key].add(value)
        processed += len(frame["domain"])
        if processed % 1_000_000 < len(frame["domain"]):
            progress("family_join", processed, spec.rows, started, year=spec.year)
    if processed != spec.rows:
        raise RuntimeError(f"raw family 成员未完整扫描：{spec.path}")
    unique = sum(len(values) == 1 for values in mapped.values())
    ambiguous = sum(len(values) > 1 for values in mapped.values())
    missing = len(targets) - len(mapped)
    return dict(mapped), {
        "target_keys": len(targets),
        "unique": unique,
        "ambiguous": ambiguous,
        "missing": missing,
        "raw_rows": processed,
        "wall_seconds": time.monotonic() - started,
    }


def add_family_columns(
    columns: dict[str, list[Any]], domains: Sequence[str], mapping: Mapping[str, set[str]]
) -> None:
    family_hashes: list[bytes | None] = []
    statuses: list[str] = []
    for domain in domains:
        values = mapping.get(domain, set())
        if len(values) == 1:
            family_hashes.append(sample_digest(next(iter(values))))
            statuses.append("unique")
        elif len(values) > 1:
            family_hashes.append(None)
            statuses.append("ambiguous")
        else:
            family_hashes.append(None)
            statuses.append("missing")
    columns["family_sha256"] = family_hashes
    columns["family_mapping_status"] = statuses


def add_benign_family_columns(columns: dict[str, list[Any]]) -> None:
    rows = len(columns["label"])
    columns["family_sha256"] = [None] * rows
    columns["family_mapping_status"] = ["not_applicable"] * rows


def combine_columns(parts: Sequence[Mapping[str, Sequence[Any]]]) -> dict[str, list[Any]]:
    if not parts:
        raise ValueError("没有可合并的逐样本列")
    names = set(parts[0])
    if any(set(part) != names for part in parts[1:]):
        raise ValueError("良性与 DGA 特征列不一致")
    return {name: [value for part in parts for value in part[name]] for name in sorted(names)}


def table_from_columns(columns: Mapping[str, Sequence[Any]]) -> pa.Table:
    arrays: dict[str, pa.Array] = {}
    for name, values in columns.items():
        if name in {"esld_sha256", "family_sha256"}:
            arrays[name] = pa.array(values, type=pa.binary(32))
        elif name in {"label", "c00_error", "source_threshold_error"}:
            arrays[name] = pa.array(values, type=pa.int8())
        elif name == "row_index":
            arrays[name] = pa.array(values, type=pa.int64())
        elif name in {"year", "family_mapping_status"}:
            arrays[name] = pa.array(values, type=pa.string())
        else:
            arrays[name] = pa.array(values, type=pa.float32())
    return pa.table(arrays)


def arrow_numpy(table: pa.Table, name: str) -> np.ndarray:
    return np.asarray(table.column(name).combine_chunks().to_numpy(zero_copy_only=False))


def empirical_rank_reference(values: np.ndarray) -> np.ndarray:
    finite = np.asarray(values, dtype=np.float64)
    if not np.isfinite(finite).all():
        raise ValueError("经验秩拟合发现非有限值")
    return np.sort(finite)


def apply_empirical_midrank(values: np.ndarray, reference: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    left = np.searchsorted(reference, values, side="left")
    right = np.searchsorted(reference, values, side="right")
    return (left + right) / (2.0 * max(len(reference), 1))


def matrix_from_table(
    table: pa.Table,
    names: Sequence[str],
    references: Mapping[str, np.ndarray] | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    raw = {name: arrow_numpy(table, name).astype(np.float64, copy=False) for name in names}
    if references is None:
        references = {name: empirical_rank_reference(values) for name, values in raw.items()}
    matrix = np.column_stack(
        [apply_empirical_midrank(raw[name], references[name]) for name in names]
    )
    return matrix, dict(references)


def model_features(candidate: str, mode: str) -> tuple[str, ...]:
    if candidate == "d0":
        return D0_FEATURES
    signals = DE_SIGNALS if candidate == "de" else ENGRAM_SIGNALS
    suffix = "" if mode == "real" else f"_{mode}"
    return (*D0_FEATURES, *(f"{name}{suffix}" for name in signals))


def fit_error_model(
    table: pa.Table, names: Sequence[str], settings: Mapping[str, Any]
) -> tuple[LogisticRegression, dict[str, np.ndarray], dict[str, Any]]:
    matrix, references = matrix_from_table(table, names)
    target = arrow_numpy(table, "c00_error").astype(np.int64, copy=False)
    if set(np.unique(target)) != {0, 1}:
        raise ValueError("T17 诊断拟合必须同时含正确与错误样本")
    model = LogisticRegression(
        penalty=settings["penalty"],
        solver=str(settings["solver"]),
        max_iter=int(settings["max_iter"]),
        tol=float(settings["tol"]),
        random_state=42,
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        model.fit(matrix, target)
    convergence = [str(item.message) for item in caught if issubclass(item.category, ConvergenceWarning)]
    if convergence or int(model.n_iter_[0]) >= int(settings["max_iter"]):
        raise RuntimeError(f"逻辑回归未收敛：{convergence or model.n_iter_.tolist()}")
    return model, references, {
        "features": list(names),
        "intercept": model.intercept_.tolist(),
        "coefficients": model.coef_.tolist(),
        "iterations": model.n_iter_.tolist(),
    }


def predict_error_model(
    model: LogisticRegression,
    references: Mapping[str, np.ndarray],
    table: pa.Table,
    names: Sequence[str],
) -> np.ndarray:
    matrix, _ = matrix_from_table(table, names, references)
    return model.predict_proba(matrix)[:, 1]


def binary_log_loss(target: np.ndarray, probability: np.ndarray) -> np.ndarray:
    epsilon = np.finfo(np.float64).eps
    probability = np.clip(np.asarray(probability, dtype=np.float64), epsilon, 1.0 - epsilon)
    target = np.asarray(target, dtype=np.float64)
    return -(target * np.log(probability) + (1.0 - target) * np.log1p(-probability))


def paired_interval(candidate: np.ndarray, reference: np.ndarray, z_value: float) -> dict[str, Any]:
    difference = np.asarray(candidate, dtype=np.float64) - np.asarray(reference, dtype=np.float64)
    if difference.size < 2 or not np.isfinite(difference).all():
        raise ValueError("成对区间输入无效")
    mean = float(np.mean(difference))
    standard_error = float(np.std(difference, ddof=1) / math.sqrt(difference.size))
    return {
        "n": int(difference.size),
        "mean_log_loss_difference": mean,
        "standard_error": standard_error,
        "ci_lower": mean - z_value * standard_error,
        "ci_upper": mean + z_value * standard_error,
        "candidate_better": mean + z_value * standard_error < 0.0,
    }


def subset_table(table: pa.Table, mask: np.ndarray) -> pa.Table:
    return table.filter(pa.array(np.asarray(mask, dtype=np.bool_)))


def table_for_label(table: pa.Table, label: int) -> pa.Table:
    return subset_table(table, arrow_numpy(table, "label") == label)


def residual_correlation(
    table: pa.Table,
    signal: str,
    controls: Sequence[str],
    control_references: Mapping[str, np.ndarray],
    signal_reference: np.ndarray,
    loss_reference: np.ndarray,
) -> float:
    control_matrix, _ = matrix_from_table(table, controls, control_references)
    design = np.column_stack((np.ones(control_matrix.shape[0]), control_matrix))
    signal_values = apply_empirical_midrank(arrow_numpy(table, signal), signal_reference)
    loss_values = apply_empirical_midrank(arrow_numpy(table, "c00_loss"), loss_reference)
    signal_residual = signal_values - design @ np.linalg.lstsq(design, signal_values, rcond=None)[0]
    loss_residual = loss_values - design @ np.linalg.lstsq(design, loss_values, rcond=None)[0]
    if np.std(signal_residual) == 0.0 or np.std(loss_residual) == 0.0:
        return 0.0
    return float(np.corrcoef(signal_residual, loss_residual)[0, 1])


def family_centered_correlation(table: pa.Table, signal: str) -> dict[str, Any]:
    status = np.asarray(table.column("family_mapping_status").to_pylist(), dtype=object)
    mask = status == "unique"
    selected = subset_table(table, mask)
    families = selected.column("family_sha256").to_pylist()
    signal_values = arrow_numpy(selected, signal).astype(np.float64)
    loss_values = arrow_numpy(selected, "c00_loss").astype(np.float64)
    groups: dict[bytes, list[int]] = defaultdict(list)
    for index, family in enumerate(families):
        if family is not None:
            groups[family].append(index)
    signal_centered = signal_values.copy()
    loss_centered = loss_values.copy()
    for indices in groups.values():
        selected_indices = np.asarray(indices, dtype=np.int64)
        signal_centered[selected_indices] -= np.mean(signal_values[selected_indices])
        loss_centered[selected_indices] -= np.mean(loss_values[selected_indices])
    valid = np.isfinite(signal_centered) & np.isfinite(loss_centered)
    correlation = 0.0
    if valid.sum() >= 2 and np.std(signal_centered[valid]) > 0.0 and np.std(loss_centered[valid]) > 0.0:
        correlation = float(np.corrcoef(signal_centered[valid], loss_centered[valid])[0, 1])
    return {"rows": int(valid.sum()), "families": len(groups), "correlation": correlation}


def analyze(
    feature_paths: Mapping[str, Path], config: Mapping[str, Any]
) -> dict[str, Any]:
    tables = {year: pq.read_table(path) for year, path in feature_paths.items()}
    t17_dga = table_for_label(tables["T17"], 1)
    t17_status = np.asarray(t17_dga.column("family_mapping_status").to_pylist(), dtype=object)
    t17_family_values = t17_dga.column("family_sha256").to_pylist()
    t17_families = {
        family
        for family, status in zip(t17_family_values, t17_status, strict=True)
        if status == "unique" and family is not None
    }
    settings = config["analysis"]["logistic_regression"]
    z_value = float(config["analysis"]["confidence_z"])
    variants = {
        "d0_real": ("d0", "real"),
        "de_real": ("de", "real"),
        "de_frequency_control": ("de", "frequency_control"),
        "de_key_control": ("de", "key_control"),
        "engram_real": ("engram", "real"),
        "engram_frequency_control": ("engram", "frequency_control"),
        "engram_key_control": ("engram", "key_control"),
    }
    output: dict[str, Any] = {"by_label": {}, "partial_rank": {}, "family_centered": {}}
    support: dict[str, Any] = {}
    for label in (0, 1):
        train = table_for_label(tables["T17"], label)
        fitted: dict[str, tuple[LogisticRegression, dict[str, np.ndarray], tuple[str, ...]]] = {}
        fit_receipts: dict[str, Any] = {}
        for name, (candidate, mode) in variants.items():
            features = model_features(candidate, mode)
            model, references, receipt = fit_error_model(train, features, settings)
            fitted[name] = (model, references, features)
            fit_receipts[name] = receipt
        label_output: dict[str, Any] = {"fit": fit_receipts, "years": {}}
        for year in ("T18", "T19"):
            current = table_for_label(tables[year], label)
            target = arrow_numpy(current, "c00_error").astype(np.int64)
            losses: dict[str, np.ndarray] = {}
            for name, (model, references, features) in fitted.items():
                probability = predict_error_model(model, references, current, features)
                losses[name] = binary_log_loss(target, probability)
            year_output: dict[str, Any] = {}
            for candidate in ("de", "engram"):
                real_name = f"{candidate}_real"
                relevant_u = (
                    (arrow_numpy(current, "char1_u") == 0.0)
                    & (arrow_numpy(current, "word1_u") == 0.0)
                    if candidate == "de"
                    else (arrow_numpy(current, "char2_u") == 0.0)
                    & (arrow_numpy(current, "char3_u") == 0.0)
                )
                comparisons = {
                    "versus_d0": paired_interval(losses[real_name], losses["d0_real"], z_value),
                    "versus_frequency_control": paired_interval(
                        losses[real_name], losses[f"{candidate}_frequency_control"], z_value
                    ),
                    "versus_key_control": paired_interval(
                        losses[real_name], losses[f"{candidate}_key_control"], z_value
                    ),
                    "in_table_versus_d0": paired_interval(
                        losses[real_name][relevant_u], losses["d0_real"][relevant_u], z_value
                    ),
                }
                family_breakdown: dict[str, Any] | None = None
                if label == 1:
                    family_status = np.asarray(
                        current.column("family_mapping_status").to_pylist(), dtype=object
                    )
                    family_values = current.column("family_sha256").to_pylist()
                    unique = family_status == "unique"
                    seen = np.asarray(
                        [
                            bool(is_unique and family in t17_families)
                            for family, is_unique in zip(family_values, unique, strict=True)
                        ],
                        dtype=np.bool_,
                    )
                    new = unique & ~seen
                    if seen.sum() < 2:
                        raise ValueError(f"{year} 缺少足够的 T17 已见 family 样本")
                    comparisons["seen_family_versus_d0"] = paired_interval(
                        losses[real_name][seen], losses["d0_real"][seen], z_value
                    )
                    family_breakdown = {
                        "unique_rows": int(unique.sum()),
                        "seen_family_rows": int(seen.sum()),
                        "new_family_rows": int(new.sum()),
                        "ambiguous_rows": int((family_status == "ambiguous").sum()),
                        "missing_rows": int((family_status == "missing").sum()),
                    }
                year_output[candidate] = {
                    "rows": int(len(target)),
                    "error_rate": float(np.mean(target)),
                    "in_table_rows": int(relevant_u.sum()),
                    "comparisons": comparisons,
                    "family_breakdown": family_breakdown,
                }
            label_output["years"][year] = year_output
        output["by_label"][str(label)] = label_output

        d0_matrix, d0_references = matrix_from_table(train, D0_FEATURES)
        del d0_matrix
        loss_reference = empirical_rank_reference(arrow_numpy(train, "c00_loss"))
        partial_for_label: dict[str, Any] = {}
        for candidate, signals in (("de", DE_SIGNALS), ("engram", ENGRAM_SIGNALS)):
            signal_references = {
                signal: empirical_rank_reference(arrow_numpy(train, signal)) for signal in signals
            }
            by_year: dict[str, dict[str, float]] = {}
            for year in ALLOWED_YEARS:
                current = table_for_label(tables[year], label)
                by_year[year] = {
                    signal: residual_correlation(
                        current,
                        signal,
                        D0_FEATURES,
                        d0_references,
                        signal_references[signal],
                        loss_reference,
                    )
                    for signal in signals
                }
            consistent = [
                signal
                for signal in signals
                if all(by_year[year][signal] > 0.0 for year in ALLOWED_YEARS)
            ]
            partial_for_label[candidate] = {
                "by_year": by_year,
                "positive_direction_all_years": consistent,
            }
        output["partial_rank"][str(label)] = partial_for_label

    for year in ALLOWED_YEARS:
        dga = table_for_label(tables[year], 1)
        output["family_centered"][year] = {
            candidate: {
                signal: family_centered_correlation(dga, signal) for signal in signals
            }
            for candidate, signals in (("de", DE_SIGNALS), ("engram", ENGRAM_SIGNALS))
        }

    for candidate in ("de", "engram"):
        improvements = []
        controls = []
        in_table = []
        seen_family = []
        for label in (0, 1):
            for year in ("T18", "T19"):
                comparisons = output["by_label"][str(label)]["years"][year][candidate]["comparisons"]
                improvements.append(comparisons["versus_d0"]["candidate_better"])
                controls.extend(
                    (
                        comparisons["versus_frequency_control"]["candidate_better"],
                        comparisons["versus_key_control"]["candidate_better"],
                    )
                )
                in_table.append(comparisons["in_table_versus_d0"]["candidate_better"])
                if label == 1:
                    seen_family.append(comparisons["seen_family_versus_d0"]["candidate_better"])
        directions = [
            bool(output["partial_rank"][str(label)][candidate]["positive_direction_all_years"])
            for label in (0, 1)
        ]
        family_signals = []
        signals = DE_SIGNALS if candidate == "de" else ENGRAM_SIGNALS
        for signal in signals:
            if all(
                output["family_centered"][year][candidate][signal]["correlation"] > 0.0
                for year in ALLOWED_YEARS
            ):
                family_signals.append(signal)
        support[candidate] = {
            "independent_improvement_all_labels_years": all(improvements),
            "real_key_advantage_all_controls_labels_years": all(controls),
            "in_table_improvement_all_labels_years": all(in_table),
            "seen_family_improvement_both_years": all(seen_family),
            "positive_direction_each_label": all(directions),
            "positive_family_centered_all_years": family_signals,
        }
        support[candidate]["passed"] = bool(
            support[candidate]["independent_improvement_all_labels_years"]
            and support[candidate]["real_key_advantage_all_controls_labels_years"]
            and support[candidate]["in_table_improvement_all_labels_years"]
            and support[candidate]["seen_family_improvement_both_years"]
            and support[candidate]["positive_direction_each_label"]
            and family_signals
        )
    output["support"] = support
    output["status"] = (
        "supported_for_equal_capacity_short_training"
        if any(value["passed"] for value in support.values())
        else "rejected_after_source_qualification"
    )
    output["supported_candidates"] = [name for name, value in support.items() if value["passed"]]
    return output


def resource_receipt() -> dict[str, Any]:
    if not torch.cuda.is_available():
        return {"device": str(pilot.device_for_run()), "peak_allocated_bytes": None, "peak_reserved_bytes": None}
    return {
        "device": torch.cuda.get_device_name(0),
        "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_reserved_bytes": int(torch.cuda.max_memory_reserved()),
    }


def main() -> int:
    args = parse_args()
    root = args.project_root.resolve()
    run_dir = args.run_dir.resolve()
    config_path = args.config.resolve()
    config = load_config(config_path)
    config_hash = sha256_file(config_path)
    script_hash = sha256_file(Path(__file__).resolve())
    identity = {"config_sha": config_hash, "script_sha256": script_hash}
    status_path = run_dir / "status.json"
    if run_dir.exists() and not args.resume:
        raise FileExistsError("运行目录已存在；只允许 --resume 继续同一身份")
    run_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    atomic_json(status_path, {"status": "running", "stage": "verify", "identity": identity})
    try:
        fit = input_specs(config, root, "fit_inputs")
        validation = input_specs(config, root, "validation_inputs")
        raw = input_specs(config, root, "raw_family_inputs")
        input_receipts = verify_all_inputs(fit, validation, raw)
        p0_config, p0 = verify_p0(config, root)
        p0_receipt = p0["receipts"]
        identity["p0_checkpoint_sha256"] = p0_receipt["checkpoint"]["sha256"]
        identity["tokenizer_sha256"] = p0_receipt["tokenizer"]["sha256"]
        atomic_json(
            run_dir / "effective-config.json",
            {"config": config, "identity": identity, "input_receipts": input_receipts, "p0": p0_receipt},
        )
        model, tokenizer, device = load_p0_model(config, root, p0_config, p0["state"])
        torch.set_float32_matmul_precision("high")
        frequency_path = run_dir / "frequency-counts.npz"
        frequency_receipt_path = run_dir / "frequency-receipt.json"
        if frequency_path.is_file() and frequency_receipt_path.is_file() and args.resume:
            frequency_receipt = json.loads(frequency_receipt_path.read_text(encoding="utf-8"))
            if frequency_receipt.get("identity") != identity:
                raise ValueError("频数断点身份不匹配")
            if frequency_receipt.get("sha256") != sha256_file(frequency_path):
                raise ValueError("频数断点 SHA-256 不匹配")
        else:
            atomic_json(status_path, {"status": "running", "stage": "frequency", "identity": identity})
            counters, frequency_summary = build_frequency_store(
                fit, tokenizer, int(config["runtime"]["parquet_batch_rows"])
            )
            atomic_npz(frequency_path, frequency_arrays(counters))
            frequency_receipt = {
                "identity": identity,
                "sha256": sha256_file(frequency_path),
                "summary": frequency_summary,
            }
            atomic_json(frequency_receipt_path, frequency_receipt)
        real_maps = load_frequency_maps(frequency_path)
        maps = build_control_maps(real_maps, config_hash)
        document_total = sum(
            int(value)
            for value in frequency_receipt["summary"]["documents_by_label"].values()
        )
        threshold = source_threshold(p0["result"])
        feature_paths: dict[str, Path] = {}
        feature_receipts: dict[str, Any] = {}
        for year in ALLOWED_YEARS:
            feature_path = run_dir / f"features-{year}.parquet"
            receipt_path = run_dir / f"features-{year}-receipt.json"
            feature_paths[year] = feature_path
            if feature_path.is_file() and receipt_path.is_file() and args.resume:
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                if receipt.get("identity") != identity or receipt.get("sha256") != sha256_file(feature_path):
                    raise ValueError(f"{year} 特征断点身份或哈希不匹配")
                feature_receipts[year] = receipt
                continue
            atomic_json(status_path, {"status": "running", "stage": f"features_{year}", "identity": identity})
            benign_spec = next(item for item in validation if item.year == year and item.label == 0)
            dga_spec = next(item for item in validation if item.year == year and item.label == 1)
            benign_columns, _ = predict_spec(
                benign_spec,
                model,
                tokenizer,
                device,
                p0_config,
                maps,
                document_total,
                float(config["keys"]["jeffreys_pseudocount"]),
                threshold,
                int(config["runtime"]["prediction_batch_size"]),
                int(config["runtime"]["parquet_batch_rows"]),
            )
            add_benign_family_columns(benign_columns)
            dga_columns, dga_domains = predict_spec(
                dga_spec,
                model,
                tokenizer,
                device,
                p0_config,
                maps,
                document_total,
                float(config["keys"]["jeffreys_pseudocount"]),
                threshold,
                int(config["runtime"]["prediction_batch_size"]),
                int(config["runtime"]["parquet_batch_rows"]),
            )
            raw_spec = next(item for item in raw if item.year == year)
            mapping, mapping_receipt = family_mapping(
                raw_spec, dga_domains, int(config["runtime"]["parquet_batch_rows"])
            )
            add_family_columns(dga_columns, dga_domains, mapping)
            del dga_domains, mapping
            table = table_from_columns(combine_columns((benign_columns, dga_columns)))
            atomic_parquet(feature_path, table)
            receipt = {
                "identity": identity,
                "year": year,
                "rows": table.num_rows,
                "columns": table.column_names,
                "sha256": sha256_file(feature_path),
                "family_mapping": mapping_receipt,
            }
            atomic_json(receipt_path, receipt)
            feature_receipts[year] = receipt
        atomic_json(status_path, {"status": "running", "stage": "analysis", "identity": identity})
        analysis = analyze(feature_paths, config)
        result = {
            "schema_version": SCHEMA_VERSION,
            "status": analysis.pop("status"),
            "screening_only": True,
            "identity": identity,
            "input_receipts": input_receipts,
            "p0_receipts": p0_receipt,
            "frequency_receipt": frequency_receipt,
            "feature_receipts": feature_receipts,
            "source_threshold": threshold,
            "analysis": analysis,
            "runtime": {
                "wall_seconds": time.monotonic() - started,
                "resource_contention": bool(config["runtime"]["resource_contention"]),
                "resources": resource_receipt(),
            },
            "interpretation_boundary": config["interpretation_boundary"],
        }
        atomic_json(run_dir / "result.json", result)
        atomic_json(
            status_path,
            {
                "status": result["status"],
                "stage": "completed",
                "identity": identity,
                "result": "result.json",
                "result_sha256": sha256_file(run_dir / "result.json"),
            },
        )
        print(json.dumps({"status": result["status"], "run_dir": str(run_dir)}, ensure_ascii=False))
        return 0
    except Exception as error:
        atomic_json(
            status_path,
            {
                "status": "failed",
                "identity": identity,
                "error_type": type(error).__name__,
                "error": str(error),
            },
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
