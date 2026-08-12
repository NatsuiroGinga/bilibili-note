---
title: "scilicet64/LSPR23 论文后续代码示例"
date: 2026-08-11
verified_on: 2026-08-11
tags:
  - 外部资源
  - 官方源码
  - LSPR23
  - 入侵检测
  - 类型/参考
related:
  - "[[Dijk-2024-LSPR23数据集与随机森林复现]]"
---

# scilicet64/LSPR23 论文后续代码示例

## 核验结论

- 仓库：<https://github.com/scilicet64/LSPR23>。
- GitHub 账号 `scilicet64` 的公开姓名为 Allard Dijk，与 Dijk 等 2024 的第一作者一致。
- README 明确称仓库提供 LSPR23 论文的代码示例，并链接论文和数据集。
- 2026-08-11 固定核验提交为 `496cc558713e8a5f46aa0b276b177a7d8835a217`，提交时间为 2024-10-14；首个提交为 `57374f6d5233cea9cebba5d12d9cbd50a7366036`。
- 仓库提交晚于论文上线时间，且 README 使用“代码示例”表述；现有证据不能证明它是论文表 8 的原始生成代码。
- 根目录没有 `LICENSE`，不能据此获得复制、修改或再分发许可。本课题只记录协议和哈希，不复制源码。

## 固定快照哈希

| 文件 | SHA256 |
| --- | --- |
| `README.md` | `20ace1d8e896018b0659a81e14d635c6621190aeb769053fb9ef688b9026cf3a` |
| `lspr23_code.py` | `171b3b3e73d6424c0aa636b51c68ef2d8172900980ae9d69cc0d566064f9a54d` |
| `requirements.txt` | `3df89fe9ebafee05c990ce868339ce8fca97ff5a641212c61ef4db2ae52e01c5` |
| `cite.bib` | `6c44eb308c2fc3379599d9b024b53e00a877929abc35717babf6cc8b04a7b17e` |

固定提交源码链接：<https://github.com/scilicet64/LSPR23/blob/496cc558713e8a5f46aa0b276b177a7d8835a217/lspr23_code.py>。

## 源码协议抽取

1. 默认只读取 CSV 的前 `80,000` 条流，不是随机抽样，也不是论文表 8 很可能使用的全量成员。
2. 对 `Flow ID`、`SrcIP`、`DstIP`、`Conn_state`、`Service`、`Segment_src`、`Segment_dst`、`Expoid_src`、`Expoid_dst` 逐值计算 SHA256，再对 `1e8` 取模，并把哈希列留作模型输入。
3. 之后只从特征中删除 `Label_src`、`Label_dst`、`Label`。因此流标识、IP、演习分段和资产标识的哈希仍可能形成身份捷径。
4. 把正负无穷替换为 NaN，但没有继续插补或删除 NaN。
5. 使用 `train_test_split(test_size=0.2, random_state=42)`；没有分层、时间或分组隔离。
6. 使用 `RandomForestClassifier(n_estimators=100, random_state=42)`；其余参数继承安装版本默认值。
7. 报告 `f1_score(..., average="weighted")`。
8. `requirements.txt` 只列包名而没有锁定版本，因而随机森林默认值、NaN 支持和指标实现不能视为环境完全固定。

## 三方证据边界

- **论文表 8**：报告 4:1 随机森林实验和 `F1=0.997`，但未披露精确输入字段、超参、种子和切分实现。
- **作者代码示例**：默认前 80k、100 树、种子 42、weighted F1；该示例可以按固定提交复跑，但不能反向补写为论文表 8 的协议。
- **本课题复现**：原样身份哈希版只能用于复现核验，禁止进入与本方法的正式胜负表；正式基线必须在统一冻结成员、合法字段、标签权限、预算和指标下以种子 42/43/44 重跑，并标为论文约束独立复现。

## Zotero 与本地状态

- Zotero 本地接口于 2026-08-11 可用。
- 以 `LSPR23` 查询检出三条 Dijk 2024 同题论文记录：`VGKDTWHX`、`HTEK2J2I`、`CDDWA2UR`。为避免新增第四条重复记录，本任务没有再次导入论文。
- 以 `scilicet64` 查询没有独立代码仓库条目。仓库在本知识库中作为论文源码证据登记，不伪装成新的论文记录。
- 核验时临时只读克隆固定在 `/tmp/lspr23-496cc558`；该路径不是长期原件。由于仓库无许可证，本仓库只持久化提交、链接、哈希与协议抽取。

## 证据边界

“代码示例可复跑”不等于“论文报告实验可严格复现”。在取得论文实际训练代码、精确成员、字段清单、环境锁和运行收据前，不得把示例结果称为表 8 复现，也不得用它声称本课题胜过公开方法。

