"""Componentes de interfaz de usuario reutilizables y estilos CSS para el Dashboard EduGuate IA.

Provee tarjetas KPI de alta fidelidad estética, contenedores de análisis narrativo
interpretativo, modal de bienvenida interactivo y filtros dinámicos sincronizados con DuckDB.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.analytics.queries import AnalyticsEngine


def inject_custom_css() -> None:
    """Inyecta reglas CSS con contraste tipográfico optimizado (WCAG AAA/AA) y alta legibilidad."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        /* Tipografía base y contraste general */
        html, body, [class*="css"], .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }

        /* Forzar legibilidad nítida en textos principales */
        .stMarkdown p, .stMarkdown span {
            color: #1E293B !important;
            font-size: 0.98rem;
            line-height: 1.6;
        }
        .stMarkdown strong {
            color: #0F172A !important;
            font-weight: 700 !important;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #0F172A !important;
            font-weight: 750 !important;
            letter-spacing: -0.015em;
        }

        /* Banner de Contexto y Referencia de Usuario */
        .edu-reference-banner {
            background: #EFF6FF !important;
            border: 1px solid #BFDBFE !important;
            border-left: 5px solid #2563EB !important;
            border-radius: 10px;
            padding: 0.85rem 1.2rem;
            margin-bottom: 1.2rem;
            font-size: 0.95rem;
            color: #1E3A8A !important;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        /* Captions más legibles y nítidos */
        [data-testid="stCaptionContainer"] {
            color: #334155 !important;
            font-size: 0.92rem !important;
            font-weight: 500 !important;
            margin-bottom: 0.6rem;
        }

        /* Estilos de Selectbox y Labels de Formularios */
        .stSelectbox label, [data-testid="stWidgetLabel"] p {
            color: #0F172A !important;
            font-weight: 700 !important;
            font-size: 0.92rem !important;
        }

        /* Hero Header */
        .edu-hero {
            background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 50%, #0D9488 100%);
            padding: 2.2rem 2.5rem;
            border-radius: 16px;
            color: #FFFFFF !important;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 25px -5px rgba(30, 58, 138, 0.25), 0 8px 10px -6px rgba(30, 58, 138, 0.2);
        }
        .edu-hero h1 {
            color: #FFFFFF !important;
            font-size: 2.2rem !important;
            font-weight: 850 !important;
            margin-bottom: 0.4rem !important;
            letter-spacing: -0.02em;
        }
        .edu-hero p {
            color: #F8FAFC !important;
            font-size: 1.05rem !important;
            font-weight: 450 !important;
            max-width: 850px;
            line-height: 1.6;
            margin-bottom: 0.8rem;
        }
        .edu-badge-container {
            display: flex;
            gap: 0.6rem;
            flex-wrap: wrap;
            margin-top: 0.8rem;
        }
        .edu-badge {
            background: rgba(255, 255, 255, 0.2) !important;
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.4) !important;
            padding: 0.35rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 700 !important;
            color: #FFFFFF !important;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }

        /* KPI Cards de Alto Contraste */
        .edu-kpi-card {
            background: #FFFFFF !important;
            border-radius: 14px;
            padding: 1.3rem 1.4rem;
            border: 1px solid #CBD5E1 !important;
            box-shadow: 0 4px 8px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            position: relative;
            overflow: hidden;
            height: 100%;
        }
        .edu-kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 18px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.06);
            border-color: #94A3B8 !important;
        }
        .edu-kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: var(--card-accent, #2563EB);
        }
        .edu-kpi-title {
            font-size: 0.88rem !important;
            font-weight: 750 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #1E293B !important;
            margin-bottom: 0.4rem;
        }
        .edu-kpi-value {
            font-size: 2.1rem !important;
            font-weight: 900 !important;
            color: #0F172A !important;
            line-height: 1.2;
            letter-spacing: -0.02em;
        }
        .edu-kpi-sub {
            font-size: 0.88rem !important;
            color: #334155 !important;
            font-weight: 600 !important;
            margin-top: 0.45rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .edu-pill {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            font-size: 0.78rem !important;
            font-weight: 800 !important;
        }

        /* Narrative Analysis Box (Mandatorio en Hackatón) */
        .edu-narrative-box {
            background: #F8FAFC !important;
            border-left: 5px solid #2563EB !important;
            border-radius: 0 12px 12px 0;
            padding: 1.25rem 1.5rem;
            margin: 1.2rem 0;
            border-top: 1px solid #CBD5E1 !important;
            border-right: 1px solid #CBD5E1 !important;
            border-bottom: 1px solid #CBD5E1 !important;
        }
        .edu-narrative-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.95rem !important;
            font-weight: 800 !important;
            color: #1E3A8A !important;
            margin-bottom: 0.55rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .edu-narrative-text {
            font-size: 1.02rem !important;
            line-height: 1.68 !important;
            color: #0F172A !important;
            font-weight: 450 !important;
        }
        .edu-narrative-text strong {
            color: #000000 !important;
            font-weight: 800 !important;
        }

        /* Streamlit Native Metrics */
        [data-testid="stMetricValue"] {
            color: #0F172A !important;
            font-weight: 850 !important;
            font-size: 1.8rem !important;
        }
        [data-testid="stMetricLabel"] {
            color: #1E293B !important;
            font-weight: 700 !important;
            font-size: 0.92rem !important;
        }

        /* Contenedores de Sección */
        .edu-section-card {
            background: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 14px;
            padding: 1.6rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
        }
        .edu-section-card p, .edu-section-card li {
            color: #1E293B !important;
            font-size: 0.98rem !important;
            line-height: 1.6;
        }
        .edu-section-card strong {
            color: #0F172A !important;
            font-weight: 700 !important;
        }

        /* Tabs de Streamlit */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 2px solid #CBD5E1;
            padding-bottom: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 11px 20px;
            font-weight: 700 !important;
            font-size: 1rem !important;
            border: none;
            color: #334155 !important;
            background-color: transparent;
        }
        .stTabs [aria-selected="true"] {
            color: #1D4ED8 !important;
            font-weight: 850 !important;
            border-bottom: 3px solid #1D4ED8 !important;
            background: #DBEAFE !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #CBD5E1 !important;
        }
        [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {
            color: #0F172A !important;
            font-weight: 800 !important;
        }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: #475569 !important;
            font-weight: 600 !important;
        }

        /* Footer */
        .edu-footer {
            text-align: center;
            padding: 2.5rem 1rem 1.5rem 1rem;
            color: #475569 !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            border-top: 1px solid #CBD5E1;
            margin-top: 3rem;
        }
        .edu-footer strong {
            color: #1E293B !important;
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Renderiza el banner principal de EduGuate IA con metadata del dataset oficial."""
    st.markdown(
        """
        <div class="edu-hero">
            <h1>🇬🇹 EduGuate IA — Sistema Analítico Educativo</h1>
            <p>
                Plataforma interactiva de inteligencia de datos basada en los <strong>4,298,887 microdatos</strong>
                del Censo de Educación Formal 2024 (INE Guatemala). Explora matrículas, tasas terminales y
                disparidades territoriales con motor analítico de alto rendimiento DuckDB.
            </p>
            <div class="edu-badge-container">
                <span class="edu-badge">📊 Ciclo Oficial 2024</span>
                <span class="edu-badge">🏛️ 22 Departamentos</span>
                <span class="edu-badge">📍 340 Municipios</span>
                <span class="edu-badge">⚡ Motor DuckDB &lt; 50ms</span>
                <span class="edu-badge">🛡️ Cero Alucinación</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_reference_banner(user_role: str | None, filters: dict[str, Any]) -> None:
    """Muestra un banner cuando hay una referencia o perfil de audiencia configurado."""
    if not user_role or user_role == "General":
        return

    detalles: list[str] = []
    if "departamento" in filters:
        detalles.append(f"Departamento: <strong>{filters['departamento']}</strong>")
    if "municipio" in filters:
        detalles.append(f"Municipio: <strong>{filters['municipio']}</strong>")
    if "nivel" in filters:
        detalles.append(f"Nivel: <strong>{filters['nivel']}</strong>")
    if "sector" in filters:
        detalles.append(f"Sector: <strong>{filters['sector']}</strong>")

    detalles_str = " | ".join(detalles) if detalles else "Ámbito Nacional Completo"

    st.markdown(
        f"""
        <div class="edu-reference-banner">
            <div>
                <span>🎯 <strong>Perfil de Audiencia Activo:</strong> {user_role}</span>
                <span style="margin-left: 0.8rem; color: #1E3A8A;">({detalles_str})</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.dialog("🇬🇹 Bienvenido a EduGuate IA — Selección de Inicio", width="large")
def render_welcome_modal(engine: AnalyticsEngine) -> None:
    """Modal de bienvenida inicial con 2 rutas: configurar referencia o ver el dashboard general."""
    mode = st.session_state.get("welcome_step", "choose")

    if mode == "choose":
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <h2 style="color: #1E3A8A; font-size: 1.5rem; font-weight: 850; margin-bottom: 0.3rem;">
                    ¿Cómo deseas iniciar tu experiencia?
                </h2>
                <p style="color: #334155; font-size: 1rem;">
                    Selecciona una de las dos modalidades para comenzar a explorar los 4.3 millones de microdatos:
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                """
                <div style="background: #EFF6FF; border: 2px solid #3B82F6; border-radius: 14px;
                            padding: 1.4rem; height: 100%;">
                    <div style="font-size: 2rem; margin-bottom: 0.4rem;">🎯</div>
                    <h3 style="color: #1D4ED8; font-size: 1.15rem; font-weight: 800; margin-bottom: 0.4rem;">
                        Configurar Audiencia y Referencia
                    </h3>
                    <p style="color: #1E293B; font-size: 0.92rem; line-height: 1.5;">
                        Define para quién estás preparando la información (autoridades, docentes, periodistas o
                        ciudadanía) y preselecciona un territorio o nivel prioritario.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            if st.button(
                "⚙️ Configurar mi Referencia",
                key="btn_modal_config",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["welcome_step"] = "configure"
                st.rerun()

        with col2:
            st.markdown(
                """
                <div style="background: #F8FAFC; border: 2px solid #CBD5E1; border-radius: 14px;
                            padding: 1.4rem; height: 100%;">
                    <div style="font-size: 2rem; margin-bottom: 0.4rem;">🏛️</div>
                    <h3 style="color: #0F172A; font-size: 1.15rem; font-weight: 800; margin-bottom: 0.4rem;">
                        Ver lo que ya se tiene (Dashboard Directo)
                    </h3>
                    <p style="color: #1E293B; font-size: 0.92rem; line-height: 1.5;">
                        Accede de inmediato al panorama nacional completo de 4,298,887 estudiantes,
                        rankings de los 22 departamentos, desglose por nivel y análisis de brechas.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            if st.button("📊 Explorar Dashboard General", key="btn_modal_explore", use_container_width=True):
                st.session_state["show_welcome_dialog"] = False
                st.session_state["welcome_step"] = "choose"
                st.session_state["user_role"] = "General"
                st.rerun()

    elif mode == "configure":
        st.markdown("### 🎯 Configuración de Audiencia y Datos de Referencia")
        st.caption("Estos datos básicos sirven como referencia para adaptar el contexto y enfocar el análisis.")

        role_options = [
            "🏛️ Autoridad Educativa / Ministerio / Política Pública",
            "🏫 Director de Escuela / Equipo Docente",
            "📰 Periodista / Investigador Académico",
            "👥 Padre de Familia / Organización Ciudadana",
            "📊 Analista de Datos / Especialista en Políticas",
        ]
        selected_role = st.selectbox(
            "1. ¿A quién le mostrarás o para quién analizas los datos?",
            options=role_options,
            index=0,
        )

        deptos = ["Todos los Departamentos (Nivel Nacional)"] + engine.get_departments_list()
        selected_depto = st.selectbox("2. Departamento de referencia inicial:", options=deptos, index=0)

        if selected_depto != "Todos los Departamentos (Nivel Nacional)":
            mupios = ["Todos los Municipios"] + engine.get_municipalities_list(departamento=selected_depto)
            selected_mupio = st.selectbox("Municipio de referencia (opcional):", options=mupios, index=0)
        else:
            selected_mupio = "Todos los Municipios"

        niveles = ["Todos los Niveles Educativos"] + engine.get_unique_values("nivel")
        selected_nivel = st.selectbox("3. Nivel educativo prioritario:", options=niveles, index=0)

        sectores = ["Todos los Sectores"] + engine.get_unique_values("sector")
        selected_sector = st.selectbox("4. Sector institucional prioritario:", options=sectores, index=0)

        st.markdown("---")
        b_col1, b_col2 = st.columns([1.5, 1])

        with b_col1:
            if st.button(
                "🚀 Aplicar Referencia y Ver Datos",
                key="btn_apply_ref",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["user_role"] = selected_role
                st.session_state["show_welcome_dialog"] = False
                st.session_state["welcome_step"] = "choose"

                # Guardar valores de presets para que el sidebar los adopte
                if selected_depto != "Todos los Departamentos (Nivel Nacional)":
                    st.session_state["preset_depto"] = selected_depto
                else:
                    st.session_state["preset_depto"] = "Todos"

                if selected_mupio != "Todos los Municipios":
                    st.session_state["preset_mupio"] = selected_mupio
                else:
                    st.session_state["preset_mupio"] = "Todos"

                if selected_nivel != "Todos los Niveles Educativos":
                    st.session_state["preset_nivel"] = selected_nivel
                else:
                    st.session_state["preset_nivel"] = "Todos"

                if selected_sector != "Todos los Sectores":
                    st.session_state["preset_sector"] = selected_sector
                else:
                    st.session_state["preset_sector"] = "Todos"

                st.rerun()

        with b_col2:
            if st.button("⬅️ Volver a opciones", key="btn_back_modal", use_container_width=True):
                st.session_state["welcome_step"] = "choose"
                st.rerun()


def render_kpi_card(
    title: str,
    value: str,
    subtitle: str = "",
    accent_color: str = "#2563EB",
    pill_text: str | None = None,
    pill_bg: str = "#EFF6FF",
    pill_color: str = "#1D4ED8",
) -> None:
    """Renderiza una tarjeta KPI visualmente destacada con badges y formato de alto contraste."""
    pill_html = ""
    if pill_text:
        pill_html = f'<span class="edu-pill" style="background:{pill_bg}; color:{pill_color};">{pill_text}</span>'

    st.markdown(
        f"""
        <div class="edu-kpi-card" style="--card-accent: {accent_color};">
            <div class="edu-kpi-title">{title}</div>
            <div class="edu-kpi-value">{value}</div>
            <div class="edu-kpi-sub">
                {pill_html}
                <span>{subtitle}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_narrative_box(text: str, title: str = "Análisis e Interpretación Ejecutiva") -> None:
    """Renderiza el contenedor obligatorio de análisis escrito interpretativo para no técnicos."""
    st.markdown(
        f"""
        <div class="edu-narrative-box">
            <div class="edu-narrative-header">
                <span>💡</span> {title}
            </div>
            <div class="edu-narrative-text">
                {text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_filters(engine: AnalyticsEngine) -> dict[str, Any]:
    """Construye y gestiona los filtros globales interactivos en la barra lateral."""
    st.sidebar.markdown("### 🎛️ Filtros Globales")
    st.sidebar.caption("Segmenta los 4.3M de registros en tiempo real.")

    # Botón para reabrir el modal de referencia en cualquier momento
    if st.sidebar.button("🎯 Cambiar Referencia / Audiencia", use_container_width=True):
        st.session_state["show_welcome_dialog"] = True
        st.session_state["welcome_step"] = "choose"
        st.rerun()

    st.sidebar.markdown("---")

    # 1. Departamento con soporte a preset
    deptos = ["Todos"] + engine.get_departments_list()
    preset_depto = st.session_state.get("preset_depto", "Todos")
    depto_idx = deptos.index(preset_depto) if preset_depto in deptos else 0

    selected_depto = st.sidebar.selectbox(
        "Departamento:",
        options=deptos,
        index=depto_idx,
        help="Filtra por cualquiera de los 22 departamentos de Guatemala.",
    )

    # 2. Municipio con soporte a preset
    mupios = ["Todos"] + engine.get_municipalities_list(
        departamento=selected_depto if selected_depto != "Todos" else None
    )
    preset_mupio = st.session_state.get("preset_mupio", "Todos")
    mupio_idx = mupios.index(preset_mupio) if preset_mupio in mupios else 0

    selected_mupio = st.sidebar.selectbox(
        "Municipio:",
        options=mupios,
        index=mupio_idx,
        disabled=(selected_depto == "Todos"),
        help="Selecciona un departamento primero para filtrar por municipio específico.",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 🎯 Dimensiones Educativas")

    # 3. Nivel con soporte a preset
    niveles = ["Todos"] + engine.get_unique_values("nivel")
    preset_nivel = st.session_state.get("preset_nivel", "Todos")
    nivel_idx = niveles.index(preset_nivel) if preset_nivel in niveles else 0
    selected_nivel = st.sidebar.selectbox("Nivel Educativo:", options=niveles, index=nivel_idx)

    # 4. Sector con soporte a preset
    sectores = ["Todos"] + engine.get_unique_values("sector")
    preset_sector = st.session_state.get("preset_sector", "Todos")
    sector_idx = sectores.index(preset_sector) if preset_sector in sectores else 0
    selected_sector = st.sidebar.selectbox("Sector:", options=sectores, index=sector_idx)

    # 5. Área
    areas = ["Todos"] + engine.get_unique_values("area")
    selected_area = st.sidebar.selectbox("Área Geográfica:", options=areas, index=0)

    # 6. Sexo
    sexos = ["Todos"] + engine.get_unique_values("sexo")
    selected_sexo = st.sidebar.selectbox("Sexo:", options=sexos, index=0)

    # Botón para limpiar filtros
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Restablecer Filtros", use_container_width=True):
        st.session_state.pop("preset_depto", None)
        st.session_state.pop("preset_mupio", None)
        st.session_state.pop("preset_nivel", None)
        st.session_state.pop("preset_sector", None)
        st.rerun()

    # Información de arquitectura en el footer del sidebar
    st.sidebar.markdown(
        """
        <div style="font-size: 0.8rem; color: #334155; margin-top: 2rem; line-height: 1.5;">
            <strong style="color: #0F172A;">EduGuate IA v1.0</strong><br>
            Hackatón AI Builders GT 2024<br>
            Procesamiento: DuckDB & Polars<br>
            Dataset: 4,298,887 filas
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Construir diccionario de filtros activos
    filters: dict[str, Any] = {}
    if selected_depto != "Todos":
        filters["departamento"] = selected_depto
    if selected_mupio != "Todos":
        filters["municipio"] = selected_mupio
    if selected_nivel != "Todos":
        filters["nivel"] = selected_nivel
    if selected_sector != "Todos":
        filters["sector"] = selected_sector
    if selected_area != "Todos":
        filters["area"] = selected_area
    if selected_sexo != "Todos":
        filters["sexo"] = selected_sexo

    return filters


def render_footer() -> None:
    """Renderiza el pie de página institucional."""
    st.markdown(
        """
        <div class="edu-footer">
            <p><strong>EduGuate IA</strong> — Sistema Analítico Inteligente de Educación en Guatemala</p>
            <p>Desarrollado para el Hackatón AI Builders GT 2024 | Basado en Microdatos Abiertos del INE Guatemala</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
