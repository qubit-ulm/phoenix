from __future__ import annotations

import copy

import pytest

from phoenix.fgen.instruction import (
    InstructionGroup,
    LinearOperationInstruction,
    MapApplyInstruction,
)
from phoenix.fgen.instructionvar import (
    InstructionEnvironment,
    InstructionScalar,
    InstructionVariable,
    KeyOffset,
    StringOffset,
    SymbolicOffset,
)
from phoenix.keymap import Key, KeyMap


def make_vector_variables():
    scalar = KeyMap(name="scalar")
    scalar.entry("value")
    scalar.entry("aux")

    vector = KeyMap(name="vector")
    vector.link("left", scalar)
    vector.link("right", scalar)

    lhs = InstructionVariable.new("lhs", config=vector)
    rhs = InstructionVariable.new("rhs", config=vector)
    out = InstructionVariable.new("out", config=vector)
    return scalar, vector, lhs, rhs, out


def test_instruction_variable_progress_evaluates_key_offsets():
    _scalar, _vector, lhs, _rhs, _out = make_vector_variables()

    progressed = lhs("left", "aux")

    assert isinstance(progressed.plain_offsets[0], KeyOffset)
    assert progressed.offsets == [0, 1]
    assert str(progressed) == "<lhs@(+left:+aux)>"


def test_instruction_variable_fuse_and_symbolic_offsets():
    _scalar, _vector, lhs, _rhs, _out = make_vector_variables()
    left = lhs("left")
    symbolic = SymbolicOffset("dynamic_index", input_config=left.output_config)
    fused = left | type(lhs())(
        symbolic,
        input_config=left.output_config,
        output_config=left.output_config,
    )

    assert fused.offsets == [0, "dynamic_index"]
    symbolic.substitute("thread_idx")
    assert fused.offsets == [0, "thread_idx"]


def test_instruction_environment_merge_and_fuse():
    _scalar, _vector, lhs, rhs, _out = make_vector_variables()
    base = InstructionEnvironment({lhs: lhs("left")})
    inner = InstructionEnvironment({rhs: rhs("right")})

    merged = base.merge(inner)
    fused = base | inner

    assert merged[lhs].offsets == [0]
    assert merged[rhs].offsets == [2]
    assert fused[lhs].offsets == [0]
    assert fused[rhs].offsets == [2]


def test_instruction_group_wraps_nested_lists_and_deepcopies():
    _scalar, _vector, lhs, rhs, out = make_vector_variables()
    leaf = LinearOperationInstruction(
        tgt0=out("left", "value"),
        src0=lhs("left", "value"),
        alpha=2.0,
    )
    nested = InstructionGroup([[leaf]])
    cloned = copy.deepcopy(nested)

    assert isinstance(next(iter(nested.instructions)), InstructionGroup)
    assert len(nested) == 1
    assert cloned is not nested
    assert cloned.record_payload(detailed=True)["count"] == 1


def test_mapapply_walk_expands_environments():
    scalar, _vector, lhs, _rhs, out = make_vector_variables()
    local_in = InstructionVariable.new("local_in", config=scalar)
    local_out = InstructionVariable.new("local_out", config=scalar)
    content = InstructionGroup(
        [
            LinearOperationInstruction(
                tgt0=local_out("value"),
                src0=local_in("value"),
                alpha=1.0,
            )
        ]
    )
    mapped = MapApplyInstruction(
        content=content,
        environments=[
            InstructionEnvironment({local_in: lhs("left"), local_out: out("left")}),
            InstructionEnvironment({local_in: lhs("right"), local_out: out("right")}),
        ],
    )

    walked = list(mapped.walk(include_control=False))

    assert len(mapped) == 2
    assert len(walked) == 2
    assert all(item[2].ftype.endswith("linear") for item in walked)


def test_instruction_scalar_generalization_and_string_offsets():
    assert InstructionScalar.generalize("I", "F") == "F"
    assert InstructionScalar.generalize("C", "F", "I") == "C"
    literal = StringOffset("thread_idx")

    assert literal.compute()[0] == "thread_idx"
    literal.replace_expression("lane_idx")
    assert literal.compute()[0] == "lane_idx"


def test_instruction_group_append_accepts_compatible_linear_instruction():
    _scalar, _vector, lhs, rhs, out = make_vector_variables()
    group = InstructionGroup(
        [
            LinearOperationInstruction(
                tgt0=out("left", "value"),
                src0=lhs("left", "value"),
                alpha=1.0,
            )
        ]
    )

    group.append(
        LinearOperationInstruction(
            tgt0=out("right", "value"),
            src0=rhs("right", "value"),
            alpha=1.0,
        )
    )

    assert len(list(group.instructions)) == 2
