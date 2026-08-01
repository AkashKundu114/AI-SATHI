from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from shared.config.settings import get_settings

logger = logging.getLogger("email_reporter")


def render_metrics_html_report(metrics: dict) -> str:
    
    collected_at = metrics.get("collected_at", "")[:19].replace("T", " ")
    month = metrics.get("month_bucket", "")
    users = metrics.get("users", {})
    tiers = users.get("tiers", {})
    prod = metrics.get("product", {})
    api = metrics.get("api_usage", {})
    sec = metrics.get("security", {})

    return f


def _pct(part: int, total: int) -> str:
    if not total:
        return "0.0"
    return f"{(part / total) * 100:.1f}"


async def send_metrics_email(metrics: dict, recipient_email: str | None = None) -> bool:
    
    s = get_settings()
    to_addr = recipient_email or s.metrics_alert_email
    if not to_addr:
        logger.warning("No recipient email provided and METRICS_ALERT_EMAIL is not set in environment.")
        return False

    if not s.smtp_host:
        logger.warning("SMTP_HOST is not configured in environment settings. Skipping email delivery.")
        return False

    html_content = render_metrics_html_report(metrics)

    msg = EmailMessage()
    msg["Subject"] = f"📊 AI-SATHI Metrics Report [{metrics.get('month_bucket', '')}]"
    msg["From"] = s.smtp_from_email or f"AI-SATHI Analytics <{s.smtp_username}>"
    msg["To"] = to_addr
    msg.set_content("Please enable HTML viewing to see the full AI-SATHI metrics report.")
    msg.add_alternative(html_content, subtype="html")

    try:
        if s.smtp_port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, context=context, timeout=15) as server:
                if s.smtp_username and s.smtp_password:
                    server.login(s.smtp_username, s.smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15) as server:
                server.starttls(context=ssl.create_default_context())
                if s.smtp_username and s.smtp_password:
                    server.login(s.smtp_username, s.smtp_password)
                server.send_message(msg)

        logger.info("Successfully sent metrics report email to %s", to_addr)
        return True
    except Exception as exc:
        logger.exception("Failed to deliver metrics report email to %s: %s", to_addr, exc)
        return False
