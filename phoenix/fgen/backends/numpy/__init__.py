"""NumPy backend package."""

from importlib import import_module

_EXPORTS = {
    "NPBuilder": "phoenix.fgen.backends.numpy.numpy_builder",
    "NPComputeResource": "phoenix.fgen.backends.numpy.numpy_builder",
    "NPLibrary": "phoenix.fgen.backends.numpy.numpy_builder",
    "NumPyBackend": "phoenix.fgen.backends.numpy.numpy_backend",
    "NumPyCA": "phoenix.fgen.backends.numpy.numpy_adaa",
    "NumPyIA": "phoenix.fgen.backends.numpy.numpy_adaa",
    "NumPyPyWrapperLibrary": "phoenix.fgen.backends.numpy.numpy_wrapper",
    "NumPyRA": "phoenix.fgen.backends.numpy.numpy_adaa",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module = import_module(_EXPORTS[name])
    return getattr(module, name)
