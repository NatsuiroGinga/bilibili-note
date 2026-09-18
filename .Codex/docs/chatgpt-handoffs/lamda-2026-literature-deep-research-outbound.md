# ChatGPT 只读交接包

**状态：外部候选，未核验。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-drift-20260908`
- commit：`43bcac46d8883056851159e52a9c2df1359ea5b8`
- requested_model：`auto`
- requested_effort：`high`
- fallback_model：`GPT-5.6 Thinking`
- selection_rationale：`多篇全文、版本关系、官方仓库与引用链交叉核验需要普通ChatGPT当前可用的高能力模型和深度研究；若自动路由不可用则降级到高思考模型。`
- requested_mode：`deep-research`
- requested_apps：`github,zotero,sider-scholar,scite`
- source_scope：`仅公开论文、OpenReview、arXiv、作者或会议官网、官方GitHub/Hugging Face/DOI页面，以及出站包明确列出的公开Markdown`
- fulltext_required：`true`
- zotero_ingest_required：`true`
- allowed_paths：
  - `.Codex/docs/2026-09-08-LAMDA原论文与相关文献综述/公开交接上下文.md`
  - `.Codex/docs/ChatGPT交接工作流.md`

## 任务

仅研究公开来源。先核准 LAMDA Android 恶意软件时间漂移论文身份，再系统提取数据协议、全部实验、泄漏风险、2023至2026直接近邻与引用链，并给出证据等级和可证伪研究空白。不要读取或推断未列路径、私有数据、权重、日志、PDF原件或凭据。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果只是未核验外部候选，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出凭据、数据、
权重、检查点、日志、原始 PDF 或其他敏感内容。
