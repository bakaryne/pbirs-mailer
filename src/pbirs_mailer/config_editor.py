"""Safe reading, validation, and writing helpers for the Configurator."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import ConfigurationError, _read_config_text, load_config


def load_config_document(path: Path) -> dict[str, Any]:
    """Load the editable JSON document and validate it with the V1 engine."""
    try:
        document = json.loads(_read_config_text(path))
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Fichier de configuration introuvable : {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"JSON invalide dans {path} : ligne {exc.lineno}.") from exc

    if not isinstance(document, dict):
        raise ConfigurationError("configuration doit être un objet JSON.")

    load_config(path)
    return document


def validate_config_document(document: dict[str, Any], base_dir: Path) -> None:
    """Validate an in-memory document without changing the real configuration."""
    base_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = _write_temporary_document(document, base_dir, "config-validation")
    try:
        load_config(temporary_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def save_config_document(path: Path, document: dict[str, Any]) -> Path | None:
    """Validate and atomically save a document, backing up an existing file."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = _write_temporary_document(document, path.parent, path.name)
    backup_path: Path | None = None

    try:
        load_config(temporary_path)
        if path.exists():
            backup_path = _next_backup_path(path)
            shutil.copy2(path, backup_path)
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return backup_path


def split_recipients(value: str) -> list[str]:
    """Accept one address per line, or comma/semicolon-separated addresses."""
    return [item.strip() for item in re.split(r"[;,\n]+", value) if item.strip()]


def _write_temporary_document(
    document: dict[str, Any],
    directory: Path,
    prefix: str,
) -> Path:
    if not isinstance(document, dict):
        raise ConfigurationError("configuration doit être un objet JSON.")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{prefix}.",
        suffix=".tmp",
        dir=directory,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(document, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return temporary_path


def _next_backup_path(path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = path.with_name(f"{path.stem}.backup-{timestamp}{path.suffix}")
    counter = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}.backup-{timestamp}-{counter}{path.suffix}")
        counter += 1
    return candidate
