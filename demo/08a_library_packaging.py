"""
Demo 08a: organize generated libraries and one shared makefile.

This demo focuses on file layout rather than numerical execution. It shows how
several small generated libraries can be written side by side and then attached
to one shared makefile that documents the resulting build graph.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import (
    BiLinearOperationInstruction,
    CallInstruction,
    InstructionGroup,
)
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.fgen.makefile import MakeFileManager
from phoenix.keymap import Key, KeyMap


def build_vector_layout():
    """
    Build the shared vector layout used by all routines in this packaging demo.

    Using one common layout makes the final dependency graph easier to follow:
    every routine accepts the same symbolic argument contract.
    """

    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)

    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)
    return lhs, rhs, out


def build_packaged_libraries(backend_name: str, *, output_root: Path):
    """
    Create several libraries that can later be collected in one makefile.

    Three tiny ``core`` libraries each own one leaf routine. A fourth
    ``pipeline`` library depends on those routines via ``CallInstruction``.
    """

    lhs, rhs, out = build_vector_layout()
    backend = get_backend(backend_name).configure(
        general={"paths": {"build_root": str(output_root)}}
    )
    assignment_config = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }

    libraries = {}
    routines = {}
    for label, idx in zip(("a", "b", "c"), range(3), strict=True):
        library = backend.library(f"demo_packaged_core_{label}")
        routine = backend.libroutine_from_instructions(
            library,
            f"component_{label}",
            InstructionGroup(
                [
                    BiLinearOperationInstruction(
                        tgt0=out(Key(idx), "value"),
                        src0=lhs(Key(idx), "value"),
                        src1=rhs(Key(idx), "value"),
                        alpha=1.0,
                    )
                ]
            ),
            assignment_config=assignment_config,
        )
        libraries[label] = library
        routines[label] = routine

    # The pipeline library does not implement new leaf operations itself. Its
    # value is the explicit dependency structure: it packages several existing
    # routines into one higher-level entry point.
    pipeline = backend.library("demo_packaged_pipeline")
    backend.libroutine_from_instructions(
        pipeline,
        "pipeline",
        CallInstruction(routines["a"]),
        CallInstruction(routines["b"]),
        CallInstruction(routines["c"]),
        assignment_config=assignment_config,
    )
    libraries["pipeline"] = pipeline
    return libraries


def primary_artifact(library):
    """
    Pick the most useful artifact path for display.

    Different backends expose different primary files, so the demo keeps the
    display logic in one place.
    """

    for attr in ("sharedlibname", "filename", "kernelmodulename"):
        if hasattr(library, attr):
            value = getattr(library, attr)
            if value:
                path = Path(value)
                if path.is_absolute():
                    return path.resolve()
                return Path(library.relative_to_basepath(value))
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate several small libraries and one shared makefile."
    )
    parser.add_argument(
        "--backend",
        default="fortran",
        choices=("python", "c", "fortran"),
        help="backend used for the packaged output",
    )
    args = parser.parse_args()

    output_root = Path(__file__).with_name("generated_packaging_demo")
    output_root.mkdir(parents=True, exist_ok=True)

    libraries = build_packaged_libraries(args.backend, output_root=output_root)
    makefile = MakeFileManager("demo_packaging")

    # We write each library first, then attach it to the shared makefile. Doing
    # those steps explicitly makes the packaging workflow visible to the user.
    for library in libraries.values():
        ok, exc = library.prepare()
        if not ok:
            raise RuntimeError(f"Failed to prepare {library.libname}: {exc}") from exc
        ok, exc = library.write()
        if not ok:
            raise RuntimeError(f"Failed to write {library.libname}: {exc}") from exc
        makefile.append_library(library)

    makefile_path = output_root / makefile.filename
    makefile.set_filename(makefile_path)
    makefile.create_file(include_silent=True)

    print("Demo 08a: library packaging")
    print("=" * 72)
    print("Selected backend:", args.backend)
    print("Output root      :", output_root.resolve())
    print("Libraries:")
    for label, library in libraries.items():
        print(f"  {label:<8} -> {primary_artifact(library)}")
    print()
    print("Shared makefile:", makefile_path.resolve())
    print()
    print("First makefile lines:")
    for line in makefile_path.read_text().splitlines()[:20]:
        print("  ", line)


if __name__ == "__main__":
    main()
