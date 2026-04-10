from __future__ import annotations

__doc__ = """Generic atomic-region instruction used by backend-specific lowering."""

from typing import Any
import weakref

from .instruction import ContentInstruction, Instruction
from .instructionvar import InstructionEnvironment


class AtomicRegionInstruction(ContentInstruction, ftype="atomic"):
    """User-facing atomic wrapper around a region of instructions."""

    def __init__(
        self,
        content: Instruction,
        *,
        policy: str = "critical",
        attachment_mode: str = "leaf",
        itype: str | None = None,
    ):
        super().__init__(content, itype=itype)
        if policy not in {"critical", "off"}:
            raise ValueError(f"Unsupported atomic policy: {policy!r}")
        if attachment_mode not in {"leaf", "region"}:
            raise ValueError(
                f"Unsupported atomic attachment_mode: {attachment_mode!r}"
            )
        self._policy = policy
        self._attachment_mode = attachment_mode

    @property
    def policy(self) -> str:
        return self._policy

    @property
    def attachment_mode(self) -> str:
        return self._attachment_mode

    def contribute_to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "policy": self.policy,
            "attachment_mode": self.attachment_mode,
        }

    def record_payload(self, *, detailed: bool = False) -> dict[str, Any]:
        payload = super().record_payload(detailed=detailed)
        payload["policy"] = self.policy
        payload["attachment_mode"] = self.attachment_mode
        return payload

    def __deepcopy__(
        self, memo: dict[int, weakref.ReferenceType] | None = None, **kwargs: Any
    ) -> Instruction:
        if memo is None:
            memo = {}
        copied_content = self.content.deepcopy(memo=memo, **kwargs)
        copied = type(self)(
            copied_content,
            policy=self.policy,
            attachment_mode=self.attachment_mode,
            itype=self.itype,
            **kwargs,
        )
        memo[id(self)] = weakref.ref(copied)
        return copied

    def apply_environment(
        self, environment: InstructionEnvironment, **kwargs
    ) -> Instruction:
        return type(self)(
            self.content.apply_environment(environment),
            policy=self.policy,
            attachment_mode=self.attachment_mode,
            itype=self.itype,
            **kwargs,
        )


__all__ = ["AtomicRegionInstruction"]
