from shared.config.usage_limits import TIER_LIMITS


def test_tier_limits_defined():
    assert "free" in TIER_LIMITS
    assert "basic" in TIER_LIMITS
    assert "pro" in TIER_LIMITS
    assert "unlimited" in TIER_LIMITS

    free_limits = TIER_LIMITS["free"]
    assert free_limits["sarvam_chat"] == 200
    assert free_limits["sarvam_vision"] == 20
    assert free_limits["sarvam_stt"] == 50
    assert free_limits["flux"] == 15
