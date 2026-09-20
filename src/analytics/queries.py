"""Consultas DuckDB parametrizadas sobre el Parquet de inscripciones."""

from __future__ import annotations

import threading
from typing import Any

import duckdb

FILTER_KEYS: dict[str, str] = {
    "department": "departamento",
    "municipality": "municipio",
    "level": "nivel",
    "sector": "sector",
    "area": "area",
    "sex": "sexo",
    "ethnicity": "pueblo_pertenencia",
    "shift": "jornada",
    "study_plan": "plan_estudios",
    "outcome": "resultado",
    "graduate_status": "graduando",
}

SQL_COLUMNS: frozenset[str] = frozenset(
    {
        *FILTER_KEYS.values(),
        "anio",
        "codigo_establecimiento",
        "departamento_codigo",
        "municipio_codigo",
        "grado",
        "repitente",
        "graduando",
        "resultado",
    }
)

SKIP_FILTER_VALUES = {"", "todos", "todas", "all", "none", "null"}


def quote_ident(column: str) -> str:
    if column not in SQL_COLUMNS:
        raise ValueError(f"Columna no permitida: {column}")
    return f'"{column}"'


def resolve_column(name: str) -> str:
    if name in FILTER_KEYS:
        return FILTER_KEYS[name]
    if name in SQL_COLUMNS:
        return name
    raise ValueError(f"Dimensión o columna no permitida: {name}")


def normalize_filters(filters: dict | None) -> dict[str, Any]:
    if not filters:
        return {}
    cleaned: dict[str, Any] = {}
    for key, value in filters.items():
        if value is None:
            continue
        if isinstance(value, str) and value.strip().lower() in SKIP_FILTER_VALUES:
            continue
        resolve_column(key)
        cleaned[key] = value
    return cleaned


def build_where(filters: dict | None) -> tuple[str, list[Any]]:
    """WHERE con placeholders. Nunca interpola valores de usuario."""
    cleaned = normalize_filters(filters)
    clauses: list[str] = []
    params: list[Any] = []
    for key, value in cleaned.items():
        column = quote_ident(resolve_column(key))
        if isinstance(value, (list, tuple, set)):
            items = [item for item in value if item is not None and str(item).strip() != ""]
            if not items:
                continue
            placeholders = ", ".join("?" for _ in items)
            clauses.append(f"{column} IN ({placeholders})")
            params.extend(items)
        else:
            clauses.append(f"{column} = ?")
            params.append(value)
    if not clauses:
        return "", params
    return " WHERE " + " AND ".join(clauses), params


class DuckDBStore:
    """Conexión DuckDB reutilizable para leer Parquet en cada rerun de Streamlit."""

    def __init__(self, parquet_path: str) -> None:
        self.parquet_path = parquet_path
        self._con = duckdb.connect(database=":memory:")
        self._lock = threading.Lock()

    def execute(self, sql: str, params: list[Any] | None = None) -> list[tuple]:
        with self._lock:
            return self._con.execute(sql, params or []).fetchall()

    def execute_df(self, sql: str, params: list[Any] | None = None):
        with self._lock:
            return self._con.execute(sql, params or []).fetchdf()

    def from_clause(self) -> str:
        return "FROM read_parquet(?)"

    def base_params(self) -> list[Any]:
        return [self.parquet_path]

    def count(self, filters: dict | None = None) -> int:
        where, params = build_where(filters)
        sql = f"SELECT COUNT(*) {self.from_clause()}{where}"
        rows = self.execute(sql, self.base_params() + params)
        return int(rows[0][0])

    def count_equals(self, column: str, value: str, filters: dict | None = None) -> int:
        ident = quote_ident(resolve_column(column))
        where, params = build_where(filters)
        extra = f"{ident} = ?"
        sql = f"SELECT COUNT(*) {self.from_clause()}{where} {'AND' if where else 'WHERE'} {extra}"
        rows = self.execute(sql, self.base_params() + params + [value])
        return int(rows[0][0])

    def outcome_counts(self, filters: dict | None = None) -> dict[str, int]:
        where, params = build_where(filters)
        sql = f"""
            SELECT resultado, COUNT(*)
            {self.from_clause()}
            {where}
            GROUP BY resultado
        """
        rows = self.execute(sql, self.base_params() + params)
        return {str(name): int(n) for name, n in rows if name is not None}

    def repitente_counts(self, filters: dict | None = None) -> dict[str, int]:
        where, params = build_where(filters)
        sql = f"""
            SELECT repitente, COUNT(*)
            {self.from_clause()}
            {where}
            GROUP BY repitente
        """
        rows = self.execute(sql, self.base_params() + params)
        return {str(name): int(n) for name, n in rows if name is not None}

    def grouped_counts(self, group_by: str, filters: dict | None = None, limit: int | None = None) -> list[dict]:
        ident = quote_ident(resolve_column(group_by))
        where, params = build_where(filters)
        limit_sql = ""
        extra: list[Any] = []
        if limit is not None:
            limit_sql = " LIMIT ?"
            extra.append(int(limit))
        sql = f"""
            SELECT {ident} AS label, COUNT(*) AS n
            {self.from_clause()}
            {where}
            GROUP BY 1
            ORDER BY n DESC, label ASC
            {limit_sql}
        """
        rows = self.execute(sql, self.base_params() + params + extra)
        return [{"label": ("" if label is None else str(label)), "value": int(n)} for label, n in rows]

    def grouped_outcomes(self, group_by: str, filters: dict | None = None) -> list[dict[str, Any]]:
        ident = quote_ident(resolve_column(group_by))
        where, params = build_where(filters)
        sql = f"""
            SELECT
                {ident} AS label,
                resultado,
                COUNT(*) AS n
            {self.from_clause()}
            {where}
            GROUP BY 1, 2
        """
        rows = self.execute(sql, self.base_params() + params)
        buckets: dict[str, dict[str, int]] = {}
        for label, resultado, n in rows:
            key = "" if label is None else str(label)
            bucket = buckets.setdefault(key, {})
            if resultado is not None:
                bucket[str(resultado)] = int(n)
        return [{"label": label, "counts": counts} for label, counts in buckets.items()]

    def grouped_repitente(self, group_by: str, filters: dict | None = None) -> list[dict[str, Any]]:
        ident = quote_ident(resolve_column(group_by))
        where, params = build_where(filters)
        sql = f"""
            SELECT
                {ident} AS label,
                repitente,
                COUNT(*) AS n
            {self.from_clause()}
            {where}
            GROUP BY 1, 2
        """
        rows = self.execute(sql, self.base_params() + params)
        buckets: dict[str, dict[str, int]] = {}
        for label, repitente, n in rows:
            key = "" if label is None else str(label)
            bucket = buckets.setdefault(key, {})
            if repitente is not None:
                bucket[str(repitente)] = int(n)
        return [{"label": label, "counts": counts} for label, counts in buckets.items()]

    def distinct_values(self, column: str) -> list[str]:
        ident = quote_ident(resolve_column(column))
        sql = f"""
            SELECT DISTINCT {ident}
            {self.from_clause()}
            WHERE {ident} IS NOT NULL
            ORDER BY 1
        """
        rows = self.execute(sql, self.base_params())
        return [str(value) for (value,) in rows]

    def municipalities_by_department(self) -> dict[str, list[str]]:
        dept = quote_ident("departamento")
        muni = quote_ident("municipio")
        sql = f"""
            SELECT {dept} AS department, {muni} AS municipality
            {self.from_clause()}
            WHERE {dept} IS NOT NULL AND {muni} IS NOT NULL
            GROUP BY 1, 2
            ORDER BY 1, 2
        """
        rows = self.execute(sql, self.base_params())
        mapping: dict[str, list[str]] = {}
        for department, municipality in rows:
            mapping.setdefault(str(department), []).append(str(municipality))
        return mapping
