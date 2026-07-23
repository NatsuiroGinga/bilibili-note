import json
import math
from dataclasses import asdict
from pathlib import Path

import pytest
import torch

from flow_probe.bounded_physics_conditioning import (
    ConditioningDiagnostics,
    ConditioningSpec,
)
from flow_probe.bounded_physics_train import (
    BOUNDED_TRAINING_PHASE,
    FORMAL_TRAINING_STEPS,
    MAX_GRAD_NORM,
    MIN_LEARNING_RATE,
    PEAK_LEARNING_RATE,
    PHYSICS_LOSS_WEIGHT,
    STATE_LOSS_WEIGHT,
    STRUCTURE_SCHEMA_VERSION,
    TRACKING_ARTIFACT_SCHEMA_VERSION,
    WARMUP_STEPS,
    BoundedRunLayout,
    ConditioningVariantContract,
    StructureParameterGroups,
    _adapter_parameter_digest,
    _directory_manifest,
    _mean_diagnostics,
    bounded_physics_learning_rate,
    compose_conditioning_loss,
    configure_structure_trainability,
    generation_gradient_snapshot,
    gradient_checkpointing_audit,
    load_bounded_structure_artifacts,
    physics_gradient_isolation,
    prepare_base_for_bounded_training,
    resolve_conditioning_variant,
    validate_bounded_artifacts,
    validate_generation_gradient_step,
)
from flow_probe.physics_train import PhysicsTrainingError


class _TinyInjector(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.alpha = torch.nn.Parameter(torch.zeros(()))
        self.projection = torch.nn.Linear(2, 2, bias=False)


class _TinyRuntime(torch.nn.Module):
    def __init__(self, *, include_unexpected: bool = False) -> None:
        super().__init__()
        self.state_head = torch.nn.Linear(2, 1)
        self.condition_encoder = torch.nn.Linear(1, 2)
        self.injectors = torch.nn.ModuleList(_TinyInjector() for _ in range(4))
        if include_unexpected:
            self.unexpected = torch.nn.Parameter(torch.ones(()))

    @staticmethod
    def unexpected_base_parameter_names() -> tuple[str, ...]:
        return ()


class _CheckpointLayer(torch.nn.Module):
    def __init__(self, enabled: bool = False) -> None:
        super().__init__()
        self.gradient_checkpointing = enabled


class _CheckpointModel(torch.nn.Module):
    def __init__(self, enabled: bool = False) -> None:
        super().__init__()
        self.weight = torch.nn.Parameter(torch.ones(()))
        self.layer = _CheckpointLayer(enabled)
        self.is_gradient_checkpointing = enabled
        self.disable_calls = 0

    def gradient_checkpointing_disable(self) -> None:
        self.disable_calls += 1
        self.is_gradient_checkpointing = False
        self.layer.gradient_checkpointing = False


class _ArtifactRuntime:
    def __init__(self) -> None:
        self.spec = ConditioningSpec()
        self.model = torch.nn.Module()
        self.model.block = torch.nn.Module()
        self.model.block.detection = torch.nn.Linear(1, 1, bias=False)
        self.loaded_state: dict[str, torch.Tensor] | None = None
        self.strict: bool | None = None

    def load_structure_state_dict(
        self,
        state: dict[str, torch.Tensor],
        strict: bool = True,
    ) -> None:
        if set(state) != {"state_head.weight"}:
            raise ValueError("结构状态键不匹配")
        self.loaded_state = dict(state)
        self.strict = strict


@pytest.mark.parametrize(
    ("name", "state_enabled", "physics_enabled", "semantics"),
    (
        ("structure_only", False, False, "condition_latent"),
        ("combined", True, True, "predicted_queue_state"),
    ),
)
def test_conditioning_variant_contract_is_fixed(
    name: str,
    state_enabled: bool,
    physics_enabled: bool,
    semantics: str,
) -> None:
    contract = resolve_conditioning_variant(name)

    assert contract.state_loss_enabled is state_enabled
    assert contract.physics_loss_enabled is physics_enabled
    assert contract.state_semantics == semantics
    assert contract.lambda_state == STATE_LOSS_WEIGHT
    assert contract.lambda_physics == PHYSICS_LOSS_WEIGHT


@pytest.mark.parametrize("name", ("e1", "e2", "STRUCTURE_ONLY", "temporary"))
def test_conditioning_variant_rejects_unregistered_names(name: str) -> None:
    with pytest.raises(PhysicsTrainingError, match="只允许 structure_only、combined"):
        resolve_conditioning_variant(name)


def test_conditioning_variant_cannot_override_loss_switches_or_weights() -> None:
    with pytest.raises(PhysicsTrainingError, match="不得改写"):
        ConditioningVariantContract(
            "structure_only",
            state_loss_enabled=True,
            physics_loss_enabled=False,
            state_semantics="condition_latent",
        )
    with pytest.raises(PhysicsTrainingError, match="固定为 1.0"):
        ConditioningVariantContract("combined", lambda_state=0.5)
    with pytest.raises(PhysicsTrainingError, match="固定为 0.01"):
        ConditioningVariantContract("combined", lambda_physics=0.1)


def test_structure_only_records_disabled_losses_as_numeric_zero() -> None:
    generation = torch.tensor(3.0, requires_grad=True)

    def forbidden() -> torch.Tensor:
        raise AssertionError("关闭的损失工厂不应执行")

    breakdown = compose_conditioning_loss(
        "structure_only",
        generation,
        forbidden,
        forbidden,
    )

    assert breakdown.total.item() == generation.item()
    assert breakdown.state.item() == 0.0
    assert breakdown.physics.item() == 0.0


def test_combined_loss_uses_fixed_e2_weights() -> None:
    breakdown = compose_conditioning_loss(
        "combined",
        torch.tensor(2.0),
        lambda: torch.tensor(3.0),
        lambda: torch.tensor(5.0),
    )

    assert breakdown.generation.item() == 2.0
    assert breakdown.state.item() == 3.0
    assert breakdown.physics.item() == 5.0
    assert breakdown.total.item() == pytest.approx(2.0 + 3.0 + 0.01 * 5.0)


def test_bounded_learning_rate_has_fixed_four_key_points() -> None:
    expected_step_21 = MIN_LEARNING_RATE + 0.5 * (PEAK_LEARNING_RATE - MIN_LEARNING_RATE) * (
        1.0 + math.cos(math.pi * (21 - WARMUP_STEPS) / (FORMAL_TRAINING_STEPS - WARMUP_STEPS))
    )

    assert bounded_physics_learning_rate(1) == pytest.approx(MIN_LEARNING_RATE)
    assert bounded_physics_learning_rate(WARMUP_STEPS) == pytest.approx(PEAK_LEARNING_RATE)
    assert bounded_physics_learning_rate(21) == pytest.approx(expected_step_21)
    assert bounded_physics_learning_rate(FORMAL_TRAINING_STEPS) == pytest.approx(MIN_LEARNING_RATE)


@pytest.mark.parametrize("step", (True, 0, 203, 1.5))
def test_bounded_learning_rate_rejects_steps_outside_fixed_trajectory(
    step: object,
) -> None:
    with pytest.raises(PhysicsTrainingError):
        bounded_physics_learning_rate(step)  # type: ignore[arg-type]


def test_parameter_allowlist_freezes_base_and_groups_only_structure() -> None:
    base = torch.nn.Linear(2, 2)
    runtime = _TinyRuntime()

    groups = configure_structure_trainability(base, runtime)  # type: ignore[arg-type]

    assert all(not parameter.requires_grad for parameter in base.parameters())
    assert all(parameter.requires_grad for parameter in groups.all)
    assert len(groups.gates) == 4
    assert len(groups.all) == len(tuple(runtime.parameters()))
    assert set(groups.names) == {name for name, _ in runtime.named_parameters()}
    assert all(
        name.startswith(("state_head.", "condition_encoder.", "injectors."))
        for name in groups.names
    )


def test_parameter_allowlist_rejects_an_unregistered_structure_parameter() -> None:
    with pytest.raises(PhysicsTrainingError, match="不在白名单"):
        configure_structure_trainability(  # type: ignore[arg-type]
            torch.nn.Linear(2, 2),
            _TinyRuntime(include_unexpected=True),
        )


def _gradient_groups() -> StructureParameterGroups:
    state = torch.nn.Parameter(torch.tensor(2.0))
    encoder = torch.nn.Parameter(torch.tensor(3.0))
    attention = torch.nn.Parameter(torch.tensor(4.0))
    gate = torch.nn.Parameter(torch.tensor(5.0))
    return StructureParameterGroups(
        state_head=(state,),
        condition_encoder=(encoder,),
        cross_attention=(attention,),
        gates=(gate,),
        names=("state", "encoder", "attention", "gate"),
    )


def test_physics_gradient_is_strictly_isolated_to_state_head() -> None:
    groups = _gradient_groups()
    base = torch.nn.Linear(1, 1)
    for parameter in base.parameters():
        parameter.requires_grad_(False)
    physics_loss = groups.state_head[0].square()

    result = physics_gradient_isolation(physics_loss, groups, base)

    assert result["physics_to_state_head_gradient_norm"] > 0.0
    assert result["physics_to_injector_gradient_norm"] == 0.0
    assert result["physics_to_base_gradient_norm"] == 0.0


def test_physics_gradient_isolation_rejects_injector_or_base_leakage() -> None:
    groups = _gradient_groups()
    frozen_base = torch.nn.Linear(1, 1)
    for parameter in frozen_base.parameters():
        parameter.requires_grad_(False)
    leaked_loss = (groups.state_head[0] + groups.gates[0]).square()
    with pytest.raises(PhysicsTrainingError, match="越界"):
        physics_gradient_isolation(leaked_loss, groups, frozen_base)

    trainable_base = torch.nn.Linear(1, 1)
    with pytest.raises(PhysicsTrainingError, match="可训练基座"):
        physics_gradient_isolation(groups.state_head[0].square(), groups, trainable_base)


def test_generation_gradient_diagnostics_enforce_first_and_second_step_paths() -> None:
    groups = _gradient_groups()
    groups.gates[0].grad = torch.tensor(1.0)
    first = generation_gradient_snapshot(groups)
    validate_generation_gradient_step(1, first)

    for parameter in groups.all:
        parameter.grad = torch.tensor(1.0)
    second = generation_gradient_snapshot(groups)
    validate_generation_gradient_step(2, second)

    assert first == {
        "generation_to_state_head_gradient_norm": 0.0,
        "generation_to_condition_encoder_gradient_norm": 0.0,
        "generation_to_cross_attention_gradient_norm": 0.0,
        "generation_to_gate_gradient_norm": 1.0,
    }
    assert all(value > 0.0 for value in second.values())


def test_generation_gradient_diagnostics_reject_broken_paths() -> None:
    first_with_state_leak = {
        "generation_to_state_head_gradient_norm": 1.0,
        "generation_to_condition_encoder_gradient_norm": 0.0,
        "generation_to_cross_attention_gradient_norm": 0.0,
        "generation_to_gate_gradient_norm": 1.0,
    }
    second_without_attention = {
        "generation_to_state_head_gradient_norm": 1.0,
        "generation_to_condition_encoder_gradient_norm": 1.0,
        "generation_to_cross_attention_gradient_norm": 0.0,
        "generation_to_gate_gradient_norm": 1.0,
    }

    with pytest.raises(PhysicsTrainingError, match="第一步"):
        validate_generation_gradient_step(1, first_with_state_leak)
    with pytest.raises(PhysicsTrainingError, match="第二步"):
        validate_generation_gradient_step(2, second_without_attention)


def test_kbit_preparation_explicitly_disables_and_audits_checkpointing() -> None:
    model = _CheckpointModel(enabled=True)
    calls: list[dict[str, object]] = []

    def prepare(
        supplied_model: torch.nn.Module,
        **kwargs: object,
    ) -> torch.nn.Module:
        calls.append(dict(kwargs))
        return supplied_model

    prepared, audit = prepare_base_for_bounded_training(model, prepare)

    assert prepared is model
    assert calls == [{"use_gradient_checkpointing": False}]
    assert model.disable_calls == 1
    assert audit == {
        "use_gradient_checkpointing": False,
        "model_is_gradient_checkpointing": False,
        "enabled_module_names": [],
        "verified_disabled": True,
    }


@pytest.mark.parametrize("root_enabled", (False, True))
def test_checkpoint_audit_rejects_any_enabled_flag(root_enabled: bool) -> None:
    model = _CheckpointModel(enabled=root_enabled)
    if not root_enabled:
        model.layer.gradient_checkpointing = True

    with pytest.raises(PhysicsTrainingError, match="仍处于启用状态"):
        gradient_checkpointing_audit(model)


def test_step_diagnostics_include_four_layers_and_runtime_counts() -> None:
    first = ConditioningDiagnostics(
        gate_values=(0.01, 0.02, 0.03, 0.04),
        attention_entropies=(1.0, 2.0, 3.0, 4.0),
        max_residual_ratio=0.04,
        source_hook_count=1,
        target_hook_counts=(1, 1, 1, 1),
        prefill_count=0,
        cached_decode_count=0,
    )
    second = ConditioningDiagnostics(
        gate_values=(0.05, 0.06, 0.07, 0.08),
        attention_entropies=(3.0, 4.0, 5.0, 6.0),
        max_residual_ratio=0.08,
        source_hook_count=2,
        target_hook_counts=(2, 2, 2, 2),
        prefill_count=0,
        cached_decode_count=0,
    )

    metrics = _mean_diagnostics((first, second))

    for index, layer in enumerate((24, 25, 26, 27)):
        assert metrics[f"structure/gate_layer_{layer}"] == second.gate_values[index]
        assert metrics[f"structure/attention_entropy_layer_{layer}"] == pytest.approx(2.0 + index)
        assert metrics[f"runtime/target_layer_{layer}_hook_count"] == 3.0
    assert metrics["structure/max_residual_ratio"] == 0.08
    assert metrics["runtime/source_hook_count"] == 3.0


def test_artifact_layout_contains_all_required_contract_files(tmp_path: Path) -> None:
    layout = BoundedRunLayout.create(tmp_path / "run")
    expected = {
        "config_snapshot.yaml",
        "environment.json",
        "input_sha256.json",
        "console.log",
        "step_metrics.jsonl",
        "training_summary.json",
        "structure_config.json",
        "structure_state.pt",
        "base_binding.json",
        "gradient_path.json",
        "runtime_path_audit.json",
        "bypass_equivalence.json",
        "generation_sample_order.json",
        "physics_sample_order.json",
        "artifact_manifest.json",
    }

    assert {path.name for path in layout.required_paths} == expected
    with pytest.raises(PhysicsTrainingError, match="制品不完整"):
        validate_bounded_artifacts(layout)


def _write_test_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_complete_artifact_run(
    root: Path,
    runtime: _ArtifactRuntime,
    *,
    variant: str = "combined",
) -> tuple[Path, Path, dict[str, object], dict[str, object]]:
    artifact_dir = root / "run"
    artifact_dir.mkdir(parents=True)
    layout = BoundedRunLayout.create(artifact_dir)
    adapter_path = root / "frozen-s3" / "final_adapter"
    adapter_path.mkdir(parents=True)
    (adapter_path / "adapter_config.json").write_text('{"adapter": "s3"}', encoding="utf-8")

    model_id = "/models/Qwen3-1.7B"
    config = {
        "schema_version": STRUCTURE_SCHEMA_VERSION,
        "variant": variant,
        "spec": json.loads(json.dumps(asdict(runtime.spec))),
    }
    parameter_digest = _adapter_parameter_digest(runtime.model)
    binding = {
        "schema_version": STRUCTURE_SCHEMA_VERSION,
        "model_id": model_id,
        "detection_adapter_path": str(adapter_path),
        "detection_adapter_manifest": _directory_manifest(adapter_path),
        "detection_adapter_parameter_sha256_before": parameter_digest,
        "detection_adapter_parameter_sha256_after": parameter_digest,
        "gradient_checkpointing": {"verified_disabled": True},
    }
    summary = {
        "schema_version": STRUCTURE_SCHEMA_VERSION,
        "status": "finished",
        "variant": variant,
        "model_id": model_id,
        "detection_adapter_path": str(adapter_path),
        "base_and_s3_trainable_parameter_count": 0,
    }
    layout.config_snapshot.write_text("training: {}\n", encoding="utf-8")
    layout.console_log.write_text("训练完成\n", encoding="utf-8")
    layout.step_metrics.write_text('{"step": 1}\n', encoding="utf-8")
    for path in (
        layout.environment,
        layout.input_sha256,
        layout.gradient_path,
        layout.runtime_path_audit,
        layout.bypass_equivalence,
        layout.generation_sample_order,
        layout.physics_sample_order,
    ):
        _write_test_json(path, {})
    _write_test_json(layout.training_summary, summary)
    _write_test_json(layout.structure_config, config)
    _write_test_json(layout.base_binding, binding)
    torch.save({"state_head.weight": torch.ones(1)}, layout.structure_state)

    swanlog_dir = artifact_dir / "swanlog" / BOUNDED_TRAINING_PHASE
    swanlog_dir.mkdir(parents=True)
    (swanlog_dir / "run.log").write_text("finished\n", encoding="utf-8")
    tracked_names = (
        "config_snapshot",
        "environment",
        "input_sha256",
        "step_metrics",
        "training_summary",
        "structure_config",
        "structure_state",
        "base_binding",
        "gradient_path",
        "runtime_path_audit",
        "bypass_equivalence",
        "generation_sample_order",
        "physics_sample_order",
    )
    data_files = {name: str(getattr(layout, name)) for name in tracked_names}
    data_files.update(
        {
            "artifact_manifest": str(layout.artifact_manifest),
            "console_log": str(layout.console_log),
            "swanlab_log_dir": str(swanlog_dir),
        }
    )
    _write_test_json(
        layout.artifact_manifest,
        {
            "schema_version": TRACKING_ARTIFACT_SCHEMA_VERSION,
            "status": "finished",
            "phase": BOUNDED_TRAINING_PHASE,
            "run_id": "test-run",
            "data_files": data_files,
        },
    )
    return artifact_dir, adapter_path, config, binding


def _load_test_artifacts(
    runtime: _ArtifactRuntime,
    artifact_dir: Path,
    adapter_path: Path,
    *,
    model_id: str = "/models/Qwen3-1.7B",
) -> dict[str, object]:
    return load_bounded_structure_artifacts(  # type: ignore[arg-type]
        runtime,
        artifact_dir,
        expected_model_id=model_id,
        expected_detection_adapter_path=adapter_path,
    )


def test_structure_artifacts_are_bound_and_loaded_strictly(tmp_path: Path) -> None:
    runtime = _ArtifactRuntime()
    artifact_dir, adapter_path, config, binding = _write_complete_artifact_run(tmp_path, runtime)

    loaded = _load_test_artifacts(runtime, artifact_dir, adapter_path)

    assert loaded == {"structure_config": config, "base_binding": binding}
    assert runtime.strict is True
    assert runtime.loaded_state is not None
    assert torch.equal(runtime.loaded_state["state_head.weight"], torch.ones(1))


def test_structure_artifact_loading_rejects_binding_or_state_key_mismatch(
    tmp_path: Path,
) -> None:
    runtime = _ArtifactRuntime()
    artifact_dir, adapter_path, _config, _binding = _write_complete_artifact_run(
        tmp_path, runtime, variant="structure_only"
    )

    with pytest.raises(PhysicsTrainingError, match="基座路径不匹配"):
        _load_test_artifacts(runtime, artifact_dir, adapter_path, model_id="/models/another-model")
    torch.save({"unexpected": torch.ones(1)}, artifact_dir / "structure_state.pt")
    with pytest.raises(ValueError, match="结构状态键不匹配"):
        _load_test_artifacts(runtime, artifact_dir, adapter_path)


def test_structure_loading_rejects_missing_or_unfinished_run_artifacts(
    tmp_path: Path,
) -> None:
    missing_runtime = _ArtifactRuntime()
    missing_dir, missing_adapter, _config, _binding = _write_complete_artifact_run(
        tmp_path / "missing", missing_runtime
    )
    (missing_dir / "artifact_manifest.json").unlink()
    with pytest.raises(PhysicsTrainingError, match="制品不完整"):
        _load_test_artifacts(missing_runtime, missing_dir, missing_adapter)

    summary_runtime = _ArtifactRuntime()
    summary_dir, summary_adapter, _config, _binding = _write_complete_artifact_run(
        tmp_path / "summary", summary_runtime
    )
    summary = json.loads((summary_dir / "training_summary.json").read_text(encoding="utf-8"))
    summary["status"] = "crashed"
    _write_test_json(summary_dir / "training_summary.json", summary)
    with pytest.raises(PhysicsTrainingError, match="training_summary.json"):
        _load_test_artifacts(summary_runtime, summary_dir, summary_adapter)

    manifest_runtime = _ArtifactRuntime()
    manifest_dir, manifest_adapter, _config, _binding = _write_complete_artifact_run(
        tmp_path / "manifest", manifest_runtime
    )
    manifest = json.loads((manifest_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    manifest["status"] = "crashed"
    _write_test_json(manifest_dir / "artifact_manifest.json", manifest)
    with pytest.raises(PhysicsTrainingError, match="artifact_manifest.json"):
        _load_test_artifacts(manifest_runtime, manifest_dir, manifest_adapter)


def test_structure_loading_rejects_incomplete_tracking_or_s3_manifest(
    tmp_path: Path,
) -> None:
    tracking_runtime = _ArtifactRuntime()
    tracking_dir, tracking_adapter, _config, _binding = _write_complete_artifact_run(
        tmp_path / "tracking", tracking_runtime
    )
    manifest_path = tracking_dir / "artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["data_files"]["gradient_path"]
    _write_test_json(manifest_path, manifest)
    with pytest.raises(PhysicsTrainingError, match="制品路径不完整"):
        _load_test_artifacts(tracking_runtime, tracking_dir, tracking_adapter)

    binding_runtime = _ArtifactRuntime()
    binding_dir, binding_adapter, _config, binding = _write_complete_artifact_run(
        tmp_path / "binding", binding_runtime
    )
    del binding["detection_adapter_manifest"]
    _write_test_json(binding_dir / "base_binding.json", binding)
    with pytest.raises(PhysicsTrainingError, match="缺少 S3 目录清单"):
        _load_test_artifacts(binding_runtime, binding_dir, binding_adapter)


def test_structure_loading_rejects_changed_s3_directory_or_memory_parameters(
    tmp_path: Path,
) -> None:
    directory_runtime = _ArtifactRuntime()
    directory_dir, directory_adapter, _config, _binding = _write_complete_artifact_run(
        tmp_path / "directory", directory_runtime
    )
    (directory_adapter / "adapter_config.json").write_text(
        '{"adapter": "changed"}', encoding="utf-8"
    )
    with pytest.raises(PhysicsTrainingError, match="目录与训练时绑定不一致"):
        _load_test_artifacts(directory_runtime, directory_dir, directory_adapter)

    parameter_runtime = _ArtifactRuntime()
    parameter_dir, parameter_adapter, _config, _binding = _write_complete_artifact_run(
        tmp_path / "parameter", parameter_runtime
    )
    with torch.no_grad():
        next(parameter_runtime.model.parameters()).add_(1.0)
    with pytest.raises(PhysicsTrainingError, match="内存 S3 参数与训练时绑定不一致"):
        _load_test_artifacts(parameter_runtime, parameter_dir, parameter_adapter)


def test_fixed_training_constants_are_immutable_contract_values() -> None:
    assert FORMAL_TRAINING_STEPS == 202
    assert WARMUP_STEPS == 20
    assert PEAK_LEARNING_RATE == 2e-4
    assert MIN_LEARNING_RATE == 2e-5
    assert STATE_LOSS_WEIGHT == 1.0
    assert PHYSICS_LOSS_WEIGHT == 0.01
    assert MAX_GRAD_NORM == 1.0
