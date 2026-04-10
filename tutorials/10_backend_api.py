"""
Tutorial 10: backend abstraction API.

This tutorial demonstrates the modern backend entry points:

1. select a backend via ``get_backend(...)``,
2. describe argument families with ``Config``,
3. build a backend-owned library through the backend facade,
4. and call the generated routine through ``Backend.wrapped(...)``.
"""

from __future__ import annotations

import argparse
import numpy as np

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import (
    BiLinearOperationInstruction,
    InstructionGroup,
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


def build_instruction_tree(*, parametric: bool):
    """Build one small vector multiply tree."""
    # The data layout stays tiny because this tutorial is about the backend
    # facade itself, not about numerical complexity.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)

    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)

    leaves = [
        BiLinearOperationInstruction(
            tgt0=out(Key(idx), "value"),
            src0=lhs(Key(idx), "value"),
            src1=rhs(Key(idx), "value"),
            alpha=1.0,
        )
        for idx in range(3)
    ]

    # CUDA often benefits from a more explicitly parametric outer structure, so
    # the tutorial keeps that switch visible.
    #
    # The key lesson is that the backend object can participate in these higher
    # level decisions without changing the surrounding user code very much.
    group_class = (
        ParametricInstructionGroup if parametric else InstructionGroup
    )
    return vector, lhs, rhs, out, group_class(leaves)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backend abstraction tutorial."
    )
    parser.add_argument(
        "--backend",
        default="cuda",
        choices=("plain", "python", "numpy", "c", "fortran", "cuda"),
    )
    args = parser.parse_args()

    backend = get_backend(args.backend)
    # ``build_instruction_tree`` receives one backend-informed switch but
    # otherwise remains backend-independent. That split is the architectural
    # idea this tutorial is trying to highlight.
    vector, lhs, rhs, out, instruction_tree = build_instruction_tree(
        parametric=(backend.IDENTIFIER == "cuda")
    )
    library = backend.library("tutorial_backend_api")

    assignment_config = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }

    # The backend object owns both optimization/validation and the final build
    # into the selected library type.
    #
    # From the user perspective, this is the central abstraction: one object
    # covers the builder, validators, optimizers, library type, and wrapper
    # type for the chosen backend.
    backend.libroutine_from_instructions(
        library,
        "multiply",
        instruction_tree,
        assignment_config=assignment_config,
    )

    prepared_classes = adaa_classes_from_assignment_config(
        backend, assignment_config
    )
    lhs_adaa = prepared_classes[lhs]
    rhs_adaa = prepared_classes[rhs]
    out_adaa = prepared_classes[out]

    # ``wrapped`` is the shortest path from a registered routine name to a
    # callable user-facing wrapper object.
    wrapper = backend.wrapped("multiply", library, build=True)

    lhs_data = lhs_adaa.from_numpy(np.array([1.0, 2.0, 3.0]))
    rhs_data = rhs_adaa.from_numpy(np.array([4.0, 5.0, 6.0]))
    out_data = out_adaa.from_numpy(np.zeros(3))

    result_data = wrapper(lhs=lhs_data, rhs=rhs_data, out=out_data)
    result = result_data.to_numpy()
    expected = np.array([4.0, 10.0, 18.0])

    print("Tutorial 10: backend abstraction API")
    print("=" * 60)
    print("Backend identifier :", backend.IDENTIFIER)
    print("Generated module   :", library.filename)
    print("Detected keymap    :", vector)
    print("Group type         :", type(instruction_tree).__name__)
    print("Result             :", result)
    print("Expected           :", expected)
    print("Matches            :", np.allclose(result, expected))


if __name__ == "__main__":
    main()
