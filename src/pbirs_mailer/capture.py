"""Playwright-based PBIRS capture workflow."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .config import BrowserConfig, Subscription


class CaptureError(RuntimeError):
    """Raised when a PBIRS page cannot be captured."""


def normalize_text(value: str) -> str:
    """Normalize a displayed navigation label for comparisons."""
    return " ".join(value.split()).casefold()


def build_report_url(url: str, internal_page_name: str | None) -> str:
    """Add the Power BI internal page name while preserving existing parameters."""
    if not internal_page_name:
        return url
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["pageName"] = internal_page_name
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query, safe=":"), parts.fragment)
    )


def find_powerbi_frame(page: Any, timeout_seconds: float) -> Any:
    """Wait until the embedded Power BI frame is present."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            frame_url = frame.url.casefold()
            if "/powerbi/" in frame_url or "/powerbi?" in frame_url:
                return frame
        page.wait_for_timeout(250)
    raise CaptureError("Impossible de trouver la frame Power BI.")


def wait_for_powerbi_render(
    page: Any,
    action: Callable[[], Any],
    timeout_seconds: float,
    quiet_seconds: float,
    logger: logging.Logger,
) -> int:
    """Run an action, then wait until querydata traffic becomes quiet."""
    last_querydata: float | None = None
    query_count = 0

    def on_response(response: Any) -> None:
        nonlocal last_querydata, query_count
        if "/querydata" in response.url.casefold():
            query_count += 1
            last_querydata = time.monotonic()

    page.on("response", on_response)
    started = time.monotonic()
    try:
        action()
        while time.monotonic() - started < timeout_seconds:
            page.wait_for_timeout(250)
            if last_querydata is not None and time.monotonic() - last_querydata >= quiet_seconds:
                logger.info("Rendu stabilisé (%d requête(s) querydata).", query_count)
                return query_count
    finally:
        page.remove_listener("response", on_response)

    logger.warning("Délai de rendu atteint (%d requête(s) querydata détectée(s)).", query_count)
    return query_count


def _candidate_values(locator: Any) -> tuple[str, ...]:
    values: list[str] = []
    with suppress(Exception):  # The DOM can be replaced while Power BI renders.
        values.append(locator.inner_text(timeout=1_000) or "")
    for attribute in ("aria-label", "title"):
        with suppress(Exception):
            values.append(locator.get_attribute(attribute, timeout=1_000) or "")
    return tuple(values)


def _matches_label(locator: Any, target: str) -> bool:
    for value in _candidate_values(locator):
        normalized = normalize_text(value)
        if normalized == target or target in normalized:
            return True
    return False


def navigate_by_label(
    frame: Any,
    page: Any,
    display_name: str,
    browser_config: BrowserConfig,
    logger: logging.Logger,
) -> str:
    """Navigate using accessible PBIRS/Power BI tab, button or link metadata."""
    target = normalize_text(display_name)
    selectors = ('[role="tab"]', '[role="button"]', '[role="link"]')
    deadline = time.monotonic() + browser_config.frame_timeout_seconds

    while time.monotonic() < deadline:
        for selector in selectors:
            candidates = frame.locator(selector)
            try:
                count = candidates.count()
            except Exception:
                continue
            for index in range(count):
                candidate = candidates.nth(index)
                try:
                    if not candidate.is_visible() or not _matches_label(candidate, target):
                        continue
                    wait_for_powerbi_render(
                        page=page,
                        action=lambda item=candidate: item.click(timeout=10_000),
                        timeout_seconds=browser_config.render_timeout_seconds,
                        quiet_seconds=browser_config.render_quiet_seconds,
                        logger=logger,
                    )
                    logger.info("Navigation par libellé réussie : %s", display_name)
                    return selector
                except Exception as exc:
                    logger.debug("Candidat de navigation inutilisable : %s", exc)
        page.wait_for_timeout(500)

    raise CaptureError(
        f"Impossible de naviguer vers « {display_name} ». "
        "Renseignez si possible page.internal_name dans config.json."
    )


def capture_subscription(
    browser: Any,
    subscription: Subscription,
    browser_config: BrowserConfig,
    capture_dir: Path,
    logger: logging.Logger,
) -> Path:
    """Open one PBIRS report, navigate and create a PNG capture."""
    context = browser.new_context(
        viewport={
            "width": browser_config.viewport_width,
            "height": browser_config.viewport_height,
        }
    )
    page = context.new_page()
    output = capture_dir / subscription.filename
    error_output = capture_dir / f"{Path(subscription.filename).stem}-error.png"
    report_url = build_report_url(subscription.url, subscription.page.internal_name)

    try:
        logger.info("Ouverture du rapport « %s ».", subscription.name)
        wait_for_powerbi_render(
            page=page,
            action=lambda: page.goto(
                report_url,
                wait_until="domcontentloaded",
                timeout=browser_config.page_timeout_seconds * 1_000,
            ),
            timeout_seconds=browser_config.render_timeout_seconds,
            quiet_seconds=browser_config.render_quiet_seconds,
            logger=logger,
        )

        frame = find_powerbi_frame(page, browser_config.frame_timeout_seconds)
        frame.locator('[data-testid="exploration-container"]').wait_for(
            state="visible",
            timeout=browser_config.frame_timeout_seconds * 1_000,
        )
        logger.info("Contenu Power BI chargé.")

        if not subscription.page.internal_name and subscription.page.display_name:
            navigate_by_label(
                frame=frame,
                page=page,
                display_name=subscription.page.display_name,
                browser_config=browser_config,
                logger=logger,
            )

        page.wait_for_timeout(1_000)
        page.screenshot(path=str(output), full_page=True)
        logger.info("Capture créée : %s", output.name)
        return output
    except Exception as exc:
        try:
            page.screenshot(path=str(error_output), full_page=True)
            logger.error("Capture de diagnostic créée : %s", error_output.name)
        except Exception:
            logger.debug("La capture de diagnostic n'a pas pu être créée.")
        if isinstance(exc, CaptureError):
            raise
        raise CaptureError(str(exc)) from exc
    finally:
        context.close()
