"""
Demo 04b: benchmark serial and OpenMP Fortran routines on a scaled-up problem.

This demo takes the resource idea from ``04a`` one step further. Instead of
only previewing generated source code, it actually builds one benchmark library
and times several routines from it:

1. one serial routine,
2. one OpenMP routine fixed to 2 threads,
3. one OpenMP routine fixed to 4 threads,
4. and one OpenMP routine fixed to 8 threads.

The generated math is still intentionally simple. The pedagogical point is to
show how the same symbolic routine can be registered several times with
different resource settings and then compared quantitatively.

The benchmark excludes code-generation and compilation time. Only the wrapped
routine calls are timed.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import statistics
import time

import numpy as np

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import (
    BiLinearOperationInstruction,
    InstructionGroup,
    MapApplyInstruction,
)
from phoenix.fgen.instructionvar import (
    InstructionEnvironment,
    InstructionVariable,
)
from phoenix.keymap import Key, KeyMap


DEFAULT_THREAD_COUNTS = (2, 4, 8)


def parse_thread_counts(raw: str) -> tuple[int, ...]:
    """
    Parse a comma-separated thread list from the command line.

    The benchmark only makes sense for positive thread counts, so we validate
    that here once instead of scattering small checks throughout the script.
    """

    values = []
    for part in raw.split(","):
        stripped = part.strip()
        if not stripped:
            continue
        value = int(stripped)
        if value < 1:
            raise ValueError("thread counts must be positive integers")
        values.append(value)
    if not values:
        raise ValueError("at least one thread count must be selected")
    return tuple(dict.fromkeys(values))


def build_blocked_benchmark_case(num_blocks: int, block_size: int):
    """
    Build one block-structured multiply routine for the benchmark.

    The layout is intentionally two-level:

    - ``block`` holds one contiguous chunk of scalar entries,
    - ``grouped`` repeats that block ``num_blocks`` times.

    ``MapApplyInstruction`` is then used to apply one block-local worker body
    to all blocks. That gives the Fortran/OpenMP backend an outer dimension it
    can parallelize cleanly.
    """

    # ``scalar`` is the leaf domain used by every block entry.
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    # ``block`` is one local work package processed by the mapped worker body.
    block = KeyMap(name=f"benchmark_block_{block_size}")
    for idx in range(block_size):
        block.link(Key(idx), scalar)

    # ``grouped`` repeats that block layout many times. This is the dimension
    # across which the OpenMP version can distribute work.
    grouped = KeyMap(name=f"benchmark_grouped_{num_blocks}x{block_size}")
    for block_idx in range(num_blocks):
        grouped.link(Key(block_idx), block)

    # Public routine arguments live on the grouped layout.
    lhs = InstructionVariable.new("lhs", config=grouped)
    rhs = InstructionVariable.new("rhs", config=grouped)
    out = InstructionVariable.new("out", config=grouped)

    # Local worker variables live on one block only. They are mapped onto the
    # public grouped variables through one environment per block.
    lhs_block = InstructionVariable.new("lhs_block", config=block)
    rhs_block = InstructionVariable.new("rhs_block", config=block)
    out_block = InstructionVariable.new("out_block", config=block)

    # The worker body performs an elementwise multiply inside one block.
    worker = InstructionGroup(
        [
            BiLinearOperationInstruction(
                tgt0=out_block(Key(idx), "value"),
                src0=lhs_block(Key(idx), "value"),
                src1=rhs_block(Key(idx), "value"),
                alpha=1.0,
            )
            for idx in range(block_size)
        ]
    )

    # ``MapApplyInstruction`` replicates that local worker once per block.
    mapped = MapApplyInstruction(
        content=worker,
        environments=[
            InstructionEnvironment(
                {
                    lhs_block: lhs(Key(block_idx)),
                    rhs_block: rhs(Key(block_idx)),
                    out_block: out(Key(block_idx)),
                }
            )
            for block_idx in range(num_blocks)
        ],
    )

    assignments = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }
    return {
        "instruction_tree": mapped,
        "assignments": assignments,
        "lhs": lhs,
        "rhs": rhs,
        "out": out,
        "size": len(grouped),
    }


def build_benchmark_library(
    *,
    num_blocks: int,
    block_size: int,
    thread_counts: tuple[int, ...],
    build_root: Path,
):
    """
    Register one serial and several OpenMP routines into one Fortran library.

    Each OpenMP routine is created by a backend instance whose general
    configuration exposes a different ``runtime.num_processors`` value. Because
    the OpenMP resource emits ``NUM_THREADS(...)`` directly, every generated
    routine carries its own requested thread count in the pragma.
    """

    case = build_blocked_benchmark_case(num_blocks, block_size)

    serial_backend = get_backend("fortran").configure(
        general={"paths": {"build_root": str(build_root)}}
    )
    library = serial_backend.library(
        f"demo_parallel_benchmark_b{num_blocks}_s{block_size}"
    )

    # Register the serial reference routine first. All speedups are measured
    # relative to this one.
    serial_backend.libroutine_from_instructions(
        library,
        "multiply_serial",
        case["instruction_tree"],
        assignment_config=case["assignments"],
        resource_name="serial",
    )

    # Register one OpenMP variant per selected thread count.
    for threads in thread_counts:
        omp_backend = serial_backend.configure(
            general={"runtime": {"num_processors": threads}}
        )
        omp_backend.libroutine_from_instructions(
            library,
            f"multiply_omp_{threads}",
            case["instruction_tree"],
            assignment_config=case["assignments"],
            resource_name="omp",
        )

    return serial_backend, library, case


def build_runtime_inputs(backend, case):
    """
    Construct deterministic benchmark inputs in the backend's ADAA format.

    The numerical work is just elementwise multiplication, so the expected
    NumPy reference is simply ``lhs * rhs`` on the flat host arrays.
    """

    daa_assignments = backend.make_daa_assignments(case["assignments"])
    lhs_class, _ = daa_assignments[case["lhs"]]
    rhs_class, _ = daa_assignments[case["rhs"]]
    out_class, _ = daa_assignments[case["out"]]

    # The values are chosen deterministically so repeated runs are comparable.
    lhs_host = np.linspace(0.5, 2.5, case["size"], dtype=np.float64)
    rhs_host = np.linspace(1.5, 3.5, case["size"], dtype=np.float64)
    expected = lhs_host * rhs_host

    lhs_data = lhs_class.from_numpy(lhs_host)
    rhs_data = rhs_class.from_numpy(rhs_host)
    out_data = out_class.from_numpy(np.zeros(case["size"], dtype=np.float64))

    return {
        "lhs_host": lhs_host,
        "rhs_host": rhs_host,
        "expected": expected,
        "lhs_data": lhs_data,
        "rhs_data": rhs_data,
        "out_data": out_data,
    }


def validate_wrapper(wrapper, runtime_inputs) -> bool:
    """
    Run one wrapper once and compare its result against the NumPy reference.

    The validation is done before timing so benchmark failures show up as
    correctness errors instead of misleading performance numbers.
    """

    runtime_inputs["out_data"].to_zero()
    wrapper(
        lhs=runtime_inputs["lhs_data"],
        rhs=runtime_inputs["rhs_data"],
        out=runtime_inputs["out_data"],
    )
    result = runtime_inputs["out_data"].to_numpy(cache=False)
    return np.allclose(result, runtime_inputs["expected"])


def benchmark_wrapper(
    wrapper,
    runtime_inputs,
    *,
    repeats: int,
    warmup: int,
) -> float:
    """
    Time one wrapper and return the median runtime.

    The same prepared ADAA objects are reused across repetitions so the timing
    reflects routine execution rather than repeated data construction.
    """

    timings = []

    # A few warmup calls help the dynamic loader, caches, and wrapper path
    # settle before we start measuring.
    for _ in range(warmup):
        runtime_inputs["out_data"].to_zero()
        wrapper(
            lhs=runtime_inputs["lhs_data"],
            rhs=runtime_inputs["rhs_data"],
            out=runtime_inputs["out_data"],
        )

    for _ in range(repeats):
        runtime_inputs["out_data"].to_zero()
        start = time.perf_counter()
        wrapper(
            lhs=runtime_inputs["lhs_data"],
            rhs=runtime_inputs["rhs_data"],
            out=runtime_inputs["out_data"],
        )
        timings.append(time.perf_counter() - start)

    return statistics.median(timings)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark serial and OpenMP Fortran routines."
    )
    parser.add_argument(
        "--num-blocks",
        default=2048,
        type=int,
        help="number of mapped blocks in the benchmark problem",
    )
    parser.add_argument(
        "--block-size",
        default=128,
        type=int,
        help="number of scalar entries per block",
    )
    parser.add_argument(
        "--threads",
        default="2,4,8",
        help="comma-separated OpenMP thread counts",
    )
    parser.add_argument(
        "--repeats",
        default=7,
        type=int,
        help="number of measured repetitions per routine",
    )
    parser.add_argument(
        "--warmup",
        default=2,
        type=int,
        help="number of warmup calls per routine",
    )
    args = parser.parse_args()

    thread_counts = parse_thread_counts(args.threads)
    build_root = Path(__file__).with_name("generated_parallel_benchmark")
    build_root.mkdir(parents=True, exist_ok=True)

    # Generate and compile the benchmark library once.
    serial_backend, library, case = build_benchmark_library(
        num_blocks=args.num_blocks,
        block_size=args.block_size,
        thread_counts=thread_counts,
        build_root=build_root,
    )

    # Build the wrapped library and prepare the benchmark inputs.
    wrappers = serial_backend.wrap_library(library, build=True)
    runtime_inputs = build_runtime_inputs(serial_backend, case)

    routine_names = ["multiply_serial", *[f"multiply_omp_{n}" for n in thread_counts]]
    results = []

    # Validate every routine first, then benchmark it.
    for name in routine_names:
        wrapper = wrappers.create_wrapper(name)
        ok = validate_wrapper(wrapper, runtime_inputs)
        if not ok:
            raise RuntimeError(f"validation failed for benchmark routine {name!r}")
        median_runtime = benchmark_wrapper(
            wrapper,
            runtime_inputs,
            repeats=args.repeats,
            warmup=args.warmup,
        )
        results.append((name, median_runtime))

    serial_time = dict(results)["multiply_serial"]

    print("Demo 04b: parallel benchmark")
    print("=" * 72)
    print("Generated library :", Path(library.relative_to_basepath(library.filename)))
    print("Problem size      :", f"{args.num_blocks} blocks x {args.block_size} entries")
    print("Total entries     :", case["size"])
    print("Warmup / repeats  :", f"{args.warmup} / {args.repeats}")
    print()
    print(f"{'routine':<20}{'median [s]':<16}{'speedup vs serial':<20}")
    print("-" * 56)
    for name, runtime in results:
        speedup = serial_time / runtime if runtime > 0 else float("inf")
        print(f"{name:<20}{runtime:<16.6f}{speedup:<20.3f}")


if __name__ == "__main__":
    main()
