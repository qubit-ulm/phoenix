"""
Tutorial 05: vectorized NumPy backend execution.

This tutorial mirrors the Python backend tutorial closely. The main difference
is that the generated module uses NumPy arrays internally and therefore emits a
more vectorization-friendly host implementation.
"""

from __future__ import annotations

import numpy as np

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import BiLinearOperationInstruction, InstructionGroup
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import Key, KeyMap


def adaa_classes_from_assignment_config(backend, assignment_config):
    return {
        variable: adaa_class
        for variable, (adaa_class, _status) in backend.make_daa_assignments(
            assignment_config
        ).items()
    }


def build_demo():
    # Build the symbolic storage layout first.
    #
    # The important thing to notice is that nothing here is NumPy-specific yet.
    # NumPy enters later through the selected backend and ADAA class family.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")
    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)

    # Create symbolic variables over that layout.
    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)

    # Select the NumPy backend and create one backend-owned library.
    backend = get_backend("numpy")
    library = backend.library("tutorial_numpy_mul")
    assignment_config = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }

    # Register one vector multiply routine.
    #
    # The instruction tree is still phrased entry by entry so the reader can
    # see exactly which symbolic targets and sources are involved.
    backend.libroutine_from_instructions(
        library,
        "multiply",
        InstructionGroup(
            [
                BiLinearOperationInstruction(
                    tgt0=out(Key(idx), "value"),
                    src0=lhs(Key(idx), "value"),
                    src1=rhs(Key(idx), "value"),
                    alpha=1.0,
                )
                for idx in range(3)
            ]
        ),
        assignment_config=assignment_config,
    )
    return backend, library, lhs, rhs, out, assignment_config


def main() -> None:
    backend, library, lhs, rhs, out, assignment_config = build_demo()
    # Resolve the runtime data classes from the declarative assignment config.
    # This keeps the data-construction path aligned with the generated wrapper.
    adaa_classes = adaa_classes_from_assignment_config(
        backend, assignment_config
    )
    lhs_adaa = adaa_classes[lhs]
    rhs_adaa = adaa_classes[rhs]
    out_adaa = adaa_classes[out]

    # Build and wrap the generated NumPy module.
    #
    # The wrapper object is the user-facing callable. It hides the generated
    # module import and routine lookup behind one ordinary Python call.
    wrapper = backend.wrapped("multiply", library, build=True)

    # Create backend-owned data objects from ordinary NumPy arrays.
    # ``NumPyRA`` will keep the storage as host-side NumPy arrays, but the demo
    # still goes through the same ADAA conversion path as other backends.
    lhs_data = lhs_adaa.from_numpy(np.array([1.0, 2.0, 3.0]))
    rhs_data = rhs_adaa.from_numpy(np.array([4.0, 5.0, 6.0]))
    out_data = out_adaa.from_numpy(np.zeros(3))

    # Execute the wrapped routine and compare the numerical result.
    result = wrapper(lhs=lhs_data, rhs=rhs_data, out=out_data).to_numpy()
    expected = np.array([4.0, 10.0, 18.0])

    print("Tutorial 05: NumPy backend")
    print("=" * 60)
    print("Backend identifier :", backend.IDENTIFIER)
    print("Generated module   :", library.filename)
    print("Result             :", result)
    print("Expected           :", expected)
    print("Matches            :", np.allclose(result, expected))


if __name__ == "__main__":
    main()
