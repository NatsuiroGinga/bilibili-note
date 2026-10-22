#!/usr/bin/env python
"""校验服务镜像 `platform/eval-py/model.py` 与训练探针 `TabMMLP` 等价。

用冻结权重与真实 2024 面板首批 32 样本，对比：
1) state_dict 键集合与形状；
2) 两个实现的输出概率最大绝对差。

结果写入 `runs/diagnostics/ch5-eval-benchmark/model/parity_check.json`。

运行：
  /opt/miniconda3/envs/rwkv/bin/python platform/eval-py/verify_model_parity.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch
from safetensors.torch import load_file

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_DIR = REPO_ROOT / "thesis/experiments/llm_probe/runs/diagnostics/ch5-eval-benchmark"
TOOLS_DIR = REPO_ROOT / "thesis/experiments/llm_probe/tools"
sys.path.insert(0, str(TOOLS_DIR))

from ch4_lamda_tabm_pilot import TabMMLP as TrainTabMMLP  # noqa: E402

from model import TabMMLP as ServeTabMMLP  # noqa: E402


def main() -> int:
    manifest = json.loads((RUN_DIR / "model/model_manifest.json").read_text(encoding="utf-8"))
    state = load_file(str(RUN_DIR / manifest["weights_path"]))
    k = int(manifest["k"])
    d = int(manifest["input_dim"])

    train = TrainTabMMLP(d, k)
    serve = ServeTabMMLP(d, k)
    train_keys = {name: tuple(t.shape) for name, t in train.state_dict().items()}
    serve_keys = {name: tuple(t.shape) for name, t in serve.state_dict().items()}
    keys_match = train_keys == serve_keys

    train.load_state_dict(state, strict=True)
    serve.load_state_dict(state, strict=True)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    train.eval().to(device)
    serve.eval().to(device)

    meta = json.loads((RUN_DIR / "data/panel_2024_meta.json").read_text(encoding="utf-8"))
    n, dim = meta["shape"]
    x = np.fromfile(RUN_DIR / "data/panel_2024.f32", dtype="<f4").reshape(n, dim)
    order = np.fromfile(RUN_DIR / "data/request_order.i32", dtype="<i4").astype(np.int64)
    xb = torch.from_numpy(x[order[:32]].astype(np.float32)).to(device)

    with torch.no_grad():
        a = train(xb).detach().to("cpu").numpy().reshape(-1)
        b = serve(xb).detach().to("cpu").numpy().reshape(-1)
    max_abs = float(np.max(np.abs(a.astype(np.float64) - b.astype(np.float64))))

    payload = {
        "device": device.type,
        "keys_match": keys_match,
        "n_keys": len(train_keys),
        "max_abs_diff": max_abs,
        "batch": 32,
        "weights_sha256": manifest["weights_sha256"],
        "ts": datetime.now(UTC).isoformat(),
    }
    out = RUN_DIR / "model/parity_check.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if keys_match and max_abs <= 1e-6 else 1


if __name__ == "__main__":
    raise SystemExit(main())
