__doc__ = """Backend facade and resource selection for generated C libraries."""

from ..backend import (
    Backend,
    _clone_c_omp_resource,
    _resolve_omp_num_threads,
)
from .c_adaa import CCA, CIA, CRA
from .c_builder import CBuilder, CComputeResource, CLibrary
from .c_optimizers import COmpAtomicOptimizer
from .c_wrapper import CPyWrapperLibrary


class CBackend(Backend):
    """Backend facade for C code generation and wrapping."""

    IDENTIFIER = "c"
    KEYWORDS = ("c", "clang", "gcc")
    BUILDER_CLASS = CBuilder
    LIBRARY_CLASS = CLibrary
    WRAPPER_LIBRARY_CLASS = CPyWrapperLibrary
    REAL_ADAA_CLASS = CRA
    IMAG_ADAA_CLASS = CIA
    COMPLEX_ADAA_CLASS = CCA
    DEFAULT_OPTIMIZERS = (COmpAtomicOptimizer,)

    def get_resource_factories(self):
        omp_threads = _resolve_omp_num_threads(self)
        return {
            "default": lambda **_: CComputeResource("c default"),
            "serial": lambda **_: CComputeResource("c serial"),
            "omp": lambda **_: _clone_c_omp_resource(num_threads=omp_threads),
            "openmp": lambda **_: _clone_c_omp_resource(
                num_threads=omp_threads
            ),
        }

    def resolve_default_wrapper_lib(self, library):
        return library.relative_to_basepath(library.sharedlibname)


__all__ = ["CBackend"]
