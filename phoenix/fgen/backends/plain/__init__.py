"""Plain backend package."""

from importlib import import_module

_EXPORTS = {
    "PlainBackend": "phoenix.fgen.backends.plain.plain_backend",
    "PlainBuilder": "phoenix.fgen.backends.plain.plain_builder",
    "PlainComputeResource": "phoenix.fgen.backends.plain.plain_builder",
    "PlainLibrary": "phoenix.fgen.backends.plain.plain_builder",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module = import_module(_EXPORTS[name])
    return getattr(module, name)
