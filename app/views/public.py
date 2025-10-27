from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models import Tag, TagStatus, AuditLog
from app import db, limiter
from app.utils.security import sanitize_input

public_bp = Blueprint('public', __name__)

# New: Handle root-level token URLs and show countdown for active tags
@public_bp.route('/<regex("^(?!activate$)(?!admin$)(?!api$)[A-Za-zA-Z0-9]{6,16}$"):token>')
@limiter.limit("10 per minute")
def redirect_root_token(token):
    """
    Handle root-level token URLs (e.g., /ABCDEFG1).
    - ACTIVE tags: render countdown page to target URL
    - UNASSIGNED/REGISTERED: redirect to activation page
    - BLOCKED: return 404
    - Unknown tokens: auto-create as UNASSIGNED and redirect to activation
    """
    token = sanitize_input(token)

    # Basic length validation to avoid reserved paths and invalid tokens
    if not token or len(token) < 6 or len(token) > 16:
        return render_template('404.html'), 404

    tag = Tag.query.filter_by(token=token).first()

    if not tag:
        # Auto-create tag on first visit and redirect to activation
        new_tag = Tag(token=token, status=TagStatus.UNASSIGNED)
        db.session.add(new_tag)
        db.session.flush()  # get id
        AuditLog.log('system', 'token_created', new_tag.id, {
            'token': token,
            'ip': request.remote_addr,
            'source': 'redirect_root'
        })
        db.session.commit()
        return redirect(url_for('public.activate', token=token), code=302)

    # Log the access for analytics/monitoring
    AuditLog.log('system', 'token_accessed', tag.id, {
        'token': token,
        'status': tag.status.value,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'source': 'redirect_root'
    })

    if tag.status == TagStatus.BLOCKED:
        return render_template('404.html'), 404
    elif tag.status == TagStatus.ACTIVE and tag.target_url:
        # Render a friendly countdown page instead of immediate redirect
        return render_template('redirect_countdown.html', target_url=tag.target_url)
    elif tag.status in (TagStatus.UNASSIGNED, TagStatus.REGISTERED):
        return redirect(url_for('public.activate', token=token), code=302)
    else:
        return render_template('404.html'), 404

@public_bp.route('/t/<token>')
@limiter.limit("10 per minute")  # Per-IP rate limit
def redirect_token(token):
    """
    Handle token redirects:
    - If token is mapped → 301 redirect to target_url
    - If token exists but unassigned → 302 redirect to /activate?token=<token>
    - If token not found → redirect to activation page
    """
    # Sanitize token input
    token = sanitize_input(token)
    
    if not token or len(token) < 6 or len(token) > 16:
        return render_template('404.html'), 404
    
    # Find the tag
    tag = Tag.query.filter_by(token=token).first()
    
    if not tag:
        # Create tag on first visit and redirect to activation
        new_tag = Tag(token=token, status=TagStatus.UNASSIGNED)
        db.session.add(new_tag)
        db.session.flush()  # get id
        AuditLog.log('system', 'token_created', new_tag.id, {'token': token, 'ip': request.remote_addr, 'source': 'redirect'})
        db.session.commit()
        return redirect(url_for('public.activate', token=token), code=302)
    
    # Log the access
    AuditLog.log('system', 'token_accessed', tag.id, {
        'token': token,
        'status': tag.status.value,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', '')
    })
    
    # Check status and handle accordingly
    if tag.status == TagStatus.BLOCKED:
        # Tag is blocked - return 404 to hide its existence
        return render_template('404.html'), 404
    
    elif tag.status == TagStatus.ACTIVE and tag.target_url:
        # For browsers, show a friendly countdown page; API clients keep 301
        accept = request.headers.get('Accept', '')
        if 'text/html' in accept:
            return render_template('redirect_countdown.html', target_url=tag.target_url)
        return redirect(tag.target_url, code=301)
    
    elif tag.status == TagStatus.UNASSIGNED:
        # Tag exists but is unassigned - redirect to activation page
        return redirect(url_for('public.activate', token=token), code=302)
    
    elif tag.status == TagStatus.REGISTERED:
        # Tag is registered but not active - redirect to activation
        return redirect(url_for('public.activate', token=token), code=302)
    
    else:
        # Unknown status - treat as not found
        return render_template('404.html'), 404

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
    if len(token) < 6 or len(token) > 16:
        flash('Invalid token format.', 'error')
        return render_template('activate.html', token='')
    
    # Check if token exists and is in a valid state for activation
    tag = Tag.query.filter_by(token=token).first()
    
    if not tag:
        # Auto-create tag on activation page visit
        new_tag = Tag(token=token, status=TagStatus.UNASSIGNED)
        db.session.add(new_tag)
        db.session.flush()
        AuditLog.log('system', 'token_created', new_tag.id, {'token': token, 'ip': request.remote_addr, 'source': 'activate_page'})
        db.session.commit()
        flash('New token created. You can activate it now.', 'info')
        return render_template('activate.html', token=token)
    
    if tag.status == TagStatus.ACTIVE:
        flash('This token is already activated.', 'info')
        return render_template('activate.html', token=token, already_active=True)
    
    if tag.status == TagStatus.BLOCKED:
        flash('This token is blocked and cannot be activated.', 'error')
        return render_template('activate.html', token='')
    
    return render_template('activate.html', token=token)


@public_bp.route('/u/<username>')
def profile(username):
    """Public profile page"""
    from app.models import Profile
    username = sanitize_input(username.lower())
    profile = Profile.query.filter_by(username=username).first()
    if not profile:
        abort(404)
    return render_template('public/profile.html', profile=profile)

@public_bp.route('/')
def index():
    """Simple status page"""
    return render_template('index.html')

@public_bp.route('/activate/success')
def activation_success():
    token = request.args.get('token', '').strip()
    if not token:
        flash('No token provided.', 'error')
        return redirect(url_for('public.activate'))
    token = sanitize_input(token)
    from app.models import Tag, TagStatus
    tag = Tag.query.filter_by(token=token).first()
    if not tag or tag.status != TagStatus.ACTIVE or not tag.target_url:
        flash('Activation not found or token not active.', 'error')
        return redirect(url_for('public.activate', token=token))
    return render_template('redirect_countdown.html', target_url=tag.target_url)
