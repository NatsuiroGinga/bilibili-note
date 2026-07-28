"""验证物理损失能否通过真实 Qwen 隐藏表示更新 LoRA 参数。"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import torch

from flow_probe.physics import multiscale_queue_balance_residual
from flow_probe.tracking import (
    REQUIRED_SWANLAB_PROJECT,
    REQUIRED_SWANLAB_WORKSPACE,
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)


class GradientProbeError(ValueError):
    """真实基座梯度探针的输入或模型状态不合法。"""


def select_last_token_hidden(
    hidden_states: torch.Tensor,
    attention_mask: torch.Tensor,
) -> torch.Tensor:
    """按每条序列的最后一个有效令牌提取共享隐藏表示。"""
    if hidden_states.ndim != 3:
        raise GradientProbeError("隐藏状态必须采用[批量, 序列, 维度]三维形状")
    if attention_mask.ndim != 2 or attention_mask.shape != hidden_states.shape[:2]:
        raise GradientProbeError("注意力掩码形状必须与隐藏状态前两维一致")
    valid = attention_mask.to(dtype=torch.bool)
    if torch.any(valid.sum(dim=1) == 0):
        raise GradientProbeError("每条序列至少需要一个有效令牌")
    positions = torch.arange(hidden_states.shape[1], device=hidden_states.device)
    last_positions = positions.expand_as(valid).masked_fill(~valid, -1).max(dim=1).values
    batch_indices = torch.arange(hidden_states.shape[0], device=hidden_states.device)
    return hidden_states[batch_indices, last_positions]


def _prefix_prompts() -> list[str]:
    windows = (
        "窗口1：到达20字节，离开10字节，丢弃0字节，本地消费0字节。",
        "窗口2：到达30字节，离开25字节，丢弃0字节，本地消费0字节。",
        "窗口3：到达80字节，离开40字节，丢弃15字节，本地消费0字节。",
        "窗口4：到达10字节，离开25字节，丢弃0字节，本地消费0字节。",
    )
    prefix = "链路容量为每秒100字节，每个窗口为1秒。"
    prompts = [prefix + "当前位于初始时刻。"]
    for end in range(1, len(windows) + 1):
        prompts.append(prefix + "".join(windows[:end]))
    return prompts


def _gradient_norm(parameters: list[torch.nn.Parameter]) -> float:
    gradients = [
        parameter.grad.detach().float().reshape(-1)
        for parameter in parameters
        if parameter.grad is not None
    ]
    if not gradients:
        return 0.0
    return float(torch.linalg.vector_norm(torch.cat(gradients)).item())


def run_gradient_probe(
    model_path: Path,
    adapter_path: Path,
    seed: int,
) -> dict[str, object]:
    """加载量化 Qwen 与已训练 LoRA，执行一次物理损失反向传播。"""
    from peft import PeftModel, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    if not torch.cuda.is_available():
        raise RuntimeError("未检测到 CUDA，拒绝运行真实 Qwen 梯度探针")
    model_path = Path(model_path)
    adapter_path = Path(adapter_path)
    if not model_path.is_dir() or not adapter_path.is_dir():
        raise GradientProbeError("基座模型目录和 LoRA 适配器目录必须存在")
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.cuda.reset_peak_memory_stats()
    start = time.perf_counter()

    tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    base_model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=quantization,
        dtype=torch.bfloat16,
        device_map="auto",
    )
    base_model = prepare_model_for_kbit_training(
        base_model,
        use_gradient_checkpointing=False,
    )
    model = PeftModel.from_pretrained(base_model, adapter_path, is_trainable=True)
    model.config.use_cache = False
    model.train()

    prompts = _prefix_prompts()
    encoded = tokenizer(
        prompts,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )
    device = next(model.parameters()).device
    encoded = {name: value.to(device) for name, value in encoded.items()}
    outputs = model(**encoded, output_hidden_states=True, return_dict=True)
    shared_hidden = select_last_token_hidden(outputs.hidden_states[-1], encoded["attention_mask"])
    state_head = torch.nn.Sequential(
        torch.nn.Linear(model.config.hidden_size, 1),
        torch.nn.Softplus(),
    ).to(device=device, dtype=shared_hidden.dtype)
    predicted_queue = state_head(shared_hidden).transpose(0, 1)

    arrivals = torch.tensor([[20.0, 30.0, 80.0, 10.0]], device=device)
    departures = torch.tensor([[10.0, 25.0, 40.0, 25.0]], device=device)
    drops = torch.tensor([[0.0, 0.0, 15.0, 0.0]], device=device)
    consumed = torch.zeros_like(arrivals)
    capacity = torch.tensor([100.0], device=device)
    residuals = multiscale_queue_balance_residual(
        predicted_queue=predicted_queue,
        arrivals=arrivals,
        departures=departures,
        drops=drops,
        consumed=consumed,
        capacity=capacity,
        delta_seconds=1.0,
        horizons=(1, 2, 4),
    )
    physics_loss = sum(value.square().mean() for value in residuals.values())
    input_constant_loss = (arrivals - departures - drops - consumed).square().mean()
    model.zero_grad(set_to_none=True)
    state_head.zero_grad(set_to_none=True)
    physics_loss.backward()

    lora_parameters = [
        parameter
        for name, parameter in model.named_parameters()
        if parameter.requires_grad and "lora_" in name
    ]
    frozen_base_parameters = [
        parameter
        for name, parameter in model.named_parameters()
        if not parameter.requires_grad and "lora_" not in name
    ]
    lora_gradient_norm = _gradient_norm(lora_parameters)
    state_head_gradient_norm = _gradient_norm(list(state_head.parameters()))
    frozen_base_gradients = sum(parameter.grad is not None for parameter in frozen_base_parameters)
    torch.cuda.synchronize()
    checks = {
        "trainable_lora_exists": sum(parameter.numel() for parameter in lora_parameters) > 0,
        "physics_reaches_lora": lora_gradient_norm > 0.0,
        "physics_reaches_state_head": state_head_gradient_norm > 0.0,
        "input_constant_has_no_gradient_path": not input_constant_loss.requires_grad,
        "base_model_remains_frozen": frozen_base_gradients == 0,
    }
    return {
        "schema_version": "flow_probe_qwen_physics_gradient_v1",
        "seed": seed,
        "model_path": str(model_path),
        "adapter_path": str(adapter_path),
        "prompt_count": len(prompts),
        "sequence_length": int(encoded["input_ids"].shape[1]),
        "horizons": [1, 2, 4],
        "physics_loss": float(physics_loss.detach().float().item()),
        "lora_gradient_norm": lora_gradient_norm,
        "state_head_gradient_norm": state_head_gradient_norm,
        "trainable_lora_parameter_count": sum(parameter.numel() for parameter in lora_parameters),
        "frozen_base_parameter_with_gradient_count": frozen_base_gradients,
        "input_constant_loss_requires_grad": input_constant_loss.requires_grad,
        "peak_gpu_memory_mib": float(torch.cuda.max_memory_allocated() / (1024**2)),
        "runtime_seconds": time.perf_counter() - start,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
    }


def run_tracked_gradient_probe(
    model_path: Path,
    adapter_path: Path,
    output_dir: Path,
    run_name: str,
    seed: int,
) -> dict[str, object]:
    """执行一次带完整日志和 SwanLab 在线指标的真实基座梯度探针。"""
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise GradientProbeError(f"运行目录已存在，不得复用：{output_dir}")
    settings = TrackingSettings.from_mapping(
        {
            "project": REQUIRED_SWANLAB_PROJECT,
            "workspace": REQUIRED_SWANLAB_WORKSPACE,
            "run_name": run_name,
            "description": "验证队列守恒损失能否更新真实 Qwen3-1.7B LoRA 参数",
            "mode": "online",
            "tags": ["llm-probe", "pinn", "qwen-lora", "gradient"],
        }
    )
    summary_path = output_dir / "gradient_summary.json"
    metrics_path = output_dir / "swanlab_metrics.json"
    config_path = output_dir / "config_snapshot.json"
    environment_path = output_dir / "environment.json"
    config = {
        "model_path": str(model_path),
        "adapter_path": str(adapter_path),
        "seed": seed,
        "quantization": "NF4",
        "compute_dtype": "BF16",
        "horizons": [1, 2, 4],
        "claim_boundary": "只验证梯度路径，不验证检测性能增益",
    }
    data_files = {
        "gradient_summary": summary_path,
        "swanlab_metrics": metrics_path,
        "config_snapshot": config_path,
        "environment": environment_path,
    }
    with (
        capture_console_log(output_dir / "console.log"),
        swanlab_run(
            settings=settings,
            phase="qwen-physics-gradient",
            config=config,
            artifact_dir=output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        summary = run_gradient_probe(model_path, adapter_path, seed)
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        environment_path.write_text(
            json.dumps(
                {
                    "python": sys.version,
                    "platform": platform.platform(),
                    "torch": torch.__version__,
                    "cuda": torch.version.cuda,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        metrics = flatten_scalar_metrics(summary, prefix="qwen_physics_gradient")
        metrics_path.write_text(
            json.dumps(
                {"step": 0, "metrics": metrics},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        swanlab.log(metrics, step=0)
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return json.loads((output_dir / "artifact_manifest.json").read_text(encoding="utf-8"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行真实 Qwen-LoRA 物理梯度探针")
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--adapter-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    manifest = run_tracked_gradient_probe(
        model_path=args.model_path,
        adapter_path=args.adapter_path,
        output_dir=args.output_dir,
        run_name=args.run_name,
        seed=args.seed,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
