from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_paginate import Pagination, get_page_args
from app.models import Tag, User, Activation, TagStatus, AdminUser, AuditLog
from app.schemas import AdminLoginForm, TagEditForm, CSVImportForm, SearchForm
from app.utils.security import admin_required, get_current_admin, log_admin_action, sanitize_input
from app import db
import csv
import io
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login"""
    if request.method == 'POST':
        form = AdminLoginForm()
        if form.validate_on_submit():
            admin = AdminUser.query.filter_by(
                email=form.email.data, 
                is_active=True
            ).first()
            
            if admin and admin.check_password(form.password.data):
                session['admin_logged_in'] = True
                session['admin_email'] = admin.email
                admin.last_login = datetime.utcnow()
                db.session.commit()
                
                log_admin_action('admin_login', meta={'email': admin.email})
                flash('Successfully logged in.', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash('Invalid email or password.', 'error')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@admin_required
def logout():
    """Admin logout"""
    log_admin_action('admin_logout', meta={'email': session.get('admin_email')})
    session.pop('admin_logged_in', None)
    session.pop('admin_email', None)
    flash('Successfully logged out.', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    total_tags = Tag.query.count()
    unassigned_tags = Tag.query.filter_by(status=TagStatus.UNASSIGNED).count()
    active_tags = Tag.query.filter_by(status=TagStatus.ACTIVE).count()
    blocked_tags = Tag.query.filter_by(status=TagStatus.BLOCKED).count()
    total_users = User.query.count()
    total_activations = Activation.query.count()
    
    # Recent activations
    recent_activations = Activation.query.order_by(Activation.created_at.desc()).limit(5).all()
    
    # Recent audit logs
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_tags=total_tags,
                         unassigned_tags=unassigned_tags,
                         active_tags=active_tags,
                         blocked_tags=blocked_tags,
                         total_users=total_users,
                         total_activations=total_activations,
                         recent_activations=recent_activations,
                         recent_logs=recent_logs)

@admin_bp.route('/tags')
@admin_required
def tags():
    """Tag management page"""
    search_form = SearchForm()
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page', per_page=20)
    
    # Build query
    query = Tag.query
    
    # Apply search filters
    if search_form.query.data:
        search_term = f"%{search_form.query.data}%"
        query = query.filter(Tag.token.like(search_term))
    
    if search_form.status.data:
        query = query.filter(Tag.status == TagStatus(search_form.status.data))
    
    # Get paginated results
    tags = query.order_by(Tag.created_at.desc()).offset(offset).limit(per_page).all()
    total = query.count()
    
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')
    
    return render_template('admin/tags.html', 
                         tags=tags, 
                         search_form=search_form,
                         pagination=pagination)

@admin_bp.route('/tags/<int:tag_id>')
@admin_required
def tag_detail(tag_id):
    """Tag detail page"""
    tag = Tag.query.get_or_404(tag_id)
    
    # Get audit logs for this tag
    audit_logs = AuditLog.query.filter_by(tag_id=tag_id).order_by(AuditLog.created_at.desc()).all()
    
    return render_template('admin/tag_detail.html', tag=tag, audit_logs=audit_logs)

@admin_bp.route('/tags/<int:tag_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_tag(tag_id):
    """Edit tag"""
    tag = Tag.query.get_or_404(tag_id)
    form = TagEditForm(obj=tag)
    
    if form.validate_on_submit():
        old_status = tag.status.value
        old_target_url = tag.target_url
        
        tag.status = TagStatus(form.status.data)
        tag.target_url = form.target_url.data if form.target_url.data else None
        
        # Log the change
        log_admin_action('tag_updated', tag_id, {
            'old_status': old_status,
            'new_status': tag.status.value,
            'old_target_url': old_target_url,
            'new_target_url': tag.target_url
        })
        
        db.session.commit()
        flash('Tag updated successfully.', 'success')
        return redirect(url_for('admin.tag_detail', tag_id=tag_id))
    
    return render_template('admin/edit_tag.html', tag=tag, form=form)

@admin_bp.route('/tags/<int:tag_id>/block', methods=['POST'])
@admin_required
def block_tag(tag_id):
    """Block/unblock tag"""
    tag = Tag.query.get_or_404(tag_id)
    
    if tag.status == TagStatus.BLOCKED:
        tag.status = TagStatus.UNASSIGNED
        action = 'unblocked'
    else:
        tag.status = TagStatus.BLOCKED
        action = 'blocked'
    
    log_admin_action(f'tag_{action}', tag_id, {'status': tag.status.value})
    db.session.commit()
    
    flash(f'Tag {action} successfully.', 'success')
    return redirect(url_for('admin.tag_detail', tag_id=tag_id))

@admin_bp.route('/import', methods=['GET', 'POST'])
@admin_required
def import_csv():
    """CSV import page"""
    form = CSVImportForm()
    
    if form.validate_on_submit():
        csv_data = form.csv_data.data.strip()
        if not csv_data:
            flash('No CSV data provided.', 'error')
            return render_template('admin/import.html', form=form)
        
        # Parse CSV
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header
                try:
                    token = sanitize_input(row.get('token', '').strip())
                    url = sanitize_input(row.get('url', '').strip())
                    
                    if not token or not url:
                        errors.append(f"Row {row_num}: Missing token or URL")
                        skipped_count += 1
                        continue
                    
                    # Validate token format
                    if len(token) < 8 or len(token) > 16 or not token.isalnum():
                        errors.append(f"Row {row_num}: Invalid token format '{token}'")
                        skipped_count += 1
                        continue
                    
                    # Check if token already exists
                    existing_tag = Tag.query.filter_by(token=token).first()
                    if existing_tag:
                        errors.append(f"Row {row_num}: Token '{token}' already exists")
                        skipped_count += 1
                        continue
                    
                    # Create new tag
                    tag = Tag(token=token, target_url=url, status=TagStatus.UNASSIGNED)
                    db.session.add(tag)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: Error processing - {str(e)}")
                    skipped_count += 1
            
            db.session.commit()
            
            # Log the import
            log_admin_action('csv_import', meta={
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'errors': errors
            })
            
            flash(f'Import completed: {imported_count} tags imported, {skipped_count} skipped.', 'success')
            if errors:
                flash(f'Errors: {len(errors)} rows had issues.', 'warning')
            
        except Exception as e:
            flash(f'Error parsing CSV: {str(e)}', 'error')
    
    return render_template('admin/import.html', form=form)

@admin_bp.route('/export')
@admin_required
def export_csv():
    """Export tags and activations to CSV"""
    from flask import make_response
    
    # Get all tags with their activations
    tags = Tag.query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'token', 'status', 'target_url', 'buyer_name', 'buyer_email', 
        'buyer_phone', 'activation_date', 'payment_provider', 'payment_handle'
    ])
    
    for tag in tags:
        activation = tag.activations[0] if tag.activations else None
        buyer = tag.buyer
        
        writer.writerow([
            tag.token,
            tag.status.value,
            tag.target_url or '',
            buyer.name if buyer else '',
            buyer.email if buyer else '',
            buyer.phone if buyer else '',
            activation.created_at.strftime('%Y-%m-%d %H:%M:%S') if activation else '',
            activation.payment_provider.value if activation else '',
            activation.payment_handle_or_url if activation else ''
        ])
    
    output.seek(0)
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=givsimple_export.csv'
    
    log_admin_action('csv_export', meta={'exported_count': len(tags)})
    
    return response
