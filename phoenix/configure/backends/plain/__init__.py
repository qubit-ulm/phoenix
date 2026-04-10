"""Configurator for the plain symbolic backend."""

from ..base import SimpleBackendConfigurator


class PlainConfigurator(SimpleBackendConfigurator):
    """Configure the plain backend."""

    name = "plain"
    description = "Symbolic plain-text backend without external toolchain."
    default_resource = {
        "device": "symbolic",
        "parallel_model": "none",
    }
    parallel_choices = ("none",)


CONFIGURATOR = PlainConfigurator()
