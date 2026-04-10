"""Standalone settings GUI launcher."""

from __future__ import annotations

import argparse

from .gui import launch_settings_gui
from .service import ConfigurationService


def build_parser() -> argparse.ArgumentParser:
    """Create the standalone GUI parser."""
    parser = argparse.ArgumentParser(description="Open the Phoenix configuration GUI.")
    parser.add_argument("scope", nargs="?", help="optional scope: general or backend name")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the standalone settings GUI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    service = ConfigurationService()
    scope = args.scope.lower() if args.scope else None
    if scope is not None and scope not in {"general", *service.backend_names}:
        parser.error(
            "unknown scope "
            + scope
            + "; choose general or one of "
            + ", ".join(service.backend_names)
        )
    launch_settings_gui(service, scope=scope)
    return 0


__all__ = ["main"]
