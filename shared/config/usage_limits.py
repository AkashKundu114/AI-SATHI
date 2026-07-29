from __future__ import annotations

TIER_LIMITS: dict[str, dict[str, int]] = {
    "free": {
        "sarvam_chat": 200,
        "sarvam_vision": 20,
        "sarvam_stt": 50,
        "sarvam_translate": 100,
        "flux": 15,
        "total_sarvam": 370,
        "total_flux": 15,
    },
    "basic": {
        "sarvam_chat": 600,
        "sarvam_vision": 60,
        "sarvam_stt": 150,
        "sarvam_translate": 300,
        "flux": 50,
        "total_sarvam": 1110,
        "total_flux": 50,
    },
    "pro": {
        "sarvam_chat": 2000,
        "sarvam_vision": 200,
        "sarvam_stt": 500,
        "sarvam_translate": 1000,
        "flux": 200,
        "total_sarvam": 3700,
        "total_flux": 200,
    },
    "unlimited": {
        "sarvam_chat": 999999,
        "sarvam_vision": 999999,
        "sarvam_stt": 999999,
        "sarvam_translate": 999999,
        "flux": 999999,
        "total_sarvam": 999999,
        "total_flux": 999999,
    },
}
