#!/usr/bin/env python3
"""DRIFT 官方双分支骨干的源期共同成员 A/B/D/G/F 筛选运行器。

固定哈希源训练与源验证成员从现有 Parquet 按需读取；本入口是源期筛选，
指标仍使用历史 0.5 阈值与筛选攻击面板，不代表正式低误报评价。
每臂每轮保存完整训练断点，运行状态和单臂结果保存在独占运行目录。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import resource
import sys
import time
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path

import fcntl

import numpy as np
import pyarrow.parquet as pq
import torch

# 环境变量 LLM_PROBE_ROOT 覆盖项目根（服务器设为 /root/autodl-tmp/thesis/experiments/llm_probe）
ROOT = Path(os.environ.get(
    "LLM_PROBE_ROOT",
    "/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe",
))
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import ch3_drift_official_branch_conflict_diagnostic as diag
import ch3_drift_official_checkpoint_t17_eval as official
import ch3_drift_f_source_eligibility as eligibility
import ch3_drift_formal_contract as formal_contract

REF = ROOT / "runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2"
CKPT = ROOT / "runs/models/drift-official-dsn2026/finetuning.pt"
DATA = ROOT / "runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521"
OUT = Path(os.environ.get("P2P3_OUT", Path(__file__).resolve().parent))
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "mps")
BATCH = 128            # 训练批量：冻结规格，不改
EVAL_BATCH = 1024 if DEVICE.type == "cuda" else 128   # 评价批量只影响吞吐不改指标
USE_BF16 = DEVICE.type == "cuda"                      # 对齐官方 BF16 训练


def autocast_ctx():
    """仅 CUDA 启用 bf16 autocast；MPS 返回 nullcontext——
    torch.autocast(enabled=False) 在 MPS 上仍会改变 nn.Transformer 执行路径，
    触发未实现的 _nested_tensor_from_mask_left_aligned 算子（2026-09-10 实测）。"""
    return torch.autocast(device_type=DEVICE.type, dtype=torch.bfloat16) if USE_BF16 else nullcontext()
LR_HEAD = 1e-4
LR_BACKBONE = 1e-6
EPOCHS = 3
SEED = 42
BETA_KL = 1.0  # E 臂 KL 权重：任务化设定（GRPO 家族 β 无文献精确值），首轮源侧标定
ALPHA_CVAR = 0.05   # J 臂 CVaR 尾部质量（任务化设定）
LAMBDA_CVAR = 0.1   # J 臂 CVaR 项权重：量级对齐恶意 CE 项，避免 I 型尾部劫持（任务化设定）
TAU_LR = 0.01       # J 臂对偶变量 τ 的解析下降步长
ALPHA = "abcdefghijklmnopqrstuvwxyz0123456789-"
ARM_DISPLAY_NAMES = {
    "A": "干净微调",
    "B": "朴素字符增广",
    "D": "组中心跨组选择",
    "G": "良性条件误报补偿",
    "F": "组中心选择＋良性补偿",
    "MP": "混合曝光＋误报保护",
}
SAFE_RESULT_NAME = re.compile(r"[A-Za-z0-9._-]+\Z")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(path: Path, payload: dict) -> None:
    partial = path.with_name(path.name + ".partial")
    with partial.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(partial, path)


def write_checkpoint_atomic(path: Path, payload: dict) -> None:
    partial = path.with_name(path.name + ".partial")
    with partial.open("wb") as stream:
        torch.save(payload, stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(partial, path)


def rss_mib() -> float:
    # macOS 的 ru_maxrss 单位为字节；该值是进程历史峰值。
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)


def arm_label(arm: str) -> str:
    """返回同时包含稳定短键和机制展示名的日志标签。"""
    display_name = ARM_DISPLAY_NAMES.get(arm)
    return f"{arm}（{display_name}）" if display_name else arm


def result_name_arg(value: str) -> str:
    """校验结果文件名，拒绝路径分隔符和特殊文件名。"""
    if value in {".", ".."} or not SAFE_RESULT_NAME.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "结果文件名只能包含 ASCII 字母、数字、点、下划线和连字符，且不能是 . 或 .."
        )
    return value


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
    """MaskDGA 半替换近似（冻结 v2 算子，与 E-A1 v2 同源）：随机替换 SLD 一半位置。
    主判据面板算子：官方模型实测相对降 69.1%，可打开 AP 判据空间（k2 面板 AP 封顶无空间）。"""
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


def perturb1(domain: str, rng: random.Random) -> str:
    """1 位替换（弱攻击档，L 臂课程 epoch 1 用）：随机替换 SLD 的 1 个位置。"""
    body = domain.rsplit(".", 1)[0]
    tail = "." + domain.rsplit(".", 1)[1] if "." in domain else ""
    if len(body) < 1:
        return domain
    b = list(body)
    i = rng.randrange(len(body))
    c = rng.choice(ALPHA)
    while c == b[i]:
        c = rng.choice(ALPHA)
    b[i] = c
    return "".join(b) + tail


def gen_variants_L(domain: str, ep: int, rng: random.Random) -> list:
    """L 臂课程档位算子：epoch 1=1 位(弱) → 2=2 位(中) → 3=半替换(强)。
    相邻档位分布漂移最小化（Shi&Liu 2024 课程 AT 在线视角的调度原则）。"""
    if ep == 1:
        return [perturb1(domain, rng) for _ in range(4)]
    elif ep == 2:
        return [perturb2(domain, rng) for _ in range(4)]
    return [perturb_half(domain, rng) for _ in range(4)]


def load_split(limit: int) -> tuple[list[str], np.ndarray]:
    tb = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_benign_train.parquet").to_pylist()[:limit]
    td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_dga_train.parquet").to_pylist()[:limit]
    domains = [str(r["domain"]) for r in tb] + [str(r["domain"]) for r in td]
    labels = np.asarray([0] * len(tb) + [1] * len(td), dtype=np.int64)
    return domains, labels


def disable_nested_tensor(model) -> None:
    encoders = [module for module in model.modules() if isinstance(module, torch.nn.TransformerEncoder)]
    if len(encoders) != 2:
        raise RuntimeError(f"预期两个TransformerEncoder，实际为{len(encoders)}")
    for encoder in encoders:
        encoder.enable_nested_tensor = False
        encoder.use_nested_tensor = False


def load_mps_model():
    model = official.load_model(REF, CKPT, DEVICE)
    disable_nested_tensor(model)
    return model


def load_fixed_source_members(candidate_spec_value: str, purpose: str) -> tuple[list[str], np.ndarray, list[dict]]:
    if purpose not in {"source_train", "source_validation"}:
        raise ValueError("共同成员入口只允许源训练或源验证用途")
    config, _ = formal_contract.load_config("configs/ch3-drift-formal-evaluation-v1.json")
    spec_path = formal_contract.resolve_repo_relative(candidate_spec_value, must_exist=True)
    spec = eligibility.load_spec(spec_path)
    role_map = {role["role"]: role for role in config["input_roles"]}
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise RuntimeError("共同成员入口需要PyArrow") from exc
    domains: list[str] = []
    labels: list[int] = []
    receipts: list[dict] = []
    for entry in spec["roles"][purpose]:
        role_started = time.time()
        print(
            f"[源成员选择] 开始 purpose={purpose} role={entry['role']} count={entry['count']}",
            file=sys.stderr,
            flush=True,
        )
        role = role_map.get(entry["role"])
        if role is None:
            raise ValueError(f"成员角色不在正式配置中：{entry['role']}")
        valid = role["scope"] == "source" and (
            role["split"] in {"train", "test"} if purpose == "source_train" else role["split"] == "val"
        )
        if not valid:
            raise ValueError(f"成员角色用途不符：{entry['role']}")
        path = formal_contract.resolve_repo_relative(role["path"], must_exist=True)
        selected, receipt = eligibility.select_role(
            parquet=parquet,
            path=path,
            role=role,
            count=entry["count"],
            revision=config["data_revision"],
            namespace=spec["corpus_namespace"],
        )
        domains.extend(selected)
        labels.extend([0 if role["class"] == "benign" else 1] * len(selected))
        receipts.append(receipt)
        print(
            f"[源成员选择] 完成 role={entry['role']} raw_rows={receipt['raw_rows']} "
            f"selected={len(selected)} elapsed={time.time() - role_started:.1f}s",
            file=sys.stderr,
            flush=True,
        )
    if not domains or len(domains) != len(labels):
        raise RuntimeError(f"{purpose} 共同成员为空或标签错位")
    return domains, np.asarray(labels, dtype=np.int64), receipts


def source_feature_means(model, tokenizer, domains: list[str]) -> tuple[np.ndarray, np.ndarray]:
    token_sum = None
    char_sum = None
    count = 0
    model.eval()
    with torch.inference_mode():
        for offset in range(0, len(domains), EVAL_BATCH):
            chunk = domains[offset:offset + EVAL_BATCH]
            token_ids = official.encode_subword(chunk, tokenizer).to(DEVICE)
            char_ids = official.encode_char(chunk).to(DEVICE)
            token_feature, char_feature = diag.branch_features(model, token_ids, char_ids)
            token_value = token_feature.detach().cpu().numpy().sum(axis=0, dtype=np.float64)
            char_value = char_feature.detach().cpu().numpy().sum(axis=0, dtype=np.float64)
            token_sum = token_value if token_sum is None else token_sum + token_value
            char_sum = char_value if char_sum is None else char_sum + char_value
            count += len(chunk)
    if count != len(domains) or token_sum is None or char_sum is None:
        raise RuntimeError("源特征均值计算未覆盖全部共同成员")
    return (token_sum / count).astype(np.float32), (char_sum / count).astype(np.float32)


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
    s = np.concatenate(scores)
    from sklearn.metrics import average_precision_score
    pred = s >= 0.5
    mal, ben = labels01, ~labels01
    fp = int((pred & ben).sum()); fn = int((~pred & mal).sum())
    tp = int((pred & mal).sum()); tn = int((~pred & ben).sum())
    return {"AP": float(average_precision_score(labels01, s)),
            "FPR": fp / max(fp + tn, 1), "FNR": fn / max(fn + tp, 1),
            "F1": tp / max(tp + 0.5 * (fp + fn), 1), "FP": fp, "FN": fn, "n": len(s)}


def train_arm(arm: str, train_d: list[str], train_y: np.ndarray,
              tokenizer, tok_mean, char_mean,
              eval_clean: tuple[list[str], np.ndarray], eval_adv: tuple[list[str], np.ndarray],
              epochs: int, ref_model=None, checkpoint_path: Path | None = None,
              run_identity: dict | None = None, progress=None) -> dict:
    # 每臂使用相同的模型随机轨迹起点；断点恢复随后覆盖为保存的状态。
    torch.manual_seed(SEED)
    model = load_mps_model()
    n_params = sum(p.numel() for p in model.parameters())
    # 分层 lr：官方模型参数名无 "backbone"，按分类头匹配（classifier_head=1e-4，骨干=1e-6）
    opt = torch.optim.Adam([
        {"params": [p_ for n_, p_ in model.named_parameters() if "classifier_head" not in n_], "lr": LR_BACKBONE},
        {"params": [p_ for n_, p_ in model.named_parameters() if "classifier_head" in n_], "lr": LR_HEAD},
    ])
    n_head = sum(p_.numel() for n_, p_ in model.named_parameters() if "classifier_head" in n_)
    label = arm_label(arm)
    print(f"[{label}] 分层 lr：骨干 {sum(p_.numel() for p_ in model.parameters()) - n_head} 参数 @1e-6，分类头 {n_head} 参数 @1e-4", file=sys.stderr, flush=True)
    print(f"[{label}] 官方模型 {n_params} 参数，训练 {len(train_d)} 样本 × {epochs} epochs", file=sys.stderr, flush=True)
    fpr_curve: list = []
    ec, ey = eval_clean
    ea, eay = eval_adv
    rng = random.Random(SEED)
    adv_cache: dict[int, list[str]] = {}
    adv_cache_p: dict[int, list] = {}  # P 臂 K=8 扩展缓存
    adv_cache_l: dict[tuple, list] = {}  # L 臂课程缓存（键含 epoch）
    adv_cache_m: dict[tuple, list] = {}  # M 臂 Mix 缓存（键=(样本, 档位)）
    benign_cache: dict[int, list[str]] = {}
    benign_rng = random.Random(SEED + 7)  # 良性变体独立种子，不与恶意变体序列耦合
    tau_val = torch.tensor(0.5, device=DEVICE)  # J 臂对偶变量 τ（RU 形式 min_τ）
    first_epoch = 1
    if checkpoint_path is not None and checkpoint_path.exists():
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        if checkpoint["identity"] != run_identity or checkpoint["arm"] != arm:
            raise RuntimeError(f"{label} 断点身份与当前运行不一致")
        completed_epoch = int(checkpoint["completed_epoch"])
        if not 0 <= completed_epoch <= epochs:
            raise RuntimeError(f"{label} 断点轮次越界：{completed_epoch}")
        model.load_state_dict(checkpoint["model"])
        opt.load_state_dict(checkpoint["optimizer"])
        rng.setstate(checkpoint["attack_rng"])
        benign_rng.setstate(checkpoint["benign_rng"])
        torch.set_rng_state(checkpoint["cpu_rng"])
        if DEVICE.type == "mps":
            torch.mps.set_rng_state(checkpoint["mps_rng"])
        elif DEVICE.type == "cuda":
            torch.cuda.set_rng_state(checkpoint["cuda_rng"])
        adv_cache = checkpoint["adv_cache"]
        adv_cache_p = checkpoint["adv_cache_p"]
        adv_cache_l = checkpoint["adv_cache_l"]
        adv_cache_m = checkpoint["adv_cache_m"]
        benign_cache = checkpoint["benign_cache"]
        tau_val = checkpoint["tau_val"].to(DEVICE)
        fpr_curve = checkpoint["fpr_curve"]
        first_epoch = completed_epoch + 1
        print(f"[{label} 恢复] 已完成 {completed_epoch}/{epochs} 轮，从第 {first_epoch} 轮继续", file=sys.stderr, flush=True)
    if progress is not None:
        progress(arm, "running", first_epoch - 1, 0, 0, None, None)
    n = len(train_d)
    for ep in range(first_epoch, epochs + 1):
        model.train()
        order = list(range(n)); random.Random(SEED + ep).shuffle(order)
        t0 = time.time()
        nb = (n + BATCH - 1) // BATCH
        for bi in range(nb):
            idx = order[bi * BATCH:(bi + 1) * BATCH]
            batch_d = [train_d[i] for i in idx]
            batch_y = train_y[idx]
            n_main = len(batch_d)  # 拼接变体前的主样本数（E 臂 KL 只锚定主样本段）
            if arm in ("B", "C"):
                adv_batch = []
                for i in idx:
                    if train_y[i] == 1:
                        if i not in adv_cache:
                            base = perturb2(train_d[i], rng)
                            adv_cache[i] = [base] if arm == "B" else [perturb2(base, rng) for _ in range(4)]
                        if arm == "B":
                            adv_batch.append(adv_cache[i][0])
                        else:
                            adv_batch.extend(adv_cache[i])  # C 臂：K=4 变体全部入批，组相对加权才作用在变体上
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            elif arm in ("N", "N2"):
                # N 臂（per-group top-1 训练对照，BiB-CP 型分析参照算子）与
                # N2 臂（per-group 选择 + 良性误报加权×3.0）：
                # 与 D 同预算（64 变体、批 192）、同变体生成（perturb2）、同组结构（K=4），
                # 唯一差量 = 选择算子：每组内取 u 最大（s 最小=最难）的 1 个入批，
                # 无跨组竞争、无中心化。N2 在 N 基础上加组件 2（误报加权），对照 F（cross-group+加权）。
                # 训练级发现（N 首轮）：per-group 检出优于 cross-group（反 V1 捕获率序）——
                # 覆盖-强度权衡实证（chatgpt4 预警、对象三式 3.3 组重加权项）。
                mal_idx = [i for i in idx if train_y[i] == 1]
                cands: list[str] = []
                cand_owner: list[int] = []
                for i in mal_idx:
                    if i not in adv_cache:
                        base = perturb2(train_d[i], rng)
                        adv_cache[i] = [perturb2(base, rng) for _ in range(4)]
                    for v in adv_cache[i]:
                        cands.append(v)
                        cand_owner.append(i)
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
                            _lg = model.classifier_head(torch.cat([_tf, _cf], dim=1))
                            _sc.append(torch.softmax(_lg.float(), dim=1)[:, 1].cpu().numpy())
                    p_cand = np.concatenate(_sc)
                    groups: dict[int, list[int]] = {}
                    for j, o in enumerate(cand_owner):
                        groups.setdefault(o, []).append(j)
                    for js in groups.values():  # 每组取 s 最小（最难）1 个，无跨组竞争
                        adv_batch.append(cands[js[int(np.argmin(p_cand[js]))]])
                    model.train()
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
                # L 臂（攻击难度课程 × 组相对过滤，Shi&Liu 2024 漂移最小化框架的 DGA 实例化）：
                # epoch 1=1 位替换(弱) → 2=2 位(中) → 3=半替换(强)，相邻档位分布漂移最小；
                # 每档内部组相对过滤与 D 完全一致。判据（冻结，方案 §5.12）：
                # L vs D 同 screening 规格：maskdga 面板检出改善，或检出持平+干净 FPR 更低；
                # 理论预期（Shi&Liu 界）：课程版逐 epoch FPR 曲线更平稳、最终检出 ≥ D。
                mal_idx = [i for i in idx if train_y[i] == 1]
                cands: list[str] = []
                cand_owner: list[int] = []
                for i in mal_idx:
                    key = (i, ep)
                    if key not in adv_cache_l:
                        adv_cache_l[key] = gen_variants_L(train_d[i], ep, rng)
                    for v in adv_cache_l[key]:
                        cands.append(v)
                        cand_owner.append(i)
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
                            _lg = model.classifier_head(torch.cat([_tf, _cf], dim=1))
                            _sc.append(torch.softmax(_lg.float(), dim=1)[:, 1].cpu().numpy())
                    p_cand = np.concatenate(_sc)
                    fooled = (p_cand < 0.5).astype(np.float64)
                    groups: dict[int, list[int]] = {}
                    for j, o in enumerate(cand_owner):
                        groups.setdefault(o, []).append(j)
                    scored: list[tuple[float, int]] = []
                    for js in groups.values():
                        f = fooled[js]
                        adv_g = f - f.mean()
                        scored.extend((float(adv_g[k]), j) for k, j in enumerate(js))
                    scored.sort(key=lambda t: (-t[0], t[1]))  # 确定性并列破法（notes.md §J 修正②）
                    adv_batch = [cands[j] for _, j in scored[:64]]
                    model.train()
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            elif arm == "P":
                # P 臂（搜索预算扩展，定理 3/V3 的训练级检验）：与 D 唯一差量 = K 4→8
                # （每干净恶意域名 8 个 perturb2 变体、候选池 256→512、配额不变 64）——
                # V3 预测每干净样本覆盖缺口从 0.30 收至 ~0.16（Uniform 1/9），
                # 若训练收益随覆盖单调则 P 优于 D。判据同 v2 口径（Mask 改善+FPR 门）。
                mal_idx = [i for i in idx if train_y[i] == 1]
                cands: list[str] = []
                cand_owner: list[int] = []
                for i in mal_idx:
                    if i not in adv_cache_p:
                        base = perturb2(train_d[i], rng)
                        adv_cache_p[i] = [perturb2(base, rng) for _ in range(8)]
                    for v in adv_cache_p[i]:
                        cands.append(v)
                        cand_owner.append(i)
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
                            _lg = model.classifier_head(torch.cat([_tf, _cf], dim=1))
                            _sc.append(torch.softmax(_lg.float(), dim=1)[:, 1].cpu().numpy())
                    p_cand = np.concatenate(_sc)
                    fooled = (p_cand < 0.5).astype(np.float64)
                    groups: dict[int, list[int]] = {}
                    for j, o in enumerate(cand_owner):
                        groups.setdefault(o, []).append(j)
                    scored: list[tuple[float, int]] = []
                    for js in groups.values():
                        f = fooled[js]
                        adv_g = f - f.mean()
                        scored.extend((float(adv_g[k]), j) for k, j in enumerate(js))
                    scored.sort(key=lambda t: (-t[0], t[1]))
                    adv_batch = [cands[j] for _, j in scored[:64]]
                    model.train()
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            elif arm in ("M", "MP"):
                # M 臂（Mix 对照，HARD-GATE 外审 §4.2）：三档候选池每批均匀混合、无课程顺序，
                # 选择机制与 L/D 完全一致。归因结构：L−M = 课程顺序增量；M−D = 新增曝光增量。
                # MP 臂（混合曝光＋误报保护）：复用 M 的候选生成与跨组选择，
                # 并在损失分支复用 F 的真良性误报 hard ×3.0 加权；除此之外不改变训练合同。
                # 判据 v2（冻结）：主判据=Mask 检出改善且 FPR 代价 Δ_B≤+0.005，或 Mask 非劣(|Δ_M|≤0.003)且 FPR 改善；
                # 配对变化 Δ_B=(N_良性0→1−N_良性1→0)/N_良性 需报告（±0.003 为概率绝对差 0.3pp）
                mal_idx = [i for i in idx if train_y[i] == 1]
                cands: list[str] = []
                cand_owner: list[int] = []
                for i in mal_idx:
                    for tier in (1, 2, 3):
                        key = (i, tier)
                        if key not in adv_cache_m:
                            if tier == 1:
                                adv_cache_m[key] = [perturb1(train_d[i], rng) for _ in range(4)]
                            elif tier == 2:
                                adv_cache_m[key] = [perturb2(train_d[i], rng) for _ in range(4)]
                            else:
                                adv_cache_m[key] = [perturb_half(train_d[i], rng) for _ in range(4)]
                        for v in adv_cache_m[key]:
                            cands.append(v)
                            cand_owner.append(i)
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
                            _lg = model.classifier_head(torch.cat([_tf, _cf], dim=1))
                            _sc.append(torch.softmax(_lg.float(), dim=1)[:, 1].cpu().numpy())
                    p_cand = np.concatenate(_sc)
                    fooled = (p_cand < 0.5).astype(np.float64)
                    groups: dict[int, list[int]] = {}
                    for j, o in enumerate(cand_owner):
                        groups.setdefault(o, []).append(j)
                    scored: list[tuple[float, int]] = []
                    for js in groups.values():
                        f = fooled[js]
                        adv_g = f - f.mean()
                        scored.extend((float(adv_g[k]), j) for k, j in enumerate(js))
                    scored.sort(key=lambda t: (-t[0], t[1]))
                    adv_batch = [cands[j] for _, j in scored[:64]]
                    model.train()
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            elif arm in ("D", "E", "F", "H"):
                # D/E 臂（GFPO 组相对过滤，2508.09726 §3 式(2) + Drichel 2024 §4.4.2 配比锚点）：
                # 与 B 同为 64 变体配额（批次规模 192、恶意:良性倾斜度相同），唯一差量 =
                # 变体选择机制：每恶意样本 K=4 变体为组，组内 fooled（当前模型判良性）为优势，
                # "fooled − 组均值"降序取 top-64 入批（被拒变体零梯度，GFPO 过滤式优势）
                # E 臂 = D + 参考模型 KL 漂移约束（GRPO 2402.03300 式(3) −β·D_KL[π_θ‖π_ref] 任务化：
                # π_ref = 冻结初始判别器，KL 只作用于干净主样本段——干净输出分布锚定，
                # 对抗变体段自由硬化；β 为任务化设定（无文献精确值），首轮取 1.0 源侧标定）
                mal_idx = [i for i in idx if train_y[i] == 1]
                cands: list[str] = []
                cand_owner: list[int] = []
                for i in mal_idx:
                    if i not in adv_cache:
                        base = perturb2(train_d[i], rng)
                        adv_cache[i] = [perturb2(base, rng) for _ in range(4)]
                    for v in adv_cache[i]:
                        cands.append(v)
                        cand_owner.append(i)
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
                            _lg = model.classifier_head(torch.cat([_tf, _cf], dim=1))
                            _sc.append(torch.softmax(_lg.float(), dim=1)[:, 1].cpu().numpy())
                    p_cand = np.concatenate(_sc)
                    fooled = (p_cand < 0.5).astype(np.float64)
                    groups: dict[int, list[int]] = {}
                    for j, o in enumerate(cand_owner):
                        groups.setdefault(o, []).append(j)
                    scored: list[tuple[float, int]] = []
                    for js in groups.values():
                        f = fooled[js]
                        adv_g = f - f.mean()
                        scored.extend((float(adv_g[k]), j) for k, j in enumerate(js))
                    scored.sort(key=lambda t: -t[0])
                    adv_batch = [cands[j] for _, j in scored[:64]]
                    model.train()
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
                if arm == "H":
                    # H 臂良性侧（对称组相对，设计修正①②③④见 notes.md §J）：
                    # CharBot 近邻组（每良性样本 K=4），误报优势 = 连续分数 − 组均值，
                    # 跨组配额 top-32 全局竞争入批（标签 0）；与 F 的差量 = 良性侧从
                    # 「真样本加权 3.0」换为「组相对选择近邻变体」，恶意侧与 D/F 完全相同
                    ben_idx = [i for i in idx if train_y[i] == 0]
                    bcands: list[str] = []
                    bowner: list[int] = []
                    for i in ben_idx:
                        if i not in benign_cache:
                            benign_cache[i] = [perturb2(train_d[i], benign_rng) for _ in range(4)]
                        for v in benign_cache[i]:
                            bcands.append(v)
                            bowner.append(i)
                    adv_ben: list[str] = []
                    if bcands:
                        model.eval()
                        with torch.inference_mode():
                            _bs = []
                            for off in range(0, len(bcands), EVAL_BATCH):
                                _tk = official.encode_subword(bcands[off:off + EVAL_BATCH], tokenizer).to(DEVICE)
                                _ch = official.encode_char(bcands[off:off + EVAL_BATCH]).to(DEVICE)
                                with autocast_ctx():
                                    _tf, _cf = diag.branch_features(model, _tk, _ch)
                                _bs.append(torch.softmax(
                                    model.classifier_head(torch.cat([_tf, _cf], dim=1)).float(), dim=1)[:, 1].cpu().numpy())
                        p_ben = np.concatenate(_bs)
                        groups_b: dict[int, list[int]] = {}
                        for j, o in enumerate(bowner):
                            groups_b.setdefault(o, []).append(j)
                        scored_b: list[tuple[float, int]] = []
                        for js in groups_b.values():
                            pb = p_ben[js]
                            adv_g = pb - pb.mean()  # 设计修正①：连续分数中心化（非二值 fooled）
                            scored_b.extend((float(adv_g[k]), j) for k, j in enumerate(js))
                        scored_b.sort(key=lambda t: (-t[0], t[1]))  # 设计修正②：确定性并列破法
                        adv_ben = [bcands[j] for _, j in scored_b[:32]]  # 设计修正③④：显式跨组配额
                        model.train()
                    if adv_ben:
                        batch_d = batch_d + adv_ben
                        batch_y = np.concatenate([batch_y, np.zeros(len(adv_ben), dtype=np.int64)])
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            # MPS 带梯度反向 batch 上限 128：B/C 臂拼接变体后超限（192/320），
            # 用 128 子批梯度累积等效实现同一拼接大 batch 的（加权）平均损失，不改优化语义
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
                if arm == "J":
                    # J 臂 = D + 良性侧 CVaR τ-对偶（Rockafellar-Uryasev population 形式，区别于 I 的 batch top-k）：
                    # loss = 恶意项 + λ·(τ + mean(relu(ce_ben−τ))/α)；τ 每批解析下降更新
                    # （对偶 min_τ 的随机近似：dτ ∝ 1 − (1/α)·frac(ℓ>τ)）。
                    # λ=0.1 量级对齐恶意项，避免 I 型尾部劫持（任务化设定，源侧标定）
                    ben_m = sub_y == 0
                    if ben_m.any():
                        ce_ben = ce[ben_m]
                        cvaR_est = tau_val + torch.relu(ce_ben - tau_val).mean() / ALPHA_CVAR
                        ce_rest = ce[~ben_m].sum() if (~ben_m).any() else ce_ben.sum() * 0
                        loss_s = (ce_rest + LAMBDA_CVAR * cvaR_est * ben_m.sum()) / n_tot
                        with torch.no_grad():
                            tau_val -= TAU_LR * (1.0 - (ce_ben > tau_val).float().mean() / ALPHA_CVAR)
                            tau_val.clamp_(0.0, 20.0)
                    else:
                        loss_s = ce.sum() / n_tot
                elif arm == "I":
                    # I 臂 = D + 良性侧 CVaR_α 尾部软加权（组件 2 的 min-max 任务化）：
                    # 对 batch 内真良性样本的 CE 取 CVaR_α（最坏 α 分位的均值，softplus 连续松弛），
                    # 与恶意侧组相对 top-q 构成同一 min-max 泛函的两个威胁方向实例化。
                    # α=0.05 任务化设定（源侧标定）；理论对偶见 pAUC-DRO/CVaR 文献（本地全文）
                    ben_m = sub_y == 0
                    if ben_m.any():
                        ce_ben = ce[ben_m]
                        k_alpha = max(1, int(0.05 * ce_ben.numel()))
                        tail = torch.topk(ce_ben, k_alpha).values  # 最坏 α 分位（硬 CVaR）
                        cvaR = tail.mean()
                        ce_rest = ce[~ben_m].sum() if (~ben_m).any() else ce_ben.sum() * 0
                        # 恶意侧正常 CE + λ·CVaR_α(良性)；λ=1 对冲 64 变体配额压力（同 F 的量级逻辑）
                        loss_s = (ce_rest + cvaR * ben_m.sum() * 1.0) / n_tot
                    else:
                        loss_s = ce.sum() / n_tot
                elif arm in ("F", "G", "N2", "MP"):
                    # F 臂 = D + 良性误报加权（双侧组相对的良性侧最简形式）；
                    # G 臂 = 只组件 2（无对抗增广、仅良性误报加权）——四臂消融的对称单臂；
                    # N2 臂 = N（per-group 选择）+ 组件 2——对照 F（cross-group+加权）的选择算子检验。
                    # MP 臂 = M（三档混合曝光＋跨组选择）+ 本分支的良性误报保护。
                    # batch 内当前模型判恶意的真良性样本 CE ×3.0，把分布上移的误报拉回。
                    # 权重 3.0 为任务化设定（无文献精确值）：对冲 64 变体配额的恶意侧压力量级，
                    # 源侧标定；若有效再升级为良性 CharBot 近邻组相对完整形态
                    fooled_b = (p_[:, 1] >= 0.5) & (sub_y == 0)
                    w = torch.ones(len(sub_y), device=DEVICE)
                    w[fooled_b] = 3.0
                    loss_s = (ce * w).sum() / n_tot
                elif arm == "C":
                    # 组相对加权：同一恶意样本的 4 变体一组，组内"当前模型判良性(骗过)"为优势，
                    # 正优势变体权重 2.0、未骗过变体 0.5、干净样本 1.0（组相对优势的任务化，
                    # 文献定位：无先例的任务化设定，对照 Drichel 均匀混合）
                    fooled = (p_[:, 1] < 0.5) & (sub_y == 1)
                    w = torch.ones(len(sub_y), device=DEVICE)
                    w[fooled] = 2.0
                    w[(sub_y == 1) & (p_[:, 1] >= 0.5)] = 0.5
                    loss_s = (ce * w).sum() / n_tot
                else:
                    loss_s = ce.sum() / n_tot
                if arm == "E" and ref_model is not None:
                    # E 臂组件 2：干净主样本段的参考模型 KL 锚定（GRPO 式(3) −β·D_KL[π_θ‖π_ref] 任务化）
                    _gl = torch.arange(s, min(s + BATCH, n_tot), device=DEVICE)
                    _m = _gl < n_main
                    if _m.any():
                        _p = p_[_m]
                        _log_p = torch.log(_p.clamp_min(1e-9))
                        with torch.inference_mode():
                            _tf_r, _cf_r = diag.branch_features(ref_model, tok[_m], ch[_m])
                            _lg_r = ref_model.classifier_head(torch.cat([_tf_r, _cf_r], dim=1))
                        _log_p0 = torch.log_softmax(_lg_r.float(), dim=1)
                        _kl = (_p * (_log_p - _log_p0)).sum(dim=1)
                        loss_s = loss_s + BETA_KL * _kl.sum() / n_tot
                loss_s.backward()
                loss_log += loss_s.item()
            opt.step()
            if not math.isfinite(loss_log):
                raise RuntimeError(f"{label} 第 {ep} 轮第 {bi + 1} 批损失非有限值")
            if bi == 0 or (bi + 1) % 20 == 0 or bi + 1 == nb:
                elapsed = time.time() - t0
                rate = (bi + 1) / max(elapsed, 1e-9)
                eta = (nb - bi - 1) / max(rate, 1e-9)
                print(
                    f"[{label} 心跳] epoch={ep}/{epochs} batch={bi + 1}/{nb} "
                    f"loss={loss_log:.6f} elapsed={elapsed:.1f}s "
                    f"rate={rate:.3f}批/s eta={eta / 60:.1f}min rss_peak={rss_mib():.1f}MiB",
                    file=sys.stderr,
                    flush=True,
                )
                if progress is not None:
                    progress(arm, "running", ep, bi + 1, nb, loss_log, None)
        # 逐 epoch 干净 FPR 曲线（文献代理 Q1 裁决：识别"验证损失上升段"，防瞬态误判）
        model.eval()
        clean_now = metrics(model, tokenizer, ec, ey, tok_mean, char_mean)
        adv_now = metrics(model, tokenizer, ea, eay, tok_mean, char_mean)
        fpr_curve.append({"epoch": ep, "clean_FPR": clean_now["FPR"], "attack_FNR": adv_now["FNR"], "attack_AP": adv_now["AP"]})
        print(
            f"[{label} 里程碑] epoch {ep}/{epochs} 完成，"
            f"干净FPR={clean_now['FPR']:.4f} 攻击FNR={adv_now['FNR']:.4f} "
            f"攻击AP={adv_now['AP']:.4f} 耗时={time.time()-t0:.1f}s",
            file=sys.stderr,
            flush=True,
        )
        if checkpoint_path is not None:
            state = {
                "identity": run_identity,
                "arm": arm,
                "completed_epoch": ep,
                "model": model.state_dict(),
                "optimizer": opt.state_dict(),
                "attack_rng": rng.getstate(),
                "benign_rng": benign_rng.getstate(),
                "cpu_rng": torch.get_rng_state(),
                "mps_rng": torch.mps.get_rng_state() if DEVICE.type == "mps" else None,
                "cuda_rng": torch.cuda.get_rng_state() if DEVICE.type == "cuda" else None,
                "adv_cache": adv_cache,
                "adv_cache_p": adv_cache_p,
                "adv_cache_l": adv_cache_l,
                "adv_cache_m": adv_cache_m,
                "benign_cache": benign_cache,
                "tau_val": tau_val.detach().cpu(),
                "fpr_curve": fpr_curve,
            }
            write_checkpoint_atomic(checkpoint_path, state)
        if progress is not None:
            progress(arm, "checkpointed", ep, nb, nb, None, fpr_curve[-1])
    model.eval()
    clean = metrics(model, tokenizer, ec, ey, tok_mean, char_mean)
    adv = metrics(model, tokenizer, ea, eay, tok_mean, char_mean)
    return {"clean": clean, "adv": adv, "n_params": n_params, "fpr_curve": fpr_curve, "_model": model}


def run_pipeline(dry: int, arms: tuple[str, ...], epochs: int, out_name: str,
                 candidate_spec: str, identity: dict, status: dict, status_path: Path) -> None:
    torch.manual_seed(SEED); np.random.seed(SEED); random.seed(SEED)
    tokenizer = official.PreTrainedTokenizerFast(
        tokenizer_file=str(REF / "artifacts/tokenizer/tokenizer-0-30522-both.json")
    )
    tr_d, tr_y, train_receipts = load_fixed_source_members(candidate_spec, "source_train")
    ec, ey, validation_receipts = load_fixed_source_members(candidate_spec, "source_validation")
    if dry:
        tr_d, tr_y = tr_d[:dry], tr_y[:dry]
        ec, ey = ec[:dry], ey[:dry]
    td = [domain for domain, label in zip(ec, ey, strict=True) if label == 1]
    ey = ey.astype(bool)
    rng = random.Random(SEED)
    ea_k2 = [perturb2(domain, rng) for domain in td]
    ea_krand = [perturb2(domain, rng) for domain in td]  # k∈U{1..4} 预算随机化组
    ea_mask = [perturb_half(domain, rng) for domain in td]  # MaskDGA 半替换强攻击面板
    eval_clean = (ec, ey)
    eval_adv_k2 = (ea_k2, np.ones(len(ea_k2), dtype=bool))
    eval_adv_krand = (ea_krand, np.ones(len(ea_krand), dtype=bool))
    eval_adv_mask = (ea_mask, np.ones(len(ea_mask), dtype=bool))
    print(f"[官方 P2/P3] 训练 {len(tr_d)}、评价干净 {len(ec)}、对抗 k2 {len(ea_k2)}/krand {len(ea_krand)}/maskdga {len(ea_mask)}", file=sys.stderr, flush=True)

    model0 = load_mps_model()
    tok_mean, char_mean = source_feature_means(model0, tokenizer, tr_d)
    del model0

    results: dict = {}
    adv_panels = {"k2": eval_adv_k2, "krand": eval_adv_krand, "maskdga": eval_adv_mask}
    ref_model = None
    if any(a_ == "E" for a_ in arms):
        ref_model = load_mps_model()
        ref_model.eval()
        print("[E 臂] 参考模型已加载（冻结初始判别器，KL 锚定用）", file=sys.stderr, flush=True)

    def progress(arm: str, phase: str, epoch: int, batch: int, total: int,
                 loss: float | None, metrics_now: dict | None) -> None:
        arm_status = status["arms"].setdefault(arm, {})
        arm_status.update({
            "phase": phase,
            "epoch": epoch,
            "batch": batch,
            "total_batches": total,
            "last_heartbeat": now_utc(),
            "rss_peak_mib": round(rss_mib(), 1),
        })
        if loss is not None:
            arm_status["last_loss"] = loss
        if metrics_now is not None:
            arm_status["last_epoch_metrics"] = metrics_now
        status["phase"] = phase
        status["current_arm"] = arm
        write_json_atomic(status_path, status)

    for arm in arms:
        arm_result_path = OUT / f"arm-{arm}-result.json"
        if arm_result_path.exists():
            saved = json.loads(arm_result_path.read_text(encoding="utf-8"))
            if saved["identity"] != identity or saved["arm"] != arm:
                raise RuntimeError(f"{arm_label(arm)} 已完成结果身份不一致")
            results[arm] = saved["result"]
            progress(arm, "completed", epochs, 0, 0, None, None)
            print(f"[{arm_label(arm)} 恢复] 已完成单臂结果，跳过重复训练", file=sys.stderr, flush=True)
            continue
        t0 = time.time()
        r = train_arm(
            arm, tr_d, tr_y, tokenizer, tok_mean, char_mean,
            eval_clean, eval_adv_k2, epochs, ref_model=ref_model,
            checkpoint_path=OUT / f"arm-{arm}-checkpoint.pt",
            run_identity=identity,
            progress=progress,
        )
        r["wall_seconds"] = round(time.time() - t0, 1)
        arm_model = r.pop("_model")
        if arm in ARM_DISPLAY_NAMES:
            r["display_name"] = ARM_DISPLAY_NAMES[arm]
        results[arm] = r
        # 双分组评价（该臂模型）：k=2 与 k∈U{1..4}
        for pname, (pa, pay) in adv_panels.items():
            results[arm][f"adv_{pname}"] = metrics(arm_model, tokenizer, pa, pay, tok_mean, char_mean)
        write_json_atomic(arm_result_path, {"identity": identity, "arm": arm, "result": results[arm]})
        progress(arm, "completed", epochs, 0, 0, None, None)
        print(f"[里程碑] {arm_label(arm)}: clean={json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in r['clean'].items()})} adv={json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in r['adv'].items()})}", file=sys.stderr, flush=True)
        del arm_model

    if "A" in results and "B" in results and "C" in results and len(results) == 3:
        a, b, c = results["A"], results["B"], results["C"]
        am, bm, cm = a["adv_maskdga"], b["adv_maskdga"], c["adv_maskdga"]
        verdict = {
            "P2_pass": bool(bm["AP"] > am["AP"] and b["clean"]["FPR"] <= a["clean"]["FPR"]),
            "P3_pass": bool(cm["AP"] > bm["AP"] and c["clean"]["FPR"] <= b["clean"]["FPR"]),
            "panel": "maskdga-half",
            "adv_AP": {"A": round(am["AP"], 4), "B": round(bm["AP"], 4), "C": round(cm["AP"], 4)},
            "clean_FPR": {"A": round(a["clean"]["FPR"], 4), "B": round(b["clean"]["FPR"], 4), "C": round(c["clean"]["FPR"], 4)},
            "adv_FNR": {"A": round(am["FNR"], 4), "B": round(bm["FNR"], 4), "C": round(cm["FNR"], 4)},
            "k2_reference_FNR": {"A": round(a["adv"]["FNR"], 4), "B": round(b["adv"]["FNR"], 4), "C": round(c["adv"]["FNR"], 4)},
        }
    else:
        # 非 A/B/C 组合（如 L/M/D、单臂）：verdict 由主代理按冻结判据从 results 手工裁决
        verdict = {"note": f"custom arms {sorted(results)} — manual adjudication per frozen criteria"}
    payload = {"source_members": {"train": train_receipts, "validation": validation_receipts}, "results": results, "verdict": verdict}
    write_json_atomic(OUT / out_name, payload)
    status["phase"] = "completed"
    status["completed_at"] = now_utc()
    status["current_arm"] = None
    write_json_atomic(status_path, status)
    print(f"[里程碑] {json.dumps(verdict, ensure_ascii=False)} -> {out_name}", file=sys.stderr, flush=True)


def main(dry: int = 0, arms_arg: str | None = None, result_name: str | None = None,
         candidate_spec: str | None = None) -> None:
    if candidate_spec is None:
        raise ValueError("共同预算训练必须显式提供 candidate-spec")
    if dry < 0:
        raise ValueError("dry-run 不能为负数")
    arms = tuple(arms_arg.split(",")) if arms_arg else (("A",) if dry else ("A", "B", "D", "G", "F"))
    if not arms or any(not re.fullmatch(r"[A-Z][A-Z0-9]*", arm) for arm in arms):
        raise ValueError("训练臂列表不合法")
    if len(set(arms)) != len(arms):
        raise ValueError("训练臂不能重复")
    epochs = 1 if dry else EPOCHS
    out_name = result_name_arg(result_name) if result_name else (
        "official-p2p3-DRYRUN.json" if dry else "official-p2p3-result.json"
    )
    spec_path = formal_contract.resolve_repo_relative(candidate_spec, must_exist=True)
    identity = {
        "code_sha256": sha256_file(Path(__file__).resolve()),
        "member_selector_sha256": sha256_file(Path(eligibility.__file__).resolve()),
        "model_loader_sha256": sha256_file(Path(official.__file__).resolve()),
        "feature_adapter_sha256": sha256_file(Path(diag.__file__).resolve()),
        "candidate_spec_sha256": sha256_file(spec_path),
        "checkpoint_sha256": sha256_file(CKPT),
        "source_revision": DATA.name,
        "arms": list(arms),
        "epochs": epochs,
        "batch": BATCH,
        "seed": SEED,
        "device": str(DEVICE),
        "precision": "bf16" if USE_BF16 else "fp32",
        "result_name": out_name,
        "dry_run": dry,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    status_path = OUT / "run-status.json"
    with (OUT / "run.lock").open("w") as lock_stream:
        try:
            fcntl.flock(lock_stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"运行目录已有活动进程：{OUT}") from exc
        if status_path.exists():
            status = json.loads(status_path.read_text(encoding="utf-8"))
            if status["identity"] != identity:
                raise RuntimeError("运行目录身份不一致，拒绝覆盖既有制品")
            if status["phase"] == "completed":
                if not (OUT / out_name).is_file():
                    raise RuntimeError("状态为已完成但总结果文件缺失")
                print(f"[恢复] 运行已完成：{OUT / out_name}", file=sys.stderr, flush=True)
                return
        else:
            allowed = {"run.lock", "console.log"}
            unexpected = sorted(path.name for path in OUT.iterdir() if path.name not in allowed)
            if unexpected:
                raise RuntimeError(f"新运行目录含既有制品，拒绝覆盖：{unexpected}")
            status = {
                "schema": "drift-source-screen-v1",
                "identity": identity,
                "phase": "loading_source",
                "started_at": now_utc(),
                "pid": os.getpid(),
                "current_arm": None,
                "arms": {},
            }
            write_json_atomic(status_path, status)
        status["pid"] = os.getpid()
        status["resumed_at"] = now_utc()
        write_json_atomic(status_path, status)
        try:
            run_pipeline(dry, arms, epochs, out_name, candidate_spec, identity, status, status_path)
        except BaseException as exc:
            status["phase"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
            status["failed_at"] = now_utc()
            status["last_error"] = f"{type(exc).__name__}: {exc}"
            write_json_atomic(status_path, status)
            raise


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", type=int, default=0)
    ap.add_argument("--arms", default=None, help="逗号分隔臂列表，如 A,B,D,F,G（默认五臂/干跑 A）")
    ap.add_argument("--result-name", type=result_name_arg, default=None, help="结果文件名，不得含路径或特殊字符")
    ap.add_argument("--candidate-spec", required=True, help="仓库相对固定哈希源成员规格")
    a = ap.parse_args()
    main(dry=a.dry_run, arms_arg=a.arms, result_name=a.result_name, candidate_spec=a.candidate_spec)
