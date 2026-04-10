from __future__ import annotations

import numpy as np

from phoenix.adaa import ComplexArrayADAA
from phoenix.coeffbackend import CoeffBackend
from phoenix.fgen.backends.pywrapper_library import WrapperBase


class CountingCoeffBackend(CoeffBackend):
    def __init__(self):
        super().__init__()
        self.to_numpy_calls = []

    def coeff_new_array(self, size: int, dtype: str):
        return np.zeros(size, dtype=np.float64)

    def coeff_from_numpy(self, coeff_like, nparray, size: int, dtype: str) -> None:
        del size, dtype
        coeff_like[:] = np.asarray(nparray, dtype=np.float64)

    def coeff_to_numpy(self, coeff_like, size: int, dtype: str) -> np.ndarray:
        self.to_numpy_calls.append((size, dtype))
        return np.array(coeff_like, copy=True)

    def coeff_linop(
        self,
        arr_r,
        /,
        scal_a: float | None,
        arr_x,
        scal_b: float | None,
        arr_y,
        *,
        size: int,
        dtype: str,
        inplace: bool = False,
    ):
        del size, dtype
        if not inplace:
            arr_r[:] = 0
        if arr_x is not None:
            arr_r[:] += arr_x if scal_a is None else scal_a * arr_x
        if arr_y is not None:
            arr_r[:] += arr_y if scal_b is None else scal_b * arr_y


class CacheTestADAA(
    ComplexArrayADAA,
    backend=CountingCoeffBackend(),
    identifier="CACHE_TEST",
    is_anchor=True,
):
    pass


def test_to_numpy_uses_component_cache_after_first_host_load():
    obj = CacheTestADAA.from_numpy(np.array([1 + 2j, 3 + 4j], dtype=np.complex128))
    backend = obj._BACKEND

    backend.to_numpy_calls.clear()
    first = obj.to_numpy()
    second = obj.to_numpy()

    assert np.allclose(first, second)
    assert backend.to_numpy_calls == []

    obj.mark_dirty("real")
    third = obj.to_numpy()

    assert np.allclose(third, first)
    assert backend.to_numpy_calls == [(2, "f64")]


def test_to_numpy_cache_false_bypasses_and_does_not_fill_cache():
    obj = CacheTestADAA(2)
    obj.real[:] = np.array([1.0, 2.0])
    obj.imag[:] = np.array([3.0, 4.0])
    obj.reset_cache()
    backend = obj._BACKEND
    backend.to_numpy_calls.clear()

    arr = obj.to_numpy(cache=False)

    assert np.allclose(arr, np.array([1 + 3j, 2 + 4j]))
    assert backend.to_numpy_calls == [(2, "f64"), (2, "f64")]
    assert obj._cached["real"] is None
    assert obj._cached["imag"] is None
    assert obj._cached_is_dirty["real"] is True
    assert obj._cached_is_dirty["imag"] is True


def test_wrapper_marks_out_and_inout_adaa_cache_dirty():
    fixed_real = CacheTestADAA.only("real").fix_size(2)
    wrapper = WrapperBase(
        "dummy",
        lambda *_args: None,
        arguments=[
            ("RW", object(), "shared", "real", fixed_real),
            ("R", object(), "out", "real", fixed_real),
        ],
    )
    shared = fixed_real.from_numpy(np.array([5.0, 6.0]))
    shared._cache_component("real", np.array([5.0, 6.0]))

    wrapper.prepare_inputs((), {"shared": shared})
    wrapper.prepare_returns()
    wrapper.prepare_inouts()

    assert shared._cached["real"] is None
    assert shared._cached_is_dirty["real"] is True
    assert wrapper._rets["out"]._cached["real"] is None
    assert wrapper._rets["out"]._cached_is_dirty["real"] is True
