"""R2/K0 CUDA 融合 WKV 的独立 Protocol A BF16 正式资格入口。

本模块复用纯 PyTorch BF16 入口的数据、训练、评价与恢复框架，但以独立运行
身份替换 K0 的 WKV 递归算子。两个后端的模型、优化器和断点禁止混接。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

import torch
from torch.nn import functional as F

import ch3_rwkv7_field_aware_protocol_a_2x2_bf16 as pure
import rwkv7_k0_fused_backend as fused_backend
from neural_precision_runtime import DEFAULT_PROFILE_ID, fp32_island


SCHEMA_VERSION = "ch3-rwkv7-k0-fused-protocol-a-bf16-config-v1"
RESULT_SCHEMA_VERSION = "ch3-rwkv7-k0-fused-protocol-a-bf16-results-v1"
RUN_ID = "ch3-rwkv7-field-aware-protocol-a-2x2-fused-bf16-seed42-v1"
K0_SHAPE = (112, 16, 8, 1, "legacy_single_time_mix")
K0_PARAMETER_COUNT = 104_274
EXPECTED_BACKEND_FILES = {
    "backend_module": (
        "tools/rwkv7_k0_fused_backend.py",
        "cbbf9739e6f17237d428cdc4a25ddd43419ee5d7ef606d715cd344d5620c6a9b",
    ),
    "benchmark_tool": (
        "tools/ch3_rwkv7_k0_fused_benchmark.py",
        "f6c873363907cdb7ca4f3f8bb934b471081e34e5a24c94d72ff54a21745d0243",
    ),
    "benchmark_config": (
        "configs/ch3-rwkv7-k0-fused-benchmark-v1.json",
        "9c5f30157eac37c70ce8ddbe15c9b6f74c6cf17b137ec4f9c7ef58c4233e9c23",
    ),
    "vendor_manifest": (
        "vendor/rwkv7_k0_fused/manifest.json",
        "6a94d3ed057558457033bd78060928745e7dba020ddffe07b4d51e97a59425d6",
    ),
    "derived_cpp": (
        "vendor/rwkv7_k0_fused/derived/rwkv7_k0_clampw.cpp",
        "0fe48181d324f0b8a8e7d5839fbac28a734bdc2aec043efe090d571039f96015",
    ),
    "upstream_cuda": (
        "vendor/rwkv7_k0_fused/upstream/rwkv7_clampw.cu",
        "a879dd478457290ebe793a10fcd0c1b93db1e1afb9d51ff8f8f1245a0146bbfb",
    ),
    "license": (
        "vendor/rwkv7_k0_fused/LICENSE",
        "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
    ),
    "pure_pytorch_anchor": (
        "tools/ch3_rwkv7_field_aware_protocol_a_2x2_bf16.py",
        "4471ed1b10cefda3e668d7c9d281ac635c51d8e7ab6c87f09de26498c6cfd27e",
    ),
}
EXPECTED_BENCHMARK_FACTS = {
    "synthetic_equivalence_passed": True,
    "lspr23_first_batch_equivalence_passed": True,
    "selection_metric_absolute_delta": 0.004199787,
    "throughput_ratio_fused_over_pytorch": 8.668993,
    "peak_reserved_memory_ratio_fused_over_pytorch": 1.099476,
    "eligible_for_new_training_identity": False,
}

_ORIGINAL_VALIDATE_CONFIG = pure.validate_config
_ORIGINAL_VALIDATE_CHECKPOINT = pure.validate_precision_checkpoint
_ORIGINAL_CHECKPOINT_PAYLOAD = pure.checkpoint_payload
_ORIGINAL_BUILD_MANIFEST = pure.build_manifest
_ORIGINAL_RUN_EXPERIMENT = pure.run_experiment
_FUSED_BUILD_ROOT: Path | None = None


def _project_path(relative: str) -> Path:
    return Path(__file__).resolve().parents[1] / relative


def _static_variant_identity(config: Mapping[str, Any]) -> dict[str, Any]:
    variant = config["cuda_fused_variant"]
    return {
        "schema_version": "ch3-rwkv7-k0-fused-numeric-variant-identity-v1",
        "run_id": RUN_ID,
        "operator_backend": "rwkv7_k0_cuda_fused",
        "upstream_repository": variant["upstream_repository"],
        "upstream_commit": variant["upstream_commit"],
        "license": variant["license"],
        "derived_scope": variant["derived_scope"],
        "official_complete_rwkv_claim_allowed": False,
        "transparent_replacement_eligible": False,
        "independent_numeric_variant_authorized": True,
        "checkpoint_compatibility": "same_cuda_fused_variant_only",
        "file_sha256": {
            name: value["sha256"] for name, value in variant["files"].items()
        },
        "benchmark_receipt_sha256": variant["benchmark_receipt_sha256"],
        "benchmark_facts": dict(variant["benchmark_facts"]),
    }


def _validate_backend_identity(
    config: Mapping[str, Any], *, require_resolved: bool
) -> dict[str, Any]:
    variant = config.get("cuda_fused_variant", {})
    if (
        variant.get("upstream_repository") != "https://github.com/BlinkDL/RWKV-LM"
        or variant.get("upstream_commit") != fused_backend.UPSTREAM_COMMIT
        or variant.get("license") != fused_backend.LICENSE_ID
        or variant.get("operator_backend") != "rwkv7_k0_cuda_fused"
        or variant.get("head_size") != 16
        or variant.get("channels") != 112
        or variant.get("sequence_length") != 128
        or variant.get("input_dtype") != "bfloat16"
        or variant.get("output_dtype") != "bfloat16"
        or variant.get("gradient_dtype") != "bfloat16"
        or variant.get("state_dtype") != "float32"
    ):
        raise ValueError("CUDA 融合后端、上游、许可证、形状或精度身份不符")
    if variant.get("derived_scope") != {
        "input_adapter": "R2_field_aware_projection",
        "time_mix": "single_K0_RWKV7_TimeMix",
        "channel_mix_used": False,
        "complete_official_rwkv": False,
    }:
        raise ValueError("官方源码派生差异披露不符")
    if variant.get("disclosure") != {
        "transparent_replacement_eligible": False,
        "independent_numeric_variant_authorized": True,
        "user_authorization_is_effect_evidence": False,
        "checkpoint_compatibility": "same_cuda_fused_variant_only",
    }:
        raise ValueError("非透明数值变体或断点边界披露不符")
    if variant.get("benchmark_facts") != EXPECTED_BENCHMARK_FACTS:
        raise ValueError("CUDA 融合资格基准事实不符")

    files = variant.get("files", {})
    if set(files) != set(EXPECTED_BACKEND_FILES):
        raise ValueError("CUDA 融合身份文件集合不符")
    for name, (relative, expected_sha) in EXPECTED_BACKEND_FILES.items():
        value = files[name]
        if value != {"path": relative, "sha256": expected_sha}:
            raise ValueError(f"CUDA 融合身份登记不符：{name}")
        path = _project_path(relative)
        if not path.is_file() or pure.sha256_file(path) != expected_sha:
            raise ValueError(f"CUDA 融合身份文件缺失或摘要不符：{name}")

    contract = fused_backend.backend_contract()
    if (
        contract["upstream_commit"] != variant["upstream_commit"]
        or contract["license"] != variant["license"]
        or contract["head_size"] != variant["head_size"]
        or contract["channels"] != variant["channels"]
        or contract["sequence_length"] != variant["sequence_length"]
        or contract["state_dtype"] != variant["state_dtype"]
        or contract["derived_cpp_sha256"] != files["derived_cpp"]["sha256"]
    ):
        raise ValueError("融合后端运行时合同与冻结配置不一致")

    receipt_sha = variant.get("benchmark_receipt_sha256")
    if require_resolved:
        if not isinstance(receipt_sha, str) or len(receipt_sha) != 64:
            raise ValueError("融合资格收据摘要尚未注入")
    elif receipt_sha is not None:
        raise ValueError("模板不得预填融合资格收据摘要")
    return contract


def validate_config(config: Mapping[str, Any], require_resolved: bool) -> None:
    global _FUSED_BUILD_ROOT
    if config.get("schema_version") != SCHEMA_VERSION or config.get("run_id") != RUN_ID:
        raise ValueError("CUDA 融合 BF16 配置模式或运行身份不符")
    _FUSED_BUILD_ROOT = Path(config.get("paths", {}).get("extension_build_root", ""))
    if not _FUSED_BUILD_ROOT.is_absolute():
        raise ValueError("融合扩展构建根必须是独立持久绝对路径")
    _ORIGINAL_VALIDATE_CONFIG(config, require_resolved)
    architecture = config["architecture_selection"]
    if require_resolved:
        if architecture["selected_capacity"] != "K0":
            raise ValueError("CUDA 融合正式资格入口只允许已封印 K0")
    elif (
        architecture["selected_capacity"] is not None
        or architecture["capacity_receipt_sha256"] is not None
    ):
        raise ValueError("模板不得预填 R2/K0 结构收据")
    if list(config["capacities"]) != ["K0"]:
        raise ValueError("CUDA 融合入口不得暴露 K1/K2 容量")
    _validate_backend_identity(config, require_resolved=require_resolved)


def _verify_benchmark_receipt(config: Mapping[str, Any]) -> dict[str, Any]:
    variant = config["cuda_fused_variant"]
    path = Path(variant["benchmark_receipt_path"])
    if not path.is_file():
        raise RuntimeError("K0 融合资格收据缺失")
    if pure.sha256_file(path) != variant["benchmark_receipt_sha256"]:
        raise RuntimeError("K0 融合资格收据摘要不符")
    receipt = pure.load_json(path)
    if (
        receipt.get("schema_version") != "ch3-rwkv7-k0-fused-eligibility-v1"
        or receipt.get("benchmark_id") != "ch3-rwkv7-k0-fused-equivalence-speed-v1"
    ):
        raise RuntimeError("K0 融合资格收据模式或基准身份不符")
    for key, expected in EXPECTED_BENCHMARK_FACTS.items():
        actual = receipt.get(key)
        if isinstance(expected, float):
            if not isinstance(actual, (int, float)) or not math.isclose(
                float(actual), expected, rel_tol=0.0, abs_tol=5e-7
            ):
                raise RuntimeError(f"K0 融合资格收据数值不符：{key}")
        elif actual is not expected:
            raise RuntimeError(f"K0 融合资格收据事实不符：{key}")
    return receipt


class FusedK0TimeMix(pure.BF16RWKV7TimeMix):
    """只将固定 K0 的 WKV 递归替换为官方基础 CUDA 融合核。"""

    def __init__(
        self,
        channels: int,
        head_size: int,
        lora_size: int,
        layer_id: int,
        layer_count: int,
    ) -> None:
        if (channels, head_size, lora_size, layer_id, layer_count) != (112, 16, 8, 0, 1):
            raise RuntimeError("CUDA 融合 TimeMix 只允许 R2/K0/C112/H16/单层")
        if _FUSED_BUILD_ROOT is None:
            raise RuntimeError("融合扩展构建根尚未由冻结配置绑定")
        super().__init__(channels, head_size, lora_size, layer_id, layer_count)
        self.build_root = _FUSED_BUILD_ROOT

    def forward(
        self, values: torch.Tensor, value_first: torch.Tensor | None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        batch, length, channels = values.shape
        if (length, channels, self.head_size) != (128, 112, 16):
            raise RuntimeError("CUDA 融合后端只允许 K0/T128/C112/H16")
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
                (k32 * self.k_k).view(batch, length, self.heads, -1), dim=-1, p=2.0
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


def checkpoint_payload(**kwargs: Any) -> dict[str, Any]:
    payload = _ORIGINAL_CHECKPOINT_PAYLOAD(**kwargs)
    payload["schema_version"] = "ch3-rwkv7-k0-fused-bf16-complete-inflight-v1"
    payload["cuda_fused_numeric_variant"] = _static_variant_identity(kwargs["config"])
    payload["pure_pytorch_checkpoint_loaded"] = False
    return payload


def validate_precision_checkpoint(
    checkpoint: Mapping[str, Any], config: Mapping[str, Any], uses_lp: bool
) -> None:
    _ORIGINAL_VALIDATE_CHECKPOINT(checkpoint, config, uses_lp)
    if (
        checkpoint.get("schema_version")
        != "ch3-rwkv7-k0-fused-bf16-complete-inflight-v1"
        or checkpoint.get("cuda_fused_numeric_variant")
        != _static_variant_identity(config)
        or checkpoint.get("pure_pytorch_checkpoint_loaded") is not False
    ):
        raise RuntimeError("检查点不是同一 CUDA 融合数值变体，禁止恢复")


def build_manifest(output_root: Path) -> None:
    _ORIGINAL_BUILD_MANIFEST(output_root)
    config_path = output_root / "config.json"
    manifest_path = output_root / "manifest.json"
    if config_path.is_file() and manifest_path.is_file():
        config = pure.load_json(config_path)
        manifest = pure.load_json(manifest_path)
        manifest["cuda_fused_numeric_variant"] = _static_variant_identity(config)
        manifest.get("files", {}).pop("manifest.json", None)
        pure.atomic_json(manifest_path, manifest)


def run_experiment(
    config: Mapping[str, Any], args: Any, config_path: Path
) -> None:
    _verify_benchmark_receipt(config)
    output_root = Path(config["paths"]["output_root"])
    resumed_inflight_cells = sorted(
        path.stem for path in (output_root / "inflight").glob("*.pt")
    ) if args.resume else []
    environment = fused_backend.validate_build_environment()
    fused_backend.load_k0_extension(
        build_root=Path(config["paths"]["extension_build_root"]), verbose=False
    )
    _ORIGINAL_RUN_EXPERIMENT(config, args, config_path)
    aggregate_path = output_root / "aggregate-results.json"
    aggregate = pure.load_json(aggregate_path)
    aggregate["schema_version"] = RESULT_SCHEMA_VERSION
    aggregate["cuda_fused_numeric_variant"] = _static_variant_identity(config)
    aggregate["model"]["operator_backend"] = "rwkv7_k0_cuda_fused"
    aggregate["model"]["official_complete_rwkv_claim_allowed"] = False
    aggregate["resource"]["cuda_fused_backend"] = {
        "extension_build_root": config["paths"]["extension_build_root"],
        "environment": environment,
        "backend_contract": fused_backend.backend_contract(),
        "resume_compatibility": "same_cuda_fused_variant_only",
    }
    aggregate["resource"]["recovery"] = {
        "resume_requested": bool(args.resume),
        "resumed_inflight_cells": resumed_inflight_cells,
        "resumed_inflight_cell_count": len(resumed_inflight_cells),
        "checkpoint_interval_optimizer_steps": 20,
        "optimizer_step_boundary_only": True,
        "pure_pytorch_checkpoint_compatible": False,
    }
    pure.atomic_json(aggregate_path, aggregate)
    build_manifest(output_root)


def _install_variant() -> None:
    pure.SCHEMA_VERSION = SCHEMA_VERSION
    pure.RESULT_SCHEMA_VERSION = RESULT_SCHEMA_VERSION
    pure.RUN_ID = RUN_ID
    pure.CAPACITY_SHAPES = {"K0": K0_SHAPE}
    pure.R2_PARAMETER_COUNTS = {"K0": K0_PARAMETER_COUNT}
    pure.BF16RWKV7TimeMix = FusedK0TimeMix
    pure.validate_config = validate_config
    pure.checkpoint_payload = checkpoint_payload
    pure.validate_precision_checkpoint = validate_precision_checkpoint
    pure.build_manifest = build_manifest
    pure.run_experiment = run_experiment


def main() -> int:
    _install_variant()
    return pure.main()


_install_variant()


if __name__ == "__main__":
    raise SystemExit(main())
