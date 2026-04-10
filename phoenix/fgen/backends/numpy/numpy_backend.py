__doc__ = """Backend facade for NumPy-based generated libraries and wrappers."""

from ..backend import Backend
from .numpy_adaa import NumPyCA, NumPyIA, NumPyRA
from .numpy_builder import (
    NPBuilder,
    NPComputeResource,
    NPLibrary,
)
from .numpy_wrapper import NumPyPyWrapperLibrary


class NumPyBackend(Backend):
    """Backend facade for NumPy-based code generation."""

    IDENTIFIER = "numpy"
    KEYWORDS = ("numpy", "np")
    BUILDER_CLASS = NPBuilder
    LIBRARY_CLASS = NPLibrary
    WRAPPER_LIBRARY_CLASS = NumPyPyWrapperLibrary
    REAL_ADAA_CLASS = NumPyRA
    IMAG_ADAA_CLASS = NumPyIA
    COMPLEX_ADAA_CLASS = NumPyCA

    def get_resource_factories(self):
        return {
            "default": lambda **_: NPComputeResource("numpy default"),
            "numpy": lambda **_: NPComputeResource("numpy resource"),
            "serial": lambda **_: NPComputeResource("numpy serial"),
        }

    def resolve_default_wrapper_lib(self, library):
        return self.import_python_module(library)


__all__ = ["NumPyBackend"]
