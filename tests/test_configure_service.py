import json

from phoenix.configure.service import ConfigurationService
from phoenix.fgen.backend_config import Configuration


def _prepare_config_root(tmp_path, monkeypatch):
    backends_root = tmp_path / "backends"
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
        + "\n"
    )
    monkeypatch.setattr(Configuration, "BACKENDS_ROOT", backends_root)
    monkeypatch.setattr(Configuration, "CONFIG_ROOT", config_root)
    return config_root


def test_service_sets_backend_values_with_defaults(tmp_path, monkeypatch):
    config_root = _prepare_config_root(tmp_path, monkeypatch)
    service = ConfigurationService()

    target = service.set_value("fortran.resource.parallel_model", "omp")

    saved = json.loads(target.read_text())
    assert target == config_root.parent / "fortran" / "fortran_default.json"
    assert saved["backend"] == "fortran"
    assert saved["enabled"] is True
    assert saved["resource"]["parallel_model"] == "omp"
    assert "makefile" in saved["support"]


def test_initialization_persists_disabled_backends(tmp_path, monkeypatch):
    config_root = _prepare_config_root(tmp_path, monkeypatch)
    service = ConfigurationService()

    written = service.initialize_backends(
        {
            "fortran": False,
            "python": True,
        }
    )

    fortran_data = json.loads(
        (config_root.parent / "fortran" / "fortran_default.json").read_text()
    )
    python_data = json.loads(
        (config_root.parent / "python" / "python_default.json").read_text()
    )

    assert written["fortran"] == config_root.parent / "fortran" / "fortran_default.json"
    assert fortran_data["enabled"] is False
    assert python_data["enabled"] is True
    states = {row["backend"]: row["state"] for row in service.backend_status_rows()}
    assert states["fortran"] == "disabled"
