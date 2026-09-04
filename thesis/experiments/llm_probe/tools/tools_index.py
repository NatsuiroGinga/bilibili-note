# -*- coding: utf-8 -*-
"""tools/ 目录索引生成器：只读扫描本目录，把结果写成 tools/INDEX.md。

背景：tools/ 下 143 个顶层 .py 脚本互相用裸 `import xxx` 引用，依赖 Python 把
`tools/` 自动加入 sys.path；同时 27 份冻结实验配置记录了 `base.tool_path` 与
`tool_sha256`，认的是文件的当前路径与内容哈希。这两点决定了 tools/ 在四格实验
跑完、单独立项重组之前必须保持"不移动、不改名、不删除"——本生成器因此只做
"加索引"这一件事，绝不改写、移动或删除任何被扫描的文件。

用法：
    /opt/miniconda3/envs/rwkv/bin/python tools/tools_index.py
    # 或从仓库根：
    /opt/miniconda3/envs/rwkv/bin/python thesis/experiments/llm_probe/tools/tools_index.py

输出：tools/INDEX.md（幂等——相同输入产出逐字节相同的文件，不含时间戳等易变量）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, Optional

TOOLS_DIR = Path(__file__).resolve().parent
SELF_NAME = Path(__file__).name
INDEX_PATH = TOOLS_DIR / "INDEX.md"

# ---------------------------------------------------------------------------
# 角色分类规则
#
# 判定顺序（先命中先得）：一次性审计 → 诊断探针 → 评价与指标 → 数据物化与视图
# → 兜底（按“是否可执行”分训练入口 / 机制实现）。
#
# 关键词只匹配"文件名（不含扩展名，小写）+ docstring 首句"这一小段文本，不用
# 整份 docstring —— 实测发现扩大到全文档字符串后，"eval"/"诊断"等词会命中大量
# 背景说明段落里的无关提及（例如某脚本背景里提到 `model.eval()` 或"验证集"），
# 造成误分类；首句是作者自己写的一句话摘要，信噪比明显更高。
ROLE_ORDER = [
    "entrypoint",
    "mechanism",
    "eval",
    "data_view",
    "probe",
    "ops",
    "audit",
]

ROLE_LABELS = {
    "entrypoint": "训练入口",
    "mechanism": "机制实现",
    "eval": "评价与指标",
    "data_view": "数据物化与视图",
    "probe": "诊断探针",
    "ops": "远程与运维",
    "audit": "一次性审计",
}

# 一次性审计：核验/核实历史决策、修复历史产物、判定制品完整性的一次性脚本。
AUDIT_KW = [
    "audit", "qualification", "apicheck", "recon", "repair",
    "recovery_proof", "verify", "tier_identity", "read_mlp_ref",
    "measure_we_probe_costs", "validate_swanlab_contracts", "grouping_recon",
    "自检", "只读核实", "核验", "核对", "复核", "勘察", "侦察", "收据", "机械阻断",
]

# 诊断探针：只读判定某个现象/差异/性能的成因，不产生正式训练制品。
PROBE_KW = ["_probe", "diagnostic", "benchmark", "诊断", "探针"]

# 评价与指标：从既有制品重算/汇总/统计指标，不训练新模型。
EVAL_KW = [
    "eval", "metrics", "metric_table", "gap_ci", "f1_column",
    "alert_budget", "fp_budget", "crossyear_f1", "build_metrics",
    "operational_backfill", "级评价",
]

# 数据物化与视图：产出/整理供下游消费的数据制品，不训练模型。
DATA_KW = [
    "materialize", "ingest", "prepare", "field_manifest", "partition",
    "sidecar", "raw83_prepare", "固化", "物化",
]

# 远程与运维：服务器同步、GPU 环境、rsync/ssh 一类运维脚本（top-level .py 目前
# 没有命中项，该分组主要服务子目录里的 .sh/.exp 文件）。
OPS_KW = ["remote", "rsync", "ssh", "gpu_env", "deploy_", "push_and_run"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def count_lines(text: str) -> int:
    return len(text.splitlines())


def get_module_docstring(text: str) -> Optional[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    return ast.get_docstring(tree)


_SENTENCE_END_CHARS = "。！？!?"
_MAX_SENTENCE_CHARS = 160


def first_sentence(doc: Optional[str]) -> str:
    """取 docstring 首段，按句末标点截到第一句。

    首段＝docstring 开头到第一个空行之间的所有行拼接（不能只看第一行——第一句
    经常跨行换行，例如"...F1，\\n 按..."只取第一行会在逗号处断句）。
    句末标点只认中文 `。` 与 `!?`，**不认 ASCII 句点 `.`**——本语料库的 `.` 几乎全部
    出现在小数（`5.9`、`2.4e-4`）、模块路径（`torch.compile`）或文件名
    （`ch3_full.py`）里，用它分句会把"对齐 Dijk 2026 §5.9 训练协议"截成
    "对齐 Dijk 2026 §5."这类残句。
    """
    if not doc:
        return ""
    doc = doc.strip()
    if not doc:
        return ""
    paragraph_lines = []
    for line in doc.splitlines():
        if line.strip() == "":
            break
        paragraph_lines.append(line.strip())
    if not paragraph_lines:
        paragraph_lines = [doc.splitlines()[0].strip()]
    paragraph = " ".join(paragraph_lines)

    end = -1
    for i, ch in enumerate(paragraph):
        if ch in _SENTENCE_END_CHARS:
            end = i
            break
    sentence = paragraph[: end + 1] if end >= 0 else paragraph_lines[0]
    if len(sentence) > _MAX_SENTENCE_CHARS:
        sentence = sentence[:_MAX_SENTENCE_CHARS].rstrip() + "…"
    return sentence


def _is_main_guard(node: ast.stmt) -> bool:
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if not isinstance(test, ast.Compare):
        return False
    values = []
    for side in [test.left, *test.comparators]:
        if isinstance(side, ast.Name):
            values.append(side.id)
        elif isinstance(side, ast.Constant):
            values.append(side.value)
    return "__name__" in values and "__main__" in values


def _is_simple_assign(node: ast.stmt) -> bool:
    if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        return False
    val = getattr(node, "value", None)
    if val is None:
        return True
    simple_types = (ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Set, ast.Name, ast.Attribute)
    if isinstance(val, simple_types):
        return True
    if isinstance(val, ast.UnaryOp) and isinstance(val.operand, ast.Constant):
        return True
    if isinstance(val, ast.BinOp):
        return True
    return False


def analyze_executable(text: str) -> tuple[bool, int]:
    """返回 (是否有 `if __name__==\"__main__\"` 守卫, 模块顶层"实质执行语句"计数)。

    第二项用于识别历史上写成"从上到下线性执行、没有 __main__ 守卫"的冻结协议脚本
    （例如 ch3_backbone_protocolA.py）——它们 import 即执行，属于可执行入口，
    但用 `if __name__` 判断会被误判成"库模块"。顶层出现 for/while/with/try，
    或对非简单常量的调用型赋值，达到阈值即视为"无守卫的可执行入口"。
    实测：真正的纯定义模块（如 ch3_backbone_models.py）该计数为 0-1；
    无守卫入口脚本普遍在 12 以上，阈值取 3 有清晰间隔。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False, 0
    has_guard = False
    exec_count = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef,
                              ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue  # 模块 docstring
        if isinstance(node, ast.If):
            if _is_main_guard(node):
                has_guard = True
                continue
            exec_count += 1
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            if _is_simple_assign(node):
                continue
            exec_count += 1
            continue
        exec_count += 1
    return has_guard, exec_count


def is_executable(text: str) -> bool:
    has_guard, exec_count = analyze_executable(text)
    return has_guard or exec_count >= 3


def classify_role(stem: str, doc_first_sentence: str, executable: bool) -> str:
    haystack = f"{stem} {doc_first_sentence}".lower()

    def hit(keywords: Iterable[str]) -> bool:
        return any(kw.lower() in haystack for kw in keywords)

    if hit(AUDIT_KW):
        return "audit"
    if hit(PROBE_KW):
        return "probe"
    if hit(EVAL_KW):
        return "eval"
    if hit(DATA_KW):
        return "data_view"
    if hit(OPS_KW):
        return "ops"
    return "entrypoint" if executable else "mechanism"


class PyRecord:
    __slots__ = ("rel_path", "name", "lines", "doc_sentence", "has_doc", "executable", "role")

    def __init__(self, path: Path, rel_to: Path):
        text = read_text(path)
        self.rel_path = path.relative_to(rel_to).as_posix()
        self.name = path.name
        self.lines = count_lines(text)
        doc = get_module_docstring(text)
        self.has_doc = doc is not None and doc.strip() != ""
        self.doc_sentence = first_sentence(doc) if self.has_doc else ""
        self.executable = is_executable(text)
        self.role = classify_role(path.stem, self.doc_sentence, self.executable)


def collect_top_level() -> list[PyRecord]:
    records = []
    for path in sorted(TOOLS_DIR.glob("*.py")):
        records.append(PyRecord(path, TOOLS_DIR))
    return records


NON_PY_TYPE_LABELS = {
    ".rs": "Rust 源码",
    ".toml": "Cargo 配置",
    ".lock": "依赖锁文件",
    ".json": "JSON 配置/模式",
    ".md": "文档",
    ".sh": "Shell 脚本",
    ".exp": "expect 脚本",
}


def describe_non_py(path: Path) -> str:
    """对非 .py 文件做尽量便宜的一句话说明抽取（Rust 模块注释 / shell 首条注释）。"""
    suffix = path.suffix.lower()
    try:
        text = read_text(path)
    except Exception:
        return ""
    lines = text.splitlines()
    if suffix == ".rs":
        # 只认 `//!` 模块级文档注释，不用 `///`——`///` 挂在紧随其后的具体条目
        # （某个 struct/enum/const）上，不代表整个文件，实测抓到会文不对题
        # （例如把某个错误枚举的注释当成了文件说明）。
        for line in lines[:20]:
            s = line.strip()
            if s.startswith("//!"):
                text = s[3:].strip()
                if text:
                    return text
        return ""
    if suffix in (".sh", ".exp"):
        for line in lines[:20]:
            s = line.strip()
            if s.startswith("#!"):
                continue
            if s.startswith("#"):
                return s.lstrip("#").strip()
            if s:
                break
        return ""
    return ""


class OtherRecord:
    __slots__ = ("rel_path", "name", "suffix", "lines", "note")

    def __init__(self, path: Path, rel_to: Path):
        self.rel_path = path.relative_to(rel_to).as_posix()
        self.name = path.name
        self.suffix = path.suffix.lower()
        try:
            self.lines = count_lines(read_text(path))
        except Exception:
            self.lines = 0
        self.note = describe_non_py(path)


# __pycache__ 是 Python 字节码缓存：.gitignore 已排除、内容可随时从源码重新生成、
# 逐个 .pyc 列出来没有任何可读价值，扫描时整目录跳过。
SKIP_DIR_NAMES = {"__pycache__"}


def collect_subdirs() -> list[tuple[Path, list[PyRecord], list[OtherRecord]]]:
    result = []
    for sub in sorted(p for p in TOOLS_DIR.iterdir() if p.is_dir() and p.name not in SKIP_DIR_NAMES):
        py_records = []
        other_records = []
        for path in sorted(sub.rglob("*")):
            if path.is_dir():
                continue
            if SKIP_DIR_NAMES & set(path.relative_to(sub).parts[:-1]):
                continue
            if path.suffix == ".py":
                py_records.append(PyRecord(path, sub))
            else:
                other_records.append(OtherRecord(path, sub))
        result.append((sub, py_records, other_records))
    return result


SUBDIR_NOTES = {
    "_resume_audit": "断点续训一致性核验：比较 selected.pt/inflight.pt 检查点并驱动重跑场景（一次性审计）。",
    "ch3_final_weights_assets": "第三章定稿模型（协议 A 四格）权重的推理资产与说明（数据物化与视图）。",
    "dijk2026_replication": "Dijk 2026（SSRN 6597680）复现的数据读取层、只读勘察脚本与运行驱动 shell（数据物化与视图 + 一次性审计 + 远程与运维混合，逐文件角色见下表）。",
    "env": "服务器 venv 激活脚本（远程与运维）。",
    "lspr24_g0": "LSPR24 物化管线 Rust crate：canonical 化、字段清单、外部排序、G0 资格门与跨年物化（数据物化与视图）。",
    "r2_genis_totbytes_verifier": "pcap 总字节数校验 Rust crate（一次性审计）。",
    "r2_quic_qlog_audit": "QUIC qlog 审计 Rust crate（一次性审计）。",
    "remote_exec": "GPU 服务器环境探测与 rsync 推拉 expect 脚本（远程与运维）。",
}


def shell_role_note(name: str) -> str:
    lname = name.lower()
    if any(kw in lname for kw in ("remote", "rsync", "ssh", "push", "pull", "gpu_env")):
        return "远程与运维"
    if any(kw in lname for kw in ("recon", "audit")):
        return "一次性审计（勘察/核验类驱动脚本）"
    return "驱动脚本"


def render_top_level_section(records: list[PyRecord]) -> str:
    by_role: dict[str, list[PyRecord]] = {r: [] for r in ROLE_ORDER}
    for rec in records:
        by_role[rec.role].append(rec)

    lines = ["## 顶层模块索引（按角色分组）", ""]
    for role in ROLE_ORDER:
        group = by_role[role]
        lines.append(f"### {ROLE_LABELS[role]}（{len(group)}）")
        lines.append("")
        if not group:
            lines.append("（本层无此角色文件）")
            lines.append("")
            continue
        lines.append("| 文件 | 行数 | 可执行入口 | 说明 |")
        lines.append("|---|---:|---|---|")
        for rec in group:
            exe = "是" if rec.executable else "否"
            desc = rec.doc_sentence if rec.has_doc else "（无 docstring，见下方待补清单）"
            desc = desc.replace("|", "\\|")
            lines.append(f"| `{rec.name}` | {rec.lines} | {exe} | {desc} |")
        lines.append("")
    return "\n".join(lines)


def render_no_docstring_section(records: list[PyRecord]) -> str:
    missing = [r for r in records if not r.has_doc]
    lines = [f"## 无 docstring 文件（待补充，{len(missing)} 个）", ""]
    if not missing:
        lines.append("（无——顶层全部 .py 文件都有模块 docstring）")
    else:
        for rec in missing:
            lines.append(f"- `{rec.name}`")
    lines.append("")
    return "\n".join(lines)


def render_subdir_section(subdirs: list[tuple[Path, list[PyRecord], list[OtherRecord]]]) -> str:
    lines = ["## 子目录", ""]
    for sub, py_records, other_records in subdirs:
        note = SUBDIR_NOTES.get(sub.name, "")
        lines.append(f"### {sub.name}/")
        lines.append("")
        if note:
            lines.append(note)
            lines.append("")
        total_files = len(py_records) + len(other_records)
        lines.append(f"文件数：{total_files}（.py {len(py_records)} 个，其他 {len(other_records)} 个）")
        lines.append("")
        lines.append("| 相对路径 | 类型 | 行数 | 角色 | 说明 |")
        lines.append("|---|---|---:|---|---|")
        merged: list[tuple[str, str, int, str, str]] = []
        for rec in py_records:
            desc = rec.doc_sentence if rec.has_doc else "（无 docstring）"
            merged.append((rec.rel_path, "Python", rec.lines, ROLE_LABELS[rec.role], desc))
        for rec in other_records:
            type_label = NON_PY_TYPE_LABELS.get(rec.suffix, rec.suffix or "（无扩展名）")
            if rec.suffix in (".sh", ".exp"):
                role_note = shell_role_note(rec.name)
            elif rec.suffix in (".rs",):
                role_note = "数据物化与视图" if sub.name == "lspr24_g0" else "一次性审计"
            else:
                role_note = "—"
            desc = rec.note if rec.note else "—"
            merged.append((rec.rel_path, type_label, rec.lines, role_note, desc))
        merged.sort(key=lambda t: t[0])
        for rel_path, type_label, lines_n, role_note, desc in merged:
            desc = desc.replace("|", "\\|")
            lines.append(f"| `{rel_path}` | {type_label} | {lines_n} | {role_note} | {desc} |")
        lines.append("")
    return "\n".join(lines)


def render_stats(records: list[PyRecord], subdirs: list[tuple[Path, list[PyRecord], list[OtherRecord]]]) -> str:
    total_files = len(records)
    total_lines = sum(r.lines for r in records)
    by_role_count = {role: 0 for role in ROLE_ORDER}
    for rec in records:
        by_role_count[rec.role] += 1
    no_doc = sum(1 for r in records if not r.has_doc)

    lines = ["## 当前规模统计", ""]
    lines.append(f"- 顶层 `.py` 文件：{total_files} 个，共 {total_lines} 行")
    lines.append(f"- 顶层文件中无 docstring：{no_doc} 个")
    lines.append(f"- 子目录：{len(subdirs)} 个")
    role_parts = "、".join(f"{ROLE_LABELS[r]} {by_role_count[r]}" for r in ROLE_ORDER)
    lines.append(f"- 顶层角色计数：{role_parts}")
    for sub, py_records, other_records in subdirs:
        lines.append(f"  - `{sub.name}/`：{len(py_records) + len(other_records)} 个文件（.py {len(py_records)}）")
    lines.append("")
    return "\n".join(lines)


HEADER = """# tools/ 索引

> **本文件由 `tools/tools_index.py` 生成，请勿手改。** 分组规则错了改生成器、
> 重新运行 `/opt/miniconda3/envs/rwkv/bin/python tools/tools_index.py` 后
> 重新提交——手改的内容会在下次生成时被覆盖丢失。

## 为什么 tools/ 是扁平的

`tools/` 下的脚本靠裸 `import ch3_xxx` 这类写法互相引用，依赖 Python 把脚本所在
目录（`tools/`）自动加入 `sys.path`；一旦把文件移进子目录，这类导入会全线断裂。
同时，27 份冻结实验配置里记录了 `base.tool_path` 与 `tool_sha256`——文件一动，
路径和内容哈希都变了，已有运行制品就没法再溯源到当初实际执行的代码，而四格实验
即将启动。**这两条决定了 tools/ 现在只能加索引，不能重组**；重组要等四格实验跑
完、单独立项评估依赖图后再做。

## 分组规则说明

角色判定顺序：一次性审计 → 诊断探针 → 评价与指标 → 数据物化与视图 → 兜底
（按"是否可执行"分训练入口 / 机制实现）。关键词只匹配"文件名 + docstring 首句"，
不用整份 docstring——实测扩大到全文后 `eval`/`诊断` 等词会命中背景说明段落里的
无关提及，误伤了不少文件；首句是作者自己写的摘要，信噪比更高。

"可执行入口"不是单看 `if __name__ == "__main__"`：仓库里有一批历史脚本
（如 `ch3_backbone_protocolA.py`）写成"从上到下线性执行、没有 `__main__` 守卫"，
import 即执行，判定用的是"有守卫，或模块顶层有 ≥3 条非简单赋值的实质执行语句"。
这套组合规则是启发式的，边界情形（例如同时符合两种角色描述的脚本）按更具体的
关键词优先，具体清单见生成器源码顶部的注释；分组明显错误的按生成器规则调整后
重新生成，不要手改本文件。

"""


def build_index_text() -> str:
    records = collect_top_level()
    subdirs = collect_subdirs()

    parts = [
        HEADER,
        render_stats(records, subdirs),
        render_top_level_section(records),
        render_no_docstring_section(records),
        render_subdir_section(subdirs),
    ]
    return "\n".join(parts).rstrip() + "\n"


def main() -> None:
    text = build_index_text()
    INDEX_PATH.write_text(text, encoding="utf-8")
    print(f"写入 {INDEX_PATH}（{len(text)} 字节）")


if __name__ == "__main__":
    main()
