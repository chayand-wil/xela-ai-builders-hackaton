"""EduGuate IA — entrada Streamlit. `streamlit run app.py`"""

from __future__ import annotations

import streamlit as st

from src.dashboard.chat import render_chat
from src.dashboard.compare import render_compare
from src.dashboard.discover import render_discover
from src.dashboard.explorer import render_explorer
from src.dashboard.filters import normalize_options, render_sidebar_filters
from src.dashboard.layout import (
    ANALYTICS_UNAVAILABLE,
    render_disclaimer,
    render_methodology,
    show_error,
)
from src.dashboard.overview import render_overview
from src.dashboard.territory import render_territory

st.set_page_config(
    page_title="EduGuate IA",
    page_icon="🇬🇹",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def _analytics_singleton():
    from src.analytics.service import get_analytics

    return get_analytics()


def _load_analytics():
    try:
        from src.analytics.service import get_analytics  # noqa: F401
    except ImportError as exc:
        return None, f"{ANALYTICS_UNAVAILABLE}\n\n{exc}"
    try:
        return _analytics_singleton(), None
    except Exception as exc:  # noqa: BLE001
        return None, f"{ANALYTICS_UNAVAILABLE}\n\n{exc}"


def main() -> None:
    st.title("EduGuate IA")
    st.subheader("Entiende la educación de Guatemala con datos de 2024")
    st.markdown(
        "Explora tu territorio o conversa con el asistente. Cada cifra incluye una explicación "
        "sencilla y la información necesaria para comprobar cómo fue calculada."
    )

    svc, analytics_error = _load_analytics()
    options: dict = {}
    filters: dict = {}

    if svc is None:
        st.sidebar.header("Filtros")
        st.sidebar.warning("No hay opciones: falta la capa analítica.")
        show_error(ANALYTICS_UNAVAILABLE, analytics_error)
    else:
        try:
            with st.spinner("Cargando opciones de filtro…"):
                options = normalize_options(svc.filter_options())
            filters = render_sidebar_filters(options)
        except Exception as exc:  # noqa: BLE001
            show_error("No se pudieron leer las opciones de filtro.", str(exc))
            svc = None

    preguntar, panorama, territorio, comparar, explorar, descubrir, metodologia = st.tabs(
        [
            "Asistente con gráficos",
            "Panorama nacional",
            "Territorio",
            "Comparar",
            "Explorador",
            "Descubrir",
            "Metodología",
        ]
    )

    with preguntar:
        render_chat(filters)

    with panorama:
        if svc is None:
            show_error(ANALYTICS_UNAVAILABLE, analytics_error)
        else:
            render_overview(svc, filters)

    with territorio:
        if svc is None:
            show_error(ANALYTICS_UNAVAILABLE, analytics_error)
        else:
            render_territory(svc, filters, options)

    with comparar:
        if svc is None:
            show_error(ANALYTICS_UNAVAILABLE, analytics_error)
        else:
            render_compare(svc, filters, options)

    with explorar:
        if svc is None:
            show_error(ANALYTICS_UNAVAILABLE, analytics_error)
        else:
            render_explorer(svc, filters)

    with descubrir:
        if svc is None:
            show_error(ANALYTICS_UNAVAILABLE, analytics_error)
        else:
            render_discover(svc, filters)

    with metodologia:
        render_methodology()

    render_disclaimer()


main()
