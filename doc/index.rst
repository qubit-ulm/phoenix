PHOENIX Documentation
=====================

.. image:: _static/phoenix-wordmark.png
   :alt: PHOENIX logo
   :align: center
   :width: 420

Name: ``PHOENIX``

Acronym: Parallel Hybrid Operations for Enhanced Numerical Implementations and
eXecutions

The wordmark is used as the documentation logo. The reduced square mark is
used as HTML favicon and can also serve as window decoration or application
symbol. The original design assets live in ``design/`` at the repository root.

PHOENIX is a code-generation framework for structured numerical operations.
It lets you describe operations symbolically with keymaps, instruction
variables, and instruction groups, then lower those descriptions into callable
implementations for multiple backends such as pure Python, NumPy, MATLAB,
Julia, Fortran, C, and CUDA.

The project has three main layers:

1. Symbolic problem description via :mod:`phoenix.keymap`,
   :mod:`phoenix.fgen.instruction`, and
   :mod:`phoenix.fgen.instructionvar`.
2. Routine construction via routine variables, code containers, compute
   resources, builders, and libraries in :mod:`phoenix.fgen`.
3. Backend data handling via ADAAs and backend-specific wrappers in
   :mod:`phoenix.adaa`, :mod:`phoenix.adaas`, and the
   backend modules under :mod:`phoenix.fgen.backends`.

.. toctree::
   :maxdepth: 2
   :caption: Guide

   getting_started
   architecture
   backends
   configuration
   testing
   tutorials
   examples
   citation
   api/index


Reference Aids
==============

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
