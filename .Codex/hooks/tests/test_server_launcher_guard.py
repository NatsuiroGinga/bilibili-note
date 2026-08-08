from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "server_launcher_guard.py"
SPEC = importlib.util.spec_from_file_location("server_launcher_guard", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
HOOK = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HOOK
SPEC.loader.exec_module(HOOK)


class ServerLauncherGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _payload(self, command: str, tool_name: str = "Bash") -> dict[str, object]:
        key = "command" if tool_name == "Bash" else "cmd"
        return {
            "hook_event_name": "PreToolUse",
            "cwd": str(self.root),
            "tool_name": tool_name,
            "tool_input": {key: command},
        }

    def test_rejects_set_u_before_bashrc_in_remote_command(self) -> None:
        payload = self._payload(
            "ssh host 'set -u; source ~/.bashrc; cd /root/autodl-tmp/thesis'"
        )

        output = HOOK.handle_hook_input(io.StringIO(json.dumps(payload)), self.root)

        decision = output["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("之前启用了 nounset", decision["permissionDecisionReason"])

    def test_correct_order_is_neutral_and_does_not_grant_permission(self) -> None:
        payload = self._payload(
            "ssh host 'source ~/.bashrc; set -u; cd /root/autodl-tmp/thesis'"
        )

        output = HOOK.handle_hook_input(io.StringIO(json.dumps(payload)), self.root)

        self.assertIsNone(output)

    def test_rejects_set_o_nounset_before_bashrc(self) -> None:
        decision = HOOK.inspect_text(
            "expect /tmp/gpu-exec.exp 'set -o nounset; source ~/.bashrc; nvidia-smi'"
        )

        self.assertTrue(decision.denied)
        self.assertIn("source ~/.bashrc", decision.reason)

    def test_rejects_wrong_order_inside_inline_screen_script(self) -> None:
        command = (
            'ssh host "screen -dmS train bash -lc '
            "'set -euo pipefail; source ~/.bashrc; cd /root/autodl-tmp/thesis'\""
        )

        decision = HOOK.inspect_text(command)

        self.assertTrue(decision.denied)
        self.assertIn("nounset", decision.reason)

    def test_unrelated_local_command_is_neutral(self) -> None:
        decision = HOOK.inspect_text("set -u; source ~/.bashrc; printf '%s\\n' local")

        self.assertEqual(decision.status, "neutral")

    def test_reads_referenced_expect_script_and_rejects_wrong_order(self) -> None:
        script = self.root / "launch.exp"
        script.write_text(
            'spawn ssh host\nsend "set -u; source ~/.bashrc; '
            'cd /root/autodl-tmp/thesis\\r"\n',
            encoding="utf-8",
        )
        payload = self._payload(f"expect {script}")

        decision = HOOK.inspect_payload(payload, self.root)

        self.assertTrue(decision.denied)
        self.assertEqual(decision.origin, str(script.resolve()))

    def test_file_mode_accepts_correct_server_launcher(self) -> None:
        script = self.root / "gpu-launch.sh"
        script.write_text(
            "#!/usr/bin/env bash\nsource ~/.bashrc\nset -u\ncd /root/autodl-tmp/thesis\n",
            encoding="utf-8",
        )

        decision = HOOK.inspect_file(script, self.root)

        self.assertEqual(decision.status, "pass")
        self.assertFalse(decision.denied)

    def test_file_mode_rejects_wrong_server_launcher(self) -> None:
        script = self.root / "gpu-launch.sh"
        script.write_text(
            "#!/usr/bin/env bash\nset -u\nsource ~/.bashrc\ncd /root/autodl-tmp/thesis\n",
            encoding="utf-8",
        )

        decision = HOOK.inspect_file(script, self.root)

        self.assertTrue(decision.denied)

    def test_extracts_nested_exec_command_from_functions_exec(self) -> None:
        source = (
            "const r = await tools.exec_command({"
            "cmd: \"expect /tmp/gpu-exec.exp 'set -u; source ~/.bashrc'\""
            "});"
        )
        payload = {
            "hook_event_name": "PreToolUse",
            "cwd": str(self.root),
            "tool_name": "functions.exec",
            "tool_input": {"source": source},
        }

        decision = HOOK.inspect_payload(payload, self.root)

        self.assertTrue(decision.denied)

    def test_exec_command_cmd_field_is_checked(self) -> None:
        payload = self._payload(
            "expect /tmp/gpu-exec.exp 'set -u; source ~/.bashrc'",
            tool_name="exec_command",
        )

        decision = HOOK.inspect_payload(payload, self.root)

        self.assertTrue(decision.denied)

    def test_malformed_hook_input_remains_neutral(self) -> None:
        output = HOOK.handle_hook_input(io.StringIO("not-json"), self.root)

        self.assertIsNone(output)

    def test_deny_output_only_uses_supported_pre_tool_use_fields(self) -> None:
        payload = self._payload(
            "ssh host 'set -u; source ~/.bashrc; cd /root/autodl-tmp/thesis'"
        )

        output = HOOK.handle_hook_input(io.StringIO(json.dumps(payload)), self.root)

        self.assertIsNotNone(output)
        assert output is not None
        self.assertEqual(set(output), {"hookSpecificOutput"})
        self.assertEqual(
            set(output["hookSpecificOutput"]),
            {
                "hookEventName",
                "permissionDecision",
                "permissionDecisionReason",
            },
        )

    def test_non_target_tool_remains_neutral(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "cwd": str(self.root),
            "tool_name": "apply_patch",
            "tool_input": {
                "patch": "set -u; source ~/.bashrc; /root/autodl-tmp/thesis"
            },
        }

        decision = HOOK.inspect_payload(payload, self.root)

        self.assertEqual(decision.status, "neutral")


if __name__ == "__main__":
    unittest.main()
