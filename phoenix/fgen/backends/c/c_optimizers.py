from __future__ import annotations

__doc__ = """C backend optimizers, including OpenMP atomic-region lowering."""

from ...atomic import AtomicRegionInstruction
from ...buildchain import Optimizer
from ...instruction import (
    ContentInstruction,
    EnvironmentInstruction,
    Instruction,
    InstructionGroup,
    LeafInstruction,
    MapApplyInstruction,
)
from .c_atomic import CAtomicInstruction
from .c_resource import is_c_omp_resource


class COmpAtomicOptimizer(Optimizer, identifier="c_omp_atomic"):
    """Resolve atomic leaf wrapping for C OpenMP resources."""

    def apply(self, instruction: Instruction, **extra_args):
        return self._rewrite(
            instruction,
            parallel=is_c_omp_resource(extra_args.get("resource")),
        )

    def _rewrite(self, instruction: Instruction, *, parallel: bool):
        if isinstance(instruction, CAtomicInstruction):
            return instruction
        if isinstance(instruction, AtomicRegionInstruction):
            inner = self._rewrite(instruction.content, parallel=parallel)
            if instruction.policy == "off" or not parallel:
                return inner
            if instruction.attachment_mode == "leaf":
                distributed = self._distribute(instruction.content, parallel=parallel)
                if distributed is not None:
                    return distributed
            return CAtomicInstruction(
                inner,
                attachment_mode="region",
                itype=instruction.itype,
            )
        if isinstance(instruction, InstructionGroup):
            return type(instruction)(
                [
                    self._rewrite(child, parallel=parallel)
                    for child in instruction.instructions
                ],
                itype=instruction.itype,
            )
        if isinstance(instruction, MapApplyInstruction):
            return type(instruction)(
                self._rewrite(instruction.content, parallel=parallel),
                environments=list(instruction.environments),
                itype=instruction.itype,
            )
        if isinstance(instruction, EnvironmentInstruction):
            return type(instruction)(
                self._rewrite(instruction.content, parallel=parallel),
                environment=instruction.environment,
                itype=instruction.itype,
            )
        if type(instruction) is ContentInstruction:
            return type(instruction)(
                self._rewrite(instruction.content, parallel=parallel),
                itype=instruction.itype,
            )
        return instruction

    def _distribute(self, instruction: Instruction, *, parallel: bool):
        if isinstance(instruction, AtomicRegionInstruction):
            return self._rewrite(instruction, parallel=parallel)
        if isinstance(instruction, LeafInstruction):
            return CAtomicInstruction(
                instruction,
                attachment_mode="leaf",
                itype=instruction.itype,
            )
        if isinstance(instruction, InstructionGroup):
            distributed = []
            for child in instruction.instructions:
                rewritten_child = self._distribute(child, parallel=parallel)
                if rewritten_child is None:
                    return None
                distributed.append(rewritten_child)
            return type(instruction)(distributed, itype=instruction.itype)
        if isinstance(instruction, MapApplyInstruction):
            content = self._distribute(instruction.content, parallel=parallel)
            if content is None:
                return None
            return type(instruction)(
                content,
                environments=list(instruction.environments),
                itype=instruction.itype,
            )
        if isinstance(instruction, EnvironmentInstruction):
            content = self._distribute(instruction.content, parallel=parallel)
            if content is None:
                return None
            return type(instruction)(
                content,
                environment=instruction.environment,
                itype=instruction.itype,
            )
        if type(instruction) is ContentInstruction:
            content = self._distribute(instruction.content, parallel=parallel)
            if content is None:
                return None
            return type(instruction)(content, itype=instruction.itype)
        return None


__all__ = ["COmpAtomicOptimizer"]
