"""Backend registry and convenience exports for Phoenix code generation."""

from .backend import AssignmentConfig, Backend, Config, get_backend
from .c.c_backend import CBackend
from .cuda.cuda_backend import CUDABackend
from .fortran.fortran_backend import FortranBackend
from .julia.julia_backend import JuliaBackend
from .matlab.matlab_backend import MatlabBackend
from .numpy.numpy_backend import NumPyBackend
from .opencl.opencl_backend import OpenCLBackend
from .plain.plain_backend import PlainBackend
from .python.python_backend import PythonBackend

__all__ = [
    "AssignmentConfig",
    "Backend",
    "CBackend",
    "CUDABackend",
    "Config",
    "FortranBackend",
    "JuliaBackend",
    "MatlabBackend",
    "NumPyBackend",
    "OpenCLBackend",
    "PlainBackend",
    "PythonBackend",
    "get_backend",
]
