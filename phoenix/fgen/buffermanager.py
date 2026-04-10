"""
Experimental buffer helpers for staged reduction of parallel write targets.

This module intentionally stays outside the generic instruction module for now.
It is a mostly direct extraction of the ``BufferManager`` prototype from the
``comm_3p`` test stage. The user remains responsible for explicitly placing
buffered targets into the instruction tree and wiring the corresponding
environments.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from ..adaas import STATUS_BUFFER, STATUS_INOUT
from .instruction import (
    AccumulateOperationInstruction,
    EnvironmentInstruction,
    Instruction,
    InstructionGroup,
    MapApplyInstruction,
)
from .instructionvar import (
    InstructionEnvironment,
    InstructionVariable,
    KeyOffset,
)
from ..keymap import Entry, KeyMap


class BufferManager:
    """Track buffer variables and reduction/copy instructions for one target."""

    def __init__(
        self,
        variable,
        output_config=None,
        name=None,
        inner_buffer=None,
        is_leaf=None,
    ):
        if name is None:
            name = f"buff_{variable._name}"
        if output_config is None and inner_buffer is not None:
            output_config = inner_buffer.keymap
        self._name = name
        self._variable = variable
        self._output_config = output_config

        self._dynamic_keymap = KeyMap(name=f"{name}_dynamic")
        self._buffer_tgt = InstructionVariable.new(
            name=name,
            config=self._dynamic_keymap,
            is_buffer=True,
        )
        self._buffer_aux = InstructionVariable.new(
            name=name + "_p",
            config=self._dynamic_keymap,
            is_buffer=True,
        )
        self._memory = {}

        self._name = self._buffer_tgt._name
        self._adaa = None
        self._next = inner_buffer
        if is_leaf is None and inner_buffer is not None:
            is_leaf = False
        self._is_leaf = is_leaf

    @property
    def buffer(self):
        return self._buffer_tgt

    @property
    def auxbuf(self):
        return self._buffer_aux

    @property
    def variable(self):
        return self._variable

    @property
    def name(self):
        return self._name

    @property
    def keymap(self):
        return self._dynamic_keymap

    @property
    def size(self):
        return len(self._dynamic_keymap)

    @property
    def buffered(self):
        for offset, buffered_list in self._memory.items():
            for buffered in buffered_list:
                yield offset, buffered

    def _normalize_offsets(self, offsets: tuple[Any, ...] | list[Any] | Any):
        if isinstance(offsets, tuple):
            if len(offsets) == 1:
                return offsets[0]
            return offsets
        if isinstance(offsets, list):
            if len(offsets) == 1:
                return offsets[0]
            return tuple(offsets)
        return offsets

    def register(self, offsets):
        """
        Add one offset combination to the buffer and return the buffered target.
        """
        target = self._variable(offsets)
        if offsets not in self._memory:
            self._memory[offsets] = []
        enumerator = len(self._memory[offsets])
        if self._output_config is None:
            output_config = target.output_config
        else:
            output_config = self._output_config
        if self._is_leaf is None:
            self._is_leaf = isinstance(output_config, Entry)
        self._dynamic_keymap.link(
            (offsets, enumerator),
            domain=output_config,
        )
        extended_offset = (offsets, enumerator)
        buffered_variable = self._buffer_tgt(
            KeyOffset(
                extended_offset,
                keymap=None,
                out_config=output_config,
            ),
            input_config=self._dynamic_keymap,
            output_config=output_config,
            _pure_copy=True,
        )
        self._memory[offsets].append(extended_offset)
        return buffered_variable

    def __call__(self, *offsets):
        return self.register(*offsets)

    def set_adaa(
        self, adaa_class=None, force_overwrite=False, exception_existing=True
    ):
        if adaa_class is None:
            raise ValueError("No ADAA class provided")
        if self._adaa is None or force_overwrite:
            self._adaa = adaa_class.set_keymap(self._dynamic_keymap)
        elif exception_existing:
            raise ValueError("ADAA is already set up")
        return self._adaa

    def assignments(self, adaa_class=None, status=STATUS_INOUT | STATUS_BUFFER):
        if self._adaa is None:
            self.set_adaa(adaa_class)
        assignments = {
            self._buffer_tgt: (self._adaa, status),
            self._buffer_aux: (self._adaa, status),
        }
        if self._next is not None:
            assignments.update(self._next.assignments(adaa_class, status))
        return assignments

    def _clone_assignment_config(self, base_spec, *, status, layout):
        from .backends.backend import AssignmentConfig, Config
        if isinstance(base_spec, AssignmentConfig):
            config = base_spec
        elif isinstance(base_spec, dict):
            config = Config(**base_spec)
        elif isinstance(base_spec, str):
            config = Config(status=base_spec)
        else:
            raise TypeError(
                "buffer assignment base spec must be a status string, "
                "AssignmentConfig, or dict"
            )
        return replace(
            config,
            status=status,
            is_buffer=True,
            layout=layout,
            options=dict(config.options) if config.options is not None else None,
        )

    def assignment_configs(
        self, assignment_config_map, *, status="B", _inherited_base_spec=None
    ):
        """
        Return backend ``Config`` specs for this buffer hierarchy.

        The returned mapping can be merged directly with ordinary
        instruction-variable assignment configs and resolved via
        ``backend.make_daa_assignments(...)``.
        """
        if self._variable in assignment_config_map:
            effective_base_spec = assignment_config_map[self._variable]
        elif _inherited_base_spec is not None:
            effective_base_spec = _inherited_base_spec
        else:
            raise KeyError(
                f"buffered variable {self._variable.get_name()!r} has no base "
                f"assignment config"
            )

        configs = {
            self._buffer_tgt: self._clone_assignment_config(
                effective_base_spec,
                status=status,
                layout=self._dynamic_keymap,
            ),
            self._buffer_aux: self._clone_assignment_config(
                effective_base_spec,
                status=status,
                layout=self._dynamic_keymap,
            ),
        }
        if self._next is not None:
            configs.update(
                self._next.assignment_configs(
                    assignment_config_map=assignment_config_map,
                    status=status,
                    _inherited_base_spec=effective_base_spec,
                )
            )
        return configs

    def handle_reduction(self, memory=None):
        if memory is None:
            memory = self._memory
        while True:
            memory, reduction_steps = self.reduction_step(memory)
            if len(reduction_steps) < 1:
                break
            yield reduction_steps

    @staticmethod
    def reduction_step(memory):
        new_memory = {}
        reduction_steps = []
        if memory is None:
            raise ValueError("No buffer memory found")

        maxlen = max((len(group) for group in memory.values()))
        nextpow2 = int(math.log2(maxlen - 0.1))
        stepdist = 2**nextpow2

        for key, ext_keys in memory.items():
            num_targets = len(ext_keys)
            new_memory[key] = []
            for num in range(min(stepdist, num_targets)):
                new_memory[key].append(ext_keys[num])
                if num + stepdist < num_targets:
                    reduction_steps.append(
                        (ext_keys[num], ext_keys[num + stepdist])
                    )
        return new_memory, reduction_steps

    def handle_copy(self, memory=None):
        if memory is None:
            memory = self._memory
        grouped = []
        for key, targets in memory.items():
            grouped.append((targets[0], key))
        return grouped

    def create_mapapply_instruction(self, content, environments):
        return MapApplyInstruction(content=content, environments=environments)

    def create_environment(self, *pairs):
        instruction_env = InstructionEnvironment()
        for inner, offset in pairs:
            instruction_env.update(inner, offset)
        return instruction_env

    def create_accumulate_instruction(self, tgt, src):
        return AccumulateOperationInstruction(tgt, src)

    def generate_in_buffer_additions(self):
        if self._next is None:
            instructions = []
            for _offset, buffered in self._memory.items():
                in_buffer_off = buffered[0]
                instructions.append(
                    self.create_accumulate_instruction(
                        self._buffer_tgt(in_buffer_off),
                        self._buffer_aux(in_buffer_off),
                    )
                )
            yield InstructionGroup(instructions)
            return

        environments = []
        for _offset, buffered in self._memory.items():
            in_buffer_off = buffered[0]
            environments.append(
                self.create_environment(
                    (self._next.buffer, self._buffer_tgt(in_buffer_off)),
                    (self._next.auxbuf, self._buffer_aux(in_buffer_off)),
                )
            )
        for content in self._next.generate_in_buffer_additions():
            yield self.create_mapapply_instruction(content, environments)

    def generate_reduction_operators(self):
        if self._next is None:
            for redux_keys in self.handle_reduction():
                instructions = []
                for tgt_key, src_key in redux_keys:
                    instructions.append(
                        self.create_accumulate_instruction(
                            self._buffer_tgt(tgt_key),
                            self._buffer_tgt(src_key),
                        )
                    )
                yield InstructionGroup(instructions)
            return

        environments = []
        for buffered_keys in self._memory.values():
            for buffered_key in buffered_keys:
                environments.append(
                    self.create_environment(
                        (
                            self._next.buffer,
                            self._buffer_tgt(buffered_key),
                        ),
                    )
                )
        for content in self._next.generate_reduction_operators():
            yield self.create_mapapply_instruction(content, environments)

        for redux_keys in self.handle_reduction():
            environments = []
            for tgt_key, src_key in redux_keys:
                environments.append(
                    self.create_environment(
                        (
                            self._next.buffer,
                            self._buffer_tgt(tgt_key),
                        ),
                        (
                            self._next.auxbuf,
                            self._buffer_tgt(src_key),
                        ),
                    )
                )
            for content in self._next.generate_in_buffer_additions():
                yield self.create_mapapply_instruction(content, environments)

    def generate_copy_operators(self):
        if self._next is None:
            instructions = []
            for offset, buffered_keys in self._memory.items():
                instructions.append(
                    self.create_accumulate_instruction(
                        self._variable(offset),
                        self._buffer_tgt(buffered_keys[0]),
                    )
                )
            yield InstructionGroup(instructions)
            return

        environments = []
        for offset, buffered_keys in self._memory.items():
            in_buffer_off = buffered_keys[0]
            environments.append(
                self.create_environment(
                    (
                        self._next.buffer,
                        self._buffer_tgt(in_buffer_off),
                    ),
                    (
                        self._next.variable,
                        self._variable(offset),
                    ),
                )
            )
        for content in self._next.generate_copy_operators():
            yield self.create_mapapply_instruction(content, environments)

    def resolve_buffer(self):
        yield from self.generate_reduction_operators()
        yield from self.generate_copy_operators()


class BufferedEnvironmentInstruction(EnvironmentInstruction, ftype="buffered"):
    """
    Thin marker wrapper for buffered instruction regions.

    The instruction behaves like a normal :class:`EnvironmentInstruction`. It
    intentionally does not perform any automatic buffer rewrites; buffered
    targets must be inserted explicitly by the user.
    """

    def __init__(
        self,
        content: Instruction,
        *,
        environment: InstructionEnvironment | None = None,
        itype: str | None = None,
    ):
        if environment is None:
            environment = InstructionEnvironment()
        super().__init__(content, environment=environment, itype=itype)


__all__ = [
    "BufferManager",
    "BufferedEnvironmentInstruction",
]
