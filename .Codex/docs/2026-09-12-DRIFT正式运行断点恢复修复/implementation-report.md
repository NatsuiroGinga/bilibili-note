# DRIFT 正式运行断点恢复工程实现报告

## 范围与技能收据

- 实现文件：`.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official_p2p3_full.py`
- 新建报告：本文件。
- 未修改：模型、数据、A/B/D/F/G 臂、损失、攻击算子、`krand` 行为、`--target-limit` 默认值、SwanLab project、启动脚本及其他工作树文件。
- 已读取并执行 `daily-coding` 技能：`/Users/bilibili/.codex/skills/backup/daily-coding-20260811-112930/SKILL.md`；读取时间为 2026-09-12 21:54:00 +0800；SHA256 为 `da2399b50859b9d57281b9bc0dc456082db93d47486ae22967ebf3f17d354ae3`。

## 实现内容

1. 增加 `CHECKPOINT_SCHEMA_VERSION = "p2p3_official_full_checkpoint_v2"`，断点同时绑定模式版本、臂、种子、批量、轮数、训练样本数、批次数、变体配额与 `progress_semantics="next_batch_to_process"`。
2. 断点加载前已初始化随机数发生器、对抗缓存、FPR 曲线、epoch 日志、样本数、批次数和变体配额。加载先做全字段合同校验；旧格式、缺字段或任一不一致均列出全部发现项并失败关闭，保留原断点且不迁移。
3. 使用 `next_epoch` 与 `next_batch_idx`：批 `bi` 的批粒度断点写入 `bi + 1`；epoch 评价后写入下一 epoch 与批 `0`。加载后不删除断点，也不重建覆盖已恢复的随机状态或对抗缓存。PyTorch CPU 与 CUDA 随机状态均纳入新断点。
4. 每臂以非阻塞 `fcntl.flock` 保护断点加载、训练、该臂目标评价及 `result_{arm}.json` 原子写入；已有同臂写者会立即报出锁文件路径并停止。
5. 保留每臂结果文件；总汇总改为 `result_all_<本次臂集合>.json`，并采用临时文件加原子替换，避免不同臂集合进程共同覆盖 `result_all.json`。
6. 启动日志明确分为“从头训练”与“断点恢复”。

## 验证

- 通过：`git diff --check`。
- 通过：`PYTHONPYCACHEPREFIX=/tmp/drift-formal-pycache /opt/miniconda3/envs/rwkv/bin/python -m py_compile .Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official_p2p3_full.py`。
- 计划原样的 `--help` 命令在本机默认远端根目录下因缺少 `ch3_drift_official_branch_conflict_diagnostic` 导入失败；这是本机没有 `/root/autodl-tmp/...` 的路径依赖，尚未触及训练。
- 通过：以本工作树的 `thesis/experiments/llm_probe` 映射 `LLM_PROBE_ROOT` 后运行同一脚本 `--help`，正常显示四个参数。
- 通过静态检索：模式版本、合同字段、`next_epoch`/`next_batch_idx`、非阻塞锁、独立汇总名均存在；旧的 `ckpt_path.unlink()` 与共享 `result_all.json` 写入已不存在。

## 未验证边界

- 本任务没有启动本机或服务器训练，也没有创建人工夹具、单元测试或集成测试。
- 真实恢复、旧断点拒绝、同臂竞争和多进程汇总须在科学合同冻结后，用新的服务器运行目录进行验证；不得接续旧 v1/v2 运行目录。
