"""
Demo 01a: explicit spin-chain generator with nearest-neighbor exchange.

This is the more direct executable track. The state and Hamiltonian layouts
are small and hand-written, and the script goes all the way to a generated
routine that can be called through a PHOENIX backend.
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


INTERACTION_STRENGTH = 1.0


def build_demo_model():
    """
    Build the hand-written spin-chain model and return all symbolic objects.

    Keeping the model assembly in one helper makes the later demo stages able
    to import and reuse the same symbolic setup instead of duplicating it.
    """

    # The labels are explicit strings here because the executable series aims
    # to stay readable first and generic second.
    sites = ("a", "b", "c", "d")
    pairs = ("ab", "bc", "cd")

    # this is the keymap local to a site. We only care for z polarization,
    # which means that the state operator has some contribution of
    # sigma_z in the spins subspace
    site_domain = KeyMap(name="site_domain")
    site_domain.entry("z")

    # to transfer via a flip flip mechanism, we require the xy and yx
    # correlation, so these are also added to the pair domain
    pair_domain = KeyMap(name="pair_domain")
    pair_domain.entry("xy")
    pair_domain.entry("yx")

    # the flip flop operator without the phase term for a pair is xx + yy
    # We could actually go with a common coefficient of the pair here, but this
    # is a little simpler
    ham_domain = KeyMap(name="ham_domain")
    ham_domain.entry("xx")
    ham_domain.entry("yy")

    # we generate a keymap that holds the whole state...
    state_keymap = KeyMap(name="state_1d_three_spins")
    # ... and the whole Hamiltonian
    ham_keymap = KeyMap(name="ham_1d_three_spins")

    # then we add the keymaps local to the individual spins and pairs under
    # a helpful key, we choose the name of the spin or pair. Now all spins,
    # a to d, have the site_domain attached, and the state_keymap can address any
    # entry by keymap.goto(spin_name, entry_name)
    state_keymap.link("a", site_domain)
    state_keymap.link("b", site_domain)
    state_keymap.link("c", site_domain)
    state_keymap.link("d", site_domain)

    # we simply add the pairs right after. The keymap is allowed to become
    # quite heterogenous, as long as they can share a common datatype
    state_keymap.link("ab", pair_domain)
    state_keymap.link("bc", pair_domain)
    state_keymap.link("cd", pair_domain)

    # finally, the Hamiltonian will have its xx and yy entries added for every pair
    ham_keymap.link("ab", ham_domain)
    ham_keymap.link("bc", ham_domain)
    ham_keymap.link("cd", ham_domain)

    return {
        "sites": sites,
        "pairs": pairs,
        "site_domain": site_domain,
        "pair_domain": pair_domain,
        "ham_domain": ham_domain,
        "state_keymap": state_keymap,
        "ham_keymap": ham_keymap,
    }


def create_variables(model):
    # ``rho`` is the current state, ``ham`` the static coupling data, and
    # ``out`` the generated right-hand side.
    rho = InstructionVariable.new("rho", config=model["state_keymap"])
    ham = InstructionVariable.new("ham", config=model["ham_keymap"])
    out = InstructionVariable.new("out", config=model["state_keymap"])
    return rho, ham, out


def create_assignment_config(rho, ham, out, family="real"):
    # The generated routine reads ``rho`` and ``ham`` and accumulates into
    # ``out``. The family selector keeps the demo switchable between real-only
    # and other assignment families if desired.
    return {
        rho: Config(status="R", family=family),
        ham: Config(status="R", family=family),
        out: Config(status="RW", family=family),
    }


def build_explicit_instructions(model, rho, ham, out):
    # This routine stays deliberately explicit: every local rule is written as
    # one small symbolic instruction group before it is embedded into the full
    # chain through environments.
    out_pair = InstructionVariable.new("out_pair", config=model["pair_domain"])
    out_site = InstructionVariable.new("out_site", config=model["site_domain"])
    ham_pair = InstructionVariable.new("ham_pair", config=model["ham_domain"])
    rho_pair = InstructionVariable.new("rho_pair", config=model["pair_domain"])
    rho_site = InstructionVariable.new("rho_site", config=model["site_domain"])

    # rho is on the left side of the two spin subspace we are looking at
    rho_is_L_instructions = InstructionGroup(
        [
            # [Z0, XX] -> YX
            BiLinearOperationInstruction(
                tgt0=out_pair("yx"),
                src0=rho_site("z"),
                src1=ham_pair("xx"),
                alpha=+INTERACTION_STRENGTH,
            ),
            # [Z0, YY] -> -XY
            BiLinearOperationInstruction(
                tgt0=out_pair("xy"),
                src0=rho_site("z"),
                src1=ham_pair("yy"),
                alpha=-INTERACTION_STRENGTH,
            ),
        ]
    )

    # rho is on the right side of the two spin subspace we are looking at
    rho_is_R_instructions = InstructionGroup(
        [
            # [0Z, XX] -> XY
            BiLinearOperationInstruction(
                tgt0=out_pair("xy"),
                src0=rho_site("z"),
                src1=ham_pair("xx"),
                alpha=+INTERACTION_STRENGTH,
            ),
            # [0Z, YY] -> -YX
            BiLinearOperationInstruction(
                tgt0=out_pair("yx"),
                src0=rho_site("z"),
                src1=ham_pair("yy"),
                alpha=-INTERACTION_STRENGTH,
            ),
        ]
    )

    # the ham and rho pair matches and the left subspace cancels to the identity
    # while the right subspace 'survives'
    rho_goes_R_instructions = InstructionGroup(
        [
            # [YX, YY] -> 0Z
            BiLinearOperationInstruction(
                tgt0=out_site("z"),
                src0=rho_pair("yx"),
                src1=ham_pair("yy"),
                alpha=+INTERACTION_STRENGTH,
            ),
            # [XY, XX] -> -0Z
            BiLinearOperationInstruction(
                tgt0=out_site("z"),
                src0=rho_pair("xy"),
                src1=ham_pair("xx"),
                alpha=-INTERACTION_STRENGTH,
            ),
        ]
    )

    # the ham and rho pair matches and the right subspace cancels to the identity
    # while the left subspace 'survives'
    rho_goes_L_instructions = InstructionGroup(
        [
            # [XY, YY] -> Z0
            BiLinearOperationInstruction(
                tgt0=out_site("z"),
                src0=rho_pair("xy"),
                src1=ham_pair("yy"),
                alpha=-INTERACTION_STRENGTH,
            ),
            # [YX, XX] -> -Z0
            BiLinearOperationInstruction(
                tgt0=out_site("z"),
                src0=rho_pair("yx"),
                src1=ham_pair("xx"),
                alpha=-INTERACTION_STRENGTH,
            ),
        ]
    )

    # we collect the offsetted instructions in the four groups we have just
    # established
    instructions = []

    # rho_is_L_instructions need environments where
    # we are in a spin pair subspace and rho lives in the same
    # subspace as the left spin
    for environment_dict in [
        {
            out_pair: out("ab"),
            rho_site: rho("a"),
            ham_pair: ham("ab"),
        },
        {
            out_pair: out("bc"),
            rho_site: rho("b"),
            ham_pair: ham("bc"),
        },
        {
            out_pair: out("cd"),
            rho_site: rho("c"),
            ham_pair: ham("cd"),
        },
    ]:
        instructions.append(
            EnvironmentInstruction(
                rho_is_L_instructions,
                environment=InstructionEnvironment(environment_dict),
            )
        )

    # rho_is_R_instructions
    # same as above, but rho's subspace matches the right pair index now and not the left
    for environment_dict in [
        {
            out_pair: out("ab"),
            rho_site: rho("b"),
            ham_pair: ham("ab"),
        },
        {
            out_pair: out("bc"),
            rho_site: rho("c"),
            ham_pair: ham("bc"),
        },
        {
            out_pair: out("cd"),
            rho_site: rho("d"),
            ham_pair: ham("cd"),
        },
    ]:
        instructions.append(
            EnvironmentInstruction(
                rho_is_R_instructions,
                environment=InstructionEnvironment(environment_dict),
            )
        )

    # rho_goes_L_instructions
    # here, rho is a pair and projects to a single out, left of pair
    for environment_dict in [
        {
            out_site: out("a"),
            rho_pair: rho("ab"),
            ham_pair: ham("ab"),
        },
        {
            out_site: out("b"),
            rho_pair: rho("bc"),
            ham_pair: ham("bc"),
        },
        {
            out_site: out("c"),
            rho_pair: rho("cd"),
            ham_pair: ham("cd"),
        },
    ]:
        instructions.append(
            EnvironmentInstruction(
                rho_goes_L_instructions,
                environment=InstructionEnvironment(environment_dict),
            )
        )

    # rho_goes_R_instructions
    # here, rho is a pair and projects to a single out, right of pair
    for environment_dict in [
        {
            out_site: out("b"),
            rho_pair: rho("ab"),
            ham_pair: ham("ab"),
        },
        {
            out_site: out("c"),
            rho_pair: rho("bc"),
            ham_pair: ham("bc"),
        },
        {
            out_site: out("d"),
            rho_pair: rho("cd"),
            ham_pair: ham("cd"),
        },
    ]:
        instructions.append(
            EnvironmentInstruction(
                rho_goes_R_instructions,
                environment=InstructionEnvironment(environment_dict),
            )
        )

    # all other combinations are truncated away.

    return InstructionGroup(instructions)


def preview_lines(path: str | Path, limit: int | None = None) -> str:
    if limit is None:
        return "\n".join(Path(path).read_text().splitlines())
    return "\n".join(Path(path).read_text().splitlines()[:limit])


def main() -> None:
    # get some command line arguments
    parser = argparse.ArgumentParser(
        description="Explicit 1D three-spin overlap cases."
    )
    parser.add_argument(
        "--backend",
        default="python",
        choices=("python", "numpy", "c", "fortran", "cuda"),
    )
    parser.add_argument("--resource", default="default")
    args = parser.parse_args()

    # we build the model, which we hide in a helper routine for now to keep
    # the workflow clear
    model = build_demo_model()

    # we create the variables that we can use in the generation of the instructions.
    # It is important to use consistent variables, they will try to find and associate
    # to each other, so variables that play the same role in two routines ideally are
    # the same actual object.
    rho, ham, out = create_variables(model)

    # use the variables to create all the instructions required for a timestep
    instructions = build_explicit_instructions(model, rho, ham, out)

    # I have introduced the get_backend function for convenience, so you can just
    # request a backend by name. The backend object you receive has quite universal
    # default choices selected
    backend = get_backend(args.backend)

    # this is a little technical. We basically create some information, what
    # kind of datatype we want for the variables, so far we have not specified
    # anything about that
    assignment_config = create_assignment_config(rho, ham, out)

    # the backend comes with predefined suggestions how these variable information
    # is mapped onto specific datatypes. We only asked a variable to be real or
    # complex, but the library needs something a little more language specific
    daa_assignments = backend.make_daa_assignments(assignment_config)

    # the library is also specific to a backend choice, as the language
    # you compile into has a lot of implication such as file name, compiler type,
    # linker, overall layout, dependencies, ...
    # The automatic backend comes directly with the right choice for the language of
    # choice
    library = backend.library(
        "demo_explicit_chain_cases",
        resource=backend.create_resource(args.resource),
    )

    # library wil be populated with the routine you create. In phoenix, a routine
    # must be bound to some library, that's why the request is made from the
    # view of the library
    routine = library.libroutine_from_instructions(
        "apply_generator_explicit",
        instructions,
        daa_assignments=daa_assignments,
        resource_name=args.resource,
    )
    library.build(compile=False, force=True)

    print("Demo 01: explicit chain with environments")
    print("=" * 72)
    print("Backend             :", backend.IDENTIFIER)
    print("Routine             :", routine.name)
    print("Instruction count   :", len(list(instructions.instructions)))
    print("Generated file      :", library.filename)
    print()
    print(preview_lines(library.relative_to_basepath(library.filename)))
    print(library.basepath)


if __name__ == "__main__":
    main()
