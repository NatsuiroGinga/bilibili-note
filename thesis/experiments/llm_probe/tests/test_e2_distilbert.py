"""E2 DistilBERT 训练适配器的最小运行合同。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from flow_probe.e2_hard_domain_baselines import E2BaselineBudget, E2TextSample
from flow_probe.e2_hard_domain_data import E2_FEATURE_FIELDS


def _text(duration: float) -> str:
    return " ".join(
        f"{field}={duration + index}" for index, field in enumerate(E2_FEATURE_FIELDS)
    )


def _sample(sample_id: str, duration: float, label: int) -> E2TextSample:
    return E2TextSample(
        sample_id=sample_id,
        capture_id="source-capture",
        text=_text(duration),
        label=label,
    )


def test_classification_head_reset_accepts_same_seed_identical_digest() -> None:
    torch = pytest.importorskip("torch")
    from flow_probe.e2_distilbert import _reset_classification_head

    class TinyClassifier(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.pre_classifier = torch.nn.Linear(2, 2)
            self.classifier = torch.nn.Linear(2, 2)

        @staticmethod
        def _init_weights(module) -> None:
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            torch.nn.init.zeros_(module.bias)

    model = TinyClassifier()
    torch.manual_seed(42)
    model._init_weights(model.pre_classifier)
    model._init_weights(model.classifier)

    head_binding = _reset_classification_head(model, torch, seed=42)

    assert head_binding["mode"] == "explicit_seeded_pretrained_initialization"
    assert head_binding["seed"] == 42
    assert head_binding["reset_performed"] is True
    assert head_binding["parameter_digest_changed"] is False
    assert head_binding["loaded_head_sha256"] == head_binding["initialized_head_sha256"]


def test_training_adapter_runs_source_only_with_shared_b0_runtime(monkeypatch) -> None:
    torch = pytest.importorskip("torch")
    from flow_probe import e2_distilbert
    from flow_probe.e2_distilbert import (
        E2DistilBertTrainingAdapter,
        E2DistilBertTrainingSettings,
    )
    from flow_probe.shared_b0_distilbert_baseline import RuntimeSelection

    class TinyTokenizer:
        def __call__(self, texts, **kwargs):
            del kwargs
            values = [float(texts_item.split()[0].split("=", 1)[1]) for texts_item in texts]
            input_ids = torch.tensor([[value, 1.0] for value in values], dtype=torch.float32)
            return {
                "input_ids": input_ids,
                "attention_mask": torch.ones_like(input_ids),
            }

    class TinyClassifier(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.pre_classifier = torch.nn.Linear(1, 1)
            self.classifier = torch.nn.Linear(1, 2)

        def forward(self, input_ids, attention_mask=None):
            del attention_mask
            pooled = input_ids.mean(dim=1, keepdim=True)
            hidden = torch.relu(self.pre_classifier(pooled))
            return SimpleNamespace(logits=self.classifier(hidden))

    class TinyAutoTokenizer:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            del args, kwargs
            return TinyTokenizer()

    class TinyAutoModel:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            del args, kwargs
            model = TinyClassifier()
            with torch.no_grad():
                for parameter in model.parameters():
                    parameter.fill_(9.0)
            return model

    monkeypatch.setattr(
        e2_distilbert,
        "load_runtime_modules",
        lambda: SimpleNamespace(
            torch=torch,
            auto_tokenizer=TinyAutoTokenizer,
            auto_model=TinyAutoModel,
        ),
    )
    monkeypatch.setattr(
        e2_distilbert,
        "_resolve_training_runtime",
        lambda modules, settings: RuntimeSelection(
            device="cpu",
            precision="float32",
            torch_dtype=torch.float32,
            use_grad_scaler=False,
        ),
    )
    monkeypatch.setattr(
        e2_distilbert,
        "_validate_base_model_binding",
        lambda settings: {
            "schema_version": "flow_probe_e2_distilbert_base_binding_v1",
            "identifier": settings.model_identifier,
            "source": settings.model_source,
            "binding_sha256": "a" * 64,
            "artifact_count": 2,
            "total_size_bytes": 10,
            "weight_artifacts": {
                "model.safetensors": {"sha256": "b" * 64, "size_bytes": 10}
            },
        },
    )
    adapter = E2DistilBertTrainingAdapter(
        E2DistilBertTrainingSettings(
            model_source="in-memory-test-model",
            expected_model_binding_sha256="a" * 64,
            per_device_train_batch_size=2,
            per_device_eval_batch_size=1,
            gradient_accumulation_steps=1,
            num_train_epochs=1,
            num_workers=0,
        )
    )
    train = (
        _sample("train-0", 0.0, 0),
        _sample("train-1", 1.0, 0),
        _sample("train-2", 4.0, 1),
        _sample("train-3", 5.0, 1),
    )
    calibration = (
        _sample("calibration-0", 0.5, 0),
        _sample("calibration-1", 4.5, 1),
    )

    predictor = adapter.fit_source_only(
        train=train,
        calibration=calibration,
        budget=E2BaselineBudget(seed=42, max_iterations=1),
    )
    probabilities = predictor.predict_malicious_probabilities(
        [_text(0.25), _text(4.25)]
    )

    assert len(probabilities) == 2
    assert all(0.0 <= value <= 1.0 for value in probabilities)
    assert adapter.last_training_summary is not None
    assert adapter.last_training_summary["source_only_fit"] is True
    assert adapter.last_training_summary["final_test_visible"] is False
    assert adapter.last_training_summary["base_model_binding"]["binding_sha256"] == "a" * 64
    head_binding = adapter.last_training_summary["classification_head_initialization"]
    assert head_binding["mode"] == "explicit_seeded_reset"
    assert head_binding["seed"] == 42
    assert head_binding["loaded_head_sha256"] != head_binding["initialized_head_sha256"]


def test_base_model_binding_rejects_unregistered_or_finetuned_source(
    monkeypatch, tmp_path
) -> None:
    from flow_probe import e2_distilbert
    from flow_probe.e2_distilbert import (
        E2DistilBertTrainingError,
        E2DistilBertTrainingSettings,
    )

    settings = E2DistilBertTrainingSettings(
        model_source=str(tmp_path),
        expected_model_binding_sha256="a" * 64,
    )
    monkeypatch.setattr(
        e2_distilbert,
        "validate_model_source",
        lambda model: {
            "source_kind": "local_mirror",
            "local_files_verified": True,
            "binding_sha256": "b" * 64,
            "artifact_count": 2,
            "total_size_bytes": 10,
            "artifacts": {
                "model.safetensors": {"sha256": "c" * 64, "size_bytes": 10}
            },
        },
    )
    with pytest.raises(E2DistilBertTrainingError, match="预注册值不一致"):
        e2_distilbert._validate_base_model_binding(settings)

    (tmp_path / "config.json").write_text(
        '{"architectures": ["DistilBertForSequenceClassification"]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        e2_distilbert,
        "validate_model_source",
        lambda model: {
            "source_kind": "local_mirror",
            "local_files_verified": True,
            "binding_sha256": "a" * 64,
            "artifact_count": 2,
            "total_size_bytes": 10,
            "artifacts": {
                "model.safetensors": {"sha256": "c" * 64, "size_bytes": 10}
            },
        },
    )
    with pytest.raises(E2DistilBertTrainingError, match="拒绝旧分类检查点"):
        e2_distilbert._validate_base_model_binding(settings)
