"""Fórmulas centralizadas de indicadores. El dashboard y el agente deben usar solo estas."""

from __future__ import annotations

RATE_OUTCOMES = ("Promovido", "No promovido", "Retirado", "Retirado definitivo")
WITHDRAWAL_OUTCOMES = ("Retirado", "Retirado definitivo")
PROMOTION_OUTCOME = "Promovido"
NON_PROMOTION_OUTCOME = "No promovido"
VIGENTE_OUTCOME = "Vigente"
IGNORADO_LABEL = "Ignorado"
REPITENTE_YES = "Sí"
REPITENTE_NO = "No"


def _get(counts: dict[str, int], key: str) -> int:
    return int(counts.get(key, 0))


def rate_denominator(counts: dict[str, int]) -> int:
    return sum(_get(counts, name) for name in RATE_OUTCOMES)


def percent(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return (numerator / denominator) * 100.0


def enrollment_total(counts: dict[str, int]) -> int:
    return sum(int(n) for n in counts.values())


def promotion_parts(counts: dict[str, int]) -> tuple[float | None, int, int]:
    num = _get(counts, PROMOTION_OUTCOME)
    den = rate_denominator(counts)
    return percent(num, den), num, den


def non_promotion_parts(counts: dict[str, int]) -> tuple[float | None, int, int]:
    num = _get(counts, NON_PROMOTION_OUTCOME)
    den = rate_denominator(counts)
    return percent(num, den), num, den


def withdrawal_parts(counts: dict[str, int]) -> tuple[float | None, int, int]:
    num = sum(_get(counts, name) for name in WITHDRAWAL_OUTCOMES)
    den = rate_denominator(counts)
    return percent(num, den), num, den


def repetition_parts(counts: dict[str, int]) -> tuple[float | None, int, int]:
    """Tasa de repitencia: Sí / (Sí + No). Ignorado queda fuera del denominador."""
    num = _get(counts, REPITENTE_YES)
    den = num + _get(counts, REPITENTE_NO)
    return percent(num, den), num, den


def vigente_count(counts: dict[str, int]) -> int:
    return _get(counts, VIGENTE_OUTCOME)


def ignorado_count(counts: dict[str, int]) -> int:
    return _get(counts, IGNORADO_LABEL)
