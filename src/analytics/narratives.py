"""Generador determinista de análisis escrito interpretativo para acompañar visualizaciones y KPIs.

Cumple el requisito estricto del hackatón:
'No basta con mostrar la visualización, hay que explicar qué significa y qué se concluye de ella
para un público no técnico.'
"""

from __future__ import annotations

import polars as pl

from src.analytics.indicators import KPISummary


def explain_kpis(kpis: KPISummary) -> str:
    """Genera una narrativa clara y ejecutiva para un resumen de indicadores."""
    if kpis.matricula_total == 0:
        return "No se encontraron registros para la combinación de filtros seleccionada."

    ambito = "a nivel nacional"
    if "departamento" in kpis.filters and kpis.filters["departamento"]:
        ambito = f"en el departamento de {kpis.filters['departamento']}"
    if "municipio" in kpis.filters and kpis.filters["municipio"]:
        ambito += f", municipio de {kpis.filters['municipio']}"

    # Construir texto explicativo
    p1 = (
        f"Durante el ciclo escolar 2024 se registraron **{kpis.matricula_total:,} inscripciones** {ambito}. "
        f"De los estudiantes que cerraron el ciclo escolar con resultado terminal conocido, "
        f"el **{kpis.tasa_promocion:.1f}% ({kpis.promovidos:,}) culminó promovido** al siguiente grado."
    )

    detalles = []
    if kpis.tasa_no_promocion > 0:
        detalles.append(f"un **{kpis.tasa_no_promocion:.1f}% ({kpis.no_promovidos:,}) no logró la promoción**")
    if kpis.tasa_retiro > 0:
        detalles.append(f"un **{kpis.tasa_retiro:.1f}% ({kpis.retirados:,}) abandonó o se retiró** del ciclo escolar")

    if detalles:
        p2 = " En contraste, " + " y ".join(detalles) + "."
    else:
        p2 = ""

    p3 = ""
    if kpis.repitentes > 0:
        p3 = (
            f" Adicionalmente, el **{kpis.tasa_repitencia:.1f}% ({kpis.repitentes:,})** "
            "corresponde a estudiantes que estaban repitiendo el grado."
        )

    return p1 + p2 + p3


def explain_ranking(
    df: pl.DataFrame,
    dimension: str = "departamento",
    metric: str = "matricula",
    metric_label: str = "inscripciones",
) -> str:
    """Genera un párrafo analítico comparando los extremos (mayor y menor) de un ranking."""
    if df.is_empty():
        return "No hay datos suficientes para generar un análisis comparativo."

    # Ordenar de mayor a menor
    df_sorted = df.sort(metric, descending=True)
    top_row = df_sorted.row(0, named=True)
    bottom_row = df_sorted.row(-1, named=True)

    top_name = top_row.get(dimension, "N/A")
    top_val = top_row.get(metric, 0)
    bottom_name = bottom_row.get(dimension, "N/A")
    bottom_val = bottom_row.get(metric, 0)

    total_sum = df[metric].sum() if metric in ["matricula", "promovidos", "retirados"] else None

    if metric == "matricula" and total_sum:
        top_pct = (top_val / total_sum) * 100.0
        return (
            f"El territorio con mayor volumen de matrícula es **{top_name}**, acumulando **{top_val:,} inscripciones** "
            f"({top_pct:.1f}% del total evaluado). En el extremo opuesto se sitúa **{bottom_name}** con "
            f"**{bottom_val:,}**, reflejando una marcada concentración territorial de la población estudiantil."
        )

    if "tasa" in metric:
        brecha = top_val - bottom_val
        return (
            f"Existe una brecha de **{brecha:.1f} puntos porcentuales** en la {metric_label.lower()}: "
            f"**{top_name}** presenta el valor más elevado (**{top_val:.1f}%**), "
            f"mientras que **{bottom_name}** registra el índice más bajo (**{bottom_val:.1f}%**). "
            f"Esta disparidad evidencia desigualdades estructurales en las condiciones educativas territoriales."
        )

    return (
        f"El valor más alto se concentra en **{top_name}** ({top_val:,} {metric_label}), "
        f"mientras que **{bottom_name}** registra la menor cifra ({bottom_val:,} {metric_label})."
    )


def explain_breakdown(
    df: pl.DataFrame,
    dimension: str,
) -> str:
    """Explica la distribución porcentual y resalta puntos críticos de abandono o aprobación."""
    if df.is_empty():
        return "No hay registros disponibles para este desglose."

    df_sorted = df.sort("matricula", descending=True)
    mayor = df_sorted.row(0, named=True)
    mayor_nombre = mayor.get(dimension, "N/A")
    mayor_pct = mayor.get("pct_matricula", 0.0)
    mayor_mat = mayor.get("matricula", 0)

    texto = (
        f"La mayor concentración de estudiantes se localiza en **{mayor_nombre}**, "
        f"abarcando el **{mayor_pct:.1f}% de la matrícula ({mayor_mat:,} inscripciones)**."
    )

    # Identificar el punto crítico de retiro si la columna existe
    if "tasa_retiro" in df.columns:
        df_retiro = df.filter(pl.col("tasa_retiro").is_not_null()).sort("tasa_retiro", descending=True)
        if not df_retiro.is_empty():
            critico = df_retiro.row(0, named=True)
            crit_nombre = critico.get(dimension, "N/A")
            crit_tasa = critico.get("tasa_retiro", 0.0)
            if crit_nombre != mayor_nombre:
                texto += (
                    f" Sin embargo, el segmento con mayor vulnerabilidad de abandono es **{crit_nombre}**, "
                    f"donde la tasa de retiro alcanza un crítico **{crit_tasa:.1f}%**."
                )

    return texto
