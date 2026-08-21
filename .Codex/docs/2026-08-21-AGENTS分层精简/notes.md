# AGENTS 分层精简证据笔记

## 官方 OpenAI 文档

### Custom instructions with AGENTS.md

- OpenAI 开发者文档链接：https://developers.openai.com/codex/guides/agents-md
- 当前规范页链接：https://learn.chatgpt.com/docs/agent-configuration/agents-md
- `openaiDeveloperDocs` 已从 OpenAI 开发者文档链接取得完整正文；命令行直连被站点拒绝不影响官方文档工具取证。
- 每次运行或终端会话开始时构建一次指令链，运行中不动态重建。
- 全局层先检查 `AGENTS.override.md`，否则读取 `AGENTS.md`，只取首个非空文件。
- 项目层从项目根走到当前目录；每层依次检查 `AGENTS.override.md`、`AGENTS.md`、配置的回退名，每层最多纳入一个文件。
- 从根到近层拼接，近层因后出现而覆盖前层。
- 空文件跳过；主页面称组合大小达到 `project_doc_max_bytes` 后停止，默认 `32 KiB`。
- 官方建议把专用规则放在最接近适用代码的目录，并用新会话验证加载来源。

### Project instructions discovery

- 链接：https://learn.chatgpt.com/docs/config-file/config-advanced#project-instructions-discovery
- `project_doc_max_bytes` 控制读取量，`project_doc_fallback_filenames` 增加每层回退文件名。
- 该页称上限是“从每个 `AGENTS.md` 读取多少”，与主页面的“组合大小”表述不完全一致。

## 本机状态

- `codex-cli 0.148.0`。
- `~/.codex/config.toml` 未显式设置 `project_doc_max_bytes` 或 `project_doc_fallback_filenames`。
- 采用默认且保守的组合 `32,768` 字节上限验收。
- 共享暂存区已有另一任务四个文件，本任务不得清空、覆盖或夹带提交。

## 待盘点

- 已用 `fd` 找到 10 个活动 `AGENTS.md`，未发现 `AGENTS.override.md`。
- 修改前总字节 `87,446`；根文件 `31,193` 字节。
- 修改前组合字节：根 `31,193`；`raw` `36,729`；`wiki` `33,776`；`output` `33,158`；论文章节 `41,888`；RWKV 文档 `46,588`；`llm_probe/scripts` `57,133`。除根外所列路径均超过保守组合上限。
- 重复率采用“去空白后跨文件重复的 12 字符片段数 / 全部文件 12 字符片段数”，修改前为 `6.11%`。该指标只衡量字面重复；概念重复另由规则审计表裁决。

## 逐文件规则审计

| 文件 | 当前规则域 | 重复或冲突 | 处理决定 | 不可删依据 |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | 全仓路由、恢复、证据、技能、图件、检索、工程、子代理 | 混入章节图件、实验细节、检索长说明、事故复述；根自身逼近上限 | 只保留全仓沟通工具、安全、研究证据、恢复、通用执行、子代理分档；专用规则下沉 | 用户本轮明确要求；研究诚信、凭据、恢复和 Git 安全是全仓边界 |
| `.Codex/docs/AGENTS.md` | 过程文档职责与记录 | 重复根级凭据、恢复说明，含 PINN 专属台账 | 只保留过程文档落点、计划/报告最小字段、历史归档边界 | 该目录承担可恢复记录和审计证据 |
| `.Codex/docs/RWKV/AGENTS.md` | RWKV 恢复、当前门禁、Rust、源码、同步 | 大量候选、比例、数据集和事故瞬时状态；恢复路由与根重复 | 只保留 RWKV 唯一恢复链、事实源优先级、章节写回、路线专属 Rust/源码原则；当前事实链接总控/恢复卡 | RWKV 是默认论文主线，必须保持唯一恢复入口 |
| `output/AGENTS.md` | 高层交付与旧 PINN/R2 双总控 | 与当前 RWKV 默认路线冲突 | 改为高层交付通则；明确 PINN/R2 文档只在显式历史路线下读取和更新 | 防止把旧摘要当当前事实 |
| `raw/AGENTS.md` | 原件、下载、数据集来源、PDF | 与根证据纪律、wiki 笔记要求重复 | 保留原件不可变、合法获取、全文入库、付费墙阻塞、来源与校验和；跨层事项改链接 | 原件真实性和不可变性是该层核心职责 |
| `wiki/AGENTS.md` | 结构化知识与 Obsidian | 与根全文证据边界重复 | 保留模式、元数据、双链、论文原结论与本课题推论分离 | 知识层结构和引用可追溯性不可由根替代 |
| `thesis/AGENTS.md` | 章节路线、PINN 理论、数据、图件 | 固定 PINN 与根默认 RWKV 冲突；数据集、字段预算为瞬时合同 | 改为论文边界、正文证据、图件完整合同和实验目录衔接；路线和数据事实链接当前总控 | 论文公开表述和图件质量是 `thesis/` 专属规则 |
| `thesis/chapters/AGENTS.md` | 正文章节、W0-W5、自审 | 图件规格与根冲突（`155 mm/600 dpi` 对 `165 mm/≥300 ppi`）；重复证据链 | 保留正式章节唯一目录、W0-W5、写作工具链与六项自审；图件只引用父级合同 | 章节定稿门禁只适用于正文目录 |
| `thesis/experiments/llm_probe/AGENTS.md` | 实验、远程、数据、PyTorch、运行、日志 | 与根凭据/第三方接口重复；含长事故复述和当前阈值细节 | 保留实验有效性、资源安全、PyTorch、最终测试、真实运行、日志与结果写回；事故改链接故障手册 | 用户明确要求保留实验有效性和 PyTorch 通用规则 |
| `thesis/experiments/llm_probe/scripts/AGENTS.md` | 远程脚本 | 与实验层同步规则少量重复 | 只保留脚本特有合同、`PIPESTATUS`、`uv`、`bash -n` 和禁止删除 | 远程脚本退出码与日志语义需要近层硬约束 |

## 关键冲突

- 当前主线：根级默认 RWKV，但 `thesis/AGENTS.md` 仍写第三章固定 PINN；必须以当前根恢复协议为准，论文层不再冻结历史路线。
- `output/AGENTS.md` 把 PINN/R2 两份文档称为默认恢复文档，与根级“仅用户明确指定才读取”冲突；改为历史路线专用。
- 图件规格：`thesis/chapters/AGENTS.md` 的 `155 mm/600 dpi` 与根级 `165 mm/≥300 ppi，推荐400 ppi` 冲突；统一为实测合同并放到 `thesis/AGENTS.md`。
- 调试测试：全局调试纪律要求回归测试，但实验工程禁止人工夹具和独立冒烟实验；根级明确由近层实验有效性规则限定验证形式。

## 来源与不可删规则组

- 官方 Codex 发现语义：OpenAI 官方文档。
- 全局中文、`rg`/`fd`、`.Codex/docs/` 落点：用户当轮与仓库上层强制指令。
- 研究证据、最终测试隔离、魔法数字、恢复与凭据：仓库长期规则和用户本轮保留清单。
- Git 快照与不触碰其他代理改动：仓库执行纪律和用户本轮文件所有权要求。
- 子代理模型分档：仓库长期成本与能力治理规则，用户本轮明确要求保留。
- PyTorch、远程、日志和资源规则：实验工程真实故障和可复现性需求；历史事故细节迁回既有故障手册，不常驻加载。

## 修改后统计

- 10 个活动 `AGENTS.md` 总字节：`41,712`，比修改前减少 `45,734` 字节（`52.30%`）。
- 12 字符跨文件重复率：`4.30%`，比修改前 `6.11%` 下降 `1.81` 个百分点。
- 组合字节：根 `12,669`；`raw` `15,502`；`wiki` `14,372`；`output` `13,829`；论文章节 `19,661`；RWKV 文档 `18,102`；`llm_probe/scripts` `27,094`。全部低于 `32,768`。
- 自动加载链模拟按每层 `AGENTS.override.md`、`AGENTS.md` 顺序选首个非空文件；仓库未发现 override，七条代表路径均只选预期的 `AGENTS.md`。

## 后续精度入口

- 实现提交 `b74d858` 与文档提交 `d92296d` 已在当前 `HEAD` 历史中。
- B76 RTX 5090 新神经训练的工程默认 profile 为 `cuda-bf16-amp-fp32-sensitive-v1`；规则只登记入口、精度组成、例外收据、科学比较边界和活动旧运行禁切换。
- 共享配置为 `thesis/experiments/llm_probe/configs/neural-precision-profiles-v1.json`，运行工具为 `thesis/experiments/llm_probe/tools/neural_precision_runtime.py`，完整合同为 `.Codex/docs/RWKV/2026-08-21-RTX5090神经训练默认精度模式/实施报告.md`。
- 该 profile 是“工程默认、效果实验待证”，不得写成项目全模型精度最优。
