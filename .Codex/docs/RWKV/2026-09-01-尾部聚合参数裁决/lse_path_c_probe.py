# -*- coding: utf-8 -*-
"""路径 C（LSE 软聚合，τ 可学）数值核验：稳定性、极限、τ 梯度、尺度耦合、编译。

合成输入 + 构造真值，CPU，不创建任何运行身份。判据在各节 assert 中。
"""
import torch

torch.manual_seed(42)


def segment_lse(logits: torch.Tensor, owner: torch.Tensor, num_entities: int,
                rho: torch.Tensor) -> torch.Tensor:
    """S_e = (1/tau) * log( (1/m_e) * sum_i exp(tau * l_i) )，tau = exp(rho)。

    静态实现：scatter amax 做 max-shift（detach，只定位），scatter_add 求和。
    无 topk、无排序、无布尔索引、无数据依赖控制流。
    """
    tau = torch.exp(rho)
    z = tau * logits
    shift = torch.full((num_entities,), float("-inf"), dtype=z.dtype, device=z.device)
    shift = shift.scatter_reduce(0, owner, z.detach(), reduce="amax", include_self=True)
    exp_term = torch.exp(z - shift[owner])
    denom = torch.zeros(num_entities, dtype=z.dtype, device=z.device)
    denom = denom.scatter_add(0, owner, exp_term)
    m = torch.zeros(num_entities, dtype=z.dtype, device=z.device)
    m = m.scatter_add(0, owner, torch.ones_like(z))
    return (shift + torch.log(denom) - torch.log(m)) / tau


def make_bag(m, scale=1.0, dtype=torch.float64):
    l = torch.randn(m, dtype=dtype) * scale
    owner = torch.zeros(m, dtype=torch.long)
    return l, owner


# ---- 1. 极限行为：tau 大 → max（误差 ≤ log m / tau），tau 小 → mean ----
l, owner = make_bag(1000, scale=3.0)
for rho_val, ref, tol_fn in [
    (torch.log(torch.tensor(1e4)), l.max(), lambda tau: torch.log(torch.tensor(1000.0)) / tau),
    (torch.log(torch.tensor(1e-4)), l.mean(), lambda tau: torch.tensor(1e-3)),
]:
    S = segment_lse(l, owner, 1, rho_val.double())
    tau = torch.exp(rho_val)
    err = (S[0] - ref).abs().item()
    bound = tol_fn(tau).item()
    print(f"tau={tau.item():.1e}  S={S[0].item():.6f}  ref={ref.item():.6f}  "
          f"|err|={err:.2e}  理论界={bound:.2e}")
    assert err <= bound + 1e-12

# ---- 2. 数值稳定性：极端 logit 与极端 tau 不产生 inf/nan（值与梯度）----
print("\n稳定性扫描（logit 幅度 × tau），全部要求值与梯度有限：")
ok_all = True
for scale in [1.0, 30.0, 100.0]:
    for tau_val in [1e-3, 1.0, 1e3]:
        l2 = (torch.randn(50, dtype=torch.float32) * scale).requires_grad_(True)
        rho = torch.log(torch.tensor(tau_val, dtype=torch.float32)).requires_grad_(True)
        S = segment_lse(l2, torch.zeros(50, dtype=torch.long), 1, rho)
        S.sum().backward()
        finite = (torch.isfinite(S).all() and torch.isfinite(l2.grad).all()
                  and torch.isfinite(rho.grad).all())
        ok_all &= bool(finite)
        print(f"  scale={scale:>6.1f} tau={tau_val:>7.1e} S={S.item():>12.4f} "
              f"|dS/drho|={rho.grad.abs().item():.3e} 有限={bool(finite)}")
assert ok_all

# ---- 3. dS/dtau = KL(w||unif)/tau^2 闭式 与 autograd 一致；量级扫描 ----
print("\ndS/dtau 闭式对拍 + 量级（袋 m=1000，logit 尺度 3）：")
l3, _ = make_bag(1000, scale=3.0)
for tau_val in [1e-3, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 100.0, 1000.0]:
    rho = torch.log(torch.tensor(tau_val, dtype=torch.float64)).requires_grad_(True)
    S = segment_lse(l3, torch.zeros(1000, dtype=torch.long), 1, rho)
    S.sum().backward()
    tau = torch.tensor(tau_val, dtype=torch.float64)
    w = torch.softmax(tau * l3, dim=0)
    # 数值稳定的闭式：dS/dtau = (sum w_i l_i - S)/tau = KL(w||unif)/tau^2
    closed = ((w * l3).sum() - S.detach()[0]) / tau
    auto = rho.grad / tau             # dS/dtau = (dS/drho)/tau
    rel = ((auto - closed).abs() / closed.abs().clamp_min(1e-300)).item()
    print(f"  tau={tau_val:>8.3f}  dS/dtau={auto.item():.4e}  闭式={closed.item():.4e} "
          f" 相对差={rel:.1e}")
    assert rel < 1e-5
# 理论：tau→0 时 dS/dtau→Var/2；tau→∞ 时 ≤ log(m)/tau^2 → 0（初始化在大 tau 有梯度平台）
var_half = (l3.var(unbiased=False) / 2).item()
print(f"  Var/2 = {var_half:.4e}（tau→0 极限对照）")

# ---- 4. 尺度耦合恒等式：S_tau(c*l) = c * S_{c*tau}(l) ----
print("\n尺度耦合核验（跨年 logit 尺度漂移 = 有效 tau 漂移）：")
c = 2.5
for tau_val in [0.1, 1.0, 10.0]:
    lhs = segment_lse(c * l3, torch.zeros(1000, dtype=torch.long), 1,
                      torch.log(torch.tensor(tau_val, dtype=torch.float64)))
    rhs = c * segment_lse(l3, torch.zeros(1000, dtype=torch.long), 1,
                          torch.log(torch.tensor(c * tau_val, dtype=torch.float64)))
    d = (lhs - rhs).abs().item()
    print(f"  tau={tau_val}: |S_tau(c l) - c S_(c tau)(l)| = {d:.2e}")
    assert d < 1e-9

# ---- 5. gradcheck（双精度，l 与 rho 同时）----
def f(lv, rv):
    return segment_lse(lv, torch.zeros(12, dtype=torch.long), 1, rv).sum()

lv = (torch.randn(12, dtype=torch.float64)).requires_grad_(True)
rv = torch.tensor(0.3, dtype=torch.float64, requires_grad=True)
assert torch.autograd.gradcheck(f, (lv, rv), eps=1e-6, atol=1e-8)
print("\ngradcheck(l, rho) 通过（float64）")

# ---- 6. dS/dl 支撑：权重泄漏到整袋；有效参与率对照 ATk ----
print("\n权重泄漏（m=1000，logit 尺度 3）：")
for tau_val in [0.5, 1.0, 2.0, 5.0]:
    tau = torch.tensor(tau_val, dtype=torch.float64)
    w = torch.softmax(tau * l3, dim=0)
    part = (1.0 / (w ** 2).sum()).item()   # 参与率 1/sum w^2
    nonzero = int((w > 1e-12).sum())
    print(f"  tau={tau_val}: 参与率≈{part:.1f} 条流等效支撑，>1e-12 权重的流 {nonzero}/1000")

# ---- 7. torch.compile fullgraph=True 零图断裂 + 换形状二次调用 ----
print("\ntorch.compile 核验：")
import torch._dynamo as dynamo

dynamo.reset()
rho_p = torch.nn.Parameter(torch.tensor(0.0))
def loss_fn(logits, owner, num_entities):
    S = segment_lse(logits, owner, num_entities, rho_p)
    return S.square().mean()

explain = dynamo.explain(loss_fn)(
    torch.randn(500), torch.randint(0, 40, (500,)), 40)
print(f"  graph_break_count = {explain.graph_break_count}")
assert explain.graph_break_count == 0
dynamo.reset()
compiled = torch.compile(loss_fn, fullgraph=True)
out1 = compiled(torch.randn(500), torch.randint(0, 40, (500,)), 40)
out1.backward()
g1 = rho_p.grad.clone(); rho_p.grad = None
out2 = compiled(torch.randn(801), torch.randint(0, 33, (801,)), 33)
out2.backward()
print(f"  fullgraph=True 编译执行成功，换形状二次调用成功；drho 有限={bool(torch.isfinite(g1))}")
print("\n全部断言通过。参数量：1 个标量 rho（tau = exp(rho)）。")
