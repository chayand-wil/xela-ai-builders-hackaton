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
    st.subheader("Educación Formal · ciclo 2024 · INE Guatemala")
    st.markdown(
        "Tablero para entender inscripciones escolares **sin recalcular tasas en la pantalla**. "
        "El código analítico cuenta; esta interfaz muestra y explica."
    )

    audience = st.sidebar.selectbox(
        "¿Para quién es esta vista?",
        ("Público general", "Municipalidad", "MINEDUC"),
        help="Cambia el nivel de detalle y la forma de explicar los resultados.",
    )
    st.session_state["audience"] = audience
    try:
        from src.integrations.wren import WrenClient

        wren_status = WrenClient().status()
        with st.sidebar.expander("Motor de consultas"):
            if wren_status.ready:
                st.success(wren_status.message)
            elif wren_status.enabled:
                st.warning(wren_status.message)
                st.caption("La aplicación continúa automáticamente con DuckDB directo.")
            else:
                st.info(wren_status.message)
    except Exception as exc:  # noqa: BLE001
        with st.sidebar.expander("Motor de consultas"):
            st.warning("No se pudo comprobar WrenAI; se usará DuckDB directo.")
            st.caption(str(exc))

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

    panorama, territorio, preguntar, comparar, explorar, descubrir, metodologia = st.tabs(
        [
            "Panorama nacional",
            "Territorio",
            "Preguntar a los datos",
            "Comparar",
            "Explorador",
            "Descubrir",
            "Metodología",
        ]
    )

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

    with preguntar:
        render_chat(filters, audience)

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
