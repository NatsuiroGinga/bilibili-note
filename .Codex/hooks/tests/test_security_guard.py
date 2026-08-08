from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

USER_HOOKS = Path.home() / ".codex/hooks.json"
USER_GUARD = Path.home() / ".codex/hooks/security-guard.js"
USER_LAUNCHER = Path.home() / ".codex/hooks/run-node-hook.sh"


class SecurityGuardTest(unittest.TestCase):
    def _run_guard(self, command: str) -> subprocess.CompletedProcess[str]:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": str(Path.cwd()),
        }
        return subprocess.run(
            ["node", str(USER_GUARD)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )

    def test_neutral_bash_is_silent(self) -> None:
        result = self._run_guard("printf '%s\\n' 安全")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_catastrophic_bash_uses_pretooluse_deny(self) -> None:
        result = self._run_guard("rm -rf /")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        output = json.loads(result.stdout)
        self.assertEqual(set(output), {"hookSpecificOutput"})
        decision = output["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("灾难性命令", decision["permissionDecisionReason"])

    def test_confirm_branch_uses_pretooluse_ask(self) -> None:
        result = self._run_guard("git reset --hard")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        output = json.loads(result.stdout)
        self.assertEqual(set(output), {"hookSpecificOutput"})
        decision = output["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "ask")
        self.assertIn("git reset --hard", decision["permissionDecisionReason"])

    def test_active_configuration_uses_launcher_without_prompt_injection(self) -> None:
        configuration = json.loads(USER_HOOKS.read_text(encoding="utf-8"))
        hooks = configuration["hooks"]
        pre_tool_use = hooks["PreToolUse"]

        self.assertEqual(len(pre_tool_use), 1)
        self.assertEqual(pre_tool_use[0]["matcher"], "Bash")
        self.assertEqual(
            pre_tool_use[0]["hooks"][0]["command"],
            f'/bin/sh "{USER_LAUNCHER}" "security-guard.js"',
        )
        self.assertNotIn("UserPromptSubmit", hooks)


if __name__ == "__main__":
    unittest.main()
