"""
Demo 07a: compare available ADAA families.

The symbolic backend and the storage wrapper family are different concerns in
PHOENIX. This demo focuses only on the storage side:

- how one host/device wrapper is constructed from NumPy data,
- how host-side inspection works through ``to_numpy()``,
- and how the default arithmetic helpers behave across available backends.
"""

from __future__ import annotations

import numpy as np

from phoenix.fgen.backends.c.c_adaa import CRA
from phoenix.fgen.backends.cuda.cuda_cupy_adaa import PROVIDE_CUPY
from phoenix.fgen.backends.cuda.cuda_pycuda_adaa import PROVIDE_PYCUDA
from phoenix.fgen.backends.numpy.numpy_adaa import NumPyRA
from phoenix.fgen.backends.opencl.opencl_adaa import PROVIDE_OPENCL

if PROVIDE_OPENCL:
    from phoenix.fgen.backends.opencl.opencl_adaa import OpenClRA
else:
    OpenClRA = None

if PROVIDE_CUPY:
    from phoenix.fgen.backends.cuda.cuda_cupy_adaa import CupyRA
else:
    CupyRA = None

if PROVIDE_PYCUDA:
    from phoenix.fgen.backends.cuda.cuda_pycuda_adaa import PyCudaRA
else:
    PyCudaRA = None


def available_families():
    """
    Return the ADAA families that can be demonstrated in this environment.

    ``CRA`` is always importable, but its actual operations still depend on the
    configured C helper library. We therefore keep it in the list and let the
    per-family execution path report a clear error if the support library is
    missing.
    """

    return (
        ("NumPy", NumPyRA),
        ("C", CRA),
        ("OpenCL", OpenClRA),
        ("CuPy", CupyRA),
        ("PyCUDA", PyCudaRA),
    )


def demonstrate_family(label: str, adaa_class) -> dict[str, object]:
    """
    Run the same small operation set through one ADAA class.

    The goal is to compare ownership and conversion behavior, so the math stays
    intentionally tiny and repetitive.
    """

    source = np.array([1.0, -2.0, 3.5], dtype=np.float64)
    other = np.array([-0.5, 4.0, 2.5], dtype=np.float64)

    if adaa_class is None:
        return {"label": label, "available": False, "detail": "not installed"}

    try:
        # ``from_numpy`` is the ordinary entry point when a user already has
        # host-side NumPy data and wants to hand it to one backend wrapper.
        base = adaa_class.from_numpy(source)
        other_data = adaa_class.from_numpy(other)

        # ``to_numpy(cache=True)`` is intentionally called twice so the demo can
        # talk about cached host views, especially for device-backed families.
        host_once = base.to_numpy(cache=True)
        host_twice = base.to_numpy(cache=True)

        # The generic ADAA helpers are backend-agnostic; only the underlying
        # storage and transfer path differ between families.
        zeroed = base.copy().to_zero().to_numpy()
        added = (base + other_data).to_numpy()
        scaled = (2.0 * base).to_numpy()
        negated = (-base).to_numpy()

        # ``mark_dirty`` invalidates the cached host copy explicitly. The next
        # ``to_numpy`` call therefore has to refresh from the backend storage.
        base.mark_dirty()
        refreshed = base.to_numpy(cache=True)
    except Exception as exc:
        return {"label": label, "available": False, "detail": str(exc)}

    return {
        "label": label,
        "available": True,
        "host_once": host_once,
        "host_twice": host_twice,
        "zeroed": zeroed,
        "added": added,
        "scaled": scaled,
        "negated": negated,
        "refreshed": refreshed,
    }


def main() -> None:
    print("Demo 07a: ADAA families")
    print("=" * 72)
    print("Each section below applies the same default operations to one")
    print("backend-owned ADAA family and then converts the result back to NumPy.")
    print()

    for label, adaa_class in available_families():
        result = demonstrate_family(label, adaa_class)
        print(f"[{label}]")
        if not result["available"]:
            print("  skipped:", result["detail"])
            print()
            continue

        print("  first host copy :", result["host_once"])
        print("  cached host copy:", result["host_twice"])
        print("  to_zero         :", result["zeroed"])
        print("  addition        :", result["added"])
        print("  scalar multiply :", result["scaled"])
        print("  sign change     :", result["negated"])
        print("  after mark_dirty:", result["refreshed"])
        print()


if __name__ == "__main__":
    main()
