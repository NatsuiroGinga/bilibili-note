#!/usr/bin/env python
"""第五章评测服务对比压测器（Python / Rust 共用同一请求流与客户端）。

用法：
  /opt/miniconda3/envs/rwkv/bin/python platform/eval-bench/bench.py --service py
  /opt/miniconda3/envs/rwkv/bin/python platform/eval-bench/bench.py --service rs
  /opt/miniconda3/envs/rwkv/bin/python platform/eval-bench/bench.py --combine

协议：`POST /eval`，请求体为裸 little-endian float32 `(n, 4561)`；响应 JSON
`{"probs":[...], "batch": n}`。客户端为 asyncio + httpx，连接池大小等于并发数。

测量口径：
- 预热 20 个请求不计入；
- 并发 1 与 8 各跑 3 轮完整面板（303 请求 / 9,686 样本），延迟为客户端观测的
  端到端往返时间（含排队）；
- 吞吐 = 9,686 / 单轮墙钟，取 3 轮中位数；
- RSS 由 `ps -o rss=` 每 50 ms 采样，报告全程峰值与启动完成后基线；
- 启动时间 = spawn 到 `/health` 首次 200 的墙钟，含模型加载。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import statistics
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_DIR = REPO_ROOT / "thesis/experiments/llm_probe/runs/diagnostics/ch5-eval-benchmark"
MODEL_DIR = RUN_DIR / "model"
DATA_DIR = RUN_DIR / "data"
RESULTS_DIR = RUN_DIR / "results"
LOGS_DIR = RUN_DIR / "logs"
PYTHON = "/opt/miniconda3/envs/rwkv/bin/python"
TCH_LIB = "/opt/miniconda3/envs/rwkv/lib/python3.14/site-packages/torch/lib"
BATCH = 32
SERVICES = {"py": 18081, "rs": 18082}


class RssSampler(threading.Thread):
    def __init__(self, pid: int, interval_s: float = 0.05) -> None:
        super().__init__(daemon=True)
        self.pid = pid
        self.interval_s = interval_s
        self.samples: list[tuple[float, int]] = []
        self._stop = threading.Event()

    def run(self) -> None:
        while not self._stop.is_set():
            try:
                out = subprocess.run(
                    ["ps", "-o", "rss=", "-p", str(self.pid)],
                    capture_output=True,
                    text=True,
                    check=False,
                ).stdout.strip()
                if out:
                    self.samples.append((time.perf_counter(), int(out.split()[0])))
            except (ValueError, OSError):
                pass
            time.sleep(self.interval_s)

    def stop(self) -> None:
        self._stop.set()
        self.join(timeout=2.0)

    def max_mb(self) -> float:
        return max((kb for _, kb in self.samples), default=0) / 1024.0

    def current_mb(self) -> float:
        try:
            out = subprocess.run(
                ["ps", "-o", "rss=", "-p", str(self.pid)],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            return int(out.split()[0]) / 1024.0 if out else 0.0
        except (ValueError, OSError):
            return 0.0


def load_stream() -> tuple[np.ndarray, np.ndarray, list[bytes]]:
    meta = json.loads((DATA_DIR / "panel_2024_meta.json").read_text(encoding="utf-8"))
    n, d = meta["shape"]
    x = np.fromfile(DATA_DIR / "panel_2024.f32", dtype="<f4").reshape(n, d)
    order = np.fromfile(DATA_DIR / "request_order.i32", dtype="<i4").astype(np.int64)
    if order.size != n:
        raise SystemExit(f"request order size {order.size} != panel {n}")
    bodies = [x[order[i : i + BATCH]].astype("<f4", copy=False).tobytes() for i in range(0, n, BATCH)]
    return x, order, bodies


def service_command(service: str, port: int) -> list[str]:
    manifest = str(MODEL_DIR / "model_manifest.json")
    if service == "py":
        return [PYTHON, str(REPO_ROOT / "platform/eval-py/app.py"), "--manifest", manifest, "--port", str(port)]
    return [str(REPO_ROOT / "platform/eval-rs/run.sh"), "--manifest", manifest, "--port", str(port)]


def wait_health(url: str, timeout_s: float = 180.0) -> float:
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout_s:
        try:
            r = httpx.get(f"{url}/health", timeout=2.0)
            if r.status_code == 200:
                return time.perf_counter() - t0
        except httpx.HTTPError:
            pass
        time.sleep(0.02)
    raise RuntimeError(f"service at {url} did not become healthy within {timeout_s}s")


async def one_request(client: httpx.AsyncClient, url: str, body: bytes) -> tuple[float, int]:
    t0 = time.perf_counter()
    r = await client.post(f"{url}/eval", content=body, headers={"content-type": "application/octet-stream"})
    dt = time.perf_counter() - t0
    r.raise_for_status()
    data = r.json()
    probs = data["probs"]
    n = int(data["batch"])
    if len(probs) != n:
        raise RuntimeError(f"response has {len(probs)} probs for batch {n}")
    return dt, n


async def run_pass(url: str, bodies: list[bytes], concurrency: int) -> dict:
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(limits=limits, timeout=120.0) as client:
        queue: asyncio.Queue[int] = asyncio.Queue()
        for i in range(len(bodies)):
            queue.put_nowait(i)
        latencies: list[float] = []
        samples_done = 0
        lock = asyncio.Lock()

        async def worker() -> None:
            nonlocal samples_done
            while True:
                try:
                    i = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return
                dt, n = await one_request(client, url, bodies[i])
                async with lock:
                    latencies.append(dt)
                    samples_done += n

        t0 = time.perf_counter()
        await asyncio.gather(*(worker() for _ in range(concurrency)))
        wall = time.perf_counter() - t0
    return {
        "concurrency": concurrency,
        "wall_s": wall,
        "requests": len(latencies),
        "samples": samples_done,
        "throughput_samples_s": samples_done / wall,
        "latency_ms": latency_stats(latencies),
    }


def latency_stats(latencies_s: list[float]) -> dict:
    ms = np.array(latencies_s, dtype=np.float64) * 1000.0
    return {
        "p50": float(np.percentile(ms, 50)),
        "p95": float(np.percentile(ms, 95)),
        "p99": float(np.percentile(ms, 99)),
        "mean": float(ms.mean()),
        "min": float(ms.min()),
        "max": float(ms.max()),
        "n": int(ms.size),
    }


def guard_no_training() -> None:
    out = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True, check=False).stdout
    markers = ("ch5_system_runner", "export_model.py", "ch4_lamda_tabm_pilot.py")
    hits = [line.strip() for line in out.splitlines() if any(m in line for m in markers) and "eval-bench/bench.py" not in line]
    if hits:
        raise SystemExit("检测到其他训练/导出进程占用 MPS，停止压测：\n" + "\n".join(hits))


def run_service(service: str, repeats: int, warmup: int, concurrency_levels: list[int]) -> int:
    guard_no_training()
    x_panel, _, bodies = load_stream()
    port = SERVICES[service]
    url = f"http://127.0.0.1:{port}"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f"{service}_server.log"
    cmd = service_command(service, port)
    env = os.environ.copy()
    if service == "rs":
        env["DYLD_LIBRARY_PATH"] = f"{TCH_LIB}:{env.get('DYLD_LIBRARY_PATH', '')}"
    print(f"[bench:{service}] spawn {' '.join(cmd)}", flush=True)
    t_spawn = time.perf_counter()
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env, cwd=str(REPO_ROOT))
        sampler = RssSampler(proc.pid)
        sampler.start()
        try:
            wait_health(url)
            startup_s = time.perf_counter() - t_spawn
            rss_after_startup = sampler.current_mb()
            print(f"[bench:{service}] healthy in {startup_s:.3f}s, rss={rss_after_startup:.1f}MB", flush=True)

            # 数值一致性：首请求
            first_dt, first_n = asyncio.run(one_request_sync(url, bodies[0]))
            consistency = fetch_probs(url, bodies[0])
            reference = json.loads((DATA_DIR / "reference_batch0_probs.json").read_text(encoding="utf-8"))
            max_abs_ref = float(
                np.max(np.abs(np.array(consistency["probs"]) - np.array(reference["probs"])))
            )
            consistency.update(
                {
                    "service": service,
                    "max_abs_diff_vs_reference": max_abs_ref,
                    "first_request_latency_ms": first_dt * 1000.0,
                    "batch": first_n,
                }
            )
            (RESULTS_DIR / f"consistency_{service}.json").write_text(
                json.dumps(consistency, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print(f"[bench:{service}] consistency max_abs_diff={max_abs_ref:.3e}", flush=True)

            # 预热
            for i in range(warmup):
                asyncio.run(one_request_sync(url, bodies[i % len(bodies)]))
            print(f"[bench:{service}] warmup {warmup} requests done", flush=True)

            scenarios: dict[str, dict] = {}
            for c in concurrency_levels:
                passes = []
                for _ in range(repeats):
                    passes.append(asyncio.run(run_pass(url, bodies, c)))
                scenarios[f"c{c}"] = {
                    "concurrency": c,
                    "passes": passes,
                    "throughput_samples_s_median": float(statistics.median(p["throughput_samples_s"] for p in passes)),
                    "throughput_samples_s_all": [p["throughput_samples_s"] for p in passes],
                    "latency_ms_per_pass": [p["latency_ms"] for p in passes],
                    "latency_ms_median_of_passes": {
                        "p50": float(statistics.median(p["latency_ms"]["p50"] for p in passes)),
                        "p95": float(statistics.median(p["latency_ms"]["p95"] for p in passes)),
                        "p99": float(statistics.median(p["latency_ms"]["p99"] for p in passes)),
                        "n_per_pass": int(passes[0]["latency_ms"]["n"]),
                        "n_passes": len(passes),
                    },
                }
                med = scenarios[f"c{c}"]["latency_ms_median_of_passes"]
                print(
                    f"[bench:{service}] c={c} "
                    f"p50={med['p50']:.2f}ms p95={med['p95']:.2f}ms p99={med['p99']:.2f}ms "
                    f"thr={scenarios[f'c{c}']['throughput_samples_s_median']:.1f} samples/s",
                    flush=True,
                )

            payload = {
                "schema_version": "ch5-eval-service-result-v1",
                "service": service,
                "command": cmd,
                "url": url,
                "startup_s": startup_s,
                "rss_mb_after_startup": rss_after_startup,
                "rss_mb_max": sampler.max_mb(),
                "rss_samples_n": len(sampler.samples),
                "warmup_requests": warmup,
                "repeats": repeats,
                "batch": BATCH,
                "n_requests": len(bodies),
                "n_samples": int(sum(len(b) // 4 // x_panel.shape[1] for b in bodies)),
                "scenarios": scenarios,
                "consistency": consistency,
                "ts": datetime.now(UTC).isoformat(),
            }
            (RESULTS_DIR / f"{service}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print(f"[bench:{service}] wrote {RESULTS_DIR / f'{service}.json'}", flush=True)
            return 0
        finally:
            sampler.stop()
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


async def one_request_sync(url: str, body: bytes) -> tuple[float, int]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        return await one_request(client, url, body)


def fetch_probs(url: str, body: bytes) -> dict:
    r = httpx.post(f"{url}/eval", content=body, headers={"content-type": "application/octet-stream"}, timeout=120.0)
    r.raise_for_status()
    return r.json()


def environment() -> dict:
    def sysctl(key: str) -> str:
        try:
            return subprocess.run(["sysctl", "-n", key], capture_output=True, text=True, check=False).stdout.strip()
        except OSError:
            return ""

    manifest = json.loads((MODEL_DIR / "model_manifest.json").read_text(encoding="utf-8"))
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": sysctl("machdep.cpu.brand_string"),
        "memory_bytes": int(sysctl("hw.memsize") or 0),
        "python": platform.python_version(),
        "torch": manifest.get("torch_version"),
        "tch": "0.25.0 (git d5bbf6fe6cdbb06006aac5cb673be3c8d029c24b, TORCH_VERSION=2.12.0)",
        "libtorch": "Python torch 2.12.0（LIBTORCH_USE_PYTORCH=1，无版本 bypass）",
        "client": f"httpx {httpx.__version__}, numpy {np.__version__}",
    }


def combine() -> int:
    py = json.loads((RESULTS_DIR / "py.json").read_text(encoding="utf-8"))
    rs = json.loads((RESULTS_DIR / "rs.json").read_text(encoding="utf-8"))
    manifest = json.loads((MODEL_DIR / "model_manifest.json").read_text(encoding="utf-8"))
    consistency = {
        "reference": "export_model.py: Python MPS forward on batch0",
        "max_abs_diff_vs_reference": {
            "py": py["consistency"]["max_abs_diff_vs_reference"],
            "rs": rs["consistency"]["max_abs_diff_vs_reference"],
        },
    }
    ref = np.array(json.loads((DATA_DIR / "reference_batch0_probs.json").read_text(encoding="utf-8"))["probs"])
    pyp = np.array(py["consistency"]["probs"])
    rsp = np.array(rs["consistency"]["probs"])
    consistency["py_vs_rs_max_abs_diff"] = float(np.max(np.abs(pyp - rsp)))
    consistency["py_vs_reference_max_abs_diff"] = float(np.max(np.abs(pyp - ref)))
    consistency["rs_vs_reference_max_abs_diff"] = float(np.max(np.abs(rsp - ref)))

    levels = sorted({int(k[1:]) for k in py["scenarios"]})

    def series(pct: str) -> dict:
        out = {}
        for name, data in (("py", py), ("rs", rs)):
            out[name] = [
                data["scenarios"][f"c{c}"]["latency_ms_median_of_passes"][pct] for c in levels
            ]
        return out

    def throughput() -> dict:
        out = {}
        for name, data in (("py", py), ("rs", rs)):
            out[name] = [
                data["scenarios"][f"c{c}"]["throughput_samples_s_median"] for c in levels
            ]
        return out

    chart = {
        "services": ["py", "rs"],
        "concurrency": levels,
        "batch": BATCH,
        "panel_samples": int(py["n_samples"]),
        "latency_stat": "median of per-pass percentiles over 3 passes (ms)",
        "throughput_stat": "median of 3 full-panel passes (samples/s)",
        "p50_ms": series("p50"),
        "p95_ms": series("p95"),
        "p99_ms": series("p99"),
        "throughput_samples_s": throughput(),
        "rss_mb_max": {"py": py["rss_mb_max"], "rs": rs["rss_mb_max"]},
        "startup_s": {"py": py["startup_s"], "rs": rs["startup_s"]},
    }
    benchmark = {
        "schema_version": "ch5-eval-service-benchmark-v1",
        "experiment": {
            "purpose": "同一 tabm4 权重与同一 2024 测试面板请求流下的评测服务层对比",
            "model": "uniform tabm4 (k=4), seed 42",
            "panel": "2024 test, 9,686 samples, batch 32, fixed order seed 42",
            "hardware": "Apple Silicon MPS（同机、串行运行）",
            "note": "张量计算同核（libtorch），差异集中在 HTTP/序列化/调度/进程模型",
        },
        "environment": environment(),
        "model_manifest": manifest,
        "services": {"py": py, "rs": rs},
        "consistency": consistency,
        "chart_data": chart,
        "ts": datetime.now(UTC).isoformat(),
    }
    out = RUN_DIR / "benchmark.json"
    out.write_text(json.dumps(benchmark, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[bench] wrote {out}", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="第五章评测服务对比压测器")
    parser.add_argument("--service", choices=("py", "rs"))
    parser.add_argument("--combine", action="store_true")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--concurrency", type=int, nargs="+", default=[1, 8])
    args = parser.parse_args()
    if args.combine:
        return combine()
    if not args.service:
        parser.error("需要 --service 或 --combine")
    return run_service(args.service, args.repeats, args.warmup, args.concurrency)


if __name__ == "__main__":
    raise SystemExit(main())
