#!/usr/bin/env bash
# 全容量表格 ResNet（表格预归一化残差多层感知机）骨干专属论文配方协议 A 远程启动器。
#
# 用法：
#   bash scripts/remote_launchers/run_ch3_tabular_resnet_paper_recipe_protocol_a_seed42_v1.sh \
#       [--stage <select-input|select-optimizer|cells|evaluate>] [--resume]
#
# 阶段顺序固定为 select-input -> select-optimizer -> cells -> evaluate；
# 未显式给出 --stage 时自动从首个未完成阶段续跑，已完成阶段幂等跳过。
# 内部由 screen 以 "--worker --stage <阶段> [--resume]" 重入本脚本，人工不需要
# 直接传入 --worker。
#
# 启动前按顺序执行十一道机械门禁（见 run_gates），任一门禁失败都保留诊断并以
# 非零码退出，绝不创建 screen 会话；门禁全部通过后才进入分阶段执行。
#
# 身份说明（本脚本不负责校验，仅记录约束来源以便排障）：冻结结构为输入投影
# 83->192、两个 LayerNorm 预归一化残差块 192->384->192、CPA 融合 384->192 与输出头
# 192->1，可训练参数量恒为 387074；两个输入候选的输出维同为 83，因此参数量相等。
# 这些由 tools/ch3_tabular_resnet_paper_recipe_protocol_a.py 自身在 --validate-config
# 与 build_model 内部三方比对，本启动器只在门禁 3 做一次轻量复核。

PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe

if [[ -r "$HOME/.bashrc" ]]; then
    source "$HOME/.bashrc" || true
fi
source "$PROJECT_ROOT/tools/env/activate.sh"
set -Eeuo pipefail
umask 027

readonly RUN_ID=ch3-tabular-resnet-paper-recipe-protocol-a-seed42-v1
readonly SCREEN_NAME="$RUN_ID"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-tabular-resnet-paper-recipe-protocol-a-seed42-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_tabular_resnet_paper_recipe_protocol_a.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_tabular_resnet_paper_recipe_protocol_a_seed42_v1.sh"
readonly MEMORY_GATE_PATH="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly CARDINALITY_RECEIPT_PATH="$PROJECT_ROOT/runs/diagnostics/ch3-lspr23-field-cardinality-receipt-v1/field-cardinality-receipt.json"
readonly PRECISION_PROFILES_PATH="$PROJECT_ROOT/configs/neural-precision-profiles-v1.json"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly RESOURCE_RECEIPT="$OUTPUT_ROOT/resource-receipt.json"
readonly RESOURCE_SAMPLES="$OUTPUT_ROOT/resource-samples.tsv"
readonly EXPECTED_PARAMETER_COUNT=387074
readonly -a STAGE_ORDER=(select-input select-optimizer cells evaluate)
# 防止 pgrep 匹配到自身：用 [c] 字符类拆开固定脚本名首字母。
readonly PEER_PROCESS_PATTERN="python.*[c]h3_tabular_resnet_paper_recipe_protocol_a[.]py.*${RUN_ID}"

# 运行期状态变量，先用空串初始化以满足 set -u。
MONITOR_PID=""
GPU_FREE_MIN_MIB=""
ESTIMATED_PEAK_GIB=""
DISK_AVAILABLE_KIB=""
DISK_USED_PERCENT=""
GPU_FREE_MIB_AT_ADMISSION=""
SAMPLE_INTERVAL_SECONDS=""

cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# 通用助手
# ---------------------------------------------------------------------------

# 读取冻结配置里的整型字段，参数为点分路径，例如
# resource_contract.minimum_free_disk_gib。
read_config_int() {
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
node = config
for key in sys.argv[2].split("."):
    node = node[key]
print(int(node))
' "$CONFIG_PATH" "$1"
}

launcher_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    mkdir -p -- "$LAUNCHER_ROOT"
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-tabular-resnet-paper-recipe-protocol-a-launcher-status-v1",
    "run_id": sys.argv[2], "state": sys.argv[3], "stage": sys.argv[4],
    "detail": sys.argv[5], "exit_code": None if sys.argv[6] == "null" else int(sys.argv[6]),
    "updated_at_unix": time.time(),
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$LAUNCHER_ROOT/status.json" "$RUN_ID" "$state" "$stage" "$detail" "$exit_code"
}

stage_status_path() {
    printf '%s/stages/%s.json' "$LAUNCHER_ROOT" "$1"
}

stage_is_finished() {
    local path
    path=$(stage_status_path "$1")
    [[ -s "$path" ]] && rg -q '"state": "finished"' "$path"
}

write_stage_status() {
    local stage=$1 state=$2 detail=$3 exit_code=$4
    mkdir -p -- "$LAUNCHER_ROOT/stages"
    local path
    path=$(stage_status_path "$stage")
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-tabular-resnet-paper-recipe-protocol-a-stage-status-v1",
    "run_id": sys.argv[2], "stage": sys.argv[3], "state": sys.argv[4],
    "detail": sys.argv[5], "exit_code": None if sys.argv[6] == "null" else int(sys.argv[6]),
    "updated_at_unix": time.time(),
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$path" "$RUN_ID" "$stage" "$state" "$detail" "$exit_code"
}

# 以纯重定向（非管道）方式执行一个机械门禁函数，避免管道产生的子 Shell
# 吞掉门禁内部为后续门禁设置的变量（例如 GPU_FREE_MIN_MIB）。
run_gate() {
    local name=$1 log_path=$2
    shift 2
    mkdir -p -- "$(dirname "$log_path")"
    "$@" > "$log_path" 2>&1
    local code=$?
    if (( code == 0 )); then
        printf '门禁通过：%s（诊断见 %s）\n' "$name" "$log_path"
    else
        printf '门禁失败：%s，退出码=%s\n' "$name" "$code" >&2
        cat "$log_path" >&2
    fi
    return "$code"
}

# 以 tee 管道方式执行外部命令并记录日志。关闭 errexit 后立即保存完整
# PIPESTATUS，分别检查主命令与 tee 的退出码。
run_logged() {
    local log_path=$1
    shift
    mkdir -p -- "$(dirname "$log_path")"
    set +e
    "$@" 2>&1 | tee "$log_path"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    printf '%s\n' "${pipeline_status[0]}" > "$log_path.command-exit-code.txt"
    printf '%s\n' "${pipeline_status[1]}" > "$log_path.tee-exit-code.txt"
    if (( pipeline_status[1] != 0 )); then
        return "${pipeline_status[1]}"
    fi
    return "${pipeline_status[0]}"
}

check_capability() {
    local missing=0 tool located
    for tool in rg uv screen flock nvidia-smi sha256sum; do
        if ! located=$(command -v "$tool"); then
            printf '缺少必需命令：%s\n' "$tool" >&2
            missing=1
        fi
    done
    return "$missing"
}

# ---------------------------------------------------------------------------
# 十一道机械门禁（1 加载 activate.sh 已在脚本顶部完成，2-11 见下）
# ---------------------------------------------------------------------------

# 门禁 2：调用工具自身的 --validate-config。
gate_validate_config() {
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config
}

# 门禁 3：冻结结构与参数量复核。工具内部已做闭式、冻结登记值与实例化三方比对，
# 本门禁只在启动前最后再核一次配置侧的登记值与禁增结构开关，失败时不用等进程
# 起来即可停住。
gate_architecture_freeze() {
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
expected_total = int(sys.argv[2])
architecture = config.get("architecture")
if not isinstance(architecture, dict):
    print("配置缺少 architecture 对象", file=sys.stderr)
    raise SystemExit(78)
errors = []
expected_scalars = {
    "input_dimension": 83, "main_width": 192, "hidden_width": 384,
    "hidden_factor": 2.0, "residual_blocks": 2, "activation": "relu",
    "hidden_dropout": 0.15, "residual_dropout": 0.0, "fusion_dropout": 0.1,
    "normalization": "per_token_layer_norm",
}
for key, expected in expected_scalars.items():
    if architecture.get(key) != expected:
        errors.append(f"architecture.{key} 期望 {expected}，实际 {architecture.get(key)}")
for key in ("additional_normalization_layers", "attention", "gating", "multi_scale",
            "piecewise_linear_encoding", "port_embedding"):
    if architecture.get(key) is not False:
        errors.append(f"architecture.{key} 必须为假（禁止增加该结构），实际 {architecture.get(key)}")
if architecture.get("normalization_deviates_from_paper_batch_norm") is not True:
    errors.append("architecture.normalization_deviates_from_paper_batch_norm 必须为真："
                  "LayerNorm 替代 BatchNorm 是任务适配，须显式标注")
d_in = 83
d = 192
h = 384
blocks = 2
closed_form = (d_in * d + d) + blocks * (2 * d + d * h + h + h * d + d) + (2 * d * d + d) + (d + 1 + 1)
if closed_form != expected_total:
    errors.append(f"启动器独立复算的闭式参数量 {closed_form} 与期望 {expected_total} 不符")
declared_total = architecture.get("parameter_count")
if declared_total != expected_total:
    errors.append(f"architecture.parameter_count 期望 {expected_total}，实际 {declared_total}")
for candidate in config.get("input_candidates", []):
    candidate_key = candidate.get("key")
    candidate_dimension = candidate.get("input_dimension")
    candidate_total = candidate.get("parameter_count")
    if candidate_dimension != d_in:
        errors.append(f"输入候选 {candidate_key} 的 input_dimension 期望 {d_in}，实际 {candidate_dimension}")
    if candidate_total != expected_total:
        errors.append(f"输入候选 {candidate_key} 的 parameter_count 期望 {expected_total}，实际 {candidate_total}")
if errors:
    for message in errors:
        print(f"冻结结构复核失败：{message}", file=sys.stderr)
    raise SystemExit(78)
print(f"冻结结构复核通过：两块 192/384 残差、闭式与登记参数量均为 {expected_total}，禁增结构开关全为假")
' "$CONFIG_PATH" "$EXPECTED_PARAMETER_COUNT"
}

# 门禁 4：字段基数收据存在且 complete 为真。收据路径必须从配置的
# paths.field_cardinality_receipt 读取——工具运行时真正打开的是这一条，不是
# 启动器写死的常量；先与 CARDINALITY_RECEIPT_PATH 交叉核对，不一致时显式失败，
# 避免"门禁在一份文件上报通过、工具在另一份文件上跑"的错位。
gate_cardinality_receipt() {
    local declared_path
    if ! declared_path=$(uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
print(config["paths"]["field_cardinality_receipt"])
' "$CONFIG_PATH"); then
        printf '读取配置字段 paths.field_cardinality_receipt 失败\n' >&2
        return 78
    fi
    if [[ "$declared_path" != "$CARDINALITY_RECEIPT_PATH" ]]; then
        printf '配置声明的收据路径与启动器固定路径不一致：配置=%s 启动器=%s\n' \
            "$declared_path" "$CARDINALITY_RECEIPT_PATH" >&2
        return 78
    fi
    if [[ ! -s "$declared_path" ]]; then
        printf '字段基数收据不存在或为空：%s\n' "$declared_path" >&2
        return 66
    fi
    uv run --no-sync python -c '
import json, pathlib, sys
receipt = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if receipt.get("complete") is not True:
    print("字段基数收据 complete 字段不为真，拒绝消费", file=sys.stderr)
    raise SystemExit(66)
print("字段基数收据核对通过：complete=true")
' "$declared_path"
}

# 门禁 5：精度档案存在，且配置声明的 precision_profile_id 在其 profiles 成员
# 之列。只核对成员资格，不在启动器内复述精度合同的具体取值。
gate_precision_profile_membership() {
    if [[ ! -s "$PRECISION_PROFILES_PATH" ]]; then
        printf '精度档案不存在或为空：%s\n' "$PRECISION_PROFILES_PATH" >&2
        return 66
    fi
    local profile_id
    if ! profile_id=$(uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
print(config["precision_profile_id"])
' "$CONFIG_PATH"); then
        printf '读取配置字段 precision_profile_id 失败\n' >&2
        return 78
    fi
    uv run --no-sync python -c '
import json, pathlib, sys
profiles_document = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
profile_id = sys.argv[2]
profiles = profiles_document.get("profiles", {})
if profile_id not in profiles:
    print(f"精度档案中未找到配置声明的 precision_profile_id：{profile_id}", file=sys.stderr)
    raise SystemExit(78)
print(f"精度档案成员核对通过：{profile_id}")
' "$PRECISION_PROFILES_PATH" "$profile_id"
}

# 门禁 6：分位数候选准入台账自洽门。四个策略键各自的 value 与 source 必须同时
# 存在或同时为 null——有值无依据是魔法数字，有依据无值是登记不全，两者都必须
# 在启动前停住。本门禁只判自洽与报告准入状态，不裁定候选二是否应当参与：
# 那由工具的 resolve_quantile_policy 依同一份台账机械裁定。
gate_quantile_policy_ledger() {
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
policy = config.get("quantile_policy")
if not isinstance(policy, dict):
    print("配置缺少 quantile_policy 对象", file=sys.stderr)
    raise SystemExit(78)
expected_keys = ["noise_standard_deviation", "output_distribution", "n_quantiles", "subsample"]
if list(policy.keys()) != expected_keys:
    print(f"quantile_policy 键集合或顺序不符，期望 {expected_keys}，实际 {list(policy.keys())}",
          file=sys.stderr)
    raise SystemExit(78)
errors = []
missing = []
for key in expected_keys:
    entry = policy[key]
    if not isinstance(entry, dict) or set(entry.keys()) != {"value", "source"}:
        errors.append(f"quantile_policy.{key} 必须是恰含 value 与 source 两键的对象")
        continue
    has_value = entry["value"] is not None
    has_source = isinstance(entry["source"], str) and bool(entry["source"].strip())
    if has_value != has_source:
        errors.append(f"quantile_policy.{key} 的 value 与 source 未同时存在或同时为 null")
    if not has_value:
        missing.append(key)
if errors:
    for message in errors:
        print(f"分位数台账自洽门失败：{message}", file=sys.stderr)
    raise SystemExit(78)
if missing:
    print(f"分位数台账自洽门通过：候选二 source-quantile-83 未准入，缺少依据的策略键={missing}；"
          "阶段一只比较候选一 standardized-83，缺项与理由会写入封印")
else:
    print("分位数台账自洽门通过：四个策略键均已封印，候选二 source-quantile-83 参与阶段一比较")
' "$CONFIG_PATH"
}

# 门禁 7：显存阈值门。resource_contract.minimum_free_gpu_memory_mib 若为 null，
# 说明该阈值待裁定，显式失败退出——这是有意设计的阻塞点。
gate_gpu_threshold_present() {
    local value
    if ! value=$(uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
value = config["resource_contract"]["minimum_free_gpu_memory_mib"]
print("null" if value is None else value)
' "$CONFIG_PATH"); then
        printf '读取配置字段 resource_contract.minimum_free_gpu_memory_mib 失败\n' >&2
        return 78
    fi
    if [[ "$value" == null ]]; then
        printf 'GPU 显存准入阈值待裁定：resource_contract.minimum_free_gpu_memory_mib 为 null\n' >&2
        return 71
    fi
    if [[ ! "$value" =~ ^[0-9]+$ ]]; then
        printf 'GPU 显存准入阈值类型不合法：%s\n' "$value" >&2
        return 78
    fi
    GPU_FREE_MIN_MIB="$value"
    printf 'GPU 显存准入阈值已裁定：%s MiB\n' "$GPU_FREE_MIN_MIB"
}

# 门禁 8：调用 tools/memory_admission_gate.sh（读 cgroup，不读宿主机 free）。
# 预计峰值取冻结配置的 resource_contract.minimum_cgroup_available_memory_gib，
# 该值是冻结合同里唯一可追溯的 GiB 量级，不额外臆造。
gate_memory_admission() {
    local estimated_peak_gib
    if ! estimated_peak_gib=$(read_config_int resource_contract.minimum_cgroup_available_memory_gib); then
        printf '读取配置字段 resource_contract.minimum_cgroup_available_memory_gib 失败\n' >&2
        return 78
    fi
    ESTIMATED_PEAK_GIB="$estimated_peak_gib"
    bash "$MEMORY_GATE_PATH" "$estimated_peak_gib" "$RUN_ID"
}

# 门禁 9：磁盘可用量满足 resource_contract.minimum_free_disk_gib。
gate_disk_space() {
    local minimum_gib disk_fields available_kib used_percent minimum_kib
    if ! minimum_gib=$(read_config_int resource_contract.minimum_free_disk_gib); then
        printf '读取配置字段 resource_contract.minimum_free_disk_gib 失败\n' >&2
        return 78
    fi
    disk_fields=$(df -Pk "$PROJECT_ROOT" | tail -n 1)
    available_kib=$(printf '%s\n' "$disk_fields" | awk '{print $4}')
    used_percent=$(printf '%s\n' "$disk_fields" | awk '{gsub(/%/, "", $5); print $5}')
    minimum_kib=$(( minimum_gib * 1024 * 1024 ))
    if [[ ! "$available_kib" =~ ^[0-9]+$ || ! "$used_percent" =~ ^[0-9]+$ ]]; then
        printf '磁盘资源读数无效：available_kib=%s used_percent=%s\n' "$available_kib" "$used_percent" >&2
        return 69
    fi
    if (( available_kib < minimum_kib || used_percent >= 80 )); then
        printf '磁盘资源门失败：available_kib=%s used_percent=%s minimum_kib=%s\n' \
            "$available_kib" "$used_percent" "$minimum_kib" >&2
        return 69
    fi
    DISK_AVAILABLE_KIB="$available_kib"
    DISK_USED_PERCENT="$used_percent"
    printf '磁盘资源门通过：available_kib=%s used_percent=%s minimum_kib=%s\n' \
        "$DISK_AVAILABLE_KIB" "$DISK_USED_PERCENT" "$minimum_kib"
}

# 门禁 10：GPU 空闲显存满足门禁 7 裁定的阈值。
gate_gpu_free_memory() {
    local free_mib
    free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | awk 'NR == 1 {gsub(/ /, "", $0); print $0}')
    if [[ ! "$free_mib" =~ ^[0-9]+$ ]]; then
        printf 'GPU 空闲显存读数无效：%s\n' "$free_mib" >&2
        return 69
    fi
    if (( free_mib < GPU_FREE_MIN_MIB )); then
        printf 'GPU 空闲显存不足：free_mib=%s minimum=%s\n' "$free_mib" "$GPU_FREE_MIN_MIB" >&2
        return 69
    fi
    GPU_FREE_MIB_AT_ADMISSION="$free_mib"
    printf 'GPU 空闲显存门通过：free_mib=%s minimum=%s\n' "$GPU_FREE_MIB_AT_ADMISSION" "$GPU_FREE_MIN_MIB"
}

# 门禁 11：并发互斥门。GRANDE、TabM32 或 FT-Transformer 的 screen 会话活动时不得
# 强行启动，避免同卡资源争用。判据：按会话名前缀检测，已知前缀为 ch3-grande、
# ch3-tabm32 与 ch3-ft-transformer。这是名称模式检测，不是精确进程识别——若对方
# screen 会话改名或以其他前缀重启，本门禁无法探测到，需要人工核对看板与
# `screen -ls` 的实际输出。
gate_concurrency_mutex() {
    local peer_sessions prefix found=0
    for prefix in ch3-grande ch3-tabm32 ch3-ft-transformer; do
        peer_sessions=$(screen -ls | rg -i "$prefix" || true)
        if [[ -n "$peer_sessions" ]]; then
            if (( found == 0 )); then
                printf '同卡邻居 screen 会话仍在运行，按看板约定不得强行启动：\n' >&2
                found=1
            fi
            printf '%s\n' "$peer_sessions" >&2
        fi
    done
    if (( found != 0 )); then
        return 72
    fi
    printf '并发互斥门通过：未发现 ch3-grande、ch3-tabm32 或 ch3-ft-transformer 前缀的 screen 会话\n'
}

run_gates() {
    run_gate "02-validate-config" "$LAUNCHER_ROOT/gates/02-validate-config.log" gate_validate_config || return $?
    run_gate "03-architecture-freeze" "$LAUNCHER_ROOT/gates/03-architecture-freeze.log" gate_architecture_freeze || return $?
    run_gate "04-cardinality-receipt" "$LAUNCHER_ROOT/gates/04-cardinality-receipt.log" gate_cardinality_receipt || return $?
    run_gate "05-precision-profile-membership" "$LAUNCHER_ROOT/gates/05-precision-profile-membership.log" gate_precision_profile_membership || return $?
    run_gate "06-quantile-policy-ledger" "$LAUNCHER_ROOT/gates/06-quantile-policy-ledger.log" gate_quantile_policy_ledger || return $?
    run_gate "07-gpu-threshold-present" "$LAUNCHER_ROOT/gates/07-gpu-threshold-present.log" gate_gpu_threshold_present || return $?
    run_gate "08-memory-admission" "$LAUNCHER_ROOT/gates/08-memory-admission.log" gate_memory_admission || return $?
    run_gate "09-disk-space" "$LAUNCHER_ROOT/gates/09-disk-space.log" gate_disk_space || return $?
    run_gate "10-gpu-free-memory" "$LAUNCHER_ROOT/gates/10-gpu-free-memory.log" gate_gpu_free_memory || return $?
    run_gate "11-concurrency-mutex" "$LAUNCHER_ROOT/gates/11-concurrency-mutex.log" gate_concurrency_mutex || return $?
}

# ---------------------------------------------------------------------------
# 资源收据与采样
# ---------------------------------------------------------------------------

write_resource_receipt() {
    local cgroup_limit_bytes cgroup_current_bytes maximum_parallel_jobs maximum_parallel_cells_per_job
    if [[ -r /sys/fs/cgroup/memory.max ]]; then
        cgroup_limit_bytes=$(< /sys/fs/cgroup/memory.max)
        cgroup_current_bytes=$(< /sys/fs/cgroup/memory.current)
    elif [[ -r /sys/fs/cgroup/memory/memory.limit_in_bytes ]]; then
        cgroup_limit_bytes=$(< /sys/fs/cgroup/memory/memory.limit_in_bytes)
        cgroup_current_bytes=$(< /sys/fs/cgroup/memory/memory.usage_in_bytes)
    else
        cgroup_limit_bytes=unavailable
        cgroup_current_bytes=unavailable
    fi
    maximum_parallel_jobs=$(read_config_int resource_contract.maximum_parallel_jobs)
    maximum_parallel_cells_per_job=$(read_config_int resource_contract.maximum_parallel_cells_per_job)
    mkdir -p -- "$OUTPUT_ROOT"
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
def to_int_or_none(text):
    return None if text == "unavailable" else int(text)
value = {
    "schema_version": "ch3-tabular-resnet-paper-recipe-protocol-a-resource-receipt-v1",
    "run_id": sys.argv[2],
    "admitted_at_unix": time.time(),
    "gpu_free_mib_at_admission": int(sys.argv[3]),
    "gpu_free_mib_minimum": int(sys.argv[4]),
    "estimated_peak_gib_for_memory_gate": float(sys.argv[5]),
    "disk_available_kib": int(sys.argv[6]),
    "disk_used_percent": int(sys.argv[7]),
    "cgroup_limit_bytes": to_int_or_none(sys.argv[8]),
    "cgroup_current_bytes_at_admission": to_int_or_none(sys.argv[9]),
    "resource_sample_interval_seconds": int(sys.argv[10]),
    "maximum_parallel_jobs": int(sys.argv[11]),
    "maximum_parallel_cells_per_job": int(sys.argv[12]),
    "concurrent_resource_measurement_is_fair_efficiency_evidence": False,
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$RESOURCE_RECEIPT" "$RUN_ID" \
        "$GPU_FREE_MIB_AT_ADMISSION" "$GPU_FREE_MIN_MIB" "$ESTIMATED_PEAK_GIB" \
        "$DISK_AVAILABLE_KIB" "$DISK_USED_PERCENT" \
        "$cgroup_limit_bytes" "$cgroup_current_bytes" \
        "$SAMPLE_INTERVAL_SECONDS" "$maximum_parallel_jobs" "$maximum_parallel_cells_per_job"
}

resource_monitor() {
    printf 'unix_time\tgpu_used_mib\tcgroup_current_bytes\n' > "$RESOURCE_SAMPLES"
    while true; do
        local gpu_used cgroup_current
        gpu_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | awk 'NR == 1 {gsub(/ /, "", $0); print $0}')
        if [[ -r /sys/fs/cgroup/memory.current ]]; then
            cgroup_current=$(< /sys/fs/cgroup/memory.current)
        elif [[ -r /sys/fs/cgroup/memory/memory.usage_in_bytes ]]; then
            cgroup_current=$(< /sys/fs/cgroup/memory/memory.usage_in_bytes)
        else
            cgroup_current=unavailable
        fi
        printf '%s\t%s\t%s\n' "$(date +%s)" "$gpu_used" "$cgroup_current" >> "$RESOURCE_SAMPLES"
        sleep "$SAMPLE_INTERVAL_SECONDS"
    done
}

finalize_resources() {
    if [[ ! -s "$RESOURCE_SAMPLES" ]]; then
        printf '资源采样文件缺失或为空，跳过收据汇总：%s\n' "$RESOURCE_SAMPLES" >&2
        return 0
    fi
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
receipt_path = pathlib.Path(sys.argv[1])
samples_path = pathlib.Path(sys.argv[2])
receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
rows = []
for line in samples_path.read_text(encoding="utf-8").splitlines()[1:]:
    fields = line.split("\t")
    if len(fields) != 3:
        continue
    unix_time, gpu_used, cgroup_current = fields
    try:
        rows.append((
            int(unix_time), int(gpu_used),
            None if cgroup_current == "unavailable" else int(cgroup_current),
        ))
    except ValueError:
        continue
if not rows:
    raise SystemExit("资源采样为空或全部不可解析")
peak_gpu_used = max(row[1] for row in rows)
cgroup_values = [row[2] for row in rows if row[2] is not None]
peak_cgroup_current = max(cgroup_values) if cgroup_values else None
receipt.update({
    "finished_at_unix": time.time(),
    "sample_count": len(rows),
    "peak_gpu_used_mib": peak_gpu_used,
    "peak_cgroup_current_bytes": peak_cgroup_current,
})
temporary = receipt_path.with_name(receipt_path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, receipt_path)
' "$RESOURCE_RECEIPT" "$RESOURCE_SAMPLES"
}

# ---------------------------------------------------------------------------
# 分阶段执行
# ---------------------------------------------------------------------------

# 未显式指定起始阶段时，取首个未完成阶段；若四个阶段全部已完成则回落到最后一个
# 阶段（run_stage_loop 会把它当作已完成继续幂等跳过）。
resolve_start_stage() {
    local explicit=$1
    if [[ -n "$explicit" ]]; then
        printf '%s\n' "$explicit"
        return 0
    fi
    local stage
    for stage in "${STAGE_ORDER[@]}"; do
        if ! stage_is_finished "$stage"; then
            printf '%s\n' "$stage"
            return 0
        fi
    done
    printf '%s\n' "${STAGE_ORDER[-1]}"
}

run_stage_loop() {
    local start_stage=$1 resume_flag=$2
    local started=0 stage completed=0 total=${#STAGE_ORDER[@]}
    local loop_start now elapsed remaining stage_code throughput_per_hour
    loop_start=$(date +%s)
    for stage in "${STAGE_ORDER[@]}"; do
        if (( started == 0 )); then
            if [[ "$stage" == "$start_stage" ]]; then
                started=1
            else
                completed=$((completed + 1))
                continue
            fi
        fi
        if stage_is_finished "$stage" && [[ -z "$resume_flag" ]]; then
            printf '阶段=%s 已完成，幂等跳过\n' "$stage"
            write_stage_status "$stage" skipped already_finished null
            completed=$((completed + 1))
            continue
        fi
        write_stage_status "$stage" running stage_started null
        now=$(date +%s)
        printf '阶段=%s 开始：%s（已完成阶段=%s/%s，累计耗时=%ss）\n' \
            "$stage" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$completed" "$total" "$(( now - loop_start ))"
        if run_logged "$OUTPUT_ROOT/${stage}.log" uv run --no-sync python "$TOOL_PATH" \
            --config "$CONFIG_PATH" --stage "$stage" --resource-receipt "$RESOURCE_RECEIPT" ${resume_flag:+--resume}; then
            write_stage_status "$stage" finished stage_finished 0
        else
            stage_code=$?
            write_stage_status "$stage" failed stage_failed "$stage_code"
            return "$stage_code"
        fi
        completed=$((completed + 1))
        now=$(date +%s)
        elapsed=$((now - loop_start))
        remaining=0
        throughput_per_hour=0
        if (( completed > 0 && elapsed > 0 )); then
            remaining=$(( elapsed * (total - completed) / completed ))
            throughput_per_hour=$(( completed * 3600 / elapsed ))
        fi
        printf '心跳：已处理量=%s 总量=%s 吞吐=%s阶段/小时 累计耗时=%ss 估计剩余=%ss\n' \
            "$completed" "$total" "$throughput_per_hour" "$elapsed" "$remaining"
    done
    if (( started == 0 )); then
        printf '未找到起始阶段：%s\n' "$start_stage" >&2
        return 64
    fi
}

on_worker_signal() {
    if [[ -n "$MONITOR_PID" ]]; then
        kill "$MONITOR_PID" || true
    fi
    launcher_status interrupted worker signal_received 130
    exit 130
}

worker() {
    local start_stage=$1 resume_flag=$2 code=0
    mkdir -p -- "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || { printf '同名运行锁已占用。\n' >&2; return 75; }
    trap on_worker_signal HUP INT TERM

    if ! uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config \
        > "$LAUNCHER_ROOT/worker-revalidate.log" 2>&1; then
        cat "$LAUNCHER_ROOT/worker-revalidate.log" >&2
        launcher_status failed worker revalidate_config_failed 78
        return 78
    fi

    SAMPLE_INTERVAL_SECONDS=$(read_config_int resource_contract.resource_sample_interval_seconds)
    launcher_status running "$start_stage" stage_loop_started null
    resource_monitor &
    MONITOR_PID=$!

    if run_stage_loop "$start_stage" "$resume_flag"; then
        code=0
    else
        code=$?
    fi

    kill "$MONITOR_PID" || true
    wait "$MONITOR_PID" || true
    MONITOR_PID=""

    # 收据汇总失败不应阻断收尾状态写入，否则运行会永远卡在 running。
    if ! finalize_resources; then
        printf '资源收据汇总失败，已记录但不阻断收尾状态写入\n' >&2
    fi

    if (( code != 0 )); then
        launcher_status failed worker stage_loop_failed "$code"
        return "$code"
    fi

    launcher_status finished complete all_stages_finished 0
}

# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------

usage() {
    printf '用法：%s [--stage <select-input|select-optimizer|cells|evaluate>] [--resume]\n' "$0" >&2
}

MODE=launch
START_STAGE=""
RESUME_FLAG=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --worker)
            MODE=worker
            shift
            ;;
        --stage)
            START_STAGE="${2:-}"
            shift 2
            ;;
        --resume)
            RESUME_FLAG=1
            shift
            ;;
        *)
            usage
            exit 64
            ;;
    esac
done

if [[ -n "$START_STAGE" ]]; then
    stage_known=0
    for candidate_stage in "${STAGE_ORDER[@]}"; do
        if [[ "$candidate_stage" == "$START_STAGE" ]]; then
            stage_known=1
        fi
    done
    if (( stage_known == 0 )); then
        printf '未知阶段：%s\n' "$START_STAGE" >&2
        exit 64
    fi
fi

if [[ "$MODE" == worker ]]; then
    resolved_stage=$(resolve_start_stage "$START_STAGE")
    worker "$resolved_stage" "$RESUME_FLAG"
    exit $?
fi

if ! check_capability; then
    exit 76
fi
for required_path in "$CONFIG_PATH" "$TOOL_PATH" "$SCRIPT_PATH" "$MEMORY_GATE_PATH"; do
    [[ -s "$required_path" ]] || { printf '生产文件未完整同步：%s\n' "$required_path" >&2; exit 67; }
done

if screen -ls | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '已存在同名 screen，不重复启动：%s\n' "$SCREEN_NAME"
    exit 0
fi
if peer_pid=$(pgrep -f "$PEER_PROCESS_PATTERN"); then
    printf '检测到同运行身份的进程已在运行，拒绝重复启动：%s\n' "$peer_pid" >&2
    exit 75
fi

if [[ -s "$LAUNCHER_ROOT/status.json" ]] && rg -q '"state": "finished"' "$LAUNCHER_ROOT/status.json"; then
    printf '同一运行身份已完成，不重复启动：%s\n' "$OUTPUT_ROOT"
    exit 0
fi

if run_gates; then
    :
else
    gate_exit_code=$?
    launcher_status failed gates mechanical_gate_failed "$gate_exit_code"
    exit "$gate_exit_code"
fi

SAMPLE_INTERVAL_SECONDS=$(read_config_int resource_contract.resource_sample_interval_seconds)
write_resource_receipt

resolved_stage=$(resolve_start_stage "$START_STAGE")
mkdir -p -- "$LAUNCHER_ROOT"
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
printf '%s --stage %s%s\n' "$SCRIPT_PATH" "$resolved_stage" "${RESUME_FLAG:+ --resume}" > "$LAUNCHER_ROOT/command.txt"
sha256sum "$CONFIG_PATH" "$TOOL_PATH" "$SCRIPT_PATH" "$MEMORY_GATE_PATH" > "$LAUNCHER_ROOT/input-sha256.txt"
launcher_status prepared launch mechanical_gates_passed null

screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker --stage "$resolved_stage" ${RESUME_FLAG:+--resume}
resume_display=false
if [[ -n "$RESUME_FLAG" ]]; then
    resume_display=true
fi
printf 'CH3_TABULAR_RESNET_PAPER_RECIPE_PROTOCOL_A_STARTED session=%s output=%s start_stage=%s resume=%s\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT" "$resolved_stage" "$resume_display"
