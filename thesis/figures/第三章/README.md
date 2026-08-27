# 第三章图件说明

本目录保存第三章的正式图件与可重复执行的生成源码。规格以 `thesis/figures/AGENTS.md`
的学位论文图件合同为准；本文件只说明本章的生成方式、数据来源与证据边界。

## 生成命令

```bash
uv lock --project thesis/figures/第三章
# 方法机制图（图 3-1 至图 3-4），不使用实验数据
uv run --project thesis/figures/第三章 python thesis/figures/第三章/绘制第三章机制图.py
# 实验结果图（图 3-5 至图 3-12），只从权威制品取数
uv run --project thesis/figures/第三章 python thesis/figures/第三章/绘制第三章结果图.py
```

结果图依赖的制品在 `thesis/experiments/llm_probe/runs/` 下，受 Git 忽略。本机缺失时，
`resultdata.py` 会报出精确路径并提示用 `tools/remote_exec/gpu_rsync_pull.exp` 从服务器
拉取，不会静默改用旧数据。

## 源码分工

| 文件 | 职责 |
| --- | --- |
| `figstyle.py` | 字体解析、版面换算、绘图原语、逐字字形断言。两个生成脚本共用，是字体的唯一来源。 |
| `resultdata.py` | 结果图取数层：定位制品、登记 SHA-256、按键路径取字段、按合同口径重算检出率。 |
| `绘制第三章机制图.py` | 产出图 3-1 至图 3-4，不承载实验数据。 |
| `绘制第三章结果图.py` | 产出图 3-5 至图 3-12（图 3-10 已撤下）。 |
| `图件清单.json` | 按生成器分段登记环境、字体、尺寸、实测分辨率，并逐图登记数据来源键路径。 |

## 文件合同

- `*.svg`：保留文本与矢量对象的可编辑源。
- `*.pdf`：矢量版，供放大核查与排版引用。
- `*.png`：400 ppi 提交版与 Word 插入版。
- 三种格式在每次生成后由脚本核对：SVG 可解析、PDF 文件头有效、PNG 实测 ppi 不低于 300。

## 视觉规范

规格全部取自 `thesis/figures/AGENTS.md`，此处只记录本目录的实际取值：

- 页面 A4；本章图件宽 130～150 mm，高 85～95 mm，均在合同上限 165 mm × 140 mm 之内。
- 中文黑体按 `figstyle.resolve_cjk_font()` 逐字面核验后选中，优先 `SimHei`，取不到才按
  `Heiti SC`、`PingFang SC` 顺序回退，并在图件清单中登记实际字体名、文件路径与 face 索引。
  集合字体（`.ttc`）必须指定 face 索引——不指定会解析到繁体字面，2026-08-26 审查已实测
  到该缺陷使图 3-5 至图 3-11 内嵌 `STHeitiTC-Medium`，现由统一走 `figstyle.py` 关闭。
- 西文 Times New Roman；数学符号 Cambria Math，取不到时回退 mathtext 内置字集并显式登记。
- 最小字号 8 pt，主标注 9 pt；主线 1.0 pt，辅助线 0.5 pt。
- 彩色只作辅助：四格与各方法一律先用填充图案（无、`//`、`..`、`xx`、`///`、`\\`）与线型
  （实线、长虚线、点线、点划线）区分，灰度打印仍可读。

## 数据来源与证据边界

1. 图 3-1 至图 3-4 是方法与协议示意图，不承载实验数据，也不表示任何候选已通过实验裁决。
2. 图 3-5 至图 3-12 只从下列权威制品取数，每个数字都可在图件清单的 `data_keys` 中指回字段：
   - `runs/diagnostics/ch3-full-mlp-complete-entity-lp-protocol-a-q0-seed42-v1-bf16-v1/`
     （正式 CPA×ELP 四格，BF16，单种子 seed42）
   - `runs/diagnostics/ch3-metrics-table-20260825b/`（统一指标总表）
   - `runs/diagnostics/ch3-published-neural-operational-backfill-v1/`（已发表神经基线完整曲线）
3. 检出率一律在完整可达告警预算曲线上取「实际假阳率不超过名义预算的最后一个点」，不使用
   制品中 `dr_at_fpr` 的名义秩位键。该规则由 `resultdata.verify_against_metrics_table()`
   对四个方法、六档预算与统一指标总表逐位自校，不一致即报错停止。
4. 图 3-10（攻击类别分面）已于 2026-08-26 撤下：当前权威制品不含任何按攻击类别的分面字段，
   无法换底重绘。旧文件移入 `作废/`，撤下理由与恢复条件登记在图件清单的 `withdrawn` 段。
5. 全部结果图为单种子 seed42 的单次运行，图内不写多种子误差；目标年读数属封印后描述性评价。
6. 正文只引用本目录下的图件，不引用 `runs/`、`output/` 或任何临时目录中的图片。
