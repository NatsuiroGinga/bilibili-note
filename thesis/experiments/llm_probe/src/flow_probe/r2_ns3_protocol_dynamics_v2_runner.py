"""运行 R2 ns-3 TCP/UDP 动力学真值 v2 正式矩阵。"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Final

from flow_probe import r2_ns3_tcp_truth_v2_runner as truth
from flow_probe.r2_ns3_protocol_runner import _load_manifest


PARAMS_SCHEMA: Final = "flow_probe_r2_ns3_protocol_dynamics_v2_formal_params_v1"
STATE_SCHEMA: Final = "flow_probe_r2_ns3_protocol_dynamics_v2_state_v1"
SUMMARY_SCHEMA: Final = "flow_probe_r2_ns3_protocol_dynamics_v2_summary_v1"
EXPECTED_MANIFEST_SHA256: Final = truth.EXPECTED_MANIFEST_SHA256


class FormalMatrixError(RuntimeError):
    """正式矩阵输入、门禁、运行或制品违反冻结合同。"""


def _require_sha(value: object, name: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise FormalMatrixError(f"{name}必须是小写SHA-256")
    return value


def _resolve_under(root: Path, value: object, name: str) -> Path:
    if not isinstance(value, str) or not value:
        raise FormalMatrixError(f"{name}必须是非空路径字符串")
    candidate = Path(value)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise FormalMatrixError(f"{name}必须位于项目根内") from error
    return resolved


def _verify_artifact_manifest(root: Path) -> None:
    value = json.loads((root / "artifact-manifest.json").read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise FormalMatrixError("字段闭合制品清单必须是JSON数组")
    expected: dict[str, tuple[int, str]] = {}
    for item in value:
        if not isinstance(item, Mapping):
            raise FormalMatrixError("字段闭合制品清单项必须是对象")
        logical = item.get("logical_path")
        size = item.get("size_bytes")
        digest = item.get("sha256")
        if not isinstance(logical, str) or not isinstance(size, int):
            raise FormalMatrixError("字段闭合制品清单路径或大小不合法")
        expected[logical] = (size, _require_sha(digest, "字段闭合制品哈希"))
    for logical, (size, digest) in expected.items():
        artifact = (root / logical).resolve()
        try:
            artifact.relative_to(root.resolve())
        except ValueError as error:
            raise FormalMatrixError("字段闭合制品路径越界") from error
        if (
            not artifact.is_file()
            or artifact.is_symlink()
            or artifact.stat().st_size != size
            or truth._file_sha256(artifact) != digest
        ):
            raise FormalMatrixError(f"字段闭合制品哈希不一致：{logical}")


def _verify_field_closure(
    root: Path, expected_summary_sha: str, scenario_sha: str, contract_sha: str
) -> Mapping[str, object]:
    if not root.is_dir() or root.is_symlink():
        raise FormalMatrixError("字段闭合输出根不存在、不是目录或是符号链接")
    summary_path = root / "summary.json"
    if truth._file_sha256(summary_path) != expected_summary_sha:
        raise FormalMatrixError("字段闭合汇总SHA-256不一致")
    summary = truth._read_json(summary_path, "字段闭合汇总")
    state = truth._read_json(root / "run-state.json", "字段闭合状态")
    if (
        summary.get("status") != "pass"
        or summary.get("planned_run_count") != 5
        or summary.get("completed_run_count") != 5
        or state.get("status") != "finished"
        or state.get("completed_run_count") != 5
        or summary.get("scenario_source_sha256") != scenario_sha
        or summary.get("contract_sha256") != contract_sha
        or summary.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256
    ):
        raise FormalMatrixError("字段闭合未形成绑定当前源码和合同的5/5通过收据")
    aggregate = summary.get("aggregate")
    if not isinstance(aggregate, Mapping) or any(
        int(aggregate.get(key, 0)) <= 0
        for key in (
            "acked_bytes",
            "rtt_sample_count",
            "contraction_event_count",
            "ack_residual_valid_terms",
            "loss_residual_valid_terms",
        )
    ):
        raise FormalMatrixError("字段闭合缺少非零ACK、RTT、收缩或固定残差有效项")
    _verify_artifact_manifest(root)
    return summary


def _artifact_manifest(root: Path) -> list[dict[str, object]]:
    return truth._artifact_manifest(root)


def _run_from_params(path: Path) -> Mapping[str, object]:
    params = truth._read_json(path.resolve(), "v2正式矩阵受控参数")
    expected_keys = {
        "schema_version",
        "project_root",
        "ns3_root",
        "manifest_path",
        "scenario_source",
        "contract_path",
        "field_closure_output_dir",
        "output_dir",
        "expected_manifest_sha256",
        "expected_scenario_source_sha256",
        "expected_contract_sha256",
        "expected_field_closure_summary_sha256",
    }
    if set(params) != expected_keys or params.get("schema_version") != PARAMS_SCHEMA:
        raise FormalMatrixError("v2正式矩阵参数键集合或模式版本不符")
    project_root = Path(str(params["project_root"])).resolve()
    if project_root != Path(__file__).resolve().parents[2]:
        raise FormalMatrixError("project_root与当前安装代码根不一致")
    ns3_root = Path(str(params["ns3_root"])).resolve()
    if ns3_root.as_posix() != "/root/autodl-tmp/thesis/ns3/ns-3.48":
        raise FormalMatrixError("ns-3根不是固定服务器路径")
    manifest_path = _resolve_under(project_root, params["manifest_path"], "manifest_path")
    scenario_path = _resolve_under(project_root, params["scenario_source"], "scenario_source")
    contract_path = _resolve_under(project_root, params["contract_path"], "contract_path")
    closure_root = _resolve_under(
        project_root, params["field_closure_output_dir"], "field_closure_output_dir"
    )
    output_root = _resolve_under(project_root, params["output_dir"], "output_dir")
    if manifest_path != project_root / "runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.jsonl":
        raise FormalMatrixError("正式矩阵清单路径偏离冻结路径")
    if scenario_path != project_root / "ns3/r2_protocol_dynamics_v2_scenario.cc":
        raise FormalMatrixError("正式矩阵场景路径偏离v2独立路径")
    if output_root != project_root / "runs/ns3-data/r2-protocol-dynamics-v2-formal-attempt1":
        raise FormalMatrixError("正式矩阵输出身份不符")
    expected_manifest = _require_sha(params["expected_manifest_sha256"], "清单哈希")
    scenario_sha = _require_sha(params["expected_scenario_source_sha256"], "场景哈希")
    contract_sha = _require_sha(params["expected_contract_sha256"], "合同哈希")
    closure_summary_sha = _require_sha(
        params["expected_field_closure_summary_sha256"], "字段闭合汇总哈希"
    )
    if expected_manifest != EXPECTED_MANIFEST_SHA256:
        raise FormalMatrixError("正式矩阵未绑定冻结清单哈希")
    for artifact, expected in (
        (manifest_path, expected_manifest),
        (scenario_path, scenario_sha),
        (contract_path, contract_sha),
    ):
        if truth._file_sha256(artifact) != expected:
            raise FormalMatrixError(f"正式输入SHA-256不一致：{artifact.name}")
    compiled_source = ns3_root / truth.COMPILED_SOURCE
    if truth._file_sha256(compiled_source) != scenario_sha:
        raise FormalMatrixError("项目场景与ns-3 scratch双副本SHA-256不一致")
    _verify_field_closure(closure_root, closure_summary_sha, scenario_sha, contract_sha)
    runs = _load_manifest(manifest_path)
    if len(runs) != 512:
        raise FormalMatrixError("冻结清单未恰含512条运行")
    if output_root.exists() or output_root.is_symlink():
        raise FormalMatrixError("正式输出根已存在，禁止覆盖或复用")
    output_root.mkdir(parents=True)
    runs_root = output_root / "runs"
    runs_root.mkdir()
    started_monotonic = time.monotonic()
    state: dict[str, object] = {
        "schema_version": STATE_SCHEMA,
        "status": "running",
        "review_status": "review_pending",
        "started_at": truth._utc_now(),
        "planned_run_count": 512,
        "completed_run_count": 0,
        "failed_run_count": 0,
        "active_run": None,
    }
    truth._write_json_atomic(output_root / "matrix-state.json", state)
    receipts: list[Mapping[str, object]] = []
    try:
        for index, run in enumerate(runs):
            identity = f"{index:04d}-{run.transport_family.lower()}"
            state["active_run"] = f"{run.physics_group_sha256}:{run.transport_family}"
            state["updated_at"] = truth._utc_now()
            truth._write_json_atomic(output_root / "matrix-state.json", state)
            receipt = truth._run_one(
                ns3_root, runs_root, identity, run, contract_sha, scenario_sha
            )
            receipts.append(receipt)
            completed = len(receipts)
            elapsed = max(time.monotonic() - started_monotonic, 1e-9)
            rate = completed * 60.0 / elapsed
            remaining_seconds = (512 - completed) * 60.0 / rate
            state.update(
                {
                    "completed_run_count": completed,
                    "runs_per_minute": rate,
                    "estimated_finish_at": (
                        datetime.now(timezone.utc) + timedelta(seconds=remaining_seconds)
                    ).isoformat(),
                    "updated_at": truth._utc_now(),
                }
            )
            truth._write_json_atomic(output_root / "matrix-state.json", state)
        families: dict[str, set[str]] = defaultdict(set)
        aggregate: Counter[str] = Counter()
        for run, receipt in zip(runs, receipts, strict=True):
            families[run.physics_group_sha256].add(run.transport_family)
            metrics = receipt.get("metrics")
            if not isinstance(metrics, Mapping):
                raise FormalMatrixError("正式运行收据缺少指标")
            for key, value in metrics.items():
                if isinstance(value, int):
                    aggregate[key] += value
        if len(families) != 256 or any(value != {"TCP", "UDP"} for value in families.values()):
            raise FormalMatrixError("正式矩阵未形成256个完整TCP/UDP配对")
        summary: dict[str, object] = {
            "schema_version": SUMMARY_SCHEMA,
            "status": "review_pending",
            "review_status": "review_pending",
            "planned_run_count": 512,
            "completed_run_count": 512,
            "failed_run_count": 0,
            "valid_pair_count": 256,
            "manifest_sha256": expected_manifest,
            "scenario_source_sha256": scenario_sha,
            "contract_sha256": contract_sha,
            "field_closure_summary_sha256": closure_summary_sha,
            "aggregate": dict(aggregate),
            "finished_at": truth._utc_now(),
        }
        truth._write_json_atomic(output_root / "matrix-summary.json", summary)
        state.update(
            {
                "status": "review_pending",
                "completed_run_count": 512,
                "active_run": None,
                "finished_at": truth._utc_now(),
            }
        )
        truth._write_json_atomic(output_root / "matrix-state.json", state)
        truth._write_json_atomic(
            output_root / "artifact-manifest.json", _artifact_manifest(output_root)
        )
        return summary
    except BaseException as error:
        state.update(
            {
                "status": "failed",
                "failed_run_count": 1,
                "error": str(error),
                "finished_at": truth._utc_now(),
            }
        )
        truth._write_json_atomic(output_root / "matrix-state.json", state)
        truth._write_json_atomic(
            output_root / "artifact-manifest.json", _artifact_manifest(output_root)
        )
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行R2 ns-3 TCP/UDP动力学真值v2正式矩阵")
    parser.add_argument("--params", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = _run_from_params(args.params)
    except (OSError, ValueError, truth.TcpTruthV2Error, FormalMatrixError) as error:
        print(f"R2 ns-3 TCP/UDP动力学真值v2正式矩阵失败：{error}", file=os.sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
