"""
Tutorial 03: generate symbolic plain-text output.

The plain backend is the easiest backend to inspect because it emits readable
text instead of executable code. This makes it a good bridge between the
instruction tree from tutorial 02 and the executable backends in later
tutorials.
"""

from __future__ import annotations

# The plain backend in this tutorial is used directly through ``PlainLibrary``.
# This keeps the example close to the lower-level generation API.
from phoenix.adaas import STATUS_INPUT, STATUS_INOUT
from phoenix.fgen.backends.python.python_adaa import PythonRA
from phoenix.fgen.backends.plain.plain_builder import PlainLibrary
from phoenix.fgen.instruction import BiLinearOperationInstruction, InstructionGroup
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import Key, KeyMap


def build_library() -> PlainLibrary:
    # Create a nested vector-of-scalars layout.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")
    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)

    # Define the symbolic variables that the instruction tree will use.
    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)

    # The plain backend still needs a data-layout class to describe the routine
    # arguments. Here we reuse the Python real-valued ADAA family and bind it
    # to the vector keymap.
    adaa = PythonRA.set_keymap(vector)

    # The library object owns the generated file and the registered routines.
    library = PlainLibrary("tutorial_plain_mul")
    library.libroutine_from_instructions(
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
        daa_assignments={
            lhs: (adaa, STATUS_INPUT),
            rhs: (adaa, STATUS_INPUT),
            out: (adaa, STATUS_INOUT),
        },
    )
    return library


def main() -> None:
    library = build_library()

    # ``compile=False`` means “write the generated file, but do not try to call
    # any native compiler afterwards”.
    library.build(compile=False)
    path = Path(library.filename)

    print("Tutorial 03: plain backend")
    print("=" * 60)
    print("Generated file:", path.resolve())
    print()
    print("Preview:\n")

    # Reading the file back is the central point of this tutorial: the output
    # shows how the symbolic instruction group is lowered into the plain backend.
    print(path.read_text())


if __name__ == "__main__":
    main()
