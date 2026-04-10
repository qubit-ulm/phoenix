from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "example" / "tests" / "multispinlib.py"

spec = importlib.util.spec_from_file_location("multispinlib", MODULE_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"cannot import {MODULE_PATH}")
multispinlib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(multispinlib)


Group = multispinlib.Group
Hamiltonian = multispinlib.Hamiltonian
HamiltonianTerm = multispinlib.HamiltonianTerm
Nuclear = multispinlib.Nuclear
Single = multispinlib.Single
SpatialPosition3D = multispinlib.SpatialPosition3D
System = multispinlib.System
Vector = multispinlib.Vector


class NuclearSpin(Single, Nuclear, SpatialPosition3D):
    pass


class MultiSpinLibTests(unittest.TestCase):
    def setUp(self):
        self.spin_a = NuclearSpin(name="A", gamma=2.0, pos=(0.0, 0.0, 0.0))
        self.spin_b = NuclearSpin(name="B", gamma=1.0, pos=(1.0, 0.0, 0.0))
        self.spin_c = NuclearSpin(name="C", gamma=1.0, pos=(3.0, 0.0, 0.0))

        self.molecule = Group(name="mol")
        self.molecule.append(self.spin_a, self.spin_b)

        self.root = Group(self.molecule, self.spin_c, name="sys")
        self.system = System(self.root, name="sys")

    def test_system_units_follow_recursive_leaf_order(self):
        units = list(self.system.units())
        self.assertEqual(units, [self.spin_a, self.spin_b, self.spin_c])
        index_map = self.system.unit_index_map()
        self.assertEqual(index_map[self.spin_a], 0)
        self.assertEqual(index_map[self.spin_b], 1)
        self.assertEqual(index_map[self.spin_c], 2)

    def test_pair_iter_applies_consider_and_exclude_filters(self):
        pairs = list(
            self.system.pair_iter(
                considers=[lambda a, b: a.distance(b) <= 2.1],
                excludes=[lambda a, b: {a.name, b.name} == {"A", "B"}],
            )
        )
        self.assertEqual(pairs, [(self.spin_b, self.spin_c)])

    def test_system_create_hamiltonian_binds_system(self):
        ham = self.system.create_hamiltonian(name="demo")
        self.assertIs(ham.system, self.system)
        self.assertEqual(ham.name, "demo")
        self.assertEqual(ham.terms, ())

    def test_hamiltonian_term_evaluates_static_and_dynamic_coefficients(self):
        static_term = HamiltonianTerm(
            units=(self.spin_a, self.spin_b),
            coefficient=2.5,
            specifier=("zz",),
            system=self.system,
            kind="static",
        )
        dynamic_term = HamiltonianTerm(
            units=(self.spin_c,),
            coefficient=lambda time, system, term: system.unit_index_map()[self.spin_c] + time,
            specifier=("rf",),
            system=self.system,
            kind="dynamic",
        )
        self.assertEqual(static_term._evaluate_coeff(system=self.system), 2.5)
        self.assertEqual(dynamic_term._evaluate_coeff(time=0.5, system=self.system), 2.5)
        fixed = dynamic_term.fix(time=0.5, system=self.system)
        self.assertEqual(fixed.coefficient, 2.5)

    def test_hamiltonian_extend_and_copy_preserve_terms(self):
        term_a = HamiltonianTerm(
            units=(self.spin_a,),
            coefficient=1.0,
            specifier=("z0",),
            system=self.system,
            kind="local",
        )
        term_b = HamiltonianTerm(
            units=(self.spin_a, self.spin_b),
            coefficient=-0.25,
            specifier=("zz01",),
            system=self.system,
            kind="coupling",
        )

        ham = self.system.create_hamiltonian(name="source").extend(term_a, term_b)
        clone = ham.copy(name="clone")

        self.assertEqual(ham.terms, (term_a, term_b))
        self.assertEqual(clone.terms, (term_a, term_b))
        self.assertIs(clone.system, self.system)
        self.assertEqual(clone.name, "clone")
        self.assertIsNot(clone, ham)

    def test_spatial_transforms_update_positions(self):
        spin = NuclearSpin(name="T", pos=(1.0, 0.0, 0.0))
        spin.apply("translate", (0.0, 2.0, 0.0))
        self.assertEqual(spin.position().as_tuple(), (1.0, 2.0, 0.0))

        spin.apply("rotate", angle=90, axis=(0.0, 0.0, 1.0), degrees=True)
        pos = spin.position().as_tuple()
        self.assertTrue(np.allclose(pos[:2], (-2.0, 1.0), atol=1e-12))

    def test_vector_center_of_mass_uses_weights(self):
        pos = Vector.get_cms((Vector(0.0, 0.0, 0.0), 1.0), (Vector(2.0, 0.0, 0.0), 3.0))
        self.assertEqual(pos.as_tuple(), (1.5, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
