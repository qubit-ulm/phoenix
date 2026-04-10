"""Configurator for the Fortran backend."""

from ..base import ExecutableField, SimpleBackendConfigurator


class FortranConfigurator(SimpleBackendConfigurator):
    """Configure the Fortran backend."""

    name = "fortran"
    description = "Fortran backend using f2py for Python-facing builds."
    executable_fields = (
        ExecutableField("compiler", "Fortran compiler", ("gfortran", "ifx", "flang")),
        ExecutableField("linker", "Fortran linker", ("gfortran", "ifx", "flang")),
        ExecutableField("python", "Python executable", ("python3", "python")),
        ExecutableField("f2py", "f2py executable"),
    )
    default_flags = {
        "object": ["-fPIC", "-march=native"],
        "shared": ["-shared", "-Wl,-rpath,'$$ORIGIN:$$ORIGIN/..'"],
        "f2py_compile": ["-O3", "-march=native", "-ffree-line-length-none"],
        "extra_object": [],
        "extra_shared": [],
        "extra_f2py_compile": [],
    }
    default_prefixes = {
        "include": "-I",
        "library": "-L",
    }
    default_resource = {
        "device": "cpu",
        "parallel_model": "serial",
    }
    parallel_choices = ("serial", "omp")


CONFIGURATOR = FortranConfigurator()
