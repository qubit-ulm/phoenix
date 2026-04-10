__doc__ = """Backend facade for symbolic plain-text code generation."""

from ..backend import Backend
from .plain_builder import (
    PlainBuilder,
    PlainComputeResource,
    PlainLibrary,
)


class PlainBackend(Backend):
    """Backend facade for symbolic plain-text code generation."""

    IDENTIFIER = "plain"
    KEYWORDS = ("plain", "text", "symbolic")
    BUILDER_CLASS = PlainBuilder
    LIBRARY_CLASS = PlainLibrary

    def get_resource_factories(self):
        return {
            "default": lambda **_: PlainComputeResource("plain default"),
            "serial": lambda **_: PlainComputeResource("plain serial"),
        }


__all__ = ["PlainBackend"]
