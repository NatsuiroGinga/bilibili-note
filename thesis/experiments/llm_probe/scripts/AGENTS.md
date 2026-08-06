# 远程启动与脚本规则

<!-- 规则加载哨兵：NOTE_LLM_PROBE_SCRIPTS -->

修改、同步或运行 `scripts/` 前，完整读取 `.Codex/docs/agents-split/remote-script-execution-contract.md`；该合同与上级规则同等强制。

- 正式远程操作只用统一启动器；未覆盖时使用持久化脚本和参数，经白名单 `rsync` 与 SHA-256 核对后执行，禁止复杂内联。
- 禁止 `rsync --delete`；状态、检查点、日志和制品必须持久化，不依赖 `screen` 套接字。
- 管道前创建日志目录；关闭 `errexit` 时立即保存完整 `PIPESTATUS`，分别检查主命令与 `tee`。失败保留原始退出码和脱敏日志。
- 正式训练、评估和物化包装器必须使用 `uv run --no-sync`，禁止在正式进程启动时自动解析或同步环境；依赖变更须在启动前单独完成并核验，不能让并行运行争用同一虚拟环境。
- 修改的 Shell 脚本只在交付、审查或提交前集中一次 `bash -n`；`0644` 包装器用 `bash` 启动。
