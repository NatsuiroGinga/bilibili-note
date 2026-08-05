#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

params_path=${1:?缺少参数文件}
worker_mode=${2:-launcher}

repo_id=$(jq -er '.repo_id' "$params_path")
endpoint=$(jq -er '.endpoint' "$params_path")
model_dir=$(jq -er '.model_dir' "$params_path")
partial_dir=$(jq -er '.partial_dir' "$params_path")
screen_name=$(jq -er '.screen_name' "$params_path")
log_path=$(jq -er '.log_path' "$params_path")
state_path=$(jq -er '.state_path' "$params_path")
manifest_path=$(jq -er '.manifest_path' "$params_path")
checksums_path=$(jq -er '.checksums_path' "$params_path")
minimum_free_bytes=$(jq -er '.minimum_free_bytes' "$params_path")

expected_repo=distilbert/distilbert-base-multilingual-cased
expected_endpoint=https://hf-mirror.com
expected_model_dir=/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased
expected_partial_dir=/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased.partial

if [[ "$repo_id" != "$expected_repo" || "$endpoint" != "$expected_endpoint" ]]; then
  printf '%s\n' '模型来源不符合冻结合同。' >&2
  exit 2
fi
if [[ "$model_dir" != "$expected_model_dir" || "$partial_dir" != "$expected_partial_dir" ]]; then
  printf '%s\n' '模型目标路径不符合冻结合同。' >&2
  exit 2
fi
if [[ "$log_path" != runs/* || "$state_path" != runs/* ]]; then
  printf '%s\n' '下载日志和状态必须位于 runs/。' >&2
  exit 2
fi

write_state() {
  local status=$1
  local exit_code=$2
  local revision=${3:-}
  local downloaded_bytes=${4:-0}
  local state_parent
  local temporary
  state_parent=$(dirname "$state_path")
  mkdir -p "$state_parent"
  temporary="${state_path}.tmp.$$"
  jq -n \
    --arg status "$status" \
    --arg repo_id "$repo_id" \
    --arg endpoint "$endpoint" \
    --arg model_dir "$model_dir" \
    --arg partial_dir "$partial_dir" \
    --arg revision "$revision" \
    --arg screen_name "$screen_name" \
    --arg log_path "$log_path" \
    --arg updated_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --argjson exit_code "$exit_code" \
    --argjson downloaded_bytes "$downloaded_bytes" \
    '{schema_version: 1, status: $status, repo_id: $repo_id, endpoint: $endpoint, model_dir: $model_dir, partial_dir: $partial_dir, revision: $revision, screen_name: $screen_name, log_path: $log_path, downloaded_bytes: $downloaded_bytes, exit_code: $exit_code, updated_at: $updated_at}' \
    >"$temporary"
  mv "$temporary" "$state_path"
}

downloaded_bytes() {
  if [[ -d "$model_dir" ]]; then
    du -sb "$model_dir" | awk '{print $1}'
  elif [[ -d "$partial_dir" ]]; then
    du -sb "$partial_dir" | awk '{print $1}'
  else
    printf '0\n'
  fi
}

download_worker() {
  local revision=''
  local status_code=0
  local size=0
  local checksum_manifest_sha256
  local artifact_count
  local cpu_smoke

  on_error() {
    status_code=$?
    size=$(downloaded_bytes)
    write_state failed "$status_code" "$revision" "$size"
    exit "$status_code"
  }
  trap on_error ERR

  export HF_ENDPOINT="$endpoint"
  mkdir -p "$(dirname "$model_dir")" "$(dirname "$log_path")"
  revision=$(uv run --frozen python -c 'import os; from huggingface_hub import HfApi; print(HfApi(endpoint=os.environ["HF_ENDPOINT"]).model_info("distilbert/distilbert-base-multilingual-cased").sha)')
  if [[ ! "$revision" =~ ^[0-9a-f]{40}$ ]]; then
    printf '%s\n' '无法解析官方模型修订哈希。' >&2
    exit 3
  fi
  write_state downloading 0 "$revision" "$(downloaded_bytes)"

  if [[ ! -d "$model_dir" ]]; then
    uv run --frozen hf download \
      "$repo_id" \
      config.json \
      model.safetensors \
      tokenizer.json \
      tokenizer_config.json \
      vocab.txt \
      --revision "$revision" \
      --local-dir "$partial_dir"
    test -s "$partial_dir/config.json"
    test -s "$partial_dir/vocab.txt"
    test -s "$partial_dir/tokenizer.json"
    test -s "$partial_dir/tokenizer_config.json"
    test -s "$partial_dir/model.safetensors"
    mv "$partial_dir" "$model_dir"
  fi

  cpu_smoke=$(MODEL_DIR="$model_dir" uv run --frozen python -c 'import json, os; from transformers import AutoModelForSequenceClassification, AutoTokenizer; p=os.environ["MODEL_DIR"]; t=AutoTokenizer.from_pretrained(p, local_files_only=True); m=AutoModelForSequenceClassification.from_pretrained(p, num_labels=2, local_files_only=True); x=t(["协议=TCP；持续时间=1.0；包数=2"], return_tensors="pt", padding=True, truncation=True, max_length=32); y=m(**x).logits.detach().cpu(); print(json.dumps({"status":"passed","tokenizer_class":type(t).__name__,"model_class":type(m).__name__,"logits_shape":list(y.shape)}))')

  rg --files --hidden -g '!.cache/**' "$model_dir" | sort | while IFS= read -r artifact; do
    sha256sum "$artifact"
  done >"$checksums_path"
  test -s "$checksums_path"
  checksum_manifest_sha256=$(sha256sum "$checksums_path" | awk '{print $1}')
  artifact_count=$(wc -l <"$checksums_path" | tr -d ' ')
  size=$(du -sb "$model_dir" | awk '{print $1}')
  jq -n \
    --arg repo_id "$repo_id" \
    --arg endpoint "$endpoint" \
    --arg revision "$revision" \
    --arg model_dir "$model_dir" \
    --arg checksums_path "$checksums_path" \
    --arg checksums_sha256 "$checksum_manifest_sha256" \
    --argjson artifact_count "$artifact_count" \
    --argjson total_size_bytes "$size" \
    --argjson cpu_load_smoke "$cpu_smoke" \
    --arg created_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{schema_version: 1, source: {repo_id: $repo_id, endpoint: $endpoint, revision: $revision}, local_mirror: {path: $model_dir, total_size_bytes: $total_size_bytes, artifact_count: $artifact_count, checksums_path: $checksums_path, checksums_sha256: $checksums_sha256}, cpu_load_smoke: $cpu_load_smoke, created_at: $created_at}' \
    >"${manifest_path}.tmp.$$"
  mv "${manifest_path}.tmp.$$" "$manifest_path"
  write_state finished 0 "$revision" "$size"
  printf '模型下载与 CPU 加载冒烟完成：%s，字节数=%s，修订=%s\n' "$model_dir" "$size" "$revision"
}

if [[ "$worker_mode" == worker ]]; then
  download_worker
  exit 0
fi

command -v jq >/dev/null
command -v rg >/dev/null
command -v uv >/dev/null
command -v screen >/dev/null
free_bytes=$(df -PB1 /root/autodl-tmp | awk 'NR == 2 {print $4}')
if ((free_bytes < minimum_free_bytes)); then
  printf '服务器可用空间不足：%s 字节。\n' "$free_bytes" >&2
  exit 5
fi
if screen -S "$screen_name" -Q select . >/dev/null 2>&1; then
  printf '下载会话已在运行：%s，当前字节数=%s\n' "$screen_name" "$(downloaded_bytes)"
  exit 0
fi
if [[ -d "$model_dir" && -s "$manifest_path" ]]; then
  printf '模型镜像及清单已存在：%s，当前字节数=%s\n' "$model_dir" "$(downloaded_bytes)"
  exit 0
fi

mkdir -p "$(dirname "$log_path")"
write_state prepared 0 '' "$(downloaded_bytes)"
screen -L -Logfile "$log_path" -DmS "$screen_name" bash "$0" "$params_path" worker
sleep 1
if ! screen -S "$screen_name" -Q select . >/dev/null 2>&1; then
  printf '%s\n' '模型下载 screen 会话未保持运行。' >&2
  exit 6
fi
write_state running 0 '' "$(downloaded_bytes)"
printf '模型下载已启动：screen=%s，日志=%s，当前字节数=%s\n' "$screen_name" "$log_path" "$(downloaded_bytes)"
