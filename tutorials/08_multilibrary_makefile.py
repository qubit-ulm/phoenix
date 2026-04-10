"""
Tutorial 08: multiple libraries and one shared makefile.

This tutorial focuses on library orchestration rather than numerical execution.
The central idea is that several libraries built with the same backend can
contribute targets to one shared makefile.
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


def create_vector_setup():
    # Reuse the familiar nested three-entry vector layout.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")
    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)
    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)
    return vector, lhs, rhs, out


def build_demo_libraries(backend_name: str):
    _vector, lhs, rhs, out = create_vector_setup()
    backend = get_backend(backend_name)
    libraries = {}
    routines = {}
    assignment_config = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }

    # Create three tiny libraries that each compute one component of the final
    # result. This makes the later dependency graph easy to understand.
    #
    # The artificial split is deliberate: it produces a visible dependency
    # graph in the shared makefile without burying that graph in too much math.
    for label, idx in zip(("a", "b", "c"), range(3), strict=True):
        library = backend.library(f"tutorial_library_{label}")
        routine = backend.libroutine_from_instructions(
            library,
            f"subroutine_{label}",
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

    # Create a fourth library that depends on the first three via
    # ``CallInstruction``. The resulting makefile therefore contains multiple
    # library targets with explicit dependencies.
    library_d = backend.library("tutorial_library_d")
    backend.libroutine_from_instructions(
        library_d,
        "subroutine_d",
        CallInstruction(routines["a"]),
        CallInstruction(routines["b"]),
        CallInstruction(routines["c"]),
        assignment_config=assignment_config,
    )
    libraries["d"] = library_d
    return libraries


def library_artifact(library):
    # Different backends expose different primary artifacts. This helper picks
    # the most useful display name for the current backend.
    #
    # For a Python backend that will usually be the generated module file. For
    # native backends it is more often the generated source or shared library.
    for attr in ("sharedlibname", "filename", "kernelmodulename"):
        if hasattr(library, attr):
            return getattr(library, attr)
    return "<unknown>"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate several compatible libraries and one shared makefile."
    )
    parser.add_argument(
        "--backend",
        default="fortran",
        choices=("python", "c", "fortran"),
    )
    args = parser.parse_args()

    output_dir = Path(__file__).with_name("generated_multilib_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    libraries = build_demo_libraries(args.backend)
    makefile = MakeFileManager("tutorial_multilib")

    # Each library is prepared and written individually, then attached to the
    # shared makefile manager.
    #
    # Keeping those steps explicit shows that PHOENIX libraries are ordinary
    # build artifacts that can be collected and orchestrated afterwards.
    for library in libraries.values():
        ok, exc = library.prepare()
        if not ok:
            raise RuntimeError(
                f"Failed to prepare {library.libname}: {exc}"
            ) from exc
        ok, exc = library.write()
        if not ok:
            raise RuntimeError(
                f"Failed to write {library.libname}: {exc}"
            ) from exc
        makefile.append_library(library)

    makefile_path = output_dir / makefile.filename
    makefile.set_filename(makefile_path)
    makefile.create_file(include_silent=True)

    print("Tutorial 08: multi-library makefile")
    print("=" * 60)
    print("Backend          :", args.backend)
    print("Output directory :", output_dir.resolve())
    print("Libraries:")
    for name, library in libraries.items():
        print(f"  {name}: {library_artifact(library)}")
    print()
    print("Generated makefile:", makefile_path.resolve())
    print()
    print("First lines:\n")
    text = makefile_path.read_text().splitlines()
    for line in text[:20]:
        print(line)


if __name__ == "__main__":
    main()
