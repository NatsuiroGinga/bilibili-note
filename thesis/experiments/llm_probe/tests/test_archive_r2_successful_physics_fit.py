from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts/archive_r2_successful_physics_fit.sh"
REMOTE_PROJECT_ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe"
REQUIRED_ARTIFACTS = (
    "checkpoint-latest.pt",
    "checkpoint-binding-manifest.json",
    "zero-collapse-receipt.json",
    "result.json",
    "metrics.jsonl",
)


def _render_script(tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "project"
    source = SCRIPT.read_text(encoding="utf-8")
    script = tmp_path / "archive.sh"
    script.write_text(
        source.replace(REMOTE_PROJECT_ROOT, str(project_root)), encoding="utf-8"
    )
    return script, project_root


def test_archives_complete_source_atomically_and_rejects_missing_artifact(
    tmp_path: Path,
) -> None:
    script, project_root = _render_script(tmp_path)
    source_root = project_root / "runs/r2-minimal-sidecar-physics-fit/tcp-udp-v2-seed-42"
    source_root.mkdir(parents=True)
    expected_sha256 = {}
    for name in REQUIRED_ARTIFACTS:
        payload = f"old-{name}\n".encode("utf-8")
        (source_root / name).write_bytes(payload)
        expected_sha256[name] = hashlib.sha256(payload).hexdigest()

    completed = subprocess.run(
        ["bash", str(script)],
        check=False,
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    archive_parent = project_root / "runs/superseded-archives/r2-minimal-sidecar-physics-fit"
    archives = list(archive_parent.iterdir())
    assert len(archives) == 1
    archive_root = archives[0]
    assert archive_root.name.startswith("superseded-by-probe-fix-")
    assert source_root.is_dir()
    assert list(source_root.iterdir()) == []
    assert all((archive_root / name).is_file() for name in REQUIRED_ARTIFACTS)
    receipt = json.loads((archive_root / "archive-receipt.json").read_text(encoding="utf-8"))
    assert receipt["artifact_sha256"] == expected_sha256
    assert f"archive_root={archive_root}" in completed.stdout
    assert f"source_root={source_root}" in completed.stdout
    assert "status=finished" in completed.stdout

    rejected = subprocess.run(
        ["bash", str(script)],
        check=False,
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert rejected.returncode != 0
    assert "缺少或为空的成功制品" in rejected.stderr
    assert len(list(archive_parent.iterdir())) == 1
    assert list(source_root.iterdir()) == []
