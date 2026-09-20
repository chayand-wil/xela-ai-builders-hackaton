"""Componentes de interfaz de usuario reutilizables y estilos CSS para el Dashboard EduGuate IA.

Provee tarjetas KPI de alta fidelidad estética, contenedores de análisis narrativo
interpretativo y filtros dinámicos sincronizados con el motor DuckDB.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.analytics.queries import AnalyticsEngine


def inject_custom_css() -> None:
    """Inyecta reglas CSS avanzadas para elevar el diseño visual a estándares de nivel producto."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        /* Base styling */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Hero Header */
        .edu-hero {
            background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 50%, #0D9488 100%);
            padding: 2.2rem 2.5rem;
            border-radius: 16px;
            color: #FFFFFF;
            margin-bottom: 2rem;
            box-shadow: 0 10px 25px -5px rgba(30, 58, 138, 0.25), 0 8px 10px -6px rgba(30, 58, 138, 0.2);
        }
        .edu-hero h1 {
            color: #FFFFFF !important;
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            margin-bottom: 0.4rem !important;
            letter-spacing: -0.02em;
        }
        .edu-hero p {
            color: #E2E8F0 !important;
            font-size: 1.05rem;
            max-width: 850px;
            line-height: 1.5;
            margin-bottom: 0.8rem;
        }
        .edu-badge-container {
            display: flex;
            gap: 0.6rem;
            flex-wrap: wrap;
            margin-top: 0.8rem;
        }
        .edu-badge {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.25);
            padding: 0.3rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.82rem;
            font-weight: 600;
            color: #FFFFFF;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }

        /* KPI Card */
        .edu-kpi-card {
            background: #FFFFFF;
            border-radius: 14px;
            padding: 1.25rem 1.4rem;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            position: relative;
            overflow: hidden;
            height: 100%;
        }
        .edu-kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04);
            border-color: #CBD5E1;
        }
        .edu-kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--card-accent, #3B82F6);
        }
        .edu-kpi-title {
            font-size: 0.82rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748B;
            margin-bottom: 0.35rem;
        }
        .edu-kpi-value {
            font-size: 1.85rem;
            font-weight: 800;
            color: #0F172A;
            line-height: 1.2;
            letter-spacing: -0.02em;
        }
        .edu-kpi-sub {
            font-size: 0.82rem;
            color: #64748B;
            margin-top: 0.35rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        .edu-pill {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
        }

        /* Narrative Analysis Box (Mandatorio en Hackatón) */
        .edu-narrative-box {
            background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
            border-left: 4px solid #2563EB;
            border-radius: 0 12px 12px 0;
            padding: 1.2rem 1.4rem;
            margin: 1.2rem 0;
            border-top: 1px solid #E2E8F0;
            border-right: 1px solid #E2E8F0;
            border-bottom: 1px solid #E2E8F0;
        }
        .edu-narrative-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .edu-narrative-text {
            font-size: 0.95rem;
            line-height: 1.6;
            color: #334155;
        }

        /* Alert Box */
        .edu-alert-box {
            background: #FEF3C7;
            border-left: 4px solid #F59E0B;
            border-radius: 0 10px 10px 0;
            padding: 0.9rem 1.1rem;
            font-size: 0.88rem;
            color: #92400E;
            margin: 0.8rem 0;
        }

        /* Card Section Container */
        .edu-section-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
        }

        /* Streamlit Tabs Customization */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 10px 18px;
            font-weight: 600;
            font-size: 0.95rem;
            border: none;
            color: #64748B;
            background-color: transparent;
        }
        .stTabs [aria-selected="true"] {
            color: #2563EB !important;
            border-bottom: 3px solid #2563EB !important;
            background: #EFF6FF !important;
        }

        /* Footer */
        .edu-footer {
            text-align: center;
            padding: 2.5rem 1rem 1.5rem 1rem;
            color: #94A3B8;
            font-size: 0.85rem;
            border-top: 1px solid #E2E8F0;
            margin-top: 3rem;
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


def render_kpi_card(
    title: str,
    value: str,
    subtitle: str = "",
    accent_color: str = "#2563EB",
    pill_text: str | None = None,
    pill_bg: str = "#EFF6FF",
    pill_color: str = "#1D4ED8",
) -> None:
    """Renderiza una tarjeta KPI visualmente destacada con badges y formato enriquecido."""
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

    # 1. Departamento
    deptos = ["Todos"] + engine.get_departments_list()
    selected_depto = st.sidebar.selectbox(
        "Departamento:",
        options=deptos,
        index=0,
        help="Filtra por cualquiera de los 22 departamentos de Guatemala.",
    )

    # 2. Municipio (filtrado dinámico si hay depto seleccionado)
    mupios = ["Todos"] + engine.get_municipalities_list(
        departamento=selected_depto if selected_depto != "Todos" else None
    )
    selected_mupio = st.sidebar.selectbox(
        "Municipio:",
        options=mupios,
        index=0,
        disabled=(selected_depto == "Todos"),
        help="Selecciona un departamento primero para filtrar por municipio específico.",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 🎯 Dimensiones Educativas")

    # 3. Nivel
    niveles = ["Todos"] + engine.get_unique_values("nivel")
    selected_nivel = st.sidebar.selectbox("Nivel Educativo:", options=niveles, index=0)

    # 4. Sector
    sectores = ["Todos"] + engine.get_unique_values("sector")
    selected_sector = st.sidebar.selectbox("Sector:", options=sectores, index=0)

    # 5. Área
    areas = ["Todos"] + engine.get_unique_values("area")
    selected_area = st.sidebar.selectbox("Área Geográfica:", options=areas, index=0)

    # 6. Sexo
    sexos = ["Todos"] + engine.get_unique_values("sexo")
    selected_sexo = st.sidebar.selectbox("Sexo:", options=sexos, index=0)

    # Botón para limpiar filtros
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Restablecer Filtros", use_container_width=True):
        st.rerun()

    # Información de arquitectura en el footer del sidebar
    st.sidebar.markdown(
        """
        <div style="font-size: 0.75rem; color: #64748B; margin-top: 2rem; line-height: 1.4;">
            <strong>EduGuate IA v1.0</strong><br>
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
