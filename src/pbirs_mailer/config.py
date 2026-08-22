"""Configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class ConfigurationError(ValueError):
    """Raised when the JSON configuration is invalid."""


@dataclass(frozen=True, slots=True)
class BrowserConfig:
    channel: str = "msedge"
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    page_timeout_seconds: float = 120
    frame_timeout_seconds: float = 60
    render_timeout_seconds: float = 60
    render_quiet_seconds: float = 2


@dataclass(frozen=True, slots=True)
class SmtpConfig:
    enabled: bool
    server: str
    port: int
    sender: str
    timeout_seconds: float = 30
    starttls: bool = False


@dataclass(frozen=True, slots=True)
class PageTarget:
    internal_name: str | None = None
    display_name: str | None = None


@dataclass(frozen=True, slots=True)
class Subscription:
    name: str
    url: str
    page: PageTarget
    recipients: tuple[str, ...]
    subject: str
    filename: str
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class PathsConfig:
    captures: Path
    logs: Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    browser: BrowserConfig
    smtp: SmtpConfig
    paths: PathsConfig
    subscriptions: tuple[Subscription, ...]


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{label} doit être un objet JSON.")
    return value


def _required_text(data: dict[str, Any], key: str, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{label}.{key} doit être une chaîne non vide.")
    return value.strip()


def _optional_text(data: dict[str, Any], key: str, label: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{label}.{key} doit être null ou une chaîne non vide.")
    return value.strip()


def _positive_number(data: dict[str, Any], key: str, default: float, label: str) -> float:
    value = data.get(key, default)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise ConfigurationError(f"{label}.{key} doit être un nombre strictement positif.")
    return float(value)


def _positive_int(data: dict[str, Any], key: str, default: int, label: str) -> int:
    value = data.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ConfigurationError(f"{label}.{key} doit être un entier strictement positif.")
    return value


def _boolean(data: dict[str, Any], key: str, default: bool, label: str) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ConfigurationError(f"{label}.{key} doit être un booléen.")
    return value


def _load_browser(data: dict[str, Any]) -> BrowserConfig:
    label = "browser"
    channel = data.get("channel", "msedge")
    if not isinstance(channel, str) or not channel.strip():
        raise ConfigurationError("browser.channel doit être une chaîne non vide.")

    return BrowserConfig(
        channel=channel.strip(),
        headless=_boolean(data, "headless", True, label),
        viewport_width=_positive_int(data, "viewport_width", 1920, label),
        viewport_height=_positive_int(data, "viewport_height", 1080, label),
        page_timeout_seconds=_positive_number(data, "page_timeout_seconds", 120, label),
        frame_timeout_seconds=_positive_number(data, "frame_timeout_seconds", 60, label),
        render_timeout_seconds=_positive_number(data, "render_timeout_seconds", 60, label),
        render_quiet_seconds=_positive_number(data, "render_quiet_seconds", 2, label),
    )


def _load_smtp(data: dict[str, Any]) -> SmtpConfig:
    label = "smtp"
    return SmtpConfig(
        enabled=_boolean(data, "enabled", False, label),
        server=_required_text(data, "server", label),
        port=_positive_int(data, "port", 25, label),
        sender=_required_text(data, "sender", label),
        timeout_seconds=_positive_number(data, "timeout_seconds", 30, label),
        starttls=_boolean(data, "starttls", False, label),
    )


def _load_subscription(data: dict[str, Any], index: int) -> Subscription:
    label = f"subscriptions[{index}]"
    page_data = _mapping(data.get("page", {}), f"{label}.page")
    internal_name = _optional_text(page_data, "internal_name", f"{label}.page")
    display_name = _optional_text(page_data, "display_name", f"{label}.page")

    recipients_value = data.get("recipients")
    if not isinstance(recipients_value, list) or not recipients_value:
        raise ConfigurationError(f"{label}.recipients doit être une liste non vide.")
    if not all(isinstance(item, str) and item.strip() for item in recipients_value):
        raise ConfigurationError(f"{label}.recipients contient une adresse invalide.")

    url = _required_text(data, "url", label)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigurationError(f"{label}.url doit être une URL HTTP(S) valide.")

    filename = _required_text(data, "filename", label)
    if Path(filename).name != filename or Path(filename).suffix.lower() != ".png":
        raise ConfigurationError(f"{label}.filename doit être un simple nom de fichier .png.")

    return Subscription(
        name=_required_text(data, "name", label),
        url=url,
        page=PageTarget(internal_name=internal_name, display_name=display_name),
        recipients=tuple(item.strip() for item in recipients_value),
        subject=_required_text(data, "subject", label),
        filename=filename,
        enabled=_boolean(data, "enabled", True, label),
    )


def load_config(path: Path) -> AppConfig:
    """Load and validate one V1 configuration file."""
    try:
        content = _read_config_text(path)
        raw = json.loads(content)
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Fichier de configuration introuvable : {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"JSON invalide dans {path} : ligne {exc.lineno}.") from exc

    root = _mapping(raw, "configuration")
    if root.get("version") != 1:
        raise ConfigurationError("configuration.version doit être égal à 1.")

    browser = _load_browser(_mapping(root.get("browser", {}), "browser"))
    smtp = _load_smtp(_mapping(root.get("smtp"), "smtp"))

    paths_data = _mapping(root.get("paths", {}), "paths")
    base_dir = path.resolve().parent
    captures = Path(paths_data.get("captures", "captures"))
    logs = Path(paths_data.get("logs", "logs"))
    if not captures.is_absolute():
        captures = base_dir / captures
    if not logs.is_absolute():
        logs = base_dir / logs

    subscriptions_data = root.get("subscriptions")
    if not isinstance(subscriptions_data, list) or not subscriptions_data:
        raise ConfigurationError("subscriptions doit être une liste non vide.")
    subscriptions = tuple(
        _load_subscription(_mapping(item, f"subscriptions[{index}]"), index)
        for index, item in enumerate(subscriptions_data)
    )

    names = [item.name.casefold() for item in subscriptions]
    if len(names) != len(set(names)):
        raise ConfigurationError("Chaque abonnement doit avoir un nom unique.")

    filenames = [item.filename.casefold() for item in subscriptions]
    if len(filenames) != len(set(filenames)):
        raise ConfigurationError("Chaque abonnement doit avoir un fichier de capture unique.")

    return AppConfig(
        browser=browser,
        smtp=smtp,
        paths=PathsConfig(captures=captures, logs=logs),
        subscriptions=subscriptions,
    )


def _read_config_text(path: Path) -> str:
    """Read JSON created by modern or legacy Windows text editors."""
    data = path.read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252")
