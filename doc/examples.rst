Examples
========

Demo series
-----------

The repository now uses ``demo/`` for staged examples and audience-facing
walkthroughs. The current demo tracks are:

``demo/01a_spin_system.py`` to ``demo/01c_spin_model_extended.py``
   Direct executable spin-dynamics walkthrough.

``demo/02a_spin_chain_keymaps.py`` to ``demo/02c_mapapply_lattice.py``
   Symbolic scaling path from keymaps to ``MapApplyInstruction``.

``demo/03a_backend_matrix.py``
   Side-by-side backend code-generation comparison.

``demo/04a_buffers_and_parallelism.py`` and ``demo/04b_parallel_benchmark.py``
   Explicit buffering, OpenMP resource comparison, and parallel benchmark.

``demo/05a_atomic_regions.py``
   Atomic-region lowering preview.

``demo/06a_configuration_and_testing.py``
   Configuration and backend smoke-test walkthrough.

``demo/07a_adaa_families.py``
   ADAA family comparison across available runtimes.

``demo/08a_library_packaging.py``
   Generated multi-library packaging overview.


Suggested learning order
------------------------

1. Start with the ``tutorials/00x`` nutshell series described in
   :doc:`tutorials`.
2. Continue with ``tutorials/04_python_backend.py`` and
   ``tutorials/10_backend_api.py`` for the modern backend facade.
3. Move to ``demo/01x`` if you want a concrete executable scientific example.
4. Move to ``demo/02x`` if you want to see how symbolic models scale more
   cleanly once layouts and local kernels are factored out.
5. Use ``demo/03x`` onward for backend comparison, explicit buffers,
   synchronization, configuration, and packaging topics.
