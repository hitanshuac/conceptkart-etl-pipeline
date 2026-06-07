import pytest

from price_check import validate_price_payload


def test_validation_valid_payload():
    """
    Test that a valid payload returns True for is_valid.
    """
    payload = {"price_current": 15000}
    is_valid, is_target_hit = validate_price_payload(payload, target_price=17000)
    assert is_valid is True
    assert is_target_hit is True


def test_validation_invalid_price():
    """
    Test that a negative or zero price raises a ValueError.
    """
    payload = {"price_current": 0}
    with pytest.raises(ValueError, match="ANOMALY: Price Rs.0 is too low"):
        validate_price_payload(payload, target_price=17000)


def test_validation_missing_key():
    """
    Test that a missing price_current key raises a KeyError.
    """
    payload = {"wrong_key": 15000}
    with pytest.raises(KeyError, match="FATAL: 'price_current' key is missing"):
        validate_price_payload(payload, target_price=17000)
