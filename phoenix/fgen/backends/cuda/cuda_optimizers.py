from __future__ import annotations

__doc__ = """CUDA backend optimizers and atomic-lowering placeholders."""

from ...buildchain import Optimizer


class CUDAAtomicOptimizer(Optimizer, identifier="cuda_atomic"):
    """Placeholder CUDA atomic optimizer."""

    def apply(self, instruction, **extra_args):
        del extra_args
        return instruction


__all__ = ["CUDAAtomicOptimizer"]
