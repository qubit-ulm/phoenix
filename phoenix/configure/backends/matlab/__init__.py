"""Configurator for the MATLAB/Octave backend."""

from ..base import ExecutableField, SimpleBackendConfigurator


class MatlabConfigurator(SimpleBackendConfigurator):
    """Configure the MATLAB/Octave backend."""

    name = "matlab"
    description = "MATLAB/Octave wrapper backend."
    executable_fields = (
        ExecutableField("matlab_mex", "MATLAB mex executable", ("mex",)),
        ExecutableField("octave_mex", "Octave mex executable", ("mkoctfile",)),
    )
    default_resource = {
        "device": "cpu",
        "parallel_model": "matlab",
    }
    parallel_choices = ("matlab",)


CONFIGURATOR = MatlabConfigurator()
