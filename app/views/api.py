from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models import Tag, User, Activation, TagStatus, AuditLog
from app.schemas import ActivationForm
from app.utils.normalize import normalize_card_link, PaymentNormalizationError
from app.utils.security import sanitize_input, validate_csrf_token
from app.utils.business_card import generate_default_business_card_url, ensure_user_has_profile, update_profile_with_business_card_defaults
from app.email import send_activation_email
from app import db, limiter
import re

api_bp = Blueprint('api', __name__)

@api_bp.route('/activate', methods=['POST'])
@limiter.limit("5 per minute")  # Stricter rate limit for API
def activate():
    """
    Handle token activation:
    1. Validate token exists or create it
    2. Normalize payment handle
    3. Create user and activation record
    4. Send confirmation email
    """
    try:
        # Validate CSRF token
        if not validate_csrf_token():
            return jsonify({'error': 'Invalid CSRF token'}), 400
        
        # Get and sanitize form data
        form_data = {
            'token': sanitize_input(request.form.get('token', '')),
            'name': sanitize_input(request.form.get('name', '')),
            'email': sanitize_input(request.form.get('email', '')),
            'phone': sanitize_input(request.form.get('phone', '')),
            'payment_handle': sanitize_input(request.form.get('payment_handle', ''))
        }
        
        # Validate required fields
        if not all([form_data['token'], form_data['name'], form_data['email'], form_data['payment_handle']]):
            return jsonify({'error': 'All required fields must be provided'}), 400
        
        # Validate token format
        if not re.match(r'^[a-zA-Z0-9]{6,16}$', form_data['token']):
            return jsonify({'error': 'Invalid token format'}), 400
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', form_data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        

        
        # Find the tag
        tag = Tag.query.filter_by(token=form_data['token']).first()
        
        if not tag:
            # Create tag on the fly to allow self-service activation
            tag = Tag(token=form_data['token'], status=TagStatus.UNASSIGNED)
            db.session.add(tag)
            db.session.flush()  # Get tag.id
            AuditLog.log('system', 'token_created', tag.id, {
                'token': form_data['token'],
                'ip': request.remote_addr
            })
        
        if tag.status != TagStatus.UNASSIGNED:
            if tag.status == TagStatus.ACTIVE:
                return jsonify({'error': 'Token is already activated'}), 400
            elif tag.status == TagStatus.BLOCKED:
                return jsonify({'error': 'Token is blocked'}), 400
            else:
                return jsonify({'error': 'Token is not available for activation'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=form_data['email']).first()
        
        if existing_user:
            # Check if this user already has an activation for this tag
            existing_activation = Activation.query.filter_by(
                tag_id=tag.id, 
                user_id=existing_user.id
            ).first()
            
            if existing_activation:
                return jsonify({'error': 'This token has already been activated by this user'}), 400
            
            user = existing_user
        else:
            # Create new user
            user = User(
                name=form_data['name'],
                email=form_data['email'],
                phone=form_data['phone'] if form_data['phone'] else None
            )
            db.session.add(user)
            db.session.flush()  # Get user ID
        
        # Handle card link - either normalize provided URL or generate business card
        if form_data.get('payment_handle') and form_data['payment_handle'].strip():
            # User provided a card link - normalize it
            try:
                normalized_url = normalize_card_link(form_data['payment_handle'])
                card_link_source = 'user_provided'
            except PaymentNormalizationError as e:
                return jsonify({'error': f'Invalid card link: {str(e)}'}), 400
        else:
            # No card link provided - automatically generate business card
            try:
                # Ensure user has a profile and generate business card URL
                profile = ensure_user_has_profile(user)
                update_profile_with_business_card_defaults(profile, user)
                normalized_url = generate_default_business_card_url(user)
                card_link_source = 'auto_generated'
                
                # Use a placeholder for the payment_handle field since it's required
                form_data['payment_handle'] = normalized_url
            except Exception as e:
                current_app.logger.error(f"Failed to generate business card: {e}")
                return jsonify({'error': 'Failed to generate business card'}), 500
        
        # Create activation record
        activation = Activation(
            tag_id=tag.id,
            user_id=user.id,
            payment_handle_or_url=form_data['payment_handle'],
            resolved_target_url=normalized_url
        )
        db.session.add(activation)
        
        # Update tag status and target URL
        tag.status = TagStatus.ACTIVE
        tag.target_url = normalized_url
        tag.buyer_user_id = user.id
        
        # Log the activation
        AuditLog.log('system', 'token_activated', tag.id, {
            'user_email': user.email,
            'resolved_url': normalized_url,
            'card_link_source': card_link_source,
            'ip': request.remote_addr
        })
        
        # Commit all changes
        db.session.commit()
        
        # Send confirmation email (in background if possible)
        try:
            send_activation_email(user.email, user.name, tag.token, normalized_url)
        except Exception as e:
            current_app.logger.error(f"Failed to send activation email: {e}")
            # Don't fail the activation if email fails
        
        return jsonify({
            'success': True,
            'message': 'Token activated successfully',
            'redirect_url': normalized_url
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Activation error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'givsimple-api'
    })
