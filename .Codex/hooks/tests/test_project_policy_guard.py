from __future__ import annotations

import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "project_policy_guard.py"
HOOK_DIRECTORY = str(SCRIPT_PATH.parent)
if HOOK_DIRECTORY not in sys.path:
    sys.path.insert(0, HOOK_DIRECTORY)
SPEC = importlib.util.spec_from_file_location("project_policy_guard", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
HOOK = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HOOK
SPEC.loader.exec_module(HOOK)


class ProjectPolicyGuardTest(unittest.TestCase):
    def _shell_payload(
        self, command: str, cwd: Path | None = None
    ) -> dict[str, object]:
        return {
            "hook_event_name": "PreToolUse",
            "cwd": str(cwd or HOOK.PROJECT_ROOT / HOOK.LLM_PROBE_RELATIVE),
            "tool_name": "Bash",
            "tool_input": {"command": command},
        }

    def _decision(self, command: str, cwd: Path | None = None):
        return HOOK.inspect_payload(self._shell_payload(command, cwd))

    def test_agent_name_allows_semantic_name(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "cwd": str(HOOK.PROJECT_ROOT),
            "tool_name": "Agent",
            "tool_input": {
                "task_name": "hook_policy_review",
                "message": "复核项目 Hook 策略的允许与拒绝边界。",
            },
        }

        self.assertFalse(HOOK.inspect_payload(payload).denied)

    def test_agent_name_rejects_generic_name(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "cwd": str(HOOK.PROJECT_ROOT),
            "tool_name": "Agent",
            "tool_input": {"task_name": "task1", "message": "执行一个具体检查任务。"},
        }

        decision = HOOK.inspect_payload(payload)
        self.assertTrue(decision.denied)
        self.assertEqual(decision.rule_id, "P1-AGENT")

    def test_agent_name_rejects_non_ascii_bypass(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "cwd": str(HOOK.PROJECT_ROOT),
            "tool_name": "spawn_agent",
            "tool_input": {"task_name": "任务一", "message": "尝试绕过语义名称门禁。"},
        }

        self.assertTrue(HOOK.inspect_payload(payload).denied)

    def test_remote_allows_single_read_only_query(self) -> None:
        command = (
            "source ~/.zshrc && expect /tmp/gpu-exec.exp "
            "'source ~/.bashrc; cd /root/autodl-tmp/thesis; df -h'"
        )

        self.assertFalse(self._decision(command).denied)

    def test_remote_allows_command_v_after_local_shell_setup(self) -> None:
        command = (
            "source ~/.zshrc && expect /tmp/gpu-exec.exp "
            "'source ~/.bashrc; command -v uv'"
        )

        self.assertFalse(self._decision(command).denied)

    def test_remote_allows_quoted_rg_alternation(self) -> None:
        command = (
            "source ~/.zshrc && expect /tmp/gpu-exec.exp "
            "'source ~/.bashrc; rg \"tcp|udp\" /root/autodl-tmp/thesis'"
        )

        self.assertFalse(self._decision(command).denied)

    def test_remote_allows_server_fdfind_executable(self) -> None:
        command = (
            "source ~/.zshrc && expect /tmp/gpu-exec.exp "
            "'source ~/.bashrc; /usr/bin/fdfind -t f . "
            "/root/autodl-tmp/thesis'"
        )

        self.assertFalse(self._decision(command).denied)

    def test_remote_rejects_noninteractive_fd_alias(self) -> None:
        command = (
            "source ~/.zshrc && expect /tmp/gpu-exec.exp "
            "'source ~/.bashrc; fd -t f . /root/autodl-tmp/thesis'"
        )

        self.assertTrue(self._decision(command).denied)

    def test_remote_rejects_real_pipeline(self) -> None:
        command = (
            "source ~/.zshrc && expect /tmp/gpu-exec.exp "
            "'source ~/.bashrc; rg tcp /root/autodl-tmp/thesis | wc -l'"
        )

        self.assertTrue(self._decision(command).denied)

    def test_remote_rejects_read_then_write(self) -> None:
        command = (
            "source ~/.zshrc && expect /tmp/gpu-exec.exp "
            "'source ~/.bashrc; rg tcp /root/autodl-tmp/thesis; "
            "touch /root/autodl-tmp/thesis/marker'"
        )

        self.assertTrue(self._decision(command).denied)

    def test_remote_rejects_direct_ssh(self) -> None:
        decision = self._decision("ssh host 'source ~/.bashrc; pwd'")

        self.assertTrue(decision.denied)
        self.assertEqual(decision.rule_id, "P1-REMOTE")

    def test_remote_rejects_nested_shell_bypass(self) -> None:
        decision = self._decision("bash -lc \"ssh host 'source ~/.bashrc; pwd'\"")

        self.assertTrue(decision.denied)
        self.assertEqual(decision.rule_id, "P1-REMOTE")

    def test_remote_rejects_literal_newline_bypass(self) -> None:
        command = (
            "expect /tmp/gpu-exec.exp "
            "'source ~/.bashrc; printf cmd\\nsecond /root/autodl-tmp/thesis'"
        )

        self.assertTrue(self._decision(command).denied)

    def test_rsync_allows_guarded_wrapper(self) -> None:
        command = (
            "python3 thesis/experiments/llm_probe/scripts/guarded_rsync.py "
            "--source src/flow_probe/config.py"
        )

        self.assertFalse(self._decision(command, HOOK.PROJECT_ROOT).denied)

    def test_rsync_rejects_direct_command(self) -> None:
        command = (
            "rsync -rtv thesis/experiments/llm_probe/src/ "
            "host:/root/autodl-tmp/thesis/experiments/llm_probe/src/"
        )

        decision = self._decision(command, HOOK.PROJECT_ROOT)
        self.assertTrue(decision.denied)
        self.assertEqual(decision.rule_id, "P1-RSYNC")

    def test_rsync_rejects_delete_bypass(self) -> None:
        command = (
            "bash -lc 'command rsync --delete thesis/experiments/llm_probe/src/ "
            "host:/root/autodl-tmp/thesis/experiments/llm_probe/src/'"
        )

        self.assertTrue(self._decision(command, HOOK.PROJECT_ROOT).denied)

    def test_pytest_allows_unittest(self) -> None:
        self.assertFalse(self._decision("python3 -m unittest -q").denied)

    def test_pytest_rejects_direct_command(self) -> None:
        decision = self._decision("pytest tests/test_config.py -q")

        self.assertTrue(decision.denied)
        self.assertEqual(decision.rule_id, "P1-PYTEST")

    def test_pytest_rejects_nested_uv_bypass(self) -> None:
        decision = self._decision("bash -lc 'uv run python3 -m pytest -q'")

        self.assertTrue(decision.denied)
        self.assertEqual(decision.rule_id, "P1-PYTEST")

    def test_uv_sync_allows_guarded_wrapper(self) -> None:
        command = "python3 scripts/guarded_uv_sync.py"

        self.assertFalse(self._decision(command).denied)

    def test_uv_sync_rejects_direct_command(self) -> None:
        decision = self._decision("uv sync --locked --extra gpu")

        self.assertTrue(decision.denied)
        self.assertEqual(decision.rule_id, "P1-UV-SYNC")

    def test_uv_sync_rejects_nested_command_bypass(self) -> None:
        decision = self._decision("zsh -lc 'command uv sync --locked --extra gpu'")

        self.assertTrue(decision.denied)

    def test_pytest_rejects_uv_options_bypass(self) -> None:
        decision = self._decision(
            "uv run --project . --with pytest python3 -m pytest -q"
        )

        self.assertTrue(decision.denied)

    def test_remote_rejects_wrapper_basename_outside_project(self) -> None:
        command = (
            "python3 /tmp/guarded_remote_stage.py --note GPU_SSH "
            "--script scripts/stage.sh"
        )

        decision = self._decision(command)
        self.assertTrue(decision.denied)
        self.assertEqual(decision.rule_id, "P1-REMOTE")

    def test_output_uses_supported_contract(self) -> None:
        payload = self._shell_payload("pytest -q")

        output = HOOK.handle_hook_input(io.StringIO(json.dumps(payload)))

        self.assertIsNotNone(output)
        assert output is not None
        self.assertEqual(set(output), {"hookSpecificOutput"})
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
