"""Shared configurator base classes for Phoenix backend configuration."""

from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from ..dialog import (
    prompt_choice,
    prompt_list,
    prompt_text,
    prompt_yes_no,
)
from ..scanner import (
    SystemProbe,
    detect_cpu_count,
    detect_f2py_executable,
    detect_python_executable,
    find_first_executable,
)
from ...fgen.backend_config import Configuration


@dataclass(frozen=True)
class ExecutableField:
    """Description of one executable prompt in a backend dialog."""

    key: str
    label: str
    candidates: tuple[str, ...] = ()


class BackendConfigurator:
    """Base class for per-backend configuration scanners and dialogs."""

    name = "generic"
    description = "generic backend"

    def system_probe(self) -> SystemProbe:
        """Return a probe object used for host-specific defaults."""
        return SystemProbe()

    def config_path(self) -> Path:
        """Return the target JSON path for this backend."""
        return Configuration.default_file(self.name)

    def config_exists(self) -> bool:
        """Return whether this backend already has a persisted config."""
        return self.config_path().exists()

    def load_current(self) -> dict:
        """Return the persisted config or an empty mapping."""
        if not self.config_exists():
            return {}
        return Configuration.from_file(self.config_path()).to_dict()

    def quick_scan(self) -> dict:
        """Return backend-specific scan results."""
        return {"cpu_count": detect_cpu_count()}

    def runtime_available(self) -> bool:
        """Return whether the backend is configured for runtime use."""
        if not self.config_exists():
            return False
        return bool(self.load_current().get("enabled", True))

    def dialog_available(self, scan: dict | None = None) -> bool:
        """Return whether enough was detected to offer a guided dialog."""
        del scan
        return True

    def default_config(self, scan: dict) -> dict:
        """Return a config template derived from the quick scan."""
        return {
            "backend": self.name,
            "enabled": self.recommended_enabled(scan),
        }

    def recommended_enabled(self, scan: dict | None = None) -> bool:
        """Return the recommended initial enabled state."""
        if scan is None:
            scan = self.quick_scan()
        return self.dialog_available(scan)

    def merge_defaults(self, scan: dict, current: dict) -> dict:
        """Merge current values over quick-scan defaults."""
        default = self.default_config(scan)
        for key, value in current.items():
            if isinstance(value, dict) and isinstance(default.get(key), dict):
                merged = dict(default[key])
                merged.update(value)
                default[key] = merged
            else:
                default[key] = value
        return default

    def support_root(self) -> Path:
        """Return the backend-local support directory managed by the configurator."""
        return Configuration.backend_root(self.name) / "support"

    def support_makefile_path(self) -> Path:
        """Return the generated support makefile path."""
        return self.support_root() / "Makefile"

    def enrich_config(self, data: dict) -> dict:
        """Return ``data`` augmented with support metadata."""
        enriched = deepcopy(data)
        support = dict(enriched.get("support", {}))
        support.setdefault("root", str(self.support_root()))
        support.setdefault("makefile", str(self.support_makefile_path()))
        support.setdefault("build_target", "support")
        enriched["support"] = support
        return enriched

    def support_makefile_lines(self, data: dict):
        """Yield the backend-local support makefile."""
        support = data.get("support", {})
        yield f"# Generated support makefile for backend '{self.name}'"
        yield f"BACKEND := {self.name}"
        yield f"SUPPORT_ROOT := {support.get('root', self.support_root())}"
        yield ""
        yield ".PHONY: help show support clean"
        yield ""
        yield "help:"
        yield '\t@echo "Available targets: show, support, clean"'
        yield ""
        yield "show:"
        yield '\t@echo "backend: $(BACKEND)"'
        yield '\t@echo "support root: $(SUPPORT_ROOT)"'
        yield ""
        yield "support:"
        yield '\t@echo "No compiled support artifacts are required for this backend."'
        yield ""
        yield "clean:"
        yield '\t@echo "Nothing to clean for this backend support package."'

    def write_support_files(self, data: dict) -> dict:
        """Write support-side generated files and return the config data."""
        target = Path(data["support"]["makefile"])
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w") as handle:
            for line in self.support_makefile_lines(data):
                handle.write(line + "\n")
        return data

    def build_support(self, data: dict):
        """Execute the generated support makefile."""
        support = data["support"]
        result = subprocess.run(
            ["make", "-C", support["root"], "support"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"failed to build {self.name} backend support:\n"
                + result.stdout
                + result.stderr
            )
        return f"Executed support makefile {support['makefile']}"

    def support_required(self, data: dict) -> bool:
        """Return whether this backend expects a built support artifact."""
        return bool(data.get("support", {}).get("library_file"))

    def support_ready(self, data: dict | None = None) -> bool:
        """Return whether the configured support artifact is ready to use."""
        if data is None:
            if not self.config_exists():
                return False
            data = self.load_current()
        if not self.support_required(data):
            return True
        target = data.get("support", {}).get("library_file")
        if not target:
            return False
        return Path(target).exists()

    def finalize(self, data: dict) -> list[str]:
        """Write support files and optionally build support artifacts."""
        self.write_support_files(data)
        result = self.build_support(data)
        messages = [f"Generated support makefile {data['support']['makefile']}"]
        if result is not None:
            messages.append(result)
        return messages

    def show(self) -> str:
        """Render the current configuration or an unavailable message."""
        path = self.config_path()
        if not path.exists():
            return (
                f"{self.name}: unavailable\n"
                f"reason: missing configuration file {path}"
            )
        data = Configuration.from_file(path).to_dict()
        return (
            f"{self.name}: available\n"
            f"config file: {path}\n\n"
            + json.dumps(data, indent=2, sort_keys=True)
        )

    def run_dialog(self, scan: dict, current: dict) -> dict:
        """Run the interactive dialog and return the resulting config."""
        del scan, current
        raise NotImplementedError

    def save(self, data: dict) -> Path:
        """Persist the backend configuration and return the path."""
        config = Configuration(self.name, data=data, file_path=self.config_path())
        return config.save()

    def short_status(self) -> str:
        """Return a one-line status string for overview listings."""
        runtime = "available" if self.runtime_available() else "unavailable"
        dialog = "yes" if self.dialog_available(self.quick_scan()) else "no"
        return f"{self.name:<8} runtime={runtime:<11} guided_dialog={dialog}"


class SimpleBackendConfigurator(BackendConfigurator):
    """Convenience configurator for backends with mostly JSON scalar fields."""

    executable_fields: tuple[ExecutableField, ...] = ()
    default_flags: dict[str, list[str]] = {}
    default_prefixes: dict[str, str] = {}
    default_resource: dict[str, str] = {}
    fixed_values: dict[str, object] = {}
    parallel_choices: tuple[str, ...] | None = None

    def quick_scan(self) -> dict:
        """Return default executable guesses and host metadata."""
        scan = super().quick_scan()
        executables = {}
        for field in type(self).executable_fields:
            if field.key == "python":
                executables[field.key] = detect_python_executable()
            elif field.key == "f2py":
                executables[field.key] = detect_f2py_executable() or ""
            else:
                executables[field.key] = (
                    find_first_executable(*field.candidates)
                    if field.candidates
                    else None
                )
        scan["executables"] = executables
        return scan

    def dialog_available(self, scan: dict | None = None) -> bool:
        """Return whether the required executables were detected."""
        if scan is None:
            scan = self.quick_scan()
        if not type(self).executable_fields:
            return True
        values = scan.get("executables", {})
        return any(values.get(field.key) for field in type(self).executable_fields)

    def default_config(self, scan: dict) -> dict:
        """Build the default config dictionary from the scan."""
        data = super().default_config(scan)
        probe = self.system_probe()
        executables = {}
        scanned = scan.get("executables", {})
        for field in type(self).executable_fields:
            value = scanned.get(field.key)
            if value:
                executables[field.key] = value
            elif field.key == "python":
                executables[field.key] = probe.python()
            elif field.key == "f2py":
                executables[field.key] = probe.f2py() or "f2py"
            elif field.candidates:
                executables[field.key] = probe.default_executable(*field.candidates)
            else:
                executables[field.key] = field.key
        if executables:
            data["executables"] = executables
        if type(self).default_flags:
            data["flags"] = {
                key: list(value)
                for key, value in type(self).default_flags.items()
            }
        if type(self).default_prefixes:
            data["prefixes"] = dict(type(self).default_prefixes)
        if type(self).default_resource:
            data["resource"] = dict(type(self).default_resource)
        if type(self).fixed_values:
            data.update(type(self).fixed_values)
        return data

    def run_dialog(self, scan: dict, current: dict) -> dict:
        """Prompt for executables, flags, prefixes, and resource settings."""
        merged = self.merge_defaults(scan, current)
        print(f"Configuring backend '{self.name}'")
        print(self.description)
        merged["enabled"] = prompt_yes_no(
            "Enable backend",
            default=bool(merged.get("enabled", self.recommended_enabled(scan))),
        )

        if type(self).executable_fields:
            print("\nExecutables")
            merged.setdefault("executables", {})
            for field in type(self).executable_fields:
                default = merged["executables"].get(field.key, "")
                merged["executables"][field.key] = prompt_text(
                    field.label,
                    default=default,
                )

        if type(self).default_flags:
            print("\nFlags")
            merged.setdefault("flags", {})
            for key, default_values in type(self).default_flags.items():
                merged["flags"][key] = prompt_list(
                    f"{key.replace('_', ' ')}",
                    default=merged["flags"].get(key, default_values),
                )

        if type(self).default_prefixes:
            print("\nPrefixes")
            merged.setdefault("prefixes", {})
            for key, default in type(self).default_prefixes.items():
                merged["prefixes"][key] = prompt_text(
                    f"{key} prefix",
                    default=merged["prefixes"].get(key, default),
                )

        if type(self).default_resource:
            print("\nResource")
            merged.setdefault("resource", {})
            device_default = merged["resource"].get(
                "device", type(self).default_resource.get("device", "")
            )
            merged["resource"]["device"] = prompt_text(
                "device",
                default=device_default,
            )
            parallel_default = merged["resource"].get(
                "parallel_model",
                type(self).default_resource.get("parallel_model", ""),
            )
            if type(self).parallel_choices is None:
                merged["resource"]["parallel_model"] = prompt_text(
                    "parallel model",
                    default=parallel_default,
                )
            else:
                merged["resource"]["parallel_model"] = prompt_choice(
                    "parallel model",
                    list(type(self).parallel_choices),
                    default=parallel_default,
                )

        return merged
