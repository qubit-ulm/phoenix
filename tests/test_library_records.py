from __future__ import annotations

from pathlib import Path

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import InstructionGroup, LinearOperationInstruction
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import Key, KeyMap


def make_library_case():
    scalar = KeyMap(name="scalar")
    scalar.entry("value")
    vector = KeyMap(name="vector")
    vector.link("a", scalar)
    vector.link("b", scalar)

    lhs = InstructionVariable.new("lhs", config=vector)
    out = InstructionVariable.new("out", config=vector)
    instruction = InstructionGroup(
        [
            LinearOperationInstruction(
                tgt0=out(Key("a"), "value"),
                src0=lhs(Key("a"), "value"),
                alpha=1.0,
            ),
            LinearOperationInstruction(
                tgt0=out(Key("b"), "value"),
                src0=lhs(Key("b"), "value"),
                alpha=2.0,
            ),
        ]
    )
    return vector, lhs, out, instruction


def test_library_content_and_checksum_change(tmp_path):
    _vector, lhs, out, instruction = make_library_case()
    backend = get_backend("python").configure(
        general={"paths": {"build_root": str(tmp_path)}}
    )
    library = backend.library("release_library")
    assignments = {
        lhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }

    backend.libroutine_from_instructions(
        library,
        "copy_one",
        instruction,
        assignment_config=assignments,
    )
    checksum_before = library.build_checksum

    backend.libroutine_from_instructions(
        library,
        "copy_two",
        instruction,
        assignment_config=assignments,
    )
    checksum_after = library.build_checksum

    assert library["copy_one"] is not None
    assert library["copy_two"] is not None
    assert checksum_before != checksum_after
    assert sorted(name for name, _ in library.content) == ["copy_one", "copy_two"]


def test_library_build_writes_generated_module(tmp_path):
    _vector, lhs, out, instruction = make_library_case()
    backend = get_backend("python").configure(
        general={"paths": {"build_root": str(tmp_path)}}
    )
    library = backend.library("release_library_build")
    backend.libroutine_from_instructions(
        library,
        "copy_one",
        instruction,
        assignment_config={
            lhs: Config(status="R", family="real"),
            out: Config(status="RW", family="real"),
        },
    )

    library.build(force=True, compile=False)
    generated = Path(library.relative_to_basepath(library.filename))

    assert generated.exists()
    assert "copy_one" in generated.read_text()
