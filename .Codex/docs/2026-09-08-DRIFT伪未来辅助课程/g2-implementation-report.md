# N12 G2 严格 family 隔离短步实现报告

## 技能收据

- 读取时间（UTC）：`2026-09-08T07:02:28Z`
- `/Users/bilibili/.codex/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/subagent-driven-development/SKILL.md`：SHA-256 `8dd1b8e698edec3700c6d89517dbe96febd3bacd3f6ea21c1a3569c62ea104b5`
- `/Users/bilibili/.codex/skills/backup/daily-coding-20260811-112930/SKILL.md`：SHA-256 `da2399b50859b9d57281b9bc0dc456082db93d47486ae22967ebf3f17d354ae3`
- `/Users/bilibili/.codex/skills/pytorch-patterns/SKILL.md`：SHA-256 `22b76f559f17d4b0e44eda71d353065e5da181203d165546edb08c16cc362d85`

## 实施范围

- 已创建：G2 Python 单入口、冻结配置与远程启动器。
- 不修改：G0、G1、P0、研究卡、路线总控、恢复卡和既有运行制品。
- 科学状态：实现与静态入口检查不能支持课程有效性；仅真实 T17 G2 运行的闭合制品可进入冻结停止门。

## 验证记录

- 通过：`/opt/miniconda3/envs/rwkv/bin/python -m py_compile tools/ch3_drift_n12_g2_family_isolated_short_step.py`。
- 通过：`/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_n12_g2_family_isolated_short_step.py --help`。
- 通过：模块导入并输出 `ch3-drift-n12-g2-family-isolated-short-step-v1`。
- 通过：`jq empty configs/ch3-drift-n12-g2-family-isolated-short-step-v1.json`。
- 通过：`bash -n scripts/remote_launchers/run_ch3_drift_n12_g2_family_isolated_short_step_v1.sh`。
- 通过：计划范围内 `git diff --check`。
