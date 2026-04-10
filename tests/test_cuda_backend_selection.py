import numpy as np
import pytest

from phoenix.configure.backends.cuda import CUDAConfigurator
from phoenix.fgen.backend_config import Configuration
from phoenix.fgen.backends import Config
from phoenix.fgen.backends.cuda import cuda_backend as cuda_backend_module
from phoenix.fgen.backends.cuda.cuda_backend import CUDABackend
from phoenix.fgen.backends.cuda.cuda_pycuda_adaa import PROVIDE_PYCUDA
from phoenix.fgen.backends.numpy.numpy_adaa import NumPyCA, NumPyIA, NumPyRA
from phoenix.fgen.backends.python.python_adaa import PythonCA, PythonIA, PythonRA
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import KeyMap

if PROVIDE_PYCUDA:
    from phoenix.fgen.backends.cuda.cuda_pycuda_adaa import PyCudaRA
else:
    PyCudaRA = None


def make_scalar_variable():
    scalar = KeyMap(name="scalar")
    scalar.entry("value")
    return InstructionVariable.new("value", config=scalar)


def test_cuda_backend_uses_configured_adaa_library(monkeypatch):
    monkeypatch.setattr(
        cuda_backend_module,
        "CUPY_FAMILIES",
        {"complex": "cupy-complex", "real": "cupy-real", "imag": "cupy-imag"},
    )
    monkeypatch.setattr(
        cuda_backend_module,
        "PYCUDA_FAMILIES",
        {
            "complex": "pycuda-complex",
            "real": "pycuda-real",
            "imag": "pycuda-imag",
        },
    )

    backend = CUDABackend(
        configuration=Configuration(
            "cuda",
            data={"runtime": {"adaa_library": "pycuda"}},
        )
    )

    assert backend.selected_adaa_library() == "pycuda"
    assert backend.get_assignment_families() == {
        "complex": "pycuda-complex",
        "real": "pycuda-real",
        "imag": "pycuda-imag",
        "default": "pycuda-complex",
    }


def test_cuda_backend_defaults_to_cupy_when_available(monkeypatch):
    monkeypatch.setattr(cuda_backend_module, "PROVIDE_CUPY", True)
    monkeypatch.setattr(cuda_backend_module, "PROVIDE_PYCUDA", True)
    monkeypatch.setattr(
        cuda_backend_module,
        "CUPY_FAMILIES",
        {"complex": "cupy-complex", "real": "cupy-real", "imag": "cupy-imag"},
    )
    monkeypatch.setattr(
        cuda_backend_module,
        "PYCUDA_FAMILIES",
        {
            "complex": "pycuda-complex",
            "real": "pycuda-real",
            "imag": "pycuda-imag",
        },
    )

    backend = CUDABackend(configuration=Configuration.empty("cuda"))

    assert backend.selected_adaa_library() == "cupy"
    assert backend.get_assignment_families()["default"] == "cupy-complex"


def test_cuda_backend_make_daa_assignments_follows_runtime_selector(monkeypatch):
    monkeypatch.setattr(
        cuda_backend_module,
        "CUPY_FAMILIES",
        {"complex": PythonCA, "real": PythonRA, "imag": PythonIA},
    )
    monkeypatch.setattr(
        cuda_backend_module,
        "PYCUDA_FAMILIES",
        {"complex": NumPyCA, "real": NumPyRA, "imag": NumPyIA},
    )

    variable = make_scalar_variable()

    cupy_backend = CUDABackend(
        configuration=Configuration(
            "cuda",
            data={"runtime": {"adaa_library": "cupy"}},
        )
    )
    pycuda_backend = CUDABackend(
        configuration=Configuration(
            "cuda",
            data={"runtime": {"adaa_library": "pycuda"}},
        )
    )

    cupy_assignment = cupy_backend.make_daa_assignments(
        {variable: Config(status="RW", family="real")}
    )
    pycuda_assignment = pycuda_backend.make_daa_assignments(
        {variable: Config(status="RW", family="real")}
    )

    assert cupy_assignment[variable][0].find_anchor_class() is PythonRA
    assert pycuda_assignment[variable][0].find_anchor_class() is NumPyRA


def test_cuda_configurator_records_detected_runtime_libraries():
    configurator = CUDAConfigurator()
    scan = {
        "executables": {
            "compiler": "/usr/bin/nvcc",
            "linker": "/usr/bin/nvcc",
        },
        "hardware": {
            "gpu_name": "Test GPU",
            "cupy": False,
            "pycuda": True,
        },
    }

    config = configurator.default_config(scan)

    assert config["runtime"] == {
        "cupy_available": False,
        "pycuda_available": True,
        "adaa_library": "pycuda",
    }


@pytest.mark.skipif(not PROVIDE_PYCUDA, reason="PyCUDA not installed")
def test_pycuda_real_adaa_default_operations():
    source = np.array([1.0, -2.0, 3.5], dtype=np.float64)
    other = np.array([-0.5, 4.0, 2.5], dtype=np.float64)

    initialized = PyCudaRA.from_numpy(source)
    rhs = PyCudaRA.from_numpy(other)

    assert np.allclose(initialized.to_numpy(), source)

    zeroed = initialized.copy().to_zero()
    assert np.allclose(zeroed.to_numpy(), np.zeros_like(source))

    added = initialized + rhs
    assert np.allclose(added.to_numpy(), source + other)

    scaled = 2.0 * initialized
    assert np.allclose(scaled.to_numpy(), 2.0 * source)

    negated = -initialized
    assert np.allclose(negated.to_numpy(), -source)
