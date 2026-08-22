# SwanLab 统一标签门与 GRANDE 发布修复计划

## 任务目标

1. 在 `src/flow_probe/tracking.py` 建立唯一 SwanLab 最终合同函数，使配置校验与运行时初始化使用同一实现。
2. 新增预注册标签别名表和全配置扫描器，机械报告现有直接 `swanlab.init` 入口；本轮不迁移全仓入口。
3. 新增 GRANDE 独立 `publish-repair` 身份，只读绑定已完成的 G-A/G-B 选择、源侧聚合结果、完整曲线、检查点、资源收据和父配置哈希，零训练上传既有聚合指标。

## 文件所有权

- 修改：`thesis/experiments/llm_probe/src/flow_probe/tracking.py`
- 新增：`thesis/experiments/llm_probe/configs/swanlab-tag-aliases-v1.json`
- 新增：`thesis/experiments/llm_probe/tools/validate_swanlab_contracts.py`
- 新增：`thesis/experiments/llm_probe/tools/ch3_grande_swanlab_publish_repair.py`
- 新增：`thesis/experiments/llm_probe/configs/ch3-grande-swanlab-publish-repair-v1.json`
- 新增：`thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_grande_swanlab_publish_repair_v1.sh`
- 新增：本目录 `实施报告.md`
- 不修改父 GRANDE 配置、状态、检查点、聚合结果和历史失败证据。

## P0 实施步骤

1. 在统一函数中严格验证最终标签：容器必须显式为 `list` 或 `tuple`；每项必须严格为 `str`；原值须与 `strip()` 相同且非空；按 Unicode 码点计数不超过 20；总数不超过 50；原标签无重复；NFC 规范化后无冲突；只接受预注册单射别名，禁止静默截断。
2. 同一合同同时验证 `workspace`、`project`、`name`、`group`，拒绝 `SWANLAB_TAGS` 环境漂移，写入包含原标签、有效标签、别名映射、规范化结果与目的地的标签收据。
3. 提供统一 SwanLab 初始化入口；GRANDE 发布修复不得直接调用 `swanlab.init`。
4. 扫描器对真实 JSON 配置调用同一合同函数，并列出剩余直接初始化入口；扫描报告不自动改写旧配置或源码。
5. GRANDE 修复在任何 SwanLab 操作前验证父运行所需制品及 SHA-256，确认 G-A/G-B 均为 20 轮、20000 步且已有选择；禁止读取训练数据和目标年数组。
6. 发布修复只执行 `swanlab ping`、`swanlab verify`、统一初始化、上传已有聚合指标并结束，产出 `parent-binding.json`、`tag-receipt.json`、`swanlab-receipt.json`、`status.json`、`manifest.json` 和 `publish-repair.log`。

## 阻塞条件

- 父运行任一绑定制品缺失、哈希不一致或 G-A/G-B 完成条件不满足。
- 父配置、状态或失败证据需要改写。
- `SWANLAB_TAGS` 存在且与最终有效标签不一致。
- 标签无法通过预注册别名表机械变换为合法集合。
- SwanLab 目的地与启动器授权值不一致。
- `ping` 或 `verify` 任一失败。

## 验收命令

```bash
UV_CACHE_DIR=/tmp/uv-cache PYTHONPYCACHEPREFIX=/tmp/codex-pycache uv run --no-sync python -m py_compile src/flow_probe/tracking.py tools/validate_swanlab_contracts.py tools/ch3_grande_swanlab_publish_repair.py
UV_CACHE_DIR=/tmp/uv-cache PYTHONPYCACHEPREFIX=/tmp/codex-pycache uv run --no-sync python -c 'from flow_probe.tracking import validate_swanlab_contract, initialize_swanlab_run; print("import-ok")'
UV_CACHE_DIR=/tmp/uv-cache PYTHONPYCACHEPREFIX=/tmp/codex-pycache uv run --no-sync python tools/validate_swanlab_contracts.py --help
UV_CACHE_DIR=/tmp/uv-cache PYTHONPYCACHEPREFIX=/tmp/codex-pycache uv run --no-sync python tools/ch3_grande_swanlab_publish_repair.py --help
UV_CACHE_DIR=/tmp/uv-cache PYTHONPYCACHEPREFIX=/tmp/codex-pycache uv run --no-sync python tools/ch3_grande_swanlab_publish_repair.py --config configs/ch3-grande-swanlab-publish-repair-v1.json --validate-config
UV_CACHE_DIR=/tmp/uv-cache PYTHONPYCACHEPREFIX=/tmp/codex-pycache uv run --no-sync python tools/validate_swanlab_contracts.py --config-root configs --alias-config configs/swanlab-tag-aliases-v1.json --output /tmp/swanlab-contract-scan.json
bash -n scripts/remote_launchers/run_ch3_grande_swanlab_publish_repair_v1.sh
git diff --check
```

## 状态

- [x] 恢复规则、审计事实与故障手册。
- [x] 定位根因并冻结单一修复假设。
- [ ] 实现统一合同与配置扫描器。
- [ ] 实现 GRANDE 零重训发布修复。
- [ ] 完成静态验收与实施报告。

