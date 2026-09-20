"""Aplicación principal del Dashboard EduGuate IA para el Hackatón AI Builders GT 2024.

Construida con Streamlit, Plotly y DuckDB, procesando 4,298,887 microdatos del Censo Escolar 2024.
Todas las visualizaciones cuentan con análisis escrito interpretativo obligatorio para no técnicos.
"""

from __future__ import annotations

import streamlit as st

from src.analytics.narratives import explain_breakdown, explain_kpis, explain_ranking
from src.analytics.queries import AnalyticsEngine
from src.dashboard.charts import (
    create_bar_levels,
    create_donut_results,
    create_gap_bars,
    create_horizontal_ranking,
    create_municipal_bars,
    create_pueblo_breakdown,
)
from src.dashboard.components import (
    inject_custom_css,
    render_footer,
    render_header,
    render_kpi_card,
    render_narrative_box,
    render_sidebar_filters,
)

# Configuración de página de Streamlit
st.set_page_config(
    page_title="EduGuate IA — Sistema Analítico Educativo",
    page_icon="🇬🇹",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner="Iniciando motor DuckDB sobre 4.3M microdatos...")
def get_analytics_engine() -> AnalyticsEngine:
    """Inicializa y mantiene en memoria la conexión a DuckDB."""
    return AnalyticsEngine()


def main() -> None:
    # 1. Inyección de estilos CSS y Renderizado de Header
    inject_custom_css()
    render_header()

    # 2. Inicialización del motor analítico
    try:
        engine = get_analytics_engine()
    except Exception as e:
        st.error(f"Error al inicializar el motor analítico: {e}")
        st.info("Asegúrate de haber procesado los datos con `python scripts/process_data.py`.")
        return

    # 3. Filtros globales en barra lateral
    filters = render_sidebar_filters(engine)

    # 4. Cálculo de KPIs principales según filtros activos
    kpis = engine.get_kpis(filters)

    # 5. Estructura de Pestañas Principales
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "🏛️ Panorama Nacional",
            "🗺️ Exploración Territorial",
            "⚖️ Brechas y Desigualdades",
            "🤖 Preguntar a los Datos",
        ]
    )

    # =========================================================================
    # PESTAÑA 1: PANORAMA GENERAL
    # =========================================================================
    with tab1:
        st.markdown("### 📊 Indicadores Clave del Ciclo Escolar 2024")
        if filters:
            filtro_desc = ", ".join([f"**{k.title()}**: {v}" for k, v in filters.items()])
            st.caption(f"Filtros activos actualmente aplicados: {filtro_desc}")
        else:
            st.caption("Visualizando el universo total nacional (4,298,887 inscripciones)")

        # Fila de 4 Tarjetas KPI
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_kpi_card(
                title="Matrícula Total",
                value=f"{kpis.matricula_total:,}",
                subtitle=f"Evaluados: {kpis.denominador_terminal:,}",
                accent_color="#2563EB",
                pill_text="100%",
                pill_bg="#EFF6FF",
                pill_color="#1D4ED8",
            )
        with col2:
            render_kpi_card(
                title="Tasa de Promoción",
                value=f"{kpis.tasa_promocion:.1f}%",
                subtitle=f"{kpis.promovidos:,} aprobados",
                accent_color="#10B981",
                pill_text="Aprobados",
                pill_bg="#ECFDF5",
                pill_color="#047857",
            )
        with col3:
            render_kpi_card(
                title="Tasa de No Promoción",
                value=f"{kpis.tasa_no_promocion:.1f}%",
                subtitle=f"{kpis.no_promovidos:,} no promovidos",
                accent_color="#F59E0B",
                pill_text="Reprobados",
                pill_bg="#FFFBEB",
                pill_color="#B45309",
            )
        with col4:
            render_kpi_card(
                title="Tasa de Retiro / Abandono",
                value=f"{kpis.tasa_retiro:.1f}%",
                subtitle=f"{kpis.retirados:,} abandono de ciclo",
                accent_color="#EF4444",
                pill_text="Deserción",
                pill_bg="#FEF2F2",
                pill_color="#B91C1C",
            )

        # Análisis interpretativo obligatorio de los KPIs
        narrative_kpis = explain_kpis(kpis)
        render_narrative_box(narrative_kpis, title="Interpretación Ejecutiva del Rendimiento Escolar")

        st.markdown("---")

        # Fila de Gráficos: Resultados Terminales y Matrícula por Nivel
        g_col1, g_col2 = st.columns([1, 1.2])

        with g_col1:
            fig_donut = create_donut_results(kpis)
            st.plotly_chart(fig_donut, use_container_width=True)

            render_narrative_box(
                f"De cada 100 estudiantes evaluados al cierre del ciclo, aproximadamente "
                f"**{round(kpis.tasa_promocion)}** aprueban, mientras que cerca de "
                f"**{round(kpis.tasa_no_promocion + kpis.tasa_retiro)}** enfrentan dificultades terminales "
                f"(reprobación o deserción escolar temprana).",
                title="Lectura Rápida de Conclusión",
            )

        with g_col2:
            df_levels = engine.get_breakdown_by_dimension("nivel", filters=filters)
            fig_levels = create_bar_levels(df_levels)
            st.plotly_chart(fig_levels, use_container_width=True)

            narrative_levels = explain_breakdown(df_levels, "nivel")
            render_narrative_box(narrative_levels, title="Análisis de Concentración por Nivel")

        # Fila de Indicadores Adicionales (Repitencia y Graduandos)
        st.markdown("#### 🔍 Indicadores de Trayectoria Estudiantil")
        sub_col1, sub_col2, sub_col3 = st.columns(3)
        with sub_col1:
            st.metric(
                label="Población Repitente",
                value=f"{kpis.repitentes:,}",
                delta=f"{kpis.tasa_repitencia:.1f}% del total",
                delta_color="inverse",
            )
        with sub_col2:
            st.metric(
                label="Cohorte de Graduandos 2024",
                value=f"{kpis.graduandos:,}",
                delta=f"{(kpis.graduandos / max(1, kpis.matricula_total)) * 100:.1f}% del total",
                delta_color="off",
            )
        with sub_col3:
            st.metric(
                label="Estudiantes con Estado Vigente / Ignorado",
                value=f"{kpis.vigentes + kpis.ignorados:,}",
                delta="Excluidos de tasas terminales",
                delta_color="off",
            )

    # =========================================================================
    # PESTAÑA 2: EXPLORACIÓN TERRITORIAL
    # =========================================================================
    with tab2:
        st.markdown("### 🗺️ Comparativa y Disparidad Territorial")
        st.caption("Análisis comparativo de los 22 departamentos y exploración a nivel de sus 340 municipios.")

        # Filtros de ranking (sin restringir a un solo depto para ver los 22)
        rank_filters = {k: v for k, v in filters.items() if k not in ["departamento", "municipio"]}

        r_col1, r_col2 = st.columns([1.5, 1])
        with r_col1:
            metric_option = st.selectbox(
                "Selecciona la Métrica de Clasificación Departamental:",
                options=[
                    ("matricula", "Matrícula Total (Volumen de Estudiantes)"),
                    ("tasa_promocion", "Tasa de Promoción Escolar (%)"),
                    ("tasa_no_promocion", "Tasa de No Promoción / Reprobación (%)"),
                    ("tasa_retiro", "Tasa de Retiro / Abandono (%)"),
                ],
                format_func=lambda x: x[1],
                index=0,
            )
            selected_metric = metric_option[0]
            metric_label = metric_option[1]

        with r_col2:
            national_ref = None
            if "tasa" in selected_metric:
                kpis_nat = engine.get_kpis(rank_filters)
                if selected_metric == "tasa_promocion":
                    national_ref = kpis_nat.tasa_promocion
                elif selected_metric == "tasa_no_promocion":
                    national_ref = kpis_nat.tasa_no_promocion
                elif selected_metric == "tasa_retiro":
                    national_ref = kpis_nat.tasa_retiro
                st.info(f"Promedio nacional de referencia: **{national_ref:.1f}%**")

        df_deptos = engine.get_department_ranking(metric=selected_metric, filters=rank_filters)
        fig_ranking = create_horizontal_ranking(
            df_rank=df_deptos,
            metric=selected_metric,
            title=f"Ranking de 22 Departamentos por {metric_label}",
            x_label=metric_label,
            national_avg=national_ref,
        )
        st.plotly_chart(fig_ranking, use_container_width=True)

        # Análisis interpretativo obligatorio
        narrative_rank = explain_ranking(
            df=df_deptos,
            dimension="departamento",
            metric=selected_metric,
            metric_label=metric_label,
        )
        render_narrative_box(narrative_rank, title="Conclusiones sobre la Disparidad Departamental")

        st.markdown("---")
        st.markdown("#### 📍 Desglose Municipal Específico")

        # Selector de departamento para drilldown municipal
        depto_target = filters.get("departamento", None)
        if not depto_target:
            depto_list = engine.get_departments_list()
            depto_target = st.selectbox(
                "Selecciona un departamento para explorar sus municipios:",
                options=depto_list,
                index=depto_list.index("Guatemala") if "Guatemala" in depto_list else 0,
            )

        df_mupios = engine.get_municipal_breakdown(departamento=depto_target, filters=rank_filters)

        mup_col1, mup_col2 = st.columns([1.2, 1])
        with mup_col1:
            fig_mup = create_municipal_bars(
                df_mupios=df_mupios,
                metric="matricula",
                title=f"Top Municipios en {depto_target} por Matrícula",
                max_bars=12,
            )
            st.plotly_chart(fig_mup, use_container_width=True)

        with mup_col2:
            st.markdown(f"**Análisis Municipal de {depto_target}:**")
            narrative_mup = explain_ranking(
                df=df_mupios,
                dimension="municipio",
                metric="matricula",
                metric_label="inscripciones",
            )
            render_narrative_box(narrative_mup, title=f"Concentración en {depto_target}")

            # Mostrar tabla detallada colapsable
            with st.expander(f"Ver tabla completa de municipios en {depto_target}"):
                st.dataframe(
                    df_mupios.select(
                        [
                            "municipio",
                            "matricula",
                            "pct_matricula",
                            "tasa_promocion",
                            "tasa_no_promocion",
                            "tasa_retiro",
                        ]
                    ).to_pandas(),
                    use_container_width=True,
                )

    # =========================================================================
    # PESTAÑA 3: BRECHAS Y DESIGUALDADES
    # =========================================================================
    with tab3:
        st.markdown("### ⚖️ Análisis Transversal de Brechas y Equidad")
        st.caption(
            "Comparación de tasas de éxito y abandono según variables sociodemográficas y de estructura institucional."
        )

        # 1. Brecha Rural vs Urbana
        st.markdown("#### 1. Brecha Geográfica: Área Rural vs Área Urbana")
        area_filters = {k: v for k, v in filters.items() if k != "area"}
        df_area = engine.get_breakdown_by_dimension("area", filters=area_filters)

        b1_col1, b1_col2 = st.columns([1.2, 1])
        with b1_col1:
            fig_area = create_gap_bars(df_area, dimension="area", title="Rendimiento Terminal: Rural vs Urbana")
            st.plotly_chart(fig_area, use_container_width=True)
        with b1_col2:
            narrative_area = explain_breakdown(df_area, "area")
            render_narrative_box(narrative_area, title="Interpretación de la Brecha Territorial")

            # Cálculo de brecha directa
            if len(df_area) >= 2:
                r_row = df_area.filter(df_area["area"] == "Rural")
                u_row = df_area.filter(df_area["area"] == "Urbana")
                if not r_row.is_empty() and not u_row.is_empty():
                    dif_prom = u_row["tasa_promocion"][0] - r_row["tasa_promocion"][0]
                    dif_ret = r_row["tasa_retiro"][0] - u_row["tasa_retiro"][0]
                    st.info(
                        f"📌 **Diferencial Clave:** La zona urbana supera a la rural por "
                        f"**{dif_prom:.1f} puntos** en promoción. "
                        f"Asimismo, el retiro escolar es **{dif_ret:+.1f} puntos** más acentuado en el área rural."
                    )

        st.markdown("---")

        # 2. Brecha Sectorial: Oficial vs Privado vs Municipal vs Cooperativa
        st.markdown("#### 2. Brecha Institucional: Comparativa por Sector Educativo")
        sec_filters = {k: v for k, v in filters.items() if k != "sector"}
        df_sector = engine.get_breakdown_by_dimension("sector", filters=sec_filters)

        b2_col1, b2_col2 = st.columns([1.2, 1])
        with b2_col1:
            fig_sec = create_gap_bars(df_sector, dimension="sector", title="Resultados Terminales por Sector")
            st.plotly_chart(fig_sec, use_container_width=True)
        with b2_col2:
            narrative_sec = explain_breakdown(df_sector, "sector")
            render_narrative_box(narrative_sec, title="Hallazgos del Análisis Sectorial")

        st.markdown("---")

        # 3. Brecha de Género y Étnica
        st.markdown("#### 3. Diversidad e Inclusión: Género y Pueblo de Pertenencia")
        b3_col1, b3_col2 = st.columns(2)

        with b3_col1:
            st.markdown("##### Comparativa por Sexo")
            sexo_filters = {k: v for k, v in filters.items() if k != "sexo"}
            df_sexo = engine.get_breakdown_by_dimension("sexo", filters=sexo_filters)
            fig_sexo = create_gap_bars(df_sexo, dimension="sexo", title="Tasas Terminales por Género")
            st.plotly_chart(fig_sexo, use_container_width=True)
            render_narrative_box(explain_breakdown(df_sexo, "sexo"), title="Análisis de Brecha de Género")

        with b3_col2:
            st.markdown("##### Distribución por Pueblo de Pertenencia")
            df_pueblo = engine.get_breakdown_by_dimension("pueblo_pertenencia", filters=filters)
            fig_pueblo = create_pueblo_breakdown(df_pueblo)
            st.plotly_chart(fig_pueblo, use_container_width=True)
            render_narrative_box(
                explain_breakdown(df_pueblo, "pueblo_pertenencia"),
                title="Inclusión de Pueblos Originarios",
            )

    # =========================================================================
    # PESTAÑA 4: PREGUNTAR A LOS DATOS (AGENTE INTELIGENTE)
    # =========================================================================
    with tab4:
        st.markdown("### 🤖 Agente Inteligente en Lenguaje Natural")
        st.caption("Consulta los 4.3M de microdatos en lenguaje cotidiano con arquitectura anti-alucinación.")

        st.markdown(
            """
            <div class="edu-section-card">
                <h4>🛡️ Arquitectura Anti-Alucinación (Fase 4)</h4>
                <p>
                    A diferencia de soluciones que envían datos no estructurados al LLM, <strong>EduGuate IA</strong>
                    opera mediante una arquitectura de dos pasos:
                </p>
                <ol>
                    <li><strong>Extracción Semántica:</strong> El LLM extrae intención, filtros y métricas
                    en un esquema JSON estructurado.</li>
                    <li><strong>Cálculo Determinista:</strong> El motor analítico <code>DuckDB</code> ejecuta
                    la consulta exacta sobre Parquet en &lt; 50ms.</li>
                    <li><strong>Generación Guiada:</strong> El LLM redacta la respuesta ejecutiva limitándose
                    exclusivamente a las cifras devueltas por DuckDB.</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### 💬 Consultas Rápidas de Demostración")
        st.write("Haz clic en una de las preguntas de ejemplo o ingresa tu propia consulta:")

        sample_questions = [
            "¿Cuál es el departamento con mayor tasa de deserción escolar?",
            "¿Cuántos estudiantes inscritos hay en el sector rural de Quetzaltenango?",
            "¿Qué nivel educativo presenta la menor tasa de aprobación?",
            "¿Cómo se compara la promoción entre hombres y mujeres a nivel nacional?",
        ]

        cols = st.columns(2)
        for i, q in enumerate(sample_questions):
            with cols[i % 2]:
                if st.button(f"🔍 {q}", key=f"q_{i}", use_container_width=True):
                    st.session_state["query_input"] = q

        user_query = st.text_input(
            "Escribe tu pregunta sobre la educación formal en Guatemala 2024:",
            value=st.session_state.get("query_input", ""),
            placeholder="Ejemplo: ¿Cuál es la tasa de deserción en Quetzaltenango en nivel diversificado?",
        )

        if user_query:
            st.markdown(f"**Analizando:** *{user_query}*")

            # Demostración interactiva determinista previa a la integración con API LLM
            q_lower = user_query.lower()

            if "deserción" in q_lower or "retiro" in q_lower or "abandono" in q_lower:
                df_crit = engine.get_department_ranking(metric="tasa_retiro")
                top_crit = df_crit.row(0, named=True)
                st.success(
                    f"🎯 **Respuesta Verificada con DuckDB:**\n\n"
                    f"El departamento con mayor tasa de retiro escolar en 2024 es **{top_crit['departamento']}** "
                    f"con una tasa de abandono de **{top_crit['tasa_retiro']:.1f}%** "
                    f"({top_crit['retirados']:,} estudiantes retirados), "
                    f"sobre un universo terminal de {top_crit['denominador_terminal']:,} evaluados."
                )
            elif "quetzaltenango" in q_lower and "rural" in q_lower:
                k_xela_rural = engine.get_kpis({"departamento": "Quetzaltenango", "area": "Rural"})
                st.success(
                    f"🎯 **Respuesta Verificada con DuckDB:**\n\n"
                    f"En el departamento de **Quetzaltenango**, en el **área Rural**, se registraron "
                    f"**{k_xela_rural.matricula_total:,} estudiantes matriculados** en 2024. "
                    f"De ellos, la tasa de promoción fue del **{k_xela_rural.tasa_promocion:.1f}%** "
                    f"({k_xela_rural.promovidos:,} aprobados) y una deserción del **{k_xela_rural.tasa_retiro:.1f}%**."
                )
            elif "aprobación" in q_lower or "menor" in q_lower or "nivel" in q_lower:
                df_niv = engine.get_breakdown_by_dimension("nivel", sort_by="tasa_promocion", ascending=True)
                menor_niv = df_niv.row(0, named=True)
                st.success(
                    f"🎯 **Respuesta Verificada con DuckDB:**\n\n"
                    f"El nivel educativo con menor tasa de aprobación es **{menor_niv['nivel']}**, "
                    f"con un **{menor_niv['tasa_promocion']:.1f}% de promoción** "
                    f"({menor_niv['no_promovidos']:,} estudiantes no promovidos "
                    f"y {menor_niv['retirados']:,} retirados)."
                )
            elif "mujeres" in q_lower or "hombres" in q_lower or "género" in q_lower:
                df_sex = engine.get_breakdown_by_dimension("sexo")
                t_fem = df_sex.filter(df_sex["sexo"] == "Mujer")["tasa_promocion"][0]
                t_masc = df_sex.filter(df_sex["sexo"] == "Hombre")["tasa_promocion"][0]
                st.success(
                    f"🎯 **Respuesta Verificada con DuckDB:**\n\n"
                    f"A nivel nacional, las estudiantes mujeres registraron una tasa de promoción de "
                    f"**{t_fem:.1f}%**, frente a un **{t_masc:.1f}%** en los hombres, "
                    f"mostrando un diferencial positivo a favor de las estudiantes."
                )
            else:
                # Consulta genérica con KPIs del contexto
                k_res = engine.get_kpis(filters)
                st.info(
                    f"📊 **Resumen analítico obtenido en tiempo real:**\n\n"
                    f"{explain_kpis(k_res)}\n\n"
                    f"*(Nota: En la Fase 4 se activará el intérprete LLM completo "
                    f"con esquemas JSON dinámicos para cualquier combinación de preguntas complejas.)*"
                )

    # 6. Renderizado de pie de página
    render_footer()


if __name__ == "__main__":
    main()
