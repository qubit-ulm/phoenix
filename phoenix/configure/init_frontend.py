"""Standalone initialization dialogue frontend for Phoenix backends."""

from __future__ import annotations

import argparse

from .dialog import prompt_yes_no
from .service import ConfigurationService


def run_initialization_dialogue(service: ConfigurationService | None = None):
    """Run the initialization dialogue and persist the selected backends."""
    service = ConfigurationService() if service is None else service
    selection = {}
    print("Phoenix backend initialization")
    print("Select which backends shall be provided.\n")
    for backend in service.backend_names:
        recommended = service.recommended_backend_selection()[backend]
        selection[backend] = prompt_yes_no(
            f"Enable backend '{backend}'",
            default=recommended,
        )
    return service.initialize_backends(selection)


def build_parser() -> argparse.ArgumentParser:
    """Create the standalone init parser."""
    parser = argparse.ArgumentParser(
        description="Initialize Phoenix backend configurations."
    )
    parser.add_argument("--gui", action="store_true", help="open the initialization GUI")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the standalone initialization frontend."""
    parser = build_parser()
    args = parser.parse_args(argv)
    service = ConfigurationService()
    if args.gui:
        from .gui import launch_initialization_gui

        launch_initialization_gui(service)
        return 0

    written = run_initialization_dialogue(service)
    for backend, path in written.items():
        print(f"{backend}: wrote {path}")
    return 0


__all__ = ["main", "run_initialization_dialogue"]
