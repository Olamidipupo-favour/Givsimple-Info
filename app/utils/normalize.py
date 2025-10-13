import re
from urllib.parse import urlparse, urljoin
from app.models import PaymentProvider
from app.config import Config

class PaymentNormalizationError(Exception):
    """Raised when payment handle cannot be normalized"""
    pass

def normalize_cashapp(handle):
    """
    Normalize Cash App handle to https://cash.app/$Handle format
    """
    # Remove any existing protocol and domain
    handle = handle.strip()
    if handle.startswith('https://cash.app/'):
        return handle
    if handle.startswith('http://cash.app/'):
        return handle.replace('http://', 'https://')
    if handle.startswith('cash.app/'):
        return f'https://{handle}'
    
    # Remove @ symbol if present
    if handle.startswith('@'):
        handle = handle[1:]
    
    # Remove $ symbol if present, we'll add it back
    if handle.startswith('$'):
        handle = handle[1:]
    
    # Ensure handle is not empty
    if not handle:
        raise PaymentNormalizationError("Cash App handle cannot be empty")
    
    # Validate handle format (alphanumeric and underscores)
    if not re.match(r'^[a-zA-Z0-9_]+$', handle):
        raise PaymentNormalizationError("Cash App handle contains invalid characters")
    
    return f'https://cash.app/${handle}'

def normalize_paypal(handle):
    """
    Normalize PayPal handle to https://paypal.me/Name format
    """
    handle = handle.strip()
    
    # If already a full URL, validate and return
    if handle.startswith('https://paypal.me/'):
        return handle
    if handle.startswith('http://paypal.me/'):
        return handle.replace('http://', 'https://')
    if handle.startswith('paypal.me/'):
        return f'https://{handle}'
    
    # Remove @ symbol if present
    if handle.startswith('@'):
        handle = handle[1:]
    
    # Validate handle format
    if not re.match(r'^[a-zA-Z0-9_-]+$', handle):
        raise PaymentNormalizationError("PayPal handle contains invalid characters")
    
    return f'https://paypal.me/{handle}'

def normalize_venmo(handle):
    """
    Normalize Venmo handle to https://venmo.com/u/handle format
    """
    handle = handle.strip()
    
    # If already a full URL, validate and return
    if handle.startswith('https://venmo.com/u/'):
        return handle
    if handle.startswith('http://venmo.com/u/'):
        return handle.replace('http://', 'https://')
    if handle.startswith('venmo.com/u/'):
        return f'https://{handle}'
    
    # Remove @ symbol if present
    if handle.startswith('@'):
        handle = handle[1:]
    
    # Validate handle format
    if not re.match(r'^[a-zA-Z0-9_-]+$', handle):
        raise PaymentNormalizationError("Venmo handle contains invalid characters")
    
    return f'https://venmo.com/u/{handle}'

def normalize_zelle(email=None, phone=None):
    """
    Normalize Zelle to internal instruction page
    """
    if not email and not phone:
        raise PaymentNormalizationError("Zelle requires either email or phone")
    
    # Basic email validation
    if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise PaymentNormalizationError("Invalid email format for Zelle")
    
    # Basic phone validation (US format)
    if phone and not re.match(r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$', phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')):
        raise PaymentNormalizationError("Invalid phone format for Zelle")
    
    # Create instruction URL
    params = []
    if email:
        params.append(f'email={email}')
    if phone:
        params.append(f'phone={phone}')
    
    return f'https://givsimple.com/pay-by-zelle?{"&".join(params)}'

def normalize_generic_url(url):
    """
    Validate and normalize generic URLs against allowed domains
    """
    url = url.strip()
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    # Parse URL
    parsed = urlparse(url)
    if not parsed.netloc:
        raise PaymentNormalizationError("Invalid URL format")
    
    # Check against allowed domains
    domain = parsed.netloc.lower()
    allowed_domains = Config.ALLOWED_PAYMENT_DOMAINS
    
    is_allowed = False
    for allowed_domain in allowed_domains:
        if domain == allowed_domain or domain.endswith(f'.{allowed_domain}'):
            is_allowed = True
            break
    
    if not is_allowed:
        raise PaymentNormalizationError(f"Domain {domain} is not in allowed payment domains")
    
    return url

def detect_payment_provider(handle):
    """
    Detect payment provider from handle
    """
    handle_lower = handle.lower().strip()
    
    if any(indicator in handle_lower for indicator in ['cash.app', '$']):
        return PaymentProvider.CASHAPP
    elif any(indicator in handle_lower for indicator in ['paypal.me', 'paypal']):
        return PaymentProvider.PAYPAL
    elif any(indicator in handle_lower for indicator in ['venmo.com', 'venmo']):
        return PaymentProvider.VENMO
    elif any(indicator in handle_lower for indicator in ['zelle']):
        return PaymentProvider.ZELLE
    else:
        return PaymentProvider.GENERIC

def normalize_payment_handle(handle, email=None, phone=None):
    """
    Main function to normalize any payment handle
    Returns tuple: (normalized_url, payment_provider)
    """
    if not handle:
        raise PaymentNormalizationError("Payment handle cannot be empty")
    
    # Detect provider
    provider = detect_payment_provider(handle)
    
    try:
        if provider == PaymentProvider.CASHAPP:
            normalized_url = normalize_cashapp(handle)
        elif provider == PaymentProvider.PAYPAL:
            normalized_url = normalize_paypal(handle)
        elif provider == PaymentProvider.VENMO:
            normalized_url = normalize_venmo(handle)
        elif provider == PaymentProvider.ZELLE:
            normalized_url = normalize_zelle(email, phone)
        else:  # GENERIC
            normalized_url = normalize_generic_url(handle)
        
        return normalized_url, provider
    
    except Exception as e:
        if isinstance(e, PaymentNormalizationError):
            raise
        else:
            raise PaymentNormalizationError(f"Failed to normalize payment handle: {str(e)}")

def validate_token_format(token):
    """
    Validate token format (6-16 alphanumeric characters)
    """
    if not token:
        return False
    
    if not re.match(r'^[a-zA-Z0-9]{6,16}$', token):
        return False
    
    return True
