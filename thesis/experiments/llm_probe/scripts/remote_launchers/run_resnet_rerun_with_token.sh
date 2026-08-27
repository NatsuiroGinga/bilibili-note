#!/usr/bin/env bash
# ResNet 同源重评带令牌包装器：从冻结共享配置读取验证标签用途令牌并注入环境，
# 再执行既有启动器。令牌是仓库内公开的 SHA256 承诺值；本脚本不打印、不落盘令牌。
set -Eeuo pipefail

P=/root/autodl-tmp/thesis/experiments/llm_probe
cd "$P"

TOKEN="$(uv run --no-sync python - <<'PY'
import json

payload = json.load(open("configs/ch3-protocol-a-raw83-shared-v1.json", encoding="utf-8"))


def find(node):
    if isinstance(node, dict):
        if "label_stage_token_sha256" in node:
            return node["label_stage_token_sha256"]["validate"]
        for value in node.values():
            result = find(value)
            if result:
                return result
    return None


token = find(payload)
if not token:
    raise SystemExit("共享配置中未找到 label_stage_token_sha256.validate")
print(token)
PY
)"
[ -n "$TOKEN" ] || { printf '%s\n' "令牌读取为空" >&2; exit 5; }
export PROTOCOL_A_RAW83_VALIDATE_LABEL_TOKEN="$TOKEN"
printf '%s\n' "[disclosure] 验证令牌已注入（${#TOKEN} 位，不回显）"

exec bash scripts/remote_launchers/run_ch3_tabular_resnet_lspr24_inmemory_descriptive_eval_v1.sh "${1:-all}"
