#!/usr/bin/env python3
"""恢复 DRIFT T17 等权 MTP/TPP/TOV 训练后的完整辅助头。"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pyarrow.parquet as pq
import torch
from tokenizers import Tokenizer
from torch import Tensor, nn

import ch3_drift_n10_conservative_fusion_pilot as pilot


SCHEMA_VERSION = "ch3-drift-t17-equal3-auxheads-gradient-base-v1"
ARMS = ("char", "subword")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--arm", required=True, choices=ARMS)
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_file(path: Path, expected_hash: str, description: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"{description}不存在：{path}")
    digest = sha256_file(path)
    if digest != expected_hash:
        raise ValueError(f"{description} SHA-256 不匹配")
    return digest


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("配置 schema_version 不匹配")
    if config.get("approved_scope") != "t17_equal3_auxiliary_gradient_baseline_only":
        raise ValueError("配置未保持等权三任务梯度基准范围")
    if config.get("screening_only") is not True or config.get("seed") != 42:
        raise ValueError("配置必须保持 screening_only 与冻结种子 42")
    if config.get("dataset_revision") != "3b31077020cd1c013d0a75cad51042a2327c4521":
        raise ValueError("DRIFT 数据 revision 不匹配")
    training = config["training"]
    expected_training = {
        "batch_size": 1024,
        "optimizer": "adam",
        "learning_rate": 0.0001,
        "member_passes": 1,
        "cuda_bf16_autocast": True,
        "gradient_clip_norm": 1.0,
        "checkpoint_samples": 32768,
        "tasks": ["MTP", "TPP", "TOV"],
        "loss_combination": "unweighted_sum",
    }
    if training != expected_training:
        raise ValueError("训练配方偏离冻结 P0 等权三任务基准")
    if config["pretraining"] != {
        "mask_ratio": 0.15,
        "shuffle_probability": 0.5,
        "ignore_index": -100,
        "use_bert_pretokenizer": False,
    }:
        raise ValueError("预训练任务参数偏离冻结 P0")
    return config


def verify_p0_contract(config: Mapping[str, Any], root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    p0 = config["p0"]
    receipts: dict[str, Any] = {}
    for key, hash_key, description in (
        ("config", "config_sha256", "P0 配置"),
        ("source_code", "source_code_sha256", "P0 源代码"),
        ("tokenizer", "tokenizer_sha256", "P0 tokenizer"),
        ("char_backbone", "char_backbone_sha256", "P0 字符骨干"),
        ("subword_backbone", "subword_backbone_sha256", "P0 子词骨干"),
    ):
        file_path = root / str(p0[key])
        receipts[key] = {
            "path": str(file_path),
            "sha256": verify_file(file_path, str(p0[hash_key]), description),
        }
    p0_config = pilot.load_config(root / str(p0["config"]), root)
    training = p0_config["training"]
    if (
        int(training["batch_size"]),
        str(training["optimizer"]),
        float(training["learning_rate"]),
        int(training["pretraining_member_passes"]),
        bool(training["cuda_bf16_autocast"]),
    ) != (1024, "adam", 0.0001, 1, True):
        raise ValueError("P0 配置中的训练配方与恢复配置不一致")
    if p0_config["pretraining"] != {
        "tasks": ["MTP", "TPP", "TOV"],
        "mask_ratio": 0.15,
        "shuffle_probability": 0.5,
        "use_bert_pretokenizer": False,
        "ignore_index": -100,
    }:
        raise ValueError("P0 三任务定义与恢复配置不一致")
    return p0_config, receipts


def verify_fit_inputs(
    config: Mapping[str, Any], root: Path, p0_config: Mapping[str, Any]
) -> tuple[tuple[pilot.InputPart, pilot.InputPart], list[dict[str, Any]]]:
    parts = pilot.input_parts(dict(p0_config), root, "fit")
    configured = config["fit_inputs"]
    if len(configured) != 2:
        raise ValueError("T17 fit 必须包含两类成员")
    receipts: list[dict[str, Any]] = []
    for part, item in zip(parts, configured, strict=True):
        if part.label != int(item["label"]) or part.expected_rows != int(item["rows"]):
            raise ValueError("T17 fit 标签或行数偏离 P0")
        expected_path = (root / str(item["path"])).resolve()
        if part.path.resolve() != expected_path:
            raise ValueError("T17 fit 路径偏离 P0")
        parquet = pq.ParquetFile(part.path)
        if parquet.schema_arrow.names != ["domain", "label"]:
            raise ValueError(f"T17 fit 字段不匹配：{part.path}")
        if int(parquet.metadata.num_rows) != int(item["rows"]):
            raise ValueError(f"T17 fit 行数不匹配：{part.path}")
        digest = verify_file(part.path, str(item["sha256"]), "T17 fit 输入")
        receipts.append(
            {
                "path": str(part.path),
                "label": part.label,
                "rows": part.expected_rows,
                "sha256": digest,
            }
        )
    return parts, receipts


def checkpoint_identity(
    arm: str,
    config_hash: str,
    script_hash: str,
    p0_receipts: Mapping[str, Any],
    input_receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "arm": arm,
        "config_sha256": config_hash,
        "script_sha256": script_hash,
        "p0_config_sha256": p0_receipts["config"]["sha256"],
        "p0_source_code_sha256": p0_receipts["source_code"]["sha256"],
        "tokenizer_sha256": p0_receipts["tokenizer"]["sha256"],
        "input_sha256": [item["sha256"] for item in input_receipts],
    }


def save_checkpoint(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    torch.save(dict(value), partial)
    os.replace(partial, path)


def verify_checkpoint_identity(state: Mapping[str, Any], identity: Mapping[str, Any]) -> None:
    if state.get("identity") != identity:
        raise ValueError("恢复检查点身份不匹配")


def capture_rng() -> dict[str, Any]:
    return pilot.capture_rng_state()


def restore_rng(state: Mapping[str, Any]) -> None:
    pilot.restore_rng_state(dict(state))


def prepare_model(
    p0_config: dict[str, Any], tokenizer: Tokenizer
) -> tuple[pilot.StaticDual, torch.device]:
    pilot.set_seed(42)
    device = pilot.device_for_run()
    model = pilot.build_static(p0_config, tokenizer.get_vocab_size()).to(device)
    return model, device


def task_losses(
    branch: pilot.PretrainedBranch,
    views: tuple[Tensor, Tensor, Tensor, Tensor, Tensor, Tensor],
    ignore_index: int,
) -> tuple[Tensor, dict[str, Tensor], dict[str, int]]:
    losses = {
        "MTP": nn.functional.cross_entropy(
            branch(views[0], "MTP").flatten(0, 1),
            views[1].flatten(),
            ignore_index=ignore_index,
        ),
        "TPP": nn.functional.cross_entropy(
            branch(views[2], "TPP").flatten(0, 1),
            views[3].flatten(),
            ignore_index=ignore_index,
        ),
        "TOV": nn.functional.cross_entropy(branch(views[4], "TOV"), views[5]),
    }
    valid = {
        "MTP": int(views[1].ne(ignore_index).sum().item()),
        "TPP": int(views[3].ne(ignore_index).sum().item()),
        "TOV": int(views[5].numel()),
    }
    return losses["MTP"] + losses["TPP"] + losses["TOV"], losses, valid


def train_branch(
    arm: str,
    branch: pilot.PretrainedBranch,
    tokenizer: Tokenizer,
    p0_config: Mapping[str, Any],
    config: Mapping[str, Any],
    parts: tuple[pilot.InputPart, pilot.InputPart],
    device: torch.device,
    checkpoint_path: Path,
    identity: Mapping[str, Any],
    resume_state: Mapping[str, Any] | None,
) -> dict[str, Any]:
    optimizer = torch.optim.Adam(branch.parameters(), lr=float(config["training"]["learning_rate"]))
    completed_batch = -1
    examples_seen = 0
    loss_sums = {task: 0.0 for task in config["training"]["tasks"]}
    valid_counts = {task: 0 for task in config["training"]["tasks"]}
    batches = 0
    if resume_state is not None:
        verify_checkpoint_identity(resume_state, identity)
        branch.load_state_dict(resume_state["branch"], strict=True)
        optimizer.load_state_dict(resume_state["optimizer"])
        completed_batch = int(resume_state["completed_batch"])
        examples_seen = int(resume_state["examples_seen"])
        loss_sums = {key: float(value) for key, value in resume_state["loss_sums"].items()}
        valid_counts = {key: int(value) for key, value in resume_state["valid_counts"].items()}
        batches = int(resume_state["batches"])
        restore_rng(resume_state["rng_state"])
    settings = config["pretraining"]
    batch_size = int(config["training"]["batch_size"])
    checkpoint_interval = int(config["training"]["checkpoint_samples"]) // batch_size
    started = time.monotonic()
    for index, domains in enumerate(pilot.iter_domain_batches(parts, batch_size, 42)):
        if index <= completed_batch:
            continue
        if arm == "char":
            ids_cpu = pilot.encode_char_cpu(domains, int(p0_config["model"]["max_len_char"]))
        else:
            ids_cpu = pilot.encode_subword_cpu(
                domains, tokenizer, int(p0_config["model"]["max_len_token"])
            )
        views_cpu = pilot.pretraining_views(
            ids_cpu,
            int(config["seed"]) + index,
            int(settings["ignore_index"]),
            float(settings["mask_ratio"]),
            float(settings["shuffle_probability"]),
        )
        views = tuple(
            (value.pin_memory() if device.type == "cuda" else value).to(
                device, non_blocking=device.type == "cuda"
            )
            for value in views_cpu
        )
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast(
            device_type=device.type,
            dtype=torch.bfloat16,
            enabled=device.type == "cuda" and bool(config["training"]["cuda_bf16_autocast"]),
        ):
            total_loss, losses, valid = task_losses(
                branch, views, int(settings["ignore_index"])
            )
        if not torch.isfinite(total_loss):
            raise FloatingPointError("预训练损失出现非有限值")
        total_loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(
            branch.parameters(), max_norm=float(config["training"]["gradient_clip_norm"])
        )
        if not torch.isfinite(gradient_norm):
            raise FloatingPointError("预训练梯度范数出现非有限值")
        optimizer.step()
        examples_seen += len(domains)
        batches += 1
        for task in loss_sums:
            loss_sums[task] += float(losses[task].detach().cpu())
            valid_counts[task] += valid[task]
        completed_batch = index
        if (index + 1) % checkpoint_interval == 0:
            save_checkpoint(
                checkpoint_path,
                {
                    "identity": identity,
                    "status": "running",
                    "branch": branch.state_dict(),
                    "optimizer": optimizer.state_dict(),
                    "scheduler": None,
                    "grad_scaler": None,
                    "completed_batch": completed_batch,
                    "examples_seen": examples_seen,
                    "batches": batches,
                    "loss_sums": loss_sums,
                    "valid_counts": valid_counts,
                    "rng_state": capture_rng(),
                },
            )
            print(
                json.dumps(
                    {
                        "arm": arm,
                        "batches": batches,
                        "examples_seen": examples_seen,
                        "elapsed_seconds": time.monotonic() - started,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
    expected = sum(part.expected_rows for part in parts)
    if examples_seen != expected:
        raise RuntimeError(f"T17 fit 未完整遍历：{examples_seen} != {expected}")
    final = {
        "identity": identity,
        "status": "completed",
        "branch": branch.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": None,
        "grad_scaler": None,
        "completed_batch": completed_batch,
        "examples_seen": examples_seen,
        "batches": batches,
        "loss_sums": loss_sums,
        "valid_counts": valid_counts,
        "rng_state": capture_rng(),
    }
    save_checkpoint(checkpoint_path, final)
    return {
        "examples_seen": examples_seen,
        "batches": batches,
        "mean_batch_loss": {key: value / max(batches, 1) for key, value in loss_sums.items()},
        "valid_counts": valid_counts,
        "wall_seconds": time.monotonic() - started,
        "throughput_examples_per_second": expected / max(time.monotonic() - started, 1e-12),
    }


def compare_encoder(
    branch: pilot.PretrainedBranch, original_path: Path
) -> dict[str, Any]:
    expected_state = pilot.load_checkpoint(original_path)["branch"]
    actual_state = pilot.EncoderBranch(branch).state_dict()
    if set(expected_state) != set(actual_state):
        return {
            "keys_equal": False,
            "tensor_exact_match": False,
            "missing": sorted(set(expected_state) - set(actual_state)),
            "extra": sorted(set(actual_state) - set(expected_state)),
        }
    mismatched: list[str] = []
    maximum = 0.0
    for key in sorted(actual_state):
        actual = actual_state[key].detach().cpu()
        expected = expected_state[key].detach().cpu()
        if not torch.equal(actual, expected):
            mismatched.append(key)
            maximum = max(maximum, float((actual.float() - expected.float()).abs().max()))
    return {
        "keys_equal": True,
        "tensor_exact_match": not mismatched,
        "mismatched_tensor_count": len(mismatched),
        "maximum_absolute_difference": maximum,
        "first_mismatched_tensors": mismatched[:10],
    }


def resource_receipt() -> dict[str, Any]:
    if not torch.cuda.is_available():
        return {
            "device": str(pilot.device_for_run()),
            "peak_allocated_bytes": None,
            "peak_reserved_bytes": None,
        }
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
    if run_dir.name != config["arms"][args.arm]:
        raise ValueError("运行目录名与实验臂身份不一致")
    if run_dir.exists() and not args.resume:
        raise FileExistsError("运行目录已存在；只允许 --resume 继续同一身份")
    run_dir.mkdir(parents=True, exist_ok=True)
    status_path = run_dir / "status.json"
    checkpoint_path = run_dir / "checkpoint.pt"
    config_hash = sha256_file(config_path)
    script_hash = sha256_file(Path(__file__).resolve())
    started = time.monotonic()
    atomic_json(status_path, {"status": "running", "stage": "verify", "arm": args.arm})
    try:
        p0_config, p0_receipts = verify_p0_contract(config, root)
        parts, input_receipts = verify_fit_inputs(config, root, p0_config)
        identity = checkpoint_identity(
            args.arm, config_hash, script_hash, p0_receipts, input_receipts
        )
        predecessor_rng: Mapping[str, Any] | None = None
        if args.arm == "subword":
            char_root = root / "runs" / "diagnostics" / str(config["arms"]["char"])
            char_checkpoint_path = char_root / "checkpoint.pt"
            char_status = json.loads((char_root / "status.json").read_text(encoding="utf-8"))
            char_state = pilot.load_checkpoint(char_checkpoint_path)
            expected_char_identity = checkpoint_identity(
                "char", config_hash, script_hash, p0_receipts, input_receipts
            )
            verify_checkpoint_identity(char_state, expected_char_identity)
            if char_status.get("status") != "completed" or char_state.get("status") != "completed":
                raise ValueError("字符辅助头基准尚未完成")
            char_checkpoint_hash = sha256_file(char_checkpoint_path)
            if char_status.get("checkpoint_sha256") != char_checkpoint_hash:
                raise ValueError("字符辅助头检查点与状态哈希不匹配")
            if char_status.get("identity") != expected_char_identity:
                raise ValueError("字符辅助头状态身份不匹配")
            identity["predecessor_char_checkpoint_sha256"] = char_checkpoint_hash
            predecessor_rng = char_state["rng_state"]
        tokenizer = Tokenizer.from_file(str(root / str(config["p0"]["tokenizer"])))
        model, device = prepare_model(p0_config, tokenizer)
        torch.set_float32_matmul_precision("high")
        resume_state = (
            pilot.load_checkpoint(checkpoint_path)
            if args.resume and checkpoint_path.is_file()
            else None
        )
        if args.arm == "subword" and resume_state is None:
            if predecessor_rng is None:
                raise ValueError("子词基准缺少已核验的字符前序随机状态")
            restore_rng(predecessor_rng)
        branch = model.char if args.arm == "char" else model.token
        atomic_json(
            run_dir / "effective-config.json",
            {
                "config": config,
                "arm": args.arm,
                "identity": identity,
                "p0_receipts": p0_receipts,
                "input_receipts": input_receipts,
            },
        )
        atomic_json(
            status_path,
            {"status": "running", "stage": "training", "arm": args.arm, "identity": identity},
        )
        training = train_branch(
            args.arm,
            branch,
            tokenizer,
            p0_config,
            config,
            parts,
            device,
            checkpoint_path,
            identity,
            resume_state,
        )
        original_key = "char_backbone" if args.arm == "char" else "subword_backbone"
        comparison = compare_encoder(branch, root / str(config["p0"][original_key]))
        result = {
            "schema_version": SCHEMA_VERSION,
            "status": "completed",
            "screening_only": True,
            "arm": args.arm,
            "identity": identity,
            "training": training,
            "encoder_comparison_to_p0": comparison,
            "checkpoint_sha256": sha256_file(checkpoint_path),
            "full_branch_parameter_count": sum(parameter.numel() for parameter in branch.parameters()),
            "auxiliary_head_parameter_count": sum(
                parameter.numel()
                for name, parameter in branch.named_parameters()
                if name.startswith(("mtp_head", "tpp_head", "tov_head"))
            ),
            "runtime": {
                "wall_seconds": time.monotonic() - started,
                "resources": resource_receipt(),
            },
            "interpretation_boundary": config["interpretation_boundary"],
        }
        atomic_json(run_dir / "result.json", result)
        atomic_json(
            status_path,
            {
                "status": "completed",
                "stage": "completed",
                "arm": args.arm,
                "identity": identity,
                "result_sha256": sha256_file(run_dir / "result.json"),
                "checkpoint_sha256": result["checkpoint_sha256"],
            },
        )
        print(json.dumps({"status": "completed", "arm": args.arm}, ensure_ascii=False))
        return 0
    except Exception as error:
        atomic_json(
            status_path,
            {
                "status": "failed",
                "arm": args.arm,
                "error_type": type(error).__name__,
                "error": str(error),
            },
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
