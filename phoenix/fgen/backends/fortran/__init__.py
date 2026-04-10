"""Fortran backend package."""

from importlib import import_module

_EXPORTS = {
    "FortranBackend": "phoenix.fgen.backends.fortran.fortran_backend",
    "FortranBuilder": "phoenix.fgen.backends.fortran.fortran_builder",
    "FortranCA": "phoenix.fgen.backends.fortran.fortran_adaa",
    "FortranComputeResource": "phoenix.fgen.backends.fortran.fortran_builder",
    "FortranIA": "phoenix.fgen.backends.fortran.fortran_adaa",
    "FortranLibrary": "phoenix.fgen.backends.fortran.fortran_builder",
    "FortranLocalVariable": "phoenix.fgen.backends.fortran.fortran_builder",
    "FortranMFTPythonModule": "phoenix.fgen.backends.fortran.fortran_builder",
    "FortranPyWrapperLibrary": "phoenix.fgen.backends.fortran.fortran_wrapper",
    "FortranRA": "phoenix.fgen.backends.fortran.fortran_adaa",
    "OMP_FORTRAN_DEFAULT_RESOURCE": "phoenix.fgen.backends.fortran.fortran_resource",
    "OMPFortranSingleLayerResource": "phoenix.fgen.backends.fortran.fortran_resource",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module = import_module(_EXPORTS[name])
    return getattr(module, name)
