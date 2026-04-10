"""
Tutorial 14: instruction environments.

This tutorial introduces ``InstructionEnvironment`` directly. The purpose of an
environment is to rewrite a local instruction template in terms of outer
variables without changing the template itself.
"""

from __future__ import annotations

from phoenix.fgen.instruction import InstructionGroup, LinearOperationInstruction
from phoenix.fgen.instructionvar import InstructionEnvironment, InstructionVariable
from phoenix.keymap import Key, KeyMap


def build_environment_demo():
    # Build two layouts:
    #
    #   scalar -> one value used by the local template
    #   vector -> three scalar entries used by the outer variables
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)

    # ``local_src`` / ``local_out`` define the reusable local instruction
    # template, while ``global_src`` / ``global_out`` are the actual public
    # variables.
    local_src = InstructionVariable.new("local_src", config=scalar)
    local_out = InstructionVariable.new("local_out", config=scalar)
    global_src = InstructionVariable.new("global_src", config=vector)
    global_out = InstructionVariable.new("global_out", config=vector)

    template = InstructionGroup(
        [
            LinearOperationInstruction(
                tgt0=local_out("value"),
                src0=local_src("value"),
                alpha=3.0,
            )
        ]
    )

    # The environment states: interpret the local template as operating on the
    # second vector element of the global variables.
    #
    # In other words: the local template itself never changes, but the meaning
    # of its symbolic variables is redirected by the environment.
    environment = InstructionEnvironment(
        {
            local_src: global_src(Key(1)),
            local_out: global_out(Key(1)),
        }
    )
    return template, environment


def main() -> None:
    template, environment = build_environment_demo()
    # ``apply_environment`` is the key operation of this tutorial. It produces
    # a new instruction tree where all local variables have been interpreted in
    # the requested outer context.
    resolved = template.apply_environment(environment)

    print("Tutorial 14: instruction environments")
    print("=" * 60)
    print("Template payload:")
    print(template.record_payload(detailed=True))
    print()
    print("Environment mapping:")
    print(environment.as_dict())
    print()
    print("Resolved payload:")
    print(resolved.record_payload(detailed=True))


if __name__ == "__main__":
    main()
