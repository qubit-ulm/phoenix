"""Configurator for the NumPy backend."""

from ..base import ExecutableField, SimpleBackendConfigurator


class NumPyConfigurator(SimpleBackendConfigurator):
    """Configure the NumPy backend."""

    name = "numpy"
    description = "NumPy backend using host arrays and vectorized expressions."
    executable_fields = (
        ExecutableField("python", "Python executable", ("python3", "python")),
    )
    default_resource = {
        "device": "cpu",
        "parallel_model": "numpy",
    }
    parallel_choices = ("numpy",)


CONFIGURATOR = NumPyConfigurator()
