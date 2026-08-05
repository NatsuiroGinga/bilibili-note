# 远程启动与脚本规则

<!-- 规则加载哨兵：NOTE_LLM_PROBE_SCRIPTS -->

修改、同步或运行 `scripts/` 前，必须完整读取 `.Codex/docs/agents-split/remote-script-execution-contract.md`；该合同与上级规则同等强制。

- 正式远程操作只用统一启动器；未覆盖时以持久化脚本和参数经白名单 `rsync`、SHA-256 核对后执行，禁止复杂内联。
- `rsync` 只用白名单相对路径，禁止 `--delete`。环境、同步和恢复服从合同；状态、检查点和制品须持久化，不依赖 `screen` 套接字。
- 管道执行前创建日志目录；关闭 `errexit` 时立即保存完整 `PIPESTATUS`，分别检查主命令与 `tee`。失败保留原始退出码和非空脱敏日志。修改的 Shell 脚本仅在交付、审查或提交前集中一次 `bash -n`；`0644` 包装器用 `bash` 启动。
