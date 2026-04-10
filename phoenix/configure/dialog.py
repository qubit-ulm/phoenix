"""Small interactive prompt helpers for backend configuration."""

from __future__ import annotations


def prompt_text(label: str, default: str | None = None) -> str:
    """Prompt for a text value and fall back to ``default`` on empty input."""
    suffix = ""
    if default not in (None, ""):
        suffix = f" [{default}]"
    value = input(f"{label}{suffix}: ").strip()
    if value:
        return value
    return "" if default is None else str(default)


def prompt_choice(
    label: str,
    choices: list[str] | tuple[str, ...],
    default: str | None = None,
) -> str:
    """Prompt until a value from ``choices`` is entered."""
    choice_list = "/".join(choices)
    while True:
        value = prompt_text(f"{label} ({choice_list})", default=default)
        if value in choices:
            return value
        print(f"Please enter one of: {choice_list}")


def prompt_list(label: str, default: list[str] | tuple[str, ...] | None = None) -> list[str]:
    """Prompt for a comma-separated list."""
    if default is None:
        default_text = ""
    else:
        default_text = ", ".join(default)
    raw = prompt_text(label, default=default_text)
    if not raw.strip():
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def prompt_yes_no(label: str, default: bool = True) -> bool:
    """Prompt for a boolean choice."""
    default_text = "y" if default else "n"
    while True:
        value = prompt_text(f"{label} (y/n)", default=default_text).lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please enter y or n.")
