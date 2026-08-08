# 任务十一稀疏状态监督实现报告

## 实现范围

- 在 `physics_train.py` 新增确定性状态掩码接口，支持 `dense`、`anchor0_only`、`anchor0_plus_one`。
- `anchor0_plus_one` 按 `seed + group_id` 哈希排序唯一组，再循环分配 `q1-q4`，保证组计数差不超过 1；返回值按 `sample_id` 索引，同组样本复用内部锚点。
- 新增掩码状态均方误差，训练只使用观测锚点；队列守恒残差仍使用完整预测状态，未修改物理公式、LoRA 结构和既有 `dense` 语义。
- 验证阶段新增观测与未观测锚点均方误差；摘要新增监督模式、观测比例和训练掩码哈希。
- 新增种子 42 稀疏监督配置与 `S1-S4` 运行脚本，物理损失权重固定为 `0.01`。
- 按用户加速授权未采用测试驱动开发；实现后补充契约测试，但未在本机运行 Pytest。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/physics_train.py`
- `thesis/experiments/llm_probe/tests/test_physics_train.py`
- `thesis/experiments/llm_probe/configs/physics_sparse_seed42.yaml`
- `thesis/experiments/llm_probe/scripts/run_physics_sparse.sh`

## 后置验证

- `UV_CACHE_DIR=/tmp/uv-cache uv run --group dev black src/flow_probe/physics_train.py tests/test_physics_train.py`：通过，两个文件无需继续改动。
- `UV_CACHE_DIR=/tmp/uv-cache uv run --group dev ruff check src/flow_probe/physics_train.py tests/test_physics_train.py`：通过。
- `PYTHONPYCACHEPREFIX=/tmp/task11-pycache python3 -m py_compile src/flow_probe/physics_train.py tests/test_physics_train.py`：通过。
- `bash -n scripts/run_physics_sparse.sh`：通过。
- 本机未运行 Pytest，符合仓库要求。

## 服务器定向测试

```bash
source /root/.bashrc
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest -q tests/test_physics_train.py -k 'anchor0_only_masks or anchor0_plus_one_balances or masked_state_loss'
```

## 遗留风险

- 尚未在服务器项目环境运行定向 Pytest，也未执行两步 GPU 冒烟。
- `dense` 模式的未观测锚点集合为空，摘要写入 `null`，且不会向 SwanLab 发送非数值的未观测指标；稀疏模式会记录数值。
- 实验结果无论通过或失败，都只裁决当前 `q0` 锚定稀疏监督与现有残差和训练方式，不裁决是否保留 PINN 研究方向。
