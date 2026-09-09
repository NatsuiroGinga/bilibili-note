```text
actual_model: GPT-6 Astra Pro
actual_effort: 本对话未暴露可独立核验的 effort 档位；不将“深度研究”要求等同于已确认的模型思考档位。
actual_mode: 普通 ChatGPT 对话内的多轮公开文献检索、全文核对与综合；未取得独立 Deep Research 作业状态。
used_apps: Sider Scholar、GitHub、Hugging Face；辅助使用 web 核对公开学术全文、会议记录和官方制品页面。
核验截止日期: 2026-09-08
```

# LAMDA：身份、数据制品、实验与研究方向审查

**核心判断：LAMDA 的身份及 ICLR 2026 Poster 状态已经核准；但本轮能够完整逐表核对的是 2025 年的 arXiv v1，不能把这些数字直接标注为“已核验的 ICLR 2026 定稿结果”。** 更值得优先处理的问题，是官方预处理使用了全部年份训练分片的协变量，以及论文、附录和当前代码之间存在若干可定位的不一致。([arxiv.org](https://arxiv.org/abs/2505.18551)) fileciteturn8file0L2-L5

本报告附有两份 Markdown 核验记录，作为正文的一部分：

[逐表数字账本：主文与附录的已核验数值、位置及缺口](sandbox:/mnt/data/lamda_research/LAMDA_v1_numeric_ledger_2026-09-08.md)

[官方制品记录：固定提交、目录清单、远端校验值及未完成项](sandbox:/mnt/data/lamda_research/LAMDA_artifact_manifest_2026-09-08.md)

证据等级含义：**【在线全文】**表示读到了论文正文、附录或官方代码/数据卡；**【在线摘要】**只支持摘要层面的描述；**【仅题录】**支持身份、日期、场所等元数据；**【推论】**是基于已列证据的审计判断或待验证设计。下面不以摘要替代实验或方法证据。

---

## 一、正式身份与版本关系

### 1.1 已核准的论文

**【仅题录】正式题名：**

**LAMDA: A Longitudinal Android Malware Benchmark for Concept Drift Analysis**

作者顺序：

**Md Ahsanul Haque；Ismail Hossain；Md Mahmuduzzaman Kamol；Md Jahangir Alam；Suresh Kumar Amalapuram；Sajedul Talukder；Mohammad Saidur Rahman。**

稳定入口：[arXiv](https://arxiv.org/abs/2505.18551)、[arXiv DOI](https://doi.org/10.48550/arXiv.2505.18551)、[OpenReview 论坛](https://openreview.net/forum?id=1FnCrZtBNQ)、[ICLR 官方记录](https://iclr.cc/virtual/2026/poster/10011850)、[官方项目页](https://iqsec-lab.github.io/LAMDA/)、[官方 GitHub](https://github.com/IQSeC-Lab/LAMDA)。以上交叉指向同一 Android 恶意软件基准，未与其他 LaMDA 项目混用。([arxiv.org](https://arxiv.org/abs/2505.18551))

| 项目 | 核验结果 | 证据等级 |
|---|---|---|
| arXiv 标识 | `2505.18551` | 仅题录 |
| 本轮可核对版本 | `2505.18551v1` | 在线全文 |
| v1 提交时间 | **2025-05-24 06:36:39 UTC** | 仅题录 |
| v1 规模 | 31 页、21 图、16 表 | 仅题录 |
| OpenReview forum | **`1FnCrZtBNQ`** | 仅题录 |
| ICLR 2026 状态 | **Poster，已由会议官网确认** | 仅题录 |
| OpenReview 修订链、接收决定日期、定稿更新时间 | **未取得可完整核验的记录** | 未核验 |
| arXiv v1 与 ICLR 定稿是否逐项一致 | **不能确认** | 未核验 |

上述版本信息来自 arXiv 与会议官网；官方仓库也使用同一 OpenReview 标识。([arxiv.org](https://arxiv.org/abs/2505.18551)) fileciteturn9file0L2-L5

**【推论】引用方式应分开：**介绍论文归属时可以写“ICLR 2026”；引用本报告的实验数字时，应写“arXiv:2505.18551v1，表 X”。当前仓库存在 DetectBERT、ViT 实验代码，但“代码存在”不证明相应结果已经进入会议定稿，也不证明本轮核验了这些结果。fileciteturn5file0L2-L5

---

## 二、官方数据、固定版本、文件与许可

### 2.1 官方性与可固定标识

**【在线全文／仅题录】**论文项目页、GitHub README 与 Hugging Face 数据集互相链接，已核准官方数据入口为：

[Hugging Face：IQSeC-Lab/LAMDA](https://huggingface.co/datasets/IQSeC-Lab/LAMDA)
[数据 DOI：10.57967/hf/5563](https://doi.org/10.57967/hf/5563)

本轮 GitHub 读取仅涉及已核准为公开的作者机构仓库。([iqsec-lab.github.io](https://iqsec-lab.github.io/LAMDA/)) fileciteturn9file0L2-L5

| 制品 | 固定标识 | 日期／边界 |
|---|---|---|
| GitHub commit | `7728bfafcd5539a286b5f8c47b6f1e3b2d1f4249` | 2026-03-28 21:43:02 UTC |
| GitHub tree | `e3e2877b5f8c5bbeeca272f18c62751d02104432` | 递归目录返回 `truncated=false` |
| Hugging Face revision | `ad9614bdd5556767f97ced2fce797c2f06408ebf` | 仓库更新日期为 2026-02-14；精确 UTC 未核准 |
| 数据 DOI | `10.57967/hf/5563` | 是数据标识，不是逐文件校验值 |

GitHub 固定提交与目录证据如下；HF 的全部文件尚未完成与该 revision 的逐一绑定，不能称为完整冻结清单。fileciteturn4file0L2-L5 fileciteturn5file0L2-L5 ([huggingface.co](https://huggingface.co/datasets/IQSeC-Lab/LAMDA/tree/main/NPZ_Version))

### 2.2 文件清单核验到什么程度

**【在线全文】**GitHub 根目录已核到 `.gitignore`、`README.md`、`code/`、`index.html`、`metadata.csv.gz`、`static/`。HF 根目录已核到：

```text
Baseline/
NPZ_Version/
var_thresh_0.0001/
var_thresh_0.01/
README.md
metadata.csv
以及若干仓库配置文件
```

`NPZ_Version/npz_Baseline/` 的 **50 个条目**已经逐项列入附件：12 个年份各有特征 train/test 与 metadata train/test，另有 `vocabulary.txt`、`vocabulary_selected.txt`。其他两个 NPZ 变体和全部 Parquet 叶子文件没有完成同等级枚举。fileciteturn5file0L2-L5 ([huggingface.co](https://huggingface.co/datasets/IQSeC-Lab/LAMDA/tree/main/NPZ_Version/npz_Baseline))

**【在线全文】校验信息示例：**

| 文件 | 可核验信息 |
|---|---|
| GitHub `metadata.csv.gz` | 49,047,738 字节；Git blob SHA-1：`f6762b2ab4589d782f0abd70a9abc231d95de1a3` |
| HF `Baseline/2013/2013_test.parquet` | 页面显示 5.04 MB；远端 SHA-256：`208528e70c2c71c3765c4749d0293cd2816ca316dce60ef6eef42899d5aca323` |

**这些是远端元数据，不是本轮下载后对实际字节重新计算的结果。** Git blob SHA-1、Xet hash 与原始文件 SHA-256 也不能互换。fileciteturn5file0L2-L5 ([huggingface.co](https://huggingface.co/datasets/IQSeC-Lab/LAMDA/blob/main/Baseline/2013/2013_test.parquet))

### 2.3 许可证及重要制品缺口

**【在线全文】**HF 数据卡声明 **MIT**；本轮固定 GitHub 目录中没有定位到独立 `LICENSE`。论文 v1 的 CC BY 4.0、项目网页的 CC BY-SA 4.0 与数据卡 MIT 是不同对象的许可，不能据此认定上游 APK、第三方依赖与所有代码采用同一许可。([huggingface.co](https://huggingface.co/datasets/IQSeC-Lab/LAMDA)) fileciteturn5file0L2-L5

**【在线全文→推论】**附录 G 声称提供阈值前原始矩阵和序列化的方差选择器，但在本轮核到的发布目录中，没有定位到对应完整制品。**词表文本不等于逐 APK 原始特征矩阵；已经经过全时期筛选的矩阵，不能完整恢复“只用历史时期重新筛选”的输入。**这是干净时间外推复核的前置条件，不应被省略。([arxiv.org](https://arxiv.org/html/2505.18551v1))

---

## 三、全文中的数据定义与官方协议

### 3.1 来源、纳入排除、时间与标签

| 项目 | 全文及代码中可核准的定义 | 等级与位置 |
|---|---|---|
| 来源 | AndroZoo APK、SHA-256、VirusTotal 检出信息及入库时间；使用 apktool 与 Drebin 风格静态特征提取 | 在线全文；§3、附录 B |
| 时间字段 | 官方 README 明确按 APK **加入 AndroZoo 的时间**组织年月；不是已核准的首次发布或首次恶意活动时间 | 在线全文；README |
| 二分类标签 | 良性：VT 检出数为 0；恶意：至少 4；1–3 的不确定样本排除 | 在线全文；§3 |
| 抽样目标 | 每年目标良性、恶意各约 50,000，保持月度分布，并额外准备约 20% 应对提取失败 | 在线全文；§3 |
| 其他排除 | 损坏、不能正常反编译或特征提取失败的样本 | 在线全文；§3 |
| 年份 | 2013、2014、2016—2025；**缺 2015** | 在线全文；表 2 |
| 总规模 | **1,008,381**：恶意 **369,906**，良性 **638,475** | 在线全文；表 2 |
| 家族 | AVClass 标签；报告 **1,380** 个有效家族，同时有 Singleton 与 Unknown | 在线全文；附录 A、表 3–4 |
| 元数据 | hash、binary label、family、VT count、year-month | 在线全文；README、预处理代码 |

数据定义与计数见 §3、附录 A—B；“时间是入库时间”可由官方 README 单独确认。([arxiv.org](https://arxiv.org/html/2505.18551v1)) fileciteturn9file0L2-L5

**【推论】**“2015 缺失”应解释为本次数据构建未包含该年有效记录，不能扩大成“AndroZoo 从来没有 2015 年样本”。2025 也不能被当成完整自然年、稳定恶意率的代表。([arxiv.org](https://arxiv.org/html/2505.18551v1))

**【在线全文】**原始全局词表为 **9,690,482** 维；主基线 `VarianceThreshold=0.001` 后为 **4,561** 维。特征涵盖权限、组件、Intent、API、网络地址等静态类别。表 6 另列 `0.0001→25,460` 维、`0.01→925` 维；但 B.1 文字将后一项写成 **915**，存在内部冲突。~~~~~~~~~~~~~~~~~~~~~~

### 3.2 两层切分不要混淆

**【在线全文】**数据发布时的年度 train/test 分片，与模型评价的 IID/NEAR/FAR 是两层操作。官方当前监督代码的协议为：

| 层次 | 定义 |
|---|---|
| 发布分片 | 年度数据分为约 80% train、20% test |
| 静态训练 | 2013—2014 的 train 分片，排除 **2013-12、2014-08** |
| IID | 上述两个保留月份的 test 分片 |
| NEAR | 2016—2017 |
| FAR | 2018—2025 |
| 分类阈值 | 当前监督代码为 **0.5** |

这些定义可直接定位到 `run_model()` 中的训练月份与 `splits`。([arxiv.org](https://arxiv.org/html/2505.18551v1)) fileciteturn12file0L2-L5

**【推论】**这里的“IID”是作者的协议名称，不是经过独立统计检验后证明所有数据独立同分布。API Graph 对照使用的时间范围、训练年份和类别分布也不同，因此两数据集成绩之差不能单独识别“漂移强度”的因果贡献。([arxiv.org](https://arxiv.org/html/2505.18551v1))

---

## 四、主要实验数字：可引用结果与解释边界

**完整逐表数值见数字账本。**它保留了主文与附录不同的数值，不把冲突表格合并。以下为最影响研究决策的结果。

### 4.1 静态监督：长期退化主要表现为漏报增加

**【在线全文】定位：主文表 1 的 LAMDA 部分、附录 C.2 表 7；均为 arXiv v1。单位为百分数，± 按作者原样保留。**

| 模型 | IID F1 | NEAR F1 | FAR F1 | FAR FNR | FAR FPR |
|---|---:|---:|---:|---:|---:|
| LightGBM | 97.49 ± 0.17 | 59.48 ± 28.20 | 47.24 ± 27.33 | 64.10 ± 22.97 | 1.30 ± 0.95 |
| MLP | 97.21 ± 0.12 | 56.57 ± 28.41 | 47.59 ± 25.30 | 64.40 ± 20.63 | 1.14 ± 0.71 |
| SVM | 94.98 ± 1.07 | 52.91 ± 28.40 | 41.86 ± 22.55 | 69.93 ± 16.85 | 1.27 ± 0.76 |
| XGBoost | 97.05 ± 0.14 | 55.84 ± 29.73 | 42.75 ± 25.86 | 68.11 ± 20.43 | 1.69 ± 0.57 |

表 7 还报告 Accuracy、Precision、Recall、ROC AUC、PR AUC，已全部转录进附件。~~~~~~~~~~~~~~~~~~~~~~

**【推论】**LightGBM 的 IID→NEAR、IID→FAR F1 分别下降 **38.01、50.25 个百分点**。但 FAR 汇总不能替代逐年混淆矩阵，也不能把所有下降都归因于 \(P(Y\mid X)\) 的变化：类别先验、样本选择、标签变化和特征可用性同时可能变化。上述百分点是表格相减，不是新实验。~~~~~~~~~~~~~~~~~~~~~~

### 4.2 种子、方差和模型配置

**【在线全文】**监督启动器使用 run ID 1—5，主脚本据此设置 Python、NumPy、PyTorch 随机种子。但树模型没有逐项显式绑定相同 run seed；论文汇总还涉及切分内不同年份。**不能把表中的大标准差统一解释为“五个随机种子的方差”，更不能当作置信区间。**fileciteturn10file0L2-L5 fileciteturn11file0L2-L5 ([arxiv.org](https://arxiv.org/html/2505.18551v1))

**【在线全文】**当前固定代码的监督 MLP 使用 1024/512/256/128 隐层、20 epochs、Adam 学习率 0.001、batch 512；LightGBM 最多 5,000 棵树、学习率 0.02、256 leaves、源训练内验证及早停。完整参数已记入附件。**当前代码默认方差阈值是 0.0001，不是主基线 0.001，直接运行不能自动视为表 7 的复现。**fileciteturn11file0L2-L5 fileciteturn12file0L2-L5

### 4.3 持续学习

**【在线全文】定位：附录 J.3，表 15—16。下表是作者报告的跨 experiences/tasks 平均 F1，不是仅该年份测试集的 F1。**

| 设置及训练终点 | Naive | Joint | Replay |
|---|---:|---:|---:|
| Domain-IL，至 2025 | 72.71 ± 0.83 | 88.52 ± 0.46 | 80.57 ± 0.15 |
| Class-IL，至 2024 | 13.27 ± 1.33 | 81.79 ± 0.29 | 12.49 ± 1.76 |

Domain-IL 是跨年二分类；Class-IL 使用 154 个家族，排除 2025。全部逐年结果已列入附件。([arxiv.org](https://arxiv.org/html/2505.18551v1))

**【在线全文→推论】**当前 Domain-IL 代码的 replay 容量为 200，启动器重复三次但未传入不同 seed。代码把已见年份评价叫 backward、未来年份评价叫 forward；这些是相应数据上的成绩，**不是通常需要减去参照成绩的 BWT/FWT 指标**。不能据名称直接套用其他持续学习论文的迁移量解释。fileciteturn13file0L2-L5 fileciteturn14file0L2-L5 fileciteturn15file0L2-L5

### 4.4 漂移检测、标签与后续适应工作

| 结果 | 数字与定位 | 证据边界 |
|---|---|---|
| CADE 在 LAMDA | F1 **0.4407**、FNR **0.4734**、FPR **0.1729**；附录 H 表 14 | 在线全文；无方差，完整预算与时序未核准，不能与静态表 7 直接排名 |
| 标签重新扫描 | 原恶意样本中 **2,985** 个后来被记为良性；附录 F 表 13 | 在线全文；不等同于人工确认的原标签错误 |
| 特征解释变化 | Top-100 SHAP 特征 Jaccard 距离约 **0.9**；§4.5 | 在线全文；作者文字近似，不是本轮逐点重算 |
| 分布距离 | 2014 与 2025 间 Jeffreys divergence 最高约 **7.0**；§5 | 在线全文；不是因果概念漂移证明 |
| CITADEL 在 LAMDA，月标注预算 50 | F1 **70.9±1.2**、FNR **33.6±1.6**、FPR **2.0±0.1**；CITADEL 表 IV | 在线全文；引入了持续标注资源 |
| CITADEL 在 LAMDA，月标注预算 400 | F1 **77.7±0.1**、FNR **24.0±0.1**、FPR **2.3±0.4**；同表 | 在线全文；不是对原论文零适应静态成绩的公平直接比较 |

这些数字分别来自 LAMDA 附录与 CITADEL 正文；预算 100、200 及其余标签表格均已列入附件。([arxiv.org](https://arxiv.org/html/2505.18551v1))

### 4.5 必须单列的冲突与未完成项

| 冲突／缺口 | 已观察到的情况 |
|---|---|
| 主文表 1 vs 附录表 8 | API Graph 的 LightGBM IID F1 分别为 **85.95、83.14**；FAR F1 分别为 **68.20、69.07**，不能混合引用 |
| §4.1 vs 表 1/7 | LightGBM IID FNR：文字 **1.47%**，表格 **1.74%** |
| 附录 B.1 vs 表 6 | 阈值 0.01 的特征维数：文字 **915**，表格 **925** |
| 家族稳定性口径 | 相邻文字写 58 个可比家族，图 6 标题写 60；待核具体筛选集合 |
| 会议定稿 | DetectBERT/ViT 等是否补充、数值是否更新：**待全文核验** |
| 图中精确数列 | 未获得可可靠转录的全部逐月/逐年点值：**待全文核验** |
| CL 完整评价矩阵 | 图 18—21 对应训练年×测试年矩阵：**待全文核验** |

前三项是可定位的在线全文冲突，而不是推测；不能自行选择更“合理”的数字替作者纠正。([arxiv.org](https://arxiv.org/html/2505.18551v1))

---

## 五、泄漏、标签时效与评估饱和审计

### 5.1 已证实的是“未来协变量进入预处理”，不是所有形式的泄漏

**【在线全文】**固定提交的 `vectorization_npz_creation.py` 汇集 **2013、2014、2016—2025 全部年份的训练分片**，构建词表并拟合 `VarianceThreshold`；测试分片仅执行 transform。fileciteturn8file0L2-L5

**【推论】**对于只在 2013—2014 训练、向未来预测的任务，这不是严格 source-only 预处理。应区分：

- **严格归纳式时间外推**：词表、特征选择及阈值均只能由历史数据确定。
- **全时期表示预处理**：允许未来未标注协变量参与表示构建，但须明确这一信息条件。

目前证据**没有证明**未来测试分片参与拟合，也没有证明未来标签被监督模型使用。将其笼统称为“测试标签泄漏”会超出证据。fileciteturn8file0L2-L5

### 5.2 重复与近重复：尚未得到实算结论

**【推论】**公开 hash 字段使精确重复审计可行，但本轮未计算跨年份、train/test、不同特征变体的哈希交集，也未计算 APK 重打包、同应用版本等近重复。HF 多配置汇总行数不能直接当作唯一 APK 数，更不能单凭行数认定发生重复泄漏。([huggingface.co](https://huggingface.co/datasets/IQSeC-Lab/LAMDA)) fileciteturn9file0L2-L5

### 5.3 标签阈值实验不等于噪声鲁棒性实验

**【在线全文】**表 11 是累计阈值 `VT≥k` 的样本统计；表 12 是**恰好 `VT=k`** 子集的结果。原始集合已经排除 VT=1—3，因此表 11 阈值 1—4 的计数相同，并不表明模型对不同噪声水平稳定。~~~~~~~~~~~~~~~~~~~~~~

**【推论】**改变 VT 阈值同时改变样本量、家族构成、恶意行为显著程度和类别先验，不是仅改变标签噪声。若没有控制这些因素，不能把性能变化单独归因于“噪声鲁棒性”。重新扫描也必须记录每条标签的可用时间；使用后来的标签重建历史训练任务，可能引入回溯性信息优势。([arxiv.org](https://arxiv.org/html/2505.18551v1))

### 5.4 家族筛选含未来测试集合条件

**【在线全文】**Class-IL 以测试集中样本数超过 10 等条件选出 154 个家族。([arxiv.org](https://arxiv.org/html/2505.18551v1))

**【推论】**这可以是合法的固定基准构造，但不等价于不知道未来家族目录的开放世界部署。研究新家族发现时，应单独设置“家族首次出现之前不可见”的协议，不能用已筛好的固定标签空间证明开放集能力。

### 5.5 天花板和饱和风险是局部的，不是全局的

**【在线全文】**2025 年只有 **23 个恶意样本、44,640 个良性样本**；2024 年也仅有 **794 个恶意样本**。定位：表 2。([arxiv.org](https://arxiv.org/html/2505.18551v1))

**【推论】**在 2025 全部样本上恒预测良性，Accuracy 就达到：

\[
\frac{44\,640}{44\,663}\approx 99.9485\%,
\]

但恶意类 Recall 为 0、FNR 为 100%。这是计数推导，不是模型实验；也不意味着测试分片恰有某个确定的恶意样本数。

**【推论】**因此存在准确率饱和、少数阳性导致召回率离散跳变、跨年平均掩盖高风险年份等问题；但 FAR F1 约 42%—48% 又说明**不能把整个 LAMDA 宣称为“已经接近性能天花板”**。更合理的目标是固定误报预算下的漏报、逐年风险和低样本置信区间。~~~~~~~~~~~~~~~~~~~~~~

---

## 六、2023—2026 文献及可核验的引用关系

### 6.1 直接近邻：完整题录与版本

下面的“直接近邻”包括同类 Android 时间漂移任务及明确讨论 LAMDA 的工作；**不等于都在 LAMDA 上做过实验**。

**R1｜【在线全文】Continuous Learning for Android Malware Detection**
**Yizheng Chen；Zhoujie Ding；David Wagner。**2023，**USENIX Security 2023**，1127–1144。
[会议记录](https://www.usenix.org/conference/usenixsecurity23/presentation/chen-yizheng)；[arXiv:2302.04332](https://arxiv.org/abs/2302.04332)；[官方仓库](https://github.com/wagner-group/active-learning)。它提供层次对比学习与主动标注的直接基线；并非无标签测试时适应。([arxiv.org](https://arxiv.org/html/2302.04332))

**R2｜【在线全文】Combating Concept Drift with Explanatory Detection and Adaptation for Android Malware Classification**
**Yiling He；Junchi Lei；Zhan Qin；Kui Ren；Chun Chen。**2025，**ACM CCS 2025**。
[DOI:10.1145/3719027.3744792](https://doi.org/10.1145/3719027.3744792)；[arXiv:2405.04095](https://arxiv.org/abs/2405.04095)；[官方 DREAM 仓库](https://github.com/E0HYL/DREAM-drift-adapt)。v1 为 2024-05-07，旧题名为 *Going Proactive and Explanatory Against Malware Concept Drift*；本轮核对 v3，日期 2025-05-24。方法含专家标签与解释修订反馈，不能归为纯无监督 TTA。([arxiv.org](https://arxiv.org/html/2405.04095v3))

**R3｜【在线全文】MADCAT: Combating Malware Detection Under Concept Drift with Test-Time Adaptation**
**Eunjin Roh；Yigitcan Kaya；Christopher Kruegel；Giovanni Vigna；Sanghyun Hong。**2025，预印本；正式发表场所未核准。
[arXiv:2505.18734v1](https://arxiv.org/abs/2505.18734v1)，2025-05-24。官方代码仓库未核准。
**关键边界：§4.2 主实验用真实标签平衡适应数据；§4.3 与附录 B.2 又报告了伪标签平衡方案。**必须同时交代，不能只引用前者否定全文，也不能只引用后者掩盖主实验的信息条件。该文在 API Graph 上实验，不是本轮已核验的 LAMDA 结果。MADCAT 已在你的 Zotero 中，此处仅建议核对版本和相关章节。([arxiv.org](https://arxiv.org/html/2505.18734v1))

**R4｜【在线全文；场所为仅题录】Regression-aware Continual Learning for Android Malware Detection**
**Daniele Ghiani；Daniele Angioni；Giorgio Piras；Angelo Sotgiu；Luca Minnei；Srishti Gupta；Maura Pintor；Fabio Roli；Battista Biggio。**
[arXiv:2507.18313](https://arxiv.org/abs/2507.18313)：v1 为 **2025-07-24**，v2 为 **2026-07-10**。v2 作者备注称已获 **IEEE TIFS** 接收；期刊 DOI 和正式卷期未核准，官方仓库未核准。全文关注更新后把旧的正确预测变成错误预测的 regression；这是“平均遗忘”之外的安全相关评价对象。([arxiv.org](https://arxiv.org/abs/2507.18313))

**R5｜【在线全文】CITADEL: A Semi-Supervised Active Learning Framework for Malware Detection Under Continuous Distribution Drift**
**Md Ahsanul Haque；Md Mahmuduzzaman Kamol；Ismail Hossain；Suresh Kumar Amalapuram；Vladik Kreinovich；Mohammad Saidur Rahman。**2025，预印本；正式发表场所未核准。
[arXiv:2511.11979v1](https://arxiv.org/abs/2511.11979v1)，2025-11-15；[官方仓库](https://github.com/IQSeC-Lab/CITADEL)。**它明确在 LAMDA 上报告带月度标注预算的结果。**Sider 返回的简化作者记录不完整，以上采用论文全文作者顺序。([arxiv.org](https://arxiv.org/html/2511.11979v1))

**R6｜【在线全文】Beyond the Tesseract: Trustworthy Dataset Curation for Sound Evaluations of Android Malware Classifiers**
**Theo Chow；Mario D’Onghia；Lorenz Linhardt；Zeliang Kan；Daniel Arp；Lorenzo Cavallaro；Fabio Pierazzi。**2026，**IEEE SaTML 2026**。
[arXiv:2506.23814](https://arxiv.org/abs/2506.23814)；[机构记录](https://discovery.ucl.ac.uk/id/eprint/10220473)；[官方仓库](https://github.com/s2labres/hypercube-ml)。v1 为 2025-06-30，旧题名 *Breaking Out from the Tesseract: Reassessing ML-based Malware Detection under Spatio-Temporal Drift*；v2 为 **2026-03-23**。
它是 **TESSERACT 的后续独立论文，不是本地已有 TESSERACT 的重复条目**。v2 讨论时间戳、时间选择、应用市场、VT 阈值和规模等数据构造因素，并明确评论 LAMDA。([arxiv.org](https://arxiv.org/html/2506.23814v2))

**R7｜【在线全文】DRMD: Deep Reinforcement Learning for Malware Detection under Concept Drift**
**Shae McFadden；Myles Foley；Mario D’Onghia；Chris Hicks；Vasilios Mavroudis；Nicola Paoletti；Fabio Pierazzi。**2026，**AAAI 40(2):854–862**。
[DOI:10.1609/aaai.v40i2.37053](https://doi.org/10.1609/aaai.v40i2.37053)；[arXiv:2508.18839](https://arxiv.org/abs/2508.18839)；[官方仓库](https://github.com/s2labres/DRMD)。本轮核对 v2，2025-11-14；正式记录发表于 2026-03-14。
正文把任务表述为 **one-step MDP/contextual bandit**；附录已有监督学习及 NeuralUCB/NeuralTS 对照。不能将它解释为已经证明长期、多步策略规划优于所有监督方法。([ojs.aaai.org](https://ojs.aaai.org/index.php/AAAI/article/view/37053))

**R8｜【在线全文】McNdroid: A Longitudinal Multimodal Benchmark for Robust Drift Detection in Android Malware**
**Md Mahmuduzzaman Kamol；Jesus Lopez；Saeefa Rubaiyet Nowmi；Emilia Rivas；Md Ahsanul Haque；Edward Raff；Aritran Piplai；Mohammad Saidur Rahman。**2026，预印本；正式发表场所未核准。
[arXiv:2605.06894v1](https://arxiv.org/abs/2605.06894v1)，2026-05-07；[官方仓库](https://github.com/IQSeC-Lab/McNdroid)。
§3.2 明确以 **2013 年训练数据**建立静态词表，这是与 LAMDA 全时期训练分片预处理的重要方法差别。它是另行构建的多模态集合，未计算哈希交集前，不能假定它就是 LAMDA 的同样本扩展。([arxiv.org](https://arxiv.org/html/2605.06894v1))

### 6.2 引用关系：只列已定位的边

下表每行均为 **【在线全文】证据**，含义是“已在引用方全文中找到引用”，不要求被引论文也已全文读完。

| 引用方 → 被引方 | 正文位置／参考文献编号 | 解释边界 |
|---|---|---|
| **LAMDA v1 → R1 Chen** | §1、§2、§4.1；**[17]** | 方法与比较背景 |
| **LAMDA v1 → Drift Forensics** | §1；**[18]** | 漂移分析近邻 |
| **R2 DREAM v3 → R1 Chen** | §2 及相关工作；**Chen et al., 2023a** | 主动学习与适应背景 |
| **R3 MADCAT v1 → R1 Chen** | §1、§2、§4.1；**Chen et al., 2023a** | 模型／适应基线 |
| **R3 MADCAT v1 → Is It Overkill?** | §2；**Chen et al., 2023b** | 不要与上一条 Chen 2023a 混淆 |
| **R5 CITADEL v1 → LAMDA** | §V-A；**[15]** | 明确使用 LAMDA |
| **R5 CITADEL v1 → R1 Chen** | §II、§V-D、表 IV；**[11]** | 主动学习比较 |
| **R6 Beyond v2 → LAMDA** | §XI；**[40]** | 正文误拼为 “LAMBDA”，但参考文献指向正确题名 |
| **R4 Regression-aware v2 → LAMDA** | §III-A；**[21]** | 引用数据集；不等于该文在 LAMDA 上实验 |
| **R4 Regression-aware v2 → Temporal-Incremental Learning** | §III-A、§VI；**[22]** | 持续学习近邻 |
| **R7 DRMD v2 → R1 Chen；Beyond v1** | §1／§5；**Chen et al., 2023；Chow et al., 2025** | 引用的是 Beyond 的早期版本 |
| **R8 McNdroid v1 → LAMDA** | §1、§3.1—3.2；**[32]** | 数据集构造与比较 |
| **R8 McNdroid v1 → R1 Chen；Beyond v1** | §7 **[17]**；§1 **[19]** | 分别是适应方法和数据评估背景 |

上述边来自各引用方全文的正文与参考文献，不是依据年份推断。([arxiv.org](https://arxiv.org/html/2505.18551v1))

**【在线全文→推论】版本特别重要：**Regression-aware 的 LAMDA 引用出现在本轮读到的 **2026 年 v2**；Beyond 对 LAMDA 的评论也在 **v2** 中核到。其 v1 本轮未检出相同引用，不能把 v2 的引用边回填到 v1。([arxiv.org](https://arxiv.org/html/2507.18313v1))

**【未证】**MADCAT↔LAMDA、DRMD→LAMDA，以及 RWKV/mHC→LAMDA 的直接引用或实验证据，本轮未检出。时间接近、研究主题相同、作者重叠都不能替代引用证据。这个引用图是经核验的子图，不是宣称完整的被引数据库导出。

### 6.3 未取得全文的近邻：单列，不据摘要采纳结论

**R9｜【仅题录】Drift Forensics of Malware Classifiers**
**Theo Chow；Zeliang Kan；Lorenz Linhardt；Lorenzo Cavallaro；Daniel Arp；Fabio Pierazzi。**2023，**AISec@CCS**，197–207。
[DOI:10.1145/3605764.3623918](https://doi.org/10.1145/3605764.3623918)；[会议目录](https://www.sigsac.org/ccs/CCS2023/tocs/tocs-aisec23.html)；[机构记录](https://discovery.ucl.ac.uk/id/eprint/10182372/)。
部分题录对 Cavallaro/Arp 顺序存在差异；这里采用会议目录顺序。官方仓库未核准；不据摘要转述其方法结论。([sigsac.org](https://www.sigsac.org/ccs/CCS2023/tocs/tocs-aisec23.html))

**R10｜【仅题录】Is It Overkill? Analyzing Feature-Space Concept Drift in Malware Detectors**
**Zhi Chen；Zhenning Zhang；Zeliang Kan；Limin Yang；Jacopo Cortellazzi；Feargus Pendlebury；Fabio Pierazzi；Lorenzo Cavallaro；Gang Wang。**2023，**IEEE S&P Workshops**，21–28。
[DOI:10.1109/SPW59333.2023.00007](https://doi.org/10.1109/SPW59333.2023.00007)；[作者公开出版目录](https://fabio.pierazzi.com/publications/)。官方仓库未核准；其“特征漂移是否导致决策退化”等具体结论需全文复核。([arxiv.org](https://arxiv.org/html/2505.18734v1))

**R11｜【仅题录】Temporal-Incremental Learning for Android Malware Detection**
**Tiezhu Sun；Nadia Daoudi；Weiguo Pian；Kisub Kim；Kevin Allix；Tegawendé F. Bissyandé；Jacques Klein。**2025，**ACM TOSEM 34(4)，Article 101，1–30**。
[DOI:10.1145/3702990](https://doi.org/10.1145/3702990)；[机构记录](https://orbilu.uni.lu/handle/10993/62892)。部分记录显示 2024 年在线发表，2025 年卷期；FSE Journal First 展示不应另算一篇新论文。官方仓库未核准，本轮不采纳未读全文的效果结论。([orbilu.uni.lu](https://orbilu.uni.lu/handle/10993/62892))

---

## 七、RWKV 与 mHC：来源机制，而非现成的 LAMDA 结论

### 7.1 RWKV

**【在线全文】RWKV: Reinventing RNNs for the Transformer Era**，**Findings of EMNLP 2023**，14048–14077。
[正式出版记录与 DOI](https://aclanthology.org/2023.findings-emnlp.936/)；[arXiv:2305.13048](https://arxiv.org/abs/2305.13048)；[官方仓库](https://github.com/BlinkDL/RWKV-LM)。

正式 ACL 版作者顺序：

Bo Peng；Eric Alcaide；Quentin Anthony；Alon Albalak；Samuel Arcadinho；Stella Biderman；Huanqi Cao；Xin Cheng；Michael Chung；Leon Derczynski；Xingjian Du；Matteo Grella；Kranthi Gv；Xuzheng He；Haowen Hou；Przemyslaw Kazienko；Jan Kocon；Jiaming Kong；Bartłomiej Koptyra；Hayden Lau；Jiaju Lin；Krishna Sri Ipsit Mantri；Ferdinand Mom；Atsushi Saito；Guangyu Song；Xiangru Tang；Johan Wind；Stanisław Woźniak；Zhenyuan Zhang；Qinghua Zhou；Jian Zhu；Rui-Jie Zhu。

后续 arXiv 作者记录存在变化，不能与正式 ACL 版作者串混合。([aclanthology.org](https://aclanthology.org/2023.findings-emnlp.936/))

**【在线全文】**§3.1 与附录 D 的核心是 time-mixing、channel-mixing、receptance 门控及带时间衰减的递推聚合。递推状态提供序列记忆，**不等于参数已经完成持续学习**。([arxiv.org](https://arxiv.org/html/2305.13048))

**【推论】**LAMDA 发布的静态特征列没有自然执行顺序。把列按编号输入 RWKV，不能仅凭“模型有时间记忆”就声称利用了恶意软件长期漂移。更可检验的输入是因果可用的月度统计序列，或另行核准的真实 API 顺序数据。

### 7.2 mHC

**【在线全文】mHC: Manifold-Constrained Hyper-Connections**
**Zhenda Xie；Yixuan Wei；Huanqi Cao；Chenggang Zhao；Chengqi Deng；Jiashi Li；Damai Dai；Huazuo Gao；Jiang Chang；Kuai Yu；Liang Zhao；Shangyan Zhou；Zhean Xu；Zhengyan Zhang；Wangding Zeng；Shengding Hu；Yuqing Wang；Jingyang Yuan；Lean Wang；Wenfeng Liang。**

2025/2026，预印本；正式发表场所和官方代码仓库未核准。
[arXiv:2512.24880](https://arxiv.org/abs/2512.24880)；[DOI](https://doi.org/10.48550/arXiv.2512.24880)。v1 为 2025-12-31，v2 为 **2026-01-05**。([arxiv.org](https://arxiv.org/html/2512.24880v2))

**【在线全文】**§4.2 的 manifold constraint 约束的是残差流混合矩阵，通过 Sinkhorn-Knopp 等处理接近非负、行列和均为 1 的双随机结构。**它不是对 Android 输入特征的语义流形约束，也不是时间漂移鲁棒性定理。**([arxiv.org](https://arxiv.org/html/2512.24880v2))

---

## 八、可证伪的任务化算法方向

以下全部为 **【推论／研究设计】**，本轮没有运行任何真实实验，不声称有效。

### 8.1 先固定三个不同的信息条件

| 任务 | 允许观察 | 不应混入 |
|---|---|---|
| 静态域泛化／时间外推 | 历史特征、历史标签、历史校准集 | 未来协变量拟合词表、未来标签调阈值 |
| 测试时适应 | 已到达的未标注样本及过去状态 | 真实测试标签平衡数据、未来月份统计 |
| 持续／主动学习 | 按预算和延迟到达的标签、历史回放 | 无成本即时全标签、事后家族目录选择 |

**【推论】**TTA 还需明确“先适应再预测当前批次”还是“先预测再更新”的 prequential 协议；两者不能混作同一资源条件。

共同评价应包含逐月/逐年 F1、AP、固定历史阈值下的 FPR/FNR、最差年份、旧恶意样本负向翻转率、标注预算、计算量及延迟。离线画 ROC 后获得的 `TPR@FPR`，应与部署中仅由历史校准集确定阈值的实际表现分开。种子不确定性、跨年份变化和少数阳性计数不确定性也应分别报告。

### 8.2 八个方向的前提、对照与失败门

| 方向 | 适用前提与可观测量 | 必须有的对照与指标 | 失败门 |
|---|---|---|---|
| **静态域泛化** | 多个历史年月环境；只用历史数据拟合特征。观察类条件特征频率、分组 FP/FN | ERM、Group DRO/CVaR、固定重加权；另设全时期表示诊断组。比较最差年份 FNR 与误报约束 | 换成 source-only 预处理后优势消失；或仅靠提高 FPR 换召回 |
| **持续学习** | 明确标签延迟、回放容量。观察旧恶意样本从正确到错误的负向翻转、逐任务矩阵 | Naive、等容量 Replay、Cumulative/Joint、regression-aware 对照；FNR、负向翻转、遗忘、成本 | 平均 F1 上升但旧恶意样本漏报恶化；或需要未来测试家族筛选 |
| **噪声鲁棒训练** | VT 是弱标签线索而非人工真值；VT count 不作为部署分类输入 | 普通交叉熵、排除不确定样本、鲁棒损失；匹配样本量、家族和类别比例；人工噪声仅作辅助 | “有效”仅来自丢弃困难家族，或只在 IID／人工翻转噪声上成立 |
| **RWKV 机制迁移** | 有真实顺序，或因果可用的月度特征／误差统计；延迟标签只能在到达后进入状态 | EWMA、GRU、MLP、集合模型；列置乱、状态重置消融；检测延迟、误警、下游 FNR、计算量 | 任意特征列排序决定优势；读取未来误差；不优于简单状态模型 |
| **mHC** | 同一骨干和输入表示，只改变残差流连接；观察梯度、混合矩阵约束误差 | 普通残差、HC、mHC，匹配参数/FLOPs；训练稳定性与 FAR 风险分别比较 | 收益完全由增加容量解释；训练更稳却没有时间外推收益 |
| **课程学习** | 难度仅由历史损失、历史置信度或已知家族信息确定 | 随机顺序、静态重加权、易到难／难到易、主动学习；新家族与罕见家族召回 | 把低 VT／新家族持续压低权重，造成关键样本长期学不到；只有 IID 收益 |
| **强化学习** | 定义放行、告警、拒判／查询动作及代价、标签延迟；存在真实预算约束 | 成本敏感监督学习、拒判模型、上下文 bandit；这些基线在 DRMD 已有先例。比较预算下风险与延迟 | 需要每步即时真实奖励；或不优于同预算监督／bandit，而仅换了算法名称 |
| **博弈／鲁棒优化** | 对手只能重加权历史环境、类条件风险或合理不确定集合 | ERM、固定重加权、Group DRO、CVaR；最差年份 FNR、FPR 约束及资源成本 | 对手集合由目标年标签拟合；或不可实现的特征扰动被宣称为真实 APK 鲁棒性 |

**【在线全文→推论】课程学习不是空白名词。**CITADEL 附录 E、表 XI 已比较课程方案，但对象是 **API Graph，而非 LAMDA**。不能将那组结果推广为“课程学习普遍无效”，也不能把“在恶意软件漂移中加入课程学习”本身当作未经研究的新颖性。([arxiv.org](https://arxiv.org/html/2511.11979v1))

**【在线全文→推论】强化学习也不能仅做名称替换。**DRMD 已有 one-step MDP、监督对照及神经 bandit 对照。更具体的增量应是可观测的延迟反馈、查询预算或非对称风险机制，而不是将二分类损失换成奖励后声称产生了长期规划能力。([arxiv.org](https://arxiv.org/html/2508.18839v2))

---

## 九、优先级、研究空白与最小验证

### 9.1 按优先级排序的全文精读清单

| 优先级 | 材料 | 必须解决的问题 |
|---|---|---|
| **P0** | LAMDA v1、ICLR 接收版及固定提交代码 | 定稿差异、表 1/8 冲突、特征阈值、真实切分、原始特征制品 |
| **P1** | Beyond the Tesseract v2；Regression-aware CL v2 | 数据构造偏差；平均遗忘之外的安全负向翻转 |
| **P2** | Chen 2023；CITADEL v1 | 标注预算、选择偏差、月度适应及强基线 |
| **P3** | McNdroid v1；DREAM v3 | source-only 表示、多模态筛选偏差、专家反馈条件 |
| **P4** | 本地已有 MADCAT 的 §4.2、§4.3、附录 B.2；DRMD v2 | 无标签条件是否真实；成本和反馈是否可部署 |
| **P5** | TIML、Drift Forensics、Is It Overkill? 全文 | 补齐本轮尚未取得的直接近邻证据 |
| **P6** | RWKV 原论文；mHC v2 | 只在任务和基线明确后检验机制迁移，不先承诺架构收益 |

这是一份 **【推论】研究排序**。本地已有的 MADCAT、TESSERACT 不重复推荐导入；**Beyond the Tesseract 是独立后续论文**。

### 9.2 当前可成立的研究空白

**【推论】第一，严格时间因果的表示构建。**在同一批样本、同一监督器、同一评估协议下，隔离“全时期训练分片预处理”与“仅历史预处理”的差别，是比先堆叠新架构更基础的可证伪问题。

**【推论】第二，非对称安全风险下的有限预算适应。**平均 F1、平均遗忘和旧恶意样本负向翻转并不是同一个目标。值得检验的是：固定误报及标注预算时，能否减少关键恶意样本的更新后漏报。

**【推论】第三，时间戳和标签的双重可用性。**样本什么时候进入系统、标签什么时候成熟，应分别进入实验协议；否则可能同时把入库偏差和事后重标注当作模型适应能力。

**【推论】第四，低恶意率末期的稳健评价。**2024—2025 的小阳性计数需要单独审计，不能依靠高 Accuracy 或跨年平均掩盖不确定性。这里的空白是可靠的任务与估计，而不只是再提高一个汇总分数。

### 9.3 最小下一步验证

**【推论】先做一个范围有限、可明确失败的验证，而不是同时组合八类方法：**

1. **冻结与审计。**绑定论文版本、代码提交和实际数据文件 revision；记录逐文件 SHA-256、schema、逐年标签数与跨分片哈希交集。先确认阈值前原始特征是否真正可用；不可用时，不宣称完成 source-only 重建。
2. **只复现 LightGBM 与 MLP。**分别采用官方预处理和仅历史预处理，保持样本、监督参数及历史校准阈值一致，输出逐年混淆矩阵，并解决表格与代码差异。
3. **只加入一种任务机制。**优先比较“固定容量回放”与“回放＋旧恶意样本负向翻转约束”，明确标注延迟和预算，使用滚动时间起点评价；若 FPR 超限、关键年份漏报恶化，或优势依赖未来信息，即判定失败。

**最终结论：LAMDA 是已经核准的公开长期 Android 漂移基准，但当前证据不支持把“ICLR 定稿、arXiv v1、最新代码、HF 全部变体”视为一份完全一致、已复现的实验对象。**本轮交付的是绑定来源和版本的外部候选：身份、v1 表格及若干关键代码行为已有直接证据；会议定稿修订链、完整逐文件校验、重复样本实算、部分近邻全文和任何新算法效果仍未完成核验。后续最值得先验证的不是“哪种复杂架构更强”，而是**时间上允许知道什么，以及在同一信息预算下究竟减少了哪一种错误**。
