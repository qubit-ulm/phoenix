from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from phoenix.fgen.backends.c.c_adaa import CCA, CIA, CRA
from phoenix.fgen.backends.cuda.cuda_cupy_adaa import PROVIDE_CUPY
from phoenix.fgen.backends.fortran.fortran_adaa import FortranCA, FortranIA, FortranRA
from phoenix.fgen.backends.numpy.numpy_adaa import NumPyCA, NumPyIA, NumPyRA
from phoenix.fgen.backends.opencl.opencl_adaa import PROVIDE_OPENCL
from phoenix.fgen.backends.cuda.cuda_pycuda_adaa import PROVIDE_PYCUDA
from phoenix.fgen.backends.python.python_adaa import PythonCA, PythonIA, PythonRA

if PROVIDE_CUPY:
    from phoenix.fgen.backends.cuda.cuda_cupy_adaa import CupyCA, CupyIA, CupyRA
if PROVIDE_OPENCL:
    from phoenix.fgen.backends.opencl.opencl_adaa import OpenClCA, OpenClIA, OpenClRA
if PROVIDE_PYCUDA:
    from phoenix.fgen.backends.cuda.cuda_pycuda_adaa import PyCudaCA, PyCudaIA, PyCudaRA


def expected_for_class(cls, array: np.ndarray) -> np.ndarray:
    keys = tuple(cls._DATATYPES)
    if keys == ("real", "imag"):
        return np.asarray(array, dtype=np.complex128)
    if keys == ("real",):
        return np.asarray(array.real, dtype=np.float64)
    if keys == ("imag",):
        return 1j * np.asarray(array.imag, dtype=np.float64)
    raise AssertionError(f"Unexpected datatype layout: {keys}")


BACKEND_CASES = [
    pytest.param(PythonCA, PythonRA, PythonIA, id="python"),
    pytest.param(NumPyCA, NumPyRA, NumPyIA, id="numpy"),
    pytest.param(FortranCA, FortranRA, FortranIA, id="fortran"),
    pytest.param(CCA, CRA, CIA, id="c"),
]

if PROVIDE_CUPY:
    BACKEND_CASES.append(
        pytest.param(CupyCA, CupyRA, CupyIA, id="cuda-cupy")
    )
if PROVIDE_OPENCL:
    BACKEND_CASES.append(
        pytest.param(OpenClCA, OpenClRA, OpenClIA, id="opencl")
    )
if PROVIDE_PYCUDA:
    BACKEND_CASES.append(
        pytest.param(PyCudaCA, PyCudaRA, PyCudaIA, id="cuda-pycuda")
    )


@pytest.mark.parametrize("complex_cls,real_cls,imag_cls", BACKEND_CASES)
def test_adaa_backend_ops(complex_cls, real_cls, imag_cls):
    source = np.array([1 + 2j, 3 + 4j, -5 + 0.5j], dtype=np.complex128)
    other = np.array([-2 + 1j, 0.25 - 3j, 4 - 2j], dtype=np.complex128)

    for cls in (complex_cls, real_cls, imag_cls):
        obj = cls.from_numpy(source)
        assert np.allclose(obj.to_numpy(), expected_for_class(cls, source))

        copied = obj.copy()
        obj.to_zero()
        assert np.allclose(obj.to_numpy(), expected_for_class(cls, np.zeros_like(source)))
        assert np.allclose(copied.to_numpy(), expected_for_class(cls, source))

        lhs = cls.from_numpy(source)
        rhs = cls.from_numpy(other)

        added = lhs + rhs
        assert np.allclose(
            added.to_numpy(),
            expected_for_class(cls, source) + expected_for_class(cls, other),
        )

        subtracted = lhs - rhs
        assert np.allclose(
            subtracted.to_numpy(),
            expected_for_class(cls, source) - expected_for_class(cls, other),
        )

        scaled = 2.5 * lhs
        assert np.allclose(
            scaled.to_numpy(),
            2.5 * expected_for_class(cls, source),
        )

        negated = -lhs
        assert np.allclose(
            negated.to_numpy(),
            -expected_for_class(cls, source),
        )

        divided = lhs / 2.0
        assert np.allclose(
            divided.to_numpy(),
            expected_for_class(cls, source) / 2.0,
        )
