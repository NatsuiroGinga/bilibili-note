#!/usr/bin/env python
"""训练并导出第五章评测服务对比实验的冻结模型（uniform tabm4）。

边界：不修改训练内核。本脚本直接导入既有探针模块
`ch4_lamda_tabm_pilot.TabMMLP` 与 `train_epochs_tabm`，按探针脚本 `run_arm`
完全相同的顺序（同 seed、同年度流、同 parts、同优化器年度重建）重训一次，
仅额外把最终 state_dict 导出为 safetensors，并物化 2024 测试面板与固定请求顺序。

产物目录：`thesis/experiments/llm_probe/runs/diagnostics/ch5-eval-benchmark/`
- `model/tabm4_state.safetensors`：float32 state_dict（Python/Rust 两端共同加载）
- `model/model_manifest.json`：配置、哈希、2024 F1、与探针 preds 的一致性
- `data/panel_2024.f32`：2024 测试面板 float32 裸矩阵（9686 × 4561）
- `data/panel_2024_meta.json`：形状、dtype、来源
- `data/request_order.i32`：固定种子 42 的 9686 样本排列
- `data/reference_batch0_probs.json`：首请求（order[:32]）的 Python MPS 参考概率

运行：
  /opt/miniconda3/envs/rwkv/bin/python platform/eval-py/export_model.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "thesis/experiments/llm_probe/tools"
RUN_DIR = REPO_ROOT / "thesis/experiments/llm_probe/runs/diagnostics/ch5-eval-benchmark"
MODEL_DIR = RUN_DIR / "model"
DATA_DIR = RUN_DIR / "data"
PILOT_DIR = REPO_ROOT / "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-tabm-pilot"

sys.path.insert(0, str(TOOLS_DIR))
import ch3_lamda_domain_il_e4 as ch3  # noqa: E402
from ch4_lamda_tabm_pilot import (  # noqa: E402
    TabMMLP,
    f1_of,
    train_epochs_tabm,
)
from ch4_lamda_training_process_2x2 import build_parts  # noqa: E402

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
SEED = ch3.SEED
ARM = "tabm4"
K = 4
BATCH_FOR_SERVICE = 32
REQUEST_ORDER_SEED = 42


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    years = list(ch3.DOMAIN_YEARS)
    print(f"[export] arm={ARM} k={K} device={DEVICE.type} seed={SEED}", flush=True)
    print(
        f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
        f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
        f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={ch3.OFFICIAL_MEMORY}",
        flush=True,
    )

    store = {y: ch3.load_year(y, "train") for y in years}
    input_dim = int(store[years[0]][0].shape[1])
    rng = np.random.default_rng(SEED)
    buf_rng = np.random.default_rng(SEED)
    model = TabMMLP(input_dim, K).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[model] input_dim={input_dim} params={n_params:,}", flush=True)

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        parts, _meta = build_parts(store, years, idx, x_curr, y_curr, buf_rng)
        print(
            f"[parts] {year}: rows={int(sum(p[0].shape[0] for p in parts)):,} "
            f"pos={int(sum(int((p[1] == 1).sum()) for p in parts)):,}",
            flush=True,
        )
        t_epoch = time.time()
        train_epochs_tabm(model, parts, ch3.OFFICIAL_EPOCHS, DEVICE, rng, ARM, year)
        xt, yt = ch3.load_year(year, "test")
        m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, DEVICE)
        del xt, yt
        print(f"[{year}] current_f1={m['f1']:.4f} ({time.time() - t_epoch:.0f}s)", flush=True)

    # 2024 回测（与探针 backward F1 对照）与面板物化
    x2024, y2024 = ch3.load_year(2024, "test")
    scores_2024 = ch3.score_shard(model, x2024, ch3.OFFICIAL_BATCH, DEVICE).astype(np.float32)
    f1_2024 = f1_of(y2024, scores_2024)
    pilot = np.load(PILOT_DIR / "preds_tabm4_2024.npz")
    max_abs_vs_pilot = float(
        np.max(np.abs(scores_2024.astype(np.float64) - pilot["y_score"].astype(np.float64)))
    )
    print(
        f"[2024] f1={f1_2024:.10f} max_abs_vs_pilot={max_abs_vs_pilot:.3e}",
        flush=True,
    )

    panel_path = DATA_DIR / "panel_2024.f32"
    x2024.astype("<f4").tofile(panel_path)
    order = np.random.default_rng(REQUEST_ORDER_SEED).permutation(x2024.shape[0])
    order_path = DATA_DIR / "request_order.i32"
    order.astype("<i4").tofile(order_path)
    (DATA_DIR / "panel_2024_meta.json").write_text(
        json.dumps(
            {
                "shape": list(x2024.shape),
                "dtype": "float32-le",
                "path": str(panel_path.name),
                "source": "ch3.load_year(2024, 'test')",
                "n_samples": int(x2024.shape[0]),
                "n_features": int(x2024.shape[1]),
                "positive": int(y2024.sum()),
                "request_order_seed": REQUEST_ORDER_SEED,
                "request_order_path": str(order_path.name),
                "service_batch": BATCH_FOR_SERVICE,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # 首请求参考概率：Python MPS、冻结权重
    first = order[:BATCH_FOR_SERVICE]
    xb = torch.from_numpy(x2024[first].astype(np.float32)).to(DEVICE)
    model.eval()
    with torch.no_grad():
        ref = model(xb).detach().cpu().numpy().reshape(-1).astype(np.float64)
    (DATA_DIR / "reference_batch0_probs.json").write_text(
        json.dumps({"indices": [int(i) for i in first], "probs": ref.tolist()}, indent=2) + "\n",
        encoding="utf-8",
    )
    torch.mps.synchronize() if DEVICE.type == "mps" else None

    state = {k: v.detach().to("cpu").contiguous().float() for k, v in model.state_dict().items()}
    from safetensors.torch import save_file

    weights_path = MODEL_DIR / "tabm4_state.safetensors"
    save_file(state, str(weights_path), metadata={"format": "pt", "arm": ARM, "seed": str(SEED)})
    weights_sha = sha256_file(weights_path)

    manifest = {
        "schema_version": "ch5-eval-service-model-v1",
        "arm": ARM,
        "k": K,
        "input_dim": input_dim,
        "n_params": n_params,
        "seed": SEED,
        "device_trained": DEVICE.type,
        "torch_version": torch.__version__,
        "protocol": {
            "epochs": ch3.OFFICIAL_EPOCHS,
            "batch": ch3.OFFICIAL_BATCH,
            "lr": ch3.OFFICIAL_LR,
            "momentum": ch3.OFFICIAL_MOMENTUM,
            "weight_decay": ch3.OFFICIAL_WEIGHT_DECAY,
            "memory": ch3.OFFICIAL_MEMORY,
            "domain_years": years,
        },
        "f1_2024": f1_2024,
        "max_abs_diff_vs_pilot_preds": max_abs_vs_pilot,
        "weights_path": str(weights_path.relative_to(RUN_DIR)),
        "weights_sha256": weights_sha,
        "panel_path": str(panel_path.relative_to(RUN_DIR)),
        "panel_sha256": sha256_file(panel_path),
        "request_order_path": str(order_path.relative_to(RUN_DIR)),
        "request_order_sha256": sha256_file(order_path),
        "service_batch": BATCH_FOR_SERVICE,
        "n_requests": int(np.ceil(x2024.shape[0] / BATCH_FOR_SERVICE)),
        "wall_seconds": round(time.time() - t0, 1),
        "ts": datetime.now(UTC).isoformat(),
    }
    (MODEL_DIR / "model_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"[export] weights={weights_path} sha256={weights_sha[:16]}… "
        f"wall={manifest['wall_seconds']}s",
        flush=True,
    )
    print(f"[export] panel={panel_path} order={order_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
