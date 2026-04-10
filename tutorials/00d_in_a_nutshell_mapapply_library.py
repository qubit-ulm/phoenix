"""
Tutorial 00d: PHOENIX in a nutshell, part 4.

This script extends the first-library example to several matrices through
``MapApplyInstruction``. The point is to show that the same local symbolic
kernel can be rebound repeatedly without rewriting the algebra.
"""

from __future__ import annotations

import numpy as np

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import (
    BiLinearOperationInstruction,
    InstructionGroup,
    MapApplyInstruction,
)
from phoenix.fgen.instructionvar import InstructionEnvironment, InstructionVariable
from phoenix.keymap import Key, KeyMap


def adaa_classes_from_assignment_config(backend, assignment_config):
    return {
        variable: adaa_class
        for variable, (adaa_class, _status) in backend.make_daa_assignments(
            assignment_config
        ).items()
    }


def build_local_kernel():
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

    content = InstructionGroup(
        [
            BiLinearOperationInstruction(
                tgt0=matrix_out(target),
                src0=matrix_a(src_a),
                src1=matrix_b(src_b),
                alpha=factor,
            )
            for (src_a, src_b), (target, factor) in pauli_commutator.items()
        ]
    )
    return hermitian2, matrix_a, matrix_b, matrix_out, content


def main() -> None:
    backend = get_backend("python")
    library = backend.library("tutorial_nutshell_mapapply")

    num_matrices = 4
    local_keymap, matrix_a, matrix_b, matrix_out, local_kernel = build_local_kernel()

    # Build the outer array layout: each site points to the same local matrix
    # keymap from the previous tutorial.
    matrix_array = KeyMap(name="matrix array")
    for idx in range(num_matrices):
        matrix_array.link(Key(idx), local_keymap)

    array_a = InstructionVariable.new("array_a", config=matrix_array)
    array_b = InstructionVariable.new("array_b", config=matrix_array)
    array_out = InstructionVariable.new("array_out", config=matrix_array)

    # ``MapApplyInstruction`` reuses the local kernel in several environments.
    #
    # Each environment says how the local symbolic variables should be rebound
    # for one specific matrix in the outer array.
    environments = [
        InstructionEnvironment(
            {
                matrix_a: array_a(Key(idx)),
                matrix_b: array_b(Key(idx)),
                matrix_out: array_out(Key(idx)),
            }
        )
        for idx in range(num_matrices)
    ]
    instruction_tree = MapApplyInstruction(
        content=local_kernel,
        environments=environments,
    )

    assignment_config = {
        array_a: Config(status="R", family="real"),
        array_b: Config(status="R", family="real"),
        array_out: Config(status="RW", family="real"),
    }

    backend.libroutine_from_instructions(
        library,
        "array_commutator2i",
        instruction_tree,
        assignment_config=assignment_config,
    )
    wrapper = backend.wrapped("array_commutator2i", library, build=True)

    adaa_classes = adaa_classes_from_assignment_config(
        backend, assignment_config
    )
    array_a_host = np.array(
        [
            1.0,
            2.0,
            3.0,
            2.0,
            3.0,
            4.0,
            3.0,
            4.0,
            5.0,
            4.0,
            5.0,
            6.0,
        ]
    )
    array_b_host = np.array(
        [
            4.0,
            5.0,
            6.0,
            5.0,
            6.0,
            7.0,
            6.0,
            7.0,
            8.0,
            7.0,
            8.0,
            9.0,
        ]
    )
    array_out_host = np.zeros_like(array_a_host)

    result = wrapper(
        array_a=adaa_classes[array_a].from_numpy(array_a_host),
        array_b=adaa_classes[array_b].from_numpy(array_b_host),
        array_out=adaa_classes[array_out].from_numpy(array_out_host),
    ).to_numpy()

    # Recreate the same tiny local reference block by block on the host. This
    # makes the role of ``MapApplyInstruction`` easy to see: it is simply
    # repeated rebinding of one local kernel.
    expected = np.zeros_like(array_a_host)
    for idx in range(num_matrices):
        xa, ya, za = array_a_host[3 * idx : 3 * idx + 3]
        xb, yb, zb = array_b_host[3 * idx : 3 * idx + 3]
        expected[3 * idx : 3 * idx + 3] = np.array(
            [
                -2.0 * ya * zb + 2.0 * za * yb,
                -2.0 * za * xb + 2.0 * xa * zb,
                -2.0 * xa * yb + 2.0 * ya * xb,
            ]
        )

    print("Tutorial 00d: mapapply library in a nutshell")
    print("=" * 60)
    print("Backend              :", backend.IDENTIFIER)
    print("Generated file       :", library.relative_to_basepath(library.filename))
    print("Matrices in the demo :", num_matrices)
    print("Computed result      :", result)
    print("Expected result      :", expected)
    print("Matches reference    :", np.allclose(result, expected))


if __name__ == "__main__":
    main()
