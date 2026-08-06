"""R2 最终旁路包装器的最小运行合同。"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = PROJECT_ROOT / "scripts/run_r2_final_probe.sh"


def test_wrapper_disables_uv_automatic_sync() -> None:
    source = WRAPPER.read_text(encoding="utf-8")
    assert "uv run --no-sync python -m flow_probe.r2_final_distilbert_probe" in source
