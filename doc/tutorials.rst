Tutorials
=========

The ``tutorials/`` directory contains a moderated learning path through the
main Phoenix concepts. The filenames keep a stable numbered series, but for a
first read the grouped order below is more helpful than following the numbers
strictly once the backend facade is introduced.

Learning Path
-------------

``tutorials/00a_in_a_nutshell_keymaps.py``
   Very short first contact with keymaps, composed keys, and offset lookup.

``tutorials/00b_in_a_nutshell_instructions.py``
   Builds a tiny symbolic instruction group on top of that keymap.

``tutorials/00c_in_a_nutshell_first_library.py``
   Uses ``get_backend("python")`` and the backend facade to register and call
   a first generated routine without introducing compiled toolchains yet.

``tutorials/00d_in_a_nutshell_mapapply_library.py``
   Extends the nutshell routine with ``MapApplyInstruction`` so the reader sees
   the "one local kernel, many environments" idea immediately.

``tutorials/01_keymaps_and_variables.py``
   Introduces symbolic storage layouts with keymaps and instruction variables.

``tutorials/02_instruction_tree.py``
   Builds a small instruction tree and shows compact versus detailed record
   payloads.

``tutorials/03_plain_backend.py``
   Generates plain-text symbolic output for inspection.

``tutorials/04_python_backend.py``
   Uses ``get_backend("python")`` and the backend facade to build and run a
   pure Python routine.

``tutorials/05_numpy_backend.py``
   Uses ``get_backend("numpy")`` and the backend facade to build and run a
   vectorized NumPy routine.

``tutorials/10_backend_api.py``
   Introduces the current backend-selection formalism centered on
   ``get_backend(...)``, backend-owned libraries, assignment configs, and
   backend-managed wrappers.

``tutorials/14_instruction_environments.py``
   Introduces ``InstructionEnvironment`` directly and shows how a local
   instruction template is rebound to outer variables.

``tutorials/15_mapapply_instruction.py``
   Demonstrates ``MapApplyInstruction`` as the structured “apply this local
   content in many environments” building block.

``tutorials/12_buffered_environment.py``
   Demonstrates explicit user-managed buffers. Buffer registration and
   placement stay under user control; PHOENIX does not auto-bufferize the
   instruction tree. ``BufferManager`` and related helper instructions are
   used explicitly where the user wants scratch storage.

``tutorials/13_parametric_nested_keymaps.py``
   Shows that ``ParametricInstructionGroup`` can preserve nested symbolic
   layouts instead of forcing a flattened keymap first.

``tutorials/11_backend_mixed_resources.py``
   Shows how several compatible backend instances can register routines into
   one shared library.

``tutorials/06_c_backend.py``
   Uses ``get_backend("c")`` to build and execute a compiled C backend.

``tutorials/07_fortran_backend.py``
   Uses ``get_backend("fortran")`` to build and execute a Fortran backend.

``tutorials/08_multilibrary_makefile.py``
   Demonstrates dependency tracking and shared makefile generation across
   several libraries created through one backend facade.

``tutorials/09_cuda_backend.py``
   Demonstrates CUDA backend selection together with direct kernel calls from
   Python through the CUDA wrapper layer.

``tutorials/16_fortran_parallel_switch.py``
   Builds one Fortran library containing a scalar routine and a second routine
   whose resource preset is selected via a command-line switch.

``tutorials/17_cuda_adaa_selection.py``
   Shows that ``get_backend("cuda")`` stays the public CUDA entry point while
   ``runtime.adaa_library`` selects either the CuPy or PyCUDA ADAA family.
   The tutorial also demonstrates PyCUDA default ADAA operations directly.

Notes
-----

The later tutorials require native toolchains:

- C needs a working C compiler.
- Fortran needs a working Fortran compiler together with ``f2py`` from the
  active Python environment.
- CUDA needs ``nvcc`` together with CuPy for direct kernel launches.

Before running those compiled-backend tutorials, configure the backend once:

.. code-block:: bash

   phoenix-config --dialogue c
   phoenix-config --dialogue fortran
   phoenix-config --dialogue cuda

The first five tutorials together with ``10``, ``14``, and ``15`` are
generation-only or pure-Python and should work in any normal Python
environment. The new ``00x`` nutshell series is the shortest route through the
same material if you want a quick first pass before the longer annotated
tutorials.

Buffer note
-----------

The current buffer formalism deliberately leaves more responsibility with the
user. ``BufferManager`` is an explicit helper: users decide where buffers are
registered, how many independent slots are needed, and where reduction/copy
instructions are inserted. Newer grouped-buffer workflows likewise start from
explicit user placement of the corresponding buffer instructions instead of
automatic tree traversal.
