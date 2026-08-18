# -*- coding: utf-8 -*-
"""只读诊断：判定「打包批前向 vs 逐条截断前向」的 2.4e-4 差异来自 TF32 精度还是掩码错误。

可证伪假设：该差异是 cuDNN RNN 在 RTX 5090 上默认启用 TF32（10 位尾数）所致，
与补零位是否污染状态无关。
预测：关闭 TF32 后同一比较的最大绝对差应降到 1e-5 量级以下。

三条对照，一次只改一个变量：
  A 打包批 vs 逐条截断单独前向        —— 跨内核路径，TF32 开 / 关各测一次
  B 打包批 vs 不打包的补零满批前向    —— 数学上真实位应完全相同（补零只在尾部）
  C 打包批重复两次                    —— 同一路径的可重复性下界
不训练、不评价、不写盘、不创建运行身份。
"""

import numpy as np
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe"
CACHE = f"{ROOT}/runs/diagnostics/dijk-repro/cache"
L, D, HID, SEED = 128, 83, 111, 42

dev = "cuda"
X23 = np.load(f"{CACHE}/X23.npy", mmap_mode="r")
I23 = np.load(f"{CACHE}/I23.npy")
M23 = np.load(f"{CACHE}/M23.npy")

# 取一批既有补零又有满长的序列
lens_all = M23.sum(1)
pick = np.concatenate([np.flatnonzero(lens_all < L)[:32], np.flatnonzero(lens_all == L)[:32]])
idx = I23[pick]
msk = torch.from_numpy(M23[pick]).to(dev)
xb = torch.from_numpy(np.asarray(X23[idx.reshape(-1)], np.float32)).reshape(64, L, D).to(dev)
lens = msk.sum(1).to(torch.int64).clamp(min=1)
print(f"批 64 条：真实长度 最小 {int(lens.min())} 最大 {int(lens.max())} "
      f"含补零 {int((lens < L).sum())} 条")

torch.manual_seed(SEED)
gru = nn.GRU(D, HID, num_layers=1, bias=True, batch_first=True).to(dev).eval()


def packed_fwd():
    p = pack_padded_sequence(xb, lens.cpu(), batch_first=True, enforce_sorted=False)
    o, _ = gru(p)
    h, _ = pad_packed_sequence(o, batch_first=True, total_length=L)
    return h * msk.unsqueeze(-1)


def padded_fwd():
    """不打包，直接把含补零的满批喂进 GRU，再掩码。补零只在尾部，真实位数学上应相同。"""
    o, _ = gru(xb)
    return o * msk.unsqueeze(-1)


def truncated_maxdiff(href):
    w = 0.0
    for i in range(64):
        n = int(lens[i])
        s, _ = gru(xb[i:i + 1, :n, :])
        w = max(w, (s[0] - href[i, :n]).abs().max().item())
    return w


with torch.no_grad():
    for tf32 in (True, False):
        torch.backends.cudnn.allow_tf32 = tf32
        torch.backends.cuda.matmul.allow_tf32 = tf32
        h_pk = packed_fwd()
        a = truncated_maxdiff(h_pk)
        b = (padded_fwd() - h_pk).abs().max().item()
        c = (packed_fwd() - h_pk).abs().max().item()
        print(f"TF32={'开' if tf32 else '关'}  "
              f"A 打包vs逐条截断={a:.3e}  "
              f"B 打包vs补零满批={b:.3e}  "
              f"C 打包重复两次={c:.3e}")

    # 决定性检验：补零位输入换成 1e3 噪声，真实位输出是否逐位不变（与 TF32 无关）
    torch.backends.cudnn.allow_tf32 = True
    torch.backends.cuda.matmul.allow_tf32 = True
    h0 = packed_fwd()
    pad = (msk < 0.5).unsqueeze(-1)
    xb_bak = xb.clone()
    xb.copy_(torch.where(pad, torch.randn_like(xb) * 1e3, xb))
    h1 = packed_fwd()
    xb.copy_(xb_bak)
    print(f"决定性 补零位输入改 1e3 噪声后真实位最大差={(h1 - h0).abs().max().item():.3e}（应为 0）")
