# -*- coding: utf-8 -*-
"""FT 训练数据路径耗时基准：量化「X23 显存常驻」的收益上限。

被检验的假设：训练步的 GPU 利用率波动（服务器实测 31%–95%）来自每步从主机
gather ``8,192 × 83`` 的特征行；若成立，把 ``X23`` 常驻显存可消除该开销。

本工具只测数据路径，不训练、不改模型：

1. ``索引构造``：从 ``I23`` 读取一个微批的流索引（常驻后仍然需要）；
2. ``主机取行``：``X23[indices]`` 的 numpy 花式索引（常驻后消除）；
3. ``主机到设备``：``torch.from_numpy(...).to(device)``（常驻后消除）；
4. ``设备内取行``：若显存足够，把 ``X23`` 搬入设备后在设备内索引（常驻后的新开销）。

收益上限 = (主机取行 + 主机到设备 − 设备内取行) / 单步总时长。

证据边界：纯数据路径基准，不含前向反向；与训练并发运行时 CPU 存在争用，
结果标 ``resource_contention``。不进论文结果。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

RUN_ID = "ch3-ft-data-path-benchmark-v1"
SCHEMA_VERSION = "ch3-ft-data-path-benchmark-receipt-v1"
SEQ_LEN = 128


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def pick_device(name: str) -> torch.device:
    """设备无关选择：优先按参数，其次 CUDA，再次 MPS，最后 CPU。"""
    if name != "auto":
        return torch.device(name)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def synchronize(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize()
    elif device.type == "mps":
        torch.mps.synchronize()


def timed(fn, repeats: int, device: torch.device) -> float:
    """返回单次平均秒数；先热身三次再计时。"""
    for _ in range(3):
        fn()
    synchronize(device)
    start = time.perf_counter()
    for _ in range(repeats):
        fn()
    synchronize(device)
    return (time.perf_counter() - start) / repeats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument("--output-root", default=f"runs/diagnostics/{RUN_ID}")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--micro-batch", type=int, default=64)
    parser.add_argument("--repeats", type=int, default=15)
    parser.add_argument("--step-seconds", type=float, default=0.208,
                        help="对照用的单步总时长；服务器实测 4.80 步/秒")
    parser.add_argument("--try-resident", action="store_true",
                        help="尝试把 X23 搬入设备并测设备内索引；显存不足会跳过")
    args = parser.parse_args()

    cache_root = Path(args.cache_root).resolve()
    output_root = Path(args.output_root).resolve()
    device = pick_device(args.device)

    features = np.load(cache_root / "X23.npy", mmap_mode="r")
    indices = np.load(cache_root / "I23.npy", mmap_mode="r")
    rng = np.random.default_rng(0)

    def build_indices() -> np.ndarray:
        rows = np.sort(rng.choice(len(indices), args.micro_batch, replace=False))
        return np.asarray(indices[rows])[:, :SEQ_LEN].reshape(-1)

    sample = build_indices()
    values = np.asarray(features[sample])
    print(f"设备={device}  每步 {len(sample):,} 条流 × {values.shape[1]} 维 = {values.nbytes / 1e6:.2f} MB", flush=True)

    index_only = timed(build_indices, args.repeats, device)
    host_gather_total = timed(lambda: np.asarray(features[build_indices()]), args.repeats, device)
    host_gather = host_gather_total - index_only
    to_device = timed(lambda: torch.from_numpy(values).to(device), args.repeats, device)

    resident: dict[str, Any] = {"attempted": bool(args.try_resident), "succeeded": False}
    device_gather = None
    if args.try_resident and device.type != "cpu":
        try:
            resident_matrix = torch.from_numpy(np.asarray(features)).to(device)
            sample_tensor = torch.from_numpy(sample).to(device)

            def device_index() -> torch.Tensor:
                return resident_matrix[sample_tensor]

            device_gather = timed(device_index, args.repeats, device)
            resident["succeeded"] = True
            resident["matrix_bytes"] = int(resident_matrix.numel() * resident_matrix.element_size())
            del resident_matrix, sample_tensor
            if device.type == "cuda":
                torch.cuda.empty_cache()
        except RuntimeError as error:
            resident["error"] = str(error)[:200]

    eliminated = host_gather + to_device
    added = device_gather if device_gather is not None else 0.0
    upper_bound = (eliminated - added) / args.step_seconds

    receipt = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "evidence_tier": "engineering_only_data_path_benchmark",
        "resource_contention": True,
        "target_reads": 0,
        "device": str(device),
        "micro_batch_sequences": args.micro_batch,
        "flows_per_step": int(len(sample)),
        "bytes_per_step": int(values.nbytes),
        "seconds": {
            "index_build": index_only,
            "host_gather": host_gather,
            "host_to_device": to_device,
            "device_gather": device_gather,
        },
        "reference_step_seconds": args.step_seconds,
        "data_path_share": (index_only + host_gather + to_device) / args.step_seconds,
        "resident_upper_bound_gain": upper_bound,
        "resident": resident,
    }
    atomic_json(output_root / "data-path-benchmark.json", receipt)

    print(f"索引构造      : {index_only:.5f} 秒", flush=True)
    print(f"主机取行      : {host_gather:.5f} 秒", flush=True)
    print(f"主机到设备    : {to_device:.5f} 秒", flush=True)
    if device_gather is not None:
        print(f"设备内取行    : {device_gather:.5f} 秒（常驻后的新开销）", flush=True)
    else:
        print("设备内取行    : 未测（未启用或显存不足）", flush=True)
    print(f"数据侧占单步  : {100 * receipt['data_path_share']:.1f}%", flush=True)
    print(f"常驻收益上限  : {100 * upper_bound:.1f}%", flush=True)
    print("CH3_FT_DATA_PATH_BENCHMARK_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
