# Rust vs Python 评测服务对比：检索与设计输入

- 任务：为第五章 Web 平台增加「Rust 评测服务 vs Python(FastAPI/PyTorch) 评测服务」实验提供外部依据。
- 边界：只登记文献/基准与设计建议，**不做存废裁决**；训练内核保持 PyTorch 不动。
- 日期：2026-10-22
- 证据等级：A＝官方原始数据/官方文档；B＝同行评议论文或官方工程博客；C＝可复现的第三方基准/技术报告；D＝仅二手转述或博客断言。

---

## 0. 结论摘要（供裁决，不替代实验）

1. TechEmpower R23 官方原始数据（56 核 Xeon、40GbE）显示：**JSON 测试高并发（512 连接）下 Rust axum 约 271 万 req/s，FastAPI 约 35.5 万 req/s（约 7.6×）；低并发（16 连接）下仅 2.78 万 vs 2.13 万（约 1.3×）**。服务层语言差距随并发上升而放大，单请求/低并发差距远小于吞吐差距。
2. PyTorch 的 GIL 释放在**绑定层按算子路径选择性实现**，不是全局保证；纯 Python 前后处理仍受 GIL 限制。因此 Python 服务的并发扩展通常依赖多进程（uvicorn workers/gunicorn），这会放大内存与启动成本。
3. Rust 重写推理/数据管道的先例（HF tokenizers、safetensors）主要收益在**纯 CPU 数据路径**；模型前向仍依赖底层内核。candle 是纯 Rust 重实现，数值与性能均不等同于 PyTorch；tch-rs 复用 libtorch，是唯一有希望做到「同权重、同内核、逐位一致」的路线，但 MPS 需要借用 Python 的 PyTorch 动态库。
4. 诚实边界：**若 Rust 与 Python 都调用同一 libtorch 核，Rust 只能赢在 HTTP/序列化/调度/进程模型等请求开销；张量计算占主导时差距会被摊薄，低并发单请求差异可能只有毫秒级甚至不可测。** 这应由实验证实，不能由基准外推。

---

## 1. 问题一：Rust 相对 Python 在 ML 推理/评测服务层的优势

### 1.1 TechEmpower Web Framework Benchmarks（最新轮次 R23）

**检索式**
- `TechEmpower Web Framework Benchmarks latest round 2026 Rust actix axum Python FastAPI results`
- `TechEmpower benchmarks Round 23 results Rust axum actix Python uvicorn requests per second`
- `techempower.com blog Round 23 results announcement date`
- `"techempower" round 23 FastAPI requests per second results JSON test`

**来源**
- 官方轮次公告：<https://www.techempower.com/blog/2025/03/17/framework-benchmarks-round-23/>
- 官方结果入口：<https://www.techempower.com/benchmarks/#section=data-r23>
- 官方运行 UUID：`91a66052-9d86-446c-b31a-eadbd669ed08`（提交 `523534bb61450e3522d775a749ad060753e26e3a`）
- 本机可读的 R23 原始 JSON 镜像（UUID/提交与官方一致，SHA-256 `9300a12950f64852af228556e342896e971122cf821433382d7f8b6d432c1023`）：
  <https://github.com/0xRichardL/system-design-practice/blob/main/foundations/backend-frameworks/sep_2026/references/techempower-r23-physical.json>
- 本任务抽取表：`techempower-r23-selected.tsv`（同目录）

**官方硬件与方法（R23）**
- 物理机：HPE DL360 Gen10 Plus，56 核 Xeon Gold 6330 @ 2.00 GHz，64 GB，40 Gbps ConnectX-6；软件栈更新，官方称网络受限场景约 3× 提升。
- JSON 测试：连接并发 16/32/64/128/256/512，每档 15 s。
- Plaintext 测试：pipeline 并发 256/1024/4096/16384，每档 15 s（因此不能与 JSON 的「连接数」直接对比）。
- RPS＝`totalRequests / (endTime - startTime)`，由原始 JSON 重算。

**关键数字（R23，物理机）**

| 框架 | JSON c=16 | JSON c=512 | Plaintext pipeline=16384 |
|---|---:|---:|---:|
| Rust axum | 27,804 | 2,709,794 | 11,710,931 |
| Rust hyper | 27,635 | 2,885,610 | 15,993,844 |
| Rust may-minihttp | 27,669 | 3,102,062 | 23,753,976 |
| Python FastAPI | 21,271 | 354,899 | 285,089 |
| Python FastAPI+uvicorn | 22,191 | 322,402 | — |
| Python Starlette | 24,635 | 599,108 | 468,453 |
| Python Uvicorn | 26,800 | 797,037 | 717,625 |
| Python Django | 19,784 | 164,869 | 178,287 |

- **高并发 JSON：Rust axum / FastAPI ≈ 7.6×；低并发 JSON：≈ 1.3×。**
- R23 中 `actix` 条目只有代码统计、无测试读数，故不能引用 actix 的 R23 数字；可用 axum/hyper 代表 Rust 侧。
- 注意：TechEmpower 是**无业务逻辑的框架微基准**，其 JSON 测试只含路由＋序列化，不含模型推理；绝对 RPS 不能外推到评测服务，但「低并发差距小、高并发差距大」的相对形态有参考价值。

**证据等级**：A（官方原始结果 JSON 重算；官方站点因本机 DNS 被代理接管无法直连，使用 UUID 一致的镜像副本，已记录哈希）。

### 1.2 Python GIL 对推理服务并发的影响

**检索式**
- `PyTorch releases GIL during inference torch operations GIL release documentation`
- `PyTorch GIL released C++ ATen operations source code gil_scoped_release inference threads`

**来源与结论**
- PyTorch 生成的 ATen Python 绑定中包含「release the GIL and switch to the correct CUDA device」包装（`tools/autograd/templates/python_variable_methods_dispatch.h`，生成文件 `torch/csrc/autograd/generated/python_variable_methods_dispatch.h`）。→ 多数张量算子调用期间 GIL 被释放。
- AOTInductor runner 的 PR #199681 明确在构造与 `run()/boxed_run()` 周围释放 GIL，并以「canary Python 线程能否推进」做测试；官方将其作为多实例/多线程推理的改进。
- Inductor 生成的 CPU 推理 wrapper 含注释「release GIL to support multiple instances inference (in different threads of the same process)」，代码为 `pybind11::gil_scoped_release`（PR #123897 曾因自定义算子回调短暂回退后恢复）。
- **但这是按路径选择性实现，不是全局保证**：PyTorch issue #163062 记录了一个依赖设备张量形状的 `torch` 调用未释放 GIL 的反例；量化动态线性层的论坛案例显示多线程无吞吐增益，怀疑绑定/内核路径未释放 GIL。
- 结论：**模型前向的大算子调用通常不长期占住 GIL，但 Python 侧预处理/后处理、tokenization、JSON 构造、Pydantic 校验等纯 Python 代码仍串行化**。FastAPI 的 async 事件循环遇到 CPU-bound 后处理会被阻塞；常规做法是多进程 worker，代价是每进程独立加载模型（内存×N）与更长启动/预热。

**证据等级**：B+（PyTorch 源码/PR 与 issue 为一手，但无单一官方文档给出「所有推理调用都释放 GIL」的保证）。

### 1.3 已发表的「Rust 重写 Python 推理/数据路径」实例

**检索式**
- `Hugging Face tokenizers written in Rust why performance Python bindings`
- 待补：safetensors 设计动机、candle 发布博客、tree-sitter Rust 重写

**已知（待逐条核验原文）**
- HF `tokenizers`：Python 包是 Rust 实现的绑定；官方文档称 1 GB 文本 tokenize <20 s，对比纯 Python 约 20 min（约 80×）。收益来自把**纯 CPU 字符串处理**移出解释器，而非替代模型前向。
- safetensors：Rust 实现，动机包括零拷贝/内存映射与加载安全；主要收益在权重加载与共享，不在前向计算。
- candle（HF）：纯 Rust 推理框架，动机是部署简单（无 Python 运行时、静态二进制、启动快）与 CPU/ Metal/CUDA 支持；官方定位不是「全面快于 PyTorch」。
- tree-sitter：从 JavaScript 重写到 Rust 的解析器，属于「CPU-bound 纯计算迁出解释器」的类比，不是 ML 推理先例，只作旁证。

**证据等级**：B（官方文档/仓库）；具体数字需以官方 README 原文为准，后续补 URL 与原文摘录。

---

## 2. 问题二：Rust 侧技术选型（tch-rs vs candle vs burn）

> 状态：待检索补全。

### 2.1 后端支持与权重兼容路径
### 2.2 数值一致性风险
### 2.3 推荐路线与理由

---

## 3. 问题三：诚实边界（Rust 优势为 0 或负的指标）

> 状态：待检索补全。

### 3.1 同 libtorch 核时 Rust 的收益上界
### 3.2 单用户/低并发可测性
### 3.3 Python+FastAPI 在批处理场景的真实吞吐

---

## 4. 裁决输入表

> 状态：待汇总。

| 编号 | 问题 | 主张 | 证据（URL/制品） | 等级 | 方向 | 备注 |
|---|---|---|---|---|---|---|

---

## 5. 实验设计建议（只建议，不裁决）

> 状态：待汇总。
