from shared.observability.email_reporter import _pct, render_metrics_html_report


def test_render_metrics_html_report():
    sample_metrics = {
        "collected_at": "2026-07-29T23:00:00Z",
        "month_bucket": "2026-07",
        "users": {
            "total": 50,
            "onboarded": 45,
            "new_24h": 5,
            "tiers": {"free": 40, "basic": 5, "pro": 3, "unlimited": 2},
        },
        "product": {
            "ledger_entries_total": 120,
            "total_income_inr": 15000.0,
            "total_expense_inr": 5000.0,
            "catalog_creations_total": 30,
            "seller_profiles_total": 12,
        },
        "api_usage": {
            "sarvam_chat": 250,
            "sarvam_vision": 25,
            "sarvam_stt": 40,
            "sarvam_translate": 80,
            "flux": 10,
            "total_calls": 405,
            "estimated_cost_inr": 59.0,
            "estimated_cost_usd": 0.71,
        },
        "security": {
            "rate_limited_numbers_24h": 1,
            "total_webhook_dedup_records": 150,
        },
    }

    html = render_metrics_html_report(sample_metrics)
    assert "AI-SATHI Metrics & Health Report" in html
    assert "50" in html
    assert "2026-07" in html
    assert "Basic (₹99)" in html
    assert "₹59.00" in html


def test_percentage_helper():
    assert _pct(25, 100) == "25.0"
    assert _pct(0, 50) == "0.0"
    assert _pct(10, 0) == "0.0"
