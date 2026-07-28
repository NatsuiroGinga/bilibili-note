"""生成任务十七唯一一次 ns-3 域随机化配置矩阵。"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

SCHEMA_VERSION: Final = "flow_probe_ns3_domain_randomization_v1"
DEFAULT_SEED: Final = 20_260_722
SPLIT_COUNTS: Final = {
    "train": 120,
    "calibration": 30,
    "unseen_configuration": 30,
    "out_of_range": 30,
}
IN_RANGE_QUEUE_MODELS: Final = ("fifo", "codel")
TRANSPORTS: Final = ("udp", "tcp")
ARRIVAL_MODELS: Final = ("constant", "bursty")
PACKET_SIZES: Final = (256, 512, 768, 1024, 1280, 1400)


class DomainRandomizationError(ValueError):
    """域随机化配置或输出路径不满足冻结契约。"""


@dataclass(frozen=True)
class DomainConfig:
    """一个独立 ns-3 运行的环境、流量和测量配置。"""

    schema_version: str
    config_id: str
    split: str
    seed: int
    run: int
    duration_seconds: float
    window_seconds: float
    traffic_mode: str
    transport: str
    queue_model: str
    arrival_model: str
    initial_capacity_mbps: float
    shifted_capacity_mbps: float
    capacity_shift_seconds: float
    access_delay_ms: float
    bottleneck_delay_ms: float
    queue_limit_packets: int
    downstream_loss_rate: float
    sender_count: int
    benign_rate_mbps: float
    attack_rate_mbps: float
    attack_start_seconds: float
    packet_size_bytes: int
    jitter_max_ms: float
    burst_on_mean_seconds: float
    burst_off_mean_seconds: float
    measurement_noise_std_ratio: float

    @property
    def environment_key(self) -> tuple[object, ...]:
        """返回禁止跨切分重复的环境参数元组。"""
        return (
            self.initial_capacity_mbps,
            self.shifted_capacity_mbps,
            self.capacity_shift_seconds,
            self.access_delay_ms,
            self.bottleneck_delay_ms,
            self.queue_model,
            self.queue_limit_packets,
            self.downstream_loss_rate,
            self.transport,
            self.packet_size_bytes,
            self.sender_count,
            self.arrival_model,
        )

    def to_record(self) -> dict[str, object]:
        """转换为稳定的 JSON 记录。"""
        return asdict(self)


def _rounded_uniform(generator: random.Random, lower: float, upper: float) -> float:
    return round(generator.uniform(lower, upper), 4)


def _in_range_config(
    generator: random.Random,
    *,
    split: str,
    ordinal: int,
    global_index: int,
) -> DomainConfig:
    initial_capacity = _rounded_uniform(generator, 2.0, 10.0)
    shift_ratio = generator.choice((1.0, 0.85, 0.70, 0.55))
    shifted_capacity = round(initial_capacity * shift_ratio, 4)
    shift_seconds = 0.0 if shift_ratio == 1.0 else _rounded_uniform(generator, 4.0, 8.0)
    sender_count = generator.randint(2, 8)
    traffic_mode = "benign" if global_index % 2 == 0 else "dos"
    total_benign_rate = initial_capacity * _rounded_uniform(generator, 0.25, 1.05)
    benign_rate = round(total_benign_rate / sender_count, 4)
    attacker_count = max(sender_count - 1, 1)
    total_attack_rate = initial_capacity * _rounded_uniform(generator, 1.20, 3.50)
    attack_rate = round(total_attack_rate / attacker_count, 4)
    return DomainConfig(
        schema_version=SCHEMA_VERSION,
        config_id=f"dr-{split}-{ordinal:03d}",
        split=split,
        seed=DEFAULT_SEED + global_index,
        run=1,
        duration_seconds=12.0,
        window_seconds=0.1,
        traffic_mode=traffic_mode,
        transport=TRANSPORTS[global_index % len(TRANSPORTS)],
        queue_model=generator.choice(IN_RANGE_QUEUE_MODELS),
        arrival_model=ARRIVAL_MODELS[(global_index // 2) % len(ARRIVAL_MODELS)],
        initial_capacity_mbps=initial_capacity,
        shifted_capacity_mbps=shifted_capacity,
        capacity_shift_seconds=shift_seconds,
        access_delay_ms=_rounded_uniform(generator, 0.5, 5.0),
        bottleneck_delay_ms=_rounded_uniform(generator, 2.0, 20.0),
        queue_limit_packets=generator.randint(20, 100),
        downstream_loss_rate=_rounded_uniform(generator, 0.0, 0.02),
        sender_count=sender_count,
        benign_rate_mbps=benign_rate,
        attack_rate_mbps=attack_rate,
        attack_start_seconds=_rounded_uniform(generator, 3.0, 7.0),
        packet_size_bytes=PACKET_SIZES[global_index % len(PACKET_SIZES)],
        jitter_max_ms=_rounded_uniform(generator, 0.0, 80.0),
        burst_on_mean_seconds=_rounded_uniform(generator, 0.05, 0.50),
        burst_off_mean_seconds=_rounded_uniform(generator, 0.02, 0.30),
        measurement_noise_std_ratio=generator.choice((0.0, 0.01, 0.03, 0.05)),
    )


def _out_of_range_config(
    generator: random.Random,
    *,
    ordinal: int,
    global_index: int,
) -> DomainConfig:
    low_capacity = ordinal % 2 == 0
    initial_capacity = _rounded_uniform(
        generator,
        0.5 if low_capacity else 12.0,
        1.5 if low_capacity else 20.0,
    )
    shift_ratio = generator.choice((1.0, 0.40, 0.65))
    shifted_capacity = round(initial_capacity * shift_ratio, 4)
    shift_seconds = 0.0 if shift_ratio == 1.0 else _rounded_uniform(generator, 3.0, 9.0)
    sender_count = generator.randint(2, 10)
    traffic_mode = "benign" if ordinal % 2 == 0 else "dos"
    total_benign_rate = initial_capacity * _rounded_uniform(generator, 0.15, 1.20)
    benign_rate = round(total_benign_rate / sender_count, 4)
    attacker_count = max(sender_count - 1, 1)
    total_attack_rate = initial_capacity * _rounded_uniform(generator, 1.10, 4.50)
    attack_rate = round(total_attack_rate / attacker_count, 4)
    return DomainConfig(
        schema_version=SCHEMA_VERSION,
        config_id=f"dr-out_of_range-{ordinal:03d}",
        split="out_of_range",
        seed=DEFAULT_SEED + global_index,
        run=1,
        duration_seconds=12.0,
        window_seconds=0.1,
        traffic_mode=traffic_mode,
        transport=TRANSPORTS[global_index % len(TRANSPORTS)],
        queue_model="red",
        arrival_model=ARRIVAL_MODELS[(global_index // 2) % len(ARRIVAL_MODELS)],
        initial_capacity_mbps=initial_capacity,
        shifted_capacity_mbps=shifted_capacity,
        capacity_shift_seconds=shift_seconds,
        access_delay_ms=_rounded_uniform(generator, 0.1, 8.0),
        bottleneck_delay_ms=_rounded_uniform(generator, 30.0, 100.0),
        queue_limit_packets=(
            generator.randint(5, 15) if ordinal % 2 == 0 else generator.randint(120, 200)
        ),
        downstream_loss_rate=_rounded_uniform(generator, 0.03, 0.10),
        sender_count=sender_count,
        benign_rate_mbps=benign_rate,
        attack_rate_mbps=attack_rate,
        attack_start_seconds=_rounded_uniform(generator, 2.5, 8.0),
        packet_size_bytes=(128 if ordinal % 2 == 0 else 1500),
        jitter_max_ms=_rounded_uniform(generator, 80.0, 200.0),
        burst_on_mean_seconds=_rounded_uniform(generator, 0.02, 0.80),
        burst_off_mean_seconds=_rounded_uniform(generator, 0.01, 0.60),
        measurement_noise_std_ratio=generator.choice((0.08, 0.12, 0.20)),
    )


def generate_domain_configs(seed: int = DEFAULT_SEED) -> tuple[DomainConfig, ...]:
    """生成冻结的 120/30/30/30 独立配置。"""
    if isinstance(seed, bool) or not isinstance(seed, int) or seed <= 0:
        raise DomainRandomizationError("随机种子必须为正整数")
    generator = random.Random(seed)
    configs: list[DomainConfig] = []
    global_index = 0
    for split in ("train", "calibration", "unseen_configuration"):
        for ordinal in range(1, SPLIT_COUNTS[split] + 1):
            global_index += 1
            configs.append(
                _in_range_config(
                    generator,
                    split=split,
                    ordinal=ordinal,
                    global_index=global_index,
                )
            )
    for ordinal in range(1, SPLIT_COUNTS["out_of_range"] + 1):
        global_index += 1
        configs.append(
            _out_of_range_config(
                generator,
                ordinal=ordinal,
                global_index=global_index,
            )
        )
    _validate_configs(configs)
    return tuple(configs)


def _validate_configs(configs: list[DomainConfig]) -> None:
    expected_count = sum(SPLIT_COUNTS.values())
    if len(configs) != expected_count:
        raise DomainRandomizationError(f"配置数应为 {expected_count}，实际为 {len(configs)}")
    config_ids = [config.config_id for config in configs]
    if len(config_ids) != len(set(config_ids)):
        raise DomainRandomizationError("config_id 存在重复")
    environment_keys = [config.environment_key for config in configs]
    if len(environment_keys) != len(set(environment_keys)):
        raise DomainRandomizationError("环境参数元组存在跨运行重复")
    actual_counts = {
        split: sum(config.split == split for config in configs) for split in SPLIT_COUNTS
    }
    if actual_counts != SPLIT_COUNTS:
        raise DomainRandomizationError(
            f"四类切分数量不满足冻结契约：{actual_counts} != {SPLIT_COUNTS}"
        )
    if any(config.queue_model != "red" for config in configs if config.split == "out_of_range"):
        raise DomainRandomizationError("范围外测试必须使用训练未见的 RED 队列")
    if any(config.queue_model == "red" for config in configs if config.split != "out_of_range"):
        raise DomainRandomizationError("RED 队列不得泄漏到训练、校准或未见配置测试")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_domain_manifest(output_dir: Path, configs: tuple[DomainConfig, ...]) -> dict[str, object]:
    """写出不可覆盖的配置清单及摘要。"""
    normalized_output = Path(output_dir).expanduser().resolve()
    if normalized_output.exists() or normalized_output.is_symlink():
        raise DomainRandomizationError(f"输出目录已存在，不得覆盖：{normalized_output}")
    normalized_output.mkdir(parents=True)
    manifest_path = normalized_output / "config_manifest.jsonl"
    with manifest_path.open("w", encoding="utf-8") as destination:
        for config in configs:
            destination.write(
                json.dumps(config.to_record(), ensure_ascii=False, sort_keys=True) + "\n"
            )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "total_config_count": len(configs),
        "split_counts": {
            split: sum(config.split == split for config in configs) for split in SPLIT_COUNTS
        },
        "queue_models": sorted({config.queue_model for config in configs}),
        "transports": sorted({config.transport for config in configs}),
        "arrival_models": sorted({config.arrival_model for config in configs}),
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "input_leakage_prohibition": [
            "capacity",
            "queue_truth",
            "scenario_or_config_id",
            "attack_label",
            "seed",
            "run",
        ],
    }
    summary_path = normalized_output / "manifest_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成任务十七 ns-3 域随机化配置矩阵")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    configs = generate_domain_configs(args.seed)
    summary = write_domain_manifest(args.output_dir, configs)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
