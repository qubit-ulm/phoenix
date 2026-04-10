from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from phoenix.coeffbackend import CoeffBackend
from phoenix.fgen.backend_config import Configuration
from phoenix.fgen.backends.cuda.cuda_builder import CUDALibrary
from phoenix.fgen.backends.fortran.fortran_builder import FortranMFTPythonModule
from phoenix.fgen.library import Library
from phoenix.fgen.makefile import MakeFileManager
from phoenix.toolbox.backends.f2py_utils import preprocess_f90


class BackendConfigPathTests(unittest.TestCase):
    def test_library_paths_follow_general_configuration(self):
        general = Configuration.general().update(
            {
                "paths": {
                    "build_root": "custom_build_root",
                    "doc_suffix": ".docs.txt",
                    "makefile_name": "Local.mk",
                    "manifest_name": "manifest.custom.json",
                    "build_log_name": "custom.log",
                }
            }
        )
        library = Library("demo", general_configuration=general)

        self.assertTrue(library.basepath.startswith("custom_build_root/demo"))
        self.assertTrue(Path(library.docname).name.endswith(".docs.txt"))
        self.assertEqual(Path(library.makefilename).name, "Local.mk")
        self.assertEqual(
            Path(library.manifestname).name,
            "manifest.custom.json",
        )
        self.assertEqual(Path(library.logname).name, "custom.log")

    def test_makefile_manager_uses_default_naming(self):
        default_manager = MakeFileManager(None)
        named_manager = MakeFileManager("demo")

        self.assertEqual(default_manager.filename, "Makefile")
        self.assertEqual(named_manager.filename, "Makefile_demo")

    def test_c_basic_ops_library_uses_configured_support_library_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "libphoenix_c_support.so"
            target.write_text("", encoding="ascii")
            backend = Configuration.for_backend("c").update(
                {"support": {"library_file": str(target)}}
            )

            with patch.object(
                Configuration, "for_backend", return_value=backend
            ):
                from phoenix.fgen.backends.c.c_adaa import _CBasicOpsLibrary

                self.assertEqual(_CBasicOpsLibrary.resolve_target(), target)

    def test_preprocess_f90_uses_default_fortran_compiler(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch(
            "phoenix.toolbox.backends.f2py_utils.subprocess.run"
        ) as run_mock:
            preprocess_f90(
                "example.F90",
                directory=tmpdir,
            )

        compile_cmd = run_mock.call_args.args[0]
        self.assertEqual(compile_cmd[:4], ["gfortran", "-cpp", "-E", "-P"])

    def test_cuda_basic_ops_library_uses_configured_support_library_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "libphoenix_cuda_support.so"
            target.write_text("", encoding="ascii")
            backend = Configuration.for_backend("cuda").update(
                {"support": {"library_file": str(target)}}
            )

            with patch.object(
                Configuration, "for_backend", return_value=backend
            ):
                from phoenix.fgen.backends.cuda.cuda_pycuda_adaa import (
                    _PyCudaBasicOpsLibrary,
                )

                self.assertEqual(_PyCudaBasicOpsLibrary.resolve_target(), target)

    def test_cuda_library_build_target_depends_on_support_target_for_pycuda(self):
        backend = Configuration.for_backend("cuda").update(
            {
                "runtime": {"adaa_library": "pycuda"},
                "support": {
                    "makefile": "/tmp/cuda-support/Makefile",
                    "root": "/tmp/cuda-support",
                    "build_target": "support",
                    "library_file": "/tmp/cuda-support/lib/libphoenix_cuda_support.so",
                },
            }
        )
        library = CUDALibrary("cuda_demo", configuration=backend)

        build_target = library.get_build_target()
        dependency_names = [dep.target_name() for dep in build_target.dependencies]

        self.assertTrue(
            any(name.startswith("support_cuda_demo_") for name in dependency_names)
        )

    def test_coeffbackend_zero_and_copy_default_to_linop(self):
        class DummyCoeffBackend(CoeffBackend):
            def __init__(self):
                self.calls = []

            def coeff_new_array(self, size: int, dtype: str):
                del dtype
                return [0] * size

            def coeff_from_numpy(self, coeff_like, nparray, size: int, dtype: str):
                del coeff_like, nparray, size, dtype

            def coeff_to_numpy(self, coeff_like, size: int, dtype: str):
                del coeff_like, size, dtype
                return []

            def coeff_linop(
                self,
                arr_r,
                /,
                scal_a,
                arr_x,
                scal_b,
                arr_y,
                *,
                size,
                dtype,
                inplace=False,
            ):
                self.calls.append(
                    (arr_r, scal_a, arr_x, scal_b, arr_y, size, dtype, inplace)
                )

        backend = DummyCoeffBackend()
        target = [1, 2, 3]
        source = [4, 5, 6]

        backend.coeff_to_zero(target, size=3, dtype="f64")
        backend.coeff_copy_data(target, source, size=3, dtype="f64")

        self.assertEqual(
            backend.calls,
            [
                (target, None, None, None, None, 3, "f64", False),
                (target, None, source, None, None, 3, "f64", False),
            ],
        )

    def test_f90_python_module_falls_back_to_configured_python_when_f2py_path_is_stale(self):
        backend = Configuration.for_backend("fortran").update(
            {
                "executables": {
                    "f2py": "/does/not/exist/f2py",
                    "python": "/custom/python3",
                }
            }
        )
        target = object.__new__(FortranMFTPythonModule)
        target._configuration = backend
        def fake_exists(path_obj):
            return str(path_obj) == "/custom/python3"

        with patch("phoenix.fgen.backends.fortran.fortran_builder.Path.exists", autospec=True) as exists_mock:
            exists_mock.side_effect = fake_exists
            self.assertEqual(
                FortranMFTPythonModule._default_f2py_command(target),
                "/does/not/exist/f2py",
            )


if __name__ == "__main__":
    unittest.main()
