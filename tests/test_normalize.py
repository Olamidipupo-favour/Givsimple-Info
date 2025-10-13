import pytest
from app.utils.normalize import (
    normalize_cashapp, normalize_paypal, normalize_venmo, 
    normalize_zelle, normalize_generic_url, detect_payment_provider,
    normalize_payment_handle, validate_token_format, PaymentNormalizationError
)

class TestCashAppNormalization:
    def test_normalize_cashapp_with_dollar_sign(self):
        assert normalize_cashapp("$user123") == "https://cash.app/$user123"
    
    def test_normalize_cashapp_without_dollar_sign(self):
        assert normalize_cashapp("user123") == "https://cash.app/$user123"
    
    def test_normalize_cashapp_with_at_sign(self):
        assert normalize_cashapp("@user123") == "https://cash.app/$user123"
    
    def test_normalize_cashapp_full_url(self):
        assert normalize_cashapp("https://cash.app/$user123") == "https://cash.app/$user123"
    
    def test_normalize_cashapp_http_url(self):
        assert normalize_cashapp("http://cash.app/$user123") == "https://cash.app/$user123"
    
    def test_normalize_cashapp_domain_only(self):
        assert normalize_cashapp("cash.app/$user123") == "https://cash.app/$user123"
    
    def test_normalize_cashapp_empty_handle(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_cashapp("")
    
    def test_normalize_cashapp_invalid_characters(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_cashapp("user@123")

class TestPayPalNormalization:
    def test_normalize_paypal_basic(self):
        assert normalize_paypal("user123") == "https://paypal.me/user123"
    
    def test_normalize_paypal_with_at_sign(self):
        assert normalize_paypal("@user123") == "https://paypal.me/user123"
    
    def test_normalize_paypal_full_url(self):
        assert normalize_paypal("https://paypal.me/user123") == "https://paypal.me/user123"
    
    def test_normalize_paypal_http_url(self):
        assert normalize_paypal("http://paypal.me/user123") == "https://paypal.me/user123"
    
    def test_normalize_paypal_domain_only(self):
        assert normalize_paypal("paypal.me/user123") == "https://paypal.me/user123"
    
    def test_normalize_paypal_invalid_characters(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_paypal("user@123")

class TestVenmoNormalization:
    def test_normalize_venmo_basic(self):
        assert normalize_venmo("user123") == "https://venmo.com/u/user123"
    
    def test_normalize_venmo_with_at_sign(self):
        assert normalize_venmo("@user123") == "https://venmo.com/u/user123"
    
    def test_normalize_venmo_full_url(self):
        assert normalize_venmo("https://venmo.com/u/user123") == "https://venmo.com/u/user123"
    
    def test_normalize_venmo_http_url(self):
        assert normalize_venmo("http://venmo.com/u/user123") == "https://venmo.com/u/user123"
    
    def test_normalize_venmo_domain_only(self):
        assert normalize_venmo("venmo.com/u/user123") == "https://venmo.com/u/user123"
    
    def test_normalize_venmo_invalid_characters(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_venmo("user@123")

class TestZelleNormalization:
    def test_normalize_zelle_with_email(self):
        result = normalize_zelle(email="test@example.com")
        assert "email=test@example.com" in result
        assert "https://givsimple.com/pay-by-zelle" in result
    
    def test_normalize_zelle_with_phone(self):
        result = normalize_zelle(phone="+1234567890")
        assert "phone=%2B1234567890" in result
        assert "https://givsimple.com/pay-by-zelle" in result
    
    def test_normalize_zelle_with_both(self):
        result = normalize_zelle(email="test@example.com", phone="+1234567890")
        assert "email=test@example.com" in result
        assert "phone=%2B1234567890" in result
    
    def test_normalize_zelle_no_contact_info(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_zelle()
    
    def test_normalize_zelle_invalid_email(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_zelle(email="invalid-email")
    
    def test_normalize_zelle_invalid_phone(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_zelle(phone="123")

class TestGenericURLNormalization:
    def test_normalize_generic_url_with_protocol(self):
        assert normalize_generic_url("https://example.com") == "https://example.com"
    
    def test_normalize_generic_url_without_protocol(self):
        assert normalize_generic_url("example.com") == "https://example.com"
    
    def test_normalize_generic_url_allowed_domain(self):
        assert normalize_generic_url("https://cash.app/test") == "https://cash.app/test"
    
    def test_normalize_generic_url_disallowed_domain(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_generic_url("https://malicious.com")

class TestPaymentProviderDetection:
    def test_detect_cashapp(self):
        assert detect_payment_provider("$user123") == "cashapp"
        assert detect_payment_provider("https://cash.app/$user") == "cashapp"
    
    def test_detect_paypal(self):
        assert detect_payment_provider("paypal.me/user") == "paypal"
        assert detect_payment_provider("https://paypal.me/user") == "paypal"
    
    def test_detect_venmo(self):
        assert detect_payment_provider("@user123") == "venmo"
        assert detect_payment_provider("https://venmo.com/u/user") == "venmo"
    
    def test_detect_zelle(self):
        assert detect_payment_provider("zelle") == "zelle"
        assert detect_payment_provider("Zelle payment") == "zelle"
    
    def test_detect_generic(self):
        assert detect_payment_provider("https://example.com") == "generic"

class TestTokenValidation:
    def test_validate_token_valid(self):
        assert validate_token_format("ABC12345") == True
        assert validate_token_format("abcdefgh") == True
        assert validate_token_format("12345678") == True
        assert validate_token_format("ABC1234567890123") == True  # 16 chars
        assert validate_token_format("qwerty") == True  # 6 chars now valid
    
    def test_validate_token_invalid_length(self):
        assert validate_token_format("ABC12") == False  # Too short
        assert validate_token_format("ABC123456789012345") == False  # Too long
    
    def test_validate_token_invalid_characters(self):
        assert validate_token_format("ABC-123") == False  # Hyphen
        assert validate_token_format("ABC@123") == False  # At sign
        assert validate_token_format("ABC 123") == False  # Space
    
    def test_validate_token_empty(self):
        assert validate_token_format("") == False
        assert validate_token_format(None) == False

class TestPaymentHandleNormalization:
    def test_normalize_cashapp_handle(self):
        url, provider = normalize_payment_handle("$user123")
        assert url == "https://cash.app/$user123"
        assert provider == "cashapp"
    
    def test_normalize_paypal_handle(self):
        url, provider = normalize_payment_handle("user123")
        assert url == "https://paypal.me/user123"
        assert provider == "paypal"
    
    def test_normalize_venmo_handle(self):
        url, provider = normalize_payment_handle("@user123")
        assert url == "https://venmo.com/u/user123"
        assert provider == "venmo"
    
    def test_normalize_zelle_handle(self):
        url, provider = normalize_payment_handle("zelle", email="test@example.com")
        assert "https://givsimple.com/pay-by-zelle" in url
        assert provider == "zelle"
    
    def test_normalize_generic_url(self):
        url, provider = normalize_payment_handle("https://cash.app/test")
        assert url == "https://cash.app/test"
        assert provider == "generic"
    
    def test_normalize_empty_handle(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_payment_handle("")
    
    def test_normalize_invalid_handle(self):
        with pytest.raises(PaymentNormalizationError):
            normalize_payment_handle("invalid@domain.com")
