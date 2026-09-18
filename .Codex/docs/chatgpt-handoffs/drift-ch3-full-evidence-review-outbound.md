# ChatGPT 只读交接包

**状态：外部候选，待本地全文和实验复核。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-drift-20260908`
- commit：`1e2201f5576f9d78feabc3e042e9c65423b4ef4d`
- requested_model：`GPT-6 Pro`
- requested_effort：`high`
- fallback_model：`GPT-5.5`
- selection_rationale：`多篇全文、综述和理论命题需要高能力模型进行联合核查`
- requested_mode：`deep-research`
- requested_apps：`github`
- task_type：`literature-review`
- source_scope：`固定提交中的16份Markdown与DRIFT官方arXiv v2`
- sanitized_summary_included：`false`
- fulltext_required：`true`
- zotero_ingest_required：`false`
- allowed_paths：
  - `wiki/papers/attack-detection/朱焱雷-全文.md`
  - `.Codex/docs/2026-09-07-DGA检测系统综述/文献综述.md`
  - `.Codex/docs/2026-09-07-DRIFT引用与方法前沿/文献综述.md`
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/task_plan.md`
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/zhuh-ch3-benchmark.md`
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/V4真实T17嵌套编辑耦合核查实施报告.md`
  - `thesis/methods/第三章-朱焱雷第三章机制构思与创新声明分析.md`
  - `thesis/methods/第三章-F指标空间与朱焱雷实验对照核查.md`
  - `thesis/methods/第三章-DRIFT数据角色与评价协议.md`
  - `thesis/methods/第三章-正式攻击与目标抽样合同裁决.md`
  - `thesis/methods/第三章-正式评价与F指标空间科研裁决.md`
  - `thesis/methods/第三章-理论命题包.md`
  - `thesis/methods/第三章-方法来源台账.md`
  - `thesis/methods/第三章-命题级原创性排重报告.md`
  - `thesis/methods/第三章-命题级原创性科研裁决.md`
  - `wiki/papers/methodology/2024-Losch-ESAT选择性对抗训练.md`

## 任务

请通过 GitHub 应用只读打开本包指定的仓库、分支、固定提交和全部 allowed_paths，并另行读取 DRIFT 官方 arXiv v2：https://arxiv.org/abs/2605.10436。先列出实际成功打开的路径及提交号；再核对朱焱雷第三章主表、消融、机制数量与创新声明，核对 DRIFT 的任务设定、时间漂移方法与实验结论，审查当前 F 方案的形式化链条、V4 共享前缀边界、指标提升空间、评价合同及命题级原创性排重。必须区分原文事实、本课题已有证据、数学推论和仍待真实实验检验的假设；指出具体文件、小节、公式、表格或页码。不得修改仓库、裁决候选存废或提出新的数值设定。最终返回一份可供本地逐条复核的 Markdown 审查报告。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
