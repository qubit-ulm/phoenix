Configuration
=============

Name: ``PHOENIX``

Acronym: Parallel Hybrid Operations for Enhanced Numerical Implementations and
eXecutions

The configuration layer is the user-facing interface for inspecting and
changing persistent settings. It writes the shared configuration file under
``phoenix/fgen/backends/config/general.json``, backend defaults such as
``phoenix/fgen/backends/fortran/fortran_default.json``, and backend-local
support files under folders such as ``phoenix/fgen/backends/c/support/``.

The release-cleanup helper ``make release-dump`` or
``bash scripts/release_dump.sh`` can be used afterwards to move generated
support artifacts, Sphinx build output, demo media, and other non-release
files out of the tracked working tree.

Configuration Frontends
-----------------------

PHOENIX now ships with three frontends that all call the same configuration
service:

``phoenix-config``
   Main command-line interface for reading, writing, showing status, launching
   per-backend dialogues, opening the settings GUI, and rolling backend smoke
   tests.

``phoenix-config-init``
   Standalone backend-initialization frontend. It detects compilers and Python
   libraries, then lets you choose which backends shall be provided.

``phoenix-config-gui``
   Standalone settings GUI launcher.

The module entry points remain available as well:

.. code-block:: bash

   python -m phoenix.configure
   python -m phoenix.configure --status
   python -m phoenix.configure --test python


Dotted Setting Paths
--------------------

Settings can be addressed with dotted paths similar to ``gsettings``.
Backend-specific settings begin with the backend name.

Examples:

.. code-block:: bash

   phoenix-config fortran.executables.compiler
   phoenix-config fortran.executables.compiler gfortran
   phoenix-config fortran.resource.parallel_model '"omp"'
   phoenix-config fortran.enabled false
   phoenix-config general.logging.level DEBUG

The first path element determines the configuration scope:

- ``general`` addresses the shared configuration file.
- ``fortran``, ``c``, ``cuda``, ``opencl``, ``python``, ``numpy``, ``plain``,
  ``julia``, and ``matlab`` address backend-local configuration files.
- If no backend name is used, the setting is interpreted as part of the general
  configuration.


Backend Enable State
--------------------

Each backend configuration carries an ``enabled`` flag. This is distinct from
toolchain detection.

- A backend may be enabled even if a compiler path or Python runtime library is
  currently missing.
- In that case PHOENIX can still generate code suited for that backend, but
  wrappers may not be available and generated makefiles may contain placeholder
  compiler commands.
- Detection only influences recommended defaults during initialization and
  dialogue prompts.


Status View
-----------

Use the status view to inspect the current backend state:

.. code-block:: bash

   phoenix-config --status

The table distinguishes between several states:

- ``supported``: backend exists in PHOENIX, but no matching local toolchain was
  detected and no configuration has been written yet.
- ``available``: backend support was detected, but no persistent configuration
  has been written yet.
- ``enabled``: backend is configured and enabled.
- ``disabled``: backend is configured but explicitly disabled.


Backend Smoke Tests
-------------------

The main configuration frontend can also roll backend smoke tests:

.. code-block:: bash

   phoenix-config --test python
   phoenix-config --test fortran
   phoenix-config --test all

The smoke-test path is intentionally non-GUI. It is meant for release checks
and developer validation after changing backend configuration, builders, or
wrapper paths.

The smoke tests combine:

- generic code-generation checks for a basic instruction group,
- a mapapply generation check,
- runtime execution for the stable installed wrapper backends,
- and NumPy-based result comparisons on the runtime path.


Per-Backend Dialogue
--------------------

The main configuration script can still launch the interactive backend dialogue:

.. code-block:: bash

   phoenix-config --dialogue fortran
   phoenix-config --dialogue c
   phoenix-config --dialogue all

This dialogue is intended for editing one backend at a time. Because the
backend name is already the first segment of a dotted path, the backend does
not need to be passed separately for direct ``get`` and ``set`` calls.


Initialization Frontend
-----------------------

Initialization is separate from ordinary setting access. The initializer scans
for likely compilers, Python interpreters, and backend-related Python modules,
then proposes backend enable defaults.

CLI dialogue:

.. code-block:: bash

   phoenix-config-init
   phoenix-config --initialize-dialogue

GUI:

.. code-block:: bash

   phoenix-config-init --gui
   phoenix-config --initialize-gui

The initialization dialogue asks ``y/n`` per backend. The default is based on
what was detected locally, but the final selection is always up to the user.


Settings GUI
------------

The settings GUI is a standalone frontend and can also be opened through the
main configuration script:

.. code-block:: bash

   phoenix-config --gui
   phoenix-config-gui
   phoenix-config-gui fortran

The GUI presents a scrollable two-column editor with parameter name and current
value, plus a read-only default column. Current values are prefilled, defaults
are shown alongside them, and changes can be saved or aborted.

The GUI and the per-backend dialogue are mutually exclusive modes of the main
configuration command. Initialization is handled by its own dialogue or GUI.


Defaults and System Detection
-----------------------------

The configuration scanner contains a small system-probe layer. It is used to:

- detect likely compiler and interpreter paths,
- detect optional Python libraries such as ``pyopencl`` or ``cupy``,
- provide placeholder executable names if the actual toolchain is missing,
- refresh defaults when a backend is initialized again later.

This keeps the configuration module focused on standardized access to settings,
while the frontends provide different ways for users to interact with it.
