from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import PropertyMock, patch

from phoenix.configure.service import ConfigurationService
from phoenix.fgen.backend_config import Configuration


@dataclass
class _FakeConfigurator:
    name: str
    root: Path

    def load_current(self) -> dict:
        return {}

    def quick_scan(self) -> dict:
        return {}

    def merge_defaults(self, scan: dict, current: dict) -> dict:
        del scan, current
        return {"backend": self.name}

    def enrich_config(self, data: dict) -> dict:
        data = dict(data)
        data.setdefault("support", {})
        data["support"].setdefault("root", str(self.root / "support"))
        data["support"].setdefault("makefile", str(self.root / "support" / "Makefile"))
        return data

    def config_path(self) -> Path:
        return self.root / f"{self.name}_default.json"

    def write_support_files(self, data: dict) -> dict:
        support_root = Path(data["support"]["root"])
        support_root.mkdir(parents=True, exist_ok=True)
        Path(data["support"]["makefile"]).write_text(
            ".PHONY: support\nsupport:\n\t@echo fake\n",
            encoding="ascii",
        )
        return data


class ConfigureServiceTests(unittest.TestCase):
    def test_render_status_includes_ready_column(self):
        service = ConfigurationService()

        with patch.object(
            ConfigurationService,
            "backend_status_rows",
            return_value=[
                {
                    "backend": "fortran",
                    "state": "enabled",
                    "configured": "yes",
                    "enabled": "yes",
                    "detected": "yes",
                    "ready": "no",
                }
            ],
        ):
            rendered = service.render_status()

        self.assertIn("ready", rendered.splitlines()[0])
        self.assertIn("no", rendered)

    def test_backend_status_reports_ready_for_existing_support_artifact(self):
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
            support_library = backends_root / "fortran" / "support" / "lib" / "dummy.so"
            support_library.parent.mkdir(parents=True)
            support_library.write_text("", encoding="ascii")
            config_path = backends_root / "fortran" / "fortran_default.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                json.dumps(
                    {
                        "backend": "fortran",
                        "enabled": True,
                        "support": {"library_file": str(support_library)},
                    }
                )
                + "\n",
                encoding="ascii",
            )

            with patch.object(Configuration, "BACKENDS_ROOT", backends_root), patch.object(
                Configuration, "CONFIG_ROOT", config_root
            ):
                service = ConfigurationService()
                row_map = {row["backend"]: row for row in service.backend_status_rows()}

            self.assertEqual(row_map["fortran"]["configured"], "yes")
            self.assertEqual(row_map["fortran"]["ready"], "yes")

    def test_backend_status_reports_not_ready_for_missing_support_artifact(self):
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
            config_path = backends_root / "fortran" / "fortran_default.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                json.dumps(
                    {
                        "backend": "fortran",
                        "enabled": True,
                        "support": {
                            "library_file": str(
                                backends_root / "fortran" / "support" / "lib" / "missing.so"
                            )
                        },
                    }
                )
                + "\n",
                encoding="ascii",
            )

            with patch.object(Configuration, "BACKENDS_ROOT", backends_root), patch.object(
                Configuration, "CONFIG_ROOT", config_root
            ):
                service = ConfigurationService()
                row_map = {row["backend"]: row for row in service.backend_status_rows()}

            self.assertEqual(row_map["fortran"]["configured"], "yes")
            self.assertEqual(row_map["fortran"]["ready"], "no")

    def test_initialize_backends_with_build_supports_builds_all_backends(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ConfigurationService()
            fake_map = {
                "alpha": _FakeConfigurator("alpha", Path(tmpdir) / "alpha"),
                "beta": _FakeConfigurator("beta", Path(tmpdir) / "beta"),
            }
            built = []

            def fake_get_configurator(name):
                return fake_map[name]

            def fake_build_backend_support(_self, backend):
                built.append(backend)
                return [f"build {backend}"]

            with patch(
                "phoenix.configure.service.get_configurator",
                new=fake_get_configurator,
            ), patch.object(
                ConfigurationService,
                "backend_names",
                new_callable=PropertyMock,
                return_value=("alpha", "beta"),
            ), patch.object(
                ConfigurationService,
                "build_backend_support",
                new=fake_build_backend_support,
            ):
                written = service.initialize_backends(
                    {"alpha": True, "beta": False},
                    build_supports=True,
                )

            self.assertEqual(set(written), {"alpha", "beta"})
            self.assertEqual(built, ["alpha", "beta"])


if __name__ == "__main__":
    unittest.main()
