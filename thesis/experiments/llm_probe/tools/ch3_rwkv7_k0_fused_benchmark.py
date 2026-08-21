"""RWKV-7 K0 纯 PyTorch 与 CUDA 融合核等价性和速度基准。"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import random
import subprocess
import threading
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

import ch3_rwkv7_field_aware_protocol_a_2x2 as legacy
import ch3_rwkv7_field_aware_protocol_a_2x2_bf16 as pure
import rwkv7_k0_fused_backend as fused_backend
from neural_precision_runtime import (
    autocast_context,
    fp32_island,
    load_and_validate_contract,
    validate_runtime_profile,
)


SCHEMA_VERSION = "ch3-rwkv7-k0-fused-benchmark-config-v1"
RESULT_SCHEMA_VERSION = "ch3-rwkv7-k0-fused-benchmark-results-v1"
BENCHMARK_ID = "ch3-rwkv7-k0-fused-equivalence-speed-v1"
SOURCE_ARRAYS = ("X23", "y23", "I23", "M23", "E23", "T23")
FORBIDDEN_TARGET_TOKENS = ("X24", "y24", "I24", "M24", "s24", "d24", "t24")
K0 = {"capacity": "K0", "channels": 112, "head_size": 16, "length": 128}


def log(message: str) -> None:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return Path(__file__).resolve().parent.parent / path


def validate_config(config: Mapping[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("融合核基准配置模式不符")
    if config.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError("融合核基准身份不符")
    if config.get("source_arrays") != list(SOURCE_ARRAYS):
        raise ValueError("融合核基准源年数组白名单不符")
    encoded = json.dumps(config, ensure_ascii=False)
    if any(token in encoded for token in FORBIDDEN_TARGET_TOKENS):
        raise ValueError("融合核基准配置不得枚举目标年数组")
    if config.get("target_year_paths_enumerated") != 0:
        raise ValueError("融合核基准的目标年路径枚举数必须为零")
    if config.get("k0_contract") != {
        "capacity": "K0",
        "channels": 112,
        "head_size": 16,
        "heads": 7,
        "sequence_length": 128,
        "chunk_length": 16,
        "input_dtype": "bfloat16",
        "output_dtype": "bfloat16",
        "state_dtype": "float32",
        "parameter_count": 104274,
    }:
        raise ValueError("K0 形状、精度或参数量合同不符")
    source = config.get("upstream", {})
    if source != {
        "repository": "https://github.com/BlinkDL/RWKV-LM",
        "commit": fused_backend.UPSTREAM_COMMIT,
        "license": "Apache-2.0",
    }:
        raise ValueError("上游来源合同不符")
    thresholds = config.get("numeric_thresholds", {})
    if thresholds != {
        "absolute": 0.03125,
        "relative": 0.02,
        "relative_denominator_floor": 1e-12,
        "selection_metric_absolute": 1e-6,
    }:
        raise ValueError("数值与选择指标门未按预注册值冻结")
    epoch = config.get("epoch_benchmark", {})
    if (
        epoch.get("cell") != "C00"
        or epoch.get("steps") != 1000
        or epoch.get("effective_batch_sequences") != 64
        or epoch.get("microbatch_sequences") != 8
        or epoch.get("selection_metric")
        != "LSPR23_entity_disjoint_validation_flow_average_precision"
    ):
        raise ValueError("整轮基准的格子、步数、批量或选择指标不符")
    performance = config.get("performance_qualification", {})
    if performance != {
        "minimum_throughput_ratio": 1.0,
        "maximum_peak_reserved_memory_ratio": 1.0,
        "require_selection_epoch_equal": True,
    }:
        raise ValueError("性能资格门不符")
    output_root = Path(config["paths"]["output_root"])
    build_root = Path(config["paths"]["extension_build_root"])
    if not output_root.is_absolute() or not build_root.is_absolute():
        raise ValueError("基准运行根和扩展编译根必须是服务器绝对路径")
    if output_root not in build_root.parents:
        raise ValueError("扩展编译根必须位于独立基准运行根内")
    if "bf16-v1" in str(output_root):
        raise ValueError("融合核基准不得写入活动纯 PyTorch 运行根")


def error_metrics(
    candidate: torch.Tensor,
    reference: torch.Tensor,
    thresholds: Mapping[str, float],
) -> dict[str, Any]:
    candidate64 = candidate.detach().double().cpu()
    reference64 = reference.detach().double().cpu()
    if candidate64.shape != reference64.shape:
        raise RuntimeError(
            f"数值对照形状不符：{tuple(candidate64.shape)} != {tuple(reference64.shape)}"
        )
    difference = (candidate64 - reference64).abs()
    denominator = reference64.abs().clamp(
        min=float(thresholds["relative_denominator_floor"])
    )
    allowed = float(thresholds["absolute"]) + float(thresholds["relative"]) * reference64.abs()
    finite = bool(torch.isfinite(candidate64).all() and torch.isfinite(reference64).all())
    return {
        "shape": list(reference64.shape),
        "finite": finite,
        "max_abs": float(difference.max()) if difference.numel() else 0.0,
        "max_rel": float((difference / denominator).max()) if difference.numel() else 0.0,
        "rmse": float(torch.sqrt(torch.mean(difference.square())))
        if difference.numel()
        else 0.0,
        "reference_scale": float(torch.sqrt(torch.mean(reference64.square())))
        if reference64.numel()
        else 0.0,
        "passed": finite and bool((difference <= allowed).all()),
    }


def mapping_error_summary(
    candidate: Mapping[str, torch.Tensor],
    reference: Mapping[str, torch.Tensor],
    thresholds: Mapping[str, float],
) -> dict[str, Any]:
    if set(candidate) != set(reference):
        raise RuntimeError("映射对照的键集不符")
    metrics = {
        name: error_metrics(candidate[name], reference[name], thresholds)
        for name in sorted(reference)
    }
    worst_name = max(metrics, key=lambda name: metrics[name]["max_abs"])
    return {
        "tensor_count": len(metrics),
        "all_passed": all(value["passed"] for value in metrics.values()),
        "worst_max_abs_name": worst_name,
        "worst_max_abs": metrics[worst_name]["max_abs"],
        "metrics": metrics,
    }


def pure_operator(
    inputs: Sequence[torch.Tensor], *, quantize_inputs: bool
) -> torch.Tensor:
    values = tuple(
        tensor.to(torch.bfloat16).float() if quantize_inputs else tensor.float()
        for tensor in inputs
    )
    r, w_raw, k, v, a, b = values
    w_clamped = -F.softplus(-w_raw) - 0.5
    return legacy.rwkv7_op(r, w_clamped, k, v, a, b, K0["head_size"])


def run_synthetic_branch(
    *,
    branch: str,
    initial: Sequence[torch.Tensor],
    upstream_gradient: torch.Tensor,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    parameters = [nn.Parameter(value.detach().clone().float()) for value in initial]
    optimizer = torch.optim.AdamW(
        parameters,
        lr=float(config["synthetic"]["optimizer_learning_rate"]),
        weight_decay=float(config["synthetic"]["optimizer_weight_decay"]),
    )
    if branch == "fp32":
        output = pure_operator(parameters, quantize_inputs=False)
    elif branch == "pytorch":
        output = pure_operator(parameters, quantize_inputs=True)
    elif branch == "fused":
        quantized = tuple(value.to(torch.bfloat16).contiguous() for value in parameters)
        output = fused_backend.rwkv7_k0_fused(
            *quantized,
            build_root=Path(config["paths"]["extension_build_root"]),
            verbose=bool(config["extension"]["verbose_build"]),
        ).float()
    else:
        raise ValueError(f"未知合成分支：{branch}")
    loss = (output.float() * upstream_gradient).sum() / output.numel()
    loss.backward()
    gradients = {
        name: parameter.grad.detach().clone()
        for name, parameter in zip(("r", "w_raw", "k", "v", "a", "b"), parameters)
        if parameter.grad is not None
    }
    optimizer.step()
    updated = {
        name: parameter.detach().clone()
        for name, parameter in zip(("r", "w_raw", "k", "v", "a", "b"), parameters)
    }
    return {
        "output": output.detach(),
        "loss": loss.detach().reshape(1),
        "gradients": gradients,
        "updated": updated,
    }


def run_synthetic(config: Mapping[str, Any]) -> dict[str, Any]:
    fused_backend.load_k0_extension(
        build_root=Path(config["paths"]["extension_build_root"]),
        verbose=bool(config["extension"]["verbose_build"]),
    )
    seed = int(config["synthetic"]["seed"])
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    device = torch.device("cuda")
    shape = (
        int(config["synthetic"]["batch_sequences"]),
        K0["length"],
        K0["channels"],
    )
    generator = torch.Generator(device=device).manual_seed(seed)
    initial = (
        torch.randn(shape, generator=generator, device=device) * 0.2,
        torch.empty(shape, device=device).uniform_(-7.0, 1.0, generator=generator),
        torch.randn(shape, generator=generator, device=device) * 0.2,
        torch.randn(shape, generator=generator, device=device) * 0.2,
        torch.randn(shape, generator=generator, device=device) * 0.2,
        torch.randn(shape, generator=generator, device=device) * 0.2,
    )
    initial = tuple(value.to(torch.bfloat16).float() for value in initial)
    upstream_gradient = torch.randn(shape, generator=generator, device=device).float()
    branches = {
        name: run_synthetic_branch(
            branch=name,
            initial=initial,
            upstream_gradient=upstream_gradient,
            config=config,
        )
        for name in ("fp32", "pytorch", "fused")
    }
    thresholds = config["numeric_thresholds"]
    comparisons: dict[str, Any] = {}
    for candidate, reference in (("pytorch", "fp32"), ("fused", "fp32"), ("fused", "pytorch")):
        key = f"{candidate}_vs_{reference}"
        comparisons[key] = {
            "output": error_metrics(
                branches[candidate]["output"], branches[reference]["output"], thresholds
            ),
            "loss": error_metrics(
                branches[candidate]["loss"], branches[reference]["loss"], thresholds
            ),
            "six_input_gradients": mapping_error_summary(
                branches[candidate]["gradients"],
                branches[reference]["gradients"],
                thresholds,
            ),
            "optimizer_step": mapping_error_summary(
                branches[candidate]["updated"],
                branches[reference]["updated"],
                thresholds,
            ),
        }
    qualification = comparisons["fused_vs_pytorch"]
    passed = (
        qualification["output"]["passed"]
        and qualification["loss"]["passed"]
        and qualification["six_input_gradients"]["all_passed"]
        and qualification["optimizer_step"]["all_passed"]
    )
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "phase": "synthetic",
        "benchmark_id": BENCHMARK_ID,
        "seed": seed,
        "shape": list(shape),
        "fp32_reference_scope": "共同BF16量化输入上的FP32递归与累加",
        "comparisons": comparisons,
        "passed": passed,
    }


class FusedK0TimeMix(pure.BF16RWKV7TimeMix):
    """只把 K0 TimeMix 内部 WKV 递归替换为融合核。"""

    def __init__(self, *, build_root: Path) -> None:
        super().__init__(112, 16, 8, 0, 1)
        self.build_root = build_root

    def forward(
        self, values: torch.Tensor, value_first: torch.Tensor | None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        batch, length, channels = values.shape
        if (length, channels, self.head_size) != (128, 112, 16):
            raise RuntimeError("融合后端只允许 K0/T128/C112/H16")
        shifted = self.time_shift(values) - values
        xr = values + shifted * self.x_r
        xw = values + shifted * self.x_w
        xk = values + shifted * self.x_k
        xv = values + shifted * self.x_v
        xa = values + shifted * self.x_a
        xg = values + shifted * self.x_g
        r = self.receptance(xr)
        k = self.key(xk)
        v = self.value(xv)
        value_first = v
        a_gate = torch.sigmoid(self.a0 + (xa @ self.a1) @ self.a2)
        g = torch.sigmoid(xg @ self.g1) @ self.g2
        with fp32_island(xw, device_type="cuda", torch_module=torch) as (xw32,):
            w_raw = self.w0 + torch.tanh(xw32 @ self.w1) @ self.w2
        with fp32_island(k, a_gate, device_type="cuda", torch_module=torch) as (
            k32,
            a32,
        ):
            kk = F.normalize(
                (k32 * self.k_k).view(batch, length, self.heads, -1),
                dim=-1,
                p=2.0,
            ).view(batch, length, channels)
            recurrent_k = k32 * (1 + (a32 - 1) * self.k_a)
        fused_inputs = tuple(
            tensor.to(torch.bfloat16).contiguous()
            for tensor in (r, w_raw, recurrent_k, v, -kk, kk * a_gate.float())
        )
        output16 = fused_backend.rwkv7_k0_fused(
            *fused_inputs, build_root=self.build_root
        )
        with fp32_island(
            output16,
            r,
            recurrent_k,
            v,
            device_type="cuda",
            torch_module=torch,
        ) as (output32, r32, k32, v32):
            output32 = self.ln_x(output32.view(batch * length, channels)).view(
                batch, length, channels
            )
            bonus = (
                (
                    r32.view(batch, length, self.heads, -1)
                    * k32.view(batch, length, self.heads, -1)
                    * self.r_k
                ).sum(dim=-1, keepdim=True)
                * v32.view(batch, length, self.heads, -1)
            ).view(batch, length, channels)
        return self.output((output32 + bonus) * g), value_first


def build_k0_model(
    base_config: Mapping[str, Any],
    *,
    backend: str,
    initial_state: Mapping[str, torch.Tensor] | None,
    build_root: Path,
    device: torch.device,
) -> pure.BF16RWKV7ProtocolAModel:
    model = pure.build_model(
        base_config, "K0", "C00", base_config["precision"]["profile_id"]
    )
    if backend == "fused":
        model.time_mix_layers[0].time_mix = FusedK0TimeMix(build_root=build_root)
    elif backend not in {"fp32", "pytorch"}:
        raise ValueError(f"未知 K0 后端：{backend}")
    if initial_state is not None:
        model.load_state_dict(initial_state, strict=True)
    actual = sum(parameter.numel() for parameter in model.parameters())
    if actual != 104274:
        raise RuntimeError(f"K0/R2 参数量变更：{actual}")
    return model.to(device)


def initial_model_state(
    base_config: Mapping[str, Any], seed: int
) -> dict[str, torch.Tensor]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    model = pure.build_model(
        base_config, "K0", "C00", base_config["precision"]["profile_id"]
    )
    return {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}


def model_state_sha256(state: Mapping[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        tensor = state[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(json.dumps(list(tensor.shape)).encode("ascii"))
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def load_base_and_source(
    config: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, np.ndarray], np.ndarray, np.ndarray]:
    base_path = resolve_project_path(config["paths"]["base_config"])
    base_config = load_json(base_path)
    if (
        base_config.get("schema_version") != pure.SCHEMA_VERSION
        or base_config["capacities"]["K0"]["hidden_size"] != 112
        or base_config["capacities"]["K0"]["head_size"] != 16
    ):
        raise RuntimeError("当前 BF16 参照配置与 K0 合同不符")
    source = legacy.load_arrays(Path(config["paths"]["cache_root"]), SOURCE_ARRAYS)
    train_rows, validation_rows, _ = legacy.source_split(source, base_config)
    return base_config, source, train_rows, validation_rows


def runtime_profile(base_config: Mapping[str, Any]) -> dict[str, Any]:
    contract = load_and_validate_contract(
        resolve_project_path(base_config["precision"]["contract_path"])
    )
    return validate_runtime_profile(
        contract,
        base_config["precision"]["profile_id"],
        "cuda",
        torch,
    )


def run_model_step(
    *,
    backend: str,
    base_config: Mapping[str, Any],
    initial_state: Mapping[str, torch.Tensor],
    values: torch.Tensor,
    valid: torch.Tensor,
    labels: torch.Tensor,
    flow_pos_weight: torch.Tensor,
    profile: Mapping[str, Any],
    build_root: Path,
    seed: int,
) -> dict[str, Any]:
    model = build_k0_model(
        base_config,
        backend=backend,
        initial_state=initial_state,
        build_root=build_root,
        device=values.device,
    )
    model.train()
    optimizer, _ = pure.make_optimizer(base_config, model)
    optimizer.zero_grad(set_to_none=True)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    context = nullcontext() if backend == "fp32" else autocast_context(
        profile, "cuda", torch
    )
    with context:
        logits = model(values, valid)
    with fp32_island(logits, labels, device_type="cuda", torch_module=torch) as (
        logits32,
        labels32,
    ):
        mask32 = valid.float()
        loss = (
            F.binary_cross_entropy_with_logits(
                logits32,
                labels32,
                pos_weight=flow_pos_weight,
                reduction="none",
            )
            * mask32
        ).sum() / int(mask32.sum().item())
    loss.backward()
    gradients = {
        name: parameter.grad.detach().cpu().float().clone()
        for name, parameter in model.named_parameters()
        if parameter.grad is not None
    }
    gradient_norm = torch.nn.utils.clip_grad_norm_(
        model.parameters(), float(base_config["training"]["gradient_clip_norm"])
    )
    optimizer.step()
    updated = {
        name: parameter.detach().cpu().float().clone()
        for name, parameter in model.named_parameters()
    }
    return {
        "logits": logits.detach().cpu().float(),
        "loss": loss.detach().cpu().reshape(1),
        "gradients": gradients,
        "updated": updated,
        "gradient_norm": float(gradient_norm),
    }


def run_lspr23_first_batch(config: Mapping[str, Any]) -> dict[str, Any]:
    fused_backend.load_k0_extension(
        build_root=Path(config["paths"]["extension_build_root"]),
        verbose=bool(config["extension"]["verbose_build"]),
    )
    base_config, source, train_rows, _ = load_base_and_source(config)
    profile = runtime_profile(base_config)
    seed = int(config["epoch_benchmark"]["seed"])
    state = initial_model_state(base_config, seed)
    rows = train_rows[: int(config["epoch_benchmark"]["microbatch_sequences"])]
    device = torch.device("cuda")
    values, valid, labels, _ = legacy.gather_sequence_batch(source, "23", rows, device)
    flow_positive_weight, _ = legacy.source_loss_weights(source, train_rows)
    flow_pos_weight = torch.tensor(flow_positive_weight, device=device, dtype=torch.float32)
    branches = {
        backend: run_model_step(
            backend=backend,
            base_config=base_config,
            initial_state=state,
            values=values,
            valid=valid,
            labels=labels,
            flow_pos_weight=flow_pos_weight,
            profile=profile,
            build_root=Path(config["paths"]["extension_build_root"]),
            seed=seed,
        )
        for backend in ("fp32", "pytorch", "fused")
    }
    thresholds = config["numeric_thresholds"]
    comparisons: dict[str, Any] = {}
    for candidate, reference in (("pytorch", "fp32"), ("fused", "fp32"), ("fused", "pytorch")):
        key = f"{candidate}_vs_{reference}"
        comparisons[key] = {
            "logits": error_metrics(
                branches[candidate]["logits"], branches[reference]["logits"], thresholds
            ),
            "loss": error_metrics(
                branches[candidate]["loss"], branches[reference]["loss"], thresholds
            ),
            "parameter_gradients": mapping_error_summary(
                branches[candidate]["gradients"],
                branches[reference]["gradients"],
                thresholds,
            ),
            "optimizer_step": mapping_error_summary(
                branches[candidate]["updated"],
                branches[reference]["updated"],
                thresholds,
            ),
        }
    qualification = comparisons["fused_vs_pytorch"]
    passed = (
        qualification["logits"]["passed"]
        and qualification["loss"]["passed"]
        and qualification["parameter_gradients"]["all_passed"]
        and qualification["optimizer_step"]["all_passed"]
    )
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "phase": "lspr23-first-batch",
        "benchmark_id": BENCHMARK_ID,
        "seed": seed,
        "row_count": int(len(rows)),
        "valid_flow_count": int(valid.sum().item()),
        "initial_state_sha256": model_state_sha256(state),
        "target_year_paths_enumerated": 0,
        "comparisons": comparisons,
        "passed": passed,
    }


class ExternalGpuMemorySampler:
    def __init__(self, interval_seconds: float) -> None:
        self.interval_seconds = interval_seconds
        self.pid = os.getpid()
        self.maximum_mib = 0.0
        self.error: str | None = None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _sample(self) -> float:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,used_memory",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        total = 0.0
        for line in result.stdout.splitlines():
            columns = [value.strip() for value in line.split(",")]
            if len(columns) == 2 and int(columns[0]) == self.pid:
                total += float(columns[1])
        return total

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.maximum_mib = max(self.maximum_mib, self._sample())
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                self.error = str(error)
                return
            self._stop.wait(self.interval_seconds)

    def __enter__(self) -> "ExternalGpuMemorySampler":
        self._thread.start()
        return self

    def __exit__(self, *_: Any) -> None:
        self._stop.set()
        self._thread.join(timeout=max(5.0, self.interval_seconds * 4))
        if self.error is not None:
            raise RuntimeError(f"nvidia-smi 外部显存采样失败：{self.error}")


def run_epoch(config: Mapping[str, Any], backend: str) -> dict[str, Any]:
    if backend == "fused":
        fused_backend.load_k0_extension(
            build_root=Path(config["paths"]["extension_build_root"]),
            verbose=bool(config["extension"]["verbose_build"]),
        )
    base_config, source, train_rows, validation_rows = load_base_and_source(config)
    profile = runtime_profile(base_config)
    seed = int(config["epoch_benchmark"]["seed"])
    state = initial_model_state(base_config, seed)
    device = torch.device("cuda")
    model = build_k0_model(
        base_config,
        backend=backend,
        initial_state=state,
        build_root=Path(config["paths"]["extension_build_root"]),
        device=device,
    )
    model.train()
    optimizer, _ = pure.make_optimizer(base_config, model)
    flow_positive_weight, sequence_positive_weight = legacy.source_loss_weights(
        source, train_rows
    )
    flow_pos_weight = torch.tensor(flow_positive_weight, device=device, dtype=torch.float32)
    effective_batch_size = int(config["epoch_benchmark"]["effective_batch_sequences"])
    microbatch_size = int(config["epoch_benchmark"]["microbatch_sequences"])
    steps = int(config["epoch_benchmark"]["steps"])
    generator = torch.Generator().manual_seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(device)
    processed_valid_flows = 0
    running_loss = 0.0
    torch.cuda.synchronize(device)
    started = time.perf_counter()
    with ExternalGpuMemorySampler(
        float(config["epoch_benchmark"]["external_memory_sample_interval_seconds"])
    ) as memory_sampler:
        for step in range(1, steps + 1):
            positions = torch.randint(
                0,
                len(train_rows),
                (effective_batch_size,),
                generator=generator,
            ).numpy()
            rows = train_rows[positions]
            total_valid_flows, _ = pure.effective_batch_denominators(
                source, rows, sequence_positive_weight
            )
            optimizer.zero_grad(set_to_none=True)
            step_loss = 0.0
            for start in range(0, effective_batch_size, microbatch_size):
                micro_rows = rows[start : start + microbatch_size]
                values, valid, labels, _ = legacy.gather_sequence_batch(
                    source, "23", micro_rows, device
                )
                with autocast_context(profile, "cuda", torch):
                    logits = model(values, valid)
                with fp32_island(
                    logits, labels, device_type="cuda", torch_module=torch
                ) as (logits32, labels32):
                    mask32 = valid.float()
                    loss = (
                        F.binary_cross_entropy_with_logits(
                            logits32,
                            labels32,
                            pos_weight=flow_pos_weight,
                            reduction="none",
                        )
                        * mask32
                    ).sum() / total_valid_flows
                loss.backward()
                step_loss += float(loss.detach())
            gradient_norm = torch.nn.utils.clip_grad_norm_(
                model.parameters(), float(base_config["training"]["gradient_clip_norm"])
            )
            if not math.isfinite(float(gradient_norm)):
                raise RuntimeError(f"{backend} 整轮基准第 {step} 步梯度非有限")
            optimizer.step()
            running_loss += step_loss
            processed_valid_flows += total_valid_flows
            if step == 1 or step % 100 == 0 or step == steps:
                elapsed = time.perf_counter() - started
                log(
                    f"{backend} step={step}/{steps} "
                    f"valid_flows={processed_valid_flows} throughput="
                    f"{processed_valid_flows / max(elapsed, 1e-9):.2f} flow/s"
                )
        torch.cuda.synchronize(device)
        elapsed_seconds = time.perf_counter() - started
    predictions, labels, _ = pure.predict_source_rows(
        model,
        source,
        validation_rows,
        device,
        int(base_config["evaluation"]["sequence_batch_size"]),
        profile,
    )
    from sklearn.metrics import average_precision_score

    validation_flow_ap = float(average_precision_score(labels, predictions))
    if not math.isfinite(validation_flow_ap):
        raise RuntimeError(f"{backend} 整轮基准选择指标非有限")
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "phase": "epoch-throughput",
        "backend": backend,
        "benchmark_id": BENCHMARK_ID,
        "seed": seed,
        "selected_epoch": 1,
        "steps": steps,
        "processed_valid_flows": processed_valid_flows,
        "elapsed_seconds": elapsed_seconds,
        "valid_flows_per_second": processed_valid_flows / elapsed_seconds,
        "mean_step_loss": running_loss / steps,
        "validation_flow_average_precision": validation_flow_ap,
        "initial_state_sha256": model_state_sha256(state),
        "cuda_memory_allocated_bytes": int(torch.cuda.memory_allocated(device)),
        "cuda_memory_reserved_bytes": int(torch.cuda.memory_reserved(device)),
        "cuda_max_memory_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
        "cuda_max_memory_reserved_bytes": int(torch.cuda.max_memory_reserved(device)),
        "external_process_peak_gpu_memory_mib": memory_sampler.maximum_mib,
        "external_measurement_source": "nvidia-smi进程级限频采样",
        "target_year_paths_enumerated": 0,
        "finite": True,
    }


def evaluate_eligibility(
    config: Mapping[str, Any],
    synthetic: Mapping[str, Any],
    first_batch: Mapping[str, Any],
    pytorch_epoch: Mapping[str, Any],
    fused_epoch: Mapping[str, Any],
) -> dict[str, Any]:
    thresholds = config["numeric_thresholds"]
    performance = config["performance_qualification"]
    same_initial_state = (
        pytorch_epoch["initial_state_sha256"] == fused_epoch["initial_state_sha256"]
    )
    selection_delta = abs(
        fused_epoch["validation_flow_average_precision"]
        - pytorch_epoch["validation_flow_average_precision"]
    )
    selection_metric_passed = selection_delta <= float(
        thresholds["selection_metric_absolute"]
    )
    selection_epoch_equal = (
        fused_epoch["selected_epoch"] == pytorch_epoch["selected_epoch"]
    )
    throughput_ratio = (
        fused_epoch["valid_flows_per_second"]
        / pytorch_epoch["valid_flows_per_second"]
    )
    memory_ratio = (
        fused_epoch["cuda_max_memory_reserved_bytes"]
        / pytorch_epoch["cuda_max_memory_reserved_bytes"]
    )
    throughput_passed = throughput_ratio >= float(
        performance["minimum_throughput_ratio"]
    )
    memory_passed = memory_ratio <= float(
        performance["maximum_peak_reserved_memory_ratio"]
    )
    eligible = all(
        (
            synthetic["passed"],
            first_batch["passed"],
            same_initial_state,
            selection_metric_passed,
            selection_epoch_equal,
            throughput_passed,
            memory_passed,
        )
    )
    return {
        "schema_version": "ch3-rwkv7-k0-fused-eligibility-v1",
        "benchmark_id": BENCHMARK_ID,
        "synthetic_equivalence_passed": synthetic["passed"],
        "lspr23_first_batch_equivalence_passed": first_batch["passed"],
        "same_initial_state": same_initial_state,
        "selection_metric_absolute_delta": selection_delta,
        "selection_metric_passed": selection_metric_passed,
        "selection_epoch_equal": selection_epoch_equal,
        "throughput_ratio_fused_over_pytorch": throughput_ratio,
        "throughput_passed": throughput_passed,
        "peak_reserved_memory_ratio_fused_over_pytorch": memory_ratio,
        "peak_reserved_memory_passed": memory_passed,
        "eligible_for_new_training_identity": eligible,
        "failure_action": None if eligible else "保留当前纯PyTorch BF16后端",
    }


def result_path(config: Mapping[str, Any], name: str) -> Path:
    return Path(config["paths"]["output_root"]) / f"{name}.json"


def write_phase_result(config: Mapping[str, Any], name: str, result: Mapping[str, Any]) -> None:
    value = {
        **result,
        "config_sha256": sha256_file(Path(config["_config_path"])),
        "backend_contract": fused_backend.backend_contract(),
    }
    atomic_json(result_path(config, name), value)


def run_all(config: dict[str, Any]) -> None:
    synthetic = run_synthetic(config)
    write_phase_result(config, "synthetic", synthetic)
    if not synthetic["passed"]:
        raise RuntimeError("合成六输入等价性门失败")
    first_batch = run_lspr23_first_batch(config)
    write_phase_result(config, "lspr23-first-batch", first_batch)
    if not first_batch["passed"]:
        raise RuntimeError("LSPR23 冻结首批等价性门失败")
    pytorch_epoch = run_epoch(config, "pytorch")
    write_phase_result(config, "epoch-pytorch", pytorch_epoch)
    fused_epoch = run_epoch(config, "fused")
    write_phase_result(config, "epoch-fused", fused_epoch)
    eligibility = evaluate_eligibility(
        config, synthetic, first_batch, pytorch_epoch, fused_epoch
    )
    write_phase_result(config, "eligibility", eligibility)
    if not eligibility["eligible_for_new_training_identity"]:
        raise RuntimeError("融合核训练身份资格门未通过")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RWKV-7 K0 CUDA 融合核等价性与速度基准")
    parser.add_argument("--config", required=True)
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument(
        "--phase",
        choices=(
            "synthetic",
            "lspr23-first-batch",
            "epoch-pytorch",
            "epoch-fused",
            "eligibility",
            "all",
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_path = Path(args.config).resolve()
    config = load_json(config_path)
    validate_config(config)
    config["_config_path"] = str(config_path)
    if args.validate_config:
        print(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "benchmark_id": BENCHMARK_ID,
                    "config_sha256": sha256_file(config_path),
                    "backend_contract": fused_backend.backend_contract(),
                    "validation": "passed",
                    "cuda_executed": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.phase is None:
        raise SystemExit("正式基准必须提供 --phase")
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    if args.phase == "all":
        run_all(config)
        return 0
    if args.phase == "synthetic":
        result = run_synthetic(config)
    elif args.phase == "lspr23-first-batch":
        result = run_lspr23_first_batch(config)
    elif args.phase in {"epoch-pytorch", "epoch-fused"}:
        result = run_epoch(config, args.phase.removeprefix("epoch-"))
    else:
        synthetic = load_json(result_path(config, "synthetic"))
        first_batch = load_json(result_path(config, "lspr23-first-batch"))
        pytorch_epoch = load_json(result_path(config, "epoch-pytorch"))
        fused_epoch = load_json(result_path(config, "epoch-fused"))
        result = evaluate_eligibility(
            config, synthetic, first_batch, pytorch_epoch, fused_epoch
        )
    write_phase_result(config, args.phase, result)
    passed = result.get("passed", result.get("eligible_for_new_training_identity", True))
    if not passed:
        raise RuntimeError(f"融合核基准阶段失败：{args.phase}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
