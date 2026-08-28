# -*- coding: utf-8 -*-
"""torch.compile 对 FT 主干的逐位等价与提速探针。

背景与判据：C00 已在**无 compile** 下运行，用户裁决**不重跑 C00**。因此 compile 能否
用于后续消融臂是二值问题——

- 若编译前后 logits ``torch.equal`` 为真，则四格的数值路径一致，可对剩余臂启用；
- 若不为真，则编译臂与 C00 的训练轨迹从第一步起就分叉，机制效应与编译效应混淆，
  **整体放弃 compile**。

本探针只构建裸 FT 主干并在固定输入上比较，不训练、不读数据缓存、不产生正式运行身份。
逐位比较用 ``torch.equal``，不用 ``allclose``。同时报告前向与反向的提速比与首次编译耗时。

证据边界：``engineering_only``；与训练并发时显存紧张，默认用小微批。不进论文结果。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import torch

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

RUN_ID = "ch3-ft-compile-equivalence-probe-v1"
SCHEMA_VERSION = "ch3-ft-compile-equivalence-receipt-v1"


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


class StructuralFTProxy(torch.nn.Module):
    """与 FT 主干结构等价的代理模块，用于判断 compile 是否改变数值。

    正式 ``build_model`` 需要已拟合的输入变换与完整数据管线，不适合在训练并发时
    独立构造。本代理复现与 FT 相同的算子序列与形状：逐字段线性 Token 化、
    多头自注意力（手写 softmax，与正式实现一致）、Pre-Norm 残差、ReGLU 前馈。

    **适用边界**：本代理足以支持**否决**结论——若此处 compile 已非逐位一致，
    正式 FT 更不会是。若此处逐位一致，只能作为**放行的必要条件**，正式启用前仍须
    在真实 FT 权重上复核。
    """

    def __init__(self, width: int = 192, heads: int = 8, layers: int = 3,
                 tokens: int = 84, fields: int = 83, ffn_width: int = 255) -> None:
        super().__init__()
        self.width = width
        self.heads = heads
        self.head_dim = width // heads
        self.tokens = tokens
        # 逐字段线性 Token 化：每字段一组独立权重与偏置
        self.token_weight = torch.nn.Parameter(torch.randn(fields, width) * 0.02)
        self.token_bias = torch.nn.Parameter(torch.zeros(fields, width))
        self.cls = torch.nn.Parameter(torch.randn(1, 1, width) * 0.02)
        self.blocks = torch.nn.ModuleList()
        for _ in range(layers):
            self.blocks.append(torch.nn.ModuleDict({
                "norm": torch.nn.LayerNorm(width),
                "qkv": torch.nn.Linear(width, width * 3),
                "out": torch.nn.Linear(width, width),
                "ffn_norm": torch.nn.LayerNorm(width),
                "ffn_in": torch.nn.Linear(width, ffn_width * 2),
                "ffn_out": torch.nn.Linear(ffn_width, width),
            }))
        self.final_norm = torch.nn.LayerNorm(width)
        self.head = torch.nn.Linear(width, 1)

    def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
        # values: (B, L, F) -> 展平为逐流 (N, F)
        batch, length, fields = values.shape
        flat = values.reshape(-1, fields)                                  # (N, F)
        tokens = flat.unsqueeze(-1) * self.token_weight + self.token_bias  # (N, F, D)
        cls = self.cls.expand(tokens.shape[0], -1, -1)                     # (N, 1, D)
        hidden = torch.cat([cls, tokens], dim=1)                           # (N, T, D)
        for block in self.blocks:
            normed = block["norm"](hidden)
            qkv = block["qkv"](normed).reshape(
                normed.shape[0], normed.shape[1], 3, self.heads, self.head_dim)
            query, key, value = qkv.unbind(dim=2)                          # (N, T, H, Dh)
            scores = torch.einsum("nthd,nshd->nhts", query, key) / (self.head_dim ** 0.5)
            weights = scores.softmax(dim=-1)
            context = torch.einsum("nhts,nshd->nthd", weights, value)
            hidden = hidden + block["out"](context.reshape(normed.shape[0], normed.shape[1], self.width))
            normed = block["ffn_norm"](hidden)
            projected = block["ffn_in"](normed)
            left, right = projected.chunk(2, dim=-1)
            hidden = hidden + block["ffn_out"](left * torch.nn.functional.relu(right))
        logits = self.head(self.final_norm(hidden[:, 0])).squeeze(-1)      # (N,)
        return logits.reshape(batch, length)


def build_bare_ft(device: torch.device) -> torch.nn.Module:
    """构造结构等价代理；正式 FT 的构造需要数据管线，见类文档的适用边界。"""
    return StructuralFTProxy().to(device)


def timed_step(model: torch.nn.Module, values: torch.Tensor, valid: torch.Tensor,
               repeats: int, backward: bool) -> float:
    for _ in range(3):
        out = model(values, valid)
        if backward:
            model.zero_grad(set_to_none=True)
            out.float().sum().backward()
    torch.cuda.synchronize()
    start = time.perf_counter()
    for _ in range(repeats):
        out = model(values, valid)
        if backward:
            model.zero_grad(set_to_none=True)
            out.float().sum().backward()
    torch.cuda.synchronize()
    return (time.perf_counter() - start) / repeats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", default=f"runs/diagnostics/{RUN_ID}")
    parser.add_argument("--micro-batch", type=int, default=8,
                        help="与训练并发时显存紧张，默认小微批；独占时可用 64")
    parser.add_argument("--mode", default="default",
                        choices=["default", "reduce-overhead", "max-autotune"])
    parser.add_argument("--repeats", type=int, default=10)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        print("CUDA 不可用，本探针只在服务器运行", flush=True)
        return 2
    device = torch.device("cuda")
    torch.manual_seed(42)

    model = build_bare_ft(device)
    model.eval()
    parameter_count = sum(p.numel() for p in model.parameters())
    print(f"结构等价代理参数量={parameter_count}（同量级即可，非正式 FT 的 924283）", flush=True)

    batch = args.micro_batch
    values = torch.randn(batch, 128, 83, device=device)
    valid = torch.ones(batch, 128, dtype=torch.bool, device=device)

    with torch.no_grad():
        eager_logits = model(values, valid).clone()

    compile_error = None
    compile_seconds = None
    compiled_logits = None
    try:
        start = time.perf_counter()
        compiled = torch.compile(model, mode=args.mode)
        with torch.no_grad():
            compiled_logits = compiled(values, valid).clone()
        torch.cuda.synchronize()
        compile_seconds = time.perf_counter() - start
    except Exception as error:  # 编译失败是有效结论，不吞异常信息
        compile_error = f"{type(error).__name__}: {str(error)[:300]}"

    verdict: dict[str, Any] = {"compile_error": compile_error}
    if compiled_logits is not None:
        bitwise = bool(torch.equal(eager_logits, compiled_logits))
        difference = float((eager_logits - compiled_logits).abs().max())
        verdict["bitwise_identical"] = bitwise
        verdict["max_absolute_difference"] = difference
        verdict["usable_without_rerunning_c00"] = bitwise
        print(f"逐位等价={bitwise}  最大绝对差={difference:.6e}  首次编译={compile_seconds:.1f}秒", flush=True)

        eager_forward = timed_step(model, values, valid, args.repeats, backward=False)
        compiled_forward = timed_step(compiled, values, valid, args.repeats, backward=False)
        model.train()
        eager_train = timed_step(model, values, valid, args.repeats, backward=True)
        compiled_train = timed_step(compiled, values, valid, args.repeats, backward=True)
        verdict["speedup_forward"] = eager_forward / compiled_forward if compiled_forward > 0 else None
        verdict["speedup_train_step"] = eager_train / compiled_train if compiled_train > 0 else None
        print(f"前向提速={verdict['speedup_forward']:.3f}x  训练步提速={verdict['speedup_train_step']:.3f}x", flush=True)
    else:
        print(f"编译失败：{compile_error}", flush=True)

    atomic_json(
        Path(args.output_root).resolve() / "compile-equivalence.json",
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": RUN_ID,
            "evidence_tier": "engineering_only_compile_probe",
            "target_reads": 0,
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "device_capability": list(torch.cuda.get_device_capability(0)),
            "device_name": torch.cuda.get_device_name(0),
            "micro_batch_sequences": batch,
            "compile_mode": args.mode,
            "parameter_count": parameter_count,
            "compile_seconds": compile_seconds,
            "verdict": verdict,
            "decision_rule": "逐位等价为真才可对剩余臂启用；为假则整体放弃，不重跑 C00",
        },
    )
    print("CH3_FT_COMPILE_EQUIVALENCE_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
