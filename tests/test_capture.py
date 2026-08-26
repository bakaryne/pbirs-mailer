import logging
from urllib.parse import parse_qs, urlsplit

import pytest

from pbirs_mailer.capture import (
    POWERBI_LOADING_SELECTOR,
    POWERBI_ROOT_SELECTOR,
    CaptureError,
    build_report_url,
    normalize_text,
    wait_for_powerbi_render,
)


def test_build_report_url_preserves_existing_parameters() -> None:
    result = build_report_url(
        "http://pbirs/Reports/powerbi/report?rs:embed=true&filter=A%2FB",
        "ReportSection42",
    )

    query = parse_qs(urlsplit(result).query)
    assert "rs:embed=true" in result
    assert query == {
        "rs:embed": ["true"],
        "filter": ["A/B"],
        "pageName": ["ReportSection42"],
    }


def test_build_report_url_does_not_change_url_without_internal_name() -> None:
    url = "http://pbirs/Reports/powerbi/report?rs:embed=true"
    assert build_report_url(url, None) == url


def test_normalize_text_handles_spaces_and_case() -> None:
    assert normalize_text("  Observation   MÉDICALE  ") == "observation médicale"


class FakeFrame:
    def __init__(self, url: str) -> None:
        self.url = url


class FakePage:
    def __init__(self) -> None:
        self.main_frame = FakeFrame("http://pbirs/Reports/powerbi/Folder/Report")
        self.embedded_frame = FakeFrame("http://pbirs/PowerBI/?id=42")
        self.frames = [self.main_frame, self.embedded_frame]

    def wait_for_timeout(self, _milliseconds: int) -> None:
        raise AssertionError("The embedded frame should be found immediately")


def test_find_powerbi_frame_does_not_return_main_pbirs_page() -> None:
    from pbirs_mailer.capture import find_powerbi_frame

    page = FakePage()
    assert find_powerbi_frame(page, timeout_seconds=1) is page.embedded_frame


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def monotonic(self) -> float:
        return self.value


class FakeRequest:
    url = "http://pbirs/PowerBI/querydata"


class FakeLocator:
    def __init__(self, frame: "FakeRenderFrame", selector: str) -> None:
        self.frame = frame
        self.selector = selector

    def wait_for(self, **_kwargs: object) -> None:
        assert self.selector == POWERBI_ROOT_SELECTOR

    def count(self) -> int:
        assert self.selector == POWERBI_LOADING_SELECTOR
        return 1

    def nth(self, _index: int) -> "FakeLocator":
        return self

    def is_visible(self) -> bool:
        return self.frame.spinner_visible


class FakeRenderFrame:
    def __init__(self) -> None:
        self.spinner_visible = True

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(self, selector)

    def evaluate(self, _script: str) -> dict[str, int]:
        return {"visuals": 3, "revision": 1}


class FakeRenderPage:
    def __init__(self, clock: FakeClock, frame: FakeRenderFrame) -> None:
        self.clock = clock
        self.frame = frame
        self.handlers: dict[str, list] = {}
        self.tick = 0
        self.request = FakeRequest()
        self.finish_request = True

    def on(self, event: str, handler: object) -> None:
        self.handlers.setdefault(event, []).append(handler)

    def remove_listener(self, event: str, handler: object) -> None:
        self.handlers[event].remove(handler)

    def emit(self, event: str, payload: object) -> None:
        for handler in tuple(self.handlers.get(event, ())):
            handler(payload)

    def wait_for_timeout(self, milliseconds: int) -> None:
        self.clock.value += milliseconds / 1_000
        self.tick += 1
        if self.tick == 2 and self.finish_request:
            self.emit("requestfinished", self.request)
        if self.tick == 3:
            self.frame.spinner_visible = False


def test_wait_for_powerbi_render_waits_for_all_conditions(monkeypatch) -> None:
    clock = FakeClock()
    frame = FakeRenderFrame()
    page = FakeRenderPage(clock, frame)
    monkeypatch.setattr("pbirs_mailer.capture.time.monotonic", clock.monotonic)

    def action() -> None:
        page.emit("request", page.request)

    returned_frame, query_count = wait_for_powerbi_render(
        page=page,
        action=action,
        timeout_seconds=5,
        quiet_seconds=0.5,
        stable_seconds=0.5,
        frame_timeout_seconds=1,
        logger=logging.getLogger("test"),
        frame=frame,
    )

    assert returned_frame is frame
    assert query_count == 1
    assert page.tick >= 6
    assert all(not handlers for handlers in page.handlers.values())


def test_wait_for_powerbi_render_fails_if_querydata_never_finishes(monkeypatch) -> None:
    clock = FakeClock()
    frame = FakeRenderFrame()
    page = FakeRenderPage(clock, frame)
    page.finish_request = False
    monkeypatch.setattr("pbirs_mailer.capture.time.monotonic", clock.monotonic)

    with pytest.raises(CaptureError, match="pas devenu stable"):
        wait_for_powerbi_render(
            page=page,
            action=lambda: page.emit("request", page.request),
            timeout_seconds=1,
            quiet_seconds=0.25,
            stable_seconds=0.25,
            frame_timeout_seconds=1,
            logger=logging.getLogger("test"),
            frame=frame,
        )

    assert all(not handlers for handlers in page.handlers.values())
