"""Configurator for the C backend."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ..base import ExecutableField, SimpleBackendConfigurator


def _merge_unique_flags(existing: list[str], additions: list[str]) -> list[str]:
    """Return ``existing`` with ``additions`` appended once in order."""
    merged = list(existing)
    for flag in additions:
        if flag not in merged:
            merged.append(flag)
    return merged


class CConfigurator(SimpleBackendConfigurator):
    """Configure the C backend and its native support library."""

    name = "c"
    description = "C backend using a host compiler and shared-library linker."
    executable_fields = (
        ExecutableField("compiler", "C compiler", ("cc", "gcc", "clang")),
        ExecutableField("linker", "C linker", ("cc", "gcc", "clang")),
    )
    default_flags = {
        "object": ["-fPIC", "-march=native"],
        "shared": ["-shared", "-Wl,-rpath,'$$ORIGIN:$$ORIGIN/..'"],
        "extra_object": [],
        "extra_shared": [],
    }
    default_prefixes = {
        "include": "-I",
        "library": "-L",
    }
    default_resource = {
        "device": "cpu",
        "parallel_model": "serial",
    }
    parallel_choices = ("serial", "omp")

    SUPPORT_HEADER = "phoenix_c_support.h"
    SUPPORT_SOURCE = "phoenix_c_support.c"
    SUPPORT_LIBRARY = "libphoenix_c_support.so"
    SUPPORT_NAME = "phoenix_c_support"

    def enrich_config(self, data: dict) -> dict:
        """Add support-library metadata and corresponding compiler flags."""
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
        flags["extra_object"] = _merge_unique_flags(
            flags["extra_object"],
            [f"-I{include_dir}"],
        )
        flags["extra_shared"] = _merge_unique_flags(
            flags["extra_shared"],
            [
                f"-L{lib_dir}",
                f"-l{type(self).SUPPORT_NAME}",
                f"-Wl,-rpath,{lib_dir}",
            ],
        )
        enriched["flags"] = flags
        return enriched

    def support_makefile_lines(self, data: dict):
        """Yield the makefile used to build the C support library."""
        support = data["support"]
        compiler = data.get("executables", {}).get("compiler", "cc")
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
        yield "OBJECT := $(LIB_DIR)/phoenix_c_support.o"
        yield f"TARGET := {support['library_file']}"
        yield f"CFLAGS := -std=c99 -I$(INCLUDE_DIR) {object_flags}".rstrip()
        yield f"LDFLAGS := {shared_flags}".rstrip()
        yield ""
        yield ".PHONY: help show support clean"
        yield ""
        yield "help:"
        yield '\t@echo "Available targets: show, support, clean"'
        yield ""
        yield "show:"
        yield '\t@echo "backend: c"'
        yield '\t@echo "support root: $(SUPPORT_ROOT)"'
        yield '\t@echo "header: $(INCLUDE_DIR)/phoenix_c_support.h"'
        yield '\t@echo "library: $(TARGET)"'
        yield ""
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

        with open(support["header_file"], "w") as handle:
            handle.write("\n".join(self._header_lines()) + "\n")
        with open(support["source_file"], "w") as handle:
            handle.write("\n".join(self._source_lines()) + "\n")
        return super().write_support_files(data)

    def build_support(self, data: dict):
        """Compile the C support shared library."""
        super().build_support(data)
        support = data["support"]
        if not Path(support["library_file"]).exists():
            raise RuntimeError(
                f"failed to build C backend support library {support['library_file']}"
            )
        return f"Built support library {support['library_file']}"

    def _header_lines(self):
        """Return the header file contents."""
        yield "#ifndef PHOENIX_C_SUPPORT_H"
        yield "#define PHOENIX_C_SUPPORT_H"
        yield ""
        yield "#include <stddef.h>"
        yield "#include <stdint.h>"
        yield ""
        for dtype, ctype in (
            ("f32", "float"),
            ("f64", "double"),
            ("i32", "int32_t"),
            ("i64", "int64_t"),
        ):
            yield f"void phoenix_zero_{dtype}({ctype} *buffer, int32_t size);"
        yield ""
        for dtype, ctype in (
            ("f32", "float"),
            ("f64", "double"),
            ("i32", "int32_t"),
            ("i64", "int64_t"),
        ):
            yield f"void coeff_zero_{dtype}({ctype} *arr, size_t size);"
            yield (
                f"void coeff_copy_{dtype}({ctype} *dst, const {ctype} *src, size_t size);"
            )
            yield (
                f"void coeff_linop_{dtype}("
                f"{ctype} *r, {ctype} a, const {ctype} *x, int has_a, "
                f"{ctype} b, const {ctype} *y, int has_b, int has_y, "
                f"size_t size, int inplace);"
            )
        yield ""
        yield "#endif"

    def _source_lines(self):
        """Return the source file contents."""
        yield '#include "phoenix_c_support.h"'
        yield ""
        yield "#define DEFINE_ZERO(NAME, TYPE)                                        \\"
        yield "    void phoenix_zero_##NAME(TYPE *buffer, int32_t size) {             \\"
        yield "        for (int32_t idx = 0; idx < size; ++idx) {                      \\"
        yield "            buffer[idx] = (TYPE)0;                                      \\"
        yield "        }                                                               \\"
        yield "    }"
        yield ""
        yield "#define DEFINE_ZERO_COPY_LINOP(NAME, TYPE)                               \\"
        yield "    void coeff_zero_##NAME(TYPE *arr, size_t size) {                    \\"
        yield "        for (size_t i = 0; i < size; ++i) {                              \\"
        yield "            arr[i] = (TYPE)0;                                            \\"
        yield "        }                                                                \\"
        yield "    }                                                                    \\"
        yield "                                                                         \\"
        yield "    void coeff_copy_##NAME(TYPE *dst, const TYPE *src, size_t size) {    \\"
        yield "        for (size_t i = 0; i < size; ++i) {                              \\"
        yield "            dst[i] = src[i];                                             \\"
        yield "        }                                                                \\"
        yield "    }                                                                    \\"
        yield "                                                                         \\"
        yield "    void coeff_linop_##NAME(                                             \\"
        yield "        TYPE *r,                                                         \\"
        yield "        TYPE a,                                                          \\"
        yield "        const TYPE *x,                                                   \\"
        yield "        int has_a,                                                       \\"
        yield "        TYPE b,                                                          \\"
        yield "        const TYPE *y,                                                   \\"
        yield "        int has_b,                                                       \\"
        yield "        int has_y,                                                       \\"
        yield "        size_t size,                                                     \\"
        yield "        int inplace                                                      \\"
        yield "    ) {                                                                  \\"
        yield "        for (size_t i = 0; i < size; ++i) {                              \\"
        yield "            TYPE value = inplace ? r[i] : (TYPE)0;                       \\"
        yield "            if (x != NULL) {                                             \\"
        yield "                value += has_a ? (a * x[i]) : x[i];                      \\"
        yield "            }                                                            \\"
        yield "            if (has_y && y != NULL) {                                    \\"
        yield "                value += has_b ? (b * y[i]) : y[i];                      \\"
        yield "            } else if (has_b) {                                          \\"
        yield "                value += b;                                              \\"
        yield "            }                                                            \\"
        yield "            r[i] = value;                                                \\"
        yield "        }                                                                \\"
        yield "    }"
        yield ""
        yield "DEFINE_ZERO(f32, float)"
        yield "DEFINE_ZERO(f64, double)"
        yield "DEFINE_ZERO(i32, int32_t)"
        yield "DEFINE_ZERO(i64, int64_t)"
        yield ""
        yield "DEFINE_ZERO_COPY_LINOP(f32, float)"
        yield "DEFINE_ZERO_COPY_LINOP(f64, double)"
        yield "DEFINE_ZERO_COPY_LINOP(i32, int32_t)"
        yield "DEFINE_ZERO_COPY_LINOP(i64, int64_t)"


CONFIGURATOR = CConfigurator()
