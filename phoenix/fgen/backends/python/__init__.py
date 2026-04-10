"""Python backend package."""

from importlib import import_module

_EXPORTS = {
    "PyBuilder": "phoenix.fgen.backends.python.python_builder",
    "PyComputeResource": "phoenix.fgen.backends.python.python_builder",
    "PyLibrary": "phoenix.fgen.backends.python.python_builder",
    "PyPyWrapperLibrary": "phoenix.fgen.backends.python.python_wrapper",
    "PythonBackend": "phoenix.fgen.backends.python.python_backend",
    "PythonCA": "phoenix.fgen.backends.python.python_adaa",
    "PythonIA": "phoenix.fgen.backends.python.python_adaa",
    "PythonRA": "phoenix.fgen.backends.python.python_adaa",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module = import_module(_EXPORTS[name])
    return getattr(module, name)
