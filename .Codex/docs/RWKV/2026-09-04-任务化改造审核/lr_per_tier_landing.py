"""核实 lr_K = c*beta_K 在生产数据结构上能否落地，不改 CvarThresholdState。

生产路径（ch3_ft_c00_dual_selection.py:2779-2825）：
    xi = xi_state.get(positive_entity_ids).to(device)   # (Np, |K|) 叶张量
    ...
    loss_rank.backward()
    xi_updated = (xi.detach() - float(ranking_cfg["xi_learning_rate"]) * xi.grad).cpu()
    xi_state.commit(positive_entity_ids, xi_updated)

本脚本用真实的 CvarThresholdState 与 cvar_pauc_loss 跑一遍：标量 lr 与 (1,|K|)
广播向量 lr 两条路径，核对形状、commit 写回与逐档步长确实不同。
运行：/opt/miniconda3/envs/rwkv/bin/python <本文件>
"""

import sys

import numpy as np
import torch

sys.path.insert(0, "thesis/experiments/llm_probe/tools")
import ch3_ft_entity_ranking_loss as ranking  # noqa: E402

BUDGETS = [121, 606, 1213, 2426, 4853, 9706]
NEG_POOL = 121336
N_POS, N_NEG = 2, 64
C = 1e-5


def one_step(lr, ids, pos, neg, eff, state):
    xi = state.get(ids)
    xi.retain_grad()
    loss, _ = ranking.cvar_pauc_loss(pos, neg, eff, xi)
    loss.backward()
    xi_updated = (xi.detach() - lr * xi.grad).cpu()
    state.commit(ids, xi_updated)
    return xi.grad.clone(), xi_updated


def main():
    torch.manual_seed(0)
    eff = [ranking.effective_budget(k, NEG_POOL, N_NEG) for k in BUDGETS]
    betas = torch.tensor([k / NEG_POOL for k in BUDGETS], dtype=torch.float32)
    ids = np.array([7, 11], dtype=np.int64)
    pos = torch.zeros(N_POS)
    neg = torch.linspace(-1.0, 3.0, N_NEG)  # 故意让不少配对活动

    print("一、标量 lr（现行生产路径）")
    s1 = ranking.CvarThresholdState(budgets=BUDGETS, init_value=0.0)
    g1, u1 = one_step(1e-4, ids, pos, neg, eff, s1)
    print("   xi.grad shape =", tuple(g1.shape), " xi_updated shape =", tuple(u1.shape))
    print("   更新后 xi[0] =", ["%+.6e" % v for v in u1[0].tolist()])

    print("\n二、逐档 lr_K = c*beta_K（(1,|K|) 广播张量，不改任何数据结构）")
    s2 = ranking.CvarThresholdState(budgets=BUDGETS, init_value=0.0)
    lr_vec = (C * betas).unsqueeze(0)  # (1, |K|)
    print("   lr_vec shape =", tuple(lr_vec.shape), " 广播到 (Np,|K|) 合法 =",
          tuple((lr_vec * g1).shape) == (N_POS, len(BUDGETS)))
    print("   lr_K =", ["%.4e" % v for v in lr_vec[0].tolist()])
    g2, u2 = one_step(lr_vec, ids, pos, neg, eff, s2)
    print("   更新后 xi[0] =", ["%+.6e" % v for v in u2[0].tolist()])

    print("\n三、逐档单步位移是否被拉平（lr_K*|grad| 应与档位无关）")
    disp_scalar = (1e-4 * g1[0]).abs()
    disp_vector = (lr_vec[0] * g2[0]).abs()
    print(f"{'K':>6} {'|grad|':>12} {'标量 lr 位移':>14} {'逐档 lr 位移':>14}")
    for i, k in enumerate(BUDGETS):
        print(f"{k:>6} {float(g1[0, i].abs()):>12.5e} {float(disp_scalar[i]):>14.5e} "
              f"{float(disp_vector[i]):>14.5e}")
    print("   标量 lr 位移跨档倍率 = %.2f" % float(disp_scalar.max() / disp_scalar.min()))
    print("   逐档 lr 位移跨档倍率 = %.2f" % float(disp_vector.max() / disp_vector.min()))

    print("\n四、CvarThresholdState 是否需要改动")
    sd = s2.state_dict()
    print("   state_dict 顶层键 =", sorted(sd.keys()))
    print("   commit() 只按行写回、不含 lr；get() 返回 (Np,|K|) 叶张量 —— 无需改动")

    print("\n五、位移与档位无关的解析核对")
    print("   位移(K) = lr_K*|dL/dxi| = c*beta_K*(1/(Np|K|))*(n/K_eff - 1)")
    print("           = (c/(Np|K|))*(n*beta_K/K_eff - beta_K) = (c/(Np|K|))*(n/n_neg - beta_K)")
    print("   n 相同时逐档只差一个 beta_K（<=0.08），故位移近似恒为 c*n/(Np*|K|*n_neg)。")


if __name__ == "__main__":
    main()
