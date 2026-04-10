__doc__ = """Backend facade for generated Julia libraries."""

from ..backend import Backend
from .julia_builder import (
    JuliaBuilder,
    JuliaComputeResource,
    JuliaLibrary,
)


class JuliaBackend(Backend):
    """Backend facade for Julia code generation and wrapping."""

    IDENTIFIER = "julia"
    KEYWORDS = ("julia",)
    BUILDER_CLASS = JuliaBuilder
    LIBRARY_CLASS = JuliaLibrary

    def get_resource_factories(self):
        return {
            "default": lambda **_: JuliaComputeResource("julia default"),
            "serial": lambda **_: JuliaComputeResource("julia serial"),
        }


__all__ = ["JuliaBackend"]
