---
title: "Yandex FT-Transformer 官方源码"
date: 2026-08-20
tags: [GitHub, FT-Transformer, 表格数据, 类型/参考]
---

# Yandex FT-Transformer 官方源码

- URL：<https://github.com/yandex-research/rtdl-revisiting-models>
- 核验 HEAD：`e3ed46cac38568785289d8fa16b8cfa585bde27e`
- 许可证：Apache-2.0。
- 状态：官方论文实现和推荐包已核验；**固定快照已归档**至 `thesis/experiments/llm_probe/vendor/ft_transformer/`（`bin/ft_transformer.py` SHA-256 `2eddb24549aa322840f1e699b80b3ed9137bba2032592c333ad34998310326b3`、`LICENSE` SHA-256 `bd39fcc730a79d256b14fcdccbfc8ac9f0c7fad4a2e8d01fc513def67980fe35`，清单见同目录 `manifest.json`）；仍未导入正式环境，未运行本候选真实前向/反向。归档经 Codex 于 2026-08-21 授权（看板提交 `956abcb`），范围限于未修改的上游单文件、许可证与清单，不含整仓库或依赖缓存。
- 官方推荐默认示例：3 个 Transformer 块、宽度 192、8 个注意力头、注意力随机失活 0.2、前馈扩张 `4/3`、AdamW；论文通常用 100 次 TPE 调参。
- 关联：[[2021-Gorishniy-表格数据深度学习模型再审视]]。
