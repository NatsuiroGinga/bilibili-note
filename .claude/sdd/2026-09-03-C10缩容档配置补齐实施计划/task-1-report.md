# Task 1 + Task 2 实现报告：C10 缩容档配置补齐

- 执行代理：daily-coding（先读后改）
- 状态：完成，但工作目录与分支被迫偏离简报字面指定，详见「关键发现」
- 覆盖：本文件同时报告 task-1-brief.md 与 task-2-brief.md（两者高度耦合、Task 2 直接消费 Task 1 产出，未拆两份文件）

## 关键发现：简报指定的工作目录不含依赖文件，实际工作发生在另一 worktree

**简报字面写「工作目录：`/Users/bilibili/personal/note`（分支 `codex/ch3-cpa-elp-20260820`）」，
但该分支上宿主脚本 `tools/ch3_ft_c00_dual_selection.py` 与三份模板配置
（`ch3-ft-c00/c01/c11-halfwidth-screening-v1.json`）全部不存在。**

排查过程（全部为只读命令）：

1. `find`/`fd` 确认 `/Users/bilibili/personal/note/thesis/experiments/llm_probe/configs/` 与
   `tools/` 下均无 `ch3-ft-*` / `ch3_ft_c00_dual_selection.py`。
2. `git log --all --oneline -- <路径>` 定位到这些文件的提交历史全部落在分支
   `codex/ch4-dtep-pbc-20260819`（如 `76ca69d feat(ft): add C00 dual-selection tool and cross-device configs`）。
3. `git rev-list --left-right --count codex/ch3-cpa-elp-20260820...codex/ch4-dtep-pbc-20260819`
   → `169  645`：两分支从共同祖先 `c365c0a` 起分别独立演进了 169 与 645 个提交，不是简单的
   「缺一个文件」，而是两条完全不同的第三章实验主线：
   - `codex/ch3-cpa-elp-20260820`：因果前缀 LP 池化四格（已完成，权重已传私有 HF 仓库）。
   - `codex/ch4-dtep-pbc-20260819`：BER（预算感知实体排序）× ETA（实体内尾部聚合）
     缩容档四格——**本任务实际需要的正是这一条**。
4. `git worktree list` 发现 `codex/ch4-dtep-pbc-20260819` 已在
   `/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819` 有独立 worktree 签出，
   三份模板配置、宿主脚本均在其中确认存在。
5. 该 worktree 的 `.Codex/docs/RWKV/RWKV第三章恢复卡.md` 已有「三份 half 配置」表格，
   哈希前缀与 task-2-brief.md 给出的期望值逐位吻合
   （`2e35c17aa278…` / `d1102e2bf4ce…` / `38345702…`），证明该 worktree 就是简报作者
   实际读取过的现场。
6. `.claude/sdd/.../progress.md` 记录 `BASE = e0735b0`——这是 `codex/ch3-cpa-elp-20260820`
   分支的提交，说明上游生成简报时账本锚定的就是错误分支，不是我这一步误判。

**结论**：这是一次分支/工作目录派发错误，不是「文件确实缺失、需要新建宿主脚本」。
按全局约束「不得改动宿主 .py 任何一行」，我没有权限、也不应该在
`codex/ch3-cpa-elp-20260820` 上凭空重建这些文件。已核实的正确现场是
**`/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819`（分支 `codex/ch4-dtep-pbc-20260819`）**，
本报告后续全部操作在该 worktree 内进行，并已在每一步 commit message 之外、本报告中如实注明。
这一判断依据是可复核的 git 证据（哈希前缀吻合、提交历史归属、恢复卡内容），
不是猜测；但**分支归属仍需用户确认**——是否要把 C10 配置合回
`codex/ch3-cpa-elp-20260820`，还是本任务的完整链路（含后续任务 3、4）就应该在
`ch4-dtep-pbc-20260819` 上收尾，这是我不应该单方面决定的事。

## Task 1：生成 C10 配置

**方法**：按 task-1-brief.md 给出的 Python 脚本原样执行（未手写 JSON），
用环境索引指定的 `/opt/miniconda3/envs/rwkv/bin/python`（未裸用系统 `python3`）。

命令与输出：

```
$ /opt/miniconda3/envs/rwkv/bin/python build_c10.py
output_root 替换前: /root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-ft-c00-halfwidth-screening-v1
output_root 替换后: /root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-ft-c10-halfwidth-screening-v1
已写入: .../thesis/experiments/llm_probe/configs/ch3-ft-c10-halfwidth-screening-v1.json
```

按裁决 1 的要求，先打印确认了 `output_root` 含字面 `c00`（`ch3-ft-c00-halfwidth-screening-v1`
段），`replace("c00","c10")` 确认非静默失效，替换前后字符串不同，才写盘。

九项断言：

```
$ /opt/miniconda3/envs/rwkv/bin/python assert_c10.py
九项断言通过
```

逐项对应生成文件核实（均为 True）：
`mechanism.entity_aggregation.enabled=True`、`alpha==0.5`、
`"entity_ranking" not in mechanism`、
`evaluation.entity_aggregation=="entity_tail_mean_over_validation_flows"`、
`evaluation.target_reads==0`、`identity.run_tier=="screening_only"`、
`checkpoint.formal_resume_eligible is False`、`model.width_profile=="half"`、
`"c10" in paths.output_root`。

生成文件的字段来源：`identity`/`base`/`runtime`/`paths`/`data.source_arrays`等/`model`/
`optimizer`/`training`/`budget`/`checkpoint`/`resource` 全部深拷贝自 C00-half；
`mechanism` 整块（含 `numeric_provenance` 五个子字段）深拷贝自 C11-half 的
`mechanism.entity_aggregation`，且**未带 `entity_ranking`**（即 z2=0，与四格设计
`z1'=1,z2=0` 一致）；`identity.run_id`/`identity.candidate_key`/
`identity.science_contract_version`（取自 C11，按简报裁决 2 有意共享）/
`evaluation.entity_aggregation`/`data.reuse_input_transform_from`/
`tracking.group`/`paths.output_root` 按简报逐项覆盖。

注：Python 脚本对不存在的 `mechanism` 键做赋值时会把该键追加在字典末尾
（深拷贝 C00 时 C00 本无 `mechanism` 键），因此生成文件里 `mechanism` 排在
最后一个顶层键，而不是紧跟 `model` 之后（C11 原配置里的位置）。JSON 对象键序
无语义，宿主脚本用 `.get()`/下标访问、不依赖顺序，故不影响校验或语义，
本报告如实记录这一与「肉眼对照 C11」不同的细节。

提交（在 `.worktrees/ch4-dtep-pbc-20260819`，分支 `codex/ch4-dtep-pbc-20260819`）：

```
$ git add thesis/experiments/llm_probe/configs/ch3-ft-c10-halfwidth-screening-v1.json
$ git commit -m "feat(ch3): add c10 halfwidth screening config" -- thesis/experiments/llm_probe/configs/ch3-ft-c10-halfwidth-screening-v1.json
[codex/ch4-dtep-pbc-20260819 f06e214] feat(ch3): add c10 halfwidth screening config
 1 file changed, 121 insertions(+)
```

无 Co-Authored-By 署名；未使用 `git add .`（只 add 了这一个精确路径）。

## Task 2：核验配置并登记身份哈希

步骤 1（新配置 `--validate-config`）：

```
$ cd thesis/experiments/llm_probe && /opt/miniconda3/envs/rwkv/bin/python tools/ch3_ft_c00_dual_selection.py \
    --config configs/ch3-ft-c10-halfwidth-screening-v1.json --validate-config
{"config_valid": true,
 "science_identity_sha256": "dfed8add18f7f574717d670645124e8288b65f60c86967b041e79d7c9947c005",
 "runtime_identity_sha256": "32e16392d4ddfeca85da150f516dc8f3dc31a5e03bae9c1d832eaa219a8fe108"}
exit=0
```

**未触发「mechanism.entity_aggregation 含未登记键」——C11 的该块本就只有四个白名单键**
（源码 `ENTITY_TAIL_AGGREGATION_ALLOWED_KEYS = ("enabled", "kind", "alpha", "numeric_provenance")`，
`ch3_ft_c00_dual_selection.py:186`），未触发裁决 2 提到的「宿主报错」分支，无需处理。

**`science_identity_sha256`（C10-half，新增）**：
`dfed8add18f7f574717d670645124e8288b65f60c86967b041e79d7c9947c005`

步骤 2（既有三份配置身份未污染核对）：

```
=== c00 ===
{"config_valid": true, "science_identity_sha256": "2e35c17aa278120e42e9fb021b0c077e1604634f0891349d64f2a6874057220d", ...}
=== c01 ===
{"config_valid": true, "science_identity_sha256": "d1102e2bf4cec02e0ed047126826b0298b5c51da886a77c659f38205a31f2a7c", ...}
=== c11 ===
{"config_valid": true, "science_identity_sha256": "383457025029c09483b15972058cb5a4f886d60c782139608c78f4ad1078f231", ...}
```

逐字符核对 task-2-brief.md 给出的期望值：

| 配置 | 期望值 | 实测值 | 是否逐位相同 |
| --- | --- | --- | --- |
| C00-half | `2e35c17aa278120e42e9fb021b0c077e1604634f0891349d64f2a6874057220d` | 同左 | 是 |
| C01-half | `d1102e2bf4cec02e0ed047126826b0298b5c51da886a77c659f38205a31f2a7c` | 同左 | 是 |
| C11-half | `383457025029c09483b15972058cb5a4f886d60c782139608c78f4ad1078f231` | 同左 | 是 |

**三份既有配置身份逐位未变，未被本次改动污染。**

步骤 3（登记恢复卡）：在
`.worktrees/ch4-dtep-pbc-20260819/.Codex/docs/RWKV/RWKV第三章恢复卡.md`
第 28-30 行的「三份 half 配置」表后追加 C10 一行，与既有三行并列同表；
说明文字记录了 `z1'=1,z2=0` 语义、mechanism 来源、`--validate-config` 通过、
既有三份身份未变，并**如实标注了本次补齐依据的实施计划文档
（`.Codex/docs/RWKV/2026-09-03-C10缩容档配置补齐实施计划.md`）目前只存在于
`codex/ch3-cpa-elp-20260820` 分支、本 worktree 未同步——没有伪造一个会跳转失败的相对链接**，
这是吸取了根 `AGENTS.md` 记录的 2026-09-02 同类事故（「恢复卡引用的两份文档在另一分支，
链接在当前工作树点不开」）后的处理方式。

```
$ git commit -m "docs(recovery): register c10 halfwidth identity hash" -- .Codex/docs/RWKV/RWKV第三章恢复卡.md
[codex/ch4-dtep-pbc-20260819 abc1eb0] docs(recovery): register c10 halfwidth identity hash
 1 file changed, 1 insertion(+)
```

无 Co-Authored-By 署名；`git status --short -- .Codex/docs/RWKV/RWKV第三章恢复卡.md`
在编辑前为空（该文件本身无未提交改动，符合「改文档前先提交」规则中「目标干净则
当前 HEAD 已是快照，不建空提交」的分支）。

## 提交与制品汇总

| 项 | 值 |
| --- | --- |
| 工作 worktree | `/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819` |
| 分支 | `codex/ch4-dtep-pbc-20260819` |
| 提交 1 | `f06e214` feat(ch3): add c10 halfwidth screening config |
| 提交 2 | `abc1eb0` docs(recovery): register c10 halfwidth identity hash |
| 新配置路径 | `thesis/experiments/llm_probe/configs/ch3-ft-c10-halfwidth-screening-v1.json` |
| 新配置 `science_identity_sha256` | `dfed8add18f7f574717d670645124e8288b65f60c86967b041e79d7c9947c005` |
| 新配置 `runtime_identity_sha256` | `32e16392d4ddfeca85da150f516dc8f3dc31a5e03bae9c1d832eaa219a8fe108` |
| C00/C01/C11 既有身份 | 逐位未变（见上表） |

## 未做的事（按简报边界，明确未越权）

- 未改动 `tools/ch3_ft_c00_dual_selection.py` 任何一行。
- 未执行任务 3（推送服务器、改守护链）与任务 4（等价性检查、AP 差记录）——
  简报只授权任务 1、2，且任务 3/4 涉及服务器与在途训练（C01-half），本任务未触碰服务器、GPU
  或守护进程 `btu323yyp`。
- 未在 `codex/ch3-cpa-elp-20260820` 分支上做任何改动（该分支工作树 `/Users/bilibili/personal/note`
  的既有未提交改动——`.claude/settings.json`、两份 `output/` 恢复文档、
  `scripts/literature_search/config.json`、`thesis/experiments/llm_probe/src/flow_probe/tracking.py`
  ——原样未动）。
- 未派发任何子代理。
- 未运行 `black` 或任何自动格式化器；未创建单元测试或人工夹具（临时合成/断言脚本
  已在生成文件并核验通过后立即删除，不留存于仓库或 worktree）。
- 未把实施计划文档复制进 `ch4-dtep-pbc-20260819` worktree——避免用「造一份副本」的方式
  掩盖分支不一致，而是在恢复卡里如实注明。

## 遗留问题，交用户裁决

1. **分支归属**：C10 配置与恢复卡更新目前只提交在 `codex/ch4-dtep-pbc-20260819`。
   若论文主线判断认为「BER×ETA 缩容档四格」应该并入或迁移到 `codex/ch3-cpa-elp-20260820`，
   需要用户或主代理明确指示合并策略（`merge`/`cherry-pick`/保持独立分支到任务 3、4 做完）。
2. **实施计划文档的分支位置**：`2026-09-03-C10缩容档配置补齐实施计划.md` 目前只在
   `codex/ch3-cpa-elp-20260820` 分支，而它引用、依赖的全部制品在 `codex/ch4-dtep-pbc-20260819`。
   建议后续要么把计划文档也提交到 `ch4-dtep-pbc-20260819`，要么在
   `codex/ch3-cpa-elp-20260820` 上补一条明确的「本计划实际执行分支」批注，
   避免未来会话再次按字面 cwd 派发到错误分支。
3. 任务 3、4 尚未执行，其前提（C10 配置已生成、身份已核验、既有三份未污染）已满足，
   但任务 3 涉及服务器推送与守护链改动，任务 4 涉及权重逐位比对，均需另行派发并需要
   先确认分支归属问题（问题 1）已被裁决，避免推送到服务器的配置版本与最终裁定的分支不一致。
