"""
Tutorial 15: MapApplyInstruction.

This tutorial demonstrates ``MapApplyInstruction`` directly. A mapapply takes a
local instruction template and a list of environments, then applies that local
template once per environment.
"""

from __future__ import annotations

from phoenix.fgen.instruction import (
    InstructionGroup,
    LinearOperationInstruction,
    MapApplyInstruction,
)
from phoenix.fgen.instructionvar import InstructionEnvironment, InstructionVariable
from phoenix.keymap import Key, KeyMap


def build_mapapply_demo():
    # Build a local scalar layout and a batched outer vector layout.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    vector = KeyMap(name="vector4")
    for idx in range(4):
        vector.link(Key(idx), scalar)

    # Local variables describe one worker body. Global variables describe the
    # full vector visible to the final routine caller.
    local_src = InstructionVariable.new("local_src", config=scalar)
    local_out = InstructionVariable.new("local_out", config=scalar)
    global_src = InstructionVariable.new("global_src", config=vector)
    global_out = InstructionVariable.new("global_out", config=vector)

    content = InstructionGroup(
        [
            LinearOperationInstruction(
                tgt0=local_out("value"),
                src0=local_src("value"),
                alpha=2.0,
            )
        ]
    )

    # Build one environment per vector position. ``MapApplyInstruction`` will
    # later reuse the same local content once per environment entry.
    environments = [
        InstructionEnvironment(
            {
                local_src: global_src(Key(idx)),
                local_out: global_out(Key(idx)),
            }
        )
        for idx in range(4)
    ]

    mapped = MapApplyInstruction(content=content, environments=environments)
    return content, mapped


def main() -> None:
    content, mapped = build_mapapply_demo()
    # ``unpack()`` is useful here because it makes the replication explicit:
    # the reader can compare the compact mapped form with the expanded form.
    flattened = InstructionGroup(mapped.unpack())

    print("Tutorial 15: mapapply instruction")
    print("=" * 60)
    print("Local content payload:")
    print(content.record_payload(detailed=True))
    print()
    print("MapApply payload:")
    print(mapped.record_payload(detailed=True))
    print()
    print("Flattened/unpacked payload:")
    print(flattened.record_payload(detailed=True))


if __name__ == "__main__":
    main()
