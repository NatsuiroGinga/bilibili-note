---
title: "hyx1999/SAM-Decoding 官方源码"
date: 2026-08-11
verified_on: 2026-08-11
tags:
  - 外部资源
  - 官方源码
  - 后缀自动机
  - 推测解码
  - 类型/参考
related:
  - "[[2025-Hu-SAM-Decoding后缀自动机推测解码]]"
---

# hyx1999/SAM-Decoding 官方源码

## 核验结论

- 仓库：https://github.com/hyx1999/SAM-Decoding
- 2026-08-11 只读核验的 `HEAD`：`aaf939819223147ce544e3a80f65758ac7758076`。
- README 链接 arXiv:2411.10666，并明确把后缀自动机用于当前文本与文本库的最长后缀检索。
- README 给出静态自动机构建脚本、无静态自动机的运行选项，以及 `samd`／`samd_sam_only` 推理入口。
- 根目录 `LICENSE` 入口在核验日返回 404；在未进一步审计仓库树前，许可证记为**未确认**。

## 证据边界

该仓库证明论文方法存在公开实现，但不证明其状态与 RWKV-8 ROSA 等价，也不提供网络异常检测、固定容量记忆或正常预测残差的证据。
