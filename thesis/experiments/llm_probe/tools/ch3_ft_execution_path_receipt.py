# -*- coding: utf-8 -*-
"""四格执行路径观测层：记录每个前向调用点的实际调用对象、Dynamo 编译统计与图断裂位置。

为什么需要本模块
----------------
第三章恢复卡的「论文正式定稿前硬门禁」要求：*每臂运行收据须记录实际调用路径、
图断裂与回退，而非只记录 ``torch.compile`` 配置*。配置项无法证明代码究竟走了编译
还是即时执行——``torch.compile`` 只替换 ``forward``，经 ``model.encode``／
``model.inject``／``model.predict`` 的调用直接落回原模块（2026-08-31 目标机实测：
``compiled.encode.__self__ is raw`` 为 ``True``、``compiled.forward is raw.forward``
为 ``False``），且模块内部的数据依赖分支会造成图断裂并静默回退即时执行。

接口核验（2026-08-31 目标机 RTX 4080 SUPER `sm_89`、PyTorch `2.13.0+cu130` 实测；
证据见 ``.Codex/docs/RWKV/2026-08-31-四格编译路径统一/notes.md`` 的接口核验表）
------------------------------------------------------------------------------
- ``torch._dynamo.utils.counters``：``defaultdict``，实测含 ``frames{total,ok}``、
  ``stats{calls_captured,unique_graphs}``、``graph_break``（``Counter``：完整原因文本 →
  次数）、``unimplemented``、``resumes{torch_dynamo_resume_in_<函数>_at_<行号>: 次数}``、
  ``aot_autograd``、``inductor``。这些是**编译期**计数：同形状重复调用命中缓存时不再增长，
  新形状或新帧触发编译时才增长。
- ``torch._dynamo.utils.graph_break_reasons``：``list``，每项含 ``.reason``（多行文本）、
  ``.user_stack``（``FrameSummary`` 列表，带文件、行号、函数名）、``.graph_break``（``bool``）。
  这是「断在哪」的唯一直接来源。
- ``torch._dynamo.eval_frame.OptimizedModule``：编译包装体类型，带 ``_orig_mod``。
  ``isinstance`` 判定即可区分「调用入口进入 Dynamo」与「调用入口是原模块」。

本模块只观测与落盘，不做任何阻断
--------------------------------
按 ``thesis/experiments/llm_probe/AGENTS.md``「默认不新增阻断门、披露优先于阻断」，
本模块不抛异常、不返回非零退出码。四格是否真的同路径由 ``--compare`` 子命令在四臂
收据齐备后离线判定，不在单臂运行内阻断。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

RECEIPT_SCHEMA_VERSION = "ch3-ft-execution-path-receipt-v1"

# 已知调用点白名单。新增前向调用点必须同时登记到这里，否则四格比对会把它
# 报成「仅出现在部分臂」的未知调用点，而不是静默忽略。
KNOWN_CALL_SITES = (
    "flow_forward_bare_train",
    "flow_forward_bare_validation",
    "flow_forward_bare_combined",
    "flow_forward_bare_zero_gate_model",
    "flow_forward_bare_zero_gate_reference",
    "flow_forward_entity_memory_train",
    "flow_forward_entity_memory_validation",
    "flow_forward_entity_memory_combined",
    "ranking_forward_bare",
    "ranking_forward_entity_memory",
)

# 门禁三条统一条款各自对应的调用点集合，供 --compare 逐条判定。
GATE_CLAUSES = {
    "共同逐流骨干统一走编译路径": (
        "flow_forward_bare_train",
        "flow_forward_bare_combined",
        "flow_forward_entity_memory_train",
        "flow_forward_entity_memory_combined",
    ),
    "C01与C11的实体排序检查点统一即时执行": (
        "ranking_forward_bare",
        "ranking_forward_entity_memory",
    ),
    "C10与C11的记忆注意力统一执行路径": (
        "flow_forward_entity_memory_train",
        "flow_forward_entity_memory_combined",
    ),
}


class ExecutionPathLedger:
    """按调用点累积「实际被调用的对象是什么」。

    ``record`` 在每个微批前向前调用一次。首次遇到某调用点时做一次类型判定并落成
    条目，之后只自增计数，因此稳态开销是一次字典查找加一次整数自增，不影响数值路径。
    """

    def __init__(self) -> None:
        self._sites: dict[str, dict[str, Any]] = {}

    def reset(self) -> None:
        self._sites.clear()

    def record(self, site: str, callable_obj: Any, *, checkpointed: bool) -> None:
        entry = self._sites.get(site)
        if entry is None:
            entry = _describe_callable(site, callable_obj, checkpointed=checkpointed)
            self._sites[site] = entry
        entry["call_count"] += 1

    def call_sites(self) -> list[dict[str, Any]]:
        return [dict(entry) for _, entry in sorted(self._sites.items())]

    def is_empty(self) -> bool:
        return not self._sites


# 模块级单例：七个前向调用点分散在 ``ch3_ft_c00_dual_selection`` 的六个函数里，
# 逐层传参会改动六个函数签名并牵动断点恢复与零门断言的调用方；这里沿用与
# ``torch._dynamo.utils.counters`` 相同的单例累积器写法，只由 ``run_training``／
# ``probe_runtime`` 在入口处 ``reset()`` 一次。
LEDGER = ExecutionPathLedger()


def _describe_callable(site: str, callable_obj: Any, *, checkpointed: bool) -> dict[str, Any]:
    """判定该调用点的入口对象是 Dynamo 包装体还是原模块。"""
    from torch._dynamo.eval_frame import OptimizedModule

    wrapped = isinstance(callable_obj, OptimizedModule)
    underlying = getattr(callable_obj, "_orig_mod", callable_obj)
    return {
        "site": site,
        # compiled_entry：调用入口进入 Dynamo，模块内部仍可能因图断裂逐段回退即时执行；
        # eager：调用入口就是原模块，Dynamo 完全不介入（实测 counters 零增长）。
        "execution_path": "compiled_entry" if wrapped else "eager",
        "callable_type": type(callable_obj).__name__,
        "underlying_type": type(underlying).__name__,
        "dynamo_wrapped_entry": wrapped,
        "under_gradient_checkpoint": checkpointed,
        "known_site": site in KNOWN_CALL_SITES,
        "call_count": 0,
    }


def _frame_fields(frame: Any) -> dict[str, Any]:
    """把 ``FrameSummary`` 拆成文件、行号、函数名；缺字段时降级为字符串。"""
    filename = getattr(frame, "filename", None)
    if filename is None:
        return {"raw": str(frame)}
    return {
        "file": str(filename),
        "line": getattr(frame, "lineno", None),
        "function": getattr(frame, "name", None),
        "source": (getattr(frame, "line", None) or "").strip() or None,
    }


def dynamo_compile_snapshot(max_break_records: int = 128) -> dict[str, Any]:
    """读取当前进程累计的 Dynamo 编译与图断裂统计。

    只读不清空：``counters`` 是编译期累积量，运行全程读到的是「本进程一共编译了多少帧、
    在哪些位置断裂」，正是门禁要的那份记录。
    """
    import torch._dynamo.utils as dynamo_utils

    counters = dynamo_utils.counters
    frames = dict(counters.get("frames", {}))
    stats = dict(counters.get("stats", {}))
    graph_break = counters.get("graph_break", {})
    unimplemented = counters.get("unimplemented", {})
    resumes = dict(counters.get("resumes", {}))

    total_frames = int(frames.get("total", 0))
    ok_frames = int(frames.get("ok", 0))

    reasons = list(getattr(dynamo_utils, "graph_break_reasons", []) or [])
    break_records = [
        {
            "reason_head": str(getattr(record, "reason", record)).splitlines()[0],
            "user_stack": [_frame_fields(frame) for frame in (getattr(record, "user_stack", None) or [])],
        }
        for record in reasons[:max_break_records]
    ]

    return {
        "frames_total": total_frames,
        "frames_ok": ok_frames,
        "frames_not_ok": total_frames - ok_frames,
        "unique_graphs": int(stats.get("unique_graphs", 0)),
        "calls_captured": int(stats.get("calls_captured", 0)),
        "graph_break_total": int(sum(graph_break.values())),
        "graph_break_by_reason": {str(key).splitlines()[0]: int(value) for key, value in graph_break.items()},
        "unimplemented_by_reason": {str(key).splitlines()[0]: int(value) for key, value in unimplemented.items()},
        "resume_functions": {str(key): int(value) for key, value in resumes.items()},
        "graph_break_records": break_records,
        "graph_break_records_truncated": len(reasons) > max_break_records,
        "graph_break_records_total": len(reasons),
    }


def classify_break_sites(snapshot: dict[str, Any], project_root: str) -> dict[str, Any]:
    """把图断裂按「本仓库代码」与「torch 站内实现」分开。

    区分的意义：本仓库代码里的断裂是我们能改的（例如数据依赖布尔索引），
    torch 站内实现的断裂是这套 PyTorch 构建自身的行为，四格一致但改不动。

    注意 ``.venv`` 就在项目根之下（目标机实测断点出现在
    ``<项目根>/.venv/lib/python3.10/site-packages/torch/_native/registry.py``），
    因此只按前缀判断会把 torch 自身的断裂误记为本仓库断裂，必须额外排除
    ``site-packages``。
    """
    project = str(Path(project_root).resolve())
    repository: dict[str, int] = {}
    library: dict[str, int] = {}
    for record in snapshot.get("graph_break_records", []):
        stack = record.get("user_stack") or []
        frame = stack[-1] if stack else {}
        path = frame.get("file")
        key = "%s:%s in %s | %s" % (
            path, frame.get("line"), frame.get("function"), record.get("reason_head"),
        )
        own_code = bool(path) and path.startswith(project) and "site-packages" not in path
        bucket = repository if own_code else library
        bucket[key] = bucket.get(key, 0) + 1
    return {
        "repository_break_sites": repository,
        "library_break_sites": library,
        "repository_break_site_count": len(repository),
        "library_break_site_count": len(library),
    }


def runtime_environment_snapshot() -> dict[str, Any]:
    """记录门禁「同一 GPU、同一 PyTorch／CUDA」两款要用到的运行环境事实。

    既有的 ``environment-receipt.json`` 只记 ``torch.__version__``、``platform`` 与显存字节数，
    **没有 GPU 型号与计算能力**；而 inductor 为不同计算能力生成不同的核
    （目标机 `sm_89` 对旧三格的 `sm_120`），因此这两项必须进收据才能机械判定。
    ``torch.get_float32_matmul_precision()`` 一并记录：恢复卡把它列为未冻结候选，
    收据须留下每臂的实际值。
    """
    import torch

    snapshot: dict[str, Any] = {
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "float32_matmul_precision": torch.get_float32_matmul_precision(),
        "device_name": None,
        "device_capability": None,
    }
    if torch.cuda.is_available():
        index = torch.cuda.current_device()
        snapshot["device_name"] = torch.cuda.get_device_name(index)
        snapshot["device_capability"] = list(torch.cuda.get_device_capability(index))
    return snapshot


def build_execution_path_receipt(
    config: dict[str, Any],
    *,
    stage: str,
    project_root: str,
    ledger: ExecutionPathLedger | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """组装完整的执行路径收据。"""
    active = LEDGER if ledger is None else ledger
    snapshot = dynamo_compile_snapshot()
    call_sites = active.call_sites()
    compile_settings = config.get("runtime", {}).get("torch_compile") or {}
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "run_id": config.get("identity", {}).get("run_id"),
        "stage": stage,
        # 配置声明值保留，但它只是「打算怎么做」；下面两块才是「实际怎么执行的」。
        "torch_compile_declared": {
            "enabled": bool(compile_settings.get("enabled", False)),
            "mode": compile_settings.get("mode"),
        },
        "execution_environment": runtime_environment_snapshot(),
        "call_sites": call_sites,
        "call_site_paths": {entry["site"]: entry["execution_path"] for entry in call_sites},
        "dynamo": snapshot,
        "break_site_classification": classify_break_sites(snapshot, project_root),
        "unknown_call_sites": [entry["site"] for entry in call_sites if not entry["known_site"]],
        "target_reads": 0,
    }
    if extra:
        receipt.update(extra)
    return receipt


def write_execution_path_receipt(
    output_root: Any,
    config: dict[str, Any],
    *,
    stage: str,
    project_root: str,
    atomic_json: Any,
    logger: Any = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """落盘 ``receipts/execution-path.json``，并把一行摘要打进日志。

    ``atomic_json`` 由宿主传入，避免本模块重复实现一套原子写。
    """
    receipt = build_execution_path_receipt(
        config, stage=stage, project_root=project_root, extra=extra
    )
    atomic_json(Path(output_root) / "receipts" / "execution-path.json", receipt)
    if logger is not None:
        dynamo = receipt["dynamo"]
        logger.info(
            "执行路径收据已落盘：阶段=%s 调用点=%s 编译帧=%d/%d 图断裂=%d（本仓库断点=%d 站内断点=%d）",
            stage,
            receipt["call_site_paths"],
            dynamo["frames_ok"],
            dynamo["frames_total"],
            dynamo["graph_break_total"],
            receipt["break_site_classification"]["repository_break_site_count"],
            receipt["break_site_classification"]["library_break_site_count"],
        )
    return receipt


def compare_receipts(paths: list[Path]) -> dict[str, Any]:
    """离线比对多臂收据，逐条判定门禁三款统一条款。

    只报告，不阻断：返回结构里带 ``consistent`` 布尔，由调用者决定怎么处理。
    """
    loaded = []
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        loaded.append((payload.get("run_id") or path.name, payload))

    per_site: dict[str, dict[str, str]] = {}
    for run_id, payload in loaded:
        for site, execution_path in (payload.get("call_site_paths") or {}).items():
            per_site.setdefault(site, {})[run_id] = execution_path

    clause_results = {}
    for clause, sites in GATE_CLAUSES.items():
        observed = {}
        for site in sites:
            observed.update(per_site.get(site, {}))
        distinct = sorted(set(observed.values()))
        clause_results[clause] = {
            "sites": list(sites),
            "observed": observed,
            "distinct_paths": distinct,
            "consistent": len(distinct) <= 1,
        }

    # 「同一 GPU、同一 PyTorch／CUDA」两款门禁：v1 收据没有 execution_environment 字段，
    # 此时判定值为 None（无法判定），不冒充通过。
    execution_environments = {
        run_id: payload.get("execution_environment") for run_id, payload in loaded
    }
    if all(value is not None for value in execution_environments.values()):
        distinct_environments = {
            json.dumps(value, ensure_ascii=False, sort_keys=True) for value in execution_environments.values()
        }
        environment_identical: bool | None = len(distinct_environments) <= 1
    else:
        environment_identical = None

    environment = {
        run_id: {
            "torch_compile_declared": payload.get("torch_compile_declared"),
            "frames_total": (payload.get("dynamo") or {}).get("frames_total"),
            "frames_ok": (payload.get("dynamo") or {}).get("frames_ok"),
            "graph_break_total": (payload.get("dynamo") or {}).get("graph_break_total"),
            "repository_break_sites": sorted(
                ((payload.get("break_site_classification") or {}).get("repository_break_sites") or {}).keys()
            ),
        }
        for run_id, payload in loaded
    }

    # 图断裂签名只能在**共享同一模块集合**的臂之间比较：C00／C01 不构造因果实体记忆，
    # 其仓库断点必然为空；C10／C11 构造记忆注意力，必然带该模块的断点。把四臂放进
    # 同一个集合比较会必然不一致，那是机制差异不是路径差异。因此按「是否走记忆路径」
    # 分组，组内要求断裂签名逐条相同。
    groups: dict[str, dict[str, list[str]]] = {}
    for run_id, payload in loaded:
        sites = set((payload.get("call_site_paths") or {}).keys())
        has_memory = any(site.startswith("flow_forward_entity_memory") for site in sites)
        group = "entity_memory_arms" if has_memory else "bare_backbone_arms"
        groups.setdefault(group, {})[run_id] = environment[run_id]["repository_break_sites"]

    break_signature_groups = {}
    for group, members in groups.items():
        distinct = {json.dumps(value, ensure_ascii=False) for value in members.values()}
        break_signature_groups[group] = {
            "arms": sorted(members),
            "break_sites": members,
            "identical_within_group": len(distinct) <= 1,
        }

    return {
        "schema_version": "ch3-ft-execution-path-comparison-v1",
        "arms": [run_id for run_id, _ in loaded],
        "per_site_paths": per_site,
        "gate_clauses": clause_results,
        "environment": environment,
        "execution_environments": execution_environments,
        "execution_environment_identical": environment_identical,
        "break_signature_groups": break_signature_groups,
        "break_signatures_identical_within_groups": all(
            item["identical_within_group"] for item in break_signature_groups.values()
        ),
        # consistent 只汇总「路径类」判定。执行环境是否一致单独报告：
        # v1 收据无该字段时为 None，不能因缺字段就把整体判成不通过，也不能冒充通过。
        "consistent": all(item["consistent"] for item in clause_results.values())
        and all(item["identical_within_group"] for item in break_signature_groups.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="四格执行路径收据比对（只读，不阻断）")
    parser.add_argument(
        "--compare", nargs="+", required=True, help="各臂 receipts/execution-path.json 路径"
    )
    args = parser.parse_args()
    result = compare_receipts([Path(item) for item in args.compare])
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
