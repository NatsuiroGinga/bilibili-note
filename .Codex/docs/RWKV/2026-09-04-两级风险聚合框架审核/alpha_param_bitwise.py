# -*- coding: utf-8 -*-
"""E3：把 α 注册成模型参数后，z1=0 四格臂能否与现有运行**逐位一致**（§四 第 2 项）。

两条独立风险，分开测：
  R1 控制器风险：g_flow / g_rank 各多出一个恒零坐标，c 与 combined 是否改变
  R2 RNG 风险：多注册一个参数是否移动权重初始化的随机数流
"""
import sys
import torch

sys.path.insert(0, "/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819/thesis/experiments/llm_probe/tools")
import ch3_ft_gradient_controller as C

print("=" * 78)
print("R1：多一个恒零坐标是否改变 c、combined、一阶不变量")
print("=" * 78)
torch.manual_seed(7)
P = 5000
g_f = torch.randn(P)
g_r = torch.randn(P) * 3.0
g_r -= 2.0 * g_f                                    # 造出负内积，逼投影分支

comb0, d0 = C.combine_gradients(g_f, g_r)
# α 在 z1=0 臂上 alpha=None ⟹ 尾部路径不启用 ⟹ α 收不到梯度 ⟹ 该坐标恒零
g_f1 = torch.cat([g_f, torch.zeros(1)])
g_r1 = torch.cat([g_r, torch.zeros(1)])
comb1, d1 = C.combine_gradients(g_f1, g_r1)

print(f"  c        : {d0['c_scaling']!r}  →  {d1['c_scaling']!r}   相同={d0['c_scaling']==d1['c_scaling']}")
print(f"  内积     : {d0['inner_product']!r}  →  {d1['inner_product']!r}   相同={d0['inner_product']==d1['inner_product']}")
print(f"  ‖g_r^+‖  : {d0['grad_norm_rank_projected']!r}  →  {d1['grad_norm_rank_projected']!r}")
print(f"  投影触发 : {d0['projection_triggered']} → {d1['projection_triggered']}")
print(f"  ** 前 P 个坐标逐位相同 = {bool(torch.equal(comb0, comb1[:P]))} **")
print(f"  ** 新增坐标的合成梯度 = {float(comb1[P])!r}（应精确为 0） **")

print()
print("=" * 78)
print("R2：注册顺序对权重初始化随机数流的影响")
print("=" * 78)


def build(with_alpha_before):
    torch.manual_seed(1234)
    mods = {}
    if with_alpha_before == "randn_before":
        mods["alpha"] = torch.nn.Parameter(torch.randn(()))     # 消耗 RNG
    lin = torch.nn.Linear(16, 8)
    if with_alpha_before == "const_after":
        mods["alpha"] = torch.nn.Parameter(torch.tensor(0.5))   # 不消耗 RNG
    return lin.weight.detach().clone(), mods


w_base, _ = build("none")
w_const, _ = build("const_after")
w_randn, _ = build("randn_before")
print(f"  基线（无 α）与「常量 α，构造在后」权重逐位相同 = {bool(torch.equal(w_base, w_const))}")
print(f"  基线（无 α）与「randn α，构造在前」权重逐位相同 = {bool(torch.equal(w_base, w_randn))}")
print("  ⟹ α 必须用**不消耗随机数**的常量初始化；否则 z1=0 臂的权重初始化整体平移，")
print("     四格逐位断言必然失败，而失败信号与 α 本身无关，极难归因。")

print()
print("=" * 78)
print("R3：Adam 在梯度恒为 0 的参数上是否仍会移动它")
print("=" * 78)
a = torch.nn.Parameter(torch.tensor(0.5))
opt = torch.optim.Adam([a], lr=1e-2)
for _ in range(50):
    opt.zero_grad(set_to_none=True)
    a.grad = torch.zeros_like(a)
    opt.step()
print(f"  50 步梯度恒 0 后 α = {float(a)!r}，位移 = {float(a) - 0.5!r}")
a2 = torch.nn.Parameter(torch.tensor(0.5))
opt2 = torch.optim.Adam([a2], lr=1e-2)
seq = []
for step in range(50):
    opt2.zero_grad(set_to_none=True)
    a2.grad = torch.tensor(-1.0) if step % 10 == 0 else torch.zeros(())   # 每 10 步才有一次信号
    opt2.step()
    seq.append(float(a2))
print(f"  每 10 步给一次 grad=-1（模拟 c=0 占空比 0.9），50 步后 α = {seq[-1]:.6f}，位移 = {seq[-1]-0.5:+.6f}")
