# R2 DistilBERT 零步失败组归档脚本简报

## 结论

已新增最小恢复辅助脚本 `thesis/experiments/llm_probe/scripts/archive_r2_distilbert_failed_variant.sh`。该脚本只负责把尚未开始训练的失败组移入同一种子目录下的 `failed-attempts/`，不修改训练入口、配置或现有运行制品。

SwanLab `401 Unauthorized` 已由主任务核验为瞬时在线鉴权故障；服务器后续已通过连接、身份、项目和既有运行查询。本脚本不处理登录，也不把基础设施故障解释为实验失败。

## 调用合同

```text
bash scripts/archive_r2_distilbert_failed_variant.sh RUN_ROOT SEED VARIANT REASON
```

目标路径固定为：

```text
RUN_ROOT/seed-<SEED>/failed-attempts/<VARIANT>-<REASON>-<UTC>/
```

参数 `SEED` 必须是十进制非负整数；`VARIANT` 与 `REASON` 只能使用 ASCII 字母、数字、点、下划线和连字符。脚本拒绝复用或覆盖任何已有目标路径。

## 安全门禁

脚本仅在以下条件全部满足时执行移动：

1. 组目录和 `run_state.json` 均存在，且不是符号链接。
2. `run_state.json` 同时满足 `status=failed`、`current_step=0`、`latest_checkpoint=null`。
3. 组目录不存在 `finalization_receipt.json`。
4. 组目录中不存在 `checkpoint-*` 或 `.checkpoint-*` 条目。
5. 源目录与 `failed-attempts/` 位于同一文件系统。
6. 生成移动前清单后，再次执行上述状态与制品门禁。

移动前后清单按相对路径记录条目类型、字节数和 SHA-256。普通文件计算内容摘要；符号链接计算链接目标文本摘要。两份排序清单必须完全一致，否则脚本保留两份清单并以非零状态退出。核对成功后，归档目录保存：

- `archive-manifest-before.tsv`
- `archive-manifest-after.tsv`
- `archive-receipt.json`

脚本控制台输出保持 ASCII，避免远程包装器的编码与转义问题。

## 文件范围

本任务只新增：

- `thesis/experiments/llm_probe/scripts/archive_r2_distilbert_failed_variant.sh`
- `.Codex/docs/sdd/task-r2-physics-sidecar-signal/2026-08-03-r2-distilbert-failed-variant-archive-script.md`

未修改训练代码、三份种子配置、启动器、数据、模型或运行制品。

## 验证

按任务边界只执行了一次 Shell 语法检查：

```text
bash -n thesis/experiments/llm_probe/scripts/archive_r2_distilbert_failed_variant.sh
退出码：0
```

没有运行脚本本体、测试、Pyright、Ruff、格式化或 Git 命令，也没有连接服务器或移动任何运行制品。
