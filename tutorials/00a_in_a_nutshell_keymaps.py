"""
Tutorial 00a: PHOENIX in a nutshell, part 1.

This script introduces the smallest useful PHOENIX object: the keymap.
Keymaps describe symbolic storage layouts. Everything that follows in the
tutorial series builds on that idea.
"""

from __future__ import annotations

from phoenix.keymap import Key, KeyMap


def main() -> None:
    # Create a small "leaf" keymap. Leaf keymaps hold actual named entries.
    spin_component = KeyMap(name="spin component")
    spin_component.entry("x")
    spin_component.entry("y")
    spin_component.entry("z")

    # Create a second keymap that links several leaves together.
    #
    # This models a tiny spin chain with two sites. Each site reuses the same
    # "x/y/z" layout from the leaf keymap above.
    spin_chain = KeyMap(name="two-site spin chain")
    spin_chain.link("site0", spin_component)
    spin_chain.link("site1", spin_component)

    print("Tutorial 00a: keymaps in a nutshell")
    print("=" * 60)

    # ``len(keymap)`` returns the number of leaf entries visible through the
    # full recursive structure. Two sites times three components gives six.
    print("Leaf entries in spin_component:", len(spin_component))
    print("Leaf entries in spin_chain    :", len(spin_chain))

    # Show the recursive content. The keys are composed automatically.
    print("\nRecursive key iteration:")
    for key, entry in spin_chain.items(recursive=True):
        print(f"  {key!s:>12} -> {entry}")

    # Composed keys can be built explicitly. ``Key`` is PHOENIX' symbolic key
    # object. Using it directly makes later code easier to read because nested
    # access stays explicit.
    composed_key = Key("site1") | Key("z")
    print("\nComposed key access:")
    print("  key object :", composed_key)
    print("  lookup     :", spin_chain[composed_key])

    # Keymaps also convert between symbolic keys and flat offsets. That bridge
    # is important because generated backends ultimately emit flat arrays.
    offset = spin_chain.key2off("site1", "y")
    print("\nOffset mapping:")
    print("  spin_chain.key2off('site1', 'y') ->", offset)
    print("  spin_chain.off2key(offset)       ->", spin_chain.off2key(offset))
    print("  spin_chain.off2dom(offset)       ->", spin_chain.off2dom(offset))

    # ``tree()`` is a compact way to visualize the nested structure.
    print("\nKeymap tree:")
    for level, _key, entry in spin_chain.tree():
        print("  " * level + f"- {entry}")


if __name__ == "__main__":
    main()
