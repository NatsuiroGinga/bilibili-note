# DRIFT 条件记忆源期资格诊断实施计划

> **执行要求**：实现时使用 `daily-coding`，保持最小变更；本仓库不创建人工测试，语法与入口检查后直接运行冻结源期真实数据。

**目标**：用 T17-only P0 对 T17、T18、T19 验证集完成确定性前向，判断 DeepEmbed／Engram 条件记忆所需的表内低支持、组合惊异与类条件语义碰撞是否具有超过普通 n-gram 和打乱负控的独立错误关联。

**设计依据**：[第三章 DRIFT 条件记忆机制轴研究卡](../../../thesis/methods/第三章-DRIFT条件记忆机制轴研究卡.md)

## 全局边界

- 只读取 T17 `train`、T17/T18/T19 `val` 与三年 raw DGA family 文件；入口拒绝 T20–T25。
- 复用冻结 P0 检查点、tokenizer、模型公式和 FP32 验证路径，不更新任何权重。
- family 只作非歧义 DGA 分面，不进入模型、键、关联模型或阈值；良性不伪造 family。
- 输出不保留原始域名，只保存 SHA-256 样本键、预测、连续诊断量和合法分面。
- 主裁决使用连续量、逐样本成对对数损失差和 95% 正态近似区间；不添加频数阈值或候选网格。

## 文件边界

- 新建 `thesis/experiments/llm_probe/tools/ch3_drift_condmem_source_qualification.py`：唯一诊断入口，负责身份核验、T17 频数、三年特征前向、family 定向连接、诊断模型和原子结果。
- 新建 `thesis/experiments/llm_probe/configs/ch3-drift-condmem-source-qualification-v1.json`：冻结成员、行数、SHA-256、P0 身份、统计与运行参数。
- 新建 `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_drift_condmem_source_qualification_v1.sh`：通过统一启动与回传入口运行，回传上限覆盖逐样本 Parquet。
- 不修改 P0、旧探针、旧配置或任何 T20–T25 制品。

## 实施步骤

### 任务一：冻结配置与身份核验

- [x] 配置显式登记两份 T17 train、六份 T17–T19 val、三份 raw DGA 的路径、标签、行数和 SHA-256。
- [x] 登记 P0 检查点、tokenizer、配置和代码 SHA-256；入口使用 `strict=True` 加载并核对完成状态。
- [x] 入口机械拒绝路径或年份中出现 T20–T25、绝对数据路径、非 `screening_only` 或非冻结 revision。

### 任务二：T17 安全键统计

- [x] 以去重 eSLD 为文档单元，分别累计良性／DGA 的字符 1/2/3-gram 与 WordPiece unigram 文档频数。
- [x] 原子保存结构化频数表和摘要；断点存在且身份一致时复用，不重复扫描。
- [x] 生成确定性的全频数循环置换与同总支持层类条件循环置换，不搜索随机种子。

### 任务三：三年逐样本前向与 family 连接

- [x] 使用 P0 的 FP32、`eval()`、`inference_mode()` 路径，对 900,000 个验证样本一次前向。
- [x] 写出 C00 概率、logit 差、有符号余量、损失、错误、长度形态、OOV、支持、碰撞、组合惊异和普通 n-gram 分数。
- [x] 仅为三年 DGA val 键流式扫描 raw family；多 family 标歧义并从主 family 分面排除。
- [x] 每年原子发布一个去域名 Parquet；状态记录输入、模型、代码和输出哈希。

### 任务四：冻结关联模型与裁决

- [x] 在 T17 val 分类别拟合 `D0`、`D_DE`、`D_Engram` 及两个负控版本；连续变量仅用 T17 经验秩变换。
- [x] 冻结后一次评价 T18 和 T19，输出逐样本对数损失差、均值、标准误和 95% 区间。
- [x] 输出连续偏秩关联、非歧义 family 内中心化关联、新 family 描述分面和敏感性结果。
- [x] 按研究卡逐项生成支持／证伪布尔量；任一硬条件失败即否决当前条件记忆轴，不自动进入短训。

### 任务五：验证与真实运行

- [x] 使用 `/opt/miniconda3/envs/rwkv/bin/python -m py_compile` 检查 Python 语法。
- [x] 使用 `bash -n` 检查启动器，并运行工具 `--help` 验证入口。
- [x] 用 `git diff --check` 检查新增文件；不运行 `black`、pytest 或人工夹具。
- [x] 同步三个新增文件到服务器，核对 SHA-256，通过统一启动器运行并启用本机回传。
- [x] 回收结果后使用 `results-analysis` 读取原始 JSON／Parquet，再更新 DRIFT 恢复卡。

## 执行问题

- 首次启动发现服务器缺四个 T18/T19 验证文件；从本机冻结哈希制品同步后以同一身份恢复，计算前失败不构成科学结果。
- 第二次启动发现 raw Parquet 实际字段顺序为 `domain,label,family`；仅修正字段顺序断言，重新通过语法与入口检查后以同一配置恢复。

## 当前状态

**已完成**：运行状态为 `rejected_after_source_qualification`；完整裁决由结果报告与 DRIFT 恢复卡承接。
