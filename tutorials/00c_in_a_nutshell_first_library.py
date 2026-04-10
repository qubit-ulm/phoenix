"""
Tutorial 00c: PHOENIX in a nutshell, part 3.

This script turns a small symbolic instruction set into a real library through
the modern backend facade. No builder is instantiated manually; the backend
owns the builder, validators, wrappers, and library type.
"""

from __future__ import annotations

import numpy as np

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import BiLinearOperationInstruction, InstructionGroup
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import KeyMap


def adaa_classes_from_assignment_config(backend, assignment_config):
    # ``backend.make_daa_assignments(...)`` expands the user-facing ``Config``
    # objects into concrete ADAA classes and statuses. For tutorial data setup
    # we only need the classes.
    return {
        variable: adaa_class
        for variable, (adaa_class, _status) in backend.make_daa_assignments(
            assignment_config
        ).items()
    }


def build_instruction_tree():
    hermitian2 = KeyMap(name="2x2 Hermitian matrix")
    hermitian2.entry("x")
    hermitian2.entry("y")
    hermitian2.entry("z")

    matrix_a = InstructionVariable.new("mat_a", config=hermitian2)
    matrix_b = InstructionVariable.new("mat_b", config=hermitian2)
    matrix_out = InstructionVariable.new("mat_out", config=hermitian2)

    pauli_commutator = {
        ("x", "y"): ("z", -2.0),
        ("y", "x"): ("z", 2.0),
        ("y", "z"): ("x", -2.0),
        ("z", "y"): ("x", 2.0),
        ("z", "x"): ("y", -2.0),
        ("x", "z"): ("y", 2.0),
    }

    leaves = [
        BiLinearOperationInstruction(
            tgt0=matrix_out(target),
            src0=matrix_a(src_a),
            src1=matrix_b(src_b),
            alpha=factor,
        )
        for (src_a, src_b), (target, factor) in pauli_commutator.items()
    ]
    return hermitian2, matrix_a, matrix_b, matrix_out, InstructionGroup(leaves)


def main() -> None:
    backend = get_backend("python")
    library = backend.library("tutorial_nutshell_single")

    hermitian2, matrix_a, matrix_b, matrix_out, instruction_group = (
        build_instruction_tree()
    )

    # ``Config`` is the modern user-facing assignment description.
    #
    # All three arguments are real-valued arrays in this tiny example, and the
    # target is marked ``RW`` because the generated wrapper may operate on a
    # provided output object.
    assignment_config = {
        matrix_a: Config(status="R", family="real"),
        matrix_b: Config(status="R", family="real"),
        matrix_out: Config(status="RW", family="real"),
    }

    # Register the symbolic routine in the backend-owned library.
    backend.libroutine_from_instructions(
        library,
        "commutator2i",
        instruction_group,
        assignment_config=assignment_config,
    )

    # Build the library and ask the backend for a callable wrapper.
    wrapper = backend.wrapped("commutator2i", library, build=True)

    # Convert host NumPy arrays into the backend-owned ADAA objects that match
    # the wrapper contract.
    adaa_classes = adaa_classes_from_assignment_config(
        backend, assignment_config
    )
    matrix_a_data = adaa_classes[matrix_a].from_numpy(np.array([1.0, 2.0, 3.0]))
    matrix_b_data = adaa_classes[matrix_b].from_numpy(np.array([4.0, 5.0, 6.0]))
    matrix_out_data = adaa_classes[matrix_out].from_numpy(np.zeros(3))

    result = wrapper(
        mat_a=matrix_a_data,
        mat_b=matrix_b_data,
        mat_out=matrix_out_data,
    ).to_numpy()

    # The symbolic routine is just a structured bilinear map, so we can write
    # the expected result down directly.
    expected = np.array([
        -2.0 * 2.0 * 6.0 + 2.0 * 3.0 * 5.0,
        -2.0 * 3.0 * 4.0 + 2.0 * 1.0 * 6.0,
        -2.0 * 1.0 * 5.0 + 2.0 * 2.0 * 4.0,
    ])

    print("Tutorial 00c: first library in a nutshell")
    print("=" * 60)
    print("Backend           :", backend.IDENTIFIER)
    print("Generated file    :", library.relative_to_basepath(library.filename))
    print("Symbolic keymap   :", hermitian2)
    print("Computed result   :", result)
    print("Expected result   :", expected)
    print("Matches reference :", np.allclose(result, expected))


if __name__ == "__main__":
    main()
