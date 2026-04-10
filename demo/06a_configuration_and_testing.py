"""
Demo 06a: configuration CLI and backend smoke tests.

This script is intentionally conservative: it only runs read-only queries plus
the ``--test`` entry point. It does not open the GUI and it does not write new
configuration values. That makes it a safe onboarding demo for an already
configured development environment.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    """
    Execute the configuration CLI through the active Python interpreter.

    Using ``sys.executable -m phoenix.configure`` ensures the same virtual
    environment is used that also imports the library for this demo.
    """

    command = [sys.executable, "-m", "phoenix.configure", *arguments]
    return subprocess.run(command, capture_output=True, text=True, check=False)


def print_run(title: str, *arguments: str) -> None:
    """
    Run one CLI command and print both the command line and its output.

    Showing the exact invocation is part of the tutorial value: a user should
    be able to copy the command directly after reading the demo output.
    """

    command = [sys.executable, "-m", "phoenix.configure", *arguments]
    result = run_cli(*arguments)

    print(title)
    print("-" * len(title))
    print("Command :", shlex.join(command))
    print("Exit code:", result.returncode)
    if result.stdout.strip():
        print("Stdout:")
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print("Stderr:")
        print(result.stderr.rstrip())
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Demonstrate the configuration CLI and smoke-test entry point."
    )
    parser.add_argument(
        "--backend",
        default="python",
        help="backend name used for --show and --test examples",
    )
    parser.add_argument(
        "--skip-test",
        action="store_true",
        help="skip the backend smoke test run",
    )
    args = parser.parse_args()

    print("Demo 06a: configuration and testing")
    print("=" * 72)
    print(
        "This demo only performs read-only CLI queries plus an optional backend"
    )
    print("smoke test. It does not rewrite backend configuration files.")
    print()

    # First show the high-level backend state table. This is the broadest
    # overview and is therefore the natural first command for a new user.
    print_run("Backend status overview", "--status")

    # Next show a single dotted-path lookup. This demonstrates the gsettings-
    # style configuration access model without mutating any values.
    print_run(
        "Read one dotted general setting",
        "general.runtime.zero_tolerance",
    )

    # Showing one backend scope is useful once the user wants to inspect the
    # resolved current/default configuration in JSON form.
    print_run("Show one backend scope as JSON", "--show", args.backend)

    # ``--test`` is intentionally last because it can take longer than the
    # status and lookup commands. The demo keeps it optional for environments
    # where only the read-only walkthrough is desired.
    if not args.skip_test:
        print_run("Run one backend smoke test", "--test", args.backend)


if __name__ == "__main__":
    main()
