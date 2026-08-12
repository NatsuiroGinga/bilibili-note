---
title: "AdityaLab/FOIL 官方源码"
date: 2026-08-11
verified_on: 2026-08-11
tags:
  - 外部资源
  - 官方源码
  - 时间序列
  - 分布外泛化
  - 类型/参考
related:
  - "[[2024-Liu-FOIL时间序列OOD不变学习]]"
---

# AdityaLab/FOIL 官方源码

## 核验结论

- 仓库：https://github.com/AdityaLab/FOIL
- 2026-08-11 只读核验的 `HEAD`：`601c54a054906479cc3b2a38e19459af89a44622`。
- README 明确称其为 ICML 2024 论文 FOIL 的官方实现，并链接 arXiv:2406.09130。
- README 给出的复现顺序是先推断环境，再学习不变表示；公开了 Informer 原始版和 Informer+FOIL 的示例入口。
- 根目录 `LICENSE` 为 MIT 许可证。

## 证据边界

该仓库只证明作者公开了 FOIL 的实现与运行入口。它不替代论文的方法、实验和限制证据，也不能证明候选 C 在网络入侵检测上有效。
