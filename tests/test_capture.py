from urllib.parse import parse_qs, urlsplit

from pbirs_mailer.capture import build_report_url, normalize_text


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
