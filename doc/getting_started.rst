Getting Started
===============

Name: ``PHOENIX``

Acronym: Parallel Hybrid Operations for Enhanced Numerical Implementations and
eXecutions

PHOENIX is most useful when you want to describe a numerical operation once and
reuse that description across several execution backends. The normal workflow
looks like this:

1. Define a data layout with a :class:`phoenix.keymap.KeyMap`.
2. Create symbolic instruction-variable classes with
   :class:`phoenix.fgen.instructionvar.InstructionVariable`.
3. Build an instruction stream from leaf instructions such as
   :class:`phoenix.fgen.instruction.LinearOperationInstruction` or
   :class:`phoenix.fgen.instruction.BiLinearOperationInstruction`.
4. Select a backend with :func:`phoenix.fgen.backends.get_backend`.
5. Bind symbolic variables through backend-owned assignment configs or ADAA
   assignments.
6. Lower the instruction stream into a backend-owned library.
7. Wrap the generated routine through the backend so it can be called from
   Python.

Between steps 3 and 5, PHOENIX is mostly operating on an IR, an intermediate
representation. In practice that means the instruction objects still describe
the computation structurally and symbolically, before any backend-specific
syntax or calling convention has been chosen.

Before you use a compiled backend such as C, Fortran, or CUDA, initialize and
configure the relevant backend once:

.. code-block:: bash

   phoenix-config-init
   phoenix-config --dialogue c
   phoenix-config --dialogue fortran

The configuration layer writes backend JSON files, generates backend-local
support files under folders such as ``phoenix/fgen/backends/c/support/``, and
builds required support artifacts such as the C helper library when the local
toolchain is available.

Minimal Example
---------------

The script below demonstrates the symbolic layer without generating code yet.
It is the first part of the ``00x`` "in a nutshell" series and is the shortest
path to understanding keys, keymaps, and symbolic offsets.

.. literalinclude:: ../tutorials/00a_in_a_nutshell_keymaps.py
   :language: python
   :caption: ``tutorials/00a_in_a_nutshell_keymaps.py``


First End-to-End Workflow
-------------------------

For a compact runnable backend example, start with the pure-Python backend
facade. It does not require an external compiler and mirrors the same workflow
used by the compiled backends. The nutshell library tutorial below is the new
smallest complete example of the backend facade.

.. literalinclude:: ../tutorials/00c_in_a_nutshell_first_library.py
   :language: python
   :caption: ``tutorials/00c_in_a_nutshell_first_library.py``


When To Use Which Backend
-------------------------

``get_backend("python")``
   Best for debugging, inspection, and tutorials.

``get_backend("numpy")``
   Good when vectorized Python code is sufficient and NumPy is acceptable as a
   runtime dependency.

``get_backend("fortran")``
   Good fit when you want generated Fortran and straightforward ``f2py``
   wrapping. Configure it first with ``phoenix-config --dialogue fortran``.

``get_backend("c")``
   Good when you want an explicit C ABI, shared-library compilation, and
   backend-owned C-style storage. Configure it first with
   ``phoenix-config --dialogue c``.

``get_backend("opencl")``
   Good when you want generated OpenCL kernels launched directly from Python
   through ``pyopencl`` while keeping the coefficient data on the device.

``get_backend("cuda")``
   Intended for routines that should lower parts of the workload into CUDA
   kernels while keeping host-callable entry points in Python. Configure it
   first with ``phoenix-config --dialogue cuda``.
