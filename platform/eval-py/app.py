#!/usr/bin/env python
"""第五章评测服务对比：Python FastAPI + PyTorch (MPS) 侧。

契约（两端完全一致）：
- `GET /health` → `{"status":"ok","device":"mps","input_dim":4561,"k":4}`
- `POST /eval`，请求体为裸 little-endian float32 矩阵（行优先，shape `(n, input_dim)`，
  `1 <= n <= 32`），响应 `{"probs":[float, ...], "batch": n}`；概率为 k 个成员 sigmoid 的均值。
- 不使用 JSON 传输大矩阵：4561 维特征若用十进制文本会有 ~3 MB/请求，测到的主要是
  浮点格式化而非服务开销；两端共用同一二进制契约。

模型来源：`runs/diagnostics/ch5-eval-benchmark/model/tabm4_state.safetensors`，
由 `platform/eval-py/export_model.py` 以探针同种子重训后导出。模型结构直接导入
训练探针的 `TabMMLP`，不复制一份实现，避免结构漂移。

运行：
  /opt/miniconda3/envs/rwkv/bin/python platform/eval-py/app.py \
      --manifest <.../model/model_manifest.json> --port 18081
"""

from __future__ import annotations

import argparse
import threading
import time
from pathlib import Path

import numpy as np
import torch
import uvicorn
from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from safetensors.torch import load_file

from model import TabMMLP

MAX_BATCH = 32
_MODEL: TabMMLP | None = None
_INPUT_DIM = 0
_DEVICE = torch.device("cpu")
_LOCK = threading.Lock()
_STARTUP: dict[str, float] = {}


def build_app(manifest_path: Path) -> FastAPI:
    global _MODEL, _INPUT_DIM, _DEVICE
    import json

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_dir = manifest_path.resolve().parents[1]
    t_load = time.perf_counter()
    _DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    k = int(manifest["k"])
    _INPUT_DIM = int(manifest["input_dim"])
    weights = run_dir / manifest["weights_path"]
    state = load_file(str(weights))
    model = TabMMLP(_INPUT_DIM, k)
    model.load_state_dict(state, strict=True)
    model.eval().to(_DEVICE)
    with torch.no_grad():
        model(torch.zeros(1, _INPUT_DIM, device=_DEVICE))
    _MODEL = model
    _STARTUP["model_load_s"] = time.perf_counter() - t_load
    print(
        f"[eval-py] device={_DEVICE.type} input_dim={_INPUT_DIM} k={k} "
        f"params={sum(p.numel() for p in model.parameters()):,} "
        f"model_load={_STARTUP['model_load_s']:.3f}s",
        flush=True,
    )

    app = FastAPI(title="ch5-eval-py")

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "device": _DEVICE.type,
            "input_dim": _INPUT_DIM,
            "k": int(manifest["k"]),
            "model_load_s": _STARTUP["model_load_s"],
        }

    @app.post("/eval")
    def eval_batch(payload: bytes = Body(..., media_type="application/octet-stream")) -> JSONResponse:
        t0 = time.perf_counter()
        n_floats = len(payload) // 4
        if len(payload) % 4 != 0 or n_floats % _INPUT_DIM != 0:
            return JSONResponse({"error": "body is not a whole (n, input_dim) float32 matrix"}, status_code=400)
        n = n_floats // _INPUT_DIM
        if n < 1 or n > MAX_BATCH:
            return JSONResponse({"error": f"batch must be 1..{MAX_BATCH}, got {n}"}, status_code=400)

        arr = np.frombuffer(payload, dtype="<f4").reshape(n, _INPUT_DIM).copy()
        x = torch.from_numpy(arr)
        with _LOCK:
            with torch.no_grad():
                probs = _MODEL(x.to(_DEVICE)).detach().to("cpu").reshape(-1).tolist()
        return JSONResponse({"probs": probs, "batch": n})

    app.state.startup = _STARTUP
    return app


def main() -> int:
    parser = argparse.ArgumentParser(description="第五章 Python 评测服务")
    parser.add_argument("--manifest", required=True, help="model_manifest.json 路径")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18081)
    args = parser.parse_args()
    app = build_app(Path(args.manifest))
    print(f"[eval-py] listening on {args.host}:{args.port}", flush=True)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning", access_log=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
