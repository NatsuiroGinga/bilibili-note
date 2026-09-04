"""核实 §2.6.3 的位移上界常数：|dL/dxi| 到底是 1/beta 还是 (1/(Np*|K|))*(1/beta)。

直接导入生产模块 `ch3_ft_entity_ranking_loss.cvar_pauc_loss`（active_policy=
causal_prefix_truncation 走的正是这一支，见 bag_policy_diagnostics 的
`_score_and_loss(..., stratified=False)`），用构造输入反传，读 xi.grad 实测。

合成输入只用于验证公式实现与常数，不产生任何 SwanLab 身份、不进论文结果。
运行：/opt/miniconda3/envs/rwkv/bin/python <本文件>
"""

import sys

import torch

sys.path.insert(0, "thesis/experiments/llm_probe/tools")
import ch3_ft_entity_ranking_loss as ranking  # noqa: E402

BUDGETS = [121, 606, 1213, 2426, 4853, 9706]
NEG_POOL = 121336
N_POS, N_NEG = 2, 64
LR = 1e-4  # 冻结配置 xi_learning_rate


def main():
    torch.manual_seed(0)
    eff = [ranking.effective_budget(k, NEG_POOL, N_NEG) for k in BUDGETS]
    betas = [k / NEG_POOL for k in BUDGETS]
    print("K_eff =", ["%.5f" % e for e in eff])
    print("beta  =", ["%.5e" % b for b in betas])
    print("K_eff / n_neg == beta ?", all(abs(e / N_NEG - b) < 1e-12 for e, b in zip(eff, betas)))

    # 构造：正实体分数固定，负实体分数张成一段区间，使不同 xi 下活动数可控。
    pos = torch.zeros(N_POS)
    neg = torch.linspace(-6.0, 2.0, N_NEG)
    pairwise = torch.nn.functional.softplus(neg.unsqueeze(0) - pos.unsqueeze(1))

    print("\n" + "=" * 78)
    print("一、逐档实测 dL/dxi 与两个候选解析式对比")
    print(f"{'K':>6} {'K_eff':>9} {'n_act':>6} {'实测 dL/dxi':>14} "
          f"{'(1-n/Keff)/(Np|K|)':>19} {'1-n/Keff':>12} {'比值':>8}")
    # 取一组 xi：每档取一个使活动数为 0 或 3 的阈值，覆盖两种情形。
    for target_active in (0, 3):
        print(f"-- 目标活动数 = {target_active}")
        xi_rows = []
        for _ in range(N_POS):
            row = []
            for _col in range(len(BUDGETS)):
                srt = torch.sort(pairwise[0], descending=True).values
                thr = float(srt[target_active] + srt[max(target_active - 1, 0)]) / 2 if target_active > 0 \
                    else float(srt[0]) + 1.0
                row.append(thr)
            xi_rows.append(row)
        xi = torch.tensor(xi_rows, dtype=torch.float32, requires_grad=True)
        loss, diag = ranking.cvar_pauc_loss(pos, neg, eff, xi)
        loss.backward()
        for col, (k, e) in enumerate(zip(BUDGETS, eff)):
            n_act = int((pairwise[0] > xi[0, col]).sum())
            g = float(xi.grad[0, col])
            pred_with = (1.0 - n_act / e) / (N_POS * len(BUDGETS))
            pred_without = 1.0 - n_act / e
            print(f"{k:>6} {e:>9.5f} {n_act:>6} {g:>14.6e} {pred_with:>19.6e} "
                  f"{pred_without:>12.6e} {g / pred_with:>8.4f}")

    print("\n" + "=" * 78)
    print("二、最坏情形位移：把 xi 压到 0（全部 128 对都活动）")
    xi0 = torch.zeros(N_POS, len(BUDGETS), requires_grad=True)
    loss0, _ = ranking.cvar_pauc_loss(pos, neg, eff, xi0)
    loss0.backward()
    print(f"{'K':>6} {'1/beta':>10} {'实测|dL/dxi|':>14} {'lr*|g| 位移':>14} "
          f"{'文档 lr/beta':>14} {'文档高估倍数':>12}")
    for col, (k, b) in enumerate(zip(BUDGETS, betas)):
        g = abs(float(xi0.grad[0, col]))
        doc = LR / b
        print(f"{k:>6} {1 / b:>10.2f} {g:>14.6e} {LR * g:>14.6e} {doc:>14.6e} "
              f"{doc / (LR * g):>12.4f}")

    print("\n" + "=" * 78)
    print("三、修正后的耦合约束：要求单步位移 < 带宽 1/kappa")
    print("   位移(K) = lr_K * (1/(Np|K|)) * (n_act/K_eff - 1)，最坏 n_act = n_neg")
    for kappa in (1e2, 1e4):
        print(f"-- kappa = {kappa:.0e}，带宽 = {1 / kappa:.3e}")
        for col, (k, b) in enumerate(zip(BUDGETS, betas)):
            g = abs(float(xi0.grad[0, col]))
            need_lr = (1.0 / kappa) / g
            print(f"   K={k:>5}  |dL/dxi|={g:>10.4f}  现行 lr=1e-4 位移={LR * g:>10.4e}"
                  f"  {'跨过' if LR * g > 1 / kappa else '可停'}  需 lr < {need_lr:.4e}")

    print("\n" + "=" * 78)
    print("四、lr_K = c*beta_K 的实际位移（修正常数后）")
    print(f"{'c':>8} {'K':>6} {'lr_K':>12} {'位移':>12} {'kappa=1e4 带宽/位移':>20}")
    for c in (1e-5, 1e-4, 1e-3):
        for col, (k, b) in enumerate(zip(BUDGETS, betas)):
            g = abs(float(xi0.grad[0, col]))
            lr_k = c * b
            disp = lr_k * g
            if col in (0, 5):
                print(f"{c:>8.0e} {k:>6} {lr_k:>12.4e} {disp:>12.4e} {(1e-4) / disp:>20.2f}")


def typical_case():
    """用 C01 实测活动率算「典型步」位移，而不是最坏情形上界。

    实测（ch3-ft-c01-entitybce-halfwidth-screening-v1 第 8 轮
    falsifiable_observables.per_budget_active_rate_epoch_mean）：
    活动率是 (Np x Nn)=128 个配对中超过 xi 的比例。
    """
    rates_ep8 = [0.004203125, 0.0096484375, 0.0135, 0.01925, 0.0288125, 0.0425390625]
    eff = [ranking.effective_budget(k, NEG_POOL, N_NEG) for k in BUDGETS]
    print("\n" + "=" * 78)
    print("五、用 C01 第 8 轮实测活动率算典型步位移（非最坏情形）")
    print(f"{'K':>6} {'K_eff':>8} {'实测活动率':>11} {'每正实体活动数':>14} "
          f"{'n=0 位移':>11} {'n=1 位移':>11} {'kappa=1e4 带宽 1e-4':>18}")
    for k, e, r in zip(BUDGETS, eff, rates_ep8):
        n_per_pos = r * N_NEG
        d0 = LR * (1.0 / (N_POS * len(BUDGETS))) * 1.0
        d1 = LR * (1.0 / (N_POS * len(BUDGETS))) * abs(1.0 - 1.0 / e)
        verdict = "n>=1 跨过" if d1 > 1e-4 else "都可停"
        print(f"{k:>6} {e:>8.4f} {r:>11.6f} {n_per_pos:>14.3f} "
              f"{d0:>11.4e} {d1:>11.4e} {verdict:>18}")


if __name__ == "__main__":
    main()
    typical_case()
