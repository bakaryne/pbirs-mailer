"""PBIRS Mailer application orchestration."""

from __future__ import annotations

import logging
from dataclasses import replace
from logging.handlers import RotatingFileHandler

from .capture import capture_subscription
from .config import AppConfig
from .mailer import build_message, send_message


def browser_launch_error_message(exc: Exception) -> str:
    """Return an actionable message for known browser startup failures."""
    details = str(exc).casefold()
    if "opening in existing browser session" in details or "profile is already in use" in details:
        return (
            "Microsoft Edge utilise déjà le profil imposé à Playwright. "
            "Fermez toutes les fenêtres et tous les processus Edge, puis réessayez."
        )
    return (
        "Impossible d'ouvrir Microsoft Edge avec Playwright. "
        "Vérifiez qu'Edge est installé, puis relancez setup.cmd."
    )


def configure_logging(config: AppConfig, verbose: bool = False) -> logging.Logger:
    """Configure console and rotating file logs."""
    config.paths.logs.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("pbirs_mailer")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    file_handler = RotatingFileHandler(
        config.paths.logs / "pbirs-mailer.log",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def select_subscriptions(config: AppConfig, requested_names: tuple[str, ...]) -> tuple:
    """Return enabled subscriptions optionally filtered by CLI name."""
    enabled = tuple(item for item in config.subscriptions if item.enabled)
    if not requested_names:
        return enabled
    requested = {name.casefold() for name in requested_names}
    selected = tuple(item for item in enabled if item.name.casefold() in requested)
    unknown = requested - {item.name.casefold() for item in selected}
    if unknown:
        raise ValueError(f"Abonnement(s) introuvable(s) : {', '.join(sorted(unknown))}")
    return selected


def run(
    config: AppConfig,
    *,
    dry_run: bool = False,
    no_send: bool = False,
    headed: bool = False,
    requested_names: tuple[str, ...] = (),
    verbose: bool = False,
) -> int:
    """Run selected subscriptions and return a process exit code."""
    logger = configure_logging(config, verbose=verbose)
    subscriptions = select_subscriptions(config, requested_names)
    if not subscriptions:
        logger.error("Aucun abonnement actif à traiter.")
        return 2

    effective_send = config.smtp.enabled and not no_send
    logger.info(
        "%d abonnement(s) sélectionné(s) | envoi SMTP : %s",
        len(subscriptions),
        "activé" if effective_send else "désactivé",
    )
    if dry_run:
        for subscription in subscriptions:
            logger.info("Configuration valide : %s", subscription.name)
        return 0

    config.paths.captures.mkdir(parents=True, exist_ok=True)
    browser_config = replace(config.browser, headless=False) if headed else config.browser

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright n'est pas installé. Exécutez : pip install -e .")
        return 2

    failures = 0
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(
                channel=browser_config.channel,
                headless=browser_config.headless,
            )
        except Exception as exc:
            logger.error(browser_launch_error_message(exc))
            logger.debug("Erreur de démarrage du navigateur : %s", exc, exc_info=True)
            return 2
        try:
            for subscription in subscriptions:
                try:
                    image = capture_subscription(
                        browser=browser,
                        subscription=subscription,
                        browser_config=browser_config,
                        capture_dir=config.paths.captures,
                        logger=logger,
                    )
                    if effective_send:
                        message = build_message(subscription, config.smtp, image)
                        send_message(message, config.smtp)
                        logger.info(
                            "Mail envoyé pour « %s » (%d destinataire(s)).",
                            subscription.name,
                            len(subscription.recipients),
                        )
                    else:
                        logger.info("Envoi ignoré pour « %s ».", subscription.name)
                    logger.info("OK : %s", subscription.name)
                except Exception:
                    failures += 1
                    logger.exception("ÉCHEC : %s", subscription.name)
        finally:
            browser.close()

    logger.info(
        "Traitement terminé : %d succès, %d échec(s).",
        len(subscriptions) - failures,
        failures,
    )
    return 1 if failures else 0
