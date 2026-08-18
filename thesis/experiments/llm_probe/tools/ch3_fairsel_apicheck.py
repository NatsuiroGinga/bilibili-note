# -*- coding: utf-8 -*-
"""ch3_2x2_fairsel.py 用到的、相对 ch3_full.py 新增的 PyTorch 接口的运行时核验。

只做接口存在性与语义核验（构造给定真值），不产生任何科学结论、不注册运行身份。
核验项：
  1. torch.cuda.empty_cache 存在且可调用
  2. nn.Module.load_state_dict 能把 cuda state_dict 装回新建的同构 cuda 模型，且参数逐位相同
  3. torch.Generator().manual_seed(s) + torch.randint(generator=) 在相同 seed 下可复现
"""
import inspect

import numpy as np
import torch
import torch.nn as nn

print("torch", torch.__version__, "cuda", torch.cuda.is_available())

# 1
assert hasattr(torch.cuda, "empty_cache") and callable(torch.cuda.empty_cache)
print("empty_cache 签名:", inspect.signature(torch.cuda.empty_cache))
torch.cuda.empty_cache()
print("1 OK torch.cuda.empty_cache 存在且可调用")

# 2
print("load_state_dict 签名:", inspect.signature(nn.Module.load_state_dict))


class M(nn.Module):
    def __init__(self):
        super().__init__()
        self.f = nn.Linear(7, 5)
        self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

    @property
    def p(self):
        return torch.exp(self.p_log).clamp(1e-3, 1e3)


dev = "cuda" if torch.cuda.is_available() else "cpu"
a = M().to(dev)
with torch.no_grad():
    a.p_log.fill_(0.37)
snap = {k: v.detach().clone() for k, v in a.state_dict().items()}
b = M().to(dev)
ret = b.load_state_dict(snap)
print("load_state_dict 返回:", ret)
assert all(torch.equal(a.state_dict()[k], b.state_dict()[k]) for k in snap), "参数回载不一致"
assert abs(a.p.item() - b.p.item()) < 1e-12, "p_log 回载后派生量不一致"
assert all(v.device.type == dev for v in b.state_dict().values()), "回载后不在目标设备"
print(f"2 OK 快照回载逐位一致，p={b.p.item():.6f}，设备={dev}")

# 3
g1 = torch.Generator().manual_seed(42)
g2 = torch.Generator().manual_seed(42)
r1 = torch.randint(0, 1000, (64,), generator=g1).to(dev)
r2 = torch.randint(0, 1000, (64,), generator=g2).to(dev)
assert torch.equal(r1, r2), "同 seed 生成器不可复现"
print("3 OK torch.Generator + randint(generator=) 同 seed 可复现")
print("全部接口核验通过")
