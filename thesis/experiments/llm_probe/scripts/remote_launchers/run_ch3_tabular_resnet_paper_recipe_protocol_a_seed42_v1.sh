#!/usr/bin/env bash
# N14 表格 ResNet 协议 A 源年资格运行。当前脚本绝不打开目标年。

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
CONFIG="$PROJECT_ROOT/configs/ch3-tabular-resnet-paper-recipe-protocol-a-seed42-v1.json"
TOOL="$PROJECT_ROOT/tools/ch3_tabular_resnet_paper_recipe_protocol_a.py"
# `src/` 已由可编辑安装的 _editable_impl_flow_probe.pth 进入导入路径，但 `tools/` 没有。
# `protocol_a_raw83` 依赖 `dijk2026_replication.dijk_fields`，该包位于 `tools/` 下，
# 故显式把 `tools/` 并入 PYTHONPATH，否则依赖闭包导入在预检即失败。
export PYTHONPATH="$PROJECT_ROOT/tools${PYTHONPATH:+:$PYTHONPATH}"
RUN_ID="ch3-tabular-resnet-paper-recipe-protocol-a-seed42-v2"
OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
LOG_PATH="$LAUNCHER_ROOT/launcher.log"
STATUS_PATH="$LAUNCHER_ROOT/status.json"
UV_CACHE_DIR="${UV_CACHE_DIR:-/root/autodl-tmp/.cache/uv}"
PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/root/autodl-tmp/.cache/pycache}"
export UV_CACHE_DIR PYTHONPYCACHEPREFIX

mkdir -p "$LAUNCHER_ROOT" "$OUTPUT_ROOT"

write_status() {
  local state="$1"
  local stage="$2"
  local exit_code="$3"
  local detail="$4"
  STATUS_PATH="$STATUS_PATH" STATE="$state" STAGE="$stage" EXIT_CODE="$exit_code" DETAIL="$detail" \
    uv run --no-sync python -c 'import json, os, pathlib, tempfile, time; p=pathlib.Path(os.environ["STATUS_PATH"]); p.parent.mkdir(parents=True, exist_ok=True); value={"schema_version":"ch3-tabular-resnet-launcher-status-v2","run_id":"ch3-tabular-resnet-paper-recipe-protocol-a-seed42-v2","state":os.environ["STATE"],"stage":os.environ["STAGE"],"exit_code":int(os.environ["EXIT_CODE"]),"detail":os.environ["DETAIL"],"target_feature_rows_read":0,"target_label_rows_read":0,"updated_at_unix":time.time()}; fd,name=tempfile.mkstemp(prefix=p.name+".partial.",dir=p.parent); pathlib.Path(name).write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8"); os.close(fd); os.replace(name,p)'
}

fail() {
  local code="$1"
  local stage="$2"
  local detail="$3"
  write_status "failed" "$stage" "$code" "$detail"
  printf '%s\n' "$detail" >&2
  exit "$code"
}

command -v uv >/dev/null 2>&1 || fail 20 "preflight" "uv 不在 PATH"
command -v rg >/dev/null 2>&1 || fail 21 "preflight" "rg 不在 PATH"
command -v jq >/dev/null 2>&1 || fail 22 "preflight" "jq 不在 PATH"
[[ -f "$CONFIG" && -f "$TOOL" ]] || fail 23 "preflight" "N14 配置或工具缺失"

SOURCE_MANIFEST="$(jq -er '.paths.source_dataset_manifest' "$CONFIG")" || fail 24 "preflight" "源 dataset-manifest 路径缺失"
OUTPUT_CONFIG="$(jq -er '.paths.output_root' "$CONFIG")" || fail 25 "preflight" "输出根配置缺失"
QUALIFICATION_SEAL="$(jq -er '.paths.source_qualification_seal' "$CONFIG")" || fail 26 "preflight" "源资格封印路径缺失"
TARGET_STATUS="$(jq -er '.target_gate.qualification_status' "$CONFIG")" || fail 27 "preflight" "目标资格状态缺失"
TARGET_MANIFEST_TYPE="$(jq -r '.paths.target_dataset_manifest | type' "$CONFIG")"

[[ "$OUTPUT_CONFIG" == "$OUTPUT_ROOT" ]] || fail 28 "preflight" "配置输出根与启动器运行身份不符"
[[ "$SOURCE_MANIFEST" == */dataset-manifest.json ]] || fail 29 "preflight" "源输入不是 dataset-manifest.json"
[[ -f "$SOURCE_MANIFEST" ]] || fail 30 "preflight" "共享 Raw83 源清单尚未发布"
[[ "$TARGET_STATUS" == "blocked-until-external-source-qualification" ]] || fail 31 "preflight" "当前目标配置未保持阻塞"
[[ "$TARGET_MANIFEST_TYPE" == "null" ]] || fail 32 "preflight" "当前配置不应注入目标清单"
[[ "$(jq -r '.target_gate.winning_arm | type' "$CONFIG")" == "null" ]] || fail 33 "preflight" "当前配置不应注入胜出臂"
[[ "$(jq -r '.training.wall_clock_limit_seconds | type' "$CONFIG")" == "null" ]] || fail 34 "preflight" "禁止设置人为墙钟上限"
[[ "$(jq -r '.training.checkpoint_every_optimizer_steps' "$CONFIG")" == "20" ]] || fail 35 "preflight" "检查点间隔必须为20个完整优化步"
[[ "$(jq -r '.precision_profile_id' "$CONFIG")" == "cuda-bf16-amp-fp32-sensitive-v1" ]] || fail 36 "preflight" "BF16 精度配置不符"
[[ "$(jq -r '.architecture.parameter_count' "$CONFIG")" == "387074" ]] || fail 37 "preflight" "参数量登记不符"
[[ "$(jq -r '.swanlab.maximum_init_attempts' "$CONFIG")" == "2" ]] || fail 38 "preflight" "SwanLab 两次上限不符"

TRAIN_TOKEN_ENV="$(jq -er '.label_stage_token_env.train' "$CONFIG")"
VALIDATE_TOKEN_ENV="$(jq -er '.label_stage_token_env.validate' "$CONFIG")"
[[ -n "${!TRAIN_TOKEN_ENV:-}" ]] || fail 39 "preflight" "训练标签用途令牌环境变量未设置"
[[ -n "${!VALIDATE_TOKEN_ENV:-}" ]] || fail 40 "preflight" "验证标签用途令牌环境变量未设置"

if rg -n 'X'"23|X"'24|field_'"cardinality" "$TOOL" "$CONFIG" "$0" >/dev/null; then
  fail 41 "preflight" "发现旧缓存或旧字段基数路径残留"
fi
uv run --no-sync python -c 'import numpy, sklearn, torch, swanlab; from flow_probe.protocol_a_raw83 import open_protocol_a_dataset; import neural_precision_runtime' \
  || fail 43 "preflight" "依赖闭包导入失败"
uv run --no-sync python "$TOOL" --config "$CONFIG" --validate-config \
  || fail 44 "preflight" "配置机械核验失败"
bash "$PROJECT_ROOT/tools/memory_admission_gate.sh" 24 "$RUN_ID" \
  || fail 45 "preflight" "内存准入门失败"

write_status "running" "select-input" 0 "开始源年 A/B C00 输入选择"
set +e
uv run --no-sync python "$TOOL" --config "$CONFIG" --stage select-input --resume 2>&1 | tee -a "$LOG_PATH"
PIPE_CODES=("${PIPESTATUS[@]}")
set -e
[[ "${PIPE_CODES[0]}" == "0" && "${PIPE_CODES[1]}" == "0" ]] \
  || fail "${PIPE_CODES[0]}" "select-input" "输入选择或日志写入失败"

write_status "running" "select-optimizer" 0 "开始封印输入上的两个 AdamW 候选选择"
set +e
uv run --no-sync python "$TOOL" --config "$CONFIG" --stage select-optimizer --resume 2>&1 | tee -a "$LOG_PATH"
PIPE_CODES=("${PIPESTATUS[@]}")
set -e
[[ "${PIPE_CODES[0]}" == "0" && "${PIPE_CODES[1]}" == "0" ]] \
  || fail "${PIPE_CODES[0]}" "select-optimizer" "优化器选择或日志写入失败"

write_status "running" "cells" 0 "开始 C00/C01/C10/C11 四格和源年指标"
set +e
uv run --no-sync python "$TOOL" --config "$CONFIG" --stage cells --resume 2>&1 | tee -a "$LOG_PATH"
PIPE_CODES=("${PIPESTATUS[@]}")
set -e
[[ "${PIPE_CODES[0]}" == "0" && "${PIPE_CODES[1]}" == "0" ]] \
  || fail "${PIPE_CODES[0]}" "cells" "四格、源年评价或日志写入失败"

[[ -f "$OUTPUT_ROOT/source-cells-sealed.json" ]] || fail 46 "postflight" "四格源年封印缺失"
[[ -f "$QUALIFICATION_SEAL" ]] || fail 47 "postflight" "LSPR23 全部封印后的资格封印缺失"
[[ "$(jq -r '.all_four_cells_sealed' "$OUTPUT_ROOT/source-cells-sealed.json")" == "true" ]] \
  || fail 48 "postflight" "四格封印不完整"
[[ "$(jq -r '.target_feature_rows_read' "$QUALIFICATION_SEAL")" == "0" ]] \
  || fail 49 "postflight" "资格封印声明读取目标特征"
[[ "$(jq -r '.target_label_rows_read' "$QUALIFICATION_SEAL")" == "0" ]] \
  || fail 50 "postflight" "资格封印声明读取目标标签"

write_status "finished" "source-qualified" 0 "N14 源年选择、四格指标和资格封印完成；目标仍由外部主进程阻塞"
printf '%s\n' "N14 源年资格完成：$OUTPUT_ROOT"
