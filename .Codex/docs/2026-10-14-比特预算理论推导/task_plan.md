# 比特预算理论推导——任务计划

- 日期：2026-10-14
- 任务来源：主代理派发（对标朱焱雷第三章 3.5 节四个理论小节形态，产出本框架的数学推导＋可实测预测）
- 边界：不下选题裁决、不实现算法、不改仓库既有源码、禁止本机训练（允许读数据、算统计量）

## 文件所有权

- 本目录 `task_plan.md`、`notes.md`、`report.md` 仅本任务写入。
- 只读引用：`wiki/papers/attack-detection/lamda-related/2026-Asadi-FreeMOCA-Memory-Free-Continual-Malicious-Code-全文.md`、`wiki/papers/attack-detection/2019-Chaudhry-AGEM高效终身学习.md`、`thesis/experiments/llm_probe/runs/diagnostics/ch3-lamda-domain-il-e4-replication-v1/` 下制品、`thesis/experiments/llm_probe/domain_il_experiment.py`。

## 四个小节（按优先级）

1. S1 比特预算最优分配（KKT/等价最优性条件；全给一侧的充分条件）——**最有理论分量**
2. S2 有限比特下历史分布覆盖界（与 N, B, t, d 相关）
3. S3 插值路径低损失条件（借鉴 FreeMOCA §3.2–3.4 LMC 论证，本设定：二值稀疏特征 + warm-start）
4. S4 插值权重规则（逐层参数位移导出 λ_ℓ）的稳定性/最优性

## 验收标准

- 每个定理/引理标注：假设、结论、推导状态（已证/部分/猜想）、依据出处（文件名＋行号）。
- 常数全部来自任务简报第二节的实测表或本地文献，不臆造。
- 每个小节配一条可实测预测：改变 X 时 Y 应单调，写明测法、成本、证伪条件。
- 能用一条命令验证的判断先跑（本机允许：读 metrics JSON、算统计量；禁止训练）。

## 状态

- [x] 任务目录建立
- [ ] 读 FreeMOCA 全文（§3.2/§3.3/§3.4 + Algorithm 1 行 85–102）
- [ ] 读 A-GEM / EWC 类参数保持笔记
- [ ] 实测数据复核（E4 曲线 JSON）
- [ ] S1 推导落盘 notes.md
- [ ] S2 推导落盘
- [ ] S3 推导落盘
- [ ] S4 推导落盘
- [ ] report.md 汇总
