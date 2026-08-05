"""共享 B0 DistilBERT 冻结输入、指标、恢复和跟踪合同测试。"""

from __future__ import annotations

import builtins
import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from flow_probe.shared_b0_distilbert_baseline import (
    CHECKPOINT_SCHEMA_VERSION,
    CONFIG_SCHEMA_VERSION,
    EXPECTED_PROTOCOL_STATUS,
    EXPECTED_STAGE,
    EXTERNAL_EVALUATION_SPLIT,
    FIXED_LABEL_MAPPING,
    FIXED_MODEL_ID,
    INPUT_COLUMNS,
    MODEL_FINGERPRINT,
    REQUIRED_SPLITS,
    SELECTION_SPLIT,
    SMOKE_SAMPLE_COUNT,
    RunStateController,
    ScalarLogger,
    SharedB0DistilBertError,
    _swanlab_attempt,
    build_development_scalars,
    build_training_step_scalars,
    compute_binary_metrics,
    config_snapshot,
    forward_probability_batch,
    load_config,
    prepare_frozen_inputs,
    prepare_run,
    prepare_smoke_inputs,
    prepare_smoke_run,
    resolve_latest_legal_checkpoint,
    validate_model_source,
)
from flow_probe.shared_b0_view import ARTIFACT_SCHEMA_VERSION


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _split_frame(sample_ids: list[str], labels: list[int]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "sample_id": sample_id,
                "stable_order": stable_order,
                "text": f"包数={stable_order + 1}；总字节={(stable_order + 1) * 64}",
                "label": label,
            }
            for stable_order, (sample_id, label) in enumerate(zip(sample_ids, labels, strict=True))
        ],
        columns=list(INPUT_COLUMNS),
    )


def _write_frozen_dataset(
    root: Path,
    *,
    train_count: int = 4,
    genis_count: int = 2,
    tqhc2_count: int = 2,
) -> None:
    rows = {
        "train": (
            [f"train-{index}" for index in range(train_count)],
            [index % 2 for index in range(train_count)],
        ),
        "genis": (
            [f"genis-{index}" for index in range(genis_count)],
            [index % 2 for index in range(genis_count)],
        ),
        "tqhc2": (
            [f"tqhc2-{index}" for index in range(tqhc2_count)],
            [(index + 1) % 2 for index in range(tqhc2_count)],
        ),
    }
    for name, relative in REQUIRED_SPLITS.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        sample_ids, labels = rows[name]
        _split_frame(sample_ids, labels).to_parquet(path, index=False, compression="zstd")
    _write_json(
        root / "manifests/input_binding.json",
        {"schema_version": ARTIFACT_SCHEMA_VERSION, "fixture": True},
    )
    _write_json(
        root / "manifests/statistics.json",
        {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "stage": EXPECTED_STAGE,
            "status": EXPECTED_PROTOCOL_STATUS,
            "candidate_count": train_count,
            "validation": {
                "genis": {"count": genis_count},
                "tqhc2": {"count": tqhc2_count},
            },
        },
    )
    _refresh_publication(root)


def _refresh_publication(root: Path) -> None:
    relative_paths = {
        *REQUIRED_SPLITS.values(),
        "manifests/input_binding.json",
        "manifests/statistics.json",
    }
    artifacts = {
        relative: {
            "sha256": _sha256(root / relative),
            "size_bytes": (root / relative).stat().st_size,
        }
        for relative in sorted(relative_paths)
    }
    checksums_path = root / "manifests/checksums.json"
    counts = {
        name: len(pd.read_parquet(root / relative, columns=["sample_id"]))
        for name, relative in REQUIRED_SPLITS.items()
    }
    _write_json(
        checksums_path,
        {"schema_version": ARTIFACT_SCHEMA_VERSION, "artifacts": artifacts},
    )
    _write_json(
        root / "manifests/freeze_manifest.json",
        {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "stage": EXPECTED_STAGE,
            "status": EXPECTED_PROTOCOL_STATUS,
            "candidate_count": counts["train"],
            "validation_counts": {"genis": counts["genis"], "tqhc2": counts["tqhc2"]},
            "atomic_publication": True,
            "input_binding_sha256": artifacts["manifests/input_binding.json"]["sha256"],
            "checksums_sha256": _sha256(checksums_path),
        },
    )


def _write_model_mirror(root: Path) -> None:
    _write_json(root / "config.json", dict(MODEL_FINGERPRINT))
    (root / "vocab.txt").write_text("[PAD]\n[UNK]\n", encoding="utf-8")
    (root / "tokenizer_config.json").write_text("{}\n", encoding="utf-8")
    (root / "model.safetensors").write_bytes(b"fixture-model-weights")


def _real_config_path() -> Path:
    return Path(__file__).resolve().parents[1] / "configs/shared_b0_distilbert_seed42_v1.yaml"


def _fixture_config(tmp_path: Path, dataset_dir: Path, model_dir: Path):
    base = load_config(_real_config_path())
    return replace(
        base,
        dataset=replace(base.dataset, root=dataset_dir.resolve()),
        model=replace(base.model, source=str(model_dir.resolve())),
        run=replace(base.run, output_dir=(tmp_path / "run").resolve()),
    )


def _write_checkpoint(
    output_dir: Path,
    *,
    step: int,
    binding_sha256: str,
    next_epoch: int,
    next_batch_index: int,
) -> Path:
    checkpoint = output_dir / f"checkpoint-{step}"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text("{}\n", encoding="utf-8")
    (checkpoint / "model.safetensors").write_bytes(b"checkpoint-model")
    (checkpoint / "training_state.pt").write_bytes(b"checkpoint-state")
    artifact_names = ("config.json", "model.safetensors", "training_state.pt")
    artifacts = {
        name: {
            "sha256": _sha256(checkpoint / name),
            "size_bytes": (checkpoint / name).stat().st_size,
        }
        for name in artifact_names
    }
    _write_json(
        checkpoint / "checkpoint_manifest.json",
        {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "binding_sha256": binding_sha256,
            "global_step": step,
            "next_epoch": next_epoch,
            "next_batch_index": next_batch_index,
            "best_model": None,
            "best_epoch": None,
            "best_macro_f1": None,
            "artifacts": artifacts,
        },
    )
    return checkpoint


def test_real_config_parses_without_importing_model_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.split(".", maxsplit=1)[0] in {"torch", "transformers", "swanlab"}:
            raise AssertionError(f"配置解析提前导入了模型运行时：{name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    config = load_config(_real_config_path())
    snapshot = config_snapshot(config)

    assert snapshot["schema_version"] == CONFIG_SCHEMA_VERSION
    assert config.model.identifier == FIXED_MODEL_ID
    assert config.run.seed == 42
    assert snapshot["evaluation"]["selection_split"] == SELECTION_SPLIT
    assert snapshot["evaluation"]["external_evaluation_split"] == EXTERNAL_EVALUATION_SPLIT
    assert snapshot["evaluation"]["threshold"] == 0.5


def test_prepare_frozen_inputs_binds_exact_three_files_and_label_mapping(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    _write_frozen_dataset(dataset_dir)

    prepared = prepare_frozen_inputs(dataset_dir)

    assert tuple(prepared.splits) == ("train", "genis", "tqhc2")
    assert prepared.splits["train"].sample_ids == (
        "train-0",
        "train-1",
        "train-2",
        "train-3",
    )
    assert prepared.splits["train"].stable_orders == (0, 1, 2, 3)
    assert prepared.splits["train"].labels == (0, 1, 0, 1)
    assert prepared.binding["label_mapping"] == {"0": "benign", "1": "malicious"}
    assert set(prepared.binding["splits"]) == set(REQUIRED_SPLITS)
    assert len(prepared.binding_sha256) == 64
    assert FIXED_LABEL_MAPPING[0] == "benign"
    assert FIXED_LABEL_MAPPING[1] == "malicious"


def test_smoke16_skips_tqhc2_uses_fixed_rows_and_isolates_output(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    model_dir = tmp_path / "model"
    _write_frozen_dataset(
        dataset_dir,
        train_count=SMOKE_SAMPLE_COUNT + 4,
        genis_count=SMOKE_SAMPLE_COUNT + 4,
    )
    _write_model_mirror(model_dir)
    tqhc2_path = dataset_dir / REQUIRED_SPLITS[EXTERNAL_EVALUATION_SPLIT]
    tqhc2_path.unlink()

    config = _fixture_config(tmp_path, dataset_dir, model_dir)
    inputs = prepare_smoke_inputs(dataset_dir)
    smoke_output = tmp_path / "smoke" / "distilbert-smoke16"
    prepared = prepare_smoke_run(
        config,
        inputs,
        validate_model_source(config.model),
        smoke_output,
    )

    assert tuple(inputs.splits) == ("train", SELECTION_SPLIT)
    assert all(len(split) == SMOKE_SAMPLE_COUNT for split in inputs.splits.values())
    assert inputs.splits["train"].sample_ids == tuple(
        f"train-{index}" for index in range(SMOKE_SAMPLE_COUNT)
    )
    assert inputs.splits[SELECTION_SPLIT].stable_orders == tuple(range(SMOKE_SAMPLE_COUNT))
    assert inputs.binding["tqhc2_access"] == "forbidden"
    assert EXTERNAL_EVALUATION_SPLIT not in inputs.binding["splits"]
    assert prepared.config.run.output_dir == smoke_output.resolve()
    assert prepared.config.run.output_dir != config.run.output_dir
    assert prepared.config.training.num_train_epochs == 1
    assert prepared.config.training.per_device_train_batch_size == SMOKE_SAMPLE_COUNT
    assert prepared.config.training.gradient_accumulation_steps == 1
    assert prepared.config.training.resume_from_checkpoint == "never"
    assert config.training.num_train_epochs == 3
    assert config.run.output_dir == (tmp_path / "run").resolve()


def test_prepare_frozen_inputs_rejects_hash_mismatch(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    _write_frozen_dataset(dataset_dir)
    path = dataset_dir / REQUIRED_SPLITS["train"]
    frame = pd.read_parquet(path)
    frame.loc[0, "label"] = 1
    frame.to_parquet(path, index=False, compression="zstd")

    with pytest.raises(SharedB0DistilBertError, match="哈希不一致|大小不一致"):
        prepare_frozen_inputs(dataset_dir)


def test_prepare_frozen_inputs_rejects_overlap_after_hash_refresh(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    _write_frozen_dataset(dataset_dir)
    path = dataset_dir / REQUIRED_SPLITS["genis"]
    frame = pd.read_parquet(path)
    frame.loc[0, "sample_id"] = "train-0"
    frame.to_parquet(path, index=False, compression="zstd")
    _refresh_publication(dataset_dir)

    with pytest.raises(SharedB0DistilBertError, match="sample_id 重叠"):
        prepare_frozen_inputs(dataset_dir)


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [("stable_order", 8, "stable_order"), ("label", 2, "label")],
)
def test_prepare_frozen_inputs_rejects_order_or_label_violation(
    tmp_path: Path,
    column: str,
    value: int,
    message: str,
) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    _write_frozen_dataset(dataset_dir)
    path = dataset_dir / REQUIRED_SPLITS["tqhc2"]
    frame = pd.read_parquet(path)
    frame.loc[1, column] = value
    frame.to_parquet(path, index=False, compression="zstd")
    _refresh_publication(dataset_dir)

    with pytest.raises(SharedB0DistilBertError, match=message):
        prepare_frozen_inputs(dataset_dir)


def test_binary_metrics_include_detection_calibration_and_brier_values() -> None:
    metrics = compute_binary_metrics(
        [0, 0, 1, 1],
        [0.1, 0.6, 0.8, 0.4],
        calibration_bins=10,
    )

    assert metrics["accuracy"] == pytest.approx(0.5)
    assert metrics["macro_f1"] == pytest.approx(0.5)
    assert metrics["benign_f1"] == pytest.approx(0.5)
    assert metrics["malicious_f1"] == pytest.approx(0.5)
    assert metrics["malicious_recall"] == pytest.approx(0.5)
    assert metrics["benign_false_positive_rate"] == pytest.approx(0.5)
    assert metrics["balanced_accuracy"] == pytest.approx(0.5)
    assert metrics["expected_calibration_error"] == pytest.approx(0.375)
    assert metrics["brier_score"] == pytest.approx(0.1925)


def test_cpu_stub_forward_preserves_batch_order_and_probability_range() -> None:
    torch = pytest.importorskip("torch")

    class StubTokenizer:
        def __call__(self, texts, **kwargs):
            del kwargs
            lengths = torch.tensor([[len(text)] for text in texts], dtype=torch.long)
            return {"input_ids": lengths, "attention_mask": torch.ones_like(lengths)}

    class StubModel(torch.nn.Module):
        def forward(self, input_ids, attention_mask):
            del attention_mask
            score = input_ids[:, 0].float() / 10.0
            return SimpleNamespace(logits=torch.stack((-score, score), dim=1))

    probabilities = forward_probability_batch(
        model=StubModel(),
        tokenizer=StubTokenizer(),
        texts=("一", "四个字符"),
        device="cpu",
        max_length=16,
        torch_module=torch,
    )

    assert len(probabilities) == 2
    assert probabilities[0] < probabilities[1]
    assert all(0.0 <= value <= 1.0 and math.isfinite(value) for value in probabilities)


def test_resume_selects_latest_legal_checkpoint_and_restores_prepared_state(
    tmp_path: Path,
) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    model_dir = tmp_path / "model"
    _write_frozen_dataset(dataset_dir)
    _write_model_mirror(model_dir)
    config = _fixture_config(tmp_path, dataset_dir, model_dir)
    inputs = prepare_frozen_inputs(dataset_dir)
    model_binding = validate_model_source(config.model)
    first = prepare_run(config, inputs, model_binding)
    checkpoint = _write_checkpoint(
        config.run.output_dir,
        step=3,
        binding_sha256=first.binding_sha256,
        next_epoch=1,
        next_batch_index=0,
    )
    invalid_latest = config.run.output_dir / "checkpoint-5"
    invalid_latest.mkdir()
    controller = RunStateController(first.state_path)
    controller.transition(
        "running",
        current_step=3,
        current_epoch=1,
        latest_checkpoint=str(checkpoint),
    )
    controller.mark_interrupted(KeyboardInterrupt())

    assert (
        resolve_latest_legal_checkpoint(config.run.output_dir, first.binding_sha256) == checkpoint
    )
    resumed = prepare_run(config, inputs, model_binding)
    resumed_state = json.loads(resumed.state_path.read_text(encoding="utf-8"))

    assert resumed.resume_checkpoint == checkpoint
    assert resumed_state["status"] == "prepared"
    assert resumed_state["current_step"] == 3
    assert resumed_state["current_epoch"] == 1


def test_swanlab_scalar_events_are_flat_and_finish_explicitly(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    model_dir = tmp_path / "model"
    _write_frozen_dataset(dataset_dir)
    _write_model_mirror(model_dir)
    config = _fixture_config(tmp_path, dataset_dir, model_dir)
    prepared = prepare_run(
        config,
        prepare_frozen_inputs(dataset_dir),
        validate_model_source(config.model),
    )
    controller = RunStateController(prepared.state_path)

    class FakeSwanLab:
        def __init__(self) -> None:
            self.init_kwargs = None
            self.logged = []
            self.finished = []

        def init(self, **kwargs):
            self.init_kwargs = kwargs
            return SimpleNamespace(id="fake-run-id")

        def log(self, metrics, step):
            self.logged.append((metrics, step))

        def finish(self, **kwargs):
            self.finished.append(kwargs)

    fake = FakeSwanLab()
    step_metrics = build_training_step_scalars(
        loss=0.25,
        learning_rate=0.00002,
        epoch=1,
        optimizer_step=1,
    )
    dev_metrics = build_development_scalars(
        compute_binary_metrics([0, 1], [0.1, 0.9]),
        epoch=1,
    )
    with _swanlab_attempt(prepared, controller, config_snapshot(config), fake) as logger:
        assert isinstance(logger, ScalarLogger)
        logger.log(step_metrics, step=1, event="optimizer_step")
        logger.log(dev_metrics, step=1, event="development_evaluation")

    assert fake.init_kwargs["project"] == "malicious-traffic-llm"
    assert fake.init_kwargs["workspace"] == "mortiswang"
    assert all(len(tag) <= 20 for tag in fake.init_kwargs["tags"])
    assert len(fake.logged) == 2
    assert all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for metrics, _ in fake.logged
        for value in metrics.values()
    )
    assert fake.finished == [{}]
    attempts = controller.state["swanlab_attempts"]
    assert attempts[-1]["status"] == "finished"
