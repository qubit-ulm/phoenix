from __future__ import annotations

__doc__ = """Fortran backend compute-resource helpers, including OpenMP resources."""

from .fortran_builder import (
    FortranComputeResource,
    FortranLocalVariable,
    FortranMultiFrameExpandContainer,
)
from ..openmp_support import (
    ExternalImport,
    OMP_FORTRAN_IMPORT,
)


class OMPFortranParallelMultiFrameExpandContainer(FortranMultiFrameExpandContainer):
    """Fortran multiframe expansion wrapped in an OpenMP parallel loop."""

    DEFAULT_LOCAL_VARIABLE_CLASS = FortranLocalVariable

    def __init__(
        self,
        *,
        context,
        num_threads=None,
        local_variable_class=None,
        local_variable_capture=None,
        **buildargs,
    ):
        super().__init__(
            context=context,
            local_variable_class=local_variable_class,
            local_variable_capture=local_variable_capture,
            **buildargs,
        )
        self._num_threads = num_threads
        self.requires(ExternalImport(OMP_FORTRAN_IMPORT))

    def get_private_variables(self):
        if self._local_variable_capture is None:
            return
            yield
        for variable in self._local_variable_capture.captured:
            yield variable.name

    def generate_head_containers(self, **kwargs):
        num_threads_clause = ""
        if self._num_threads is not None:
            num_threads_clause = f" NUM_THREADS({self._num_threads})"
        private_vars = ", ".join(self.get_private_variables())
        pragma = f"!$OMP PARALLEL DO{num_threads_clause} SCHEDULE(STATIC)"
        if private_vars:
            pragma = (
                "!$OMP PARALLEL DO "
                f"PRIVATE({private_vars}){num_threads_clause} SCHEDULE(STATIC)"
            )
        yield from self.codelines_from_text(pragma)
        yield from super().generate_head_containers(**kwargs)

    def generate_foot_containers(self, **kwargs):
        yield from super().generate_foot_containers(**kwargs)
        yield from self.codelines_from_text("!$OMP END PARALLEL DO")


class OMPFortranSingleLayerResource(FortranComputeResource):
    """Fortran resource that parallelizes exactly one multiframe layer."""

    def __init__(
        self,
        descriptor="omp fortran single layer",
        *args,
        num_threads=None,
        **kwargs,
    ):
        super().__init__(descriptor=descriptor, *args, **kwargs)
        self._num_threads = num_threads

    def create_mfe_container(
        self,
        *,
        context,
        local_variable_capture=None,
        name=None,
        loop_container=None,
        loop_capture=None,
    ):
        del name, loop_container, loop_capture
        return OMPFortranParallelMultiFrameExpandContainer(
            context=context,
            num_threads=self._num_threads,
            local_variable_capture=local_variable_capture,
        )


def is_fortran_omp_resource(resource) -> bool:
    return isinstance(resource, OMPFortranSingleLayerResource)


OMP_FORTRAN_DEFAULT_RESOURCE = OMPFortranSingleLayerResource(
    descriptor="omp fortran root"
)
OMP_FORTRAN_DEFAULT_RESOURCE.append_resource_layer(
    FortranComputeResource("omp fortran fallback")
)

OMP_DEFAULT_RESOURCE = OMP_FORTRAN_DEFAULT_RESOURCE

__all__ = [
    "OMP_DEFAULT_RESOURCE",
    "OMP_FORTRAN_DEFAULT_RESOURCE",
    "OMPFortranParallelMultiFrameExpandContainer",
    "OMPFortranSingleLayerResource",
    "is_fortran_omp_resource",
]
