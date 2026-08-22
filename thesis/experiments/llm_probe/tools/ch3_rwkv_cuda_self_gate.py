"""CUDA-RWKV 小型容量自身资格门。

模块导入、帮助和配置检查不会初始化 CUDA 或编译扩展。只有显式执行
``--run`` 才会加载官方 CUDA 核并运行固定构造输入资格检查。
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "ch3-rwkv-cuda-self-gate-config-v1"
RESULT_SCHEMA_VERSION = "ch3-rwkv-cuda-self-gate-result-v1"
UPSTREAM_COMMIT = "952102498e9ed367ea0a59ee64106916d474d30f"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOOLS_ROOT = Path(__file__).resolve().parent
EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "gate_id",
    "display_name",
    "source",
    "shape",
    "precision",
    "environment",
    "backend",
    "fixed_input",
    "optimizer",
    "measurement",
    "paths",
    "identity_files",
    "artifacts",
}
EXPECTED_IDENTITY_FILES = {
    "configs/ch3-rwkv-cuda-self-gate-v1.json",
    "tools/ch3_rwkv_cuda_self_gate.py",
    "tools/rwkv7_k0_fused_backend.py",
    "scripts/remote_launchers/run_ch3_rwkv_cuda_self_gate_v1.sh",
    "vendor/rwkv7_k0_fused/LICENSE",
    "vendor/rwkv7_k0_fused/manifest.json",
    "vendor/rwkv7_k0_fused/upstream/rwkv7_clampw.cpp",
    "vendor/rwkv7_k0_fused/upstream/rwkv7_clampw.cu",
    "vendor/rwkv7_k0_fused/derived/rwkv7_k0_clampw.cpp",
}
INPUT_NAMES = ("r", "w", "k", "v", "a", "b")
torch: Any | None = None


def _require_torch() -> Any:
    global torch
    if torch is None:
        try:
            torch = importlib.import_module("torch")
        except ModuleNotFoundError as error:
            raise RuntimeError("执行 CUDA 资格门需要目标环境的 PyTorch") from error
    return torch


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _require_exact_keys(
    value: Mapping[str, Any], expected: set[str], location: str
) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"{location} 字段不符：缺失={missing}，多余={extra}")


def _require_mapping(value: Any, location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{location} 必须是对象")
    return value


def load_config(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"配置不存在：{resolved}")
    value = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("配置根必须是对象")
    validate_config(value)
    return value


def validate_config(config: Mapping[str, Any]) -> None:
    _require_exact_keys(config, EXPECTED_TOP_LEVEL_KEYS, "配置根")
    if config["schema_version"] != SCHEMA_VERSION:
        raise ValueError("配置模式版本不符")
    if config["gate_id"] != "ch3-rwkv-cuda-self-gate-v1":
        raise ValueError("资格门身份不符")

    source = _require_mapping(config["source"], "source")
    _require_exact_keys(source, {"repository", "commit", "license"}, "source")
    if source["commit"] != UPSTREAM_COMMIT or source["license"] != "Apache-2.0":
        raise ValueError("官方提交或许可证不符")

    shape = _require_mapping(config["shape"], "shape")
    _require_exact_keys(
        shape,
        {
            "batch",
            "sequence_length",
            "channels",
            "head_size",
            "heads",
            "low_rank",
            "chunk_length",
        },
        "shape",
    )
    expected_shape = {
        "batch": 2,
        "sequence_length": 128,
        "channels": 112,
        "head_size": 16,
        "heads": 7,
        "low_rank": 8,
        "chunk_length": 16,
    }
    if dict(shape) != expected_shape:
        raise ValueError(f"小型容量形状必须精确为 {expected_shape}")
    if int(shape["channels"]) != int(shape["head_size"]) * int(shape["heads"]):
        raise ValueError("通道数必须等于头大小乘头数")
    if int(shape["sequence_length"]) % int(shape["chunk_length"]) != 0:
        raise ValueError("序列长度必须能被分块长度整除")

    precision = _require_mapping(config["precision"], "precision")
    _require_exact_keys(
        precision,
        {
            "kernel_input",
            "kernel_output",
            "kernel_gradient",
            "kernel_state",
            "module_parameter",
        },
        "precision",
    )
    if dict(precision) != {
        "kernel_input": "bfloat16",
        "kernel_output": "bfloat16",
        "kernel_gradient": "bfloat16",
        "kernel_state": "float32",
        "module_parameter": "float32",
    }:
        raise ValueError("精度合同不符")

    environment = _require_mapping(config["environment"], "environment")
    _require_exact_keys(
        environment,
        {
            "torch_version",
            "cuda_version",
            "compute_capability",
            "cuda_arch_list",
            "required_commands",
        },
        "environment",
    )
    if environment["torch_version"] != "2.13.0+cu130":
        raise ValueError("PyTorch 版本合同不符")
    if environment["cuda_version"] != "13.0":
        raise ValueError("CUDA 版本合同不符")
    if environment["compute_capability"] != [12, 0]:
        raise ValueError("计算能力合同不符")
    if environment["cuda_arch_list"] != "12.0":
        raise ValueError("CUDA 架构列表合同不符")
    if environment["required_commands"] != ["nvcc", "ninja", "c++"]:
        raise ValueError("编译命令合同不符")

    backend = _require_mapping(config["backend"], "backend")
    _require_exact_keys(
        backend, {"module", "extension_name", "operator_namespace"}, "backend"
    )
    if dict(backend) != {
        "module": "rwkv7_k0_fused_backend",
        "extension_name": "rwkv7_k0_clampw_h16_c112_t128_v1",
        "operator_namespace": "rwkv7_k0_clampw",
    }:
        raise ValueError("独立 CUDA 后端合同不符")

    fixed_input = _require_mapping(config["fixed_input"], "fixed_input")
    _require_exact_keys(
        fixed_input,
        {
            "seed",
            "absolute_bound",
            "perturbation",
            "perturb_index",
            "prefix_length",
        },
        "fixed_input",
    )
    if int(fixed_input["seed"]) != 20260822:
        raise ValueError("固定种子不符")
    if float(fixed_input["absolute_bound"]) != 0.5:
        raise ValueError("构造输入边界不符")
    if float(fixed_input["perturbation"]) != 0.125:
        raise ValueError("微扰幅度不符")
    if fixed_input["perturb_index"] != [0, 1, 0]:
        raise ValueError("微扰位置不符")
    prefix_length = int(fixed_input["prefix_length"])
    if not 0 < prefix_length < int(shape["sequence_length"]):
        raise ValueError("有效前缀长度越界")

    optimizer = _require_mapping(config["optimizer"], "optimizer")
    _require_exact_keys(
        optimizer, {"name", "learning_rate", "weight_decay"}, "optimizer"
    )
    if dict(optimizer) != {
        "name": "AdamW",
        "learning_rate": 0.001,
        "weight_decay": 0.01,
    }:
        raise ValueError("优化器合同不符")

    measurement = _require_mapping(config["measurement"], "measurement")
    _require_exact_keys(
        measurement, {"warmup_iterations", "measured_iterations"}, "measurement"
    )
    if int(measurement["warmup_iterations"]) != 3:
        raise ValueError("预热次数不符")
    if int(measurement["measured_iterations"]) != 20:
        raise ValueError("测量次数不符")

    paths = _require_mapping(config["paths"], "paths")
    _require_exact_keys(paths, {"output_root", "build_root"}, "paths")
    output_root = Path(str(paths["output_root"]))
    build_root = Path(str(paths["build_root"]))
    if not output_root.is_absolute() or not build_root.is_absolute():
        raise ValueError("运行根和构建根必须是绝对持久路径")
    try:
        build_root.relative_to(output_root)
    except ValueError as error:
        raise ValueError("构建根必须位于运行根内") from error
    if str(output_root).startswith("/tmp/") or output_root == Path("/tmp"):
        raise ValueError("运行根不得位于 /tmp")

    identity_files = config["identity_files"]
    if not isinstance(identity_files, list) or set(identity_files) != EXPECTED_IDENTITY_FILES:
        raise ValueError("执行身份文件集合不符")
    if len(identity_files) != len(EXPECTED_IDENTITY_FILES):
        raise ValueError("执行身份文件集合存在重复项")
    for relative in identity_files:
        candidate = Path(str(relative))
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"执行身份路径必须是仓库内相对路径：{relative}")

    artifacts = _require_mapping(config["artifacts"], "artifacts")
    _require_exact_keys(
        artifacts,
        {
            "completion_receipt",
            "attempt_directory",
            "environment_receipt",
            "binary_manifest",
        },
        "artifacts",
    )
    if dict(artifacts) != {
        "completion_receipt": "completion-receipt.json",
        "attempt_directory": "attempts",
        "environment_receipt": "build-environment.json",
        "binary_manifest": "extension-binaries.json",
    }:
        raise ValueError("制品名称合同不符")


def static_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "gate_id": config["gate_id"],
        "source": config["source"],
        "shape": config["shape"],
        "precision": config["precision"],
        "environment": config["environment"],
        "backend": config["backend"],
        "fixed_input": config["fixed_input"],
        "optimizer": config["optimizer"],
        "measurement": config["measurement"],
        "reads_external_records": False,
        "creates_tracking_identity": False,
        "optimizer_update_count": 1,
        "scientific_status_before_execution": "实验待证",
    }


def _identity_file_hashes(config: Mapping[str, Any]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in config["identity_files"]:
        path = (PROJECT_ROOT / str(relative)).resolve()
        try:
            path.relative_to(PROJECT_ROOT)
        except ValueError as error:
            raise RuntimeError(f"执行身份路径逃逸项目根：{relative}") from error
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"执行身份文件缺失或为符号链接：{relative}")
        hashes[str(relative)] = _sha256_file(path)
    return hashes


def _launcher_input_identity(input_hashes: Mapping[str, str]) -> str:
    manifest = "".join(
        f"{digest}  {relative}\n" for relative, digest in input_hashes.items()
    )
    return _sha256_bytes(manifest.encode("utf-8"))


def _load_backend(config: Mapping[str, Any]) -> Any:
    if str(TOOLS_ROOT) not in sys.path:
        sys.path.insert(0, str(TOOLS_ROOT))
    module = importlib.import_module(str(config["backend"]["module"]))
    required = (
        "backend_contract",
        "validate_build_environment",
        "load_k0_extension",
        "rwkv7_k0_fused",
    )
    missing = [name for name in required if not callable(getattr(module, name, None))]
    if missing:
        raise RuntimeError(f"独立 CUDA 后端接口缺失：{missing}")
    return module


def _command_version(command: str) -> dict[str, str]:
    path = shutil.which(command)
    if path is None:
        raise RuntimeError(f"缺少编译命令：{command}")
    return _path_version(Path(path))


def _path_version(path: Path) -> dict[str, str]:
    completed = subprocess.run(
        [str(path), "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    output = (completed.stdout or completed.stderr).strip()
    return {"path": str(path), "version": output}


def _environment_receipt(
    backend: Any, config: Mapping[str, Any]
) -> dict[str, Any]:
    value = dict(backend.validate_build_environment())
    required_commands = config["environment"]["required_commands"]
    value["command_versions"] = {
        str(command): _command_version(str(command)) for command in required_commands
    }
    cxx_path = Path(str(value["cxx"])).resolve()
    value["active_cxx_version"] = _path_version(cxx_path)
    value["python_version"] = sys.version
    value["platform"] = sys.platform
    value["cuda_arch_list"] = os.environ.get("TORCH_CUDA_ARCH_LIST", "12.0")
    return value


def _tensor_contract(tensor: torch.Tensor) -> dict[str, Any]:
    return {
        "shape": list(tensor.shape),
        "dtype": str(tensor.dtype),
        "device": str(tensor.device),
        "contiguous": bool(tensor.is_contiguous()),
        "finite": bool(torch.isfinite(tensor).all().item()),
        "nonzero_count": int(torch.count_nonzero(tensor).item()),
        "requires_grad": bool(tensor.requires_grad),
    }


def _make_fixed_inputs(config: Mapping[str, Any]) -> tuple[torch.Tensor, ...]:
    shape = config["shape"]
    fixed_input = config["fixed_input"]
    tensor_shape = (
        int(shape["batch"]),
        int(shape["sequence_length"]),
        int(shape["channels"]),
    )
    generator = torch.Generator(device="cuda")
    generator.manual_seed(int(fixed_input["seed"]))
    bound = float(fixed_input["absolute_bound"])
    values = []
    for _ in INPUT_NAMES:
        value = torch.empty(tensor_shape, dtype=torch.float32, device="cuda")
        value.uniform_(-bound, bound, generator=generator)
        values.append(
            value.to(dtype=torch.bfloat16).contiguous().requires_grad_(True)
        )
    return tuple(values)


def _kernel_call(
    backend: Any,
    values: Sequence[torch.Tensor],
    build_root: Path,
) -> torch.Tensor:
    return backend.rwkv7_k0_fused(*values, build_root=build_root, verbose=False)


def _forward_backward_snapshot(
    backend: Any,
    base_values: Sequence[torch.Tensor],
    build_root: Path,
) -> dict[str, Any]:
    leaves = tuple(value.detach().clone().requires_grad_(True) for value in base_values)
    output = _kernel_call(backend, leaves, build_root)
    loss = output.float().square().mean() + output.float().mean().square()
    loss.backward()
    gradients = tuple(value.grad.detach().clone() for value in leaves)
    return {
        "output": output.detach().clone(),
        "loss": loss.detach().clone(),
        "gradients": gradients,
    }


def _determinism_and_gradient_gate(
    backend: Any,
    base_values: Sequence[torch.Tensor],
    build_root: Path,
) -> dict[str, Any]:
    first = _forward_backward_snapshot(backend, base_values, build_root)
    second = _forward_backward_snapshot(backend, base_values, build_root)
    output_equal = bool(torch.equal(first["output"], second["output"]))
    loss_equal = bool(torch.equal(first["loss"], second["loss"]))
    gradient_equal = {
        name: bool(torch.equal(left, right))
        for name, left, right in zip(
            INPUT_NAMES, first["gradients"], second["gradients"]
        )
    }
    gradient_contracts = {
        name: _tensor_contract(gradient)
        for name, gradient in zip(INPUT_NAMES, first["gradients"])
    }
    expected_shape = [2, 128, 112]
    gradient_contract_passed = all(
        value["shape"] == expected_shape
        and value["dtype"] == "torch.bfloat16"
        and value["device"].startswith("cuda")
        and value["contiguous"]
        and value["finite"]
        and value["nonzero_count"] > 0
        for value in gradient_contracts.values()
    )
    output_contract_passed = (
        list(first["output"].shape) == expected_shape
        and first["output"].dtype == torch.bfloat16
        and first["output"].is_cuda
        and first["output"].is_contiguous()
        and bool(torch.isfinite(first["output"]).all().item())
    )
    passed = (
        output_equal
        and loss_equal
        and all(gradient_equal.values())
        and output_contract_passed
        and bool(torch.isfinite(first["loss"]).all().item())
        and gradient_contract_passed
    )
    if not passed:
        raise RuntimeError("固定输入确定性、有限值或六梯度资格门失败")
    return {
        "passed": True,
        "output": _tensor_contract(first["output"]),
        "loss": {
            "dtype": str(first["loss"].dtype),
            "finite": bool(torch.isfinite(first["loss"]).item()),
            "value": float(first["loss"].item()),
        },
        "bitwise_equal": {
            "output": output_equal,
            "loss": loss_equal,
            "gradients": gradient_equal,
        },
        "gradients": gradient_contracts,
    }


def _perturbation_gate(
    backend: Any,
    base_values: Sequence[torch.Tensor],
    build_root: Path,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    with torch.no_grad():
        baseline = _kernel_call(backend, base_values, build_root)
        baseline_loss = baseline.float().square().mean()
    perturbation = float(config["fixed_input"]["perturbation"])
    index = tuple(int(value) for value in config["fixed_input"]["perturb_index"])
    results: dict[str, Any] = {}
    for position, name in enumerate(INPUT_NAMES):
        changed = [value.detach().clone() for value in base_values]
        changed[position][index] = changed[position][index] + perturbation
        changed[position] = changed[position].contiguous()
        with torch.no_grad():
            output = _kernel_call(backend, changed, build_root)
            loss = output.float().square().mean()
        output_delta = float((output.float() - baseline.float()).abs().max().item())
        loss_delta = float((loss - baseline_loss).abs().item())
        finite = bool(torch.isfinite(output).all().item() and torch.isfinite(loss).item())
        changed_result = not torch.equal(output, baseline) or not torch.equal(
            loss, baseline_loss
        )
        unchanged_others = all(
            torch.equal(changed[other], base_values[other])
            for other in range(len(INPUT_NAMES))
            if other != position
        )
        passed = finite and changed_result and unchanged_others
        if not passed:
            raise RuntimeError(f"输入 {name} 的单张量微扰资格门失败")
        results[name] = {
            "passed": True,
            "finite": finite,
            "other_inputs_unchanged": unchanged_others,
            "output_max_abs_delta": output_delta,
            "loss_abs_delta": loss_delta,
        }
    return {"passed": True, "inputs": results}


def _masked_loss(
    logits: torch.Tensor, labels: torch.Tensor, valid: torch.Tensor
) -> torch.Tensor:
    weights = valid.to(dtype=torch.float32)
    numerator = ((logits.float() - labels.float()).square() * weights).sum()
    return numerator / weights.sum().clamp_min(1.0)


def _make_model_inputs(config: Mapping[str, Any]) -> tuple[torch.Tensor, torch.Tensor]:
    shape = config["shape"]
    generator = torch.Generator(device="cuda")
    generator.manual_seed(int(config["fixed_input"]["seed"]) + 1)
    values = torch.rand(
        int(shape["batch"]),
        int(shape["sequence_length"]),
        int(shape["channels"]),
        generator=generator,
        dtype=torch.float32,
        device="cuda",
    )
    values = values.mul_(2.0).sub_(1.0)
    labels = values[:, :, 0].tanh()
    return values, labels


def _new_model(
    backend: Any, build_root: Path, config: Mapping[str, Any]
) -> Any:
    torch_module = _require_torch()
    nn_module = torch_module.nn

    class LowRankProjection(nn_module.Module):
        def __init__(self, channels: int, rank: int) -> None:
            super().__init__()
            self.down = nn_module.Linear(
                channels, rank, bias=False, dtype=torch_module.float32
            )
            self.up = nn_module.Linear(
                rank, channels, bias=True, dtype=torch_module.float32
            )

        def forward(self, values: Any) -> Any:
            return self.up(torch_module.tanh(self.down(values.float())))

    class IndependentCudaBlock(nn_module.Module):
        def __init__(self, channels: int, rank: int) -> None:
            super().__init__()
            self.norm = nn_module.LayerNorm(channels, dtype=torch_module.float32)
            self.projections = nn_module.ModuleDict(
                {name: LowRankProjection(channels, rank) for name in INPUT_NAMES}
            )

        def forward(self, values: Any) -> Any:
            normalized = self.norm(values.float())
            kernel_inputs = tuple(
                self.projections[name](normalized)
                .to(dtype=torch_module.bfloat16)
                .contiguous()
                for name in INPUT_NAMES
            )
            output = _kernel_call(backend, kernel_inputs, build_root)
            return values.float() + output.float()

    class IndependentGateModel(nn_module.Module):
        def __init__(self, channels: int, rank: int) -> None:
            super().__init__()
            self.input_projection = nn_module.Linear(
                channels, channels, bias=True, dtype=torch_module.float32
            )
            self.cuda_block = IndependentCudaBlock(channels, rank)
            self.output_head = nn_module.Linear(
                channels, 1, bias=True, dtype=torch_module.float32
            )

        def forward(self, values: Any, valid: Any) -> Any:
            gate = valid.to(dtype=torch_module.float32).unsqueeze(-1)
            projected = self.input_projection(values.float() * gate) * gate
            hidden = self.cuda_block(projected) * gate
            return self.output_head(hidden).squeeze(-1) * valid.to(
                dtype=torch_module.float32
            )

    torch.manual_seed(int(config["fixed_input"]["seed"]) + 2)
    torch.cuda.manual_seed_all(int(config["fixed_input"]["seed"]) + 2)
    model = IndependentGateModel(
        int(config["shape"]["channels"]), int(config["shape"]["low_rank"])
    ).cuda()
    for parameter in model.parameters():
        if parameter.dtype != torch.float32:
            raise RuntimeError("最小独立模型参数必须保持 FP32")
    return model


def _mask_gate(
    backend: Any, build_root: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    model = _new_model(backend, build_root, config)
    model.eval()
    values, labels = _make_model_inputs(config)
    prefix_length = int(config["fixed_input"]["prefix_length"])
    valid = torch.zeros(
        int(config["shape"]["batch"]),
        int(config["shape"]["sequence_length"]),
        dtype=torch.bool,
        device="cuda",
    )
    valid[:, :prefix_length] = True
    padded = values.detach().clone()
    padded[:, prefix_length:] = 0.0
    with torch.no_grad():
        original_logits = model(values, valid)
        padded_logits = model(padded, valid)
        zero_valid = torch.zeros_like(valid)
        zero_logits = model(values, zero_valid)
        zero_loss = _masked_loss(zero_logits, labels, zero_valid)
    prefix_equal = bool(
        torch.equal(
            original_logits[:, :prefix_length], padded_logits[:, :prefix_length]
        )
    )
    zero_output = int(torch.count_nonzero(zero_logits).item()) == 0
    zero_contribution = float(zero_loss.item()) == 0.0
    passed = prefix_equal and zero_output and zero_contribution
    if not passed:
        raise RuntimeError("外层独立模型掩码资格门失败")
    return {
        "passed": True,
        "prefix_length": prefix_length,
        "valid_prefix_bitwise_equal": prefix_equal,
        "zero_mask_output_nonzero_count": int(torch.count_nonzero(zero_logits).item()),
        "zero_mask_loss_contribution": float(zero_loss.item()),
    }


def _module_parameter_snapshot(module: Any) -> dict[str, Any]:
    return {
        name: parameter.detach().clone()
        for name, parameter in module.named_parameters()
    }


def _module_update_receipt(
    module: Any, before: Mapping[str, Any]
) -> dict[str, Any]:
    finite = True
    changed: list[str] = []
    for name, parameter in module.named_parameters():
        finite = finite and bool(torch.isfinite(parameter).all().item())
        if not torch.equal(before[name], parameter.detach()):
            changed.append(name)
    return {"finite": finite, "changed_parameters": changed, "updated": bool(changed)}


def _optimizer_update_gate(
    backend: Any, build_root: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    model = _new_model(backend, build_root, config)
    model.train()
    values, labels = _make_model_inputs(config)
    valid = torch.ones(
        int(config["shape"]["batch"]),
        int(config["shape"]["sequence_length"]),
        dtype=torch.bool,
        device="cuda",
    )
    modules = {
        "input_projection": model.input_projection,
        "cuda_block": model.cuda_block,
        "output_head": model.output_head,
    }
    before = {name: _module_parameter_snapshot(module) for name, module in modules.items()}
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(config["optimizer"]["learning_rate"]),
        weight_decay=float(config["optimizer"]["weight_decay"]),
    )
    optimizer.zero_grad(set_to_none=True)
    logits = model(values, valid)
    loss = _masked_loss(logits, labels, valid)
    if not torch.isfinite(loss).item():
        raise RuntimeError("单次优化更新损失非有限")
    loss.backward()
    gradients_finite = all(
        parameter.grad is None or bool(torch.isfinite(parameter.grad).all().item())
        for parameter in model.parameters()
    )
    if not gradients_finite:
        raise RuntimeError("单次优化更新参数梯度非有限")
    optimizer.step()
    updates = {
        name: _module_update_receipt(module, before[name])
        for name, module in modules.items()
    }
    passed = all(value["finite"] and value["updated"] for value in updates.values())
    if not passed:
        raise RuntimeError("输入投影、CUDA 块或输出头未完成有限参数更新")
    return {
        "passed": True,
        "optimizer": config["optimizer"],
        "loss": float(loss.detach().item()),
        "parameter_gradients_finite": gradients_finite,
        "modules": updates,
    }


def _throughput_receipt(
    backend: Any,
    build_root: Path,
    base_values: Sequence[torch.Tensor],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    detached = tuple(value.detach() for value in base_values)
    warmup = int(config["measurement"]["warmup_iterations"])
    measured = int(config["measurement"]["measured_iterations"])
    with torch.no_grad():
        for _ in range(warmup):
            _kernel_call(backend, detached, build_root)
        torch.cuda.synchronize()
        started = time.perf_counter()
        for _ in range(measured):
            _kernel_call(backend, detached, build_root)
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - started
    sequences = int(config["shape"]["batch"]) * measured
    tokens = sequences * int(config["shape"]["sequence_length"])
    return {
        "warmup_iterations": warmup,
        "measured_iterations": measured,
        "elapsed_seconds": elapsed,
        "sequences_per_second": sequences / elapsed,
        "tokens_per_second": tokens / elapsed,
        "scope": "自身资格门资源记录",
    }


def _binary_manifest(build_root: Path, extension_name: str) -> dict[str, Any]:
    candidates = sorted(
        path
        for path in build_root.rglob("*.so")
        if not path.is_symlink()
        and path.is_file()
        and (extension_name in path.name or extension_name in str(path.parent))
    )
    if not candidates:
        raise RuntimeError("扩展加载后未找到持久动态库")
    binaries = [
        {
            "path": str(path.resolve()),
            "size_bytes": path.stat().st_size,
            "sha256": _sha256_file(path),
        }
        for path in candidates
    ]
    return {"extension_name": extension_name, "binaries": binaries}


def _memory_receipt() -> dict[str, int]:
    return {
        "allocated_bytes": int(torch.cuda.memory_allocated()),
        "reserved_bytes": int(torch.cuda.memory_reserved()),
        "max_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "max_reserved_bytes": int(torch.cuda.max_memory_reserved()),
    }


def _next_attempt_directory(output_root: Path, name: str) -> Path:
    attempts_root = output_root / name
    attempts_root.mkdir(parents=True, exist_ok=True)
    existing = [
        int(path.name.split("-")[-1])
        for path in attempts_root.glob("attempt-*")
        if path.is_dir() and path.name.split("-")[-1].isdigit()
    ]
    attempt = attempts_root / f"attempt-{max(existing, default=0) + 1}"
    attempt.mkdir(parents=False, exist_ok=False)
    return attempt


def _current_completion_matches(
    completion_path: Path,
    input_identity: str,
    environment: Mapping[str, Any],
    build_root: Path,
) -> bool:
    if not completion_path.is_file():
        return False
    receipt = json.loads(completion_path.read_text(encoding="utf-8"))
    if not receipt.get("passed") or receipt.get("input_identity_sha256") != input_identity:
        return False
    if receipt.get("environment") != environment:
        return False
    binary_manifest = receipt.get("extension_binaries")
    if not isinstance(binary_manifest, Mapping):
        return False
    binaries = binary_manifest.get("binaries")
    if not isinstance(binaries, list) or not binaries:
        return False
    for item in binaries:
        if not isinstance(item, Mapping):
            return False
        path = Path(str(item.get("path", "")))
        try:
            path.resolve().relative_to(build_root.resolve())
        except ValueError:
            return False
        if (
            path.is_symlink()
            or not path.is_file()
            or _sha256_file(path) != item.get("sha256")
        ):
            return False
    return True


def run_gate(config: Mapping[str, Any]) -> dict[str, Any]:
    _require_torch()
    output_root = Path(str(config["paths"]["output_root"]))
    build_root = Path(str(config["paths"]["build_root"]))
    artifacts = config["artifacts"]
    output_root.mkdir(parents=True, exist_ok=True)
    build_root.mkdir(parents=True, exist_ok=True)
    input_hashes = _identity_file_hashes(config)
    input_identity = _canonical_sha256({"files": input_hashes})
    launcher_input_identity = _launcher_input_identity(input_hashes)
    backend = _load_backend(config)
    contract = backend.backend_contract()
    if contract["upstream_commit"] != UPSTREAM_COMMIT:
        raise RuntimeError("独立 CUDA 后端官方提交不符")
    if contract["extension_name"] != config["backend"]["extension_name"]:
        raise RuntimeError("扩展名称不符")
    environment = _environment_receipt(backend, config)
    environment_path = output_root / str(artifacts["environment_receipt"])
    completion_path = output_root / str(artifacts["completion_receipt"])
    if _current_completion_matches(
        completion_path, input_identity, environment, build_root
    ):
        receipt = json.loads(completion_path.read_text(encoding="utf-8"))
        return {
            "gate_id": config["gate_id"],
            "passed": True,
            "idempotent_skip": True,
            "execution_identity_sha256": receipt["execution_identity_sha256"],
            "completion_receipt": str(completion_path),
        }
    _atomic_write_json(environment_path, environment)

    attempt = _next_attempt_directory(output_root, str(artifacts["attempt_directory"]))
    started = time.time()
    try:
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.use_deterministic_algorithms(True, warn_only=False)
        torch.backends.cudnn.benchmark = False
        torch.manual_seed(int(config["fixed_input"]["seed"]))
        torch.cuda.manual_seed_all(int(config["fixed_input"]["seed"]))
        torch.cuda.reset_peak_memory_stats()

        backend.load_k0_extension(build_root=build_root, verbose=True)
        first_binaries = _binary_manifest(
            build_root, str(config["backend"]["extension_name"])
        )
        backend.load_k0_extension(build_root=build_root, verbose=True)
        second_binaries = _binary_manifest(
            build_root, str(config["backend"]["extension_name"])
        )
        if first_binaries != second_binaries:
            raise RuntimeError("同进程第二次加载改变了扩展二进制身份")
        binary_path = output_root / str(artifacts["binary_manifest"])
        _atomic_write_json(binary_path, first_binaries)

        base_values = _make_fixed_inputs(config)
        input_contracts = {
            name: _tensor_contract(value)
            for name, value in zip(INPUT_NAMES, base_values)
        }
        if not all(
            value["shape"] == [2, 128, 112]
            and value["dtype"] == "torch.bfloat16"
            and value["device"].startswith("cuda")
            and value["contiguous"]
            and value["finite"]
            and value["requires_grad"]
            for value in input_contracts.values()
        ):
            raise RuntimeError("六输入形状、精度、设备、连续性或有限性不符")

        determinism = _determinism_and_gradient_gate(
            backend, base_values, build_root
        )
        perturbation = _perturbation_gate(
            backend, base_values, build_root, config
        )
        masking = _mask_gate(backend, build_root, config)
        optimizer_update = _optimizer_update_gate(backend, build_root, config)
        throughput = _throughput_receipt(
            backend, build_root, base_values, config
        )
        memory = _memory_receipt()
        execution_identity = _canonical_sha256(
            {
                "input_identity_sha256": input_identity,
                "environment": environment,
                "extension_binaries": first_binaries,
            }
        )
        receipt = {
            "schema_version": RESULT_SCHEMA_VERSION,
            "gate_id": config["gate_id"],
            "passed": True,
            "idempotent_skip": False,
            "scientific_status": "实验待证",
            "input_identity_sha256": input_identity,
            "launcher_input_identity_sha256": launcher_input_identity,
            "execution_identity_sha256": execution_identity,
            "input_file_sha256": input_hashes,
            "backend_contract": contract,
            "environment": environment,
            "extension_binaries": first_binaries,
            "same_process_second_load_binary_identity_equal": True,
            "kernel_inputs": input_contracts,
            "determinism_and_gradients": determinism,
            "single_input_perturbations": perturbation,
            "outer_model_masking": masking,
            "single_optimizer_update": optimizer_update,
            "throughput": throughput,
            "cuda_memory": memory,
            "started_unix_seconds": started,
            "finished_unix_seconds": time.time(),
        }
        attempt_receipt = attempt / "result.json"
        _atomic_write_json(attempt_receipt, receipt)
        _atomic_write_json(completion_path, receipt)
        return receipt
    except BaseException as error:
        failure = {
            "schema_version": RESULT_SCHEMA_VERSION,
            "gate_id": config["gate_id"],
            "passed": False,
            "scientific_status": "实验待证",
            "input_identity_sha256": input_identity,
            "launcher_input_identity_sha256": launcher_input_identity,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "started_unix_seconds": started,
            "failed_unix_seconds": time.time(),
        }
        _atomic_write_json(attempt / "failure.json", failure)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="运行 CUDA-RWKV 小型容量自身资格门"
    )
    parser.add_argument("--config", required=True, type=Path, help="冻结配置路径")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--validate-config", action="store_true", help="只检查配置")
    actions.add_argument("--print-contract", action="store_true", help="输出静态合同")
    actions.add_argument("--run", action="store_true", help="执行目标 CUDA 资格门")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config)
    if args.validate_config:
        print(
            json.dumps(
                {"gate_id": config["gate_id"], "config_valid": True},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.print_contract:
        print(json.dumps(static_contract(config), ensure_ascii=False, indent=2))
        return 0
    if not args.run:
        parser.print_help()
        return 0
    result = run_gate(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
