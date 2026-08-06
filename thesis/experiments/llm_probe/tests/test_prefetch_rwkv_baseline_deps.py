from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "prefetch_rwkv_baseline_deps.sh"


def test_validate_only_does_not_create_remote_artifacts(tmp_path: Path) -> None:
    config_path = tmp_path / "prefetch.json"
    config_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": "rwkv-baseline-deps-test",
                "output_root": "/root/autodl-tmp/thesis/experiments/llm_probe/artifacts/rwkv-baseline-deps",
                "sources": [
                    {
                        "name": "RWKV-LM",
                        "repository": "https://github.com/BlinkDL/RWKV-LM.git",
                        "commit": "952102498e9ed367ea0a59ee64106916d474d30f",
                    }
                ],
                "audit_packages": ["torch", "numpy"],
                "download_requirements": ["ninja", "wheel"],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", str(SCRIPT), str(config_path)],
        cwd=PROJECT_ROOT,
        env={**os.environ, "RWKV_PREFETCH_VALIDATE_ONLY": "1"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "status": "validated",
        "run_id": "rwkv-baseline-deps-test",
        "source_count": 1,
        "audit_package_count": 2,
        "download_requirement_count": 2,
        "missing_command_probe": None,
    }


def test_prepare_output_root_creates_missing_parent(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "rwkv-baseline-deps"

    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; prepare_output_root "$2"',
            "_",
            str(SCRIPT),
            str(output_root),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert output_root.is_dir()
