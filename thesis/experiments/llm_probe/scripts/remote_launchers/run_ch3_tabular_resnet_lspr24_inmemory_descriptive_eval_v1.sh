#!/usr/bin/env bash
# 表格 ResNet 四格 LSPR24 零物化内存直读描述性评价启动器。
# 用法：bash run_ch3_tabular_resnet_lspr24_inmemory_descriptive_eval_v1.sh [verify|selfcheck|evaluate|all]
# 该运行不训练、不物化、不改阈值、不碰源年封印；旧运行
# ch3-tabular-resnet-lspr24-zero-train-descriptive-eval-v1 保留作证据，不被覆盖。

source ~/.bashrc >/dev/null 2>&1
set -euo pipefail

PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
RUN_ID="ch3-tabular-resnet-lspr24-inmemory-descriptive-eval-v1"
CONFIG="$PROJECT_ROOT/configs/$RUN_ID.json"
ENTRY="$PROJECT_ROOT/tools/ch3_tabular_resnet_lspr24_inmemory_descriptive_eval.py"
LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
ACTION="${1:-all}"

case "$ACTION" in
    verify|selfcheck|evaluate|all) ;;
    *)
        printf '%s\n' "用法：bash $0 [verify|selfcheck|evaluate|all]" >&2
        exit 2
        ;;
esac

cd "$PROJECT_ROOT"
# shellcheck source=/dev/null
source "$PROJECT_ROOT/tools/env/activate.sh"
export OMP_NUM_THREADS=1
# `src/` 已由可编辑安装进入导入路径，`tools/` 没有；protocol_a_raw83 依赖
# tools/ 下的 dijk2026_replication.dijk_fields，故显式并入 PYTHONPATH。
export PYTHONPATH="$PROJECT_ROOT/tools${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/root/autodl-tmp/.cache/pycache}"

[ -f "$CONFIG" ] || { printf '%s\n' "配置缺失：$CONFIG" >&2; exit 3; }
[ -f "$ENTRY" ] || { printf '%s\n' "入口缺失：$ENTRY" >&2; exit 4; }

# 源年自检要走冻结标签解析器，用途令牌只能来自既有环境，不在脚本内回显或写入。
if [ "$ACTION" = "selfcheck" ] || [ "$ACTION" = "all" ]; then
    [ -n "${PROTOCOL_A_RAW83_VALIDATE_LABEL_TOKEN:-}" ] \
        || { printf '%s\n' "验证标签用途令牌环境变量未设置" >&2; exit 5; }
fi

mkdir -p "$LAUNCHER_ROOT"
LOG="$LAUNCHER_ROOT/$ACTION.log"
STATE="$LAUNCHER_ROOT/$ACTION-exit-code.txt"
rm -f "$STATE"

set +e
uv run --no-sync python "$ENTRY" --config "$CONFIG" --action "$ACTION" 2>&1 | tee "$LOG"
codes=("${PIPESTATUS[@]}")
set -e
main_code="${codes[0]}"
tee_code="${codes[1]}"
printf '%s\n' "$main_code" > "$STATE"
if [ "$tee_code" -ne 0 ]; then
    printf '%s\n' "tee 写日志失败，退出码 $tee_code" >&2
    exit "$tee_code"
fi
exit "$main_code"
