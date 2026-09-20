"""Tab de chat: UI solamente. La lógica vive en `src.agent.ask`."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.dashboard.charts import bars_from_result
from src.dashboard.layout import active_filters_text, result_get, show_error, to_mapping


def _load_ask():
    try:
        from src.agent import ask
    except ImportError:
        try:
            from src.agent.interpreter import ask  # type: ignore
        except ImportError as exc:
            return None, str(exc)
    return ask, None


def _render_answer(payload: Any) -> None:
    if payload is None:
        st.warning("El agente no devolvió respuesta.")
        return
    if isinstance(payload, str):
        st.markdown(payload)
        return
    data = to_mapping(payload)
    answer = (
        result_get(payload, "answer", "respuesta", "text", "message", "content", default=None)
        or data.get("output")
    )
    if answer:
        st.markdown(str(answer))
    else:
        st.json(data or {"raw": str(payload)})

    query = result_get(payload, "query", default=None)
    query_map = to_mapping(query)
    result = result_get(payload, "result", default=None)
    metric = result_get(payload, "metric", "metrica", default=None) or query_map.get("metric")
    used_filters = result_get(payload, "filters", "filtros", default=None) or query_map.get("filters")
    value = result_get(payload, "value", default=None)
    if value is None:
        value = result_get(result, "value", default=None)
    unit = result_get(payload, "unit", default=None)
    if unit is None:
        unit = result_get(result, "unit", default=None)
    meta_bits = []
    if metric:
        meta_bits.append(f"Métrica: `{metric}`")
    if value is not None:
        unit_txt = f" {unit}" if unit else ""
        meta_bits.append(f"Valor: {value}{unit_txt}")
    if meta_bits:
        st.caption(" · ".join(meta_bits))
    if used_filters:
        st.caption(active_filters_text(used_filters if isinstance(used_filters, dict) else to_mapping(used_filters)))
    rows = result_get(result, "rows", default=[])
    if rows:
        st.plotly_chart(
            bars_from_result(result, title="Resultado de la consulta", horizontal=len(rows) > 6),
            width="stretch",
        )
        with st.expander("Ver datos y trazabilidad"):
            st.dataframe(rows, width="stretch", hide_index=True)


def render_chat(filters: dict[str, str], audience: str = "Público general") -> None:
    st.subheader("Preguntar a los datos")
    st.write(
        "Escriba en español. El agente interpreta la pregunta, pide el cálculo a la misma capa "
        "analítica del dashboard y explica el resultado. No genera SQL libre."
    )
    st.caption(active_filters_text(filters))
    st.caption(f"Perfil de explicación: **{audience}**.")
    st.info(
        "Los filtros del menú izquierdo se envían como contexto (`extra_filters`). "
        "Si no hay clave de API, el backend puede responder en modo demostración."
    )

    ask, err = _load_ask()
    if ask is None:
        show_error(
            "El módulo de conversación no está disponible (`from src.agent import ask`).",
            err,
        )
        return

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    suggestions = (
        "¿Cuántas inscripciones hay en Quetzaltenango?",
        "Compara retiro rural y urbano en nivel básico.",
        "¿Qué municipios tienen mayor no promoción?",
        "¿Cómo se distribuyen las inscripciones por sector?",
    )
    with st.expander("Preguntas sugeridas", expanded=not st.session_state.chat_messages):
        st.write(" · ".join(suggestions))

    for item in st.session_state.chat_messages:
        with st.chat_message(item["role"]):
            if item["role"] == "assistant":
                _render_answer(item["content"])
            else:
                st.markdown(item["content"])

    prompt = st.chat_input("Ejemplo: ¿Cuál es la tasa de retiro en Quetzaltenango?")
    if not prompt:
        return

    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Consultando indicadores…"):
                try:
                    response = ask(prompt, extra_filters=filters)
                except TypeError:
                    response = ask(prompt, filters)
        except Exception as exc:  # noqa: BLE001
            show_error("No se pudo completar la pregunta.", str(exc))
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": f"Error: {exc}"}
            )
            return
        _render_answer(response)
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
