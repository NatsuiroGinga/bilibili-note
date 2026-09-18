# ChatGPT 只读交接包

**状态：外部候选，待本地全文和实验复核。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-drift-20260908`
- commit：`43bcac46d8883056851159e52a9c2df1359ea5b8`
- requested_model：`auto`
- requested_effort：`high`
- fallback_model：`GPT-5.5 Thinking`
- selection_rationale：`旧对话已覆盖主体，本次只补新诊断、引用复现增量与DRIFT比较，使用普通ChatGPT深度研究并限制新增近邻数量。`
- requested_mode：`deep-research`
- requested_apps：`sider-scholar,consensus,scite,github`
- task_type：`experiment-analysis`
- source_scope：`旧对话上下文、公开论文全文、官方代码和官方数据`
- sanitized_summary_included：`true`
- fulltext_required：`true`
- zotero_ingest_required：`false`
- allowed_paths：
  - `.Codex/docs/2026-09-08-LAMDA原论文与相关文献综述/公开交接上下文.md`
  - `.Codex/docs/ChatGPT交接工作流.md`

## 任务

这是既有LAMDA深度研究对话的有界增量追问，不要重做此前已完成的正式题录、论文表格、官方制品枚举、代码固定修订、数据完整性和既有综述。只补三类缺口：第一，结合给定聚合诊断，核对官方年份划分、特征构建、全期词表和方差筛选的精确论文及官方源码锚点，并区分未来协变量预处理与标签泄漏；第二，截至当前只列独立引用、第三方复现和实际使用版图的新增证据，并在最多六篇新增直接近邻内给出同协议最强基线、指标天花板、剩余时间漂移或未见恶意软件族病灶、公开性、单卡成本和可复现性；第三，用公开证据比较LAMDA与DRIFT作为第三章主数据或备选数据的任务结构、时间轴、家族字段、低误报评价、预处理资格、资源和可复现性。方法建议只映射序列状态、条件记忆、迁移、课程和稳健风险等家族的真实适配缺口，不强行使用RWKV。只用原论文、官方代码、官方数据和完整全文；仅题录或摘要必须降级。不得改变现有研究合同、Goal、恢复卡或候选排序。

## 脱敏实验摘要

来源期与近时段聚合诊断，完整4561维视图：AP IID/2016/2017=0.994404/0.937396/0.346236；ROC-AUC IID/2016/2017=0.994836/0.948836/0.545725；FNR IID/2016/2017=0.025211/0.222449/0.918489。该诊断只具筛查身份；官方4561维特征存在2013至2025全期词表和方差筛选读取未来协变量统计的预处理疑点，不能据此裁决严格时间外推资格。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
