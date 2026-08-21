"""RWKV-7 K0 基础 WKV CUDA 融合后端。

模块导入不触发编译。只有显式调用 ``load_k0_extension`` 或
``rwkv7_k0_fused`` 时才核验目标环境并加载扩展。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Sequence

import torch


UPSTREAM_COMMIT = "952102498e9ed367ea0a59ee64106916d474d30f"
LICENSE_ID = "Apache-2.0"
HEAD_SIZE = 16
CHANNELS = 112
HEADS = 7
SEQUENCE_LENGTH = 128
CHUNK_LENGTH = 16
TARGET_TORCH_VERSION = "2.13.0+cu130"
TARGET_CUDA_VERSION = "13.0"
TARGET_CAPABILITY = (12, 0)
EXTENSION_NAME = "rwkv7_k0_clampw_h16_c112_t128_v1"
VENDOR_ROOT = Path(__file__).resolve().parent.parent / "vendor" / "rwkv7_k0_fused"
MANIFEST_PATH = VENDOR_ROOT / "manifest.json"
CPP_SOURCE = VENDOR_ROOT / "derived" / "rwkv7_k0_clampw.cpp"
CUDA_SOURCE = VENDOR_ROOT / "upstream" / "rwkv7_clampw.cu"
EXPECTED_SOURCE_SHA256 = {
    "LICENSE": "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
    "upstream/rwkv7_clampw.cpp": (
        "f6781adacbe0ab8638b666e0bd49098e262a861b7cc95fb1735ab54a43d82628"
    ),
    "upstream/rwkv7_clampw.cu": (
        "a879dd478457290ebe793a10fcd0c1b93db1e1afb9d51ff8f8f1245a0146bbfb"
    ),
}

_EXTENSION_LOADED = False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_vendor_sources() -> dict[str, str]:
    if not MANIFEST_PATH.is_file() or not CPP_SOURCE.is_file() or not CUDA_SOURCE.is_file():
        raise RuntimeError("融合核供应商源码或清单缺失")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if (
        manifest.get("upstream_commit") != UPSTREAM_COMMIT
        or manifest.get("license") != LICENSE_ID
    ):
        raise RuntimeError("融合核上游提交或许可证不符")
    actual: dict[str, str] = {}
    for relative, expected in EXPECTED_SOURCE_SHA256.items():
        path = VENDOR_ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"融合核供应商原件缺失：{relative}")
        actual[relative] = _sha256(path)
        if actual[relative] != expected:
            raise RuntimeError(f"融合核供应商原件摘要不符：{relative}")
    return actual


def backend_contract() -> dict[str, Any]:
    """返回不触发 CUDA 初始化或扩展编译的静态合同。"""

    source_sha256 = _validate_vendor_sources()
    return {
        "schema_version": "rwkv7-k0-fused-backend-contract-v1",
        "upstream_commit": UPSTREAM_COMMIT,
        "license": LICENSE_ID,
        "head_size": HEAD_SIZE,
        "channels": CHANNELS,
        "heads": HEADS,
        "sequence_length": SEQUENCE_LENGTH,
        "chunk_length": CHUNK_LENGTH,
        "input_dtype": "bfloat16",
        "output_dtype": "bfloat16",
        "gradient_dtype": "bfloat16",
        "state_dtype": "float32",
        "target_torch_version": TARGET_TORCH_VERSION,
        "target_cuda_version": TARGET_CUDA_VERSION,
        "target_compute_capability": list(TARGET_CAPABILITY),
        "source_sha256": source_sha256,
        "derived_cpp_sha256": _sha256(CPP_SOURCE),
        "extension_name": EXTENSION_NAME,
    }


def validate_build_environment() -> dict[str, Any]:
    """核验唯一目标环境，不提供静默回退。"""

    if torch.__version__ != TARGET_TORCH_VERSION:
        raise RuntimeError(
            f"PyTorch 版本不符：实际 {torch.__version__}，冻结 {TARGET_TORCH_VERSION}"
        )
    if torch.version.cuda != TARGET_CUDA_VERSION:
        raise RuntimeError(
            f"PyTorch CUDA 版本不符：实际 {torch.version.cuda}，冻结 {TARGET_CUDA_VERSION}"
        )
    if not torch.cuda.is_available():
        raise RuntimeError("融合核要求可用 CUDA")
    capability = tuple(int(value) for value in torch.cuda.get_device_capability())
    if capability != TARGET_CAPABILITY:
        raise RuntimeError(
            f"CUDA 计算能力不符：实际 {capability}，冻结 {TARGET_CAPABILITY}"
        )
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("目标 GPU 不支持 BF16")
    nvcc = shutil.which("nvcc")
    ninja = shutil.which("ninja")
    cxx = shutil.which(os.environ.get("CXX", "c++"))
    if not nvcc or not ninja or not cxx:
        raise RuntimeError(
            f"编译工具不完整：nvcc={nvcc}, ninja={ninja}, cxx={cxx}"
        )
    return {
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "compute_capability": list(capability),
        "device_name": torch.cuda.get_device_name(),
        "bf16_supported": True,
        "nvcc": nvcc,
        "ninja": ninja,
        "cxx": cxx,
    }


def _validate_build_root(build_root: Path) -> Path:
    resolved = build_root.expanduser().resolve()
    if str(resolved).startswith("/tmp/") or resolved == Path("/tmp"):
        raise RuntimeError("扩展编译根不得位于 /tmp")
    resolved.mkdir(parents=True, exist_ok=True)
    probe = resolved / ".rwkv7-k0-write-probe"
    probe.write_text("ok\n", encoding="utf-8")
    probe.unlink()
    return resolved


def load_k0_extension(*, build_root: Path, verbose: bool = False) -> Any:
    """编译并加载 K0 专用 CUDA 扩展。"""

    global _EXTENSION_LOADED
    contract = backend_contract()
    environment = validate_build_environment()
    resolved_build_root = _validate_build_root(build_root)
    if _EXTENSION_LOADED:
        return torch.ops.rwkv7_k0_clampw

    previous_extensions_dir = os.environ.get("TORCH_EXTENSIONS_DIR")
    previous_arch_list = os.environ.get("TORCH_CUDA_ARCH_LIST")
    os.environ["TORCH_EXTENSIONS_DIR"] = str(resolved_build_root)
    os.environ["TORCH_CUDA_ARCH_LIST"] = "12.0"
    flags = [
        "-res-usage",
        f"-D_N_={HEAD_SIZE}",
        f"-D_CHUNK_LEN_={CHUNK_LENGTH}",
        "--use_fast_math",
        "-O3",
        "-Xptxas -O3",
        "--extra-device-vectorization",
    ]
    try:
        from torch.utils.cpp_extension import load

        load(
            name=EXTENSION_NAME,
            sources=[str(CUDA_SOURCE), str(CPP_SOURCE)],
            extra_cflags=["-O3"],
            extra_cuda_cflags=flags,
            is_python_module=False,
            verbose=verbose,
        )
    finally:
        if previous_extensions_dir is None:
            os.environ.pop("TORCH_EXTENSIONS_DIR", None)
        else:
            os.environ["TORCH_EXTENSIONS_DIR"] = previous_extensions_dir
        if previous_arch_list is None:
            os.environ.pop("TORCH_CUDA_ARCH_LIST", None)
        else:
            os.environ["TORCH_CUDA_ARCH_LIST"] = previous_arch_list
    if not hasattr(torch.ops.rwkv7_k0_clampw, "forward"):
        raise RuntimeError("扩展加载后未注册 rwkv7_k0_clampw 算子")
    _EXTENSION_LOADED = True
    _ = contract, environment
    return torch.ops.rwkv7_k0_clampw


def _validate_inputs(inputs: Sequence[torch.Tensor]) -> None:
    if len(inputs) != 6:
        raise RuntimeError("融合核必须接收六个输入")
    expected_shape = None
    device = None
    requires_grad = None
    for index, tensor in enumerate(inputs):
        if not isinstance(tensor, torch.Tensor):
            raise TypeError(f"第 {index + 1} 个输入不是 PyTorch 张量")
        if tensor.ndim != 3 or tensor.shape[1:] != (SEQUENCE_LENGTH, CHANNELS):
            raise RuntimeError(
                f"第 {index + 1} 个输入形状必须为 [B,{SEQUENCE_LENGTH},{CHANNELS}]"
            )
        if tensor.shape[0] <= 0:
            raise RuntimeError("融合核批量必须为正")
        if tensor.dtype != torch.bfloat16:
            raise RuntimeError(f"第 {index + 1} 个输入必须为 BF16")
        if not tensor.is_cuda:
            raise RuntimeError(f"第 {index + 1} 个输入必须位于 CUDA")
        if not tensor.is_contiguous():
            raise RuntimeError(f"第 {index + 1} 个输入必须连续")
        if expected_shape is None:
            expected_shape = tensor.shape
            device = tensor.device
            requires_grad = tensor.requires_grad
        elif tensor.shape != expected_shape or tensor.device != device:
            raise RuntimeError("六个输入必须同形且位于同一 CUDA 设备")
        elif tensor.requires_grad != requires_grad:
            raise RuntimeError("六个输入的 requires_grad 状态必须一致")


class _RWKV7K0FusedFunction(torch.autograd.Function):
    @staticmethod
    def forward(
        ctx: Any,
        r: torch.Tensor,
        w_raw: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        a: torch.Tensor,
        b: torch.Tensor,
    ) -> torch.Tensor:
        _validate_inputs((r, w_raw, k, v, a, b))
        batch = r.shape[0]
        shaped = tuple(
            tensor.view(batch, SEQUENCE_LENGTH, HEADS, HEAD_SIZE)
            for tensor in (r, w_raw, k, v, a, b)
        )
        output = torch.empty_like(shaped[3])
        state = torch.empty(
            batch,
            HEADS,
            SEQUENCE_LENGTH // CHUNK_LENGTH,
            HEAD_SIZE,
            HEAD_SIZE,
            dtype=torch.float32,
            device=r.device,
        )
        state_a = torch.empty(
            batch,
            SEQUENCE_LENGTH,
            HEADS,
            HEAD_SIZE,
            dtype=torch.float32,
            device=r.device,
        )
        torch.ops.rwkv7_k0_clampw.forward(*shaped, output, state, state_a)
        ctx.save_for_backward(*shaped, state, state_a)
        return output.view(batch, SEQUENCE_LENGTH, CHANNELS)

    @staticmethod
    def backward(ctx: Any, grad_output: torch.Tensor) -> tuple[torch.Tensor, ...]:
        if grad_output.dtype != torch.bfloat16:
            raise RuntimeError("融合核上游梯度必须为 BF16")
        grad_output = grad_output.contiguous()
        r, w_raw, k, v, a, b, state, state_a = ctx.saved_tensors
        shaped_grad = grad_output.view(
            grad_output.shape[0], SEQUENCE_LENGTH, HEADS, HEAD_SIZE
        )
        gradients = tuple(torch.empty_like(value) for value in (r, w_raw, k, v, a, b))
        torch.ops.rwkv7_k0_clampw.backward(
            r,
            w_raw,
            k,
            v,
            a,
            b,
            shaped_grad,
            state,
            state_a,
            *gradients,
        )
        return tuple(
            gradient.view(gradient.shape[0], SEQUENCE_LENGTH, CHANNELS)
            for gradient in gradients
        )


def rwkv7_k0_fused(
    r: torch.Tensor,
    w_raw: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    a: torch.Tensor,
    b: torch.Tensor,
    *,
    build_root: Path,
    verbose: bool = False,
) -> torch.Tensor:
    """运行 K0 专用官方基础 WKV 前反向路径。"""

    if not _EXTENSION_LOADED:
        load_k0_extension(build_root=build_root, verbose=verbose)
    return _RWKV7K0FusedFunction.apply(r, w_raw, k, v, a, b)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="核验 RWKV-7 K0 CUDA 融合后端合同")
    parser.add_argument("--contract", action="store_true", help="输出静态合同")
    parser.add_argument(
        "--validate-build-environment",
        action="store_true",
        help="核验目标 PyTorch、CUDA、GPU 和编译工具",
    )
    parser.add_argument("--load-extension", action="store_true", help="编译并加载扩展")
    parser.add_argument("--build-root", type=Path, help="持久扩展编译根")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not (args.contract or args.validate_build_environment or args.load_extension):
        parser.print_help()
        return 0
    result: dict[str, Any] = {"contract": backend_contract()}
    if args.validate_build_environment or args.load_extension:
        result["environment"] = validate_build_environment()
    if args.load_extension:
        if args.build_root is None:
            parser.error("--load-extension 必须同时提供 --build-root")
        load_k0_extension(build_root=args.build_root, verbose=args.verbose)
        result["extension_loaded"] = True
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
