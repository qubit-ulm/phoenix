PHOENIX Tutorial Series
=======================

Recommended reading order
-------------------------

00a_in_a_nutshell_keymaps.py
  Very short introduction to keymaps, composed keys, and offset lookup.

00b_in_a_nutshell_instructions.py
  Adds symbolic instruction variables and one tiny instruction group.

00c_in_a_nutshell_first_library.py
  Uses the backend facade to build and call a first generated routine.

00d_in_a_nutshell_mapapply_library.py
  Extends the nutshell example with MapApplyInstruction across several local environments.

01_keymaps_and_variables.py
  Introduces the symbolic storage model.

02_instruction_tree.py
  Builds a small instruction group and shows compact vs detailed records.

03_plain_backend.py
  Generates symbolic plain-text output.

04_python_backend.py
  Generates and executes a pure Python backend.

05_numpy_backend.py
  Generates and executes a vectorized NumPy backend.

10_backend_api.py
  Introduces the current high-level backend selection API.

14_instruction_environments.py
  Introduces InstructionEnvironment directly and shows how local templates are
  rebound to outer variables.

15_mapapply_instruction.py
  Demonstrates MapApplyInstruction as “one local template, many environments”.

12_buffered_environment.py
  Demonstrates explicit user-managed BufferManager usage, staged buffer
  resolution, and the backend-specific reset lines that can now be used to zero
  reusable buffers inside generated code.

13_parametric_nested_keymaps.py
  Shows that ParametricInstructionGroup now also supports nested keymaps, so
  changing a plain group to a parametric one no longer requires flattening the
  symbolic storage layout first.

11_backend_mixed_resources.py
  Shows how several compatible backend instances can populate one library.

06_c_backend.py
  Builds and calls a compiled C backend.

07_fortran_backend.py
  Builds and calls a compiled Fortran/f2py backend.

08_multilibrary_makefile.py
  Demonstrates dependency handling across several libraries using one backend facade.

09_cuda_backend.py
  Shows CUDA host wrappers together with direct kernel launches from Python.

16_fortran_parallel_switch.py
  Creates one Fortran library with a scalar routine and a second routine whose
  resource preset is selected via a command-line switch.

17_cuda_adaa_selection.py
  Shows the CUDA ADAA selector for CuPy vs PyCUDA and demonstrates the PyCUDA
  default ADAA operations directly.

Current note on buffers
-----------------------

The current buffer formalism is intentionally explicit. Users create and place
buffer helpers themselves, and PHOENIX lowers those symbolic choices to the
selected backend. Buffer registration is not inferred globally from the
instruction tree.

Current recommendation
----------------------

The numbered filenames are now aligned with the current documentation. The
``00x`` series is the shortest path, while ``01`` onward is the fuller,
slower-paced tutorial set.
