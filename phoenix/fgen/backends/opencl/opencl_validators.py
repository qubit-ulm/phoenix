"""OpenCL-specific build validators."""

from __future__ import annotations

from ...buildchain import (
    ValidationError,
    Validator,
    iter_instruction_nodes,
)
from .opencl_builder import OpenCLDeviceResource
from ...instruction import CallInstruction


class OpenCLKernelRoutineCallValidator(
    Validator, identifier="opencl_kernel_no_kernel_call"
):
    """Reject nested kernel calls when compiling for OpenCL device resources."""

    def validate(self, instruction, report, **extra_args):
        resource = extra_args.get("resource")
        if not isinstance(resource, OpenCLDeviceResource):
            return True, None
        bad_calls = []
        for _parent, node, level in iter_instruction_nodes(instruction):
            if not isinstance(node, CallInstruction):
                continue
            routine = node.routine
            container = getattr(routine, "container", None)
            if bool(getattr(container, "is_kernel", False)):
                bad_calls.append(
                    {
                        "level": level,
                        "routine": getattr(routine, "name", repr(routine)),
                    }
                )
        report[self.identifier] = bad_calls
        if bad_calls:
            return False, bad_calls
        return True, None

    def handle_fail(self, details, report, **extra_args):
        del report, extra_args
        return ValidationError(
            "kernel-capable OpenCL resources must not call other kernel routines: "
            f"{details}"
        )


__all__ = ["OpenCLKernelRoutineCallValidator"]
