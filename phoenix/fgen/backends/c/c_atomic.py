from __future__ import annotations

__doc__ = """C-specific atomic wrappers used after backend optimization."""

from typing import Any

from ...atomic import AtomicRegionInstruction
from ...codecontainer import EmbeddingContainer
from ...instruction import (
    ContentInstruction,
)


class CAtomicInstruction(ContentInstruction, ftype="c_atomic"):
    """C-backend internal atomic wrapper after optimizer resolution."""

    def __init__(
        self,
        content,
        *,
        attachment_mode: str = "region",
        itype: str | None = None,
    ):
        super().__init__(content, itype=itype)
        if attachment_mode not in {"leaf", "region"}:
            raise ValueError(
                f"Unsupported atomic attachment_mode: {attachment_mode!r}"
            )
        self._attachment_mode = attachment_mode

    @property
    def attachment_mode(self) -> str:
        return self._attachment_mode

    def contribute_to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "attachment_mode": self.attachment_mode,
        }

    def record_payload(self, *, detailed: bool = False) -> dict[str, Any]:
        payload = super().record_payload(detailed=detailed)
        payload["attachment_mode"] = self.attachment_mode
        return payload


class CAtomicLeafContainer(EmbeddingContainer):
    """Wrap one emitted C statement in an OpenMP atomic pragma."""

    def generate_head_containers(self):
        yield from self.codelines_from_text("#pragma omp atomic")


class CAtomicRegionContainer(EmbeddingContainer):
    """Wrap one emitted C region in an OpenMP critical section."""

    INDENT_BODY = True

    def generate_head_containers(self):
        yield from self.codelines_from_text("#pragma omp critical")
        yield from self.codelines_from_text("{")

    def generate_foot_containers(self):
        yield from self.codelines_from_text("}")


def _handle_c_atomic_instruction(self, instruction, context, buildargs):
    container_class = (
        CAtomicLeafContainer
        if instruction.attachment_mode == "leaf"
        else CAtomicRegionContainer
    )
    atomic_container = container_class(context=context, **buildargs)
    for child in self.containers_from_instruction(
        instruction.content,
        context=atomic_container.context,
        **buildargs,
    ):
        atomic_container.append(child)
    yield atomic_container


def _handle_atomic_region_instruction(self, instruction, context, buildargs):
    from .c_resource import is_c_omp_resource

    resource = buildargs.get("resource")
    if instruction.policy == "off" or not is_c_omp_resource(resource):
        yield from self.containers_from_instruction(
            instruction.content,
            context=context,
            **buildargs,
        )
        return
    yield from _handle_c_atomic_instruction(
        self,
        CAtomicInstruction(
            instruction.content,
            attachment_mode="region",
            itype=instruction.itype,
        ),
        context,
        buildargs,
    )


def register_c_atomic_handlers(builder_class) -> None:
    builder_class.set_instruction_class_handler(
        AtomicRegionInstruction,
        _handle_atomic_region_instruction,
    )
    builder_class.set_instruction_class_handler(
        CAtomicInstruction,
        _handle_c_atomic_instruction,
    )


__all__ = [
    "CAtomicInstruction",
    "CAtomicLeafContainer",
    "CAtomicRegionContainer",
    "register_c_atomic_handlers",
]
