# RWKV 恢复协议分流实施计划

> **代理执行要求：**本任务为规则与文档修改，不改生产代码，不适用测试驱动开发。

## 目标

为 RWKV 专属会话建立独立、精简、可验证的上下文恢复路径，同时保持 PINN/R2 默认恢复路径不变。

## 文件职责

- 修改 `AGENTS.md`：先判定路线，再选择唯一恢复协议。
- 修改 `.Codex/docs/RWKV/AGENTS.md`：规定 RWKV 会话的先读路径和写回边界。
- 创建 `.Codex/docs/RWKV/RWKV路线总控.md`：保存 RWKV 当前状态与唯一下一顺序。
- 创建 `.Codex/docs/RWKV/2026-08-06-RWKV恢复协议分流-notes.md`：记录修改依据和验证结果。

## 任务

- [x] 固定路线分流设计与安全边界。
- [x] 修改项目根恢复协议。
- [x] 修改 RWKV 局部恢复协议。
- [x] 创建 RWKV 路线总控。
- [x] 核验默认读取路径、禁读边界、路线哨兵和文档链接。
- [x] 写回验证结果并将计划标记完成。

## 验收命令

```bash
rg 'RESEARCH_ROUTE=RWKV|RWKV 路线|PINN/R2|默认不读取' AGENTS.md .Codex/docs/RWKV/AGENTS.md .Codex/docs/RWKV/RWKV路线总控.md --line-number --context 1
rg 'output/开题改进交接文档.md|output/第一创新点实验总控.md' .Codex/docs/RWKV/AGENTS.md .Codex/docs/RWKV/RWKV路线总控.md --line-number
rg '[[:blank:]]+$' AGENTS.md .Codex/docs/RWKV/AGENTS.md .Codex/docs/RWKV/RWKV路线总控.md
```

第二条命令只允许命中“默认不读取、跨路线时按需读取”的否定性边界，不得命中默认先读清单。

## 状态

**已完成**：RWKV 与 PINN/R2 恢复路径已经互斥分流；三份验收检查均通过。
