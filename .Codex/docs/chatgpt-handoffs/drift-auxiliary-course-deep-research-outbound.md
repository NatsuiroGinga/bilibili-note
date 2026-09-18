# ChatGPT 只读交接包

**状态：外部候选，未核验。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-drift-20260908`
- commit：`43bcac46d8883056851159e52a9c2df1359ea5b8`
- requested_model：`auto`
- requested_effort：`high`
- fallback_model：`GPT-5.6 Thinking`
- selection_rationale：`多篇全文、引用链和理论近邻排重需要普通 ChatGPT 可用的高能力模型；深度研究只负责公开候选，本地 Codex 负责全文复核与最终裁决。`
- requested_mode：`deep-research`
- requested_apps：`sider-scholar,consensus,scite,github`
- source_scope：`仅公开论文、会议或期刊官网、arXiv、作者主页和公开GitHub；只读取白名单公开Markdown`
- fulltext_required：`true`
- zotero_ingest_required：`false`
- allowed_paths：
  - `.Codex/docs/2026-09-08-DRIFT伪未来辅助课程/公开交接上下文.md`

## 任务

仅研究公开来源。系统发现并排重辅助任务负迁移、验证反馈任务加权、课程式多任务预训练、ForkMerge/PCGrad/GradNorm/DWA/Auto-lambda/AANG、训练域内留出组的 episodic domain generalization，以及恶意软件或 DGA 自监督适应直接近邻。重点判断“源侧伪未来 family 验证反馈调度 MTP/TPP/TOV”是否只是已知方法换名。返回逐篇稳定标识、全文入口、公式或章节、覆盖关系与缺口；不得接触私有数据、日志、权重、凭据或未公开测试信息。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果只是未核验外部候选，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出凭据、数据、
权重、检查点、日志、原始 PDF 或其他敏感内容。
