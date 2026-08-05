from __future__ import annotations

import hashlib
import json
import random
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

import flow_probe.shared_b0_physics_train as shared_train
from flow_probe.physics_train import ContinuousQueueStateHead, queue_balance_residual
from flow_probe.shared_b0_physics_train import (
    EXPECTED_GENERATION_RECORDS,
    EXPECTED_PHYSICS_MICRO_STEPS,
    EXPECTED_PHYSICS_RECORDS,
    AuxiliaryTensorBatch,
    PreparedInputs,
    SharedB0PhysicsTrainingError,
    TrainingProgress,
    build_auxiliary_tensor_batch,
    build_baseline_contract,
    build_generation_schedule,
    build_physics_schedule,
    build_run_binding,
    build_state_prompt_texts,
    build_training_runtime,
    compose_run_binding,
    compute_auxiliary_loss,
    ensure_finite_losses,
    finite_gradient_norm,
    initialize_state_head,
    load_shared_b0_physics_training_config,
    load_training_checkpoint,
    parameter_tree_sha256,
    parse_state_sidecar_record,
    physics_batch_weight,
    progress_for_step,
    save_training_checkpoint,
    state_mask_sha256,
    validate_generation_batch_contract,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs/shared_b0_physics_baselines_seed42_200_v1.yaml"


def _classification_records(count: int = 1000) -> list[dict[str, object]]:
    return [
        {
            "sample_id": f"sample-{index:05d}",
            "stable_order": index,
            "prompt": f"普通共享字段样本 {index}",
            "completion": '{"binary_label":"benign"}',
        }
        for index in range(count)
    ]


def _state_mask(index: int) -> list[bool]:
    return [True, *[position == index % 4 for position in range(4)]]


def _sidecar_record(index: int) -> dict[str, object]:
    increments = [10.0, 10.0, 10.0, 10.0]
    cumulative = [0.0, 10.0, 20.0, 30.0, 40.0]
    return {
        "sample_id": f"sample-{index:05d}",
        "group_id": f"group-{index % 11}",
        "stable_order": index,
        "usage": "train_fit_diagnostic",
        "state_targets": [0.0, 0.1, 0.2, 0.3, 0.4],
        "state_mask_inputs": _state_mask(index),
        "normalization_scale": 100.0,
        "capacity_by_anchor": cumulative,
        "received_bytes_by_anchor": cumulative,
        "received_packets_by_anchor": [0.0, 1.0, 2.0, 3.0, 4.0],
        "dequeued_bytes_by_anchor": [0.0] * 5,
        "dropped_bytes_by_anchor": [0.0] * 5,
        "anchor_times": [0.0, 0.1, 0.2, 0.3, 0.4],
        "unused_increments": increments,
    }


def _prepared_inputs(use_fallback: bool = False) -> PreparedInputs:
    classification = _classification_records()
    sidecar = [_sidecar_record(index) for index in range(EXPECTED_PHYSICS_RECORDS)]
    micro_batch, accumulation = (1, 4) if use_fallback else (2, 2)
    generation = build_generation_schedule(
        classification,
        micro_batch_size=micro_batch,
        gradient_accumulation_steps=accumulation,
    )
    physics = build_physics_schedule(sidecar)
    states = [parse_state_sidecar_record(record) for record in sidecar]
    hashes = {
        "classification_train_file": "1" * 64,
        "classification_validation_file": "2" * 64,
        "physics_sidecar_file": "3" * 64,
        "physics_dataset_manifest": "4" * 64,
    }
    return PreparedInputs(
        classification_records=tuple(classification),
        validation_records=tuple(classification[:8]),
        classification_by_id={
            str(record["sample_id"]): record for record in classification
        },
        sidecar_records=tuple(sidecar),
        sidecar_by_id={str(record["sample_id"]): record for record in sidecar},
        generation_schedule=generation,
        physics_schedule=physics,
        state_mask_sha256=state_mask_sha256(states),
        hashes=hashes,
        audit={"status": "passed"},
    )


def test_real_config_freezes_scientific_contract_and_two_semantic_baselines() -> None:
    config = load_shared_b0_physics_training_config(CONFIG_PATH)

    assert config.probe.seed == 42
    assert config.max_steps == 200
    assert config.save_steps == 20
    assert config.physics_records == 2421
    assert config.physics_micro_steps == 400
    assert config.physics_usage == "train_fit_diagnostic"
    assert config.state_mask == "anchor0_plus_one"
    assert config.visible_observation_fields == shared_train.EXPECTED_VISIBLE_FIELDS
    assert config.generation_batch(False) == (2, 2)
    assert config.generation_batch(True) == (1, 4)
    assert config.loss_weights("state_supervision") == (1.0, 0.0)
    assert config.loss_weights("standard_pinn") == (1.0, 0.01)
    assert (
        build_baseline_contract("state_supervision").reads_physics_coefficients is False
    )
    assert build_baseline_contract("standard_pinn").reads_physics_coefficients is True


@pytest.mark.parametrize("pair", [(2, 2), (1, 4)])
def test_only_two_effective_generation_batch_profiles_are_accepted(
    pair: tuple[int, int],
) -> None:
    validate_generation_batch_contract(*pair)


@pytest.mark.parametrize("pair", [(4, 1), (2, 4), (1, 2), (3, 2)])
def test_other_generation_batch_profiles_are_rejected(pair: tuple[int, int]) -> None:
    with pytest.raises(SharedB0PhysicsTrainingError, match="只允许"):
        validate_generation_batch_contract(*pair)


def test_generation_schedule_maps_200_steps_to_800_positions_in_both_profiles() -> None:
    records = _classification_records()
    primary = build_generation_schedule(
        records,
        micro_batch_size=2,
        gradient_accumulation_steps=2,
    )
    fallback = build_generation_schedule(
        records,
        micro_batch_size=1,
        gradient_accumulation_steps=4,
    )

    assert len(primary.batches) == 400
    assert len(fallback.batches) == 800
    assert (
        len(primary.sample_ids)
        == len(fallback.sample_ids)
        == EXPECTED_GENERATION_RECORDS
    )
    assert primary.sample_ids == fallback.sample_ids
    assert len(set(primary.sample_ids)) == EXPECTED_GENERATION_RECORDS
    assert primary.to_mapping()["schedule_sha256"] == primary.schedule_sha256


def test_physics_schedule_has_fixed_batch_boundaries_and_exact_single_coverage() -> (
    None
):
    records = [_sidecar_record(index) for index in range(EXPECTED_PHYSICS_RECORDS)]
    first = build_physics_schedule(records)
    second = build_physics_schedule(list(reversed(records)))

    assert first == second
    assert len(first.batches) == EXPECTED_PHYSICS_MICRO_STEPS
    assert first.batch_sizes.count(7) == 21
    assert first.batch_sizes.count(6) == 379
    assert len(first.sample_ids) == EXPECTED_PHYSICS_RECORDS
    assert len(set(first.sample_ids)) == EXPECTED_PHYSICS_RECORDS
    assert first.to_mapping()["schedule_sha256"] == first.schedule_sha256


def test_progress_tracks_independent_generation_and_physics_cursors() -> None:
    primary = _prepared_inputs(False)
    fallback = _prepared_inputs(True)

    primary_final = progress_for_step(
        200,
        primary.generation_schedule,
        primary.physics_schedule,
        2,
    )
    fallback_final = progress_for_step(
        200,
        fallback.generation_schedule,
        fallback.physics_schedule,
        4,
    )

    assert primary_final.generation_micro_step == 400
    assert fallback_final.generation_micro_step == 800
    assert primary_final.generation_cursor == fallback_final.generation_cursor == 800
    assert primary_final.physics_micro_step == fallback_final.physics_micro_step == 400
    assert primary_final.physics_cursor == fallback_final.physics_cursor == 2421


class _AccessAudit(dict[str, object]):
    def __init__(self, value: dict[str, object]) -> None:
        super().__init__(value)
        self.accessed: list[str] = []

    def get(self, key: str, default: object = None) -> object:
        self.accessed.append(key)
        return super().get(key, default)


def test_state_branch_consumes_signed_mask_without_reading_physics_coefficients() -> (
    None
):
    raw = _sidecar_record(3)
    raw["group_id"] = "changed-group-does-not-matter"
    audit = _AccessAudit(raw)

    parsed = parse_state_sidecar_record(audit)
    tensors = build_auxiliary_tensor_batch([audit], "state_supervision", "cpu")

    mask_inputs = raw["state_mask_inputs"]
    assert isinstance(mask_inputs, list)
    assert parsed.state_mask == tuple(mask_inputs)
    assert tensors.scale is None
    assert not (set(audit.accessed) & shared_train.PHYSICS_COEFFICIENT_FIELDS)


@pytest.mark.parametrize(
    "mask",
    [
        [False, True, False, False, False],
        [True, False, False, False, False],
        [True, True, True, False, False],
        [True, 1, False, False, False],
        [True, True, False, False],
    ],
)
def test_signed_mask_contract_rejects_invalid_length_anchor0_count_or_type(
    mask: list[object],
) -> None:
    record = _sidecar_record(0)
    record["state_mask_inputs"] = mask
    with pytest.raises(SharedB0PhysicsTrainingError, match="state_mask_inputs"):
        parse_state_sidecar_record(record)


def test_masked_state_loss_matches_hand_calculation() -> None:
    predicted = torch.tensor([[2.0, 10.0, 20.0, 30.0, 4.0]])
    target = torch.zeros((1, 5))
    mask = torch.tensor([[True, False, False, False, True]])
    tensors = AuxiliaryTensorBatch(state_targets=target, state_mask=mask)

    result = compute_auxiliary_loss(predicted, tensors, "state_supervision")

    assert result.state.item() == pytest.approx((4.0 + 16.0) / 2.0)
    assert result.total.item() == pytest.approx(10.0)
    assert result.physics is None
    assert result.valid_state_elements == 2
    assert not result.physics_coefficients_accessed


def test_standard_pinn_only_adds_point_zero_one_times_existing_residual_loss() -> None:
    raw = _sidecar_record(0)
    tensors = build_auxiliary_tensor_batch([raw], "standard_pinn", "cpu")
    predicted = torch.tensor([[0.0, 0.2, 0.2, 0.3, 0.4]], requires_grad=True)

    result = compute_auxiliary_loss(predicted, tensors, "standard_pinn")
    direct_residual = queue_balance_residual(
        predicted,
        tensors.scale,
        tensors.capacity,
        tensors.received,
        tensors.dequeued,
        tensors.dropped_before,
        tensors.dropped_after,
    )
    direct_physics = direct_residual.square().mean()

    assert result.physics is not None
    assert result.physics.requires_grad
    assert result.physics.detach().item() == pytest.approx(
        direct_physics.detach().item()
    )
    assert result.total.detach().item() == pytest.approx(
        (result.state + 0.01 * direct_physics).detach().item()
    )
    assert result.physics_coefficients_accessed
    result.total.backward()
    assert predicted.grad is not None
    assert bool(torch.isfinite(predicted.grad).all().item())
    assert int(torch.count_nonzero(predicted.grad).item()) > 0


def test_physics_residual_gradient_reaches_shared_lora_and_state_head() -> None:
    shared_lora = torch.nn.Linear(3, 4)
    state_head = ContinuousQueueStateHead(4)
    predicted = state_head(shared_lora(torch.ones((2, 3))))
    raw = [_sidecar_record(0), _sidecar_record(1)]
    tensors = build_auxiliary_tensor_batch(raw, "standard_pinn", "cpu")

    result = compute_auxiliary_loss(predicted, tensors, "standard_pinn")
    assert result.physics is not None
    result.physics.backward()

    assert any(parameter.grad is not None for parameter in shared_lora.parameters())
    assert any(parameter.grad is not None for parameter in state_head.parameters())


def test_variable_physics_batch_means_receive_equal_per_sample_weight() -> None:
    six_total = 6.0 * physics_batch_weight(6)
    seven_total = 7.0 * physics_batch_weight(7)

    assert six_total / 6.0 == pytest.approx(physics_batch_weight(6))
    assert seven_total / 7.0 == pytest.approx(physics_batch_weight(7))
    assert physics_batch_weight(6) * (2421 / 400) == pytest.approx(6.0)
    assert physics_batch_weight(7) * (2421 / 400) == pytest.approx(7.0)


def test_nonfinite_loss_and_gradient_fail_immediately() -> None:
    with pytest.raises(FloatingPointError, match="损失"):
        ensure_finite_losses(total=torch.tensor(float("nan")))
    parameter = torch.nn.Parameter(torch.ones(2))
    parameter.grad = torch.tensor([1.0, float("inf")])
    with pytest.raises(FloatingPointError, match="梯度"):
        finite_gradient_norm([parameter])


def test_two_baselines_share_identical_state_head_initialization_hash() -> None:
    state_head, state_hash = initialize_state_head(8, 42)
    pinn_head, pinn_hash = initialize_state_head(8, 42)

    assert state_hash == pinn_hash
    assert parameter_tree_sha256(state_head) == parameter_tree_sha256(pinn_head)
    assert all(
        torch.equal(left, right)
        for left, right in zip(
            state_head.parameters(), pinn_head.parameters(), strict=True
        )
    )


class _PromptTokenizer:
    eos_token = "<eos>"

    def apply_chat_template(self, messages, **kwargs) -> str:
        del kwargs
        return f"USER:{messages[0]['content']}\nASSISTANT:"


def test_physics_fields_never_enter_state_qwen_prompt() -> None:
    classification = _classification_records(2)
    prompts = build_state_prompt_texts(classification, _PromptTokenizer())

    assert prompts == [
        "USER:普通共享字段样本 0\nASSISTANT:",
        "USER:普通共享字段样本 1\nASSISTANT:",
    ]
    assert all(
        field not in prompt
        for prompt in prompts
        for field in shared_train.PROHIBITED_CLASSIFICATION_FIELDS
    )


def test_run_bindings_share_every_common_hash_and_only_switch_baseline_loss() -> None:
    config = load_shared_b0_physics_training_config(CONFIG_PATH)
    prepared = _prepared_inputs()
    base = {"schema_version": "qwen_sft_training_binding_v1", "seed": 42}
    state = compose_run_binding(
        base,
        config,
        prepared,
        "state_supervision",
        "a" * 64,
        "b" * 64,
        use_hardware_fallback=False,
        output_dir=Path("runs/formal/shared-b0-seed42"),
    )
    pinn = compose_run_binding(
        base,
        config,
        prepared,
        "standard_pinn",
        "a" * 64,
        "b" * 64,
        use_hardware_fallback=False,
        output_dir=Path("runs/formal/shared-b0-seed42"),
    )

    differing = {key for key in state if state[key] != pinn[key]}
    assert differing == {"baseline", "lambda_physics", "binding_sha256"}
    assert (
        state["state_head_initialization_sha256"]
        == pinn["state_head_initialization_sha256"]
    )
    assert state["lora_initialization_sha256"] == pinn["lora_initialization_sha256"]


class _FakeModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.lora_linear = torch.nn.Linear(3, 3)
        self.config = SimpleNamespace(hidden_size=3, use_cache=True)

    def save_pretrained(self, path: str) -> None:
        target = Path(path)
        target.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), target / "adapter_model.pt")


class _FakeTrainer:
    def __init__(self, model: _FakeModel, train_dataset: object) -> None:
        self.model = model
        self.train_dataset = train_dataset
        self.data_collator = lambda rows: rows
        self.accelerator = SimpleNamespace(scaler=None)
        self.optimizer = None
        self.lr_scheduler = None

    def create_optimizer_and_scheduler(self, num_training_steps: int) -> None:
        self.optimizer = torch.optim.AdamW(
            [
                parameter
                for parameter in self.model.parameters()
                if parameter.requires_grad
            ],
            lr=0.001,
        )
        self.lr_scheduler = torch.optim.lr_scheduler.LambdaLR(
            self.optimizer,
            lambda step: max(0.0, 1.0 - step / num_training_steps),
        )


def test_runtime_is_strictly_wired_to_task02_public_builders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_shared_b0_physics_training_config(CONFIG_PATH)
    prepared = _prepared_inputs()
    calls: list[str] = []
    model = _FakeModel()

    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "is_bf16_supported", lambda: True)

    def model_builder(*args):
        del args
        calls.append("model")
        return model, object()

    def dataset_builder(records, tokenizer):
        del tokenizer
        calls.append("dataset")
        return list(records)

    def trainer_builder(*args, **kwargs):
        del args
        calls.append("trainer")
        return _FakeTrainer(kwargs["model"], kwargs["train_dataset"])

    monkeypatch.setattr(shared_train, "build_qwen_model_and_tokenizer", model_builder)
    monkeypatch.setattr(shared_train, "build_chat_dataset", dataset_builder)
    monkeypatch.setattr(shared_train, "build_sft_trainer", trainer_builder)

    runtime = build_training_runtime(
        config,
        prepared,
        "state_supervision",
        use_hardware_fallback=False,
        output_dir=Path("runs/formal/runtime-wiring-test"),
    )

    assert calls == ["model", "dataset", "dataset", "trainer"]
    assert runtime.model is model
    assert runtime.optimizer is not None
    assert all(
        id(parameter)
        in {
            id(item)
            for group in runtime.optimizer.param_groups
            for item in group["params"]
        }
        for parameter in runtime.state_head.parameters()
    )


def _binding(name: str = "state_supervision") -> dict[str, object]:
    payload = {
        "schema_version": shared_train.BINDING_SCHEMA_VERSION,
        "baseline": name,
        "lambda_state": 1.0,
        "lambda_physics": 0.0 if name == "state_supervision" else 0.01,
        "config_sha256": "a" * 64,
    }
    digest = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    return {**payload, "binding_sha256": digest}


def _toy_setup(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    model = _FakeModel()
    head = ContinuousQueueStateHead(3)
    optimizer = torch.optim.AdamW(
        [*model.parameters(), *head.parameters()],
        lr=0.01,
    )
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer,
        lambda step: max(0.0, 1.0 - step / 8.0),
    )
    return model, head, optimizer, scheduler


def _toy_steps(model, head, optimizer, scheduler, start: int, stop: int, metrics):
    for step in range(start, stop + 1):
        optimizer.zero_grad(set_to_none=True)
        random_scale = random.random() + float(np.random.random())
        inputs = torch.rand((2, 3))
        loss = head(model.lora_linear(inputs)).sum() * random_scale
        loss.backward()
        optimizer.step()
        scheduler.step()
        metrics.append({"step": step, "loss": float(loss.detach().item())})


def _assert_parameter_trees_equal(left, right) -> None:
    left_state = left.state_dict()
    right_state = right.state_dict()
    assert set(left_state) == set(right_state)
    assert all(torch.equal(left_state[key], right_state[key]) for key in left_state)


def test_four_steps_equal_two_steps_checkpoint_and_resume(tmp_path: Path) -> None:
    binding = _binding()
    continuous_model, continuous_head, continuous_optimizer, continuous_scheduler = (
        _toy_setup(42)
    )
    continuous_metrics: list[dict[str, object]] = []
    _toy_steps(
        continuous_model,
        continuous_head,
        continuous_optimizer,
        continuous_scheduler,
        1,
        4,
        continuous_metrics,
    )

    split_model, split_head, split_optimizer, split_scheduler = _toy_setup(42)
    split_metrics: list[dict[str, object]] = []
    _toy_steps(
        split_model,
        split_head,
        split_optimizer,
        split_scheduler,
        1,
        2,
        split_metrics,
    )
    checkpoint = save_training_checkpoint(
        tmp_path / "checkpoint-000002",
        model=split_model,
        state_head=split_head,
        optimizer=split_optimizer,
        scheduler=split_scheduler,
        gradient_scaler=None,
        progress=TrainingProgress(2, 4, 8, 4, 25),
        binding=binding,
        metrics=split_metrics,
    )

    resumed_model, resumed_head, resumed_optimizer, resumed_scheduler = _toy_setup(777)
    progress, resumed_metrics = load_training_checkpoint(
        checkpoint,
        model=resumed_model,
        state_head=resumed_head,
        optimizer=resumed_optimizer,
        scheduler=resumed_scheduler,
        gradient_scaler=None,
        expected_binding=binding,
    )
    _toy_steps(
        resumed_model,
        resumed_head,
        resumed_optimizer,
        resumed_scheduler,
        3,
        4,
        resumed_metrics,
    )

    assert progress == TrainingProgress(2, 4, 8, 4, 25)
    assert resumed_metrics == continuous_metrics
    _assert_parameter_trees_equal(resumed_model, continuous_model)
    _assert_parameter_trees_equal(resumed_head, continuous_head)
    assert resumed_scheduler.state_dict() == continuous_scheduler.state_dict()
    assert (checkpoint / "adapter").is_dir()
    for filename in shared_train._CHECKPOINT_REQUIRED_FILES:
        assert (checkpoint / filename).is_file()


def test_checkpoint_rejects_baseline_or_config_binding_mismatch_before_restore(
    tmp_path: Path,
) -> None:
    model, head, optimizer, scheduler = _toy_setup(42)
    checkpoint = save_training_checkpoint(
        tmp_path / "checkpoint-000002",
        model=model,
        state_head=head,
        optimizer=optimizer,
        scheduler=scheduler,
        gradient_scaler=None,
        progress=TrainingProgress(2, 4, 8, 4, 25),
        binding=_binding("state_supervision"),
        metrics=[],
    )
    expected = _binding("standard_pinn")

    with pytest.raises(SharedB0PhysicsTrainingError, match="绑定不一致"):
        load_training_checkpoint(
            checkpoint,
            model=model,
            state_head=head,
            optimizer=optimizer,
            scheduler=scheduler,
            gradient_scaler=None,
            expected_binding=expected,
        )


def test_build_run_binding_includes_public_qwen_binding_and_all_schedule_hashes(
    tmp_path: Path,
) -> None:
    config = load_shared_b0_physics_training_config(CONFIG_PATH)
    train_file = tmp_path / "train.jsonl"
    validation_file = tmp_path / "validation.jsonl"
    train_file.write_text("{}\n", encoding="utf-8")
    validation_file.write_text("{}\n", encoding="utf-8")
    config = replace(
        config,
        classification_train_file=train_file,
        classification_validation_file=validation_file,
        output_dirs=(
            ("state_supervision", tmp_path / "state"),
            ("standard_pinn", tmp_path / "pinn"),
        ),
    )
    prepared = _prepared_inputs()

    binding = build_run_binding(
        config,
        prepared,
        "state_supervision",
        "a" * 64,
        "b" * 64,
        output_dir=tmp_path / "formal-state-supervision",
    )

    base_binding = binding["base_training_binding"]
    assert isinstance(base_binding, dict)
    assert base_binding["seed"] == 42
    assert (
        binding["generation_schedule_sha256"]
        == prepared.generation_schedule.schedule_sha256
    )
    assert (
        binding["physics_schedule_sha256"] == prepared.physics_schedule.schedule_sha256
    )
    assert binding["state_mask_sha256"] == prepared.state_mask_sha256
    assert binding["output_dir"] == str(
        (tmp_path / "formal-state-supervision").resolve()
    )
    assert binding["binding_sha256"] == shared_train._canonical_sha256(
        {key: value for key, value in binding.items() if key != "binding_sha256"}
    )


def test_formal_cli_requires_explicit_output_dir() -> None:
    common = [
        "--config",
        str(CONFIG_PATH),
        "--baseline",
        "state_supervision",
    ]

    preflight = shared_train._parse_args([*common, "--preflight-only"])
    assert preflight.output_dir is None

    with pytest.raises(SystemExit):
        shared_train._parse_args(common)

    formal = shared_train._parse_args(
        [*common, "--output-dir", "runs/formal/unique-run"]
    )
    assert formal.output_dir == Path("runs/formal/unique-run")


class _FakeSwanlab:
    def __init__(self, run_id: str = "swan-run-123") -> None:
        self.run_id = run_id
        self.init_kwargs: dict[str, object] = {}
        self.log_calls: list[tuple[dict[str, float], int]] = []
        self.finish_calls: list[dict[str, object]] = []

    def init(self, **kwargs):
        self.init_kwargs = dict(kwargs)
        return SimpleNamespace(id=self.run_id)

    def log(self, metrics, *, step: int) -> None:
        self.log_calls.append((dict(metrics), step))

    def finish(self, **kwargs) -> None:
        self.finish_calls.append(dict(kwargs))


def _formal_step_metrics(step: int = 1) -> dict[str, float]:
    return {
        "optimization_step": float(step),
        "generation_loss": 1.0,
        "state_loss": 0.5,
        "physics_loss": 0.25,
        "total_loss": 1.5025,
        "gradient_norm": 0.75,
        "nonfinite_count": 0.0,
    }


def test_swanlab_online_logger_records_required_step_metrics_and_finishes(
    tmp_path: Path,
) -> None:
    config = load_shared_b0_physics_training_config(CONFIG_PATH)
    output_dir = tmp_path / "formal-state-supervision"
    fake = _FakeSwanlab()
    binding = _binding()

    with shared_train.swanlab_online_training_run(
        config,
        "state_supervision",
        output_dir,
        binding,
        swanlab_module=fake,
    ) as logger:
        logger.log(_formal_step_metrics(), 1)

    assert fake.init_kwargs["project"] == "malicious-traffic-llm"
    assert fake.init_kwargs["workspace"] == "mortiswang"
    assert fake.init_kwargs["mode"] == "online"
    assert fake.init_kwargs["log_dir"] == str(output_dir / "swanlog/train")
    logged, step = fake.log_calls[0]
    assert step == 1
    assert logged["train/generation_loss"] == 1.0
    assert logged["train/state_loss"] == 0.5
    assert logged["train/physics_loss"] == 0.25
    assert logged["train/total_loss"] == 1.5025
    assert logged["train/gradient_norm"] == 0.75
    assert logged["train/nonfinite_count"] == 0.0
    assert logged["train/optimization_step"] == 1.0
    assert fake.finish_calls == [{}]
    record = json.loads((output_dir / "swanlab_run.json").read_text("utf-8"))
    assert record["status"] == "finished"
    assert record["last_completed_step"] == 1
    assert (output_dir / "swanlog/train").is_dir()


def test_swanlab_failure_finishes_as_crashed_and_keeps_local_record(
    tmp_path: Path,
) -> None:
    config = load_shared_b0_physics_training_config(CONFIG_PATH)
    output_dir = tmp_path / "formal-standard-pinn"
    fake = _FakeSwanlab("swan-failed-456")

    with pytest.raises(RuntimeError, match="训练失败"):
        with shared_train.swanlab_online_training_run(
            config,
            "standard_pinn",
            output_dir,
            _binding("standard_pinn"),
            swanlab_module=fake,
        ) as logger:
            logger.log(_formal_step_metrics(), 1)
            raise RuntimeError("训练失败")

    assert fake.finish_calls == [{"state": "crashed", "error": "训练失败"}]
    record = json.loads((output_dir / "swanlab_run.json").read_text("utf-8"))
    assert record["status"] == "crashed"
    assert record["last_completed_step"] == 1
    assert "训练失败" in record["failure"]
    assert (output_dir / "swanlog/train").is_dir()
