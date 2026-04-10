"""
Tutorial 00b: PHOENIX in a nutshell, part 2.

This script builds a small symbolic instruction set on top of a keymap. The
goal is to show what PHOENIX means by "describe the computation once".
"""

from __future__ import annotations

from phoenix.fgen.instruction import (
    BiLinearOperationInstruction,
    InstructionGroup,
)
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import KeyMap


def build_commutator_model():
    # Represent a 2x2 Hermitian matrix through the three Pauli coefficients.
    #
    # The keymap now describes one logical object, not a flat implementation.
    hermitian2 = KeyMap(name="2x2 Hermitian matrix")
    hermitian2.entry("x")
    hermitian2.entry("y")
    hermitian2.entry("z")

    # Create symbolic instruction variables that live on that layout.
    #
    # These are not runtime arrays yet. They are symbolic placeholders used to
    # describe how one future routine should read and write data.
    matrix_a = InstructionVariable.new("mat_a", config=hermitian2)
    matrix_b = InstructionVariable.new("mat_b", config=hermitian2)
    matrix_out = InstructionVariable.new("mat_out", config=hermitian2)

    # The commutator [A, B] in the Pauli basis has only six non-zero terms.
    pauli_commutator = {
        ("x", "y"): ("z", -2.0),
        ("y", "x"): ("z", 2.0),
        ("y", "z"): ("x", -2.0),
        ("z", "y"): ("x", 2.0),
        ("z", "x"): ("y", -2.0),
        ("x", "z"): ("y", 2.0),
    }

    leaves = []
    for (src_a, src_b), (target, factor) in pauli_commutator.items():
        # Every leaf says:
        #
        #   target += alpha * src0 * src1
        #
        # That is enough to describe the whole routine symbolically.
        leaves.append(
            BiLinearOperationInstruction(
                tgt0=matrix_out(target),
                src0=matrix_a(src_a),
                src1=matrix_b(src_b),
                alpha=factor,
            )
        )

    return hermitian2, matrix_a, matrix_b, matrix_out, InstructionGroup(leaves)


def main() -> None:
    hermitian2, matrix_a, matrix_b, matrix_out, instruction_group = (
        build_commutator_model()
    )

    print("Tutorial 00b: instructions in a nutshell")
    print("=" * 60)
    print("Keymap:", hermitian2)
    print("Variables:", matrix_a.__name__, matrix_b.__name__, matrix_out.__name__)
    print("Number of leaf instructions:", len(list(instruction_group.instructions)))

    print("\nInstruction payload preview:")
    for num, instruction in enumerate(instruction_group.instructions, start=1):
        payload = instruction.to_dict("tgt0", "src0", "src1", "alpha")
        print(f"  {num:02d}. {payload}")


if __name__ == "__main__":
    main()
