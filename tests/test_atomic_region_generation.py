from __future__ import annotations

from pathlib import Path

from phoenix.fgen.atomic import AtomicRegionInstruction
from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import (
    BiLinearOperationInstruction,
    InstructionGroup,
)
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import KeyMap


def make_atomic_case():
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


def build_atomic_source(
    tmp_path,
    backend_name,
    *,
    attachment_mode="leaf",
    policy="critical",
    resource_name="omp",
):
    content, assignments = make_atomic_case()
    backend = get_backend(backend_name).configure(
        general={"paths": {"build_root": str(tmp_path)}}
    )
    library = backend.library(f"{backend_name}_atomic_generation")
    backend.libroutine_from_instructions(
        library,
        "atomic_mul",
        AtomicRegionInstruction(
            content,
            attachment_mode=attachment_mode,
            policy=policy,
        ),
        assignment_config=assignments,
        resource_name=resource_name,
    )
    library.build(force=True, compile=False)
    return Path(library.relative_to_basepath(library.filename)).read_text()


def test_fortran_leaf_atomic_region_distributes_to_leaf_pragmas(tmp_path):
    generated = build_atomic_source(tmp_path, "fortran", attachment_mode="leaf")

    assert generated.count("!$OMP ATOMIC") == 2
    assert "!$OMP CRITICAL" not in generated


def test_fortran_region_atomic_region_stays_region_wrapper(tmp_path):
    generated = build_atomic_source(tmp_path, "fortran", attachment_mode="region")

    assert generated.count("!$OMP CRITICAL") == 1
    assert generated.count("!$OMP END CRITICAL") == 1
    assert "!$OMP ATOMIC" not in generated


def test_c_leaf_atomic_region_distributes_to_leaf_pragmas(tmp_path):
    generated = build_atomic_source(tmp_path, "c", attachment_mode="leaf")

    assert generated.count("#pragma omp atomic") == 2
    assert "#pragma omp critical" not in generated


def test_atomic_region_policy_off_disables_atomic_wrapping(tmp_path):
    generated = build_atomic_source(
        tmp_path,
        "fortran",
        attachment_mode="leaf",
        policy="off",
    )

    assert "!$OMP ATOMIC" not in generated
    assert "!$OMP CRITICAL" not in generated
