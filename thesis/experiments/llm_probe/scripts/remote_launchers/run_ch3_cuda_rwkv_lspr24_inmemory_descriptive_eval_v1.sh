#!/usr/bin/env bash
# 封印后 CUDA-RWKV 四格 LSPR24 零物化内存直读描述性评价启动器。
# 用法：bash run_ch3_cuda_rwkv_lspr24_inmemory_descriptive_eval_v1.sh [verify|selfcheck|evaluate|all]
set -euo pipefail

PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
RUN_ID="ch3-cuda-rwkv-lspr24-inmemory-descriptive-eval-v1"
CONFIG="$PROJECT_ROOT/configs/$RUN_ID.json"
ENTRY="$PROJECT_ROOT/tools/ch3_cuda_rwkv_lspr24_inmemory_descriptive_eval.py"
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
# 与 run_ch3_cuda_rwkv_raw83_qualification_seed42_v1.sh 相同的冻结 CUDA 环境；
# 合法性由 cuda_rwkv_official_backend.validate_build_environment 统一校验，此处不重复设门。
CUDA_HOME="/usr/local/cuda"
export CUDA_HOME
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
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
