__doc__ = """Backend facade for generated MATLAB or Octave libraries."""

from ..backend import Backend
from .matlab_builder import (
    MatlabBuilder,
    MatlabComputeResource,
    MatlabLibrary,
)


class MatlabBackend(Backend):
    """Backend facade for MATLAB code generation and wrapping."""

    IDENTIFIER = "matlab"
    KEYWORDS = ("matlab", "octave")
    BUILDER_CLASS = MatlabBuilder
    LIBRARY_CLASS = MatlabLibrary

    def get_resource_factories(self):
        return {
            "default": lambda **_: MatlabComputeResource("matlab default"),
            "serial": lambda **_: MatlabComputeResource("matlab serial"),
        }


__all__ = ["MatlabBackend"]
