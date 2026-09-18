# MP 两个参照 F／M 的制品定位盘点

> 盘点时间：2026-09-13。
>
> 范围：只读本工作树的精确文件名与既有过程文档；未连接服务器、未使用凭据、未重算指标。
>
> 结论边界：本文件不作科研裁决，也不把文档转录冒充原始运行制品。

## 结论

- 本工作树未找到 `run5-result-armF.json`、`console-run5-armF.log`、`console-lm2.log` 或含 L／M／D 的服务器 `result.json` 副本。
- F 的可追溯来源目前仅为过程文档登记的远端运行目录与备份路径；远端是否仍存在、实际运行设备、原始日志、模型哈希与完整指标均**未在本轮核验**。
- M 的可追溯来源目前仅为过程文档中 `console-lm2.log` 与三臂 `result.json` 的登记及其表格转录；同样没有本地原始日志和 JSON。
- 本地 `official-p2p3-result.json` 的唯一结果键为 `P`，不是 F 或 M；`official-p2p3-console.log` 是 MPS 上的 A／B 等本机运行记录，不能作 F 或 M 证据。

## 精确定位结果

| 对象 | 已记录运行身份或路径 | 本地精确文件名命中 | 可核事实 | 未核缺项 |
| --- | --- | --- | --- | --- |
| F | 远端主运行目录：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/p2p3-official-v1/`；备份：同目录 `backup-k2verdict/run5-result-armF.json`、`backup-k2verdict/console-run5-armF.log` | 无 | `task_plan.md` §5.6.1／§5.6.6 将 F 登记为五臂筛选中的运行5 | 原始 JSON、原始日志、模型哈希、数据版本哈希、精确样本清单、设备与指标读数均未本地核验 |
| M | `task_plan.md` §5.12.4：`console-lm2.log` 与含 L／M／D 的 `result.json` | 无 | 文档转录 M：clean AP `0.99751`、clean FPR `0.02813`、clean FNR `0.016`、`maskdga` FNR `0.00853`、`k2` FNR `0.0132` | 原始 JSON、原始日志、模型哈希、数据版本哈希、设备、种子和完整三面板定义未本地核验 |
| 本地 P | `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official-p2p3-result.json` | 命中 | 文件仅含 `results.P`；其记录 `wall_seconds=5494.2`，并有 k2／krand／maskdga 结果 | 不是 F 或 M，不能替代任一参照 |
| 本地 MPS 控制台 | `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official-p2p3-console.log` | 命中 | 记录 A、B 等臂；首行写训练6万、干净评价1.5万、三对抗面板各7500；出现 MPS 后端回退警告 | 未核到 F 或 M；不可作为远端 F／M 的设备或读数证据 |

## F 的已登记冻结规格与可比性

过程文档 §5.6.1 对 A 至 G 的筛选规格登记为：T17 训练固定平衡筛选子集6万（良性／DGA各3万）、3个训练轮次、训练批量128、Adam 分层学习率、种子42、阈值0.5；干净 T18 验证1.5万，对抗 `k2`／`krand`／`maskdga` 各7500。`load_split` 取两个 Parquet 当前行序前3万，不是随机抽样。

这只能说明 F **按文档应属于同一筛选合同**，不能替代 F 原始 JSON 和日志来确认实际执行的模型、数据、样本、种子、设备或指标。因此与当前 MP 的可比性仍缺：共同代码提交、数据／成员身份、实际攻击实现、阈值口径、设备与精度、训练预算和原始指标制品。

## M 的已登记规格与可比性

§5.12.4 将 M 描述为“Mix：同攻击曝光无课程”，并登记其三项面板转录指标。该节只给出运行身份为 `console-lm2.log` 与含 L／M／D 的 `result.json`，当前工作树无对应回收件。

因此 M 与当前 MP 的关系只能标为“机制名称近似、原始运行身份待核”。在未取得原始制品前，不能把文档表中的 M 数字当作 MP 的基线、效果上界、已复现读数或候选裁决依据。

## 本轮执行的定位命令

```text
fd --hidden --type f '^run5-result-armF\\.json$' .
fd --hidden --type f '^console-run5-armF\\.log$' .
fd --hidden --type f '^console-lm2\\.log$' .
fd --hidden --type f '^result\\.json$' .Codex/docs/chatgpt-handoffs thesis/experiments/llm_probe
fd --hidden --type f '^official-p2p3-result\\.json$' .
fd --hidden --type f '^official-p2p3-console\\.log$' .
```

前四项没有本地命中；后两项只命中本地 P 及 MPS A／B 等记录。
