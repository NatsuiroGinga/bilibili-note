#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验 v8：PINN 在 ns-3 测试床数据上（CI-PRD 真实数据验证）
目的：v7 用合成 1-D 高斯数据证机制；本脚本在 ns-3 仿真产出的真实拓扑 ρ(node,t) 上验证
      autodiff PINN 残差检测 DDoS 注入，并对比 ns-3 ground-truth I1 残差（|in-out|）。
数据：ns3_testbed.cc 产出的 CSV（x_position, t, rho, i1_residual），7 节点 × 20 窗口。
方法：复用 v7 PINN 架构（MLP(2,64,64,1) + autodiff 连续性残差），数据源换为 ns-3 CSV。
      L = MSE(ρ_θ, ρ_data) + λ·MSE(∂ρ/∂t + U·∂ρ/∂x, 0)
检测：注入邻域(x≈0.7, t≈5) |残差| vs 远区 |残差|；PINN 残差 vs ground-truth I1 残差相关性。
依赖：torch(MPS), pandas, swanlab。运行：uv run python pinn_testbed.py [--data path]
"""
import os, argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import swanlab

torch.manual_seed(42); np.random.seed(42)
DEV = 'mps' if torch.backends.mps.is_available() else 'cpu'
U = 0.5            # 平流速度（与 v7 一致）
EPOCHS = 3000
LAM = 0.1
ATTACK_X, ATTACK_T = 0.7, 5.0  # ns-3 DDoS 注入点（SV1, t=5s）

class PINN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(2,64), nn.Tanh(), nn.Linear(64,64), nn.Tanh(), nn.Linear(64,1))
    def forward(self, x, t):
        return self.net(torch.cat([x, t], dim=1))

def residual(model, x, t):
    x = x.requires_grad_(True); t = t.requires_grad_(True)
    rho = model(x, t)
    rt = torch.autograd.grad(rho, t, torch.ones_like(rho), create_graph=True)[0]
    rx = torch.autograd.grad(rho, x, torch.ones_like(rho), create_graph=True)[0]
    return rt + U * rx

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default=os.path.join(os.path.dirname(__file__), 'data/testbed_rho.csv'))
    args = parser.parse_args()

    # ===== 读 ns-3 数据 =====
    df = pd.read_csv(args.data)
    print(f"读取 ns-3 数据: {len(df)} 行, 节点数={df['x'].nunique()}, 时间步={df['t'].nunique()}")
    print(f"  x 范围: {df['x'].min():.1f}-{df['x'].max():.1f}, t 范围: {df['t'].min():.1f}-{df['t'].max():.1f}")
    print(f"  ρ 范围: {df['rho'].min():.0f}-{df['rho'].max():.0f}")
    print(f"  I1 残差范围: {df['i1_residual'].min():.0f}-{df['i1_residual'].max():.0f}")

    # 归一化 t 到 [0,1] + ρ 归一化到 [0,1]（避免数据损失淹没物理损失）
    t_max = df['t'].max()
    rho_max = df['rho'].max() + 1e-8
    x = torch.tensor(df['x'].values, dtype=torch.float32, device=DEV).reshape(-1,1)
    t = torch.tensor(df['t'].values / t_max, dtype=torch.float32, device=DEV).reshape(-1,1)
    rho = torch.tensor(df['rho'].values / rho_max, dtype=torch.float32, device=DEV).reshape(-1,1)
    i1_gt = df['i1_residual'].values  # ground truth I1 残差（未归一化）

    # ===== PINN 训练 =====
    model = PINN().to(DEV)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    run = swanlab.init(
        project="ci-prd-pinn", name="v8-testbed-ns3",
        description="PINN 在 ns-3 测试床数据上：autodiff 残差检测 DDoS + 对比 ground-truth I1",
        config={"U": U, "attack_point": [ATTACK_X, ATTACK_T], "epochs": EPOCHS, "lambda": LAM,
                "device": DEV, "data_source": "ns-3", "n_samples": len(df)},
        mode="online",
    )
    for ep in range(EPOCHS):
        opt.zero_grad()
        rho_p = model(x, t)
        res = residual(model, x, t)
        data_loss = ((rho_p - rho)**2).mean()
        res_loss = (res**2).mean()
        loss = data_loss + LAM * res_loss
        loss.backward(); opt.step()
        if ep % 300 == 0:
            swanlab.log({"loss": loss.item(), "data_loss": data_loss.item(),
                         "res_loss": res_loss.item()}, step=ep)
            print(f"  ep{ep}: loss={loss.item():.5f} data={data_loss.item():.5f} res={res_loss.item():.5f}")

    # ===== 检测：网格上算残差 =====
    gx = torch.linspace(0, 1, 50, device=DEV)
    gt = torch.linspace(0, 1, 50, device=DEV)
    XM, TM = torch.meshgrid(gx, gt, indexing='ij')
    xs = XM.reshape(-1,1); ts = TM.reshape(-1,1)
    res = residual(model, xs, ts).detach()
    res_np = np.abs(res.cpu().numpy().reshape(50,50))

    # 注入邻域 vs 远区
    gxn, gtn = gx.cpu().numpy(), gt.cpu().numpy()
    dist = np.sqrt((XM.cpu().numpy() - ATTACK_X)**2 + (TM.cpu().numpy() - ATTACK_T/t_max)**2)
    near = res_np[dist < 0.2].mean()
    far = res_np[dist > 0.4].mean()
    peak = res_np.max()
    peak_idx = np.unravel_index(np.argmax(res_np), res_np.shape)

    print(f"\n真实 DDoS 注入: (x={ATTACK_X}, t={ATTACK_T}s → t_norm={ATTACK_T/t_max:.2f})")
    print(f"|残差|峰值={peak:.4f} @ ({gx[peak_idx[0]]:.2f},{gt[peak_idx[1]]:.2f})")
    print(f"注入邻域|残差|均值={near:.4f} | 远区={far:.4f} | 倍数={near/max(far,1e-6):.1f}x")
    det = near > 3 * far
    print(f"检测: {'✅ PINN 残差在注入邻域显著高于远区' if det else '⚠️ 未显著'}")

    # ===== 对比 PINN 残差 vs ns-3 ground-truth I1 残差 =====
    # 在数据点上算 PINN 残差
    res_at_data = np.abs(residual(model, x, t).detach().cpu().numpy().flatten())
    corr = np.corrcoef(res_at_data, i1_gt)[0, 1] if np.std(res_at_data) > 0 and np.std(i1_gt) > 0 else 0
    print(f"\nPINN 残差 vs ns-3 I1 ground-truth 相关性: Pearson r={corr:.3f}")
    print(f"  (r>0.5 表示 PINN 残差与真实守恒破坏一致)")

    swanlab.log({"near_res": float(near), "far_res": float(far),
                 "res_ratio": float(near / max(far, 1e-6)),
                 "peak_res": float(peak), "detected": int(det),
                 "i1_corr": float(corr)})
    swanlab.finish()

if __name__ == '__main__':
    main()
