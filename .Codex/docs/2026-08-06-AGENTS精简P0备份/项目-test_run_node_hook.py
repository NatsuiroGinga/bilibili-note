from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

LAUNCHER = Path(__file__).resolve().parents[1] / "run_node_hook.sh"


class RunNodeHookTest(unittest.TestCase):
    def _fixture(self, root: Path, script: str) -> Path:
        launcher = root / LAUNCHER.name
        shutil.copy2(LAUNCHER, launcher)
        (root / "session-start.js").write_text(script, encoding="utf-8")
        return launcher

    def test_preserves_stdin_stderr_and_child_exit_code(self) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node)
        assert node is not None

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            launcher = self._fixture(
                root,
                "const fs=require('fs');"
                "process.stdout.write(fs.readFileSync(0,'utf8'));"
                "process.stderr.write('子进程错误\\n');"
                "process.exit(23);",
            )
            env = os.environ.copy()
            env["PATH"] = f"{Path(node).parent}:/usr/bin:/bin"

            result = subprocess.run(
                ["/bin/sh", str(launcher), "session-start.js"],
                input='{"hook_event_name":"SessionStart"}',
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

        self.assertEqual(result.returncode, 23)
        self.assertEqual(result.stdout, '{"hook_event_name":"SessionStart"}')
        self.assertEqual(result.stderr, "子进程错误\n")

    def test_rejects_unknown_hook_name(self) -> None:
        result = subprocess.run(
            ["/bin/sh", str(LAUNCHER), "security-guard.js"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 64)
        self.assertIn("拒绝未知脚本", result.stderr)

    def test_reports_missing_node_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            launcher = self._fixture(root, "process.exit(0);")
            env = {"HOME": str(root), "PATH": ""}

            result = subprocess.run(
                ["/bin/sh", str(launcher), "session-start.js"],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

        self.assertEqual(result.returncode, 127)
        self.assertIn("找不到 Node.js", result.stderr)

    def test_recovers_node_from_nvm_with_restricted_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            launcher = self._fixture(root, "process.exit(0);")
            fake_bin = root / ".nvm/fake-bin"
            fake_bin.mkdir(parents=True)
            fake_node = fake_bin / "node"
            fake_node.write_text(
                "#!/bin/sh\nprintf '%s' \"$1\"\n",
                encoding="utf-8",
            )
            fake_node.chmod(0o755)
            (root / ".nvm/nvm.sh").write_text(
                'PATH="$NVM_DIR/fake-bin:$PATH"\nexport PATH\n',
                encoding="utf-8",
            )

            result = subprocess.run(
                ["/bin/sh", str(launcher), "session-start.js"],
                text=True,
                capture_output=True,
                check=False,
                env={"HOME": str(root), "PATH": ""},
            )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, str(root.resolve() / "session-start.js"))
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
