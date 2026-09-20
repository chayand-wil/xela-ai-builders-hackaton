# WrenAI — capa semántica opcional con respaldo DuckDB

Proyecto MDL mínimo sobre el Parquet de inscripciones (`educacion_formal_2024`).

- Conexión de ejemplo: `connection_info.example.json` (DuckDB / directorio Parquet).
- Modelo: `models/inscripciones/`
- Reglas de tasas y enums: `knowledge/rules/tasas.md`

El dashboard y el chat conservan `src.analytics.service` como fuente determinista de
indicadores. El adaptador `src/integrations/wren/` permite ejecutar consultas MDL de
solo lectura y reporta su estado en la barra lateral. Si Wren no está instalado,
compilado o conectado, la web continúa con DuckDB directo y lo informa claramente.

```bash
python -m pip install -e "C:\Users\pablo\Downloads\WrenAI-main\core\wren"
wren context validate --path wren
wren context build --path wren
```

Después copie `connection_info.example.json` como `connection_info.json`, ajuste la
ruta al directorio que contiene el Parquet y active:

```dotenv
ENABLE_WREN=true
WREN_PROJECT_DIR=wren
WREN_MDL_PATH=wren/target/mdl.json
WREN_CONNECTION_FILE=wren/connection_info.json
```

Prueba manual gobernada:

```powershell
wren query --sql 'SELECT departamento, COUNT(*) AS inscripciones FROM "inscripciones" GROUP BY departamento ORDER BY inscripciones DESC LIMIT 5' --mdl wren/target/mdl.json --connection-file wren/connection_info.json --output json
```

No se envía SQL escrito por usuarios directamente al CLI. El cliente aplica límite
de filas, prohíbe sentencias que no empiecen con `SELECT`/`WITH` y usa argumentos de
proceso sin shell.
