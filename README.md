# PHOENIX

![PHOENIX logo](design/logo.png)

Parallel Hybrid Operations for Enhanced Numerical Implementations and eXecutions

PHOENIX is a symbolic code-generation framework for structured numerical
operations. You describe an operation once using keymaps, symbolic instruction
variables, and instruction groups, then lower that description into callable
implementations for multiple execution backends.

The project is aimed at workflows where symbolic structure matters as much as
raw throughput: sparse or patterned operators, reusable routines, backend-aware
data ownership, and code generation that stays inspectable.

## What PHOENIX provides

- Symbolic storage layouts with `phoenix.keymap.KeyMap`
- An instruction IR in `phoenix.fgen.instruction`
- Backend builders for plain text, Python, NumPy, C, Fortran, OpenCL, CUDA,
  MATLAB, and Julia
- Backend-specific ADAA classes for runtime storage and conversion
- Wrapper layers that turn generated routines into Python-callable libraries

## Core workflow

The normal PHOENIX workflow is:

1. Define a symbolic data layout with a keymap.
2. Create symbolic instruction variables.
3. Build an instruction stream from leaf instructions and instruction groups.
4. Bind symbolic variables to ADAA classes and statuses.
5. Lower the instruction stream with a backend object.
6. Wrap and call the generated routine from Python.

Between steps 3 and 5, PHOENIX operates on an intermediate representation
(IR): the computation is still symbolic and backend-neutral, but already
structured enough to be lowered into code.

## Repository layout

- `phoenix/`: installable package
- `phoenix/fgen/`: code-generation pipeline, builders, wrappers, and backend
  implementations
- `tutorials/`: guided learning path, now starting with the `00x` "in a nutshell" series
- `demo/`: staged demo series and backend-oriented walkthroughs
- `tests/`: focused regression tests
- `doc/`: Sphinx documentation
- `design/`: logo assets including the wordmark and reduced square mark
- `scripts/`: guided install stages and repository maintenance helpers

## Installation

The easiest setup path is the guided installer:

```bash
make install
```

This runs the staged shell scripts in `scripts/`:

- `00_welcome.sh`
- `01_system_check.sh`
- `02_python_env.sh`
- `03_install_package.sh`
- `04_suggest_toolchains.sh`
- `05_configure_backends.sh`
- `06_build_support.sh`
- `07_smoke_tests.sh`
- `08_post_install_notes.sh`

The stages are also available individually through the root `Makefile`, for
example:

```bash
make install-check
make install-package
make install-configure
make install-test
```

If you prefer a manual installation, PHOENIX can still be installed directly
with `pip`.

Base dependency:

- `numpy`

Optional dependency groups:

- `.[docs]` for the Sphinx theme used by the documentation
- `.[test]` for the test runner
- `.[opencl]` for OpenCL wrapper support
- `.[cuda-cupy]` or `.[cuda-pycuda]` for the CUDA ADAA runtime family
- `.[dev]` for a small docs-and-tests development environment

`requirements.txt` intentionally describes only the minimal runtime baseline:

```bash
python -m pip install -r requirements.txt
```

Examples:

```bash
python -m pip install -e .
python -m pip install -e ".[docs,test]"
python -m pip install -e ".[cuda-cupy]"
```

After installation, inspect and configure the available backends with:

```bash
phoenix-config --status
phoenix-config-init
```

## Backend configuration

Backends that depend on external toolchains should be configured explicitly.
The configuration frontends store backend-local JSON files such as
`phoenix/fgen/backends/fortran/fortran_default.json`, write backend-local
support files under folders such as `phoenix/fgen/backends/c/support/`, and
build required support artifacts such as the C or CUDA helper library when the
local toolchain is available.

Common commands:

```bash
phoenix-config --status
phoenix-config fortran.resource.parallel_model
phoenix-config fortran.resource.parallel_model '"omp"'
phoenix-config fortran.executables.compiler gfortran
phoenix-config --dialogue fortran
phoenix-config --gui
phoenix-config-init
phoenix-config-init --gui
```

The configuration interface follows a dotted naming convention similar to
`gsettings`. Backend-specific parameters start with the backend name, so
`fortran.executables.compiler` or `fortran.resource.parallel_model` can be read
or written directly from the command line. Each backend configuration also
contains an `enabled` flag so a backend can be selected even if required
toolchains or Python libraries are missing.

`phoenix-config --status` reports whether backends are supported, detected,
enabled, or disabled. `phoenix-config --dialogue <backend>` opens the guided
per-backend dialogue, while `phoenix-config --gui` opens the scrollable table
editor. Initialization is intentionally separate and is exposed through
`phoenix-config-init` or through `phoenix-config --initialize-dialogue` /
`--initialize-gui`.

The same entrypoint can also run backend smoke tests:

```bash
phoenix-config --test python
phoenix-config --test all
```

`--test` runs a release-style smoke test for the selected backend. This is a
non-GUI path intended for backend verification after configuration changes. The test
always covers code generation for a basic instruction group and a mapapply
routine. Runtime execution is rolled for the stable installed backends where a
wrapper path is configured.

Support builds are intentionally separate from dialogue or initialization so
auto-detected settings can still be edited before invoking the toolchain:

```bash
phoenix-config --build c
phoenix-config --build cuda
phoenix-config --build all
phoenix-config --initialize-auto
```

`--build <backend|all>` generates and executes the backend support makefiles.
`--initialize-auto` is equivalent in spirit to initializing all backends with
their recommended enable flags and then running the support build step for all
backends.

For CUDA, support build and runtime selection are deliberately distinct:

- `runtime.adaa_library` selects the runtime ADAA family, currently `cupy` or
  `pycuda`
- `phoenix-config --build cuda` builds the CUDA backend support library with
  `nvcc` regardless of which ADAA family is currently selected
- the `ready` status still reflects whether the active runtime selection has the
  support artifacts it requires; today that mainly matters for `pycuda`

## Backends

The project contains builders and wrappers for several backend families:

- `phoenix.fgen.backends.plain.plain_builder`: symbolic plain-text output for inspection
- `phoenix.fgen.backends.python.python_builder`: pure Python code generation
- `phoenix.fgen.backends.numpy.numpy_builder`: NumPy-based generated code
- `phoenix.fgen.backends.c.c_builder`: C code with explicit pointer-style interfaces
- `phoenix.fgen.backends.fortran.fortran_builder`: Fortran code intended for `f2py` wrapping
- `phoenix.fgen.backends.opencl.opencl_builder`: OpenCL kernel generation and Python launch support
- `phoenix.fgen.backends.cuda.cuda_builder`: CUDA-oriented code generation and wrapper support
- `phoenix.fgen.backends.matlab.matlab_builder`: MATLAB code or MATLAB wrappers around compiled backends
- `phoenix.fgen.backends.julia.julia_builder`: Julia code or Julia wrappers around compiled backends

For compiled backends such as C, Fortran, and CUDA, run
`phoenix-config --dialogue <backend>` before building routines so compiler
paths, support artifacts, and backend-local makefiles are available.

For data ownership and conversion, the backend-local modules under
`phoenix.fgen.backends` provide the current ADAA implementations. The aggregate
modules `phoenix.adaas` and `phoenix.coeffbackends` provide consolidated
imports.

## Tutorials

Start with the scripts in `tutorials/` in this reading order:

1. `tutorials/00a_in_a_nutshell_keymaps.py`
2. `tutorials/00b_in_a_nutshell_instructions.py`
3. `tutorials/00c_in_a_nutshell_first_library.py`
4. `tutorials/00d_in_a_nutshell_mapapply_library.py`
5. `tutorials/01_keymaps_and_variables.py`
6. `tutorials/02_instruction_tree.py`
7. `tutorials/03_plain_backend.py`
8. `tutorials/04_python_backend.py`
9. `tutorials/05_numpy_backend.py`
10. `tutorials/10_backend_api.py`
11. `tutorials/14_instruction_environments.py`
12. `tutorials/15_mapapply_instruction.py`
13. `tutorials/12_buffered_environment.py`
14. `tutorials/13_parametric_nested_keymaps.py`
15. `tutorials/11_backend_mixed_resources.py`
16. `tutorials/06_c_backend.py`
17. `tutorials/07_fortran_backend.py`
18. `tutorials/08_multilibrary_makefile.py`
19. `tutorials/09_cuda_backend.py`
20. `tutorials/17_cuda_adaa_selection.py`
21. `tutorials/16_fortran_parallel_switch.py`

Before running compiled-backend tutorials, configure the corresponding backend
first:

```bash
phoenix-config --dialogue c
phoenix-config --dialogue fortran
phoenix-config --dialogue cuda
```

## Demos

The `demo/` directory contains staged demo series:

- `01x`: explicit executable spin-dynamics walkthrough
- `02x`: scalable symbolic-model construction path
- `03x`: backend generation comparison
- `04x`: buffers, OpenMP resources, and parallel benchmark
- `05x`: atomic-region lowering preview
- `06x`: configuration and backend smoke-testing walkthrough
- `07x`: ADAA family comparison
- `08x`: generated library packaging

## Running tests

The focused regression tests live in `tests/` and can be run with:

```bash
pytest tests
```

Current top-level tests cover ADAA selection and backend array operations.

## Release cleanup

Before preparing a release tree, move generated artifacts out of the tracked
working tree:

```bash
make release-dump-dry
make release-dump
```

This moves generated build folders, cache folders, compiled Python artifacts,
Sphinx output, demo output media, and similar non-release files aside while
leaving shipped assets such as `design/logo.png` and `doc/_static/*` in place.

For fun, you can also run:

```bash
make file-statistics
```

## Release-stage testing strategy

The release-stage suite is split into five layers:

1. Generic symbolic core: keymaps, instruction trees, instruction variables,
   environments, and library registration.
2. ADAA arithmetic: copy, zero, elementwise add/subtract, and scalar
   multiplication/division across backend-owned ADAA families.
3. Backend generation matrix: every backend lowers a basic instruction group
   and a mapapply routine for real, imag, and complex assignment families.
4. Backend runtime smoke: configured runtime backends execute a stable wrapped
   routine and compare the result against a NumPy reference.
5. Configuration smoke: dotted configuration access, backend initialization,
   status reporting, and `phoenix-config --test`.

## Building the documentation

The Sphinx sources live in `doc/`.

```bash
sphinx-build -b html doc doc/_build/html
```

The main documentation pages are:

- `doc/getting_started.rst`
- `doc/architecture.rst`
- `doc/backends.rst`
- `doc/tutorials.rst`
- `doc/examples.rst`

## How to cite

If you use PHOENIX in research work, please cite the software and refer to the
repository metadata in [CITATION.cff](CITATION.cff).

Plain-text reference:

```text
Matthias Kost. PHOENIX: Parallel Hybrid Operations for Enhanced Numerical
Implementations and eXecutions. Version 1.0. https://github.com/qubit-ulm/phoenix.
```

GitHub and other tooling can also read the machine-readable citation metadata
from `CITATION.cff` directly.

## Status

PHOENIX contains active code for the symbolic layer, backend builders, wrappers,
and tutorials, but the repository also includes older experimental material and
historical files. If you are new to the project, checkout the `tutorials/`, 
`tests/`, and `doc/` directories and keep the documentation nearby.

## License

See `LICENSE`.
