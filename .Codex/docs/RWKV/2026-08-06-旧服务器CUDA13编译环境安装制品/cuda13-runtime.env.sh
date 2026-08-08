# RWKV/Mamba CUDA 扩展编译的项目级可复现环境。
export CUDA_HOME=/usr/local/cuda-13.0
export VIRTUAL_ENV=/root/autodl-tmp/thesis/experiments/llm_probe/.venv
export PATH="$VIRTUAL_ENV/bin:$CUDA_HOME/bin${PATH:+:${PATH}}"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
