"""
Demo 02a: keymaps for a tiny spin chain in Pauli-string notation.

This first file is intentionally small and only introduces the symbolic data
layout.  We start with a one-dimensional chain of three spins and keep

- one local polarization component ``"z"`` on every site,
- two pair components ``"xy"`` and ``"yx"`` on every nearest-neighbor bond,
- and two Hamiltonian bond components ``"xx"`` and ``"yy"``.

The important point for the talk is that the keys already look like the physics:

- ``((0, 1), "z")`` means a local polarization on site 1,
- ``(((0, 0), (0, 1)), "xy")`` means the pair component on the first bond.
"""

from __future__ import annotations

from phoenix.keymap import KeyMap


def build_demo_model():
    # This first symbolic demo only needs one short one-dimensional chain.
    sites = (0, 1, 2)
    bonds = ((0, 1), (1, 2))

    # ``site_domain`` describes what one single site stores.
    site_domain = KeyMap(name="site_domain")
    site_domain.entry("z")

    # ``pair_domain`` describes the two correlation channels stored per bond.
    pair_domain = KeyMap(name="pair_domain")
    pair_domain.entry("xy")
    pair_domain.entry("yx")

    # ``ham_domain`` is the local Hamiltonian layout attached to every bond.
    ham_domain = KeyMap(name="ham_domain")
    ham_domain.entry("xx")
    ham_domain.entry("yy")

    # The global keymaps are built by attaching those local domains repeatedly.
    state_keymap = KeyMap(name="state_1d_three_spins")
    ham_keymap = KeyMap(name="ham_1d_three_spins")

    for site in sites:
        state_keymap.link(site, site_domain)
    for bond in bonds:
        state_keymap.link(bond, pair_domain)
        ham_keymap.link(bond, ham_domain)

    return {
        "sites": sites,
        "bonds": bonds,
        "state_keymap": state_keymap,
        "ham_keymap": ham_keymap,
    }


def main() -> None:
    model = build_demo_model()

    print("Demo 02a: keymaps for a 1D three-spin chain")
    print("=" * 72)
    print("State entries:")
    for site in model["sites"]:
        print(f"  {site!r} -> components ('z',)")
    for bond in model["bonds"]:
        print(f"  {bond!r} -> components ('xy', 'yx')")
    print()
    print("Hamiltonian entries:")
    for bond in model["bonds"]:
        print(f"  {bond!r} -> components ('xx', 'yy')")
    print()
    print("State keymap size      :", len(model["state_keymap"]))
    print("Hamiltonian keymap size:", len(model["ham_keymap"]))
    print()
    print("Example offsets and targets:")
    print("  (0, 'z') ->", model["state_keymap"].goto(0, "z"))
    print(
        "  ((0, 1), 'xy') ->",
        model["state_keymap"].goto((0, 1), "xy"),
    )
    print(
        "  ((1, 2), 'xx') in H ->",
        model["ham_keymap"].goto((1, 2), "xx"),
    )


if __name__ == "__main__":
    main()
