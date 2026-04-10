"""
Tutorial 02: building a small instruction tree.

This tutorial extends the symbolic keymap setup from tutorial 01 with a tiny
instruction group. The result is still backend-neutral: we are building an
intermediate representation, not target-language code yet.
"""

from __future__ import annotations

# ``BiLinearOperationInstruction`` models an update of the form
# ``target = alpha * source0 * source1`` on the symbolic level.
from phoenix.fgen.instruction import BiLinearOperationInstruction, InstructionGroup
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import Key, KeyMap


def build_instruction_group() -> InstructionGroup:
    # Rebuild the same scalar and vector layout from tutorial 01.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)

    # Define three symbolic variables that all share the same layout:
    # two inputs and one output.
    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)

    # Each leaf instruction multiplies the two input entries and writes the
    # result into the matching output entry.
    leaves = [
        BiLinearOperationInstruction(
            tgt0=out(Key(idx), "value"),
            src0=lhs(Key(idx), "value"),
            src1=rhs(Key(idx), "value"),
            alpha=1.0,
        )
        for idx in range(3)
    ]

    # ``InstructionGroup`` preserves the order of the leaf instructions and
    # becomes the root of the symbolic instruction tree.
    return InstructionGroup(leaves)


def main() -> None:
    instructions = build_instruction_group()
    print("Tutorial 02: instruction trees")
    print("=" * 60)
    print("Instruction group type:", type(instructions).__name__)
    print("Contained instructions:", len(list(instructions.instructions)))
    print()
    print("Compact record payload:")

    # The compact payload is useful for logs and manifests.
    print(instructions.record_payload(detailed=False))
    print()
    print("Detailed record payload:")

    # The detailed payload shows the full symbolic content of the instruction
    # tree and is often the better representation while learning the API.
    print(instructions.record_payload(detailed=True))


if __name__ == "__main__":
    main()
