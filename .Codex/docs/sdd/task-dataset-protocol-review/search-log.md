# 数据集与统一基线协议检索日志

## 检索日期与范围

- 检索日期：2026-07-24。
- 时间范围：优先 2020 至 2026；开放集入侵识别的奠基论文放宽至 2017。
- 数据边界：GeNIS 2025、TQH-C2 2026 与 ns-3；不引入第四个实验数据集。
- 全文门槛：核心文献必须有可读 PDF 或官方数据说明，并能定位到页码、章节、表格、公式或稳定行号。

## 检索来源

| 来源                                 | 用途                                       | 结果                                                                                             |
| ------------------------------------ | ------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| 本地 `raw/papers/` 与 `wiki/papers/` | 发现已有全文、既有笔记和重复文件           | 复用 6 篇已有全文与 6 篇既有笔记；识别 GeNIS 一个损坏重复件                                      |
| 本地 Zotero 9.0.6                    | 按题名、DOI 与作者去重并导入核心记录       | 复用 5 条既有记录；向 `attack-detection` 导入 8 条候选，随后将 YaTC 与一条延迟检出的既有记录合并 |
| 出版社与会议官方页面                 | 核验题名、作者、出版年、卷期页码与 DOI     | 核验 IEEE、ACM、Elsevier、MDPI、AAAI 与 USENIX 元数据                                            |
| arXiv 官方页面与 PDF                 | 获取作者公开全文                           | Sweet Danger 的机构下载返回 403 后，改用 arXiv:2507.16438 官方全文                               |
| Zenodo 与本地官方 README             | 核验 TQH-C2 版本、文件结构、标签与采集单元 | 核验 DOI 10.5281/zenodo.21330095；发现 README 顶部为 1.0.1、引用块仍写 1.0.0                     |

## 概念组与执行过的检索式

| 编号 | 检索式                                                                                | 目标                               | 命中后处理                                                          |
| ---- | ------------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------- |
| Q01  | `network intrusion detection dataset split leakage session flow capture random split` | 查找流级、会话级与采集级泄漏证据   | 纳入 Sweet Danger、Bad Design Smells 与 FlowPic                     |
| Q02  | `encrypted traffic classification per-flow per-packet split fair evaluation`          | 查找加密流量公平切分与输入比较     | 纳入 Sweet Danger；复核 ET-BERT、YaTC                               |
| Q03  | `PCAP preprocessing burst packet sequence bidirectional flow`                         | 查找 PCAP 到流、突发和序列的处理   | 纳入 FlowPic、ET-BERT、YaTC                                         |
| Q04  | `open set intrusion recognition unknown attack train test`                            | 查找未知攻击留出协议               | 纳入 Cruz 等人的开放集入侵识别论文                                  |
| Q05  | `cross evaluation cross dataset generalization network intrusion detection`           | 查找跨来源字段交集与域外评价       | 纳入 XeNIDS 与 Cantone 等人的跨数据集研究                           |
| Q06  | `physics-informed neural network network traffic simulation real testbed queue`       | 查找仿真监督、残差与真实验证分工   | 纳入交通状态 PINN 与 PRED                                           |
| Q07  | `GeNIS 2025 preprocessed train holdout stratification`                                | 核验 GeNIS 官方随机分层文件        | 纳入 GeNIS 数据论文，并标记其随机行级划分不能直接作为本项目最终协议 |
| Q08  | `TQH-C2 encrypted command control dataset profile interval jitter`                    | 核验 TQH-C2 的自然分组与跨条件用途 | 纳入官方 README 作为数据契约，不把它计入 12 篇论文核心全文          |

## 身份核验与去重

| 记录                         | 核验结果                                                                                                                                                                                               |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| GeNIS                        | 论文 DOI `10.1016/j.dib.2025.111487`；数据 DOI `10.5281/zenodo.14919237`。`raw/papers/1-s2.0-S2352340925002197-main.pdf` 为损坏重复件，审查使用可读的 `(2)` 文件；未删除任何原件。                     |
| TQH-C2                       | 数据 DOI `10.5281/zenodo.21330095`。本地 README 为 1.0.1，引用块仍为 1.0.0；协议固定实际使用版本与归档哈希，不只记录概念 DOI。                                                                         |
| Sweet Danger                 | ACM DOI `10.1145/3718958.3750498`，作者公开版为 arXiv:2507.16438；两者视为同一作品。                                                                                                                   |
| Cross-dataset generalization | 预印本题名以 `On the` 开头；正式 IEEE Access 题名为 `Machine Learning in Network Intrusion Detection: A Cross-Dataset Generalization Study`，DOI `10.1109/ACCESS.2024.3472907`；参考文献采用正式题名。 |
| XeNIDS                       | 正式题名、卷期页码与 DOI `10.1109/TNSM.2022.3157344` 经出版元数据核验。                                                                                                                                |
| PRED                         | USENIX NSDI 2025 官方页面可核验，无需补造 DOI。                                                                                                                                                        |

## 全文获取记录

| 文件                                                      | 来源类型         | 页数 | SHA-256                                                            |
| --------------------------------------------------------- | ---------------- | ---: | ------------------------------------------------------------------ |
| `2017-Cruz-Open-Set-Intrusion-Recognition.pdf`            | arXiv 官方全文   |    6 | `8c8db8cef37b6b110b56aa0e39e4c86046e948656d720dcd929f65a2a1d4d292` |
| `2021-Shapira-FlowPic.pdf`                                | 作者公开全文     |   15 | `718695fb789164ffc6e37afa1bb01e9b7bd6d7f05f5800c6a15361ead8a4c644` |
| `2022-Apruzzese-XeNIDS-Cross-Evaluation.pdf`              | 作者机构公开全文 |   18 | `9f722b5b73eaffd1ec261851b0dc52a7023724a37cc40caa26fe497f5880f4ff` |
| `2024-Cantone-Cross-Dataset-Generalization-NIDS.pdf`      | 作者公开全文     |   23 | `0c367d36e40744c15aa63c5bbb3b56f46afae34342a8d8ebbf129d735cfcce37` |
| `2024-Flood-Bad-Design-Smells-NIDS-Datasets.pdf`          | 作者公开全文     |   18 | `0c6d7d8ec2651fee77c23136801813aa5c95c6d967f15c5f7cfde19a3b575f28` |
| `2025-Zhao-Sweet-Danger-Encrypted-Traffic-Evaluation.pdf` | arXiv 官方全文   |   15 | `c377e34b718ee04c35a2350c5155d546e82aa0f310f84739a55b379d171ce26e` |

上述 6 份新增 PDF 共 6,919,345 字节，约 6.60 MiB，均通过 `pdfinfo` 与逐页文本提取检查。其余 6 篇核心全文复用仓库已有原件。

## Zotero 入库与去重审计

- 目标分类为 `attack-detection`，分类键为 `riqcxzm4`。
- GeNIS、HIKARI-2021、ET-BERT、Traffic PINN 与 PRED 复用既有记录，不重复导入。
- Sweet Danger、Bad Design Smells、FlowPic、YaTC、开放集入侵识别、XeNIDS、跨数据集泛化研究与 TQH-C2 共 8 条候选已导入目标分类。
- 导入后复查发现 YaTC 与既有记录重复；已在 Zotero 的“重复条目”视图中合并，并选择元数据完整的会议论文版本作为主记录。
- 合并后按完整题名检索只返回 1 条记录，键为 `7B32DSZS`，类型为 `conferencePaper`，DOI 为 `10.1609/aaai.v37i4.25674`，卷期页码为 37(4):5420–5427。
- 该次合并使 8 次导入形成 7 条净新增记录，并补全 1 条既有 YaTC 记录；没有删除附件或笔记。

## 检索收敛

- 候选材料共 16 项：12 篇核心论文、1 份核心数据契约、3 篇补充材料。
- 最终核心论文 12 篇，覆盖分组泄漏、PCAP 表征、开放集、跨数据集及 PINN/仿真与真实验证分工。
- 新增候选不再改变 `sample_id`、组级切分、字段预算或域外测试的主要裁决，达到主题饱和。
- 12 篇核心论文与 TQH-C2 官方说明均有全文或官方材料，无需生成 `missing-fulltext.md`。
