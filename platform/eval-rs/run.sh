#!/usr/bin/env bash
# 运行 Rust 评测服务；libtorch 动态库来自冻结实验环境的 Python torch。
set -euo pipefail
cd "$(dirname "$0")"
TORCH_LIB="/opt/miniconda3/envs/rwkv/lib/python3.14/site-packages/torch/lib"
export DYLD_LIBRARY_PATH="${TORCH_LIB}:${DYLD_LIBRARY_PATH:-}"
exec ./target/release/ch5-eval-rs "$@"
