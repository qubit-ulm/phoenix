__doc__ = """Backend facade for generated pure-Python libraries and wrappers."""

from ..backend import Backend
from .python_adaa import PythonCA, PythonIA, PythonRA
from .python_builder import (
    PyBuilder,
    PyComputeResource,
    PyLibrary,
)
from .python_wrapper import PyPyWrapperLibrary


class PythonBackend(Backend):
    """Backend facade for pure-Python code generation."""

    IDENTIFIER = "python"
    KEYWORDS = ("python", "py")
    BUILDER_CLASS = PyBuilder
    LIBRARY_CLASS = PyLibrary
    WRAPPER_LIBRARY_CLASS = PyPyWrapperLibrary
    REAL_ADAA_CLASS = PythonRA
    IMAG_ADAA_CLASS = PythonIA
    COMPLEX_ADAA_CLASS = PythonCA

    def get_resource_factories(self):
        return {
            "default": lambda **_: PyComputeResource("python default"),
            "python": lambda **_: PyComputeResource("python resource"),
            "serial": lambda **_: PyComputeResource("python serial"),
        }

    def resolve_default_wrapper_lib(self, library):
        return self.import_python_module(library)


__all__ = ["PythonBackend"]
