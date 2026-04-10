"""
Demo 04a: explicit buffers and serial vs OpenMP resource lowering.

This demo deliberately combines two topics that often appear together in real
applications:

1. multiple symbolic writes may target the same logical output location, so we
   stage them through explicit buffers and then reduce/copy them back, and
2. a routine can be emitted either with a serial resource preset or an OpenMP
   preset.

The focus is the structure, not benchmark numbers. We therefore inspect the
buffer layout symbolically and the parallel resource lowering textually rather
than timing the result.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.buffermanager import BufferManager
from phoenix.fgen.instruction import (
    BiLinearOperationInstruction,
    InstructionGroup,
    LinearOperationInstruction,
    MapApplyInstruction,
)
from phoenix.fgen.instructionvar import InstructionEnvironment, InstructionVariable
from phoenix.keymap import Key, KeyMap


def build_buffered_case():
    """
    Build one tiny buffered accumulation tree.

    The target vector has two logical entries. We intentionally write to the
    left entry twice so the reader can see how the buffer manager resolves
    write conflicts into explicit reduction stages.
    """

    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    vector = KeyMap(name="vector2")
    for idx in range(2):
        vector.link(Key(idx), scalar)

    src = InstructionVariable.new("src", config=vector)
    tgt = InstructionVariable.new("tgt", config=vector)

    # ``buffer`` owns one dynamic keymap that grows as we register buffered
    # slots. Every registration represents one separate write position.
    buffer = BufferManager(tgt, name="tgt_buffer")
    left_0 = buffer.register(0)
    left_1 = buffer.register(0)
    right_0 = buffer.register(1)

    # The first stage writes only into the temporary buffer slots.
    staged_writes = InstructionGroup(
        [
            LinearOperationInstruction(
                tgt0=buffer.buffer(left_0),
                src0=src(0, "value"),
                alpha=1.0,
            ),
            LinearOperationInstruction(
                tgt0=buffer.buffer(left_1),
                src0=src(1, "value"),
                alpha=2.0,
            ),
            LinearOperationInstruction(
                tgt0=buffer.buffer(right_0),
                src0=src(1, "value"),
                alpha=3.0,
            ),
        ]
    )

    # ``resolve_buffer`` yields the reduction and copy-back stages needed to
    # turn those temporary writes into ordinary writes to ``tgt``.
    reduction_stages = list(buffer.resolve_buffer())
    full_tree = InstructionGroup([staged_writes, *reduction_stages])

    base_assignments = {
        src: Config(status="R", family="real"),
        tgt: Config(status="RW", family="real"),
    }
    buffer_assignments = buffer.assignment_configs(base_assignments, status="B")
    all_assignments = dict(base_assignments)
    all_assignments.update(buffer_assignments)

    return {
        "instruction_tree": full_tree,
        "buffer": buffer,
        "assignments": all_assignments,
    }


def build_parallel_preview_case():
    """
    Build one simple vector multiply routine used only for resource preview.

    This second case is deliberately simpler than the buffered symbolic tree
    above. The goal is to show serial vs OpenMP source emission cleanly.
    """

    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    vector = KeyMap(name="vector4")
    for idx in range(4):
        vector.link(Key(idx), scalar)

    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)

    # Build one local scalar worker body first.
    lhs_local = InstructionVariable.new("lhs_local", config=scalar)
    rhs_local = InstructionVariable.new("rhs_local", config=scalar)
    out_local = InstructionVariable.new("out_local", config=scalar)

    worker = InstructionGroup(
        [
            BiLinearOperationInstruction(
                tgt0=out_local("value"),
                src0=lhs_local("value"),
                src1=rhs_local("value"),
                alpha=1.0,
            )
        ]
    )

    # Then map that worker over all vector positions. This produces a clearer
    # parallel lowering path than emitting four independent leaf operations.
    instruction_tree = MapApplyInstruction(
        content=worker,
        environments=[
            InstructionEnvironment(
                {
                    lhs_local: lhs(Key(idx)),
                    rhs_local: rhs(Key(idx)),
                    out_local: out(Key(idx)),
                }
            )
            for idx in range(4)
        ],
    )
    assignments = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }
    return instruction_tree, assignments


def build_resource_preview(backend_name: str, *, output_root: Path, threads: int) -> tuple[Path, str]:
    """
    Generate serial and OpenMP variants for one backend and return the source.

    The generated code is not compiled here. We only need the text output so we
    can point at the serial routine, the OpenMP routine, and the pragma lines.
    """

    instruction_tree, assignments = build_parallel_preview_case()
    build_root = output_root / backend_name

    serial_backend = get_backend(backend_name).configure(
        general={"paths": {"build_root": str(build_root)}}
    )
    parallel_backend = serial_backend.configure(
        general={"runtime": {"num_processors": threads}}
    )

    library = serial_backend.library(f"demo_buffered_{backend_name}")
    serial_backend.libroutine_from_instructions(
        library,
        "multiply_serial",
        instruction_tree,
        assignment_config=assignments,
        resource_name="serial",
    )
    parallel_backend.libroutine_from_instructions(
        library,
        "multiply_parallel",
        instruction_tree,
        assignment_config=assignments,
        resource_name="omp",
    )
    library.build(force=True, compile=False)
    source_path = Path(library.relative_to_basepath(library.filename))
    return source_path, source_path.read_text()


def interesting_lines(text: str, *, backend_name: str) -> list[str]:
    """
    Extract the most instructive lines from the generated source.

    We keep the filter small so the output stays readable in a terminal demo.
    """

    lowered = []
    for line in text.splitlines():
        stripped = line.strip()
        lowered_stripped = stripped.lower()
        if "multiply_serial" in lowered_stripped or "multiply_parallel" in lowered_stripped:
            lowered.append(stripped)
            continue
        if backend_name == "c" and "#pragma omp" in stripped:
            lowered.append(stripped)
            continue
        if backend_name == "fortran" and "!$OMP" in stripped:
            lowered.append(stripped)
            continue
    return lowered


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show explicit buffers and serial/OpenMP lowering."
    )
    parser.add_argument(
        "--backend",
        default="fortran",
        choices=("c", "fortran"),
        help="language backend used for the serial/OpenMP preview",
    )
    parser.add_argument(
        "--threads",
        default=4,
        type=int,
        help="thread count forwarded into the OpenMP resource",
    )
    args = parser.parse_args()

    demo = build_buffered_case()
    output_root = Path(__file__).with_name("generated_buffer_parallel")
    output_root.mkdir(parents=True, exist_ok=True)

    source_path, source_text = build_resource_preview(
        args.backend,
        output_root=output_root,
        threads=args.threads,
    )

    print("Demo 04a: buffers and parallelism")
    print("=" * 72)
    print("Selected backend :", args.backend)
    print("Configured threads:", args.threads)
    print("Generated source :", source_path)
    print()
    print("Buffered symbolic slots:")
    for logical_offset, buffered_key in demo["buffer"].buffered:
        print("  logical target", logical_offset, "-> buffer slot", buffered_key)
    print()
    print("Buffered symbolic stages:")
    for num, instruction in enumerate(demo["instruction_tree"].instructions, start=1):
        print(f"  stage {num}: {type(instruction).__name__}")
    print()
    print("Interesting serial/OpenMP source lines:")
    for line in interesting_lines(source_text, backend_name=args.backend):
        print("  ", line)


if __name__ == "__main__":
    main()
