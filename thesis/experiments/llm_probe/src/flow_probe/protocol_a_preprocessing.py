"""Protocol A Raw83 的训练区 A/B 变换状态与共享视图。"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterator, Mapping

import numpy as np

from flow_probe.protocol_a_raw83 import (
    DIJK_FEATURES,
    QUANTILE_INDICES,
    SCHEMA_VERSION,
    SOURCE_ROW_COUNT,
    SPECIAL_INDICES,
    ProtocolARaw83Error,
    _artifact,
    _open_partial_npy,
    atomic_write_json,
    canonical_sha256,
    load_json,
    sha256_file,
    source_data_root,
    validate_config,
)


def _training_indices(output_root: Path) -> np.ndarray:
    bitmap = np.load(
        output_root / "split" / "training-valid-flow-bitmap.npy",
        mmap_mode="r",
        allow_pickle=False,
    )
    if bitmap.shape != (SOURCE_ROW_COUNT,) or not np.all((bitmap == 0) | (bitmap == 1)):
        raise ProtocolARaw83Error("训练有效流位图非法")
    indices = np.flatnonzero(bitmap)
    if indices.size == 0:
        raise ProtocolARaw83Error("训练有效流不得为空")
    return indices


def _iter_index_batches(indices: np.ndarray, batch_rows: int) -> Iterator[np.ndarray]:
    if batch_rows <= 0:
        raise ProtocolARaw83Error("batch_rows 必须为正整数")
    for start in range(0, indices.size, batch_rows):
        yield indices[start : start + batch_rows]


def _save_npz_atomic(path: Path, run_id: str, **arrays: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{run_id}")
    with temporary.open("wb") as handle:
        np.savez(handle, **arrays)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _state_content_hash(path: Path) -> str:
    with np.load(path, allow_pickle=False) as state:
        content = {
            name: {
                "dtype": state[name].dtype.str,
                "shape": list(state[name].shape),
                "sha256": hashlib.sha256(state[name].tobytes(order="C")).hexdigest(),
            }
            for name in sorted(state.files)
        }
    return canonical_sha256(content)


def fit_candidate_a(
    config: Mapping[str, Any],
    *,
    batch_rows: int,
) -> dict[str, Any]:
    """只用训练有效流拟合均值填补与 StandardScaler 状态。"""

    validate_config(config)
    from sklearn import __version__ as sklearn_version
    from sklearn.preprocessing import StandardScaler

    run_root = Path(config["paths"]["output_root"])
    output_root = source_data_root(config)
    raw = np.load(output_root / "raw" / "lspr23-raw83.npy", mmap_mode="r", allow_pickle=False)
    indices = _training_indices(output_root)
    width = len(DIJK_FEATURES)
    sums = np.zeros(width, dtype=np.float64)
    compensation = np.zeros(width, dtype=np.float64)
    finite_counts = np.zeros(width, dtype=np.int64)
    missing_counts = np.zeros(width, dtype=np.int64)
    for rows in _iter_index_batches(indices, batch_rows):
        batch = np.asarray(raw[rows], dtype=np.float64)
        finite = np.isfinite(batch)
        missing_counts += np.count_nonzero(~finite, axis=0)
        finite_counts += np.count_nonzero(finite, axis=0)
        batch_sums = np.where(finite, batch, 0.0).sum(axis=0, dtype=np.float64)
        corrected = batch_sums - compensation
        updated = sums + corrected
        compensation = (updated - sums) - corrected
        sums = updated
    if np.any(finite_counts == 0):
        fields = [DIJK_FEATURES[index] for index in np.flatnonzero(finite_counts == 0)]
        raise ProtocolARaw83Error(f"训练区全缺字段：{fields}")
    means = sums / finite_counts
    scaler = StandardScaler(copy=True, with_mean=True, with_std=True)
    for rows in _iter_index_batches(indices, batch_rows):
        batch = np.asarray(raw[rows], dtype=np.float64)
        missing = ~np.isfinite(batch)
        if np.any(missing):
            batch[missing] = np.take(means, np.nonzero(missing)[1])
        scaler.partial_fit(batch)
    if int(np.asarray(scaler.n_samples_seen_).max()) != indices.size:
        raise ProtocolARaw83Error("StandardScaler 实际样本数与训练有效流不一致")
    scale = np.asarray(scaler.scale_, dtype=np.float64)
    variance = np.asarray(scaler.var_, dtype=np.float64)
    scale[variance == 0] = 1.0
    state_path = output_root / "states" / "candidate-a-standard.npz"
    _save_npz_atomic(
        state_path,
        str(config["run_id"]),
        mean=np.asarray(scaler.mean_, dtype="<f8"),
        variance=np.asarray(variance, dtype="<f8"),
        scale=np.asarray(scale, dtype="<f8"),
        finite_counts=np.asarray(finite_counts, dtype="<i8"),
        missing_or_invalid_counts=np.asarray(missing_counts, dtype="<i8"),
    )
    hash_payload = {
        "schema_version": f"{SCHEMA_VERSION}-candidate-a-state-v1",
        "algorithm": "mean-impute-standardscaler-ddof0-clip-v1",
        "clip": list(config["preprocessing"]["candidate_a"]["clip"]),
        "training_valid_flow_count": int(indices.size),
        "training_valid_flow_bitmap_sha256": sha256_file(
            output_root / "split" / "training-valid-flow-bitmap.npy"
        ),
        "raw_file_sha256": sha256_file(output_root / "raw" / "lspr23-raw83.npy"),
        "sklearn_version": sklearn_version,
        "state_content_sha256": _state_content_hash(state_path),
    }
    identity = {
        **hash_payload,
        "transform_state_hash": canonical_sha256(hash_payload),
        "state_artifact": _artifact(state_path),
    }
    atomic_write_json(run_root / "receipts" / "p3-candidate-a-state.json", identity)
    return identity


def _fill_training_matrix(
    raw: np.ndarray,
    indices: np.ndarray,
    columns: tuple[int, ...],
    means: np.ndarray,
    destination: np.memmap,
    *,
    batch_rows: int,
) -> None:
    offset = 0
    for rows in _iter_index_batches(indices, batch_rows):
        batch = np.asarray(raw[np.ix_(rows, columns)], dtype=np.float64)
        missing = ~np.isfinite(batch)
        if np.any(missing):
            batch[missing] = np.take(means, np.nonzero(missing)[1])
        destination[offset : offset + rows.size] = batch.astype("<f4")
        offset += rows.size
    destination.flush()


def fit_candidate_b(
    config: Mapping[str, Any],
    *,
    batch_rows: int,
) -> dict[str, Any]:
    """保持官方单次 C 行主序随机流，逐列拟合分位数地标。"""

    validate_config(config)
    from numpy import __version__ as numpy_version
    from sklearn import __version__ as sklearn_version
    from sklearn.preprocessing import QuantileTransformer

    run_root = Path(config["paths"]["output_root"])
    output_root = source_data_root(config)
    run_id = str(config["run_id"])
    raw = np.load(output_root / "raw" / "lspr23-raw83.npy", mmap_mode="r", allow_pickle=False)
    indices = _training_indices(output_root)
    with np.load(output_root / "states" / "candidate-a-standard.npz", allow_pickle=False) as a_state:
        means = np.asarray(a_state["mean"], dtype=np.float64)[list(QUANTILE_INDICES)]
    parameters = config["preprocessing"]["candidate_b"]
    noise_base = float(parameters["noise"])
    n_quantiles = max(min(indices.size // 30, 1_000), 10)
    if n_quantiles != int(parameters["expected_n_quantiles"]):
        raise ProtocolARaw83Error(
            f"分位数数量与冻结配置不一致：{n_quantiles}"
        )
    temporary_root = run_root / "temporary" / "candidate-b"
    temporary_root.mkdir(parents=True, exist_ok=True)
    filled_path = temporary_root / f"filled-noisy-training.f4.partial.{run_id}.npy"
    filled_noisy = _open_partial_npy(
        filled_path,
        dtype="<f4",
        shape=(indices.size, len(QUANTILE_INDICES)),
    )
    _fill_training_matrix(
        raw,
        indices,
        QUANTILE_INDICES,
        means,
        filled_noisy,
        batch_rows=batch_rows,
    )
    stds = np.empty(len(QUANTILE_INDICES), dtype="<f4")
    for local_index in range(len(QUANTILE_INDICES)):
        stds[local_index] = np.std(filled_noisy[:, local_index], ddof=0)
    noise_scale = noise_base / np.maximum(stds, noise_base)
    random_generator = np.random.default_rng(int(parameters["random_state"]))
    noise_receipts_root = run_root / "receipts" / "p4-noise-batches"
    noise_receipts_root.mkdir(parents=True, exist_ok=True)
    previous_stop = 0
    noise_receipt_hashes: list[str] = []
    filled_content_digest = hashlib.sha256()
    for start in range(0, indices.size, batch_rows):
        stop = min(start + batch_rows, indices.size)
        if start != previous_stop:
            raise ProtocolARaw83Error("P4 随机流批起点不连续")
        noise_batch = random_generator.standard_normal(
            size=(stop - start, len(QUANTILE_INDICES)),
            dtype=np.float64,
        )
        batch = np.array(filled_noisy[start:stop], dtype="<f4", copy=True)
        batch += noise_batch * noise_scale
        filled_noisy[start:stop] = batch
        filled_noisy.flush()
        content_sha256 = hashlib.sha256(batch.tobytes(order="C")).hexdigest()
        filled_content_digest.update(batch.tobytes(order="C"))
        receipt_path = noise_receipts_root / f"batch-{start:09d}-{stop:09d}.json"
        receipt = {
            "schema_version": f"{SCHEMA_VERSION}-p4-noise-batch-receipt-v1",
            "start_row": start,
            "end_row": stop,
            "shape": [stop - start, len(QUANTILE_INDICES)],
            "random_stream": parameters["random_stream"],
            "numpy_version": numpy_version,
            "filled_noisy_slice_sha256": content_sha256,
        }
        if receipt_path.exists() and load_json(receipt_path) != receipt:
            raise ProtocolARaw83Error(f"P4 随机流批收据不匹配：{receipt_path}")
        atomic_write_json(receipt_path, receipt)
        noise_receipt_hashes.append(sha256_file(receipt_path))
        previous_stop = stop
    if previous_stop != indices.size:
        raise ProtocolARaw83Error("P4 随机流未连续覆盖全部训练流")
    noisy_training_sha256 = filled_content_digest.hexdigest()
    quantiles_path = temporary_root / f"quantiles.f8.partial.{run_id}.npy"
    references_path = temporary_root / f"references.f8.partial.{run_id}.npy"
    quantiles = _open_partial_npy(
        quantiles_path,
        dtype="<f8",
        shape=(n_quantiles, len(QUANTILE_INDICES)),
    )
    references_map = _open_partial_npy(
        references_path,
        dtype="<f8",
        shape=(n_quantiles,),
    )
    column_receipts = run_root / "receipts" / "p4-quantile-columns"
    column_receipts.mkdir(parents=True, exist_ok=True)
    references: np.ndarray | None = None
    for local_index in range(len(QUANTILE_INDICES)):
        receipt_path = column_receipts / f"column-{local_index:02d}.json"
        if receipt_path.exists():
            receipt = load_json(receipt_path)
            column = np.asarray(quantiles[:, local_index])
            column_sha = hashlib.sha256(column.tobytes(order="C")).hexdigest()
            current_references = np.asarray(references_map)
            references_sha = hashlib.sha256(
                current_references.tobytes(order="C")
            ).hexdigest()
            if (
                receipt.get("raw_feature_index") != QUANTILE_INDICES[local_index]
                or receipt.get("quantiles_sha256") != column_sha
                or receipt.get("references_sha256") != references_sha
                or receipt.get("noisy_training_sha256") != noisy_training_sha256
            ):
                raise ProtocolARaw83Error(f"分位数列断点收据不匹配：{receipt_path}")
            if references is None:
                references = current_references.copy()
            elif not np.array_equal(references, current_references):
                raise ProtocolARaw83Error("断点 references_ 不一致")
            continue
        transformer = QuantileTransformer(
            n_quantiles=n_quantiles,
            output_distribution=str(parameters["output_distribution"]),
            subsample=parameters["subsample"],
            random_state=int(parameters["random_state"]),
            copy=True,
        )
        transformer.fit(np.asarray(filled_noisy[:, local_index : local_index + 1]))
        quantiles[:, local_index] = np.asarray(transformer.quantiles_)[:, 0]
        quantiles.flush()
        current_references = np.asarray(transformer.references_, dtype="<f8")
        if references is None:
            references = current_references
            references_map[:] = current_references
            references_map.flush()
        elif not np.array_equal(references, current_references):
            raise ProtocolARaw83Error("逐列 QuantileTransformer references_ 不一致")
        atomic_write_json(
            receipt_path,
            {
                "schema_version": f"{SCHEMA_VERSION}-p4-quantile-column-receipt-v1",
                "local_column_index": local_index,
                "raw_feature_index": QUANTILE_INDICES[local_index],
                "quantiles_sha256": hashlib.sha256(
                    np.asarray(quantiles[:, local_index]).tobytes(order="C")
                ).hexdigest(),
                "references_sha256": hashlib.sha256(
                    current_references.tobytes(order="C")
                ).hexdigest(),
                "noisy_training_sha256": noisy_training_sha256,
            },
        )
    if references is None:
        raise ProtocolARaw83Error("分位数状态未生成")
    state_path = output_root / "states" / "candidate-b-official-quantile.npz"
    _save_npz_atomic(
        state_path,
        run_id,
        mean=np.asarray(means, dtype="<f8"),
        std=np.asarray(stds, dtype="<f8"),
        noise_scale=np.asarray(noise_scale, dtype="<f8"),
        quantiles=np.asarray(quantiles, dtype="<f8"),
        references=np.asarray(references, dtype="<f8"),
    )
    hash_payload = {
        "schema_version": f"{SCHEMA_VERSION}-candidate-b-state-v1",
        "algorithm": "official-quantile-parameters-seven-a-columns-task-adaptation-v1",
        "official_commit": config["vendor"]["commit"],
        "quantile_indices": list(QUANTILE_INDICES),
        "special_indices_copied_from_a": list(SPECIAL_INDICES),
        "n_quantiles": n_quantiles,
        "output_distribution": parameters["output_distribution"],
        "subsample": parameters["subsample"],
        "random_state": parameters["random_state"],
        "noise": parameters["noise"],
        "random_stream": parameters["random_stream"],
        "random_stream_batch_continuity": "contiguous-[start,end)-cover-training-valid-order-v1",
        "random_stream_batch_rows": int(batch_rows),
        "random_stream_batch_count": len(noise_receipt_hashes),
        "training_valid_flow_count": int(indices.size),
        "training_valid_flow_bitmap_sha256": sha256_file(
            output_root / "split" / "training-valid-flow-bitmap.npy"
        ),
        "numpy_version": numpy_version,
        "sklearn_version": sklearn_version,
        "filled_noisy_content_sha256": noisy_training_sha256,
        "noise_batch_receipts_sha256": canonical_sha256(noise_receipt_hashes),
        "state_content_sha256": _state_content_hash(state_path),
    }
    identity = {
        **hash_payload,
        "transform_state_hash": canonical_sha256(hash_payload),
        "state_artifact": _artifact(state_path),
    }
    atomic_write_json(run_root / "receipts" / "p4-candidate-b-state.json", identity)
    for temporary_path in (filled_path, quantiles_path, references_path):
        if temporary_path.exists():
            temporary_path.unlink()
    if temporary_root.exists() and not any(temporary_root.iterdir()):
        temporary_root.rmdir()
    return identity


def _restore_quantile_transformer(state_path: Path) -> Any:
    from sklearn.preprocessing import QuantileTransformer

    with np.load(state_path, allow_pickle=False) as state:
        quantiles = np.asarray(state["quantiles"], dtype=np.float64)
        references = np.asarray(state["references"], dtype=np.float64)
    transformer = QuantileTransformer(
        n_quantiles=quantiles.shape[0],
        output_distribution="normal",
        subsample=1_000_000_000,
        random_state=42,
        copy=True,
    )
    transformer.quantiles_ = quantiles
    transformer.references_ = references
    transformer.n_quantiles_ = quantiles.shape[0]
    transformer.n_features_in_ = quantiles.shape[1]
    return transformer


def _transform_a(raw_batch: np.ndarray, state_path: Path, clip: tuple[float, float]) -> np.ndarray:
    with np.load(state_path, allow_pickle=False) as state:
        mean = np.asarray(state["mean"], dtype=np.float64)
        scale = np.asarray(state["scale"], dtype=np.float64)
    values = np.asarray(raw_batch, dtype=np.float64)
    missing = ~np.isfinite(values)
    if np.any(missing):
        values[missing] = np.take(mean, np.nonzero(missing)[1])
    values = (values - mean) / scale
    np.clip(values, clip[0], clip[1], out=values)
    return values.astype("<f4")


def _transform_b(
    raw_batch: np.ndarray,
    a_batch: np.ndarray,
    state_path: Path,
    transformer: Any,
) -> np.ndarray:
    with np.load(state_path, allow_pickle=False) as state:
        mean = np.asarray(state["mean"], dtype=np.float64)
    selected = np.asarray(raw_batch[:, QUANTILE_INDICES], dtype=np.float64)
    missing = ~np.isfinite(selected)
    if np.any(missing):
        selected[missing] = np.take(mean, np.nonzero(missing)[1])
    transformed = np.asarray(transformer.transform(selected), dtype="<f4")
    if not np.all(np.isfinite(transformed)):
        raise ProtocolARaw83Error("候选 B 视图变换产生非有限值")
    result = np.empty_like(a_batch)
    result[:, QUANTILE_INDICES] = transformed
    result[:, SPECIAL_INDICES] = a_batch[:, SPECIAL_INDICES]
    if not np.array_equal(result[:, SPECIAL_INDICES], a_batch[:, SPECIAL_INDICES]):
        raise ProtocolARaw83Error("候选 B 七特殊列未逐位复制候选 A")
    return result


def _view_batch_receipt_path(output_root: Path, arm: str, batch_index: int) -> Path:
    return output_root / "receipts" / f"p5-view-{arm.lower()}-batches" / f"batch-{batch_index:06d}.json"


def materialize_source_views(
    config: Mapping[str, Any],
    *,
    batch_rows: int,
) -> dict[str, Any]:
    validate_config(config)
    run_root = Path(config["paths"]["output_root"])
    output_root = source_data_root(config)
    run_id = str(config["run_id"])
    raw = np.load(output_root / "raw" / "lspr23-raw83.npy", mmap_mode="r", allow_pickle=False)
    a_state_path = output_root / "states" / "candidate-a-standard.npz"
    b_state_path = output_root / "states" / "candidate-b-official-quantile.npz"
    a_final = output_root / "views" / "lspr23-candidate-a-standard.npy"
    b_final = output_root / "views" / "lspr23-candidate-b-quantile.npy"
    a_partial = a_final.with_name(f"{a_final.name}.partial.{run_id}")
    b_partial = b_final.with_name(f"{b_final.name}.partial.{run_id}")
    final_paths = (a_final, b_final)
    partial_paths = (a_partial, b_partial)
    receipt_roots = (
        run_root / "receipts" / "p5-view-a-batches",
        run_root / "receipts" / "p5-view-b-batches",
    )

    def candidate_matches(path: Path, receipt_root: Path) -> bool:
        receipt_paths = sorted(receipt_root.glob("batch-*.json"))
        if not path.exists() or not receipt_paths:
            return False
        candidate = np.load(path, mmap_mode="r", allow_pickle=False)
        for receipt_path in receipt_paths:
            receipt = load_json(receipt_path)
            start = int(receipt["start_row"])
            stop = int(receipt["end_row"])
            observed = hashlib.sha256(
                np.asarray(candidate[start:stop], dtype="<f4").tobytes(order="C")
            ).hexdigest()
            if observed != receipt.get("content_sha256"):
                return False
        return True

    selected_paths: list[Path] = []
    rebuild_components: list[bool] = []
    stale_partials: list[Path] = []
    for final, partial, receipt_root in zip(final_paths, partial_paths, receipt_roots):
        receipts_present = any(receipt_root.glob("batch-*.json"))
        if receipts_present and candidate_matches(partial, receipt_root):
            selected_paths.append(partial)
            rebuild_components.append(False)
        elif receipts_present and candidate_matches(final, receipt_root):
            selected_paths.append(final)
            rebuild_components.append(False)
            if partial.exists():
                stale_partials.append(partial)
        elif receipts_present:
            selected_paths.append(partial)
            rebuild_components.append(True)
        else:
            selected_paths.append(partial if partial.exists() else final if final.exists() else partial)
            rebuild_components.append(False)
    work_a, work_b = selected_paths
    view_a = _open_partial_npy(work_a, dtype="<f4", shape=raw.shape)
    view_b = _open_partial_npy(work_b, dtype="<f4", shape=raw.shape)
    clip = tuple(float(value) for value in config["preprocessing"]["candidate_a"]["clip"])
    transformer = _restore_quantile_transformer(b_state_path)
    digest_a = hashlib.sha256()
    digest_b = hashlib.sha256()
    batch_index = 0
    for start in range(0, SOURCE_ROW_COUNT, batch_rows):
        stop = min(start + batch_rows, SOURCE_ROW_COUNT)
        raw_batch = np.asarray(raw[start:stop])
        batch_a = _transform_a(raw_batch, a_state_path, clip)
        batch_b = _transform_b(raw_batch, batch_a, b_state_path, transformer)
        for arm, batch, destination in (("A", batch_a, view_a), ("B", batch_b, view_b)):
            content_sha = hashlib.sha256(batch.tobytes(order="C")).hexdigest()
            receipt_path = _view_batch_receipt_path(run_root, arm, batch_index)
            if receipt_path.exists():
                receipt = load_json(receipt_path)
                arm_index = 0 if arm == "A" else 1
                if rebuild_components[arm_index]:
                    destination[start:stop] = batch
                    destination.flush()
                written_sha = hashlib.sha256(
                    np.asarray(destination[start:stop], dtype="<f4").tobytes(order="C")
                ).hexdigest()
                if (
                    receipt.get("start_row") != start
                    or receipt.get("end_row") != stop
                    or receipt.get("content_sha256") != content_sha
                    or receipt.get("written_slice_sha256") != written_sha
                ):
                    raise ProtocolARaw83Error(f"视图断点收据不匹配：{receipt_path}")
            else:
                destination[start:stop] = batch
                destination.flush()
                atomic_write_json(
                    receipt_path,
                    {
                        "schema_version": f"{SCHEMA_VERSION}-p5-view-batch-receipt-v1",
                        "arm": arm,
                        "batch_index": batch_index,
                        "start_row": start,
                        "end_row": stop,
                        "content_sha256": content_sha,
                        "written_slice_sha256": content_sha,
                    },
                )
        digest_a.update(batch_a.tobytes(order="C"))
        digest_b.update(batch_b.tobytes(order="C"))
        batch_index += 1
    del view_a, view_b
    for work_path, partial, final in zip((work_a, work_b), partial_paths, final_paths):
        if work_path == partial:
            os.replace(partial, final)
    for stale_partial in stale_partials:
        if stale_partial.exists():
            stale_partial.unlink()
    a_receipt = load_json(run_root / "receipts" / "p3-candidate-a-state.json")
    b_receipt = load_json(run_root / "receipts" / "p4-candidate-b-state.json")
    receipt = {
        "schema_version": f"{SCHEMA_VERSION}-p5-source-views-v1",
        "source_row_count": SOURCE_ROW_COUNT,
        "field_count": len(DIJK_FEATURES),
        "transform_state_hashes": {
            "A": a_receipt["transform_state_hash"],
            "B": b_receipt["transform_state_hash"],
        },
        "view_content_sha256": {"A": digest_a.hexdigest(), "B": digest_b.hexdigest()},
        "target_feature_rows_read": 0,
        "target_label_rows_read": 0,
        "artifacts": {
            "source_view_a": _artifact(a_final),
            "source_view_b": _artifact(b_final),
            "candidate_a_state": _artifact(a_state_path),
            "candidate_b_state": _artifact(b_state_path),
        },
    }
    receipt["receipt_content_sha256"] = canonical_sha256(receipt)
    atomic_write_json(run_root / "receipts" / "p5-source-views.json", receipt)
    for path in (a_final, b_final):
        path.chmod(0o440)
    return receipt
