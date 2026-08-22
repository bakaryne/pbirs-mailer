"""Email construction and SMTP delivery."""

from __future__ import annotations

import html
import mimetypes
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path

from .config import SmtpConfig, Subscription


def build_message(
    subscription: Subscription,
    smtp_config: SmtpConfig,
    image_path: Path,
) -> EmailMessage:
    """Build a multipart email containing the capture as an inline image."""
    domain = smtp_config.sender.rpartition("@")[2] or "localhost"
    image_cid = make_msgid(domain=domain)
    cid = image_cid[1:-1]

    message = EmailMessage()
    message["Subject"] = subscription.subject
    message["From"] = smtp_config.sender
    message["To"] = ", ".join(subscription.recipients)
    target = subscription.page.display_name or subscription.page.internal_name or subscription.name
    message.set_content(
        "Bonjour,\n\n"
        f"Vous trouverez ci-dessous le rapport : {target}\n\n"
        f"Ouvrir le rapport Power BI : {subscription.url}\n\n"
        "Cordialement\n"
    )

    safe_target = html.escape(target)
    safe_url = html.escape(subscription.url, quote=True)
    message.add_alternative(
        f"""\
<html>
  <body>
    <p>Bonjour,</p>
    <p>Vous trouverez ci-dessous le suivi <strong>{safe_target}</strong>.</p>
    <p><img src="cid:{cid}" style="max-width:100%;height:auto;border:0" alt="{safe_target}"></p>
    <p><a href="{safe_url}">Ouvrir le rapport Power BI</a></p>
    <p>Cordialement</p>
  </body>
</html>
""",
        subtype="html",
    )

    mime_type, _ = mimetypes.guess_type(image_path.name)
    maintype, subtype = (mime_type or "image/png").split("/", 1)
    html_part = message.get_payload()[1]
    html_part.add_related(
        image_path.read_bytes(),
        maintype=maintype,
        subtype=subtype,
        cid=image_cid,
        filename=image_path.name,
    )
    return message


def send_message(message: EmailMessage, smtp_config: SmtpConfig) -> None:
    """Send one message through the configured SMTP relay."""
    with smtplib.SMTP(
        smtp_config.server,
        smtp_config.port,
        timeout=smtp_config.timeout_seconds,
    ) as smtp:
        if smtp_config.starttls:
            smtp.starttls()
        smtp.send_message(message)
