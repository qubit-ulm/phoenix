"""Configurator for the OpenCL backend."""

from ..base import SimpleBackendConfigurator
from ...dialog import prompt_text, prompt_yes_no
from ...scanner import detect_opencl_support


class OpenCLConfigurator(SimpleBackendConfigurator):
    """Configure the OpenCL backend."""

    name = "opencl"
    description = "OpenCL backend using pyopencl runtime compilation."
    default_resource = {
        "device": "gpu_or_cpu",
        "parallel_model": "opencl",
    }
    parallel_choices = ("opencl",)

    def quick_scan(self) -> dict:
        scan = super().quick_scan()
        scan["opencl"] = detect_opencl_support()
        return scan

    def dialog_available(self, scan: dict | None = None) -> bool:
        if scan is None:
            scan = self.quick_scan()
        support = scan.get("opencl", {})
        return bool(support.get("pyopencl") or support.get("clinfo"))

    def default_config(self, scan: dict) -> dict:
        data = super().default_config(scan)
        data["executables"] = {"runtime_compiler": "pyopencl.Program.build"}
        return data

    def run_dialog(self, scan: dict, current: dict) -> dict:
        merged = self.merge_defaults(scan, current)
        print(f"Configuring backend '{self.name}'")
        print(self.description)
        merged["enabled"] = prompt_yes_no(
            "Enable backend",
            default=bool(merged.get("enabled", self.recommended_enabled(scan))),
        )
        support = scan.get("opencl", {})
        if support.get("preview"):
            print("\nDetected OpenCL preview:")
            for line in support["preview"]:
                print(f"  {line}")
        print("\nRuntime")
        merged.setdefault("executables", {})
        merged["executables"]["runtime_compiler"] = prompt_text(
            "runtime compiler description",
            default=merged["executables"].get(
                "runtime_compiler",
                "pyopencl.Program.build",
            ),
        )
        print("\nResource")
        merged.setdefault("resource", {})
        merged["resource"]["device"] = prompt_text(
            "device",
            default=merged["resource"].get("device", "gpu_or_cpu"),
        )
        merged["resource"]["parallel_model"] = "opencl"
        return merged


CONFIGURATOR = OpenCLConfigurator()
