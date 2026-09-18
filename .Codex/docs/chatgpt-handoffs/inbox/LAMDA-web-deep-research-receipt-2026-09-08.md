# LAMDA 普通 ChatGPT 网页研究回收收据

## 执行事实

- 对话：https://chatgpt.com/c/6a9f912e-4abc-83ea-b7ba-3aa85cc61d6a
- 内部 WEB 标识：`96d34057-2cdd-4d89-b8d3-9773d7a1c827`
- 启动界面：普通 ChatGPT 的“聊天”而非“工作”。
- 选择状态：输入框显示“深度研究”，并显式选择 Sider Scholar 与 GitHub。
- 完成状态：完成，界面显示“思考了 33m 14s”。
- 模型：界面模型按钮显示 `6 Pro`；主报告自报 `actual_model: GPT-6 Astra Pro`。两者按原样同时保留，不自行归并名称。
- 思考强度：主报告声明界面没有可独立核验的 effort 档位；requested `high` 不能冒充 actual effort。
- 模式边界：任务确实经“深度研究”入口发送；主报告同时声明“未取得独立 Deep Research 作业状态”。因此只能确认普通 ChatGPT 内进行了 33 分钟多轮研究，不能声称取得可独立审计的后端作业 ID。
- 实际应用：Sider Scholar、GitHub、Hugging Face；GitHub 只访问公开官方仓库。

## 回收制品

- `LAMDA_v1_numeric_ledger_2026-09-08.md`：网页模型生成的逐表数字账本，原样下载。
- `LAMDA_artifact_manifest_2026-09-08.md`：网页模型生成的公开制品清单，原样下载。
- 主回复：旧对话实际已生成 `LAMDA-2026-external-deep-research-raw.md` 附件；2026-09-08 复查后已原样回收到 inbox。
- 主回复制品：`443` 行、`40963` 字节，SHA-256 为 `56c2c6abcf0831c39215fb1b6f55daee9077edd42483b5f04818582ce274031a`；与浏览器下载件逐字节一致。

## 独立复核结果

已由本地全文、官方代码和 API 接受：

- LAMDA 身份、ICLR 2026 Poster、arXiv v1、HF/GitHub 固定修订。
- 全时期训练分片参与词表和方差筛选，属于未来无标签协变量预处理，不是已证测试标签泄漏。
- `0.001/0.0001` 阈值与目录/代码不一致。
- 表 11 与表 12 的 VT 干预口径不同。
- Class-IL 按测试集家族支持度筛 154 类。
- `average_precision_score` 被论文列名写为 PR-AUC。
- 持续学习启动器重复三次但不传 run seed。

已修正网页输出：

- 网页把 Drift Forensics 列为仅题录；本地随后取得作者公开 PDF、完成 MinerU 全文转换并入库，证据已升级为全文。
- 网页指出 OpenReview 定稿未逐页取得；本地直连也返回 403，故仍保持待核，不把 arXiv v1 数字冒充会议终稿。

未采纳为结论：

- 任何 RWKV、mHC、课程学习、强化学习或博弈机制的有效性。
- 未实际计算的重复/近重复率、逐年置信区间和新算法效果。
