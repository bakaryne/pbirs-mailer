import json
from pathlib import Path

import pytest

from pbirs_mailer.config import ConfigurationError
from pbirs_mailer.config_editor import (
    load_config_document,
    save_config_document,
    split_recipients,
    validate_config_document,
)


def valid_document() -> dict:
    return {
        "version": 1,
        "browser": {
            "channel": "msedge",
            "headless": True,
            "viewport_width": 1920,
            "viewport_height": 1080,
            "page_timeout_seconds": 120,
            "frame_timeout_seconds": 60,
            "render_timeout_seconds": 120,
            "render_quiet_seconds": 5,
            "render_stable_seconds": 3,
        },
        "smtp": {
            "enabled": False,
            "server": "smtp.example.org",
            "port": 25,
            "sender": "sender@example.org",
            "timeout_seconds": 30,
            "starttls": False,
        },
        "paths": {"captures": "captures", "logs": "logs"},
        "subscriptions": [
            {
                "name": "Report A",
                "enabled": True,
                "url": "http://pbirs.example.org/Reports/powerbi/report",
                "page": {"internal_name": None, "display_name": "Overview"},
                "recipients": ["recipient@example.org"],
                "subject": "Report A",
                "filename": "report-a.png",
            }
        ],
    }


def test_save_document_is_loadable_and_utf8(tmp_path: Path) -> None:
    path = tmp_path / "config.json"

    backup = save_config_document(path, valid_document())

    assert backup is None
    assert load_config_document(path)["subscriptions"][0]["name"] == "Report A"
    assert path.read_text(encoding="utf-8").endswith("\n")


def test_save_document_creates_backup_before_replacing(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    original = valid_document()
    save_config_document(path, original)
    updated = valid_document()
    updated["subscriptions"][0]["subject"] = "Updated subject"

    backup = save_config_document(path, updated)

    assert backup is not None
    assert json.loads(backup.read_text(encoding="utf-8")) == original
    assert load_config_document(path)["subscriptions"][0]["subject"] == "Updated subject"


def test_invalid_document_does_not_replace_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    original = valid_document()
    save_config_document(path, original)
    invalid = valid_document()
    invalid["subscriptions"][0]["filename"] = "../escape.png"

    with pytest.raises(ConfigurationError, match="simple nom de fichier"):
        save_config_document(path, invalid)

    assert load_config_document(path) == original
    assert not list(tmp_path.glob("*.backup-*.json"))


def test_validate_document_does_not_create_configuration(tmp_path: Path) -> None:
    validate_config_document(valid_document(), tmp_path)

    assert not (tmp_path / "config.json").exists()
    assert not list(tmp_path.glob("*.tmp"))


def test_split_recipients_accepts_lines_commas_and_semicolons() -> None:
    value = "one@example.org\ntwo@example.org, three@example.org;four@example.org"

    assert split_recipients(value) == [
        "one@example.org",
        "two@example.org",
        "three@example.org",
        "four@example.org",
    ]
