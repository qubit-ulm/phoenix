from __future__ import annotations

__doc__ = """CUDA atomic lowering hooks and handler registration."""

from ...atomic import AtomicRegionInstruction


def _handle_cuda_atomic_region_instruction(self, instruction, context, buildargs):
    from .cuda_builder import CUDADeviceResource

    resource = buildargs.get("resource")
    if instruction.policy == "off" or not isinstance(resource, CUDADeviceResource):
        yield from self.containers_from_instruction(
            instruction.content,
            context=context,
            **buildargs,
        )
        return
    raise ValueError(
        "CUDA atomic region lowering is not implemented yet; "
        "use policy='off' or a non-device resource."
    )


def register_cuda_atomic_handlers(builder_class) -> None:
    builder_class.set_instruction_class_handler(
        AtomicRegionInstruction,
        _handle_cuda_atomic_region_instruction,
    )


__all__ = ["register_cuda_atomic_handlers"]
