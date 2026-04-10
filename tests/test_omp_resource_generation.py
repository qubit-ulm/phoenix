from __future__ import annotations

from pathlib import Path

from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.instruction import (
    BiLinearOperationInstruction,
    InstructionGroup,
    MapApplyInstruction,
)
from phoenix.fgen.instructionvar import InstructionEnvironment, InstructionVariable
from phoenix.fgen.backends.c.c_resource import (
    OMPCSingleLayerResource,
)
from phoenix.fgen.backends.fortran.fortran_resource import (
    OMPFortranSingleLayerResource,
)
from phoenix.keymap import Key, KeyMap


def make_parallel_case():
    scalar = KeyMap(name="scalar")
    scalar.entry("value")

    vector = KeyMap(name="vector")
    for idx in range(4):
        vector.link(Key(idx), scalar)

    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)

    lhs_s = InstructionVariable.new("lhs_s", config=scalar)
    rhs_s = InstructionVariable.new("rhs_s", config=scalar)
    out_s = InstructionVariable.new("out_s", config=scalar)

    content = InstructionGroup(
        [
            BiLinearOperationInstruction(
                tgt0=out_s("value"),
                src0=lhs_s("value"),
                src1=rhs_s("value"),
                alpha=1.0,
            )
        ]
    )
    environments = [
        InstructionEnvironment(
            {
                lhs_s: lhs(Key(idx)),
                rhs_s: rhs(Key(idx)),
                out_s: out(Key(idx)),
            }
        )
        for idx in range(4)
    ]
    instruction = MapApplyInstruction(content=content, environments=environments)
    assignments = {
        lhs: Config(status="R", family="real"),
        rhs: Config(status="R", family="real"),
        out: Config(status="RW", family="real"),
    }
    return instruction, assignments


def build_source(tmp_path, backend_name, *, backend_config=None, general=None, resource=None):
    instruction, assignments = make_parallel_case()
    backend = get_backend(backend_name).configure(
        backend=backend_config or {},
        general={"paths": {"build_root": str(tmp_path)}, **(general or {})},
    )
    library = backend.library(f"{backend_name}_omp_generation")
    backend.libroutine_from_instructions(
        library,
        "multiply",
        instruction,
        assignment_config=assignments,
        resource=resource,
        resource_name=None if resource is not None else "omp",
    )
    library.build(force=True, compile=False)
    return Path(library.relative_to_basepath(library.filename)).read_text()


def test_fortran_omp_pragma_uses_backend_thread_configuration(tmp_path):
    generated = build_source(
        tmp_path,
        "fortran",
        backend_config={"omp": {"num_cores": 6}},
        general={"runtime": {"num_processors": 2}},
    )

    assert "!$OMP PARALLEL DO" in generated
    assert "NUM_THREADS(6)" in generated
    assert generated.count("!$OMP PARALLEL DO") == 1


def test_c_omp_pragma_falls_back_to_general_num_processors(tmp_path):
    generated = build_source(
        tmp_path,
        "c",
        general={"runtime": {"num_processors": 5}},
    )

    assert "#pragma omp parallel for" in generated
    assert "num_threads(5)" in generated
    assert generated.count("#pragma omp parallel for") == 1


def test_nested_omp_resources_keep_per_layer_thread_counts():
    outer = OMPFortranSingleLayerResource("outer omp", num_threads=3)
    inner = OMPFortranSingleLayerResource("inner omp", num_threads=2, outer_layer=outer)

    assert inner is outer.next_layer
    assert outer._num_threads == 3
    assert inner._num_threads == 2


def test_default_omp_resource_stays_single_layer_with_serial_fallback():
    backend = get_backend("fortran").configure(
        backend={"omp": {"num_cores": 4}},
    )

    resource = backend.create_resource("omp")

    assert isinstance(resource, OMPFortranSingleLayerResource)
    assert resource.next_layer is not None
    assert not isinstance(resource.next_layer, OMPFortranSingleLayerResource)


def test_c_nested_omp_resources_keep_per_layer_thread_counts():
    outer = OMPCSingleLayerResource("outer omp", num_threads=7)
    inner = OMPCSingleLayerResource("inner omp", num_threads=4, outer_layer=outer)

    assert inner is outer.next_layer
    assert outer._num_threads == 7
    assert inner._num_threads == 4
