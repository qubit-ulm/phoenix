"""
Demo 02c: move from explicit environments to MapApplyInstruction on a 2D lattice.

Compared with demo 02b, this script makes two conceptual steps:

1. sites are now addressed by row and column, so pair terms are keyed like
   ``(((i_1, j_1), (i_2, j_2)), "yx")``;
2. local rules are now replicated with ``MapApplyInstruction``.

To avoid a dummy "missing neighbor" entry, we split the bond updates by
coordination class.  Each mapped case only contains the neighbors that really
exist for that kind of bond.
"""

from __future__ import annotations

import argparse
from collections import defaultdict

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import (
    BiLinearOperationInstruction,
    CallInstruction,
    InstructionGroup,
    MapApplyInstruction,
    ParametricInstructionGroup,
)
from phoenix.fgen.instructionvar import (
    InstructionEnvironment,
    InstructionVariable,
)
from phoenix.keymap import KeyMap


POL_TO_PAIR_SCALE = 1.0
PAIR_TO_POL_SCALE = 1.0
NEIGHBOR_PAIR_SCALE = 0.35


def lattice_sites(rows: int, cols: int):
    # Enumerate all lattice sites in row-major order so the demo output stays
    # easy to read and compare across backends.
    return tuple((row, col) for row in range(rows) for col in range(cols))


def lattice_bonds(rows: int, cols: int):
    # Horizontal and vertical nearest-neighbor bonds are both included.
    bonds = []
    for row in range(rows):
        for col in range(cols):
            site = (row, col)
            if col + 1 < cols:
                bonds.append((site, (row, col + 1)))
            if row + 1 < rows:
                bonds.append((site, (row + 1, col)))
    return tuple(bonds)


def bond_kind(bond):
    (r0, _), (r1, _) = bond
    return "h" if r0 == r1 else "v"


def build_demo_model(rows: int, cols: int):
    # The 2D model reuses the same local domains as the 1D chain demos, but it
    # attaches them to site tuples and bond tuples instead of simple labels.
    sites = lattice_sites(rows, cols)
    bonds = lattice_bonds(rows, cols)

    site_domain = KeyMap(name="site_domain")
    site_domain.entry("z")

    pair_domain = KeyMap(name="pair_domain")
    pair_domain.entry("xy")
    pair_domain.entry("yx")

    ham_domain = KeyMap(name="ham_domain")
    ham_domain.entry("xx")
    ham_domain.entry("yy")

    state_keymap = KeyMap(name=f"state_{rows}x{cols}")
    ham_keymap = KeyMap(name=f"ham_{rows}x{cols}")

    for site in sites:
        state_keymap.link(site, site_domain)
    for bond in bonds:
        state_keymap.link(bond, pair_domain)
        ham_keymap.link(bond, ham_domain)

    tail_neighbors = {}
    head_neighbors = {}
    for bond in bonds:
        tail, head = bond
        tail_neighbors[bond] = tuple(
            other for other in bonds if other != bond and tail in other
        )
        head_neighbors[bond] = tuple(
            other for other in bonds if other != bond and head in other
        )

    return {
        "sites": sites,
        "bonds": bonds,
        "site_domain": site_domain,
        "pair_domain": pair_domain,
        "ham_domain": ham_domain,
        "tail_neighbors": tail_neighbors,
        "head_neighbors": head_neighbors,
        "state_keymap": state_keymap,
        "ham_keymap": ham_keymap,
    }


def create_variables(model):
    rho = InstructionVariable.new("rho", config=model["state_keymap"])
    ham = InstructionVariable.new("ham", config=model["ham_keymap"])
    out = InstructionVariable.new("out", config=model["state_keymap"])
    return rho, ham, out


def create_assignment_config(rho, ham, out):
    return {
        rho: Config(status="R", family="real"),
        ham: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }


def build_local_current_group(
    model,
    num_tail_neighbors: int,
    num_head_neighbors: int,
    *,
    use_parametric_inner: bool,
):
    rho_left = InstructionVariable.new("rho_left", config=model["site_domain"])
    rho_right = InstructionVariable.new(
        "rho_right", config=model["site_domain"]
    )
    tail_pairs = [
        InstructionVariable.new(
            f"tail_pair_{num}", config=model["pair_domain"]
        )
        for num in range(num_tail_neighbors)
    ]
    head_pairs = [
        InstructionVariable.new(
            f"head_pair_{num}", config=model["pair_domain"]
        )
        for num in range(num_head_neighbors)
    ]
    ham_local = InstructionVariable.new(
        "ham_local", config=model["ham_domain"]
    )
    out_pair = InstructionVariable.new("out_pair", config=model["pair_domain"])

    def wrap_local_instructions(local_instructions):
        if use_parametric_inner:
            return ParametricInstructionGroup(local_instructions)
        return InstructionGroup(local_instructions)

    groups = [
        wrap_local_instructions(
            [
                BiLinearOperationInstruction(
                    tgt0=out_pair("xy"),
                    src0=rho_left("z"),
                    src1=ham_local("xx"),
                    alpha=+POL_TO_PAIR_SCALE,
                ),
                BiLinearOperationInstruction(
                    tgt0=out_pair("yx"),
                    src0=rho_left("z"),
                    src1=ham_local("yy"),
                    alpha=-POL_TO_PAIR_SCALE,
                ),
            ]
        ),
        wrap_local_instructions(
            [
                BiLinearOperationInstruction(
                    tgt0=out_pair("xy"),
                    src0=rho_right("z"),
                    src1=ham_local("yy"),
                    alpha=-POL_TO_PAIR_SCALE,
                ),
                BiLinearOperationInstruction(
                    tgt0=out_pair("yx"),
                    src0=rho_right("z"),
                    src1=ham_local("xx"),
                    alpha=+POL_TO_PAIR_SCALE,
                ),
            ]
        ),
    ]

    for pair_var in tail_pairs:
        groups.append(
            wrap_local_instructions(
                [
                    BiLinearOperationInstruction(
                        tgt0=out_pair("xy"),
                        src0=pair_var("xy"),
                        src1=ham_local("xx"),
                        alpha=+NEIGHBOR_PAIR_SCALE,
                    ),
                    BiLinearOperationInstruction(
                        tgt0=out_pair("yx"),
                        src0=pair_var("yx"),
                        src1=ham_local("yy"),
                        alpha=+NEIGHBOR_PAIR_SCALE,
                    ),
                ]
            )
        )

    for pair_var in head_pairs:
        groups.append(
            wrap_local_instructions(
                [
                    BiLinearOperationInstruction(
                        tgt0=out_pair("xy"),
                        src0=pair_var("xy"),
                        src1=ham_local("yy"),
                        alpha=-NEIGHBOR_PAIR_SCALE,
                    ),
                    BiLinearOperationInstruction(
                        tgt0=out_pair("yx"),
                        src0=pair_var("yx"),
                        src1=ham_local("xx"),
                        alpha=-NEIGHBOR_PAIR_SCALE,
                    ),
                ]
            )
        )

    return groups, {
        "rho_left": rho_left,
        "rho_right": rho_right,
        "tail_pairs": tail_pairs,
        "head_pairs": head_pairs,
        "ham_local": ham_local,
        "out_pair": out_pair,
    }


def build_local_polarization_group(model):
    rho_pair = InstructionVariable.new("rho_pair", config=model["pair_domain"])
    ham_local = InstructionVariable.new(
        "ham_local_pol", config=model["ham_domain"]
    )
    out_left = InstructionVariable.new("out_left", config=model["site_domain"])
    out_right = InstructionVariable.new(
        "out_right", config=model["site_domain"]
    )

    return (
        InstructionGroup(
            [
                BiLinearOperationInstruction(
                    tgt0=out_left("z"),
                    src0=rho_pair("xy"),
                    src1=ham_local("xx"),
                    alpha=-PAIR_TO_POL_SCALE,
                ),
                BiLinearOperationInstruction(
                    tgt0=out_left("z"),
                    src0=rho_pair("yx"),
                    src1=ham_local("yy"),
                    alpha=+PAIR_TO_POL_SCALE,
                ),
                BiLinearOperationInstruction(
                    tgt0=out_right("z"),
                    src0=rho_pair("xy"),
                    src1=ham_local("xx"),
                    alpha=+PAIR_TO_POL_SCALE,
                ),
                BiLinearOperationInstruction(
                    tgt0=out_right("z"),
                    src0=rho_pair("yx"),
                    src1=ham_local("yy"),
                    alpha=-PAIR_TO_POL_SCALE,
                ),
            ]
        ),
        {
            "rho_pair": rho_pair,
            "ham_local": ham_local,
            "out_left": out_left,
            "out_right": out_right,
        },
    )


def build_current_maps(model, rho, ham, out, *, use_parametric_inner: bool):
    grouped_bonds = defaultdict(list)
    for bond in model["bonds"]:
        signature = (
            len(model["tail_neighbors"][bond]),
            len(model["head_neighbors"][bond]),
        )
        grouped_bonds[signature].append(bond)

    maps = []
    for (num_tail, num_head), bonds in grouped_bonds.items():
        local_groups, local_vars = build_local_current_group(
            model,
            num_tail,
            num_head,
            use_parametric_inner=use_parametric_inner,
        )
        environments = [
            InstructionEnvironment(
                {
                    local_vars["rho_left"]: rho(bond[0]),
                    local_vars["rho_right"]: rho(bond[1]),
                    **{
                        local_vars["tail_pairs"][num]: rho(
                            model["tail_neighbors"][bond][num]
                        )
                        for num in range(num_tail)
                    },
                    **{
                        local_vars["head_pairs"][num]: rho(
                            model["head_neighbors"][bond][num]
                        )
                        for num in range(num_head)
                    },
                    local_vars["ham_local"]: ham(bond),
                    local_vars["out_pair"]: out(bond),
                }
            )
            for bond in bonds
        ]
        maps.extend(
            MapApplyInstruction(content=local_group, environments=environments)
            for local_group in local_groups
        )

    return maps


def build_polarization_map(model, rho, ham, out):
    polarization_group, polarization_vars = build_local_polarization_group(
        model
    )
    polarization_map = MapApplyInstruction(
        content=polarization_group,
        environments=[
            InstructionEnvironment(
                {
                    polarization_vars["rho_pair"]: rho(bond),
                    polarization_vars["ham_local"]: ham(bond),
                    polarization_vars["out_left"]: out(bond[0]),
                    polarization_vars["out_right"]: out(bond[1]),
                }
            )
            for bond in model["bonds"]
        ],
    )
    return polarization_map


def preview_lines(path: str | Path, limit: int = 32) -> str:
    return "\n".join(Path(path).read_text().splitlines()[:limit])


def main() -> None:
    parser = argparse.ArgumentParser(description="Mapped 2D lattice demo.")
    parser.add_argument(
        "--backend",
        default="fortran",
        choices=("python", "numpy", "c", "fortran", "cuda"),
    )
    parser.add_argument("--resource", default="default")
    parser.add_argument("--rows", type=int, default=2)
    parser.add_argument("--cols", type=int, default=2)
    parser.add_argument("--parametric-inner", action="store_true")
    args = parser.parse_args()
    args.parametric_inner = True

    model = build_demo_model(args.rows, args.cols)
    rho, ham, out = create_variables(model)
    assignment_config = create_assignment_config(rho, ham, out)

    backend = get_backend(args.backend)
    library = backend.library(
        "demo_mapped_lattice",
        resource=backend.create_resource(args.resource),
    )
    current_maps = build_current_maps(
        model, rho, ham, out, use_parametric_inner=args.parametric_inner
    )
    current_routines = []
    flattened_leaf_count = 0
    for num, instruction in enumerate(current_maps, start=1):
        current_routines.append(
            backend.libroutine_from_instructions(
                library,
                f"apply_generator_current_case_{num}",
                instruction,
                assignment_config=assignment_config,
                resource_name=args.resource,
            )
        )
        flattened_leaf_count += len(list(instruction.flatten().instructions))

    polarization_map = build_polarization_map(model, rho, ham, out)
    polarization_routine = backend.libroutine_from_instructions(
        library,
        "apply_generator_polarization",
        polarization_map,
        assignment_config=assignment_config,
        resource_name=args.resource,
    )
    flattened_leaf_count += len(list(polarization_map.flatten().instructions))

    summary_routine = backend.libroutine_from_instructions(
        library,
        "apply_generator_mapapply",
        InstructionGroup(
            [
                *[CallInstruction(routine) for routine in current_routines],
                CallInstruction(polarization_routine),
            ]
        ),
        assignment_config=assignment_config,
        resource_name=args.resource,
    )
    library.build(compile=False)

    print("Demo 02c: mapped lattice rules")
    print("=" * 72)
    print("Backend                 :", backend.IDENTIFIER)
    print("Lattice                 :", f"{args.rows}x{args.cols}")
    print("Current case routines   :", len(current_routines))
    print("Flattened leaf count    :", flattened_leaf_count)
    print("Generated file          :", library.filename)
    print("Summary routine         :", summary_routine.name)
    print()
    print("Pair keys are now addressed directly by bond tuples.")
    print(
        "Neighbor cases are split by coordination class into separate routines."
    )
    print()
    print(
        preview_lines(
            library.relative_to_basepath(library.filename),
            90000,
        )
    )


if __name__ == "__main__":
    main()
