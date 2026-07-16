#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验 v6：CI-PRD 物理约束模型——不变量作软约束损失（v5 证明"加特征"无效，需约束）
目的：真正测 CI-PRD 式"物理信息"——把守恒不变量违反度作损失软约束，强迫模型遵守物理。
对比 v5：特征叠加(MLP_inv)失败 → 改约束损失是否能在 OOD 上接近/超过朴素阈值。
模型（numpy 梯度下降逻辑回归）：
  损失 L = BCE(y, p) + λ · mean[ max(0, v - p) ]
  v = 不变量违反度 ∈[0,1]（I2 偏离双向平衡 + I3 单向SYN）
  约束项：不变量强违反(v高)时若模型预测 p 低(判良性)则惩罚 → 逼模型在物理违反时判攻击
OOD：训 Wed-21 DDoS → 测 Wed-14 暴力破解（未见攻击类型）
依赖：numpy, pandas, scikit-learn（scaler）。运行：uv run python ciprd_constrained.py
"""
import os, warnings
import numpy as np
import pandas as pd
import swanlab
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, precision_score, recall_score

warnings.filterwarnings("ignore")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
D = os.path.join(REPO, 'raw/datasets/CSE-CIC-IDS2018')
TRAIN_FILE = f'{D}/Wednesday-21-02-2018_TrafficForML_CICFlowMeter.csv'
OOD_FILE   = f'{D}/Wednesday-14-02-2018_TrafficForML_CICFlowMeter.csv'
MAX_PER_CLASS = 15000
DROP = ['Dst Port', 'Protocol', 'Timestamp', 'Label']

def load(path, mpc):
    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip()
    df = df[df['Label'].str.strip() != 'Label']
    df['Label'] = df['Label'].str.strip()
    y = (df['Label'] != 'Benign').astype(int).values
    tf = pd.to_numeric(df['TotLen Fwd Pkts'], errors='coerce').fillna(0)
    tb = pd.to_numeric(df['TotLen Bwd Pkts'], errors='coerce').fillna(0)
    pb = pd.to_numeric(df['Tot Bwd Pkts'], errors='coerce').fillna(0)
    syn = pd.to_numeric(df['SYN Flag Cnt'], errors='coerce').fillna(0)
    i2 = (tf / (tf + tb + 1.0)).values
    i3 = ((syn > 0) & (pb == 0)).astype(float).values
    v = np.clip(np.abs(2 * i2 - 1), 0, 1)   # 不变量违反度：0=双向平衡,1=完全单向
    v = np.maximum(v, i3)                    # 叠加 I3 单向 SYN
    num = df.drop(columns=[c for c in DROP if c in df.columns], errors='ignore')
    X = num.apply(pd.to_numeric, errors='coerce').replace([np.inf, -np.inf], np.nan).fillna(0).values
    idx = []
    for c in [0, 1]:
        ic = np.where(y == c)[0]
        if len(ic) > mpc:
            ic = np.random.RandomState(42).choice(ic, mpc, replace=False)
        idx.extend(ic)
    idx = np.array(idx)
    return X[idx], v[idx], y[idx]

def sigmoid(z): return 1 / (1 + np.exp(-np.clip(z, -30, 30)))

def train_constrained(X, v, y, lam, lr=0.1, epochs=300):
    """逻辑回归 + 物理约束损失。L = BCE + λ·mean[max(0, v-p)]"""
    n, d = X.shape
    w = np.zeros(d); b = 0.0
    for _ in range(epochs):
        z = X @ w + b; p = sigmoid(z)
        # BCE 梯度
        grad_z = (p - y) / n
        # 约束项梯度：v > p 时 dL/dp = -λ/n → 促 p 升
        mask = (v > p).astype(float)
        grad_z += lam * (-mask) / n
        w -= lr * (X.T @ grad_z)
        b -= lr * grad_z.sum()
    return w, b

def train_plain(X, y, lr=0.1, epochs=300):
    return train_constrained(X, np.zeros(len(y)), y, lam=0.0, lr=lr, epochs=epochs)

def metrics(y, p):
    return dict(F1=f1_score(y, p, zero_division=0), Prec=precision_score(y, p, zero_division=0),
                Rec=recall_score(y, p, zero_division=0),
                FPR=((p == 1) & (y == 0)).sum() / max((y == 0).sum(), 1))

def main():
    np.random.seed(42)
    Xtr, vtr, ytr = load(TRAIN_FILE, MAX_PER_CLASS)
    Xoo, voo, yoo = load(OOD_FILE, MAX_PER_CLASS)
    sc = StandardScaler().fit(Xtr)
    Xtr_s, Xoo_s = sc.transform(Xtr), sc.transform(Xoo)
    print(f"训练 {len(ytr)} 行(攻击{ytr.mean():.0%}) | OOD {len(yoo)} 行(攻击{yoo.mean():.0%})")
    print(f"\n{'模型':<26}{'F1':>7}{'Prec':>7}{'Recall':>8}{'FPR':>8}  说明")
    print('-'*72)
    swanlab.init(project="ci-prd-pinn", name="v6-constrained-lr",
                 description="v6: 物理约束 LR（不变量作软约束损失，CI-PRD proxy）",
                 config={"train":"Wed-21 DDoS","ood":"Wed-14 暴力破解","max_per_class":MAX_PER_CLASS}, mode="online")
    # 1 纯数据驱动 LR（无物理）
    w, b = train_plain(Xtr_s, ytr); p = (sigmoid(Xoo_s @ w + b) > 0.5).astype(int)
    m = metrics(yoo, p); print(f"{'LR_纯数据驱动':<26}{m['F1']:>7.3f}{m['Prec']:>7.3f}{m['Rec']:>8.3f}{m['FPR']:>8.3f}  无物理")
    swanlab.log({"LR_纯数据驱动/F1": m['F1'], "LR_纯数据驱动/FPR": m['FPR']})
    # 2 物理约束 LR（CI-PRD proxy），不同 λ
    for lam in [0.5, 1.0, 2.0]:
        w, b = train_constrained(Xtr_s, vtr, ytr, lam=lam); p = (sigmoid(Xoo_s @ w + b) > 0.5).astype(int)
        m = metrics(yoo, p); print(f"{'LR_物理约束(λ=%.1f)'%lam:<26}{m['F1']:>7.3f}{m['Prec']:>7.3f}{m['Rec']:>8.3f}{m['FPR']:>8.3f}  CI-PRD proxy")
        swanlab.log({f"LR_物理约束λ{lam}/F1": m['F1'], f"LR_物理约束λ{lam}/FPR": m['FPR']})
    # 3 朴素 I2/I3 阈值（参照，v5/v3）
    p_thr = (voo > 0.9).astype(int)   # 不变量强违反 → 攻击
    m = metrics(yoo, p_thr); print(f"{'不变量硬阈值(参照)':<26}{m['F1']:>7.3f}{m['Prec']:>7.3f}{m['Rec']:>8.3f}{m['FPR']:>8.3f}  物理硬阈值")
    swanlab.log({"不变量硬阈值/F1": m['F1'], "不变量硬阈值/FPR": m['FPR']})
    # 4 同分布 sanity
    from sklearn.model_selection import train_test_split
    Xa, Xb, va, vb, ya, yb = train_test_split(Xtr_s, vtr, ytr, test_size=0.3, random_state=42, stratify=ytr)
    w, b = train_constrained(Xa, va, ya, lam=1.0); p = (sigmoid(Xb @ w + b) > 0.5).astype(int)
    m = metrics(yb, p); print(f"\n同分布 sanity LR_物理约束: F1={m['F1']:.3f} Recall={m['Rec']:.3f} FPR={m['FPR']:.3f}")
    swanlab.log({"indist/F1": m['F1'], "indist/FPR": m['FPR']})
    swanlab.finish()

if __name__ == '__main__':
    main()
