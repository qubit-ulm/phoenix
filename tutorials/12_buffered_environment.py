"""
Tutorial 12: explicit buffered targets with stacked buffer levels.

This example demonstrates the explicit buffer helper API:

1. a local write target is redirected into an inner buffer,
2. an outer environment aliases that inner buffer onto a second buffer level,
3. reduction/copy instructions are generated afterwards to resolve the buffers.
"""

from __future__ import annotations

import argparse
from phoenix.fgen.backends import get_backend
from phoenix.fgen.backends.c.c_builder import CLocalVariable
from phoenix.fgen.backends.fortran.fortran_builder import FortranLocalVariable
from phoenix.fgen.backends.numpy.numpy_builder import NPLocalVariable
from phoenix.fgen.backends.plain.plain_builder import PlainLocalVariable
from phoenix.fgen.backends.python.python_builder import PyLocalVariable
from phoenix.fgen.buffermanager import BufferManager
from phoenix.fgen.instruction import (
    InstructionGroup,
    LinearOperationInstruction,
    MapApplyInstruction,
)
from phoenix.fgen.instructionvar import (
    InstructionEnvironment,
    InstructionVariable,
)
from phoenix.keymap import Key, KeyMap


LOCAL_VARIABLE_CLASSES = {
    "plain": PlainLocalVariable,
    "python": PyLocalVariable,
    "numpy": NPLocalVariable,
    "c": CLocalVariable,
    "fortran": FortranLocalVariable,
    "cuda": CLocalVariable,
}


def build_demo():
    # Build three nested layouts:
    #
    #   scalar       -> one value
    #   local_pair   -> left/right scalar pair
    #   batched_pairs -> two local pairs
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    local_pair = KeyMap(name="local_pair")
    local_pair.link(Key("left"), scalar)
    local_pair.link(Key("right"), scalar)

    batched_pairs = KeyMap(name="batched_pairs")
    for batch in range(2):
        batched_pairs.link(Key(batch), local_pair)

    # ``src_local`` / ``tgt_local`` are used inside one local map body, while
    # ``src`` / ``tgt`` are the outer batched variables.
    #
    # This split is important for understanding both environments and buffers:
    # the local instruction body never needs to know that it is part of a
    # larger batched problem.
    src_local = InstructionVariable.new("src_local", config=local_pair)
    tgt_local = InstructionVariable.new("tgt_local", config=local_pair)
    src = InstructionVariable.new("src", config=batched_pairs)
    tgt = InstructionVariable.new("tgt", config=batched_pairs)

    # Create two buffer layers. The outer buffer maps onto the inner one.
    inner_buffer = BufferManager(
        tgt_local,
        name="inner_target_buffer",
    )
    outer_buffer = BufferManager(
        tgt,
        name="outer_target_buffer",
        output_config=inner_buffer.keymap,
        inner_buffer=inner_buffer,
    )

    # Register several symbolic buffer slots. These represent separate write
    # positions even when they eventually reduce back to the same logical target.
    #
    # That is the whole purpose of the buffer helper: keep temporary write
    # positions explicit instead of relying on implicit atomic behavior.
    left_0 = inner_buffer.register(Key("left"))
    left_1 = inner_buffer.register(Key("left"))
    right_0 = inner_buffer.register(Key("right"))

    local_content = InstructionGroup(
        [
            LinearOperationInstruction(
                tgt0=inner_buffer.buffer(left_0),
                src0=src_local(Key("left")),
                alpha=1.0,
            ),
            LinearOperationInstruction(
                tgt0=inner_buffer.buffer(left_1),
                src0=src_local(Key("right")),
                alpha=2.0,
            ),
            LinearOperationInstruction(
                tgt0=inner_buffer.buffer(right_0),
                src0=src_local(Key("right")),
                alpha=3.0,
            ),
        ]
    )

    # The map environments connect the local content to the outer batched
    # variables and to one outer buffer slot per batch.
    mapped = MapApplyInstruction(
        content=local_content,
        environments=[
            InstructionEnvironment(
                {
                    src_local: src(Key(batch)),
                    inner_buffer.buffer: outer_buffer.register(Key(batch)),
                }
            )
            for batch in range(2)
        ],
    )

    # ``apply_environment`` resolves the top-level environment relation and
    # yields an ordinary instruction group again.
    #
    # After that step the demo can inspect the result like any other ordinary
    # instruction tree.
    resolved = mapped.apply_environment(InstructionEnvironment())
    return {
        "resolved": resolved,
        "inner_buffer": inner_buffer,
        "outer_buffer": outer_buffer,
    }


def preview_tozero_lines(backend_name: str):
    # The local variable classes differ by backend. This helper previews the
    # reset lines that one such backend-local buffer variable would emit.
    #
    # We keep this preview separate from the symbolic part so the user can see
    # where backend-local code generation begins.
    local_class = LOCAL_VARIABLE_CLASSES[backend_name]
    temp = local_class("buffer_preview", size=4, dtype="f64")
    return list(temp.generate_tozero_lines())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show explicit BufferManager stacking and reset lines."
    )
    parser.add_argument(
        "--backend",
        default="cuda",
        choices=("plain", "python", "numpy", "c", "fortran", "cuda"),
    )
    args = parser.parse_args()

    data = build_demo()
    resolved = data["resolved"]
    inner_buffer = data["inner_buffer"]
    outer_buffer = data["outer_buffer"]
    backend = get_backend(args.backend)

    print("Tutorial 12: explicit buffered targets")
    print("=" * 60)
    print("Backend:", backend.IDENTIFIER)
    print("Resolved instruction type :", type(resolved).__name__)
    print("Resolved instruction count:", len(list(resolved.instructions)))
    print()
    print("Resolved payload:")
    print(resolved.record_payload(detailed=True))
    print()
    print("Inner buffered offsets:", list(inner_buffer.buffered))
    print("Outer buffered offsets:", list(outer_buffer.buffered))
    print()
    print("Representative reset lines for one buffer variable:")
    for line in preview_tozero_lines(args.backend):
        print("  ", line)
    print()
    print("Outer reduction/copy stages:")
    for num, instruction in enumerate(outer_buffer.resolve_buffer(), start=1):
        print(f"Stage {num}: {type(instruction).__name__}")
        print(instruction.record_payload(detailed=True))


if __name__ == "__main__":
    main()
