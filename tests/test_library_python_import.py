from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from phoenix.fgen.backend_config import Configuration
from phoenix.fgen.backends import get_backend


class LibraryPythonImportTests(unittest.TestCase):
    def test_python_library_import_python_module_uses_generic_library_api(self):
        backend = get_backend("python")
        with tempfile.TemporaryDirectory() as tmpdir:
            general = Configuration.general().update(
                {"paths": {"build_root": tmpdir}}
            )
            library = backend.clone(general_configuration=general).library(
                "demo_import"
            )
            module_path = Path(library.relative_to_basepath(library.filename))
            module_path.parent.mkdir(parents=True, exist_ok=True)
            module_path.write_text("VALUE = 17\n", encoding="ascii")

            module = backend.import_python_module(library)

            self.assertEqual(module.VALUE, 17)

    def test_plain_library_import_python_module_raises_explicitly(self):
        backend = get_backend("plain")
        with tempfile.TemporaryDirectory() as tmpdir:
            general = Configuration.general().update(
                {"paths": {"build_root": tmpdir}}
            )
            library = backend.clone(general_configuration=general).library(
                "demo_plain"
            )

            with self.assertRaises(NotImplementedError):
                backend.import_python_module(library)


if __name__ == "__main__":
    unittest.main()
