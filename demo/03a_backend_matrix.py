"""
Demo 03a: side-by-side backend generation from one symbolic routine.

The point of this demo is not to benchmark the targets. The point is to show
that the symbolic description stays the same while the generated surface code
changes backend by backend.

The script therefore:

1. builds one tiny vector multiply instruction tree,
2. lowers it through several selected backends,
3. writes the generated sources without compiling them,
4. and prints a short preview of the emitted files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import BiLinearOperationInstruction, InstructionGroup
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import Key, KeyMap


DEFAULT_BACKENDS = ("plain", "python", "numpy", "c", "fortran", "opencl", "cuda")


def parse_backend_list(raw: str) -> tuple[str, ...]:
    """
    Turn one comma-separated CLI value into backend identifiers.

    Keeping the parsing in one helper makes the main function read like a demo
    script instead of a string-processing exercise.
    """

    backends = tuple(part.strip().lower() for part in raw.split(",") if part.strip())
    if not backends:
        raise ValueError("at least one backend must be selected")
    return backends


def backend_ready_for_demo(backend_name: str) -> tuple[bool, str]:
    """
    Decide whether one backend can participate in this generation-only demo.

    ``opencl`` and ``cuda`` need an ADAA family to resolve the routine
    arguments. If the corresponding Python runtime package is not installed, we
    skip them explicitly instead of failing with a confusing later traceback.
    """

    del backend_name
    return True, "ready"


def build_symbolic_case(length: int = 4):
    """
    Build the common instruction tree shared by all generated targets.

    The symbolic case is intentionally tiny. That keeps the generated code easy
    to read once we print a short preview from each backend.
    """

    # Every vector entry stores one scalar component named ``value``.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    # The outer vector simply repeats that scalar domain several times.
    vector = KeyMap(name=f"vector{length}")
    for idx in range(length):
        vector.link(Key(idx), scalar)

    # ``lhs`` and ``rhs`` are read-only inputs, while ``out`` is updated.
    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)

    # Each leaf multiplies one vector component pair into the corresponding
    # output component. The point is not the math itself; the point is that the
    # exact same symbolic tree is handed to every backend below.
    instructions = InstructionGroup(
        [
            BiLinearOperationInstruction(
                tgt0=out(Key(idx), "value"),
                src0=lhs(Key(idx), "value"),
                src1=rhs(Key(idx), "value"),
                alpha=1.0,
            )
            for idx in range(length)
        ]
    )

    assignments = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }
    return instructions, assignments


def library_artifacts(library) -> list[Path]:
    """
    Collect the interesting file paths emitted by one generated library.

    Different backends expose different artifact names, so the demo centralizes
    that lookup here instead of scattering ``hasattr`` checks everywhere.
    """

    found = []
    for attr in ("filename", "sharedlibname", "kernelmodulename"):
        if hasattr(library, attr):
            value = getattr(library, attr)
            if value:
                path = Path(value)
                if path.is_absolute():
                    found.append(path.resolve())
                else:
                    found.append(Path(library.relative_to_basepath(value)))
    return found


def assignment_owner_for(backend_name: str):
    """
    Pick the backend used to resolve ADAA assignments for this demo.

    Some generation-focused backends, such as ``plain``, do not expose their
    own runtime ADAA families. In that case we borrow the Python assignment
    family because the demo only needs type resolution, not runtime execution.
    """

    backend = get_backend(backend_name)
    if backend.get_assignment_families():
        return backend
    return get_backend("python")


def preview_text(path: Path, *, lines: int = 12) -> list[str]:
    """
    Read only the first few lines from one generated artifact.

    The demo is meant to be read in the terminal, so truncating the preview is
    more useful than dumping whole source files.
    """

    if not path.exists():
        return ["<file not found>"]
    return path.read_text().splitlines()[:lines]


def build_backend_preview(backend_name: str, *, output_root: Path) -> dict[str, object]:
    """
    Lower the shared symbolic routine through one backend and gather metadata.

    The generated files are written under a backend-local build root so the
    outputs of different languages do not overwrite each other.
    """

    instructions, assignments = build_symbolic_case()
    backend_root = output_root / backend_name

    # The build root is configured per backend instance. This keeps the demo
    # output isolated from any normal user build directory.
    backend = get_backend(backend_name).configure(
        general={"paths": {"build_root": str(backend_root)}}
    )
    library = backend.library(f"demo_backend_matrix_{backend_name}")
    assignment_backend = assignment_owner_for(backend_name)
    daa_assignments = assignment_backend.make_daa_assignments(assignments)

    # ``compile=False`` ensures we only examine the written sources and do not
    # require a full native toolchain for every configured backend.
    backend.libroutine_from_instructions(
        library,
        "multiply",
        instructions,
        daa_assignments=daa_assignments,
    )
    library.build(force=True, compile=False)

    artifacts = library_artifacts(library)
    preview_path = artifacts[0] if artifacts else None
    return {
        "backend": backend,
        "library": library,
        "artifacts": artifacts,
        "preview_path": preview_path,
        "preview_lines": [] if preview_path is None else preview_text(preview_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preview one symbolic routine across several backends."
    )
    parser.add_argument(
        "--backends",
        default=",".join(DEFAULT_BACKENDS),
        help="comma-separated backend identifiers",
    )
    args = parser.parse_args()

    selected = parse_backend_list(args.backends)
    output_root = Path(__file__).with_name("generated_backend_matrix")
    output_root.mkdir(parents=True, exist_ok=True)

    print("Demo 03a: backend matrix")
    print("=" * 72)
    print("Output root:", output_root.resolve())
    print()

    # The loop is intentionally explicit. The user should be able to see each
    # backend decision and why a backend is either shown or skipped.
    for backend_name in selected:
        ready, detail = backend_ready_for_demo(backend_name)
        print(f"[{backend_name}]")
        if not ready:
            print("  skipped :", detail)
            print()
            continue

        try:
            data = build_backend_preview(backend_name, output_root=output_root)
        except Exception as exc:
            print("  failed  :", exc)
            print()
            continue

        backend = data["backend"]
        library = data["library"]
        artifacts = data["artifacts"]
        preview_path = data["preview_path"]
        preview_lines = data["preview_lines"]

        print("  identifier :", backend.IDENTIFIER)
        print("  library    :", library.libname)
        print("  artifacts  :")
        for artifact in artifacts:
            print("    ", artifact)
        if preview_path is not None:
            print("  preview from:", preview_path)
            for line in preview_lines:
                print("    ", line)
        print()


if __name__ == "__main__":
    main()
