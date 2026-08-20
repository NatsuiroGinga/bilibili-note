# 全项目文档混合检索架构审计笔记

## 审计环境

- 工作树：`/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819`
- 日期：2026-08-20
- 模型：`gpt-5.6-sol`
- 推理强度：`high`
- 性质：只读审计；仅本目录为可写交付物。

## 证据日志

### 规则与技能

- 已读取根 `AGENTS.md` 与 `.Codex/docs/AGENTS.md`。
- 已读取 `planning-with-files` 与 `expression-skill`。
- `scripts/AGENTS.md` 不存在，未发现可加载的该层局部规则。

### 既有检索实现

- 当前配置只扫描 `wiki/papers/**/*.md`；新合同索引 495 个笔记视图、486 个论文身份、7307 个分块。
- 当前向量矩阵为 384 维；此前实测 6854 块精确点积热中位数约 0.74 毫秒，扩展前瓶颈不是向量扫描。
- 已具备 YAML 元数据、论文/笔记身份、稳定块键、嵌入合同哈希、原子替换、增量向量复用、论文级 RRF 和本地/在线分区。
- GitHub/HF 候选通道在审计期间插入实施，提交 `1c70406`；它们独立输出，不改变本地索引架构。

### 机械规模快照

命令均使用 `fd` 遍历，排除 `runs`、`.cache` 与 `.git`；历史归档只统计路径和字节，不读取正文。

| 根目录 | 全部文件 | Markdown | Markdown 字节 |
|---|---:|---:|---:|
| `.Codex/docs` | 1214 | 1051 | 10,276,322 |
| `wiki` | 587 | 587 | 3,036,721 |
| `thesis` | 861 | 32 | 252,321 |
| `output` | 17 | 17 | 326,217 |
| `Research` | 9 | 9 | 75,778 |
| `raw` | 357 | 6 | 73,565 |
| `.agents` | 4 | 4 | 7,600 |
| `scripts` | 22 | 1 | 8,619 |

- 上述范围共有 1701 个 Markdown；合计约 14.1 MB。
- `.Codex/docs` 非 archive/备份模式的活动 Markdown 1041 个，显式 `archive/` Markdown 22 个。
- `.Codex/docs/RWKV` 活动 Markdown 377 个；`archive` 与 `archive-pinn-ch3` 合计 4 个。
- `.Codex/docs` 中 `task_plan.md` 72 个、`notes.md` 66 个、文件名含“实施计划”65 个、含“报告”116 个。
- 恢复卡 4 个、总控类文件 5 个；当前一层入口含路线总控、第三章恢复卡、第四章恢复卡和旧兼容当前恢复卡。
- `wiki/papers` 有 503 个非 INDEX Markdown、17 个 `INDEX.md`；当前合法论文索引较少是因为非法 YAML、非论文对象和缺原件合同被排除。
- `thesis/chapters` 有 18 个 Markdown。
- 文档集合之外还有 Python 391、Shell 162、JSON 129、YAML 102、Rust 51、BibTeX 32 等文件；不应因扩展“全项目文档”默认把源码、配置和运行制品全部转成自然语言块。

### 最大文档与长文边界

- 最大活动 Markdown 包括 `output/Physics Manifold Constrained Representation.md` 124,197 字节、Dijk 协议审计 119,566 字节、LSPR24 数据合同 93,816 字节。
- 历史废稿与归档同样可能超过 60–95 KB，若不按状态过滤，会因重复术语和长文本块数压过当前真源。

### 权威性事实

- 文献事实：`raw/` 原件与 `wiki/papers` 全文核验笔记是事实源；在线题录只是候选。
- 路线边界：RWKV 路线总控是公共合同；第三/四章恢复卡分别是章节当前状态；旧兼容恢复卡不是默认入口。
- 运行事实：原始 JSON/NPZ/日志和运行制品优先于报告；实施计划是需求，不是结果；审查报告是验收，不是运行事实。
- 论文公开论断：`thesis/` 是发布表述层，但其证据仍应回指原件、知识笔记或实验制品。
- `.Codex/docs` 同时包含活动计划、过程笔记、报告、恢复卡、废稿和归档，不能只凭目录赋予统一权威等级。

### 敏感面与排除

- 默认排除环境文件、密钥、令牌、证书、登录命令、私有地址、缓存、模型权重、检查点、逐样本预测、最终测试标签、原始大数组和 `runs/` 全量正文。
- 实验检索只能读取明确 allowlist 的聚合收据、manifest、状态和指标 JSON；凭据值不得进入块文本、元数据、错误或哈希收据。
- `raw/` 二进制不进入文本索引；只索引已核验结构化笔记及可公开元数据。

### 可复核命令

```bash
fd -e md -t f . <root> --exclude runs --exclude .cache | wc -l
fd -e md -t f . <root> --exclude runs --exclude .cache -0 | xargs -0 wc -c
fd -t f '^task_plan\.md$' .Codex/docs | wc -l
fd -t f '恢复卡.*\.md$' .Codex/docs output | wc -l
fd -t f '^INDEX\.md$' wiki | wc -l
```

## 未关闭问题

- `Research/` 的长期定位尚未在根规则中定义为权威交付层，默认只能作为低权威研究过程材料。
- 真实用户 `real-user-query-v1` 的 8 条查询尚未独立标注 qrel，不能用于验收或调参。
- 全项目索引尚无真实构建与延迟收据；ANN 阈值只能设为测量触发条件，不能按文档数拍固定切换点。
