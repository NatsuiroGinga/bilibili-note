# Prettier 禁用 Hook 验收记录

日期：2026-07-31

## 结论

项目级命令前置 Hook 已加入职责单一的 Prettier 禁用守卫。它只恢复这一条机械门禁，不恢复此前为下载和远程工作暂停的其他项目执行门禁。

Hook 能拒绝以下显式调用：

- 直接执行 `prettier` 或 `node_modules/.bin/prettier`。
- 通过 `npx`、`npm exec`、`pnpm`、`yarn`、`bunx` 和 `corepack` 调用。
- 通过常见 `bash -lc`、`sh -c`、`zsh -c`、`eval` 或管道包装调用。
- 直接使用 Node.js 执行 `prettier/bin/prettier` 入口。

Hook 不会因为 `rg` 搜索词、`cat` 文件名、`printf` 文本、安装或查询包信息等普通提及而拒绝命令。

## 修改文件

- `.Codex/hooks.json`：注册项目 `PreToolUse`，只调用 Prettier 守卫；保留原有 `PreCompact`。
- `.Codex/hooks/prettier_guard.py`：新增确定性命令识别和结构化拒绝输出。
- `.Codex/hooks/tests/test_prettier_guard.py`：新增直接调用、包装调用、嵌套调用和误拦边界测试。
- `.Codex/hooks/tests/test_hooks_integration.py`：把三目录集成样例改为当前 Prettier 门禁合同。
- `thesis/experiments/llm_probe/AGENTS.md`：删除交付阶段可运行 Prettier 的例外，改为任何阶段均禁止。
- `.Codex/docs/2026-07-31-Prettier禁用Hook实施计划.md`：记录范围、阶段和验收合同。

实验 `AGENTS.md` 同时存在其他任务的未提交改动。本任务只修改其中一条 Prettier 规则，没有覆盖或回滚其他改动。

## 验证

命令识别测试：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -v -s .Codex/hooks/tests -p 'test_prettier_guard.py'
Ran 3 tests in 0.002s
OK
```

三目录配置集成测试：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -v -s .Codex/hooks/tests -p 'test_hooks_integration.py'
Ran 2 tests in 0.928s
OK
```

集成测试分别从仓库根、`thesis/experiments/llm_probe` 和其 `scripts` 子目录运行配置中的真实 Hook 命令，确认普通文本提及无输出放行，`npx prettier` 返回唯一受支持的 `PreToolUse` 拒绝对象。

`jq empty .Codex/hooks.json` 退出码为零。未运行 Prettier、其他格式化工具、抽象语法树解析或实验测试。

## 生效边界

- 当前会话不会热加载修改后的 Hook 定义，因此本会话剩余工具调用不能依赖新守卫。
- 新会话启动后需要在 `/hooks` 审查并信任新的项目 Hook 哈希；信任后才会在真实工具执行前生效。
- 用户级 `PreToolUse` 当前仍为禁用状态，本实现不修改用户级配置，也不依赖它。
- 守卫检查显式命令位置和常见包装器。任意自定义脚本别名、包脚本别名或刻意混淆命令不在当前无误拦合同内，仍由常驻规则禁止。

## 未修改内容

- 已暂停的远程、同步、下载、测试和子代理命名门禁。
- 论文正文、实验源码、配置、数据、运行制品和服务器状态。
- 用户级 Hook 配置、Hook 信任状态和 Git 历史。
