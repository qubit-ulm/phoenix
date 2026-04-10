"""
Stable checksum helpers for reproducible build identities.

The routines in this module normalize nested payloads into a deterministic,
JSON-compatible structure and derive cryptographic digests from it. The
helpers are intentionally conservative: only explicitly supported primitive or
container-like values are serialized automatically, while richer objects are
expected to provide a ``checksum_payload()`` method.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _class_name(value: type) -> str:
    """Return the fully-qualified name of a class object."""
    return f"{value.__module__}.{value.__qualname__}"


def stable_normalize(value, _active=None):
    """Normalize a value into a deterministic JSON-compatible structure."""
    if _active is None:
        _active = set()
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="surrogateescape")
    if isinstance(value, dict):
        marker = id(value)
        if marker in _active:
            return {"__type__": "cycle", "class": "dict"}
        _active.add(marker)
        normalized = []
        for key, item in value.items():
            normalized.append(
                (
                    stable_normalize(key, _active=_active),
                    stable_normalize(item, _active=_active),
                )
            )
        normalized.sort(key=lambda pair: json.dumps(pair[0], sort_keys=True))
        _active.remove(marker)
        return {"__type__": "dict", "items": normalized}
    if isinstance(value, (list, tuple)):
        marker = id(value)
        if marker in _active:
            return {"__type__": "cycle", "class": type(value).__name__}
        _active.add(marker)
        normalized = [stable_normalize(item, _active=_active) for item in value]
        _active.remove(marker)
        return normalized
    if isinstance(value, (set, frozenset)):
        marker = id(value)
        if marker in _active:
            return {"__type__": "cycle", "class": type(value).__name__}
        _active.add(marker)
        normalized = [stable_normalize(item, _active=_active) for item in value]
        normalized.sort(key=lambda item: json.dumps(item, sort_keys=True))
        _active.remove(marker)
        return {"__type__": "set", "items": normalized}
    if isinstance(value, type):
        return {"__type__": "class", "name": _class_name(value)}
    marker = id(value)
    if marker in _active:
        return {"__type__": "cycle", "class": _class_name(type(value))}
    if hasattr(value, "checksum_payload"):
        _active.add(marker)
        normalized = stable_normalize(value.checksum_payload(), _active=_active)
        _active.remove(marker)
        return normalized
    if hasattr(value, "to_dict"):
        _active.add(marker)
        normalized = stable_normalize(value.to_dict(), _active=_active)
        _active.remove(marker)
        return normalized
    if hasattr(value, "__dict__"):
        return {
            "__type__": "object",
            "class": _class_name(type(value)),
            "repr": repr(value),
        }
    return repr(value)


def stable_dumps(value) -> str:
    """Serialize a normalized value in a canonical JSON representation."""
    normalized = stable_normalize(value)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def stable_checksum(value, *, algorithm: str = "sha256") -> str:
    """Return a stable hexadecimal digest for a payload."""
    payload = stable_dumps(value).encode("utf-8")
    return hashlib.new(algorithm, payload).hexdigest()
