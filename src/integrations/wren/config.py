"""Configuración de WrenAI sin efectos secundarios al importar."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class WrenConfig:
    enabled: bool
    executable: str
    project_dir: Path
    mdl_path: Path
    connection_file: Path
    timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> "WrenConfig":
        project = Path(os.getenv("WREN_PROJECT_DIR", "wren")).resolve()
        return cls(
            enabled=_enabled(os.getenv("ENABLE_WREN")),
            executable=os.getenv("WREN_EXECUTABLE", "wren"),
            project_dir=project,
            mdl_path=Path(os.getenv("WREN_MDL_PATH", str(project / "target" / "mdl.json"))).resolve(),
            connection_file=Path(
                os.getenv("WREN_CONNECTION_FILE", str(project / "connection_info.json"))
            ).resolve(),
            timeout_seconds=max(1, int(os.getenv("WREN_TIMEOUT_SECONDS", "30"))),
        )
