"""
Tutorial 16: Fortran resource switch with scalar and parallel routines.

This tutorial creates one Fortran library containing two routines:

1. ``multiply_scalar`` uses a serial Fortran resource.
2. ``multiply_parallel`` uses a resource selected through ``--parallel``.

The example therefore shows how one library can expose both a scalar and a
parallel variant side by side.
"""

from __future__ import annotations

import argparse
from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import BiLinearOperationInstruction, InstructionGroup
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import Key, KeyMap


def build_instruction_tree():
    # Build a simple vector layout large enough that an OpenMP-flavoured
    # lowering is meaningful as a demonstration.
    #
    # The vector is still tiny by HPC standards, but large enough that the
    # generated routine visibly contains repeated work items.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    vector = KeyMap(name="vector8")
    for idx in range(8):
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
            for idx in range(8)
        ]
    )
    return lhs, rhs, out, instruction_tree


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build serial and parallel Fortran routines in one library."
    )
    parser.add_argument(
        "--parallel",
        default="omp",
        choices=("serial", "omp"),
        help="resource preset for the second routine",
    )
    parser.add_argument(
        "--threads",
        default=8,
        type=int,
        help="number of processors exposed through the general configuration",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="compile the generated library instead of only writing it",
    )
    args = parser.parse_args()

    lhs, rhs, out, instruction_tree = build_instruction_tree()

    # Configure one serial backend instance and one backend instance with a
    # caller-controlled processor count. Both are still Fortran backends and can
    # therefore register routines into the same Fortran library.
    #
    # This is the same pattern as in the mixed-resource tutorial, but phrased
    # here with an explicitly Fortran-specific focus.
    scalar_backend = get_backend("fortran")
    parallel_backend = get_backend("fortran").configure(
        general={"runtime": {"num_processors": args.threads}}
    )

    library = scalar_backend.library("tutorial_fortran_parallel_switch")
    assignments = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }

    # Always emit the scalar reference routine.
    scalar_backend.libroutine_from_instructions(
        library,
        "multiply_scalar",
        instruction_tree,
        assignment_config=assignments,
        resource_name="serial",
    )

    # Emit the second routine using the user-selected resource preset. When the
    # preset is ``omp``, the Fortran backend uses its OpenMP-oriented resource
    # description.
    #
    # The generated library therefore contains two routines with identical
    # symbolic math but different resource choices.
    parallel_backend.libroutine_from_instructions(
        library,
        "multiply_parallel",
        instruction_tree,
        assignment_config=assignments,
        resource_name=args.parallel,
    )

    library.build(compile=bool(args.build))

    print("Tutorial 16: Fortran parallel switch")
    print("=" * 60)
    print("Library           :", library.libname)
    print("Generated source  :", library.filename)
    print("Parallel preset   :", args.parallel)
    print("Configured threads:", args.threads)
    print("Registered routes :", [name for name, _ in library.content])


if __name__ == "__main__":
    main()
