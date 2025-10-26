from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db, csrf
from app.models import User, Profile, Tag, AuditLog
from app.schemas import UserRegisterForm, UserLoginForm, ProfileForm
from app.utils.security import user_required, sanitize_input, get_current_user
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = UserRegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data.lower()).first()
        if existing_user:
            flash('An account with this email already exists. Please log in.', 'error')
            return redirect(url_for('user.login'))
        # Check if username exists
        existing_profile = Profile.query.filter_by(username=form.username.data.lower()).first()
        if existing_profile:
            flash('This username is already taken. Choose another.', 'error')
            return render_template('user/register.html', form=form)
        
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip()
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        
        profile = Profile(
            user_id=user.id,
            username=form.username.data.lower().strip(),
            display_name=form.name.data.strip()
        )
        db.session.add(profile)
        db.session.commit()
        
        session['user_logged_in'] = True
        session['user_email'] = user.email
        flash('Registration successful. Welcome!', 'success')
        return redirect(url_for('user.dashboard'))
    return render_template('user/register.html', form=form)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = UserLoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if not user or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'error')
            return render_template('user/login.html', form=form)
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        session['user_logged_in'] = True
        session['user_email'] = user.email
        flash('Logged in successfully.', 'success')
        return redirect(url_for('user.dashboard'))
    return render_template('user/login.html', form=form)

@user_bp.route('/logout')
@user_required
def logout():
    session.pop('user_logged_in', None)
    session.pop('user_email', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('public.index'))

@user_bp.route('/dashboard')
@user_required
def dashboard():
    user = get_current_user()
    profile = user.profile
    # Stats: tags and audit logs
    tags = Tag.query.filter_by(buyer_user_id=user.id).all()
    tag_ids = [t.id for t in tags]
    activations = AuditLog.query.filter(AuditLog.tag_id.in_(tag_ids), AuditLog.action == 'token_activated').count() if tag_ids else 0
    accesses = AuditLog.query.filter(AuditLog.tag_id.in_(tag_ids), AuditLog.action == 'token_accessed').count() if tag_ids else 0
    return render_template('user/dashboard.html', user=user, profile=profile, tags=tags, activations=activations, accesses=accesses)

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@user_required
def profile_edit():
    user = get_current_user()
    profile = user.profile
    form = ProfileForm()
    if request.method == 'POST' and form.validate_on_submit():
        profile.display_name = sanitize_input(form.display_name.data or '')
        profile.headline = sanitize_input(form.headline.data or '')
        profile.bio = sanitize_input(form.bio.data or '')
        profile.avatar_url = sanitize_input(form.avatar_url.data or '')
        profile.theme = sanitize_input(form.theme.data or 'light')
        profile.links_json = (form.links_json.data or '').strip() or None
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('user.dashboard'))
    # Pre-fill form
    form.display_name.data = profile.display_name
    form.headline.data = profile.headline
    form.bio.data = profile.bio
    form.avatar_url.data = profile.avatar_url
    form.theme.data = profile.theme or 'light'
    form.links_json.data = profile.links_json or ''
    return render_template('user/profile_edit.html', form=form, profile=profile)

@user_bp.route('/tags')
@user_required
def manage_tags():
    user = get_current_user()
    tags = Tag.query.filter_by(buyer_user_id=user.id).all()
    return render_template('user/tags.html', tags=tags, user=user)

@user_bp.route('/nfc/write')
@user_required
def nfc_write():
    user = get_current_user()
    profile = user.profile
    # Profile URL to write to NFC tag
    profile_url = url_for('public.profile', username=profile.username, _external=True)
    return render_template('user/nfc_write.html', profile_url=profile_url, profile=profile)