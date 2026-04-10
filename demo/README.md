# Demo Overview

The `demo/` folder contains several independent staged demo series. The first
two were already present and walk from a concrete spin example toward a more
scalable symbolic description. The later series focus on backend comparison,
parallel code generation, synchronization, configuration, ADAA families, and
packaging.

## Series `01x`: explicit executable spin dynamics

- [01a_spin_system.py](/home/matthias/Code/phoenix/demo/01a_spin_system.py)
  builds a small hand-written spin-chain generator and lowers it through a selected backend.
- [01b_spin_system_applied.py](/home/matthias/Code/phoenix/demo/01b_spin_system_applied.py)
  reuses that generator, integrates a short trajectory, and writes an animation.
- [01c_spin_model_extended.py](/home/matthias/Code/phoenix/demo/01c_spin_model_extended.py)
  extends the executable model with a denser truncated Pauli-string basis and higher-order correction terms.

This series is the more direct path. It is good when you want to show an audience a concrete workflow from symbolic model to generated routine to numerical output.

Related output files:

- [01b_spin_system_applied.gif](/home/matthias/Code/phoenix/demo/01b_spin_system_applied.gif)
- [01c_spin_model_extended.gif](/home/matthias/Code/phoenix/demo/01c_spin_model_extended.gif)

## Series `02x`: symbolic model scaling path

- [02a_spin_chain_keymaps.py](/home/matthias/Code/phoenix/demo/02a_spin_chain_keymaps.py)
  introduces the symbolic storage layout.
- [02b_explicit_chain_cases.py](/home/matthias/Code/phoenix/demo/02b_explicit_chain_cases.py)
  adds explicit local rules with `EnvironmentInstruction`.
- [02c_mapapply_lattice.py](/home/matthias/Code/phoenix/demo/02c_mapapply_lattice.py)
  moves to `MapApplyInstruction` and a lattice-style setup that scales more naturally.

This series is the better path if the goal is to explain how PHOENIX descriptions become more reusable and scalable as the symbolic structure is factored out.

## Series `03x`: backend matrix generation

- [03a_backend_matrix.py](/home/matthias/Code/phoenix/demo/03a_backend_matrix.py)
  lowers one small symbolic routine through several backends and prints the
  generated source snippets side by side.

This series is useful once the audience already understands the symbolic side
and now wants to see what PHOENIX changes, and what it does not change, across
target languages.

## Series `04x`: buffers and parallel resources

- [04a_buffers_and_parallelism.py](/home/matthias/Code/phoenix/demo/04a_buffers_and_parallelism.py)
  shows how `BufferManager` stages writes through explicit buffer slots and how
  the same buffered instruction tree can be emitted with serial and OpenMP
  resource presets.
- [04b_parallel_benchmark.py](/home/matthias/Code/phoenix/demo/04b_parallel_benchmark.py)
  compiles one scaled-up Fortran benchmark library and compares a serial
  routine against OpenMP variants fixed to 2, 4, and 8 threads.

This series is the right place when the discussion moves from symbolic
correctness toward write hazards, reductions, and parallel lowering choices.

## Series `05x`: atomic regions

- [05a_atomic_regions.py](/home/matthias/Code/phoenix/demo/05a_atomic_regions.py)
  compares `AtomicRegionInstruction` in leaf mode, region mode, and `policy="off"`
  and previews the emitted synchronization wrappers.

This series is meant as a compact synchronization walkthrough that complements
the buffer demo.

## Series `06x`: configuration and backend testing

- [06a_configuration_and_testing.py](/home/matthias/Code/phoenix/demo/06a_configuration_and_testing.py)
  demonstrates the user-facing configuration CLI, dotted-path access, status
  inspection, and the backend smoke-test entry point.

This series is useful for onboarding users who want to understand how the
generated backends are prepared and verified on a real machine.

## Series `07x`: ADAA families and host/device transfer

- [07a_adaa_families.py](/home/matthias/Code/phoenix/demo/07a_adaa_families.py)
  compares the available NumPy, C, OpenCL, CuPy, and PyCUDA ADAA classes and
  runs the same small operation set through each available wrapper family.

This series is aimed at explaining the storage side of PHOENIX rather than the
instruction lowering side.

## Series `08x`: library packaging

- [08a_library_packaging.py](/home/matthias/Code/phoenix/demo/08a_library_packaging.py)
  builds a tiny multi-library layout, collects the generated artifacts, and
  writes one shared makefile.

This series is the deployment-oriented end of the demo track: once a symbolic
routine exists, how is it written out and organized on disk?

## Running the demos

The demos now assume PHOENIX is importable from the active environment, for example after:

```bash
python -m pip install -e .
```

Then run a demo directly, for example:

```bash
python demo/01a_spin_system.py --backend python
python demo/01b_spin_system_applied.py --backend numpy
python demo/02c_mapapply_lattice.py --backend plain
python demo/03a_backend_matrix.py
python demo/04b_parallel_benchmark.py --num-blocks 512 --block-size 64
python demo/06a_configuration_and_testing.py --backend python
```

Compiled-backend demos may also require backend configuration through `phoenix-config --dialogue <backend>`.
