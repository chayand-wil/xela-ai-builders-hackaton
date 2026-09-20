"""Helpers de presentación: normalización de resultados, estados UI y pie de página."""

from __future__ import annotations

from typing import Any

import streamlit as st

FILTER_LABELS: dict[str, str] = {
    "department": "Departamento",
    "municipality": "Municipio",
    "level": "Nivel",
    "sector": "Sector",
    "area": "Área",
    "sex": "Sexo",
    "ethnicity": "Pueblo de pertenencia",
    "shift": "Jornada",
    "study_plan": "Plan de estudios",
    "outcome": "Resultado",
    "graduate_status": "Condición de graduando",
}

KPI_ORDER: tuple[tuple[str, str], ...] = (
    ("enrollment_count", "Inscripciones"),
    ("promotion_rate", "Promoción"),
    ("non_promotion_rate", "No promoción"),
    ("withdrawal_rate", "Retiro"),
)

METRIC_ALIASES: dict[str, str] = {
    "enrollment": "enrollment_count",
    "enrollments": "enrollment_count",
    "inscripciones": "enrollment_count",
    "total": "enrollment_count",
    "promotion": "promotion_rate",
    "promocion": "promotion_rate",
    "promoción": "promotion_rate",
    "non_promotion": "non_promotion_rate",
    "no_promocion": "non_promotion_rate",
    "no_promoción": "non_promotion_rate",
    "withdrawal": "withdrawal_rate",
    "retiro": "withdrawal_rate",
}

ANALYTICS_UNAVAILABLE = (
    "Capa analítica no disponible. El dashboard no inventa cifras: "
    "necesita `src.analytics.service.get_analytics()`."
)

SOURCE_LINE = (
    "Fuente: microdatos de Educación Formal 2024, Instituto Nacional de Estadística (INE). "
    "Cada fila es una inscripción del ciclo, no una persona única."
)


def to_mapping(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return dict(obj.model_dump())
    if hasattr(obj, "dict") and callable(obj.dict):
        try:
            return dict(obj.dict())
        except TypeError:
            pass
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return {}


def result_get(obj: Any, *keys: str, default: Any = None) -> Any:
    data = to_mapping(obj)
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
        if hasattr(obj, key):
            value = getattr(obj, key)
            if value is not None:
                return value
    return default


def active_filters_text(filters: dict[str, Any] | None) -> str:
    if not filters:
        return "Sin filtros (panorama según la selección actual: todo el país)."
    parts = []
    for key, value in filters.items():
        if value in (None, "", [], "Todos"):
            continue
        label = FILTER_LABELS.get(key, key)
        parts.append(f"{label}: {value}")
    return "Filtros activos: " + "; ".join(parts) if parts else "Sin filtros territoriales ni demográficos."


def format_number(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}".replace(",", ",")
        return f"{value:,.1f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def format_kpi_value(item: Any) -> str:
    unit = str(result_get(item, "unit", default="") or "").lower()
    value = result_get(item, "value", default=None)
    if value is None:
        return "—"
    if unit in {"percent", "percentage", "pct", "%", "tasa"}:
        try:
            return f"{float(value):.1f}%"
        except (TypeError, ValueError):
            return str(value)
    try:
        return format_number(int(value) if float(value).is_integer() else value)
    except (TypeError, ValueError):
        return str(value)


def denominator_caption(item: Any) -> str:
    numerator = result_get(item, "numerator", default=None)
    denominator = result_get(item, "denominator", default=None)
    unit = str(result_get(item, "unit", default="") or "").lower()
    metric = str(result_get(item, "metric", default="") or "")
    if metric in {"enrollment_count", "enrollment"} or unit in {"count", "inscripciones", "records"}:
        if denominator not in (None, 0):
            return f"Denominador / universo visible: {format_number(denominator)} inscripciones."
        if numerator not in (None,):
            return f"Conteo de inscripciones: {format_number(numerator)}."
        return "Conteo de inscripciones (no personas únicas)."
    parts = []
    if numerator is not None:
        parts.append(f"numerador {format_number(numerator)}")
    if denominator is not None:
        parts.append(f"denominador {format_number(denominator)} (resultado conocido)")
    if parts:
        return "De cada 100 inscripciones con resultado conocido · " + "; ".join(parts) + "."
    return "Tasa calculada por la capa analítica (no se recalcula aquí)."


def extract_rows(obj: Any) -> list[dict[str, Any]]:
    raw = result_get(obj, "rows", "data", "items", default=None)
    if raw is None and isinstance(obj, list):
        raw = obj
    if raw is None:
        return []
    if hasattr(raw, "to_dict"):
        try:
            return list(raw.to_dict(orient="records"))
        except TypeError:
            pass
    rows: list[dict[str, Any]] = []
    for item in raw:
        rows.append(to_mapping(item) or {"value": item})
    return rows


def row_label(row: dict[str, Any]) -> str:
    for key in (
        "label",
        "name",
        "category",
        "group",
        "department",
        "municipality",
        "level",
        "sector",
        "area",
        "outcome",
        "sex",
        "ethnicity",
        "key",
    ):
        if row.get(key) not in (None, ""):
            return str(row[key])
    return "Sin etiqueta"


def row_value(row: dict[str, Any]) -> float | None:
    for key in ("value", "count", "enrollment", "n", "total", "rate", "share"):
        if key in row and row[key] is not None:
            try:
                return float(row[key])
            except (TypeError, ValueError):
                continue
    return None


def normalize_kpis(payload: Any) -> dict[str, Any]:
    data = to_mapping(payload)
    found: dict[str, Any] = {}
    if isinstance(payload, list):
        for item in payload:
            metric = str(result_get(item, "metric", "id", "name", default="") or "")
            key = METRIC_ALIASES.get(metric, metric)
            if key:
                found[key] = item
        return found
    for canonical, _label in KPI_ORDER:
        if canonical in data:
            found[canonical] = data[canonical]
            continue
        for alias, target in METRIC_ALIASES.items():
            if target == canonical and alias in data:
                found[canonical] = data[alias]
                break
    if found:
        return found
    if result_get(payload, "metric"):
        metric = str(result_get(payload, "metric"))
        found[METRIC_ALIASES.get(metric, metric)] = payload
    return found


def show_error(message: str, detail: str | None = None) -> None:
    st.error(message)
    if detail:
        with st.expander("Detalle técnico"):
            st.code(detail)


def show_empty(message: str = "No hay inscripciones con los filtros actuales.") -> None:
    st.info(message)


def render_source_and_filters(filters: dict[str, Any] | None) -> None:
    st.caption(f"{SOURCE_LINE} {active_filters_text(filters)}")


def render_disclaimer() -> None:
    st.divider()
    st.caption(
        "Estas cifras describen **inscripciones del ciclo escolar 2024**. "
        "No permiten seguimiento longitudinal de una misma persona entre años ni entre grados. "
        "Vigente e Ignorado se excluyen del denominador de las tasas de cierre de ciclo."
    )


def render_methodology() -> None:
    st.subheader("Cómo leer estas cifras")
    st.markdown(
        """
**Grano del dato.** Cada fila del archivo es una **inscripción** del ciclo 2024, no necesariamente
una persona única. Una misma persona podría aparecer más de una vez si se inscribió en más de un
registro. Por eso hablamos de inscripciones, no de “niños únicos”.

**Tasas de cierre de ciclo.** Promoción, no promoción y retiro se calculan solo sobre inscripciones
con resultado terminal conocido:

- Promovido
- No promovido
- Retirado
- Retirado definitivo

El **retiro** consolida los códigos de *Retirado* y *Retirado definitivo*.

**Vigente e Ignorado.** Se muestran aparte (por ejemplo en la composición de resultado) y **no entran**
en el denominador de esas tasas, para no diluir el cierre del ciclo.

**Por qué promoción puede verse como 85.3% y no 85.2%.** El 85.2% describe la proporción de
registros promovidos sobre todas las filas. La tarjeta de promoción usa únicamente los
**4,296,706 resultados finales conocidos**, como exige la metodología; por eso muestra 85.3% al
redondear a un decimal. No son cifras contradictorias: tienen denominadores distintos.

**Establecimientos.** Un centro puede tener varios `codigo_establecimiento` (por nivel u otra
organización). **No llamamos “escuelas”** al conteo de códigos.

**Municipios.** El municipio se deriva del código de establecimiento, no de la columna original
`Depto_mupio`. En Guatemala departamento se esperan **17** municipios.

**Qué no está en el dataset.** Notas, edad, discapacidad, docentes, infraestructura, trayectoria
individual ni series 2020–2023.

Todas las tasas las calcula el código de `src.analytics`. Esta pantalla solo las muestra.
        """
    )
    st.markdown(
        """
**Controles de volumen (referencia de calidad, no recalculados aquí):** total nacional
**4,298,887** inscripciones; **22** departamentos; **340** municipios en el país; departamento de
Guatemala con **17** municipios. El reporte de validación confirma diferencia cero contra el total esperado.
        """
    )


def render_kpi_row(kpis: dict[str, Any]) -> None:
    cols = st.columns(4)
    for column, (key, title) in zip(cols, KPI_ORDER, strict=True):
        item = kpis.get(key)
        with column:
            if not item:
                st.metric(title, "—")
                st.caption("La capa analítica no devolvió este indicador.")
                continue
            narrative = result_get(item, "narrative", default=None)
            st.metric(title, format_kpi_value(item))
            unit = str(result_get(item, "unit", default="") or "")
            if unit == "percent":
                st.caption("De cada 100 inscripciones con resultado conocido.")
            else:
                st.caption("Registros de inscripción del ciclo 2024.")
            with st.expander("Ver cómo se calculó"):
                st.write(denominator_caption(item))
                if narrative:
                    st.write(str(narrative))
