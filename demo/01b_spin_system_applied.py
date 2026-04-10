"""
Demo 01b: apply the spin-system generator from demo 01a to a short trajectory.
"""

from __future__ import annotations

import argparse
import importlib.util
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter


def load_demo01_module():
    """Load ``01a_spin_system.py`` for reuse in this second stage."""
    module_path = Path(__file__).with_name("01a_spin_system.py")
    spec = importlib.util.spec_from_file_location(
        "demo01a_spin_system", module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create import spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_backend_problem(*, backend_name: str, resource_name: str):
    """Reuse the model and routine setup from demo 01a."""
    demo01 = load_demo01_module()
    model = demo01.build_demo_model()
    rho, ham, out = demo01.create_variables(model)
    instructions = demo01.build_explicit_instructions(model, rho, ham, out)

    backend = demo01.get_backend(backend_name)
    assignment_config = demo01.create_assignment_config(rho, ham, out)
    daa_assignments = backend.make_daa_assignments(assignment_config)
    state_adaa_class = daa_assignments[rho][0]
    ham_adaa_class = daa_assignments[ham][0]

    library = backend.library(
        "demo_spin_system_applied",
        resource=backend.create_resource(resource_name),
    )
    routine = library.libroutine_from_instructions(
        "apply_generator_explicit",
        instructions,
        daa_assignments=daa_assignments,
        resource_name=resource_name,
    )
    wrapper = backend.wrapped(routine.name, library, build=True)
    return {
        "demo01": demo01,
        "model": model,
        "backend": backend,
        "routine": routine,
        "wrapper": wrapper,
        "state_adaa_class": state_adaa_class,
        "ham_adaa_class": ham_adaa_class,
        "rho_var": rho,
        "ham_var": ham,
        "out_var": out,
        "library": library,
    }


def to_numpy_flat(adaa) -> np.ndarray:
    """Convert one ADAA state into a flat NumPy array."""
    return np.asarray(adaa.to_numpy(), dtype=np.float64).reshape(-1)


def build_initial_state(model) -> np.ndarray:
    """Prepare a localized initial polarization on the first site."""
    initial_state = np.zeros(model["state_keymap"].size, dtype=np.float64)
    initial_state[model["state_keymap"].goto("a", "z")[0]] = 1.0
    return initial_state


def build_hamiltonian(model, coupling: float) -> np.ndarray:
    """Populate the nearest-neighbour XX and YY couplings."""
    hamiltonian = np.zeros(model["ham_keymap"].size, dtype=np.float64)
    for pair in model["pairs"]:
        for component in ("xx", "yy"):
            hamiltonian[
                model["ham_keymap"].goto(pair, component)[0]
            ] = coupling
    return hamiltonian


def local_z_indices(model) -> list[int]:
    """Return the flattened state offsets for the four site populations."""
    return [
        model["state_keymap"].goto(site, "z")[0] for site in model["sites"]
    ]


def integrate_trajectory(
    *,
    wrapper,
    state_adaa_class,
    ham_adaa,
    initial_state: np.ndarray,
    dt: float,
    num_steps: int,
    observed_indices: list[int],
) -> tuple[np.ndarray, float]:
    """Integrate the generated dynamics with an explicit Euler stepper."""
    current = state_adaa_class.from_numpy(initial_state)
    frames = [to_numpy_flat(current)[observed_indices]]
    start = time.perf_counter()
    for _step in range(num_steps):
        # The wrapper evaluates the generated right-hand side for the current
        # state, then the demo advances the state with a simple explicit Euler
        # step. The integrator is intentionally basic so the generated routine
        # remains the main point of interest.
        rhs = wrapper(rho=current, ham=ham_adaa)
        current = current + dt * rhs
        frames.append(to_numpy_flat(current)[observed_indices])
    runtime = time.perf_counter() - start
    return np.asarray(frames, dtype=np.float64), runtime


def animate_populations(
    *,
    frames: np.ndarray,
    dt: float,
    sites: tuple[str, ...],
    output_path: Path,
    title: str,
) -> None:
    """Create an animated line plot of the four site populations."""
    figure, axis = plt.subplots(figsize=(8.2, 4.8), constrained_layout=True)
    times = np.arange(frames.shape[0], dtype=np.float64) * dt
    colors = ("#d1495b", "#edae49", "#00798c", "#30638e")
    lines = []
    for idx, site in enumerate(sites):
        (line,) = axis.plot(
            [], [], lw=2.5, color=colors[idx], label=f"site {site}"
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
        current_times = times[: frame_idx + 1]
        for line_idx, line in enumerate(lines):
            line.set_data(current_times, frames[: frame_idx + 1, line_idx])
        title_text.set_text(
            f"{title}\nstep {frame_idx} / {frames.shape[0] - 1}, "
            f"time {times[frame_idx]:.2f}"
        )
        return (*lines, title_text)

    # ``FuncAnimation`` repeatedly redraws the four local site populations.
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
    """Parse the demo command line."""
    parser = argparse.ArgumentParser(
        description="Apply the generated spin-system routine to a short simulation."
    )
    parser.add_argument(
        "--backend",
        default="numpy",
        choices=("python", "numpy", "c", "fortran", "cuda"),
    )
    parser.add_argument("--resource", default="default")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--dt", type=float, default=0.05)
    parser.add_argument(
        "--output",
        default=str(Path(__file__).with_suffix(".gif")),
    )
    return parser.parse_args()


def main() -> None:
    """Build the generated routine, run a short trajectory, and animate it."""
    args = parse_args()
    setup = build_backend_problem(
        backend_name=args.backend,
        resource_name=args.resource,
    )
    model = setup["model"]
    initial_state = build_initial_state(model)
    hamiltonian = build_hamiltonian(
        model,
        coupling=setup["demo01"].INTERACTION_STRENGTH,
    )
    ham_adaa = setup["ham_adaa_class"].from_numpy(hamiltonian)
    observed = local_z_indices(model)

    frames, runtime = integrate_trajectory(
        wrapper=setup["wrapper"],
        state_adaa_class=setup["state_adaa_class"],
        ham_adaa=ham_adaa,
        initial_state=initial_state,
        dt=args.dt,
        num_steps=args.steps,
        observed_indices=observed,
    )

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    animate_populations(
        frames=frames,
        dt=args.dt,
        sites=model["sites"],
        output_path=output_path,
        title=f"Spin-system populations ({setup['backend'].IDENTIFIER})",
    )

    print("Demo 01b: applied spin-system trajectory")
    print("=" * 72)
    print("Backend             :", setup["backend"].IDENTIFIER)
    print("Routine             :", setup["routine"].name)
    print("Generated file      :", setup["library"].filename)
    print("Build folder        :", Path(setup["library"].basepath).resolve())
    print("Steps               :", args.steps)
    print("dt                  :", args.dt)
    print("Integration runtime :", f"{runtime:.6f} s")
    print("Animation           :", output_path)
    print("Final populations   :", np.array2string(frames[-1], precision=6))


if __name__ == "__main__":
    main()
