"""CLI for Phoenix configuration access, editing, and initialization."""

from __future__ import annotations

import argparse
import json

from .service import ConfigurationService, format_value, parse_value


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Phoenix configuration access and backend initialization."
    )
    parser.add_argument("target", nargs="?", help="scope or dotted configuration path")
    parser.add_argument("value", nargs="?", help="value for dotted path updates")
    parser.add_argument("--show", action="store_true", help="show one scope as JSON")
    parser.add_argument("--status", action="store_true", help="show backend status")
    parser.add_argument(
        "--dialogue",
        nargs="?",
        const="",
        metavar="BACKEND",
        help="run the guided dialogue for one backend or 'all'",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="open the settings GUI for all scopes or the selected target/backend",
    )
    parser.add_argument(
        "--initialize-dialogue",
        action="store_true",
        help="run the initialization dialogue",
    )
    parser.add_argument(
        "--initialize-gui",
        action="store_true",
        help="run the initialization GUI",
    )
    parser.add_argument(
        "--initialize-auto",
        action="store_true",
        help="initialize all auto-detected backends and build their supports",
    )
    parser.add_argument(
        "--test",
        metavar="BACKEND",
        help="run backend smoke tests for one backend or 'all'",
    )
    parser.add_argument(
        "--reset",
        nargs="?",
        const="",
        metavar="BACKEND",
        help="reset one backend configuration to detected defaults",
    )
    parser.add_argument(
        "--clear",
        nargs="?",
        const="",
        metavar="BACKEND",
        help="remove one backend configuration file",
    )
    parser.add_argument(
        "--build",
        nargs="?",
        const="",
        metavar="BACKEND",
        help="write and build backend support makefiles for one backend or 'all'",
    )
    return parser


def _show_value(value) -> None:
    if isinstance(value, dict):
        print(json.dumps(value, indent=2, sort_keys=True))
        return
    print(format_value(value))


def _run_dialogue(service: ConfigurationService, backend: str) -> int:
    if backend == "all":
        for name in service.backend_names:
            target, _, messages = service.configure_backend_dialogue(name)
            print(f"Wrote {target}")
            for message in messages:
                print(message)
            print()
        return 0

    target, _, messages = service.configure_backend_dialogue(backend)
    print(f"Wrote {target}")
    for message in messages:
        print(message)
    return 0


def _resolve_backend_mode_target(
    parser: argparse.ArgumentParser,
    service: ConfigurationService,
    explicit: str | None,
    positional: str | None,
    *,
    allow_all: bool,
    mode: str,
) -> str:
    backend = None
    if explicit:
        backend = explicit.lower()
    elif positional:
        if positional.lower() == "all" and allow_all:
            backend = "all"
        else:
            resolved = service.resolve_scope(positional)
            backend = resolved.scope
    else:
        backend = "all" if allow_all else None
    if backend is None:
        parser.error(
            f"{mode} expects a backend; choose from "
            + ", ".join(service.backend_names)
        )
    if backend == "general":
        parser.error(
            f"{mode} expects a backend scope, not 'general'; choose from "
            + ", ".join(service.backend_names)
            + (", or 'all'" if allow_all else "")
        )
    if backend == "all" and allow_all:
        return backend
    if backend not in service.backend_names:
        parser.error(
            f"unknown backend for {mode}: "
            + backend
            + "; choose from "
            + ", ".join(service.backend_names)
            + (", or 'all'" if allow_all else "")
        )
    return backend


def main(argv: list[str] | None = None) -> int:
    """Run the Phoenix configuration CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    service = ConfigurationService()

    mode_count = sum(
        bool(item)
        for item in (
            args.status,
            args.dialogue,
            args.gui,
            args.initialize_dialogue,
            args.initialize_gui,
            args.initialize_auto,
            args.test,
            args.reset is not None,
            args.clear is not None,
            args.build is not None,
        )
    )
    if mode_count > 1:
        parser.error("choose only one of --status, --dialogue, --gui, --initialize-dialogue, --initialize-gui, --initialize-auto, --test, --reset, --clear, or --build")

    if args.status:
        print(service.render_status())
        return 0

    if args.dialogue is not None:
        backend = _resolve_backend_mode_target(
            parser,
            service,
            args.dialogue,
            args.target,
            allow_all=True,
            mode="--dialogue",
        )
        return _run_dialogue(service, backend)

    if args.initialize_dialogue:
        from .init_frontend import run_initialization_dialogue

        written = run_initialization_dialogue(service)
        for backend, path in written.items():
            print(f"{backend}: wrote {path}")
        return 0

    if args.initialize_gui:
        from .gui import launch_initialization_gui

        launch_initialization_gui(service)
        return 0

    if args.initialize_auto:
        written = service.initialize_auto()
        for backend, path in written.items():
            print(f"{backend}: wrote {path}")
        return 0

    if args.gui:
        from .gui import launch_settings_gui

        scope = None
        if args.target:
            resolved = service.resolve_scope(args.target)
            scope = resolved.scope
        launch_settings_gui(service, scope=scope)
        return 0

    if args.test:
        from .testing import GENERATION_BACKENDS, run_selected_backend_tests

        backend = _resolve_backend_mode_target(
            parser,
            service,
            args.test,
            args.target,
            allow_all=True,
            mode="--test",
        )
        if backend != "all" and backend not in GENERATION_BACKENDS:
            parser.error(
                "unknown backend for --test: "
                + backend
                + "; choose from "
                + ", ".join(GENERATION_BACKENDS)
                + ", or 'all'"
            )
        reports = run_selected_backend_tests(backend)
        exit_code = 0
        for report in reports:
            print(report.render())
            print()
            if not report.passed:
                exit_code = 1
        return exit_code

    if args.reset is not None:
        backend = _resolve_backend_mode_target(
            parser,
            service,
            args.reset,
            args.target,
            allow_all=True,
            mode="--reset",
        )
        if backend == "all":
            for name in service.backend_names:
                target, _, messages = service.reset_backend(name)
                print(f"Wrote {target}")
                for message in messages:
                    print(message)
                print()
            return 0
        target, _, messages = service.reset_backend(backend)
        print(f"Wrote {target}")
        for message in messages:
            print(message)
        return 0

    if args.clear is not None:
        backend = _resolve_backend_mode_target(
            parser,
            service,
            args.clear,
            args.target,
            allow_all=True,
            mode="--clear",
        )
        if backend == "all":
            for name in service.backend_names:
                target = service.clear_backend(name)
                print(f"Cleared {target}")
            return 0
        target = service.clear_backend(backend)
        print(f"Cleared {target}")
        return 0

    if args.build is not None:
        backend = _resolve_backend_mode_target(
            parser,
            service,
            args.build,
            args.target,
            allow_all=True,
            mode="--build",
        )
        targets = service.backend_names if backend == "all" else (backend,)
        for name in targets:
            messages = service.build_backend_support(name)
            for message in messages:
                print(message)
            if backend == "all":
                print()
        return 0

    if args.show:
        scope = "general"
        if args.target:
            resolved = service.resolve_scope(args.target)
            scope = resolved.scope if not resolved.local_path else resolved.scope
        print(service.show_scope(scope))
        return 0

    if args.target and args.value is not None:
        target = service.set_value(args.target, parse_value(args.value))
        print(target)
        return 0

    if args.target:
        value = service.get_value(args.target)
        _show_value(value)
        return 0

    print(service.render_status())
    return 0


__all__ = ["main"]
