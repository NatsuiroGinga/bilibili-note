"""共享 B0 两条物理基线的公开检测与训练拟合诊断薄封装。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import yaml

from flow_probe.config import ProbeConfig
from flow_probe.evaluate_model import (
    EvaluationSettings,
    build_evaluation_binding,
    build_evaluation_settings,
    evaluate_model,
    evaluation_binding_sha256,
)
from flow_probe.tracking import TrackingSettings

CONFIG_SCHEMA_VERSION = "flow_probe_shared_b0_physics_evaluation_config_v1"
WRAPPER_BINDING_SCHEMA_VERSION = "flow_probe_shared_b0_physics_evaluation_binding_v1"
PHYSICS_BINDING_SCHEMA_VERSION = "flow_probe_shared_b0_physics_fit_binding_v1"
PHYSICS_SUMMARY_SCHEMA_VERSION = "flow_probe_shared_b0_physics_fit_diagnostic_v1"
EVALUATION_SCOPE = "train_fit_diagnostic"
BASELINES = ("state_supervision", "standard_pinn")
DATASETS = ("genis", "tqhc2")
EXPECTED_MODEL_ID = "/root/autodl-tmp/thesis/models/Qwen3-1.7B"
EXPECTED_FEATURE_VIEW = "shared_b0_common_v1"
EXPECTED_CLASSIFICATION_TRAIN = Path(
    "runs/data-frozen/dataset-v1-shared-b0/candidate/qwen_train.jsonl"
)
EXPECTED_SIDECAR_ROOT = Path(
    "runs/data-frozen/dataset-v1-shared-b0-physics-v1"
)
EXPECTED_SIDECAR_FILE = EXPECTED_SIDECAR_ROOT / "candidate/ns3_physics_train.jsonl"
EXPECTED_SIDECAR_MANIFEST = EXPECTED_SIDECAR_ROOT / "dataset_manifest.json"
EXPECTED_RECORDS = 2421
EXPECTED_ANCHORS = 5
FORBIDDEN_PHYSICS_CLAIMS = (
    "未见物理测试",
    "外部物理泛化",
    "跨拓扑泛化",
    "对新拓扑有效",
    "对未见配置有效",
)


class SharedB0PhysicsEvaluationError(ValueError):
    """评估配置、训练制品或诊断合同不合法。"""


class PhysicsBatchPredictor(Protocol):
    """把一批普通分类记录与对应旁路转换为诊断行。"""

    def __call__(
        self,
        classification_records: Sequence[Mapping[str, object]],
        sidecar_records: Sequence[Mapping[str, object]],
    ) -> Sequence[Mapping[str, object]]: ...


@dataclass(frozen=True)
class TrainingArtifactPaths:
    """任务 03 单条完成运行的固定制品路径。"""

    run_dir: Path

    @property
    def adapter_dir(self) -> Path:
        return self.run_dir / "adapter"

    @property
    def state_head_file(self) -> Path:
        return self.run_dir / "state_head/state_head.pt"

    @property
    def state_head_metadata(self) -> Path:
        return self.run_dir / "state_head/metadata.json"

    @property
    def training_binding(self) -> Path:
        return self.run_dir / "training_binding.json"

    @property
    def artifact_manifest(self) -> Path:
        return self.run_dir / "artifact_manifest.json"

    @property
    def run_state(self) -> Path:
        return self.run_dir / "run_state.json"

    @property
    def train_summary(self) -> Path:
        return self.run_dir / "train_summary.json"


@dataclass(frozen=True)
class PhysicsDiagnosticSettings:
    """仅训练拟合用途的固定旁路与输出。"""

    evaluation_scope: str
    classification_train_file: Path
    sidecar_root: Path
    sidecar_file: Path
    dataset_manifest: Path
    output_file: Path
    batch_size: int

    @property
    def binding_file(self) -> Path:
        return self.output_file.with_name("physics_train_fit_binding.json")

    @property
    def progress_file(self) -> Path:
        return self.output_file.with_name("physics_train_fit_progress.json")

    @property
    def partial_file(self) -> Path:
        return self.output_file.with_name(
            "physics_train_fit_predictions.partial.jsonl"
        )


@dataclass(frozen=True)
class SharedB0PhysicsEvaluationConfig:
    """一条基线与一个公开清单的固定评估配置。"""

    config_path: Path
    config_sha256: str
    baseline: str
    dataset: str
    probe: ProbeConfig
    artifacts: TrainingArtifactPaths
    test_file: Path
    output_dir: Path
    evaluation_settings: EvaluationSettings
    physics: PhysicsDiagnosticSettings
    tracking: TrackingSettings
    raw: Mapping[str, object]


@dataclass(frozen=True)
class ValidatedTrainingArtifacts:
    """已通过任务 03 绑定和关键制品哈希验证的结果。"""

    training_binding: Mapping[str, object]
    training_binding_sha256: str
    training_binding_file_sha256: str
    artifact_manifest_file_sha256: str
    adapter_tree_sha256: str
    state_head_file_sha256: str
    state_head_metadata_file_sha256: str


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise SharedB0PhysicsEvaluationError(f"{description}必须是映射")
    return value


def _string(mapping: Mapping[str, object], key: str, description: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SharedB0PhysicsEvaluationError(f"{description}.{key} 必须是非空字符串")
    return value.strip()


def _integer(mapping: Mapping[str, object], key: str, description: str) -> int:
    value = mapping.get(key)
    if type(value) is not int:
        raise SharedB0PhysicsEvaluationError(f"{description}.{key} 必须是整数")
    return value


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise SharedB0PhysicsEvaluationError(f"无法读取制品：{path}") from error
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path, description: str) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SharedB0PhysicsEvaluationError(
            f"无法读取合法 {description}：{path}"
        ) from error
    if not isinstance(value, dict):
        raise SharedB0PhysicsEvaluationError(f"{description}顶层必须是对象")
    return value


def _read_jsonl(path: Path, description: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    try:
        with Path(path).open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise SharedB0PhysicsEvaluationError(
                        f"{description}第 {line_number} 行不是对象"
                    )
                rows.append(value)
    except (OSError, json.JSONDecodeError) as error:
        raise SharedB0PhysicsEvaluationError(
            f"无法读取合法 {description}：{path}"
        ) from error
    return rows


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as target:
            json.dump(
                value,
                target,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            target.write("\n")
            target.flush()
            os.fsync(target.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    text = "".join(
        json.dumps(
            dict(row),
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
        for row in rows
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as target:
            target.write(text)
            target.flush()
            os.fsync(target.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _expected_run_dir(baseline: str) -> Path:
    suffix = (
        "state-supervision" if baseline == "state_supervision" else "standard-pinn"
    )
    return Path(f"runs/baselines/shared-b0-qwen-{suffix}-seed42-200-v1")


def _expected_test_file(dataset: str) -> Path:
    filename = "genis_qwen.jsonl" if dataset == "genis" else "tqhc2_qwen.jsonl"
    return Path("runs/data-frozen/dataset-v1-shared-b0/validation") / filename


def _expected_config_id(baseline: str, dataset: str) -> str:
    baseline_name = baseline.replace("_", "-")
    return f"shared-b0-{baseline_name}-seed42-{dataset}-batch16-v1"


def load_shared_b0_physics_evaluation_config(
    path: Path,
) -> SharedB0PhysicsEvaluationConfig:
    """读取并拒绝任何偏离固定公开评估与训练拟合诊断的配置。"""
    path = Path(path)
    try:
        raw_value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise SharedB0PhysicsEvaluationError(f"无法读取评估配置：{path}") from error
    raw = _mapping(raw_value, "评估配置")
    if raw.get("schema_version") != CONFIG_SCHEMA_VERSION:
        raise SharedB0PhysicsEvaluationError("评估配置 schema_version 不匹配")
    if raw.get("status") != "review_pending":
        raise SharedB0PhysicsEvaluationError("评估配置状态必须是 review_pending")
    baseline = _string(raw, "baseline", "评估配置")
    if baseline not in BASELINES:
        raise SharedB0PhysicsEvaluationError("baseline 只允许两条共享 B0 物理基线")

    probe = ProbeConfig.from_mapping(_mapping(raw.get("probe"), "probe"))
    if (
        probe.model_id != EXPECTED_MODEL_ID
        or probe.feature_view != EXPECTED_FEATURE_VIEW
        or probe.seed != 42
        or probe.max_input_length != 512
        or probe.max_new_tokens != 16
    ):
        raise SharedB0PhysicsEvaluationError("模型、字段视图、种子或令牌上限偏离固定协议")

    training = _mapping(raw.get("training_artifacts"), "training_artifacts")
    run_dir = Path(_string(training, "run_dir", "training_artifacts"))
    if run_dir != _expected_run_dir(baseline):
        raise SharedB0PhysicsEvaluationError("训练运行目录与基线身份不匹配")

    public = _mapping(raw.get("public_evaluation"), "public_evaluation")
    dataset = _string(public, "dataset", "public_evaluation")
    if dataset not in DATASETS:
        raise SharedB0PhysicsEvaluationError("公开评估数据集只允许 genis 或 tqhc2")
    if raw.get("config_id") != _expected_config_id(baseline, dataset):
        raise SharedB0PhysicsEvaluationError("config_id 与基线和数据集不匹配")
    test_file = Path(_string(public, "test_file", "public_evaluation"))
    expected_test_file = _expected_test_file(dataset)
    if test_file != expected_test_file:
        raise SharedB0PhysicsEvaluationError("公开评估清单偏离冻结 GeNIS/TQH-C2 文件")
    output_dir = Path(_string(public, "output_dir", "public_evaluation"))
    expected_output = run_dir / f"evaluation-{dataset}-batch16-v1"
    if output_dir != expected_output:
        raise SharedB0PhysicsEvaluationError("公开评估输出目录与基线或清单不匹配")
    settings = build_evaluation_settings(public)
    if settings != EvaluationSettings(
        batch_size=16,
        length_bucket=False,
        flush_every_batches=1,
        resume=True,
        attention_backend="sdpa",
    ):
        raise SharedB0PhysicsEvaluationError("公开评估必须固定为批量16、无分桶、SDPA和批级恢复")

    physics_raw = _mapping(raw.get("physics_diagnostic"), "physics_diagnostic")
    physics = PhysicsDiagnosticSettings(
        evaluation_scope=_string(
            physics_raw, "evaluation_scope", "physics_diagnostic"
        ),
        classification_train_file=Path(
            _string(
                physics_raw,
                "classification_train_file",
                "physics_diagnostic",
            )
        ),
        sidecar_root=Path(
            _string(physics_raw, "sidecar_root", "physics_diagnostic")
        ),
        sidecar_file=Path(
            _string(physics_raw, "sidecar_file", "physics_diagnostic")
        ),
        dataset_manifest=Path(
            _string(physics_raw, "dataset_manifest", "physics_diagnostic")
        ),
        output_file=Path(
            _string(physics_raw, "output_file", "physics_diagnostic")
        ),
        batch_size=_integer(physics_raw, "batch_size", "physics_diagnostic"),
    )
    if (
        physics.evaluation_scope != EVALUATION_SCOPE
        or physics.classification_train_file != EXPECTED_CLASSIFICATION_TRAIN
        or physics.sidecar_root != EXPECTED_SIDECAR_ROOT
        or physics.sidecar_file != EXPECTED_SIDECAR_FILE
        or physics.dataset_manifest != EXPECTED_SIDECAR_MANIFEST
        or physics.output_file != run_dir / "physics_train_fit_diagnostic.json"
        or physics.batch_size != 16
    ):
        raise SharedB0PhysicsEvaluationError("物理诊断必须严格绑定训练拟合集和批量16")

    tracking = TrackingSettings.from_mapping(
        _mapping(raw.get("tracking"), "tracking")
    )
    return SharedB0PhysicsEvaluationConfig(
        config_path=path,
        config_sha256=_file_sha256(path),
        baseline=baseline,
        dataset=dataset,
        probe=probe,
        artifacts=TrainingArtifactPaths(run_dir),
        test_file=test_file,
        output_dir=output_dir,
        evaluation_settings=settings,
        physics=physics,
        tracking=tracking,
        raw=dict(raw),
    )


def _adapter_manifest(adapter_dir: Path) -> list[dict[str, object]]:
    if not adapter_dir.is_dir() or adapter_dir.is_symlink():
        raise SharedB0PhysicsEvaluationError("LoRA 适配器目录不存在或为符号链接")
    files = sorted(path for path in adapter_dir.rglob("*") if path.is_file())
    if not files:
        raise SharedB0PhysicsEvaluationError("LoRA 适配器目录为空")
    if any(path.is_symlink() for path in files):
        raise SharedB0PhysicsEvaluationError("LoRA 适配器目录不得包含符号链接")
    return [
        {
            "path": path.relative_to(adapter_dir).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _file_sha256(path),
        }
        for path in files
    ]


def _artifact_index(manifest: Mapping[str, object]) -> Mapping[str, Mapping[str, object]]:
    raw_entries = manifest.get("artifacts")
    if not isinstance(raw_entries, list):
        raise SharedB0PhysicsEvaluationError("训练制品清单缺少 artifacts")
    index: dict[str, Mapping[str, object]] = {}
    for value in raw_entries:
        entry = _mapping(value, "训练制品条目")
        relative = _string(entry, "path", "训练制品条目")
        if relative in index:
            raise SharedB0PhysicsEvaluationError(f"训练制品清单路径重复：{relative}")
        index[relative] = entry
    return index


def _verify_manifest_file(
    run_dir: Path,
    index: Mapping[str, Mapping[str, object]],
    relative: str,
) -> None:
    entry = index.get(relative)
    if entry is None:
        raise SharedB0PhysicsEvaluationError(f"训练制品清单缺少：{relative}")
    path = run_dir / relative
    if not path.is_file() or path.is_symlink():
        raise SharedB0PhysicsEvaluationError(f"训练制品不存在或为符号链接：{relative}")
    if entry.get("bytes") != path.stat().st_size or entry.get("sha256") != _file_sha256(
        path
    ):
        raise SharedB0PhysicsEvaluationError(f"训练制品哈希或字节数变化：{relative}")


def _verify_bound_file(path_value: object, expected_sha256: object, name: str) -> None:
    if not isinstance(path_value, str) or not isinstance(expected_sha256, str):
        raise SharedB0PhysicsEvaluationError(f"训练绑定缺少 {name} 路径或哈希")
    path = Path(path_value)
    if not path.is_file() or _file_sha256(path) != expected_sha256:
        raise SharedB0PhysicsEvaluationError(f"训练绑定的 {name} 文件或哈希变化")


def validate_training_artifacts(
    config: SharedB0PhysicsEvaluationConfig,
) -> ValidatedTrainingArtifacts:
    """验证完成状态、训练绑定、关键模型制品和全部绑定数据哈希。"""
    artifacts = config.artifacts
    required = (
        artifacts.training_binding,
        artifacts.artifact_manifest,
        artifacts.run_state,
        artifacts.train_summary,
        artifacts.state_head_file,
        artifacts.state_head_metadata,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SharedB0PhysicsEvaluationError(f"训练制品缺失：{', '.join(missing)}")

    binding = _read_json(artifacts.training_binding, "训练绑定")
    binding_sha256 = binding.get("binding_sha256")
    if not isinstance(binding_sha256, str) or binding_sha256 != _canonical_sha256(
        {key: value for key, value in binding.items() if key != "binding_sha256"}
    ):
        raise SharedB0PhysicsEvaluationError("训练绑定自身哈希不一致")
    expected_lambda = 0.0 if config.baseline == "state_supervision" else 0.01
    if (
        binding.get("baseline") != config.baseline
        or binding.get("lambda_state") != 1.0
        or binding.get("lambda_physics") != expected_lambda
        or binding.get("max_steps") != 200
        or binding.get("physics_records") != EXPECTED_RECORDS
        or binding.get("physics_usage") != EVALUATION_SCOPE
    ):
        raise SharedB0PhysicsEvaluationError("训练绑定的基线、权重或固定协议不匹配")

    run_state = _read_json(artifacts.run_state, "运行状态")
    train_summary = _read_json(artifacts.train_summary, "训练摘要")
    if (
        run_state.get("status") != "completed"
        or run_state.get("binding_sha256") != binding_sha256
        or run_state.get("optimization_step") != 200
        or train_summary.get("status") != "completed"
        or train_summary.get("binding_sha256") != binding_sha256
        or train_summary.get("optimization_step") != 200
        or train_summary.get("generation_records") != 800
        or train_summary.get("physics_records") != EXPECTED_RECORDS
        or train_summary.get("nonfinite_count") != 0
    ):
        raise SharedB0PhysicsEvaluationError("训练运行尚未按固定协议完整完成")

    manifest = _read_json(artifacts.artifact_manifest, "训练制品清单")
    if manifest.get("status") != "completed" or manifest.get(
        "binding_sha256"
    ) != binding_sha256:
        raise SharedB0PhysicsEvaluationError("训练制品清单状态或绑定不一致")
    index = _artifact_index(manifest)
    for relative in (
        "training_binding.json",
        "state_head/state_head.pt",
        "state_head/metadata.json",
    ):
        _verify_manifest_file(artifacts.run_dir, index, relative)
    adapter_manifest = _adapter_manifest(artifacts.adapter_dir)
    for entry in adapter_manifest:
        _verify_manifest_file(
            artifacts.run_dir,
            index,
            f"adapter/{entry['path']}",
        )

    state_metadata = _read_json(artifacts.state_head_metadata, "状态头元数据")
    if (
        state_metadata.get("binding_sha256") != binding_sha256
        or state_metadata.get("initialization_sha256")
        != binding.get("state_head_initialization_sha256")
    ):
        raise SharedB0PhysicsEvaluationError("状态头元数据与训练绑定不一致")

    base = _mapping(binding.get("base_training_binding"), "普通 Qwen 训练绑定")
    _verify_bound_file(
        base.get("train_file"),
        binding.get("classification_train_sha256"),
        "分类训练",
    )
    _verify_bound_file(
        base.get("validation_file"),
        binding.get("classification_validation_sha256"),
        "分类验证",
    )
    _verify_bound_file(
        str(config.physics.sidecar_file),
        binding.get("physics_sidecar_sha256"),
        "物理旁路",
    )
    _verify_bound_file(
        str(config.physics.dataset_manifest),
        binding.get("physics_dataset_manifest_sha256"),
        "物理旁路清单",
    )

    return ValidatedTrainingArtifacts(
        training_binding=binding,
        training_binding_sha256=binding_sha256,
        training_binding_file_sha256=_file_sha256(artifacts.training_binding),
        artifact_manifest_file_sha256=_file_sha256(artifacts.artifact_manifest),
        adapter_tree_sha256=_canonical_sha256(adapter_manifest),
        state_head_file_sha256=_file_sha256(artifacts.state_head_file),
        state_head_metadata_file_sha256=_file_sha256(
            artifacts.state_head_metadata
        ),
    )


def build_public_evaluation_wrapper_binding(
    config: SharedB0PhysicsEvaluationConfig,
    artifacts: ValidatedTrainingArtifacts,
    records: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """在原评估绑定外补充训练制品、基线和数据哈希。"""
    public_binding = build_evaluation_binding(
        config.probe,
        config.evaluation_settings,
        config.test_file,
        records,
        config.artifacts.adapter_dir,
    )
    value = {
        "schema_version": WRAPPER_BINDING_SCHEMA_VERSION,
        "evaluation_scope": "public_detection",
        "baseline": config.baseline,
        "dataset": config.dataset,
        "config_sha256": config.config_sha256,
        "training_binding_sha256": artifacts.training_binding_sha256,
        "training_binding_file_sha256": artifacts.training_binding_file_sha256,
        "artifact_manifest_file_sha256": artifacts.artifact_manifest_file_sha256,
        "adapter_tree_sha256": artifacts.adapter_tree_sha256,
        "state_head_file_sha256": artifacts.state_head_file_sha256,
        "state_head_metadata_file_sha256": (
            artifacts.state_head_metadata_file_sha256
        ),
        "classification_train_sha256": artifacts.training_binding[
            "classification_train_sha256"
        ],
        "classification_validation_sha256": artifacts.training_binding[
            "classification_validation_sha256"
        ],
        "physics_sidecar_sha256": artifacts.training_binding[
            "physics_sidecar_sha256"
        ],
        "physics_dataset_manifest_sha256": artifacts.training_binding[
            "physics_dataset_manifest_sha256"
        ],
        "evaluation_test_file_sha256": _file_sha256(config.test_file),
        "public_evaluation_binding": public_binding,
        "public_evaluation_binding_sha256": evaluation_binding_sha256(
            public_binding
        ),
        "wrapper_code_sha256": _file_sha256(Path(__file__)),
    }
    return {**value, "binding_sha256": _canonical_sha256(value)}


def _validate_existing_binding(path: Path, expected: Mapping[str, object]) -> None:
    stored = _read_json(path, "评估薄封装绑定")
    if stored != dict(expected):
        differing = sorted(
            key
            for key in set(stored) | set(expected)
            if stored.get(key) != expected.get(key)
        )
        raise SharedB0PhysicsEvaluationError(
            f"评估薄封装绑定不一致：{', '.join(differing)}"
        )


def run_public_detection_evaluation(
    config: SharedB0PhysicsEvaluationConfig,
    *,
    evaluator: Callable[..., Mapping[str, object]] = evaluate_model,
) -> dict[str, object]:
    """验证训练与清单哈希后，原样调用既有可恢复公开评估器。"""
    validated = validate_training_artifacts(config)
    records = _read_jsonl(config.test_file, "公开评估清单")
    binding = build_public_evaluation_wrapper_binding(config, validated, records)
    wrapper_binding_path = config.output_dir / "shared_b0_evaluation_binding.json"
    result_path = config.output_dir / "shared_b0_evaluation_result.json"

    if result_path.is_file():
        if not wrapper_binding_path.is_file():
            raise SharedB0PhysicsEvaluationError("已完成评估缺少薄封装绑定")
        _validate_existing_binding(wrapper_binding_path, binding)
        result = _read_json(result_path, "公开评估完成结果")
        progress = _read_json(
            config.output_dir / "evaluation_progress.json", "公开评估进度"
        )
        if (
            result.get("status") != "completed"
            or result.get("binding_sha256") != binding["binding_sha256"]
            or progress.get("status") != "finished"
            or not (config.output_dir / "evaluation_summary.json").is_file()
            or not (config.output_dir / "predictions.jsonl").is_file()
        ):
            raise SharedB0PhysicsEvaluationError("公开评估完成制品不完整")
        return {**result, "idempotent": True}

    if wrapper_binding_path.is_file():
        _validate_existing_binding(wrapper_binding_path, binding)
    else:
        if config.output_dir.exists() and any(config.output_dir.iterdir()):
            raise SharedB0PhysicsEvaluationError("公开评估目录非空且缺少薄封装绑定")
        _atomic_write_json(wrapper_binding_path, binding)

    summary = dict(
        evaluator(
            probe=config.probe,
            test_file=config.test_file,
            output_dir=config.output_dir,
            adapter_path=config.artifacts.adapter_dir,
            tracking=config.tracking,
            settings=config.evaluation_settings,
        )
    )
    public_binding = _read_json(
        config.output_dir / "evaluation_binding.json", "公共评估绑定"
    )
    if public_binding != binding["public_evaluation_binding"]:
        raise SharedB0PhysicsEvaluationError("公共评估器实际绑定与预检绑定不一致")
    progress = _read_json(
        config.output_dir / "evaluation_progress.json", "公共评估进度"
    )
    if progress.get("status") != "finished":
        raise SharedB0PhysicsEvaluationError("公共评估器未完成全部批次")
    result = {
        "schema_version": "flow_probe_shared_b0_public_evaluation_result_v1",
        "status": "completed",
        "evaluation_scope": "public_detection",
        "baseline": config.baseline,
        "dataset": config.dataset,
        "binding_sha256": binding["binding_sha256"],
        "public_evaluation_binding_sha256": binding[
            "public_evaluation_binding_sha256"
        ],
        "evaluation_summary_sha256": _file_sha256(
            config.output_dir / "evaluation_summary.json"
        ),
        "predictions_sha256": _file_sha256(
            config.output_dir / "predictions.jsonl"
        ),
        "summary": summary,
        "idempotent": False,
    }
    _atomic_write_json(result_path, result)
    return result


def _physics_binding(
    config: SharedB0PhysicsEvaluationConfig,
    artifacts: ValidatedTrainingArtifacts,
    sidecar_records: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    sample_ids = [str(record.get("sample_id", "")) for record in sidecar_records]
    value = {
        "schema_version": PHYSICS_BINDING_SCHEMA_VERSION,
        "evaluation_scope": EVALUATION_SCOPE,
        "baseline": config.baseline,
        "training_binding_sha256": artifacts.training_binding_sha256,
        "adapter_tree_sha256": artifacts.adapter_tree_sha256,
        "state_head_file_sha256": artifacts.state_head_file_sha256,
        "state_head_metadata_file_sha256": (
            artifacts.state_head_metadata_file_sha256
        ),
        "classification_train_sha256": _file_sha256(
            config.physics.classification_train_file
        ),
        "physics_sidecar_sha256": _file_sha256(config.physics.sidecar_file),
        "physics_dataset_manifest_sha256": _file_sha256(
            config.physics.dataset_manifest
        ),
        "sample_order_sha256": _canonical_sha256(sample_ids),
        "record_count": len(sidecar_records),
        "batch_size": config.physics.batch_size,
        "wrapper_code_sha256": _file_sha256(Path(__file__)),
    }
    return {**value, "binding_sha256": _canonical_sha256(value)}


def _prepare_physics_records(
    config: SharedB0PhysicsEvaluationConfig,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    from flow_probe.shared_b0_physics_sidecar import (
        validate_shared_b0_physics_sidecar,
    )

    validate_shared_b0_physics_sidecar(
        config.physics.sidecar_root,
        config.physics.classification_train_file,
    )
    classification = _read_jsonl(
        config.physics.classification_train_file, "分类训练清单"
    )
    sidecar = _read_jsonl(config.physics.sidecar_file, "物理旁路")
    if len(sidecar) != EXPECTED_RECORDS:
        raise SharedB0PhysicsEvaluationError("训练拟合物理旁路必须恰有 2421 条")
    classification_by_id: dict[str, dict[str, object]] = {}
    for record in classification:
        sample_id = record.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id:
            raise SharedB0PhysicsEvaluationError("分类训练记录缺少 sample_id")
        if sample_id in classification_by_id:
            raise SharedB0PhysicsEvaluationError(f"分类训练 sample_id 重复：{sample_id}")
        classification_by_id[sample_id] = record

    def order_key(record: Mapping[str, object]) -> tuple[int, str]:
        stable_order = record.get("stable_order")
        sample_id = record.get("sample_id")
        if type(stable_order) is not int or not isinstance(sample_id, str):
            raise SharedB0PhysicsEvaluationError("物理旁路缺少稳定顺序或 sample_id")
        return stable_order, sample_id

    ordered_sidecar = sorted(sidecar, key=order_key)
    sample_ids = [str(record["sample_id"]) for record in ordered_sidecar]
    if len(sample_ids) != len(set(sample_ids)):
        raise SharedB0PhysicsEvaluationError("物理旁路 sample_id 重复")
    missing = [sample_id for sample_id in sample_ids if sample_id not in classification_by_id]
    if missing:
        raise SharedB0PhysicsEvaluationError(f"分类训练清单缺少旁路标识：{missing[0]}")
    joined = [classification_by_id[sample_id] for sample_id in sample_ids]
    return joined, ordered_sidecar


def _finite_metric(values: Sequence[float], *, square: bool) -> float | None:
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return None
    if square:
        return sum(value * value for value in finite) / len(finite)
    return sum(abs(value) for value in finite) / len(finite)


def _summarize_physics_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    include_groups: bool,
) -> dict[str, object]:
    if not rows:
        raise SharedB0PhysicsEvaluationError("物理诊断行不能为空")
    state_errors: list[float] = []
    supervised_errors: list[float] = []
    anchor_errors: list[list[float]] = [[] for _ in range(EXPECTED_ANCHORS)]
    residuals: list[float] = []
    valid_state_elements = 0
    nonfinite_count = 0
    groups: dict[str, list[Mapping[str, object]]] = {}
    seen: set[str] = set()

    for row in rows:
        sample_id = row.get("sample_id")
        group_id = row.get("group_id")
        if not isinstance(sample_id, str) or not sample_id or sample_id in seen:
            raise SharedB0PhysicsEvaluationError("物理诊断 sample_id 缺失或重复")
        if not isinstance(group_id, str) or not group_id:
            raise SharedB0PhysicsEvaluationError("物理诊断 group_id 缺失")
        predicted = row.get("predicted_state")
        targets = row.get("state_targets")
        mask = row.get("state_mask_inputs")
        residual = row.get("queue_balance_residual")
        if (
            not isinstance(predicted, list)
            or not isinstance(targets, list)
            or not isinstance(mask, list)
            or not isinstance(residual, list)
            or len(predicted) != EXPECTED_ANCHORS
            or len(targets) != EXPECTED_ANCHORS
            or len(mask) != EXPECTED_ANCHORS
            or len(residual) != EXPECTED_ANCHORS - 1
            or any(type(value) is not bool for value in mask)
        ):
            raise SharedB0PhysicsEvaluationError("物理诊断行的五锚点或四窗口合同不合法")
        if mask[0] is not True or sum(mask) != 2:
            raise SharedB0PhysicsEvaluationError("物理诊断掩码不是 anchor0_plus_one")
        for anchor, (predicted_value, target_value, observed) in enumerate(
            zip(predicted, targets, mask, strict=True)
        ):
            if (
                not isinstance(predicted_value, (int, float))
                or isinstance(predicted_value, bool)
                or not isinstance(target_value, (int, float))
                or isinstance(target_value, bool)
            ):
                raise SharedB0PhysicsEvaluationError("状态预测和目标必须是数值")
            error = float(predicted_value) - float(target_value)
            if not math.isfinite(error):
                nonfinite_count += 1
            state_errors.append(error)
            anchor_errors[anchor].append(error)
            if observed:
                supervised_errors.append(error)
                valid_state_elements += 1
        for value in residual:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise SharedB0PhysicsEvaluationError("队列平衡残差必须是数值")
            number = float(value)
            if not math.isfinite(number):
                nonfinite_count += 1
            residuals.append(number)
        seen.add(sample_id)
        groups.setdefault(group_id, []).append(row)

    summary: dict[str, object] = {
        "evaluation_scope": EVALUATION_SCOPE,
        "sample_count": len(rows),
        "group_count": len(groups),
        "state_mse": _finite_metric(state_errors, square=True),
        "state_mae": _finite_metric(state_errors, square=False),
        "supervised_state_mse": _finite_metric(supervised_errors, square=True),
        "supervised_state_mae": _finite_metric(supervised_errors, square=False),
        "state_by_anchor": [
            {
                "anchor_index": index,
                "mse": _finite_metric(values, square=True),
                "mae": _finite_metric(values, square=False),
                "element_count": len(values),
            }
            for index, values in enumerate(anchor_errors)
        ],
        "mask_coverage": valid_state_elements / (len(rows) * EXPECTED_ANCHORS),
        "valid_state_elements": valid_state_elements,
        "total_state_elements": len(rows) * EXPECTED_ANCHORS,
        "queue_balance_residual_mse": _finite_metric(residuals, square=True),
        "queue_balance_residual_elements": len(residuals),
        "nonfinite_count": nonfinite_count,
    }
    if include_groups:
        summary["groups"] = {
            group_id: _summarize_physics_rows(group_rows, include_groups=False)
            for group_id, group_rows in sorted(groups.items())
        }
    return summary


def summarize_physics_diagnostic_rows(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """汇总训练拟合状态、掩码、残差与逐组指标。"""
    return _summarize_physics_rows(rows, include_groups=True)


def validate_physics_diagnostic_claims(value: object) -> None:
    """拒绝把训练拟合诊断包装成未见物理或跨拓扑结论。"""
    if isinstance(value, str):
        found = [phrase for phrase in FORBIDDEN_PHYSICS_CLAIMS if phrase in value]
        if found:
            raise SharedB0PhysicsEvaluationError(
                f"训练拟合诊断包含禁止表述：{', '.join(found)}"
            )
    elif isinstance(value, Mapping):
        for key, item in value.items():
            validate_physics_diagnostic_claims(key)
            validate_physics_diagnostic_claims(item)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for item in value:
            validate_physics_diagnostic_claims(item)


def _restore_physics_rows(
    path: Path,
    expected_sample_ids: Sequence[str],
) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    rows = _read_jsonl(path, "物理诊断部分预测")
    if len(rows) > len(expected_sample_ids):
        raise SharedB0PhysicsEvaluationError("物理诊断部分预测超过绑定记录数")
    for index, row in enumerate(rows):
        if row.get("sample_id") != expected_sample_ids[index]:
            raise SharedB0PhysicsEvaluationError("物理诊断恢复顺序与绑定不一致")
    return rows


def _build_torch_physics_predictor(
    config: SharedB0PhysicsEvaluationConfig,
    artifacts: ValidatedTrainingArtifacts,
) -> PhysicsBatchPredictor:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    from flow_probe.physics_train import ContinuousQueueStateHead, queue_balance_residual
    from flow_probe.qwen_physics_gradient import select_last_token_hidden
    from flow_probe.shared_b0_physics_train import (
        build_auxiliary_tensor_batch,
        build_state_prompt_texts,
        parameter_tree_sha256,
    )

    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("训练拟合物理诊断需要支持 BF16 的 CUDA GPU")
    tokenizer_source = (
        config.artifacts.adapter_dir
        if (config.artifacts.adapter_dir / "tokenizer_config.json").is_file()
        else config.probe.model_id
    )
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_source, use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    base_model = AutoModelForCausalLM.from_pretrained(
        config.probe.model_id,
        quantization_config=quantization,
        dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation="sdpa",
    )
    model = PeftModel.from_pretrained(
        base_model,
        str(config.artifacts.adapter_dir),
        is_trainable=False,
    )
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    model.config.use_cache = True
    model.eval()
    device = next(
        parameter.device
        for parameter in model.parameters()
        if parameter.device.type != "meta"
    )
    hidden_size = int(getattr(model.config, "hidden_size", 0))
    if hidden_size <= 0:
        raise SharedB0PhysicsEvaluationError("模型缺少状态头隐藏维度")
    state_head = ContinuousQueueStateHead(hidden_size).to(
        device=device,
        dtype=torch.bfloat16,
    )
    state = torch.load(
        config.artifacts.state_head_file,
        map_location="cpu",
        weights_only=True,
    )
    state_head.load_state_dict(state, strict=True)
    metadata = _read_json(config.artifacts.state_head_metadata, "状态头元数据")
    if parameter_tree_sha256(state_head) != metadata.get(
        "final_parameter_tree_sha256"
    ):
        raise SharedB0PhysicsEvaluationError("状态头参数树哈希与元数据不一致")
    if metadata.get("binding_sha256") != artifacts.training_binding_sha256:
        raise SharedB0PhysicsEvaluationError("状态头绑定哈希变化")
    state_head.eval()

    def predict(
        classification_records: Sequence[Mapping[str, object]],
        sidecar_records: Sequence[Mapping[str, object]],
    ) -> Sequence[Mapping[str, object]]:
        prompts = build_state_prompt_texts(classification_records, tokenizer)
        encoded = tokenizer(
            prompts,
            padding=True,
            truncation=True,
            max_length=config.probe.max_input_length,
            add_special_tokens=False,
            return_tensors="pt",
        )
        input_ids = encoded["input_ids"].to(device)
        attention_mask = encoded["attention_mask"].to(device)
        with torch.inference_mode():
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_hidden_states=True,
                return_dict=True,
            )
            hidden_states = getattr(outputs, "hidden_states", None)
            if not hidden_states:
                raise SharedB0PhysicsEvaluationError("模型没有返回隐藏状态")
            hidden = select_last_token_hidden(hidden_states[-1], attention_mask)
            predicted = state_head(hidden).float()
            tensors = build_auxiliary_tensor_batch(
                sidecar_records,
                "standard_pinn",
                device,
            )
            residual = queue_balance_residual(
                predicted,
                tensors.scale,
                tensors.capacity,
                tensors.received,
                tensors.dequeued,
                tensors.dropped_before,
                tensors.dropped_after,
            ).float()
        predicted_values = predicted.cpu().tolist()
        residual_values = residual.cpu().tolist()
        rows: list[dict[str, object]] = []
        for raw, predicted_row, residual_row in zip(
            sidecar_records,
            predicted_values,
            residual_values,
            strict=True,
        ):
            rows.append(
                {
                    "sample_id": raw.get("sample_id"),
                    "group_id": raw.get("group_id"),
                    "predicted_state": predicted_row,
                    "state_targets": raw.get("state_targets"),
                    "state_mask_inputs": raw.get("state_mask_inputs"),
                    "queue_balance_residual": residual_row,
                }
            )
        return rows

    return predict


def run_physics_fit_diagnostic(
    config: SharedB0PhysicsEvaluationConfig,
    *,
    predictor: PhysicsBatchPredictor | None = None,
) -> dict[str, object]:
    """按固定批次可恢复地评估训练拟合状态和队列残差。"""
    validated = validate_training_artifacts(config)
    classification, sidecar = _prepare_physics_records(config)
    binding = _physics_binding(config, validated, sidecar)
    paths = config.physics
    expected_sample_ids = [str(record["sample_id"]) for record in sidecar]

    if paths.output_file.is_file():
        if not paths.binding_file.is_file():
            raise SharedB0PhysicsEvaluationError("已完成物理诊断缺少绑定")
        _validate_existing_binding(paths.binding_file, binding)
        summary = _read_json(paths.output_file, "训练拟合物理诊断")
        if (
            summary.get("status") != "completed"
            or summary.get("evaluation_scope") != EVALUATION_SCOPE
            or summary.get("binding_sha256") != binding["binding_sha256"]
        ):
            raise SharedB0PhysicsEvaluationError("训练拟合物理诊断完成制品不合法")
        validate_physics_diagnostic_claims(summary)
        return {**summary, "idempotent": True}

    if paths.binding_file.is_file():
        _validate_existing_binding(paths.binding_file, binding)
    else:
        if paths.partial_file.exists() or paths.progress_file.exists():
            raise SharedB0PhysicsEvaluationError("物理诊断部分制品缺少绑定")
        _atomic_write_json(paths.binding_file, binding)
        _atomic_write_jsonl(paths.partial_file, [])
    rows = _restore_physics_rows(paths.partial_file, expected_sample_ids)
    _atomic_write_json(
        paths.progress_file,
        {
            "status": "running" if rows else "prepared",
            "evaluation_scope": EVALUATION_SCOPE,
            "binding_sha256": binding["binding_sha256"],
            "completed_samples": len(rows),
            "total_samples": len(sidecar),
        },
    )
    active_predictor = predictor or _build_torch_physics_predictor(config, validated)
    for start in range(len(rows), len(sidecar), paths.batch_size):
        stop = min(start + paths.batch_size, len(sidecar))
        batch_rows = list(
            active_predictor(classification[start:stop], sidecar[start:stop])
        )
        if len(batch_rows) != stop - start:
            raise SharedB0PhysicsEvaluationError("物理诊断预测批次行数不一致")
        for offset, row in enumerate(batch_rows):
            if row.get("sample_id") != expected_sample_ids[start + offset]:
                raise SharedB0PhysicsEvaluationError("物理诊断预测批次顺序不一致")
        rows.extend(dict(row) for row in batch_rows)
        _atomic_write_jsonl(paths.partial_file, rows)
        _atomic_write_json(
            paths.progress_file,
            {
                "status": "running",
                "evaluation_scope": EVALUATION_SCOPE,
                "binding_sha256": binding["binding_sha256"],
                "completed_samples": len(rows),
                "total_samples": len(sidecar),
            },
        )

    metrics = summarize_physics_diagnostic_rows(rows)
    summary = {
        "schema_version": PHYSICS_SUMMARY_SCHEMA_VERSION,
        "status": "completed",
        "evaluation_scope": EVALUATION_SCOPE,
        "baseline": config.baseline,
        "binding_sha256": binding["binding_sha256"],
        "training_binding_sha256": validated.training_binding_sha256,
        "metrics": metrics,
        "idempotent": False,
    }
    validate_physics_diagnostic_claims(summary)
    _atomic_write_json(paths.output_file, summary)
    _atomic_write_json(
        paths.progress_file,
        {
            "status": "finished",
            "evaluation_scope": EVALUATION_SCOPE,
            "binding_sha256": binding["binding_sha256"],
            "completed_samples": len(rows),
            "total_samples": len(sidecar),
        },
    )
    return summary


def preflight_evaluation(
    config: SharedB0PhysicsEvaluationConfig,
    mode: str,
) -> dict[str, object]:
    """在加载模型前验证训练制品、数据清单和目标绑定。"""
    validated = validate_training_artifacts(config)
    if mode == "public_detection":
        records = _read_jsonl(config.test_file, "公开评估清单")
        binding = build_public_evaluation_wrapper_binding(
            config,
            validated,
            records,
        )
        records_count = len(records)
    elif mode == "physics_fit":
        _, sidecar = _prepare_physics_records(config)
        binding = _physics_binding(config, validated, sidecar)
        records_count = len(sidecar)
    else:
        raise SharedB0PhysicsEvaluationError("mode 只允许 public_detection 或 physics_fit")
    return {
        "status": "passed",
        "mode": mode,
        "baseline": config.baseline,
        "dataset": config.dataset if mode == "public_detection" else None,
        "records": records_count,
        "binding_sha256": binding["binding_sha256"],
        "training_binding_sha256": validated.training_binding_sha256,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="共享 B0 公开检测与训练拟合物理诊断"
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=("public_detection", "physics_fit"),
        required=True,
    )
    parser.add_argument("--preflight-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = load_shared_b0_physics_evaluation_config(args.config)
    if args.preflight_only:
        result = preflight_evaluation(config, args.mode)
    elif args.mode == "public_detection":
        result = run_public_detection_evaluation(config)
    else:
        result = run_physics_fit_diagnostic(config)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
