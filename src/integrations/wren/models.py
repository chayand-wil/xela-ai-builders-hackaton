"""Contratos pequeños y serializables del adaptador WrenAI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WrenStatus:
    enabled: bool
    available: bool
    ready: bool
    message: str


@dataclass(frozen=True)
class WrenResult:
    rows: list[dict[str, Any]] = field(default_factory=list)
    provider: str = "wren"
