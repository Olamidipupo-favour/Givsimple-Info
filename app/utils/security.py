import secrets
import string
from functools import wraps
from flask import session, redirect, url_for, flash, request, current_app
from app.models import AdminUser, AuditLog
from app import db

def generate_secure_token(length=12):
    """Generate a secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_admin():
    """Get current admin user from session"""
    if not session.get('admin_logged_in'):
        return None
    
    admin_email = session.get('admin_email')
    if not admin_email:
        return None
    
    return AdminUser.query.filter_by(email=admin_email, is_active=True).first()

def log_admin_action(action, tag_id=None, meta=None):
    """Log admin action to audit log"""
    admin = get_current_admin()
    actor = admin.email if admin else 'system'
    
    AuditLog.log(actor, action, tag_id, meta)

def sanitize_input(text):
    """Basic input sanitization"""
    if not text:
        return text
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()

def validate_csrf_token():
    """Validate CSRF token for API requests"""
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(request.form.get('csrf_token'))
        return True
    except:
        return False

def rate_limit_key():
    """Generate rate limit key for current request"""
    from flask_limiter.util import get_remote_address
    return f"rate_limit:{get_remote_address()}"

def is_safe_url(target):
    """Check if URL is safe for redirects"""
    from urllib.parse import urlparse, urljoin
    
    if not target:
        return False
    
    # Parse the target URL
    parsed = urlparse(target)
    
    # Allow relative URLs
    if not parsed.netloc:
        return True
    
    # Check against allowed domains
    allowed_domains = current_app.config.get('ALLOWED_PAYMENT_DOMAINS', [])
    domain = parsed.netloc.lower()
    
    for allowed_domain in allowed_domains:
        if domain == allowed_domain or domain.endswith(f'.{allowed_domain}'):
            return True
    
    return False
