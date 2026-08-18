---
title: "mims-harvard/Raincoat 官方源码"
date: 2026-08-12
verified_on: 2026-08-12
tags: [外部资源, 官方源码, 时间序列, 域适应, 类型/参考]
related: ["[[2023-He-RAINCOAT特征标签移位时序适应]]"]
---

# mims-harvard/Raincoat 官方源码

## 核验事实

- 仓库：https://github.com/mims-harvard/Raincoat
- 只读核验 `HEAD`：`624795a7be4de45d265642ada58f28fbe0111237`。
- README 明确对应 ICML 2023 RAINCOAT，并公开时频编码、训练器和多域实验入口。
- 许可证：MIT。
- 依赖声明为 PyTorch 1.7、NumPy 1.20.1、scikit-learn 0.24.1 等旧栈，RTX 5090 上不能视为开箱可用。

## 本课题边界

仓库可用来核对普通 RAINCOAT 强基线，不证明时频适应适合 LSPR 表格流量，也不证明候选有效。

