# 实施计划：第四章 E2 排序门控主动获取先导

> **日期**：2026-10-15
> **上位文件**：`thesis/methods/第四章-RGA-DBA研究问题卡.md`（判据冻结处）／`第四章-RGA-DBA机制设计.md`
> **用户裁决**：E2「现在实现并跑」；第四章范围「你自己看文献来决定」（⇒ 本计划**只实现 RGA 一侧**，DBA 不实现）
> **实现代理**：唯一，`sonnet`。主代理不放行第二个实现代理改同一范围。

---

## 1. 文件边界（**严格**）

| 动作 | 路径 |
| --- | --- |
| **新建**（唯一新建的代码） | `thesis/experiments/llm_probe/tools/ch4_lamda_rank_gated_acquisition_e2.py` |
| **禁止改动** | `thesis/experiments/llm_probe/tools/ch3_lamda_domain_il_e4.py`（第三章全部证据由它产出，动它就断证据链） |
| **禁止改动** | `thesis/chapters/**`（另一代理刚定稿）、`thesis/figures/**` |
| **新建制品目录** | `thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-rank-gated-acquisition-e2/` |

## 2. 接口

**导入**（`from ch3_lamda_domain_il_e4 import ...`，同目录，脚本已有 `if __name__ == "__main__"` 保护，import 无副作用）：
`load_year, ChenEncoderMLP, split_by_year, ReplayBuffer, iterate_batches_parts, train_epochs, evaluate, score_shard, write_json, now_utc`，常量 `DOMAIN_YEARS, OFFICIAL_EPOCHS, OFFICIAL_BATCH, OFFICIAL_LR, OFFICIAL_MEMORY, THRESHOLD, SEED`。

**数据根解析**（硬约束）：`DATA_ROOT` **必须**从环境变量 `LAMDA_DATA_ROOT` 解析；未设置时报错退出并打印应设置的路径，**不得**在新脚本里再写死绝对路径。当前实测可用值（由启动器导出，不写进代码）：
`/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767`。
导入后以 `mod.DATA_ROOT = Path(os.environ["LAMDA_DATA_ROOT"])` 覆盖被导入模块的值。

**主线**：与第三章主臂**逐字一致**——`buffer-scheme=quota`、`reuse-scheme=deficit`、`buffer-repeat=2`、`memory=200`、`epochs=10`、`batch=1024`、`lr=0.01`、`seed=42`、阈值 0.5。**实现方式是按 `main()` 的年度循环逐句镜像**（导入函数、不 shell 出去调另一个脚本、不改原脚本）。

**侧支**（主线不受影响，不回流）：在分叉年度 $Y$，主线跑完 $Y-1$ 后：
1. 深拷贝模型与缓冲；
2. 用 `Y-1` 的模型给 $D_Y^{train}$ 打分为 `score_shard`；
3. 对 $\Lambda \in \{200, 800\}$：
   - `active`：取分数 **top-$\Lambda$** 索引；
   - `passive`：**均匀随机**取 $\Lambda$ 条（用 `np.random.default_rng(SEED + Y * 1000 + Λ)`，确定性可复现）；
4. 两条索引取子集后（**只保留这两个子集**，其余 $D_Y^{train}$ 视为无标签、不参与训练），与主线缓冲合并，`train_epochs` 十轮；
5. `buffer_only`：只用缓冲训练十轮；
6. 每臂在 $D_Y^{test}$ 上 `evaluate`，并**保存逐样本预测**（`y_true` 与 `y_score`）供离线配对 bootstrap。

**分叉年度**：$\{2016,\ 2017,\ 2018,\ 2024\}$。**不得**读取 2019–2023 的测试分片。

**每臂必须记录**：F1、精确率、召回率、准确率、FPR、FNR、平衡准确率、**实际取得的正例条数**（$Y$ 训练分片中该子集内 label==1 的条数）。

## 3. 制品

| 文件 | 内容 |
| --- | --- |
| `e2_protocol.json` | 冻结的判据与配置（分叉年、$\Lambda$ 网格、臂定义、阈值、种子、判据文本），**运行前写出** |
| `e2_results.json` | 每臂指标 ＋ 取得正例数 |
| `preds_<arm>.npz` | 每臂在分叉年度测试分片上的逐样本 `y_true`/`y_score` |
| `full_e2.log` | 控制台全文（主线逐年读数 ＋ 每臂读数） |

## 4. 验收命令（**按序，任一步失败即停**）

```bash
PY=/opt/miniconda3/envs/rwkv/bin/python
TOOLS=thesis/experiments/llm_probe/tools
export LAMDA_DATA_ROOT=/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767

# 1) 语法与导入
$PY -m py_compile $TOOLS/ch4_lamda_rank_gated_acquisition_e2.py
$PY -c "import sys; sys.path.insert(0,'$TOOLS'); import ch4_lamda_rank_gated_acquisition_e2 as m; print('import ok')"

# 2) 主线复现门（**决定性验收**）
$PY $TOOLS/ch4_lamda_rank_gated_acquisition_e2.py --main-only
# 期望：末年 2025 的 12 年平均 F1 == 0.8170（与 full_expreplay_m200_quota_deficit_r2_diag.log 末行一致）
#       不相等 ⇒ 停止，镜像错了，不得继续

# 3) 全量
$PY $TOOLS/ch4_lamda_rank_gated_acquisition_e2.py
```

## 5. 阻塞条件

- **主线复现门的读数对不上 0.8170** ⇒ 立即停，报主代理；不得"调一调凑上去"。
- `LAMDA_DATA_ROOT` 未设置或路径不存在 ⇒ 报错退出，不得回退到硬编码。
- 需要改动 `ch3_lamda_domain_il_e4.py` 才能完成任务 ⇒ 停，报主代理改计划；**不自行修改**。

## 6. 成本

主线 12 年度流实测约 2 分钟（单年度训练 4.7–12.0 秒）；侧支 4 年 × (2$\Lambda$ × 2 策略 ＋ 1 buffer_only) = 20 臂，每臂训练规模 $\le 2{,}200$ 行 × 10 轮 ⇒ 每臂数秒。**合计 5 分钟以内**，MPS 单进程。

## 7. 判据（**从研究问题卡复制，不得改动**）

主判据：$\Delta F_1(s)=F_1^{\text{active}}(s)-F_1^{\text{passive}}(s)$ 随 $\alpha_s$ 的**单调性**。

- **支持**：$\Delta F_1(2024)$ 显著为正，且大于 $\Delta F_1(2017)$，后者不小于 $\Delta F_1(2016)$ 与 $\Delta F_1(2018)$（后两者预期落 $|\cdot|<0.5$）。
- **部分支持**：仅 2024 显著为正。
- **证伪**：任一臂 $\Delta F_1<0$；或四年均不可分辨。
- **强证伪**：$\Delta F_1(2024)\le 0$。

不确定性：**单一冻结种子 42**（`AGENTS.md` L41 禁多种子）；由测试集**配对 bootstrap**（$n=2000$）给出 95% 区间，报告时**必须**标注"该区间只量化样本不确定性，不冒充训练随机性"。
