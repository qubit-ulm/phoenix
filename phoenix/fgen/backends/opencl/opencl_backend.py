__doc__ = """Backend facade for generated OpenCL libraries and wrappers."""

from ...buildchain import SingleMapApplyChainValidator
from ..backend import Backend
from .opencl_adaa import PROVIDE_OPENCL
from .opencl_builder import (
    OpenCLBuilder,
    OpenCLDeviceResource,
    OpenCLHostResource,
    OpenCLLibrary,
)
from .opencl_validators import OpenCLKernelRoutineCallValidator
from .opencl_wrapper import OpenCLPyWrapperLibrary


class OpenCLBackend(Backend):
    """Backend facade for OpenCL code generation and wrapping."""

    IDENTIFIER = "opencl"
    KEYWORDS = ("opencl", "ocl")
    BUILDER_CLASS = OpenCLBuilder
    LIBRARY_CLASS = OpenCLLibrary
    WRAPPER_LIBRARY_CLASS = OpenCLPyWrapperLibrary
    DEFAULT_VALIDATORS = (
        SingleMapApplyChainValidator,
        OpenCLKernelRoutineCallValidator,
    )
    if PROVIDE_OPENCL:
        from .opencl_adaa import OpenClCA, OpenClIA, OpenClRA

        REAL_ADAA_CLASS = OpenClRA
        IMAG_ADAA_CLASS = OpenClIA
        COMPLEX_ADAA_CLASS = OpenClCA

    def get_resource_factories(self):
        return {
            "default": lambda **_: OpenCLDeviceResource("opencl default"),
            "device": lambda **_: OpenCLDeviceResource("opencl device"),
            "host": lambda **_: OpenCLHostResource("opencl host"),
            "serial": lambda **_: OpenCLHostResource("opencl serial"),
        }


__all__ = ["OpenCLBackend"]
