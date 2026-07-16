#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验 v7：真正 autodiff PINN（I1 连续性方程，CI-PRD 核心）
目的：v6 的 numpy 约束只是 proxy；本脚本用 torch.autograd 真正实现 PINN——
      NN 拟合流量密度 ρ(x,t)，损失含连续性方程残差 ∂ρ/∂t + u·∂ρ/∂x = s（autodiff 求），
      残差幅值作异常得分，定位"破坏守恒的源"（DDoS 注入点）。
数据（合成连续性场，证明机制；后续换测试床实测 ρ）：
  - 正常：平流高斯包 ρ=f(x-u·t)，满足 ∂ρ/∂t+u·∂ρ/∂x=0（无源 s=0）。
  - 攻击：在 (x0=0.7, t0=0.5) 注入局部 DDoS 源 → 该处 ρ 偏离无源连续性，残差应尖峰。
方法：NN ρ_θ(x,t)；L = MSE(ρ_θ,ρ_data) + λ·MSE(residual,0)，residual=∂ρ_θ/∂t+u·∂ρ_θ/∂x（autodiff）。
检测：训练后在网格上算 residual，峰值位置 vs 真实注入点；攻击处残差 vs 正常处。
依赖：torch（MPS）。运行：uv run python ciprd_pinn_autodiff.py
"""
import os
import numpy as np
import torch
import torch.nn as nn

torch.manual_seed(42); np.random.seed(42)
DEV = 'mps' if torch.backends.mps.is_available() else 'cpu'
U = 0.5            # 平流速度
X0, T0 = 0.7, 0.5  # 真实 DDoS 注入点

def rho_field(x, t, attack=True):
    """正常=平流高斯包(s=0)；攻击=叠加局部源注入。"""
    rho = torch.exp(-((x - U*t - 0.5)**2) / 0.02)   # 平流包，满足 ∂ρ/∂t+u∂ρ/∂x=0
    if attack:
        rho = rho + 1.5 * torch.exp(-((x - X0)**2 + (t - T0)**2) / 0.01)  # DDoS 源注入
    return rho

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
    return rt + U * rx   # 连续性残差（s=0 假设）

def main():
    # 采样点
    N = 2000
    x = torch.rand(N,1, device=DEV); t = torch.rand(N,1, device=DEV)
    rho = rho_field(x, t, attack=True)  # 含攻击的训练数据
    model = PINN().to(DEV)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    lam = 0.1  # 物理约束权重（moderate：让模型拟合数据同时残差暴露违反）
    for ep in range(2000):
        opt.zero_grad()
        rho_p = model(x, t)
        res = residual(model, x, t)
        loss = ((rho_p - rho)**2).mean() + lam * (res**2).mean()
        loss.backward(); opt.step()
        if ep % 500 == 0:
            print(f"  ep{ep}: loss={loss.item():.5f} data={((rho_p-rho)**2).mean().item():.5f} res={(res**2).mean().item():.5f}")
    # 检测：网格上算残差，找峰值
    gx = torch.linspace(0,1,50, device=DEV); gt = torch.linspace(0,1,50, device=DEV)
    XM, TM = torch.meshgrid(gx, gt, indexing='ij')
    xs = XM.reshape(-1,1); ts = TM.reshape(-1,1)
    with torch.no_grad():
        # 残差需 autodiff，不能 no_grad
        pass
    res = residual(model, xs, ts).detach().reshape(50,50)
    res_np = np.abs(res.cpu().numpy())   # 用 |残差|（高斯注入残差在斜坡最大、中心为0，数学预期）
    gxn, gtn = gx.cpu().numpy(), gt.cpu().numpy()
    # 注入邻域（半径0.15内）|残差| 均值 vs 远区（距注入>0.3）|残差| 均值
    dist = np.sqrt((XM.cpu().numpy()-X0)**2 + (TM.cpu().numpy()-T0)**2)
    near = res_np[dist < 0.15].mean()
    far = res_np[dist > 0.3].mean()
    peak = res_np.max()
    peak_idx = np.unravel_index(np.argmax(res_np), res_np.shape)
    print(f"\n真实 DDoS 注入点: ({X0},{T0})")
    print(f"|残差|峰值={peak:.4f} @ ({gx[peak_idx[0]]:.2f},{gt[peak_idx[1]]:.2f})（高斯斜坡处，预期）")
    print(f"注入邻域|残差|均值={near:.4f} | 远区|残差|均值={far:.4f} | 倍数={near/max(far,1e-6):.1f}x")
    print(f"检测: {'✅ 注入邻域残差显著高于远区（autodiff PINN 暴露守恒破坏）' if near > 3*far else '⚠️ 邻域残差未显著高于远区'}")

if __name__ == '__main__':
    main()
