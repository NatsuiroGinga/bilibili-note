#!/usr/bin/env python3
"""UserPromptSubmit 钩子：按仓库 AGENTS.md「技能编排」节，把当前提示路由到应当调用的技能。

存在原因：2026-08-13 会话中，主代理把完整技能链路写进了 AGENTS.md，随后一个都没调用——
实验没连 SwanLab（导致 Lp 收敛轨迹无数据、只能退化成柱状图）、正文没走 ml-paper-writing
与 writing-anti-ai（首稿文风不合格被废）、图件没走 publication-chart-skill。
本钩子把"该调哪个技能"变成每轮可见的明文提醒，而不是依赖记忆。

输出走 stdout，Claude Code 会作为附加上下文注入本轮。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# 与仓库其余钩子（如 project_policy_guard.py）一致的仓库根定位方式：
# 本文件位于 <root>/.Codex/hooks/skill_routing_reminder.py。
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 关键词 → (阶段, 技能链路)。顺序即优先级，命中即输出，可多条命中。
ROUTES: list[tuple[tuple[str, ...], str, str]] = [
    (
        ("跑实验", "启动实验", "训练", "重跑", "train", "跑一下", "跑起来", "实验脚本"),
        "实验运行",
        "swanlab-skill（init/log/finish，workspace=mortiswang project=malicious-traffic-llm）"
        " → 跑完 results-analysis",
    ),
    (
        ("结果", "指标", "AP", "分析", "消融", "显著", "对比"),
        "实验分析",
        "results-analysis → results-report。未产出分析制品前结论只能标「实验待证」",
    ),
    (
        ("画图", "图件", "figure", "图表", "曲线", "作图"),
        "图表",
        "publication-chart-skill 定图型 → 落根 AGENTS.md「学位论文图件合同」",
    ),
    (
        ("正文", "写章节", "第三章", "第四章", "起草", "改写", "论文"),
        "正文",
        "paper-miner（仅取结构）→ ml-paper-writing → citation-verification"
        " → writing-anti-ai → paper-self-review",
    ),
    (
        # 第三方 API 触发词：库名、常见接口动词、以及"埋点/接入/调用"这类必然要碰外部 API 的动作。
        # 起因：2026-08-13 凭记忆写 swanlab.init(experiment_name=) 与 run.public.cloud.project_name，
        # 实测 0.9.0 参数为 name=、Run 无 public 属性，推上服务器首个 run 即崩。
        # 同型事故此前已发生过一次（torch.flatnonzero 不存在）。
        (
            "swanlab", "torch", "numpy", "pandas", "sklearn", "matplotlib", "pyarrow",
            "transformers", "api", "接口", "埋点", "接入", "调用", "sdk", "库",
            "参数名", "签名", "属性", "版本",
        ),
        "第三方 API",
        "npx ctx7@latest library <名称> \"<查什么>\" → npx ctx7@latest docs <ID> \"<查什么>\""
        "（强制，先查后写；等价入口 find-docs 技能）。"
        "语法检查与「以前见过」都不能证明运行时属性存在；记录库名、目标机版本、来源与签名",
    ),
    (
        ("bug", "报错", "失败", "异常", "崩", "不对", "修复", "调试"),
        "调试",
        "systematic-debugging + bug-detective 并用，一次只改一个变量",
    ),
    (
        ("实现", "写脚本", "写代码", "重构", "新功能"),
        "实现",
        "writing-plans → subagent-driven-development → daily-coding",
    ),
    (
        ("文献", "论文调研", "查重", "相关工作", "引用"),
        "文献",
        "planning-with-files 先建 task_plan.md/notes.md → literature-reviewer → citation-verification",
    ),
    (
        ("新机制", "新方法", "换方案", "创新点", "公式", "数据合同"),
        "机制构思",
        "research-ideation → brainstorming（仅此情形；常规运行不得借此重开冻结合同）",
    ),
]

BANNED = (
    "nature-writing / nature-polishing / nature-response / nature-data /"
    " latex-conference-template-organizer / mine-writing-patterns 在本中文学位论文仓库停用"
)

# --- AGENTS.md 规则文件提醒 ---------------------------------------------
# 起因：仓库规则分层（根 → 子域），进入子域前必须先读该目录的 AGENTS.md，
# 但主代理经常跳过。这里把"本轮该读哪几份"变成每轮可见的明文清单。

# 扫描时剔除的目录名：依赖缓存、构建产物、大体量运行制品目录。
# 注意 ".Codex" 本身不能排除——RWKV/过程文档规则就存放在其中。
_EXCLUDE_DIR_NAMES = frozenset(
    {
        "node_modules",
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "runs",  # thesis/experiments/llm_probe/runs：Git 忽略，数万文件
        "dist",
        "build",
        "target",
        ".cache",
    }
)

# 模块级缓存：同一进程内避免重复遍历（钩子每轮以新进程启动，
# 缓存主要防止同一次调用中意外重复扫描）。
_AGENTS_MD_CACHE: list[Path] | None = None


def _scan_agents_md() -> list[Path]:
    """递归查找仓库内所有名为 AGENTS.md 的规则文件（排除依赖/缓存/大体量目录）。"""
    global _AGENTS_MD_CACHE
    if _AGENTS_MD_CACHE is not None:
        return _AGENTS_MD_CACHE

    found: list[Path] = []
    try:
        for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
            dirnames[:] = [d for d in dirnames if d not in _EXCLUDE_DIR_NAMES]
            if "AGENTS.md" in filenames:
                found.append(Path(dirpath) / "AGENTS.md")
    except Exception:
        found = []

    _AGENTS_MD_CACHE = found
    return found


# 各 AGENTS.md 相对仓库根路径 → 一句话说明它管什么（供提醒行附注）。
_AGENTS_MD_DESCRIPTIONS: dict[str, str] = {
    "AGENTS.md": "根规则，唯一来源；研究边界、路线绑定、证据纪律、子代理分级",
    "thesis/AGENTS.md": "论文正文与方法边界，进入 llm_probe 前必读",
    "thesis/chapters/AGENTS.md": "正式章节 W0-W5 写作门禁",
    "thesis/experiments/llm_probe/AGENTS.md": "llm_probe 实验工程规则与按需合同入口",
    "thesis/experiments/llm_probe/scripts/AGENTS.md": "远程启动与脚本执行合同（SSH/同步/启动器）",
    ".Codex/docs/AGENTS.md": "过程文档与归档规则",
    ".Codex/docs/RWKV/AGENTS.md": "RWKV 路线规则，取代根目录 PINN/R2 默认恢复路径",
    "raw/AGENTS.md": "原始材料不可变原件层规则",
    "wiki/AGENTS.md": "Obsidian 知识层规则，知识写回边界",
    "output/AGENTS.md": "高层交付与恢复文档规则",
}

# 关键词 → 命中时应追加提醒的 AGENTS.md 相对路径（相对仓库根）。
# 顺序即优先级；根 AGENTS.md 永远单独追加，不放在这张表里。
_AGENTS_MD_ROUTES: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (
        (
            "正文", "写章节", "章节写作", "改写章节", "起草正文", "摘要",
            "绪论", "总结与展望", "第一章", "第二章", "第三章", "第四章",
            "第五章", "第六章", "w0", "w1", "w2", "w3", "w4", "w5",
        ),
        ("thesis/AGENTS.md", "thesis/chapters/AGENTS.md"),
    ),
    (
        (
            "跑实验", "启动实验", "训练", "重跑", "train", "实验脚本",
            "llm_probe", "swanlab", "消融", "调参", "推理", "物化",
        ),
        ("thesis/experiments/llm_probe/AGENTS.md",),
    ),
    (
        ("远程", "ssh", "同步", "rsync", "启动器", "服务器", "脚本"),
        ("thesis/experiments/llm_probe/scripts/AGENTS.md",),
    ),
    (
        ("文献", "论文调研", "查重", "相关工作", "引用", "zotero", "pdf", "原件"),
        ("raw/AGENTS.md",),
    ),
    (
        ("笔记", "知识库", "wiki", "obsidian", "结构化笔记"),
        ("wiki/AGENTS.md",),
    ),
    (
        (
            "过程文档", "计划文档", "任务计划", "task_plan", "notes.md",
            "登记册", "检查点", "恢复卡", "归档",
        ),
        (".Codex/docs/AGENTS.md",),
    ),
    (
        ("开题改进交接文档", "第一创新点实验总控", "恢复文档", "交接文档"),
        ("output/AGENTS.md",),
    ),
    (
        ("rwkv", "research_route"),
        (".Codex/docs/RWKV/AGENTS.md",),
    ),
]

# 单轮最多额外列出的子域 AGENTS.md 数（根文件不计入），防止极端多关键词
# 命中时把提醒撑爆，挤占真实上下文（总输出需控制在 40 行以内）。
_MAX_EXTRA_AGENTS_FILES = 6


def _build_agents_reminder(prompt: str) -> str:
    """按提示关键词命中，生成"本轮须先读的规则文件"提醒段。"""
    try:
        files = _scan_agents_md()
        if not files:
            return ""

        by_rel: dict[str, Path] = {}
        for path in files:
            try:
                rel = path.relative_to(PROJECT_ROOT).as_posix()
            except Exception:
                continue
            by_rel[rel] = path

        prompt_lower = prompt.lower()
        selected: list[str] = []
        if "AGENTS.md" in by_rel:
            selected.append("AGENTS.md")

        for keys, rels in _AGENTS_MD_ROUTES:
            if len(selected) - 1 >= _MAX_EXTRA_AGENTS_FILES:
                break
            if not any(k in prompt_lower for k in keys):
                continue
            for rel in rels:
                if rel in by_rel and rel not in selected:
                    selected.append(rel)

        if not selected:
            return ""

        lines = ["", "=== 本轮须先读的规则文件 ==="]
        for rel in selected:
            abs_path = str(by_rel[rel])
            desc = _AGENTS_MD_DESCRIPTIONS.get(rel, "子域规则，进入该目录前须先读")
            lines.append(f"  {abs_path}    （{desc}）")
        lines.append(
            "规则加载：从项目根走到当前目录，每层只加载第一份，"
            "近层优先，组合上限 32,768 字节。"
        )
        return "\n".join(lines)
    except Exception:
        return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(payload, dict):
        return 0
    prompt = str(payload.get("prompt", ""))
    if not prompt.strip():
        return 0

    try:
        hits = [
            (stage, chain)
            for keys, stage, chain in ROUTES
            if any(k in prompt for k in keys)
        ]

        lines = ["=== 技能编排提醒（AGENTS.md「技能编排」节，强制）==="]
        if hits:
            lines.append("本轮命中的阶段与应调技能：")
            for stage, chain in hits:
                lines.append(f"  [{stage}] {chain}")
            lines.append("")
            lines.append("调用方式：Skill 工具，名称取自可用技能清单。跳过链路属违规，")
            lines.append("与仓库规则冲突时须显式说明冲突点与采纳理由，不得静默略过。")
        else:
            lines.append("未命中特定阶段。若本轮涉及实验、分析、图表、正文或调试，")
            lines.append("先对照 AGENTS.md「技能编排」表确认应调技能，再动手。")
        lines.append(f"停用清单：{BANNED}")
        lines.append("全程沟通遵循 expression-skill：结论优先、给证据路径、早暴露风险。")
        lines.append("=" * 46)

        agents_reminder = _build_agents_reminder(prompt)
        if agents_reminder:
            lines.append(agents_reminder)

        print("\n".join(lines))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
