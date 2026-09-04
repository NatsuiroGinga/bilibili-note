# -*- coding: utf-8 -*-
"""E2：α 作为可训练标量时，与**生产代码**梯度控制器 c 的交互（合成输入，CPU，零 GPU）。

用的是真实模块，不是复刻：
  ch3_ft_gradient_controller.combine_gradients / verify_first_order_invariants
  ch3_ft_entity_ranking_loss.cvar_pauc_loss / tail_aggregate
  ch3_ft_c00_dual_selection 的 _shared_parameters / _flat_grad_from_params 逐字复用语义

回答被审文档 §四 第 3 项：「α 的梯度是否会被梯度控制器 c 缩放？」
以及 §四 第 4 项的边界数值行为。
"""
import sys
import torch

TOOLS = "/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819/thesis/experiments/llm_probe/tools"
sys.path.insert(0, TOOLS)
import ch3_ft_entity_ranking_loss as R
import ch3_ft_gradient_controller as C

torch.manual_seed(0)
D = torch.float32


def soft_tail_aggregate(flow_scores, flow_valid, flow_entity, num_entities, alpha):
    """被审文档 §二 算子的**向量化**版本，与 tail_aggregate 同接口。

    t = clamp(α·m, 1, m)，k = ⌊t⌋，f = t − k，S_e = (Σ_{i<k} s_i + f·s_k) / t
    """
    dtype = flow_scores.dtype
    valid_bool = flow_valid if flow_valid.dtype == torch.bool else flow_valid > 0
    entity_index = flow_entity.to(torch.long)
    filled = torch.where(valid_bool, flow_scores, torch.full_like(flow_scores, torch.finfo(dtype).min))
    order_by_score = torch.argsort(filled, descending=True, stable=True)
    order = order_by_score[torch.argsort(entity_index[order_by_score], stable=True)]
    sorted_scores, sorted_entity = filled[order], entity_index[order]
    sorted_valid = valid_bool[order]
    total = flow_scores.shape[0]
    ones = torch.ones(total, dtype=torch.long)
    total_per_entity = torch.zeros(num_entities, dtype=torch.long).index_add_(0, entity_index, ones)
    group_start = torch.cumsum(total_per_entity, 0) - total_per_entity
    rank = (torch.arange(total) - group_start[sorted_entity]).to(dtype)
    m = torch.zeros(num_entities, dtype=dtype).index_add_(0, entity_index, valid_bool.to(dtype))

    t = torch.clamp(alpha * m, min=1.0)
    t = torch.minimum(t, m.clamp(min=1.0))          # 与 tail_aggregate 的 k≤m 夹紧同构
    k = torch.floor(t)
    f = t - k
    # 权重：秩 < k 的取 1，秩 == k 的取 f，其余 0；无效流一律 0
    w = torch.where(rank < k[sorted_entity], torch.ones_like(rank),
                    torch.where(rank == k[sorted_entity], f[sorted_entity], torch.zeros_like(rank)))
    w = torch.where(sorted_valid, w, torch.zeros_like(w))
    totals = torch.zeros(num_entities, dtype=dtype).index_add_(0, sorted_entity, w * sorted_scores)
    return {"entity_scores": totals / t, "t_per_entity": t, "m_per_entity": m}


# ---------------------------------------------------------------- 1. 生产梯度路径
print("=" * 78)
print("检验 A：α 是模型参数时，combine_gradients 是否把 c 乘到 α 的梯度上")
print("=" * 78)

N_FLOW, N_ENT, N_FEAT = 240, 24, 8


class Scorer(torch.nn.Module):
    """极小真实模型：线性打分头 + 一个可训练标量 α（被审文档 §2.1 的提法）。"""

    def __init__(self):
        super().__init__()
        self.head = torch.nn.Linear(N_FEAT, 1)
        self.alpha = torch.nn.Parameter(torch.tensor(0.5))

    def forward(self, x):
        return self.head(x).squeeze(-1)


def shared_parameters(model):                       # 与 ch3_ft_c00_dual_selection:2346 逐字同义
    return [p for p in model.parameters() if p.requires_grad]


def flat_grad(params):                              # 与 ch3_ft_c00_dual_selection:2351 逐字同义
    return torch.cat([(p.grad.detach().clone() if p.grad is not None else torch.zeros_like(p)).reshape(-1)
                      for p in params]).to(torch.float32)


def alpha_slice(model):
    off = 0
    for name, p in model.named_parameters():
        if name == "alpha":
            return off, off + p.numel()
        off += p.numel()
    raise AssertionError("模型里没有 alpha")


def one_step(model, xi_scale, tag):
    x = torch.randn(N_FLOW, N_FEAT)
    owner = torch.arange(N_FLOW) % N_ENT
    valid = torch.ones(N_FLOW, dtype=torch.bool)
    y = (torch.rand(N_FLOW) > 0.7).float()
    is_pos = torch.zeros(N_ENT, dtype=torch.bool)
    is_pos[:4] = True                                # 4 正实体 / 20 负实体
    params = shared_parameters(model)

    # ---- 阶段一：逐流 BCE（不含 α）----
    model.zero_grad(set_to_none=True)
    torch.nn.functional.binary_cross_entropy_with_logits(model(x), y).backward()
    g_flow = flat_grad(params)

    # ---- 阶段二：排序损失（含 α，经软 top-k）----
    model.zero_grad(set_to_none=True)
    agg = soft_tail_aggregate(model(x), valid, owner, N_ENT, model.alpha)
    S = agg["entity_scores"]
    pos, neg = S[is_pos], S[~is_pos]
    xi = torch.full((int(is_pos.sum()), 6), xi_scale)
    loss_rank, _ = R.cvar_pauc_loss(pos, neg, [1.0, 2.0, 4.0, 8.0, 12.0, 16.0], xi)
    loss_rank.backward()
    g_rank = flat_grad(params)

    combined, diag = C.combine_gradients(g_flow, g_rank)
    inv = C.verify_first_order_invariants(combined, g_flow, diag)
    lo, hi = alpha_slice(model)
    c = diag["c_scaling"]
    print(f"\n[{tag}] c = {c:.6f}   投影触发 = {diag['projection_triggered']}   一阶不变量 = {inv['both_hold']}")
    print(f"  g_flow[α] = {float(g_flow[lo]):+.10e}   （逐流损失不含 α ⟹ 应精确为 0）")
    print(f"  g_rank[α] = {float(g_rank[lo]):+.10e}")
    print(f"  combined[α] = {float(combined[lo]):+.10e}")
    print(f"  c · g_rank[α] = {float(c * g_rank[lo]):+.10e}")
    print(f"  ** combined[α] 与 c·g_rank[α] 逐位相同 = "
          f"{float(combined[lo]) == float(c * g_rank[lo])} **")
    return float(g_flow[lo]), float(g_rank[lo]), float(combined[lo]), c


one_step(Scorer(), xi_scale=0.0, tag="ξ=0，活动集非空")
# ξ 取极大 ⟹ 全部 hinge 关闭 ⟹ 排序梯度精确为零 ⟹ c=0（对应 c_scaling_median=0 的步）
gf, gr, cb, c0 = one_step(Scorer(), xi_scale=1e4, tag="ξ 极大，活动集全空")
print(f"\n  活动集全空时：g_rank[α] = {gr:+.3e}，c = {c0}，combined[α] = {cb:+.3e}")
print(f"  ⟹ 该步 α 收到的梯度精确为 {cb}")

# ---------------------------------------------------------------- 2. α 不是模型参数时
print()
print("=" * 78)
print("检验 B：α 若不在 model.parameters() 里，_combine_and_step 会怎样")
print("=" * 78)
m2 = Scorer()
alpha_free = torch.tensor(0.5, requires_grad=True)      # 游离标量，不注册进模型
opt = torch.optim.Adam(m2.parameters(), lr=1e-2)        # 优化器只收 model.parameters()
x = torch.randn(N_FLOW, N_FEAT); owner = torch.arange(N_FLOW) % N_ENT
valid = torch.ones(N_FLOW, dtype=torch.bool)
is_pos = torch.zeros(N_ENT, dtype=torch.bool); is_pos[:4] = True
S = soft_tail_aggregate(m2(x), valid, owner, N_ENT, alpha_free)["entity_scores"]
loss, _ = R.cvar_pauc_loss(S[is_pos], S[~is_pos], [1.0, 2.0, 4.0, 8.0, 12.0, 16.0],
                           torch.zeros((4, 6)))
loss.backward()
print(f"  反传后 alpha_free.grad = {alpha_free.grad}")
before = float(alpha_free)
opt.zero_grad(set_to_none=True)                          # _combine_and_step 第 3027 行
print(f"  optimizer.zero_grad(set_to_none=True) 后 alpha_free.grad = {alpha_free.grad}")
opt.step()                                               # 第 3034 行
print(f"  optimizer.step() 后 α：{before} → {float(alpha_free)}   位移 = {float(alpha_free)-before}")

# ---------------------------------------------------------------- 3. 解析梯度与符号
print()
print("=" * 78)
print("检验 C：∂S_e/∂α 的闭式与符号（决定 α 能否停在内点）")
print("=" * 78)
print("  闭式推导：S = (Σ_{i<k}s_i + f·s_k)/t，t=α·m ⟹ ∂S/∂t = (s_k − S)/t，∂t/∂α = m")
print("           ⟹ ∂S/∂α = m·(s_k − S)/t = (s_k − S)/α，而 s_k ≤ S（S 是前 t 条的均值）")
print("           ⟹ **∂S_e/∂α ≤ 0 对每个实体恒成立**")
bad = 0
for trial in range(200):
    m = int(torch.randint(3, 40, (1,)))
    s = torch.randn(m, dtype=torch.float64)
    a = torch.tensor(float(torch.rand(1)) * 0.9 + 0.05, dtype=torch.float64, requires_grad=True)
    if a * m <= 1.0 or a * m >= m:
        continue
    ss, _ = torch.sort(s, descending=True)
    t = a * m
    k = torch.floor(t); f = t - k; ki = int(k)
    S = (ss[:ki].sum() + ss[ki] * f) / t
    S.backward()
    closed = float((ss[ki] - S.detach()) / a.detach())
    if abs(float(a.grad) - closed) > 1e-9 or float(a.grad) > 0:
        bad += 1
print(f"  200 组随机 (m, s, α) 中，自动微分与闭式不符或梯度为正的组数 = {bad}")

# ---------------------------------------------------------------- 4. 边界
print()
print("=" * 78)
print("检验 D：边界 m_e = 0 / 1 / 2 与 α·m 恰为整数")
print("=" * 78)
for m_e in (0, 1, 2, 3):
    if m_e == 0:
        owner = torch.zeros(2, dtype=torch.long); valid = torch.zeros(2, dtype=torch.bool)
        sc = torch.randn(2, requires_grad=True)
    else:
        owner = torch.zeros(m_e, dtype=torch.long); valid = torch.ones(m_e, dtype=torch.bool)
        sc = torch.randn(m_e, requires_grad=True)
    for a0 in (0.5, 1.0):
        a = torch.tensor(a0, requires_grad=True)
        try:
            out = soft_tail_aggregate(sc, valid, owner, 1, a)
            S = out["entity_scores"][0]
            hard = R.tail_aggregate(sc.detach(), valid, owner, 1, a0)["entity_scores"][0]
            g = torch.autograd.grad(S, a, allow_unused=True)[0]
            print(f"  m_e={m_e} α={a0}: t={float(out['t_per_entity'][0]):.4f} "
                  f"软 S={float(S):+.8f} 硬 S={float(hard):+.8f} "
                  f"逐位同={float(S)==float(hard)} ∂S/∂α={float(g) if g is not None else None}")
        except Exception as exc:                       # noqa: BLE001
            print(f"  m_e={m_e} α={a0}: 抛出 {type(exc).__name__}: {exc}")
