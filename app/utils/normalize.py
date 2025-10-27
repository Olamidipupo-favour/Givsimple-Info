import re
from urllib.parse import urlparse

class PaymentNormalizationError(Exception):
    """Raised when a card link cannot be normalized"""
    pass


def normalize_card_link(url: str) -> str:
    """
    Validate and normalize a card link as a full HTTPS URL.
    - Requires scheme `https://` (converts `http://` to `https://`).
    - Ensures URL parses with a netloc.
    Returns the normalized URL string.
    """
    url = (url or '').strip()
    if not url:
        raise PaymentNormalizationError("Card link cannot be empty")

    # Require HTTPS (upgrade http)
    if url.startswith('http://'):
        url = 'https://' + url[len('http://'):]
    elif not url.startswith('https://'):
        raise PaymentNormalizationError("Card link must be a full https URL")

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise PaymentNormalizationError("Invalid URL format")

    return url


def validate_token_format(token: str) -> bool:
    """
    Validate token format (6-16 alphanumeric characters)
    """
    if not token:
        return False

    if not re.match(r'^[a-zA-Z0-9]{6,16}$', token):
        return False

    return True
