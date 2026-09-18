# LAMDA 来源期与近时段资格探针实施计划

> **执行代理必须读取：** `superpowers:subagent-driven-development` 与 `daily-coding`。本仓库禁止人工夹具和 `black`，只做语法/入口检查后运行真实来源与开发数据。

**目标：** 实现一个只读取 LAMDA 2013、2014、2016、2017 的 `screening_only` 工具，量化时间退化、低误报、新颖特征向量和 URL 域名特征捷径；机械拒绝读取 2018--2025 封印年份。

**结构：** 以 PyArrow 分批扫描 Parquet，不把全数据装入内存。模型复用 LAMDA 官方 MLP 的 BatchNorm、ReLU、Dropout、批量和学习率模式，但用 `128→64→32` 的三层减半宽度满足本仓库本机筛选 `≤100` 万参数上限，并只训练 6 轮。分别训练完整 4561 特征和移除 `URLDomainList` 的特征视图，输出来源 IID、2016、2017 以及新颖子集的同一指标表。

**技术栈：** `/opt/miniconda3/envs/rwkv/bin/python`、PyTorch 2.12、PyArrow 25、scikit-learn 1.9、NumPy 2.4；本机优先 MPS，精度固定 float32。

**证据规格：** `.Codex/docs/2026-09-08-下一候选网络安全数据集筛选/notes.md` 与下载目录 `manifest.json`。

## 全局约束

- 只修改 `thesis/experiments/llm_probe/tools/ch3_lamda_source_near_screening.py` 和实现报告；不修改数据、恢复卡、路线总控或其他工具。
- 你不是唯一代理，不得回滚、暂存或提交他人变更，不执行任何 Git 写操作。
- 输入根必须精确为 `thesis/experiments/llm_probe/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767`，启动时核验 manifest 的 repo、revision、26 个文件、总字节、25 个官方哈希零错配、24 个 Parquet、1,008,381 行和 4,566 列。
- 允许读取的年份固定为 2013、2014、2016、2017。任何参数、路径或扫描结果出现 2018--2025 时立即在读取行数据前失败；封印文件只能由既有 manifest 代表。
- 2013、2014 除各自最后月份 `2013-12`、`2014-08` 外用于训练；这两个末月构成来源 IID 验证。2016、2017 各自是开发分面，不用于选轮、阈值或超参数。
- 样本单位是 APK Hash。`hash`、`label`、`family`、`vt_count`、`year_month` 永不作为输入特征。
- 训练固定单一种子 42、最多 6 轮、批量 512、Adam 学习率 0.001、float32。这些值分别来自官方脚本默认种子/批量/优化器和本仓库本机最多 6 轮规则。
- 两个模型均须小于等于 1000000 参数；完整视图预期 594753 参数，去 URL 视图预期 415169 参数。运行时对实际参数量机械断言。
- 不使用 SwanLab，不打开网络，不写逐样本原始 Hash；制品中的 APK 身份只保存二进制 SHA256 摘要或聚合量。
- 这是 `screening_only`，不得把结果写入论文效果表或声称方法有效。
- 官方向量化代码已确认用 2013--2025 全部年份 train 分片拟合全局词表和方差选择器。输出配置与状态必须写 `published_feature_space_uses_future_covariates=true`，并明确本探针无法消除该风险；不得将当前 4561 维结果称为严格源期归纳协议。

## 任务：实现并运行资格探针

**文件：**

- 新建：`thesis/experiments/llm_probe/tools/ch3_lamda_source_near_screening.py`
- 首次真实运行：`thesis/experiments/llm_probe/runs/diagnostics/lamda-iclr2026-source-near-screening-v1/`；该运行发现去 URL 视图用 3158 维指纹查询 4561 维训练指纹集合，新颖子集无效，必须保留并标记，禁止覆盖或删除。
- 修复后权威运行：`thesis/experiments/llm_probe/runs/diagnostics/lamda-iclr2026-source-near-screening-fingerprint-fix-v2/`
- 资源合同修复后最终权威运行：`thesis/experiments/llm_probe/runs/diagnostics/lamda-iclr2026-source-near-screening-budget1m-v3/`。v2 的完整/去 URL 模型分别有 5364481/3927809 参数，超过本机筛选上限，只保留探索收据并标记资源合同违规。
- 新建报告：`.Codex/docs/2026-09-08-下一候选网络安全数据集筛选/lamda-screening-implementation-report.md`

**必须实现：**

1. `load_and_verify_manifest(data_root: Path) -> dict`：核验上述冻结身份与完成状态。
2. `discover_allowed_files(data_root: Path) -> dict[int, list[Path]]`：只返回四个允许年份的 train/test Parquet；在打开 Parquet 前拒绝封印年份。
3. `load_feature_views(mapping_path: Path) -> dict[str, list[str]]`：返回 `all_features` 与排除映射前缀 `URLDomainList_` 的 `without_url_domain`；断言前者 4561 项、URL 项 1403 项、后者 3158 项。
4. 分批数据迭代：PyArrow 扫描时只读取当前视图特征与 `label/year_month/hash/family/vt_count`，按年月路由训练、IID 和两个开发分面；训练批不得读取开发区。
5. 模型：`input→128→64→32→1`，每个隐藏层依次 BatchNorm、ReLU、Dropout(0.5)，损失使用数值稳定的 `BCEWithLogitsLoss`。每轮只依据 IID 验证 AP 保存最佳状态。该宽度以 4561 维最宽输入下不超过 100 万参数为约束，并沿用官方 MLP 最小隐藏宽度 128 后逐层减半。
6. 阈值：同时报告固定概率 0.5 和仅由 IID 良性分数确定的零假阳性阈值 `nextafter(max_benign_score, +inf)`；开发分数不参与阈值。
7. 指标：样本数、阳性率、ROC-AUC、AP、F1、宏 F1、FPR、FNR、Brier 分数；开发区另按年月和恶意家族报告召回及最坏分面，不设事后支持阈值。
8. 新颖子集：无论模型使用完整视图还是去 URL 视图，都只用训练区**完整 4561 位特征**的 SHA256 指纹定义同一个新颖掩码；开发区同时报告全体与移除来源重复特征向量后的指标。不得把不同 Hash 的相同特征向量称为同 APK 泄漏。
9. 两个视图各自独立训练且使用相同公共随机种子；报告 `URLDomainList` 移除前后的完整差量，但只把它解释为捷径诊断。
10. 输出 `effective-config.json`、`status.json`、`metrics.json`、`resource.json` 和 `manifest.json`。记录输入 manifest SHA256、工具 SHA256、设备、Python/torch/pyarrow/sklearn/numpy 版本、墙钟、峰值常驻内存；MPS 无可靠显存接口时写 `null` 并说明。完成时 manifest 必须追加所有输出文件的字节与 SHA256，`status.json.started_at` 保留真实开始时刻。
11. 所有输出都记录 `published_feature_space_uses_future_covariates=true` 和官方代码 revision `7728bfafcd5539a286b5f8c47b6f1e3b2d1f4249`；结果只能裁决错误余量和 URL 特征影响，不能裁决无泄漏正式资格。
12. 运行中每轮写进度和累计墙钟。任何异常将 `status.json` 写成 `failed` 并保留阶段和错误类别，不吞异常。

**支持/失败门：**

- 数据资格支持：2016 或 2017 至少一个开发分面的 AP 下降，并且 FNR 或 FPR 相对 IID 恶化；方向还须与 LAMDA 原论文五次运行的 IID→NEAR 退化一致。本次单训练种子结果只作描述性复核，不生成或冒充训练不确定性区间。
- 数据资格失败：IID 与两个开发年没有上述同向恶化，或者恶化只存在于完整 URL 域名视图而在去 URL 视图及新颖子集消失。
- URL 捷径支持：完整视图显著优于去 URL 视图，但新颖子集或较晚开发年的优势收缩；只说明 URL 特征影响，不直接否决数据。
- RWKV 不参与本探针，任何结果都不得据此决定 RWKV 机制存废。

**验收命令：**

```bash
/opt/miniconda3/envs/rwkv/bin/python -m py_compile thesis/experiments/llm_probe/tools/ch3_lamda_source_near_screening.py
/opt/miniconda3/envs/rwkv/bin/python thesis/experiments/llm_probe/tools/ch3_lamda_source_near_screening.py --help
/opt/miniconda3/envs/rwkv/bin/python thesis/experiments/llm_probe/tools/ch3_lamda_source_near_screening.py \
  --data-root thesis/experiments/llm_probe/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767 \
  --output-dir thesis/experiments/llm_probe/runs/diagnostics/lamda-iclr2026-source-near-screening-budget1m-v3
```

实现代理必须在报告中给出三个命令的退出码、真实运行状态、指标路径、资源路径和任何偏离；不得创建人工测试。
