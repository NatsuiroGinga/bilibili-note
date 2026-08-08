from __future__ import annotations

import datetime as dt
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "precompact_snapshot.py"
SPEC = importlib.util.spec_from_file_location("precompact_snapshot", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
HOOK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOOK)


class PreCompactSnapshotTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        (self.root / ".codex").mkdir()
        (self.root / ".Codex/docs/sdd/task-17-observability").mkdir(parents=True)
        (self.root / "output").mkdir()
        (self.root / "AGENTS.md").write_text("# 强制规则\n", encoding="utf-8")
        (self.root / ".codex/precompact_snapshot.json").write_text(
            json.dumps(
                {
                    "enabled": True,
                    "active_plan": (
                        ".Codex/docs/sdd/task-17-observability/task_plan.md"
                    ),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.plan = self.root / ".Codex/docs/sdd/task-17-observability/task_plan.md"
        self.plan.write_text(
            "# 任务十七\n\n## 当前状态\n\n- 已完成 210/210。\n\n## 下一步\n\n- 运行辨识。\n",
            encoding="utf-8",
        )
        self.documents = [
            self.root / "output/开题改进交接文档.md",
            self.root / "output/第一创新点实验总控.md",
        ]
        for index, document in enumerate(self.documents, start=1):
            document.write_text(f"# 人工正文 {index}\n\n不得覆盖。\n", encoding="utf-8")
        self.payload = {
            "session_id": "test-session",
            "turn_id": "test-turn",
            "transcript_path": None,
            "cwd": str(self.root),
            "hook_event_name": "PreCompact",
            "model": "gpt-test",
            "trigger": "manual",
        }
        self.now = dt.datetime(2026, 7, 22, 18, 0, tzinfo=dt.timezone.utc)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_sample_input_matches_official_required_fields(self) -> None:
        sample_path = Path(__file__).with_name("precompact-input.json")
        sample = json.loads(sample_path.read_text(encoding="utf-8"))
        self.assertTrue(HOOK.REQUIRED_INPUT_KEYS.issubset(sample))
        self.assertEqual(sample["hook_event_name"], "PreCompact")
        self.assertIn(sample["trigger"], {"manual", "auto"})

    def test_parse_payload_accepts_minimal_payload_without_optional_fields(self) -> None:
        import io

        resolved_root = self.root.resolve()
        minimal_payload = {
            "session_id": "test-session",
            "transcript_path": None,
            "cwd": str(resolved_root),
            "hook_event_name": "PreCompact",
            "trigger": "manual",
        }
        stream = io.StringIO(json.dumps(minimal_payload))
        parsed = HOOK._parse_payload(stream, resolved_root)
        self.assertEqual(parsed["hook_event_name"], "PreCompact")
        self.assertEqual(parsed["trigger"], "manual")
        self.assertNotIn("turn_id", parsed)
        self.assertNotIn("model", parsed)

    def test_updates_temporary_documents_without_overwriting_manual_body(self) -> None:
        result = HOOK.handle_event(self.payload, self.root, now=self.now)

        self.assertTrue(result["continue"])
        for document in self.documents:
            content = document.read_text(encoding="utf-8")
            self.assertIn("不得覆盖。", content)
            self.assertIn("- 已完成 210/210。", content)
            self.assertEqual(content.count(HOOK.START_MARKER), 1)
            self.assertEqual(content.count(HOOK.END_MARKER), 1)

    def test_repeated_trigger_keeps_a_single_snapshot_block(self) -> None:
        HOOK.handle_event(self.payload, self.root, now=self.now)
        result = HOOK.handle_event(self.payload, self.root, now=self.now)

        self.assertTrue(result["continue"])
        for document in self.documents:
            content = document.read_text(encoding="utf-8")
            self.assertEqual(content.count(HOOK.START_MARKER), 1)
            self.assertEqual(content.count(HOOK.END_MARKER), 1)

    def test_missing_source_preserves_existing_documents_and_reports_failure(
        self,
    ) -> None:
        before = {
            document: document.read_text(encoding="utf-8")
            for document in self.documents
        }
        self.plan.unlink()

        result = HOOK.handle_event(self.payload, self.root, now=self.now)

        self.assertTrue(result["continue"])
        self.assertIn("systemMessage", result)
        self.assertIn("活动计划不存在", result["systemMessage"])
        for document in self.documents:
            self.assertEqual(document.read_text(encoding="utf-8"), before[document])

    def test_malformed_markers_preserve_both_documents(self) -> None:
        self.documents[0].write_text(
            f"# 人工正文\n\n{HOOK.START_MARKER}\n损坏区块\n", encoding="utf-8"
        )
        before = {
            document: document.read_text(encoding="utf-8")
            for document in self.documents
        }

        result = HOOK.handle_event(self.payload, self.root, now=self.now)

        self.assertTrue(result["continue"])
        self.assertIn("systemMessage", result)
        for document in self.documents:
            self.assertEqual(document.read_text(encoding="utf-8"), before[document])

    def test_disabled_config_does_not_modify_documents(self) -> None:
        (self.root / ".codex/precompact_snapshot.json").write_text(
            json.dumps(
                {
                    "enabled": False,
                    "active_plan": (
                        ".Codex/docs/sdd/task-17-observability/task_plan.md"
                    ),
                }
            ),
            encoding="utf-8",
        )
        before = [document.read_bytes() for document in self.documents]

        result = HOOK.handle_event(self.payload, self.root, now=self.now)

        self.assertEqual(result, {"continue": True, "suppressOutput": True})
        self.assertEqual([document.read_bytes() for document in self.documents], before)


if __name__ == "__main__":
    unittest.main()
