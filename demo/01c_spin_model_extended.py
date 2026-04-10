"""
Demo 01c: extended spin-chain model with contiguous order-3 correction terms.
"""

from __future__ import annotations

import argparse
import importlib.util
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter


# In this version we try to simulate the spin dynamics in a higher precision by
# taking higher orders and neighboring overlaps into account.
#
# Note that the pair operators in the time step that only partially overlap
# with a Hamiltonian term were discarded. To compensate for that, the demo uses
# a dense truncated Pauli-string basis:
#
# - no zeros are allowed between populated support sites
# - but strings are still truncated at a finite maximum order
#
# For simplicity we still use zero-padded full strings in the algebraic steps.
# That keeps the commutator logic explicit, even though it limits grouping.

# The overall application flow in this demo is:
#
# 1. build a truncated symbolic operator basis
# 2. derive the non-zero Liouvillian couplings inside that basis
# 3. turn those couplings into Phoenix instructions
# 4. let a selected backend generate executable code from those instructions
# 5. wrap the generated routine so it behaves like a Python function
# 6. run a small time integration and store frames
# 7. animate the local site populations
#
# This is intentionally written in a very explicit style so the individual
# application steps stay visible.


from phoenix.fgen.backends import Config
from phoenix.fgen.instruction import (
    CallInstruction,
    InstructionGroup,
    LinearOperationInstruction,
)
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import KeyMap


PAULI_TABLE = {
    "0": {"0": ("0", 0), "x": ("x", 0), "y": ("y", 0), "z": ("z", 0)},
    "x": {"0": ("x", 0), "x": ("0", 0), "y": ("z", 1), "z": ("y", 3)},
    "y": {"0": ("y", 0), "x": ("z", 3), "y": ("0", 0), "z": ("x", 1)},
    "z": {"0": ("z", 0), "x": ("y", 1), "y": ("x", 3), "z": ("0", 0)},
}

SUMMARY_ROUTINE_NAME = "apply_generator"


def load_demo01_module():
    """Load ``01a_spin_system.py`` so the executable series shares one base."""
    # The earlier executable demo already provides the backend-selection convenience
    # through ``get_backend(...)`` and also stores the common coupling
    # constant. Importing that file dynamically lets us reuse those pieces
    # without renaming the demo file or copying definitions.
    module_path = Path(__file__).with_name("01a_spin_system.py")
    spec = importlib.util.spec_from_file_location(
        "demo01a_spin_system", module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create import spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def all_pauli_words(order: int, prefix: str = ""):
    """Yield all non-identity Pauli words of one fixed support order."""
    # A support order of 3 means strings such as ``xyz`` or ``zyx`` that act
    # on three consecutive sites. The recursion only emits actual Pauli letters
    # and therefore excludes the all-identity word automatically.
    if order <= 0:
        yield prefix
        return
    yield from all_pauli_words(order - 1, prefix=f"{prefix}x")
    yield from all_pauli_words(order - 1, prefix=f"{prefix}y")
    yield from all_pauli_words(order - 1, prefix=f"{prefix}z")


def pad_pauli_word(word: str, start: int, num_spins: int) -> str:
    """Embed a local Pauli word into the full chain."""
    # Example for four spins:
    #   word="xy", start=1  ->  "0xy0"
    #
    # Using one full-length string per basis element keeps the commutator logic
    # simple because Hamiltonian terms and basis terms always have the same
    # string length when they are multiplied.
    padded = ["0"] * num_spins
    for offset, letter in enumerate(word):
        padded[start + offset] = letter
    return "".join(padded)


def simplify_pauli_string(padded: str) -> tuple[str, tuple[int, ...]]:
    """Return active letters and active positions of a full Pauli string."""
    # The basis uses zero-padded strings for convenience during algebra, but
    # for truncation decisions we only care about the non-identity support.
    # This helper strips the zeros away and records the active site positions.
    positions = []
    reduced = []
    for index, letter in enumerate(padded):
        if letter == "0":
            continue
        positions.append(index)
        reduced.append(letter)
    return "".join(reduced), tuple(positions)


def is_dense_support(positions: tuple[int, ...]) -> bool:
    """Return whether the active support forms one contiguous interval."""
    # ``(0, 1, 2)`` is accepted, ``(0, 2)`` is rejected. This is the actual
    # truncation rule of the demo: we keep contiguous clusters only.
    if len(positions) <= 1:
        return True
    return tuple(range(positions[0], positions[-1] + 1)) == positions


def pauli_label(start: int, letters: str) -> str:
    """Create a readable label for one dense local Pauli word."""
    # Phoenix keymaps work best with readable symbolic keys. The generated
    # strings are later used both as dictionary entries and as labels for the
    # backend variables, so it is useful to encode the support location here.
    parts = []
    for offset, letter in enumerate(letters):
        parts.append(f"s{start + offset:02d}_{letter}")
    return "corr_" + "__".join(parts)


def create_truncated_basis(
    num_spins: int, max_order: int
) -> dict[str, object]:
    """Create the contiguous Pauli basis up to the requested support order."""
    # ``basis_map`` is the object the backend eventually sees. It behaves like
    # the state keymaps in the earlier demos, but now every entry corresponds
    # to one dense Pauli string instead of just a site term or pair term.
    basis_map = KeyMap(name=f"extended_spin_chain_n{num_spins}_m{max_order}")
    basis_labels: list[str] = []
    basis_strings: list[str] = []
    basis_index: dict[str, int] = {}
    labels_by_order: dict[int, list[str]] = {
        order: [] for order in range(1, max_order + 1)
    }
    local_z_indices = [-1] * num_spins

    # Besides the keymap we also keep several parallel containers:
    #
    # - ``basis_labels``   : readable labels in flat-keymap order
    # - ``basis_strings``  : zero-padded Pauli strings in the same order
    # - ``basis_index``    : reverse lookup from full string to flat index
    # - ``labels_by_order``: split view of the same basis by support order
    # - ``local_z_indices``: offsets of the observables we want to plot later

    # First choose the support order, then slide that support window along the
    # chain, then enumerate all Pauli words that fit into that window.
    for order in range(1, max_order + 1):
        for start in range(num_spins - order + 1):
            for letters in all_pauli_words(order):
                label = pauli_label(start, letters)
                full_string = pad_pauli_word(letters, start, num_spins)

                # ``basis_map.entry(label)`` reserves one slot in the flat
                # generated coefficient vector. The other lists record how that
                # slot is interpreted.
                basis_map.entry(label)
                basis_index[full_string] = len(basis_strings)
                basis_labels.append(label)
                basis_strings.append(full_string)
                labels_by_order[order].append(label)

                # We need the one-site Z operators later because those are the
                # physical observables shown in the animation. Recording their
                # offsets now avoids expensive lookups during the simulation.
                if order == 1 and letters == "z":
                    local_z_indices[start] = len(basis_strings) - 1

    return {
        "basis_map": basis_map,
        "basis_labels": basis_labels,
        "basis_strings": basis_strings,
        "basis_index": basis_index,
        "labels_by_order": labels_by_order,
        "local_z_indices": local_z_indices,
    }


def potential_bond_starts(
    support_start: int,
    support_order: int,
    num_spins: int,
) -> range:
    """Return bond positions that can affect one contiguous support interval."""
    # Only bonds that touch the current support can contribute to the
    # commutator. For a contiguous cluster this means all internal bonds plus
    # the bond immediately to the left and right, if those exist.
    left = max(0, support_start - 1)
    right = min(num_spins - 2, support_start + support_order - 1)
    return range(left, right + 1)


def pauli_comm(string_a: str, string_b: str):
    """Return the commutator product string and factor."""
    # This is the algebraic core of the demo. It computes
    #
    #   [A, B] = A B - B A
    #
    # for two Pauli strings represented as character arrays. The table above
    # stores the local multiplication rule and the associated phase exponent.
    if len(string_a) != len(string_b):
        raise ValueError("Pauli strings must have the same length")
    result_ab = []
    result_ba = []
    phase_ab = 0
    phase_ba = 0
    for letter_a, letter_b in zip(string_a, string_b):
        letter_ab, phase_step_ab = PAULI_TABLE[letter_a][letter_b]
        letter_ba, phase_step_ba = PAULI_TABLE[letter_b][letter_a]
        result_ab.append(letter_ab)
        result_ba.append(letter_ba)
        phase_ab += phase_step_ab
        phase_ba += phase_step_ba
    result_ab = "".join(result_ab)
    result_ba = "".join(result_ba)
    if result_ab != result_ba:
        raise RuntimeError(
            "Pauli multiplication produced inconsistent strings"
        )
    factor = 1j**phase_ab - 1j**phase_ba
    if abs(factor) < 1.0e-14:
        # Zero commutators are skipped early because they do not generate any
        # Liouvillian entries and would only bloat the generated instruction set.
        return None, None
    return result_ab, factor


def build_generator_triplets(
    *,
    num_spins: int,
    max_order: int,
    coupling: float,
) -> dict[str, object]:
    """Build the truncated Liouvillian including dense order-3 corrections."""
    # Up to this point we only have a basis. This function derives the actual
    # generator matrix in sparse triplet form:
    #
    #   (row, col, alpha)
    #
    # meaning "basis entry ``col`` contributes ``alpha`` to the time derivative
    # of basis entry ``row``".
    basis = create_truncated_basis(num_spins, max_order)
    basis_strings = basis["basis_strings"]
    basis_index = basis["basis_index"]

    sparse_entries_by_order: dict[int, dict[tuple[int, int], float]] = {
        order: {} for order in range(1, max_order + 1)
    }

    # Loop over every basis operator as a possible input column of the
    # Liouvillian. We then commute it with every Hamiltonian bond term that can
    # actually overlap with its support.
    for col, basis_string in enumerate(basis_strings):
        reduced, positions = simplify_pauli_string(basis_string)
        if not reduced:
            continue
        support_start = positions[0]
        support_order = len(positions)

        for bond_start in potential_bond_starts(
            support_start,
            support_order,
            num_spins,
        ):
            # The nearest-neighbour flip-flop Hamiltonian consists of XX and YY
            # on each bond, so we treat both contributions explicitly.
            for local_letters in ("xx", "yy"):
                ham_string = pad_pauli_word(
                    local_letters, bond_start, num_spins
                )
                prod_string, factor = pauli_comm(ham_string, basis_string)
                if prod_string is None:
                    continue
                _, prod_positions = simplify_pauli_string(prod_string)
                prod_order = len(prod_positions)

                # This is the truncation stage. We only keep results that still
                # fit into the chosen support order and remain contiguous.
                if prod_order == 0 or prod_order > max_order:
                    continue
                if not is_dense_support(prod_positions):
                    continue
                row = basis_index.get(prod_string)
                if row is None:
                    continue

                # ``i [H, rho]`` turns the raw commutator phase into a real
                # coefficient for the generator of observable evolution.
                value = 1.0j * 0.5 * coupling * factor
                if abs(value.imag) > 1.0e-12:
                    raise RuntimeError("Expected real Liouvillian entries")
                key = (row, col)
                sparse_entries_by_order[prod_order][
                    key
                ] = sparse_entries_by_order[prod_order].get(key, 0.0) + float(
                    np.real(value)
                )

    # Finally convert the sparse dictionaries into sorted triplet lists grouped
    # by output order. That grouping will later be mirrored in one generated
    # worker routine per order.
    basis["triplets_by_order"] = {
        order: [
            (row, col, value)
            for (row, col), value in sorted(entries.items())
            if abs(value) > 1.0e-14
        ]
        for order, entries in sparse_entries_by_order.items()
    }
    return basis


def to_numpy_flat(adaa) -> np.ndarray:
    """Convert an ADAA instance into a flat NumPy vector."""
    # The wrapper returns backend-aware ADAA objects. For plotting and time
    # stepping in Python we convert them back to a plain 1D NumPy array.
    return np.asarray(adaa.to_numpy(), dtype=np.float64).reshape(-1)


def build_backend_problem(
    *,
    backend_name: str,
    resource_name: str,
    num_spins: int,
    max_order: int,
    coupling: float,
):
    """Generate the extended backend library and its wrapped summary routine."""
    # This function is the Phoenix-facing heart of the demo. Everything above
    # was pure model construction; now we hand that model to the code generator.
    demo01 = load_demo01_module()
    basis = build_generator_triplets(
        num_spins=num_spins,
        max_order=max_order,
        coupling=coupling,
    )
    basis_map = basis["basis_map"]
    basis_labels = basis["basis_labels"]
    triplets_by_order = basis["triplets_by_order"]

    # Demo 01a already exposes the common backend lookup helper. Reusing it keeps
    # the command-line interface consistent across the demos.
    backend = demo01.get_backend(backend_name)
    library = backend.library("demo_spin_model_extended")

    # ``coeff`` is the current state vector in the truncated Pauli basis.
    # ``rhs`` is the generated time derivative. Both use the same symbolic
    # layout because they live in the same basis.
    coeff = InstructionVariable.new("coeff", config=basis_map)
    rhs = InstructionVariable.new("rhs", config=basis_map)
    assignment_config = {
        coeff: Config(status="R", family="real", layout=basis_map),
        rhs: Config(status="RW", family="real", layout=basis_map),
    }

    # The backend translates the abstract family/status description into
    # concrete backend-specific array classes.
    daa_assignments = backend.make_daa_assignments(assignment_config)
    adaa_class = daa_assignments[coeff][0]

    # CUDA uses a host/device split for summary vs worker calls. Other backends
    # can run both levels on the same resource selection.
    if backend.IDENTIFIER == "cuda":
        worker_resource_name = "device"
        summary_resource_name = "host"
    else:
        worker_resource_name = resource_name
        summary_resource_name = resource_name

    order_routines = {}
    for order in range(1, max_order + 1):
        triplets = triplets_by_order[order]
        if not triplets:
            continue

        # Each sparse triplet becomes one symbolic linear instruction:
        #
        #   rhs[row] += alpha * coeff[col]
        #
        # This is the point where the derived generator matrix is converted into
        # Phoenix's symbolic instruction language.
        instructions = InstructionGroup(
            [
                LinearOperationInstruction(
                    tgt0=rhs(basis_labels[row]),
                    src0=coeff(basis_labels[col]),
                    alpha=alpha,
                )
                for row, col, alpha in triplets
            ]
        )

        # One worker routine per support order keeps the generated code more
        # manageable than putting the whole basis into a single giant routine.
        order_routines[order] = backend.libroutine_from_instructions(
            library,
            f"apply_order_{order}",
            instructions,
            daa_assignments=daa_assignments,
            resource_name=worker_resource_name,
        )

    # The summary routine is intentionally simple: it just calls all worker
    # routines consecutively. The backend wrapper exposes only this one routine
    # to the simulation code below.
    summary_tree = InstructionGroup(
        [
            CallInstruction(order_routines[order])
            for order in sorted(order_routines)
        ]
    )
    summary_routine = backend.libroutine_from_instructions(
        library,
        SUMMARY_ROUTINE_NAME,
        summary_tree,
        daa_assignments=daa_assignments,
        resource_name=summary_resource_name,
    )

    # ``backend.wrapped(...)`` performs the remaining application step:
    # generated code is built, loaded, and wrapped into a Python-callable
    # object that accepts ADAA inputs and returns ADAA outputs.
    wrapper = backend.wrapped(summary_routine.name, library, build=True)
    return {
        "basis": basis,
        "backend": backend,
        "library": library,
        "wrapper": wrapper,
        "adaa_class": adaa_class,
        "summary_routine": summary_routine,
        "order_routines": order_routines,
    }


def integrate_trajectory(
    *,
    wrapper,
    adaa_class,
    initial_state: np.ndarray,
    dt: float,
    num_steps: int,
    local_z_indices: list[int],
) -> tuple[np.ndarray, float]:
    """Integrate with a second-order forward Euler / Heun update."""
    # The generated backend routine computes the right-hand side only. Time
    # integration is still handled explicitly here in Python so that the demo
    # shows how generated kernels can be embedded into a larger application.
    current = adaa_class.from_numpy(
        np.asarray(initial_state, dtype=np.float64)
    )
    frames = [to_numpy_flat(current)[local_z_indices]]
    start = time.perf_counter()
    for _step in range(num_steps):
        # Heun's method evaluates the RHS twice:
        #
        # 1. at the current state
        # 2. at an Euler-predicted state
        #
        # and then averages both slopes. For this linear problem it matches the
        # second-order truncation of the exponential propagator.
        k1 = wrapper(coeff=current)
        predictor = current + dt * k1
        k2 = wrapper(coeff=predictor)
        current = current + 0.5 * dt * (k1 + k2)

        # Only the local Z entries are recorded because these are the directly
        # interpretable spin populations we want to visualize.
        frames.append(to_numpy_flat(current)[local_z_indices])
    runtime = time.perf_counter() - start
    return np.asarray(frames, dtype=np.float64), runtime


def animate_populations(
    *,
    frames: np.ndarray,
    dt: float,
    output_path: Path,
    title: str,
) -> None:
    """Create an animated line plot of the four local populations."""
    # The plotting code is intentionally kept separate from the integrator so
    # the data-generation and visualization steps remain independent.
    figure, axis = plt.subplots(figsize=(8.2, 4.8), constrained_layout=True)
    times = np.arange(frames.shape[0], dtype=np.float64) * dt
    labels = ("a", "b", "c", "d")
    colors = ("#d1495b", "#edae49", "#00798c", "#30638e")
    lines = []
    for idx, label in enumerate(labels):
        (line,) = axis.plot(
            [], [], lw=2.5, color=colors[idx], label=f"site {label}"
        )
        lines.append(line)

    ymin = float(np.min(frames))
    ymax = float(np.max(frames))
    pad = max(0.05, 0.1 * (ymax - ymin if ymax > ymin else 1.0))
    axis.set_xlim(times[0], times[-1])
    axis.set_ylim(ymin - pad, ymax + pad)
    axis.set_xlabel("time")
    axis.set_ylabel(r"local population $\langle \sigma_z \rangle$")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="upper right")
    title_text = axis.set_title(f"{title}\nstep 0 / {frames.shape[0] - 1}")

    def update(frame_idx: int):
        # ``FuncAnimation`` repeatedly calls this function with a frame number.
        # We update every line object in place to avoid rebuilding the plot.
        current_times = times[: frame_idx + 1]
        for line_idx, line in enumerate(lines):
            line.set_data(current_times, frames[: frame_idx + 1, line_idx])
        title_text.set_text(
            f"{title}\nstep {frame_idx} / {frames.shape[0] - 1}, "
            f"time {times[frame_idx]:.2f}"
        )
        return (*lines, title_text)

    animation = FuncAnimation(
        figure,
        update,
        frames=frames.shape[0],
        interval=80,
        blit=False,
    )
    animation.save(output_path, writer=PillowWriter(fps=12))
    plt.close(figure)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    # The script accepts the same backend names as the earlier demos so it can
    # serve as a drop-in comparison between simple and extended models.
    parser = argparse.ArgumentParser(
        description="Extended spin-chain model with order-3 correction terms."
    )
    parser.add_argument(
        "--backend",
        default="numpy",
        choices=("python", "numpy", "c", "fortran", "cuda"),
    )
    parser.add_argument("--resource", default="serial")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--dt", type=float, default=0.05)
    parser.add_argument("--max-order", type=int, default=3)
    parser.add_argument(
        "--output",
        default=str(Path(__file__).with_suffix(".gif")),
    )
    return parser.parse_args()


def main() -> None:
    """Build the extended model, run the trajectory, and save the animation."""
    args = parse_args()
    demo01 = load_demo01_module()
    num_spins = len(demo01.build_demo_model()["sites"])

    # This performs the full Phoenix code-generation pipeline and returns a
    # wrapped summary routine that we can call from Python.
    setup = build_backend_problem(
        backend_name=args.backend,
        resource_name=args.resource,
        num_spins=num_spins,
        max_order=args.max_order,
        coupling=demo01.INTERACTION_STRENGTH,
    )

    basis = setup["basis"]

    # The initial operator is a local ``sigma_z`` polarization on the first
    # site. In the truncated basis this corresponds to one single coefficient
    # being set to 1.
    initial_state = np.zeros(basis["basis_map"].size, dtype=np.float64)
    initial_state[basis["local_z_indices"][0]] = 1.0

    # Run the actual time evolution using the generated summary routine.
    frames, runtime = integrate_trajectory(
        wrapper=setup["wrapper"],
        adaa_class=setup["adaa_class"],
        initial_state=initial_state,
        dt=args.dt,
        num_steps=args.steps,
        local_z_indices=basis["local_z_indices"],
    )

    # After the trajectory is known, render the animation into a gif file.
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    animate_populations(
        frames=frames,
        dt=args.dt,
        output_path=output_path,
        title=f"Extended spin-chain populations ({setup['backend'].IDENTIFIER})",
    )

    print("Demo 01c: extended spin model with correction terms")
    print("=" * 72)
    print("Backend             :", setup["backend"].IDENTIFIER)
    print("Summary routine     :", setup["summary_routine"].name)
    print("Output order blocks :", sorted(setup["order_routines"]))
    print("Basis size          :", basis["basis_map"].size)
    print(
        "Generator nonzeros  :",
        sum(len(triplets) for triplets in basis["triplets_by_order"].values()),
    )
    print("Generated file      :", setup["library"].filename)
    print("Build folder        :", Path(setup["library"].basepath).resolve())
    print("Steps               :", args.steps)
    print("dt                  :", args.dt)
    print("Integrator          : second-order forward Euler (Heun)")
    print("Animation           :", output_path)
    print("Final populations   :", np.array2string(frames[-1], precision=6))
    print("Integration runtime :", f"{runtime:.6f} s")


if __name__ == "__main__":
    main()
