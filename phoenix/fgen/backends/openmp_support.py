from __future__ import annotations

__doc__ = """Shared OpenMP support helpers used by backend-specific resources."""

from ..library import Library, LibraryContent
from ..libroutinevar import ExternalImport
from ..makefile import MFTExternalLibrary


class OpenMPDependencyLibrary(Library):
    """Placeholder library contributing OpenMP compiler and linker flags."""

    def __init__(self, plain_name, *, compiler_flag="-fopenmp"):
        self._compiler_flag = compiler_flag
        self._target = MFTExternalLibrary(
            plain_name,
            compflags=[compiler_flag],
            linkflags=[compiler_flag],
            silent=False,
        )
        super().__init__(plain_name)

    def _get_libname(self):
        return self._plain_name

    def prepare(self, force=False):
        del force
        return True, None

    def write(self, force=False):
        del force
        return True, None

    def compile(self, makefile=None, force=False, execute=True):
        del makefile, force, execute
        return True, None

    def write_all_files(self):
        return True

    def get_makefile_targets(self):
        yield self._target

    def get_header_target(self):
        return self._target

    def get_object_target(self):
        return None

    def get_library_target(self):
        return self._target

    def get_codefile_target(self):
        return None


OMP_FORTRAN_LIBRARY = OpenMPDependencyLibrary("omp_lib")
OMP_C_LIBRARY = OpenMPDependencyLibrary("omp")

OMP_FORTRAN_IMPORT = LibraryContent("omp_lib", library=OMP_FORTRAN_LIBRARY)
OMP_C_IMPORT = LibraryContent("omp", library=OMP_C_LIBRARY)

__all__ = [
    "ExternalImport",
    "OMP_C_IMPORT",
    "OMP_C_LIBRARY",
    "OMP_FORTRAN_IMPORT",
    "OMP_FORTRAN_LIBRARY",
    "OpenMPDependencyLibrary",
]
