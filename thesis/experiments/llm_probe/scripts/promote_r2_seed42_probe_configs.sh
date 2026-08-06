#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail

project_root="/root/autodl-tmp/thesis/experiments/llm_probe"
config_root="$project_root/configs"
promotion_root="$project_root/runs/launchers/r2-final-sidecar/promotions"
promotion_id="seed42-$(date -u +%Y%m%dT%H%M%SZ)-$$"
receipt_root="$promotion_root/$promotion_id"

names=(
  "r2_final_distilbert_f-a_seed42.yaml"
  "r2_final_distilbert_f-p_seed42.yaml"
  "r2_final_distilbert_f-s_seed42.yaml"
)
temporary_names=(
  ".r2_final_distilbert_f-a_seed42.yaml.729ff161.tmp"
  ".r2_final_distilbert_f-p_seed42.yaml.42331148.tmp"
  ".r2_final_distilbert_f-s_seed42.yaml.de3c0844.tmp"
)
expected_hashes=(
  "729ff1611fdd979ab26290e19cf3e6f3802df8925d07acab0287a1e88c4d4586"
  "42331148d9115dad3f14b87e1609db26a8faf777f9749639a4971da3125f98a1"
  "de3c0844b8b6c76d57796811e6ec41d9a71c419d3a7902c29510612a93a154f3"
)

if pgrep -f 'flow_probe\.r2_final_distilbert_probe' >/dev/null; then
  printf '已有旁路探针进程，拒绝提升配置。\n' >&2
  exit 3
fi

for index in "${!names[@]}"; do
  target="$config_root/${names[$index]}"
  temporary="$config_root/${temporary_names[$index]}"
  if [[ ! -f "$target" || ! -f "$temporary" ]]; then
    printf '正式配置或临时配置缺失：%s\n' "${names[$index]}" >&2
    exit 4
  fi
  actual_hash="$(sha256sum "$temporary" | cut -d' ' -f1)"
  if [[ "$actual_hash" != "${expected_hashes[$index]}" ]]; then
    printf '临时配置摘要不一致：%s\n' "${temporary_names[$index]}" >&2
    exit 5
  fi
done

mkdir -p "$receipt_root/originals"
for name in "${names[@]}"; do
  cp -p "$config_root/$name" "$receipt_root/originals/$name"
done

committed=0
rollback() {
  if [[ $committed -eq 0 ]]; then
    for name in "${names[@]}"; do
      if [[ -f "$receipt_root/originals/$name" ]]; then
        cp -p "$receipt_root/originals/$name" "$config_root/$name"
      fi
    done
    printf 'failed_rolled_back\n' >"$receipt_root/status.txt"
  fi
}
trap rollback EXIT

for index in "${!names[@]}"; do
  mv -- "$config_root/${temporary_names[$index]}" "$config_root/${names[$index]}"
done

for index in "${!names[@]}"; do
  actual_hash="$(sha256sum "$config_root/${names[$index]}" | cut -d' ' -f1)"
  if [[ "$actual_hash" != "${expected_hashes[$index]}" ]]; then
    printf '正式配置提升后摘要不一致：%s\n' "${names[$index]}" >&2
    exit 6
  fi
done

committed=1
printf 'finished\n' >"$receipt_root/status.txt"
trap - EXIT

printf 'promotion_id=%s\n' "$promotion_id"
printf 'receipt_root=%s\n' "$receipt_root"
printf 'status=finished\n'
