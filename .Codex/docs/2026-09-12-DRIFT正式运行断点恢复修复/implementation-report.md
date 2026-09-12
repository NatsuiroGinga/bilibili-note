# DRIFT 正式运行断点恢复工程实现报告

## 范围与技能收据

- 实现文件：`.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official_p2p3_full.py`
- 新建报告：本文件。
- 未修改：模型、数据、A/B/D/F/G 臂、损失、攻击算子、`krand` 行为、`--target-limit` 默认值、SwanLab project、启动脚本及其他工作树文件。
- 已读取并执行 `daily-coding` 技能：`/Users/bilibili/.codex/skills/backup/daily-coding-20260811-112930/SKILL.md`；读取时间为 2026-09-12 21:54:00 +0800；SHA256 为 `da2399b50859b9d57281b9bc0dc456082db93d47486ae22967ebf3f17d354ae3`。

## 实现内容

1. 增加 `CHECKPOINT_SCHEMA_VERSION = "p2p3_official_full_checkpoint_v2"`，断点同时绑定模式版本、臂、种子、批量、轮数、训练样本数、批次数、变体配额、`progress_semantics="next_batch_to_process"`、运行设备类型和 CUDA RNG 状态数量。
2. 断点加载前已初始化随机数发生器、对抗缓存、FPR 曲线、epoch 日志、样本数、批次数和变体配额。加载固定使用 `map_location="cpu"`，在任何 RNG 恢复前汇总校验全部合同字段、CPU RNG 张量类型、CUDA RNG 列表类型与数量；旧格式、缺字段、跨设备、设备数不一致或 RNG 状态不合法均失败关闭，保留原断点且不迁移。
3. 使用 `next_epoch` 与 `next_batch_idx`：批 `bi` 的批粒度断点写入 `bi + 1`；epoch 评价后写入下一 epoch 与批 `0`。加载后不删除断点，也不重建覆盖已恢复的随机状态或对抗缓存。仅当当前设备为 CUDA 且校验通过时恢复 CUDA RNG；CPU/MPS 断点的 `None` 不会传给 CUDA API。
4. `--arms` 会剥离空白、拒绝空值、重复值和未知臂，只允许 A/B/D/F/G，并按固定允许顺序规范化。因此锁、权重、结果和唯一汇总集合名不接受任意路径片段。
5. 参数解析后、数据或模型加载前拒绝 `--epochs <= 0`（错误包含当前值）与 `--target-limit < 0`；保持 `0=全量` 和正数上限的既有语义。训练前数据门另拒绝非正批量、空训练集、训练域和标签数量不一致、零批次，以及未同时且仅含标签 0/1 的训练数据。
6. 每臂以非阻塞 `fcntl.flock` 保护断点加载、训练、该臂目标评价及 `result_{arm}.json` 原子写入；已有同臂写者会立即报出锁文件路径并停止。无论任一臂或汇总写入是否异常，`finally` 都会调用 `run.finish()`；收尾异常仅写入中文 stderr，不覆盖训练或锁异常，也不阻塞本地结果。
7. 保留每臂结果文件；总汇总改为 `result_all_<本次臂集合>.json`，并采用临时文件加原子替换，避免不同臂集合进程共同覆盖 `result_all.json`。启动日志明确分为“从头训练”与“断点恢复”。

## 验证

- 通过：`git diff --check`。
- 通过：`PYTHONPYCACHEPREFIX=/tmp/drift-formal-pycache /opt/miniconda3/envs/rwkv/bin/python -m py_compile .Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official_p2p3_full.py`。
- 计划原样的 `--help` 命令在本机默认远端根目录下因缺少 `ch3_drift_official_branch_conflict_diagnostic` 导入失败；这是本机没有 `/root/autodl-tmp/...` 的路径依赖，尚未触及训练。
- 通过：以本工作树的 `thesis/experiments/llm_probe` 映射 `LLM_PROBE_ROOT` 后运行同一脚本 `--help`，正常显示四个参数。
- 通过静态检索：CPU 映射加载、设备与 CUDA RNG 数量合同、RNG 类型与数量检查、严格臂解析、参数和训练前数据门、非阻塞锁、独立汇总名与不掩盖原异常的 `run.finish()` 收尾均存在；旧的 `ckpt_path.unlink()` 与共享 `result_all.json` 写入已不存在。

## 未验证边界

- 本任务没有启动本机或服务器训练，也没有创建人工夹具、单元测试或集成测试。
- 真实恢复、旧断点拒绝、同臂竞争和多进程汇总须在科学合同冻结后，用新的服务器运行目录进行验证；不得接续旧 v1/v2 运行目录。
