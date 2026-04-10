from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from phoenix.adaa import ComplexArrayADAA, ImagArrayADAA, RealArrayADAA
from phoenix.fgen.backends.numpy.numpy_adaa import NumPyCA, NumPyIA, NumPyRA


def test_only_restricts_datatypes():
    assert RealArrayADAA._DATATYPES == {"real": "f64"}
    assert ImagArrayADAA._DATATYPES == {"imag": "f64"}
    assert ComplexArrayADAA._DATATYPES == {"real": "f64", "imag": "f64"}


def test_select_can_swap_components_with_copy():
    arr = NumPyCA.from_numpy(np.array([1 + 2j, 3 + 4j]))
    swapped = arr.select(real="imag", imag="real", copy=True)
    assert np.allclose(swapped.to_numpy(), np.array([2 + 1j, 4 + 3j]))
    assert swapped.real is not arr.real
    assert swapped.imag is not arr.imag


def test_select_can_alias_components_without_copy():
    arr = NumPyCA.from_numpy(np.array([1 + 2j, 3 + 4j]))
    real_view = arr.select("real", copy=False)
    imag_view = arr.select("imag", copy=False)
    assert real_view._DATATYPES == {"real": "f64"}
    assert imag_view._DATATYPES == {"imag": "f64"}
    assert real_view.real is arr.real
    assert imag_view.imag is arr.imag


def test_real_and_imag_numpy_exports_are_restricted():
    arr = np.array([1 + 2j, 3 + 4j])
    assert np.allclose(NumPyRA.from_numpy(arr).to_numpy(), np.array([1.0, 3.0]))
    assert np.allclose(NumPyIA.from_numpy(arr).to_numpy(), np.array([0 + 2j, 0 + 4j]))
