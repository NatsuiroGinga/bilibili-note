#!/usr/bin/env python3
"""验证 QUIC v6 的 aioquic 二进制覆盖层与节奏收据。"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
from typing import Any


RECEIPT_PREFIX = "R2_QUIC_V5_PACING "


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def tree_sha256(root: Path) -> tuple[int, str]:
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(root).as_posix()
        digest.update(f"{relative}\0{sha256_file(path)}\n".encode())
    return len(files), digest.hexdigest()


class FakeLoop:
    def time(self) -> float:
        return 1.1

    def call_at(self, *_args: Any) -> None:
        raise AssertionError("聚焦验证不应设置计时器")


class FakeQuic:
    _pacing_at = 1.0

    def datagrams_to_send(self, *, now: float) -> list[tuple[bytes, tuple[str, int]]]:
        assert now == 1.1
        return [(b"abc", ("127.0.0.1", 4433))]

    def get_timer(self) -> None:
        return None


class FakeTransport:
    def __init__(self) -> None:
        self.sent: list[tuple[bytes, tuple[str, int]]] = []

    def sendto(self, data: bytes, address: tuple[str, int]) -> None:
        self.sent.append((data, address))


def verify(args: argparse.Namespace) -> dict[str, Any]:
    import aioquic
    import aioquic._buffer as buffer_extension
    import aioquic._crypto as crypto_extension
    from aioquic.asyncio.protocol import QuicConnectionProtocol

    overlay_root = args.tool_root.resolve() / "aioquic-overlay/aioquic"
    package_path = Path(aioquic.__file__).resolve()
    protocol_path = Path(__import__("aioquic.asyncio.protocol", fromlist=["x"]).__file__).resolve()
    buffer_path = Path(buffer_extension.__file__).resolve()
    crypto_path = Path(crypto_extension.__file__).resolve()
    source_count, source_tree = tree_sha256(args.source_package_root.resolve())
    overlay_count, overlay_tree = tree_sha256(overlay_root)

    protocol = object.__new__(QuicConnectionProtocol)
    protocol._transmit_task = None
    protocol._loop = FakeLoop()
    protocol._quic = FakeQuic()
    protocol._transport = FakeTransport()
    protocol._timer = None
    protocol._timer_at = None
    protocol._r2_pacing_sequence = 0
    captured = io.StringIO()
    with contextlib.redirect_stderr(captured):
        protocol.transmit()
    line = captured.getvalue().strip()
    receipt = (
        json.loads(line.removeprefix(RECEIPT_PREFIX)) if line.startswith(RECEIPT_PREFIX) else {}
    )

    checks = {
        "source_package_tree_exact": source_tree == args.expected_source_tree_sha256,
        "source_package_file_count_exact": source_count == 36,
        "overlay_file_count_exact": overlay_count == source_count,
        "package_from_overlay": package_path == overlay_root / "__init__.py",
        "protocol_from_overlay": protocol_path == overlay_root / "asyncio/protocol.py",
        "buffer_from_overlay": buffer_path == overlay_root / "_buffer.abi3.so",
        "crypto_from_overlay": crypto_path == overlay_root / "_crypto.abi3.so",
        "buffer_hash_exact": sha256_file(buffer_path) == args.expected_buffer_sha256,
        "crypto_hash_exact": sha256_file(crypto_path) == args.expected_crypto_sha256,
        "patched_protocol_hash_exact": sha256_file(protocol_path) == args.expected_protocol_sha256,
        "receipt_schema_exact": receipt.get("schema_version")
        == "flow_probe_r2_quic_endpoint_pacing_v5",
        "receipt_payload_exact": receipt.get("packet_bytes") == 3
        and receipt.get("sequence") == 0
        and receipt.get("pacing_requested") is True,
        "transport_send_exact": protocol._transport.sent == [(b"abc", ("127.0.0.1", 4433))],
    }
    return {
        "schema_version": "flow_probe_r2_quic_v6_overlay_verification_v1",
        "valid": all(checks.values()),
        "checks": checks,
        "source_package_tree_sha256": source_tree,
        "overlay_tree_sha256": overlay_tree,
        "source_file_count": source_count,
        "overlay_file_count": overlay_count,
        "receipt": receipt,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool-root", type=Path, required=True)
    parser.add_argument("--source-package-root", type=Path, required=True)
    parser.add_argument("--expected-source-tree-sha256", required=True)
    parser.add_argument("--expected-buffer-sha256", required=True)
    parser.add_argument("--expected-crypto-sha256", required=True)
    parser.add_argument("--expected-protocol-sha256", required=True)
    args = parser.parse_args()
    result = verify(args)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
