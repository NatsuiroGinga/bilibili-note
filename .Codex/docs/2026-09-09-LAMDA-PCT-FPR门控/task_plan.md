# LAMDA PCT 与 FPR gate 筛选实施计划

> **给工程代理：** 运行前阅读本计划；本任务只作来源／项目开发层 `screening_only`，不得读取封印年。

**目标：** 在同一 LAMDA MLP 和 Replay 合同下，检验 PCT/Focal Distillation 是否能在恶意漏判修复的同时降低安全回归，并用历史良性 gate 检查 FPR 是否增加。

**候选：** 四臂为 ER、ER＋PCT、ER＋缺口修复、ER＋缺口修复＋PCT。缺口修复沿用已核验的 margin 缺口定义；PCT 使用论文公式（7）的 FD-LM 形式，alpha=1、beta=5、lambda=1 作为有直接论文依据的初始筛选值。

## 全局约束

- 数据版本固定为 `IQSeC-Lab/LAMDA` revision `ad9614bdd5556767f97ced2fce797c2f06408ebf`。
- 只枚举来源年 `2013/2014` 和项目开发层 `2016/2017`；封印年 `2018--2025` 不读取。
- 发布 `4561` 维特征空间含未来协变量，运行身份必须为 `screening_only`。
- 固定种子 `42`、每年 `10` 轮、批量 `1024`、既有 SGD、阈值 `0.5`、总回放容量 `200`。
- PCT 只用上一冻结模型输出与当前／历史已到达标签；缺口修复只用当前年度真实恶意标签。
- FPR gate 只用历史年度测试集的良性样本作筛选诊断，不参与当前年度训练；最终正式运行仍需独立时间一致 gate。

## 实现文件

- 新建：`thesis/experiments/llm_probe/tools/ch3_lamda_pct_screening.py`
- 新建：`thesis/experiments/llm_probe/configs/ch3-lamda-pct-fpr-screening-v1.json`
- 输出：`runs/diagnostics/ch3-lamda-pct-fpr-screening-seed42-v1/`

## 训练目标

缺口修复项：

\[
L_{FN}=\frac{\sum_{i\in R_t}[a-z^-_i]_+\,\operatorname{BCE}(p_i,1)}{\sum_{i\in R_t}[a-z^-_i]_+}.
\]

PCT FD-LM 项：

\[
L_{FD}=\frac{1}{\sum_i w_i}\sum_i w_i\frac{1}{2}(z_i-z^-_i)^2,
\qquad
w_i=\alpha+\beta\mathbf 1(\hat y^-_i=y_i).
\]

联合臂使用 `L_cur + L_replay + L_FN + L_FD`；单臂分别关闭另一项。

## 评价与停止门

- 每年和 pooled 开发层报告 AP、AUROC、F1、FPR、FNR、Brier、恶意正向修复、旧恶意负向翻转和良性新增误报。
- 历史良性 gate 记录更新前后 FPR；候选只有在 gate FPR 不增加时才有资格继续。
- 相对 ER，FNR 必须下降，旧恶意负向翻转不得增加；联合臂必须不劣于两个单臂。
- PCT 只降低 NFR 而不修复恶意，或与阈值匹配无差异，均降级为直接基线。
- 任一 arm 使用未来标签、当前测试反馈训练、重新调阈值或改写数据合同，运行作废。

## 执行顺序

1. 完成代码入口检查与配置校验。
2. 服务器运行唯一筛选身份并回传摘要、逐年指标、预测和资源收据。
3. 主代理独立复算 pooled 与配对翻转。
4. 只有至少一个候选通过安全和修复门，才设计正式 FPR gate 与封印评价；否则保留 ER，停止扩展。

## 状态

本机预筛已完成；PCT、Cotter 和 Kumar 原件已下载并完成 MinerU 解析，入口与配置通过本地检查。预筛身份 `ch3-lamda-pct-fpr-screening-mps-seed42-v1` 实际运行设备为 CPU（本轮 `mps_available=false`），四臂均完成来源年 `2013/2014` 与项目开发层 `2016/2017` 的筛查，封印年未读取。资源收据记录续跑墙钟 `629.0021` 秒；因使用 `--resume`，该数值不是空目录全量重跑墙钟。

- 本机结果仅用于候选筛选；服务器 CUDA 只在候选通过开发期门槛且独立分析完成后做最终确认和正式制品。四臂结果及逐样本预测已落盘，待主代理独立分析后裁决，不重复缺口修复实验。

## 错误记录

- 2026-09-09：服务器关机后再次推送返回 SSH `255`；DoH 解析确认域名真实地址，但服务端主动断开。该事件是远程资源状态问题，不是 PCT 代码或实验失败；服务器恢复后需重新解析短 TTL 地址再连接。
