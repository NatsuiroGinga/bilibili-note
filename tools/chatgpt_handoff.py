#!/usr/bin/env python3
"""初始化项目并生成普通 ChatGPT 的受管只读交接包。"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = "chatgpt-handoff-v2"
DEFAULT_HANDOFF_ROOT = ".Codex/docs/chatgpt-handoffs"
FORBIDDEN_PARTS = frozenset(
    {
        "runs",
        "raw",
        "data",
        "dataset",
        "datasets",
        "logs",
        "checkpoints",
        ".env",
        ".ssh",
        ".git",
    }
)
FORBIDDEN_SUFFIXES = (
    ".csv",
    ".tsv",
    ".jsonl",
    ".npy",
    ".npz",
    ".pcap",
    ".pcapng",
    ".pdf",
    ".log",
    ".pem",
    ".key",
    ".pt",
    ".pth",
    ".ckpt",
)
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
TASK_TYPES = (
    "literature-search",
    "literature-review",
    "neighbor-deduplication",
    "mechanism-counterexample",
    "experiment-analysis",
    "figure-suggestion",
    "note-suggestion",
    "draft-suggestion",
)
SENSITIVE_TEXT_PATTERNS = (
    ("个人绝对路径", re.compile(r"(?i)(?:~/(?:users|home|private|var|tmp|root)/|/(?:users|home|private|var|tmp|root)/|[a-z]:\\users\\)")),
    ("原始数据或数据集", re.compile(r"(?i)(?:原始(?:数据|样本|流量)|数据集|raw[-_ ]?data|dataset)")),
    ("检查点或权重", re.compile(r"(?i)(?:检查点|模型权重|权重文件|checkpoint|state_dict|\.(?:pt|pth|ckpt)\b)")),
    ("日志", re.compile(r"(?i)(?:日志|原始 log|log(?:file|s)?|swanlab|wandb|tensorboard)")),
    ("凭据", re.compile(r"(?i)(?:凭据|令牌|密钥|密码|私钥|secret|token|api[_ -]?key|credential|password)")),
    ("服务器连接", re.compile(r"(?i)(?:ssh://|sftp://|\b(?:ssh|sftp|rsync)\b|用户名@|hostname\s*=|host\s*=)")),
    ("目标期信息", re.compile(r"(?i)(?:目标期|目标年份|target[-_ ]?(?:period|year)|最终测试(?:集|样本|标签)?|holdout)")),
)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(text, encoding="utf-8")
    partial.replace(path)


def git_value(project_root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project_root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def project_root(value: Path) -> Path:
    root = value.expanduser().resolve()
    actual = Path(git_value(root, "rev-parse", "--show-toplevel")).resolve()
    if root != actual:
        raise ValueError(f"project-root 必须是 Git 工作树根目录：{actual}")
    return root


def safe_relative_path(value: str, root: Path, require_file: bool = True) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"路径不允许越界：{value}")
    lowered = value.lower()
    if any(part.lower() in FORBIDDEN_PARTS for part in path.parts):
        raise ValueError(f"路径属于禁止交接范围：{value}")
    if lowered.endswith(FORBIDDEN_SUFFIXES):
        raise ValueError(f"路径后缀属于禁止交接范围：{value}")
    if any(token in lowered for token in ("secret", "password", "credential", "id_rsa")):
        raise ValueError(f"路径疑似敏感：{value}")
    candidate = (root / Path(*path.parts)).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError(f"路径不位于项目内：{value}")
    if require_file and not candidate.is_file():
        raise ValueError(f"允许路径不存在或不是文件：{value}")
    return path.as_posix()


def validate_scalar(name: str, value: str, maximum: int = 200) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > maximum:
        raise ValueError(f"{name} 不能为空且不得超过 {maximum} 字符")
    if any(ord(char) < 32 for char in normalized):
        raise ValueError(f"{name} 不得含控制字符")
    return normalized


def validate_external_text(name: str, value: str, maximum: int) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > maximum:
        raise ValueError(f"{name} 不能为空且不得超过 {maximum} 字符")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in normalized):
        raise ValueError(f"{name} 不得含控制字符")
    for label, pattern in SENSITIVE_TEXT_PATTERNS:
        if pattern.search(normalized):
            raise ValueError(f"{name} 包含禁止交接内容：{label}")
    return normalized


def normalize_repository(remote: str) -> str:
    value = remote.strip()
    if value.startswith("git@github.com:"):
        value = value.removeprefix("git@github.com:")
    elif "github.com/" in value:
        value = value.split("github.com/", 1)[1]
    return value.removesuffix(".git").strip("/")


def handoff_root(root: Path, configured: str) -> Path:
    relative = safe_relative_path(configured, root, require_file=False)
    destination = (root / relative).resolve()
    if destination == root:
        raise ValueError("handoff-root 不能等于项目根")
    return destination


def initialize(args: argparse.Namespace) -> None:
    root = project_root(args.project_root)
    destination = handoff_root(root, args.handoff_root)
    config_path = root / ".chatgpt-handoff.json"
    config: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "handoff_root": destination.relative_to(root).as_posix(),
    }
    if not config_path.exists():
        atomic_write(config_path, json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "inbox").mkdir(parents=True, exist_ok=True)
    templates = {
        destination / "TEMPLATE.md": (
            "# ChatGPT 交接包模板\n\n"
            "交接包由 chatgpt_handoff.py create 生成，不手工填入敏感内容。\n"
        ),
        destination / "inbox" / "INBOX_TEMPLATE.md": (
            "# ChatGPT 回收记录\n\n"
            "- outbound_id：\n"
            "- actual_model：\n"
            "- actual_effort：\n"
            "- actual_mode：\n"
            "- used_apps：\n"
            "- 状态：外部候选，待本地全文和实验复核\n"
        ),
    }
    for path, content in templates.items():
        if not path.exists():
            atomic_write(path, content)
    print(
        json.dumps(
            {
                "status": "initialized",
                "project_root": str(root),
                "handoff_root": str(destination),
                "config": str(config_path),
            },
            ensure_ascii=False,
        )
    )


def load_project_config(root: Path) -> dict[str, Any]:
    path = root / ".chatgpt-handoff.json"
    if not path.is_file():
        raise ValueError("项目尚未初始化，请先运行 init")
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("项目交接配置版本不匹配")
    return config


def create(args: argparse.Namespace) -> None:
    root = project_root(args.project_root)
    config = load_project_config(root)
    destination = handoff_root(root, str(config["handoff_root"]))
    name = validate_scalar("name", args.name, maximum=80)
    if not NAME_PATTERN.fullmatch(name):
        raise ValueError("name 只能包含字母、数字、下划线和连字符")
    paths = [
        safe_relative_path(line.strip(), root)
        for line in args.paths.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not paths:
        raise ValueError("路径清单不能为空")
    task_type = validate_scalar("task-type", args.task_type, maximum=80)
    task = validate_external_text("task", args.task, maximum=8000)
    sanitized_summary = args.sanitized_summary.strip()
    if task_type == "experiment-analysis" and not sanitized_summary:
        raise ValueError("experiment-analysis 必须提供 --sanitized-summary")
    if sanitized_summary:
        sanitized_summary = validate_external_text(
            "sanitized-summary", sanitized_summary, maximum=12000
        )
    model = validate_scalar("model", args.model)
    effort = validate_scalar("effort", args.effort)
    fallback_model = args.fallback_model.strip()
    if fallback_model:
        fallback_model = validate_scalar("fallback-model", fallback_model)
    rationale = validate_external_text(
        "selection-rationale", args.selection_rationale, maximum=500
    )
    source_scope = validate_external_text("source-scope", args.source_scope, maximum=500)
    apps = [validate_scalar("app", item) for item in args.apps.split(",") if item.strip()]
    repository = args.repository or normalize_repository(
        git_value(root, "remote", "get-url", "origin")
    )
    branch = args.branch or git_value(root, "branch", "--show-current")
    commit = args.commit or git_value(root, "rev-parse", "HEAD")
    output = destination / f"{name}-outbound.md"
    lines = [
        "# ChatGPT 只读交接包",
        "",
        "**状态：外部候选，待本地全文和实验复核。**",
        "",
        "## 快照与执行配置",
        "",
        f"- repository：\x60{repository}\x60",
        f"- branch：\x60{branch}\x60",
        f"- commit：\x60{commit}\x60",
        f"- requested_model：\x60{model}\x60",
        f"- requested_effort：\x60{effort}\x60",
        f"- fallback_model：\x60{fallback_model}\x60",
        f"- selection_rationale：\x60{rationale}\x60",
        f"- requested_mode：\x60{args.mode}\x60",
        f"- requested_apps：\x60{','.join(apps)}\x60",
        f"- task_type：\x60{task_type}\x60",
        f"- source_scope：\x60{source_scope}\x60",
        f"- sanitized_summary_included：\x60{str(bool(sanitized_summary)).lower()}\x60",
        f"- fulltext_required：\x60{str(args.fulltext_required).lower()}\x60",
        f"- zotero_ingest_required：\x60{str(args.zotero_ingest_required).lower()}\x60",
        "- allowed_paths：",
        *[f"  - \x60{path}\x60" for path in paths],
        "",
        "## 任务",
        "",
        task,
        "",
        *(
            [
                "## 脱敏实验摘要",
                "",
                sanitized_summary,
                "",
            ]
            if sanitized_summary
            else []
        ),
        "## 返回合同",
        "",
        "返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、",
        "结论、逐项证据、来源与精确位置、不确定性和未回答问题。",
        "结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。",
        "",
        "## 禁止操作",
        "",
        "不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、",
        "数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、",
        "未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。",
        "",
    ]
    atomic_write(output, "\n".join(lines))
    print(
        json.dumps(
            {
                "status": "created",
                "output": str(output),
                "repository": repository,
                "branch": branch,
                "commit": commit,
            },
            ensure_ascii=False,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init_parser = commands.add_parser("init", help="初始化当前 Git 项目的交接目录")
    init_parser.add_argument("--project-root", required=True, type=Path)
    init_parser.add_argument("--handoff-root", default=DEFAULT_HANDOFF_ROOT)

    create_parser = commands.add_parser("create", help="生成一个受管只读交接包")
    create_parser.add_argument("--project-root", required=True, type=Path)
    create_parser.add_argument("--name", required=True)
    create_parser.add_argument("--paths", required=True, type=Path)
    create_parser.add_argument("--task", required=True)
    create_parser.add_argument("--task-type", choices=TASK_TYPES, default="literature-review")
    create_parser.add_argument("--sanitized-summary", default="")
    create_parser.add_argument("--model", default="auto")
    create_parser.add_argument("--effort", default="auto")
    create_parser.add_argument("--fallback-model", default="")
    create_parser.add_argument(
        "--selection-rationale",
        default="由发起方按任务复杂度、额度与可用模型选择",
    )
    create_parser.add_argument(
        "--mode",
        choices=("chat", "deep-research", "agent"),
        default="chat",
    )
    create_parser.add_argument("--apps", default="github")
    create_parser.add_argument("--source-scope", default="白名单路径")
    create_parser.add_argument("--fulltext-required", action="store_true")
    create_parser.add_argument("--zotero-ingest-required", action="store_true")
    create_parser.add_argument("--repository")
    create_parser.add_argument("--branch")
    create_parser.add_argument("--commit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "init":
            initialize(args)
        else:
            create(args)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
