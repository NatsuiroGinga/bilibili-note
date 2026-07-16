#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验 v5：CI-PRD（物理信息）对比基线——验证"物理信息 > 纯数据驱动 > 朴素阈值"
目的：补 v1-v4 未实证的推断——守恒不变量作特征/约束是否真能提升检测与 OOD 泛化。
设计（OOD 泛化检验）：
  训练：Wednesday-21-02（DDoS HOIC）Benign + DDoS
  OOD 测试：Wednesday-14-02（FTP/SSH 暴力破解，训练时未见的攻击类型）
  假设：+守恒不变量特征的模型，因"单向流"这一物理信号跨 DDoS/暴力破解共享，
        OOD 泛化优于只记 DDoS 原始特征的纯数据驱动模型。
对比：
  - 朴素 I2 阈值（v3 同款，参照）
  - LogReg_raw / LogReg_inv（原始特征 / +不变量特征）
  - MLP_raw / MLP_inv
诚实定位：流级数据的"物理信息"操作化为守恒不变量特征（I2/I3）——非 autodiff PDE 残差
  （autodiff PINN 是 I1/测试床场景）。本实验是 CI-PRD 物理信息优势的可行性 proxy。
依赖：pandas, scikit-learn（uv 环境）。运行：uv run python ciprd_vs_baselines.py
"""
import os, warnings
import numpy as np
import pandas as pd
import swanlab
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, precision_score, recall_score

warnings.filterwarnings("ignore")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
D = os.path.join(REPO, 'raw/datasets/CSE-CIC-IDS2018')
TRAIN_FILE = f'{D}/Wednesday-21-02-2018_TrafficForML_CICFlowMeter.csv'   # DDoS HOIC
OOD_FILE   = f'{D}/Wednesday-14-02-2018_TrafficForML_CICFlowMeter.csv'   # 暴力破解
MAX_PER_CLASS = 15000   # 每类上限（提速）
INV_COLS = ['TotLen Fwd Pkts', 'TotLen Bwd Pkts', 'Tot Bwd Pkts', 'SYN Flag Cnt']
DROP = ['Dst Port', 'Protocol', 'Timestamp', 'Label']

def load(path, max_per_class):
    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip()
    df = df[df['Label'].str.strip() != 'Label']  # 去散落表头行
    df['Label'] = df['Label'].str.strip()
    df['y'] = (df['Label'] != 'Benign').astype(int)
    # 不变量特征
    tf = pd.to_numeric(df['TotLen Fwd Pkts'], errors='coerce').fillna(0)
    tb = pd.to_numeric(df['TotLen Bwd Pkts'], errors='coerce').fillna(0)
    pb = pd.to_numeric(df['Tot Bwd Pkts'], errors='coerce').fillna(0)
    syn = pd.to_numeric(df['SYN Flag Cnt'], errors='coerce').fillna(0)
    df['I2'] = tf / (tf + tb + 1.0)
    df['I3'] = ((syn > 0) & (pb == 0)).astype(int)
    # 原始数值特征
    num = df.drop(columns=[c for c in DROP if c in df.columns] + ['I2', 'I3', 'y'], errors='ignore')
    Xraw = num.apply(pd.to_numeric, errors='coerce').replace([np.inf, -np.inf], np.nan).fillna(0)
    Xinv = Xraw.copy(); Xinv['I2'] = df['I2']; Xinv['I3'] = df['I3']
    y = df['y'].values
    # 平衡子采样
    idx = []
    for c in [0, 1]:
        ic = np.where(y == c)[0]
        if len(ic) > max_per_class:
            ic = np.random.RandomState(42).choice(ic, max_per_class, replace=False)
        idx.extend(ic)
    idx = np.array(idx)
    return Xraw.iloc[idx].reset_index(drop=True), Xinv.iloc[idx].reset_index(drop=True), y[idx]

def metrics(y, p):
    return dict(F1=f1_score(y, p, zero_division=0),
                Prec=precision_score(y, p, zero_division=0),
                Rec=recall_score(y, p, zero_division=0),
                FPR=((p == 1) & (y == 0)).sum() / max((y == 0).sum(), 1))

def main():
    np.random.seed(42)
    print("加载训练集 (Wed-21 DDoS HOIC)...")
    Xraw_tr, Xinv_tr, y_tr = load(TRAIN_FILE, MAX_PER_CLASS)
    print(f"  训练: {len(y_tr)} 行, 攻击占比 {y_tr.mean():.2%}")
    print("加载 OOD 测试集 (Wed-14 暴力破解)...")
    Xraw_oo, Xinv_oo, y_oo = load(OOD_FILE, MAX_PER_CLASS)
    print(f"  OOD: {len(y_oo)} 行, 攻击占比 {y_oo.mean():.2%}")

    # 标准化（fit on train）
    sc_raw = StandardScaler().fit(Xraw_tr)
    sc_inv = StandardScaler().fit(Xinv_tr)

    models = {
        'LogReg_raw': (LogisticRegression(max_iter=1000), sc_raw.transform(Xraw_tr), sc_raw.transform(Xraw_oo), 'raw'),
        'LogReg_inv': (LogisticRegression(max_iter=1000), sc_inv.transform(Xinv_tr), sc_inv.transform(Xinv_oo), 'inv'),
        'MLP_raw': (MLPClassifier(hidden_layer_sizes=(64,32), max_iter=40, random_state=42), sc_raw.transform(Xraw_tr), sc_raw.transform(Xraw_oo), 'raw'),
        'MLP_inv': (MLPClassifier(hidden_layer_sizes=(64,32), max_iter=40, random_state=42), sc_inv.transform(Xinv_tr), sc_inv.transform(Xinv_oo), 'inv'),
    }

    print("\n=== OOD 测试（训 DDoS → 测暴力破解，未见攻击类型）===")
    print(f"{'模型':<14}{'F1':>7}{'Precision':>10}{'Recall':>8}{'FPR':>8}  物理?")
    print('-'*55)
    swanlab.init(project="ci-prd-pinn", name="v5-feature-vs-baseline",
                 description="v5: 纯数据驱动 vs +不变量特征 vs 朴素阈值（OOD）",
                 config={"train":"Wed-21 DDoS","ood":"Wed-14 暴力破解","max_per_class":MAX_PER_CLASS}, mode="online")
    for name, (m, Xtr, Xoo, tag) in models.items():
        m.fit(Xtr, y_tr)
        p = m.predict(Xoo)
        mt = metrics(y_oo, p)
        print(f"{name:<14}{mt['F1']:>7.3f}{mt['Prec']:>10.3f}{mt['Rec']:>8.3f}{mt['FPR']:>8.3f}  {'+不变量' if tag=='inv' else '否'}")
        swanlab.log({f"{name}/F1": mt['F1'], f"{name}/Precision": mt['Prec'],
                     f"{name}/Recall": mt['Rec'], f"{name}/FPR": mt['FPR']})

    # 朴素 I2 阈值（参照）
    i2_oo = Xinv_oo['I2'].values
    p_thr = ((i2_oo > 0.95) | (i2_oo < 0.05)).astype(int)
    mt = metrics(y_oo, p_thr)
    print(f"{'I2阈值(参照)':<14}{mt['F1']:>7.3f}{mt['Prec']:>10.3f}{mt['Rec']:>8.3f}{mt['FPR']:>8.3f}  +不变量(硬阈值)")
    swanlab.log({"I2阈值/F1": mt['F1'], "I2阈值/Recall": mt['Rec'], "I2阈值/FPR": mt['FPR']})

    # 同分布测试（训 DDoS → 测 DDoS held-out， sanity）
    print("\n=== 同分布 sanity（训 Wed-21 → 测 Wed-21 同分布）===")
    from sklearn.model_selection import train_test_split
    Xa, Xb, ya, yb = train_test_split(sc_inv.transform(Xinv_tr), y_tr, test_size=0.3, random_state=42, stratify=y_tr)
    m = MLPClassifier(hidden_layer_sizes=(64,32), max_iter=40, random_state=42).fit(Xa, ya)
    mt = metrics(yb, m.predict(Xb))
    print(f"MLP_inv 同分布: F1={mt['F1']:.3f} Recall={mt['Rec']:.3f} FPR={mt['FPR']:.3f}")
    swanlab.log({"indist/F1": mt['F1'], "indist/Recall": mt['Rec'], "indist/FPR": mt['FPR']})
    swanlab.finish()

if __name__ == '__main__':
    main()
