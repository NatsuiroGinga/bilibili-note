#!/usr/bin/env python3
"""正式运行：双侧组相对对抗训练五臂（A/B/D/F/G），官方 24M DRIFT 模型。

冻结规格 v1（2026-09-10，正式运行前冻结；screening 七臂见 official_p2p3.py §5.6）：
  训练数据 = T17-T19 {benign,dga}_{train,test} 全量合并（官方协议，类不平衡如实保留）
  源验证   = T17-T19 val 全量
  目标面板 = T20-T25 无后缀全量（目标知情评价面板；T20 两文件由官方 HF 补齐，缺失则登记）
  对抗面板 = T18 dga val 全量生成 charbot2 / krand / maskdga 半替换（E-A1 v2 同源算子）
  训练     = 3 epochs、主批 --batch（默认 256）、变体配额 = 主批//2、
             Adam 分层 lr（骨干 1e-6 / 分类头 1e-4）、种子 42、bf16 autocast（CUDA）
  臂       = A 干净 / B 朴素增广 / D 组相对过滤 / F 组过滤+良性加权 / G 只良性加权
             （E KL 锚定已否决，不重跑）
  判读口径 = FNR（0.5 阈值检出率）为主（screening 已证 AP 三面板封顶无区分度）
  断点     = 每 epoch 追加落盘 metrics json + 每臂完成原子写 result_{arm}.json 与 state_dict
  跟踪     = SwanLab 在线模式（project=ch3-drift-official），失败回退 local，不阻塞训练
  运行时断言：臂名、数据文件存在性、批量、种子打印进日志；缺文件列出清单后停止。
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch

ROOT = Path(os.environ.get(
    "LLM_PROBE_ROOT",
    "/root/autodl-tmp/thesis/experiments/llm_probe",
))
sys.path.insert(0, str(ROOT / "tools"))
import ch3_drift_official_branch_conflict_diagnostic as diag
import ch3_drift_official_checkpoint_t17_eval as official

REF = ROOT / "runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2"
CKPT = ROOT / "runs/models/drift-official-dsn2026/finetuning.pt"
DATA = ROOT / "runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521"
OUT = Path(os.environ.get("P2P3_FULL_OUT", ROOT / "runs/diagnostics/p2p3-official-full-v1"))
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "mps")
BATCH = 256            # 正式主批（冻结 v1）
EPOCHS = 3
SEED = 42
LR_HEAD = 1e-4
LR_BACKBONE = 1e-6
BETA_BENIGN = 3.0      # 组件 2 良性误报加权（任务化设定，screening F 臂同值）
ALPHA = "abcdefghijklmnopqrstuvwxyz0123456789-"
USE_BF16 = DEVICE.type == "cuda"
EVAL_BATCH = 1024 if DEVICE.type == "cuda" else 128

TRAIN_FILES = [f"T{y}_{c}_{s}" for y in (17, 18, 19) for c in ("benign", "dga") for s in ("train", "test")]
VAL_FILES = [f"T{y}_{c}_val" for y in (17, 18, 19) for c in ("benign", "dga")]
TARGET_YEARS = [20, 21, 22, 23, 24, 25]


def autocast_ctx():
    return torch.autocast(device_type=DEVICE.type, dtype=torch.bfloat16) if USE_BF16 else nullcontext()


def perturb2(domain: str, rng: random.Random) -> str:
    body = domain.rsplit(".", 1)[0]
    tail = "." + domain.rsplit(".", 1)[1] if "." in domain else ""
    if len(body) < 4:
        return domain
    b = list(body)
    for i in rng.sample(range(len(body)), 2):
        c = rng.choice(ALPHA)
        while c == b[i]:
            c = rng.choice(ALPHA)
        b[i] = c
    return "".join(b) + tail


def perturb_half(domain: str, rng: random.Random) -> str:
    body = domain.rsplit(".", 1)[0]
    tail = "." + domain.rsplit(".", 1)[1] if "." in domain else ""
    if len(body) < 4:
        return domain
    b = list(body)
    for i in rng.sample(range(len(body)), max(1, len(body) // 2)):
        c = rng.choice(ALPHA)
        while c == b[i]:
            c = rng.choice(ALPHA)
        b[i] = c
    return "".join(b) + tail


def load_domains(stem: str) -> list[str]:
    path = DATA / "DRIFT_input_eSLD" / f"{stem}.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"必需数据文件缺失：{path}")
    return pq.read_table(path, columns=["domain"]).column(0).to_pylist()


def load_train() -> tuple[list[str], np.ndarray]:
    domains: list[str] = []
    labels: list[int] = []
    for stem in TRAIN_FILES:
        d = load_domains(stem)
        domains.extend(d)
        labels.extend([0 if "benign" in stem else 1] * len(d))
        print(f"[数据] {stem}: {len(d)} 域", file=sys.stderr, flush=True)
    return domains, np.asarray(labels, dtype=np.int64)


def metrics(model, tokenizer, domains: list[str], labels01: np.ndarray, tok_mean, char_mean) -> dict:
    model.eval()
    scores = []
    with torch.inference_mode():
        for off in range(0, len(domains), EVAL_BATCH):
            chunk = domains[off:off + EVAL_BATCH]
            tok = official.encode_subword(chunk, tokenizer).to(DEVICE)
            ch = official.encode_char(chunk).to(DEVICE)
            with autocast_ctx():
                tf, cf = diag.branch_features(model, tok, ch)
            s = diag.probabilities(model, tf.cpu().numpy(), cf.cpu().numpy(),
                                   tok_mean, char_mean, DEVICE, EVAL_BATCH)
            scores.append(s["static_fusion"])
    sc = np.concatenate(scores)
    from sklearn.metrics import average_precision_score
    pred = sc >= 0.5
    mal, ben = labels01, ~labels01
    fp = int((pred & ben).sum()); fn = int((~pred & mal).sum())
    tp = int((pred & mal).sum()); tn = int((~pred & ben).sum())
    return {"AP": float(average_precision_score(labels01, sc)),
            "FPR": fp / max(fp + tn, 1), "FNR": fn / max(fn + tp, 1),
            "F1": tp / max(tp + 0.5 * (fp + fn), 1), "FP": fp, "FN": fn, "n": len(sc)}


def train_arm(arm: str, train_d: list[str], train_y: np.ndarray, tokenizer, tok_mean, char_mean,
              eval_clean: tuple[list[str], np.ndarray], eval_adv_k2, eval_adv_krand, eval_adv_mask,
              epochs: int, run=None) -> dict:
    model = official.load_model(REF, CKPT, DEVICE)
    opt = torch.optim.Adam([
        {"params": [p_ for n_, p_ in model.named_parameters() if "classifier_head" not in n_], "lr": LR_BACKBONE},
        {"params": [p_ for n_, p_ in model.named_parameters() if "classifier_head" in n_], "lr": LR_HEAD},
    ])
    n_params = sum(p_.numel() for p_ in model.parameters())
    print(f"[{arm}] 官方模型 {n_params} 参数，训练 {len(train_d)} 样本 × {epochs} epochs，主批 {BATCH}", file=sys.stderr, flush=True)
    fpr_curve, epoch_log = [], []
    ec, ey = eval_clean
    rng = random.Random(SEED)
    adv_cache: dict[int, list[str]] = {}
    quota = BATCH // 2
    n = len(train_d)
    for ep in range(1, epochs + 1):
        model.train()
        order = list(range(n)); random.Random(SEED + ep).shuffle(order)
        t0 = time.time()
        nb = (n + BATCH - 1) // BATCH
        for bi in range(nb):
            idx = order[bi * BATCH:(bi + 1) * BATCH]
            batch_d = [train_d[i] for i in idx]
            batch_y = train_y[idx]
            n_main = len(batch_d)
            if arm == "B":
                adv_batch = [adv_cache.setdefault(i, [perturb2(train_d[i], rng)])[0]
                             for i in idx if train_y[i] == 1]
            elif arm in ("D", "F"):
                mal_idx = [i for i in idx if train_y[i] == 1]
                cands, owner = [], []
                for i in mal_idx:
                    if i not in adv_cache:
                        base = perturb2(train_d[i], rng)
                        adv_cache[i] = [perturb2(base, rng) for _ in range(4)]
                    for v in adv_cache[i]:
                        cands.append(v); owner.append(i)
                adv_batch = []
                if cands:
                    model.eval()
                    with torch.inference_mode():
                        _sc = []
                        for off in range(0, len(cands), EVAL_BATCH):
                            _tk = official.encode_subword(cands[off:off + EVAL_BATCH], tokenizer).to(DEVICE)
                            _ch = official.encode_char(cands[off:off + EVAL_BATCH]).to(DEVICE)
                            with autocast_ctx():
                                _tf, _cf = diag.branch_features(model, _tk, _ch)
                            _sc.append(torch.softmax(
                                model.classifier_head(torch.cat([_tf, _cf], dim=1)).float(), dim=1)[:, 1].cpu().numpy())
                    fooled = (np.concatenate(_sc) < 0.5).astype(np.float64)
                    groups: dict[int, list[int]] = {}
                    for j, o in enumerate(owner):
                        groups.setdefault(o, []).append(j)
                    scored: list[tuple[float, int]] = []
                    for js in groups.values():
                        f = fooled[js]; g = f - f.mean()
                        scored.extend((float(g[k]), j) for k, j in enumerate(js))
                    scored.sort(key=lambda t: -t[0])
                    adv_batch = [cands[j] for _, j in scored[:quota]]
                    model.train()
            else:
                adv_batch = []
            if adv_batch:
                batch_d = batch_d + adv_batch
                batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            y_t = torch.from_numpy(batch_y).long().to(DEVICE)
            opt.zero_grad(set_to_none=True)
            loss_log = 0.0
            n_tot = len(batch_d)
            for s in range(0, n_tot, BATCH):
                sub_d = batch_d[s:s + BATCH]
                sub_y = y_t[s:s + BATCH]
                tok = official.encode_subword(sub_d, tokenizer).to(DEVICE)
                ch = official.encode_char(sub_d).to(DEVICE)
                with autocast_ctx():
                    tf, cf = diag.branch_features(model, tok, ch)
                    logits2 = model.classifier_head(torch.cat([tf, cf], dim=1))
                logits2 = logits2.float()
                p_ = torch.softmax(logits2, dim=1)
                ce = torch.nn.functional.cross_entropy(logits2, sub_y, reduction="none")
                if arm in ("F", "G"):
                    fooled_b = (p_[:, 1] >= 0.5) & (sub_y == 0)
                    w = torch.ones(len(sub_y), device=DEVICE)
                    w[fooled_b] = BETA_BENIGN
                    loss_s = (ce * w).sum() / n_tot
                else:
                    loss_s = ce.sum() / n_tot
                loss_s.backward()
                loss_log += loss_s.item()
            opt.step()
            if bi % 500 == 0:
                eta = (time.time() - t0) / (bi + 1) * (nb - bi - 1)
                print(f"[{arm} 心跳] epoch {ep} 批 {bi+1}/{nb} loss={loss_log:.4f} ETA {eta/60:.1f} min", file=sys.stderr, flush=True)
        model.eval()
        fpr_now = metrics(model, tokenizer, ec, ey, tok_mean, char_mean)["FPR"]
        fpr_curve.append({"epoch": ep, "clean_FPR": fpr_now})
        epoch_log.append({"epoch": ep, "clean_FPR": fpr_now, "seconds": round(time.time() - t0, 1)})
        print(f"[{arm} 里程碑] epoch {ep}/{epochs} 干净 FPR={fpr_now:.4f}（{time.time()-t0:.1f}s）", file=sys.stderr, flush=True)
        if run is not None:
            run.log({"clean_FPR": fpr_now, "epoch": ep})
        # 每 epoch 断点（原子）
        (OUT / f"epochlog_{arm}.json").write_text(json.dumps(epoch_log, ensure_ascii=False, indent=1), encoding="utf-8")
    model.eval()
    clean = metrics(model, tokenizer, ec, ey, tok_mean, char_mean)
    result = {"clean": clean, "fpr_curve": fpr_curve, "n_params": n_params,
              "n_train": len(train_d), "epochs": epochs}
    for pname, panel in (("adv_k2", eval_adv_k2), ("adv_krand", eval_adv_krand), ("adv_maskdga", eval_adv_mask)):
        pa, pay = panel
        result[pname] = metrics(model, tokenizer, pa, pay, tok_mean, char_mean)
        print(f"[{arm} 面板] {pname}: FNR={result[pname]['FNR']:.4f}", file=sys.stderr, flush=True)
    # 正式：state_dict 落盘
    torch.save(model.state_dict(), OUT / f"state_{arm}.pt")
    return result


def main() -> None:
    global BATCH, EPOCHS
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="A,B,D,F,G")
    ap.add_argument("--batch", type=int, default=BATCH)
    ap.add_argument("--epochs", type=int, default=EPOCHS)
    ap.add_argument("--target-limit", type=int, default=200000, help="目标知情面板每年每类抽样上限（0=全量）")
    a = ap.parse_args()
    BATCH = a.batch; EPOCHS = a.epochs
    arms = tuple(a.arms.split(","))
    OUT.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(SEED); np.random.seed(SEED); random.seed(SEED)
    print(f"[正式] 臂={arms} 批={BATCH} epochs={EPOCHS} 种子={SEED} 设备={DEVICE} bf16={USE_BF16}", file=sys.stderr, flush=True)

    tokenizer = official.PreTrainedTokenizerFast(
        tokenizer_file=str(REF / "artifacts/tokenizer/tokenizer-0-30522-both.json"))
    model0 = official.load_model(REF, CKPT, DEVICE)

    train_d, train_y = load_train()
    print(f"[数据] 训练合并 {len(train_d)} 域（良性 {int((train_y==0).sum())} / DGA {int((train_y==1).sum())}）", file=sys.stderr, flush=True)
    val_d, val_y = [], []
    for stem in VAL_FILES:
        d = load_domains(stem)
        val_d.extend(d); val_y.extend([0 if "benign" in stem else 1] * len(d))
    val_y = np.asarray(val_y, dtype=bool)
    print(f"[数据] 源验证 {len(val_d)} 域", file=sys.stderr, flush=True)

    # 中和均值：训练数据特征太大，用 T17 val 30 万域重算（与 screening 同口径）
    zt = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_benign_val.parquet", columns=["domain"]).column(0).to_pylist()
    zd = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_dga_val.parquet", columns=["domain"]).column(0).to_pylist()
    _tok, _char = diag.extract_features(model0, tokenizer, zt + zd, DEVICE, EVAL_BATCH)
    tok_mean = _tok.mean(axis=0, dtype=np.float64).astype(np.float32)
    char_mean = _char.mean(axis=0, dtype=np.float64).astype(np.float32)
    del _tok, _char, zt, zd

    rng = random.Random(SEED)
    adv_src = [str(x) for x in load_domains("T18_dga_val")]
    eval_adv_k2 = ([perturb2(d, rng) for d in adv_src], np.ones(len(adv_src), dtype=bool))
    eval_adv_krand = ([perturb2(d, rng) for d in adv_src], np.ones(len(adv_src), dtype=bool))
    eval_adv_mask = ([perturb_half(d, rng) for d in adv_src], np.ones(len(adv_src), dtype=bool))
    print(f"[面板] 对抗三面板各 {len(adv_src)} 域", file=sys.stderr, flush=True)

    # 目标知情面板（T20-25 无后缀；T20 缺失则登记跳过）
    target_panels: dict[str, tuple[list[str], np.ndarray]] = {}
    for y in TARGET_YEARS:
        stems = [f"T{y}_benign", f"T{y}_dga"]
        missing = [s for s in stems if not (DATA / "DRIFT_input_eSLD" / f"{s}.parquet").is_file()]
        if missing:
            print(f"[面板] T{y} 缺失文件 {missing}，该年跳过并登记", file=sys.stderr, flush=True)
            continue
        lim = a.target_limit
        td, ty = [], []
        for s in stems:
            d = load_domains(s)
            if lim and len(d) > lim:
                random.Random(SEED + y).shuffle(d); d = d[:lim]
            td.extend(d); ty.extend([0 if "benign" in s else 1] * len(d))
        target_panels[f"T{y}"] = (td, np.asarray(ty, dtype=bool))
        print(f"[面板] T{y} {len(td)} 域", file=sys.stderr, flush=True)

    # SwanLab（online 失败回退 local，不阻塞）
    run = None
    try:
        import swanlab
        run = swanlab.init(project="ch3-drift-official", experiment_name=f"p2p3-full-{'-'.join(arms)}",
                           config={"arms": arms, "batch": BATCH, "epochs": EPOCHS, "seed": SEED,
                                   "n_train": len(train_d), "beta_benign": BETA_BENIGN},
                           mode=os.environ.get("SWANLAB_MODE", "online"))
        print(f"[swanlab] run url: {run.url}", file=sys.stderr, flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[swanlab] 初始化失败（回退本地日志）：{exc}", file=sys.stderr, flush=True)

    results: dict = {}
    for arm in arms:
        t0 = time.time()
        r = train_arm(arm, train_d, train_y, tokenizer, tok_mean, char_mean,
                      (val_d, val_y), eval_adv_k2, eval_adv_krand, eval_adv_mask, EPOCHS, run=run)
        r["wall_seconds"] = round(time.time() - t0, 1)
        for yname, (pa, pay) in target_panels.items():
            m = official.load_model(REF, OUT / f"state_{arm}.pt", DEVICE)
            r[f"target_{yname}"] = metrics(m, tokenizer, pa, pay, tok_mean, char_mean)
            print(f"[{arm} 目标] {yname}: FPR={r[f'target_{yname}']['FPR']:.4f} FNR={r[f'target_{yname}']['FNR']:.4f}", file=sys.stderr, flush=True)
        results[arm] = r
        (OUT / f"result_{arm}.json").write_text(
            json.dumps({k: v for k, v in r.items()}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[里程碑] {arm} 完成 {r['wall_seconds']}s -> result_{arm}.json", file=sys.stderr, flush=True)
    if run is not None:
        run.finish()
    (OUT / "result_all.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[里程碑] 全部臂完成 -> result_all.json", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
