from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = PROJECT_ROOT / "thesis/experiments/llm_probe/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import guarded_execution_common as common  # noqa: E402
import guarded_remote_runner as remote_runner  # noqa: E402
import guarded_remote_stage as remote_stage  # noqa: E402
import guarded_rsync as guarded_rsync  # noqa: E402
import guarded_uv_sync as guarded_uv_sync  # noqa: E402


def _completed(
    argv: list[str],
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, returncode, stdout, stderr)


class GuardedRsyncTest(unittest.TestCase):
    def test_plan_allows_whitelisted_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "src/module.py"
            source.parent.mkdir()
            source.write_text("value = 1\n", encoding="utf-8")

            plan = guarded_rsync.build_sync_plan("src/module.py", project_root=root)

            self.assertEqual(plan.source_relative, "src/module.py")
            self.assertEqual(len(plan.sha256), 64)
            self.assertTrue(plan.remote_absolute.endswith("/src/module.py"))

    def test_plan_rejects_parent_escape_and_run_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(common.GuardViolation):
                guarded_rsync.build_sync_plan("../secret", project_root=root)
            with self.assertRaises(common.GuardViolation):
                guarded_rsync.build_sync_plan("runs/result.json", project_root=root)

    def test_plan_rejects_symlink_bypass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "real.py"
            source.write_text("value = 1\n", encoding="utf-8")
            link = root / "src/link.py"
            link.parent.mkdir()
            link.symlink_to(source)

            with self.assertRaises(common.GuardViolation):
                guarded_rsync.build_sync_plan("src/link.py", project_root=root)

    def test_apply_creates_parent_transfers_and_verifies_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "scripts/stage.sh"
            source.parent.mkdir()
            source.write_text("printf ok\n", encoding="utf-8")
            plan = guarded_rsync.build_sync_plan("scripts/stage.sh", project_root=root)
            fake_exec = root / "gpu-exec.exp"
            fake_rsync = root / "gpu-rsync-push.exp"
            fake_exec.write_text("", encoding="utf-8")
            fake_rsync.write_text("", encoding="utf-8")
            calls: list[list[str]] = []

            def runner(
                argv: list[str], **_: object
            ) -> subprocess.CompletedProcess[str]:
                calls.append(argv)
                stdout = plan.sha256 if "sha256sum" in argv[-1] else ""
                return _completed(argv, stdout=stdout)

            with mock.patch.object(
                guarded_rsync, "GPU_EXEC", fake_exec
            ), mock.patch.object(guarded_rsync, "GPU_RSYNC", fake_rsync):
                result = guarded_rsync.apply_sync_plan(plan, runner=runner)

            self.assertEqual(result["verify_exit_code"], 0)
            self.assertEqual(len(calls), 3)
            self.assertIn("mkdir -p", calls[0][-1])
            self.assertEqual(calls[1][1], str(fake_rsync))

    def test_apply_rejects_remote_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "scripts/stage.sh"
            source.parent.mkdir()
            source.write_text("printf ok\n", encoding="utf-8")
            plan = guarded_rsync.build_sync_plan("scripts/stage.sh", project_root=root)
            fake_exec = root / "gpu-exec.exp"
            fake_rsync = root / "gpu-rsync-push.exp"
            fake_exec.write_text("", encoding="utf-8")
            fake_rsync.write_text("", encoding="utf-8")

            def runner(
                argv: list[str], **_: object
            ) -> subprocess.CompletedProcess[str]:
                stdout = "0" * 64 if "sha256sum" in argv[-1] else ""
                return _completed(argv, stdout=stdout)

            with mock.patch.object(
                guarded_rsync, "GPU_EXEC", fake_exec
            ), mock.patch.object(
                guarded_rsync, "GPU_RSYNC", fake_rsync
            ), self.assertRaises(
                common.GuardViolation
            ):
                guarded_rsync.apply_sync_plan(plan, runner=runner)

    def test_prepare_only_preserves_sanitized_failure_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "scripts/stage.sh"
            source.parent.mkdir()
            source.write_text("printf ok\n", encoding="utf-8")
            plan = guarded_rsync.build_sync_plan("scripts/stage.sh", project_root=root)
            fake_exec = root / "gpu-exec.exp"
            fake_exec.write_text("", encoding="utf-8")
            password = "diagnostic-secret-password"
            remote = "ssh -p 12345 tester@example.invalid"

            def runner(
                argv: list[str], **_: object
            ) -> subprocess.CompletedProcess[str]:
                return _completed(
                    argv,
                    returncode=17,
                    stdout=f"spawn {remote}\npassword={password}\n",
                    stderr=(
                        "ssh: connect to host example.invalid port 12345: 连接失败\n"
                        "tester@example.invalid\n"
                        f"{'x' * 2500}"
                    ),
                )

            with mock.patch.object(
                guarded_rsync, "GPU_EXEC", fake_exec
            ), mock.patch.dict(
                os.environ,
                {"GPU_PWD": password, "GPU_SSH": remote},
            ), self.assertRaises(
                guarded_rsync.ManagedCommandFailure
            ) as raised:
                guarded_rsync.prepare_remote_parent(plan, runner=runner)

            diagnostic = raised.exception.diagnostic
            self.assertEqual(diagnostic["step"], "prepare")
            self.assertEqual(diagnostic["exit_code"], 17)
            serialized = json.dumps(diagnostic, ensure_ascii=False)
            self.assertNotIn(password, serialized)
            self.assertNotIn("tester@example.invalid", serialized)
            self.assertNotIn("example.invalid", serialized)
            self.assertNotIn("12345", serialized)
            self.assertIn("<凭据已脱敏>", serialized)
            self.assertIn("<端口已脱敏>", serialized)
            self.assertIn("<诊断已截断>", serialized)

    def test_prepare_only_never_starts_transfer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "scripts/stage.sh"
            source.parent.mkdir()
            source.write_text("printf ok\n", encoding="utf-8")
            plan = guarded_rsync.build_sync_plan("scripts/stage.sh", project_root=root)
            fake_exec = root / "gpu-exec.exp"
            fake_exec.write_text("", encoding="utf-8")
            calls: list[list[str]] = []

            def runner(
                argv: list[str], **_: object
            ) -> subprocess.CompletedProcess[str]:
                calls.append(argv)
                return _completed(argv)

            with mock.patch.object(guarded_rsync, "GPU_EXEC", fake_exec):
                result = guarded_rsync.prepare_remote_parent(plan, runner=runner)

            self.assertEqual(result, {"prepare_exit_code": 0})
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][1], str(fake_exec))


class GuardedUvSyncTest(unittest.TestCase):
    def test_exact_commands_fix_locked_gpu_extra(self) -> None:
        dry_run, apply = guarded_uv_sync.uv_commands()

        self.assertEqual(apply, ["uv", "sync", "--locked", "--extra", "gpu"])
        self.assertEqual(dry_run, [*apply, "--dry-run"])

    def test_dry_run_rejects_critical_removal(self) -> None:
        def runner(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            return _completed(argv, stdout="Would uninstall torch 2.7.0\n")

        with self.assertRaises(common.GuardViolation):
            guarded_uv_sync.execute_uv_sync(
                apply=False,
                hardware_tier="gpu",
                runner=runner,
            )

    def test_safe_plan_does_not_apply(self) -> None:
        calls: list[list[str]] = []

        def runner(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            calls.append(argv)
            return _completed(argv, stdout="Would install package 1.0\n")

        result = guarded_uv_sync.execute_uv_sync(
            apply=False,
            hardware_tier="cpu",
            runner=runner,
        )

        self.assertEqual(result["dry_run_exit_code"], 0)
        self.assertEqual(len(calls), 1)

    def test_safe_apply_runs_import_check(self) -> None:
        calls: list[list[str]] = []

        def runner(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            calls.append(argv)
            return _completed(argv)

        result = guarded_uv_sync.execute_uv_sync(
            apply=True,
            hardware_tier="cpu",
            runner=runner,
        )

        self.assertEqual(result["apply_exit_code"], 0)
        self.assertEqual(result["import_check_exit_code"], 0)
        self.assertEqual(len(calls), 3)


class GuardedRemoteStageTest(unittest.TestCase):
    def _fixture(self, root: Path) -> remote_stage.RemoteStagePlan:
        script = root / "scripts/stage.sh"
        params = root / "configs/stage.json"
        script.parent.mkdir()
        params.parent.mkdir()
        script.write_text("printf 'ok\\n'\n", encoding="utf-8")
        params.write_text('{"seed": 42}\n', encoding="utf-8")
        return remote_stage.build_stage_plan(
            script="scripts/stage.sh",
            params="configs/stage.json",
            log="runs/probe/console.log",
            state="runs/probe/run_state.json",
            capabilities="runs/probe/capabilities.json",
            project_root=root,
        )

    def test_plan_and_command_preserve_fixed_order_and_single_line(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan = self._fixture(Path(temporary))

            command = remote_stage.build_remote_command(plan)

            self.assertLess(command.index("source ~/.bashrc"), command.index("set -E"))
            self.assertNotIn("\n", command)
            self.assertNotIn("\\n", command)
            self.assertIn("guarded_remote_runner.py", command)

    def test_plan_rejects_non_script_and_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            (root / "configs").mkdir()
            (root / "src/stage.py").write_text("", encoding="utf-8")
            (root / "configs/stage.json").write_text("not-json", encoding="utf-8")

            with self.assertRaises(common.GuardViolation):
                remote_stage.build_stage_plan(
                    script="src/stage.py",
                    params="configs/stage.json",
                    log="runs/probe/console.log",
                    state="runs/probe/state.json",
                    capabilities="runs/probe/capabilities.json",
                    project_root=root,
                )

    def test_main_writes_managed_failure_diagnostic_to_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            receipt = Path(temporary) / "stage-receipt.json"
            plan = remote_stage.RemoteStagePlan(
                script="scripts/stage.sh",
                params="configs/stage.json",
                log="runs/probe/console.log",
                state="runs/probe/state.json",
                capabilities="runs/probe/capabilities.json",
                script_sha256="1" * 64,
                params_sha256="2" * 64,
            )
            failure = guarded_rsync.ManagedCommandFailure(
                "远端目标父目录创建或验证失败。",
                step="prepare",
                result=_completed(
                    ["expect"],
                    returncode=17,
                    stderr="受管入口失败",
                ),
            )
            parser = mock.Mock()
            parser.parse_args.return_value = mock.Mock(
                script=plan.script,
                params=plan.params,
                log=plan.log,
                state=plan.state,
                capabilities=plan.capabilities,
                receipt="runs/probe/receipt.json",
                apply=True,
            )

            with mock.patch.object(
                remote_stage, "_parser", return_value=parser
            ), mock.patch.object(
                remote_stage,
                "local_receipt_path",
                return_value=receipt,
            ), mock.patch.object(
                remote_stage,
                "build_stage_plan",
                return_value=plan,
            ), mock.patch.object(
                remote_stage,
                "apply_stage_plan",
                side_effect=failure,
            ), mock.patch(
                "builtins.print"
            ):
                exit_code = remote_stage.main()

            payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 2)
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["diagnostic"]["step"], "prepare")
            self.assertEqual(payload["diagnostic"]["exit_code"], 17)
            self.assertEqual(payload["diagnostic"]["stderr"], "受管入口失败")


class LoggedProcessTest(unittest.TestCase):
    def test_success_creates_parent_and_nonempty_log(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "nested/console.log"
            result = remote_runner.run_logged_process(
                ["bash", "-c", "printf ok"],
                cwd=Path(temporary),
                log_path=log,
            )

            self.assertEqual(result.final_exit_code, 0)
            self.assertTrue(result.log_nonempty)
            self.assertEqual(log.read_text(encoding="utf-8"), "ok")

    def test_process_failure_preserves_original_exit_code_when_log_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = remote_runner.run_logged_process(
                ["bash", "-c", "exit 7"],
                cwd=Path(temporary),
                log_path=Path(temporary) / "console.log",
            )

            self.assertEqual(result.process_exit_code, 7)
            self.assertEqual(result.final_exit_code, 7)
            self.assertFalse(result.log_nonempty)

    def test_empty_success_becomes_generic_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = remote_runner.run_logged_process(
                ["bash", "-c", "true"],
                cwd=Path(temporary),
                log_path=Path(temporary) / "console.log",
            )

            self.assertEqual(result.process_exit_code, 0)
            self.assertEqual(result.final_exit_code, 1)

    def test_unwritable_target_fails_before_process_start(self) -> None:
        def reject(_: Path):
            raise OSError("不可写")

        with tempfile.TemporaryDirectory() as temporary:
            result = remote_runner.run_logged_process(
                ["bash", "-c", "printf should-not-run"],
                cwd=Path(temporary),
                log_path=Path(temporary) / "console.log",
                open_log=reject,
            )

            self.assertIsNone(result.process_exit_code)
            self.assertEqual(result.logger_exit_code, 1)
            self.assertEqual(result.final_exit_code, 1)

    def test_stage_writes_finished_state_and_capability_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = GuardedRemoteStageTest()._fixture(root)
            state_path = root / plan.state
            capabilities_path = root / plan.capabilities
            with mock.patch.dict(
                os.environ, {"GUARDED_BASHRC_LOADED": "1"}
            ), mock.patch.object(
                remote_runner,
                "collect_capabilities",
                return_value={"schema_version": 1, "commands": {}},
            ):
                exit_code = remote_runner.execute_stage(
                    project_root=root,
                    script_value=plan.script,
                    params_value=plan.params,
                    log_value=plan.log,
                    state_value=plan.state,
                    capabilities_value=plan.capabilities,
                    expected_script_sha256=plan.script_sha256,
                    expected_params_sha256=plan.params_sha256,
                )

            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(state["status"], "finished")
            self.assertTrue(capabilities_path.is_file())


if __name__ == "__main__":
    unittest.main()
