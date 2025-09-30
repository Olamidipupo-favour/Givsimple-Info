from flask import current_app
from app.models import AdminUser, db
from app.config import Config
from datetime import datetime

def create_default_admin():
    """Create default admin user if none exists"""
    admin_count = AdminUser.query.count()
    
    if admin_count == 0:
        admin = AdminUser(
            email=Config.ADMIN_EMAIL,
            is_active=True
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        
        db.session.add(admin)
        db.session.commit()
        
        current_app.logger.info(f"Created default admin user: {Config.ADMIN_EMAIL}")
        return admin
    
    return None

def init_admin_user():
    """Initialize admin user on app startup"""
    try:
        create_default_admin()
    except Exception as e:
        current_app.logger.error(f"Failed to create default admin: {e}")
