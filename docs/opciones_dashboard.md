# Opciones para mostrar el dashboard

Premisa: la **ingesta y el ETL ya existen**. El dashboard solo consume datos procesados (Parquet + capa analítica, p. ej. DuckDB) y **no recalcula códigos**. Las cifras salen de indicadores compartidos; el dashboard las muestra y las explica.

El reto pide: etiquetas en palabras, gráficas claras, **análisis escrito**, público no técnico, y al menos **vista general + una desagregación** (departamento / nivel). El agente más adelante debe poder hablar de *ese* análisis.

---

## 1. Cómo se “muestra” (plataforma)

| Opción | Qué es | Ventaja | Costo / riesgo | Encaje hackatón |
|---|---|---|---|---|
| **A. Streamlit + Plotly** | App Python: `streamlit run app.py` | Rápido, un solo lenguaje, filtros y texto al lado de la gráfica. Stack ya acordado. | Menos “app de producto”; layout rígido. | **Recomendada para MVP** |
| **B. Dash (Plotly)** | App Python más estructurada | Control fino de layout. | Más código, más lento de iterar. | Solo si Streamlit se queda corto |
| **C. Panel / Gradio** | Similar a Streamlit | Gradio encaja bien con chat. | Ecosistema más chico; duplicas trabajo si ya hay Streamlit. | No priorizar |
| **D. Next.js / React + API** | Front JS, backend Python | UI más pulida, fácil de demo. | Dos stacks, más tiempo, más que explicar en el pitch. | Fuera de alcance salvo sobra tiempo |
| **E. Notebook (Jupyter / Marimo)** | Informe interactivo | Muy rápido de prototipar. | No se siente producto; peor para pitch y agente. | Solo para explorar, no entrega |
| **F. HTML estático (Quarto / Plotly export)** | Páginas fijas con cifras precalculadas | Cero servidor, 100% reproducible. | Poco filtro; el agente no “ve” la misma UI. | Complemento, no dashboard vivo |
| **G. Metabase / Superset / Evidence** | BI sobre SQL | Filtros y mapas listos. | Caja negra, peor para “comprensión de tu solución”. | Evitar |

**Decisión sugerida:** **A**. El resto de este archivo asume Streamlit + Plotly sobre indicadores ya calculados.

Cómo se ve en la práctica:

1. Usuario abre la app.
2. Elige filtros (departamento, nivel, etc.).
3. DuckDB / `src/analytics` devuelve agregados pequeños (no 4.3 M de filas al browser).
4. Plotly dibuja; un bloque de texto explica qué significa.

---

## 2. Arquitectura de pantallas (qué páginas hay)

El mínimo del reto: **nacional + una desagregación**. Las opciones siguientes se pueden combinar.

| ID | Vista | Qué muestra | Prioridad |
|---|---|---|---|
| **V1. Portada / panorama nacional** | KPIs + 2–3 gráficas + un párrafo de lectura | Matrícula, promovidos, no promovidos, retirados. Cumple “vista general”. | **MVP** |
| **V2. Territorio** | Departamento → municipio | Ranking, mapa o barras. Cumple “desagregación”. | **MVP** |
| **V3. Niveles y grados** | Preprimaria → diversificado; grado *dentro de* nivel | Dónde se pierde más gente. | **MVP** si hay tiempo; si no, un gráfico en V1 |
| **V4. Brechas** | Urbano/rural, público/privado, sexo, pueblo | Contrastes que el dataset sí permite. | Alta (periodismo / política) |
| **V5. Resultado del ciclo** | Promovido / no promovido / retirado (+ vigente, ignorado aparte) | Núcleo del “cómo cerró el año”. | Incluir en V1 |
| **V6. Establecimientos** | Top de códigos / recuentos por código | Fácil de malinterpretar (un centro = varios códigos). | Baja; si se hace, con disclaimer |
| **V7. Chat junto al dashboard** | Misma página, sidebar o pestaña | El agente explica *estas* gráficas. | Fase agente; dejar hueco |
| **V8. Informe imprimible** | PDF o markdown generado | Útil para municipalidad. | Fuera del MVP |

**Navegación posible en Streamlit:**

- **Tabs:** `Panorama` \| `Territorio` \| `Niveles` \| `Preguntar` — simple para el pitch.
- **Multipage:** `pages/1_Panorama.py`, `pages/2_Territorio.py` — más limpio si crece.
- **Una sola página con scroll** — peor para demo (se pierde el juez).

**Recomendada:** tabs o 2 páginas (`Panorama` + `Territorio`), filtros globales en el sidebar.

---

## 3. Qué poner en cada gráfica (contenido)

Todas las cifras deben cuadrar con las de validación (total **4,298,887**, Guatemala **17** municipios, etc.).

### 3.1 Indicadores (tarjetas / KPIs)

Posibilidades (no hace falta las 10):

- Total de **inscripciones** (no “estudiantes únicos”).
- % **Promovido**, % **No promovido**, % **Retirado** (retiro = códigos 3+4; vigente e ignorado fuera del denominador, como en el plan).
- % **Rural** vs urbana.
- % **Público**.
- Nivel con más matrícula (casi siempre Primaria).
- Departamento con peor promoción o mayor retiro (con n visible).

Cada KPI: **número + etiqueta en español + denominador** (“de cada 100 inscripciones con resultado conocido…”).

### 3.2 Tipos de visualización

| Gráfica | Pregunta que responde | Cuándo usarla | Cuidado |
|---|---|---|---|
| **Barras horizontales** | ¿Quién tiene más / peor? | Rankings de 22 departamentos | Ordenar por métrica, no alfabético |
| **Barras apiladas 100%** | ¿Cómo se reparte el resultado? | Promovido / no / retiro por nivel | No mezclar vigente en el stack de tasas |
| **Barras agrupadas** | ¿Urbano vs rural? ¿Sexo? | Brechas | Misma escala, mismos filtros |
| **Treemap** | ¿Dónde está el volumen? | Matrícula por nivel o sector | Volumen ≠ “peor resultado” |
| **Mapa coroplético** | ¿Dónde geográficamente? | Departamentos (fácil) o municipios (más trabajo) | Sin geojson, un mapa feo resta; barras bastan |
| **Lollipop / dot plot** | Comparar tasas | 22 departamentos | Mejor que pie |
| **Tabla ordenable** | Cifras exactas | Municipios de un depto | Complemento, no reemplazo de gráfica |
| **Heatmap** | Nivel × departamento | Si hay espacio | Explicar la escala |
| **Pie / donut** | Composición | Máximo **uno** (sexo o sector) | Evitar pies de 22 slices |
| **Sankey** | Flujo | No hay trayectoria de alumno | **No usar** (el dato no lo permite) |
| **Línea de tiempo** | Evolución | Solo hay 2024 | **No usar** |

**Set mínimo recomendado (4 gráficas + texto):**

1. Donut o barras: composición de **resultado nacional**.
2. Barras: **matrícula por nivel**.
3. Barras horizontales: **tasa de retiro o no promoción por departamento**.
4. Barras o tabla: **desagregación municipal** al elegir un departamento.

---

## 4. Cómo mostrar el análisis escrito (el requisito que más se olvida)

No basta la gráfica. Opciones de narrativa:

| Modo | Cómo | Ventaja | Riesgo |
|---|---|---|---|
| **N1. Plantillas** | Texto con huecos: “En {depto}, el {nivel} tiene {x}% de retiro, frente a {y}% nacional.” | Cifras siempre reales; fácil de explicar a jueces. | Suena rígido |
| **N2. IA sobre agregados** | El LLM recibe *solo* el JSON de la vista filtrada y redacta 3–5 oraciones | Tono más humano | Puede alucinar si le das libertad; hay que anclar a números |
| **N3. Hallazgos fijos** | 4–5 insights precalculados en ETL (p. ej. “primaria concentra 56%”) | Perfecto para pitch | No reacciona a filtros |
| **N4. Híbrido** | Plantilla + 1 párrafo de IA + insights fijos en portada | Cumple “explicar” y alimenta al agente | Un poco más de trabajo |

**Recomendado: N4.** El agente debe reutilizar los mismos textos/insights para “¿por qué marcas ese nivel como crítico?”.

Reglas de redacción para cualquiera de los modos:

- Decir **inscripciones**, no “niños únicos”.
- Mostrar **n** junto al %.
- Si el filtro deja pocos casos, decirlo.
- No afirmar causas (pobreza, COVID, docentes): el dataset no las tiene.
- Tratar `Ignorado` de forma explícita.

---

## 5. Interacción (filtros y estados)

**Filtros globales (sidebar), todos opcionales:**

- Departamento → Municipio (cascada)
- Nivel (y grado solo si hay nivel)
- Sector, Área, Sexo, Pueblo, Jornada, Resultado

**Estados de UI (obligatorios para no verse roto):**

- Cargando Parquet / primera query
- Sin coincidencias con los filtros
- Error de archivo / ruta
- Advertencia: “conteo de códigos ≠ escuelas”

**Extras posibles:**

- Botón “Restablecer filtros”
- “Comparar con el país” (línea de referencia en barras)
- Descarga CSV del agregado visible (no del microdato completo)
- Modo “explicar esta gráfica” → abre el chat con contexto de la vista

---

## 6. Cómo se ve el layout (wireframe textual)

```text
┌─────────────────────────────────────────────────────────────┐
│ EduGuate IA · Educación Formal 2024                         │
│ Filtros: [Depto ▾] [Nivel ▾] [Sector ▾]   [Restablecer]     │
├──────────────┬──────────────────────────────────────────────┤
│ Inscripciones│  Promovido     No promovido     Retiro       │
│ 4,298,887    │  85.2%         9.2%             5.5%         │
├──────────────┴──────────────────────────────────────────────┤
│ [Panorama] [Territorio] [Preguntar]                         │
│                                                             │
│  ┌─────────────┐  ┌──────────────────────────────────────┐  │
│  │ Resultado   │  │ Matrícula por nivel                  │  │
│  │ (barras)    │  │                                      │  │
│  └─────────────┘  └──────────────────────────────────────┘  │
│                                                             │
│  Lectura: “La mayoría de inscripciones está en Primaria     │
│  (56%). El retiro se concentra en…”                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Tres paquetes para decidir rápido

### Paquete S (mínimo que cumple el reto)

- Streamlit, una página, dos tabs.
- 4 KPIs + 3 gráficas + 1 ranking departamental.
- Texto 100% plantilla.
- Sin mapa.

### Paquete M (recomendado)

- Tabs Panorama + Territorio.
- 4 gráficas Plotly + tabla municipal.
- Narrativa híbrida (plantilla + párrafo IA).
- Línea de referencia nacional.
- Placeholder de chat.

### Paquete L (si sobra tiempo)

- Mapa departamental.
- Vista de brechas (área, sector, pueblo).
- Chat embebido con “explica esta vista”.
- Exportar CSV del agregado.

---

## 8. Lo que no hay que mostrar (aunque se pueda)

- Evolución 2020–2024 (no hay otros años).
- Trayectoria de un estudiante (no hay ID).
- Notas, edad, discapacidad, docentes, infraestructura.
- “Número de escuelas” = `nunique(codigo_establecimiento)`.
- Municipios desde `Depto_mupio`.
- Modalidad bilingüe (columna inexistente).
- SQL libre tecleado por el usuario sobre el Parquet crudo.

---

## 9. Criterio de elección (para el pitch)

Elegir la opción que se pueda **explicar en dos minutos**: de dónde sale cada cifra, por qué esas cuatro gráficas, y por qué el texto no inventa.

Orden sugerido de implementación:

1. KPIs nacionales contra las cifras de validación.
2. Gráfica de resultado + gráfica de nivel (con texto).
3. Tab territorio (departamento → municipio).
4. Filtros que recomputan las mismas funciones analíticas.
5. Hueco para el agente (misma capa de indicadores).
