from __future__ import annotations

import unittest

from phoenix.fgen.buffermanager import BufferManager
from phoenix.fgen.backends import Config, get_backend
from phoenix.fgen.backends.fortran.fortran_adaa import FortranRA
from phoenix.fgen.instructionvar import InstructionVariable
from phoenix.keymap import KeyMap
from phoenix.fgen.libroutinevar import LibRoutineVariable


class BufferManagerTests(unittest.TestCase):
    def test_assignments_include_auxiliary_and_nested_buffers(self):
        scalar = KeyMap(name="scalar")
        scalar.entry("value")

        base = InstructionVariable.new("base", config=scalar)
        inner = BufferManager(base, name="inner")
        outer = BufferManager(
            base,
            name="outer",
            output_config=inner.keymap,
            inner_buffer=inner,
        )

        assignments = outer.assignments(adaa_class=FortranRA)

        self.assertIn(outer.buffer, assignments)
        self.assertIn(outer.auxbuf, assignments)
        self.assertIn(inner.buffer, assignments)
        self.assertIn(inner.auxbuf, assignments)

    def test_assignment_configs_merge_with_backend_assignment_config(self):
        scalar = KeyMap(name="scalar")
        scalar.entry("value")

        state = InstructionVariable.new("state", config=scalar)
        inner = BufferManager(state, name="inner")
        outer = BufferManager(
            state,
            name="outer",
            output_config=inner.keymap,
            inner_buffer=inner,
        )

        backend = get_backend("fortran")
        base_assignment_config = {
            state: Config(
                status="RW",
                family="complex",
                components=("real", "imag"),
            )
        }
        merged_config = {
            **base_assignment_config,
            **outer.assignment_configs(base_assignment_config),
        }

        assignments = backend.make_daa_assignments(merged_config)

        self.assertIn(state, assignments)
        self.assertIn(outer.buffer, assignments)
        self.assertIn(outer.auxbuf, assignments)
        self.assertIn(inner.buffer, assignments)
        self.assertIn(inner.auxbuf, assignments)

        for variable in (outer.buffer, outer.auxbuf, inner.buffer, inner.auxbuf):
            adaa_class, status = assignments[variable]
            self.assertEqual(status, LibRoutineVariable.STATUS_INOUT | LibRoutineVariable.STATUS_BUFFER)
            self.assertEqual(
                tuple(key for key, _dtype in adaa_class.datatypes()),
                ("real", "imag"),
            )
            self.assertEqual(adaa_class.get_fixed_size(), variable._default_config.size)

    def test_assignment_configs_require_existing_base_assignment_for_root_buffer(self):
        scalar = KeyMap(name="scalar")
        scalar.entry("value")

        state = InstructionVariable.new("state", config=scalar)
        buffer = BufferManager(state, name="buffer")

        with self.assertRaises(KeyError):
            buffer.assignment_configs({})

    def test_nested_buffers_inherit_root_assignment_config(self):
        scalar = KeyMap(name="scalar")
        scalar.entry("value")

        state = InstructionVariable.new("state", config=scalar)
        local = InstructionVariable.new("local", config=scalar)
        inner = BufferManager(local, name="inner")
        outer = BufferManager(
            state,
            name="outer",
            output_config=inner.keymap,
            inner_buffer=inner,
        )

        configs = outer.assignment_configs(
            {state: Config(status="RW", components=("real",))}
        )

        self.assertIn(outer.buffer, configs)
        self.assertIn(outer.auxbuf, configs)
        self.assertIn(inner.buffer, configs)
        self.assertIn(inner.auxbuf, configs)


if __name__ == "__main__":
    unittest.main()
