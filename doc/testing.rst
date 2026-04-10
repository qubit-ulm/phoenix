Testing
=======

Name: ``PHOENIX``

Acronym: Parallel Hybrid Operations for Enhanced Numerical Implementations and
eXecutions

PHOENIX uses a layered release-stage testing strategy so symbolic-core
regressions, backend-generation regressions, and configured runtime regressions
can be isolated quickly.

Release Strategy
----------------

The current strategy is organized into five layers:

1. Generic symbolic core: keymaps, key extension, tagged keys, instruction
   variables, offsets, environments, instruction groups, and library
   registration.
2. ADAA arithmetic: copy, zero, select, add, subtract, scalar multiply, and
   scalar divide across backend-owned ADAA families.
3. Backend generation matrix: every backend lowers a basic instruction group
   and a mapapply routine across ``real``, ``imag``, and ``complex``
   assignment families.
4. Backend runtime smoke: installed and configured runtime backends execute a
   stable wrapped routine and compare the result against a NumPy reference.
5. Configuration smoke: dotted configuration access, backend initialization,
   status reporting, and backend smoke invocation through
   ``phoenix-config --test``.


Generic-Core Coverage
---------------------

The generic modules should be covered independently of any concrete backend:

- ``phoenix.keymap``: entry insertion, nested links, recursive key iteration,
  offset roundtrips, key extension, automatic renaming, label-key handling,
  region indexing, and lock behaviour.
- ``phoenix.fgen.instructionvar``: offset progression, symbolic offsets,
  variable fusion, environment merge and fuse semantics, and scalar dtype
  generalization.
- ``phoenix.fgen.instruction``: instruction grouping, deep-copy semantics,
  mapapply traversal, and serialized record payloads.
- ``phoenix.fgen.library``: routine registration, content lookup, checksum
  changes, and generated file emission.


Backend Coverage
----------------

Backends are tested in two modes.

Generation smoke:

- All shipped backends participate.
- A basic instruction group is lowered.
- A mapapply routine is lowered on the stable generation path.
- All three assignment families are covered.

Runtime smoke:

- Only installed and configured wrapper backends participate.
- The runtime path focuses on the stable release family.
- Wrapper execution is compared against NumPy reference data.
- Backend setup issues are surfaced separately from symbolic-core issues.


Configuration-Driven Smoke Tests
--------------------------------

The configuration frontend exposes backend smoke tests directly:

.. code-block:: bash

   phoenix-config --test python
   phoenix-config --test c
   phoenix-config --test all

This gives a small release-style test entrypoint for the currently configured
backend environment without requiring any GUI interaction.
