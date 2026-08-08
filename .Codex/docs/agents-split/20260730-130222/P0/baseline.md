# P0 AGENTS.md 活动链基线

## 运行环境

- 运行标识：`20260730-130222`。
- 日期：2026-07-30。
- Codex：`codex-cli 0.144.5`。
- Git 提交：`acdf98ba5cc776f7c19495fc53b1164e916eb33c`。
- 仓库：`/Users/bilibili/personal/note`。
- 信任状态：`/Users/bilibili/.codex/config.toml` 将本仓库标为 `trusted`；只读子进程也实际加载了项目规则。
- 用户级 `~/.codex/AGENTS.md`：10,385 字节。该文件单独注入，下面的 32 KiB 风险表只核算项目规则链。
- 当前配置未设置持久化 `project_doc_max_bytes`，按默认 32,768 字节验收。

## 实施前文件

| 文件                                             | 字节数 | SHA-256                                                            |
| ------------------------------------------------ | -----: | ------------------------------------------------------------------ |
| `AGENTS.md`                                      |  7,947 | `7d066755da5676a7968b3276efb522fd5b574520643e7dd5384f596b5153e4c2` |
| `thesis/AGENTS.md`                               |  6,202 | `673e6c3b2ac8e35d88f6029de00f6bce630bc4aa76a4a3186782d7dfc1840e23` |
| `thesis/experiments/llm_probe/AGENTS.md`         | 25,589 | `ead7c2027693e8a66aaf9d1c4fa8ed26bdaafcb3ce0686907e3c76cf17d99ce3` |
| `thesis/experiments/llm_probe/scripts/AGENTS.md` | 待创建 | 不适用                                                             |

快照位于同目录的 `AGENTS.root.md`、`AGENTS.thesis.md` 和 `AGENTS.llm-probe.md`。三份快照已再次计算 SHA-256，与上表完全一致。

## 理论活动链

| 启动工作目录                           | 自动发现的项目规则文件                                        | 项目合计 | 相对 32,768 字节 |
| -------------------------------------- | ------------------------------------------------------------- | -------: | ---------------: |
| 仓库根                                 | 根 `AGENTS.md`                                                |    7,947 |        余 24,821 |
| `thesis/experiments/llm_probe`         | 根、`thesis/AGENTS.md`、`llm_probe/AGENTS.md`                 |   39,738 |         超 6,970 |
| `thesis/experiments/llm_probe/scripts` | 根、`thesis/AGENTS.md`、`llm_probe/AGENTS.md`；局部文件不存在 |   39,738 |         超 6,970 |

从仓库根启动只会自动发现根规则。根规则要求任务涉及 `llm_probe` 时主动完整读取 `thesis/AGENTS.md` 和 `llm_probe/AGENTS.md`，但文件不会因为随后编辑深层路径而自动注入。P1 必须保留到 `scripts/AGENTS.md` 的人工路由，不能复制脚本细则到上层。

## 实际注入验证

使用 Codex 自带的只读调试子进程，不允许模型搜索文件：

```bash
codex --cd <目录> debug prompt-input "只报告启动时注入的 AGENTS.md 规则文件和规则加载哨兵，不得调用工具，不得搜索文件。"
```

中间诊断只对 `llm_probe` 和 `scripts` 临时增加：

```bash
--config project_doc_max_bytes=65536
```

结果如下：

| 启动工作目录与预算       | 可见哨兵                                                                | 完整性                                                                     |
| ------------------------ | ----------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 根，默认                 | `NOTE_ROOT_20260724`                                                    | 根规则完整，未发现深层规则                                                 |
| `llm_probe`，默认        | `NOTE_ROOT_20260724`、`NOTE_THESIS_20260724`、`NOTE_LLM_PROBE_20260724` | 项目文件内容达到默认预算后截断，末尾停在“测试 Shel”，不是完整父规则        |
| `scripts`，默认，P1 前   | 同上                                                                    | 局部文件不存在，活动链与 `llm_probe` 相同，并发生相同截断                  |
| `llm_probe`，65,536      | 同上                                                                    | 完整看到父规则最后一条生成式评测规则，证明默认结果是预算截断而非路径未发现 |
| `scripts`，65,536，P1 前 | 同上                                                                    | 完整看到三层规则；没有伪造 `scripts` 哨兵                                  |

调试输出中项目文档正文在默认 `llm_probe` 会话占 32,772 字节，其中 4 字节是组合包装开销，对应文件预算正好耗尽 32,768 字节；65,536 诊断输出为 39,741 字节，其中 3 字节是组合开销，对应三个项目文件 39,738 字节。

## 既有工作树差异

实施前 `llm_probe/AGENTS.md` 相对 `HEAD` 有 19 条新增规则。其差异保存在 `pre-existing-llm-probe.diff`。调研文档记录的 25,589 字节与当前文件一致，因此这些规则属于已识别基线，不在本任务中回滚或丢弃。

其他实验代码、配置、测试和两份 `output/` 恢复文档也有既有改动。本任务不修改它们。
