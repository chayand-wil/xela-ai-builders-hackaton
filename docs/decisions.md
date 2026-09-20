# Registro de Decisiones de Arquitectura (ADRs) — EduGuate IA

Este documento registra formalmente las decisiones técnicas, metodológicas y arquitectónicas tomadas durante el desarrollo de **EduGuate IA**, justificando el contexto, las alternativas evaluadas y las razones de su elección.

---

## ADR-001: Adopción de Apache Parquet y DuckDB para el Almacenamiento y Consulta

### Estado: Aprobado e Implementado
### Fecha: 2026-09-20

### Contexto:
El dataset crudo consta de 22 archivos Excel (`.xlsx`) con un total de 4,298,887 registros y un peso conjunto superior a 210 MB. Leer estos archivos directamente en tiempo real en una aplicación web o en un agente provocaría latencias inaceptables (> 20 segundos por consulta) y saturaría la memoria RAM.

### Alternativas Consideradas:
1. **Base de Datos Relacional Tradicional (PostgreSQL / MySQL):** Excelente para concurrencia, pero introduce una dependencia de infraestructura externa, configuración de credenciales y dificulta la reproducibilidad local inmediata exigida en la evaluación.
2. **SQLite:** Ligero y sin servidor, pero su modelo de almacenamiento por filas es ineficiente para agregaciones analíticas sobre 4.3 millones de filas.
3. **Apache Parquet + DuckDB:** Formato columnar comprimido con Zstandard (`zstd`) consultado mediante un motor analítico embebido (*in-process OLAP*).

### Decisión:
Se eligió **Apache Parquet + DuckDB**:
- El dataset de 4.3 millones de registros se comprimió a tan solo **2.32 MB** (reducción > 98%).
- DuckDB ejecuta consultas de agregación y filtros sobre el archivo Parquet en menos de **50 milisegundos**.
- Cero infraestructura externa: 100% reproducible localmente en cualquier máquina sin necesidad de configurar servicios de base de datos.

---

## ADR-002: Normalización del Prefijo `00-` y Asignación al Municipio de Guatemala Capital (`0101`)

### Estado: Aprobado e Implementado
### Fecha: 2026-09-20

### Contexto:
En el archivo `guatemala-2024.xlsx`, aproximadamente 309,919 registros (cerca del 36% del departamento) presentan el prefijo histórico `00-` en el campo `CodEstablecimiento` (ej. `00-18-0001-43`), en lugar de `01-`. El segundo segmento de estos códigos corresponde a la zona de la Ciudad de Guatemala (Zonas 1 a 25, salvo 20, 22 y 23 que no existen).

### Riesgo Identificado:
Si el segundo segmento se interpretara ingenuamente como código de municipio, el departamento de Guatemala reportaría 39 municipios ficticios en lugar de los 17 oficiales, y más de 310 mil estudiantes quedarían mal atribuidos geográficamente.

### Decisión:
1. Todos los registros con prefijo `00-` pertenecen administrativamente a la Ciudad de Guatemala y se les asigna estrictamente el código municipal oficial del INE: `0101` (`Guatemala`).
2. En el código del establecimiento, el prefijo `00-` se normaliza a `01-` para mantener la coherencia estructural del código (`DD-MM-NNNN-SS`).
3. **Resultado verificado:** El departamento de Guatemala reporta exactamente **17 municipios** y el total nacional se mantiene en los **340 municipios** oficiales con datos.

---

## ADR-003: Principio de Separación Estricta entre Capa Analítica y Modelo de Lenguaje (Anti-Alucinación)

### Estado: Aprobado
### Fecha: 2026-09-20

### Contexto:
Los Modelos de Lenguaje (LLMs) son propensos a cometer errores de cálculo matemático ("alucinaciones numéricas") cuando se les pide realizar conteos o porcentajes directamente sobre grandes volúmenes de texto o datos sin procesar.

### Decisión:
Establecer un desacoplamiento estricto:
- **La capa de código (DuckDB + Python)** es la única responsable de filtrar, contar y calcular tasas.
- **El agente LLM** actúa como un traductor semántico: convierte la intención del usuario a una llamada de consulta tipada, recibe los datos agregados exactos y genera la explicación en lenguaje natural.
- El LLM **nunca genera SQL libre ni ejecuta código arbitrario** sobre la base de datos.

---

## ADR-004: Metodología para el Cálculo de Tasas de Resultado Escolar

### Estado: Aprobado
### Fecha: 2026-09-20

### Contexto:
La variable `Resultado_F` incluye 6 categorías: `Promovido`, `Vigente`, `Retirado`, `Retirado definitivo`, `No promovido` e `Ignorado`.

### Decisión:
1. **Denominador de Tasas:** Las tasas de promoción, no promoción y retiro se calculan sobre el universo de registros con resultado terminal conocido:
   $$\text{Denominador} = \text{Promovidos} + \text{No promovidos} + \text{Retirados} + \text{Retirados definitivos}$$
2. **Retiro Consolidado:** Los códigos `3` (`Retirado`) y `4` (`Retirado definitivo`) se combinan para la métrica general de abandono/retiro escolar (5.5%).
3. **Exclusiones:** Los registros clasificados como `Vigente` (0.05%) e `Ignorado` se reportan por separado como categorías explícitas y se excluyen del denominador de las tasas de resultado para no distorsionar el indicador de cierre de ciclo.

---

## ADR-005: Elección de Streamlit y Plotly para la Interfaz del Dashboard

### Estado: Aprobado
### Fecha: 2026-09-20

### Contexto:
El dashboard debe ser interactivo, intuitivo para usuarios no técnicos y fácil de defender técnicamente en un pitch de 5 minutos.

### Alternativas Consideradas:
1. **Framework Web Complejo (Next.js / React + FastAPI):** Proporciona una interfaz moderna pero duplica el esfuerzo de desarrollo (dos lenguajes, dos entornos) y aumenta la complejidad de explicación en el pitch sin sumar valor sustancial a los criterios de evaluación.
2. **Streamlit + Plotly:** Ecosistema nativo en Python, reactivo, con componentes interactivos y visualizaciones profesionales integradas en el mismo lenguaje del pipeline.

### Decisión:
Se adoptó **Streamlit + Plotly** por su rapidez de iteración, integración directa con DuckDB y la capacidad de situar fácilmente bloques de **análisis escrito interpretativo** junto a cada visualización.

---

## ADR-006: WrenAI como capa semántica, no como motor de cifras del producto

### Estado: Aprobado
### Fecha: 2026-09-20

### Contexto:
El equipo pidió instalar el agente WrenAI desde la carpeta local `Downloads/WrenAI-main`. Wren genera SQL gobernado (MDL) y es útil para documentar significado de columnas, enumeraciones y métricas. El plan del hackatón y ADR-003 prohíben SQL libre del modelo como fuente de cifras.

### Decisión:
1. Instalar el paquete `wrenai` (CLI + SDK) y el skill de descubrimiento en `.cursor/skills/wren/`.
2. Modelar el Parquet de Educación Formal 2024 como proyecto Wren (DuckDB) para contexto y validación de definiciones.
3. **El dashboard y el chat de producto siguen calculando solo con `src/analytics` (consultas parametrizadas DuckDB).** Wren no sustituye esa capa.
4. El intérprete LLM mapea la pregunta a métricas permitidas; si Wren se usa, es para enriquecer contexto o dry-plan, no para ejecutar SQL arbitrario en la demo.
