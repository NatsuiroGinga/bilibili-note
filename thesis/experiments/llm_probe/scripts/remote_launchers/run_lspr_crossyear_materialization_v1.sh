#!/usr/bin/env bash

PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
source "$PROJECT_ROOT/tools/env/activate.sh" || {
    printf '无法加载项目环境：%s\n' "$PROJECT_ROOT/tools/env/activate.sh" >&2
    exit 70
}
if [[ -r "${HOME}/.bashrc" ]]; then
    source "${HOME}/.bashrc" >/dev/null 2>&1 || {
        printf '无法加载服务器 Shell 环境。\n' >&2
        exit 70
    }
fi
source "$PROJECT_ROOT/tools/env/activate.sh" || {
    printf '重新加载项目环境失败。\n' >&2
    exit 70
}
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT
readonly CONFIG_RELATIVE_PATH=configs/lspr-crossyear-c12-seed42-v1.json
readonly CONFIG_PATH="$PROJECT_ROOT/$CONFIG_RELATIVE_PATH"
readonly RUN_ID=lspr23-lspr24-crossyear-materialization-v1
readonly LAUNCH_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly EXPECTED_LSPR23_ZIP_SIZE=1925103715
readonly EXPECTED_LSPR23_MD5=f3f5bf9f7cecf2186511eabb38f7accc
readonly MIN_AVAILABLE_MEMORY_KIB=$((8 * 1024 * 1024))
readonly STARTED_AT="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
readonly ATTEMPT_ID="$(date -u '+%Y%m%dT%H%M%SZ')-$$"
readonly ATTEMPT_DIR="$LAUNCH_ROOT/attempt-$ATTEMPT_ID"
readonly LOG_PATH="$ATTEMPT_DIR/launcher.log"
readonly ATTEMPT_STATUS_PATH="$ATTEMPT_DIR/status.json"
readonly CANONICAL_STATUS_PATH="$LAUNCH_ROOT/status.json"
readonly LOCK_DIR="$LAUNCH_ROOT/active.lock"
readonly MATERIALIZATION_MARKER="$ATTEMPT_DIR/materialization.started"
readonly CONFIG_SHA_CONTEXT_PATH="$ATTEMPT_DIR/config.sha256"
readonly OUTPUT_ROOT_CONTEXT_PATH="$ATTEMPT_DIR/output-root.txt"

CONFIG_SHA256=unavailable
OUTPUT_ROOT=unavailable
LSPR23_ZIP_PATH=
LSPR24_PARQUET_PATH=
TEMPORARY_ROOT=
OUTPUT_PARTIAL_ROOT=
MD5_MODE=
SHA256_MODE=
LOCK_HELD=0

timestamp() {
    date -u '+%Y-%m-%dT%H:%M:%SZ'
}

json_escape() {
    local value=$1
    value=${value//\\/\\\\}
    value=${value//\"/\\\"}
    value=${value//$'\n'/\\n}
    value=${value//$'\r'/\\r}
    value=${value//$'\t'/\\t}
    printf '%s' "$value"
}

write_state_file() {
    local target_path=$1
    local state=$2
    local phase=$3
    local exit_code=$4
    local finished_at=$5
    local blocking_path=$6
    local recovery_action=$7
    local target_partial="${target_path}.partial"
    local finished_json=null
    local blocking_json=null

    if [[ "$exit_code" != null && ! "$exit_code" =~ ^[0-9]+$ ]]; then
        printf '拒绝写入非法退出码：%s\n' "$exit_code" >&2
        return 65
    fi
    if [[ -n "$finished_at" ]]; then
        finished_json="\"$(json_escape "$finished_at")\""
    fi
    if [[ -n "$blocking_path" ]]; then
        blocking_json="\"$(json_escape "$blocking_path")\""
    fi

    {
        printf '{\n'
        printf '  "schema_version": "lspr-crossyear-materialization-launch-state-v1",\n'
        printf '  "run_id": "%s",\n' "$(json_escape "$RUN_ID")"
        printf '  "attempt_id": "%s",\n' "$(json_escape "$ATTEMPT_ID")"
        printf '  "state": "%s",\n' "$(json_escape "$state")"
        printf '  "phase": "%s",\n' "$(json_escape "$phase")"
        printf '  "exit_code": %s,\n' "$exit_code"
        printf '  "started_at": "%s",\n' "$(json_escape "$STARTED_AT")"
        printf '  "finished_at": %s,\n' "$finished_json"
        printf '  "config_sha256": "%s",\n' "$(json_escape "$CONFIG_SHA256")"
        printf '  "log_path": "%s",\n' "$(json_escape "$LOG_PATH")"
        printf '  "output_root": "%s",\n' "$(json_escape "$OUTPUT_ROOT")"
        printf '  "blocking_path": %s,\n' "$blocking_json"
        printf '  "recovery_action": "%s",\n' "$(json_escape "$recovery_action")"
        printf '  "final_accessed": false\n'
        printf '}\n'
    } > "$target_partial"
    mv -f -- "$target_partial" "$target_path"
}

write_state() {
    local state=$1
    local phase=$2
    local exit_code=$3
    local finished_at=$4
    local blocking_path=$5
    local recovery_action=$6

    write_state_file \
        "$ATTEMPT_STATUS_PATH" \
        "$state" \
        "$phase" \
        "$exit_code" \
        "$finished_at" \
        "$blocking_path" \
        "$recovery_action"
    if [[ "$LOCK_HELD" -eq 1 ]]; then
        cp -f -- "$ATTEMPT_STATUS_PATH" "${CANONICAL_STATUS_PATH}.partial"
        mv -f -- "${CANONICAL_STATUS_PATH}.partial" "$CANONICAL_STATUS_PATH"
    fi
}

log_event() {
    printf '[%s] %s\n' "$(timestamp)" "$*"
}

persist_runtime_context() {
    printf '%s\n' "$CONFIG_SHA256" > "${CONFIG_SHA_CONTEXT_PATH}.partial"
    mv -f -- "${CONFIG_SHA_CONTEXT_PATH}.partial" "$CONFIG_SHA_CONTEXT_PATH"
    printf '%s\n' "$OUTPUT_ROOT" > "${OUTPUT_ROOT_CONTEXT_PATH}.partial"
    mv -f -- "${OUTPUT_ROOT_CONTEXT_PATH}.partial" "$OUTPUT_ROOT_CONTEXT_PATH"
}

fail_run() {
    local code=$1
    local state=$2
    local phase=$3
    local blocking_path=$4
    local recovery_action=$5
    local message=$6
    local finished_at

    trap - ERR
    finished_at=$(timestamp)
    log_event "$message"
    write_state \
        "$state" \
        "$phase" \
        "$code" \
        "$finished_at" \
        "$blocking_path" \
        "$recovery_action"
    exit "$code"
}

handle_unexpected_error() {
    local code=$1
    local line_number=$2
    if [[ "$code" -eq 0 ]]; then
        code=1
    fi
    fail_run \
        "$code" \
        failed \
        unexpected_error \
        "$LOG_PATH" \
        "检查启动日志第 $line_number 行附近的错误；修复后重新调用单入口。" \
        "发生未处理错误：line=$line_number exit_code=$code。"
}

handle_signal() {
    local signal_name=$1
    local code=$2
    fail_run \
        "$code" \
        interrupted \
        signal \
        "$LOG_PATH" \
        "核对日志、输出 .partial 根和工作根；确认身份与输入未变化后再恢复。" \
        "收到信号 $signal_name，已保留状态。"
}

require_command() {
    local command_name=$1
    if command -v "$command_name" >/dev/null 2>&1; then
        log_event "依赖通过：$command_name。"
    else
        fail_run \
            69 \
            blocked \
            preflight_dependencies \
            "$command_name" \
            "在服务器预装该生产依赖；脚本不会自动安装或下载。" \
            "缺少生产依赖：$command_name。"
    fi
}

select_md5_tool() {
    if command -v md5sum >/dev/null 2>&1; then
        MD5_MODE=md5sum
    elif command -v md5 >/dev/null 2>&1; then
        MD5_MODE=md5
    elif command -v openssl >/dev/null 2>&1; then
        MD5_MODE=openssl
    else
        fail_run \
            69 \
            blocked \
            preflight_dependencies \
            md5sum \
            "提供 md5sum、md5 或 openssl；脚本不会自动安装。" \
            "缺少兼容的 MD5 摘要工具。"
    fi
    log_event "MD5 摘要工具通过：$MD5_MODE。"
}

select_sha256_tool() {
    if command -v sha256sum >/dev/null 2>&1; then
        SHA256_MODE=sha256sum
    elif command -v shasum >/dev/null 2>&1; then
        SHA256_MODE=shasum
    elif command -v openssl >/dev/null 2>&1; then
        SHA256_MODE=openssl
    else
        fail_run \
            69 \
            blocked \
            preflight_dependencies \
            sha256sum \
            "提供 sha256sum、shasum 或 openssl；脚本不会自动安装。" \
            "缺少兼容的 SHA-256 摘要工具。"
    fi
    log_event "SHA-256 摘要工具通过：$SHA256_MODE。"
}

compute_md5() {
    local path=$1
    case "$MD5_MODE" in
        md5sum)
            md5sum "$path" | awk '{print $1}'
            ;;
        md5)
            md5 -q "$path"
            ;;
        openssl)
            openssl dgst -md5 "$path" | awk '{print $NF}'
            ;;
        *)
            return 69
            ;;
    esac
}

compute_sha256() {
    local path=$1
    case "$SHA256_MODE" in
        sha256sum)
            sha256sum "$path" | awk '{print $1}'
            ;;
        shasum)
            shasum -a 256 "$path" | awk '{print $1}'
            ;;
        openssl)
            openssl dgst -sha256 "$path" | awk '{print $NF}'
            ;;
        *)
            return 69
            ;;
    esac
}

read_json_string_key() {
    local path=$1
    local key=$2
    awk -v wanted="$key" '
        BEGIN { count = 0 }
        {
            line = $0
            prefix = "^[[:space:]]*\\\"" wanted "\\\"[[:space:]]*:[[:space:]]*\\\""
            if (line ~ prefix) {
                sub(prefix, "", line)
                sub(/\"[[:space:]]*,?[[:space:]]*$/, "", line)
                print line
                count += 1
            }
        }
        END { if (count != 1) exit 65 }
    ' "$path"
}

read_json_bool_key() {
    local path=$1
    local key=$2
    awk -v wanted="$key" '
        BEGIN { count = 0 }
        {
            line = $0
            prefix = "^[[:space:]]*\\\"" wanted "\\\"[[:space:]]*:[[:space:]]*"
            if (line ~ prefix) {
                sub(prefix, "", line)
                sub(/[[:space:]]*,?[[:space:]]*$/, "", line)
                print line
                count += 1
            }
        }
        END { if (count != 1) exit 65 }
    ' "$path"
}

validate_project_path() {
    local field_name=$1
    local path=$2
    if [[ -z "$path" || "$path" == *\\* || "$path" != "$PROJECT_ROOT"/* ]]; then
        fail_run \
            65 \
            blocked \
            preflight_config \
            "$CONFIG_PATH" \
            "修复配置中的 $field_name；该路径必须是项目根内无转义的绝对路径。" \
            "配置路径越界或无法安全解析：$field_name。"
    fi
}

check_existing_state() {
    local receipt_path="$OUTPUT_ROOT/receipts/materialization.json"
    local receipt_status
    local final_accessed

    log_event "既有状态检查开始。"
    if [[ -e "$OUTPUT_ROOT" ]]; then
        if [[ ! -d "$OUTPUT_ROOT" ]]; then
            fail_run \
                20 blocked preflight_existing_state "$OUTPUT_ROOT" \
                "人工核验该路径；脚本不会覆盖或删除。" \
                "正式输出根存在但不是目录：$OUTPUT_ROOT。"
        fi
        if [[ ! -f "$receipt_path" ]]; then
            fail_run \
                21 blocked preflight_existing_state "$receipt_path" \
                "人工核验不完整输出；脚本不会覆盖或删除。" \
                "正式输出缺少成功收据：$receipt_path。"
        fi
        if ! receipt_status=$(read_json_string_key "$receipt_path" status); then
            fail_run \
                22 blocked preflight_existing_state "$receipt_path" \
                "人工核验收据版本和内容；不得改写历史证据。" \
                "无法读取成功收据的 status：$receipt_path。"
        fi
        if ! final_accessed=$(read_json_bool_key "$receipt_path" final_accessed); then
            fail_run \
                22 blocked preflight_existing_state "$receipt_path" \
                "人工核验收据版本和内容；不得改写历史证据。" \
                "无法读取成功收据的 final_accessed：$receipt_path。"
        fi
        if [[ "$receipt_status" != succeeded || "$final_accessed" != false ]]; then
            fail_run \
                23 blocked preflight_existing_state "$receipt_path" \
                "人工核验不完整或违反隔离合同的输出；脚本不会覆盖。" \
                "既有收据不满足 status=succeeded 且 final_accessed=false。"
        fi
        if [[ -e "$OUTPUT_PARTIAL_ROOT" ]]; then
            fail_run \
                24 blocked preflight_existing_state "$OUTPUT_PARTIAL_ROOT" \
                "人工核验残留 .partial 根；脚本不会自动删除。" \
                "成功输出旁仍存在 .partial 根：$OUTPUT_PARTIAL_ROOT。"
        fi
        if [[ -e "$TEMPORARY_ROOT" ]]; then
            fail_run \
                25 blocked preflight_existing_state "$TEMPORARY_ROOT" \
                "人工核验残留工作根；脚本不会自动删除。" \
                "成功输出旁仍存在工作根：$TEMPORARY_ROOT。"
        fi

        log_event "既有状态有效：物化已经成功且 final_accessed=false。"
        write_state \
            already_succeeded \
            complete \
            0 \
            "$(timestamp)" \
            "" \
            "无需恢复；使用既有成功制品，不重复启动物化。"
        exit 0
    fi

    if [[ -e "$OUTPUT_PARTIAL_ROOT" ]]; then
        fail_run \
            24 blocked preflight_existing_state "$OUTPUT_PARTIAL_ROOT" \
            "人工核验残留 .partial 根；脚本不会自动删除。" \
            "发现未完成输出根：$OUTPUT_PARTIAL_ROOT。"
    fi
    if [[ -e "$TEMPORARY_ROOT" ]]; then
        fail_run \
            25 blocked preflight_existing_state "$TEMPORARY_ROOT" \
            "人工核验残留工作根；脚本不会自动删除。" \
            "发现未完成工作根：$TEMPORARY_ROOT。"
    fi
    log_event "既有状态检查通过：无正式输出、.partial 根或工作根。"
}

existing_ancestor() {
    local probe=$1
    local parent
    while [[ ! -e "$probe" ]]; do
        parent=$(dirname -- "$probe")
        if [[ "$parent" == "$probe" ]]; then
            return 66
        fi
        probe=$parent
    done
    if [[ ! -d "$probe" ]]; then
        return 66
    fi
    printf '%s\n' "$probe"
}

cargo_stage_filter() {
    local line
    local materialization_started=0
    while IFS= read -r line || [[ -n "$line" ]]; do
        printf '%s\n' "$line"
        if [[ "$materialization_started" -eq 0 && "$line" == *Running*lspr_crossyear_materialize* ]]; then
            materialization_started=1
            printf '%s\n' "$(timestamp)" > "${MATERIALIZATION_MARKER}.partial"
            mv -f -- "${MATERIALIZATION_MARKER}.partial" "$MATERIALIZATION_MARKER"
            log_event "编译结束：Cargo 已启动固定物化二进制。"
            log_event "正式物化开始。"
            write_state \
                running \
                materializing \
                null \
                "" \
                "" \
                "等待 Rust 业务心跳和最终收据。"
        fi
    done
}

verify_completed_output() {
    local receipt_path="$OUTPUT_ROOT/receipts/materialization.json"
    local receipt_status
    local final_accessed

    if [[ ! -d "$OUTPUT_ROOT" ]]; then
        fail_run \
            74 failed postcondition "$OUTPUT_ROOT" \
            "检查启动日志及 .partial／工作根；不得以退出码 0 冒充发布成功。" \
            "生产命令退出 0，但正式输出根不存在。"
    fi
    if [[ ! -f "$receipt_path" ]]; then
        fail_run \
            74 failed postcondition "$receipt_path" \
            "检查启动日志及发布阶段；不得补写成功收据。" \
            "生产命令退出 0，但成功收据不存在。"
    fi
    if ! receipt_status=$(read_json_string_key "$receipt_path" status); then
        fail_run \
            74 failed postcondition "$receipt_path" \
            "核验收据真实结构；不得按当前脚本格式改写历史证据。" \
            "生产命令退出 0，但无法解析收据 status。"
    fi
    if ! final_accessed=$(read_json_bool_key "$receipt_path" final_accessed); then
        fail_run \
            74 failed postcondition "$receipt_path" \
            "核验收据真实结构；不得补写隔离字段。" \
            "生产命令退出 0，但无法解析 final_accessed。"
    fi
    if [[ "$receipt_status" != succeeded || "$final_accessed" != false ]]; then
        fail_run \
            74 failed postcondition "$receipt_path" \
            "人工核验物化输出；不得把不完整收据升级为成功。" \
            "生产收据不满足 status=succeeded 且 final_accessed=false。"
    fi
    if [[ -e "$OUTPUT_PARTIAL_ROOT" ]]; then
        fail_run \
            74 failed postcondition "$OUTPUT_PARTIAL_ROOT" \
            "人工核验 .partial 残留；脚本不会自动删除。" \
            "发布后仍存在 .partial 根。"
    fi
    if [[ -e "$TEMPORARY_ROOT" ]]; then
        fail_run \
            74 failed postcondition "$TEMPORARY_ROOT" \
            "人工核验工作根残留；脚本不会自动删除。" \
            "发布后仍存在工作根。"
    fi
}

run_main() {
    local zip_size_raw
    local zip_size
    local actual_md5
    local memory_available_kib
    local disk_probe
    local disk_output
    local disk_available_kib
    local command_status
    local cargo_code
    local filter_code
    local failure_code
    local failure_phase
    local blocking_path

    set -Eeuo pipefail
    trap 'handle_unexpected_error "$?" "$LINENO"' ERR
    trap 'handle_signal INT 130' INT
    trap 'handle_signal TERM 143' TERM
    trap 'handle_signal HUP 129' HUP

    log_event "启动跨年度物化单入口：run_id=$RUN_ID attempt_id=$ATTEMPT_ID。"
    write_state \
        running \
        preflight \
        null \
        "" \
        "" \
        "正在执行环境、配置、输入、状态和资源门禁。"

    if [[ "$LOCK_HELD" -ne 1 ]]; then
        fail_run \
            26 blocked preflight_lock "$LOCK_DIR" \
            "核验现有启动进程和状态；若确认是崩溃遗留锁，再由主代理人工处理。" \
            "已有物化入口持有活动锁，拒绝并发启动：$LOCK_DIR。"
    fi
    if [[ "$#" -ne 0 ]]; then
        fail_run \
            64 blocked invocation "$CONFIG_PATH" \
            "不要传入动态参数；入口只使用冻结配置。" \
            "单入口不接受命令行参数。"
    fi

    log_event "预检阶段开始：项目根、配置和日志目录。"
    if [[ ! -d "$PROJECT_ROOT" ]]; then
        fail_run \
            66 blocked preflight_paths "$PROJECT_ROOT" \
            "在 C56 核验服务器身份并同步项目根。" \
            "项目根不存在：$PROJECT_ROOT。"
    elif [[ ! -f "$CONFIG_PATH" ]]; then
        fail_run \
            66 blocked preflight_paths "$CONFIG_PATH" \
            "同步冻结配置并核对 SHA-256。" \
            "冻结配置不存在：$CONFIG_PATH。"
    elif [[ ! -d "$ATTEMPT_DIR" || ! -w "$ATTEMPT_DIR" ]]; then
        fail_run \
            73 blocked preflight_paths "$ATTEMPT_DIR" \
            "修复日志目录权限后重新调用。" \
            "唯一运行目录不可写：$ATTEMPT_DIR。"
    else
        log_event "预检通过：项目根、配置和唯一日志目录可用。"
    fi

    log_event "预检阶段开始：配置读取依赖。"
    require_command awk
    select_sha256_tool
    log_event "预检通过：配置读取依赖齐备。"

    log_event "预检阶段开始：冻结配置路径与摘要。"
    CONFIG_SHA256=$(compute_sha256 "$CONFIG_PATH")
    if [[ ! "$CONFIG_SHA256" =~ ^[0-9a-fA-F]{64}$ ]]; then
        fail_run \
            65 blocked preflight_config "$CONFIG_PATH" \
            "核验 SHA-256 工具和冻结配置。" \
            "配置 SHA-256 输出格式无效。"
    fi
    CONFIG_SHA256=${CONFIG_SHA256,,}
    if ! LSPR23_ZIP_PATH=$(read_json_string_key "$CONFIG_PATH" lspr23_zip_path); then
        fail_run 65 blocked preflight_config "$CONFIG_PATH" \
            "修复冻结配置中的 lspr23_zip_path。" \
            "无法唯一读取 lspr23_zip_path。"
    fi
    if ! LSPR24_PARQUET_PATH=$(read_json_string_key "$CONFIG_PATH" lspr24_parquet_path); then
        fail_run 65 blocked preflight_config "$CONFIG_PATH" \
            "修复冻结配置中的 lspr24_parquet_path。" \
            "无法唯一读取 lspr24_parquet_path。"
    fi
    if ! OUTPUT_ROOT=$(read_json_string_key "$CONFIG_PATH" output_root); then
        fail_run 65 blocked preflight_config "$CONFIG_PATH" \
            "修复冻结配置中的 output_root。" \
            "无法唯一读取 output_root。"
    fi
    if ! TEMPORARY_ROOT=$(read_json_string_key "$CONFIG_PATH" temporary_root); then
        fail_run 65 blocked preflight_config "$CONFIG_PATH" \
            "修复冻结配置中的 temporary_root。" \
            "无法唯一读取 temporary_root。"
    fi
    validate_project_path lspr23_zip_path "$LSPR23_ZIP_PATH"
    validate_project_path lspr24_parquet_path "$LSPR24_PARQUET_PATH"
    validate_project_path output_root "$OUTPUT_ROOT"
    validate_project_path temporary_root "$TEMPORARY_ROOT"
    OUTPUT_PARTIAL_ROOT="${OUTPUT_ROOT}.partial"
    persist_runtime_context
    write_state \
        running \
        preflight_config \
        null \
        "" \
        "" \
        "配置摘要和四个允许访问的路径已经冻结。"
    log_event "预检通过：配置 SHA-256=$CONFIG_SHA256。"

    check_existing_state

    log_event "预检阶段开始：生产依赖。"
    require_command cargo
    require_command unzip
    require_command df
    require_command wc
    require_command dirname
    select_md5_tool
    log_event "预检通过：生产依赖齐备。"

    log_event "预检阶段开始：两个冻结输入。"
    if [[ ! -f "$LSPR23_ZIP_PATH" ]]; then
        fail_run \
            66 blocked preflight_inputs "$LSPR23_ZIP_PATH" \
            "同步 LSPR23 ZIP，并重新核对官方大小与 MD5。" \
            "LSPR23 ZIP 不存在：$LSPR23_ZIP_PATH。"
    elif [[ ! -f "$LSPR24_PARQUET_PATH" ]]; then
        fail_run \
            66 blocked preflight_inputs "$LSPR24_PARQUET_PATH" \
            "同步 LSPR24 Parquet 并核验服务器端路径。" \
            "LSPR24 Parquet 不存在：$LSPR24_PARQUET_PATH。"
    fi
    zip_size_raw=$(wc -c < "$LSPR23_ZIP_PATH")
    if [[ "$zip_size_raw" =~ ^[[:space:]]*([0-9]+)[[:space:]]*$ ]]; then
        zip_size=${BASH_REMATCH[1]}
    else
        fail_run \
            65 blocked preflight_inputs "$LSPR23_ZIP_PATH" \
            "核验文件系统和 wc 输出。" \
            "无法读取 LSPR23 ZIP 大小。"
    fi
    if [[ "$zip_size" -ne "$EXPECTED_LSPR23_ZIP_SIZE" ]]; then
        fail_run \
            65 blocked preflight_inputs "$LSPR23_ZIP_PATH" \
            "重新同步官方 ZIP；不得使用大小不符的输入。" \
            "LSPR23 ZIP 大小不符：actual=$zip_size expected=$EXPECTED_LSPR23_ZIP_SIZE。"
    fi
    log_event "LSPR23 ZIP 大小通过；开始核对官方 MD5。"
    actual_md5=$(compute_md5 "$LSPR23_ZIP_PATH")
    actual_md5=${actual_md5,,}
    if [[ "$actual_md5" != "$EXPECTED_LSPR23_MD5" ]]; then
        fail_run \
            65 blocked preflight_inputs "$LSPR23_ZIP_PATH" \
            "重新同步官方 ZIP；不得使用摘要不符的输入。" \
            "LSPR23 ZIP MD5 不符。"
    fi
    log_event "预检通过：两个输入存在，LSPR23 ZIP 大小与官方 MD5 一致。"

    log_event "预检阶段开始：内存与临时根数据盘空间。"
    if [[ ! -r /proc/meminfo ]]; then
        fail_run \
            66 blocked preflight_resources /proc/meminfo \
            "在 Linux C56 服务器运行并核验可用内存。" \
            "无法读取 /proc/meminfo。"
    fi
    memory_available_kib=$(awk '/^MemAvailable:/ {print $2; found=1; exit} END {if (!found) exit 65}' /proc/meminfo)
    if [[ ! "$memory_available_kib" =~ ^[0-9]+$ ]]; then
        fail_run \
            65 blocked preflight_resources /proc/meminfo \
            "核验 Linux 内存信息格式。" \
            "MemAvailable 不是有效整数。"
    elif [[ "$memory_available_kib" -lt "$MIN_AVAILABLE_MEMORY_KIB" ]]; then
        fail_run \
            75 blocked preflight_resources /proc/meminfo \
            "等待可用内存达到至少 8 GiB 后重新调用。" \
            "可用内存不足 8 GiB。"
    fi
    if ! disk_probe=$(existing_ancestor "$TEMPORARY_ROOT"); then
        fail_run \
            66 blocked preflight_resources "$TEMPORARY_ROOT" \
            "创建或挂载临时根的既有父目录后重新调用；脚本不会创建工作根。" \
            "找不到临时根所在数据盘的既有目录。"
    fi
    if ! disk_output=$(df -Pk "$disk_probe"); then
        fail_run \
            66 blocked preflight_resources "$disk_probe" \
            "核验数据盘挂载和 df 能力。" \
            "df 无法查询临时根所在数据盘。"
    fi
    disk_available_kib=$(printf '%s\n' "$disk_output" | awk 'NR == 2 {print $4}')
    if [[ ! "$disk_available_kib" =~ ^[0-9]+$ ]]; then
        fail_run \
            65 blocked preflight_resources "$disk_probe" \
            "核验 df -Pk 输出和数据盘挂载。" \
            "临时根所在数据盘可用空间无法解析。"
    fi
    log_event "预检通过：可用内存不少于 8 GiB；临时根数据盘当前可用 ${disk_available_kib} KiB，固定 70 GiB 启动门禁已取消，运行时由物化器的磁盘低水位和实际桶空间检查保护。"

    write_state \
        prepared \
        preflight_complete \
        null \
        "" \
        "" \
        "全部门禁通过；即将执行唯一 Cargo 生产命令。"
    log_event "全部预检通过。"

    cd "$PROJECT_ROOT"
    export CARGO_NET_OFFLINE=true
    write_state \
        running \
        compiling \
        null \
        "" \
        "" \
        "Cargo 以 --release --locked 和离线模式编译；成功后自动进入物化。"
    log_event "编译开始：固定 Cargo 生产命令，网络下载已禁用。"

    set +e
    cargo run --release --locked \
        --manifest-path tools/lspr24_g0/Cargo.toml \
        --bin lspr_crossyear_materialize -- \
        --config configs/lspr-crossyear-c12-seed42-v1.json 2>&1 | cargo_stage_filter
    command_status=("${PIPESTATUS[@]}")
    set -e
    cargo_code=${command_status[0]}
    filter_code=${command_status[1]}

    if [[ -f "$MATERIALIZATION_MARKER" ]]; then
        log_event "正式物化结束：cargo_exit_code=$cargo_code。"
        failure_phase=materializing
    else
        log_event "编译结束：cargo_exit_code=$cargo_code，未观察到正式物化启动标记。"
        failure_phase=compiling
    fi

    if [[ "$cargo_code" -ne 0 || "$filter_code" -ne 0 ]]; then
        failure_code=$cargo_code
        if [[ "$failure_code" -eq 0 ]]; then
            failure_code=$filter_code
        fi
        blocking_path=$LOG_PATH
        if [[ -e "$OUTPUT_PARTIAL_ROOT" ]]; then
            blocking_path=$OUTPUT_PARTIAL_ROOT
        elif [[ -e "$TEMPORARY_ROOT" ]]; then
            blocking_path=$TEMPORARY_ROOT
        fi
        fail_run \
            "$failure_code" failed "$failure_phase" "$blocking_path" \
            "检查同一日志及精确残留路径；不得自动删除 .partial 或工作根。" \
            "Cargo 生产命令失败：cargo=$cargo_code filter=$filter_code。"
    fi
    if [[ ! -f "$MATERIALIZATION_MARKER" ]]; then
        fail_run \
            74 failed launch_observation "$LOG_PATH" \
            "核验 Cargo 输出和成功收据；不得在缺少阶段证据时宣告完成。" \
            "Cargo 退出 0，但未观察到物化二进制启动标记。"
    fi

    log_event "发布后置验收开始。"
    verify_completed_output
    log_event "发布后置验收通过：status=succeeded，final_accessed=false，无残留根。"
    write_state \
        finished \
        complete \
        0 \
        "$(timestamp)" \
        "" \
        "无需恢复；使用正式输出和物化收据。"
    log_event "跨年度物化单入口完成。"
}

mkdir -p "$LAUNCH_ROOT"
mkdir "$ATTEMPT_DIR"
if mkdir "$LOCK_DIR" 2>/dev/null; then
    LOCK_HELD=1
fi

if ! command -v tee >/dev/null 2>&1; then
    write_state \
        blocked \
        preflight_dependencies \
        69 \
        "$(timestamp)" \
        tee \
        "在服务器预装 tee；脚本不会自动安装。"
    if [[ "$LOCK_HELD" -eq 1 ]]; then
        rmdir "$LOCK_DIR"
    fi
    printf '缺少日志依赖 tee。\n' >&2
    exit 69
fi

set +e
run_main "$@" 2>&1 | tee "$LOG_PATH"
launcher_status=("${PIPESTATUS[@]}")
set -e
main_code=${launcher_status[0]}
tee_code=${launcher_status[1]}

if [[ -f "$CONFIG_SHA_CONTEXT_PATH" ]]; then
    IFS= read -r CONFIG_SHA256 < "$CONFIG_SHA_CONTEXT_PATH"
fi
if [[ -f "$OUTPUT_ROOT_CONTEXT_PATH" ]]; then
    IFS= read -r OUTPUT_ROOT < "$OUTPUT_ROOT_CONTEXT_PATH"
fi

if [[ "$tee_code" -ne 0 ]]; then
    write_state \
        failed \
        logging \
        "$tee_code" \
        "$(timestamp)" \
        "$LOG_PATH" \
        "修复日志目录或 tee 后，核验既有状态再重新调用；不得盲目重跑。" || true
    printf '日志管道失败：tee_exit_code=%s。\n' "$tee_code" >&2
    main_code=$tee_code
fi

if [[ "$LOCK_HELD" -eq 1 ]]; then
    if ! rmdir "$LOCK_DIR"; then
        write_state \
            failed \
            lock_cleanup \
            73 \
            "$(timestamp)" \
            "$LOCK_DIR" \
            "人工核验活动锁内容和进程；禁止递归删除。" || true
        printf '无法释放活动锁：%s。\n' "$LOCK_DIR" >&2
        exit 73
    fi
fi

exit "$main_code"
