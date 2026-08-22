import json
from pathlib import Path

import pytest

from pbirs_mailer.config import ConfigurationError, load_config


def valid_config() -> dict:
    return {
        "version": 1,
        "browser": {},
        "smtp": {
            "enabled": False,
            "server": "smtp.example.org",
            "port": 25,
            "sender": "sender@example.org",
        },
        "paths": {"captures": "captures", "logs": "logs"},
        "subscriptions": [
            {
                "name": "Report A",
                "url": "http://pbirs/Reports/powerbi/report?rs:embed=true",
                "page": {"internal_name": None, "display_name": "Overview"},
                "recipients": ["recipient@example.org"],
                "subject": "Report A",
                "filename": "report-a.png",
            }
        ],
    }


def write_config(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_config_resolves_relative_paths(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path, valid_config()))

    assert config.paths.captures == tmp_path / "captures"
    assert config.paths.logs == tmp_path / "logs"
    assert config.subscriptions[0].page.display_name == "Overview"


def test_load_config_rejects_path_traversal_filename(tmp_path: Path) -> None:
    data = valid_config()
    data["subscriptions"][0]["filename"] = "../capture.png"

    with pytest.raises(ConfigurationError, match="simple nom de fichier"):
        load_config(write_config(tmp_path, data))


def test_load_config_rejects_duplicate_subscription_names(tmp_path: Path) -> None:
    data = valid_config()
    second = dict(data["subscriptions"][0])
    second["name"] = "report a"
    second["filename"] = "report-b.png"
    data["subscriptions"].append(second)

    with pytest.raises(ConfigurationError, match="nom unique"):
        load_config(write_config(tmp_path, data))


@pytest.mark.parametrize("encoding", ["utf-8-sig", "cp1252"])
def test_load_config_accepts_common_windows_encodings(
    tmp_path: Path,
    encoding: str,
) -> None:
    data = valid_config()
    data["subscriptions"][0]["page"]["display_name"] = "Vue générale"
    path = tmp_path / "config.json"
    path.write_bytes(json.dumps(data, ensure_ascii=False).encode(encoding))

    config = load_config(path)

    assert config.subscriptions[0].page.display_name == "Vue générale"
