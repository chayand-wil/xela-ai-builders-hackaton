# Tasas y enums — EduGuate IA

## Grano
- Cada fila es una **inscripción** del ciclo 2024, no un estudiante único y no una escuela.

## Enum `resultado`
- Promovido
- Vigente (fuera del denominador de tasas de cierre)
- Retirado
- Retirado definitivo
- No promovido
- Ignorado (código 9 ya viene como este texto; no es nulo)

## Denominador de tasas de resultado
Denominador = Promovido + No promovido + Retirado + Retirado definitivo.

## Retiro
withdrawal = Retirado + Retirado definitivo.

## Vigente e Ignorado
Se reportan aparte. No entran en promoción, no promoción ni retiro.

## Código de establecimiento
No llamar «número de escuelas» al conteo distinto de `codigo_establecimiento`.

## Cifras del producto
Las cifras las calcula `src/analytics` con DuckDB parametrizado. Wren es contexto. No uses `wren query` como fuente de números del dashboard ni del chat.
