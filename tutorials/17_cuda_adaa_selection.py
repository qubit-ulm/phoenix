"""
Tutorial 17: CUDA ADAA selection.

This tutorial demonstrates two related ideas:

1. ``get_backend("cuda")`` stays the single CUDA backend entry point.
2. The host/device array wrapper family can still be selected through
   ``runtime.adaa_library`` with ``"cupy"`` or ``"pycuda"``.

The generated CUDA code path stays the same in both cases. Only the ADAA class
family changes, which means only the host/device array handling changes.
"""

from __future__ import annotations

import numpy as np

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.backends.cuda.cuda_cupy_adaa import PROVIDE_CUPY
from phoenix.fgen.backends.cuda.cuda_pycuda_adaa import PROVIDE_PYCUDA
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import KeyMap

if PROVIDE_PYCUDA:
    from phoenix.fgen.backends.cuda.cuda_pycuda_adaa import PyCudaRA
else:
    PyCudaRA = None
if PROVIDE_CUPY:
    from phoenix.fgen.backends.cuda.cuda_cupy_adaa import CupyRA
else:
    CupyRA = None


def make_scalar_variable():
    """Create one scalar instruction variable used for ADAA resolution."""
    scalar = KeyMap(name="scalar")
    scalar.entry("value")
    return InstructionVariable.new("value", config=scalar)


def describe_cuda_selection(adaa_library: str):
    """Print how the generic CUDA backend resolves one ADAA family."""
    # The selected backend name stays ``cuda``. Only the runtime ADAA family is
    # switched underneath that stable facade.
    backend = get_backend("cuda").configure(
        backend={"runtime": {"adaa_library": adaa_library}}
    )
    variable = make_scalar_variable()

    print(f"Selecting CUDA ADAA library: {adaa_library}")
    print("Resolved backend keyword    :", backend.IDENTIFIER)
    print("Configured ADAA library     :", backend.selected_adaa_library())
    print(
        "Configured availability     :",
        backend.configuration.get_nested(
            "runtime",
            f"{adaa_library}_available",
            default=False,
        ),
    )

    families = backend.get_assignment_families()
    if not families:
        print("Resolved real ADAA class    : unavailable in this Python env")
        print()
        return

    # ``make_daa_assignments`` lets the demo inspect which concrete ADAA class
    # the backend would choose for a normal real-valued argument.
    assignments = backend.make_daa_assignments(
        {variable: Config(status="RW", family="real")}
    )
    adaa_class, _status = assignments[variable]
    print("Resolved real ADAA class    :", adaa_class.__name__)
    print()


def demonstrate_pycuda_default_operations():
    """Run a small set of backend-agnostic default ADAA operations via PyCUDA."""
    if not PROVIDE_PYCUDA:
        print("PyCUDA operation demo       : skipped, PyCUDA is not installed")
        return

    # The real-valued ADAA is enough to demonstrate the default arithmetic API.
    source = np.array([1.0, -2.0, 3.5], dtype=np.float64)
    other = np.array([-0.5, 4.0, 2.5], dtype=np.float64)

    # ``from_numpy`` is the ordinary initialization path for host-side data.
    initialized = PyCudaRA.from_numpy(source)
    other_value = PyCudaRA.from_numpy(other)

    # ``copy`` keeps the original object intact so the individual operations are
    # easy to compare side by side.
    #
    # That makes the demo much easier to read than repeatedly mutating the same
    # object.
    zeroed = initialized.copy().to_zero()
    added = initialized + other_value
    scaled = 2.0 * initialized
    negated = -initialized

    print("PyCUDA default operations")
    print("Initialized                :", initialized.to_numpy())
    print("To zero                    :", zeroed.to_numpy())
    print("Addition                   :", added.to_numpy())
    print("Scalar multiply            :", scaled.to_numpy())
    print("Sign change                :", negated.to_numpy())
    print()
    print("PyCUDA checks")
    print(
        "Initialization matches     :",
        np.allclose(initialized.to_numpy(), source),
    )
    print(
        "To zero matches            :",
        np.allclose(zeroed.to_numpy(), np.zeros_like(source)),
    )
    print(
        "Addition matches           :",
        np.allclose(added.to_numpy(), source + other),
    )
    print(
        "Scalar multiply matches    :",
        np.allclose(scaled.to_numpy(), 2.0 * source),
    )
    print(
        "Sign change matches        :",
        np.allclose(negated.to_numpy(), -source),
    )
    print("\n")


def demonstrate_cupy_default_operations():
    """Run a small set of backend-agnostic default ADAA operations via CuPy."""
    if not PROVIDE_CUPY:
        print("CuPy operation demo       : skipped, CuPy is not installed")
        return

    # The real-valued ADAA is enough to demonstrate the default arithmetic API.
    source = np.array([1.0, -2.0, 3.5], dtype=np.float64)
    other = np.array([-0.5, 4.0, 2.5], dtype=np.float64)

    # ``from_numpy`` is the ordinary initialization path for host-side data.
    initialized = CupyRA.from_numpy(source)
    other_value = CupyRA.from_numpy(other)

    # ``copy`` keeps the original object intact so the individual operations are
    # easy to compare side by side.
    #
    # The operation list is deliberately the same as in the PyCUDA section so
    # the reader can compare the two runtime families directly.
    zeroed = initialized.copy().to_zero()
    added = initialized + other_value
    scaled = 2.0 * initialized
    negated = -initialized

    print("CuPy default operations")
    print("Initialized                :", initialized.to_numpy())
    print("To zero                    :", zeroed.to_numpy())
    print("Addition                   :", added.to_numpy())
    print("Scalar multiply            :", scaled.to_numpy())
    print("Sign change                :", negated.to_numpy())
    print()
    print("CuPy checks")
    print(
        "Initialization matches     :",
        np.allclose(initialized.to_numpy(), source),
    )
    print(
        "To zero matches            :",
        np.allclose(zeroed.to_numpy(), np.zeros_like(source)),
    )
    print(
        "Addition matches           :",
        np.allclose(added.to_numpy(), source + other),
    )
    print(
        "Scalar multiply matches    :",
        np.allclose(scaled.to_numpy(), 2.0 * source),
    )
    print(
        "Sign change matches        :",
        np.allclose(negated.to_numpy(), -source),
    )
    print("\n")


def main() -> None:
    """Run both selector demonstrations and the PyCUDA arithmetic example."""
    print("Tutorial 17: CUDA ADAA selection")
    print("=" * 60)
    print("Detected CuPy              :", PROVIDE_CUPY)
    print("Detected PyCUDA            :", PROVIDE_PYCUDA)
    print()

    # The same ``cuda`` backend facade is used in both cases. Only the runtime
    # ADAA family selection changes.
    describe_cuda_selection("cupy")
    describe_cuda_selection("pycuda")
    demonstrate_pycuda_default_operations()
    demonstrate_cupy_default_operations()


if __name__ == "__main__":
    main()
