"""Filtros globales del sidebar. Claves en inglés; etiquetas en español."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.dashboard.layout import FILTER_LABELS, to_mapping

TODOS = "Todos"
WIDGET_KEYS = (
    "department",
    "municipality",
    "level",
    "sector",
    "area",
    "sex",
    "ethnicity",
    "shift",
    "study_plan",
    "outcome",
)


def as_str_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, dict):
        return [str(v) for v in raw.values() if v not in (None, "")]
    values: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            label = item.get("label") or item.get("name") or item.get("value")
            if label is not None:
                values.append(str(label))
        elif item not in (None, ""):
            values.append(str(item))
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def normalize_options(opts: Any) -> dict[str, Any]:
    data = to_mapping(opts)
    key_aliases = {
        "departments": "department",
        "departamento": "department",
        "municipalities": "municipality",
        "municipio": "municipality",
        "municipios": "municipality",
        "nivel": "level",
        "levels": "level",
        "sectores": "sector",
        "área": "area",
        "sexo": "sex",
        "pueblo": "ethnicity",
        "ethnicity": "ethnicity",
        "jornada": "shift",
        "plan": "study_plan",
        "plan_estudios": "study_plan",
        "resultado": "outcome",
        "outcomes": "outcome",
    }
    normalized: dict[str, Any] = dict(data)
    for alias, canonical in key_aliases.items():
        if alias in data and canonical not in normalized:
            normalized[canonical] = data[alias]
    return normalized


def municipality_choices(options: dict[str, Any], department: str | None) -> list[str]:
    nested = (
        options.get("municipality_by_department")
        or options.get("municipalities_by_department")
        or options.get("geo")
    )
    if department and isinstance(nested, dict):
        return as_str_list(nested.get(department) or nested.get(department.title()))

    raw_muni = options.get("municipality")
    if isinstance(raw_muni, list) and raw_muni and isinstance(raw_muni[0], dict):
        if department:
            filtered = [
                item
                for item in raw_muni
                if str(item.get("department") or item.get("departamento") or "") == department
            ]
            return as_str_list(filtered)
        return as_str_list(raw_muni)

    names = as_str_list(raw_muni)
    if not department or not names:
        return names

    codes = options.get("municipality_code") or options.get("municipality_codes")
    code_to_name = options.get("municipality_code_to_name")
    dept_codes = options.get("department_codes") or options.get("department_code")
    prefix = None
    if isinstance(dept_codes, dict):
        prefix = str(dept_codes.get(department) or "").zfill(2)
    if prefix and isinstance(code_to_name, dict):
        return [str(name) for code, name in code_to_name.items() if str(code).zfill(4).startswith(prefix)]
    if prefix and isinstance(codes, (list, tuple)):
        kept = [str(c).zfill(4) for c in codes if str(c).zfill(4).startswith(prefix)]
        if kept and all(item[:2].isdigit() for item in names if len(item) >= 2):
            return [n for n in names if n.zfill(4)[:2] == prefix]
    return names


def build_filters(raw: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in raw.items() if value and value != TODOS}


def render_sidebar_filters(options: dict[str, Any]) -> dict[str, str]:
    st.sidebar.header("Filtros")
    st.sidebar.caption("Los indicadores y el chat usan exactamente esta selección.")

    if st.sidebar.button("Restablecer filtros", width="stretch"):
        for key in WIDGET_KEYS:
            st.session_state[f"flt_{key}"] = TODOS
        st.rerun()

    for key in WIDGET_KEYS:
        st.session_state.setdefault(f"flt_{key}", TODOS)

    department_values = [TODOS] + as_str_list(options.get("department"))
    department = st.sidebar.selectbox(
        FILTER_LABELS["department"],
        options=department_values,
        key="flt_department",
    )
    chosen_dept = None if department == TODOS else department

    muni_values = [TODOS] + municipality_choices(options, chosen_dept)
    current_muni = st.session_state.get("flt_municipality", TODOS)
    if current_muni not in muni_values:
        st.session_state["flt_municipality"] = TODOS
    st.sidebar.selectbox(
        FILTER_LABELS["municipality"],
        options=muni_values,
        key="flt_municipality",
        help="Si la lista no se estrecha al elegir departamento, las opciones llegaron planas desde analítica.",
    )

    for key in WIDGET_KEYS:
        if key in {"department", "municipality"}:
            continue
        values = [TODOS] + as_str_list(options.get(key))
        st.sidebar.selectbox(FILTER_LABELS.get(key, key), options=values, key=f"flt_{key}")

    selected = {key: st.session_state.get(f"flt_{key}", TODOS) for key in WIDGET_KEYS}
    return build_filters(selected)
