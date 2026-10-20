# 第四章架构机制文献调研：任务计划

**日期**：2026-10-20
**触发**：用户指示——架构机制调研**不限于 Mamba/RWKV**，要覆盖"很多其他模型的机制"；整理思路时**必须有文献引用**。
**上游状态**：训练过程线已整体关闭（轨迹诊断否决效率轴；LSUV −2.4581 pp 否决效果臂；提交 `e9080e4d`）。架构轴（表示层）是剩余唯一活动方向。

## 一、调研问题

在 LAMDA 的 4561 维稀疏二值特征、年度到达、MLP 基座（2.69M 参数）设定下，**哪些模型架构机制**有文献支撑、且机制理由能挂在本课题实测病灶上？

实测病灶（全部零训练制品）：特征极稀疏（激活率 0.27–1.58%）、活坐标跨年翻转（Jaccard 低至 0.42）、末期年度正例稀缺（2023 14.5%→2024 1.6%→2025 0.05%）、单位方差初始化反而更差（LSUV −2.46 pp）。

## 二、家族清单（用户裁决：不限 Mamba/RWKV）

| # | 家族 | 代表机制 | 判定用途 |
|---|---|---|---|
| A | 表格 Transformer | FT-Transformer、TabTransformer、SAINT | 特征交互建模的对照上限 |
| B | 表格专用正则/集成 | TabM、ResNet-tabular、 MixUp 类 | MLP 基座的低成本强化 |
| C | 检索/近邻混合 | TabR（kNN+DL） | 末期年度少样本的机制来源 |
| D | 特征嵌入/交互（推荐系统系） | PNN、DeepFM、DCN、AutoInt | 稀疏二值共现结构的显式建模 |
| E | 序列模型强加于特征集 | Mamba/SSM、RWKV、"tabular-as-sequence" | 用户点名；须查是否真有此线文献 |
| F | 可微树/混合 | NODE、TabNet | 与 GBDT 基线的关系 |
| G | 恶意软件域骨干 | MalBERT、DREBIN 系、深度 Malware 骨干 | 域内先例与占位（只登记不排序） |
| H | 理论/实证基线研究 | Why do tree models beat DL on tabular、TabReD | 解释"该格式利好谁" |

## 三、工具清单（强制，按序）

1. **本地混合索引**：`uv run --project scripts/literature_search --locked python -m scripts.literature_search status --json` → `query ... --scope paper --mode hybrid --json`（索引缺失时按 README 构建，或降级 lexical 并披露）。
2. **Zotero 语义检索**（MCP `zotero_semantic_search`）＋ `zotero_search_items`。
3. **scholar CLI**（`mcpmarket-me:google-scholar` 技能；已认证；单主题 ≤3 条命令防限流；返回前须 `--bibtex`）。
4. **WebSearch**（备用；限流时不用）。
5. 命中后按 `raw/AGENTS.md`/`wiki/AGENTS.md` 入库：未取得全文一律标「在线摘要/仅题录」，不得支撑正文论断。

## 四、交付

1. `notes.md`：逐条登记查询式、来源、证据等级、纳入/排除理由、与候选关系。
2. `thesis/methods/第四章-架构机制文献调研.md`：按家族组织的调研报告，**每条主张带引用**（BibTeX 元数据），末尾给「可进入材料性探针的机制清单」与建议探针成本。

## 五、停止条件

- 每家族 ≥2 个可用锚点或明确「未检得」记录即可收口；
- scholar/WebSearch 连续 3 次失败则该家族记「外部检索阻塞」，只保留 Zotero/本地结果；
- 总时长 ≤2 小时。
