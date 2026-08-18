# -*- coding: utf-8 -*-
"""逐位比较两个检查点（selected.pt 或 inflight.pt）。只读，不改任何生产制品。"""
import json
import sys

import torch


def load(p):
    return torch.load(p, map_location="cpu", weights_only=False)


def cmp_sd(sa, sb):
    assert set(sa) == set(sb), "键集合不同"
    mx = 0.0
    neq = []
    for k in sa:
        ta, tb = sa[k].cpu(), sb[k].cpu()
        if ta.dtype.is_floating_point:
            d = (ta.float() - tb.float()).abs().max().item() if ta.numel() else 0.0
        else:
            d = float((ta != tb).sum().item())
        mx = max(mx, d)
        if not torch.equal(ta, tb):
            neq.append([k, d])
    return mx, neq, len(sa)


a, b = load(sys.argv[1]), load(sys.argv[2])
out = {"file_a": sys.argv[1], "file_b": sys.argv[2]}
mx, neq, n = cmp_sd(a["model"] if "model" in a else a["state"],
                    b["model"] if "model" in b else b["state"])
out["model_n_tensors"] = n
out["model_max_abs_diff"] = mx
out["model_not_bitwise_equal"] = neq

if "opt" in a and "opt" in b:
    oa, ob = a["opt"], b["opt"]
    out["opt_param_groups_equal"] = (json.dumps(oa["param_groups"], sort_keys=True, default=str)
                                     == json.dumps(ob["param_groups"], sort_keys=True, default=str))
    omx = 0.0
    obad = []
    assert set(oa["state"]) == set(ob["state"])
    ncond = 0
    for pid in oa["state"]:
        for k in oa["state"][pid]:
            ta, tb = oa["state"][pid][k], ob["state"][pid][k]
            ncond += 1
            if torch.is_tensor(ta):
                ta, tb = ta.cpu(), tb.cpu()
                d = (ta.float() - tb.float()).abs().max().item() if ta.numel() else 0.0
                eq = torch.equal(ta, tb)
            else:
                d = abs(float(ta) - float(tb))
                eq = ta == tb
            omx = max(omx, d)
            if not eq:
                obad.append([pid, k, d])
    out["opt_n_entries"] = ncond
    out["opt_max_abs_diff"] = omx
    out["opt_not_bitwise_equal"] = obad

if "rng" in a and "rng" in b:
    r = {}
    for k in ["torch_cpu", "batch_gen"]:
        r[k] = bool(torch.equal(a["rng"][k].cpu(), b["rng"][k].cpu()))
    r["torch_cuda_all"] = [bool(torch.equal(x.cpu(), y.cpu()))
                           for x, y in zip(a["rng"]["torch_cuda_all"], b["rng"]["torch_cuda_all"])]
    out["rng_bitwise_equal"] = r

for k in ["epoch", "val_ap", "p", "npar", "n_epoch", "epoch_steps"]:
    if k in a:
        out[f"{k}_a"] = repr(a[k])
        out[f"{k}_b"] = repr(b[k])
if "best" in a:
    out["best_epoch_a"] = a["best"]["epoch"]
    out["best_epoch_b"] = b["best"]["epoch"]
    out["best_ap_a"] = repr(a["best"]["ap"])
    out["best_ap_b"] = repr(b["best"]["ap"])
    bmx, bneq, bn = cmp_sd(a["best"]["state"], b["best"]["state"])
    out["best_state_max_abs_diff"] = bmx
    out["best_state_not_bitwise_equal"] = bneq
out["hist_a"] = a["hist"]
out["hist_b"] = b["hist"]
out["hist_bitwise_equal"] = [repr(x) for x in a["hist"]] == [repr(x) for x in b["hist"]]
print(json.dumps(out, ensure_ascii=False, indent=2))
