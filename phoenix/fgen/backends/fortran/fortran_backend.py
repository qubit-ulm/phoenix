__doc__ = """Backend facade and resource selection for generated Fortran libraries."""

from ..backend import (
    Backend,
    _clone_fortran_omp_resource,
    _resolve_omp_num_threads,
)
from .fortran_adaa import FortranCA, FortranIA, FortranRA
from .fortran_builder import (
    FortranBuilder,
    FortranComputeResource,
    FortranLibrary,
)
from .fortran_optimizers import FortranOmpAtomicOptimizer
from .fortran_wrapper import FortranPyWrapperLibrary


class FortranBackend(Backend):
    """Backend facade for Fortran code generation and wrapping."""

    IDENTIFIER = "fortran"
    KEYWORDS = ("fortran", "f90", "fortran90")
    BUILDER_CLASS = FortranBuilder
    LIBRARY_CLASS = FortranLibrary
    WRAPPER_LIBRARY_CLASS = FortranPyWrapperLibrary
    REAL_ADAA_CLASS = FortranRA
    IMAG_ADAA_CLASS = FortranIA
    COMPLEX_ADAA_CLASS = FortranCA
    DEFAULT_OPTIMIZERS = (FortranOmpAtomicOptimizer,)

    def get_resource_factories(self):
        omp_threads = _resolve_omp_num_threads(self)
        return {
            "default": lambda **_: FortranComputeResource("fortran default"),
            "serial": lambda **_: FortranComputeResource("fortran serial"),
            "omp": lambda **_: _clone_fortran_omp_resource(
                num_threads=omp_threads
            ),
            "openmp": lambda **_: _clone_fortran_omp_resource(
                num_threads=omp_threads
            ),
        }

    def resolve_default_wrapper_lib(self, library):
        return self.import_python_module(library)


__all__ = ["FortranBackend"]
