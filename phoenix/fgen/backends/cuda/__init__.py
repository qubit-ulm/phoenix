"""CUDA backend package."""

from importlib import import_module

_EXPORTS = {
    "CUDABackend": "phoenix.fgen.backends.cuda.cuda_backend",
    "CUDABuilder": "phoenix.fgen.backends.cuda.cuda_builder",
    "CUDADeviceResource": "phoenix.fgen.backends.cuda.cuda_builder",
    "CUDAHostResource": "phoenix.fgen.backends.cuda.cuda_builder",
    "CUDALibrary": "phoenix.fgen.backends.cuda.cuda_builder",
    "CUDAPyWrapperLibrary": "phoenix.fgen.backends.cuda.cuda_wrapper",
    "PROVIDE_CUPY": "phoenix.fgen.backends.cuda.cuda_cupy_adaa",
    "PROVIDE_PYCUDA": "phoenix.fgen.backends.cuda.cuda_pycuda_adaa",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module = import_module(_EXPORTS[name])
    return getattr(module, name)
