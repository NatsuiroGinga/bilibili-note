import pytest

from flow_probe.physics_validity import run_validity_checks


def test_run_validity_checks_proves_required_mathematical_properties() -> None:
    summary = run_validity_checks(device_name="cpu", seed=42)

    assert summary["device"] == "cpu"
    assert summary["exact_residual_max"] == pytest.approx(0.0, abs=1e-7)
    assert summary["corrupted_residual_mean"] > summary["exact_residual_mean"]
    assert summary["scale_invariance_abs_error"] == pytest.approx(0.0, abs=1e-7)
    assert summary["physics_gradient_norm"] > 0.0
    assert summary["checks_passed"] == 4
    assert summary["checks_total"] == 4
