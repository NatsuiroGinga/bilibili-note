# ATk（top-ceil(αm) 均值）聚合的静态实现核验：值 / 梯度支撑 / fullgraph 编译
import math

import torch
import torch._dynamo as dynamo

torch.manual_seed(42)


def atk_agg(logits: torch.Tensor, mask: torch.Tensor, alpha: float) -> torch.Tensor:
    """S_e = 实体内 top-ceil(alpha*m_e) 个 logit 的均值（CVaR_α 的 ATk 经验形式）。

    全静态形状：sort + arange 比较权重矩阵，无 topk(k=张量)、无布尔索引。
    k_e = 1 时严格退化为 max。梯度经 sort 的置换回传，支撑恰为 k_e。
    """
    neg_inf = torch.finfo(logits.dtype).min
    x = torch.where(mask, logits, torch.full_like(logits, neg_inf))
    x_sorted = torch.sort(x, dim=1, descending=True).values
    m = mask.sum(dim=1, keepdim=True)
    k = torch.clamp((alpha * m).ceil(), min=1.0)  # [E,1] 浮点，仅作比较与除数
    j = torch.arange(logits.shape[1], device=logits.device).unsqueeze(0)  # [1,M]
    w = (j < k).to(logits.dtype) / k  # [E,M] 静态权重矩阵
    return (w * x_sorted).sum(dim=1)


def main() -> None:
    E, M = 6, 200
    alpha = 0.05
    lengths = [200, 150, 100, 60, 20, 5]
    logits = torch.randn(E, M, requires_grad=True)
    mask = torch.zeros(E, M, dtype=torch.bool)
    for e, L in enumerate(lengths):
        mask[e, :L] = True

    s = atk_agg(logits, mask, alpha)
    # 参考：逐实体显式 topk 均值
    ref = torch.stack([
        torch.topk(logits[e][mask[e]].detach(), max(1, math.ceil(alpha * L))).values.mean()
        for e, L in enumerate(lengths)
    ])
    print("值与逐实体 topk 均值一致:", torch.allclose(s.detach(), ref, atol=1e-6))

    s.sum().backward()
    sup = (logits.grad != 0).sum(dim=1).tolist()
    expect = [max(1, math.ceil(alpha * L)) for L in lengths]
    print("袋大小      :", lengths)
    print("梯度支撑    :", sup, "（理论 ceil(αm)∨1 =", expect, "）")

    def loss(lg, mk):
        return atk_agg(lg, mk, alpha).sum()

    exp = dynamo.explain(loss)(logits.detach().requires_grad_(True), mask)
    print("graph_break_count =", exp.graph_break_count, "graph_count =", exp.graph_count)
    dynamo.reset()
    compiled = torch.compile(loss, fullgraph=True)
    v = compiled(logits.detach().requires_grad_(True), mask)
    print("fullgraph=True 编译执行成功, loss =", v.item())

    # 变长袋在不同 E/M 下不重编译的粗查：换形状调用一次（dynamic=True 场景另测）
    logits2 = torch.randn(3, 97)
    mask2 = torch.ones(3, 97, dtype=torch.bool)
    v2 = compiled(logits2.requires_grad_(True), mask2)
    print("换形状二次调用成功, loss =", v2.item())


if __name__ == "__main__":
    main()
