"""SessionStart 钩子：检测"这台机器/这个环境是否还没准备好"，并指向迁移说明。

设计原则（按仓库规则「靠脚本不靠记性」）：
- **永不阻断会话**：任何异常都吞掉，始终 exit 0。
- **只在缺东西时说话**：环境完整时静默，避免每次开新会话都刷屏。
- **输出即上下文**：SessionStart 钩子的 stdout 会进入会话上下文。

检测三项：
1. 数据集目录是否存在（`runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767`）
2. 关键自建技能是否已恢复（`~/.claude/skills/<name>/SKILL.md`）
3. 本机的 `LAMDA_DATA_ROOT` 是否已设置

任一项缺失 ⇒ 打印一段指向 `新机器快速上手.md` 与 `bootstrap/README.md` 的提示。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

DATASET_DIRNAME = "lamda-iclr2026-baseline-ad9614bdd5556767"
REQUIRED_SKILLS = (
    "daily-coding",
    "results-analysis",
    "paper-self-review",
    "ml-paper-writing",
    "citation-verification",
)


def repo_root() -> Path:
    here = Path(__file__).resolve()
    # .Codex/hooks/<this file> -> 仓库根
    return here.parents[2]


def main() -> int:
    try:
        root = repo_root()
        problems: list[str] = []

        # 数据可能在仓库内，也可能通过 LAMDA_DATA_ROOT 指向别处（例如另一个 worktree）。
        # 两者任一可用即视为就位——否则本机会每次开会话都误报。
        local_data = root / "thesis/experiments/llm_probe/runs/data-raw" / DATASET_DIRNAME
        env_root = os.environ.get("LAMDA_DATA_ROOT", "").strip()
        env_ok = bool(env_root) and Path(env_root).is_dir()
        if not local_data.is_dir() and not env_ok:
            problems.append("数据集未就位（仓库内与 LAMDA_DATA_ROOT 均不可用）")
            problems.append(
                "  取法：/opt/miniconda3/envs/rwkv/bin/python "
                "thesis/experiments/llm_probe/scripts/download_lamda_baseline.py"
            )

        skills_dir = Path.home() / ".claude" / "skills"
        missing = [s for s in REQUIRED_SKILLS if not (skills_dir / s / "SKILL.md").is_file()]
        if missing:
            problems.append(f"技能未恢复（缺 {len(missing)} 个：" + "、".join(missing) + "）")
            problems.append("  恢复：bash bootstrap/restore.sh")

        if not os.environ.get("LAMDA_DATA_ROOT"):
            problems.append("环境变量 LAMDA_DATA_ROOT 未设置")

        if not problems:
            return 0

        print("【环境未就绪】本会话检测到下列缺失，若这是新机器请先完成迁移：")
        for p in problems:
            print(p)
        print("完整步骤见：新机器快速上手.md")
        print("搬运范围与边界见：bootstrap/README.md")
        print("验证门槛：基线复现的 12 年平均 F1 必须等于 0.8170，对不上就停。")
    except Exception:
        # 钩子永不阻断会话
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
