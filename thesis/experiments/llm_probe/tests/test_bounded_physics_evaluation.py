import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
import yaml

from flow_probe.bounded_physics_conditioning import (
    ConditioningDiagnostics,
    PhysicsConditionedGeneration,
    PhysicsConditionedOutput,
)
from flow_probe.bounded_physics_evaluation import (
    CANDIDATE_CONDITION_TOLERANCE,
    FIXED_PHYSICS_TEST_FILE,
    FIXED_SPLITS,
    PHYSICS_TEST_SAMPLES,
    BoundedPhysicsEvaluationError,
    PublicInferenceRequest,
    assert_bypass_matches_s3,
    build_analysis_training_summary,
    candidate_condition_repeat_max_diff,
    expected_prediction_files,
    load_fixed_evaluation_configuration,
    run_public_candidate_scoring,
    run_public_free_generation,
)
from flow_probe.hierarchical_evaluation import EvaluationSettings, EvaluationSplit


class _FakeTokenizer:
    pad_token_id = 63
    eos_token_id = 0

    def apply_chat_template(self, messages, **_: object) -> str:
        return "格式化：" + messages[0]["content"]

    def __call__(self, prompts, **_: object) -> dict[str, torch.Tensor]:
        rows = [[10, 11 + index] for index, _prompt in enumerate(prompts)]
        return {
            "input_ids": torch.tensor(rows, dtype=torch.long),
            "attention_mask": torch.ones((len(rows), 2), dtype=torch.long),
        }

    def encode(self, text: str, **_: object) -> list[int]:
        if text.startswith("格式化："):
            return [10, 11]
        label = json.loads(text)["label"]
        return [{"benign": 20, "dos": 21}[label]]

    def decode(self, token_ids, **_: object) -> str:
        assert list(token_ids) == [50]
        return '{"label":"benign"}'


class _FakeBaseModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.zeros(()), requires_grad=False)
        self.config = SimpleNamespace(use_cache=True)


class _FakeRuntime(torch.nn.Module):
    def __init__(self, *, leak_candidate_condition: bool = False) -> None:
        super().__init__()
        object.__setattr__(self, "model", _FakeBaseModel())
        self.leak_candidate_condition = leak_candidate_condition
        self.calls: list[dict[str, object]] = []

    @staticmethod
    def _diagnostics(*, bypass: bool, generation: bool = False) -> ConditioningDiagnostics:
        count = 0 if bypass else 1
        return ConditioningDiagnostics(
            gate_values=(0.01, 0.01, 0.01, 0.01),
            attention_entropies=(1.0, 1.0, 1.0, 1.0),
            max_residual_ratio=0.01,
            source_hook_count=count,
            target_hook_counts=(count, count, count, count),
            prefill_count=count if generation else 0,
            cached_decode_count=0,
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor | None = None,
        completion_start: torch.Tensor | None = None,
        bypass: bool = False,
        **kwargs: object,
    ) -> PhysicsConditionedOutput:
        assert "task_label" not in kwargs
        assert "state_targets" not in kwargs
        mode = "training" if labels is not None else "candidate"
        self.calls.append(
            {
                "mode": mode,
                "bypass": bypass,
                "completion_start": completion_start,
            }
        )
        batch, length = input_ids.shape
        logits = torch.zeros((batch, length, 64), dtype=torch.float32)
        if bypass:
            state = None
            condition = None
        else:
            values = (
                torch.arange(batch, dtype=torch.float32)
                if self.leak_candidate_condition and completion_start is not None
                else torch.zeros(batch, dtype=torch.float32)
            )
            state = values[:, None].expand(-1, 5).clone()
            condition = values[:, None, None].expand(-1, 9, 256).clone()
        return PhysicsConditionedOutput(
            model_output=SimpleNamespace(logits=logits, loss=logits.sum()),
            predicted_state=state,
            condition_tokens=condition,
            diagnostics=self._diagnostics(bypass=bypass),
        )

    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        bypass: bool = False,
        **kwargs: object,
    ) -> PhysicsConditionedGeneration:
        assert kwargs["num_beams"] == 1
        assert kwargs["use_cache"] is True
        assert "task_label" not in kwargs
        self.calls.append({"mode": "generation", "bypass": bypass})
        generated = torch.full(
            (input_ids.shape[0], 1),
            50,
            dtype=torch.long,
            device=input_ids.device,
        )
        return PhysicsConditionedGeneration(
            model_output=torch.cat((input_ids, generated), dim=1),
            diagnostics=self._diagnostics(bypass=bypass, generation=True),
        )


def _settings() -> EvaluationSettings:
    return EvaluationSettings.from_mapping(
        {
            "sample_dir": "samples",
            "output_dir": "output",
            "samples_per_label": 1,
            "generation_batch_size": 2,
            "scoring_batch_size": 4,
            "progress_every_batches": 1,
            "max_known_rejection_rate": 0.05,
            "seed": 42,
        }
    )


def _split() -> EvaluationSplit:
    return EvaluationSplit(
        name="family_test",
        path=Path("unused.jsonl"),
        candidate_labels=("benign", "dos"),
        free_generation_labels=("benign", "dos"),
    )


def _records() -> list[dict[str, object]]:
    return [
        {"sample_id": "sample-1", "prompt": "提示一", "task_label": "benign"},
        {"sample_id": "sample-2", "prompt": "提示二", "task_label": "dos"},
    ]


def _requests() -> list[PublicInferenceRequest]:
    return [
        PublicInferenceRequest(sample_id="sample-1", prompt="提示一"),
        PublicInferenceRequest(sample_id="sample-2", prompt="提示二"),
    ]


def test_fixed_configuration_keeps_six_splits_eval300_and_seed44_physics_test() -> None:
    raw = yaml.safe_load(
        Path("configs/bounded_physics_conditioning_seed42_eval300.yaml").read_text(encoding="utf-8")
    )

    probe, settings, _tracking, variant, _adapter, _s3, physics_test = (
        load_fixed_evaluation_configuration(raw, "e2")
    )

    assert probe.seed == 42
    assert settings.samples_per_label == 300
    assert variant.training_variant == "combined"
    assert physics_test == FIXED_PHYSICS_TEST_FILE
    assert raw["bounded_evaluation"]["physics_test_samples"] == PHYSICS_TEST_SAMPLES
    assert FIXED_SPLITS == (
        "family_test",
        "subtype_validation",
        "subtype_test",
        "ood_dos_icmp",
        "ood_dos_pushack",
        "ood_dos_udp",
    )


@pytest.mark.parametrize(
    "forbidden",
    [
        {"task_label": "dos"},
        {"state_targets": [0, 0, 0, 0, 0]},
        {"ns3_scenario_id": 7},
        {"is_unknown": True},
    ],
)
def test_public_inference_rejects_truth_fields(forbidden: dict[str, object]) -> None:
    with pytest.raises(BoundedPhysicsEvaluationError, match="拒绝真值字段"):
        PublicInferenceRequest.from_mapping({"sample_id": "sample", "prompt": "提示", **forbidden})


def test_training_generation_and_candidate_paths_all_use_runtime() -> None:
    runtime = _FakeRuntime()
    tokenizer = _FakeTokenizer()
    requests = _requests()
    training_ids = torch.tensor([[1, 2, 3]], dtype=torch.long)
    runtime(
        input_ids=training_ids,
        attention_mask=torch.ones_like(training_ids),
        labels=torch.tensor([[-100, -100, 3]], dtype=torch.long),
    )

    free = run_public_free_generation(
        runtime,
        tokenizer,
        requests,
        _split(),
        _settings(),
        None,
        bypass=False,
        max_new_tokens=16,
    )
    candidate = run_public_candidate_scoring(
        runtime,
        tokenizer,
        requests,
        _split(),
        _settings(),
        None,
        threshold=None,
        bypass=False,
    )

    assert [call["mode"] for call in runtime.calls] == [
        "training",
        "generation",
        "candidate",
    ]
    assert runtime.calls[-1]["completion_start"] is not None
    assert free.diagnostics[0].prefill_count == 1
    assert candidate.diagnostics[0].target_hook_counts == (1, 1, 1, 1)
    assert candidate.candidate_condition_repeat_max_diff <= CANDIDATE_CONDITION_TOLERANCE
    assert all("true_label" not in row for row in (*free.rows, *candidate.rows))


def test_candidate_scoring_rejects_completion_dependent_condition() -> None:
    with pytest.raises(BoundedPhysicsEvaluationError, match="候选条件差"):
        run_public_candidate_scoring(
            _FakeRuntime(leak_candidate_condition=True),
            _FakeTokenizer(),
            _requests(),
            _split(),
            _settings(),
            None,
            threshold=None,
            bypass=False,
        )


def test_candidate_condition_difference_checks_state_and_nine_tokens() -> None:
    state = torch.zeros((4, 5))
    condition = torch.zeros((4, 9, 256))
    condition[1, 3, 10] = 2e-6

    maximum, per_prompt = candidate_condition_repeat_max_diff(state, condition, 2)

    assert maximum == pytest.approx(2e-6)
    assert per_prompt == pytest.approx([2e-6, 0.0])


def test_bypass_prediction_comparison_is_per_sample_and_ignores_latency(tmp_path: Path) -> None:
    reference = [
        {
            "sample_id": "sample-1",
            "true_label": "benign",
            "generated_text": '{"label":"benign"}',
            "parsed_label": "benign",
            "is_valid": True,
            "parse_error": None,
            "input_tokens": 2,
            "generated_tokens": 1,
            "amortized_latency_ms": 99.0,
        }
    ]
    reference_path = tmp_path / "family_test_free.jsonl"
    reference_path.write_text(json.dumps(reference[0]) + "\n", encoding="utf-8")
    bypass = [{**reference[0], "amortized_latency_ms": 1.0}]

    audit = assert_bypass_matches_s3(reference_path, bypass, mode="free")

    assert audit["equivalent"] is True
    assert audit["rows"] == 1
    assert audit["max_abs_numeric_diff"] == 0.0


def test_prediction_layout_and_efficiency_fields_are_complete() -> None:
    files = expected_prediction_files(Path("predictions"))
    assert len(files) == 12
    assert len({path.name for path in files}) == 12

    runtime = _FakeRuntime()
    free = run_public_free_generation(
        runtime,
        _FakeTokenizer(),
        _requests(),
        _split(),
        _settings(),
        None,
        bypass=False,
        max_new_tokens=16,
    )
    candidate = run_public_candidate_scoring(
        runtime,
        _FakeTokenizer(),
        _requests(),
        _split(),
        _settings(),
        None,
        threshold=None,
        bypass=False,
    )
    required_latency = {"amortized_latency_p50_ms", "amortized_latency_p95_ms"}
    assert required_latency.issubset(free.summary["efficiency"])
    assert required_latency.issubset(candidate.summary["efficiency"])
    assert {"input_tokens", "generated_tokens"}.issubset(free.summary["efficiency"])
    assert {"candidate_tokens", "candidate_sequences"}.issubset(candidate.summary["efficiency"])
    assert "peak_gpu_memory_mib" in free.summary["efficiency"]
    assert "peak_gpu_memory_mib" in candidate.summary["efficiency"]


def test_analysis_uses_physics_test_metrics_instead_of_training_validation() -> None:
    training_summary = {
        "validation": {
            "unobserved_reference_mse": 99.0,
            "queue_residual_reference_mse": 88.0,
        }
    }
    physics_test_summary = {
        "metrics": {
            "five_dimensional_reference_mse": 0.4,
            "observed_reference_mse": 0.3,
            "unobserved_reference_mse": 0.2,
            "queue_residual_reference_mse": 0.1,
        }
    }

    compatible = build_analysis_training_summary(training_summary, physics_test_summary)

    assert compatible["validation"]["state_mse_unobserved"] == 0.2
    assert compatible["validation"]["physics_residual_mse"] == 0.1
    assert (
        compatible["analysis_compatibility"]["mechanism_metric_source"]
        == "physics_test_summary.json"
    )
