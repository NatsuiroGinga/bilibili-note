"""R2 训练侧车数据的精确同步白名单合同。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

from guarded_execution_common import GuardViolation  # noqa: E402
from guarded_rsync import build_sync_plan  # noqa: E402


AUTHORIZED_SIDECARS = (
    "runs/data-prepared/r2-final-sidecar-candidate-v1/common-history.parquet",
    "runs/data-prepared/r2-final-sidecar-candidate-v1/route-assignments.parquet",
)


@pytest.mark.parametrize("source", AUTHORIZED_SIDECARS)
def test_exact_training_sidecar_is_allowed(source: str) -> None:
    plan = build_sync_plan(source, source)
    assert plan.source_relative == source
    assert plan.destination_relative == source


def test_training_sidecar_cannot_be_renamed_remotely() -> None:
    with pytest.raises(GuardViolation):
        build_sync_plan(AUTHORIZED_SIDECARS[0], "runs/data-prepared/renamed.parquet")
