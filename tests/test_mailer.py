from pathlib import Path

from pbirs_mailer.config import PageTarget, SmtpConfig, Subscription
from pbirs_mailer.mailer import build_message


def test_build_message_embeds_capture_and_report_link(tmp_path: Path) -> None:
    image = tmp_path / "capture.png"
    image.write_bytes(b"not-a-real-png-but-valid-for-email-test")
    subscription = Subscription(
        name="Report",
        url="http://pbirs/Reports/powerbi/report?rs:embed=true",
        page=PageTarget(display_name="Overview"),
        recipients=("one@example.org", "two@example.org"),
        subject="Report subject",
        filename="capture.png",
    )
    smtp = SmtpConfig(
        enabled=True,
        server="smtp.example.org",
        port=25,
        sender="sender@example.org",
    )

    message = build_message(subscription, smtp, image)
    rendered = message.as_string()

    assert message["Subject"] == "Report subject"
    assert message["To"] == "one@example.org, two@example.org"
    assert "Content-ID:" in rendered
    assert "capture.png" in rendered
    assert "Ouvrir le rapport Power BI" in rendered
