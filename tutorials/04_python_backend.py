"""
Tutorial 04: pure Python backend execution through the backend facade.

This is the first fully executable backend tutorial. It uses the backend
facade, generates a Python module, wraps one routine, and runs a numerical
check against a NumPy reference.
"""

from __future__ import annotations

import numpy as np

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import BiLinearOperationInstruction, InstructionGroup
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import Key, KeyMap


def adaa_classes_from_assignment_config(backend, assignment_config):
    # ``make_daa_assignments`` returns ``{variable: (adaa_class, status)}``.
    # For data construction in the tutorial we only need the classes.
    return {
        variable: adaa_class
        for variable, (adaa_class, _status) in backend.make_daa_assignments(
            assignment_config
        ).items()
    }


def build_demo():
    # Define the now-familiar ``vector -> scalar`` layout.
    #
    # The order is always the same in these backend tutorials:
    #
    # 1. build the keymaps that describe memory layout,
    # 2. place instruction variables on those keymaps,
    # 3. create a backend-owned library,
    # 4. and only then register instructions.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")
    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)

    # Create symbolic input and output variables for that layout.
    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)

    # Select the Python backend through the high-level backend registry.
    backend = get_backend("python")
    library = backend.library("tutorial_python_mul")

    # ``Config`` objects are the user-friendly way to describe argument status
    # and datatype family. Here all arrays are real-valued, and ``out`` is
    # read/write so the wrapper may reuse a user-supplied target buffer.
    assignment_config = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }

    # Register one routine in the backend-owned library.
    #
    # The symbolic tree is still entirely backend-agnostic here. The Python
    # backend will later decide how to turn this into a concrete Python module.
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

    # Prepare the backend-local ADAA classes needed to construct input/output
    # objects that match the wrapper signature.
    #
    # This is one of the most important practical steps for users: the
    # assignment config not only tells PHOENIX about argument intent, it also
    # determines which ADAA class should hold the actual runtime data.
    adaa_classes = adaa_classes_from_assignment_config(
        backend, assignment_config
    )
    lhs_adaa = adaa_classes[lhs]
    rhs_adaa = adaa_classes[rhs]
    out_adaa = adaa_classes[out]

    # ``wrapped(..., build=True)`` writes the generated Python module and
    # returns a callable wrapper object for the selected routine.
    wrapper = backend.wrapped("multiply", library, build=True)

    # Convert NumPy arrays into backend-owned ADAA objects.
    #
    # Even for the pure Python backend we go through the ADAA layer, because
    # the same wrapper contract is used across the backend family.
    lhs_data = lhs_adaa.from_numpy(np.array([1.0, 2.0, 3.0]))
    rhs_data = rhs_adaa.from_numpy(np.array([4.0, 5.0, 6.0]))
    out_data = out_adaa.from_numpy(np.zeros(3))

    # Execute the generated routine. Passing ``out`` explicitly keeps the data
    # flow visible to the reader.
    result = wrapper(lhs=lhs_data, rhs=rhs_data, out=out_data).to_numpy()
    expected = np.array([4.0, 10.0, 18.0])

    print("Tutorial 04: python backend")
    print("=" * 60)
    print("Backend identifier :", backend.IDENTIFIER)
    print("Generated module   :", library.filename)
    print("Result             :", result)
    print("Expected           :", expected)
    print("Matches            :", np.allclose(result, expected))


if __name__ == "__main__":
    main()
