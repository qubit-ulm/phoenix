"""Julia backend package."""

from importlib import import_module

_EXPORTS = {
    "JuliaBackend": "phoenix.fgen.backends.julia.julia_backend",
    "JuliaBuilder": "phoenix.fgen.backends.julia.julia_builder",
    "JuliaComputeResource": "phoenix.fgen.backends.julia.julia_builder",
    "JuliaLibrary": "phoenix.fgen.backends.julia.julia_builder",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module = import_module(_EXPORTS[name])
    return getattr(module, name)
