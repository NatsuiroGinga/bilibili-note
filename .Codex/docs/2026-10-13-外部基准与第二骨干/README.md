# P1 外部近邻与第二骨干复现（2026-10-13）

实施计划冻结范围的工作目录。执行代理只做机械执行与自身缺陷自报；候选存废由主代理裁决。

## 文件清单

| 文件 | 作用 |
| --- | --- |
| `implementation_plan.md` | 主代理冻结的实施计划（臂定义、边界、断言、验收命令） |
| `run-log.md` | 运行日志：阶段、读数、缺陷自报、数值登记 |
| `verify_zero_disturbance.py` | 既有臂零扰动断言（缓存收据逐字段比对） |
| `zero-disturbance-audit.json` | 零扰动断言报告（verdict: pass，B 臂降级模式已登记） |
| `esat_selector.py` | ESAT 选择器：A 臂 3 快照跨快照平均熵 → 全训练集排序 → 冻结子集 |
| `README.md` | 本文件 |

## 训练/评价入口

```bash
PY=/opt/miniconda3/envs/rwkv/bin/python
SPEC=".Codex/docs/2026-09-23-DRIFT源期训练抽样合同/candidate-spec-diagnostic-v1.json"
# DRIFT 侧新臂训练（每臂独立运行目录，串行）
P2P3_OUT=<运行目录> $PY .Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official_p2p3.py \
  --arms <ARM> --result-name source-common-<arm小写>-result.json --candidate-spec "$SPEC"
# ESAT 追加 --esat-subset <子集 JSON>
# p0 正式评价（五新臂 + 既有八臂对照）
$PY .Codex/docs/2026-09-23-DRIFT源期训练抽样合同/p0_legal_attack_probe.py \
  --arms C1R,ESAT,DRICHEL,CEQ,CBN --run-name ch3-drift-source-p0-legal-attack-p1arms-mps-20261013-v1 \
  --run-dir thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-source-p0-legal-attack-p1arms-mps-20261013-v1
```

## 制品路径

- DRIFT 新臂：`thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-source-common-{c1r,esat,drichel,ceq,cbn}-mps-20261013-v1/`
- ESAT 子集清单：`…/ch3-drift-source-common-esat-mps-20261013-v1/esat-subset-rho0.5-v1.json`
- A 快照重跑：`…/ch3-drift-source-common-a-snapshot-mps-20261013-v1/`（`selector-snapshots/selector-snapshot-ep{1,2,3}.pt`）
- p0 评价：`…/ch3-drift-source-p0-legal-attack-p1arms-mps-20261013-v1/p0-legal-attack-result.json`
- 第二骨干：`…/ch3-drift-bresnet-common-{a,b,edit4,uq,d}-mps-20261013-v1/`（目录名按 bresnet 脚本口径）
