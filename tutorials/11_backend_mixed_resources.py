"""
Tutorial 11: one library, multiple compatible backends/resources.

This example shows the orchestration model for resource variants:

- the library stays language-specific,
- backend objects do the heavy lifting,
- and compatible backend instances can register different routines into the
  same library.

This older tutorial keeps the example small and backend-agnostic. A more
focused Fortran-specific resource switch tutorial is added later in the series.
"""

from __future__ import annotations

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import BiLinearOperationInstruction, InstructionGroup
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import Key, KeyMap


def build_instruction_tree():
    # Build the usual nested vector layout.
    #
    # The symbolic tree is intentionally unremarkable. The interesting part of
    # this tutorial is the resource selection, not the arithmetic.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)

    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)

    instruction_tree = InstructionGroup(
        [
            BiLinearOperationInstruction(
                tgt0=out(Key(idx), "value"),
                src0=lhs(Key(idx), "value"),
                src1=rhs(Key(idx), "value"),
                alpha=1.0,
            )
            for idx in range(3)
        ]
    )
    return lhs, rhs, out, instruction_tree


def main() -> None:
    lhs, rhs, out, instruction_tree = build_instruction_tree()

    # Create two compatible backend instances. They target the same backend
    # family but can expose different resource defaults and settings.
    #
    # This is a useful pattern in real projects: you do not need a completely
    # different symbolic model just because one routine should be serial and
    # another one should be OpenMP-enabled.
    serial_backend = get_backend("c")
    omp_backend = get_backend("c").configure(
        general={"runtime": {"num_processors": 8}}
    )

    library = serial_backend.library("tutorial_c_mixed_resources")
    assignments = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }

    # Register one serial routine and one OpenMP-enabled routine into the same
    # C library. The resource preset is selected per routine call.
    #
    # This is the part that users often miss at first: the library can stay the
    # same while the resource choice varies routine by routine.
    serial_backend.libroutine_from_instructions(
        library,
        "multiply_serial",
        instruction_tree,
        assignment_config=assignments,
        resource_name="serial",
    )
    omp_backend.libroutine_from_instructions(
        library,
        "multiply_omp",
        instruction_tree,
        assignment_config=assignments,
        resource_name="omp",
    )

    print("Tutorial 11: mixed resource backends")
    print("=" * 60)
    print("Library class     :", type(library).__name__)
    print("Serial backend    :", type(serial_backend).__name__)
    print("OMP backend       :", type(omp_backend).__name__)
    print("Registered routes :", [name for name, _ in library.content])
    print("Source file       :", library.filename)


if __name__ == "__main__":
    main()
