from __future__ import annotations

from pathlib import Path

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import BiLinearOperationInstruction, InstructionGroup
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import Key, KeyMap


def make_logging_case():
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)

    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)

    instruction = InstructionGroup(
        [
            BiLinearOperationInstruction(
                tgt0=out(Key(idx), "value"),
                src0=lhs(Key(idx), "value"),
                src1=rhs(Key(idx), "value"),
                alpha=1.0,
            )
            for idx in range(3)
        ]
    )
    assignments = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }
    return instruction, assignments


def test_build_logging_is_written_to_library_build_directory(tmp_path):
    instruction, assignments = make_logging_case()
    backend = get_backend("python").configure(
        general={
            "paths": {"build_root": str(tmp_path)},
            "logging": {"level": "DEBUG", "stdout": False},
        }
    )
    library = backend.library("logging_demo")
    backend.libroutine_from_instructions(
        library,
        "multiply",
        instruction,
        assignment_config=assignments,
    )

    library.build(force=True, compile=False)

    log_path = Path(library.relative_to_basepath(library.logname))
    text = log_path.read_text()

    assert log_path.parent == Path(library.basepath).resolve()
    assert "Starting build for" in text
    assert "Completed build for" in text


def test_force_build_resets_existing_logfile(tmp_path):
    instruction, assignments = make_logging_case()
    backend = get_backend("python").configure(
        general={
            "paths": {"build_root": str(tmp_path)},
            "logging": {"level": "INFO", "stdout": False},
        }
    )
    first_library = backend.library("logging_demo_reset")
    backend.libroutine_from_instructions(
        first_library,
        "multiply",
        instruction,
        assignment_config=assignments,
    )

    first_library.build(force=True, compile=False)
    log_path = Path(first_library.relative_to_basepath(first_library.logname))
    first_text = log_path.read_text()
    assert first_text.count("Starting build for") == 1

    log_path.write_text(first_text + "\nSTALE MARKER\n")
    second_library = backend.library("logging_demo_reset")
    backend.libroutine_from_instructions(
        second_library,
        "multiply",
        instruction,
        assignment_config=assignments,
    )
    second_library.build(force=True, compile=False)
    second_text = log_path.read_text()

    assert "STALE MARKER" not in second_text
    assert second_text.count("Starting build for") == 1
