"""
Tutorial 13: ParametricInstructionGroup with nested keymaps.

This tutorial demonstrates that parametric groups can now keep nested symbolic
layouts intact. Earlier workflows often required flattening the keymap first.
"""

from __future__ import annotations

import argparse
from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import (
    BiLinearOperationInstruction,
    InstructionGroup,
    ParametricInstructionGroup,
)
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import Key, KeyMap


def build_variables():
    """Build a nested ``vector -> scalar`` keymap and matching variables."""
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)

    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)
    return vector, lhs, rhs, out


def build_instruction_groups(lhs, rhs, out):
    """Build both the plain and the parametric version of the same leaves."""
    leaves = [
        BiLinearOperationInstruction(
            tgt0=out(Key(idx), "value"),
            src0=lhs(Key(idx), "value"),
            src1=rhs(Key(idx), "value"),
            alpha=1.0,
        )
        for idx in range(3)
    ]
    return InstructionGroup(leaves), ParametricInstructionGroup(leaves)


def preview_lines(path: str | Path, limit: int = 48) -> str:
    # Read back only the first lines so the example output stays compact.
    return "\n".join(Path(path).read_text().splitlines()[:limit])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Nested-keymap parametric group demonstration."
    )
    parser.add_argument(
        "--backend",
        default="fortran",
        choices=("plain", "python", "numpy", "c", "fortran", "cuda"),
    )
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()

    vector, lhs, rhs, out = build_variables()
    ordinary_group, parametric_group = build_instruction_groups(lhs, rhs, out)

    backend = get_backend(args.backend)
    library = backend.library("tutorial_parametric_nested_keymaps_v2")

    assignment_config = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }

    # Register two routines that differ only in the outer group class.
    backend.libroutine_from_instructions(
        library,
        "multiply_group",
        ordinary_group,
        assignment_config=assignment_config,
    )
    backend.libroutine_from_instructions(
        library,
        "multiply_parametric",
        parametric_group,
        assignment_config=assignment_config,
    )

    library.build(compile=bool(args.build))

    sample = out(Key(2), "value")
    print("Tutorial 13: nested-keymap parametric groups")
    print("=" * 68)
    print("Backend                  :", backend.IDENTIFIER)
    print("Generated file           :", library.filename)
    print("Sample symbolic variable :", sample)
    print("Sample evaluated offsets :", list(sample.evaluate()))
    print()
    print("Only the group type changed from InstructionGroup to")
    print("ParametricInstructionGroup.")
    print()
    print(preview_lines(library.filename, 48))


if __name__ == "__main__":
    main()
