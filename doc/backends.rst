Backends
========

The current public entry point is :func:`phoenix.fgen.backends.get_backend`.
Users normally select a backend object first and then let that object provide:

- a compatible language-specific library,
- the default build chain for that backend,
- ADAA classes and assignment expansion,
- wrappers for built routines.

Backend families in PHOENIX differ in two places:

1. The generated routine representation.
2. The ADAA and wrapper implementation used to call that representation.

For data ownership and conversion, newer code should prefer backend objects
plus backend-owned ADAA generation through
``backend.make_daa_assignments(...)``.
The backend-local modules such as
:mod:`phoenix.fgen.backends.python.python_backend`,
:mod:`phoenix.fgen.backends.numpy.numpy_backend`,
:mod:`phoenix.fgen.backends.fortran.fortran_backend`, and
:mod:`phoenix.fgen.backends.c.c_backend` remain available as implementation
layers. The aggregate modules :mod:`phoenix.adaas` and
:mod:`phoenix.coeffbackends` are compatibility imports on top of those layers.


Generated-code backends
-----------------------

``phoenix.fgen.backends.python.python_builder``
   Emits pure Python code using only lists, loops, and scalar operations.

``phoenix.fgen.backends.numpy.numpy_builder``
   Emits Python code that imports NumPy and uses NumPy arrays for data and
   local storage.

``phoenix.fgen.backends.matlab.matlab_builder``
   Emits either vectorized MATLAB code directly or MATLAB MEX wrappers around
   compiled C or Fortran backends.

``phoenix.fgen.backends.julia.julia_builder``
   Emits either native Julia code directly or Julia wrappers around compiled C
   or Fortran backends via ``ccall``.

``phoenix.fgen.backends.fortran.fortran_builder``
   Emits Fortran code suitable for compilation and ``f2py`` wrapping.

``phoenix.fgen.backends.c.c_builder``
   Emits C code with explicit pointer-style routine interfaces.

``phoenix.fgen.backends.opencl.opencl_builder``
   Emits OpenCL C kernel source and maps multiframe expansion to OpenCL work
   item and work group identifiers.

``phoenix.fgen.backends.cuda.cuda_builder``
   Emits CUDA-flavoured C/C++ code with host routines and kernel launch syntax
   when compute resources request kernel expansion.


Wrapper families
----------------

``phoenix.fgen.backends.python.python_wrapper``
   Calls generated Python code directly.

``phoenix.fgen.backends.numpy.numpy_wrapper``
   Calls generated NumPy-based Python code directly.

``phoenix.fgen.backends.fortran.fortran_wrapper``
   Assumes Python-callable Fortran routines, typically via ``f2py``.

``phoenix.fgen.backends.c.c_wrapper``
   Uses ``ctypes`` and C-compatible storage references.

``phoenix.fgen.backends.opencl.opencl_wrapper``
   Compiles generated ``.cl`` source through ``pyopencl`` and launches kernels
   against backend-owned OpenCL device arrays.

``phoenix.fgen.backends.cuda.cuda_wrapper``
   Uses C-style host-callable CUDA entry points for ordinary routines and can
   also launch generated kernel routines directly from Python through a PTX
   module when CuPy is available.


ADAA families
-------------

The backend-local ADAA modules describe where the actual data lives:

``phoenix.fgen.backends.python.python_adaa``: ``PythonRA`` / ``PythonCA``
   Python lists.

``phoenix.fgen.backends.numpy.numpy_adaa``: ``NumPyRA`` / ``NumPyCA``
   NumPy arrays.

``phoenix.fgen.backends.fortran.fortran_adaa``: ``FortranRA`` / ``FortranCA``
   NumPy-backed arrays intended for direct Fortran wrapper use.

``phoenix.fgen.backends.c.c_adaa``: ``CRA`` / ``CCA``
   C-owned storage with explicit conversion to and from NumPy.

``phoenix.fgen.backends.opencl.opencl_adaa``: ``OpenClRA`` / ``OpenClCA``
   OpenCL device arrays with explicit conversion to and from NumPy.

``phoenix.fgen.backends.cuda.cuda_cupy_adaa`` and ``phoenix.fgen.backends.cuda.cuda_pycuda_adaa``
   GPU-backed data for the shared CUDA backend, selected through
   ``cuda.runtime.adaa_library``.


Backend Selection Strategy
--------------------------

Typical modern usage looks like this:

1. ``backend = get_backend("numpy")`` (or ``"python"``, ``"c"``, ``"fortran"``, ...)
2. ``library = backend.library("my_library")``
3. ``backend.libroutine_from_instructions(..., assignment_config=...)``
4. ``wrapper = backend.wrapped("my_routine", library, build=True)``

If you are still exploring the symbolic workflow, start with the Python
backend. Once the symbolic operation is correct, move to NumPy, C, Fortran,
OpenCL, or CUDA depending on your runtime and deployment requirements.

Configuration Client
--------------------

Native-toolchain backends are configured through the PHOENIX configuration
frontends. The configuration service writes backend JSON files, exposes
per-backend interactive dialogues, supports direct dotted-path ``get`` and
``set`` access, and generates backend-local support files under folders such as
``phoenix/fgen/backends/c/support/``. For backends that require auxiliary
native support code, the configurator also attempts to build those support
artifacts at the end of the configuration run.

Useful commands:

.. code-block:: bash

   phoenix-config --status
   phoenix-config fortran.executables.compiler
   phoenix-config fortran.executables.compiler gfortran
   phoenix-config --dialogue c
   phoenix-config --test c
   phoenix-config --gui

Each backend also has an ``enabled`` flag. This allows a backend to remain part
of the generated-code configuration even if a compiler, runtime wrapper, or
Python package is currently missing. In that situation PHOENIX can still
generate backend-oriented code, but wrapper support or complete build commands
may be unavailable.

For the full initialization and GUI workflow, see :doc:`configuration`.
