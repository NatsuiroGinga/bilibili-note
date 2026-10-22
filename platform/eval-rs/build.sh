#!/usr/bin/env bash
# 使用冻结实验环境的 Python torch 作为 libtorch 来源构建 Rust 评测服务。
set -euo pipefail
cd "$(dirname "$0")"
export PATH="/opt/miniconda3/envs/rwkv/bin:${PATH}"
export VIRTUAL_ENV="/opt/miniconda3/envs/rwkv"
export LIBTORCH_USE_PYTORCH=1
# 依赖 pin 到 tch-rs 的 "Update for pytorch 2.12" 提交：
# d5bbf6fe6cdbb06006aac5cb673be3c8d029c24b（torch-sys 声明 TORCH_VERSION=2.12.0）。
exec cargo build --release
