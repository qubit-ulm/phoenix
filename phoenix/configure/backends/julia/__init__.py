"""Configurator for the Julia backend."""

from ..base import ExecutableField, SimpleBackendConfigurator


class JuliaConfigurator(SimpleBackendConfigurator):
    """Configure the Julia backend."""

    name = "julia"
    description = "Julia wrapper backend for generated libraries."
    executable_fields = (
        ExecutableField("julia", "Julia executable", ("julia",)),
    )
    default_resource = {
        "device": "cpu",
        "parallel_model": "julia",
    }
    parallel_choices = ("julia",)


CONFIGURATOR = JuliaConfigurator()
