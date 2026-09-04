"""插值式软 top-k：连续 α、整数点逐位等于硬 top-k、α·m=1 时逐位等于 max。"""
import sys, torch
sys.path.insert(0, "/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819/thesis/experiments/llm_probe/tools")
import ch3_ft_entity_ranking_loss as R
torch.manual_seed(0)

def soft_topk_mean(scores, alpha):
    """scores: (m,) 一维；alpha: 标量张量。返回 top-(α·m) 均值的连续插值。"""
    m = scores.numel()
    s, _ = torch.sort(scores, descending=True)
    t = torch.clamp(alpha * m, min=1.0, max=float(m))     # 有效取用条数，连续
    k = torch.floor(t)
    f = t - k
    ki = int(k.item())
    head = s[:ki].sum()
    tail = s[ki] * f if ki < m else torch.zeros((), dtype=s.dtype)
    return (head + tail) / t

l = torch.randn(9, dtype=torch.float64)
print("检验一：α 的梯度是否非零")
for a0 in (0.5, 0.3, 0.12):
    a = torch.tensor(a0, dtype=torch.float64, requires_grad=True)
    soft_topk_mean(l, a).backward()
    print("  α=%.2f  α.grad=%+.6f  非零=%s" % (a0, float(a.grad), float(a.grad) != 0.0))

print()
print("检验二：整数点上与硬 top-k 是否逐位相同")
owner = torch.zeros(9, dtype=torch.long)
valid = torch.ones(9, dtype=torch.bool)
for a0 in (1/9, 3/9, 5/9, 1.0):                      # α·m = 1,3,5,9
    a = torch.tensor(a0, dtype=torch.float64)
    soft = soft_topk_mean(l, a)
    hard = R.tail_aggregate(l, valid, owner, 1, a0)["entity_scores"][0]
    print("  α·m=%.0f  soft=%.15f  hard=%.15f  逐位相同=%s"
          % (a0*9, float(soft), float(hard), float(soft) == float(hard)))

print()
print("检验三：α·m=1 时是否逐位等于 max")
a = torch.tensor(1/9, dtype=torch.float64)
print("  soft=%.15f  max=%.15f  逐位相同=%s"
      % (float(soft_topk_mean(l, a)), float(l.max()), float(soft_topk_mean(l, a)) == float(l.max())))
