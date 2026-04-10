"""
Tutorial 01: keymaps and instruction variables.

This first tutorial stays entirely on the symbolic layer. No backend is
selected and no code is generated yet. The goal is simply to show how PHOENIX
describes structured storage layouts and how symbolic variables point into that
layout.
"""

from __future__ import annotations

# ``InstructionVariable`` is the symbolic variable class used inside
# instructions, and ``KeyMap`` / ``Key`` define symbolic storage layouts.
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import Key, KeyMap


def main() -> None:
    print("Tutorial 01: symbolic storage with keymaps")
    print("=" * 60)

    # ``scalar`` is the smallest useful keymap in this tutorial: it contains
    # exactly one entry called ``value``.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    # ``vector`` is a nested keymap. Each integer key points to the same scalar
    # sub-layout, so the resulting structure is:
    #
    #   vector
    #     0 -> scalar -> value
    #     1 -> scalar -> value
    #     2 -> scalar -> value
    vector = KeyMap(name="vector3")
    for idx in range(3):
        vector.link(Key(idx), scalar)

    # ``InstructionVariable.new(...)`` creates a fresh symbolic variable class.
    # Every call such as ``lhs(Key(1), "value")`` creates one symbolic
    # reference into the layout that can later be consumed by instructions.
    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)

    print("Created keymap:", vector)
    print("Scalar sub-layout size:", scalar.size)
    print("Vector layout size    :", vector.size)
    print("Symbolic variable class:", lhs.get_name())
    print()
    print("Three addressed entries:")

    # Each line below shows two symbolic references. At this point these are
    # not numbers and not memory addresses. They are symbolic placeholders
    # describing where a later instruction will read or write.
    for idx in range(3):
        print(" ", lhs(Key(idx), "value"), rhs(Key(idx), "value"))

    print()
    print("Offset roundtrip example:")

    # Keymaps can also translate symbolic keys to flat offsets and back again.
    # That ability is one of the core pieces that lets PHOENIX bridge symbolic
    # layouts and generated low-level code.
    offset = vector.key2off(Key(2), "value")
    print("  key  (2, value) -> offset", offset)
    print("  move offset back ->", vector.off2key(offset))
    print()
    print("This symbolic information is what later builders lower to code.")


if __name__ == "__main__":
    main()
