"""任务05 Shell 正式包装器的后置结构合同。"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = PROJECT_ROOT / "scripts/run_r2_ns3_protocol_matrix.sh"


def test_wrapper_is_cpu_only_and_uses_controlled_json() -> None:
    source = WRAPPER.read_text(encoding="utf-8")
    assert "if [[ $# -ne 1 ]]" in source
    assert "--params \"$PARAMS_PATH\"" in source
    assert 'export CUDA_VISIBLE_DEVICES=""' in source
    assert "export SWANLAB_MODE=disabled" in source
    assert "nvidia-smi" not in source
    assert "swanlab" not in source.lower().replace("swanlab_mode", "")


def test_wrapper_loads_bashrc_before_nounset() -> None:
    source = WRAPPER.read_text(encoding="utf-8")
    assert source.index("source ~/.bashrc") < source.index("set -u")
    assert "uv run --no-sync python -m flow_probe.r2_ns3_protocol_runner" in source
