#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

usage() {
  printf 'Usage: bash %s RUN_ROOT SEED VARIANT REASON\n' "${BASH_SOURCE[0]}" >&2
}

fail() {
  printf 'archive-error: %s\n' "$*" >&2
  exit 1
}

require_command() {
  local command_name=$1
  if ! command -v "$command_name" >/dev/null 2>&1; then
    fail "required command is unavailable: ${command_name}"
  fi
}

resolve_fd_command() {
  if command -v fd >/dev/null 2>&1; then
    printf '%s\n' fd
    return 0
  fi
  if command -v fdfind >/dev/null 2>&1; then
    printf '%s\n' fdfind
    return 0
  fi
  fail 'required command is unavailable: fd or fdfind'
}

move_without_overwrite() {
  local source_path=$1
  local destination_path=$2

  if [[ -e "$destination_path" || -L "$destination_path" ]]; then
    fail "refusing to overwrite destination: ${destination_path}"
  fi
  mv -T -n -- "$source_path" "$destination_path"
  if [[ -e "$source_path" || -L "$source_path" || ! -e "$destination_path" ]]; then
    fail "no-clobber move did not complete: ${source_path}"
  fi
}

validate_label() {
  local value=$1
  local label=$2
  if [[ ! "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    fail "${label} must be a non-empty ASCII path label"
  fi
}

checkpoint_entry() {
  local source_dir=$1
  "$fd_command" --hidden --no-ignore '^[.]?checkpoint-' "$source_dir"
}

validate_failed_source() {
  local source_dir=$1
  local state_path="$source_dir/run_state.json"
  local checkpoint_hit

  if [[ ! -d "$source_dir" || -L "$source_dir" ]]; then
    fail "variant directory is missing or is a symbolic link: ${source_dir}"
  fi
  if [[ ! -f "$state_path" || -L "$state_path" ]]; then
    fail "run_state.json is missing or is not a regular file: ${state_path}"
  fi
  if ! jq -e '
    type == "object"
    and has("status")
    and has("current_step")
    and has("latest_checkpoint")
    and .status == "failed"
    and ((.current_step | type) == "number")
    and .current_step == 0
    and .latest_checkpoint == null
  ' "$state_path" >/dev/null; then
    fail "variant is not an eligible zero-step failed run: ${source_dir}"
  fi
  if [[ -e "$source_dir/finalization_receipt.json" || -L "$source_dir/finalization_receipt.json" ]]; then
    fail "finalization receipt exists: ${source_dir}"
  fi
  checkpoint_hit=$(checkpoint_entry "$source_dir")
  if [[ -n "$checkpoint_hit" ]]; then
    fail "checkpoint entry exists: ${checkpoint_hit}"
  fi
}

write_payload_manifest() {
  local payload_root=$1
  local output_path=$2
  local temporary_path="${output_path}.partial.$$"

  # 清单覆盖普通文件与符号链接；符号链接摘要针对链接目标文本计算。
  (
    cd "$payload_root"
    "$fd_command" --hidden --no-ignore --type f --type l --print0 . \
      | while IFS= read -r -d '' relative_path; do
          local_path=${relative_path#./}
          if [[ "$local_path" == *$'\n'* || "$local_path" == *$'\r'* || "$local_path" == *$'\t'* ]]; then
            fail "payload path contains a control separator"
          fi
          if [[ -L "$local_path" ]]; then
            link_target=$(readlink -- "$local_path")
            if [[ "$link_target" == *$'\n'* || "$link_target" == *$'\r'* || "$link_target" == *$'\t'* ]]; then
              fail "symbolic-link target contains a control separator"
            fi
            byte_size=$(LC_ALL=C printf '%s' "$link_target" | wc -c | tr -d '[:space:]')
            checksum_line=$(LC_ALL=C printf '%s' "$link_target" | sha256sum)
            checksum=${checksum_line%% *}
            printf 'L\t%s\t%s\t%s\n' "$byte_size" "$checksum" "$local_path"
          else
            byte_size=$(stat -c '%s' -- "$local_path")
            checksum_line=$(sha256sum -- "$local_path")
            checksum=${checksum_line%% *}
            printf 'F\t%s\t%s\t%s\n' "$byte_size" "$checksum" "$local_path"
          fi
        done
  ) | LC_ALL=C sort >"$temporary_path"
  move_without_overwrite "$temporary_path" "$output_path"
}

if [[ "$#" -ne 4 ]]; then
  usage
  exit 2
fi

run_root_arg=$1
seed=$2
variant=$3
reason=$4

for command_name in cmp date jq mv readlink sha256sum sort stat tr wc; do
  require_command "$command_name"
done
fd_command=$(resolve_fd_command)
if [[ ! "$seed" =~ ^(0|[1-9][0-9]*)$ ]]; then
  fail 'seed must be a non-negative base-10 integer'
fi
validate_label "$variant" variant
validate_label "$reason" reason
if [[ ! -d "$run_root_arg" ]]; then
  fail "run root does not exist: ${run_root_arg}"
fi

run_root=$(cd "$run_root_arg" && pwd -P)
seed_root="$run_root/seed-${seed}"
source_dir="$seed_root/$variant"
archive_parent="$seed_root/failed-attempts"

if [[ ! -d "$seed_root" || -L "$seed_root" ]]; then
  fail "seed directory is missing or is a symbolic link: ${seed_root}"
fi
validate_failed_source "$source_dir"

for reserved_name in archive-manifest-before.tsv archive-manifest-after.tsv archive-receipt.json; do
  if [[ -e "$source_dir/$reserved_name" || -L "$source_dir/$reserved_name" ]]; then
    fail "reserved archive evidence name already exists: ${reserved_name}"
  fi
done

if [[ -e "$archive_parent" || -L "$archive_parent" ]]; then
  if [[ ! -d "$archive_parent" || -L "$archive_parent" ]]; then
    fail "archive parent is not a regular directory: ${archive_parent}"
  fi
else
  mkdir -- "$archive_parent"
fi

source_device=$(stat -c '%d' -- "$source_dir")
archive_device=$(stat -c '%d' -- "$archive_parent")
if [[ "$source_device" != "$archive_device" ]]; then
  fail 'source and archive parent are not on the same file system'
fi

archive_utc=$(date -u +%Y%m%dT%H%M%SZ)
archive_name="${variant}-${reason}-${archive_utc}"
destination="$archive_parent/$archive_name"
before_manifest="$archive_parent/.${archive_name}.before.tsv"
after_manifest="$archive_parent/.${archive_name}.after.tsv"

for pending_path in "$destination" "$before_manifest" "$after_manifest"; do
  if [[ -e "$pending_path" || -L "$pending_path" ]]; then
    fail "archive destination or evidence path already exists: ${pending_path}"
  fi
done

write_payload_manifest "$source_dir" "$before_manifest"

# 在原子移动前再次检查状态，避免归档已进入训练或收尾阶段的组。
validate_failed_source "$source_dir"
move_without_overwrite "$source_dir" "$destination"
write_payload_manifest "$destination" "$after_manifest"

if ! cmp -s -- "$before_manifest" "$after_manifest"; then
  move_without_overwrite "$before_manifest" "$destination/archive-manifest-before.tsv"
  move_without_overwrite "$after_manifest" "$destination/archive-manifest-after.tsv"
  fail "payload manifest mismatch after move: ${destination}"
fi

manifest_checksum_line=$(sha256sum -- "$before_manifest")
manifest_checksum=${manifest_checksum_line%% *}
move_without_overwrite "$before_manifest" "$destination/archive-manifest-before.tsv"
move_without_overwrite "$after_manifest" "$destination/archive-manifest-after.tsv"

receipt_path="$destination/archive-receipt.json"
receipt_temporary="${receipt_path}.partial.$$"
jq -n \
  --arg source "$source_dir" \
  --arg destination "$destination" \
  --arg variant "$variant" \
  --arg reason "$reason" \
  --arg archived_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg payload_manifest_sha256 "$manifest_checksum" \
  --argjson seed "$seed" \
  '{schema_version: 1, status: "verified", source: $source, destination: $destination, seed: $seed, variant: $variant, reason: $reason, archived_at: $archived_at, payload_manifest_sha256: $payload_manifest_sha256}' \
  >"$receipt_temporary"
move_without_overwrite "$receipt_temporary" "$receipt_path"

printf 'ARCHIVE_STATUS=verified\n'
printf 'ARCHIVE_PATH=%s\n' "$destination"
printf 'PAYLOAD_MANIFEST_SHA256=%s\n' "$manifest_checksum"
