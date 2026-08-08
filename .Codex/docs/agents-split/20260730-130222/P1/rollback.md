# P1 回滚说明

P1 正向补丁位于 `stage.patch`，只包含以下规则文件：

- `AGENTS.md`。
- `thesis/experiments/llm_probe/AGENTS.md`。
- `thesis/experiments/llm_probe/scripts/AGENTS.md`。

回滚前必须先运行：

```bash
git apply -R --check .Codex/docs/agents-split/20260730-130222/P1/stage.patch
```

检查通过后才可执行：

```bash
git apply -R .Codex/docs/agents-split/20260730-130222/P1/stage.patch
```

当前反向检查已经通过，但本阶段没有实际回滚。若任一目标文件在此后出现并发改动，必须停止自动应用，改用 `apply_patch` 对照 P0 快照逐项恢复，禁止覆盖用户改动。

反向应用后，`.Codex/docs/agents-split/` 下的快照、映射、完整执行合同、历史说明和报告仍作为证据保留。若确认不再被任何后续阶段引用，可整体移动到 `.Codex/docs/archive/`，不得删除其他历史记录。
