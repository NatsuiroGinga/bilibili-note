#!/usr/bin/env python3
"""DRIFT 正式评价的原 Parquet 只读数据接口。

该模块只在调用数据接口时延迟导入 PyArrow。源数据、目标成员和集合索引均只驻留
当前进程内；本模块不写成员表、攻击副本、缓存、索引或其他派生数据文件。
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import resource
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

try:
    from ch3_drift_formal_contract import (
        REPO_ROOT,
        ContractError,
        atomic_write_json,
        canonical_json_bytes,
        length_prefix_encode,
        load_config,
        member_hash,
        resolve_repo_relative,
        resolve_run_dir,
        sha256_bytes,
        sha256_file,
        transition_status,
    )
except ImportError:
    from thesis.experiments.llm_probe.tools.ch3_drift_formal_contract import (
        REPO_ROOT,
        ContractError,
        atomic_write_json,
        canonical_json_bytes,
        length_prefix_encode,
        load_config,
        member_hash,
        resolve_repo_relative,
        resolve_run_dir,
        sha256_bytes,
        sha256_file,
        transition_status,
    )


SCHEMA_VERSION = "ch3_drift_direct_data_v1"
PARQUET_SCHEMA = ("domain", "label")
DEFAULT_BATCH_SIZE = 8192
TARGET_MAX_ENTITIES = 200000
ENGINEERING_PANEL_ID = "engineering_only"
SOURCE_GROUPS = {
    "source_train_test_exact_unique_in_memory": "training",
    "source_val_exact_unique_in_memory": "validation",
    "source_validation_benign_v1": "validation_benign",
}


class DataContractError(ValueError):
    """直读数据合同失败。"""


@dataclass(frozen=True)
class InputRoleReceipt:
    role: str
    path: str
    year: int
    class_name: str
    split: str
    scope: str
    file_bytes: int
    metadata_rows: int
    rows_read: int
    row_groups: int
    schema: tuple[str, ...]
    schema_types: tuple[str, ...]
    sha256: str
    status: str = "complete"

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "path": self.path,
            "year": self.year,
            "class": self.class_name,
            "split": self.split,
            "scope": self.scope,
            "file_bytes": self.file_bytes,
            "metadata_rows": self.metadata_rows,
            "rows_read": self.rows_read,
            "row_groups": self.row_groups,
            "schema": list(self.schema),
            "schema_types": list(self.schema_types),
            "sha256": self.sha256,
            "status": self.status,
        }


@dataclass(frozen=True)
class InputReceipt:
    config_sha256: str
    data_revision: str
    requested_roles: tuple[InputRoleReceipt, ...]
    batch_size: int
    audit_scope: str
    status: str = "complete"
    config: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def role_map(self) -> dict[str, InputRoleReceipt]:
        return {role.role: role for role in self.requested_roles}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "config_sha256": self.config_sha256,
            "data_revision": self.data_revision,
            "audit_scope": self.audit_scope,
            "batch_size": self.batch_size,
            "requested_role_count": len(self.requested_roles),
            "roles": [role.to_dict() for role in self.requested_roles],
            "status": self.status,
            "content_audit_complete": self.status == "complete",
        }


@dataclass(frozen=True)
class EntityBatch:
    """不落盘的实体批次；域名只在当前消费进程中存在。"""

    exact_esld: tuple[str, ...]
    labels: tuple[int, ...]
    member_hashes: tuple[str, ...]
    year: int
    class_name: str
    panel_id: str
    role: str

    def __len__(self) -> int:
        return len(self.exact_esld)


@dataclass(frozen=True)
class SourceStore:
    """源数据的进程内稳定访问接口，不提供序列化方法。"""

    _entities: tuple[str, ...]
    _labels: tuple[int, ...]
    _sources: tuple[tuple[str, ...], ...]
    role_names: tuple[str, ...]
    raw_rows: int
    unique_count: int
    duplicate_rows: int
    cross_role_overlap_rows: int
    label_conflict_count: int
    order_root_sha256: str
    status: str = "complete"

    @property
    def entities(self) -> tuple[str, ...]:
        return self._entities

    @property
    def labels(self) -> tuple[int, ...]:
        return self._labels

    @property
    def sources(self) -> tuple[tuple[str, ...], ...]:
        return self._sources

    def iter_batches(self, batch_size: int = DEFAULT_BATCH_SIZE) -> Iterator[EntityBatch]:
        if batch_size <= 0:
            raise DataContractError("源数据批大小必须为正数")
        for start in range(0, self.unique_count, batch_size):
            end = min(start + batch_size, self.unique_count)
            yield EntityBatch(
                self._entities[start:end],
                self._labels[start:end],
                tuple("" for _ in range(end - start)),
                0,
                "source",
                "source_store",
                self.role_names[0] if self.role_names else "",
            )

    def summary(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": self.status,
            "role_names": list(self.role_names),
            "raw_rows": self.raw_rows,
            "unique_count": self.unique_count,
            "duplicate_rows": self.duplicate_rows,
            "cross_role_overlap_rows": self.cross_role_overlap_rows,
            "label_conflict_count": self.label_conflict_count,
            "order_root_sha256": self.order_root_sha256,
            "serialized_store": False,
        }


@dataclass(frozen=True)
class TargetUniqueCount:
    year: int
    class_name: str
    role: str
    raw_rows: int | None
    unique_count: int | None
    duplicate_rows: int | None
    unique_set_root_sha256: str | None
    status: str
    blocking_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "year": self.year,
            "class": self.class_name,
            "role": self.role,
            "raw_rows": self.raw_rows,
            "unique_count": self.unique_count,
            "duplicate_rows": self.duplicate_rows,
            "unique_set_root_sha256": self.unique_set_root_sha256,
            "status": self.status,
            "blocking_reason": self.blocking_reason,
        }


def _import_pyarrow() -> Any:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise DataContractError("直读入口需要已核验的 PyArrow；未修改依赖") from exc
    return pa, pq


def _validate_batch(batch: Any, *, role: InputRoleReceipt, pa: Any) -> tuple[list[str], list[int]]:
    names = tuple(batch.schema.names)
    if set(names) != set(PARQUET_SCHEMA) or len(names) != len(PARQUET_SCHEMA):
        raise DataContractError(f"{role.role} 字段必须严格为 domain,label，实际为 {list(names)}")
    domain_index = batch.schema.get_field_index("domain")
    label_index = batch.schema.get_field_index("label")
    domains = batch.column(domain_index).to_pylist()
    labels = batch.column(label_index).to_pylist()
    expected_label = 0 if role.class_name == "benign" else 1
    valid_domains: list[str] = []
    valid_labels: list[int] = []
    for index, (domain, label) in enumerate(zip(domains, labels, strict=True)):
        if not isinstance(domain, str) or not domain:
            raise DataContractError(f"{role.role} 第 {index} 行域名必须是非空字符串")
        if not isinstance(label, int) or isinstance(label, bool) or label not in (0, 1):
            raise DataContractError(f"{role.role} 第 {index} 行标签必须是 0 或 1")
        if label != expected_label:
            raise DataContractError(f"{role.role} 标签与类别 {role.class_name} 不一致")
        valid_domains.append(domain)
        valid_labels.append(label)
    return valid_domains, valid_labels


def _iter_role_rows(role: InputRoleReceipt, *, batch_size: int) -> Iterator[tuple[list[str], list[int]]]:
    if batch_size <= 0:
        raise DataContractError("Parquet 批大小必须为正数")
    pa, pq = _import_pyarrow()
    path = resolve_repo_relative(role.path, must_exist=True)
    reader = pq.ParquetFile(path, memory_map=False, pre_buffer=False)
    try:
        for batch in reader.iter_batches(batch_size=batch_size, columns=list(PARQUET_SCHEMA), use_threads=False):
            yield _validate_batch(batch, role=role, pa=pa)
    finally:
        reader.close()


def _role_receipt_from_config(config: Mapping[str, Any], role_value: Mapping[str, Any], *, batch_size: int) -> InputRoleReceipt:
    path = resolve_repo_relative(role_value["path"], must_exist=True)
    _, pq = _import_pyarrow()
    reader = pq.ParquetFile(path, memory_map=False, pre_buffer=False)
    try:
        metadata = reader.metadata
        schema_arrow = reader.schema_arrow
        names = tuple(schema_arrow.names)
        schema_types = tuple(str(schema_arrow.field(name).type) for name in names)
        if set(names) != set(PARQUET_SCHEMA) or len(names) != len(PARQUET_SCHEMA):
            raise DataContractError(f"{role_value['role']} 字段必须严格为 domain,label，实际为 {list(names)}")
        role = InputRoleReceipt(
            role=role_value["role"],
            path=role_value["path"],
            year=role_value["year"],
            class_name=role_value["class"],
            split=role_value["split"],
            scope=role_value["scope"],
            file_bytes=path.stat().st_size,
            metadata_rows=metadata.num_rows,
            rows_read=0,
            row_groups=metadata.num_row_groups,
            schema=names,
            schema_types=schema_types,
            sha256=sha256_file(path),
        )
    finally:
        reader.close()
    rows_read = 0
    for domains, _ in _iter_role_rows(role, batch_size=batch_size):
        rows_read += len(domains)
    if rows_read != role.metadata_rows:
        raise DataContractError(f"{role.role} 实读行数与 Parquet 元数据不一致")
    return InputRoleReceipt(**{**role.__dict__, "rows_read": rows_read})


def audit_inputs(config: Mapping[str, Any], *, role_names: Sequence[str] | None = None, batch_size: int = DEFAULT_BATCH_SIZE, config_sha256: str | None = None, audit_scope: str = "full") -> InputReceipt:
    """只读审计请求角色的元数据、完整内容、行数和 SHA-256。"""
    if batch_size <= 0:
        raise DataContractError("审计批大小必须为正数")
    configured = {role["role"]: role for role in config.get("input_roles", [])}
    if role_names is None:
        selected = [role["role"] for role in config["input_roles"]]
    else:
        selected = list(role_names)
        if len(selected) != len(set(selected)):
            raise DataContractError("请求角色不得重复")
        missing = [role for role in selected if role not in configured]
        if missing:
            raise DataContractError(f"请求角色不在冻结输入清单中：{missing}")
    receipts = tuple(_role_receipt_from_config(config, configured[name], batch_size=batch_size) for name in selected)
    return InputReceipt(
        config_sha256=config_sha256 or sha256_bytes(canonical_json_bytes(dict(config))),
        data_revision=str(config["data_revision"]),
        requested_roles=receipts,
        batch_size=batch_size,
        audit_scope=audit_scope,
        config=config,
    )


def _resolve_source_roles(role_group: str | Iterable[str], receipt: InputReceipt) -> tuple[InputRoleReceipt, ...]:
    role_map = receipt.role_map
    if isinstance(role_group, str):
        if role_group in SOURCE_GROUPS:
            category = SOURCE_GROUPS[role_group]
            if category == "training":
                names = [role for role in role_map if role.endswith("_train") or role.endswith("_test")]
            elif category == "validation_benign":
                names = [role for role in role_map if role.endswith("_benign_val")]
            else:
                names = [role for role in role_map if role.endswith("_val")]
        else:
            names = [role_group]
    else:
        names = list(role_group)
    if not names:
        raise DataContractError(f"源角色组为空或未在输入收据中请求：{role_group}")
    unknown = [name for name in names if name not in role_map]
    if unknown:
        raise DataContractError(f"源角色未通过本次输入审计：{unknown}")
    chosen = [role_map[name] for name in receipt.role_map if name in set(names)]
    if any(role.scope != "source" for role in chosen):
        raise DataContractError("SourceStore 只能消费 source 角色")
    return tuple(chosen)


def load_source_unique_in_memory(role_group: str | Iterable[str], input_receipt: InputReceipt) -> SourceStore:
    """按配置角色顺序和行首次出现顺序构建进程内 exact eSLD 唯一源 Store。"""
    roles = _resolve_source_roles(role_group, input_receipt)
    values: dict[str, int] = {}
    sources: dict[str, list[str]] = {}
    order: list[str] = []
    raw_rows = 0
    duplicate_rows = 0
    cross_role_overlap_rows = 0
    conflicts = 0
    for role in roles:
        for domains, labels in _iter_role_rows(role, batch_size=input_receipt.batch_size):
            raw_rows += len(domains)
            for domain, label in zip(domains, labels, strict=True):
                if domain in values:
                    duplicate_rows += 1
                    if role.role not in sources[domain]:
                        sources[domain].append(role.role)
                        cross_role_overlap_rows += 1
                    if values[domain] != label:
                        conflicts += 1
                    continue
                values[domain] = label
                sources[domain] = [role.role]
                order.append(domain)
    if conflicts:
        raise DataContractError(f"源数据存在 {conflicts} 条跨标签冲突；拒绝静默选择")
    root = hashlib.sha256()
    for domain in order:
        root.update(length_prefix_encode(domain, str(values[domain]), *sources[domain]))
    return SourceStore(
        tuple(order),
        tuple(values[domain] for domain in order),
        tuple(tuple(sources[domain]) for domain in order),
        tuple(role.role for role in roles),
        raw_rows,
        len(order),
        duplicate_rows,
        cross_role_overlap_rows,
        conflicts,
        root.hexdigest(),
    )


def _resolve_target_role(year: int, class_name: str, receipt: InputReceipt) -> tuple[InputRoleReceipt, str]:
    if not isinstance(year, int) or isinstance(year, bool) or year < 0:
        raise DataContractError("目标年份必须是非负整数")
    if class_name not in ("benign", "dga"):
        raise DataContractError("目标类别必须是 benign 或 dga")
    role_map = receipt.role_map
    target_name = f"T{year}_{class_name}"
    source_name = f"T{year}_{class_name}_val"
    if target_name in role_map:
        return role_map[target_name], "target_official_annual_v1"
    if source_name in role_map:
        return role_map[source_name], ENGINEERING_PANEL_ID
    raise DataContractError(f"目标单元未在本次输入收据中请求：{target_name}")


class TargetSelectionIterator(Iterator[EntityBatch]):
    def __init__(self, role: InputRoleReceipt, panel_id: str, receipt: InputReceipt) -> None:
        self._role = role
        self._panel_id = panel_id
        self._receipt = receipt
        self._batches: tuple[EntityBatch, ...] | None = None
        self._position = 0
        self.selection_receipt: dict[str, Any] | None = None

    def _select(self) -> None:
        if self._batches is not None:
            return
        config = self._receipt.config
        if not config:
            raise DataContractError("输入收据缺少配置身份，无法计算成员摘要")
        namespace = config["member_identity"]["namespace"]
        capacity = int(config["member_identity"]["max_entities_per_year_class"])
        if capacity != TARGET_MAX_ENTITIES:
            raise DataContractError("目标成员上限必须冻结为 200000")
        heap: list[tuple[int, str, str, int]] = []
        heap_domains: dict[str, str] = {}
        digest_domains: dict[str, str] = {}
        raw_rows = 0
        duplicate_rows = 0
        collision_count = 0
        for domains, labels in _iter_role_rows(self._role, batch_size=self._receipt.batch_size):
            raw_rows += len(domains)
            for domain, label in zip(domains, labels, strict=True):
                digest = member_hash(namespace, self._receipt.data_revision, self._panel_id, self._role.year, self._role.class_name, domain)
                digest_int = int(digest, 16)
                if domain in heap_domains:
                    duplicate_rows += 1
                    continue
                if len(heap) >= capacity and digest_int > -heap[0][0]:
                    continue
                previous_domain = digest_domains.get(digest)
                if previous_domain is not None and previous_domain != domain:
                    collision_count += 1
                    continue
                digest_domains[digest] = domain
                heapq.heappush(heap, (-digest_int, digest, domain, label))
                heap_domains[domain] = digest
                if len(heap) > capacity:
                    _, removed_digest, removed_domain, _ = heapq.heappop(heap)
                    heap_domains.pop(removed_domain, None)
                    digest_domains.pop(removed_digest, None)
        if collision_count:
            self.selection_receipt = {
                "schema_version": SCHEMA_VERSION,
                "status": "blocked",
                "collision_count": collision_count,
                "role": self._role.role,
            }
            raise DataContractError(f"目标成员摘要对应不同域名，碰撞数：{collision_count}")
        selected = sorted(heap, key=lambda item: item[1])
        root = hashlib.sha256()
        for _, digest, _, _ in selected:
            root.update(length_prefix_encode(digest))
        entities = tuple(item[2] for item in selected)
        labels = tuple(item[3] for item in selected)
        members = tuple(item[1] for item in selected)
        batch_list = []
        for start in range(0, len(selected), self._receipt.batch_size):
            end = min(start + self._receipt.batch_size, len(selected))
            batch_list.append(EntityBatch(entities[start:end], labels[start:end], members[start:end], self._role.year, self._role.class_name, self._panel_id, self._role.role))
        self._batches = tuple(batch_list)
        self.selection_receipt = {
            "schema_version": SCHEMA_VERSION,
            "status": "complete",
            "panel_id": self._panel_id,
            "year": self._role.year,
            "class": self._role.class_name,
            "role": self._role.role,
            "input_sha256": self._role.sha256,
            "raw_rows": raw_rows,
            "selected_count": len(selected),
            "max_entities": capacity,
            "unique_count": None,
            "unique_count_status": "unknown_due_to_bounded_selector",
            "heap_duplicate_rows": duplicate_rows,
            "digest_collision_count": 0,
            "selected_member_root_sha256": root.hexdigest(),
            "algorithm": "bounded_min_sha256_heap_v1",
            "exact_esld_preserved": True,
            "engineering_only": self._panel_id == ENGINEERING_PANEL_ID,
        }

    def __iter__(self) -> TargetSelectionIterator:
        return self

    def __next__(self) -> EntityBatch:
        self._select()
        assert self._batches is not None
        if self._position >= len(self._batches):
            raise StopIteration
        batch = self._batches[self._position]
        self._position += 1
        return batch


def iter_target_selected(year: int, class_name: str, input_receipt: InputReceipt) -> Iterator[EntityBatch]:
    """返回延迟执行的目标固定哈希选择器；首次迭代才完整扫描一次。"""
    role, panel_id = _resolve_target_role(year, class_name, input_receipt)
    return TargetSelectionIterator(role, panel_id, input_receipt)


def count_target_unique_in_memory(year: int, class_name: str, input_receipt: InputReceipt) -> TargetUniqueCount:
    """独立执行目标单元精确 unique 统计；容量不足时明确返回 blocked。"""
    role, _ = _resolve_target_role(year, class_name, input_receipt)
    values: set[str] = set()
    raw_rows = 0
    try:
        for domains, _ in _iter_role_rows(role, batch_size=input_receipt.batch_size):
            raw_rows += len(domains)
            values.update(domains)
        root = hashlib.sha256()
        namespace = input_receipt.config["member_identity"]["namespace"]
        panel_id = "engineering_only" if role.scope == "source" else "target_official_annual_v1"
        digests = sorted(member_hash(namespace, input_receipt.data_revision, panel_id, year, class_name, domain) for domain in values)
        for digest in digests:
            root.update(length_prefix_encode(digest))
        return TargetUniqueCount(year, class_name, role.role, raw_rows, len(values), raw_rows - len(values), root.hexdigest(), "complete")
    except MemoryError:
        return TargetUniqueCount(year, class_name, role.role, raw_rows, None, None, None, "blocked", "blocked_no_non_materialized_exact_count")


def _set_receipt_config(receipt: InputReceipt, config: Mapping[str, Any]) -> InputReceipt:
    object.__setattr__(receipt, "config", config)
    return receipt


def _rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def _write_receipt(run_dir: Path, name: str, payload: Mapping[str, Any]) -> str:
    relative = run_dir.relative_to(REPO_ROOT) / name
    return atomic_write_json(relative, payload)


def _development_audit(config: Mapping[str, Any], config_sha256: str, run_dir: Path, batch_size: int) -> dict[str, Any]:
    roles = ("T17_benign_val", "T17_dga_val")
    started = time.monotonic()
    receipt = _set_receipt_config(audit_inputs(config, role_names=roles, batch_size=batch_size, config_sha256=config_sha256, audit_scope="development"), config)
    _write_receipt(run_dir, "input-receipt.json", receipt.to_dict())
    source = load_source_unique_in_memory(roles, receipt)
    _write_receipt(run_dir, "source-read-receipt.json", source.summary())
    _write_receipt(run_dir, "overlap-conflict-audit.json", {**source.summary(), "scope": "engineering_only", "source_validation_policy": "not_frozen"})
    selections: dict[str, Any] = {}
    counts: dict[str, Any] = {}
    for class_name in ("benign", "dga"):
        iterator = iter_target_selected(17, class_name, receipt)
        for _ in iterator:
            pass
        assert isinstance(iterator, TargetSelectionIterator)
        selections[class_name] = iterator.selection_receipt
        counts[class_name] = count_target_unique_in_memory(17, class_name, receipt).to_dict()
    _write_receipt(run_dir, "target-selection-receipt.json", {"schema_version": SCHEMA_VERSION, "status": "complete", "scope": "engineering_only", "units": selections})
    _write_receipt(run_dir, "target-unique-count-receipt.json", {"schema_version": SCHEMA_VERSION, "scope": "engineering_only", "units": counts})
    elapsed = time.monotonic() - started
    _write_receipt(run_dir, "capacity-preflight.json", {"schema_version": SCHEMA_VERSION, "status": "complete", "scope": "development", "batch_size": batch_size, "peak_rss_bytes": _rss_bytes(), "elapsed_seconds": elapsed, "algorithm": "in_process_pyarrow_read_only"})
    return {"schema_version": SCHEMA_VERSION, "status": "complete", "scope": "development", "input_roles": list(roles), "engineering_only": True, "target_full_scope_not_covered": True, "elapsed_seconds": elapsed, "unvalidated_items": ["T17-T19 全源角色", "T20-T25 全目标面板", "服务器容量", "源训练-验证全量重合", "family 资格"]}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DRIFT 原 Parquet 只读数据审计")
    parser.add_argument("--config", required=True, help="评价配置相对路径")
    parser.add_argument("--run-dir", required=True, help="受管运行目录相对路径")
    parser.add_argument("--audit", action="store_true", help="执行真实输入审计")
    parser.add_argument("--scope", choices=("development", "full"), default="development", help="审计范围")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="PyArrow 读取批大小")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if not args.audit:
        print("直读入口必须明确指定 --audit", file=sys.stderr)
        return 2
    try:
        run_dir = resolve_run_dir(args.run_dir)
        if run_dir.exists() and any(run_dir.iterdir()):
            raise DataContractError("运行目录已有制品；请使用带后缀的新运行身份，不覆盖旧收据")
        config, config_sha256 = load_config(args.config)
        if config.get("config_kind") != "evaluation":
            raise DataContractError("直读审计必须使用评价配置")
        if args.scope != "development":
            raise DataContractError("本机本轮仅允许 development；全源和目标审计留待服务器")
        if args.batch_size <= 0:
            raise DataContractError("--batch-size 必须为正数")
        transition_status(run_dir.relative_to(REPO_ROOT), "created", stage="direct_read_audit")
        transition_status(run_dir.relative_to(REPO_ROOT), "running", stage="direct_read_audit")
        result = _development_audit(config, config_sha256, run_dir, args.batch_size)
        _write_receipt(run_dir, "audit-summary.json", result)
        transition_status(run_dir.relative_to(REPO_ROOT), "complete", stage="direct_read_audit")
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (ContractError, DataContractError) as exc:
        print(f"直读审计失败：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
