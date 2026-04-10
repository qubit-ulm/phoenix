from __future__ import annotations

__doc__ = """C backend compute-resource helpers, including OpenMP resources."""

from .c_builder import (
    CComputeResource,
    CLocalVariable,
    CMultiFrameExpandContainer,
)
from ..openmp_support import (
    ExternalImport,
    OMP_C_IMPORT,
)


class OMPCParallelMultiFrameExpandContainer(CMultiFrameExpandContainer):
    """C multiframe expansion wrapped in an OpenMP parallel loop."""

    DEFAULT_LOCAL_VARIABLE_CLASS = CLocalVariable

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
        self.requires(ExternalImport(OMP_C_IMPORT))

    def get_private_variables(self):
        if self._local_variable_capture is None:
            return
            yield
        for variable in self._local_variable_capture.captured:
            yield variable.name

    def generate_head_containers(self, **kwargs):
        num_threads_clause = ""
        if self._num_threads is not None:
            num_threads_clause = f" num_threads({self._num_threads})"
        private_vars = ", ".join(self.get_private_variables())
        pragma = f"#pragma omp parallel for{num_threads_clause} schedule(static)"
        if private_vars:
            pragma = (
                "#pragma omp parallel for "
                f"private({private_vars}){num_threads_clause} schedule(static)"
            )
        yield from self.codelines_from_text(pragma)
        yield from super().generate_head_containers(**kwargs)


class OMPCSingleLayerResource(CComputeResource):
    """C resource that parallelizes exactly one multiframe layer."""

    def __init__(
        self,
        descriptor="omp c single layer",
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
        return OMPCParallelMultiFrameExpandContainer(
            context=context,
            num_threads=self._num_threads,
            local_variable_capture=local_variable_capture,
        )


def is_c_omp_resource(resource) -> bool:
    return isinstance(resource, OMPCSingleLayerResource)


OMP_C_DEFAULT_RESOURCE = OMPCSingleLayerResource(descriptor="omp c root")
OMP_C_DEFAULT_RESOURCE.append_resource_layer(CComputeResource("omp c fallback"))

__all__ = [
    "OMP_C_DEFAULT_RESOURCE",
    "OMPCParallelMultiFrameExpandContainer",
    "OMPCSingleLayerResource",
    "is_c_omp_resource",
]
