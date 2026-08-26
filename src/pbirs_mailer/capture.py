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

POWERBI_ROOT_SELECTOR = '[data-testid="exploration-container"]'
POWERBI_LOADING_SELECTOR = ", ".join(
    (
        "spinner",
        '[aria-busy="true"]',
        '[class*="spinner" i]',
        '[role="progressbar"][aria-label*="loading" i]',
        '[role="progressbar"][title*="loading" i]',
    )
)


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
    stable_seconds: float,
    frame_timeout_seconds: float,
    logger: logging.Logger,
    frame: Any | None = None,
) -> tuple[Any, int]:
    """Run an action and wait for network, spinner and visual DOM stability."""
    last_querydata_activity = time.monotonic()
    query_count = 0
    pending_querydata: set[int] = set()

    def is_querydata(request: Any) -> bool:
        return "/querydata" in request.url.casefold()

    def on_request(request: Any) -> None:
        nonlocal last_querydata_activity, query_count
        if is_querydata(request):
            query_count += 1
            pending_querydata.add(id(request))
            last_querydata_activity = time.monotonic()

    def on_request_done(request: Any) -> None:
        nonlocal last_querydata_activity
        if is_querydata(request):
            pending_querydata.discard(id(request))
            last_querydata_activity = time.monotonic()

    page.on("request", on_request)
    page.on("requestfinished", on_request_done)
    page.on("requestfailed", on_request_done)
    try:
        action()
        action_finished_at = time.monotonic()
        render_deadline = action_finished_at + timeout_seconds

        if frame is None:
            remaining = max(0.1, render_deadline - time.monotonic())
            frame = find_powerbi_frame(
                page,
                min(frame_timeout_seconds, remaining),
            )

        remaining = max(0.1, render_deadline - time.monotonic())
        frame.locator(POWERBI_ROOT_SELECTOR).wait_for(
            state="visible",
            timeout=min(frame_timeout_seconds, remaining) * 1_000,
        )

        last_dom_state: Any = None
        stable_since: float | None = None
        last_spinner_count: int | None = None

        while time.monotonic() < render_deadline:
            page.wait_for_timeout(250)
            now = time.monotonic()
            spinner_count = _visible_spinner_count(frame)
            dom_state = _visual_dom_state(frame)

            if spinner_count != last_spinner_count:
                logger.debug("Visuels Power BI encore en chargement : %d", spinner_count)
                last_spinner_count = spinner_count

            last_activity = last_querydata_activity if query_count else action_finished_at
            querydata_idle = not pending_querydata and now - last_activity >= quiet_seconds
            ready_now = querydata_idle and spinner_count == 0 and dom_state is not None

            if ready_now and dom_state == last_dom_state:
                if stable_since is None:
                    stable_since = now
                elif now - stable_since >= stable_seconds:
                    logger.info(
                        "Rendu Power BI stabilisé : %d requête(s) querydata, "
                        "aucun spinner, DOM stable %.1f s.",
                        query_count,
                        stable_seconds,
                    )
                    return frame, query_count
            else:
                stable_since = None

            last_dom_state = dom_state

        raise CaptureError(
            "Le rendu Power BI n'est pas devenu stable avant le délai maximal "
            f"({query_count} requête(s) querydata, "
            f"{len(pending_querydata)} encore en cours)."
        )
    finally:
        page.remove_listener("request", on_request)
        page.remove_listener("requestfinished", on_request_done)
        page.remove_listener("requestfailed", on_request_done)


def _visible_spinner_count(frame: Any) -> int:
    """Return the number of visible Power BI loading indicators."""
    try:
        spinners = frame.locator(POWERBI_LOADING_SELECTOR)
        return sum(1 for index in range(spinners.count()) if spinners.nth(index).is_visible())
    except Exception:
        # Power BI can replace the visual tree between two polling iterations.
        return 1


def _visual_dom_state(frame: Any) -> Any:
    """Return a small, data-free signature of the current Power BI visual tree."""
    try:
        return frame.evaluate(
            """() => {
                const root = document.querySelector('[data-testid="exploration-container"]');
                if (!root) return null;

                const previous = window.__pbirsMailerRenderState;
                if (!previous || previous.root !== root) {
                    if (previous?.observer) previous.observer.disconnect();
                    const state = {root, revision: 0, observer: null};
                    state.observer = new MutationObserver(() => state.revision += 1);
                    state.observer.observe(root, {
                        subtree: true,
                        childList: true,
                        attributes: true,
                        characterData: true
                    });
                    window.__pbirsMailerRenderState = state;
                }
                const renderState = window.__pbirsMailerRenderState;

                const selectors = [
                    'visual-container',
                    '.visualContainer',
                    '[data-testid="visual-container"]',
                    '[class*="visual-container"]'
                ];
                const nodes = [...new Set(selectors.flatMap(
                    selector => [...root.querySelectorAll(selector)]
                ))];

                return {
                    revision: renderState.revision,
                    rootChildren: root.childElementCount,
                    visuals: nodes.map(node => {
                        const rect = node.getBoundingClientRect();
                        const images = [...node.querySelectorAll('img')];
                        return {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            children: node.childElementCount,
                            svgNodes: node.querySelectorAll('svg *').length,
                            canvases: node.querySelectorAll('canvas').length,
                            images: images.length,
                            loadedImages: images.filter(image => image.complete).length
                        };
                    })
                };
            }"""
        )
    except Exception:
        # A transient DOM replacement is not considered stable.
        return None


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
                        stable_seconds=browser_config.render_stable_seconds,
                        frame_timeout_seconds=browser_config.frame_timeout_seconds,
                        logger=logger,
                        frame=frame,
                    )
                    logger.info("Navigation par libellé réussie : %s", display_name)
                    return selector
                except CaptureError:
                    raise
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
        frame, _ = wait_for_powerbi_render(
            page=page,
            action=lambda: page.goto(
                report_url,
                wait_until="domcontentloaded",
                timeout=browser_config.page_timeout_seconds * 1_000,
            ),
            timeout_seconds=browser_config.render_timeout_seconds,
            quiet_seconds=browser_config.render_quiet_seconds,
            stable_seconds=browser_config.render_stable_seconds,
            frame_timeout_seconds=browser_config.frame_timeout_seconds,
            logger=logger,
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
