from __future__ import annotations

from pathlib import Path

import pytest

from phoenix.configure.testing import (
    GENERATION_BACKENDS,
    RUNTIME_BACKENDS,
    backend_runtime_ready,
    render_test_strategy,
    run_backend_test,
    run_generation_smoke,
    run_runtime_smoke,
)


@pytest.mark.parametrize("backend_name", GENERATION_BACKENDS)
def test_backend_generation_smoke_matrix(tmp_path, backend_name):
    report = run_generation_smoke(backend_name, build_root=tmp_path / backend_name)

    assert report.checks
    assert report.passed, report.render()


@pytest.mark.parametrize("backend_name", RUNTIME_BACKENDS)
def test_backend_runtime_smoke_matrix(tmp_path, backend_name):
    ready, detail = backend_runtime_ready(backend_name)
    if not ready:
        pytest.skip(detail)

    report = run_runtime_smoke(backend_name, build_root=tmp_path / backend_name)

    assert report.passed, report.render()


def test_backend_test_strategy_mentions_all_release_layers():
    strategy = render_test_strategy()

    assert "Generic symbolic core" in strategy
    assert "ADAA arithmetic" in strategy
    assert "--test" in strategy


def test_backend_test_runner_aggregates_generation_and_runtime(tmp_path):
    report = run_backend_test("python", build_root=tmp_path / "python")

    assert report.passed, report.render()
    assert any(check.name.startswith("generation-basic:complex") for check in report.checks)
    assert any(check.name.startswith("runtime-basic:real") for check in report.checks)
    assert Path(tmp_path / "python").exists()
