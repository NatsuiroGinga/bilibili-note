---
title: "外部资源索引"
date: 2026-08-08
verified_on: 2026-08-08
tags:
  - 索引
  - 外部资源
---

# 外部资源索引

本目录登记被本课题调研引用的**非论文外部资源**（模型权重、代码仓库、基准、综述）。论文笔记仍在 `wiki/papers/<方向>/`。
所有条目均于 **2026-08-08** 通过 Hugging Face 元数据接口、GitHub API/raw 文件或 Crossref API 实际核验；未核实项在各笔记内显式标注为「待验证」。

## 一、模型权重（Hugging Face）

| 资源 | 参数量 | 许可证 | 最后更新 | 下载量 | 笔记 |
| --- | --- | --- | --- | --- | --- |
| snlucsb/netFound-small | 53.4M | MIT | 2026-03-09 | 128 | [[netFound-small-权重]] |
| snlucsb/netFound-base | 174.7M | MIT | 2026-03-09 | 49 | [[netFound-base-权重]] |
| snlucsb/netFound-large | 662.2M | MIT | 2026-03-09 | 46 | [[netFound-large-权重]] |
| snlucsb/netFound-640M-base | 元数据 711.8M / 模型卡 643,825,672（口径不一致） | 无声明 | 2026-04-27 | 460 | [[netFound-640M-base-权重]] |
| wangtz/NetMamba | 未标（`pre-train.pth` 26.19MB） | 无声明 | 2024-08-13 | 未显示 | [[NetMamba-权重]] |
| fla-hub/rwkv7-1.5B-world | 1527.4M | Apache-2.0 | 2025-05-07 | 13.1K | [[rwkv7-1.5B-world-权重]] |
| RWKV/v6-Finch-1B6-HF | 未标 | Apache-2.0 | 2024-09-03 | 12.7K | [[v6-Finch-1B6-HF-权重]] |
| Qwen/Qwen2.5-0.5B | 494.0M | Apache-2.0 | 2024-09-25 | 27.2M | [[Qwen2.5-0.5B-权重]] |
| rdpahalavan/bert-network-packet-flow-header-payload | 未标（DistilBERT 约 66M，推论） | Apache-2.0 | 2023-07-22 | 15.1K | [[bert-network-packet-flow-header-payload-权重]] |

**选型提示**：只有 netFound-small/base/large、rwkv7-1.5B-world、v6-Finch-1B6-HF、Qwen2.5-0.5B 六个权重有明确开源许可证；netFound-640M-base 与 NetMamba 无许可证声明，衍生发布有法律风险。rdpahalavan 那个是已微调分类器，不是基座。

## 二、代码仓库（GitHub）

| 仓库 | 许可证 | 最后提交 | Stars | 依赖钉死 | 权重分发 | 笔记 |
| --- | --- | --- | --- | --- | --- | --- |
| SNL-UCSB/netFound | MIT | 2026-05-15 | 40 | 未声明 | HF + Zenodo(16GB) + 自建服务器(1.2TB) | [[netFound-代码仓库]] |
| wangtz19/NetMamba | 无 | 2026-04-05 | 179 | torch 2.1.1+cu121、py3.10.13、causal-conv1d 1.1.0、mamba 1.1.1 | HF + Google Drive(数据) | [[NetMamba-代码仓库]] |
| linwhitehat/ET-BERT | MIT | 2026-07-23 | 669 | torch>=1.1、CUDA 11.4 | Google Drive | [[ET-BERT-代码仓库]] |
| IDP-code/TrafficFormer | MIT | 2025-01-18 | 108 | torch==2.0.1 | Google Drive | [[TrafficFormer-代码仓库]] |
| NSSL-SJTU/YaTC | 无 | 2024-04-29 | 156 | torch=1.9.0 | Google Drive | [[YaTC-代码仓库]] |
| ZGC-LLM-Safety/TrafficLLM | 无 | 2025-11-05 | 453 | transformers==4.30.2、torch>=2.0 | Google Drive（基座走 HF） | [[TrafficLLM-代码仓库]] |

### RTX 5090（Blackwell，需 CUDA 12.8+）兼容性汇总

- **确定不兼容原说明**：NetMamba（cu121）、YaTC（torch 1.9.0）、TrafficFormer（torch 2.0.1）、ET-BERT（CUDA 11.4 声明）。
- **未声明版本，需 clone 后实测**：netFound。
- **最可能可用**：TrafficLLM 的 `torch>=2.0` 无上界，但 `transformers==4.30.2` 与 ChatGLM2 remote code 组合仍需实测。
- 结论：六个仓库中没有任何一个可以在目标硬件上开箱复现，环境重建是必做工作量。

### 分发方式风险

- 走 Google Drive 的有 4 个（ET-BERT、TrafficFormer、YaTC、TrafficLLM），无 DOI、无校验和、无版本，链接有效性均标为待验证。
- 只有 netFound 同时提供 HF 权重与 Zenodo 数据，可得性最好。

## 三、综述与基准

| 资源 | 类型 | 状态 | 笔记 |
| --- | --- | --- | --- |
| LSPR24 Zenodo 官方数据发布页（DOI 10.5281/zenodo.14900873） | 数据集发布页 | 已核验文件、大小、MD5、许可与版本关系 | [[LSPR24-Zenodo数据发布页]] |
| TQH-C2 Zenodo 数据集（概念 DOI 10.5281/zenodo.21330094） | 版本化数据集 | 已核验 5 版、v1.2.0 实际 48 单元/152,765 流、错引 DOI 风险与截止 2026-08-12 的外部使用审计 | [[TQH-C2-Zenodo数据集版本与外部使用审计]] |
| Network traffic foundation models: A systematic review（Computer Networks 2026, 卷 276, 111998, DOI 10.1016/j.comnet.2026.111998） | 系统综述 | **阻塞：ScienceDirect 返回 403，需手动下载** | [[流量基础模型系统综述-2026]] |

## 四、RWKV 官方与社区资源

| 资源 | 类型 | 核验结论 | 笔记 |
| --- | --- | --- | --- |
| RWKV.CN 论文生态目录 | 社区文献发现页 | 2026-08-08 页面声明共 247 篇、更新于 2026-08-07；只作发现线索 | [[RWKV论文生态目录]] |
| BlinkDL/RWKV-LM | 官方代码仓库 | Apache-2.0；含 RWKV-v1 至 v8、RWKV-8 设计与 ROSA 工程实现 | [[BlinkDL-RWKV-LM官方仓库]] |

## 五、查重涉及的官方研究源码

| 资源 | 类型 | 核验结论 | 笔记 |
| --- | --- | --- | --- |
| AdityaLab/FOIL | 官方代码仓库 | MIT；README 与 arXiv:2406.09130、ICML 2024 FOIL 论文对应，公开环境推断后再学不变表示的入口 | [[AdityaLab-FOIL官方源码]] |
| hyx1999/SAM-Decoding | 官方代码仓库 | README 与 arXiv:2411.10666、ACL 2025 论文对应；公开静态／动态后缀自动机实现，根目录许可证未确认 | [[hyx1999-SAM-Decoding官方源码]] |
| Clearloveyuan/DyG-Mamba | 官方代码仓库 | README 与 arXiv:2408.06966、NeurIPS 2025 对应；公开真实时间跨度进入 Mamba 扫描的实现，根目录许可证未声明 | [[Clearloveyuan-DyG-Mamba官方源码]] |
| Torea-L/JCCMTM | 官方代码仓库 | Apache-2.0；README 与 DOI 10.1016/j.neunet.2025.107922 对应，公开 `CI`、`CD`、`CICD` 掩码预训练策略；仓库不含论文全文 | [[Torea-L-JCCMTM官方源码]] |
| Thinklab-SJTU/UP2ME | 官方代码仓库 | Apache-2.0；README、ICML 2024 论文与实现一致，公开冻结预训练编码器构造稀疏通道图并完成多变量异常检测微调 | [[Thinklab-SJTU-UP2ME官方源码]] |

## 六、作者页与发表状态

| 资源 | 类型 | 核验结论 | 笔记 |
| --- | --- | --- | --- |
| Shinan Liu 公开履历 | 作者履历 | 2026-03 版本仍将 NetGuard 列为“在投，2025”；不能把预印本 ACM 模板当作 KDD 接收证据 | [[Shinan-Liu作者履历]] |

## 七、待办

1. 手动下载上述综述 PDF，存为 `raw/papers/traffic-foundation-models/2026_Perez-Jove_Network_Traffic_Foundation_Models_Systematic_Review.pdf`，再按论文笔记模板升级。
2. clone `SNL-UCSB/netFound` 核对依赖版本，判断 5090 兼容性（当前唯一未知项，也是骨干选型的关键卡点）。
3. 加载 `wangtz/NetMamba` 的 `pre-train.pth` 实测参数量，验证"26.19MB ≈ 6.5M 参数"的推论。
4. 核对 `snlucsb/netFound-640M-base` 的 711.8M 与 643.8M 差额构成。
5. 向 NetMamba、YaTC、TrafficLLM 作者确认许可证（三者均无 LICENSE）。

## 八、跨年度迁移学习官方研究源码（2026-08-12）

| 资源 | 精确提交 | 许可证 | 本课题用途 | 笔记 |
| --- | --- | --- | --- | --- |
| mims-harvard/Raincoat | `624795a7be4de45d265642ada58f28fbe0111237` | MIT | 时频表示与 Sinkhorn 纠正强基线 | [[mims-harvard-Raincoat官方源码]] |
| iLearn-Lab/NeurIPS24-ACON | `98db37cd7142827c49304e22ef05a6a60706cb63` | 未声明 | 时频互学习与相关子空间对抗近邻 | [[iLearn-Lab-ACON官方源码]] |
| EhsanEI/lar | `d695e9f2ba7652547bc1270be77a5a68ac65bb4a` | 待复核 | 普通谱分类头正则基线 | [[EhsanEI-LAR官方源码]] |
| JayD2106/WARMPOT | `7638632740070de340dddf12eccdd917ace7b6f9` | MIT | 普通非对称部分传输与源边缘权重基线 | [[JayD2106-WARMPOT官方源码]] |
| LHXXHB/EnsV | `b0bb1d1181d6796516335fa4d88391e81eb49a95` | MIT | 无标签停机门禁的一项预测共识信号 | [[LHXXHB-EnsV官方源码]] |
| DMIRLAB-Group/LCA | `45c091fca909ac13675c6ddac7e0464f0a186355` | 未声明 | 潜在因果结构诊断来源，暂不实施完整模型 | [[DMIRLAB-LCA官方源码]] |
| Scarlett125/PROTOCOL | `e17f095b38c81251caccdc4456696060b126882a` | 未声明 | 渐进部分质量与尾类再平衡原创边界 | [[Scarlett125-PROTOCOL官方源码]] |

上述仓库均只读核验，未执行训练。旧 CUDA/PyTorch 环境、未声明许可证和侵入式依赖改动分别记录在逐仓库笔记中。
