# LAMDA 官方公开制品核验记录

日期：2026-09-08。此文件是只读核验记录，不含原始 PDF、APK、模型权重或运行日志。

## 版本锚点

| 制品 | 本轮固定标识 | 时间/状态 | 证据 |
|---|---|---|---|
| 论文 | arXiv:2505.18551v1 | 2025-05-24 06:36:39 UTC | [arXiv 版本记录](https://arxiv.org/abs/2505.18551v1) |
| 会议 | OpenReview forum 1FnCrZtBNQ | ICLR 2026 Poster 已由会议官网核准；论坛修订链未取得 | [会议记录](https://iclr.cc/virtual/2026/poster/10011850)；[论坛](https://openreview.net/forum?id=1FnCrZtBNQ) |
| GitHub 代码 | 7728bfafcd5539a286b5f8c47b6f1e3b2d1f4249 | 2026-03-28T21:43:02Z | [固定提交](https://github.com/IQSeC-Lab/LAMDA/commit/7728bfafcd5539a286b5f8c47b6f1e3b2d1f4249) |
| GitHub tree | e3e2877b5f8c5bbeeca272f18c62751d02104432 | recursive tree 返回 truncated=false | 公开 GitHub API，已通过 GitHub 应用读取 |
| Hugging Face | ad9614bdd5556767f97ced2fce797c2f06408ebf | 仓库更新日期2026-02-14（Hugging Face应用元数据）；精确UTC未核准 | [提交记录](https://huggingface.co/datasets/IQSeC-Lab/LAMDA/commit/ad9614bdd5556767f97ced2fce797c2f06408ebf) |
| 数据 DOI | 10.57967/hf/5563 | DOI不是逐文件内容校验值 | [数据 DOI](https://doi.org/10.57967/hf/5563) |

以上哈希作为稳定引用。HF下列浏览清单来自本轮可访问的main页面；没有完成每个叶子文件与固定revision的逐项对应验证，不能称为完整的冻结版密码学清单。

## 官方身份与许可证

[IQSeC-Lab/LAMDA GitHub](https://github.com/IQSeC-Lab/LAMDA) 与 [Hugging Face](https://huggingface.co/datasets/IQSeC-Lab/LAMDA) 互链；GitHub公开属性已由应用核验。仅访问公开官方仓库。

证据等级：在线全文（官方数据卡/代码），或仅题录（仓库元数据）。HF数据卡声明MIT；固定GitHub根目录/递归树没有定位独立LICENSE。不能将HF声明无条件延伸至代码、AndroZoo原APK或第三方依赖。论文v1为CC BY 4.0；项目网页页脚的CC BY-SA 4.0另属网站内容。

## GitHub已核根目录

`.gitignore`、`README.md`、`code/`、`index.html`、`metadata.csv.gz`、`static/`。

`metadata.csv.gz`：49,047,738字节；Git blob SHA-1 `f6762b2ab4589d782f0abd70a9abc231d95de1a3`。Git blob SHA-1不是文件原始字节SHA-256。

重点代码（均绑定上面的固定提交）：

- `code/section_3_LAMDA_creation/LAMDA_get_train_test.py`
- `code/section_3_LAMDA_creation/vectorization_npz_creation.py`
- `code/section_4_concept_drift_analysis/anoshift_experiment_models_separate.py`
- `code/section_4_concept_drift_analysis/4_1_anoshift_script_LAMDA.sh`
- `code/Supplementary_material/continual_learning/domain_il_experiment.py`
- `code/Supplementary_material/continual_learning/class_il_experiment.py`
- `code/Supplementary_material/continual_learning/run-experiments.sh`

## Hugging Face已核目录结构

[公开根目录](https://huggingface.co/datasets/IQSeC-Lab/LAMDA/tree/main)：

```text
Baseline/
NPZ_Version/
var_thresh_0.0001/
var_thresh_0.01/
.DS_Store
.gitattributes
.gitignore
README.md
metadata.csv
```

`Baseline/`的年度目录：2013、2014、2016、2017、2018、2019、2020、2021、2022、2023、2024、2025。示例叶子已核验：`Baseline/2013/2013_train.parquet`和`Baseline/2013/2013_test.parquet`。未逐一枚举所有Parquet变体下的全部叶子，不能把命名规则视为完整下载清单。

`NPZ_Version/`下已核到：`npz_Baseline/`、`npz_var_thresh_0.0001/`、`npz_var_thresh_0.01/`。

[NPZ Baseline公开目录](https://huggingface.co/datasets/IQSeC-Lab/LAMDA/tree/main/NPZ_Version/npz_Baseline)中以下50个条目已在目录页核对；其余两个NPZ变体未逐叶子完成同等级枚举。

```text
2013_X_train.npz
2013_X_test.npz
2013_meta_train.npz
2013_meta_test.npz
2014_X_train.npz
2014_X_test.npz
2014_meta_train.npz
2014_meta_test.npz
2016_X_train.npz
2016_X_test.npz
2016_meta_train.npz
2016_meta_test.npz
2017_X_train.npz
2017_X_test.npz
2017_meta_train.npz
2017_meta_test.npz
2018_X_train.npz
2018_X_test.npz
2018_meta_train.npz
2018_meta_test.npz
2019_X_train.npz
2019_X_test.npz
2019_meta_train.npz
2019_meta_test.npz
2020_X_train.npz
2020_X_test.npz
2020_meta_train.npz
2020_meta_test.npz
2021_X_train.npz
2021_X_test.npz
2021_meta_train.npz
2021_meta_test.npz
2022_X_train.npz
2022_X_test.npz
2022_meta_train.npz
2022_meta_test.npz
2023_X_train.npz
2023_X_test.npz
2023_meta_train.npz
2023_meta_test.npz
2024_X_train.npz
2024_X_test.npz
2024_meta_train.npz
2024_meta_test.npz
2025_X_train.npz
2025_X_test.npz
2025_meta_train.npz
2025_meta_test.npz
vocabulary.txt
vocabulary_selected.txt
```

## 公开远端校验值示例

证据等级：在线全文（HF文件指针页）。来源：[Baseline/2013/2013_test.parquet](https://huggingface.co/datasets/IQSeC-Lab/LAMDA/blob/main/Baseline/2013/2013_test.parquet)。

```text
path: Baseline/2013/2013_test.parquet
size_display: 5.04 MB
sha256: 208528e70c2c71c3765c4749d0293cd2816ca316dce60ef6eef42899d5aca323
xet_hash: 8765a74b84d8c53bbd9fb7bdca7d3f284a57a5b0ab0ca0f76e063cbc2b83e6fb
```

这只是远端声明，不是本轮对实际下载字节重新计算的校验结果。所有文件的SHA-256/大小、原始字节复算和完整冻结清单：未完成。不要把Xet hash、Git blob SHA-1与原始文件SHA-256混为一谈。

## 需要独立复核的制品缺口

论文附录G称发布阈值前原始矩阵与序列化VarianceThreshold对象；本轮已核目录没有定位到对应完整raw矩阵和selector.joblib，不能仅凭“代码可以生成”判定制品已经公开。全部词表文本不等于逐APK原始特征矩阵；已经全时期筛过的4561/25460维数据，也不能完整恢复当年源数据专用筛选。

Hugging Face界面的多配置汇总行数不能直接当作唯一APK数。应对不同配置、train/test、年份分别读取schema和hash字段，并计算唯一哈希数及交集；本轮没有做该项数据实算。

## 建议的最小冻结字段（推论）

为每个实际用于实验的文件记录：repo、revision、relative_path、byte_size、remote_oid、local_sha256、schema_hash、row_count、unique_apk_hash_count、min/max_timestamp、label_counts、feature_dimension。另记录论文版本、代码提交、feature-selector拟合时间上界和类别词表可用时间。未取得的值应保持null/待核，不从文件名或README猜测。
