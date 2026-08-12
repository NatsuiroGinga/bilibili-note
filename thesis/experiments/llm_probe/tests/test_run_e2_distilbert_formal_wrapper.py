from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHELL_WRAPPER = PROJECT_ROOT / "scripts/run_e2_distilbert_formal.sh"
PYTHON_DRIVER = PROJECT_ROOT / "scripts/e2_distilbert_formal_driver.py"


def test_distilbert_formal_wrapper_freezes_protocol_model_and_runtime_contract() -> None:
    shell = SHELL_WRAPPER.read_text(encoding="utf-8")
    driver = PYTHON_DRIVER.read_text(encoding="utf-8")

    assert "uv run --no-sync python scripts/e2_distilbert_formal_driver.py" in shell
    assert "tqh-c2-v120-e1-dev-seed42-v1-20260806T092613Z/protocol" in shell
    assert "/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased" in shell
    assert "--model-binding-sha256" in shell
    assert 'PANEL = "abd_to_c"' in driver
    assert "SEED = 42" in driver
    assert "list(E2_FEATURE_FIELDS)" in driver
    assert 'mode="online"' in driver


def test_distilbert_formal_wrapper_persists_recovery_tracking_and_result_evidence() -> None:
    shell = SHELL_WRAPPER.read_text(encoding="utf-8")
    driver = PYTHON_DRIVER.read_text(encoding="utf-8")

    assert "interrupted_no_resumable_checkpoint" in shell
    assert "PIPESTATUS" in shell
    assert "model-binding.sha256" in shell
    assert "input.sha256" in shell
    assert "output.sha256" in shell
    assert "checkpoint-final/model.safetensors" in shell
    assert "artifact_manifest.json" in shell
    assert "swanlab.log(start_metrics, step=0)" in driver
    assert "swanlab.log(final_metrics" in driver
    assert '"predictions": results_dir / "predictions.jsonl"' in driver
