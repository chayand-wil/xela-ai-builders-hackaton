"""Motor de consultas analíticas sobre Apache Parquet mediante DuckDB.

Provee una capa de acceso a datos centralizada, parametrizada y de ultra alta velocidad (< 50ms)
tanto para el Dashboard de Streamlit como para el Agente Conversacional.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import duckdb
import polars as pl

from src.analytics.indicators import KPISummary, calculate_rates

logger = logging.getLogger(__name__)

ALLOWED_FILTER_COLUMNS: set[str] = {
    "anio",
    "codigo_establecimiento",
    "departamento_codigo",
    "departamento",
    "municipio_codigo",
    "municipio",
    "sector",
    "area",
    "sexo",
    "grado",
    "nivel",
    "pueblo_pertenencia",
    "plan_estudios",
    "jornada",
    "resultado",
    "repitente",
    "graduando",
}


class AnalyticsEngine:
    """Motor analítico centralizado basado en DuckDB sobre Parquet."""

    def __init__(self, parquet_path: str | Path | None = None) -> None:
        self.parquet_path = self._resolve_parquet_path(parquet_path)
        self.conn = duckdb.connect(database=":memory:")
        self._init_view()
        logger.info(f"AnalyticsEngine inicializado con fuente: {self.parquet_path}")

    def _resolve_parquet_path(self, path: str | Path | None) -> Path:
        if path:
            p = Path(path)
            if p.exists():
                return p

        # Prioridad 1: Dataset completo procesado
        default_full = Path("Data/processed/educacion_formal_2024.parquet")
        if default_full.exists():
            return default_full

        # Prioridad 2: Muestra para desarrollo
        default_sample = Path("Data/samples/educacion_formal_sample.parquet")
        if default_sample.exists():
            logger.warning(f"No se encontró {default_full}. Usando muestra de desarrollo: {default_sample}")
            return default_sample

        raise FileNotFoundError(
            "No se encontró el dataset Parquet procesado. Ejecuta primero `python scripts/process_data.py`."
        )

    def _init_view(self) -> None:
        """Crea una vista virtual en DuckDB que mapea directamente al archivo Parquet."""
        # Ruta absoluta normalizada para evitar problemas de path en SQL
        abs_path = str(self.parquet_path.resolve())
        self.conn.execute(f"CREATE OR REPLACE VIEW educacion AS SELECT * FROM read_parquet('{abs_path}')")

    def _build_where_clause(self, filters: dict[str, Any] | None) -> tuple[str, list[Any]]:
        """Construye una cláusula WHERE parametrizada y segura."""
        if not filters:
            return "", []

        clauses: list[str] = []
        params: list[Any] = []

        for col, val in filters.items():
            if col not in ALLOWED_FILTER_COLUMNS or val is None or val == "" or val == "Todos":
                continue

            if isinstance(val, (list, tuple, set)):
                if len(val) == 0:
                    continue
                placeholders = ", ".join(["?"] * len(val))
                clauses.append(f"{col} IN ({placeholders})")
                params.extend(list(val))
            else:
                clauses.append(f"{col} = ?")
                params.append(val)

        if not clauses:
            return "", []

        return "WHERE " + " AND ".join(clauses), params

    def get_kpis(self, filters: dict[str, Any] | None = None) -> KPISummary:
        """Calcula los indicadores clave de rendimiento (KPIs) oficiales para los filtros dados."""
        where_sql, params = self._build_where_clause(filters)

        query = f"""
        SELECT
            COUNT(*) AS matricula_total,
            COUNT(*) FILTER (WHERE resultado = 'Promovido') AS promovidos,
            COUNT(*) FILTER (WHERE resultado = 'No promovido') AS no_promovidos,
            COUNT(*) FILTER (WHERE resultado IN ('Retirado', 'Retirado definitivo')) AS retirados,
            COUNT(*) FILTER (WHERE resultado = 'Vigente') AS vigentes,
            COUNT(*) FILTER (WHERE resultado = 'Ignorado') AS ignorados,
            COUNT(*) FILTER (WHERE repitente = 'Sí') AS repitentes,
            COUNT(*) FILTER (WHERE graduando = 'Sí es graduando') AS graduandos
        FROM educacion
        {where_sql}
        """
        row = self.conn.execute(query, params).fetchone()
        if not row or row[0] is None:
            return KPISummary(
                matricula_total=0,
                promovidos=0,
                no_promovidos=0,
                retirados=0,
                vigentes=0,
                ignorados=0,
                repitentes=0,
                graduandos=0,
                denominador_terminal=0,
                tasa_promocion=0.0,
                tasa_no_promocion=0.0,
                tasa_retiro=0.0,
                tasa_repitencia=0.0,
                filters=filters or {},
            )

        total, prom, no_prom, ret, vig, ign, rep, grad = row
        rates = calculate_rates(
            promovidos=prom,
            no_promovidos=no_prom,
            retirados=ret,
            matricula_total=total,
            repitentes=rep,
        )

        return KPISummary(
            matricula_total=total,
            promovidos=prom,
            no_promovidos=no_prom,
            retirados=ret,
            vigentes=vig,
            ignorados=ign,
            repitentes=rep,
            graduandos=grad,
            denominador_terminal=rates["denominador_terminal"],
            tasa_promocion=rates["tasa_promocion"],
            tasa_no_promocion=rates["tasa_no_promocion"],
            tasa_retiro=rates["tasa_retiro"],
            tasa_repitencia=rates["tasa_repitencia"],
            filters=filters or {},
        )

    def get_breakdown_by_dimension(
        self,
        dimension: str,
        filters: dict[str, Any] | None = None,
        sort_by: str = "matricula",
        ascending: bool = False,
    ) -> pl.DataFrame:
        """Calcula el desglose completo y tasas terminales por cualquier dimensión categórica."""
        if dimension not in ALLOWED_FILTER_COLUMNS:
            raise ValueError(f"Dimensión no permitida: {dimension}")

        where_sql, params = self._build_where_clause(filters)
        order_dir = "ASC" if ascending else "DESC"

        # Validar columna de ordenación para evitar inyección
        allowed_sort = {
            "matricula",
            "pct_matricula",
            "tasa_promocion",
            "tasa_no_promocion",
            "tasa_retiro",
            dimension,
        }
        if sort_by not in allowed_sort:
            sort_by = "matricula"

        query = f"""
        SELECT
            {dimension},
            COUNT(*) AS matricula,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct_matricula,
            COUNT(*) FILTER (WHERE resultado = 'Promovido') AS promovidos,
            COUNT(*) FILTER (WHERE resultado = 'No promovido') AS no_promovidos,
            COUNT(*) FILTER (WHERE resultado IN ('Retirado', 'Retirado definitivo')) AS retirados,
            COUNT(*) FILTER (
                WHERE resultado IN ('Promovido', 'No promovido', 'Retirado', 'Retirado definitivo')
            ) AS denominador_terminal,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE resultado = 'Promovido') /
                NULLIF(COUNT(*) FILTER (
                    WHERE resultado IN ('Promovido', 'No promovido', 'Retirado', 'Retirado definitivo')
                ), 0), 2
            ) AS tasa_promocion,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE resultado = 'No promovido') /
                NULLIF(COUNT(*) FILTER (
                    WHERE resultado IN ('Promovido', 'No promovido', 'Retirado', 'Retirado definitivo')
                ), 0), 2
            ) AS tasa_no_promocion,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE resultado IN ('Retirado', 'Retirado definitivo')) /
                NULLIF(COUNT(*) FILTER (
                    WHERE resultado IN ('Promovido', 'No promovido', 'Retirado', 'Retirado definitivo')
                ), 0), 2
            ) AS tasa_retiro
        FROM educacion
        {where_sql}
        GROUP BY {dimension}
        ORDER BY {sort_by} {order_dir}
        """
        return self.conn.execute(query, params).pl()

    def get_department_ranking(
        self,
        metric: str = "matricula",
        filters: dict[str, Any] | None = None,
        ascending: bool = False,
    ) -> pl.DataFrame:
        """Obtiene el ranking de los 22 departamentos por la métrica seleccionada."""
        return self.get_breakdown_by_dimension(
            dimension="departamento",
            filters=filters,
            sort_by=metric,
            ascending=ascending,
        )

    def get_municipal_breakdown(
        self,
        departamento: str | int | None = None,
        filters: dict[str, Any] | None = None,
        sort_by: str = "matricula",
        ascending: bool = False,
    ) -> pl.DataFrame:
        """Obtiene el desglose de municipios dentro de un departamento (o a nivel nacional)."""
        active_filters = dict(filters or {})
        if departamento is not None:
            if isinstance(departamento, int):
                active_filters["departamento_codigo"] = departamento
            else:
                active_filters["departamento"] = departamento

        return self.get_breakdown_by_dimension(
            dimension="municipio",
            filters=active_filters,
            sort_by=sort_by,
            ascending=ascending,
        )

    def get_cross_tabulation(
        self,
        dim1: str,
        dim2: str,
        filters: dict[str, Any] | None = None,
    ) -> pl.DataFrame:
        """Genera una tabla cruzada bidimensional (conteo de registros)."""
        if dim1 not in ALLOWED_FILTER_COLUMNS or dim2 not in ALLOWED_FILTER_COLUMNS:
            raise ValueError("Dimensiones no permitidas para tabulación cruzada.")

        where_sql, params = self._build_where_clause(filters)

        query = f"""
        SELECT
            {dim1},
            {dim2},
            COUNT(*) AS total,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY {dim1}), 2) AS pct_en_fila
        FROM educacion
        {where_sql}
        GROUP BY {dim1}, {dim2}
        ORDER BY {dim1}, total DESC
        """
        return self.conn.execute(query, params).pl()

    def get_unique_values(self, column_name: str) -> list[str]:
        """Obtiene los valores únicos y ordenados de una columna para poblar selectores UI."""
        if column_name not in ALLOWED_FILTER_COLUMNS:
            return []
        query = f"SELECT DISTINCT {column_name} FROM educacion WHERE {column_name} IS NOT NULL ORDER BY {column_name}"
        rows = self.conn.execute(query).fetchall()
        return [str(r[0]) for r in rows]

    def get_departments_list(self) -> list[str]:
        """Lista alfabética de los 22 departamentos."""
        return self.get_unique_values("departamento")

    def get_municipalities_list(self, departamento: str | int | None = None) -> list[str]:
        """Lista de municipios pertenecientes a un departamento específico."""
        if departamento is None or departamento == "Todos":
            return self.get_unique_values("municipio")

        if isinstance(departamento, int):
            clause = "WHERE departamento_codigo = ?"
            params = [departamento]
        else:
            clause = "WHERE departamento = ?"
            params = [departamento]

        query = f"SELECT DISTINCT municipio FROM educacion {clause} ORDER BY municipio"
        rows = self.conn.execute(query, params).fetchall()
        return [str(r[0]) for r in rows]
