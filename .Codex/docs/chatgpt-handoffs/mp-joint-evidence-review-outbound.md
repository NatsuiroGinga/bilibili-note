# ChatGPT 只读交接包

**状态：外部候选，待本地全文和实验复核。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-drift-20260908`
- remote_ref：`refs/heads/exp/ch3-drift-20260908`
- commit：`6c1c81b0f1b61ee95faa822a932d746dec0d8275`
- snapshot_url：`https://github.com/NatsuiroGinga/bilibili-note/tree/6c1c81b0f1b61ee95faa822a932d746dec0d8275`
- remote_verification：上述证据提交已推送且可从 `origin/exp/ch3-drift-20260908` 的历史访问；
  分支头可包含后续交接元数据提交，实质审查固定读取上述证据提交
- requested_model：`auto`
- requested_effort：`high`
- fallback_model：`auto`
- selection_rationale：`该任务涉及跨文档机制与预登记合同反例审查，需使用普通 ChatGPT 当前可用的高能力模型和较高思考强度；若不可用须如实记录降级。`
- requested_mode：`chat`
- requested_apps：``
- task_type：`mechanism-counterexample`
- source_scope：`仅限列出的项目内 Markdown 中与 MP 预登记机制、比较合同、理论命题和 V4 前提核查相关的文字；不含任何原始数据、模型、运行日志或敏感信息。`
- sanitized_summary_included：`false`
- fulltext_required：`false`
- zotero_ingest_required：`false`
- allowed_paths：
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/task_plan.md`
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/zhuh-ch3-benchmark.md`
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/V4真实T17嵌套编辑耦合核查实施报告.md`
  - `thesis/methods/第三章-朱焱雷第三章机制构思与创新声明分析.md`
  - `thesis/methods/第三章-理论命题包.md`

## 任务

先通过已连接的 GitHub 应用打开私有仓库 `NatsuiroGinga/bilibili-note`，固定读取远程分支
`exp/ch3-drift-20260908` 的提交 `6c1c81b0f1b61ee95faa822a932d746dec0d8275`；不要读取默认分支，
也不要沿用上一轮对旧提交 `d4b7756a9c2baff5ca893541586b0e6c089e842f` 的 404 结果。

对 MP（混合曝光加误报保护）这一预登记缺失格进行有界、只读的联合证据审查。只阅读白名单内 Markdown；请识别公式或实验合同中可能导致不可归因、额外设计自由度、机制混淆、比较不公平或结论越界的反例与缺口，并检查 V4 否定结果是否已被理论命题包诚实吸收。不得提出或选择新阈值、超参数、测试样本、候选存废决定或合同改写。输出 Markdown：先逐条确认成功读取的仓库内路径与提交哈希，再列出已由文档明示且可核对的事实，然后列出每条反例或风险（对应路径和小节）、所依赖的假设、最小本地可证伪检查；最后列出不能从白名单判断的事项。不要访问或请求白名单外的材料或敏感运行信息。若任一路径无法读取，必须给出该路径和具体错误，不得在缺少正文时进行实质审查。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
