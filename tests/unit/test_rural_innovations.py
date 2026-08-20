import pytest
from services.catalog_service.storefront import get_seller_catalog_storefront
from services.ledger_service.baki_tagada import (
    format_baki_reminder_message,
    generate_upi_payment_link,
)


def test_generate_upi_payment_link():
    link = generate_upi_payment_link(
        "merchant@upi", "Radha SHG", 250.0, "Saree Payment"
    )
    assert "upi://pay?" in link
    assert "pa=merchant%40upi" in link
    assert "am=250.00" in link
    assert "cu=INR" in link


def test_format_baki_reminder_message():
    res = format_baki_reminder_message(
        "রহিম কাকা", 200.0, "লক্ষ্মী স্বনির্ভর গোষ্ঠী", "9876543210@upi"
    )
    assert res["customer_name"] == "রহিম কাকা"
    assert res["amount_inr"] == 200.0
    assert "রহিম কাকা" in res["reminder_text"]
    assert "₹200" in res["reminder_text"]
    assert "লক্ষ্মী স্বনির্ভর গোষ্ঠী" in res["reminder_text"]
    assert "upi://pay?" in res["upi_link"]


@pytest.mark.asyncio
async def test_get_seller_catalog_storefront_empty():
    res = await get_seller_catalog_storefront("")
    assert res["items"] == []
    assert res["storefront_url"] == ""
