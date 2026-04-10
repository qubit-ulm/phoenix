import json
from dataclasses import dataclass

from phoenix.configure.cli import main
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


def test_cli_set_and_get_dotted_backend_value(tmp_path, monkeypatch, capsys):
    _prepare_config_root(tmp_path, monkeypatch)

    assert main(["fortran.enabled", "false"]) == 0
    set_output = capsys.readouterr().out.strip()
    assert set_output.endswith("backends/fortran/fortran_default.json")

    assert main(["fortran.enabled"]) == 0
    get_output = capsys.readouterr().out.strip()
    assert get_output == "false"


def test_cli_test_backend_invokes_smoke_runner(monkeypatch, capsys):
    @dataclass
    class FakeReport:
        passed: bool = True

        def render(self):
            return "fake backend report"

    def fake_run_selected_backend_tests(name):
        assert name == "python"
        return [FakeReport()]

    monkeypatch.setattr(
        "phoenix.configure.testing.run_selected_backend_tests",
        fake_run_selected_backend_tests,
    )

    assert main(["--test", "python"]) == 0
    output = capsys.readouterr().out
    assert "fake backend report" in output


def test_cli_dialogue_accepts_backend_via_positional_target(monkeypatch, capsys):
    calls = []

    def fake_configure_backend_dialogue(_self, name):
        calls.append(name)
        return "/tmp/fake.json", {}, []

    monkeypatch.setattr(
        "phoenix.configure.service.ConfigurationService.configure_backend_dialogue",
        fake_configure_backend_dialogue,
    )

    assert main(["fortran", "--dialogue"]) == 0
    assert calls == ["fortran"]
    assert "Wrote /tmp/fake.json" in capsys.readouterr().out


def test_cli_dialogue_without_backend_runs_all(monkeypatch, capsys):
    calls = []

    def fake_configure_backend_dialogue(_self, name):
        calls.append(name)
        return f"/tmp/{name}.json", {}, []

    monkeypatch.setattr(
        "phoenix.configure.service.ConfigurationService.configure_backend_dialogue",
        fake_configure_backend_dialogue,
    )

    assert main(["--dialogue"]) == 0
    assert calls
    assert "Wrote /tmp/" in capsys.readouterr().out
