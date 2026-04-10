"""Registry of per-backend Phoenix configurators."""

from .base import BackendConfigurator
from .c import CONFIGURATOR as C_CONFIGURATOR
from .cuda import CONFIGURATOR as CUDA_CONFIGURATOR
from .fortran import CONFIGURATOR as FORTRAN_CONFIGURATOR
from .julia import CONFIGURATOR as JULIA_CONFIGURATOR
from .matlab import CONFIGURATOR as MATLAB_CONFIGURATOR
from .numpy import CONFIGURATOR as NUMPY_CONFIGURATOR
from .opencl import CONFIGURATOR as OPENCL_CONFIGURATOR
from .plain import CONFIGURATOR as PLAIN_CONFIGURATOR
from .python import CONFIGURATOR as PYTHON_CONFIGURATOR


CONFIGURATORS: dict[str, BackendConfigurator] = {
    configurator.name: configurator
    for configurator in (
        PLAIN_CONFIGURATOR,
        PYTHON_CONFIGURATOR,
        NUMPY_CONFIGURATOR,
        C_CONFIGURATOR,
        FORTRAN_CONFIGURATOR,
        JULIA_CONFIGURATOR,
        MATLAB_CONFIGURATOR,
        OPENCL_CONFIGURATOR,
        CUDA_CONFIGURATOR,
    )
}


def get_configurator(name: str) -> BackendConfigurator:
    """Return the configurator registered under ``name``."""
    key = name.lower()
    if key not in CONFIGURATORS:
        raise KeyError(f"unknown backend {name!r}")
    return CONFIGURATORS[key]


__all__ = ["BackendConfigurator", "CONFIGURATORS", "get_configurator"]
