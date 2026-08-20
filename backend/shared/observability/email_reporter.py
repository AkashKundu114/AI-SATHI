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

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f8; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
        .header {{ background: linear-gradient(135deg, #1a5276, #2980b9); color: #ffffff; padding: 25px 30px; border-bottom: 3px solid #1f618d; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
        .header p {{ margin: 5px 0 0 0; opacity: 0.85; font-size: 13px; }}
        .content {{ padding: 30px; }}
        .grid {{ display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 25px; }}
        .card {{ flex: 1 1 calc(50% - 15px); background: #f8f9fa; border-left: 4px solid #3498db; border-radius: 6px; padding: 15px; box-sizing: border-box; }}
        .card.green {{ border-left-color: #2ecc71; }}
        .card.purple {{ border-left-color: #9b59b6; }}
        .card.orange {{ border-left-color: #e67e22; }}
        .card-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #7f8c8d; font-weight: 600; margin-bottom: 5px; }}
        .card-value {{ font-size: 22px; font-weight: 700; color: #2c3e50; }}
        .card-sub {{ font-size: 12px; color: #95a5a6; margin-top: 3px; }}
        h2 {{ font-size: 16px; color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; margin-top: 25px; margin-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px; }}
        th {{ background-color: #f2f4f4; text-align: left; padding: 10px; color: #34495e; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
        td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
        tr:last-child td {{ border-bottom: none; }}
        .badge {{ display: inline-block; padding: 3px 8px; font-size: 11px; font-weight: 600; border-radius: 12px; background: #e8f8f5; color: #117864; }}
        .footer {{ background-color: #f8f9fa; padding: 15px 30px; font-size: 12px; color: #95a5a6; text-align: center; border-top: 1px solid #ecf0f1; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI-SATHI Metrics & Health Report</h1>
            <p>Generated on {collected_at} UTC • Month: {month}</p>
        </div>

        <div class="content">
            <div class="grid">
                <div class="card">
                    <div class="card-title">Total Users</div>
                    <div class="card-value">{users.get("total", 0):,}</div>
                    <div class="card-sub">{users.get("onboarded", 0):,} onboarded ({users.get("new_24h", 0)} new in 24h)</div>
                </div>
                <div class="card green">
                    <div class="card-title">Monthly API Spend</div>
                    <div class="card-value">₹{api.get("estimated_cost_inr", 0.0):,.2f}</div>
                    <div class="card-sub">~${api.get("estimated_cost_usd", 0.0):,.2f} USD ({api.get("total_calls", 0):,} total calls)</div>
                </div>
                <div class="card purple">
                    <div class="card-title">Ledger Entries</div>
                    <div class="card-value">{prod.get("ledger_entries_total", 0):,}</div>
                    <div class="card-sub">₹{prod.get("total_income_inr", 0.0):,.0f} income / ₹{prod.get("total_expense_inr", 0.0):,.0f} expense</div>
                </div>
                <div class="card orange">
                    <div class="card-title">Catalog Posters</div>
                    <div class="card-value">{prod.get("catalog_creations_total", 0):,}</div>
                    <div class="card-sub">{prod.get("seller_profiles_total", 0)} seller profiles active</div>
                </div>
            </div>

            <h2>User Tier Distribution</h2>
            <table>
                <thead>
                    <tr><th>Plan Tier</th><th>User Count</th><th>Percentage</th></tr>
                </thead>
                <tbody>
                    <tr><td><strong>Free</strong></td><td>{tiers.get("free", 0):,}</td><td>{_pct(tiers.get("free", 0), users.get("total", 1))}%</td></tr>
                    <tr><td><strong>Basic (₹99)</strong></td><td>{tiers.get("basic", 0):,}</td><td>{_pct(tiers.get("basic", 0), users.get("total", 1))}%</td></tr>
                    <tr><td><strong>Pro (₹299)</strong></td><td>{tiers.get("pro", 0):,}</td><td>{_pct(tiers.get("pro", 0), users.get("total", 1))}%</td></tr>
                    <tr><td><strong>Unlimited (₹499)</strong></td><td>{tiers.get("unlimited", 0):,}</td><td>{_pct(tiers.get("unlimited", 0), users.get("total", 1))}%</td></tr>
                </tbody>
            </table>

            <h2>Monthly API Consumption ({month})</h2>
            <table>
                <thead>
                    <tr><th>API Service</th><th>Call Count</th><th>Estimated Cost</th></tr>
                </thead>
                <tbody>
                    <tr><td>Sarvam Chat (30b / 105b)</td><td>{api.get("sarvam_chat", 0):,}</td><td>₹{(api.get("sarvam_chat", 0) * 0.012):,.2f}</td></tr>
                    <tr><td>Sarvam Vision</td><td>{api.get("sarvam_vision", 0):,}</td><td>₹{(api.get("sarvam_vision", 0) * 0.50):,.2f}</td></tr>
                    <tr><td>Sarvam STT (Saaras v3)</td><td>{api.get("sarvam_stt", 0):,}</td><td>₹{(api.get("sarvam_stt", 0) * 0.25):,.2f}</td></tr>
                    <tr><td>Sarvam Translate</td><td>{api.get("sarvam_translate", 0):,}</td><td>₹{(api.get("sarvam_translate", 0) * 0.01):,.2f}</td></tr>
                    <tr><td>Flux Pro Image Gen</td><td>{api.get("flux", 0):,}</td><td>${(api.get("flux", 0) * 0.04):,.2f} (~₹{(api.get("flux", 0) * 3.35):,.2f})</td></tr>
                </tbody>
            </table>

            <h2>System & Security Health</h2>
            <table>
                <tbody>
                    <tr><td>Active Rate Limited Numbers (24h)</td><td><span class="badge">{sec.get("rate_limited_numbers_24h", 0)}</span></td></tr>
                    <tr><td>Webhook Dedup Table Rows</td><td>{sec.get("total_webhook_dedup_records", 0):,}</td></tr>
                </tbody>
            </table>
        </div>

        <div class="footer">
            AI-SATHI Autonomous Monitoring • Confidential System Telemetry
        </div>
    </div>
</body>
</html>"""


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
