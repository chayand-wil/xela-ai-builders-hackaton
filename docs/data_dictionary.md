# Diccionario de Datos — Educación Formal 2024 (EduGuate IA)

## 1. Descripción General

El dataset procesado corresponde al censo administrativo de **Educación Formal 2024** publicado por el Instituto Nacional de Estadística (INE) de Guatemala. Cada fila representa una inscripción individual durante el ciclo escolar 2024.

- **Total de registros procesados:** `4,298,887`
- **Departamentos:** `22`
- **Municipios con datos:** `340`
- **Formato optimizado:** Apache Parquet comprimido con Zstandard (`zstd`)
- **Ubicación:** `data/processed/educacion_formal_2024.parquet`
- **Muestra representativa:** `data/samples/educacion_formal_sample.parquet` (10,000 registros)

---

## 2. Esquema de Datos Procesado (17 Columnas)

| Campo | Tipo | Origen / Transformación | Descripción y Catálogos |
|---|:---:|---|---|
| `anio` | `Int16` | `Año` | Ciclo escolar (siempre `2024`). |
| `codigo_establecimiento` | `String` | `CodEstablecimiento` normalizado | Formato `DD-MM-NNNN-SS`. Si el prefijo original era `00-`, fue normalizado a `01-`. |
| `departamento_codigo` | `Int8` | `Departamento_F` | Código numérico del departamento (`1` a `22`). |
| `departamento` | `String` | Catálogo de Departamentos | Nombre oficial del departamento (ej: `Guatemala`, `Quetzaltenango`). |
| `municipio_codigo` | `String` | Derivado de `CodEstablecimiento` | Código oficial de 4 dígitos (`0101` a `2217`). Si el código original empezaba con `00-`, se asignó a `0101`. |
| `municipio` | `String` | Catálogo de Municipios | Nombre oficial del municipio (ej: `Guatemala`, `Mixco`, `Salcajá`). |
| `sector` | `String` | `Sector` decodificado | `Público`, `Privado`, `Municipal`, `Cooperativa`. |
| `area` | `String` | `Área` decodificado | `Urbana`, `Rural`, `Ignorado`. |
| `sexo` | `String` | `Sexo` decodificado | `Hombre`, `Mujer`, `Ignorado`. |
| `grado` | `Int8` | `Grado` | Grado escolar cursado (debe interpretarse en conjunto con `nivel`). |
| `nivel` | `String` | `Nivel` decodificado | `Preprimaria`, `Primaria`, `Básico`, `Diversificado`, `Primaria de adultos`, `Ignorado`. |
| `pueblo_pertenencia` | `String` | `Pueblo_Per` decodificado | `Maya`, `Garífuna`, `Xinka`, `Afrodescendiente/Creole/Afromestizo`, `Ladino/Mestizo`, `Extranjero`, `Ignorado`. |
| `plan_estudios` | `String` | `Plan_Est` decodificado | `Diario`, `Fin de semana`, `Virtual a distancia`, `Semipresencial`, `Mixto`. |
| `jornada` | `String` | `Jornada_Est` decodificado | `Matutina`, `Vespertina`, `Nocturna`, `Doble`, `Intermedia`, `Ignorado`. |
| `resultado` | `String` | `Resultado_F` decodificado | `Promovido`, `Vigente`, `Retirado`, `Retirado definitivo`, `No promovido`, `Ignorado`. |
| `repitente` | `String` | `Repitente` decodificado | `Sí`, `No`, `Ignorado`. |
| `graduando` | `String` | `Graduando` decodificado | `Sí es graduando`, `No es graduando`, `Ignorado`. |

---

## 3. Decisiones de Limpieza y Reglas de Negocio

1. **Normalización del prefijo `00-`:**
   - En el archivo original `guatemala-2024.xlsx`, 309,919 registros presentaban el prefijo histórico `00-` (distrito central por zonas).
   - Todos corresponden al municipio de Guatemala Capital (`0101`). Se asignó formalmente `municipio_codigo = "0101"` y se normalizó el código del establecimiento a `01-`. Esto previene que se generen 39 municipios ficticios en lugar de los 17 oficiales.
2. **Derivación de Municipios:**
   - La columna original `Depto_mupio` no varía dentro de los archivos y no es confiable. La desagregación municipal se realiza estrictamente a partir de los segmentos territoriales del código de establecimiento.
3. **Preservación del Código `9`:**
   - Los registros con código `9` corresponden a la categoría oficial `"Ignorado"` y no son valores nulos ni celdas vacías.
4. **Omisión de `Modalidad`:**
   - Aunque figura en el documento descriptivo del INE, la variable no existe en los microdatos y fue omitida del esquema procesado.
5. **Hojas en libros Excel:**
   - En `solola_2024.xlsx`, se descartan automáticamente las hojas vacías (`Sheet2`, `Sheet3`) y se procesa únicamente `Sheet1`.

---

## 4. Cifras Oficiales de Control (Ground Truth)

| Métrica | Valor Esperado |
|---|---|
| Registros totales | `4,298,887` |
| Municipios en departamento de Guatemala | `17` |
| Municipios con datos a nivel nacional | `340` |
| Sector Público / Privado / Cooperativa / Municipal | `74.7%` / `20.9%` / `4.0%` / `0.3%` |
| Área Rural / Urbana | `61.4%` / `38.6%` |
| Sexo Hombre / Mujer | `50.7%` / `49.3%` |
| Nivel Primaria / Básico / Preprimaria / Diversificado | `56.4%` / `17.8%` / `17.1%` / `8.5%` |
| Resultado Promovido / No promovido / Retirado | `85.2%` / `9.2%` / `5.5%` |
