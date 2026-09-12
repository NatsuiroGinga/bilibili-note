# DRIFT 正式运行断点与并发防护实施计划

> **面向实现代理：** 必须使用 `subagent-driven-development` 执行本计划；实现前完整读取本目录 `notes.md`、目标脚本及适用的 `AGENTS.md`。本任务只修复工程可靠性，不改变科研问题、模型公式、数据合同、实验臂、评价指标或停止条件。

## 一、目标

使 `official_p2p3_full.py` 在正式全量训练中具备可验证的断点恢复语义、运行合同校验、同臂单写者保护和并发安全的结果落盘。旧 v1/v2 断点一律拒绝迁移；修复完成后仍不得直接重启，须先由主代理冻结 `krand` 面板与目标采样上限两项科学合同。

## 二、文件边界

- 修改：`.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official_p2p3_full.py`
- 新建：`.Codex/docs/2026-09-12-DRIFT正式运行断点恢复修复/implementation-report.md`
- 不修改：模型结构、A/B/D/F/G 臂定义、损失公式、学习率、种子、批量默认值、轮数、数据读取、攻击算子、目标评价采样规则、SwanLab project。

## 三、实现任务

### 任务 1：版本化断点、游标语义与并发写入修复

**断点合同**：

- 增加 `CHECKPOINT_SCHEMA_VERSION = "p2p3_official_full_checkpoint_v2"`。
- 在任何断点加载前初始化随机数发生器、对抗缓存、FPR 曲线、epoch 日志、样本数、批次数和变体配额。
- 断点写入并校验：`schema_version`、`arm`、`seed`、`batch`、`epochs`、`n_train`、`quota`、`progress_semantics="next_batch_to_process"`。
- 使用 `next_epoch` 与 `next_batch_idx`；完成批 `bi` 后保存下一批 `bi + 1`，完成 epoch 评价后保存下一 epoch 与批 `0`。
- 恢复时保留已加载的 Python、NumPy、PyTorch 随机状态和 `adv_cache`，不得随后重新初始化覆盖。
- 旧格式或合同不一致的断点必须失败关闭，错误列出全部不一致项；不得删除、覆盖或自动迁移。
- 加载断点后不得删除现有断点；继续使用临时文件加原子替换写新断点。

**并发合同**：

- 使用 `fcntl.flock` 为每个臂建立单写者锁，锁至少覆盖断点加载、训练、该臂目标评价和该臂结果写入。
- 同一臂已有写者时立即失败并给出锁路径，不得等待后并行写入。
- 保留 `result_{arm}.json`；共享 `result_all.json` 改为包含本次臂集合的独立汇总文件，避免不同进程最后写者覆盖。
- 日志必须区分“从头训练”和“断点恢复”，不能在无断点时打印续训措辞。

**明确排除**：

- 不实现真正的随机 `k` 攻击，不重命名历史结果键。
- 不改变 `--target-limit 200000` 默认值。
- 不改变对抗缓存的生成分布或把有状态缓存重构为无状态算子。
- 不启动服务器或本机正式训练。

## 四、验收命令

本仓库禁止人工夹具、单元测试、集成测试和 `black`。实现代理执行：

```bash
PYTHONPYCACHEPREFIX=/tmp/drift-formal-pycache /opt/miniconda3/envs/rwkv/bin/python -m py_compile .Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official_p2p3_full.py
/opt/miniconda3/envs/rwkv/bin/python .Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official_p2p3_full.py --help
```

主代理另做静态语义核验：合同字段齐全、恢复后无状态覆盖、保存游标指向下一未处理批、加载时不删除、锁覆盖范围正确、并发汇总无共享覆盖。真实恢复验证留到服务器可用且两项科学合同冻结后，必须使用新运行目录，不接续旧 v1/v2 断点。

## 五、状态

- [x] 2026-09-12：SwanLab 中断事实核查完成。
- [x] 2026-09-12：确定性工程缺陷与科学合同缺口分离。
- [ ] 实现代理完成代码与报告。
- [ ] 主代理完成代码复核和验收命令。
- [ ] 两项科学合同冻结后，以新身份做真实断点恢复验证。
