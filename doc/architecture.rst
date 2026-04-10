Architecture
============

Overview
--------

PHOENIX separates *what* should be computed from *how* it is executed. The
pipeline is intentionally layered:

Symbolic layer
   Keymaps, instruction variables, and instruction objects describe the
   operation in a backend-agnostic form.

Routine layer
   Builders, contexts, code containers, and routine variables interpret the
   symbolic instruction stream and create a structured routine implementation.

Backend layer
   Libraries, wrappers, and ADAAs connect generated code to concrete runtime
   storage such as Python lists, NumPy arrays, C buffers, or GPU memory.


Key Concepts
------------

What "IR" Means Here
--------------------

PHOENIX uses the term *IR* as shorthand for *intermediate representation*.
That means an internal representation that sits between the user-facing
symbolic problem description and the final emitted backend code.

In this project, the instruction layer is the central IR:

- it is structured enough to support regrouping, map-apply lowering,
  environments, dependency handling, and multiframe expansion,
- it is still backend-neutral, unlike final C, Fortran, Python, or CUDA
  source code,
- and it stays close to the symbolic objects the user creates, such as
  instruction variables and keyed offsets.

So when the documentation refers to the "instruction IR", it means the object
model in :mod:`phoenix.fgen.instruction` together with the symbolic variables
and environments that travel with it. Builders consume that IR and lower it
into backend-specific routine containers and generated source code.

Keymaps
   A keymap is a tree of domains. It provides symbolic addressing, stable
   offset lookup, and a way to describe structured arrays without hard-coding
   integer indices in user code.

Instruction variables
   Instruction variables are symbolic references into keymaps or other symbolic
   address spaces. Offsets can be integer, key-based, or symbolic.

Instructions
   Instructions are small arithmetic actions. They can be grouped, nested in
   environments, mapped over environments, or lowered into routine calls.

Routine variables
   Once instructions are lowered, symbolic variables become routine variables
   that know about input, output, local, constant, import, or multiframe roles.

Code containers
   Code containers form a tree representing the generated routine structure.
   They manage capture, scope, definition, embedding, and emitted lines.

Compute resources
   Compute resources decide how multiframe requests are expanded. A request may
   become a normal loop, a combined integer decomposition, or a kernel-driven
   expansion in a backend such as CUDA.

ADAAs
   An ADAA owns actual backend storage. The wrapper layer interacts with ADAAs
   rather than with raw arrays wherever possible. NumPy conversion is treated
   as an interface, not necessarily as the primary storage representation.


Design Notes
------------

PHOENIX is deliberately not a general tensor compiler. The codebase is oriented
toward structured sparse operations where:

- entries are naturally identified by symbolic keys,
- repeated patterns can be captured as instruction groups or map-apply blocks,
- the same symbolic operation is useful across several backend targets,
- backend-specific data ownership matters.

That combination is the reason the project contains both symbolic IR objects
and runtime data abstractions such as ADAAs.
