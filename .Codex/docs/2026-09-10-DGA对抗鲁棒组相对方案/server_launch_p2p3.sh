#!/bin/zsh
# 官方 24M P2/P3 三臂服务器一键启动（幂等：同步→环境自检→干跑→全量）
# 用法：开机后本机执行  zsh server_launch_p2p3.sh
# 凭据走 GPU_SSH_ACTIVE / GPU_PWD_ACTIVE 环境变量，不落盘

set -e
WT=/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908
cd "$WT"
EXP=$WT/thesis/experiments/llm_probe/tools/remote_exec
L=$WT/.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official_p2p3.py
R=/root/autodl-tmp/thesis/experiments/llm_probe

echo "[1/4] 同步脚本与 T17 val 数据（中和均值重算用）"
expect $EXP/gpu_rsync_push.exp "$L" "$R/tools/official_p2p3.py" > /dev/null
D=$R/runs/data-raw/drift-dga-2026-rev-3b3107020cd1c013d0a75cad51042a2327c4521/DRIFT_input_eSLD
D=$R/runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521/DRIFT_input_eSLD
for f in T17_benign_val.parquet T17_dga_val.parquet; do
  expect $EXP/gpu_rsync_push.exp "$WT/thesis/experiments/llm_probe/runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521/DRIFT_input_eSLD/$f" "$D/$f" > /dev/null
  echo "  ok: $f"
done

echo "[2/4] 服务器环境自检（torch/cuda/依赖/文件）"
expect $EXP/gpu_env_quiet.exp "cd $R && python -c 'import torch,sklearn,pyarrow,transformers; print(torch.__version__, torch.cuda.is_available())' && ls runs/models/drift-official-dsn2026/finetuning.pt runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2/model.py" | tail -3

echo "[3/4] 服务器干跑（每类 300，1 epoch）"
expect $EXP/gpu_env_quiet.exp "cd $R && LLM_PROBE_ROOT=$R P2P3_OUT=$R/runs/diagnostics/p2p3-official-v1 timeout 600 python -u tools/official_p2p3.py --dry-run 300" | tail -4

echo "[4/4] 启动全量三臂（nohup 后台，日志 runs/diagnostics/p2p3-official-v1/console.log）"
expect $EXP/gpu_env_quiet.exp "cd $R && mkdir -p runs/diagnostics/p2p3-official-v1 && LLM_PROBE_ROOT=$R P2P3_OUT=$R/runs/diagnostics/p2p3-official-v1 nohup python -u tools/official_p2p3.py > runs/diagnostics/p2p3-official-v1/console.log 2>&1 & echo LAUNCHED_PID=\$!"
echo "完成：开机到实验启动约 2-4 分钟（同步+自检+干跑+后台启动）"
