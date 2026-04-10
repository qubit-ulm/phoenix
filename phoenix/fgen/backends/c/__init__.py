"""C backend package."""

from importlib import import_module

_EXPORTS = {
    "CCA": "phoenix.fgen.backends.c.c_adaa",
    "CIA": "phoenix.fgen.backends.c.c_adaa",
    "CRA": "phoenix.fgen.backends.c.c_adaa",
    "CBackend": "phoenix.fgen.backends.c.c_backend",
    "CBuilder": "phoenix.fgen.backends.c.c_builder",
    "CComputeResource": "phoenix.fgen.backends.c.c_builder",
    "CLibrary": "phoenix.fgen.backends.c.c_builder",
    "COmpAtomicOptimizer": "phoenix.fgen.backends.c.c_optimizers",
    "CPyWrapperLibrary": "phoenix.fgen.backends.c.c_wrapper",
    "OMPCSingleLayerResource": "phoenix.fgen.backends.c.c_resource",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module = import_module(_EXPORTS[name])
    return getattr(module, name)
