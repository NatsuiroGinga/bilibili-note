"""独立 CUDA-RWKV 官方融合后端。

模块导入不触发 CUDA 初始化或扩展编译。只有显式调用
``load_extension``、``cuda_rwkv_fused`` 或 ``run_kernel_self_gate``
时才进入目标 GPU 门禁。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import torch


UPSTREAM_COMMIT = "952102498e9ed367ea0a59ee64106916d474d30f"
LICENSE_ID = "Apache-2.0"
TARGET_CAPABILITY = (12, 0)
VENDOR_ROOT = Path(__file__).resolve().parent.parent / "vendor" / "cuda_rwkv_official"
MANIFEST_PATH = VENDOR_ROOT / "manifest.json"
CPP_SOURCE = VENDOR_ROOT / "derived" / "cuda_rwkv_clampw.cpp"
CUDA_SOURCE = VENDOR_ROOT / "upstream" / "rwkv7_clampw.cu"
EXPECTED_SOURCE_SHA256 = {
    "LICENSE": "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
    "upstream/rwkv7_clampw.cpp": (
        "f6781adacbe0ab8638b666e0bd49098e262a861b7cc95fb1735ab54a43d82628"
    ),
    "upstream/rwkv7_clampw.cu": (
        "a879dd478457290ebe793a10fcd0c1b93db1e1afb9d51ff8f8f1245a0146bbfb"
    ),
    "derived/cuda_rwkv_clampw.cpp": (
        "db73fa2e1cbbfc45ffc53d1443246feb79a932b55479e5e097cfdcb328f230c6"
    ),
}


@dataclass(frozen=True)
class CapacityContract:
    key: str
    channels: int
    head_size: int
    heads: int
    sequence_length: int
    chunk_length: int
    extension_name: str
    operator_namespace: str


@dataclass(frozen=True)
class LoadedExtension:
    contract: CapacityContract
    operator: Any
    build_root: Path
    binary_path: Path
    identity: dict[str, Any]


_LOADED: dict[str, LoadedExtension] = {}


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_vendor_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.is_file() or MANIFEST_PATH.is_symlink():
        raise RuntimeError("CUDA-RWKV 官方供应商清单缺失或为符号链接")
    value = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("CUDA-RWKV 供应商清单顶层必须为对象")
    if value.get("upstream_commit") != UPSTREAM_COMMIT:
        raise RuntimeError("CUDA-RWKV 官方提交身份不符")
    if value.get("license") != LICENSE_ID:
        raise RuntimeError("CUDA-RWKV 官方许可证身份不符")
    return value


def validate_vendor_sources() -> dict[str, str]:
    """机械核验官方原件和中性派生注册文件。"""

    manifest = _load_vendor_manifest()
    actual: dict[str, str] = {}
    for relative, expected in EXPECTED_SOURCE_SHA256.items():
        path = VENDOR_ROOT / relative
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f"CUDA-RWKV 供应商文件缺失或为符号链接：{relative}")
        actual[relative] = sha256_file(path)
        if actual[relative] != expected:
            raise RuntimeError(f"CUDA-RWKV 供应商文件摘要不符：{relative}")
    declared = {
        item["path"]: item["sha256"]
        for item in [
            *manifest.get("upstream_files", []),
            *manifest.get("derived_files", []),
        ]
    }
    for relative in EXPECTED_SOURCE_SHA256:
        if relative == "LICENSE":
            continue
        if declared.get(relative) != EXPECTED_SOURCE_SHA256[relative]:
            raise RuntimeError(f"CUDA-RWKV 供应商清单未固定文件：{relative}")
    if manifest.get("license_sha256") != EXPECTED_SOURCE_SHA256["LICENSE"]:
        raise RuntimeError("CUDA-RWKV 供应商清单未固定许可证")
    return actual


def capacity_contract(capacity_key: str) -> CapacityContract:
    manifest = _load_vendor_manifest()
    raw = manifest.get("compile_contracts", {}).get(capacity_key)
    if not isinstance(raw, dict):
        raise ValueError(f"未知 CUDA-RWKV 容量：{capacity_key}")
    contract = CapacityContract(
        key=capacity_key,
        channels=int(raw["channels"]),
        head_size=int(raw["head_size"]),
        heads=int(raw["heads"]),
        sequence_length=int(raw["sequence_length"]),
        chunk_length=int(raw["chunk_length"]),
        extension_name=str(raw["extension_name"]),
        operator_namespace=str(raw["operator_namespace"]),
    )
    if contract.channels != contract.head_size * contract.heads:
        raise RuntimeError(f"{capacity_key} 通道数与头形状不一致")
    if contract.sequence_length % contract.chunk_length != 0:
        raise RuntimeError(f"{capacity_key} 序列长度不能被分块长度整除")
    return contract


def backend_contract() -> dict[str, Any]:
    """返回不触发 CUDA 初始化或编译的静态合同。"""

    source_sha256 = validate_vendor_sources()
    capacities = {}
    for key in ("small", "large"):
        item = capacity_contract(key)
        capacities[key] = {
            "channels": item.channels,
            "head_size": item.head_size,
            "heads": item.heads,
            "sequence_length": item.sequence_length,
            "chunk_length": item.chunk_length,
            "extension_name": item.extension_name,
            "operator_namespace": item.operator_namespace,
        }
    return {
        "schema_version": "cuda-rwkv-official-backend-contract-v1",
        "upstream_commit": UPSTREAM_COMMIT,
        "license": LICENSE_ID,
        "source_sha256": source_sha256,
        "vendor_manifest_sha256": sha256_file(MANIFEST_PATH),
        "capacities": capacities,
        "numeric_contract": {
            "input_dtype": "bfloat16",
            "output_dtype": "bfloat16",
            "gradient_dtype": "bfloat16",
            "state_dtype": "float32",
        },
        "target_compute_capability": list(TARGET_CAPABILITY),
    }


def _run_version(command: Sequence[str]) -> str:
    completed = subprocess.run(
        list(command), check=True, capture_output=True, text=True
    )
    return (completed.stdout or completed.stderr).strip()


def _gpu_uuid() -> str:
    completed = subprocess.run(
        ["nvidia-smi", "--query-gpu=uuid", "--format=csv,noheader"],
        check=True,
        capture_output=True,
        text=True,
    )
    values = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(values) != 1:
        raise RuntimeError("CUDA-RWKV 正式运行要求唯一可见 GPU UUID")
    return values[0]


def validate_build_environment(expected: Mapping[str, Any]) -> dict[str, Any]:
    """核验唯一目标环境，不提供其他设备路径。"""

    expected_torch = str(expected["torch_version"])
    expected_cuda = str(expected["torch_cuda_version"])
    expected_cuda_home = str(expected["cuda_home"])
    allowed_resolved_cuda_homes = tuple(
        str(value) for value in expected["allowed_resolved_cuda_homes"]
    )
    expected_nvcc_path = str(expected["nvcc_path"])
    expected_cuda_library_path = str(expected["cuda_library_path"])
    if torch.__version__ != expected_torch:
        raise RuntimeError(
            f"PyTorch 版本不符：实际 {torch.__version__}，冻结 {expected_torch}"
        )
    if torch.version.cuda != expected_cuda:
        raise RuntimeError(
            f"PyTorch CUDA 版本不符：实际 {torch.version.cuda}，冻结 {expected_cuda}"
        )
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA-RWKV 要求可用 CUDA")
    capability = tuple(int(value) for value in torch.cuda.get_device_capability())
    if capability != TARGET_CAPABILITY:
        raise RuntimeError(
            f"CUDA 计算能力不符：实际 {capability}，冻结 {TARGET_CAPABILITY}"
        )
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("目标 GPU 不支持 BF16")
    actual_cuda_home = os.environ.get("CUDA_HOME")
    if actual_cuda_home != expected_cuda_home:
        raise RuntimeError(
            f"CUDA_HOME 不符：实际 {actual_cuda_home}，冻结 {expected_cuda_home}"
        )
    cuda_home_path = Path(expected_cuda_home)
    if not cuda_home_path.is_dir():
        raise RuntimeError(f"冻结 CUDA_HOME 不是目录：{cuda_home_path}")
    resolved_cuda_home = str(cuda_home_path.resolve(strict=True))
    if resolved_cuda_home not in allowed_resolved_cuda_homes:
        raise RuntimeError(
            f"CUDA_HOME 物理落点不符：{resolved_cuda_home}"
        )
    expected_cuda_bin = str(cuda_home_path / "bin")
    library_entries = os.environ.get("LD_LIBRARY_PATH", "").split(os.pathsep)
    if not library_entries or library_entries[0] != expected_cuda_library_path:
        raise RuntimeError(
            "LD_LIBRARY_PATH 未以冻结 CUDA lib64 开头"
        )
    nvcc = shutil.which("nvcc")
    ninja = shutil.which("ninja")
    cxx = shutil.which(os.environ.get("CXX", "c++"))
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvcc or not ninja or not cxx or not nvidia_smi:
        raise RuntimeError(
            f"编译或 GPU 工具不完整：nvcc={nvcc}, ninja={ninja}, "
            f"cxx={cxx}, nvidia-smi={nvidia_smi}"
        )
    if nvcc != expected_nvcc_path:
        raise RuntimeError(
            f"nvcc PATH 首命中不符：实际 {nvcc}，冻结 {expected_nvcc_path}"
        )
    resolved_nvcc = str(Path(nvcc).resolve(strict=True))
    expected_resolved_nvcc = str(
        (Path(resolved_cuda_home) / "bin" / "nvcc").resolve(strict=True)
    )
    if resolved_nvcc != expected_resolved_nvcc:
        raise RuntimeError(
            f"nvcc 物理路径不符：{resolved_nvcc} != {expected_resolved_nvcc}"
        )
    environment = {
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "compute_capability": list(capability),
        "device_name": torch.cuda.get_device_name(),
        "gpu_uuid": _gpu_uuid(),
        "bf16_supported": True,
        "cuda_home": actual_cuda_home,
        "resolved_cuda_home": resolved_cuda_home,
        "allowed_resolved_cuda_homes": list(allowed_resolved_cuda_homes),
        "cuda_bin_path": expected_cuda_bin,
        "cuda_library_path": expected_cuda_library_path,
        "nvcc_path": nvcc,
        "resolved_nvcc_path": resolved_nvcc,
        "nvcc_version": _run_version([nvcc, "--version"]),
        "ninja_path": ninja,
        "ninja_version": _run_version([ninja, "--version"]),
        "cxx_path": cxx,
        "cxx_version": _run_version([cxx, "--version"]),
    }
    expected_device = expected.get("device_name")
    if expected_device is not None and environment["device_name"] != expected_device:
        raise RuntimeError("CUDA-RWKV GPU 名称与冻结环境不符")
    return environment


def _validate_build_root(build_root: Path, capacity_key: str) -> Path:
    resolved = build_root.expanduser().resolve()
    if resolved == Path("/tmp") or Path("/tmp") in resolved.parents:
        raise RuntimeError("CUDA-RWKV 扩展构建根不得位于 /tmp")
    if resolved.name != capacity_key:
        raise RuntimeError(f"{capacity_key} 扩展必须使用同名独立构建根")
    resolved.mkdir(parents=True, exist_ok=True)
    probe = resolved / ".cuda-rwkv-write-probe"
    probe.write_text("ok\n", encoding="utf-8")
    probe.unlink()
    return resolved


def _extension_binary(build_root: Path, extension_name: str) -> Path:
    candidates = sorted(
        path
        for path in build_root.iterdir()
        if path.is_file()
        and not path.is_symlink()
        and path.name.startswith(extension_name)
        and path.suffix in {".so", ".dylib", ".dll"}
    )
    if len(candidates) != 1:
        raise RuntimeError(
            f"CUDA-RWKV 扩展二进制数量必须为 1，实际 {len(candidates)}"
        )
    return candidates[0]


def load_extension(
    capacity_key: str,
    *,
    build_root: Path,
    expected_environment: Mapping[str, Any],
    verbose: bool = False,
) -> LoadedExtension:
    """编译并加载指定容量的独立 CUDA 扩展。"""

    contract = capacity_contract(capacity_key)
    resolved_build_root = _validate_build_root(build_root, capacity_key)
    loaded = _LOADED.get(capacity_key)
    if loaded is not None:
        if loaded.build_root != resolved_build_root:
            raise RuntimeError(f"{capacity_key} 容量不得在同进程更换构建根")
        return loaded
    source_sha256 = validate_vendor_sources()
    environment = validate_build_environment(expected_environment)
    flags = [
        "-res-usage",
        f"-D_N_={contract.head_size}",
        f"-D_CHUNK_LEN_={contract.chunk_length}",
        "--use_fast_math",
        "-O3",
        "-Xptxas",
        "-O3",
        "--extra-device-vectorization",
    ]
    cxx_flags = [
        "-O3",
        f"-DCUDA_RWKV_NAMESPACE={contract.operator_namespace}",
    ]
    previous_arch_list = os.environ.get("TORCH_CUDA_ARCH_LIST")
    os.environ["TORCH_CUDA_ARCH_LIST"] = "12.0"
    try:
        from torch.utils.cpp_extension import load

        load(
            name=contract.extension_name,
            sources=[str(CUDA_SOURCE), str(CPP_SOURCE)],
            extra_cflags=cxx_flags,
            extra_cuda_cflags=flags,
            build_directory=str(resolved_build_root),
            is_python_module=False,
            verbose=verbose,
        )
    finally:
        if previous_arch_list is None:
            os.environ.pop("TORCH_CUDA_ARCH_LIST", None)
        else:
            os.environ["TORCH_CUDA_ARCH_LIST"] = previous_arch_list
    operator = getattr(torch.ops, contract.operator_namespace)
    if not hasattr(operator, "forward") or not hasattr(operator, "backward"):
        raise RuntimeError(f"{capacity_key} 扩展未注册预期前反向算子")
    binary_path = _extension_binary(resolved_build_root, contract.extension_name)
    identity = {
        "schema_version": "cuda-rwkv-execution-identity-v1",
        "capacity": capacity_key,
        "upstream_commit": UPSTREAM_COMMIT,
        "license": LICENSE_ID,
        "source_sha256": source_sha256,
        "backend_sha256": sha256_file(Path(__file__)),
        "compile_macros": {
            "_N_": contract.head_size,
            "_CHUNK_LEN_": contract.chunk_length,
            "CUDA_RWKV_NAMESPACE": contract.operator_namespace,
        },
        "cxx_flags": cxx_flags,
        "cuda_flags": flags,
        "extension_name": contract.extension_name,
        "operator_namespace": contract.operator_namespace,
        "build_root": str(resolved_build_root),
        "extension_binary": str(binary_path),
        "extension_binary_sha256": sha256_file(binary_path),
        "environment": environment,
    }
    identity["cuda_execution_identity_sha256"] = _canonical_sha256(identity)
    loaded = LoadedExtension(
        contract=contract,
        operator=operator,
        build_root=resolved_build_root,
        binary_path=binary_path,
        identity=identity,
    )
    _LOADED[capacity_key] = loaded
    return loaded


def _validate_inputs(
    inputs: Sequence[torch.Tensor], contract: CapacityContract
) -> None:
    if len(inputs) != 6:
        raise RuntimeError("CUDA-RWKV 融合核必须接收六个输入")
    expected_shape: torch.Size | None = None
    expected_device: torch.device | None = None
    expected_requires_grad: bool | None = None
    for index, tensor in enumerate(inputs):
        if not isinstance(tensor, torch.Tensor):
            raise TypeError(f"第 {index + 1} 个 CUDA-RWKV 输入不是张量")
        if tensor.ndim != 3 or tensor.shape[1:] != (
            contract.sequence_length,
            contract.channels,
        ):
            raise RuntimeError(
                f"第 {index + 1} 个输入形状必须为 "
                f"[B,{contract.sequence_length},{contract.channels}]"
            )
        if tensor.shape[0] <= 0 or tensor.dtype != torch.bfloat16:
            raise RuntimeError("CUDA-RWKV 输入批量必须为正且精度必须为 BF16")
        if not tensor.is_cuda or not tensor.is_contiguous():
            raise RuntimeError("CUDA-RWKV 六输入必须位于 CUDA 且连续")
        if expected_shape is None:
            expected_shape = tensor.shape
            expected_device = tensor.device
            expected_requires_grad = tensor.requires_grad
        elif (
            tensor.shape != expected_shape
            or tensor.device != expected_device
            or tensor.requires_grad != expected_requires_grad
        ):
            raise RuntimeError("CUDA-RWKV 六输入必须同形、同设备且梯度状态一致")


class _CudaRwkvFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx: Any, *args: Any) -> torch.Tensor:
        *tensor_args, capacity_key = args
        loaded = _LOADED.get(str(capacity_key))
        if loaded is None:
            raise RuntimeError("CUDA-RWKV 扩展必须在自定义前向前加载")
        inputs = tuple(tensor_args)
        _validate_inputs(inputs, loaded.contract)
        batch = inputs[0].shape[0]
        shaped = tuple(
            tensor.view(
                batch,
                loaded.contract.sequence_length,
                loaded.contract.heads,
                loaded.contract.head_size,
            )
            for tensor in inputs
        )
        output = torch.empty_like(shaped[3])
        state = torch.empty(
            batch,
            loaded.contract.heads,
            loaded.contract.sequence_length // loaded.contract.chunk_length,
            loaded.contract.head_size,
            loaded.contract.head_size,
            dtype=torch.float32,
            device=inputs[0].device,
        )
        state_a = torch.empty(
            batch,
            loaded.contract.sequence_length,
            loaded.contract.heads,
            loaded.contract.head_size,
            dtype=torch.float32,
            device=inputs[0].device,
        )
        loaded.operator.forward(*shaped, output, state, state_a)
        ctx.capacity_key = str(capacity_key)
        ctx.save_for_backward(*shaped, state, state_a)
        return output.view(
            batch, loaded.contract.sequence_length, loaded.contract.channels
        )

    @staticmethod
    def backward(ctx: Any, grad_output: torch.Tensor) -> tuple[Any, ...]:
        loaded = _LOADED[ctx.capacity_key]
        grad_output = grad_output.to(dtype=torch.bfloat16).contiguous()
        r, w, k, v, a, b, state, state_a = ctx.saved_tensors
        shaped_grad = grad_output.view(
            grad_output.shape[0],
            loaded.contract.sequence_length,
            loaded.contract.heads,
            loaded.contract.head_size,
        )
        gradients = tuple(torch.empty_like(value) for value in (r, w, k, v, a, b))
        loaded.operator.backward(
            r,
            w,
            k,
            v,
            a,
            b,
            shaped_grad,
            state,
            state_a,
            *gradients,
        )
        flattened = tuple(
            gradient.view(
                gradient.shape[0],
                loaded.contract.sequence_length,
                loaded.contract.channels,
            )
            for gradient in gradients
        )
        return (*flattened, None)


def cuda_rwkv_fused(
    r: torch.Tensor,
    w: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    a: torch.Tensor,
    b: torch.Tensor,
    *,
    capacity_key: str,
    build_root: Path,
    expected_environment: Mapping[str, Any],
    verbose: bool = False,
) -> torch.Tensor:
    """执行指定容量的官方 CUDA 前反向路径。"""

    load_extension(
        capacity_key,
        build_root=build_root,
        expected_environment=expected_environment,
        verbose=verbose,
    )
    return _CudaRwkvFunction.apply(r, w, k, v, a, b, capacity_key)


def _gradient_summary(tensor: torch.Tensor) -> dict[str, Any]:
    gradient = tensor.grad
    if gradient is None:
        raise RuntimeError("CUDA-RWKV 自身门缺少返回梯度")
    finite = bool(torch.isfinite(gradient).all().item())
    nonzero = int(torch.count_nonzero(gradient).item())
    if not finite or nonzero == 0:
        raise RuntimeError("CUDA-RWKV 自身门梯度非有限或全零")
    return {
        "dtype": str(gradient.dtype),
        "shape": list(gradient.shape),
        "finite": finite,
        "nonzero": nonzero,
        "maximum_absolute": float(gradient.float().abs().max().item()),
    }


def run_kernel_self_gate(
    capacity_key: str,
    *,
    build_root: Path,
    expected_environment: Mapping[str, Any],
    reference_input_commit: str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """运行只裁决 CUDA-RWKV 核实现的确定性稳定门。"""

    loaded = load_extension(
        capacity_key,
        build_root=build_root,
        expected_environment=expected_environment,
        verbose=verbose,
    )
    contract = loaded.contract
    device = torch.device("cuda")
    element_count = contract.sequence_length * contract.channels
    base = torch.linspace(
        -0.25,
        0.25,
        steps=element_count,
        device=device,
        dtype=torch.float32,
    ).reshape(1, contract.sequence_length, contract.channels)

    def make_inputs() -> tuple[torch.Tensor, ...]:
        return tuple(
            (base * float(index + 1) / 6.0)
            .to(torch.bfloat16)
            .contiguous()
            .detach()
            .requires_grad_(True)
            for index in range(6)
        )

    repeat_outputs: list[torch.Tensor] = []
    repeat_gradients: list[tuple[torch.Tensor, ...]] = []
    gradient_receipt: list[dict[str, Any]] = []
    for _ in range(2):
        inputs = make_inputs()
        output = cuda_rwkv_fused(
            *inputs,
            capacity_key=capacity_key,
            build_root=build_root,
            expected_environment=expected_environment,
        )
        loss = output.float().square().mean()
        loss.backward()
        if not torch.isfinite(output).all() or not torch.isfinite(loss):
            raise RuntimeError("CUDA-RWKV 自身门前向或损失非有限")
        repeat_outputs.append(output.detach().clone())
        repeat_gradients.append(tuple(value.grad.detach().clone() for value in inputs))
        if not gradient_receipt:
            gradient_receipt = [_gradient_summary(value) for value in inputs]
    if not torch.equal(repeat_outputs[0], repeat_outputs[1]):
        raise RuntimeError("CUDA-RWKV 自身门重复前向不逐位一致")
    if any(
        not torch.equal(left, right)
        for left, right in zip(repeat_gradients[0], repeat_gradients[1], strict=True)
    ):
        raise RuntimeError("CUDA-RWKV 自身门重复六梯度不逐位一致")

    perturbations = []
    baseline_inputs = make_inputs()
    baseline_output = cuda_rwkv_fused(
        *baseline_inputs,
        capacity_key=capacity_key,
        build_root=build_root,
        expected_environment=expected_environment,
    ).detach()
    perturbation_time_index = contract.sequence_length // 2
    perturbation_channel_index = 0
    for input_index in range(6):
        changed = [value.detach().clone() for value in baseline_inputs]
        changed[input_index][
            0, perturbation_time_index, perturbation_channel_index
        ] += torch.tensor(
            0.03125, device=device, dtype=torch.bfloat16
        )
        changed_output = cuda_rwkv_fused(
            *changed,
            capacity_key=capacity_key,
            build_root=build_root,
            expected_environment=expected_environment,
        ).detach()
        maximum_difference = float(
            (changed_output.float() - baseline_output.float()).abs().max().item()
        )
        if not torch.isfinite(changed_output).all():
            raise RuntimeError(f"CUDA-RWKV 第 {input_index + 1} 个输入微扰产生非有限输出")
        perturbations.append(
            {
                "input_index": input_index,
                "time_index": perturbation_time_index,
                "channel_index": perturbation_channel_index,
                "maximum_absolute_difference": maximum_difference,
                "observable_after_bf16_quantization": maximum_difference > 0.0,
            }
        )

    zero_inputs = tuple(
        torch.zeros_like(value, requires_grad=False) for value in baseline_inputs
    )
    zero_output = cuda_rwkv_fused(
        *zero_inputs,
        capacity_key=capacity_key,
        build_root=build_root,
        expected_environment=expected_environment,
    )
    if int(torch.count_nonzero(zero_output).item()) != 0:
        raise RuntimeError("CUDA-RWKV 全零块输出不是严格零")

    prefix = contract.sequence_length // 2
    suffix_changed = [value.detach().clone() for value in baseline_inputs]
    for value in suffix_changed:
        value[:, prefix:] = torch.flip(value[:, prefix:], dims=(1,))
    suffix_output = cuda_rwkv_fused(
        *suffix_changed,
        capacity_key=capacity_key,
        build_root=build_root,
        expected_environment=expected_environment,
    )
    if not torch.equal(baseline_output[:, :prefix], suffix_output[:, :prefix]):
        raise RuntimeError("CUDA-RWKV 未来后缀改变了已有前缀输出")
    reset_output = cuda_rwkv_fused(
        *baseline_inputs,
        capacity_key=capacity_key,
        build_root=build_root,
        expected_environment=expected_environment,
    )
    if not torch.equal(baseline_output, reset_output):
        raise RuntimeError("CUDA-RWKV 独立块之间存在状态污染")
    second_load = load_extension(
        capacity_key,
        build_root=build_root,
        expected_environment=expected_environment,
    )
    if second_load.identity["cuda_execution_identity_sha256"] != loaded.identity[
        "cuda_execution_identity_sha256"
    ]:
        raise RuntimeError("CUDA-RWKV 同进程二次加载身份漂移")
    return {
        "schema_version": "cuda-rwkv-kernel-self-gate-v1",
        "capacity": capacity_key,
        "status": "implementation_stable",
        "effect_evidence": False,
        "reference_input_commit": reference_input_commit,
        "cuda_execution_identity_sha256": loaded.identity[
            "cuda_execution_identity_sha256"
        ],
        "output_shape": list(baseline_output.shape),
        "output_dtype": str(baseline_output.dtype),
        "six_gradient_receipt": gradient_receipt,
        "single_input_perturbations": perturbations,
        "zero_block_nonzero_output": 0,
        "future_suffix_prefix_difference": 0.0,
        "cross_block_reset_difference": 0.0,
        "same_process_second_load_identity_match": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="核验独立 CUDA-RWKV 官方融合后端合同"
    )
    parser.add_argument("--contract", action="store_true", help="输出静态合同")
    parser.add_argument("--capacity", choices=("small", "large"), default="small")
    parser.add_argument("--environment-json", type=Path, help="目标环境冻结 JSON")
    parser.add_argument("--build-root", type=Path, help="容量专用持久构建根")
    parser.add_argument("--load-extension", action="store_true", help="编译并加载扩展")
    parser.add_argument("--self-gate", action="store_true", help="运行核实现自身门")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not (args.contract or args.load_extension or args.self_gate):
        parser.print_help()
        return 0
    result: dict[str, Any] = {"contract": backend_contract()}
    if args.load_extension or args.self_gate:
        if args.environment_json is None or args.build_root is None:
            parser.error("--load-extension/--self-gate 需要 --environment-json 和 --build-root")
        expected_environment = json.loads(
            args.environment_json.read_text(encoding="utf-8")
        )
        if args.self_gate:
            result["self_gate"] = run_kernel_self_gate(
                args.capacity,
                build_root=args.build_root,
                expected_environment=expected_environment,
                verbose=args.verbose,
            )
        else:
            loaded = load_extension(
                args.capacity,
                build_root=args.build_root,
                expected_environment=expected_environment,
                verbose=args.verbose,
            )
            result["execution_identity"] = loaded.identity
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
