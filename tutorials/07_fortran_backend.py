"""
Tutorial 07: compiled Fortran backend execution.

This tutorial uses the Fortran backend through the high-level backend facade.
Compared to the C example, the symbolic setup is almost identical; the main
difference is the generated target language and the Fortran/f2py wrapper path.
"""

from __future__ import annotations

import numpy as np

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import (
    BiLinearOperationInstruction,
    ParametricInstructionGroup,
)
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
    # Build a nested vector layout with three scalar entries.
    #
    # We keep the symbolic problem the same as in the C tutorial so the reader
    # can focus on what changes when the target language becomes Fortran.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")
    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)

    # Define symbolic variables over that layout.
    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)

    # Select the Fortran backend and create a backend-owned library.
    backend = get_backend("fortran")
    library = backend.library("tutorial_fortran_mul")
    assignment_config = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }

    # ``ParametricInstructionGroup`` is used here to keep the tutorial close to
    # the modern Fortran path that can preserve more symbolic structure.
    #
    # In other words, we hand the backend a slightly richer symbolic container
    # than a plain instruction list and let the backend decide how much of that
    # structure should survive code generation.
    backend.libroutine_from_instructions(
        library,
        "multiply",
        ParametricInstructionGroup(
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
        resource_name="serial",
    )
    return backend, library, lhs, rhs, out, assignment_config


def main() -> None:
    backend, library, lhs, rhs, out, assignment_config = build_demo()
    # As in the earlier backend tutorials, the assignment config is the bridge
    # from symbolic routine arguments to concrete runtime data holders.
    adaa_classes = adaa_classes_from_assignment_config(
        backend, assignment_config
    )
    lhs_adaa = adaa_classes[lhs]
    rhs_adaa = adaa_classes[rhs]
    out_adaa = adaa_classes[out]

    # Build the Fortran source, compile it through the configured toolchain,
    # and obtain a Python-facing wrapper.
    #
    # This is the point where backend configuration matters: the Fortran
    # compiler, wrapper path, and flags all come from the saved backend config.
    wrapper = backend.wrapped("multiply", library, build=True)

    lhs_data = lhs_adaa.from_numpy(np.array([1.0, 2.0, 3.0]))
    rhs_data = rhs_adaa.from_numpy(np.array([4.0, 5.0, 6.0]))
    out_data = out_adaa.from_numpy(np.zeros(3))
    result = wrapper(lhs=lhs_data, rhs=rhs_data, out=out_data).to_numpy()
    expected = np.array([4.0, 10.0, 18.0])

    print("Tutorial 07: Fortran backend")
    print("=" * 60)
    print("Backend identifier :", backend.IDENTIFIER)
    print("Generated source   :", library.filename)
    print("Result             :", result)
    print("Expected           :", expected)
    print("Matches            :", np.allclose(result, expected))


if __name__ == "__main__":
    main()
