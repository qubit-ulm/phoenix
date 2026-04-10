"""
Portable link helper used by generated makefile targets.

The helper tries to create a symbolic link from ``destination`` to ``source``.
If symlinks are unavailable on the current platform or filesystem, it falls
back to a hard link and finally to a regular file copy.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def create_portable_link(source: str | Path, destination: str | Path) -> None:
    """Create a stable outward link or copy for a built artifact."""
    src = Path(source).resolve()
    dst = Path(destination)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists() or dst.is_symlink():
        try:
            if dst.resolve() == src:
                return
        except OSError:
            pass
        if dst.is_dir() and not dst.is_symlink():
            raise IsADirectoryError(f"Cannot overwrite directory '{dst}'.")
        dst.unlink()

    try:
        dst.symlink_to(src)
        return
    except (NotImplementedError, OSError):
        pass

    try:
        dst.hardlink_to(src)
        return
    except (NotImplementedError, OSError):
        pass

    try:
        shutil.copy2(src, dst)
    except shutil.SameFileError:
        return


def main(argv: list[str] | None = None) -> int:
    """CLI entry point used from makefile rules."""
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 2:
        raise SystemExit("usage: python -m phoenix.fgen.link_helper SRC DST")
    create_portable_link(argv[0], argv[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
