#!/usr/bin/env python3
"""低成本、幂等地刷新 `.Codex/docs/PROJECT_INDEX.{md,json}`。"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


MARKER_START = "<!-- GENERATED_START: project-index-v1 -->"
MARKER_END = "<!-- GENERATED_END: project-index-v1 -->"
DEBOUNCE_SECONDS = 20
EXCLUDED_PARTS = {".git", "raw", "runs", "cache", "vendor", "deps", "archive", "__pycache__"}
EXCLUDED_NAMES = {"PROJECT_INDEX.md", "PROJECT_INDEX.json", ".project-index.dirty", ".project-index.lock"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def entry(path: str, role: str, status: str, priority: str, summary: str, generated: bool = False) -> dict[str, Any]:
    return {"path": path, "role": role, "status": status, "priority": priority, "summary": summary, "generated": generated}


def known_entries() -> list[dict[str, Any]]:
    return [
        entry(".Codex/docs/DRIFT/DRIFT第三章恢复卡.md", "DRIFT第三章恢复", "当前", "P0", "当前状态、否决项与唯一下一动作"),
        entry(".Codex/docs/DRIFT/DRIFT路线总控.md", "DRIFT路线总控", "当前", "P0", "DRIFT独立恢复与公共合同"),
        entry(".Codex/docs/DRIFT/AGENTS.md", "DRIFT局部规则", "当前", "P0", "三类规范材料强制恢复链"),
        entry(".Codex/docs/DRIFT/CLAUDE.md", "Claude规则导入", "当前", "P1", "通过@AGENTS.md同步DRIFT规则"),
        entry(".Codex/docs/DRIFT/DRIFT历史交接入口.md", "DRIFT历史入口", "当前", "P2", "仅冲突与制品追溯时读取"),
        entry(".Codex/docs/RWKV/RWKV第三章恢复卡.md", "RWKV第三章恢复", "历史", "P2", "DRIFT已迁出；既有DRIFT段落仅迁移快照"),
        entry("thesis/methods/第三章-数据模型机制统一候选筛选台账.md", "候选状态", "当前", "P0", "第三章候选唯一状态入口"),
        entry(".Codex/docs/RWKV/RWKV路线总控.md", "公共边界", "当前", "P1", "RWKV路线恢复与跨章约束"),
        entry("AGENTS.md", "全仓规则", "当前", "P0", "证据、隔离、种子与Astra门"),
        entry(".Codex/docs/2026-09-08-DRIFT逻辑路线隔离/Goal替换建议.md", "DRIFT Goal", "待设置", "P0", "统一主方法；因素数量由证据决定", True),
        entry(".Codex/docs/2026-09-08-DRIFT逻辑路线隔离/迁移报告.md", "DRIFT迁移收据", "当前", "P1", "逻辑隔离范围与验证", True),
        entry(".Codex/docs/2026-09-07-长Goal规则迁移/报告.md", "旧长Goal合同", "历史", "P2", "旧双机制与2x2要求已被原文分析修正", True),
        entry("thesis/methods/第三章-DRIFT数据角色与评价协议.md", "DRIFT数据合同", "当前", "P0", "T17至T19冻结；T20至T25整批正式评价"),
        entry("thesis/methods/第三章-DRIFT方案A研究问题卡与最小证伪设计.md", "DRIFT研究问题", "当前", "P1", "M1与第二方向最小证伪"),
        entry("thesis/methods/第三章-朱焱雷第三章机制构思与创新声明分析.md", "章节结构参照", "当前", "P1", "整体创新主语与条件性2x2"),
        entry("raw/papers/datasets/2026-Lee-DRIFT-DGA-Temporal-Drift.pdf", "DRIFT原论文", "当前", "P0", "原始全文事实源"),
        entry("wiki/papers/datasets/2026-Lee-DRIFT-DGA-Temporal-Drift.md", "DRIFT全文分析", "当前", "P0", "数据、方法、结果与复现边界"),
        entry(".Codex/docs/2026-09-07-DGA检测系统综述/文献综述.md", "DGA系统综述", "当前", "P0", "低误报、未见家族与强基线"),
        entry(".Codex/docs/2026-09-07-DRIFT引用与方法前沿/文献综述.md", "DRIFT前沿综述", "当前快照", "P0", "引用版图、近邻与剩余差量"),
        entry(".Codex/docs/2026-09-07-跨年数据集替代调研/数据集比较综述.md", "数据集选型台账", "当前快照", "P1", "替换任务先读；禁止重新广筛", True),
        entry(".Codex/docs/2026-09-07-DRIFT方案A最小证伪实验/M1-v2投影原始对偶研究卡.md", "M1-v2证伪", "已批准短窗", "P0", "仅T17的32步短窗与一次验证", True),
        entry(".Codex/docs/2026-09-07-DRIFT方案A最小证伪实验/第二机制竞争简报.md", "第二方向证伪", "待诊断", "P0", "T17伪未见family零更新诊断", True),
        entry(".Codex/docs/2026-09-07-DRIFT零训练数据探针/可行性报告.md", "数据门", "进行中", "P1", "DRIFT资格与零训练前提", True),
        entry(".Codex/docs/2026-09-07-跨年数据集替代调研/数据集比较综述.md", "数据候选", "当前", "P1", "真实网络安全泛化轴候选", True),
        entry(".Codex/docs/2026-09-07-RWKV8-ROSA-DeepEmbed候选审查/候选机制综述与实验建议.md", "机制来源", "待核", "P1", "ROSA等机制的可试性", True),
        entry(".Codex/docs/2026-09-07-DRIFT零训练双探针/task_plan.md", "探针执行", "进行中", "P0", "分面抽样后真实pilot", True),
        entry(".Codex/docs/2026-09-07-DRIFT零训练双探针/实现报告.md", "实现证据", "待核", "P0", "仅静态检查，无真实结果", True),
        entry(".Codex/docs/2026-09-07-DRIFT引用与方法前沿/notes.md", "文献阶段记录", "进行中", "P1", "仅已落盘阶段结论", True),
        entry("thesis/experiments/llm_probe/tools/ch3_drift_rosa_deepembed_probe.py", "零训练探针", "待核", "P0", "pilot后才可冻结正式抽样"),
        entry("thesis/experiments/llm_probe/configs/ch3-drift-t17-t25-rosa-deepembed-coverage-probe-v1.json", "探针配置", "当前", "P0", "DRIFT revision和四分面声明"),
        entry("tools/update_project_index.py", "索引生成器", "当前", "P1", "幂等刷新、脏标记和会话结束回退"),
        entry("thesis/experiments/llm_probe/tools/INDEX.md", "代码导航", "当前", "P1", "工具职责索引", True),
        entry("thesis/methods/第三章定案.md", "旧路线追溯", "历史", "P2", "不指挥当前实验"),
        entry("wiki/INDEX.md", "已入库文献", "当前", "P1", "结构化全文笔记导航", True),
        entry("wiki/papers/rwkv/INDEX.md", "RWKV文献", "当前", "P1", "RWKV原件与笔记", True),
        entry(".Codex/docs/AGENTS.md", "过程规则", "当前", "P0", "过程文档与敏感边界"),
        entry(".Codex/docs/RWKV/AGENTS.md", "RWKV局部规则", "当前", "P0", "恢复与追溯条件"),
        entry(".Codex/docs/2026-09-07-第三章恢复卡方向重置/报告.md", "迁移收据", "当前", "P1", "方向重置核验", True),
        entry(".Codex/docs/RWKV/2026-09-04-第三章恢复卡过期内容归档.md", "历史证据", "归档", "P3", "旧候选与操作追溯"),
    ]


def included(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if any(part in EXCLUDED_PARTS for part in relative.parts) or path.name in EXCLUDED_NAMES:
        return False
    if path.suffix not in {".md", ".py", ".json"}:
        return False
    return str(relative).startswith((".Codex/docs/", "thesis/methods/", "thesis/experiments/llm_probe/tools/", "thesis/experiments/llm_probe/configs/", "wiki/")) or relative.as_posix() == "tools/update_project_index.py"


def inventory(root: Path) -> tuple[list[dict[str, Any]], str]:
    records: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    scopes = [root / ".Codex/docs", root / "thesis/methods", root / "thesis/experiments/llm_probe/tools", root / "thesis/experiments/llm_probe/configs", root / "wiki", root / "tools"]
    for scope in scopes:
        if not scope.exists():
            continue
        for path in sorted(scope.rglob("*")):
            if not path.is_file() or not included(path, root):
                continue
            relative = path.relative_to(root).as_posix()
            stat = path.stat()
            # 小文档与入口代码按内容哈希；大文件只保留大小，避免索引任务抢占实验 I/O。
            content = hashlib.sha256(path.read_bytes()).hexdigest() if stat.st_size <= 1_000_000 else "large"
            record = {"path": relative, "bytes": stat.st_size, "sha256": content}
            records.append(record)
            digest.update(json.dumps(record, ensure_ascii=False, sort_keys=True).encode())
    return records, digest.hexdigest()


def atomic_write(path: Path, data: str) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def manual_markdown(path: Path) -> str:
    if not path.exists():
        return "## 人工补充\n\n<!-- 手工维护内容写在此处；自动刷新不得覆盖本节。 -->\n"
    text = path.read_text(encoding="utf-8")
    if MARKER_START not in text or MARKER_END not in text:
        return "## 人工补充\n\n<!-- 原文件缺少生成标记，人工内容未自动迁移。 -->\n"
    return text.split(MARKER_END, 1)[1].lstrip("\n")


def relative_link(path: str) -> str:
    target = Path("../..") / path
    return target.as_posix()


def table(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["| 路径 | 角色 | 状态 | 优先级 | 简述 |", "|---|---|---|---|---|"]
    for item in rows:
        label = Path(item["path"]).name
        lines.append(f"| [{label}]({relative_link(item['path'])}) | {item['role']} | {item['status']} | {item['priority']} | {item['summary']} |")
    return lines


def render(entries: list[dict[str, Any]], unknown: list[str], fingerprint: str) -> str:
    by_path = {item["path"]: item for item in entries}
    groups = [
        ("当前权威入口", [".Codex/docs/DRIFT/DRIFT第三章恢复卡.md", ".Codex/docs/DRIFT/DRIFT路线总控.md", "thesis/methods/第三章-DRIFT数据角色与评价协议.md", "thesis/methods/第三章-数据模型机制统一候选筛选台账.md", "AGENTS.md"]),
        ("当前 Goal 制品", [".Codex/docs/2026-09-08-DRIFT逻辑路线隔离/Goal替换建议.md", "thesis/methods/第三章-DRIFT方案A研究问题卡与最小证伪设计.md", "thesis/methods/第三章-朱焱雷第三章机制构思与创新声明分析.md"]),
        ("进行中任务", [".Codex/docs/2026-09-07-DRIFT方案A最小证伪实验/M1-v2投影原始对偶研究卡.md", ".Codex/docs/2026-09-07-DRIFT方案A最小证伪实验/第二机制竞争简报.md", ".Codex/docs/2026-09-08-DRIFT逻辑路线隔离/迁移报告.md"]),
        ("实验代码、配置与结果", ["thesis/experiments/llm_probe/tools/ch3_drift_rosa_deepembed_probe.py", "thesis/experiments/llm_probe/configs/ch3-drift-t17-t25-rosa-deepembed-coverage-probe-v1.json", "tools/update_project_index.py", "thesis/experiments/llm_probe/tools/INDEX.md"]),
        ("论文方法文档", ["thesis/methods/第三章-数据模型机制统一候选筛选台账.md", "thesis/methods/第三章定案.md"]),
        ("文献综述", ["raw/papers/datasets/2026-Lee-DRIFT-DGA-Temporal-Drift.pdf", "wiki/papers/datasets/2026-Lee-DRIFT-DGA-Temporal-Drift.md", ".Codex/docs/2026-09-07-DGA检测系统综述/文献综述.md", ".Codex/docs/2026-09-07-DRIFT引用与方法前沿/文献综述.md", ".Codex/docs/2026-09-07-跨年数据集替代调研/数据集比较综述.md"]),
        ("规则与恢复", [".Codex/docs/AGENTS.md", ".Codex/docs/DRIFT/AGENTS.md", ".Codex/docs/DRIFT/CLAUDE.md", ".Codex/docs/DRIFT/DRIFT路线总控.md", ".Codex/docs/DRIFT/DRIFT历史交接入口.md", ".Codex/docs/RWKV/AGENTS.md", ".Codex/docs/RWKV/RWKV路线总控.md"]),
        ("历史归档", [".Codex/docs/RWKV/RWKV第三章恢复卡.md", ".Codex/docs/2026-09-07-长Goal规则迁移/报告.md", ".Codex/docs/RWKV/2026-09-04-第三章恢复卡过期内容归档.md"]),
    ]
    lines = ["# 项目统一索引", "", "仅导航，不替代恢复卡、候选台账或原始制品。", "", MARKER_START]
    for title, paths in groups:
        rows = [by_path[path] for path in paths if path in by_path]
        lines.extend([f"## {title}", ""] + table(rows) + [""])
    if unknown:
        lines.extend(["## 新增待核文档", "", f"检测到 {len(unknown)} 个未分类受管文档；先由人工确认角色与状态。", ""])
        for path in unknown[:5]:
            lines.append(f"- [{Path(path).name}]({relative_link(path)})")
        lines.append("")
    lines.extend([f"内容清单哈希：`{fingerprint}`。", MARKER_END, ""])
    return "\n".join(lines)


def refresh(root: Path) -> bool:
    docs = root / ".Codex/docs"
    markdown_path = docs / "PROJECT_INDEX.md"
    json_path = docs / "PROJECT_INDEX.json"
    records, fingerprint = inventory(root)
    old = read_json(json_path)
    if old.get("content_manifest_sha256") == fingerprint:
        return False
    entries = [item for item in known_entries() if (root / item["path"]).exists()]
    known = {item["path"] for item in entries}
    unknown = [item["path"] for item in records if item["path"] not in known]
    payload = {"schema_version": "project-index-v2", "content_manifest_sha256": fingerprint, "generated_at": int(time.time()), "manual": old.get("manual", {}), "entries": entries, "unclassified_count": len(unknown), "unclassified_paths": unknown[:20]}
    markdown = render(entries, unknown, fingerprint) + "\n" + manual_markdown(markdown_path)
    atomic_write(json_path, json.dumps(payload, ensure_ascii=False, separators=(",", ":"), indent=2) + "\n")
    atomic_write(markdown_path, markdown)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mark-dirty", action="store_true", help="标记文档变动，供防抖刷新使用")
    parser.add_argument("--refresh-if-dirty", action="store_true", help="仅在脏标记超过防抖窗口后刷新")
    parser.add_argument("--force", action="store_true", help="立即刷新，忽略脏标记年龄")
    parser.add_argument("--schedule", action="store_true", help="标脏后在短防抖窗口结束时异步刷新")
    parser.add_argument("--delay-seconds", type=float, default=0.0, help="刷新前等待，仅供异步防抖子进程使用")
    parser.add_argument("--wait-seconds", type=float, default=0.0, help="等待互斥锁的最长时间")
    args = parser.parse_args()
    root = repo_root(); docs = root / ".Codex/docs"; dirty = docs / ".project-index.dirty"; lock_path = docs / ".project-index.lock"
    if args.mark_dirty:
        dirty.touch(exist_ok=True)
        if args.schedule:
            subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--refresh-if-dirty", "--force", "--delay-seconds", str(DEBOUNCE_SECONDS)], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
        return 0
    if args.delay_seconds > 0:
        time.sleep(args.delay_seconds)
    if args.refresh_if_dirty and not dirty.exists(): return 0
    if args.refresh_if_dirty and not args.force and time.time() - dirty.stat().st_mtime < DEBOUNCE_SECONDS: return 0
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 75
        try:
            changed = refresh(root)
            if dirty.exists(): dirty.unlink()
            print("已刷新" if changed else "内容未变")
            return 0
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


if __name__ == "__main__":
    raise SystemExit(main())
