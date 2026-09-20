"""Cliente de proceso para el CLI WrenAI.

Solo acepta SQL de lectura y pasa argumentos como lista (sin shell). La capa web no
envía texto del usuario directamente a este método.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from src.integrations.wren.config import WrenConfig
from src.integrations.wren.models import WrenResult, WrenStatus


class WrenClient:
    def __init__(self, config: WrenConfig | None = None) -> None:
        self.config = config or WrenConfig.from_env()

    def status(self) -> WrenStatus:
        if not self.config.enabled:
            return WrenStatus(False, False, False, "WrenAI desactivado; DuckDB directo está activo.")
        if shutil.which(self.config.executable) is None and not Path(self.config.executable).is_file():
            return WrenStatus(True, False, False, "No se encontró el ejecutable de WrenAI.")
        missing = [path.name for path in (self.config.mdl_path, self.config.connection_file) if not path.is_file()]
        if missing:
            return WrenStatus(True, True, False, "Falta preparar: " + ", ".join(missing))
        try:
            self.config.mdl_path.read_text(encoding="utf-8")
            connection = json.loads(self.config.connection_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return WrenStatus(True, True, False, f"La configuración de WrenAI no es válida: {exc}")
        if connection.get("datasource") not in {"datafusion", "duckdb"}:
            return WrenStatus(True, True, False, "La conexión local de WrenAI no tiene un datasource compatible.")
        return WrenStatus(True, True, True, "WrenAI está listo para consultas gobernadas.")

    def smoke_test(self) -> int:
        result = self.query('SELECT COUNT(*) AS total FROM "inscripciones"', limit=1)
        if not result.rows or "total" not in result.rows[0]:
            raise RuntimeError("WrenAI respondió, pero no devolvió el conteo esperado.")
        return int(result.rows[0]["total"])

    def query(self, sql: str, *, limit: int = 500) -> WrenResult:
        status = self.status()
        if not status.ready:
            raise RuntimeError(status.message)
        normalized = sql.lstrip().lower()
        if not (normalized.startswith("select") or normalized.startswith("with")):
            raise ValueError("WrenAI solo acepta consultas de lectura en esta aplicación.")
        completed = subprocess.run(
            [
                self.config.executable,
                "query",
                "--sql",
                sql,
                "--mdl",
                str(self.config.mdl_path),
                "--connection-file",
                str(self.config.connection_file),
                "--limit",
                str(max(1, min(int(limit), 1000))),
                "--output",
                "json",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            timeout=self.config.timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            raise RuntimeError(f"WrenAI no pudo ejecutar la consulta: {detail}")
        rows = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
        return WrenResult(rows=rows)
