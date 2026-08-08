from __future__ import annotations

import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "prettier_guard.py"
SPEC = importlib.util.spec_from_file_location("prettier_guard", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
HOOK = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HOOK
SPEC.loader.exec_module(HOOK)


class PrettierGuardTest(unittest.TestCase):
    def test_rejects_direct_and_common_wrapped_invocations(self) -> None:
        commands = (
            "prettier --write README.md",
            "./node_modules/.bin/prettier --check README.md",
            "npx --yes prettier --check README.md",
            "npm exec -- prettier --write package.json",
            "pnpm prettier --write README.md",
            "pnpm exec prettier --check README.md",
            "yarn dlx prettier --write README.md",
            "bunx prettier --check README.md",
            "corepack pnpm run prettier",
            "printf data | bash -lc 'npx prettier --check README.md'",
            "node node_modules/prettier/bin/prettier.cjs --check README.md",
        )

        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(HOOK.inspect_command(command))

    def test_allows_text_mentions_and_non_execution_operations(self) -> None:
        commands = (
            "rg 'prettier --write' .Codex/docs",
            "cat prettier-migration.md",
            "printf '%s\\n' '禁止使用 prettier'",
            "npm view prettier version",
            "pnpm add prettier",
            "python3 -c \"print('prettier')\"",
            "command -v prettier",
        )

        for command in commands:
            with self.subTest(command=command):
                self.assertFalse(HOOK.inspect_command(command))

    def test_extracts_only_command_from_functions_exec(self) -> None:
        denied_payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "functions.exec",
            "tool_input": (
                "const r = await tools.exec_command({"
                "cmd: \"npx prettier --check README.md\"}); text(r.output);"
            ),
        }
        allowed_payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "functions.exec",
            "tool_input": (
                "const note = 'prettier --write'; "
                "const r = await tools.exec_command({cmd: \"pwd\"}); text(r.output);"
            ),
        }

        denied = HOOK.handle_hook_input(
            io.StringIO(json.dumps(denied_payload, ensure_ascii=False))
        )
        allowed = HOOK.handle_hook_input(
            io.StringIO(json.dumps(allowed_payload, ensure_ascii=False))
        )

        self.assertIsNotNone(denied)
        assert denied is not None
        self.assertEqual(
            denied["hookSpecificOutput"]["permissionDecision"], "deny"
        )
        self.assertIn(
            "禁止运行 Prettier",
            denied["hookSpecificOutput"]["permissionDecisionReason"],
        )
        self.assertIsNone(allowed)


if __name__ == "__main__":
    unittest.main()
