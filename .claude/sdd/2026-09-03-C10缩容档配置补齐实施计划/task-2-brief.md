# Task 2：核验配置并登记身份哈希

## 本任务全局约束（逐字取自计划）

- `run_tier` 必须为 `screening_only`；`checkpoint.formal_resume_eligible` 必须为 `false`
  （宿主 `:418` 强制：筛选检查点不得正式续训）。
- `mechanism.entity_aggregation` 开启时，键集**只能**是
  `{alpha, enabled, kind, numeric_provenance}`（宿主 `:314` 白名单，多一个键即拒）。
- `alpha` 必须严格等于已冻结的 `0.5`（宿主 `:325`，且明文禁止按实验读数回调）。
- `evaluation.target_reads` 必须为 `0`；全程不得读取 LSPR24。
- `width_profile` 为 `half`，骨干参数量断言 `240955`。
- **不得改动宿主 `.py` 任何一行**——本计划只新增配置与守护链条目。
- 提交用 `git commit -m "..." -- <精确路径>`，**绝不 `git add .`**，
  提交信息末尾**不得**有 Co-Authored-By 署名。

---

**Files**
- Read: 新配置
- Modify: `.Codex/docs/RWKV/RWKV第三章恢复卡.md`（追加身份哈希）

**Interfaces**
- Consumes：任务 1 产出的配置文件
- Produces：`science_identity_sha256`，任务 3 启动前核对用

- [ ] **步骤 1：跑宿主的配置核验**

```bash
cd thesis/experiments/llm_probe && /opt/miniconda3/envs/rwkv/bin/python tools/ch3_ft_c00_dual_selection.py --config configs/ch3-ft-c10-halfwidth-screening-v1.json --validate-config
```

预期：退出码 `0`，输出含 `science_identity_sha256`。
**若报「mechanism.entity_aggregation 含未登记键」**，说明 C11 的该块含白名单外的键，
回到任务 1 只保留 `{alpha, enabled, kind, numeric_provenance}` 四键。

- [ ] **步骤 2：确认既有四份配置身份未被污染**

```bash
cd thesis/experiments/llm_probe && for c in c00 c01 c11; do /opt/miniconda3/envs/rwkv/bin/python tools/ch3_ft_c00_dual_selection.py --config configs/ch3-ft-$c-halfwidth-screening-v1.json --validate-config 2>/dev/null | grep -o '"science_identity_sha256": *"[a-f0-9]*"'; done
```

预期逐位等于（新增配置不得改变既有身份）：

| 配置 | `science_identity_sha256` |
| --- | --- |
| C00-half | `2e35c17aa278120e42e9fb021b0c077e1604634f0891349d64f2a6874057220d` |
| C01-half | `d1102e2bf4cec02e0ed047126826b0298b5c51da886a77c659f38205a31f2a7c` |
| C11-half | `383457025029c09483b15972058cb5a4f886d60c782139608c78f4ad1078f231` |

任一不符即停下——说明改动越界碰到了共享结构。

- [ ] **步骤 3：把 C10 的哈希写进恢复卡并提交**

写入第三章恢复卡的缩容档小节，与上表并列。提交：

```bash
git commit -m "docs(recovery): register c10 halfwidth identity hash" -- .Codex/docs/RWKV/RWKV第三章恢复卡.md
```

---
