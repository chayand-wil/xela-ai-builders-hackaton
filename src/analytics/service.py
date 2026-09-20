"""Interfaz única de analítica para dashboard Streamlit y el agente."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from src.analytics import indicators as ind
from src.analytics import narratives
from src.analytics.paths import get_parquet_path
from src.analytics.queries import FILTER_KEYS, DuckDBStore, normalize_filters, resolve_column

__all__ = ["FILTER_KEYS", "AnalyticsService", "get_analytics", "get_parquet_path"]

MetricName = Literal[
    "enrollment_count",
    "promotion_rate",
    "non_promotion_rate",
    "withdrawal_rate",
    "repetition_rate",
    "distribution",
    "ranking",
    "comparison",
]

RATE_METRICS = {
    "promotion_rate",
    "non_promotion_rate",
    "withdrawal_rate",
    "repetition_rate",
}

_RATE_LABELS = {
    "promotion_rate": "Tasa de promoción",
    "non_promotion_rate": "Tasa de no promoción",
    "withdrawal_rate": "Tasa de retiro",
    "repetition_rate": "Tasa de repitencia",
}


def _empty_result(metric: str, filters: dict, unit: str = "none") -> dict[str, Any]:
    return {
        "metric": metric,
        "value": None,
        "unit": unit,
        "filters": filters,
        "numerator": None,
        "denominator": None,
        "rows": [],
        "narrative": "",
    }


def _rate_from_counts(metric: str, counts: dict[str, int]) -> tuple[float | None, int | None, int | None]:
    if metric == "promotion_rate":
        return ind.promotion_parts(counts)
    if metric == "non_promotion_rate":
        return ind.non_promotion_parts(counts)
    if metric == "withdrawal_rate":
        return ind.withdrawal_parts(counts)
    if metric == "repetition_rate":
        return ind.repetition_parts(counts)
    raise ValueError(f"Métrica de tasa desconocida: {metric}")


class AnalyticsService:
    def __init__(self, parquet_path: str | None = None) -> None:
        self.parquet_path = parquet_path or get_parquet_path()
        self.store = DuckDBStore(self.parquet_path)
        self._options_cache: dict[str, Any] | None = None

    def filter_options(self) -> dict[str, Any]:
        """Listas distintas para cada FILTER_KEYS, ordenadas. Usado por el sidebar."""
        if self._options_cache is None:
            options: dict[str, Any] = {
                key: self.store.distinct_values(column) for key, column in FILTER_KEYS.items()
            }
            options["municipality_by_department"] = self.store.municipalities_by_department()
            self._options_cache = options
        return self._options_cache

    def kpis(self, filters: dict | None = None) -> dict[str, Any]:
        """enrollment_count + tres tasas + counts de vigente/ignorado. Para tarjetas."""
        cleaned = normalize_filters(filters)
        outcomes = self.store.outcome_counts(cleaned)
        enrollment = self.compute("enrollment_count", cleaned)
        promo_v, promo_n, promo_d = ind.promotion_parts(outcomes)
        non_v, non_n, non_d = ind.non_promotion_parts(outcomes)
        with_v, with_n, with_d = ind.withdrawal_parts(outcomes)
        promotion = {
            **_empty_result("promotion_rate", cleaned, "percent"),
            "value": promo_v,
            "numerator": promo_n,
            "denominator": promo_d,
            "narrative": narratives.describe_rate(_RATE_LABELS["promotion_rate"], promo_v, promo_n, promo_d, cleaned),
        }
        non_promotion = {
            **_empty_result("non_promotion_rate", cleaned, "percent"),
            "value": non_v,
            "numerator": non_n,
            "denominator": non_d,
            "narrative": narratives.describe_rate(
                _RATE_LABELS["non_promotion_rate"], non_v, non_n, non_d, cleaned
            ),
        }
        withdrawal = {
            **_empty_result("withdrawal_rate", cleaned, "percent"),
            "value": with_v,
            "numerator": with_n,
            "denominator": with_d,
            "narrative": narratives.describe_rate(_RATE_LABELS["withdrawal_rate"], with_v, with_n, with_d, cleaned),
        }
        payload = {
            "enrollment_count": enrollment,
            "promotion_rate": promotion,
            "non_promotion_rate": non_promotion,
            "withdrawal_rate": withdrawal,
            "vigente_count": ind.vigente_count(outcomes),
            "ignorado_count": ind.ignorado_count(outcomes),
        }
        payload["narrative"] = narratives.describe_kpis(payload)
        return payload

    def distribution(self, dimension: str, filters: dict | None = None) -> dict[str, Any]:
        """Conteos por dimension (FILTER_KEYS o columna)."""
        resolve_column(dimension)
        return self.compute("distribution", filters=filters, group_by=dimension)

    def compute(
        self,
        metric: str,
        filters: dict | None = None,
        group_by: str | None = None,
        limit: int = 10,
        compare_filters: dict | None = None,
        rank_metric: str | None = None,
    ) -> dict[str, Any]:
        cleaned = normalize_filters(filters)
        if metric == "enrollment_count":
            if group_by:
                grouped = self._ranking_counts(cleaned, group_by, limit)
                grouped["metric"] = "enrollment_count"
                return grouped
            return self._enrollment(cleaned)
        if metric in RATE_METRICS:
            if group_by:
                return self._grouped_rate(metric, cleaned, group_by, limit)
            return self._scalar_rate(metric, cleaned)
        if metric == "distribution":
            if not group_by:
                raise ValueError("distribution requiere group_by o dimension")
            return self._distribution(cleaned, group_by)
        if metric == "ranking":
            if not group_by:
                raise ValueError("ranking requiere group_by")
            ranked = rank_metric or "enrollment_count"
            if ranked in RATE_METRICS:
                return self._grouped_rate(ranked, cleaned, group_by, limit, as_ranking=True)
            return self._ranking_counts(cleaned, group_by, limit)
        if metric == "comparison":
            if compare_filters is None:
                raise ValueError("comparison requiere compare_filters")
            return self._comparison(cleaned, normalize_filters(compare_filters), rank_metric or "enrollment_count")
        raise ValueError(f"Métrica no soportada: {metric}")

    def _enrollment(self, filters: dict) -> dict[str, Any]:
        value = self.store.count(filters)
        result = _empty_result("enrollment_count", filters, "count")
        result["value"] = value
        result["numerator"] = value
        result["denominator"] = value
        result["narrative"] = narratives.describe_enrollment(value, filters)
        return result

    def _scalar_rate(self, metric: str, filters: dict) -> dict[str, Any]:
        if metric == "repetition_rate":
            counts = self.store.repitente_counts(filters)
        else:
            counts = self.store.outcome_counts(filters)
        value, num, den = _rate_from_counts(metric, counts)
        result = _empty_result(metric, filters, "percent")
        result["value"] = value
        result["numerator"] = num
        result["denominator"] = den
        result["narrative"] = narratives.describe_rate(_RATE_LABELS[metric], value, num or 0, den or 0, filters)
        return result

    def _distribution(self, filters: dict, group_by: str) -> dict[str, Any]:
        rows = self.store.grouped_counts(group_by, filters)
        total = sum(int(row["value"]) for row in rows)
        result = _empty_result("distribution", filters, "count")
        result["value"] = total
        result["numerator"] = total
        result["denominator"] = total
        result["rows"] = rows
        result["group_by"] = group_by
        result["narrative"] = narratives.describe_distribution(group_by, rows, filters)
        return result

    def _ranking_counts(self, filters: dict, group_by: str, limit: int) -> dict[str, Any]:
        rows = self.store.grouped_counts(group_by, filters, limit=max(1, int(limit)))
        top = rows[0]["value"] if rows else None
        result = _empty_result("ranking", filters, "count")
        result["value"] = top
        result["numerator"] = top
        result["denominator"] = None
        result["rows"] = rows
        result["group_by"] = group_by
        result["narrative"] = narratives.describe_ranking(group_by, rows, "count", filters)
        return result

    def _grouped_rate(
        self,
        metric: str,
        filters: dict,
        group_by: str,
        limit: int,
        as_ranking: bool = False,
    ) -> dict[str, Any]:
        if metric == "repetition_rate":
            grouped = self.store.grouped_repitente(group_by, filters)
        else:
            grouped = self.store.grouped_outcomes(group_by, filters)
        rows: list[dict[str, Any]] = []
        for item in grouped:
            value, num, den = _rate_from_counts(metric, item["counts"])
            rows.append(
                {
                    "label": item["label"],
                    "value": value,
                    "numerator": num,
                    "denominator": den,
                }
            )
        rows.sort(key=lambda row: (-1 if row["value"] is None else -float(row["value"]), row["label"]))
        capped = rows[: max(1, int(limit))]
        name = "ranking" if as_ranking else metric
        result = _empty_result(name, filters, "percent")
        result["value"] = capped[0]["value"] if capped else None
        result["numerator"] = capped[0]["numerator"] if capped else None
        result["denominator"] = capped[0]["denominator"] if capped else None
        result["rows"] = capped
        result["group_by"] = group_by
        result["rank_metric"] = metric
        result["narrative"] = narratives.describe_ranking(group_by, capped, "percent", filters)
        return result

    def _comparison(self, filters: dict, compare_filters: dict, inner_metric: str) -> dict[str, Any]:
        if inner_metric not in {"enrollment_count", *RATE_METRICS}:
            inner_metric = "enrollment_count"
        left = self.compute(inner_metric, filters=filters)
        right = self.compute(inner_metric, filters=compare_filters)
        left_payload = {
            "label": "A",
            "value": left["value"],
            "unit": left["unit"],
            "filters": filters,
            "numerator": left["numerator"],
            "denominator": left["denominator"],
        }
        right_payload = {
            "label": "B",
            "value": right["value"],
            "unit": right["unit"],
            "filters": compare_filters,
            "numerator": right["numerator"],
            "denominator": right["denominator"],
        }
        diff = None
        if left["value"] is not None and right["value"] is not None:
            diff = float(right["value"]) - float(left["value"])
        result = _empty_result("comparison", filters, left["unit"])
        result["value"] = diff
        result["numerator"] = None
        result["denominator"] = None
        result["rows"] = [left_payload, right_payload]
        result["compare_filters"] = compare_filters
        result["compare_metric"] = inner_metric
        result["narrative"] = narratives.describe_comparison(left_payload, right_payload, inner_metric)
        return result


@lru_cache(maxsize=4)
def get_analytics(parquet_path: str | None = None) -> AnalyticsService:
    """Singleton cacheado por ruta de Parquet (un rerun de Streamlit reutiliza la conexión)."""
    return AnalyticsService(parquet_path or get_parquet_path())
