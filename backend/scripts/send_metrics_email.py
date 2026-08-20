from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.observability.email_reporter import render_metrics_html_report, send_metrics_email
from shared.observability.metrics import collect_system_metrics


async def main_async(to_email: str | None, dry_run: bool, json_output: bool) -> None:
    if not json_output:
        print("[*] Collecting system metrics from database...")
    metrics = await collect_system_metrics()

    if json_output:
        print(json.dumps(metrics, indent=2))
        return

    if dry_run:
        print("[+] Rendered HTML Report preview (dry run, no email sent):\n")
        html = render_metrics_html_report(metrics)
        print(html[:800] + "\n... [truncated] ...\n")
        print("Summary:")
        print(f"  * Total Users       : {metrics['users']['total']}")
        print(f"  * Monthly API Calls : {metrics['api_usage']['total_calls']}")
        print(
            f"  * Estimated Cost    : INR {metrics['api_usage']['estimated_cost_inr']} (~${metrics['api_usage']['estimated_cost_usd']})"
        )
        return

    print(f"[*] Sending metrics email report to {to_email or 'configured recipient'}...")
    success = await send_metrics_email(metrics, recipient_email=to_email)
    if success:
        print("[+] Email report delivered successfully!")
    else:
        print("[-] Email delivery failed. Check logs and SMTP configuration in .env.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect and email AI-SATHI metrics report.")
    parser.add_argument("--to", type=str, default=None, help="Recipient email address (overrides METRICS_ALERT_EMAIL)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Collect and render report locally without sending email"
    )
    parser.add_argument("--json", action="store_true", help="Output raw metrics JSON to stdout")
    args = parser.parse_args()

    asyncio.run(main_async(args.to, args.dry_run, args.json))


if __name__ == "__main__":
    main()
