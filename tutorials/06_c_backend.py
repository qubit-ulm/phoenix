"""
Tutorial 06: compiled C backend execution.

This tutorial keeps the symbolic instruction tree simple and instead focuses on
what changes once the target backend becomes native code: the library is
compiled, a C-compatible wrapper is created, and the output target is passed
explicitly.
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
    # Define the nested vector layout used throughout the early tutorials.
    #
    # Reusing the same symbolic shape from tutorial to tutorial is deliberate:
    # the backend differences become easier to see when the symbolic problem is
    # held constant.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")
    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)

    # Define symbolic variables on top of that layout.
    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)

    # Select the compiled C backend.
    backend = get_backend("c")
    library = backend.library("tutorial_c_mul")
    assignment_config = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }

    # Register the same symbolic multiply routine as before.
    #
    # The routine definition remains short, but behind the scenes the C backend
    # now has to emit a native source file, a wrapper interface, and a build
    # description instead of a pure Python module.
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
    # The C backend resolves C-backed ADAA classes here. Those objects own
    # storage that can be handed to native code without another translation
    # layer in between.
    adaa_classes = adaa_classes_from_assignment_config(
        backend, assignment_config
    )
    lhs_adaa = adaa_classes[lhs]
    rhs_adaa = adaa_classes[rhs]
    out_adaa = adaa_classes[out]

    # For native backends the wrapper usually compiles generated code and loads
    # the resulting shared library before the wrapper becomes callable.
    wrapper = backend.wrapped("multiply", library, build=True)

    lhs_data = lhs_adaa.from_numpy(np.array([1.0, 2.0, 3.0]))
    rhs_data = rhs_adaa.from_numpy(np.array([4.0, 5.0, 6.0]))
    out_data = out_adaa.from_numpy(np.zeros(3))

    # Passing ``out`` explicitly makes the in-place style of native wrappers
    # visible. The wrapper returns the same target object for convenience.
    #
    # That mirrors what many native APIs do: the caller owns the output buffer
    # and the routine fills it.
    result = wrapper(lhs=lhs_data, rhs=rhs_data, out=out_data).to_numpy()
    expected = np.array([4.0, 10.0, 18.0])

    print("Tutorial 06: C backend")
    print("=" * 60)
    print("Backend identifier :", backend.IDENTIFIER)
    print("Generated source   :", library.filename)
    print("Result             :", result)
    print("Expected           :", expected)
    print("Matches            :", np.allclose(result, expected))


if __name__ == "__main__":
    main()
