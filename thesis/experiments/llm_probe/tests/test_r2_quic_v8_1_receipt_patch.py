#!/usr/bin/env python3
"""验证 QUIC v8.1 aioquic 节奏收据补丁的三条冻结时间语义。"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_PROTOCOL = (
    PROJECT_ROOT
    / "runs/tools/r2-quic-controlled-v6/aioquic-overlay/aioquic/asyncio/protocol.py"
)
PATCH_PATH = PROJECT_ROOT / "scripts/r2_quic_v8_1_aioquic_receipt.patch"


def patched_protocol_source() -> str:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        target = root / "aioquic/asyncio/protocol.py"
        target.parent.mkdir(parents=True)
        shutil.copy2(BASE_PROTOCOL, target)
        subprocess.run(
            ["patch", "--batch", "--forward", "-p1", "-i", str(PATCH_PATH)],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        return target.read_text(encoding="utf-8")


def test_actual_timestamp_is_sampled_after_sendto() -> None:
    source = patched_protocol_source()
    send_index = source.index("self._transport.sendto(data, addr)")
    actual_index = source.index("actual_at = self._loop.time()", send_index)
    receipt_index = source.index('"actual_monotonic_ns"', actual_index)
    assert send_index < actual_index < receipt_index


def test_future_pacing_request_does_not_bind_immediate_datagram() -> None:
    source = patched_protocol_source()
    assert "pacing_due = requested_at is not None and requested_at <= invocation_at" in source
    assert "planned_at = requested_at if pacing_due else send_started_at" in source
    assert '"pacing_requested": pacing_due' in source


def test_lateness_is_exact_same_clock_difference() -> None:
    source = patched_protocol_source()
    assert "planned_monotonic_ns = round(planned_at * 1_000_000_000)" in source
    assert "actual_monotonic_ns = round(actual_at * 1_000_000_000)" in source
    expected = '"lateness_ns": actual_monotonic_ns - planned_monotonic_ns'
    assert expected in source
    assert '"lateness_ns": max(0,' not in source
