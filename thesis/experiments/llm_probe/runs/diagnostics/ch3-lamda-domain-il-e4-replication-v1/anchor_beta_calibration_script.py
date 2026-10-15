"""锚定系数 β 标定（源侧两年短程诊断，2026-10-15）。

目的：FOREVER 的 β_base 名义 1e-3 是其 LLM 短回放场景的量级对齐结果；
本协议回放与当前年混合训练 10 轮、全程作用，须在本数据上重标量级。
原则（跑前冻结）：取 β 使「β·锚定项 / 数据损失」的轮均比值最接近 0.1。

流程：2013 训练（无调度无锚，等价正式臂首年）→ 以 2013 末权重为 Θ*，
2014 年 rho 调度（cap8、a*=0.99091）+ 锚定 β，打印每轮 [anchor] ratio。
每档 β 完整重跑 2013→2014（25 s/档），避免跨档状态串扰。
只读 train 分片（源年 2013/2014），不读任何测试分片，不接触封印年。
"""
import sys

import numpy as np
import torch

sys.path.insert(0, "/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908/thesis/experiments/llm_probe/tools")
import ch3_lamda_domain_il_e4 as e4  # noqa: E402

BETAS = [5e-3]   # 首轮三档 {1e-4,1e-3,1e-2} 已测：ratio 0.003/0.029/0.174，0.1 落在 1e-3 与 1e-2 之间，按对数插值补测 5e-3


def run_once(beta: float) -> None:
    torch.manual_seed(42)
    rng = np.random.default_rng(42)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    x13, y13 = e4.load_year(2013, "train")
    x14, y14 = e4.load_year(2014, "train")
    model = e4.ChenEncoderMLP(x13.shape[1]).to(device)
    # 首年：无调度、无锚定（与正式臂 2013 年语义一致）
    e4.train_epochs(model, [(x13, y13)], e4.OFFICIAL_EPOCHS, e4.OFFICIAL_BATCH,
                    e4.OFFICIAL_LR, device, rng)
    theta_star = [p.detach().clone() for p in model.parameters()]
    buf = e4.ReplayBuffer(e4.OFFICIAL_MEMORY)
    buf.add_batch(x13, y13, 2013)
    xb, yb = buf.sample()
    blk = (xb.astype(np.int8), yb.astype(np.float32))
    print(f"\n===== beta={beta:g} =====", flush=True)
    e4.train_epochs(model, [(x14, y14), blk], e4.OFFICIAL_EPOCHS, e4.OFFICIAL_BATCH,
                    e4.OFFICIAL_LR, device, rng,
                    rho_sched=(blk, (x14, y14), 0.99091, 8, 0.0),
                    l2_beta=beta, theta_star=theta_star)


if __name__ == "__main__":
    for b in BETAS:
        run_once(b)
