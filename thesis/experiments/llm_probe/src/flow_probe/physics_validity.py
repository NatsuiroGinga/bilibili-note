"""队列守恒候选公式的数学有效性与在线跟踪入口。"""

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


def _conservative_sequence(device: torch.device, scale: float = 1.0) -> dict[str, torch.Tensor]:
    arrivals = torch.tensor([[20.0, 30.0, 80.0, 10.0]], device=device) * scale
    departures = torch.tensor([[10.0, 25.0, 40.0, 25.0]], device=device) * scale
    drops = torch.tensor([[0.0, 0.0, 15.0, 0.0]], device=device) * scale
    consumed = torch.zeros_like(arrivals)
    queues = [torch.tensor([5.0], device=device) * scale]
    for index in range(arrivals.shape[1]):
        queues.append(
            queues[-1]
            + arrivals[:, index]
            - departures[:, index]
            - drops[:, index]
            - consumed[:, index]
        )
    return {
        "predicted_queue": torch.stack(queues, dim=1),
        "arrivals": arrivals,
        "departures": departures,
        "drops": drops,
        "consumed": consumed,
        "capacity": torch.tensor([100.0], device=device) * scale,
    }


def _mean_absolute_residual(residuals: dict[int, torch.Tensor]) -> torch.Tensor:
    return torch.stack([value.abs().mean() for value in residuals.values()]).mean()


def run_validity_checks(device_name: str, seed: int) -> dict[str, object]:
    """验证候选残差的守恒解释、量纲不变性和参数梯度路径。"""
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("未检测到 CUDA，拒绝把 GPU 数学验证静默降级到 CPU")
    device = torch.device(device_name)
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
        torch.cuda.reset_peak_memory_stats(device)
        torch.cuda.synchronize(device)
    start = time.perf_counter()

    exact = _conservative_sequence(device)
    exact_residuals = multiscale_queue_balance_residual(
        **exact,
        delta_seconds=1.0,
        horizons=(1, 2, 4),
    )
    exact_values = torch.cat([value.reshape(-1) for value in exact_residuals.values()])

    corrupted = {name: value.clone() for name, value in exact.items()}
    corrupted["predicted_queue"][:, -1] += 5.0
    corrupted_residuals = multiscale_queue_balance_residual(
        **corrupted,
        delta_seconds=1.0,
        horizons=(1, 2, 4),
    )

    scaled = _conservative_sequence(device, scale=1024.0)
    scaled["predicted_queue"][:, -1] += 5.0 * 1024.0
    base_scale_residual = multiscale_queue_balance_residual(
        **corrupted,
        delta_seconds=1.0,
        horizons=(4,),
    )[4]
    scaled_residual = multiscale_queue_balance_residual(
        **scaled,
        delta_seconds=1.0,
        horizons=(4,),
    )[4]

    shared_model = torch.nn.Sequential(
        torch.nn.Linear(4, 16),
        torch.nn.Tanh(),
        torch.nn.Linear(16, 5),
        torch.nn.Softplus(),
    ).to(device)
    predicted_queue = shared_model(torch.ones((1, 4), device=device))
    model_residuals = multiscale_queue_balance_residual(
        predicted_queue=predicted_queue,
        arrivals=exact["arrivals"],
        departures=exact["departures"],
        drops=exact["drops"],
        consumed=exact["consumed"],
        capacity=exact["capacity"],
        delta_seconds=1.0,
        horizons=(1, 2, 4),
    )
    physics_loss = sum(value.square().mean() for value in model_residuals.values())
    physics_loss.backward()
    gradients = [
        parameter.grad.reshape(-1)
        for parameter in shared_model.parameters()
        if parameter.grad is not None
    ]
    gradient_norm = torch.linalg.vector_norm(torch.cat(gradients))

    if device.type == "cuda":
        torch.cuda.synchronize(device)
    runtime_seconds = time.perf_counter() - start
    exact_mean = exact_values.abs().mean()
    exact_max = exact_values.abs().max()
    corrupted_mean = _mean_absolute_residual(corrupted_residuals)
    scale_error = (base_scale_residual - scaled_residual).abs().max()
    checks = {
        "complete_conservation": bool(exact_max.item() <= 1e-7),
        "corruption_sensitivity": bool(corrupted_mean.item() > exact_mean.item() + 1e-7),
        "scale_invariance": bool(scale_error.item() <= 1e-7),
        "nonzero_parameter_gradient": bool(gradient_norm.item() > 0.0),
    }
    return {
        "schema_version": "flow_probe_physics_validity_v1",
        "seed": seed,
        "device": str(device),
        "horizons": [1, 2, 4],
        "exact_residual_mean": float(exact_mean.item()),
        "exact_residual_max": float(exact_max.item()),
        "corrupted_residual_mean": float(corrupted_mean.item()),
        "scale_invariance_abs_error": float(scale_error.item()),
        "physics_loss": float(physics_loss.item()),
        "physics_gradient_norm": float(gradient_norm.item()),
        "runtime_seconds": runtime_seconds,
        "peak_gpu_memory_mib": (
            float(torch.cuda.max_memory_allocated(device) / (1024**2))
            if device.type == "cuda"
            else 0.0
        ),
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
    }


def run_tracked_validity(
    output_dir: Path,
    run_name: str,
    device_name: str,
    seed: int,
) -> dict[str, object]:
    """执行一次不可复用目录的 SwanLab 在线数学有效性运行。"""
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise ValueError(f"运行目录已存在，不得复用：{output_dir}")
    settings = TrackingSettings.from_mapping(
        {
            "project": REQUIRED_SWANLAB_PROJECT,
            "workspace": REQUIRED_SWANLAB_WORKSPACE,
            "run_name": run_name,
            "description": "容量归一多尺度队列守恒残差的数学有效性检查",
            "mode": "online",
            "tags": ["llm-probe", "pinn", "physics", "validity"],
        }
    )
    summary_path = output_dir / "validity_summary.json"
    metrics_path = output_dir / "swanlab_metrics.json"
    config_path = output_dir / "config_snapshot.json"
    environment_path = output_dir / "environment.json"
    config = {
        "seed": seed,
        "device": device_name,
        "horizons": [1, 2, 4],
        "normalization": "capacity_byte_budget",
        "claim_boundary": "只验证数学性质，不验证检测性能增益",
    }
    data_files = {
        "validity_summary": summary_path,
        "swanlab_metrics": metrics_path,
        "config_snapshot": config_path,
        "environment": environment_path,
    }
    with (
        capture_console_log(output_dir / "console.log"),
        swanlab_run(
            settings=settings,
            phase="physics-validity",
            config=config,
            artifact_dir=output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        summary = run_validity_checks(device_name=device_name, seed=seed)
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
        metrics = flatten_scalar_metrics(summary, prefix="physics_validity")
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
    parser = argparse.ArgumentParser(description="运行 PINN 队列残差数学有效性检查")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    manifest = run_tracked_validity(
        output_dir=args.output_dir,
        run_name=args.run_name,
        device_name=args.device,
        seed=args.seed,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
