"""Backend smoke-test helpers used by CLI and regression tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil

import numpy as np

from .backends import get_configurator
from ..fgen.backend_config import Configuration
from ..fgen.backends import Config, get_backend
from ..fgen.backends.cuda.cuda_cupy_adaa import PROVIDE_CUPY
from ..fgen.backends.cuda.cuda_pycuda_adaa import PROVIDE_PYCUDA
from ..fgen.backends.opencl.opencl_adaa import PROVIDE_OPENCL
from ..fgen.instruction import (
    InstructionGroup,
    LinearOperationInstruction,
    MapApplyInstruction,
)
from ..fgen.instructionvar import InstructionEnvironment, InstructionVariable
from ..keymap import Key, KeyMap


GENERATION_BACKENDS = (
    "plain",
    "python",
    "numpy",
    "c",
    "fortran",
    "julia",
    "matlab",
    "opencl",
    "cuda",
)
RUNTIME_BACKENDS = ("python", "numpy", "c", "fortran")
FAMILIES = ("real", "imag", "complex")
RUNTIME_FAMILIES = ("real",)
MAPAPPLY_RUNTIME_FAMILIES = ("real", "complex")


@dataclass
class BackendCheck:
    """One backend smoke-test check."""

    name: str
    passed: bool
    detail: str = ""


@dataclass
class BackendTestReport:
    """Structured result of one backend smoke run."""

    backend: str
    checks: list[BackendCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Return whether all recorded checks passed."""
        return all(check.passed for check in self.checks)

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        """Append one check result."""
        self.checks.append(BackendCheck(name=name, passed=passed, detail=detail))

    def render(self) -> str:
        """Return a CLI-friendly text report."""
        lines = [f"Backend test report: {self.backend}"]
        for check in self.checks:
            prefix = "PASS" if check.passed else "FAIL"
            line = f"[{prefix}] {check.name}"
            if check.detail:
                line += f": {check.detail}"
            lines.append(line)
        lines.append(f"overall: {'passed' if self.passed else 'failed'}")
        return "\n".join(lines)


def render_test_strategy() -> str:
    """Return a concise release-stage testing strategy overview."""
    return "\n".join(
        [
            "PHOENIX release-stage test strategy",
            "1. Generic symbolic core: keymaps, instruction variables, instruction trees, library registration, configuration access.",
            "2. ADAA arithmetic: elementwise add/subtract, scalar multiply/divide, copy/zero/select across backend-owned ADAA classes.",
            "3. Backend generation smoke: every backend lowers a basic instruction group and a mapapply routine for real, imag, and complex families.",
            "4. Backend runtime smoke: installed and configured runtime backends execute wrapped routines and compare numerical output against NumPy references.",
            "5. Configuration smoke: the configuration CLI can report status, initialize backends, edit dotted settings, and run backend smoke tests with --test.",
        ]
    )


def backend_runtime_ready(backend_name: str) -> tuple[bool, str]:
    """Return whether a backend is ready for runtime smoke tests."""
    backend = backend_name.lower()
    current = Configuration.for_backend(backend).to_dict()
    if current and not current.get("enabled", True):
        return False, "backend is disabled in configuration"
    if backend == "python":
        return True, "python wrapper runtime available"
    if backend == "numpy":
        return True, "numpy wrapper runtime available"
    if backend == "c":
        compiler = current.get("executables", {}).get("compiler", "cc")
        support_lib = current.get("support", {}).get("library_file", "")
        if not shutil.which(Path(compiler).name if compiler else "cc"):
            return False, f"missing C compiler {compiler!r}"
        if support_lib and not Path(support_lib).exists():
            return False, f"missing configured support library {support_lib}"
        return True, "C compiler and support library detected"
    if backend == "fortran":
        compiler = current.get("executables", {}).get("compiler", "gfortran")
        python_executable = current.get("executables", {}).get("python", "")
        compiler_name = Path(compiler).name if compiler else "gfortran"
        if not shutil.which(compiler_name):
            return False, f"missing Fortran compiler {compiler!r}"
        if python_executable and not Path(python_executable).exists():
            return False, f"configured Python executable does not exist: {python_executable}"
        return True, "Fortran compiler and Python wrapper path detected"
    if backend == "opencl":
        return PROVIDE_OPENCL, "pyopencl runtime available" if PROVIDE_OPENCL else "pyopencl runtime not available"
    if backend == "cuda":
        selected = (
            current.get("runtime", {}).get("adaa_library")
            or ("cupy" if PROVIDE_CUPY else "pycuda")
        )
        if selected == "pycuda":
            support_lib = current.get("support", {}).get("library_file", "")
            if support_lib and not Path(support_lib).exists():
                return False, f"missing configured support library {support_lib}"
            return (
                PROVIDE_PYCUDA,
                "pycuda runtime available"
                if PROVIDE_PYCUDA
                else "pycuda runtime not available",
            )
        return (
            PROVIDE_CUPY,
            "cupy runtime available"
            if PROVIDE_CUPY
            else "cupy runtime not available",
        )
    return False, f"{backend} has no runtime wrapper smoke path"


def _family_input_array(family: str, *, length: int = 3) -> np.ndarray:
    base = np.array([1 + 2j, -2 + 0.5j, 3 - 4j], dtype=np.complex128)
    if length != 3:
        base = np.resize(base, length)
    if family == "real":
        return np.asarray(base.real, dtype=np.float64)
    if family == "imag":
        return 1j * np.asarray(base.imag, dtype=np.float64)
    if family == "complex":
        return base
    raise KeyError(f"unknown family {family}")


def _expected_linear(family: str, alpha: float) -> np.ndarray:
    return alpha * _family_input_array(family)


def _make_vector_case(*, length: int = 3):
    scalar = KeyMap(name="scalar")
    scalar.entry("value")
    vector = KeyMap(name=f"vector{length}")
    for idx in range(length):
        vector.link(Key(idx), scalar)
    source = InstructionVariable.new("source", config=vector)
    target = InstructionVariable.new("target", config=vector)
    return scalar, vector, source, target


def _basic_instruction(source, target, *, length: int = 3, alpha: float = 2.0):
    return InstructionGroup(
        [
            LinearOperationInstruction(
                tgt0=target(Key(idx), "value"),
                src0=source(Key(idx), "value"),
                alpha=alpha,
            )
            for idx in range(length)
        ]
    )


def _mapapply_instruction(scalar, source, target, *, length: int = 3, alpha: float = 2.0):
    local_in = InstructionVariable.new("local_in", config=scalar)
    local_out = InstructionVariable.new("local_out", config=scalar)
    content = InstructionGroup(
        [
            LinearOperationInstruction(
                tgt0=local_out("value"),
                src0=local_in("value"),
                alpha=alpha,
            )
        ]
    )
    environments = [
        InstructionEnvironment(
            {
                local_in: source(Key(idx)),
                local_out: target(Key(idx)),
            }
        )
        for idx in range(length)
    ]
    return MapApplyInstruction(content=content, environments=environments)


def _assignment_backend_for(backend_name: str):
    backend = get_backend(backend_name)
    if backend.get_assignment_families():
        return backend
    return get_backend("python")


def _assignment_config(source, target, family: str):
    return {
        source: Config(status="R", family=family),
        target: Config(status="RW", family=family),
    }


def _configured_backend(backend_name: str, build_root: Path):
    backend = get_backend(backend_name)
    return backend.configure(
        general={"paths": {"build_root": str(build_root)}}
    )


def run_generation_smoke(
    backend_name: str,
    *,
    build_root: Path,
    families: tuple[str, ...] = FAMILIES,
) -> BackendTestReport:
    """Build generation-only smoke routines for one backend."""
    report = BackendTestReport(backend=backend_name)
    backend = _configured_backend(backend_name, build_root)
    assignment_backend = _assignment_backend_for(backend_name)
    scalar, _vector, source, target = _make_vector_case()

    for family in families:
        library = backend.library(f"release_{backend_name}_{family}_gen")
        assignments = assignment_backend.make_daa_assignments(
            _assignment_config(source, target, family)
        )
        if backend_name in {"julia", "matlab"}:
            library.libroutine_from_instructions(
                f"basic_{family}",
                _basic_instruction(source, target),
                daa_assignments=assignments,
            )
            report.add(
                f"generation-mapapply:{family}",
                True,
                detail="mapapply generation is not part of the stable Julia/MATLAB release path",
            )
        else:
            backend.libroutine_from_instructions(
                library,
                f"basic_{family}",
                _basic_instruction(source, target),
                daa_assignments=assignments,
            )
            backend.libroutine_from_instructions(
                library,
                f"map_{family}",
                _mapapply_instruction(scalar, source, target),
                daa_assignments=assignments,
            )
            report.add(
                f"generation-mapapply:{family}",
                True,
                detail="mapapply routine generated",
            )
        library.build(force=True, compile=False)
        generated = Path(library.relative_to_basepath(library.filename))
        report.add(
            f"generation-basic:{family}",
            generated.exists(),
            detail=str(generated),
        )
    return report


def run_runtime_smoke(
    backend_name: str,
    *,
    build_root: Path,
    families: tuple[str, ...] = RUNTIME_FAMILIES,
) -> BackendTestReport:
    """Build and execute runtime smoke routines for one backend."""
    report = BackendTestReport(backend=backend_name)
    backend = _configured_backend(backend_name, build_root)
    ready, detail = backend_runtime_ready(backend_name)
    if not ready:
        report.add("runtime-ready", False, detail)
        return report
    report.add("runtime-ready", True, detail)
    scalar, _vector, source, target = _make_vector_case()

    for family in families:
        library = backend.library(f"release_{backend_name}_{family}_runtime_basic")
        config = _assignment_config(source, target, family)
        backend.libroutine_from_instructions(
            library,
            f"basic_{family}",
            _basic_instruction(source, target),
            assignment_config=config,
        )
        classes = {
            instr_var: adaa_class
            for instr_var, (adaa_class, _status) in backend.make_daa_assignments(config).items()
        }
        wrapper_basic = backend.wrapped(f"basic_{family}", library, build=True)
        source_data = classes[source].from_numpy(_family_input_array(family))
        target_data = classes[target].from_numpy(np.zeros_like(_family_input_array(family)))
        basic_return = wrapper_basic(source=source_data, target=target_data)
        basic_result = (
            basic_return.to_numpy()
            if hasattr(basic_return, "to_numpy")
            else target_data.to_numpy()
        )
        expected = _expected_linear(family, 2.0)

        report.add(
            f"runtime-basic:{family}",
            bool(np.allclose(basic_result, expected)),
            detail=f"expected={expected}, got={basic_result}",
        )
        if family not in MAPAPPLY_RUNTIME_FAMILIES:
            report.add(
                f"runtime-mapapply:{family}",
                True,
                detail="covered by generation smoke; runtime path restricted to stable families",
            )
            continue

        map_library = backend.library(f"release_{backend_name}_{family}_runtime_map")
        backend.libroutine_from_instructions(
            map_library,
            f"map_{family}",
            _mapapply_instruction(scalar, source, target),
            assignment_config=config,
        )
        wrapper_map = backend.wrapped(f"map_{family}", map_library, build=True)
        map_target = classes[target].from_numpy(np.zeros_like(_family_input_array(family)))
        map_return = wrapper_map(source=source_data, target=map_target)
        map_result = (
            map_return.to_numpy()
            if hasattr(map_return, "to_numpy")
            else map_target.to_numpy()
        )
        report.add(
            f"runtime-mapapply:{family}",
            bool(np.allclose(map_result, expected)),
            detail=f"expected={expected}, got={map_result}",
        )
    return report


def run_backend_test(
    backend_name: str,
    *,
    build_root: str | Path | None = None,
) -> BackendTestReport:
    """Run the supported smoke tests for one backend."""
    backend = backend_name.lower()
    if backend not in GENERATION_BACKENDS:
        raise KeyError(f"unknown backend {backend_name!r}")
    if build_root is None:
        with TemporaryDirectory(prefix=f"phoenix-test-{backend}-") as tmpdir:
            return run_backend_test(backend, build_root=Path(tmpdir))

    build_root = Path(build_root)
    build_root.mkdir(parents=True, exist_ok=True)
    generation = run_generation_smoke(backend, build_root=build_root / "generation")
    if backend in RUNTIME_BACKENDS:
        runtime = run_runtime_smoke(backend, build_root=build_root / "runtime")
        generation.checks.extend(runtime.checks)
    return generation


def run_selected_backend_tests(
    backend_name: str,
    *,
    build_root: str | Path | None = None,
) -> list[BackendTestReport]:
    """Run one or all backend smoke tests."""
    if backend_name.lower() == "all":
        return [
            run_backend_test(name, build_root=build_root)
            for name in GENERATION_BACKENDS
        ]
    return [run_backend_test(backend_name, build_root=build_root)]


def current_backend_test_status() -> list[dict[str, str]]:
    """Return a small table describing smoke-test expectations per backend."""
    rows = []
    for backend in GENERATION_BACKENDS:
        ready, detail = backend_runtime_ready(backend)
        configurator = get_configurator(backend)
        rows.append(
            {
                "backend": backend,
                "generation": "yes",
                "runtime": "yes" if backend in RUNTIME_BACKENDS and ready else "no",
                "enabled": "yes"
                if configurator.load_current().get("enabled", True)
                else "no",
                "detail": detail,
            }
        )
    return rows


__all__ = [
    "BackendCheck",
    "BackendTestReport",
    "FAMILIES",
    "GENERATION_BACKENDS",
    "RUNTIME_BACKENDS",
    "backend_runtime_ready",
    "current_backend_test_status",
    "render_test_strategy",
    "run_backend_test",
    "run_generation_smoke",
    "run_runtime_smoke",
    "run_selected_backend_tests",
]
