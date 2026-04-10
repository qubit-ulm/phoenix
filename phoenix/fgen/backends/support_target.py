from __future__ import annotations

__doc__ = """Makefile targets that build backend-specific support packages."""

from pathlib import Path

from ..makefile import MFTSpecial


class BackendSupportBuildTarget(
    MFTSpecial, silent=True, phony=True, identifier="BACKENDSUPPORT"
):
    """Makefile target that builds a configured backend support package."""

    def __init__(
        self,
        name,
        *,
        support_root,
        makefile,
        build_target,
        required_files=None,
    ):
        makefile_path = Path(makefile)
        support_root_path = Path(support_root)
        commands = [f'test -f "{makefile_path}"']
        commands.append(
            f'$(MAKE) -C "{support_root_path}" -f "{makefile_path.name}" {build_target}'
        )
        for required in required_files or ():
            commands.append(f'test -f "{Path(required)}"')
        super().__init__(name, commands=commands)


__all__ = ["BackendSupportBuildTarget"]
