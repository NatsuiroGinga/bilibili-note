"""并行续跑 R2 ns-3 TCP/UDP 动力学真值 v2 正式矩阵。"""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flow_probe import r2_ns3_protocol_dynamics_v2_runner as formal
from flow_probe import r2_ns3_tcp_truth_v2_runner as truth
from flow_probe.r2_ns3_protocol_matrix import ProtocolRunConfig
from flow_probe.r2_ns3_protocol_runner import _load_manifest


PARAMS_SCHEMA = "flow_probe_r2_ns3_protocol_dynamics_v2_parallel_params_v2"
STATE_SCHEMA = "flow_probe_r2_ns3_protocol_dynamics_v2_parallel_state_v2"


def _load_reused(
    roots: Sequence[Path],
    runs: Sequence[ProtocolRunConfig],
    scenario_sha: str,
    contract_sha: str,
) -> dict[int, Mapping[str, object]]:
    completed_counts: list[int] = []
    for root in roots:
        state = truth._read_json(root / "matrix-state.json", "续跑来源状态")
        completed = state.get("completed_run_count")
        if state.get("status") != "failed" or not isinstance(completed, int):
            raise formal.FormalMatrixError("续跑来源未形成受控停止状态")
        completed_counts.append(completed)
    reused: dict[int, Mapping[str, object]] = {}
    for index, run in enumerate(runs):
        identity = f"{index:04d}-{run.transport_family.lower()}"
        dirname = f"{identity}-{run.physics_group_sha256[:12]}"
        candidates: list[Path] = []
        for root in roots:
            candidates.append(root / "runs" / dirname)
            shards_root = root / "shards"
            if shards_root.is_dir() and not shards_root.is_symlink():
                candidates.extend(
                    shard / "runs" / dirname
                    for shard in shards_root.iterdir()
                    if shard.is_dir() and not shard.is_symlink()
                )
        existing = [candidate for candidate in candidates if candidate.exists()]
        if not existing:
            continue
        if len(existing) != 1:
            raise formal.FormalMatrixError("续跑来源出现重复成功配置")
        run_dir = existing[0]
        if not run_dir.is_dir() or run_dir.is_symlink():
            raise formal.FormalMatrixError("串行来源成功目录不安全")
        receipt = truth._read_json(run_dir / "receipt.json", "串行来源成功收据")
        if (
            receipt.get("status") != "pass"
            or receipt.get("coverage") != identity
            or receipt.get("physics_group_sha256") != run.physics_group_sha256
            or receipt.get("scenario_source_sha256") != scenario_sha
            or receipt.get("contract_sha256") != contract_sha
        ):
            raise formal.FormalMatrixError("串行来源成功收据绑定不一致")
        for filename, key in (
            ("main.csv", "main_csv_sha256"),
            ("tcp-sender-windows.csv", "tcp_csv_sha256"),
        ):
            artifact = run_dir / filename
            expected = formal._require_sha(receipt.get(key), f"复用{filename}哈希")
            if (
                not artifact.is_file()
                or artifact.is_symlink()
                or truth._file_sha256(artifact) != expected
            ):
                raise formal.FormalMatrixError(f"复用CSV哈希不一致：{filename}")
        reused[index] = receipt
    if len(reused) != max(completed_counts):
        raise formal.FormalMatrixError("续跑来源完成数与唯一完整成功收据数不一致")
    return reused


def _run_shard(
    shard_id: int,
    assigned: Sequence[tuple[int, ProtocolRunConfig]],
    shard_root: Path,
    ns3_root: Path,
    executable: Path,
    contract_sha: str,
    scenario_sha: str,
) -> list[Mapping[str, object]]:
    runs_root = shard_root / "runs"
    runs_root.mkdir(parents=True)
    state_path = shard_root / "state.json"
    exit_path = shard_root / "exit-code.json"
    log_path = shard_root / "shard.log"
    state: dict[str, object] = {
        "shard_id": shard_id,
        "status": "running",
        "planned_run_count": len(assigned),
        "completed_run_count": 0,
        "failed_run_count": 0,
        "active_run": None,
        "started_at": truth._utc_now(),
    }
    truth._write_json_atomic(state_path, state)
    receipts: list[Mapping[str, object]] = []
    try:
        for index, run in assigned:
            identity = f"{index:04d}-{run.transport_family.lower()}"
            state.update({"active_run": identity, "updated_at": truth._utc_now()})
            truth._write_json_atomic(state_path, state)
            started = time.monotonic()
            receipt = truth._run_one(
                ns3_root,
                runs_root,
                identity,
                run,
                contract_sha,
                scenario_sha,
                executable,
            )
            receipts.append(receipt)
            with log_path.open("a", encoding="utf-8") as log:
                log.write(
                    f"{truth._utc_now()} pass {identity} "
                    f"{time.monotonic() - started:.6f}s\n"
                )
            state.update(
                {
                    "completed_run_count": len(receipts),
                    "active_run": None,
                    "updated_at": truth._utc_now(),
                }
            )
            truth._write_json_atomic(state_path, state)
        state.update({"status": "finished", "finished_at": truth._utc_now()})
        truth._write_json_atomic(state_path, state)
        truth._write_json_atomic(exit_path, {"exit_code": 0, "recorded_at": truth._utc_now()})
        return receipts
    except BaseException as error:
        state.update(
            {
                "status": "failed",
                "failed_run_count": 1,
                "error": str(error),
                "finished_at": truth._utc_now(),
            }
        )
        truth._write_json_atomic(state_path, state)
        truth._write_json_atomic(exit_path, {"exit_code": 1, "recorded_at": truth._utc_now()})
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"{truth._utc_now()} failed {error}\n")
        raise


def _run_from_params(path: Path) -> Mapping[str, object]:
    params = truth._read_json(path.resolve(), "并行正式矩阵参数")
    expected_keys = {
        "schema_version",
        "project_root",
        "ns3_root",
        "manifest_path",
        "scenario_source",
        "contract_path",
        "field_closure_output_dir",
        "resume_from_output_dirs",
        "output_dir",
        "expected_manifest_sha256",
        "expected_scenario_source_sha256",
        "expected_contract_sha256",
        "expected_field_closure_summary_sha256",
        "worker_count",
    }
    if set(params) != expected_keys or params.get("schema_version") != PARAMS_SCHEMA:
        raise formal.FormalMatrixError("并行参数键集合或模式版本不符")
    worker_count = params.get("worker_count")
    if worker_count != 24:
        raise formal.FormalMatrixError("正式并行分片数必须恰为24")
    project_root = Path(str(params["project_root"])).resolve()
    if project_root != Path(__file__).resolve().parents[2]:
        raise formal.FormalMatrixError("project_root与当前安装代码根不一致")
    ns3_root = Path(str(params["ns3_root"])).resolve()
    manifest_path = formal._resolve_under(project_root, params["manifest_path"], "manifest_path")
    scenario_path = formal._resolve_under(project_root, params["scenario_source"], "scenario_source")
    contract_path = formal._resolve_under(project_root, params["contract_path"], "contract_path")
    closure_root = formal._resolve_under(
        project_root, params["field_closure_output_dir"], "field_closure_output_dir"
    )
    resume_values = params["resume_from_output_dirs"]
    if not isinstance(resume_values, list) or len(resume_values) != 2:
        raise formal.FormalMatrixError("24路续跑必须绑定两个来源目录")
    resume_roots = [
        formal._resolve_under(project_root, value, "resume_from_output_dirs")
        for value in resume_values
    ]
    output_root = formal._resolve_under(project_root, params["output_dir"], "output_dir")
    if output_root != project_root / "runs/ns3-data/r2-protocol-dynamics-v2-formal-attempt3":
        raise formal.FormalMatrixError("24路并行输出身份不符")
    manifest_sha = formal._require_sha(params["expected_manifest_sha256"], "清单哈希")
    scenario_sha = formal._require_sha(params["expected_scenario_source_sha256"], "场景哈希")
    contract_sha = formal._require_sha(params["expected_contract_sha256"], "合同哈希")
    closure_sha = formal._require_sha(
        params["expected_field_closure_summary_sha256"], "字段闭合汇总哈希"
    )
    for artifact, expected in (
        (manifest_path, manifest_sha),
        (scenario_path, scenario_sha),
        (contract_path, contract_sha),
    ):
        if truth._file_sha256(artifact) != expected:
            raise formal.FormalMatrixError(f"正式输入哈希不一致：{artifact.name}")
    formal._verify_field_closure(closure_root, closure_sha, scenario_sha, contract_sha)
    compiled_source = ns3_root / truth.COMPILED_SOURCE
    if truth._file_sha256(compiled_source) != scenario_sha:
        raise formal.FormalMatrixError("项目场景与scratch双副本哈希不一致")
    executable = ns3_root / "build/scratch/ns3.48-flow-probe-r2-dynamics-v2-default"
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise formal.FormalMatrixError("已构建v2可执行文件不存在或不可执行")
    runs = _load_manifest(manifest_path)
    reused = _load_reused(resume_roots, runs, scenario_sha, contract_sha)
    pending = [(index, run) for index, run in enumerate(runs) if index not in reused]
    if output_root.exists() or output_root.is_symlink():
        raise formal.FormalMatrixError("并行输出根已存在，禁止覆盖")
    output_root.mkdir(parents=True)
    shards_root = output_root / "shards"
    shards_root.mkdir()
    assignments = [pending[shard_id::worker_count] for shard_id in range(worker_count)]
    truth._write_json_atomic(
        output_root / "reused-receipts.json",
        [{"manifest_index": index, "receipt": reused[index]} for index in sorted(reused)],
    )
    started = time.monotonic()
    global_state: dict[str, object] = {
        "schema_version": STATE_SCHEMA,
        "status": "running",
        "review_status": "review_pending",
        "worker_count": worker_count,
        "running_shard_count": worker_count,
        "reused_run_count": len(reused),
        "parallel_completed_run_count": 0,
        "completed_run_count": len(reused),
        "failed_run_count": 0,
        "planned_run_count": 512,
        "started_at": truth._utc_now(),
    }
    truth._write_json_atomic(output_root / "matrix-state.json", global_state)
    futures: list[Future[list[Mapping[str, object]]]] = []
    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="r2-v2") as executor:
        for shard_id, assigned in enumerate(assignments):
            futures.append(
                executor.submit(
                    _run_shard,
                    shard_id,
                    assigned,
                    shards_root / f"shard-{shard_id:02d}",
                    ns3_root,
                    executable,
                    contract_sha,
                    scenario_sha,
                )
            )
        while not all(future.done() for future in futures):
            time.sleep(2)
            states = []
            for shard_id in range(worker_count):
                state_path = shards_root / f"shard-{shard_id:02d}/state.json"
                if state_path.is_file():
                    states.append(truth._read_json(state_path, "分片状态"))
            parallel_completed = sum(int(state["completed_run_count"]) for state in states)
            failed = sum(int(state["failed_run_count"]) for state in states)
            running = sum(state["status"] == "running" for state in states)
            elapsed = max(time.monotonic() - started, 1e-9)
            rate = parallel_completed * 60.0 / elapsed
            eta = None
            if rate > 0:
                eta = (
                    datetime.now(timezone.utc)
                    + timedelta(seconds=(len(pending) - parallel_completed) * 60.0 / rate)
                ).isoformat()
            global_state.update(
                {
                    "running_shard_count": running,
                    "parallel_completed_run_count": parallel_completed,
                    "completed_run_count": len(reused) + parallel_completed,
                    "failed_run_count": failed,
                    "runs_per_minute": rate,
                    "estimated_finish_at": eta,
                    "updated_at": truth._utc_now(),
                }
            )
            truth._write_json_atomic(output_root / "matrix-state.json", global_state)
    errors = [future.exception() for future in futures if future.exception() is not None]
    new_receipts = [receipt for future in futures if future.exception() is None for receipt in future.result()]
    if errors:
        global_state.update(
            {"status": "failed", "running_shard_count": 0, "error": str(errors[0]), "finished_at": truth._utc_now()}
        )
        truth._write_json_atomic(output_root / "matrix-state.json", global_state)
        truth._write_json_atomic(output_root / "artifact-manifest.json", truth._artifact_manifest(output_root))
        raise formal.FormalMatrixError(str(errors[0]))
    all_receipts = [reused[index] for index in sorted(reused)] + new_receipts
    families: dict[str, set[str]] = defaultdict(set)
    aggregate: Counter[str] = Counter()
    for run in runs:
        families[run.physics_group_sha256].add(run.transport_family)
    for receipt in all_receipts:
        metrics = receipt.get("metrics")
        if isinstance(metrics, Mapping):
            for key, value in metrics.items():
                if isinstance(value, int):
                    aggregate[key] += value
    if len(all_receipts) != 512 or len(families) != 256:
        raise formal.FormalMatrixError("并行续跑未形成512条运行和256个配对")
    summary = {
        "schema_version": formal.SUMMARY_SCHEMA,
        "status": "review_pending",
        "review_status": "review_pending",
        "planned_run_count": 512,
        "completed_run_count": 512,
        "failed_run_count": 0,
        "valid_pair_count": 256,
        "reused_run_count": len(reused),
        "parallel_run_count": len(new_receipts),
        "worker_count": worker_count,
        "manifest_sha256": manifest_sha,
        "scenario_source_sha256": scenario_sha,
        "contract_sha256": contract_sha,
        "field_closure_summary_sha256": closure_sha,
        "resource_evidence": {"logical_cpu_count": 208, "available_memory_gib": 685},
        "aggregate": dict(aggregate),
        "finished_at": truth._utc_now(),
    }
    truth._write_json_atomic(output_root / "matrix-summary.json", summary)
    global_state.update(
        {
            "status": "review_pending",
            "running_shard_count": 0,
            "parallel_completed_run_count": len(new_receipts),
            "completed_run_count": 512,
            "failed_run_count": 0,
            "finished_at": truth._utc_now(),
        }
    )
    truth._write_json_atomic(output_root / "matrix-state.json", global_state)
    truth._write_json_atomic(output_root / "artifact-manifest.json", truth._artifact_manifest(output_root))
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="并行续跑R2 ns-3动力学真值v2正式矩阵")
    parser.add_argument("--params", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        summary = _run_from_params(args.params)
    except (OSError, ValueError, truth.TcpTruthV2Error, formal.FormalMatrixError) as error:
        print(f"R2 ns-3动力学真值v2并行续跑失败：{error}", file=os.sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
