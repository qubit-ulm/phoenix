"""
Demo 02b: explicit local cases for the 1D three-spin chain.

This file extends demo 02a by adding the first instruction tree.  Nothing is
mapped yet.  Instead, we spell out the local cases directly and use
``EnvironmentInstruction`` to bind each local rule to one concrete bond.

For this tiny chain the interesting local cases are:

1. left polarization on the bond,
2. right polarization on the bond,
3. pair term on the same bond,
4. pair term on the left neighboring bond,
5. pair term on the right neighboring bond.

Because the chain has only two bonds, every concrete bond sees only the cases
that really exist.  There is no padded dummy neighbor.
"""

from __future__ import annotations

import argparse

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import (
    BiLinearOperationInstruction,
    EnvironmentInstruction,
    InstructionGroup,
)
from phoenix.fgen.instructionvar import (
    InstructionEnvironment,
    InstructionVariable,
)
from phoenix.keymap import KeyMap


POL_TO_PAIR_SCALE = 1.0
PAIR_TO_POL_SCALE = 1.0
NEIGHBOR_PAIR_SCALE = 0.35


def build_demo_model():
    # This symbolic model is still the same tiny three-site chain from 01a.
    sites = (0, 1, 2)
    bonds = ((0, 1), (1, 2))

    site_domain = KeyMap(name="site_domain")
    site_domain.entry("z")

    pair_domain = KeyMap(name="pair_domain")
    pair_domain.entry("xy")
    pair_domain.entry("yx")

    ham_domain = KeyMap(name="ham_domain")
    ham_domain.entry("xx")
    ham_domain.entry("yy")

    state_keymap = KeyMap(name="state_1d_three_spins")
    ham_keymap = KeyMap(name="ham_1d_three_spins")

    for site in sites:
        state_keymap.link(site, site_domain)
    for bond in bonds:
        state_keymap.link(bond, pair_domain)
        ham_keymap.link(bond, ham_domain)

    # These lookup tables encode which neighboring pair exists to the left or
    # right of one bond. The edge bonds simply have no neighbor on one side.
    left_neighbor = {
        bonds[0]: None,
        bonds[1]: bonds[0],
    }
    right_neighbor = {
        bonds[0]: bonds[1],
        bonds[1]: None,
    }

    return {
        "sites": sites,
        "bonds": bonds,
        "site_domain": site_domain,
        "pair_domain": pair_domain,
        "ham_domain": ham_domain,
        "state_keymap": state_keymap,
        "ham_keymap": ham_keymap,
        "left_neighbor": left_neighbor,
        "right_neighbor": right_neighbor,
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


def build_explicit_instructions(model, rho, ham, out):
    # We now introduce local symbolic variables that represent the pieces of
    # the state and Hamiltonian seen from one concrete bond environment.
    rho_left = InstructionVariable.new("rho_left", config=model["site_domain"])
    rho_right = InstructionVariable.new(
        "rho_right", config=model["site_domain"]
    )
    rho_same = InstructionVariable.new("rho_same", config=model["pair_domain"])
    rho_left_pair = InstructionVariable.new(
        "rho_left_pair", config=model["pair_domain"]
    )
    rho_right_pair = InstructionVariable.new(
        "rho_right_pair", config=model["pair_domain"]
    )
    ham_local = InstructionVariable.new(
        "ham_local", config=model["ham_domain"]
    )
    out_pair = InstructionVariable.new("out_pair", config=model["pair_domain"])
    out_left = InstructionVariable.new("out_left", config=model["site_domain"])
    out_right = InstructionVariable.new(
        "out_right", config=model["site_domain"]
    )

    left_polarization_case = InstructionGroup(
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
    )

    right_polarization_case = InstructionGroup(
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
    )

    same_pair_case = InstructionGroup(
        [
            BiLinearOperationInstruction(
                tgt0=out_left("z"),
                src0=rho_same("xy"),
                src1=ham_local("xx"),
                alpha=-PAIR_TO_POL_SCALE,
            ),
            BiLinearOperationInstruction(
                tgt0=out_left("z"),
                src0=rho_same("yx"),
                src1=ham_local("yy"),
                alpha=+PAIR_TO_POL_SCALE,
            ),
            BiLinearOperationInstruction(
                tgt0=out_right("z"),
                src0=rho_same("xy"),
                src1=ham_local("xx"),
                alpha=+PAIR_TO_POL_SCALE,
            ),
            BiLinearOperationInstruction(
                tgt0=out_right("z"),
                src0=rho_same("yx"),
                src1=ham_local("yy"),
                alpha=-PAIR_TO_POL_SCALE,
            ),
        ]
    )

    left_pair_case = InstructionGroup(
        [
            BiLinearOperationInstruction(
                tgt0=out_pair("xy"),
                src0=rho_left_pair("xy"),
                src1=ham_local("xx"),
                alpha=+NEIGHBOR_PAIR_SCALE,
            ),
            BiLinearOperationInstruction(
                tgt0=out_pair("yx"),
                src0=rho_left_pair("yx"),
                src1=ham_local("yy"),
                alpha=+NEIGHBOR_PAIR_SCALE,
            ),
        ]
    )

    right_pair_case = InstructionGroup(
        [
            BiLinearOperationInstruction(
                tgt0=out_pair("xy"),
                src0=rho_right_pair("xy"),
                src1=ham_local("yy"),
                alpha=-NEIGHBOR_PAIR_SCALE,
            ),
            BiLinearOperationInstruction(
                tgt0=out_pair("yx"),
                src0=rho_right_pair("yx"),
                src1=ham_local("xx"),
                alpha=-NEIGHBOR_PAIR_SCALE,
            ),
        ]
    )

    instructions = []
    for bond in model["bonds"]:
        left_site, right_site = bond
        common_environment = {
            rho_left: rho(left_site),
            rho_right: rho(right_site),
            rho_same: rho(bond),
            ham_local: ham(bond),
            out_pair: out(bond),
            out_left: out(left_site),
            out_right: out(right_site),
        }
        instructions.append(
            EnvironmentInstruction(
                left_polarization_case,
                environment=InstructionEnvironment(common_environment),
            )
        )
        instructions.append(
            EnvironmentInstruction(
                right_polarization_case,
                environment=InstructionEnvironment(common_environment),
            )
        )
        instructions.append(
            EnvironmentInstruction(
                same_pair_case,
                environment=InstructionEnvironment(common_environment),
            )
        )

        if model["left_neighbor"][bond] is not None:
            instructions.append(
                EnvironmentInstruction(
                    left_pair_case,
                    environment=InstructionEnvironment(
                        {
                            rho_left_pair: rho(model["left_neighbor"][bond]),
                            ham_local: ham(bond),
                            out_pair: out(bond),
                        }
                    ),
                )
            )
        if model["right_neighbor"][bond] is not None:
            instructions.append(
                EnvironmentInstruction(
                    right_pair_case,
                    environment=InstructionEnvironment(
                        {
                            rho_right_pair: rho(model["right_neighbor"][bond]),
                            ham_local: ham(bond),
                            out_pair: out(bond),
                        }
                    ),
                )
            )

    return InstructionGroup(instructions)


def preview_lines(path: str | Path, limit: int = 32) -> str:
    return "\n".join(Path(path).read_text().splitlines()[:limit])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Explicit 1D three-spin overlap cases."
    )
    parser.add_argument(
        "--backend",
        default="fortran",
        choices=("python", "numpy", "c", "fortran", "cuda"),
    )
    parser.add_argument("--resource", default="default")
    args = parser.parse_args()

    model = build_demo_model()
    rho, ham, out = create_variables(model)
    instructions = build_explicit_instructions(model, rho, ham, out)
    assignment_config = create_assignment_config(rho, ham, out)

    backend = get_backend(args.backend)
    library = backend.library(
        "demo_explicit_chain_cases",
        resource=backend.create_resource(args.resource),
    )
    routine = backend.libroutine_from_instructions(
        library,
        "apply_generator_explicit",
        instructions,
        assignment_config=assignment_config,
        resource_name=args.resource,
    )
    library.build(compile=False)

    print("Demo 02b: explicit chain cases with environments")
    print("=" * 72)
    print("Backend             :", backend.IDENTIFIER)
    print("Routine             :", routine.name)
    print("Instruction count   :", len(list(instructions.instructions)))
    print("Generated file      :", library.filename)
    print()
    print("The local cases are hard-coded with EnvironmentInstruction.")
    print("MapApplyInstruction has not been introduced yet.")
    print()
    print(preview_lines(library.relative_to_basepath(library.filename)))


if __name__ == "__main__":
    main()
