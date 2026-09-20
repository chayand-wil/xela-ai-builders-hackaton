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
$env:PYTHONUTF8="1"
wren context build --path wren
```

El repositorio ya incluye `connection_info.json` para el Parquet local. Wren usa
DataFusion como conector de archivos y mantiene DuckDB como motor analítico de
respaldo de la aplicación. Para otra ubicación, ajuste `source` y active:

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

En Windows se debe compilar con `PYTHONUTF8=1`; de lo contrario, las tildes del
modelo pueden quedar en Windows-1252 y Wren rechazará el MDL. La aplicación también
valida que `mdl.json` sea UTF-8 antes de anunciar que Wren está listo.

No se envía SQL escrito por usuarios directamente al CLI. El cliente aplica límite
de filas, prohíbe sentencias que no empiecen con `SELECT`/`WITH` y usa argumentos de
proceso sin shell.
