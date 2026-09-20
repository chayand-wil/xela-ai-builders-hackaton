"""Pruebas del adaptador opcional WrenAI, sin requerir instalar el CLI."""

from pathlib import Path

import pytest

from src.integrations.wren import WrenClient, WrenConfig


def _config(tmp_path: Path, *, enabled: bool = True) -> WrenConfig:
    return WrenConfig(
        enabled=enabled,
        executable="wren-test",
        project_dir=tmp_path,
        mdl_path=tmp_path / "target" / "mdl.json",
        connection_file=tmp_path / "connection_info.json",
    )


def test_disabled_status_uses_direct_fallback(tmp_path: Path) -> None:
    status = WrenClient(_config(tmp_path, enabled=False)).status()
    assert not status.ready
    assert "DuckDB" in status.message


def test_query_rejects_mutation_before_subprocess(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config(tmp_path)
    config.mdl_path.parent.mkdir()
    config.mdl_path.write_text("{}", encoding="utf-8")
    config.connection_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("src.integrations.wren.client.shutil.which", lambda _name: "wren-test")
    client = WrenClient(config)
    with pytest.raises(ValueError, match="solo acepta consultas de lectura"):
        client.query("DELETE FROM inscripciones")
