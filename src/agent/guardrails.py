"""Rechazo de preguntas fuera de alcance y aclaración de preguntas ambiguas."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

GuardStatus = Literal["ok", "reject", "clarify"]


def fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text or "")
    stripped = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return stripped.lower()


_REJECT_PATTERNS = [
    r"\bnotas?\b",
    r"\bcalificacion",
    r"\bpromedio de notas",
    r"\bdiscapacidad",
    r"\bnecesidades especiales\b",
    r"\bdesde 20\d{2}\b",
    r"\bhistor",
    r"\bserie temporal\b",
    r"\banios anteriores\b",
    r"\banos anteriores\b",
    r"\b2020\b",
    r"\b2021\b",
    r"\b2022\b",
    r"\b2023\b",
    r"\bpredic",
    r"\bpronostic",
    r"\bfuturo\b",
    r"\bdocentes?\b",
    r"\binfraestruct",
    r"\bedad\b",
    r"\bedades\b",
]

_CLARIFY_PATTERNS = [
    r"\bmejor departamento\b",
    r"\bpeor departamento\b",
    r"\bmas problemas\b",
    r"\bdonde hay mas problemas",
    r"\bmejor municipio\b",
    r"\bcual es el mejor\b",
    r"\bque tan bien\b",
]

_REJECT_MSG = (
    "Esta pregunta está fuera del alcance del MVP. El dataset 2024 no incluye notas, "
    "discapacidad, edad, docentes, infraestructura ni series históricas, y no hacemos predicciones. "
    "Puedes preguntar por inscripciones, promoción, no promoción, retiro o repitencia del ciclo 2024."
)

_CLARIFY_MSG = (
    "Necesito una métrica concreta. Por ejemplo: más inscripciones, mayor tasa de retiro, "
    "o comparar promoción entre dos departamentos. ¿Qué indicador quieres ver?"
)


def inspect_question(question: str) -> tuple[GuardStatus, str | None]:
    text = fold(question).strip()
    if len(text) < 4:
        return "clarify", "Escribe una pregunta sobre inscripciones o tasas del ciclo 2024."
    for pattern in _REJECT_PATTERNS:
        if re.search(pattern, text):
            return "reject", _REJECT_MSG
    for pattern in _CLARIFY_PATTERNS:
        if re.search(pattern, text):
            return "clarify", _CLARIFY_MSG
    return "ok", None
