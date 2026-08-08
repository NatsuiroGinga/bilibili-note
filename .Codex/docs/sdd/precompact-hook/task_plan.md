# PreCompact 强制恢复快照 Hook 实施计划

## 目标

在 Codex 上下文压缩前，以确定性、原子方式更新两份强制恢复文档中的唯一自动快照区块，不修改人工正文。

## 阶段

- [x] 阶段一：读取强制恢复文档、Hook 开发规范并核验 Codex 0.144.5。
- [x] 阶段二：从 OpenAI 官方同版本源码确认 Hook 发现、输入输出、信任与超时契约。
- [x] 阶段三：实现项目级 Hook 配置、活动计划配置和标准库脚本。
- [x] 阶段四：执行临时副本、缺失来源、幂等、真实文档与语法检查。
- [x] 阶段五：编写使用说明并完成变更自检。

## 固定边界

- 不调用 `codex exec`，不访问网络、SSH、GPU 服务器或凭据。
- 单次运行超时不超过 10 秒。
- 只修改 `<!-- PRECOMPACT_SNAPSHOT_START -->` 与 `<!-- PRECOMPACT_SNAPSHOT_END -->` 之间的内容。
- 任一来源缺失或写入失败时保留人工正文和既有文档，输出合法 JSON 告警。
- 当前活动计划默认为 `.Codex/docs/sdd/task-17-observability/task_plan.md`。

## 已确认决策

- 以 OpenAI Codex `rust-v0.144.5` 官方源码为契约来源，不采用技能中 Claude 专用变量。
- 使用 Python 标准库实现路径校验、状态提取和同目录临时文件原子替换。

## 错误记录

- 沙箱内首次创建 `.Codex/docs/sdd/precompact-hook` 被拒绝；经受控权限批准后仅创建该任务目录成功。
- 首次 `py_compile` 尝试在受限的 `.codex/hooks/__pycache__` 写入字节码而失败；验证命令改为把 `PYTHONPYCACHEPREFIX` 指向 `/tmp`，不修改生产脚本。
- 隐藏目录路径 `.codex/...` 不能作为 `python -m unittest` 的模块名；根因是前导点被解析为空模块段，改为直接运行测试文件。
- 本机 PATH 没有直接暴露 Black 和 Ruff；使用 `uv` 已缓存的工具绝对路径完成格式化与静态检查。
- 使用真实用户 `CODEX_HOME` 启动独立 App Server 时，被既有 SQLite 状态库完整性错误阻塞；未修改或移动用户状态库，改用隔离的 `/tmp/codex-hook-home` 仅执行官方 `hooks/list` 只读验证。

## 当前状态

全部实现与验证完成；等待新会话通过 `/hooks` 人工批准项目 Hook。
