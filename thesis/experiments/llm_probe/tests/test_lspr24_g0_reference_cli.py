from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


DEVELOPMENT_SCOPE = "development-visible-first-80-percent"


def _run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "flow_probe.lspr24_g0_reference", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def test_cli_exposes_one_development_only_entry_and_fails_closed(tmp_path: Path) -> None:
    project_text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert (
        'flow-probe-lspr24-g0-reference = "flow_probe.lspr24_g0_reference:main"'
        in project_text
    )

    input_path = tmp_path / "development.json"
    output_path = tmp_path / "reference.json"
    input_path.write_text(
        json.dumps(
            {
                "schema_version": "lspr24-g0-development-reference-input-v1",
                "scope": DEVELOPMENT_SCOPE,
                "rows": [
                    {
                        "protected_endpoint_id": "01" * 32,
                        "last_ns": 5_000_000_000,
                        "start_ns": 1,
                        "raw_flow_id": "02" * 32,
                        "endpoint_role_order": "source",
                        "source_row_index": 0,
                        "values": [
                            {
                                "type": "fixed_decimal_12",
                                "value": "1.0000000000005",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    materialize = _run_cli(
        "materialize",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
    )

    assert materialize.returncode == 0, materialize.stderr
    assert json.loads(materialize.stdout)["status"] == "PASS"
    assert output_path.exists()
    frozen_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()

    compare = _run_cli(
        "compare",
        "--expected",
        str(output_path),
        "--actual",
        str(output_path),
    )
    assert compare.returncode == 0, compare.stderr
    assert json.loads(compare.stdout)["status"] == "PASS"

    overwrite = _run_cli(
        "materialize",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
    )
    assert overwrite.returncode != 0
    assert hashlib.sha256(output_path.read_bytes()).hexdigest() == frozen_hash

    final_input = tmp_path / "final-test.json"
    final_output = tmp_path / "forbidden-final-reference.json"
    final_input.write_text(
        json.dumps(
            {
                "schema_version": "lspr24-g0-development-reference-input-v1",
                "scope": "final-test",
                "rows": [],
            }
        ),
        encoding="utf-8",
    )
    rejected = _run_cli(
        "materialize",
        "--input",
        str(final_input),
        "--output",
        str(final_output),
    )
    assert rejected.returncode != 0
    assert "最终区" in rejected.stderr
    assert not final_output.exists()
