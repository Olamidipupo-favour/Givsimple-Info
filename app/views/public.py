from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models import Tag, TagStatus, AuditLog
from app import db, limiter
from app.utils.security import sanitize_input

public_bp = Blueprint('public', __name__)

@public_bp.route('/t/<token>')
@limiter.limit("10 per minute")  # Per-IP rate limit
def redirect_token(token):
    """
    Handle token redirects:
    - If token is mapped → 301 redirect to target_url
    - If token exists but unassigned → 302 redirect to /activate?token=<token>
    - If token not found → 404
    """
    # Sanitize token input
    token = sanitize_input(token)
    
    if not token or len(token) < 8 or len(token) > 16:
        abort(404)
    
    # Find the tag
    tag = Tag.query.filter_by(token=token).first()
    
    if not tag:
        # Log the attempt
        AuditLog.log('system', 'token_not_found', None, {'token': token, 'ip': request.remote_addr})
        abort(404)
    
    # Log the access
    AuditLog.log('system', 'token_accessed', tag.id, {
        'token': token,
        'status': tag.status.value,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', '')
    })
    
    if tag.status == TagStatus.ACTIVE and tag.target_url:
        # Tag is active and has a target URL - redirect to it
        return redirect(tag.target_url, code=301)
    
    elif tag.status == TagStatus.UNASSIGNED:
        # Tag exists but is unassigned - redirect to activation page
        return redirect(url_for('public.activate', token=token), code=302)
    
    elif tag.status == TagStatus.BLOCKED:
        # Tag is blocked - return 404 to hide its existence
        abort(404)
    
    elif tag.status == TagStatus.REGISTERED:
        # Tag is registered but not active - redirect to activation
        return redirect(url_for('public.activate', token=token), code=302)
    
    else:
        # Unknown status - treat as not found
        abort(404)

@public_bp.route('/activate')
def activate():
    """Show activation form"""
    token = request.args.get('token', '').strip()
    
    if not token:
        flash('No token provided.', 'error')
        return render_template('activate.html', token='')
    
    # Sanitize token
    token = sanitize_input(token)
    
    # Validate token format
    if len(token) < 8 or len(token) > 16:
        flash('Invalid token format.', 'error')
        return render_template('activate.html', token='')
    
    # Check if token exists and is in a valid state for activation
    tag = Tag.query.filter_by(token=token).first()
    
    if not tag:
        flash('Token not found.', 'error')
        return render_template('activate.html', token='')
    
    if tag.status == TagStatus.ACTIVE:
        flash('This token is already activated.', 'info')
        return render_template('activate.html', token=token, already_active=True)
    
    if tag.status == TagStatus.BLOCKED:
        flash('This token is blocked and cannot be activated.', 'error')
        return render_template('activate.html', token='')
    
    return render_template('activate.html', token=token)

@public_bp.route('/pay-by-zelle')
def zelle_instructions():
    """Show Zelle payment instructions"""
    email = request.args.get('email', '').strip()
    phone = request.args.get('phone', '').strip()
    
    if not email and not phone:
        flash('Email or phone number required for Zelle instructions.', 'error')
        return redirect(url_for('public.activate'))
    
    return render_template('zelle_instructions.html', email=email, phone=phone)

@public_bp.route('/')
def index():
    """Simple status page"""
    return render_template('index.html')
