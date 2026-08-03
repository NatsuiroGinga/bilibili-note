from __future__ import annotations

import hashlib
import io
import json
import stat
import urllib.request
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
import yaml

import flow_probe.r2_protocol_contract as contract_module
from flow_probe.r2_protocol_contract import (
    COMMON_FIELDS,
    OFFICIAL_GENIS_MD5,
    OFFICIAL_GENIS_SIZE,
    OFFICIAL_GENIS_URL,
    DownloadReceipt,
    ExternalSourceRoots,
    FrozenArtifactSpec,
    GeNISArchiveInventory,
    GeNISArtifactSpec,
    R2ProtocolContractError,
    SourceArtifactLock,
    SourceLock,
    canonical_json_sha256,
    load_r2_config,
    resume_official_download,
    verify_frozen_inputs,
    verify_genis_archive,
    write_source_lock,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs" / "r2_protocol_data_v1.yaml"


def _zip_bytes(
    *,
    extra_member: tuple[zipfile.ZipInfo | str, bytes] | None = None,
    duplicate_member: bool = False,
    compression: int = zipfile.ZIP_DEFLATED,
) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=compression) as archive:
        for scale in (5, 10, 30, 60):
            for index in range(11):
                name = f"flows-{scale}-sec/part-{index:02d}.csv"
                archive.writestr(name, f"field,value\nscale,{scale}\nindex,{index}\n")
        if duplicate_member:
            archive.writestr("flows-10-sec/part-00.csv", b"duplicate\n")
        if extra_member is not None:
            archive.writestr(extra_member[0], extra_member[1])
    return output.getvalue()


def _corrupt_stored_member(payload: bytes, member_name: str) -> bytes:
    corrupted = bytearray(payload)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        info = archive.getinfo(member_name)
    name_length = int.from_bytes(payload[info.header_offset + 26 : info.header_offset + 28], "little")
    extra_length = int.from_bytes(payload[info.header_offset + 28 : info.header_offset + 30], "little")
    data_offset = info.header_offset + 30 + name_length + extra_length
    corrupted[data_offset] ^= 1
    return bytes(corrupted)


def _spec_for_payload(
    payload: bytes,
    *,
    md5: str | None = None,
    size_bytes: int | None = None,
) -> GeNISArtifactSpec:
    return GeNISArtifactSpec(
        logical_path="zenodo:14919237/2-flows.zip",
        record_id="14919237",
        doi="10.5281/zenodo.14919237",
        version="1.0.0",
        url=OFFICIAL_GENIS_URL,
        size_bytes=len(payload) if size_bytes is None else size_bytes,
        md5=hashlib.md5(payload, usedforsecurity=False).hexdigest() if md5 is None else md5,
        scales_seconds=(5, 10, 30, 60),
        csv_per_scale=11,
        materialization_scale_seconds=10,
    )


def _write_archive(path: Path, payload: bytes) -> GeNISArtifactSpec:
    path.write_bytes(payload)
    return _spec_for_payload(payload)


@dataclass
class _HTTPState:
    payload: bytes
    ignore_range: bool = False
    wrong_content_range: bool = False
    truncate_response: bool = False
    requests: list[str | None] | None = None

    def __post_init__(self) -> None:
        if self.requests is None:
            self.requests = []


@contextmanager
def _http_archive(state: _HTTPState) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            range_header = self.headers.get("Range")
            assert state.requests is not None
            state.requests.append(range_header)
            body = state.payload
            status_code = 200
            content_range = None
            if range_header is not None and not state.ignore_range:
                start = int(range_header.removeprefix("bytes=").removesuffix("-"))
                body = state.payload[start:]
                status_code = 206
                range_start = start + 1 if state.wrong_content_range else start
                content_range = f"bytes {range_start}-{len(state.payload) - 1}/{len(state.payload)}"
            if state.truncate_response:
                body = body[:-1]
            self.send_response(status_code)
            self.send_header("Content-Length", str(len(body)))
            if content_range is not None:
                self.send_header("Content-Range", content_range)
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}/2-flows.zip"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def _redirect_official_url(monkeypatch: pytest.MonkeyPatch, local_url: str) -> None:
    original_urlopen = urllib.request.urlopen

    def redirected_urlopen(
        request: urllib.request.Request, timeout: float = 120
    ) -> object:
        redirected = urllib.request.Request(
            local_url,
            headers=dict(request.header_items()),
            method=request.get_method(),
        )
        return original_urlopen(redirected, timeout=timeout)

    monkeypatch.setattr(contract_module.urllib.request, "urlopen", redirected_urlopen)


def _download_lock(destination: Path, spec: GeNISArtifactSpec, prefix: bytes) -> Path:
    partial, sidecar = contract_module._download_paths(destination)
    partial.write_bytes(prefix)
    sidecar.write_text(
        json.dumps(
            {
                "url": spec.url,
                "version": spec.version,
                "size_bytes": spec.size_bytes,
                "md5": spec.md5,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    return partial


def test_real_config_freezes_complete_r2_contract() -> None:
    config = load_r2_config(CONFIG_PATH)

    assert config.dataset_version == "flow_probe_r2_protocol_dataset_v0"
    assert config.publish_root == "runs/data-frozen/dataset-candidate-r2-protocol-v0"
    assert config.common_fields == COMMON_FIELDS
    assert config.parquet.row_group_size == 65536
    assert config.parquet.compression == "zstd"
    assert config.parquet.use_dictionary is False
    assert config.genis.url == OFFICIAL_GENIS_URL
    assert config.genis.size_bytes == OFFICIAL_GENIS_SIZE
    assert config.genis.md5 == OFFICIAL_GENIS_MD5
    assert config.ns3_matrix.base_configuration_count == 256
    assert config.ns3_matrix.protocol_run_count == 512
    assert config.ns3_matrix.paired_completion_minimum == 0.95
    assert set(config.information_budgets["groups"]) == {"A", "B", "C", "D"}
    assert config.field_roles["tcp_rtt_ms"] == "blocked_pending_semantics"
    assert config.semantic_gates["TotBytes"]["status"] == "blocked_pending_semantics"
    assert config.tqhc2_profiles["B"].extractor_evidence_mode == "verified_snapshot"
    assert {
        profile: spec.extractor_evidence_mode
        for profile, spec in config.tqhc2_profiles.items()
        if profile in {"A", "C"}
    } == {"A": "approved_manifest_only_blocked", "C": "approved_manifest_only_blocked"}
    assert tuple(
        (mapping.source_prefix, mapping.root, mapping.logical_root)
        for mapping in config.tqhc2_historical_path_mappings
    ) == (
        ("/Users/bilibili/personal/note/raw", "repository", "raw"),
        ("../../../raw", "repository", "raw"),
        (
            "/Users/bilibili/personal/note/thesis/experiments/llm_probe/src",
            "project",
            "src",
        ),
    )


def test_config_rejects_absolute_logical_source_path(tmp_path: Path) -> None:
    document = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    document["sources"]["frozen_inputs"][0]["path"] = "/absolute/source.parquet"
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    with pytest.raises(R2ProtocolContractError, match="逻辑相对路径"):
        load_r2_config(path)


def test_tqh_historical_paths_require_approved_complete_prefixes() -> None:
    config = load_r2_config(CONFIG_PATH)
    mappings = config.tqhc2_historical_path_mappings

    assert contract_module._normalise_tqh_source_path(
        "/Users/bilibili/personal/note/raw/datasets/A/file.pcap", mappings
    ) == ("repository", "raw/datasets/A/file.pcap")
    assert contract_module._normalise_tqh_source_path(
        "../../../raw/datasets/B/file.pcap", mappings
    ) == ("repository", "raw/datasets/B/file.pcap")
    assert contract_module._normalise_tqh_source_path(
        "/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py",
        mappings,
    ) == ("project", "src/flow_probe/tqh_c2.py")


@pytest.mark.parametrize(
    "source_path",
    (
        "/unapproved/prefix/raw/file.pcap",
        "/unapproved/prefix/src/flow_probe/tqh_c2.py",
        "/Users/bilibili/personal/note/rawish/file.pcap",
        "C:\\data\\raw\\file.pcap",
        "\\\\server\\share\\raw\\file.pcap",
    ),
)
def test_tqh_historical_paths_reject_unknown_component_impostors_and_windows_paths(
    source_path: str,
) -> None:
    mappings = load_r2_config(CONFIG_PATH).tqhc2_historical_path_mappings

    with pytest.raises(R2ProtocolContractError, match="完整历史前缀|Windows|UNC"):
        contract_module._normalise_tqh_source_path(source_path, mappings)


def test_tqh_historical_paths_reject_multiple_matches_and_traversal() -> None:
    mappings = (
        contract_module.TQHPathMappingSpec("/approved", "repository", "raw"),
        contract_module.TQHPathMappingSpec("/approved/raw", "repository", "raw"),
    )
    with pytest.raises(R2ProtocolContractError, match="多个历史前缀"):
        contract_module._normalise_tqh_source_path("/approved/raw/file.pcap", mappings)

    single_mapping = (mappings[1],)
    with pytest.raises(R2ProtocolContractError, match="越界"):
        contract_module._normalise_tqh_source_path(
            "/approved/raw/../outside/file.pcap", single_mapping
        )


def test_tqh_reanchored_path_rejects_symlink_escape(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    repository_root = tmp_path / "repository"
    outside = tmp_path / "outside"
    project_root.mkdir()
    (repository_root / "raw").mkdir(parents=True)
    outside.mkdir()
    (repository_root / "raw" / "escape").symlink_to(outside, target_is_directory=True)

    with pytest.raises(R2ProtocolContractError, match="越界"):
        contract_module._resolve_tqh_source_path(
            "repository",
            "raw/escape/file.pcap",
            project_root,
            repository_root,
        )


def test_canonical_json_sha256_is_key_order_independent_and_rejects_nan() -> None:
    assert canonical_json_sha256({"b": [2, 1], "a": 3}) == canonical_json_sha256(
        {"a": 3, "b": [2, 1]}
    )
    with pytest.raises(R2ProtocolContractError, match="规范 JSON"):
        canonical_json_sha256({"value": float("nan")})


def test_verify_genis_archive_records_four_scales_and_ten_second_hashes(
    tmp_path: Path,
) -> None:
    payload = _zip_bytes()
    archive_path = tmp_path / "2-flows.zip"
    spec = _write_archive(archive_path, payload)

    inventory = verify_genis_archive(archive_path, spec)

    assert dict(inventory.scale_member_counts) == {5: 11, 10: 11, 30: 11, 60: 11}
    assert len(inventory.materialization_members) == 11
    assert all(member.scale_seconds == 10 for member in inventory.materialization_members)
    assert all(member.logical_path.startswith("zenodo:14919237/") for member in inventory.materialization_members)
    with zipfile.ZipFile(archive_path) as archive:
        actual_members = {
            member.member_path: archive.read(member.member_path)
            for member in inventory.materialization_members
        }
    assert {
        member.member_path: (member.size_bytes, member.sha256)
        for member in inventory.materialization_members
    } == {
        name: (len(content), hashlib.sha256(content).hexdigest())
        for name, content in actual_members.items()
    }


def test_verify_genis_archive_rejects_wrong_size(tmp_path: Path) -> None:
    payload = _zip_bytes()
    path = tmp_path / "2-flows.zip"
    path.write_bytes(payload)

    with pytest.raises(R2ProtocolContractError, match="大小错误"):
        verify_genis_archive(path, _spec_for_payload(payload, size_bytes=len(payload) + 1))


def test_verify_genis_archive_rejects_wrong_md5(tmp_path: Path) -> None:
    payload = _zip_bytes()
    path = tmp_path / "2-flows.zip"
    path.write_bytes(payload)

    with pytest.raises(R2ProtocolContractError, match="MD5 错误"):
        verify_genis_archive(path, _spec_for_payload(payload, md5="0" * 32))


def test_verify_genis_archive_rejects_path_traversal(tmp_path: Path) -> None:
    payload = _zip_bytes(extra_member=("../escape.csv", b"unsafe\n"))
    path = tmp_path / "2-flows.zip"
    spec = _write_archive(path, payload)

    with pytest.raises(R2ProtocolContractError, match="路径不安全"):
        verify_genis_archive(path, spec)


@pytest.mark.parametrize(
    "member_name",
    ("C:\\escape.csv", "\\\\server\\share\\escape.csv"),
)
def test_verify_genis_archive_rejects_windows_and_unc_absolute_paths(
    tmp_path: Path, member_name: str
) -> None:
    payload = _zip_bytes(extra_member=(member_name, b"unsafe\n"))
    path = tmp_path / "2-flows.zip"
    spec = _write_archive(path, payload)

    with pytest.raises(R2ProtocolContractError, match="路径不安全"):
        verify_genis_archive(path, spec)


def test_verify_genis_archive_rejects_symbolic_link(tmp_path: Path) -> None:
    link = zipfile.ZipInfo("flows-10-sec/link.csv")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    payload = _zip_bytes(extra_member=(link, b"part-00.csv"))
    path = tmp_path / "2-flows.zip"
    spec = _write_archive(path, payload)

    with pytest.raises(R2ProtocolContractError, match="符号链接"):
        verify_genis_archive(path, spec)


def test_verify_genis_archive_rejects_duplicate_member(tmp_path: Path) -> None:
    payload = _zip_bytes(duplicate_member=True)
    path = tmp_path / "2-flows.zip"
    spec = _write_archive(path, payload)

    with pytest.raises(R2ProtocolContractError, match="重复成员"):
        verify_genis_archive(path, spec)


def test_verify_genis_archive_rejects_damaged_central_directory(tmp_path: Path) -> None:
    payload = _zip_bytes()[:-22]
    path = tmp_path / "2-flows.zip"
    spec = _write_archive(path, payload)

    with pytest.raises(R2ProtocolContractError, match="中央目录"):
        verify_genis_archive(path, spec)


def test_verify_genis_archive_rejects_crc_damage(tmp_path: Path) -> None:
    payload = _zip_bytes(compression=zipfile.ZIP_STORED)
    payload = _corrupt_stored_member(payload, "flows-10-sec/part-00.csv")
    path = tmp_path / "2-flows.zip"
    spec = _write_archive(path, payload)

    with pytest.raises(R2ProtocolContractError, match="CRC|内容读取"):
        verify_genis_archive(path, spec)


def test_resume_official_download_uses_matching_range_and_publishes_atomically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = _zip_bytes()
    spec = _spec_for_payload(payload)
    destination = tmp_path / "2-flows.zip"
    prefix_size = len(payload) // 3
    partial = _download_lock(destination, spec, payload[:prefix_size])
    state = _HTTPState(payload)
    with _http_archive(state) as local_url:
        _redirect_official_url(monkeypatch, local_url)
        receipt = resume_official_download(spec, destination)

    assert isinstance(receipt, DownloadReceipt)
    assert receipt.resumed_from_bytes == prefix_size
    assert receipt.range_requested is True
    assert state.requests == [f"bytes={prefix_size}-"]
    assert destination.read_bytes() == payload
    assert not partial.exists()
    assert not contract_module._download_paths(destination)[1].exists()


def test_resume_official_download_rejects_wrong_content_range_before_append(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = _zip_bytes()
    spec = _spec_for_payload(payload)
    destination = tmp_path / "2-flows.zip"
    prefix = payload[:100]
    partial = _download_lock(destination, spec, prefix)
    state = _HTTPState(payload, wrong_content_range=True)
    with _http_archive(state) as local_url:
        _redirect_official_url(monkeypatch, local_url)
        with pytest.raises(R2ProtocolContractError, match="Content-Range"):
            resume_official_download(spec, destination)

    assert partial.read_bytes() == prefix
    assert not destination.exists()


def test_resume_official_download_restarts_from_zero_after_full_200(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = _zip_bytes()
    spec = _spec_for_payload(payload)
    destination = tmp_path / "2-flows.zip"
    prefix_size = 137
    _download_lock(destination, spec, b"not-the-official-prefix"[:prefix_size])
    state = _HTTPState(payload, ignore_range=True)
    with _http_archive(state) as local_url:
        _redirect_official_url(monkeypatch, local_url)
        receipt = resume_official_download(spec, destination)

    assert receipt.resumed_from_bytes == len(b"not-the-official-prefix"[:prefix_size])
    assert state.requests == [
        f"bytes={len(b'not-the-official-prefix'[:prefix_size])}-",
        None,
    ]
    assert destination.read_bytes() == payload


def test_resume_official_download_rejects_size_error_without_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = _zip_bytes()
    spec = _spec_for_payload(payload)
    destination = tmp_path / "2-flows.zip"
    state = _HTTPState(payload, truncate_response=True)
    with _http_archive(state) as local_url:
        _redirect_official_url(monkeypatch, local_url)
        with pytest.raises(R2ProtocolContractError, match="下载大小错误"):
            resume_official_download(spec, destination)

    assert not destination.exists()
    assert contract_module._download_paths(destination)[0].exists()


def test_resume_official_download_rejects_md5_error_without_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = _zip_bytes()
    spec = _spec_for_payload(payload, md5="f" * 32)
    destination = tmp_path / "2-flows.zip"
    state = _HTTPState(payload)
    with _http_archive(state) as local_url:
        _redirect_official_url(monkeypatch, local_url)
        with pytest.raises(R2ProtocolContractError, match="MD5 错误"):
            resume_official_download(spec, destination)

    assert not destination.exists()
    partial, sidecar = contract_module._download_paths(destination)
    assert not partial.exists()
    assert not sidecar.exists()


def test_resume_official_download_discards_bad_complete_file_then_retries_from_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = _zip_bytes()
    spec = _spec_for_payload(payload)
    destination = tmp_path / "2-flows.zip"
    partial = _download_lock(destination, spec, b"x" * len(payload))
    _, sidecar = contract_module._download_paths(destination)

    with pytest.raises(R2ProtocolContractError, match="MD5 错误"):
        resume_official_download(spec, destination)

    assert not partial.exists()
    assert not sidecar.exists()
    state = _HTTPState(payload)
    with _http_archive(state) as local_url:
        _redirect_official_url(monkeypatch, local_url)
        receipt = resume_official_download(spec, destination)

    assert receipt.resumed_from_bytes == 0
    assert state.requests == [None]
    assert destination.read_bytes() == payload


def test_resume_official_download_discards_oversized_terminal_state(tmp_path: Path) -> None:
    payload = _zip_bytes()
    spec = _spec_for_payload(payload)
    destination = tmp_path / "2-flows.zip"
    partial = _download_lock(destination, spec, payload + b"oversized")
    _, sidecar = contract_module._download_paths(destination)

    with pytest.raises(R2ProtocolContractError, match="大于官方登记大小"):
        resume_official_download(spec, destination)

    assert not partial.exists()
    assert not sidecar.exists()
    assert not destination.exists()


def test_resume_official_download_sidecar_cleanup_failure_precedes_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = _zip_bytes()
    spec = _spec_for_payload(payload)
    destination = tmp_path / "2-flows.zip"
    _, sidecar = contract_module._download_paths(destination)
    original_unlink = Path.unlink

    def fail_sidecar_unlink(path: Path, *args: object, **kwargs: object) -> None:
        if path == sidecar:
            raise OSError("注入的旁路锁清理失败")
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_sidecar_unlink)
    state = _HTTPState(payload)
    with _http_archive(state) as local_url:
        _redirect_official_url(monkeypatch, local_url)
        with pytest.raises(R2ProtocolContractError, match="发布前旁路锁清理失败"):
            resume_official_download(spec, destination)

    partial, _ = contract_module._download_paths(destination)
    assert not destination.exists()
    assert partial.read_bytes() == payload
    assert sidecar.is_file()


def test_resume_official_download_concurrent_target_never_overwrites(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = _zip_bytes()
    spec = _spec_for_payload(payload)
    destination = tmp_path / "2-flows.zip"
    original_link = contract_module.os.link

    def race_link(source: Path, target: Path) -> None:
        if Path(target) == destination:
            destination.write_bytes(b"concurrent-owner")
        original_link(source, target)

    monkeypatch.setattr(contract_module.os, "link", race_link)
    state = _HTTPState(payload)
    with _http_archive(state) as local_url:
        _redirect_official_url(monkeypatch, local_url)
        with pytest.raises(R2ProtocolContractError, match="拒绝覆盖"):
            resume_official_download(spec, destination)

    partial, sidecar = contract_module._download_paths(destination)
    assert destination.read_bytes() == b"concurrent-owner"
    assert not partial.exists()
    assert not sidecar.exists()


def test_resume_official_download_rejects_existing_destination_without_request(
    tmp_path: Path,
) -> None:
    payload = _zip_bytes()
    spec = _spec_for_payload(payload)
    destination = tmp_path / "2-flows.zip"
    destination.write_bytes(b"existing")

    with pytest.raises(R2ProtocolContractError, match="拒绝覆盖"):
        resume_official_download(spec, destination)

    assert destination.read_bytes() == b"existing"


def test_resume_official_download_rejects_dangling_destination_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = _zip_bytes()
    spec = _spec_for_payload(payload)
    destination = tmp_path / "2-flows.zip"
    destination.symlink_to(tmp_path / "missing.zip")

    def unexpected_request(request: urllib.request.Request) -> object:
        raise AssertionError(f"不应发起请求：{request.full_url}")

    monkeypatch.setattr(contract_module, "_open_download", unexpected_request)
    with pytest.raises(R2ProtocolContractError, match="拒绝覆盖"):
        resume_official_download(spec, destination)

    assert destination.is_symlink()
    assert destination.readlink() == tmp_path / "missing.zip"


def test_resume_official_download_rejects_non_https_or_unregistered_url(
    tmp_path: Path,
) -> None:
    payload = _zip_bytes()
    spec = replace(_spec_for_payload(payload), url="http://127.0.0.1/file.zip")

    with pytest.raises(R2ProtocolContractError, match="Zenodo HTTPS"):
        resume_official_download(spec, tmp_path / "2-flows.zip")


def test_resume_official_download_requires_matching_sidecar_lock(tmp_path: Path) -> None:
    payload = _zip_bytes()
    spec = _spec_for_payload(payload)
    destination = tmp_path / "2-flows.zip"
    _, sidecar = contract_module._download_paths(destination)
    _download_lock(destination, spec, payload[:50])
    lock = json.loads(sidecar.read_text(encoding="utf-8"))
    lock["version"] = "different"
    sidecar.write_text(json.dumps(lock, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(R2ProtocolContractError, match="旁路锁"):
        resume_official_download(spec, destination)


def _source_lock(inventory: GeNISArchiveInventory) -> SourceLock:
    return SourceLock(
        schema_version="flow_probe_r2_source_lock_v1",
        dataset_version="flow_probe_r2_protocol_dataset_v0",
        stage="theory_selection",
        status="review_pending",
        config_sha256="1" * 64,
        code_commit="2" * 40,
        frozen_inputs=(
            SourceArtifactLock(
                logical_path="runs/input.jsonl",
                role="classification_candidate",
                sha256="3" * 64,
                size_bytes=10,
                row_count=1,
            ),
        ),
        tqhc2_artifacts=(
            SourceArtifactLock(
                logical_path="raw/tqh/source.pcap",
                role="source_pcap",
                sha256="4" * 64,
                size_bytes=20,
                profile="A",
            ),
        ),
        genis=inventory,
        candidate_source_counts=(("genis", 3973), ("ns3", 2421), ("tqhc2", 3606)),
    )


def test_write_source_lock_is_byte_reproducible_and_idempotent(tmp_path: Path) -> None:
    payload = _zip_bytes()
    archive_path = tmp_path / "2-flows.zip"
    inventory = verify_genis_archive(archive_path, _write_archive(archive_path, payload))
    lock = _source_lock(inventory)
    first = tmp_path / "first"
    second = tmp_path / "second"

    write_source_lock(lock, first)
    write_source_lock(lock, first)
    write_source_lock(lock, second)

    names = ("source-lock.json", "genis-member-lock.jsonl", "tqhc2-source-lock.jsonl")
    assert {name: (first / name).read_bytes() for name in names} == {
        name: (second / name).read_bytes() for name in names
    }


def test_write_source_lock_rejects_different_content_and_preserves_all_files(
    tmp_path: Path,
) -> None:
    payload = _zip_bytes()
    archive_path = tmp_path / "2-flows.zip"
    inventory = verify_genis_archive(archive_path, _write_archive(archive_path, payload))
    output_root = tmp_path / "lock"
    lock = _source_lock(inventory)
    write_source_lock(lock, output_root)
    names = ("source-lock.json", "genis-member-lock.jsonl", "tqhc2-source-lock.jsonl")
    original = {name: (output_root / name).read_bytes() for name in names}

    with pytest.raises(R2ProtocolContractError, match="拒绝覆盖"):
        write_source_lock(replace(lock, config_sha256="9" * 64), output_root)

    assert {name: (output_root / name).read_bytes() for name in names} == original


def test_write_source_lock_rejects_dangling_symlink_without_replacement(
    tmp_path: Path,
) -> None:
    payload = _zip_bytes()
    archive_path = tmp_path / "2-flows.zip"
    inventory = verify_genis_archive(archive_path, _write_archive(archive_path, payload))
    output_root = tmp_path / "lock"
    output_root.mkdir()
    target = output_root / "genis-member-lock.jsonl"
    missing = output_root / "missing.jsonl"
    target.symlink_to(missing)

    with pytest.raises(R2ProtocolContractError, match="拒绝覆盖"):
        write_source_lock(_source_lock(inventory), output_root)

    assert target.is_symlink()
    assert target.readlink() == missing


def test_write_source_lock_concurrent_target_never_overwrites(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = _zip_bytes()
    archive_path = tmp_path / "2-flows.zip"
    inventory = verify_genis_archive(archive_path, _write_archive(archive_path, payload))
    output_root = tmp_path / "lock"
    raced_target = output_root / "genis-member-lock.jsonl"
    original_link = contract_module.os.link

    def race_link(source: Path, target: Path) -> None:
        if Path(target) == raced_target:
            raced_target.write_bytes(b"concurrent-owner")
        original_link(source, target)

    monkeypatch.setattr(contract_module.os, "link", race_link)
    with pytest.raises(R2ProtocolContractError, match="拒绝覆盖"):
        write_source_lock(_source_lock(inventory), output_root)

    assert raced_target.read_bytes() == b"concurrent-owner"
    assert not raced_target.with_name(f"{raced_target.name}.partial").exists()


def test_write_source_lock_rejects_absolute_path(tmp_path: Path) -> None:
    payload = _zip_bytes()
    archive_path = tmp_path / "2-flows.zip"
    inventory = verify_genis_archive(archive_path, _write_archive(archive_path, payload))
    lock = _source_lock(inventory)
    unsafe = replace(
        lock,
        frozen_inputs=(
            SourceArtifactLock(
                logical_path="/absolute/input.jsonl",
                role="classification_candidate",
                sha256="3" * 64,
                size_bytes=10,
            ),
        ),
    )

    with pytest.raises(R2ProtocolContractError, match="逻辑相对路径"):
        write_source_lock(unsafe, tmp_path / "lock")


@dataclass
class _FrozenTree:
    project_root: Path
    repository_root: Path
    config: contract_module.R2ProtocolConfig
    external_sources: ExternalSourceRoots
    layer_paths: dict[str, Path]
    commit_calls: list[Path]


def _write_fixture_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _write_fixture_json(path: Path, value: object) -> None:
    _write_fixture_bytes(
        path,
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n",
    )


def _fixture_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_complete_frozen_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> _FrozenTree:
    project_root = tmp_path / "project"
    repository_root = tmp_path / "repository"
    project_root.mkdir()
    repository_root.mkdir()
    config = load_r2_config(CONFIG_PATH)
    frozen_specs: dict[str, FrozenArtifactSpec] = {}
    frozen_paths: dict[str, Path] = {}
    candidate_spec = next(
        spec for spec in config.frozen_inputs if spec.role == "classification_candidate"
    )
    budget_spec = next(
        spec for spec in config.frozen_inputs if spec.role == "budget_checksums"
    )
    candidate_path = project_root / candidate_spec.logical_path
    candidate_payload = b"".join(
        json.dumps({"source_dataset": source}).encode("utf-8") + b"\n"
        for source in ("genis", "tqhc2", "ns3")
    )
    _write_fixture_bytes(candidate_path, candidate_payload)
    frozen_specs[candidate_spec.role] = replace(
        candidate_spec,
        row_count=3,
        source_counts=(("genis", 1), ("ns3", 1), ("tqhc2", 1)),
    )
    frozen_paths[candidate_spec.role] = candidate_path
    for spec in config.frozen_inputs:
        if spec.role in {candidate_spec.role, budget_spec.role}:
            continue
        root = project_root if spec.root == "project" else repository_root
        path = root / spec.logical_path
        if spec.row_count is not None:
            _write_fixture_bytes(path, b"{}\n")
            updated = replace(
                spec,
                sha256=_fixture_sha256(path),
                row_count=1,
                checksum_manifest=None,
                checksum_key=None,
            )
        else:
            _write_fixture_bytes(path, f"fixture:{spec.role}\n".encode("utf-8"))
            updated = replace(spec, sha256=_fixture_sha256(path))
        frozen_specs[spec.role] = updated
        frozen_paths[spec.role] = path
    budget_path = project_root / budget_spec.logical_path
    _write_fixture_json(
        budget_path,
        {
            "artifacts": {
                candidate_spec.checksum_key: {
                    "sha256": _fixture_sha256(candidate_path),
                    "size_bytes": candidate_path.stat().st_size,
                }
            }
        },
    )
    frozen_specs[budget_spec.role] = replace(
        budget_spec, sha256=_fixture_sha256(budget_path)
    )
    frozen_paths[budget_spec.role] = budget_path
    ordered_frozen_specs = tuple(frozen_specs[spec.role] for spec in config.frozen_inputs)

    extractor_path = project_root / "src/flow_probe/tqh_c2.py"
    extractor_payload = b"approved B extractor snapshot\n"
    _write_fixture_bytes(extractor_path, extractor_payload)
    extractor_sha256 = _fixture_sha256(extractor_path)
    parquet_rows: dict[Path, int] = {}
    profile_specs: dict[str, contract_module.TQHProfileSpec] = {}
    profile_roots: dict[str, Path] = {}
    layer_paths: dict[str, Path] = {
        "old_frozen_input": frozen_paths["master_records"],
        "indirect_candidate": candidate_path,
        "extractor_snapshot": extractor_path,
    }
    for profile in ("A", "B", "C"):
        original_profile = config.tqhc2_profiles[profile]
        runtime_root = project_root / f"runs/tqh/{profile}"
        profile_roots[profile] = runtime_root
        raw_relative_paths = {
            "label_or_audit_source": f"raw/datasets/fixture/{profile}/label.json",
            "source_pcap": f"raw/datasets/fixture/{profile}/source.pcap",
        }
        source_rows: list[dict[str, object]] = []
        for role, logical_path in raw_relative_paths.items():
            actual_path = repository_root / logical_path
            _write_fixture_bytes(actual_path, f"{profile}:{role}\n".encode("utf-8"))
            historical_path = (
                f"/Users/bilibili/personal/note/{logical_path}"
                if profile == "A"
                else f"../../../{logical_path}"
            )
            source_rows.append(
                {
                    "path": historical_path,
                    "role": role,
                    "sha256": _fixture_sha256(actual_path),
                    "size_bytes": actual_path.stat().st_size,
                }
            )
            if profile == "B" and role == "source_pcap":
                layer_paths["tqh_raw_source"] = actual_path
        if profile == "B":
            profile_extractor_sha256 = extractor_sha256
            profile_extractor_size = extractor_path.stat().st_size
        else:
            historical_payload = f"historical {profile} extractor snapshot\n".encode("utf-8")
            profile_extractor_sha256 = hashlib.sha256(historical_payload).hexdigest()
            profile_extractor_size = len(historical_payload)
        source_rows.append(
            {
                "path": "/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py",
                "role": "extractor_source",
                "sha256": profile_extractor_sha256,
                "size_bytes": profile_extractor_size,
            }
        )
        source_manifest_path = runtime_root / config.tqhc2_source_manifest_path
        _write_fixture_json(source_manifest_path, {"files": source_rows})
        artifact_rows: list[dict[str, object]] = []
        for relative_path in config.tqhc2_expected_artifact_paths:
            path = runtime_root / relative_path
            if relative_path == config.tqhc2_source_manifest_path:
                pass
            elif relative_path == "master_records.parquet":
                _write_fixture_bytes(path, f"{profile}:master\n".encode("utf-8"))
                parquet_rows[path.resolve()] = 2
            elif relative_path == "views/packet_observations.parquet":
                _write_fixture_bytes(path, f"{profile}:packets\n".encode("utf-8"))
                parquet_rows[path.resolve()] = 4
            else:
                _write_fixture_json(path, {"profile": profile, "path": relative_path})
            artifact_rows.append(
                {
                    "path": relative_path,
                    "sha256": _fixture_sha256(path),
                    "size_bytes": path.stat().st_size,
                }
            )
            if profile == "A" and relative_path == "audit/cell-audit.json":
                layer_paths["tqh_artifact"] = path
        artifact_manifest_path = runtime_root / config.tqhc2_artifact_manifest_path
        _write_fixture_json(
            artifact_manifest_path,
            {"status": "provisional", "files": artifact_rows},
        )
        if profile == "A":
            layer_paths["tqh_artifact_manifest"] = artifact_manifest_path
        profile_specs[profile] = replace(
            original_profile,
            logical_root=f"runs/tqh/{profile}",
            artifact_manifest_sha256=_fixture_sha256(artifact_manifest_path),
            extractor_contract_sha256=profile_extractor_sha256,
            master_sha256=_fixture_sha256(runtime_root / "master_records.parquet"),
            master_rows=2,
            packets_sha256=_fixture_sha256(
                runtime_root / "views/packet_observations.parquet"
            ),
            packet_rows=4,
        )

    approved_path = project_root / config.tqhc2_approved_inputs_path
    _write_fixture_json(
        approved_path,
        {
            "profiles": {
                profile: {
                    "input_id": spec.input_id,
                    "artifact_checksums_sha256": spec.artifact_manifest_sha256,
                    "extractor_contract_sha256": spec.extractor_contract_sha256,
                    "master_record_count": spec.master_rows,
                    "packet_record_count": spec.packet_rows,
                }
                for profile, spec in profile_specs.items()
            }
        },
    )
    layer_paths["approved_inputs"] = approved_path
    genis_path = tmp_path / "2-flows.zip"
    genis_payload = _zip_bytes()
    genis_spec = _write_archive(genis_path, genis_payload)
    layer_paths["genis_archive"] = genis_path
    complete_config = replace(
        config,
        frozen_inputs=ordered_frozen_specs,
        tqhc2_profiles=profile_specs,
        tqhc2_approved_inputs_sha256=_fixture_sha256(approved_path),
        tqhc2_raw_source_role_counts={
            "extractor_source": 1,
            "label_or_audit_source": 1,
            "source_pcap": 1,
        },
        genis=genis_spec,
    )

    def fixture_parquet_rows(path: Path) -> int:
        return parquet_rows[Path(path).resolve()]

    commit_calls: list[Path] = []

    def fixture_git_commit(path: Path) -> str:
        commit_calls.append(Path(path))
        return "a" * 40

    monkeypatch.setattr(contract_module, "_parquet_rows", fixture_parquet_rows)
    monkeypatch.setattr(contract_module, "_current_git_commit", fixture_git_commit)
    return _FrozenTree(
        project_root=project_root,
        repository_root=repository_root,
        config=complete_config,
        external_sources=ExternalSourceRoots(
            genis_archive=genis_path,
            repository_root=repository_root,
            tqhc2_profile_roots=profile_roots,
        ),
        layer_paths=layer_paths,
        commit_calls=commit_calls,
    )


def test_verify_frozen_inputs_returns_complete_source_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tree = _build_complete_frozen_tree(tmp_path, monkeypatch)

    lock = verify_frozen_inputs(tree.project_root, tree.external_sources, tree.config)

    assert isinstance(lock, SourceLock)
    assert lock.code_commit == "a" * 40
    assert tree.commit_calls == [tree.project_root]
    assert len(lock.frozen_inputs) == len(tree.config.frozen_inputs)
    assert lock.candidate_source_counts == (("genis", 1), ("ns3", 1), ("tqhc2", 1))
    extractor_locks = {
        artifact.profile: artifact
        for artifact in lock.tqhc2_artifacts
        if artifact.role == "extractor_source"
    }
    assert extractor_locks["B"].evidence_mode == "verified_snapshot"
    assert extractor_locks["B"].evidence_status == "verified"
    assert {
        profile: (extractor_locks[profile].evidence_mode, extractor_locks[profile].evidence_status)
        for profile in ("A", "C")
    } == {
        "A": ("approved_manifest_only_blocked", "blocked"),
        "C": ("approved_manifest_only_blocked", "blocked"),
    }
    assert len(lock.genis.materialization_members) == 11
    output_root = tmp_path / "source-lock"
    write_source_lock(lock, output_root)
    serialized_extractors = {
        row["profile"]: row
        for row in (
            json.loads(line)
            for line in (output_root / "tqhc2-source-lock.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        if row["role"] == "extractor_source"
    }
    assert serialized_extractors["B"]["evidence_status"] == "verified"
    assert serialized_extractors["A"]["evidence_status"] == "blocked"
    assert serialized_extractors["C"]["evidence_status"] == "blocked"


@pytest.mark.parametrize(
    ("layer", "message"),
    (
        ("old_frozen_input", "SHA-256 变化"),
        ("indirect_candidate", "SHA-256 变化"),
        ("approved_inputs", "SHA-256 变化"),
        ("tqh_artifact_manifest", "SHA-256 变化"),
        ("tqh_artifact", "SHA-256 变化"),
        ("tqh_raw_source", "SHA-256 变化"),
        ("extractor_snapshot", "SHA-256 变化"),
        ("genis_archive", "大小错误"),
    ),
)
def test_verify_frozen_inputs_rejects_single_layer_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    layer: str,
    message: str,
) -> None:
    tree = _build_complete_frozen_tree(tmp_path, monkeypatch)
    path = tree.layer_paths[layer]
    path.write_bytes(path.read_bytes() + b"changed")

    with pytest.raises(R2ProtocolContractError, match=message):
        verify_frozen_inputs(tree.project_root, tree.external_sources, tree.config)


def test_verify_frozen_inputs_rejects_code_binding_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tree = _build_complete_frozen_tree(tmp_path, monkeypatch)

    def fail_code_binding(project_root: Path) -> str:
        raise R2ProtocolContractError(f"代码绑定失败：{project_root}")

    monkeypatch.setattr(contract_module, "_current_git_commit", fail_code_binding)
    with pytest.raises(R2ProtocolContractError, match="代码绑定失败"):
        verify_frozen_inputs(tree.project_root, tree.external_sources, tree.config)


def test_verify_frozen_inputs_fails_immediately_for_missing_or_changed_input(
    tmp_path: Path,
) -> None:
    config = load_r2_config(CONFIG_PATH)
    missing = FrozenArtifactSpec(
        role="missing",
        root="project",
        logical_path="missing.jsonl",
        sha256="0" * 64,
    )
    minimal_config = replace(config, frozen_inputs=(missing,), tqhc2_profiles={})
    with pytest.raises(R2ProtocolContractError, match="不存在"):
        verify_frozen_inputs(tmp_path, ExternalSourceRoots(), minimal_config)

    changed_path = tmp_path / "changed.jsonl"
    changed_path.write_text("{}\n", encoding="utf-8")
    changed = replace(missing, logical_path="changed.jsonl")
    minimal_config = replace(config, frozen_inputs=(changed,), tqhc2_profiles={})
    with pytest.raises(R2ProtocolContractError, match="SHA-256 变化"):
        verify_frozen_inputs(tmp_path, ExternalSourceRoots(), minimal_config)


def test_verify_frozen_inputs_rejects_frozen_jsonl_row_count_change(tmp_path: Path) -> None:
    config = load_r2_config(CONFIG_PATH)
    candidate_path = tmp_path / "candidate.jsonl"
    candidate_path.write_text(
        '{"source_dataset":"genis"}\n{"source_dataset":"genis"}\n',
        encoding="utf-8",
    )
    candidate = FrozenArtifactSpec(
        role="classification_candidate",
        root="project",
        logical_path="candidate.jsonl",
        sha256=hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
        row_count=1,
        source_counts=(("genis", 2),),
    )
    minimal_config = replace(config, frozen_inputs=(candidate,), tqhc2_profiles={})

    with pytest.raises(R2ProtocolContractError, match="行数变化"):
        verify_frozen_inputs(tmp_path, ExternalSourceRoots(), minimal_config)


def test_verify_frozen_inputs_rejects_frozen_jsonl_source_count_change(
    tmp_path: Path,
) -> None:
    config = load_r2_config(CONFIG_PATH)
    candidate_path = tmp_path / "candidate.jsonl"
    candidate_path.write_text(
        '{"source_dataset":"genis"}\n{"source_dataset":"genis"}\n',
        encoding="utf-8",
    )
    candidate = FrozenArtifactSpec(
        role="classification_candidate",
        root="project",
        logical_path="candidate.jsonl",
        sha256=hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
        row_count=2,
        source_counts=(("genis", 1), ("tqhc2", 1)),
    )
    minimal_config = replace(config, frozen_inputs=(candidate,), tqhc2_profiles={})

    with pytest.raises(R2ProtocolContractError, match="来源数量变化"):
        verify_frozen_inputs(tmp_path, ExternalSourceRoots(), minimal_config)
