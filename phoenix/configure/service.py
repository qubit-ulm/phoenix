"""Shared configuration service for Phoenix configuration frontends."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .backends import CONFIGURATORS, get_configurator
from ..fgen.backend_config import Configuration


def parse_value(raw: str) -> Any:
    """Parse a CLI/GUI string into a Python value."""
    text = raw.strip()
    if text == "":
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        lowered = text.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered == "null":
            return None
        return raw


def format_value(value: Any) -> str:
    """Return a stable string representation for CLI/GUI usage."""
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True)


@dataclass(frozen=True)
class ScopeInfo:
    """Resolved configuration scope for a dotted path."""

    scope: str
    local_path: tuple[str, ...]


class ConfigurationService:
    """Facade used by the CLI, dialog, init, and GUI frontends."""

    def __init__(self):
        self._configurators = CONFIGURATORS

    @property
    def backend_names(self) -> tuple[str, ...]:
        """Return all known backend names."""
        return tuple(sorted(self._configurators))

    def resolve_scope(self, dotted_path: str) -> ScopeInfo:
        """Resolve ``dotted_path`` into ``general`` or one backend scope."""
        parts = Configuration.split_path(dotted_path)
        head = parts[0].lower()
        if head == "general":
            return ScopeInfo(scope="general", local_path=parts[1:])
        if head in self._configurators:
            return ScopeInfo(scope=head, local_path=parts[1:])
        return ScopeInfo(scope="general", local_path=parts)

    def load_scope(self, scope: str) -> Configuration:
        """Load one configuration scope."""
        if scope == "general":
            return Configuration.general()
        return Configuration.for_backend(scope)

    def default_scope(self, scope: str) -> dict[str, Any]:
        """Return default data for one scope."""
        if scope == "general":
            return Configuration.general().to_dict()
        configurator = get_configurator(scope)
        return configurator.enrich_config(configurator.default_config(configurator.quick_scan()))

    def current_or_default_scope(self, scope: str) -> dict[str, Any]:
        """Return persisted data if present, otherwise defaults."""
        if scope == "general":
            return self.load_scope("general").to_dict()
        config = self.load_scope(scope)
        data = config.to_dict()
        if data:
            return data
        return self.default_scope(scope)

    def show_scope(self, scope: str) -> str:
        """Render one scope as JSON."""
        data = self.current_or_default_scope(scope)
        return json.dumps(data, indent=2, sort_keys=True)

    def get_value(self, dotted_path: str) -> Any:
        """Read one dotted configuration value."""
        resolved = self.resolve_scope(dotted_path)
        config = self.load_scope(resolved.scope)
        if not resolved.local_path:
            return config.to_dict()
        return config.get_path(resolved.local_path, default=None)

    def set_value(self, dotted_path: str, value: Any) -> Path:
        """Set one dotted configuration value and persist it."""
        resolved = self.resolve_scope(dotted_path)
        config = self._scope_with_defaults(resolved.scope)
        if not resolved.local_path:
            if not isinstance(value, dict):
                raise ValueError("setting a whole scope requires a JSON object")
            config.update(value)
        else:
            config.set_path(resolved.local_path, value)
        return self.save_scope(resolved.scope, config)

    def _scope_with_defaults(self, scope: str) -> Configuration:
        if scope == "general":
            return self.load_scope("general")
        current = self.load_scope(scope).to_dict()
        configurator = get_configurator(scope)
        merged = configurator.merge_defaults(configurator.quick_scan(), current)
        merged = configurator.enrich_config(merged)
        return Configuration(scope, data=merged, file_path=Configuration.default_file(scope))

    def save_scope(self, scope: str, config: Configuration) -> Path:
        """Persist one scope and refresh backend support files when relevant."""
        if scope != "general":
            configurator = get_configurator(scope)
            data = configurator.enrich_config(config.to_dict())
            config = Configuration(scope, data=data, file_path=Configuration.default_file(scope))
            target = config.save()
            self.prepare_backend_support(scope, data)
            return target
        return config.save(Configuration.default_file("general"))

    def prepare_backend_support(self, backend: str, data: dict[str, Any]) -> list[str]:
        """Write backend support files without building support artifacts."""
        configurator = get_configurator(backend)
        messages = []
        configurator.write_support_files(data)
        messages.append(f"Generated support makefile {data['support']['makefile']}")
        return messages

    def build_backend_support(self, backend: str) -> list[str]:
        """Write support files and build backend support artifacts."""
        configurator = get_configurator(backend)
        data = self._scope_with_defaults(backend).to_dict()
        messages = self.prepare_backend_support(backend, data)
        result = configurator.build_support(data)
        if result is not None:
            messages.append(result)
        return messages

    def configure_backend_dialogue(self, backend: str) -> tuple[Path, dict[str, Any], list[str]]:
        """Run the per-backend dialogue and persist the result."""
        configurator = get_configurator(backend)
        scan = configurator.quick_scan()
        current = configurator.load_current()
        data = configurator.enrich_config(configurator.run_dialog(scan, current))
        target = Configuration(backend, data=data, file_path=configurator.config_path()).save()
        messages = self.prepare_backend_support(backend, data)
        return target, data, messages

    def reset_backend(self, backend: str) -> tuple[Path, dict[str, Any], list[str]]:
        """Reset one backend configuration to scan-derived defaults."""
        configurator = get_configurator(backend)
        data = configurator.enrich_config(
            configurator.default_config(configurator.quick_scan())
        )
        target = Configuration(
            backend,
            data=data,
            file_path=configurator.config_path(),
        ).save()
        messages = self.prepare_backend_support(backend, data)
        return target, data, messages

    def clear_backend(self, backend: str) -> Path:
        """Remove one backend configuration file if it exists."""
        configurator = get_configurator(backend)
        target = configurator.config_path()
        if target.exists():
            target.unlink()
        return target

    def initialize_backends(
        self, enabled_by_backend: dict[str, bool], *, build_supports: bool = False
    ) -> dict[str, Path]:
        """Initialize backend configs from scans and explicit enable flags."""
        written: dict[str, Path] = {}
        for backend in self.backend_names:
            configurator = get_configurator(backend)
            current = configurator.load_current()
            scan = configurator.quick_scan()
            data = configurator.merge_defaults(scan, current)
            data["enabled"] = bool(enabled_by_backend.get(backend, data.get("enabled", False)))
            data = configurator.enrich_config(data)
            target = Configuration(
                backend,
                data=data,
                file_path=configurator.config_path(),
            ).save()
            self.prepare_backend_support(backend, data)
            written[backend] = target
        if build_supports:
            for backend in self.backend_names:
                self.build_backend_support(backend)
        return written

    def initialize_auto(self) -> dict[str, Path]:
        """Initialize all backends and execute all support builds."""
        return self.initialize_backends(
            self.recommended_backend_selection(),
            build_supports=True,
        )

    def recommended_backend_selection(self) -> dict[str, bool]:
        """Return recommended enable flags based on host detection."""
        return {
            backend: get_configurator(backend).recommended_enabled()
            for backend in self.backend_names
        }

    def backend_status_rows(self) -> list[dict[str, str]]:
        """Return human-readable backend status rows."""
        rows = []
        for backend in self.backend_names:
            configurator = get_configurator(backend)
            scan = configurator.quick_scan()
            current = configurator.load_current()
            configured = configurator.config_exists()
            enabled = current.get("enabled", configurator.recommended_enabled(scan))
            detected = configurator.dialog_available(scan)
            ready = configured and configurator.support_ready(current)
            if configured and enabled:
                state = "enabled"
            elif configured:
                state = "disabled"
            elif detected:
                state = "available"
            else:
                state = "supported"
            rows.append(
                {
                    "backend": backend,
                    "state": state,
                    "configured": "yes" if configured else "no",
                    "enabled": "yes" if enabled else "no",
                    "detected": "yes" if detected else "no",
                    "ready": "yes" if ready else "no",
                }
            )
        return rows

    def render_status(self) -> str:
        """Return a compact backend status table."""
        header = f"{'backend':<10}{'state':<12}{'configured':<12}{'enabled':<10}{'detected':<10}{'ready':<10}"
        lines = [header, "-" * len(header)]
        for row in self.backend_status_rows():
            lines.append(
                f"{row['backend']:<10}{row['state']:<12}{row['configured']:<12}"
                f"{row['enabled']:<10}{row['detected']:<10}{row['ready']:<10}"
            )
        return "\n".join(lines)

    def flattened_rows(self, scope: str | None = None) -> list[dict[str, str]]:
        """Return flattened rows for the settings GUI."""
        scopes = ["general", *self.backend_names] if scope is None else [scope]
        rows = []
        for item in scopes:
            current = Configuration(item, data=self.current_or_default_scope(item))
            defaults = Configuration(item, data=self.default_scope(item))
            row_map = {}
            for path, value in defaults.iter_paths(prefix=(item,)):
                row_map[path] = {
                    "path": ".".join(path),
                    "value": format_value(current.get_path(path[1:], default=value)),
                    "default": format_value(value),
                }
            for path, value in current.iter_paths(prefix=(item,)):
                row_map[path] = {
                    "path": ".".join(path),
                    "value": format_value(value),
                    "default": format_value(defaults.get_path(path[1:], default="")),
                }
            for path in sorted(row_map):
                dotted = ".".join(path)
                row = row_map[path]
                row["path"] = dotted
                rows.append(row)
        return rows
