# The Routine Module

Routines have been mentioned before as a construct made from instructions. As a safety measure, routines need to be bound to the data structures that the instructions are associated with. Routines themselves then stay abstract - a set of instructions rather than a specific implementation of them.

Routines might have dependencies, for example if they are made from instructions that call other routines with certain offsets.



# The Library Module

The Library module provides a class for Libraries as well as for Libroutines. Libraries are made from one or more Libroutines, while Libroutines themselves represent specific implementations of (the more abstract) routines. They are made from actual code, compiled and then available in their associated library.

Libroutines remember the routine that they are made from. They include the dependencies relevant for their implementation. When a Libroutine is included, dependencies are automatically resolved and included as well. Depending on the specific backend, dependent code can be included in the same source file or imported from other libraries.

The Library Manager class handles the creation of libraries. It provides functions and data structures to connect libraries and their dependencies and collects all code lines, to finally generate actual source code.

A libroutine can be associated to exactly one library. If a libroutine is requested as a dependency but not part of a library, it is compiled into a standalone library that consists only of this specific libroutine. If the same libroutine is needed in multiple libraries, identical copies of that libroutine have to be made. This is not a problem, as a libroutine associates to a routine, but not vice versa.

The MakeFileManager acts outside of this framework. It prepares calls to prepare and compile the Libroutines in the library source files. The MakeFileManager provides a class for MakeFileTargets. Targets are associated to source code, object files, libraries, executables and more and inherit potential dependencies from the Libraries and Libroutines they are made from.

The targets are categorized into objects, source, libraries and more to guarantee that they are properly treated and invoked by the makefile commands.