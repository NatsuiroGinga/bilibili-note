# -*- coding: utf-8 -*-
"""第三章定稿模型（协议 A）四格权重的研究用途逐流推理入口。

从 `<cell>/weights.safetensors` 载入权重，对给定的逐流特征矩阵 `X`（N×83）、
序列索引 `I`（S×Lmax，元素是 X 的行号）与掩码 `M`（S×Lmax）产出逐流分数。

前向与打分循环与冻结脚本 `tools/ch3_final_weights_freeze.py` 的 `score24()` 完全一致：
按序列分批、取前 `sequence_length` 个位置、对掩码为真的位置把 sigmoid 概率散射回逐流数组。

输入约定（必须显式声明，选错会静默给出错误分数）：
  --input-convention standardized-cache
      X 已经是缓存约定：先用 LSPR23 逐列均值/标准差标准化、再裁剪到 [-10, 10]。
      `runs/diagnostics/dijk-repro/cache/X23.npy`、`X24.npy` 就是这个约定。
  --input-convention raw
      X 是未标准化的原始 83 维特征，此时必须同时给 --normalization-json，
      入口会按 `(x - mean) / std` 后裁剪到 [-10, 10]，并把非有限值置 0。

输出：
  --out-npy          逐流分数（float32，长度 N，未被任何序列覆盖的行保持 0）
  --out-seen-npy     可选，逐流覆盖掩码（bool，长度 N）

用法示例（在 llm_probe 项目根下）：
  uv run --no-sync python inference.py \
      --package-root . --cell C11 \
      --x-npy  runs/diagnostics/dijk-repro/cache/X24.npy \
      --index-npy runs/diagnostics/dijk-repro/cache/I24.npy \
      --mask-npy  runs/diagnostics/dijk-repro/cache/M24.npy \
      --input-convention standardized-cache \
      --out-npy /path/to/scores.npy
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from safetensors.torch import load_file


class Model(nn.Module):
    """与第三章训练脚本逐字一致的结构：逐流编码 + 可选因果前缀均值 + 可学习 Lp 指数。"""

    def __init__(self, input_size: int, hidden_size: int, aggregate: bool, dropout: float = 0.1):
        super().__init__()
        self.agg = aggregate
        self.f = nn.Sequential(nn.Linear(input_size, hidden_size), nn.ReLU(), nn.Dropout(dropout))
        self.g = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size), nn.ReLU(), nn.Dropout(dropout)
        )
        self.o = nn.Linear(hidden_size, 1)
        self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

    @property
    def p(self) -> torch.Tensor:
        return torch.exp(self.p_log).clamp(1e-3, 1e3)

    def forward(self, x: torch.Tensor, m: torch.Tensor) -> torch.Tensor:
        h = self.f(x) * m.unsqueeze(-1)
        if self.agg:
            c = (torch.cumsum(h, 1) / torch.cumsum(m, 1).clamp(min=1.0).unsqueeze(-1)) * m.unsqueeze(-1)
        else:
            c = torch.zeros_like(h)
        return self.o(self.g(torch.cat([h, c], -1))).squeeze(-1)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="第三章定稿四格权重的逐流推理入口")
    ap.add_argument("--package-root", type=Path, required=True, help="归档包根目录（含 C00..C11 子目录）")
    ap.add_argument("--cell", choices=("C00", "C01", "C10", "C11"), required=True)
    ap.add_argument("--x-npy", type=Path, required=True, help="逐流特征矩阵 N×83")
    ap.add_argument("--index-npy", type=Path, required=True, help="序列索引 S×Lmax，元素是 X 的行号")
    ap.add_argument("--mask-npy", type=Path, required=True, help="序列掩码 S×Lmax")
    ap.add_argument("--out-npy", type=Path, required=True, help="输出逐流分数")
    ap.add_argument("--out-seen-npy", type=Path, default=None, help="可选：输出逐流覆盖掩码")
    ap.add_argument("--input-convention", choices=("standardized-cache", "raw"), required=True)
    ap.add_argument("--normalization-json", type=Path, default=None,
                    help="raw 约定必填：含 mean/std 两个长度 83 的列表")
    ap.add_argument("--batch-size", type=int, default=2048, help="序列批大小，默认与训练脚本一致")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return ap


def main() -> None:
    args = build_parser().parse_args()
    cfg = json.loads((args.package_root / args.cell / "config.json").read_text(encoding="utf-8"))
    arch = cfg["architecture"]
    input_size = int(arch["input_size"])
    seq_len = int(arch["sequence_length"])

    x = np.load(args.x_npy, allow_pickle=False).astype(np.float32, copy=False)
    idx = np.load(args.index_npy, allow_pickle=False)
    msk = np.load(args.mask_npy, allow_pickle=False).astype(np.float32, copy=False)
    if x.ndim != 2 or x.shape[1] != input_size:
        raise ValueError(f"X 形状应为 N×{input_size}，实为 {x.shape}")
    if idx.shape[:1] != msk.shape[:1] or idx.shape[1] < seq_len or msk.shape[1] < seq_len:
        raise ValueError(f"索引/掩码形状不匹配：{idx.shape} 与 {msk.shape}，至少需要 {seq_len} 列")

    if args.input_convention == "raw":
        if args.normalization_json is None:
            raise ValueError("--input-convention raw 必须同时给 --normalization-json")
        norm = json.loads(args.normalization_json.read_text(encoding="utf-8"))
        mean = np.asarray(norm["mean"], dtype=np.float32)
        std = np.asarray(norm["std"], dtype=np.float32)
        if mean.shape != (input_size,) or std.shape != (input_size,):
            raise ValueError(f"normalization mean/std 长度应为 {input_size}")
        x = x.copy()
        x[~np.isfinite(x)] = 0.0
        x = np.clip((x - mean) / std, -10, 10).astype(np.float32, copy=False)

    dev = torch.device(args.device)
    model = Model(input_size, int(arch["hidden_size"]), bool(cfg["cell"]["aggregate_enabled"]),
                  float(arch["dropout"])).to(dev)
    weights = load_file(str(args.package_root / args.cell / "weights.safetensors"), device=args.device)
    model.load_state_dict(weights)
    model.eval()

    gx = torch.from_numpy(x).to(dev)
    gi = torch.from_numpy(np.ascontiguousarray(idx)).to(dev)
    gm = torch.from_numpy(msk).to(dev)
    scores = torch.zeros(x.shape[0], device=dev)
    seen = torch.zeros(x.shape[0], dtype=torch.bool, device=dev)
    with torch.no_grad():
        for a in range(0, gi.shape[0], args.batch_size):
            bi = gi[a:a + args.batch_size][:, :seq_len]
            bm = gm[a:a + args.batch_size][:, :seq_len]
            b = bi.shape[0]
            pr = torch.sigmoid(model(gx[bi.reshape(-1)].reshape(b, seq_len, input_size), bm))
            fi = bi.reshape(-1)
            fm = bm.reshape(-1) > 0
            scores[fi[fm]] = pr.reshape(-1)[fm]
            seen[fi[fm]] = True

    out = scores.cpu().numpy()
    np.save(args.out_npy, out)
    seen_np = seen.cpu().numpy()
    if args.out_seen_npy is not None:
        np.save(args.out_seen_npy, seen_np)
    print(f"cell={args.cell} p={float(model.p.item()):.6f} "
          f"flows={out.size} covered={int(seen_np.sum())} "
          f"score_min={float(out[seen_np].min()):.8f} score_max={float(out[seen_np].max()):.8f} "
          f"score_mean={float(out[seen_np].mean()):.8f} -> {args.out_npy}")


if __name__ == "__main__":
    main()
