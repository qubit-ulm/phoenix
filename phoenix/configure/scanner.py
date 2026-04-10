"""Quick system scans used to propose backend configuration defaults."""

from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def find_first_executable(*candidates: str) -> str | None:
    """Return the first executable found on ``PATH``."""
    for candidate in candidates:
        path = shutil.which(candidate)
        if path is not None:
            return path
    return None


def detect_python_executable() -> str:
    """Return the current Python interpreter or a sensible fallback."""
    executable = Path(sys.executable)
    if executable.exists():
        return str(executable)
    return find_first_executable("python3", "python") or "python3"


def detect_f2py_executable() -> str | None:
    """Return a likely ``f2py`` executable."""
    python_executable = Path(detect_python_executable())
    sibling = python_executable.with_name("f2py")
    if sibling.exists():
        return str(sibling)
    return find_first_executable("f2py", "f2py3")


def detect_cpu_count() -> int:
    """Return a best-effort CPU core count."""
    return max(1, os.cpu_count() or 1)


def module_available(module_name: str) -> bool:
    """Return whether an importable module is available."""
    return importlib.util.find_spec(module_name) is not None


def run_capture(*args: str) -> str | None:
    """Run a small command and return stripped stdout on success."""
    try:
        result = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=2.0,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    return text or None


def detect_cuda_hardware() -> dict[str, object]:
    """Return a small summary of CUDA toolchain and GPU availability."""
    nvcc = find_first_executable("nvcc")
    nvidia_smi = find_first_executable("nvidia-smi")
    gpu_name = None
    if nvidia_smi is not None:
        query = run_capture(
            nvidia_smi,
            "--query-gpu=name",
            "--format=csv,noheader",
        )
        if query:
            gpu_name = query.splitlines()[0].strip()
    return {
        "nvcc": nvcc,
        "nvidia_smi": nvidia_smi,
        "gpu_name": gpu_name,
        "cupy": module_available("cupy"),
        "pycuda": module_available("pycuda"),
    }


def detect_opencl_support() -> dict[str, object]:
    """Return a small OpenCL availability summary."""
    clinfo = find_first_executable("clinfo")
    preview = run_capture(clinfo) if clinfo is not None else None
    return {
        "pyopencl": module_available("pyopencl"),
        "clinfo": clinfo,
        "preview": None if preview is None else preview.splitlines()[:3],
    }


class SystemProbe:
    """Small helper for system-dependent default detection."""

    def __init__(self):
        self._platform = platform.system().lower()

    @property
    def platform(self) -> str:
        """Return the normalized operating-system name."""
        return self._platform

    def executable(self, *candidates: str) -> str | None:
        """Return the first available executable among ``candidates``."""
        return find_first_executable(*candidates)

    def module(self, module_name: str) -> bool:
        """Return whether ``module_name`` can be imported."""
        return module_available(module_name)

    def python(self) -> str:
        """Return a likely Python executable."""
        return detect_python_executable()

    def f2py(self) -> str | None:
        """Return a likely f2py executable."""
        return detect_f2py_executable()

    def cpu_count(self) -> int:
        """Return a best-effort CPU count."""
        return detect_cpu_count()

    def default_executable(
        self,
        *candidates: str,
        fallback: str = "",
    ) -> str:
        """Return a detected executable or a placeholder fallback."""
        detected = self.executable(*candidates)
        if detected is not None:
            return detected
        if candidates:
            return candidates[0]
        return fallback
