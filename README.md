# EduGuate IA — Sistema Analítico Inteligente de Educación en Guatemala

> Herramienta analítica y conversacional con IA para democratizar los 4.29 millones de microdatos de la Educación Formal en Guatemala (INE 2024).

---

## 🚀 Instrucciones para Correr el Proyecto

Sigue estos pasos para instalar, configurar y ejecutar el proyecto localmente:

### 1. Requisitos previos
- **Python 3.11 o 3.12**
- **Git**

### 2. Clonar el repositorio
```bash
git clone git@github.com:chayand-wil/xela-ai-builders-hackaton.git
cd xela-ai-builders-hackaton
```

### 3. Crear y activar entorno virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
```
*(En Windows PowerShell: `.venv\Scripts\Activate.ps1`)*

### 4. Instalar dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 5. Configurar API Key de Groq (para el Agente Conversacional)
Crea un archivo `.env` en la raíz del proyecto con tu clave de API de Groq:
```bash
echo "GROQ_API_KEY=tu_api_key_aqui" > .env
```
*(Nota: Si no se configura API key, el agente funcionará en modo determinista local para consultas de datos).*

### 6. Procesar los datos (Ingesta & ETL)
Si necesitas reconstruir el archivo consolidado `Data/processed/educacion_formal_2024.parquet` a partir de los archivos Excel originales:
```bash
python scripts/process_data.py
```
*(Tarda aproximadamente 15-20 segundos y valida contra el 100% del Ground Truth oficial del INE).*

### 7. Iniciar el Dashboard Interactivo y Agente
```bash
streamlit run app.py
```
Abre en tu navegador `http://localhost:8501`. La aplicación incluye:
- **Modal de Bienvenida:** Selección de perfil/referencia territorial o exploración libre.
- **Pestaña 1 (Panorama Nacional):** Matrícula total, tasas clave, gráficos donut y distribución por nivel educativo.
- **Pestaña 2 (Exploración Territorial):** Ranking de 22 departamentos y drill-down a los 340 municipios.
- **Pestaña 3 (Brechas y Desigualdades):** Comparativas Rural/Urbana, Público/Privado, Sexo y Pueblos Originarios con análisis interpretativo escrito obligatorio.
- **Pestaña 4 (Preguntar a los Datos):** Chat interactivo con el Agente Conversacional impulsado por Groq y DuckDB con arquitectura anti-alucinación.

### 8. Ejecutar Pruebas Unitarias
```bash
pytest tests/ -v
```
*(28/28 pruebas unitarias automatizadas pasan en menos de 7 segundos).*

---

## 📚 Enlaces a la Documentación del Proyecto

Toda la documentación técnica, metodológica y operativa se encuentra organizada en el directorio `docs/`:

- 🏛️ **[Arquitectura del Sistema](docs/architecture.md):** Diagrama de componentes, pipeline ETL, motor analítico DuckDB y diseño anti-alucinación del LLM.
- 📖 **[Diccionario de Datos](docs/data_dictionary.md):** Especificación formal de las 17 columnas de salida, tipos de datos y catálogos de decodificación.
- 💡 **[Registro de Decisiones Técnicas (ADR)](docs/decisions.md):** Bitácora de decisiones clave (Polars/Calamine, Parquet Snappy, DuckDB en memoria, Groq JSON mode).
- 📊 **[Opciones de Dashboard y Visualizaciones](docs/opciones_dashboard.md):** Catálogo de gráficos propuestos, diseño UX/UI y directrices de accesibilidad.
- 📈 **[Control de Avances y Tracking](docs/TRACKING.md):** Matriz de progreso detallada por cada una de las fases del hackatón (90% completado).
- 📋 **[Enunciado Oficial del Hackatón](docs/hackaton.md):** Requisitos, reglas, criterios de evaluación y cifras de control oficiales del INE.
- 🗺️ **[Plan de Acción Multi-Agente](docs/PLAN_ACCION_MULTIPLES_AGENTES_EDUGUATE_IA.md):** Metodología de coordinación y roles para el desarrollo ágil del proyecto.
