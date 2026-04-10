"""MATLAB backend package."""

from importlib import import_module

_EXPORTS = {
    "MatlabBackend": "phoenix.fgen.backends.matlab.matlab_backend",
    "MatlabBuilder": "phoenix.fgen.backends.matlab.matlab_builder",
    "MatlabComputeResource": "phoenix.fgen.backends.matlab.matlab_builder",
    "MatlabLibrary": "phoenix.fgen.backends.matlab.matlab_builder",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module = import_module(_EXPORTS[name])
    return getattr(module, name)
