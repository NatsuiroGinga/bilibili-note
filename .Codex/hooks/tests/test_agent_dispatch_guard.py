from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_dispatch_guard import inspect_payload


BRIEF = (
    "唯一工作树为 `/tmp/project`，预期分支 `exp/test`。"
    "首个动作必须核对 `pwd` 与 `git branch --show-current`。"
)


def payload(task_name: str, model: str, effort: str = "high") -> dict[str, object]:
    return {
        "tool_name": "Agent",
        "tool_input": {
            "task_name": task_name,
            "model": model,
            "reasoning_effort": effort,
            "message": BRIEF,
        },
    }


class AgentDispatchGuardTest(unittest.TestCase):
    def test_versioned_current_model_names_map_exactly(self) -> None:
        valid_agents = (
            ("audit_task_gpt6_sol_high", "gpt-6-sol"),
            ("audit_task_gpt6_luna_high", "gpt-6-luna"),
            ("audit_task_gpt6_astra_high", "gpt-6-astra"),
            ("audit_task_gpt5_6_terra_high", "gpt-5.6-terra"),
        )

        for task_name, model in valid_agents:
            with self.subTest(task_name=task_name):
                self.assertEqual(inspect_payload(payload(task_name, model)), [])

    def test_legacy_unversioned_model_suffixes_are_rejected(self) -> None:
        for suffix, model in (
            ("sol", "gpt-6-sol"),
            ("terra", "gpt-5.6-terra"),
            ("luna", "gpt-6-luna"),
            ("astra", "gpt-6-astra"),
        ):
            with self.subTest(suffix=suffix):
                violations = inspect_payload(
                    payload(f"audit_task_{suffix}_high", model)
                )
                self.assertIsNotNone(violations)
                self.assertEqual(violations[0].rule_id, "ADG-NAME")

    def test_versioned_name_must_match_actual_model(self) -> None:
        violations = inspect_payload(
            payload("audit_task_gpt6_sol_high", "gpt-5.6-sol")
        )

        self.assertIsNotNone(violations)
        self.assertEqual([item.rule_id for item in violations], ["ADG-MODEL"])

    def test_effort_suffix_must_match_reasoning_effort(self) -> None:
        violations = inspect_payload(
            payload("audit_task_gpt6_luna_high", "gpt-6-luna", effort="medium")
        )

        self.assertIsNotNone(violations)
        self.assertEqual([item.rule_id for item in violations], ["ADG-EFFORT"])

    def test_worker_still_requires_shared_worktree_and_ownership_briefing(self) -> None:
        request = payload("audit_task_gpt6_luna_high", "gpt-6-luna")
        request["tool_input"]["agent_type"] = "worker"

        violations = inspect_payload(request)

        self.assertIsNotNone(violations)
        self.assertEqual(
            [item.rule_id for item in violations],
            ["ADG-BRIEF-OWNERSHIP", "ADG-BRIEF-SHARED", "ADG-BRIEF-REVERT"],
        )

    def test_non_default_gpt_5_6_models_are_not_part_of_current_policy(self) -> None:
        for model_tag, model in (
            ("gpt5_6_sol", "gpt-5.6-sol"),
            ("gpt5_6_luna", "gpt-5.6-luna"),
        ):
            with self.subTest(model=model):
                violations = inspect_payload(
                    payload(f"audit_task_{model_tag}_high", model)
                )
                self.assertIsNotNone(violations)
                self.assertEqual(violations[0].rule_id, "ADG-NAME")


if __name__ == "__main__":
    unittest.main()
