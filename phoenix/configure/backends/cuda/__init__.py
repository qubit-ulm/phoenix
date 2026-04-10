"""Configurator for the CUDA backend."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ..base import (
    ExecutableField,
    SimpleBackendConfigurator,
)
from ...dialog import prompt_choice
from ...scanner import detect_cuda_hardware


class CUDAConfigurator(SimpleBackendConfigurator):
    """Configure the CUDA backend."""

    name = "cuda"
    description = "CUDA backend using nvcc and optional GPU detection."
    executable_fields = (
        ExecutableField("compiler", "CUDA compiler", ("nvcc",)),
        ExecutableField("linker", "CUDA linker", ("nvcc",)),
    )
    default_flags = {
        "object": ["-Xcompiler", "-fPIC", "-Xcompiler", "-march=native"],
        "shared": [
            "-shared",
            "-Xcompiler",
            "-fPIC",
            "-Xcompiler",
            "-march=native",
            "-Xlinker",
            "-rpath",
            "-Xlinker",
            "'$$ORIGIN:$$ORIGIN/..'",
        ],
        "ptx": ["-ptx"],
        "extra_object": [],
        "extra_shared": [],
        "extra_ptx": [],
    }
    default_prefixes = {
        "include": "-I",
        "library": "-L",
    }
    default_resource = {
        "device": "gpu",
        "parallel_model": "cuda",
    }
    parallel_choices = ("cuda",)
    SUPPORT_HEADER = "phoenix_cuda_support.h"
    SUPPORT_SOURCE = "phoenix_cuda_support.cu"
    SUPPORT_LIBRARY = "libphoenix_cuda_support.so"
    SUPPORT_NAME = "phoenix_cuda_support"

    def enrich_config(self, data: dict) -> dict:
        """Add support-library metadata for the CUDA backend support library."""
        enriched = super().enrich_config(data)
        root = Path(enriched["support"]["root"])
        include_dir = root / "include"
        src_dir = root / "src"
        lib_dir = root / "lib"
        header_path = include_dir / type(self).SUPPORT_HEADER
        source_path = src_dir / type(self).SUPPORT_SOURCE
        library_path = lib_dir / type(self).SUPPORT_LIBRARY

        support = dict(enriched["support"])
        support.update(
            {
                "include_dir": str(include_dir),
                "src_dir": str(src_dir),
                "library_dir": str(lib_dir),
                "header_name": type(self).SUPPORT_HEADER,
                "header_file": str(header_path),
                "source_file": str(source_path),
                "library_name": type(self).SUPPORT_NAME,
                "library_file": str(library_path),
            }
        )
        enriched["support"] = support

        flags = deepcopy(enriched.get("flags", {}))
        flags.setdefault("extra_object", [])
        flags.setdefault("extra_shared", [])
        enriched["flags"] = flags
        return enriched

    def default_adaa_library(self, scan: dict) -> str:
        """Return the preferred CUDA ADAA implementation for this host."""
        hardware = scan.get("hardware", {})
        if hardware.get("cupy"):
            return "cupy"
        if hardware.get("pycuda"):
            return "pycuda"
        return "cupy"

    def quick_scan(self) -> dict:
        scan = super().quick_scan()
        scan["hardware"] = detect_cuda_hardware()
        return scan

    def default_config(self, scan: dict) -> dict:
        data = super().default_config(scan)
        hardware = scan.get("hardware", {})
        data["runtime"] = {
            "cupy_available": bool(hardware.get("cupy")),
            "pycuda_available": bool(hardware.get("pycuda")),
            "adaa_library": self.default_adaa_library(scan),
        }
        return data

    def dialog_available(self, scan: dict | None = None) -> bool:
        if scan is None:
            scan = self.quick_scan()
        executables = scan.get("executables", {})
        hardware = scan.get("hardware", {})
        return bool(
            executables.get("compiler")
            or hardware.get("gpu_name")
            or hardware.get("cupy")
            or hardware.get("pycuda")
        )

    def support_makefile_lines(self, data: dict):
        """Yield the makefile used to build the CUDA support library."""
        support = data["support"]
        compiler = data.get("executables", {}).get("compiler", "nvcc")
        linker = data.get("executables", {}).get("linker", compiler)
        object_flags = " ".join(data.get("flags", {}).get("object", []))
        shared_flags = " ".join(data.get("flags", {}).get("shared", []))
        yield f"# Generated support makefile for backend '{self.name}'"
        yield f"CC := {compiler}"
        yield f"LD := {linker}"
        yield f"SUPPORT_ROOT := {support['root']}"
        yield f"INCLUDE_DIR := {support['include_dir']}"
        yield f"SRC_DIR := {support['src_dir']}"
        yield f"LIB_DIR := {support['library_dir']}"
        yield f"SOURCE := {support['source_file']}"
        yield "OBJECT := $(LIB_DIR)/phoenix_cuda_support.o"
        yield f"TARGET := {support['library_file']}"
        yield f"CFLAGS := -I$(INCLUDE_DIR) {object_flags}".rstrip()
        yield f"LDFLAGS := {shared_flags} -lcuda".rstrip()
        yield ""
        yield ".PHONY: help show support clean"
        yield ""
        yield "help:"
        yield '\t@echo "Available targets: show, support, clean"'
        yield ""
        yield "show:"
        yield '\t@echo "backend: cuda"'
        yield '\t@echo "support root: $(SUPPORT_ROOT)"'
        yield '\t@echo "header: $(INCLUDE_DIR)/phoenix_cuda_support.h"'
        yield '\t@echo "library: $(TARGET)"'
        yield ""
        # Build support for the CUDA backend as a whole. The selected ADAA
        # runtime (CuPy vs PyCUDA) is a runtime choice and does not gate
        # whether the CUDA support library itself is compiled.
        yield "support: $(TARGET)"
        yield ""
        yield "$(LIB_DIR):"
        yield "\tmkdir -p $(LIB_DIR)"
        yield ""
        yield "$(OBJECT): $(SOURCE) | $(LIB_DIR)"
        yield "\t$(CC) -c $(SOURCE) -o $(OBJECT) $(CFLAGS)"
        yield ""
        yield "$(TARGET): $(OBJECT)"
        yield "\t$(LD) -o $(TARGET) $(OBJECT) $(LDFLAGS)"
        yield ""
        yield "clean:"
        yield "\trm -f $(OBJECT) $(TARGET)"

    def write_support_files(self, data: dict) -> dict:
        """Write the support header, source file, and makefile."""
        support = data["support"]
        for key in ("root", "include_dir", "src_dir", "library_dir"):
            Path(support[key]).mkdir(parents=True, exist_ok=True)

        with open(support["header_file"], "w", encoding="ascii") as handle:
            handle.write("\n".join(self._header_lines()) + "\n")
        with open(support["source_file"], "w", encoding="ascii") as handle:
            handle.write("\n".join(self._source_lines()) + "\n")
        return super().write_support_files(data)

    def build_support(self, data: dict):
        """Compile the CUDA backend support shared library.

        This build is backend-wide. Runtime selection between CuPy and PyCUDA
        remains independent from whether the common CUDA support library is
        built and present on disk.
        """
        super().build_support(data)
        support = data["support"]
        if not Path(support["library_file"]).exists():
            raise RuntimeError(
                f"failed to build CUDA backend support library {support['library_file']}"
            )
        return f"Built support library {support['library_file']}"

    def support_required(self, data: dict) -> bool:
        # Readiness of the currently selected runtime still depends on whether
        # PyCUDA mode is active, because only that mode consumes the shared
        # support library directly today.
        return data.get("runtime", {}).get("adaa_library") == "pycuda"

    def run_dialog(self, scan: dict, current: dict) -> dict:
        merged = super().run_dialog(scan, current)
        hardware = scan.get("hardware", {})
        runtime = merged.setdefault("runtime", {})
        runtime["cupy_available"] = bool(hardware.get("cupy"))
        runtime["pycuda_available"] = bool(hardware.get("pycuda"))

        print("\nCUDA runtime")
        print(
            "Detected ADAA libraries:"
            f" cupy={runtime['cupy_available']},"
            f" pycuda={runtime['pycuda_available']}"
        )
        runtime["adaa_library"] = prompt_choice(
            "ADAA library",
            ["cupy", "pycuda"],
            default=runtime.get(
                "adaa_library",
                self.default_adaa_library(scan),
            ),
        )
        return merged

    def _header_lines(self):
        yield "#ifndef PHOENIX_CUDA_SUPPORT_H"
        yield "#define PHOENIX_CUDA_SUPPORT_H"
        yield ""
        yield "#include <stddef.h>"
        yield "#include <stdint.h>"
        yield ""
        yield "#ifdef __cplusplus"
        yield 'extern "C" {'
        yield "#endif"
        yield ""
        yield "const char *phoenix_cuda_support_last_error(void);"
        yield ""
        for dtype, ctype in (
            ("f32", "float"),
            ("f64", "double"),
            ("i32", "int32_t"),
            ("i64", "int64_t"),
        ):
            yield f"int coeff_zero_{dtype}(uintptr_t arr, size_t size);"
            yield (
                f"int coeff_copy_{dtype}(uintptr_t dst, uintptr_t src, size_t size);"
            )
            yield (
                f"int coeff_linop_{dtype}("
                f"uintptr_t r, {ctype} a, uintptr_t x, int has_a, "
                f"{ctype} b, uintptr_t y, int has_b, int has_y, "
                f"size_t size, int inplace);"
            )
        yield ""
        yield "#ifdef __cplusplus"
        yield "}"
        yield "#endif"
        yield ""
        yield "#endif"

    def _source_lines(self):
        yield '#include "phoenix_cuda_support.h"'
        yield ""
        yield "#include <cuda.h>"
        yield "#include <stdio.h>"
        yield "#include <stdlib.h>"
        yield "#include <string.h>"
        yield ""
        yield "static char PHOENIX_CUDA_SUPPORT_ERROR[512] = \"\";"
        yield ""
        yield "const char *phoenix_cuda_support_last_error(void) {"
        yield "    return PHOENIX_CUDA_SUPPORT_ERROR;"
        yield "}"
        yield ""
        yield "static int phoenix_cuda_support_fail(const char *message) {"
        yield (
            '    snprintf(PHOENIX_CUDA_SUPPORT_ERROR, sizeof(PHOENIX_CUDA_SUPPORT_ERROR), "%s", message);'
        )
        yield "    return 1;"
        yield "}"
        yield ""
        yield (
            "static int phoenix_cuda_support_fail_cuda(const char *prefix, CUresult result) {"
        )
        yield "    const char *name = NULL;"
        yield "    const char *message = NULL;"
        yield "    cuGetErrorName(result, &name);"
        yield "    cuGetErrorString(result, &message);"
        yield "    snprintf("
        yield "        PHOENIX_CUDA_SUPPORT_ERROR,"
        yield "        sizeof(PHOENIX_CUDA_SUPPORT_ERROR),"
        yield '        "%s: %s (%s)",'
        yield "        prefix,"
        yield '        message != NULL ? message : "unknown CUDA driver error",'
        yield '        name != NULL ? name : "unknown"'
        yield "    );"
        yield "    return 1;"
        yield "}"
        yield ""
        yield "static int phoenix_cuda_support_prepare(void) {"
        yield "    CUcontext context = NULL;"
        yield "    CUresult result = cuInit(0);"
        yield "    if (result != CUDA_SUCCESS) {"
        yield (
            '        return phoenix_cuda_support_fail_cuda("cuInit failed", result);'
        )
        yield "    }"
        yield "    result = cuCtxGetCurrent(&context);"
        yield "    if (result != CUDA_SUCCESS) {"
        yield (
            '        return phoenix_cuda_support_fail_cuda("cuCtxGetCurrent failed", result);'
        )
        yield "    }"
        yield "    if (context == NULL) {"
        yield (
            '        return phoenix_cuda_support_fail("no current CUDA context available");'
        )
        yield "    }"
        yield "    return 0;"
        yield "}"
        yield ""
        yield "#define DEFINE_CUDA_BASIC_OPS(NAME, TYPE)                                       \\"
        yield "    int coeff_zero_##NAME(uintptr_t arr, size_t size) {                         \\"
        yield "        CUresult result;                                                         \\"
        yield "        if (arr == 0) {                                                          \\"
        yield "            return 0;                                                            \\"
        yield "        }                                                                        \\"
        yield "        if (phoenix_cuda_support_prepare() != 0) {                               \\"
        yield "            return 1;                                                            \\"
        yield "        }                                                                        \\"
        yield "        result = cuMemsetD8((CUdeviceptr)arr, 0, size * sizeof(TYPE));           \\"
        yield "        if (result != CUDA_SUCCESS) {                                            \\"
        yield '            return phoenix_cuda_support_fail_cuda("cuMemsetD8 failed", result); \\'
        yield "        }                                                                        \\"
        yield "        return 0;                                                                \\"
        yield "    }                                                                            \\"
        yield "                                                                                 \\"
        yield "    int coeff_copy_##NAME(uintptr_t dst, uintptr_t src, size_t size) {           \\"
        yield "        CUresult result;                                                         \\"
        yield "        if (dst == 0 || src == 0) {                                              \\"
        yield '            return phoenix_cuda_support_fail("coeff_copy received null pointer");\\'
        yield "        }                                                                        \\"
        yield "        if (phoenix_cuda_support_prepare() != 0) {                               \\"
        yield "            return 1;                                                            \\"
        yield "        }                                                                        \\"
        yield "        result = cuMemcpyDtoD((CUdeviceptr)dst, (CUdeviceptr)src, size * sizeof(TYPE));\\"
        yield "        if (result != CUDA_SUCCESS) {                                            \\"
        yield '            return phoenix_cuda_support_fail_cuda("cuMemcpyDtoD failed", result);\\'
        yield "        }                                                                        \\"
        yield "        return 0;                                                                \\"
        yield "    }                                                                            \\"
        yield "                                                                                 \\"
        yield "    int coeff_linop_##NAME(                                                      \\"
        yield "        uintptr_t r, TYPE a, uintptr_t x, int has_a, TYPE b, uintptr_t y,        \\"
        yield "        int has_b, int has_y, size_t size, int inplace                           \\"
        yield "    ) {                                                                          \\"
        yield "        CUresult result;                                                         \\"
        yield "        TYPE *host_r = NULL;                                                     \\"
        yield "        TYPE *host_x = NULL;                                                     \\"
        yield "        TYPE *host_y = NULL;                                                     \\"
        yield "        if (r == 0) {                                                            \\"
        yield "            return 0;                                                            \\"
        yield "        }                                                                        \\"
        yield "        if (phoenix_cuda_support_prepare() != 0) {                               \\"
        yield "            return 1;                                                            \\"
        yield "        }                                                                        \\"
        yield "        host_r = (TYPE *)malloc(size * sizeof(TYPE));                            \\"
        yield "        if (host_r == NULL) {                                                    \\"
        yield '            return phoenix_cuda_support_fail("malloc failed for host_r");       \\'
        yield "        }                                                                        \\"
        yield "        if (inplace) {                                                           \\"
        yield "            result = cuMemcpyDtoH(host_r, (CUdeviceptr)r, size * sizeof(TYPE));  \\"
        yield "            if (result != CUDA_SUCCESS) {                                        \\"
        yield "                free(host_r);                                                    \\"
        yield '                return phoenix_cuda_support_fail_cuda("cuMemcpyDtoH failed", result);\\'
        yield "            }                                                                    \\"
        yield "        } else {                                                                 \\"
        yield "            memset(host_r, 0, size * sizeof(TYPE));                              \\"
        yield "        }                                                                        \\"
        yield "        if (x != 0) {                                                            \\"
        yield "            host_x = (TYPE *)malloc(size * sizeof(TYPE));                        \\"
        yield "            if (host_x == NULL) {                                                \\"
        yield "                free(host_r);                                                    \\"
        yield '                return phoenix_cuda_support_fail("malloc failed for host_x");   \\'
        yield "            }                                                                    \\"
        yield "            result = cuMemcpyDtoH(host_x, (CUdeviceptr)x, size * sizeof(TYPE));  \\"
        yield "            if (result != CUDA_SUCCESS) {                                        \\"
        yield "                free(host_x);                                                    \\"
        yield "                free(host_r);                                                    \\"
        yield '                return phoenix_cuda_support_fail_cuda("cuMemcpyDtoH failed", result);\\'
        yield "            }                                                                    \\"
        yield "        }                                                                        \\"
        yield "        if (has_y && y != 0) {                                                   \\"
        yield "            host_y = (TYPE *)malloc(size * sizeof(TYPE));                        \\"
        yield "            if (host_y == NULL) {                                                \\"
        yield "                free(host_x);                                                    \\"
        yield "                free(host_r);                                                    \\"
        yield '                return phoenix_cuda_support_fail("malloc failed for host_y");   \\'
        yield "            }                                                                    \\"
        yield "            result = cuMemcpyDtoH(host_y, (CUdeviceptr)y, size * sizeof(TYPE));  \\"
        yield "            if (result != CUDA_SUCCESS) {                                        \\"
        yield "                free(host_y);                                                    \\"
        yield "                free(host_x);                                                    \\"
        yield "                free(host_r);                                                    \\"
        yield '                return phoenix_cuda_support_fail_cuda("cuMemcpyDtoH failed", result);\\'
        yield "            }                                                                    \\"
        yield "        }                                                                        \\"
        yield "        for (size_t i = 0; i < size; ++i) {                                      \\"
        yield "            TYPE value = inplace ? host_r[i] : (TYPE)0;                          \\"
        yield "            if (host_x != NULL) {                                                \\"
        yield "                value += has_a ? (a * host_x[i]) : host_x[i];                    \\"
        yield "            }                                                                    \\"
        yield "            if (host_y != NULL) {                                                \\"
        yield "                value += has_b ? (b * host_y[i]) : host_y[i];                    \\"
        yield "            } else if (has_b) {                                                  \\"
        yield "                value += b;                                                      \\"
        yield "            }                                                                    \\"
        yield "            host_r[i] = value;                                                   \\"
        yield "        }                                                                        \\"
        yield "        result = cuMemcpyHtoD((CUdeviceptr)r, host_r, size * sizeof(TYPE));      \\"
        yield "        free(host_y);                                                            \\"
        yield "        free(host_x);                                                            \\"
        yield "        free(host_r);                                                            \\"
        yield "        if (result != CUDA_SUCCESS) {                                            \\"
        yield '            return phoenix_cuda_support_fail_cuda("cuMemcpyHtoD failed", result);\\'
        yield "        }                                                                        \\"
        yield "        return 0;                                                                \\"
        yield "    }"
        yield ""
        yield "DEFINE_CUDA_BASIC_OPS(f32, float)"
        yield "DEFINE_CUDA_BASIC_OPS(f64, double)"
        yield "DEFINE_CUDA_BASIC_OPS(i32, int32_t)"
        yield "DEFINE_CUDA_BASIC_OPS(i64, int64_t)"


CONFIGURATOR = CUDAConfigurator()
