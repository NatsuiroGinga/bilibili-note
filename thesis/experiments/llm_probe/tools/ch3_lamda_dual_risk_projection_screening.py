#!/usr/bin/env python3
"""LAMDA A-GEM 式双风险梯度投影来源／开发期筛查。"""

from __future__ import annotations

import argparse
import json
import platform
import resource
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

import ch3_lamda_domain_il_replay_screening as base


RUN_YEARS = [2013, 2014, 2016, 2017]
SOURCE_YEARS = [2013, 2014]
DEVELOPMENT_YEARS = [2016, 2017]
SEALED_FINAL_YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
ARMS = ["experience_replay", "dual_risk_projection"]
THRESHOLD = 0.5


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    data = config.get("data", {})
    if config.get("arms") != ARMS:
        raise ValueError("双风险投影筛查必须恰有 ER 与双风险投影两臂")
    if data.get("run_years") != RUN_YEARS or data.get("source_years") != SOURCE_YEARS or data.get("development_years") != DEVELOPMENT_YEARS or data.get("sealed_final_years") != SEALED_FINAL_YEARS:
        raise ValueError("年份角色不符合 LAMDA 数据清单")
    if data.get("published_feature_count") != 4561 or data.get("protocol") != "Domain-IL":
        raise ValueError("LAMDA 输入合同不匹配")
    identity = config.get("identity", {})
    if identity.get("run_tier") != "screening_only" or identity.get("published_feature_space_uses_future_covariates") is not True:
        raise ValueError("双风险投影只允许 screening_only 且必须披露未来协变量")
    training = config.get("training", {})
    if training.get("seed") != 42 or training.get("epochs_per_year") != 10 or training.get("batch_size") != 1024:
        raise ValueError("训练预算不符合既有公平合同")
    if config.get("replay", {}).get("capacity") != 200:
        raise ValueError("回放容量必须为 200")
    if config.get("evaluation", {}).get("development_current_years") != DEVELOPMENT_YEARS:
        raise ValueError("开发期评价年份未冻结")
    return config


def load_train(path: Path, features: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values, labels, hashes = [], [], []
    for batch_values, batch_labels, batch_hashes, _ in base.iter_parquet(path, features):
        values.append(batch_values); labels.append(batch_labels); hashes.append(batch_hashes)
    if not labels:
        raise RuntimeError(f"年度训练未读取到样本：{path}")
    return np.concatenate(values), np.concatenate(labels), np.concatenate(hashes)


def verify_input(data_root: Path) -> tuple[list[str], dict[int, dict[str, Path]], dict[str, Any]]:
    manifest = json.loads((data_root / "manifest.json").read_text(encoding="utf-8"))
    source = manifest.get("source", {})
    if source.get("repo_id") != "IQSeC-Lab/LAMDA" or source.get("revision") != "ad9614bdd5556767f97ced2fce797c2f06408ebf":
        raise ValueError("输入 manifest 的 LAMDA 身份不匹配")
    roles = manifest.get("data_roles", {})
    if roles.get("source_years") != SOURCE_YEARS or roles.get("development_years") != DEVELOPMENT_YEARS or roles.get("sealed_final_years") != SEALED_FINAL_YEARS:
        raise ValueError("输入 manifest 的年份角色不匹配")
    import csv
    mapping = (data_root / "Baseline/feature_mapping.csv").read_text(encoding="utf-8").splitlines()
    features = [row["mapped_name"] for row in csv.DictReader(mapping)]
    if len(features) != 4561 or len(features) != len(set(features)):
        raise ValueError("特征映射不是 4561 个唯一字段")
    files = {}
    for year in RUN_YEARS:
        root = data_root / "Baseline" / str(year)
        train, test = root / f"{year}_train.parquet", root / f"{year}_test.parquet"
        if not train.is_file() or not test.is_file():
            raise FileNotFoundError(f"年度 train/test 不完整：{year}")
        files[year] = {"train": train, "test": test}
    return features, files, manifest


def scores_for(model: nn.Module, values: np.ndarray, device: torch.device) -> np.ndarray:
    model.eval(); parts = []
    with torch.inference_mode():
        for start in range(0, len(values), base.SCANNER_BATCH_SIZE):
            inputs = torch.from_numpy(values[start : start + base.SCANNER_BATCH_SIZE]).to(device=device, dtype=torch.float32)
            parts.append(model(inputs).cpu().numpy())
    return np.concatenate(parts) if parts else np.empty((0,), dtype=np.float32)


def flat_grads(grads: tuple[torch.Tensor | None, ...], params: list[nn.Parameter]) -> torch.Tensor:
    pieces = []
    for grad, param in zip(grads, params, strict=True):
        pieces.append((torch.zeros_like(param) if grad is None else grad).reshape(-1))
    return torch.cat(pieces)


def project_gradient(gradient: torch.Tensor, reference: torch.Tensor | None) -> tuple[torch.Tensor, bool, float]:
    if reference is None:
        return gradient, False, 0.0
    dot = torch.dot(gradient, reference)
    norm_sq = torch.dot(reference, reference)
    if float(norm_sq.item()) == 0.0 or float(dot.item()) >= 0.0:
        return gradient, False, float(dot.item())
    return gradient - (dot / norm_sq) * reference, True, float(dot.item())


def assign_flat_grads(params: list[nn.Parameter], gradient: torch.Tensor) -> None:
    offset = 0
    for param in params:
        size = param.numel()
        param.grad = gradient[offset : offset + size].view_as(param).detach().clone()
        offset += size


def train_epoch(model: nn.Module, optimizer: torch.optim.Optimizer, criterion: nn.Module, values: np.ndarray, labels: np.ndarray, benign_mask: np.ndarray, replay_values: np.ndarray | None, replay_labels: np.ndarray | None, protect_values: np.ndarray, device: torch.device, batch_size: int, shuffle_seed: int, use_projection: bool) -> tuple[float, int, dict[str, float | int]]:
    model.train()
    train_values, train_labels, train_benign = values, labels, benign_mask
    if replay_values is not None and replay_labels is not None and len(replay_labels):
        train_values = np.concatenate((train_values, replay_values), axis=0)
        train_labels = np.concatenate((train_labels, replay_labels), axis=0)
        train_benign = np.concatenate((train_benign, np.zeros(len(replay_labels), dtype=bool)))
    order = np.random.default_rng(shuffle_seed).permutation(len(train_labels))
    train_values, train_labels, train_benign = train_values[order], train_labels[order], train_benign[order]
    params = list(model.parameters())
    total_loss = total_samples = 0.0
    projection_events = projection_dot_sum = 0.0
    protect_tensor = torch.from_numpy(protect_values).to(device=device, dtype=torch.float32) if len(protect_values) else None
    for start in range(0, len(train_labels), batch_size):
        batch_values = train_values[start : start + batch_size]
        batch_labels = train_labels[start : start + batch_size]
        batch_benign = train_benign[start : start + batch_size]
        inputs = torch.from_numpy(batch_values).to(device=device, dtype=torch.float32)
        targets = torch.from_numpy(batch_labels.astype(np.float32, copy=False)).to(device=device)
        optimizer.zero_grad(set_to_none=True)
        current_loss = criterion(model(inputs), targets)
        if not use_projection:
            current_loss.backward(); optimizer.step()
        else:
            current_grad = flat_grads(torch.autograd.grad(current_loss, params), params)
            protect_grad = None
            benign_grad = None
            if protect_tensor is not None:
                protect_prob = model(protect_tensor)
                protect_loss = criterion(protect_prob, torch.ones_like(protect_prob))
                protect_grad = flat_grads(torch.autograd.grad(protect_loss, params), params)
            if np.any(batch_benign):
                benign_inputs = inputs[torch.from_numpy(batch_benign).to(device=device)]
                benign_prob = model(benign_inputs)
                benign_loss = criterion(benign_prob, torch.zeros_like(benign_prob))
                benign_grad = flat_grads(torch.autograd.grad(benign_loss, params), params)
            projected, event_p, dot_p = project_gradient(current_grad, protect_grad)
            projected, event_n, dot_n = project_gradient(projected, benign_grad)
            assign_flat_grads(params, projected); optimizer.step()
            projection_events += int(event_p) + int(event_n); projection_dot_sum += dot_p + dot_n
        count = len(batch_labels)
        total_loss += float(current_loss.item()) * count; total_samples += count
    if not total_samples:
        raise RuntimeError("训练批次为空")
    return total_loss / total_samples, int(total_samples), {"projection_events": int(projection_events), "projection_dot_sum": float(projection_dot_sum)}


def checkpoint_payload(model: nn.Module, optimizer: torch.optim.Optimizer, memory: base.Reservoir, year_index: int, next_epoch: int, yearly: dict[str, Any], old_positive: dict[str, bool], context: dict[str, Any] | None) -> dict[str, Any]:
    return {"schema_version": "ch3-lamda-dual-risk-projection-checkpoint-v1", "model": model.state_dict(), "optimizer": optimizer.state_dict(), "memory": memory.state_dict(), "year_index": year_index, "next_epoch": next_epoch, "yearly": yearly, "old_positive": old_positive, "context": context, "rng": base.rng_state(), "saved_at": base.now_utc()}


def execute_arm(arm: str, config: dict[str, Any], features: list[str], files: dict[int, dict[str, Path]], output_root: Path, device: torch.device, resume: bool, started_at: str) -> None:
    checkpoint_path = output_root / "checkpoints" / arm / "latest.pt"
    seed = int(config["training"]["seed"])
    use_projection = arm == "dual_risk_projection"
    if resume and checkpoint_path.is_file():
        saved = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        model = base.LamdaDomainILMLP(len(features), float(config["model"]["head_dropout"])).to(device); model.load_state_dict(saved["model"])
        optimizer = torch.optim.SGD(model.parameters(), lr=float(config["training"]["optimizer"]["lr"]), momentum=float(config["training"]["optimizer"]["momentum"]), weight_decay=float(config["training"]["optimizer"]["weight_decay"])); optimizer.load_state_dict(saved["optimizer"])
        memory = base.Reservoir.from_state(saved["memory"]); year_index, next_epoch = int(saved["year_index"]), int(saved["next_epoch"]); yearly, old_positive, context = dict(saved["yearly"]), dict(saved["old_positive"]), saved.get("context"); base.restore_rng(saved["rng"])
    else:
        base.seed_everything(seed); model = base.LamdaDomainILMLP(len(features), float(config["model"]["head_dropout"])).to(device); optimizer = torch.optim.SGD(model.parameters(), lr=float(config["training"]["optimizer"]["lr"]), momentum=float(config["training"]["optimizer"]["momentum"]), weight_decay=float(config["training"]["optimizer"]["weight_decay"])); memory = base.Reservoir(200, len(features), seed); year_index, next_epoch, yearly, old_positive, context = 0, 1, {}, {}, None
    criterion = nn.BCELoss(); epochs = int(config["training"]["epochs_per_year"]); batch_size = int(config["training"]["batch_size"])
    for index in range(year_index, len(RUN_YEARS)):
        year = RUN_YEARS[index]; values, labels, hashes = load_train(files[year]["train"], features)
        if index == year_index and next_epoch > 1 and context is not None:
            benign_mask = np.asarray(context["benign_mask"], dtype=bool)
        else:
            teacher = scores_for(model, values, device) if index else np.full(len(labels), np.nan, dtype=np.float32)
            benign_mask = (labels == 0) & np.isfinite(teacher) & (teacher >= THRESHOLD)
            context = {"year": year, "benign_mask": benign_mask}
        if use_projection and len(memory.labels):
            memory_scores = scores_for(model, memory.values, device)
            protect_values = memory.values[(memory.labels == 1) & (memory_scores >= THRESHOLD)]
        else:
            protect_values = np.empty((0, len(features)), dtype=np.uint8)
        replay_values = memory.values if len(memory.labels) else None; replay_labels = memory.labels if len(memory.labels) else None
        epoch_start = next_epoch if index == year_index else 1
        for epoch in range(epoch_start, epochs + 1):
            loss, samples, projection = train_epoch(model, optimizer, criterion, values, labels, benign_mask, replay_values, replay_labels, protect_values, device, batch_size, seed + index * epochs + epoch, use_projection)
            yearly.setdefault(str(year), {"epochs": []})["epochs"].append({"epoch": epoch, "loss": loss, "samples": samples, "projection": projection, "protect_candidates": int(len(protect_values)), "benign_candidates": int(np.sum(benign_mask)), "completed_at": base.now_utc()})
            snapshot = checkpoint_payload(model, optimizer, memory, index, epoch + 1, yearly, old_positive, context); base.atomic_torch(output_root / "checkpoints" / arm / f"year-{year}" / f"epoch-{epoch:02d}.pt", snapshot); base.atomic_torch(checkpoint_path, snapshot); base.write_status(output_root, "running", f"{arm} {year} 第 {epoch}/{epochs} 轮完成", started_at, {"arm": arm, "year": year, "epoch": epoch})
        surfaces: dict[str, Any] = {}; surfaces["current_year"], current = base.evaluate_surface(model, arm, year, "current_year", [year], files, features, output_root, device, THRESHOLD, old_positive); next_years = [RUN_YEARS[index + 1]] if index + 1 < len(RUN_YEARS) else []; surfaces["next_year"] = {"not_applicable": True} if not next_years else base.evaluate_surface(model, arm, year, "next_year", next_years, files, features, output_root, device, THRESHOLD, old_positive)[0]; backward_years = RUN_YEARS[:index]; surfaces["backward"], backward = ({"not_applicable": True}, {}) if not backward_years else base.evaluate_surface(model, arm, year, "backward", backward_years, files, features, output_root, device, THRESHOLD, old_positive); yearly[str(year)]["evaluation"] = surfaces; old_positive.update(current); old_positive.update(backward)
        for chunk_values, chunk_labels, chunk_hashes, _ in base.iter_parquet(files[year]["train"], features):
            memory.update(chunk_values, chunk_labels, [base.identity_pair(year, source_hash, row, int(label)) for row, label, source_hash in zip(chunk_values, chunk_labels, chunk_hashes, strict=True)])
        yearly[str(year)]["memory"] = {"capacity": memory.capacity, "size": int(len(memory.labels)), "seen_training_samples": memory.seen, "updated_after_training_and_evaluation": True}; context = None; snapshot = checkpoint_payload(model, optimizer, memory, index + 1, 1, yearly, old_positive, context); base.atomic_torch(output_root / "checkpoints" / arm / f"year-{year}" / "year-complete.pt", snapshot); base.atomic_torch(checkpoint_path, snapshot); base.atomic_json(output_root / "metrics" / arm / f"year-{year}.json", {"arm": arm, "trained_through_year": year, "evaluation": surfaces, "epochs": yearly[str(year)]["epochs"], "memory": yearly[str(year)]["memory"]}); next_epoch = 1


def aggregate_development(output_root: Path) -> dict[str, Any]:
    result = {"development_years": DEVELOPMENT_YEARS, "arms": {}, "screening_only": True, "independent_final_test": False}
    for arm in ARMS:
        rows=[]
        for year in DEVELOPMENT_YEARS:
            with (output_root / "predictions" / arm / f"trained-through-{year}" / "current_year.jsonl").open(encoding="utf-8") as handle: rows.extend(json.loads(line) for line in handle)
        identities=[row["sample_identity_sha256"] for row in rows]
        if len(identities)!=len(set(identities)): raise ValueError(f"{arm} 开发期汇总存在重复身份")
        labels=np.asarray([row["label"] for row in rows],dtype=np.int64); scores=np.asarray([row["score"] for row in rows],dtype=np.float64); result["arms"][arm]={"current_year_metrics":base.metrics(labels,scores,THRESHOLD),"prediction_count":len(rows),"prediction_sha256":base.hashlib.sha256("".join(identities).encode("ascii")).hexdigest()}
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description="LAMDA 来源／开发期 A-GEM 式双风险梯度投影筛查"); parser.add_argument("--config",type=Path,required=True,help="冻结 JSON 配置"); parser.add_argument("--run",action="store_true",help=argparse.SUPPRESS); parser.add_argument("--resume",action="store_true",help="从同一身份断点恢复"); parser.add_argument("--validate-config",action="store_true",help="只校验配置"); args=parser.parse_args(); config=load_config(args.config.resolve())
    if args.validate_config: print(json.dumps({"valid":True,"run_id":config["identity"]["run_id"],"run_years":RUN_YEARS,"sealed_final_years_not_read":SEALED_FINAL_YEARS,"screening_only":True},ensure_ascii=False)); return 0
    output_root=Path(config["paths"]["output_root"]); data_root=Path(config["paths"]["data_root"]); base.prepare_output(output_root,config,args.config.resolve(),args.resume); started_at=base.now_utc(); started=time.monotonic(); base.write_status(output_root,"running","开始 LAMDA 双风险梯度投影筛查",started_at)
    try:
        features,files,manifest=verify_input(data_root); base.atomic_json(output_root/"input-manifest.json",{"input_manifest_path":str(data_root/"manifest.json"),"input_manifest_sha256":base.sha256_file(data_root/"manifest.json"),"manifest":manifest,"enumerated_years":RUN_YEARS,"sealed_final_years_not_read":SEALED_FINAL_YEARS,"published_feature_space_uses_future_covariates":True,"screening_only":True}); device=base.choose_device(); torch.set_float32_matmul_precision(config["training"]["float32_matmul_precision"]); base.atomic_json(output_root/"runtime-receipt.json",{"device":str(device),"torch":torch.__version__,"numpy":np.__version__,"platform":platform.platform(),"float32_matmul_precision":config["training"]["float32_matmul_precision"],"torch_compile":False,"screening_only":True,"enumerated_years":RUN_YEARS,"sealed_final_years_not_read":SEALED_FINAL_YEARS,"started_at":started_at})
        for arm in ARMS: execute_arm(arm,config,features,files,output_root,device,args.resume,started_at)
        base.atomic_json(output_root/"development-summary.json",aggregate_development(output_root)); usage=resource.getrusage(resource.RUSAGE_SELF); base.atomic_json(output_root/"resource-receipt.json",{"device":str(device),"wall_seconds":time.monotonic()-started,"max_rss":usage.ru_maxrss,"max_rss_unit":"platform_dependent","cuda_max_memory_allocated":int(torch.cuda.max_memory_allocated()) if device.type=="cuda" else None,"cuda_max_memory_reserved":int(torch.cuda.max_memory_reserved()) if device.type=="cuda" else None}); base.atomic_json(output_root/"run-manifest.json",{"tool_sha256":base.sha256_file(Path(__file__).resolve()),"config_sha256":base.sha256_file(args.config.resolve()),"arms":ARMS,"enumerated_years":RUN_YEARS,"sealed_final_years_not_read":SEALED_FINAL_YEARS,"screening_only":True}); base.write_status(output_root,"completed","LAMDA 双风险梯度投影筛查完成",started_at); return 0
    except Exception as error: base.write_status(output_root,"failed",f"{type(error).__name__}: {error}",started_at); raise


if __name__ == "__main__": raise SystemExit(main())
