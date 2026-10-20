---
name: kb-related-retrieval
description: 检索本机知识库（~/Dev/Research，Obsidian vault）并发现与结果关联的文档，返回 Obsidian 跳转链接。当用户问"知识库里有没有 X 的资料"、"X 相关的文档有哪些"、"查一下知识库 X 及它的关联主题"、或需要基于既有知识沉淀检索并扩展关联文档时使用，即使他们没有明确说"检索"。涉及 bban-api/manba-bi/te 等跨项目工程知识时尤其适用。
---

# 知识库关联检索

## 目标

本机知识库 `~/Dev/Research`（Obsidian vault）沉淀了跨项目可复用工程知识（`bban-api/` BBAN 探测、`manba-bi/` MCDN 运维、`te/` 监控告警），文档间用 wikilink（`[[...]]`）互相关联。本 skill 让 Claude 用 MCP 工具检索知识库，并利用 wikilink 关联发现"与结果相关的其他文档"，最终给用户可点击的 Obsidian 跳转链接——解决"检索到一个文档后，怎么找到跟它关联的其他文档"。

## 何时用

- 用户问"知识库里有没有/查一下 X 的文档"、"X 相关资料"
- 用户想了解某主题的关联知识："X 还涉及哪些方面"、"和 X 相关的有哪些"
- 新会话需要基于既有沉淀快速定位相关文档，避免重复调研
- 跨项目复用知识（BBAN/MCDN/te 等）的检索场景

## 前置：MCP 工具

依赖 `research-knowledge` MCP 服务（.knowledge-mcp）的工具：

| 工具 | 用途 |
| --- | --- |
| `knowledge_search(query, mode="lexical")` | 检索（lexical 是生产默认）|
| `knowledge_get(id)` | 按索引编号读条目全文 |
| `knowledge_related(id, depth=1)` | wikilink 关联：出链+入链；depth>=2 图扩展 |
| `knowledge_cli_search(query, vault)` | Obsidian CLI 全文检索兜底 |

若工具报错/未注册（MCP 服务是常驻进程，代码更新后需重启 Claude Code 会话生效），提示用户重启会话；可降级用 `obsidian search vault=... query=...` CLI 或直接读 `~/Dev/Research` 下文件。

## 步骤

1. **检索**：`knowledge_search(query, mode="lexical")`。
   结果含 `id/path/title/score/snippet/related_out/related_in/obsidian_uri`。
   **scope 处理**：默认 `scope="auto"`。若返回警告"未识别当前项目，已仅检索通用知识"（落在 common 域，搜不到项目库），显式传目标库 scope：`scope="bban-api"`（ba/et 项目）、`"manba-bi"`（go-op）、`"te"`（te），或 `"all"` 全库。
   **中文检索技巧**（FTS5 trigram 对 2 字符中文词匹配弱、多词 AND 组合易空）：拆成单关键词分别查（"泰山"单独可命中）、附英文同义词（泰山→taishan、探测→probe、节点→node、结果→result）、仍不行用降级（rg 文件系统 / obsidian CLI）。
   **中文语义检索（效果最佳）**：中文多词查询用 `mode="semantic"` 命中质量显著高于 lexical（实测 "mcdn 探测 泰山 存储 节点状态" score 0.88-0.90，lexical 同查询为空）。首次调用加载 E5 模型约 27s；semantic 是实验模式（未过负例拒绝门槛），用户明确要求或中文查询效果差时优先使用。
2. **关联发现**：对 top 2-3 个结果调 `knowledge_related(id)`，获取
   - `related_out`（出链：该文档引用谁）
   - `related_in`（入链：谁引用该文档）
   需要更广视野时用 `knowledge_related(id, depth=2)` 做 BFS 图扩展，得到 `related_graph`。
   **降级**（若 `knowledge_related` 不可用，如 MCP 未重启）：用 `knowledge_get(id)` 读条目全文，提取其中的 `[[链接]]` 作出链；再用 `knowledge_search("<该文档标题>")` 反查哪些文档引用了它（入链）。
3. **CLI 兜底**（可选）：lexical 结果不足或为空时，`knowledge_cli_search(query)` 调 Obsidian CLI 全文检索补充。
4. **汇总输出**（见下节格式）。

## 输出格式

ALWAYS 使用以下结构：

```
## 检索结果
- <title>（<path>）
  - 摘要：<snippet>
  - 跳转：<obsidian_uri>

## 关联文档
- 出链（它引用谁）：<path> ×N
- 入链（谁引用它）：<path> ×N
- 图扩展（depth=2，可选）：<path> ×N

## 图谱提示
提醒用户可在 Obsidian Graph View 查看可视化图谱（打开 ~/Dev/Research vault，点左侧图谱图标）。
```

关联文档优先展示 Knowledge/ 下的条目（有沉淀价值），Hub/Index/registry 等导航文件降权或合并说明。

## 边界与降级

- **检索结果空**：区分"知识库确实没有"与"检索词不匹配"——先换同义词/近义词重试，再用 CLI 兜底，最后才下结论"没有"。
- **vault 名**：默认 `Research`，可用环境变量 `OBSIDIAN_VAULT_NAME` 覆盖；`knowledge_cli_search` 的 vault 参数必须匹配 Obsidian 实际 vault 名（否则 CLI 会落到默认 vault）。
- **MCP 不可用**：提示重启会话；降级用 `obsidian search` CLI 或直接读文件。
- **避免重复调研**：命中已有 Knowledge 条目时，直接引用其结论，不要重新研究；用 `knowledge_get` 读全文确认是否覆盖用户问题。

## 参考

- 知识库入口：`~/Dev/Research/README.md`（总索引），各库 `00-Hub.md` 是入口
- 图谱 canvas：`bban-api/Maps/bban-api-knowledge.canvas`（Obsidian 打开）
- 检索评测契约：`~/Dev/Research/Knowledge/local-knowledge-retrieval-evaluation.md`
