__doc__ = """Backend facade for CUDA code generation and ADAA selection."""

from ...buildchain import SingleMapApplyChainValidator
from ..backend import Backend
from .cuda_cupy_adaa import PROVIDE_CUPY
from .cuda_pycuda_adaa import PROVIDE_PYCUDA
from .cuda_builder import (
    CUDABuilder,
    CUDADeviceResource,
    CUDAHostResource,
    CUDALibrary,
)
from .cuda_optimizers import CUDAAtomicOptimizer
from .cuda_validators import CUDAKernelRoutineCallValidator
from .cuda_wrapper import CUDAPyWrapperLibrary

CUPY_FAMILIES = {}
if PROVIDE_CUPY:
    from .cuda_cupy_adaa import CupyCA, CupyIA, CupyRA

    CUPY_FAMILIES = {
        "complex": CupyCA,
        "real": CupyRA,
        "imag": CupyIA,
    }

PYCUDA_FAMILIES = {}
if PROVIDE_PYCUDA:
    from .cuda_pycuda_adaa import (
        PyCudaCA,
        PyCudaIA,
        PyCudaRA,
    )

    PYCUDA_FAMILIES = {
        "complex": PyCudaCA,
        "real": PyCudaRA,
        "imag": PyCudaIA,
    }


def _default_cuda_adaa_library() -> str:
    if PROVIDE_CUPY:
        return "cupy"
    if PROVIDE_PYCUDA:
        return "pycuda"
    return "cupy"


class CUDABackend(Backend):
    """Backend facade for CUDA code generation and wrapping."""

    IDENTIFIER = "cuda"
    KEYWORDS = ("cuda", "gpu")
    BUILDER_CLASS = CUDABuilder
    LIBRARY_CLASS = CUDALibrary
    WRAPPER_LIBRARY_CLASS = CUDAPyWrapperLibrary
    DEFAULT_VALIDATORS = (
        SingleMapApplyChainValidator,
        CUDAKernelRoutineCallValidator,
    )
    DEFAULT_OPTIMIZERS = (CUDAAtomicOptimizer,)

    def selected_adaa_library(self) -> str:
        selected = str(
            self.configuration.get_nested(
                "runtime",
                "adaa_library",
                default=_default_cuda_adaa_library(),
            )
        ).strip().lower()
        if selected not in {"cupy", "pycuda"}:
            raise ValueError(
                f"Unsupported CUDA ADAA library selection {selected!r}."
            )
        return selected

    def get_assignment_families(self):
        selected = self.selected_adaa_library()
        if selected == "pycuda":
            families = dict(PYCUDA_FAMILIES)
        else:
            families = dict(CUPY_FAMILIES)
        if families and "default" not in families:
            families["default"] = families["complex"]
        return families

    def get_resource_factories(self):
        threads = int(
            self.general_configuration.get_nested(
                "runtime", "num_processors", default=256
            )
        )
        threads = max(1, min(1024, threads))
        return {
            "default": lambda **_: CUDADeviceResource(
                "cuda device", nthreads=threads
            ),
            "host": lambda **_: CUDAHostResource("cuda host"),
            "device": lambda **_: CUDADeviceResource(
                "cuda device", nthreads=threads
            ),
        }

    def resolve_default_wrapper_lib(self, library):
        return library.relative_to_basepath(library.sharedlibname)


__all__ = [
    "CUDABackend",
    "CUPY_FAMILIES",
    "PYCUDA_FAMILIES",
]
