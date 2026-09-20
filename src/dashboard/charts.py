"""Generador de gráficos interactivos con Plotly para el Dashboard EduGuate IA.

Diseñado con una estética visual moderna, paletas semánticas armoniosas,
etiquetas formateadas en español y tiempos de renderizado ultrarrápidos.
"""

from __future__ import annotations

import plotly.graph_objects as go
import polars as pl

from src.analytics.indicators import KPISummary

# Paleta de colores curada y consistente
COLOR_PALETTE = {
    "promovido": "#10B981",  # Esmeralda / Verde éxito
    "no_promovido": "#F59E0B",  # Ámbar / Alerta
    "retirado": "#EF4444",  # Carmesí / Riesgo abandono
    "primary": "#2563EB",  # Azul institucional
    "primary_dark": "#1E3A8A",  # Azul marino profundo
    "accent": "#0D9488",  # Teal / Verde azulado
    "secondary": "#8B5CF6",  # Violeta
    "neutral_dark": "#1E293B",  # Slate 800
    "neutral_light": "#F8FAFC",  # Slate 50
    "grid": "#E2E8F0",  # Slate 200
}

FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"


def _apply_layout_defaults(
    fig: go.Figure,
    title: str = "",
    height: int = 380,
    show_legend: bool = True,
) -> go.Figure:
    """Aplica estándares visuales consistentes a cualquier figura de Plotly."""
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>" if title else "",
            "font": {"size": 15, "color": COLOR_PALETTE["neutral_dark"], "family": FONT_FAMILY},
            "x": 0.02,
            "y": 0.95,
        },
        font={"family": FONT_FAMILY, "color": COLOR_PALETTE["neutral_dark"]},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin={"l": 25, "r": 25, "t": 45, "b": 25},
        showlegend=show_legend,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.2,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 12},
        },
        hoverlabel={
            "bgcolor": "#0F172A",
            "font_size": 12,
            "font_color": "#F8FAFC",
            "font_family": FONT_FAMILY,
        },
    )
    return fig


def create_donut_results(kpis: KPISummary) -> go.Figure:
    """Genera un gráfico tipo Donut con los resultados del ciclo escolar y tasa central."""
    labels = ["Promovidos", "No promovidos", "Retirados"]
    values = [kpis.promovidos, kpis.no_promovidos, kpis.retirados]
    colors = [
        COLOR_PALETTE["promovido"],
        COLOR_PALETTE["no_promovido"],
        COLOR_PALETTE["retirado"],
    ]

    total_terminal = sum(values)
    if total_terminal == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Sin registros terminales para mostrar",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 14, "color": "#94A3B8"},
        )
        return _apply_layout_defaults(fig, "Resultados del Ciclo", show_legend=False)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.68,
                marker={"colors": colors, "line": {"color": "#FFFFFF", "width": 2}},
                textinfo="percent",
                textfont={"size": 13, "color": "#FFFFFF", "family": FONT_FAMILY},
                hovertemplate=(
                    "<b>%{label}</b><br>Estudiantes: %{value:,.0f}<br>Porcentaje: %{percent:.1%}<extra></extra>"
                ),
                sort=False,
            )
        ]
    )

    # Indicador central de Tasa de Promoción
    prom_text = (
        f"<span style='font-size:26px; font-weight:800; color:{COLOR_PALETTE['promovido']}'>"
        f"{kpis.tasa_promocion:.1f}%</span><br>"
        "<span style='font-size:12px; color:#64748B; font-weight:600'>Promoción</span>"
    )
    fig.add_annotation(
        text=prom_text,
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"family": FONT_FAMILY},
    )

    return _apply_layout_defaults(fig, "Distribución de Resultados Terminales", height=350)


def create_bar_levels(df_levels: pl.DataFrame) -> go.Figure:
    """Genera un gráfico de barras verticales con la matrícula por nivel educativo."""
    if df_levels.is_empty():
        fig = go.Figure()
        return _apply_layout_defaults(fig, "Matrícula por Nivel Educativo")

    df_pd = df_levels.to_pandas()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_pd["nivel"],
            y=df_pd["matricula"],
            text=df_pd["matricula"].apply(lambda v: f"{v:,.0f}"),
            textposition="auto",
            textfont={"size": 12, "color": "#FFFFFF", "family": FONT_FAMILY},
            marker={
                "color": df_pd["matricula"],
                "colorscale": [
                    [0.0, "#93C5FD"],
                    [0.5, "#3B82F6"],
                    [1.0, "#1D4ED8"],
                ],
                "line": {"color": "#FFFFFF", "width": 1},
            },
            customdata=df_pd["tasa_promocion"] if "tasa_promocion" in df_pd.columns else None,
            hovertemplate="<b>%{x}</b><br>Matrícula: %{y:,.0f}<br>Tasa Promoción: %{customdata:.1f}%<extra></extra>",
        )
    )

    fig.update_xaxes(
        title=None,
        tickangle=-15,
        tickfont={"size": 11, "color": COLOR_PALETTE["neutral_dark"]},
    )
    fig.update_yaxes(
        title="Estudiantes inscritos",
        gridcolor=COLOR_PALETTE["grid"],
        zeroline=False,
    )

    return _apply_layout_defaults(fig, "Matrícula Estudiantil por Nivel Educativo", height=350, show_legend=False)


def create_horizontal_ranking(
    df_rank: pl.DataFrame,
    metric: str = "matricula",
    title: str = "Ranking de Departamentos",
    x_label: str = "Matrícula Total",
    national_avg: float | None = None,
) -> go.Figure:
    """Genera un ranking horizontal de los 22 departamentos con línea opcional de promedio nacional."""
    if df_rank.is_empty():
        fig = go.Figure()
        return _apply_layout_defaults(fig, title)

    # Ordenar ascendente para que el top quede en la parte superior del gráfico horizontal
    df_sorted = df_rank.sort(metric, descending=False).to_pandas()

    is_rate = "tasa" in metric

    if is_rate:
        text_labels = df_sorted[metric].apply(lambda v: f"{v:.1f}%")
        hovertemplate = "<b>%{y}</b><br>" + x_label + ": %{x:.2f}%<extra></extra>"
        colorscale = "Viridis" if metric == "tasa_promocion" else "Reds"
    else:
        text_labels = df_sorted[metric].apply(lambda v: f"{v:,.0f}")
        hovertemplate = "<b>%{y}</b><br>" + x_label + ": %{x:,.0f}<extra></extra>"
        colorscale = "Blues"

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df_sorted["departamento"],
            x=df_sorted[metric],
            orientation="h",
            text=text_labels,
            textposition="auto",
            textfont={"size": 11, "family": FONT_FAMILY},
            marker={
                "color": df_sorted[metric],
                "colorscale": colorscale,
                "line": {"color": "#FFFFFF", "width": 1},
            },
            hovertemplate=hovertemplate,
        )
    )

    fig.update_xaxes(
        title=x_label,
        gridcolor=COLOR_PALETTE["grid"],
        zeroline=False,
    )
    fig.update_yaxes(
        title=None,
        tickfont={"size": 11, "color": COLOR_PALETTE["neutral_dark"]},
    )

    # Línea de referencia de promedio nacional si aplica
    if national_avg is not None and national_avg > 0:
        fig.add_vline(
            x=national_avg,
            line_width=2,
            line_dash="dash",
            line_color="#DC2626",
            annotation_text=f"Promedio Nal: {national_avg:.1f}{'%' if is_rate else ''}",
            annotation_position="top right",
            annotation_font={"size": 11, "color": "#DC2626", "family": FONT_FAMILY},
        )

    # Altura dinámica según la cantidad de barras
    height = max(450, len(df_sorted) * 24 + 100)
    return _apply_layout_defaults(fig, title, height=height, show_legend=False)


def create_municipal_bars(
    df_mupios: pl.DataFrame,
    metric: str = "matricula",
    title: str = "Top Municipios",
    max_bars: int = 15,
) -> go.Figure:
    """Genera un gráfico de barras horizontales para municipios dentro de un departamento."""
    if df_mupios.is_empty():
        fig = go.Figure()
        return _apply_layout_defaults(fig, title)

    df_subset = df_mupios.sort(metric, descending=True).head(max_bars)
    df_sorted = df_subset.sort(metric, descending=False).to_pandas()

    is_rate = "tasa" in metric
    text_labels = df_sorted[metric].apply(lambda v: f"{v:.1f}%" if is_rate else f"{v:,.0f}")

    fig = go.Figure(
        go.Bar(
            y=df_sorted["municipio"],
            x=df_sorted[metric],
            orientation="h",
            text=text_labels,
            textposition="auto",
            textfont={"size": 11, "family": FONT_FAMILY},
            marker={"color": "#0D9488", "line": {"color": "#FFFFFF", "width": 1}},
            hovertemplate="<b>%{y}</b><br>Valor: %{x}<extra></extra>",
        )
    )

    fig.update_xaxes(gridcolor=COLOR_PALETTE["grid"])
    fig.update_yaxes(tickfont={"size": 11})

    height = max(360, len(df_sorted) * 26 + 80)
    return _apply_layout_defaults(fig, title, height=height, show_legend=False)


def create_gap_bars(
    df_gap: pl.DataFrame,
    dimension: str,
    title: str = "Comparativa de Brechas",
) -> go.Figure:
    """Genera una comparativa visual de resultados terminales por grupos (ej. Rural vs Urbana)."""
    if df_gap.is_empty():
        fig = go.Figure()
        return _apply_layout_defaults(fig, title)

    df_pd = df_gap.to_pandas()

    fig = go.Figure()

    # Barra de Promovidos
    fig.add_trace(
        go.Bar(
            x=df_pd[dimension],
            y=df_pd["tasa_promocion"],
            name="Tasa de Promoción (%)",
            marker_color=COLOR_PALETTE["promovido"],
            text=df_pd["tasa_promocion"].apply(lambda v: f"{v:.1f}%"),
            textposition="inside",
            textfont={"size": 12, "color": "#FFFFFF", "family": FONT_FAMILY},
            hovertemplate="<b>%{x}</b><br>Promoción: %{y:.1f}%<extra></extra>",
        )
    )

    # Barra de No Promovidos
    fig.add_trace(
        go.Bar(
            x=df_pd[dimension],
            y=df_pd["tasa_no_promocion"],
            name="Tasa de No Promoción (%)",
            marker_color=COLOR_PALETTE["no_promovido"],
            text=df_pd["tasa_no_promocion"].apply(lambda v: f"{v:.1f}%"),
            textposition="inside",
            textfont={"size": 12, "color": "#FFFFFF", "family": FONT_FAMILY},
            hovertemplate="<b>%{x}</b><br>No promoción: %{y:.1f}%<extra></extra>",
        )
    )

    # Barra de Retiro
    fig.add_trace(
        go.Bar(
            x=df_pd[dimension],
            y=df_pd["tasa_retiro"],
            name="Tasa de Retiro / Abandono (%)",
            marker_color=COLOR_PALETTE["retirado"],
            text=df_pd["tasa_retiro"].apply(lambda v: f"{v:.1f}%"),
            textposition="inside",
            textfont={"size": 12, "color": "#FFFFFF", "family": FONT_FAMILY},
            hovertemplate="<b>%{x}</b><br>Retiro: %{y:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(barmode="group")
    fig.update_yaxes(
        title="Porcentaje (%)",
        gridcolor=COLOR_PALETTE["grid"],
        range=[0, 105],
    )
    fig.update_xaxes(title=None, tickfont={"size": 12, "weight": "bold"})

    return _apply_layout_defaults(fig, title, height=380, show_legend=True)


def create_pueblo_breakdown(df_pueblo: pl.DataFrame) -> go.Figure:
    """Genera un gráfico de distribución por Pueblo de Pertenencia con tasas de promoción."""
    if df_pueblo.is_empty():
        fig = go.Figure()
        return _apply_layout_defaults(fig, "Distribución por Pueblo de Pertenencia")

    df_pd = df_pueblo.sort("matricula", descending=False).to_pandas()

    fig = go.Figure(
        go.Bar(
            y=df_pd["pueblo_pertenencia"],
            x=df_pd["matricula"],
            orientation="h",
            text=df_pd["matricula"].apply(lambda v: f"{v:,.0f}"),
            textposition="auto",
            textfont={"size": 11, "family": FONT_FAMILY},
            marker={"color": "#6366F1", "line": {"color": "#FFFFFF", "width": 1}},
            customdata=df_pd["tasa_promocion"],
            hovertemplate="<b>%{y}</b><br>Matrícula: %{x:,.0f}<br>Tasa Promoción: %{customdata:.1f}%<extra></extra>",
        )
    )

    fig.update_xaxes(title="Matrícula Total", gridcolor=COLOR_PALETTE["grid"])
    fig.update_yaxes(title=None)

    height = max(300, len(df_pd) * 35 + 80)
    return _apply_layout_defaults(fig, "Matrícula por Pueblo de Pertenencia", height=height, show_legend=False)
