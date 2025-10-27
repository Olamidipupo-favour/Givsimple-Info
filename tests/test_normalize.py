import pytest
from app.utils.normalize import (
    normalize_card_link,
    validate_token_format,
    PaymentNormalizationError,
)

class TestCardLinkNormalization:
    def test_valid_https_url(self):
        assert normalize_card_link("https://example.com/path") == "https://example.com/path"

    def test_http_upgrades_to_https(self):
        assert normalize_card_link("http://example.com/path") == "https://example.com/path"

    def test_missing_scheme_error(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_card_link("example.com/path")

    def test_invalid_scheme_error(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_card_link("ftp://example.com/path")

    def test_missing_netloc_error(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_card_link("https:///no-host")

    def test_empty_error(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_card_link("")
        with pytest.raises(PaymentNormalizationError):
            normalize_card_link(None)

    def test_with_query_and_fragment(self):
        url = "https://example.com/pay?x=1#section"
        assert normalize_card_link(url) == url

class TestTokenValidation:
    def test_validate_token_valid(self):
        assert validate_token_format("ABC12345") is True
        assert validate_token_format("abcdefgh") is True
        assert validate_token_format("12345678") is True
        assert validate_token_format("ABC1234567890123") is True  # 16 chars
        assert validate_token_format("qwerty") is True  # 6 chars

    def test_validate_token_invalid_length(self):
        assert validate_token_format("ABC12") is False  # Too short
        assert validate_token_format("ABC123456789012345") is False  # Too long

    def test_validate_token_invalid_characters(self):
        assert validate_token_format("ABC-123") is False  # Hyphen
        assert validate_token_format("ABC@123") is False  # At sign
        assert validate_token_format("ABC 123") is False  # Space

    def test_validate_token_empty(self):
        assert validate_token_format("") is False
        assert validate_token_format(None) is False
