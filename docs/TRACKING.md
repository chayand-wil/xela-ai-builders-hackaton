# Control de Avances — EduGuate IA (Hackatón AI Builders GT)

> **Documento vivo para monitorear el progreso, hitos completados, entregables y próximas tareas del proyecto.**

---

## 🧭 Resumen General del Proyecto

| Métrica | Estado |
|---|---|
| **Progreso General Estimado** | **90%** |
| **Puntaje Objetivo** | **100 / 100 puntos** |
| **Dataset Base Procesado** | **4,298,887 registros** (100% del censo escolar 2024) |
| **Última Actualización** | 2026-09-20 |

```
[███████████████████████████░] 90% Completado
```

---

## 📋 Matriz de Fases

| Fase | Componente | Responsabilidad Principal | Estado |
|:---:|---|---|:---:|
| **Fase 0** | **Setup & Auditoría** | Entorno virtual, dependencias, auditoría de 23 archivos | ✅ **100% Completado** |
| **Fase 1** | **Ingesta & ETL** | Extracción, decodificación, limpieza `00-`, validación Parquet | ✅ **100% Completado** |
| **Fase 2** | **Motor Analítico** | Consultas DuckDB, centralización de fórmulas de indicadores | ✅ **100% Completado** |
| **Fase 3** | **Dashboard** | Streamlit + Plotly, vista general y territorial, análisis escrito | ✅ **100% Completado** |
| **Fase 4** | **Agente con IA** | Agente conversacional LLM sin alucinación de cifras (Groq + DuckDB) | ✅ **100% Completado** |
| **Fase 5** | **Entrega & Pitch** | 2 Videos (Arquitectura y Demo), README final y pitch de 5 min | 🔄 **Siguiente Fase** |

---

## 🔍 Detalle por Fase y Checklists

### ✅ Fase 0: Setup y Auditoría de Datos (100%)
- [x] Auditoría de los 23 archivos oficiales estipulados por el hackatón.
- [x] Identificación y descarga de los 3 archivos faltantes (`chiquimula`, `quetzaltenango`, `zacapa`).
- [x] Unificación y estructuración de los 22 departamentos en `Data/`.
- [x] Creación de entorno virtual reproducible con Python 3.12 (`.venv`).
- [x] Configuración de `requirements.txt`, `pyproject.toml` y `.gitignore`.
- [x] Conexión remota SSH con GitHub configurada y verificada.

---

### ✅ Fase 1: Ingesta & ETL (100%)
- [x] **Módulo de Catálogos (`src/ingestion/catalogs.py`):**
  - [x] Mapeo de las 10 variables codificadas (Sector, Área, Sexo, Nivel, Pueblo, Plan, Jornada, Resultado, Repitente, Graduando).
  - [x] Mapeo de los 22 departamentos y los 340 municipios por código de 4 dígitos.
- [x] **Lector de Archivos (`src/ingestion/loader.py`):**
  - [x] Detección inteligente de hojas válidas (resolución de hojas vacías en `solola_2024.xlsx`).
  - [x] Validación del contrato estricto de 15 columnas originales.
  - [x] Integración de motor Calamine en Rust para lectura de alto rendimiento.
- [x] **Limpieza y Transformación (`src/ingestion/cleaner.py`):**
  - [x] Normalización de prefijo `00-` a `01-` en `CodEstablecimiento` de Guatemala.
  - [x] Derivación correcta del municipio de la capital (`0101`) para los ~310 mil registros especiales.
  - [x] Derivación municipal estándar para el resto de departamentos (segmentos 1 y 2).
  - [x] Preservación de códigos `9` formalmente como `"Ignorado"`.
  - [x] Generación del esquema normalizado de 17 columnas de salida.
- [x] **Validación contra Ground Truth (`src/ingestion/validation.py`):**
  - [x] 4,298,887 filas verificadas (Diferencia: 0).
  - [x] 17 municipios verificados en el departamento de Guatemala.
  - [x] 340 municipios verificados a nivel nacional.
  - [x] Proporciones de Sector, Área, Sexo, Nivel y Resultado validadas con 0% de error.
  - [x] Emisión de reporte formal de auditoría (`Data/processed/validation_report.json`).
- [x] **Orquestación y Exportación (`scripts/process_data.py`):**
  - [x] Procesamiento de los 4.3 millones de registros en 16.88 segundos.
  - [x] Generación de `educacion_formal_2024.parquet` (2.32 MB).
  - [x] Generación de `educacion_formal_sample.parquet` (108 KB, 10,000 filas).
- [x] **Pruebas y Calidad:**
  - [x] 6/6 pruebas unitarias aprobadas con Pytest (`tests/test_ingestion.py`).
  - [x] 100% código aprobado por el linter `ruff`.
- [x] **Documentación:**
  - [x] Creación de `docs/data_dictionary.md`.

---

### ✅ Fase 2: Motor Analítico y Capa de Consultas DuckDB (100%)
- [x] **Configuración de DuckDB:** Conexión in-memory directa y ultrarrápida sobre `educacion_formal_2024.parquet` (< 50ms).
- [x] **Módulo de Consultas (`src/analytics/queries.py`):**
  - [x] Filtros parametrizados seguros contra inyecciones SQL.
  - [x] KPIs oficiales con métricas terminales y desgloses.
  - [x] Agregaciones por dimensión (`nivel`, `sector`, `area`, `sexo`, `pueblo`).
  - [x] Rankings de los 22 departamentos por matrícula y tasas.
  - [x] Desgloses municipales completos (los 340 municipios disponibles).
  - [x] Tabulación cruzada bidimensional (`sector` × `area`, etc.).
- [x] **Módulo de Fórmulas e Indicadores (`src/analytics/indicators.py`):**
  - [x] Fórmulas oficiales implementadas (Promoción: 85.28%, No promoción: 9.19%, Retiro: 5.53%).
  - [x] Exclusión explícita de `Vigente` e `Ignorado` del denominador terminal (ADR-004).
  - [x] Modelos Pydantic (`KPISummary`, `MetricResult`) para contratos tipados.
- [x] **Generador de Narrativas Automáticas (`src/analytics/narratives.py`):**
  - [x] Explicaciones deterministas de KPIs en lenguaje accesible.
  - [x] Análisis comparativo de rankings (detección de extremos y brechas porcentuales).
  - [x] Análisis interpretativo de desgloses por nivel y dimensión.
- [x] **Pruebas y Calidad:**
  - [x] 8/8 pruebas unitarias aprobadas en `tests/test_analytics.py` (total suite: 14/14 tests PASS).
  - [x] 100% código aprobado por el linter `ruff`.

---

### ✅ Fase 3: Dashboard Interactivo (Streamlit + Plotly) (100%)
- [x] **Arquitectura y Layout (`app.py`):**
  - [x] Configuración multipestaña optimizada para fluidez y renderizado responsivo.
  - [x] Inyección de estilos CSS avanzados y tipografía moderna (`src/dashboard/components.py`).
  - [x] Caching de alta eficiencia con `@st.cache_resource` para DuckDB.
- [x] **Pestaña 1: Panorama Nacional:**
  - [x] 4 Tarjetas KPI visuales con código semántico de color (Matrícula, Promoción, No Promoción, Retiro).
  - [x] Gráfico Donut de resultados terminales con tasa centralizada.
  - [x] Gráfico de barras por nivel educativo con gradientes visuales.
  - [x] Indicadores adicionales de trayectoria (repitencia, graduandos, vigentes/ignorados).
  - [x] Análisis escrito interpretativo obligatorio debajo de cada gráfica (`src/analytics/narratives.py`).
- [x] **Pestaña 2: Exploración Territorial:**
  - [x] Selector dinámico de métricas (Matrícula, Tasa de Promoción, No Promoción, Retiro).
  - [x] Ranking horizontal interactivo de los 22 departamentos con línea promedio nacional de referencia.
  - [x] Desglose municipal con visualización y tabla interactiva para los 340 municipios.
  - [x] Análisis explicativo de concentración poblacional y disparidad territorial.
- [x] **Pestaña 3: Brechas y Desigualdades:**
  - [x] Comparativa de brecha geográfica (Rural vs Urbana) con cálculo de diferencial de puntos.
  - [x] Comparativa de brecha sectorial (Oficial, Privado, Municipal, Cooperativa).
  - [x] Comparativa de brecha de género (Hombre vs Mujer).
  - [x] Distribución por pueblo de pertenencia y tasas de promoción asociadas.
  - [x] Explicación interpretativa para no técnicos en cada dimensión de brecha.
- [x] **Pestaña 4: Preguntar a los Datos (Preparación Fase 4):**
  - [x] Arquitectura conceptual anti-alucinación visible para los jueces.
  - [x] Consultas de demostración rápida verificadas en tiempo real contra DuckDB.
- [x] **Pruebas y Calidad:**
  - [x] 6 pruebas unitarias de gráficos y componentes (`tests/test_dashboard.py`).
  - [x] Total suite: 20/20 pruebas PASS en 1.45s.
  - [x] Verificación de inicialización de servidor Streamlit con HTTP 200 OK.
  - [x] 100% código conforme con `ruff check` y `ruff format`.

---

### ✅ Fase 4: Agente Conversacional en Lenguaje Natural (100%)
- [x] **Modal de Bienvenida y Asistente de Referencia (`src/dashboard/components.py`):**
  - [x] Modal interactivo inicial con 2 rutas: Configuración de Audiencia/Referencia vs Exploración Directa.
  - [x] Asistente de selección de audiencia (Autoridades, Docentes, Periodistas, Padres de Familia).
  - [x] Preconfiguración de territorio (Departamento/Municipio), Nivel y Sector de referencia.
  - [x] Banner contextual activo de audiencia en la cabecera.
  - [x] Botón en barra lateral para reabrir el modal de referencia en cualquier momento.
- [x] **Esquemas Tipados (`src/agent/schemas.py`):**
  - [x] Modelos Pydantic (`AgentIntent`, `AgentResponse`, `QueryCategory`).
  - [x] Categorización estricta: `DATA_QUERY`, `ANALYSIS_QUERY`, `OUT_OF_SCOPE`, `GREETING`.
- [x] **Cliente y Proveedor LLM (`src/agent/client.py`):**
  - [x] Integración de Groq Cloud (`groq/compound-mini`) con clave segura desde `.env`.
  - [x] Latencias de inferencia ultrabajas (< 400ms).
  - [x] Fallback determinista local para operación offline o sin API key.
- [x] **Herramientas Analíticas y Contexto (`src/agent/tools.py`):**
  - [x] Mapeo de intención a consultas DuckDB sobre los 4,298,887 microdatos (< 50ms).
  - [x] Inyección de hallazgos del dashboard (brechas rural/urbana, sector, niveles).
  - [x] Declaración transparente de variables disponibles para consultas fuera de alcance.
- [x] **Prompts del Sistema y Guardrails (`src/agent/prompts.py`):**
  - [x] Prompt de extracción semántica en JSON con normalización de sinónimos del INE.
  - [x] Prompt generador con **regla estricta de CERO ALUCINACIÓN**: prohibido inventar cifras.
- [x] **Orquestador Principal (`src/agent/engine.py`):**
  - [x] Flujo de 3 pasos: Extracción &rarr; Cálculo DuckDB &rarr; Generación guiada.
- [x] **Interfaz de Chat en Streamlit (`app.py` - Pestaña 4):**
  - [x] Chat interactivo en vivo con `st.chat_message` y `st.chat_input`.
  - [x] Historial de conversación persistente durante la sesión.
  - [x] Botones de preguntas sugeridas para demostración rápida ante el jurado.
  - [x] Badge de verificación: *"🛡️ Cifras calculadas con DuckDB | Latencia: X ms"*.
  - [x] Desplegable de auditoría técnica con el JSON estructurado y datos de DuckDB.
- [x] **Pruebas y Calidad:**
  - [x] 8 pruebas unitarias automatizadas (`tests/test_agent.py`).
  - [x] Total suite: 28/28 pruebas PASS en 6.46s.
  - [x] 100% código conforme con `ruff check` y `ruff format`.

---

### ⏳ Fase 5: Documentación Final, Videos y Preparación del Pitch
- [ ] Grabación Video 1: **Arquitectura del Proyecto** (máx. 3 minutos).
- [ ] Grabación Video 2: **Demostración de Funcionamiento** (máx. 3 minutos).
- [ ] Guion del Pitch de 5 minutos + preparación de ronda de preguntas (5 minutos).
- [ ] Auditoría final de reproducibilidad en limpio (`git clone` en máquina limpia).

---

## 📜 Bitácora de Commits Clave

| Commit | Fecha | Autor | Descripción del Avance |
|:---:|:---:|:---:|---|
| `3672675` | 2026-09-20 | chayand-wil | `feat(data)`: Integración de los 3 departamentos faltantes y reorganización en `Data/` |
| `bb6c032` | 2026-09-20 | chayand-wil | `Add: Ingesta y ETL`: Pipeline completo, suite pytest, parquet 2.32 MB y reporte oficial |
