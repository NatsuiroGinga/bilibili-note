# 已发表神经基线运营指标回填结果分析计划

## 目标

仅使用本地回收根 `thesis/experiments/llm_probe/runs/diagnostics/ch3-published-neural-operational-backfill-v1/`，对 Transformer、一维 CNN 和 GRU 的目标年运营指标回填制品进行机械验收与单次确定性后处理，形成可审计的严格分析包。

## 文件所有权

- 只修改本目录。
- 不修改实验源码、原始制品、路线总控、章节恢复卡或统一总表。
- 不暂存、提交或回滚工作树中其他文件。

## 阶段

- [x] P0：读取仓库、RWKV、`llm_probe` 局部规则及 `planning-with-files`、`results-analysis` 技能。
- [x] P0：读取统一目标合同，冻结 `4%` 并列组、完整曲线、首次告警和支配判据。
- [x] P0：机械核验 `manifest/status/receipt/NPZ/JSON` 的状态、哈希、形状、键、计数和跨文件一致性。
- [x] P0：提取三模型六档、完整曲线、首次告警、资源和旧锚全精度差值记录。
- [x] P0：按完整目标年运营向量机械判断 GRU 是否被 Transformer 或 CNN 支配。
- [x] P1：写成 `analysis-report.md`、`stats-appendix.md`、`figure-catalog.md`。
- [x] P1：执行文档静态检查、Git 范围核验，并只提交本目录。

## 冻结分析问题

1. 三个模型的六档名义/实际 FPR 与 DR 是否完整且收据一致？
2. 完整告警预算曲线和首次告警曲线能否支持同池逐点偏序？
3. GRU 是否在全部必需运营维度上被 Transformer 或 CNN 支配？
4. 资源收据与旧标量锚是否复现，存在何种证据边界？

## 决策

- 本轮是单次确定性后处理，不计算种子方差、置信区间、显著性检验或伪效应量。
- 单个名义或实际 `4%` 点不能形成支配结论；阈值必须整组纳入并报告实际可达 FPR。
- 只有完整目标年曲线与首次告警轴可比时，才允许宣称目标年全局支配；缺失源年曲线不能外推为源年或跨年度全局支配。
- LSPR24 已被历史访问，所有结果只能表述为目标年描述性评价。
- 仅当图能改变模型支配或使用决策时才生成；否则 `figure-catalog.md` 记录不生成理由。

## 验收命令

- `git status --short -- .Codex/docs/RWKV/2026-08-21-已发表神经基线运营指标回填结果分析`
- 使用项目环境读取 JSON/NPZ 并核验 SHA-256、键、形状、单调性和跨文件数值一致性。
- `rg -n "待补|TODO|FIXME|显著|置信区间" .Codex/docs/RWKV/2026-08-21-已发表神经基线运营指标回填结果分析`
- `git diff --check -- .Codex/docs/RWKV/2026-08-21-已发表神经基线运营指标回填结果分析`

## 状态

**分析与静态检查已完成，等待独占提交。**

## 错误记录

- `uv run --no-sync python` 读取 NPZ 时报告 `ModuleNotFoundError: No module named 'numpy'`；该环境问题不影响 JSON 和哈希验收。
- `uv run --no-sync --with numpy` 因受限网络无法解析镜像域名；未申请联网，改用 Python 标准库解析 NPZ/NPY。
- 标准库首次按 NPY 魔数解析 ZIP 成员触发断言；先检查实际成员与头部，再修正解析器，不据此判断制品损坏。
- 初版把输入收据中的 12 位小数旧锚门计入机械验收；按统一合同修正为仅记录全精度差值，不再把容差门用于身份、有效性或支配裁决。
- 一次并行检查的工具编排脚本出现 JavaScript 语法错误，未执行任何底层命令；已拆成明确的独立检查，不影响制品和分析结果。
- 首次 `git add` 因沙箱无权创建工作树共享 Git 元数据中的 `index.lock` 而失败；需要按既有提交授权在沙箱外重试，文件内容未受影响。
