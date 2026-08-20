---
title: "Yandex TabR 官方源码"
date: 2026-08-20
tags: [GitHub, TabR, 检索增强, 类型/参考]
---

# Yandex TabR 官方源码

- URL：<https://github.com/yandex-research/tabular-dl-tabr>
- 核验 HEAD：`17baa9082506f8e7a0f8d11bb1e08212926a1507`
- 许可证：MIT。
- 状态：官方实现已核验；本机未归档源码快照，未导入正式环境，未运行真实前向/反向。
- 实现事实：使用 Faiss 对训练候选键做精确最近邻；`memory_efficient` 模式先无梯度编码全候选，再只对命中上下文重算梯度；候选标签参与值模块。
- 关联：[[2024-Gorishniy-TabR检索增强表格网络]]。
