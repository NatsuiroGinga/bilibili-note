# N12 G2 折0充分性早停记录

- **记录日期**：2026-09-08
- **裁决状态**：用户批准的充分性早停；不是 `completed`，不对折1或完整 G2 五级门作结论。
- **读取边界**：只读取 T17 折0本机回传制品、既有合同与计划；未读取 T18--T25 或任何目标年份数据，未运行、恢复或修改实验。

## 输入与完整性

| 输入 | 路径 | SHA-256 |
| --- | --- | --- |
| 数据角色合同 | `thesis/methods/第三章-DRIFT数据角色与评价协议.md` | `87256a95ba347fbff2e333b207046e1b474a63150cded20c03ad245892520fec` |
| N12 研究卡 | `thesis/methods/第三章-DRIFT伪未来辅助任务课程研究卡.md` | `acf00a8a08c36be21ae211c87624cc64b201d9ac5ceb93dbb72563b9cfd3c534` |
| G2 计划 | `.Codex/docs/2026-09-08-DRIFT伪未来辅助课程/g2-implementation-plan.md` | `639fc0a7fd58d08e6cf38de2dd81b68001e6882605ca9a06e4ae393db6374aa0` |
| 原始状态 | `thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-n12-g2-family-isolated-short-step-v1/status.json` | `2c06cc6a0b89cbc35efa67680a5c591ec06b0ea9d675ccb94d29b596e82076ca` |
| 折0检查点 | `thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-n12-g2-family-isolated-short-step-v1/checkpoint.pt` | `e7035f5e1f81755a5ae84bf6267dcc27fa673ee6169ece52dd09cef164ba18c9` |
| 字符梯度 | `thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-n12-g2-family-isolated-short-step-v1/fold-0-char-gradients.pt` | `c39ae82559ba1f1798e6177f1a1fb1698e7954315d132ee2939afff83baf575e` |
| 子词梯度 | `thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-n12-g2-family-isolated-short-step-v1/fold-0-subword-gradients.pt` | `8d33c563bf4477aa8ac34f40590a4e17545b5df74af2ccb6f704da55f58513be` |

两份梯度制品均载有相同的 G2 配置哈希 `680defe1231c6da7ed0ef5ade50193f716eaed637b98d43815029cc47ff07435`、入口哈希 `ee77137c828d1cdeaf6c444bc3cd72e6d90fcce439ef3ee18e47dac5a9d2d593`，且其 `branch` 分别为 `char`、`subword`，`fold=0`。14 个 arm 收据及其哈希如下。

| arm 收据 | SHA-256 |
| --- | --- |
| `arms/fold-0-char-all_equal.json` | `2a3d8de50a21ed9cc620a668c41976da78fd94067e9b53b14bf24c2fce9cb589` |
| `arms/fold-0-char-all_unit_norm.json` | `b9c11c283cfbd16ea0f6a0141855bda3616edf1cd844a63f7c072bebd5176109` |
| `arms/fold-0-char-mtp_only.json` | `3bc1307ed2cd23decacd6f5f1e10af5caf307ceb1508050d2e159e944099a4af` |
| `arms/fold-0-char-mtp_tov_equal.json` | `bb48479639061284f740693bb1211b321832710130ed23849397af7de86d14e6` |
| `arms/fold-0-char-no_update.json` | `f9a77f13ac8929e77b54a6135589aa4adc4ccd287fc3a1ca775109b6adfbe615` |
| `arms/fold-0-char-tov_only.json` | `b433a71abb3bb36feebf0e189c87e80420640254b9290e0520b0d1ea8f9fd8f4` |
| `arms/fold-0-char-tpp_only.json` | `80a9b8b67376645d79c2fc3b0603d0b2f3421d50a6c0871e902cd32e290994a6` |
| `arms/fold-0-subword-all_equal.json` | `c4434e1599c2d31746c179d3b79cf2bf42005f401d3a4b533e7bda93b91f5df3` |
| `arms/fold-0-subword-all_unit_norm.json` | `fc1a32262dadb16fe4f2878f8e3ec7ab8d2187b67880138daa1fb50097ba886a` |
| `arms/fold-0-subword-mtp_only.json` | `5d973ab40de7c5a6ffbc449150511cae4ebd31e4dbc1c56349e84b257b7da48f` |
| `arms/fold-0-subword-mtp_tov_equal.json` | `6e72d636fef3712a73d3936e368ef9e6be709dede90b5814550c7d89fd43fa3d` |
| `arms/fold-0-subword-no_update.json` | `87c043642519f44c53d1d1e6616afdd6e9b75fad7831400a1a7f5dfdc6de23d1` |
| `arms/fold-0-subword-tov_only.json` | `efbf6bb53fdfd614b913bce4221e2bde779bf8791b521418cdaaf12947959157` |
| `arms/fold-0-subword-tpp_only.json` | `89a910a3f4a66b18a8cfb114910164cbf69aa4b81f32c76f83fb20032a6e84fb` |

## 机械复算

对每个 `branch`，以同分支 `no_update` 的 `frozen_probe` 为唯一对照，计算 `候选 BCE - no_update BCE`。正值表示该风险变差，负值表示该风险改善；不把 `refit_probe_attachment` 作为主裁决。

| 分支 | 单任务 arm | 良性 BCE 差值 | DGA micro BCE 差值 | DGA family-macro BCE 差值 | 机械判定 |
| --- | --- | ---: | ---: | ---: | --- |
| 字符 | `mtp_only` | `+0.000006160617126` | `-0.623099249502` | `-0.893016432280` | 良性变差，两个 DGA 风险改善 |
| 字符 | `tpp_only` | `+0.000007086133804` | `-0.633722893471` | `-0.820085923736` | 良性变差，两个 DGA 风险改善 |
| 字符 | `tov_only` | `+0.000011880400328` | `-0.927171178280` | `-1.186453562821` | 良性变差，两个 DGA 风险改善 |
| 子词 | `mtp_only` | `+0.000012015060573` | `-1.014559242315` | `-1.181392028007` | 良性变差，两个 DGA 风险改善 |
| 子词 | `tpp_only` | `-0.000000726708835` | `+0.209232745984` | `+0.276699854813` | 良性改善，两个 DGA 风险变差 |
| 子词 | `tov_only` | `-0.000001343833870` | `+0.274697877320` | `+0.202562588529` | 良性改善，两个 DGA 风险变差 |

对全部 12 个非 `no_update` arm（另含 `mtp_tov_equal`、`all_equal`、`all_unit_norm`）同样检查，均不满足“良性差值 `>0` 且任一 DGA 风险差值 `>0`”。因此，折0内**不存在**良性与任一 DGA 风险同时变差的候选。

## 充分性止损的逻辑与边界

G2 的 family-specific local-harm / 课程解释要求单任务臂相对 `no_update` 出现同侧风险变差，并且另一侧不形成非支配收益。折0的所有单任务臂均呈恶意侧与良性侧相反方向的交换：不存在双侧同时变差，故该解释的必要前提已经被折0充分否决。用户据此明确停止：不调参、不重跑、不恢复 G2，也不把折1断点用于补写该结论。

该早停**只停止**“存在可被另一配置双侧支配的 family-specific local-harm 任务，因而需要 family 反馈课程”的解释和相应 PF-FAC 课程主张；不把 N12 整体、跨分支双侧取舍现象或其他方向一并否决。折0实测的六个 `branch × task` 风险方向仍支持一个新的、较窄的待证病灶：在良性和 DGA 两侧风险之间求解可行的联合梯度组合／投影，而非宣称某个单任务局部有害。

## 运行与制品状态

- 用户已明确停止；远端进程组已发送 `TERM`，GPU 占用为 `1 MiB`，本机回传守护已停止。
- 折1断点保留，以便制品追溯；不用于本记录的科学结论，也不自动恢复。
- 原始 `status.json` 的 `status=running`、`stage=verify` 来自非优雅终止前的状态，现为陈旧原始状态；保留原样，不篡改为完成或失败。
- 不存在闭合 `result.json` 或 `manifest.json`，因此本记录不声称 G2 完成、五级门完成、伪未见 family 效果、课程效果或跨年效果。

## 唯一下一动作

仅用现有折0端点、梯度和固定 32 批块，执行零重训的六个 `branch × task` 双侧风险联合可行方向求解，并运行一个 32 批联合短步。只有该联合臂相对 `no_update` 与 `all_equal` 出现双侧非支配信号，才允许扩展；N13 保持备选，不自动切换或启动。
