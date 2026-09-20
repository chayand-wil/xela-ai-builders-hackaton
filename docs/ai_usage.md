# Uso de IA en EduGuate IA

El modelo de lenguaje **interpreta** la pregunta (métrica, filtros, agrupación) y **redacta** con cifras que ya calculó `src.analytics` (DuckDB sobre Parquet).

- Con `OPENAI_API_KEY` se usa salida JSON estructurada (`gpt-4o-mini` por defecto).
- Sin clave, el intérprete demo cubre el banco de preguntas del plan (palabras clave).
- Wren (`wren/`) documenta el significado de columnas, enums y tasas. **Las cifras del producto no salen de `wren query`.**
- Preguntas de notas, discapacidad, historia o predicción se rechazan en `src/agent/guardrails.py`.
