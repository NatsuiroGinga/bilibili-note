# P1 验证记录

## 仅新增阶段

先创建 `thesis/experiments/llm_probe/scripts/AGENTS.md`，未删除父级原文。初稿为 6,160 字节，四层项目链暂时为 45,898 字节，仅用于 65,536 字节诊断。

执行：

```bash
codex --cd /Users/bilibili/personal/note/thesis/experiments/llm_probe/scripts \
  --config project_doc_max_bytes=65536 \
  debug prompt-input "不得搜索文件；核对脚本规则哨兵、日志父目录、set -Eeuo pipefail、PIPESTATUS 与远程能力预检。"
```

结果：四个哨兵全部出现，`NOTE_LLM_PROBE_SCRIPTS` 可见；日志父目录、`set -Eeuo pipefail`、`PIPESTATUS`、`command -v fd`、`command -v rg`、`command -v uv` 和子文件尾部均完整可见。仅新增差异保存在 `add-only.patch`。

## 最终字节预算

| 文件                  | 字节数 |
| --------------------- | -----: |
| 根 `AGENTS.md`        |  8,035 |
| `thesis/AGENTS.md`    |  6,202 |
| `llm_probe/AGENTS.md` | 16,456 |
| `scripts/AGENTS.md`   |  1,641 |

- `llm_probe` 链：30,693 字节，余 2,075 字节。
- `scripts` 自动注入链：32,334 字节，余 434 字节。
- 完整脚本执行合同：6,857 字节，在任何脚本修改、同步或运行前由局部规则强制读取，不计入启动时自动链。

## 默认预算新进程

三个目录均使用不带预算覆盖的命令：

```bash
codex --cd <目录> debug prompt-input "只报告启动时注入的规则哨兵，不得调用工具或搜索文件。"
```

| 目录        | 实际哨兵                                              | 完整性                                                |
| ----------- | ----------------------------------------------------- | ----------------------------------------------------- |
| 仓库根      | `NOTE_ROOT_20260724`                                  | 根规则尾部可见；没有深层哨兵                          |
| `llm_probe` | 根、`NOTE_THESIS_20260724`、`NOTE_LLM_PROBE_20260724` | 父规则最后一条生成式评测规则可见；没有脚本哨兵        |
| `scripts`   | 根、thesis、llm_probe、`NOTE_LLM_PROBE_SCRIPTS`       | 脚本路由、尾部语法门禁、`PIPESTATUS` 与能力预检均可见 |

模型行为另用只读临时新会话验证：从 `llm_probe` 接收“修改 `scripts/example.sh`”任务时，在不调用工具的条件下正确报告三个已注入哨兵，并指出修改前必须完整读取 `thesis/experiments/llm_probe/scripts/AGENTS.md`。会话启动时部分可选 MCP 与 WebSocket 报警，但 HTTPS 回退完成并返回正确结果。

## 格式与回滚检查

通过项：

```bash
prettier --ignore-path /dev/null --write <本任务 Markdown 文件>
git diff --check
git apply -R --check .Codex/docs/agents-split/20260730-130222/P1/stage.patch
```

- Prettier 对所有本任务 Markdown 文件完成；规则文件均无需改写。
- `git diff --check` 无输出，退出 0。
- P1 反向补丁检查无输出，退出 0；未实际回滚。
- P0 三份快照的 SHA-256 在 P1 完成后再次核对，仍与实施前一致。

首次在普通沙箱格式化 `baseline.md` 和 `migration-map.md` 时因 `.Codex/docs/` 写权限返回 `EPERM`；随后按权限流程仅对这两个文件在沙箱外重跑 Prettier，并成功完成。该错误不涉及规则内容或语法。
