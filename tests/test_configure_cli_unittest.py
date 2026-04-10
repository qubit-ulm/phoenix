from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from phoenix.configure.cli import main
from phoenix.fgen.backend_config import Configuration


class ConfigureCliTests(unittest.TestCase):
    def test_dialogue_accepts_all_via_positional_target(self):
        calls = []

        def fake_configure_backend_dialogue(_self, name):
            calls.append(name)
            return f"/tmp/{name}.json", {}, []

        with patch(
            "phoenix.configure.service.ConfigurationService.configure_backend_dialogue",
            new=fake_configure_backend_dialogue,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(main(["all", "--dialogue"]), 0)

        self.assertTrue(calls)
        self.assertIn("Wrote /tmp/", stdout.getvalue())

    def test_build_accepts_backend_via_positional_target(self):
        calls = []

        def fake_build_backend_support(_self, name):
            calls.append(name)
            return [f"build {name}"]

        with patch(
            "phoenix.configure.service.ConfigurationService.build_backend_support",
            new=fake_build_backend_support,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(main(["fortran", "--build"]), 0)

        self.assertEqual(calls, ["fortran"])
        self.assertIn("build fortran", stdout.getvalue())

    def test_build_all_runs_all_backends(self):
        calls = []

        def fake_build_backend_support(_self, name):
            calls.append(name)
            return [f"build {name}"]

        with patch(
            "phoenix.configure.service.ConfigurationService.build_backend_support",
            new=fake_build_backend_support,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(main(["--build"]), 0)

        self.assertTrue(calls)
        self.assertIn("build ", stdout.getvalue())

    def test_build_accepts_all_via_positional_target(self):
        calls = []

        def fake_build_backend_support(_self, name):
            calls.append(name)
            return [f"build {name}"]

        with patch(
            "phoenix.configure.service.ConfigurationService.build_backend_support",
            new=fake_build_backend_support,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(main(["all", "--build"]), 0)

        self.assertTrue(calls)
        self.assertIn("build ", stdout.getvalue())

    def test_initialize_auto_writes_selected_backends(self):
        def fake_initialize_auto(_self):
            return {
                "fortran": Path("/tmp/fortran.json"),
                "python": Path("/tmp/python.json"),
            }

        with patch(
            "phoenix.configure.service.ConfigurationService.initialize_auto",
            new=fake_initialize_auto,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(main(["--initialize-auto"]), 0)

        output = stdout.getvalue()
        self.assertIn("fortran: wrote /tmp/fortran.json", output)
        self.assertIn("python: wrote /tmp/python.json", output)

    def test_dialogue_accepts_backend_via_positional_target(self):
        calls = []

        def fake_configure_backend_dialogue(_self, name):
            calls.append(name)
            return "/tmp/fake.json", {}, []

        with patch(
            "phoenix.configure.service.ConfigurationService.configure_backend_dialogue",
            new=fake_configure_backend_dialogue,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(main(["fortran", "--dialogue"]), 0)

        self.assertEqual(calls, ["fortran"])
        self.assertIn("Wrote /tmp/fake.json", stdout.getvalue())

    def test_dialogue_without_backend_runs_all(self):
        calls = []

        def fake_configure_backend_dialogue(_self, name):
            calls.append(name)
            return f"/tmp/{name}.json", {}, []

        with patch(
            "phoenix.configure.service.ConfigurationService.configure_backend_dialogue",
            new=fake_configure_backend_dialogue,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(main(["--dialogue"]), 0)

        self.assertTrue(calls)
        self.assertIn("Wrote /tmp/", stdout.getvalue())

    def test_reset_accepts_backend_via_positional_target(self):
        calls = []

        def fake_reset_backend(_self, name):
            calls.append(name)
            return "/tmp/reset.json", {}, ["reset ok"]

        with patch(
            "phoenix.configure.service.ConfigurationService.reset_backend",
            new=fake_reset_backend,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(main(["fortran", "--reset"]), 0)

        self.assertEqual(calls, ["fortran"])
        self.assertIn("Wrote /tmp/reset.json", stdout.getvalue())
        self.assertIn("reset ok", stdout.getvalue())

    def test_reset_accepts_all(self):
        calls = []

        def fake_reset_backend(_self, name):
            calls.append(name)
            return f"/tmp/{name}.json", {}, [f"reset {name}"]

        with patch(
            "phoenix.configure.service.ConfigurationService.reset_backend",
            new=fake_reset_backend,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(main(["--reset", "all"]), 0)

        self.assertTrue(calls)
        self.assertIn("reset ", stdout.getvalue())

    def test_test_accepts_all_via_positional_target(self):
        reports = []

        def fake_run_selected_backend_tests(name):
            reports.append(name)
            return []

        with patch(
            "phoenix.configure.testing.run_selected_backend_tests",
            new=fake_run_selected_backend_tests,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(main(["all", "--test", "all"]), 0)

        self.assertEqual(reports, ["all"])

    def test_clear_removes_backend_configuration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backends_root = Path(tmpdir) / "backends"
            config_root = backends_root / "config"
            config_root.mkdir(parents=True)
            (config_root / "general.json").write_text(
                json.dumps(
                    {
                        "logging": {"level": "INFO", "stdout": False},
                        "paths": {"build_root": "phoenix_build"},
                        "runtime": {"num_processors": 1},
                    }
                )
                + "\n",
                encoding="ascii",
            )
            fortran_root = backends_root / "fortran"
            fortran_root.mkdir(parents=True)
            config_path = fortran_root / "fortran_default.json"
            config_path.write_text(
                json.dumps({"backend": "fortran", "enabled": True}) + "\n",
                encoding="ascii",
            )

            with patch.object(Configuration, "BACKENDS_ROOT", backends_root), patch.object(
                Configuration, "CONFIG_ROOT", config_root
            ):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(main(["fortran", "--clear"]), 0)

            self.assertFalse(config_path.exists())
            self.assertIn("Cleared", stdout.getvalue())

    def test_clear_all_removes_all_backend_configurations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backends_root = Path(tmpdir) / "backends"
            config_root = backends_root / "config"
            config_root.mkdir(parents=True)
            (config_root / "general.json").write_text(
                json.dumps(
                    {
                        "logging": {"level": "INFO", "stdout": False},
                        "paths": {"build_root": "phoenix_build"},
                        "runtime": {"num_processors": 1},
                    }
                )
                + "\n",
                encoding="ascii",
            )
            created = []
            for backend in ("fortran", "python"):
                backend_root = backends_root / backend
                backend_root.mkdir(parents=True)
                config_path = backend_root / f"{backend}_default.json"
                config_path.write_text(
                    json.dumps({"backend": backend, "enabled": True}) + "\n",
                    encoding="ascii",
                )
                created.append(config_path)

            with patch.object(Configuration, "BACKENDS_ROOT", backends_root), patch.object(
                Configuration, "CONFIG_ROOT", config_root
            ):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(main(["--clear"]), 0)

            for config_path in created:
                self.assertFalse(config_path.exists())
            self.assertIn("Cleared", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
