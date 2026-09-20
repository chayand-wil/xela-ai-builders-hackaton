"""Tab de chat: UI solamente. La lógica vive en `src.agent.ask`."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.analytics.narratives import METRIC_LABELS
from src.dashboard.charts import bars_from_result
from src.dashboard.layout import (
    active_filters_text,
    denominator_caption,
    format_kpi_value,
    result_get,
    show_error,
    to_mapping,
)


def _load_ask():
    try:
        from src.agent import ask
    except ImportError:
        try:
            from src.agent.interpreter import ask  # type: ignore
        except ImportError as exc:
            return None, str(exc)
    return ask, None


def _queue_question(question: str) -> None:
    st.session_state["chat_pending_question"] = question


def _render_answer(payload: Any, message_index: int = 0) -> None:
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
        meta_bits.append(f"Indicador: {METRIC_LABELS.get(str(metric), metric)}")
    if value is not None:
        unit_txt = f" {unit}" if unit else ""
        meta_bits.append(f"Valor: {value}{unit_txt}")
    if meta_bits:
        st.caption(" · ".join(meta_bits))
    if used_filters:
        st.caption(active_filters_text(used_filters if isinstance(used_filters, dict) else to_mapping(used_filters)))
    provider = result_get(payload, "provider", default=None)
    language_provider = result_get(payload, "language_provider", default=None)
    if provider:
        prefix = f"Interpretación: {language_provider} · " if language_provider else ""
        st.caption(f"{prefix}Cálculo: {provider}.")
    if result:
        with st.expander("¿Cómo se calculó y qué significa?"):
            st.write(denominator_caption(result))
            st.write(
                "Cada registro representa una inscripción del ciclo 2024, no necesariamente una persona única. "
                "Una diferencia describe los datos observados, pero no demuestra por qué ocurrió."
            )
    rows = result_get(result, "rows", default=[])
    if rows:
        value_axis = "Porcentaje" if result_get(result, "unit", default="") == "percent" else "Inscripciones"
        st.plotly_chart(
            bars_from_result(
                result,
                title=f"Gráfico: {METRIC_LABELS.get(str(metric), 'resultado')} por grupo",
                horizontal=len(rows) > 6,
                value_axis_title=value_axis,
            ),
            width="stretch",
        )
        with st.expander("Ver datos y trazabilidad"):
            st.dataframe(rows, width="stretch", hide_index=True)
    elif result and result_get(result, "value", default=None) is not None:
        st.metric(METRIC_LABELS.get(str(metric), "Resultado").capitalize(), format_kpi_value(result))
    related = result_get(payload, "related_questions", default=[])
    if related:
        st.caption("Puedes continuar preguntando:")
        columns = st.columns(min(3, len(related)))
        for index, question in enumerate(related):
            columns[index % len(columns)].button(
                question,
                key=f"followup_{message_index}_{index}",
                on_click=_queue_question,
                args=(question,),
                width="stretch",
            )


def render_chat(filters: dict[str, str]) -> None:
    st.subheader("Pregunta, compara y crea gráficos")
    st.write(
        "Escribe lo que quieres conocer. Por ejemplo: **«Grafica la tasa de retiro por municipio "
        "en Alta Verapaz»**. Puedes continuar con «explícamelo», «compáralo» o «dame más detalles»."
    )
    st.caption(active_filters_text(filters))
    st.caption(
        "Si mencionas un territorio o grupo en la pregunta, esa selección reemplaza los filtros del menú. "
        "Si no mencionas ninguno, se usa la selección lateral."
    )
    st.info(
        "El asistente recuerda la conversación y respeta los filtros del menú. WrenAI consulta la capa "
        "semántica y DuckDB verifica las cifras; si no hay modelo de lenguaje, las preguntas frecuentes "
        "siguen funcionando localmente."
    )

    with st.form("assistant_question_form", clear_on_submit=True):
        typed_prompt = st.text_input(
            "Escribe tu pregunta",
            placeholder="Ejemplo: Grafica la tasa de retiro por municipio en Alta Verapaz",
        )
        submitted = st.form_submit_button("Consultar y generar gráfico", type="primary", width="stretch")

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
        columns = st.columns(2)
        for index, question in enumerate(suggestions):
            columns[index % 2].button(
                question,
                key=f"suggestion_{index}",
                on_click=_queue_question,
                args=(question,),
                width="stretch",
            )

    for message_index, item in enumerate(st.session_state.chat_messages):
        with st.chat_message(item["role"]):
            if item["role"] == "assistant":
                _render_answer(item["content"], message_index)
            else:
                st.markdown(item["content"])

    prompt = st.session_state.pop("chat_pending_question", None)
    if submitted:
        prompt = typed_prompt.strip()
    if not prompt:
        return

    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Consultando indicadores…"):
                try:
                    response = ask(
                        prompt,
                        extra_filters=filters,
                        history=st.session_state.chat_messages[:-1],
                        audience="Público general",
                    )
                except TypeError:
                    response = ask(prompt, filters)
        except Exception as exc:  # noqa: BLE001
            show_error("No se pudo completar la pregunta.", str(exc))
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": f"Error: {exc}"}
            )
            return
        _render_answer(response, len(st.session_state.chat_messages))
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
