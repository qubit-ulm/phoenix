"""OpenCL backend package."""

from importlib import import_module

_EXPORTS = {
    "OpenCLBackend": "phoenix.fgen.backends.opencl.opencl_backend",
    "OpenCLBuilder": "phoenix.fgen.backends.opencl.opencl_builder",
    "OpenCLDeviceResource": "phoenix.fgen.backends.opencl.opencl_builder",
    "OpenCLHostResource": "phoenix.fgen.backends.opencl.opencl_builder",
    "OpenCLLibrary": "phoenix.fgen.backends.opencl.opencl_builder",
    "OpenCLPyWrapperLibrary": "phoenix.fgen.backends.opencl.opencl_wrapper",
    "PROVIDE_OPENCL": "phoenix.fgen.backends.opencl.opencl_adaa",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module = import_module(_EXPORTS[name])
    return getattr(module, name)
