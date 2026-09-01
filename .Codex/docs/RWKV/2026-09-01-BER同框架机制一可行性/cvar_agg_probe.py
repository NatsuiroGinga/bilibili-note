# CVaR_α 实体聚合算子最小核验：梯度支撑规模 + torch.compile 图断裂计数
# 环境：/opt/miniconda3/envs/rwkv/bin/python（torch 2.12.0，CPU 即可）
# 该脚本只核验算子性质，不接触任何真实数据或实验代码。
import math

import torch
import torch._dynamo as dynamo

torch.manual_seed(42)


def cvar_agg_sort(logits: torch.Tensor, mask: torch.Tensor, alpha: float) -> torch.Tensor:
    """静态形状的实体内 CVaR_α 聚合（R-U 形式，ζ 取批内经验分位数并 detach）。

    logits: [E, M] padding 任意值；mask: [E, M] bool；alpha 为静态 Python 常数。
    ζ 用降序排序 + gather 取第 ceil(alpha*m) 大值，全部为静态形状算子。
    """
    neg_inf = torch.finfo(logits.dtype).min
    x = torch.where(mask, logits, torch.full_like(logits, neg_inf))
    x_sorted = torch.sort(x, dim=1, descending=True).values
    m = mask.sum(dim=1, keepdim=True)
    k = torch.clamp((alpha * m).ceil().long(), min=1)  # [E,1] 张量索引，gather 静态
    zeta = x_sorted.gather(1, k - 1).detach()
    hinge = torch.relu(logits - zeta) * mask
    s = zeta.squeeze(1) + hinge.sum(dim=1) / (alpha * m.squeeze(1).to(logits.dtype))
    return s


def max_agg(logits: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    neg_inf = torch.finfo(logits.dtype).min
    x = torch.where(mask, logits, torch.full_like(logits, neg_inf))
    return x.max(dim=1).values


def cvar_agg_dynamic(logits: torch.Tensor, mask: torch.Tensor, alpha: float) -> torch.Tensor:
    """对照：动态布尔索引版（CEM 式写法），预期触发图断裂。"""
    out = []
    for e in range(logits.shape[0]):
        v = logits[e][mask[e]]  # 动态形状
        k = max(1, math.ceil(alpha * v.numel()))
        top = torch.topk(v, k).values
        out.append(top.mean())
    return torch.stack(out)


def main() -> None:
    E, M = 6, 200
    alpha = 0.05
    logits = torch.randn(E, M, requires_grad=True)
    # 变长袋：有效流数 200/150/100/60/20/5
    lengths = [200, 150, 100, 60, 20, 5]
    mask = torch.zeros(E, M, dtype=torch.bool)
    for e, L in enumerate(lengths):
        mask[e, :L] = True

    # --- 核验 1：数值正确性（与逐实体 topk 均值一致） ---
    s_static = cvar_agg_sort(logits, mask, alpha)
    s_ref = cvar_agg_dynamic(logits.detach(), mask, alpha)
    print("值一致(atol=1e-6):", torch.allclose(s_static.detach(), s_ref, atol=1e-6))
    print("static:", [f"{v:.4f}" for v in s_static.tolist()])
    print("ref   :", [f"{v:.4f}" for v in s_ref.tolist()])

    # --- 核验 2：梯度支撑规模（CVaR_α 尾集 vs max 单点） ---
    s_static.sum().backward()
    g_cvar = logits.grad.clone()
    logits.grad = None
    max_agg(logits, mask).sum().backward()
    g_max = logits.grad.clone()
    sup_cvar = (g_cvar != 0).sum(dim=1).tolist()
    sup_max = (g_max != 0).sum(dim=1).tolist()
    expect = [max(1, math.ceil(alpha * L)) for L in lengths]
    print("袋大小        :", lengths)
    print("CVaR 梯度支撑 :", sup_cvar, "（理论 ceil(αm) =", expect, "）")
    print("max  梯度支撑 :", sup_max)

    # --- 核验 3：torch.compile 图断裂计数 ---
    def loss_static(lg, mk):
        return cvar_agg_sort(lg, mk, alpha).sum()

    def loss_dynamic(lg, mk):
        return cvar_agg_dynamic(lg, mk, alpha).sum()

    exp_static = dynamo.explain(loss_static)(logits.detach().requires_grad_(True), mask)
    print("静态版 graph_break_count =", exp_static.graph_break_count,
          "graph_count =", exp_static.graph_count)
    dynamo.reset()
    exp_dyn = dynamo.explain(loss_dynamic)(logits.detach().requires_grad_(True), mask)
    print("动态版 graph_break_count =", exp_dyn.graph_break_count,
          "graph_count =", exp_dyn.graph_count)

    # fullgraph 编译一次确认可通过
    dynamo.reset()
    compiled = torch.compile(loss_static, fullgraph=True)
    val = compiled(logits.detach().requires_grad_(True), mask)
    print("fullgraph=True 编译并执行成功，loss =", float(val))


if __name__ == "__main__":
    main()
