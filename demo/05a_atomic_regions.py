"""
Demo 05a: atomic region lowering.

This demo compares four atomic variants:

1. leaf-attached atomic wrapping,
2. region-attached atomic wrapping,
3. explicit ``policy="off"``,
4. and a serial-resource case where no OpenMP synchronization is emitted.

The intent is to make the user-visible atomic controls concrete before moving
to larger kernels.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from phoenix.fgen.atomic import AtomicRegionInstruction
from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import BiLinearOperationInstruction, InstructionGroup
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import KeyMap


def build_atomic_symbolic_case():
    """
    Build one tiny pair-wise multiply routine suitable for atomic wrapping.

    Two independent leaf operations are enough to show the difference between
    leaf-level and region-level attachment without creating a large source file.
    """

    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    pair = KeyMap(name="pair")
    pair.link("left", scalar)
    pair.link("right", scalar)

    lhs = InstructionVariable.new("lhs", config=pair)
    rhs = InstructionVariable.new("rhs", config=pair)
    out = InstructionVariable.new("out", config=pair)

    content = InstructionGroup(
        [
            BiLinearOperationInstruction(
                tgt0=out("left", "value"),
                src0=lhs("left", "value"),
                src1=rhs("left", "value"),
                alpha=1.0,
            ),
            BiLinearOperationInstruction(
                tgt0=out("right", "value"),
                src0=lhs("right", "value"),
                src1=rhs("right", "value"),
                alpha=1.0,
            ),
        ]
    )
    assignments = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }
    return content, assignments


def generate_variant(
    backend_name: str,
    *,
    output_root: Path,
    variant_name: str,
    attachment_mode: str,
    policy: str,
    resource_name: str,
) -> tuple[Path, str]:
    """
    Generate one atomic variant and return the source text.

    Each variant uses its own build root subdirectory so the preview files stay
    easy to inspect afterwards.
    """

    content, assignments = build_atomic_symbolic_case()
    build_root = output_root / f"{backend_name}_{variant_name}"

    backend = get_backend(backend_name).configure(
        general={"paths": {"build_root": str(build_root)}}
    )
    library = backend.library(f"demo_atomic_{variant_name}")
    backend.libroutine_from_instructions(
        library,
        "atomic_demo",
        AtomicRegionInstruction(
            content,
            attachment_mode=attachment_mode,
            policy=policy,
        ),
        assignment_config=assignments,
        resource_name=resource_name,
    )
    library.build(force=True, compile=False)
    source_path = Path(library.relative_to_basepath(library.filename))
    return source_path, source_path.read_text()


def extract_atomic_preview(text: str) -> list[str]:
    """
    Keep only the synchronization-related lines from one generated source.

    The surrounding routine boilerplate is not the important part of this demo,
    so we filter down to the relevant wrapper markers.
    """

    preview = []
    for line in text.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if "atomic_demo" in lowered:
            preview.append(stripped)
        elif "omp atomic" in lowered or "omp critical" in lowered:
            preview.append(stripped)
        elif "#pragma omp atomic" in lowered or "#pragma omp critical" in lowered:
            preview.append(stripped)
    return preview


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preview atomic region lowering for one backend."
    )
    parser.add_argument(
        "--backend",
        default="fortran",
        choices=("c", "fortran"),
        help="language backend used for the preview",
    )
    args = parser.parse_args()

    variants = (
        ("leaf_atomic", "leaf", "critical", "omp"),
        ("region_atomic", "region", "critical", "omp"),
        ("off_atomic", "leaf", "off", "omp"),
        ("serial_reference", "leaf", "critical", "serial"),
    )
    output_root = Path(__file__).with_name("generated_atomic_regions")
    output_root.mkdir(parents=True, exist_ok=True)

    print("Demo 05a: atomic regions")
    print("=" * 72)
    print("Selected backend:", args.backend)
    print()

    for name, attachment_mode, policy, resource_name in variants:
        print(f"[{name}]")
        print("  attachment mode:", attachment_mode)
        print("  policy         :", policy)
        print("  resource       :", resource_name)
        source_path, text = generate_variant(
            args.backend,
            output_root=output_root,
            variant_name=name,
            attachment_mode=attachment_mode,
            policy=policy,
            resource_name=resource_name,
        )
        print("  source         :", source_path)
        for line in extract_atomic_preview(text):
            print("   ", line)
        print()


if __name__ == "__main__":
    main()
