"""Configurator for the pure Python backend."""

from ..base import ExecutableField, SimpleBackendConfigurator


class PythonConfigurator(SimpleBackendConfigurator):
    """Configure the pure Python backend."""

    name = "python"
    description = "Pure Python backend using Python lists and scalar loops."
    executable_fields = (
        ExecutableField("python", "Python executable", ("python3", "python")),
    )
    default_resource = {
        "device": "cpu",
        "parallel_model": "python",
    }
    parallel_choices = ("python",)


CONFIGURATOR = PythonConfigurator()
