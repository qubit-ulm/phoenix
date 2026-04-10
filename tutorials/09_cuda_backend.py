"""
Tutorial 09: CUDA backend with host and kernel entry points.

This tutorial shows the CUDA-specific split between

1. a host-callable routine and
2. a kernel routine launched directly from Python through the CUDA wrapper.

The example deliberately keeps the numerical operation simple so the tutorial
can focus on the different call paths.
"""

from __future__ import annotations

import numpy as np
from pathlib import Path

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.backends.cuda.cuda_cupy_adaa import PROVIDE_CUPY
from phoenix.fgen.backends.cuda.cuda_builder import (
    CUDADeviceResource,
    CUDAHostResource,
)
from phoenix.fgen.instruction import (
    CallInstruction,
    InstructionGroup,
    LinearOperationInstruction,
    MapApplyInstruction,
)
from phoenix.fgen.instructionvar import (
    InstructionEnvironment,
    InstructionVariable,
)
from phoenix.keymap import Key, KeyMap

if PROVIDE_CUPY:
    import cupy as cp
    from phoenix.fgen.backends.cuda.cuda_cupy_adaa import CupyRA

    CUDA_RUNTIME_ERROR = cp.cuda.runtime.CUDARuntimeError
else:
    cp = None
    CupyRA = None
    CUDA_RUNTIME_ERROR = RuntimeError


SIZE = 4000


def adaa_classes_from_assignment_config(backend, assignment_config):
    return {
        variable: adaa_class
        for variable, (adaa_class, _status) in backend.make_daa_assignments(
            assignment_config
        ).items()
    }


def build_library():
    """Build a tiny CUDA library with one worker kernel and one host wrapper."""
    if CupyRA is None:
        raise RuntimeError("This tutorial requires CuPy to be installed.")

    # Build a scalar layout first and then a large vector on top of it. The
    # vector length is intentionally large enough that launching a kernel makes
    # conceptual sense.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    vector = KeyMap(name="vector")
    for idx in range(SIZE):
        vector.link(Key(idx), scalar)

    # ``lhs`` and ``out`` are the public variables seen by the caller, while
    # ``lhs_local`` and ``out_local`` are the variables used inside the worker
    # instruction that is executed per environment.
    lhs = InstructionVariable.new("lhs", config=vector)
    out = InstructionVariable.new("out", config=vector)
    lhs_local = InstructionVariable.new("lhs_local", config=scalar)
    out_local = InstructionVariable.new("out_local", config=scalar)

    worker_instruction = InstructionGroup(
        [
            LinearOperationInstruction(
                tgt0=out_local("value"),
                src0=lhs_local("value"),
                alpha=2.0,
            )
        ]
    )

    # Each environment maps the local worker variables to one position of the
    # global vector. ``MapApplyInstruction`` then replicates the worker over all
    # these environments.
    environments = [
        InstructionEnvironment(
            {
                lhs_local: lhs(Key(idx)),
                out_local: out(Key(idx)),
            }
        )
        for idx in range(SIZE)
    ]

    backend = get_backend("cuda")
    library = backend.library(
        "tutorial_cuda_direct", resource=CUDAHostResource()
    )
    assignment_config = {
        lhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }

    # ``double_worker`` is emitted as the device/kernel-facing routine.
    #
    # This is the routine that will actually execute on the device. The
    # ``MapApplyInstruction`` gives the backend enough structure to distribute
    # the local worker body over many vector positions.
    worker = backend.libroutine_from_instructions(
        library,
        "double_worker",
        MapApplyInstruction(
            content=worker_instruction, environments=environments
        ),
        assignment_config=assignment_config,
        resource=CUDADeviceResource(nthreads=128),
    )

    # ``double_host`` is a small host-callable routine that delegates to the
    # worker. This is the routine that ordinary host-side code would typically
    # call through a wrapper.
    #
    # Keeping both entry points in one demo helps the reader understand that a
    # CUDA backend may expose both host and kernel perspectives on the same
    # underlying computation.
    backend.libroutine_from_instructions(
        library,
        "double_host",
        CallInstruction(worker),
        assignment_config=assignment_config,
        resource=CUDAHostResource(),
    )
    return backend, library, lhs, out, assignment_config


def main() -> None:
    """Build the library and demonstrate host and direct kernel access."""
    if CupyRA is None:
        print("Tutorial 09 requires CuPy and a working CUDA toolchain.")
        return

    try:
        backend, library, lhs, out, assignment_config = build_library()
        adaa_classes = adaa_classes_from_assignment_config(
            backend, assignment_config
        )
        lhs_adaa = adaa_classes[lhs]
        out_adaa = adaa_classes[out]

        # ``wrap_library(..., build=True)`` builds the generated CUDA artifacts
        # once and then exposes multiple routine wrappers from the same library.
        #
        # That is especially useful for CUDA because host wrappers and kernel
        # wrappers naturally belong to the same generated library bundle.
        wrappers = backend.wrap_library(library, build=True)
        host_wrapper = wrappers.create_wrapper("double_host")
        kernel_wrapper = wrappers.create_wrapper("double_worker")

        lhs_data = lhs_adaa.from_numpy(np.arange(SIZE, dtype=np.float64))
        host_target = out_adaa.from_numpy(np.zeros(SIZE, dtype=np.float64))
        kernel_target = out_adaa.from_numpy(np.zeros(SIZE, dtype=np.float64))

        # The host wrapper launches the host entry point, while the kernel
        # wrapper launches the device routine directly.
        host_result = host_wrapper(lhs=lhs_data, out=host_target).to_numpy()
        kernel_result = kernel_wrapper(lhs=lhs_data, out=kernel_target).to_numpy()
    except CUDA_RUNTIME_ERROR as exc:
        print("Tutorial 09: CUDA backend")
        print("=" * 60)
        print("CUDA library generation or execution failed at runtime.")
        print("This tutorial needs a working CUDA runtime in addition to CuPy.")
        print("Failure:", exc)
        return

    expected = np.arange(SIZE) * 2.0

    print("Tutorial 09: CUDA backend")
    print("=" * 60)
    print("Backend identifier :", backend.IDENTIFIER)
    print("Generated source   :", Path(library.filename).resolve())
    print("Shared library     :", Path(library.sharedlibname).resolve())
    print("Kernel module      :", Path(library.kernelmodulename).resolve())
    print("Host matches       :", np.allclose(host_result, expected))
    print("Kernel matches     :", np.allclose(kernel_result, expected))


if __name__ == "__main__":
    main()
