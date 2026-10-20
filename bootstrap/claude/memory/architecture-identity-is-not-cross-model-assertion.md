---
name: architecture-identity-is-not-cross-model-assertion
description: 架构级恒等式只在同一组权重内成立，不能当作跨独立训练模型的可验证断言
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4bf71861-639f-455d-b431-5dbc10e3331a
  modified: 2026-08-31T14:21:06.019Z
---

「机制开关置零时退化为基线」这类**架构级恒等式**，只在**同一组权重**内成立。
把它写成跨模型断言（如「C10 上门永不激活的样本，分数须与 C00 逐位相同」）是类型错误：
两个格是两次独立训练，骨干权重不同；开关置零只切断该机制的加性通路，
**不隔离共享骨干在训练中被机制激活样本改写的间接影响**。

**Why**：2026-08-31 写 M-E 预注册断言时犯过一次，被独立复核（fable）当场抓到。
若按原样执行，正式 GPU 运行会因一个必然失败的检查而中断，浪费整轮训练。
同类间接影响正是 CEM 从第 1 轮起损害逐流 AP 的传播通道——它不是理论顾虑。

**How to apply**：写任何「置零/关闭后应与基线相同」的断言前，先问「这两边是同一组权重吗」。
同权重 → 断言逐位相等，可以用 `atol=0`。跨模型 → 改为逐轮指标差值监控之类的统计检查，
并明确写出「不得与另一格的输出逐位比较」。相关：[[syntax-check-is-not-execution]]、
[[no-verdict-before-queued-measurement]]。
