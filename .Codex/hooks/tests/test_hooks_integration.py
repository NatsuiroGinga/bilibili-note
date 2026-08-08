from __future__ import annotations

import json
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
HOOKS_CONFIG = PROJECT_ROOT / ".codex/hooks.json"
WORKING_DIRECTORIES = (
    PROJECT_ROOT,
    PROJECT_ROOT / "thesis/experiments/llm_probe",
    PROJECT_ROOT / "thesis/experiments/llm_probe/scripts",
)


def _hook_command(event: str) -> str:
    config = json.loads(HOOKS_CONFIG.read_text(encoding="utf-8"))
    return config["hooks"][event][0]["hooks"][0]["command"]


def _run_hook(
    command: str, payload: dict[str, object], cwd: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        shell=True,
        check=False,
    )


class HooksIntegrationTest(unittest.TestCase):
    def test_pre_tool_use_command_allows_and_denies_from_three_directories(
        self,
    ) -> None:
        command = _hook_command("PreToolUse")
        for cwd in WORKING_DIRECTORIES:
            with self.subTest(cwd=cwd, case="allow"):
                payload = {
                    "hook_event_name": "PreToolUse",
                    "cwd": str(cwd),
                    "tool_name": "Bash",
                    "tool_input": {
                        "command": "rg 'prettier --write' .Codex/docs"
                    },
                }
                result = _run_hook(command, payload, cwd)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")

            with self.subTest(cwd=cwd, case="deny"):
                payload["tool_input"] = {
                    "command": "npx prettier --check README.md"
                }
                result = _run_hook(command, payload, cwd)
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)
                self.assertEqual(set(output), {"hookSpecificOutput"})
                self.assertEqual(
                    output["hookSpecificOutput"]["permissionDecision"], "deny"
                )

    def test_precompact_command_updates_isolated_snapshot_from_three_directories(
        self,
    ) -> None:
        base_command = _hook_command("PreCompact")
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory)
            (fixture_root / ".codex").mkdir()
            plan_relative = Path(".Codex/docs/hook-p0-fixture/task_plan.md")
            plan = fixture_root / plan_relative
            plan.parent.mkdir(parents=True)
            plan.write_text(
                "# 隔离计划\n\n## 当前状态\n\n- 三目录快照验证。\n",
                encoding="utf-8",
            )
            (fixture_root / ".codex/precompact_snapshot.json").write_text(
                json.dumps(
                    {"enabled": True, "active_plan": plan_relative.as_posix()},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (fixture_root / "AGENTS.md").write_text("# 隔离规则\n", encoding="utf-8")
            output_directory = fixture_root / "output"
            output_directory.mkdir()
            documents = (
                output_directory / "开题改进交接文档.md",
                output_directory / "第一创新点实验总控.md",
            )
            for document in documents:
                document.write_text("# 隔离恢复文档\n", encoding="utf-8")

            command = f"{base_command} --project-root {shlex.quote(str(fixture_root))}"
            for index, cwd in enumerate(WORKING_DIRECTORIES, start=1):
                fixture_cwd = fixture_root / cwd.relative_to(PROJECT_ROOT)
                fixture_cwd.mkdir(parents=True, exist_ok=True)
                payload = {
                    "session_id": f"hook-p0-{index}",
                    "turn_id": f"turn-{index}",
                    "transcript_path": None,
                    "cwd": str(fixture_cwd),
                    "hook_event_name": "PreCompact",
                    "model": "integration-test",
                    "trigger": "manual",
                }
                with self.subTest(cwd=cwd):
                    result = _run_hook(command, payload, cwd)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    output = json.loads(result.stdout)
                    self.assertTrue(output["continue"])
                    for document in documents:
                        content = document.read_text(encoding="utf-8")
                        self.assertIn("三目录快照验证", content)
                        self.assertEqual(content.count("PRECOMPACT_SNAPSHOT_START"), 1)


if __name__ == "__main__":
    unittest.main()
